"""Tests for cloud DNS providers (Azure, GCP, AWS)."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Base Provider Tests
# =============================================================================

class TestDNSProviderBase:
    """Tests for the abstract base DNSProvider class."""

    def _make_provider(self):
        from providers.base import DNSProvider

        class ConcreteProvider(DNSProvider):
            @property
            def provider_name(self):
                return "test"

            async def create_or_update_record(self, record_name, ip_address, ttl):
                pass

            async def delete_record(self, record_name):
                pass

        return ConcreteProvider()

    def test_extract_record_name_simple(self):
        p = self._make_provider()
        assert p.extract_record_name("app.example.com", "example.com") == "app"

    def test_extract_record_name_nested_subdomain(self):
        p = self._make_provider()
        assert p.extract_record_name("a.b.c.example.com", "example.com") == "a.b.c"

    def test_extract_record_name_no_match(self):
        p = self._make_provider()
        assert p.extract_record_name("app.other.io", "example.com") == "app.other.io"

    def test_extract_record_name_exact_zone(self):
        """When FQDN equals zone, returns the FQDN unchanged (no dot-prefix match)."""
        p = self._make_provider()
        # "example.com" doesn't end with ".example.com", so it's returned as-is
        assert p.extract_record_name("example.com", "example.com") == "example.com"

    def test_provider_is_abstract(self):
        from providers.base import DNSProvider
        with pytest.raises(TypeError):
            DNSProvider()


# =============================================================================
# Azure Provider Tests
# =============================================================================

class TestAzureDNSProvider:
    """Tests for AzureDNSProvider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("MANAGED_IDENTITY_CLIENT_ID", "fake-client-id")
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "fake-sub-id")
        monkeypatch.setenv("AZURE_DNS_ZONE", "example.com")
        monkeypatch.setenv("AZURE_DNS_RESOURCE_GROUP", "fake-rg")

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    def test_init(self, mock_cred, mock_client):
        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        assert provider.provider_name == "azure"
        mock_cred.assert_called_once_with(client_id="fake-client-id")
        mock_client.assert_called_once()

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_create_or_update_record(self, mock_cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.record_sets.create_or_update = AsyncMock()
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

        mock_client.record_sets.create_or_update.assert_called_once_with(
            "fake-rg", "example.com", "app", "A",
            {"ttl": 300, "arecords": [{"ipv4_address": "1.2.3.4"}]},
        )

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_delete_record(self, mock_cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.record_sets.delete = AsyncMock()
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        await provider.delete_record("app.example.com")

        mock_client.record_sets.delete.assert_called_once_with(
            "fake-rg", "example.com", "app", "A"
        )

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_create_record_error(self, mock_cred, mock_client_cls):
        from azure.core.exceptions import HttpResponseError
        mock_client = MagicMock()
        mock_client.record_sets.create_or_update = AsyncMock(
            side_effect=HttpResponseError(message="Forbidden")
        )
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        with pytest.raises(HttpResponseError):
            await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

    @patch("providers.azure.DnsManagementClient")
    @patch("providers.azure.ManagedIdentityCredential")
    @pytest.mark.asyncio
    async def test_delete_record_error(self, mock_cred, mock_client_cls):
        from azure.core.exceptions import HttpResponseError
        mock_client = MagicMock()
        mock_client.record_sets.delete = AsyncMock(
            side_effect=HttpResponseError(message="Not found")
        )
        mock_client_cls.return_value = mock_client

        from providers.azure import AzureDNSProvider
        provider = AzureDNSProvider()
        with pytest.raises(HttpResponseError):
            await provider.delete_record("app.example.com")


# =============================================================================
# GCP Provider Tests
# =============================================================================

class TestGCPDNSProvider:
    """Tests for GCPDNSProvider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("GCP_PROJECT_ID", "fake-project")
        monkeypatch.setenv("GCP_MANAGED_ZONE", "fake-zone")
        monkeypatch.setenv("GCP_DNS_ZONE", "example.com")

    @patch("providers.gcp.google_dns")
    def test_init(self, mock_dns):
        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        assert provider.provider_name == "gcp"
        mock_dns.Client.assert_called_once_with(project="fake-project")

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_create_new_record(self, mock_dns):
        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = []
        mock_changes = MagicMock()
        mock_zone.changes.return_value = mock_changes
        mock_record = MagicMock()
        mock_zone.resource_record_set.return_value = mock_record
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

        mock_zone.resource_record_set.assert_called_once_with(
            "app.example.com.", "A", 300, ["1.2.3.4"]
        )
        mock_changes.add_record_set.assert_called_once_with(mock_record)
        mock_changes.create.assert_called_once()

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_create_replaces_existing_record(self, mock_dns):
        existing_record = MagicMock()
        existing_record.name = "app.example.com."
        existing_record.record_type = "A"

        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = [existing_record]
        mock_changes = MagicMock()
        mock_zone.changes.return_value = mock_changes
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

        mock_changes.delete_record_set.assert_called_once_with(existing_record)
        mock_changes.add_record_set.assert_called_once()

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_delete_record_exists(self, mock_dns):
        existing_record = MagicMock()
        existing_record.name = "app.example.com."
        existing_record.record_type = "A"

        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = [existing_record]
        mock_changes = MagicMock()
        mock_zone.changes.return_value = mock_changes
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        await provider.delete_record("app.example.com")

        mock_changes.delete_record_set.assert_called_once_with(existing_record)
        mock_changes.create.assert_called_once()

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, mock_dns):
        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = []
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        # Should not raise, just log warning
        await provider.delete_record("app.example.com")

    @patch("providers.gcp.google_dns")
    @pytest.mark.asyncio
    async def test_create_record_error(self, mock_dns):
        from google.api_core.exceptions import GoogleAPICallError
        mock_zone = MagicMock()
        mock_zone.list_resource_record_sets.return_value = []
        mock_changes = MagicMock()
        mock_changes.create.side_effect = GoogleAPICallError("API error")
        mock_zone.changes.return_value = mock_changes
        mock_dns.Client.return_value.zone.return_value = mock_zone

        from providers.gcp import GCPDNSProvider
        provider = GCPDNSProvider()
        with pytest.raises(GoogleAPICallError):
            await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)


# =============================================================================
# AWS Provider Tests
# =============================================================================

class TestAWSDNSProvider:
    """Tests for AWSDNSProvider."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("AWS_HOSTED_ZONE_ID", "Z1234567890")
        monkeypatch.setenv("AWS_DNS_ZONE", "example.com")
        monkeypatch.setenv("AWS_REGION", "us-east-1")

    @patch("providers.aws.boto3")
    def test_init(self, mock_boto3):
        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        assert provider.provider_name == "aws"
        mock_boto3.client.assert_called_once_with("route53", region_name="us-east-1")

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_create_or_update_record(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

        mock_client.change_resource_record_sets.assert_called_once_with(
            HostedZoneId="Z1234567890",
            ChangeBatch={
                "Changes": [{
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "app.example.com.",
                        "Type": "A",
                        "TTL": 300,
                        "ResourceRecords": [{"Value": "1.2.3.4"}],
                    },
                }]
            },
        )

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_delete_record_exists(self, mock_boto3):
        mock_client = MagicMock()
        existing = {
            "Name": "app.example.com.",
            "Type": "A",
            "TTL": 300,
            "ResourceRecords": [{"Value": "1.2.3.4"}],
        }
        mock_client.list_resource_record_sets.return_value = {
            "ResourceRecordSets": [existing]
        }
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        await provider.delete_record("app.example.com")

        mock_client.change_resource_record_sets.assert_called_once_with(
            HostedZoneId="Z1234567890",
            ChangeBatch={"Changes": [{"Action": "DELETE", "ResourceRecordSet": existing}]},
        )

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, mock_boto3):
        mock_client = MagicMock()
        mock_client.list_resource_record_sets.return_value = {
            "ResourceRecordSets": []
        }
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        # Should not raise
        await provider.delete_record("app.example.com")
        # Should not attempt deletion
        mock_client.change_resource_record_sets.assert_not_called()

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_create_record_error(self, mock_boto3):
        from botocore.exceptions import ClientError
        mock_client = MagicMock()
        mock_client.change_resource_record_sets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Forbidden"}},
            "ChangeResourceRecordSets"
        )
        mock_boto3.client.return_value = mock_client

        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        with pytest.raises(ClientError):
            await provider.create_or_update_record("app.example.com", "1.2.3.4", 300)

    @patch("providers.aws.boto3")
    @pytest.mark.asyncio
    async def test_default_region(self, mock_boto3, monkeypatch):
        monkeypatch.delenv("AWS_REGION", raising=False)
        from providers.aws import AWSDNSProvider
        provider = AWSDNSProvider()
        assert provider._region == "us-east-1"


# =============================================================================
# Provider Factory Tests
# =============================================================================

class TestProviderFactory:
    """Tests for create_dns_provider factory function."""

    @patch("kubernetes.config.load_incluster_config", MagicMock())
    def test_factory_azure(self, monkeypatch):
        monkeypatch.setenv("CLOUD_PROVIDER", "azure")
        monkeypatch.setenv("MANAGED_IDENTITY_CLIENT_ID", "x")
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "x")
        monkeypatch.setenv("AZURE_DNS_ZONE", "example.com")
        monkeypatch.setenv("AZURE_DNS_RESOURCE_GROUP", "x")
        with patch("providers.azure.ManagedIdentityCredential", MagicMock()), \
             patch("providers.azure.DnsManagementClient", MagicMock()):
            from main import create_dns_provider
            provider = create_dns_provider()
            assert provider.provider_name == "azure"

    @patch("kubernetes.config.load_incluster_config", MagicMock())
    def test_factory_gcp(self, monkeypatch):
        monkeypatch.setenv("CLOUD_PROVIDER", "gcp")
        monkeypatch.setenv("GCP_PROJECT_ID", "x")
        monkeypatch.setenv("GCP_MANAGED_ZONE", "x")
        monkeypatch.setenv("GCP_DNS_ZONE", "example.com")
        with patch("providers.gcp.google_dns", MagicMock()):
            from main import create_dns_provider
            provider = create_dns_provider()
            assert provider.provider_name == "gcp"

    @patch("kubernetes.config.load_incluster_config", MagicMock())
    def test_factory_aws(self, monkeypatch):
        monkeypatch.setenv("CLOUD_PROVIDER", "aws")
        monkeypatch.setenv("AWS_HOSTED_ZONE_ID", "x")
        monkeypatch.setenv("AWS_DNS_ZONE", "example.com")
        with patch("providers.aws.boto3", MagicMock()):
            from main import create_dns_provider
            provider = create_dns_provider()
            assert provider.provider_name == "aws"

    @patch("kubernetes.config.load_incluster_config", MagicMock())
    def test_factory_invalid(self, monkeypatch):
        monkeypatch.setenv("CLOUD_PROVIDER", "invalid")
        from main import create_dns_provider
        with pytest.raises(ValueError, match="Unsupported cloud provider"):
            create_dns_provider()
