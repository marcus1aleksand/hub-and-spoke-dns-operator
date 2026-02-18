"""Cloud DNS provider abstraction for hub-and-spoke-dns-operator."""

from providers.base import DNSProvider
from providers.azure import AzureDNSProvider
from providers.gcp import GCPDNSProvider
from providers.aws import AWSDNSProvider

__all__ = ["DNSProvider", "AzureDNSProvider", "GCPDNSProvider", "AWSDNSProvider"]
