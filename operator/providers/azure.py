"""Azure DNS provider implementation."""

import os
import logging
from azure.identity import ManagedIdentityCredential
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError

from providers.base import DNSProvider

logger = logging.getLogger(__name__)


class AzureDNSProvider(DNSProvider):
    """Azure DNS provider using Azure DNS Zones."""

    def __init__(self):
        credential = ManagedIdentityCredential(
            client_id=os.environ["MANAGED_IDENTITY_CLIENT_ID"]
        )
        self._client = DnsManagementClient(
            credential, os.environ["AZURE_SUBSCRIPTION_ID"]
        )
        self._dns_zone = os.environ["AZURE_DNS_ZONE"]
        self._resource_group = os.environ["AZURE_DNS_RESOURCE_GROUP"]

    @property
    def provider_name(self) -> str:
        return "azure"

    async def create_or_update_record(self, record_name: str, ip_address: str, ttl: int) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        try:
            await self._client.record_sets.create_or_update(
                self._resource_group,
                self._dns_zone,
                name,
                "A",
                {"ttl": ttl, "arecords": [{"ipv4_address": ip_address}]},
            )
            logger.info(f"[Azure] DNS record upserted: {name} -> {ip_address}")
        except HttpResponseError as e:
            logger.error(f"[Azure] Error upserting DNS record {name}: {e.message}")
            raise

    async def delete_record(self, record_name: str) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        try:
            await self._client.record_sets.delete(
                self._resource_group, self._dns_zone, name, "A"
            )
            logger.info(f"[Azure] DNS record deleted: {name}")
        except HttpResponseError as e:
            logger.error(f"[Azure] Error deleting DNS record {name}: {e.message}")
            raise
