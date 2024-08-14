import os
import kopf
import logging
import asyncio
from kubernetes import client, config
from azure.identity import ManagedIdentityCredential
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError
from aiohttp import web

# Configure logging to INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load in-cluster Kubernetes configuration
config.load_incluster_config()

# Initialize Kubernetes API client
api_client = client.NetworkingV1Api()

# Authenticate with Azure using Azure Managed Identity
credential = ManagedIdentityCredential(client_id=os.environ["MANAGED_IDENTITY_CLIENT_ID"])

# Initialize Azure DNS management client
dns_client = DnsManagementClient(credential, os.environ["AZURE_SUBSCRIPTION_ID"])

# Set Azure DNS Zone and Resource Group
azure_dns_zone = os.environ["AZURE_DNS_ZONE"]
azure_dns_resource_group = os.environ["AZURE_DNS_RESOURCE_GROUP"]

# Get the custom IP value from the environment variable
custom_ip_from_values = os.environ.get("CUSTOM_IP", None)


async def create_or_update_dns_record(ingress, action):
    domain = ingress["spec"]["rules"][0]["host"]
    dns_zone = f".{azure_dns_zone}"
    zone_position = domain.find(dns_zone)

    if zone_position != -1:
        domain = domain[:zone_position]

    host_without_dns_zone = domain

    # Check for custom IP annotation and ingressclass
    use_custom_ip = custom_ip_from_values and (
        ingress["metadata"]["annotations"].get("kubernetes.io/ingress.class") != "nginx-internal"
        and ingress["spec"].get("ingressClassName") != "nginx-internal"
    )
    ip = custom_ip_from_values if use_custom_ip else ingress["status"]["loadBalancer"]["ingress"][0]["ip"]

    ttl = int(os.environ.get("CUSTOM_TTL", 300))

    try:
        # Create or update the A record in Azure DNS
        await dns_client.record_sets.create_or_update(
            azure_dns_resource_group,
            azure_dns_zone,
            host_without_dns_zone,
            "A",
            {"ttl": ttl, "arecords": [{"ipv4_address": ip}]},
        )

        logger.info(f"DNS record {'created' if action == 'create' else 'updated'}: {host_without_dns_zone} -> {ip}")

    except HttpResponseError as e:
        logger.error(
            f"Error {'creating' if action == 'create' else 'updating'} DNS record {host_without_dns_zone}: {e.message}"
        )


async def delete_dns_record(ingress):
    domain = ingress["spec"]["rules"][0]["host"]
    dns_zone = f".{azure_dns_zone}"
    zone_position = domain.find(dns_zone)

    if zone_position != -1:
        domain = domain[:zone_position]

    host_without_dns_zone = domain

    try:
        # Delete the A record from Azure Public DNS Zone
        await dns_client.record_sets.delete(azure_dns_resource_group, azure_dns_zone, host_without_dns_zone, "A")

        logger.info(f"DNS record deleted: {host_without_dns_zone}")

    except HttpResponseError as f:
        logger.error(f"Error deleting DNS record {host_without_dns_zone}: {f.message}")


@kopf.on.event("networking.k8s.io/v1", "Ingress")
async def ingress_event_handler(event, **kwargs):
    if event["type"] == "ADDED":
        await create_or_update_dns_record(event["object"], "create")
    elif event["type"] == "MODIFIED":
        await create_or_update_dns_record(event["object"], "update")
    elif event["type"] == "DELETED":
        await delete_dns_record(event["object"])


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.WARNING
    settings.watching.connect_timeout = 60
    settings.watching.server_timeout = 60


async def health_check(request):
    return web.Response(text="OK")


app = web.Application()
app.router.add_get("/healthz", health_check)


async def readiness_check(request):
    return web.Response(text="OK")


app.router.add_get("/readyz", readiness_check)


async def main():
    health_check_server = web._run_app(app, host="127.0.0.1", port=8080)
    kopf_operator = kopf.operator()

    await asyncio.gather(health_check_server, kopf_operator)


if __name__ == "__main__":
    asyncio.run(main())
