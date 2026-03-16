"""Azure DNS provider implementation."""

import asyncio
import os
import logging
from azure.identity import ManagedIdentityCredential
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError

from providers.base import DNSProvider, RecordType

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

    async def create_or_update_record(self, record_name: str, value: str, record_type: RecordType = RecordType.A, ttl: int = 300) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        record_type_str = record_type.value

        def _upsert():
            if record_type == RecordType.CNAME:
                self._client.record_sets.create_or_update(
                    self._resource_group,
                    self._dns_zone,
                    name,
                    "CNAME",
                    {"ttl": ttl, "cname_record": {"cname": value}},
                )
            else:
                self._client.record_sets.create_or_update(
                    self._resource_group,
                    self._dns_zone,
                    name,
                    "A",
                    {"ttl": ttl, "arecords": [{"ipv4_address": value}]},
                )

        try:
            await asyncio.to_thread(_upsert)
            logger.info(f"[Azure] DNS record upserted: {name} -> {value} ({record_type_str})")
        except HttpResponseError as e:
            logger.error(f"[Azure] Error upserting DNS record {name}: {e.message}")
            raise

    async def delete_record(self, record_name: str, record_type: RecordType = RecordType.A) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        record_type_str = record_type.value

        def _delete():
            self._client.record_sets.delete(
                self._resource_group, self._dns_zone, name, record_type_str
            )

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"[Azure] DNS record deleted: {name} ({record_type_str})")
        except HttpResponseError as e:
            logger.error(f"[Azure] Error deleting DNS record {name}: {e.message}")
            raise
