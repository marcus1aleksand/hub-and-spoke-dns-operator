import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Mocked Environment Variables — Azure (default provider)
os.environ["CLOUD_PROVIDER"] = "azure"
os.environ["MANAGED_IDENTITY_CLIENT_ID"] = "fake-client-id"
os.environ["AZURE_SUBSCRIPTION_ID"] = "fake-subscription-id"
os.environ["AZURE_DNS_ZONE"] = "example.com"
os.environ["AZURE_DNS_RESOURCE_GROUP"] = "fake-resource-group"
os.environ["CUSTOM_IP"] = "1.2.3.4"
os.environ["CUSTOM_TTL"] = "300"

with patch("kubernetes.config.load_incluster_config", MagicMock()):
    with patch("providers.azure.ManagedIdentityCredential", MagicMock()):
        with patch("providers.azure.DnsManagementClient", MagicMock()):
            import main


@pytest.fixture
def mock_provider():
    with patch.object(main, "dns_provider") as mock:
        mock.provider_name = "azure"
        mock.create_or_update_record = AsyncMock()
        mock.delete_record = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_create_or_update_dns_record(mock_provider):
    ingress = {
        "spec": {"rules": [{"host": "test.example.com"}], "ingressClassName": "nginx"},
        "metadata": {"annotations": {}},
        "status": {"loadBalancer": {"ingress": [{"ip": "5.6.7.8"}]}},
    }

    await main.create_or_update_dns_record(ingress, "create")

    mock_provider.create_or_update_record.assert_called_once_with(
        "test.example.com", "1.2.3.4", 300
    )


@pytest.mark.asyncio
async def test_delete_dns_record(mock_provider):
    ingress = {"spec": {"rules": [{"host": "test.example.com"}]}}

    await main.delete_dns_record(ingress)
    mock_provider.delete_record.assert_called_once_with("test.example.com")


@pytest.mark.asyncio
async def test_ingress_event_handler(mock_provider):
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

    with patch("main.create_or_update_dns_record", new_callable=AsyncMock) as mock_create, \
         patch("main.delete_dns_record", new_callable=AsyncMock) as mock_delete:
        await main.ingress_event_handler(add_event)
        mock_create.assert_called_once_with(add_event["object"], "create")

        await main.ingress_event_handler(modify_event)
        mock_create.assert_called_with(modify_event["object"], "update")

        await main.ingress_event_handler(delete_event)
        mock_delete.assert_called_once_with(delete_event["object"])


@pytest.mark.asyncio
async def test_health_check():
    request = MagicMock()
    response = await main.health_check(request)
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_readiness_check():
    request = MagicMock()
    response = await main.readiness_check(request)
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Test that the metrics endpoint returns Prometheus metrics"""
    request = MagicMock()
    response = await main.metrics_handler(request)
    assert response.content_type == "text/plain; version=0.0.4; charset=utf-8"
    body = response.body.decode('utf-8')
    assert 'dns_operator_operations_total' in body
    assert 'dns_operator_operation_duration_seconds' in body
    assert 'dns_operator_errors_total' in body
    assert 'dns_operator_records_managed' in body
    assert 'dns_operator_info' in body


def test_provider_factory():
    """Test that the provider factory returns correct provider types"""
    assert main.dns_provider is not None
    assert main.dns_provider.provider_name == "azure"


# =============================================================================
# Provider Base Class Tests
# =============================================================================

def test_extract_record_name():
    """Test DNS zone stripping from FQDN"""
    from providers.base import DNSProvider

    class TestProvider(DNSProvider):
        @property
        def provider_name(self): return "test"
        async def create_or_update_record(self, *a): pass
        async def delete_record(self, *a): pass

    p = TestProvider()
    assert p.extract_record_name("app.example.com", "example.com") == "app"
    assert p.extract_record_name("deep.sub.example.com", "example.com") == "deep.sub"
    assert p.extract_record_name("other.domain.io", "example.com") == "other.domain.io"
