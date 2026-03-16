"""Tests for CNAME record support."""

import pytest
from unittest.mock import patch, MagicMock

from providers.base import RecordType, DNSRecord


class TestRecordType:
    """Tests for RecordType enum."""

    def test_record_type_a(self):
        assert RecordType.A.value == "A"

    def test_record_type_cname(self):
        assert RecordType.CNAME.value == "CNAME"


class TestDNSRecord:
    """Tests for DNSRecord dataclass."""

    def test_dns_record_a(self):
        record = DNSRecord(name="app", value="1.2.3.4", record_type=RecordType.A, ttl=300)
        assert record.name == "app"
        assert record.value == "1.2.3.4"
        assert record.record_type == RecordType.A
        assert record.ttl == 300

    def test_dns_record_cname(self):
        record = DNSRecord(name="app", value="example.com", record_type=RecordType.CNAME, ttl=300)
        assert record.name == "app"
        assert record.value == "example.com"
        assert record.record_type == RecordType.CNAME


class TestIsHostname:
    """Tests for hostname detection."""

    def _make_provider(self):
        from providers.base import DNSProvider

        class ConcreteProvider(DNSProvider):
            @property
            def provider_name(self):
                return "test"

            async def create_or_update_record(self, record_name, value, record_type=RecordType.A, ttl=300):
                pass

            async def delete_record(self, record_name, record_type=RecordType.A):
                pass

        return ConcreteProvider()

    def test_ip_address_not_hostname(self):
        p = self._make_provider()
        assert p.is_hostname("1.2.3.4") is False
        assert p.is_hostname("192.168.1.1") is False

    def test_hostname_is_hostname(self):
        p = self._make_provider()
        assert p.is_hostname("example.com") is True
        assert p.is_hostname("app.example.com") is True
        assert p.is_hostname("my-service.namespace.svc.cluster.local") is True


class TestAzureCNAMERecordSupport:
    """Tests for CNAME support in Azure provider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("MANAGED_IDENTITY_CLIENT_ID", "fake-client-id")
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "fake-sub-id")
        monkeypatch.setenv("AZURE_DNS_ZONE", "example.com")
        monkeypatch.setenv("AZURE_DNS_RESOURCE_GROUP", "fake-rg")

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_create_cname_record(self, mock_cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.record_sets.create_or_update = MagicMock()
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        await provider.create_or_update_record(
            "app.example.com", "backend.example.com", RecordType.CNAME, 300
        )

        mock_client.record_sets.create_or_update.assert_called_once_with(
            "fake-rg", "example.com", "app", "CNAME",
            {"ttl": 300, "cname_record": {"cname": "backend.example.com"}},
        )

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_delete_cname_record(self, mock_cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.record_sets.delete = MagicMock()
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        await provider.delete_record("app.example.com", RecordType.CNAME)

        mock_client.record_sets.delete.assert_called_once_with(
            "fake-rg", "example.com", "app", "CNAME"
        )


class TestGCPCNAMERecordSupport:
    """Tests for CNAME support in GCP provider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("GCP_PROJECT_ID", "fake-project")
        monkeypatch.setenv("GCP_MANAGED_ZONE", "fake-zone")
        monkeypatch.setenv("GCP_DNS_ZONE", "example.com")

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_create_cname_record(self, mock_dns):
        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = []
        mock_changes = MagicMock()
        mock_zone.changes.return_value = mock_changes
        mock_record = MagicMock()
        mock_zone.resource_record_set.return_value = mock_record
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        await provider.create_or_update_record(
            "app.example.com", "backend.example.com", RecordType.CNAME, 300
        )

        mock_zone.resource_record_set.assert_called_once_with(
            "app.example.com.", "CNAME", 300, ["backend.example.com"]
        )
        mock_changes.add_record_set.assert_called_once_with(mock_record)
        mock_changes.create.assert_called_once()

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_delete_cname_record(self, mock_dns):
        existing_record = MagicMock()
        existing_record.name = "app.example.com."
        existing_record.record_type = "CNAME"

        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = [existing_record]
        mock_changes = MagicMock()
        mock_zone.changes.return_value = mock_changes
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        await provider.delete_record("app.example.com", RecordType.CNAME)

        mock_changes.delete_record_set.assert_called_once_with(existing_record)
        mock_changes.create.assert_called_once()


class TestAWSCNAMERecordSupport:
    """Tests for CNAME support in AWS provider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("AWS_HOSTED_ZONE_ID", "Z1234567890")
        monkeypatch.setenv("AWS_DNS_ZONE", "example.com")
        monkeypatch.setenv("AWS_REGION", "us-east-1")

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_create_cname_record(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        await provider.create_or_update_record(
            "app.example.com", "backend.example.com", RecordType.CNAME, 300
        )

        mock_client.change_resource_record_sets.assert_called_once_with(
            HostedZoneId="Z1234567890",
            ChangeBatch={
                "Changes": [{
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "app.example.com.",
                        "Type": "CNAME",
                        "TTL": 300,
                        "ResourceRecords": [{"Value": "backend.example.com"}],
                    },
                }]
            },
        )

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_delete_cname_record(self, mock_boto3):
        mock_client = MagicMock()
        existing = {
            "Name": "app.example.com.",
            "Type": "CNAME",
            "TTL": 300,
            "ResourceRecords": [{"Value": "backend.example.com"}],
        }
        mock_client.list_resource_record_sets.return_value = {
            "ResourceRecordSets": [existing]
        }
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        await provider.delete_record("app.example.com", RecordType.CNAME)

        mock_client.change_resource_record_sets.assert_called_once_with(
            HostedZoneId="Z1234567890",
            ChangeBatch={"Changes": [{"Action": "DELETE", "ResourceRecordSet": existing}]},
        )


class TestAnnotationParsing:
    """Tests for annotation parsing in annotations.py."""

    def test_explicit_cname_annotation(self):
        from annotations import get_record_type
        annotations = {"hub-dns-operator.io/record-type": "CNAME"}
        assert get_record_type(annotations) == RecordType.CNAME

    def test_explicit_a_annotation(self):
        from annotations import get_record_type
        annotations = {"hub-dns-operator.io/record-type": "A"}
        assert get_record_type(annotations) == RecordType.A

    def test_default_a_without_annotation(self):
        from annotations import get_record_type
        assert get_record_type({}) == RecordType.A

    def test_case_insensitive_annotation(self):
        from annotations import get_record_type
        annotations = {"hub-dns-operator.io/record-type": "cname"}
        assert get_record_type(annotations) == RecordType.CNAME

    def test_target_from_annotation(self):
        from annotations import get_target_value
        ingress = {"status": {"loadBalancer": {"ingress": [{"ip": "1.2.3.4"}]}}}
        annotations = {
            "hub-dns-operator.io/target-hostname": "my-backend.example.com"
        }
        assert get_target_value(ingress, annotations) == "my-backend.example.com"

    def test_target_from_loadbalancer(self):
        from annotations import get_target_value
        ingress = {"status": {"loadBalancer": {"ingress": [{"ip": "1.2.3.4"}]}}}
        assert get_target_value(ingress, {}) == "1.2.3.4"

    def test_target_no_source_raises_error(self):
        from annotations import get_target_value
        ingress = {}
        with pytest.raises(ValueError, match="No target value found"):
            get_target_value(ingress, {})
