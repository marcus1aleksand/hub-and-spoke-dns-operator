"""AWS Route53 DNS provider implementation."""

import os
import logging
import boto3
from botocore.exceptions import ClientError

from providers.base import DNSProvider

logger = logging.getLogger(__name__)


class AWSDNSProvider(DNSProvider):
    """AWS Route53 DNS provider."""

    def __init__(self):
        self._hosted_zone_id = os.environ["AWS_HOSTED_ZONE_ID"]
        self._dns_zone = os.environ["AWS_DNS_ZONE"]
        self._region = os.environ.get("AWS_REGION", "us-east-1")
        self._client = boto3.client("route53", region_name=self._region)

    @property
    def provider_name(self) -> str:
        return "aws"

    async def create_or_update_record(self, record_name: str, ip_address: str, ttl: int) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        try:
            self._client.change_resource_record_sets(
                HostedZoneId=self._hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": fqdn,
                                "Type": "A",
                                "TTL": ttl,
                                "ResourceRecords": [{"Value": ip_address}],
                            },
                        }
                    ]
                },
            )
            logger.info(f"[AWS] DNS record upserted: {name} -> {ip_address}")
        except ClientError as e:
            logger.error(f"[AWS] Error upserting DNS record {name}: {e}")
            raise

    async def delete_record(self, record_name: str) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        try:
            # Need to get current record to delete it
            response = self._client.list_resource_record_sets(
                HostedZoneId=self._hosted_zone_id,
                StartRecordName=fqdn,
                StartRecordType="A",
                MaxItems="1",
            )
            record_sets = response.get("ResourceRecordSets", [])
            matching = [r for r in record_sets if r["Name"] == fqdn and r["Type"] == "A"]

            if not matching:
                logger.warning(f"[AWS] DNS record not found for deletion: {name}")
                return

            self._client.change_resource_record_sets(
                HostedZoneId=self._hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "DELETE",
                            "ResourceRecordSet": matching[0],
                        }
                    ]
                },
            )
            logger.info(f"[AWS] DNS record deleted: {name}")
        except ClientError as e:
            logger.error(f"[AWS] Error deleting DNS record {name}: {e}")
            raise
