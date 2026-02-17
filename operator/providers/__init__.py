"""Cloud DNS provider abstraction for hub-and-spoke-dns-operator."""

from operator.providers.base import DNSProvider
from operator.providers.azure import AzureDNSProvider
from operator.providers.gcp import GCPDNSProvider
from operator.providers.aws import AWSDNSProvider

__all__ = ["DNSProvider", "AzureDNSProvider", "GCPDNSProvider", "AWSDNSProvider"]
