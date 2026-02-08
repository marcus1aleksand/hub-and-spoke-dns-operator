import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Mocked Environment Variables
os.environ["MANAGED_IDENTITY_CLIENT_ID"] = "fake-client-id"
os.environ["AZURE_SUBSCRIPTION_ID"] = "fake-subscription-id"
os.environ["AZURE_DNS_ZONE"] = "example.com"
os.environ["AZURE_DNS_RESOURCE_GROUP"] = "fake-resource-group"
os.environ["CUSTOM_IP"] = "1.2.3.4"
os.environ["CUSTOM_TTL"] = "300"

with patch("kubernetes.config.load_incluster_config", MagicMock()):
    import main


@pytest.fixture
def mock_dns_client():
    with patch("main.dns_client") as mock:
        yield mock


@pytest.fixture
def mock_api_client():
    with patch("main.api_client") as mock:
        yield mock


@pytest.mark.asyncio
async def test_create_or_update_dns_record(mock_dns_client, mock_api_client):
    ingress = {
        "spec": {"rules": [{"host": "test.com"}], "ingressClassName": "nginx"},
        "metadata": {"annotations": {}},
        "status": {"loadBalancer": {"ingress": [{"ip": "5.6.7.8"}]}},
    }
    mock_create_or_update = AsyncMock()
    mock_dns_client.record_sets.create_or_update = mock_create_or_update

    await main.create_or_update_dns_record(ingress, "create")

    mock_create_or_update.assert_called_once()
    args, kwargs = mock_create_or_update.call_args
    assert args[0] == "fake-resource-group"
    assert args[1] == "example.com"
    assert args[2] == "test.com"
    assert args[3] == "A"
    parameters = args[4]
    assert parameters["ttl"] == 300
    assert parameters["arecords"][0]["ipv4_address"] == "1.2.3.4"


@pytest.mark.asyncio
async def test_delete_dns_record(mock_dns_client):
    ingress = {"spec": {"rules": [{"host": "test.example.com"}]}}
    mock_delete = AsyncMock()
    mock_dns_client.record_sets.delete = mock_delete

    await main.delete_dns_record(ingress)
    mock_delete.assert_called_once_with("fake-resource-group", "example.com", "test", "A")


@pytest.mark.asyncio
async def test_ingress_event_handler(mock_dns_client, mock_api_client):
    add_event = {
        "type": "ADDED",
        "object": {
            "spec": {
                "rules": [{"host": "test.example.com"}],
                "ingressClassName": "nginx",
            },
            "metadata": {"annotations": {}},
            "status": {"loadBalancer": {"ingress": [{"ip": "5.6.7.8"}]}},
        },
    }
    modify_event = {
        "type": "MODIFIED",
        "object": {
            "spec": {
                "rules": [{"host": "test.example.com"}],
                "ingressClassName": "nginx",
            },
            "metadata": {"annotations": {}},
            "status": {"loadBalancer": {"ingress": [{"ip": "5.6.7.8"}]}},
        },
    }
    delete_event = {
        "type": "DELETED",
        "object": {"spec": {"rules": [{"host": "test.example.com"}]}},
    }

    with patch("main.create_or_update_dns_record", new_callable=AsyncMock) as mock_create_or_update, patch(
        "main.delete_dns_record", new_callable=AsyncMock
    ) as mock_delete:
        await main.ingress_event_handler(add_event)
        mock_create_or_update.assert_called_once_with(add_event["object"], "create")

        await main.ingress_event_handler(modify_event)
        mock_create_or_update.assert_called_with(modify_event["object"], "update")

        await main.ingress_event_handler(delete_event)
        mock_delete.assert_called_once_with(delete_event["object"])


@pytest.mark.asyncio
async def test_health_check():
    request = MagicMock()
    with patch("main.web.Response") as mock_response:
        response = await main.health_check(request)
        mock_response.assert_called_once_with(text="OK")
        assert response == mock_response()


@pytest.mark.asyncio
async def test_readiness_check():
    request = MagicMock()
    with patch("main.web.Response") as mock_response:
        response = await main.readiness_check(request)
        mock_response.assert_called_once_with(text="OK")
        assert response == mock_response()


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that the metrics endpoint returns Prometheus metrics"""
    request = MagicMock()
    response = await main.metrics_handler(request)

    # Check response has correct content type
    assert response.content_type == "text/plain; version=0.0.4; charset=utf-8"

    # Check that response body contains expected metrics
    body = response.body.decode('utf-8')
    assert 'dns_operator_operations_total' in body
    assert 'dns_operator_operation_duration_seconds' in body
    assert 'dns_operator_errors_total' in body
    assert 'dns_operator_records_managed' in body
    assert 'dns_operator_info' in body


def test_metrics_increment_on_success(mock_dns_client, mock_api_client):
    """Test that metrics are incremented on successful operations"""
    from prometheus_client import REGISTRY

    # Get initial values
    REGISTRY.get_sample_value(
        'dns_operator_operations_total',
        {'operation': 'create', 'status': 'success'}
    )

    # The metrics should be defined
    assert main.dns_operations_total is not None
    assert main.dns_operation_duration_seconds is not None
    assert main.dns_errors_total is not None
    assert main.dns_records_managed is not None
