"""Google Cloud DNS provider implementation."""

import os
import logging
from google.cloud import dns as google_dns
from google.api_core.exceptions import GoogleAPICallError

from providers.base import DNSProvider

logger = logging.getLogger(__name__)


class GCPDNSProvider(DNSProvider):
    """Google Cloud DNS provider using Cloud DNS managed zones."""

    def __init__(self):
        self._project_id = os.environ["GCP_PROJECT_ID"]
        self._managed_zone = os.environ["GCP_MANAGED_ZONE"]
        self._dns_zone = os.environ["GCP_DNS_ZONE"]
        self._client = google_dns.Client(project=self._project_id)
        self._zone = self._client.zone(self._managed_zone, self._dns_zone)

    @property
    def provider_name(self) -> str:
        return "gcp"

    async def create_or_update_record(self, record_name: str, ip_address: str, ttl: int) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        try:
            # Build changes: delete existing + add new
            changes = self._zone.changes()

            # Check for existing record to replace
            existing = self._find_record(fqdn)
            if existing:
                changes.delete_record_set(existing)

            record_set = self._zone.resource_record_set(fqdn, "A", ttl, [ip_address])
            changes.add_record_set(record_set)
            changes.create()

            logger.info(f"[GCP] DNS record upserted: {name} -> {ip_address}")
        except GoogleAPICallError as e:
            logger.error(f"[GCP] Error upserting DNS record {name}: {e.message}")
            raise

    async def delete_record(self, record_name: str) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        try:
            existing = self._find_record(fqdn)
            if existing:
                changes = self._zone.changes()
                changes.delete_record_set(existing)
                changes.create()
                logger.info(f"[GCP] DNS record deleted: {name}")
            else:
                logger.warning(f"[GCP] DNS record not found for deletion: {name}")
        except GoogleAPICallError as e:
            logger.error(f"[GCP] Error deleting DNS record {name}: {e.message}")
            raise

    def _find_record(self, fqdn: str):
        """Find an existing A record by FQDN."""
        for record_set in self._zone.list_resource_record_sets():
            if record_set.name == fqdn and record_set.record_type == "A":
                return record_set
        return None
