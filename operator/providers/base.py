"""Base DNS provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


def looks_like_hostname(value: str) -> bool:
    """Check whether a DNS target value is a hostname rather than an IP address.

    Kept as a module-level helper so that the create and the delete code paths
    can classify a target identically without needing a provider instance.
    """
    if not value:
        return False
    # IPv6 addresses contain colons and are never hostnames.
    if ":" in value:
        return False
    # Check if it's an IP address (IPv4)
    parts = value.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        return False
    # Contains letters -> likely hostname
    return any(c.isalpha() for c in value)


class RecordType(Enum):
    """DNS record types supported by the operator."""

    A = "A"
    CNAME = "CNAME"


@dataclass
class DNSRecord:
    """Represents a DNS record with its properties."""

    name: str
    value: str  # IP address for A records, hostname for CNAME records
    record_type: RecordType
    ttl: int


class DNSProvider(ABC):
    """Abstract base class for cloud DNS providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'azure', 'gcp', 'aws')."""
        ...

    @abstractmethod
    async def create_or_update_record(
        self, record_name: str, value: str, record_type: RecordType = RecordType.A, ttl: int = 300
    ) -> None:
        """Create or update a DNS record (A or CNAME)."""
        ...

    @abstractmethod
    async def delete_record(self, record_name: str, record_type: RecordType = RecordType.A) -> None:
        """Delete a DNS record."""
        ...

    def extract_record_name(self, fqdn: str, dns_zone: str) -> str:
        """Extract the record name by stripping the DNS zone suffix from the FQDN."""
        zone_suffix = f".{dns_zone}"
        if fqdn.endswith(zone_suffix):
            return fqdn[: -len(zone_suffix)]
        return fqdn

    def is_hostname(self, value: str) -> bool:
        """Check if value is a hostname (not an IP address).

        Returns True if the value looks like a hostname (contains letters
        and is not a simple IPv4/IPv6 address).
        """
        return looks_like_hostname(value)
