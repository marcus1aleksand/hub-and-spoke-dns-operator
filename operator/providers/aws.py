"""AWS Route53 DNS provider implementation."""

import asyncio
import os
import logging
import boto3
from botocore.exceptions import ClientError

from providers.base import DNSProvider, RecordType

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

    async def create_or_update_record(
        self, record_name: str, value: str, record_type: RecordType = RecordType.A, ttl: int = 300
    ) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        record_type_str = record_type.value

        def _upsert():
            self._client.change_resource_record_sets(
                HostedZoneId=self._hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": fqdn,
                                "Type": record_type_str,
                                "TTL": ttl,
                                "ResourceRecords": [{"Value": value}],
                            },
                        }
                    ]
                },
            )

        try:
            await asyncio.to_thread(_upsert)
            logger.info(f"[AWS] DNS record upserted: {name} -> {value} ({record_type_str})")
        except ClientError as e:
            logger.error(f"[AWS] Error upserting DNS record {name}: {e}")
            raise

    async def delete_record(self, record_name: str, record_type: RecordType = RecordType.A) -> None:
        name = self.extract_record_name(record_name, self._dns_zone)
        fqdn = f"{name}.{self._dns_zone}."
        record_type_str = record_type.value

        def _delete():
            response = self._client.list_resource_record_sets(
                HostedZoneId=self._hosted_zone_id,
                StartRecordName=fqdn,
                StartRecordType=record_type_str,
                MaxItems="1",
            )
            record_sets = response.get("ResourceRecordSets", [])
            matching = [r for r in record_sets if r["Name"] == fqdn and r["Type"] == record_type_str]

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

        try:
            await asyncio.to_thread(_delete)
        except ClientError as e:
            logger.error(f"[AWS] Error deleting DNS record {name}: {e}")
            raise
