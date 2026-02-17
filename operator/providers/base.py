"""Base DNS provider interface."""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class DNSProvider(ABC):
    """Abstract base class for cloud DNS providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'azure', 'gcp', 'aws')."""
        ...

    @abstractmethod
    async def create_or_update_record(self, record_name: str, ip_address: str, ttl: int) -> None:
        """Create or update a DNS A record."""
        ...

    @abstractmethod
    async def delete_record(self, record_name: str) -> None:
        """Delete a DNS A record."""
        ...

    def extract_record_name(self, fqdn: str, dns_zone: str) -> str:
        """Extract the record name by stripping the DNS zone suffix from the FQDN."""
        zone_suffix = f".{dns_zone}"
        if fqdn.endswith(zone_suffix):
            return fqdn[: -len(zone_suffix)]
        return fqdn
