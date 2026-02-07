import os
import kopf
import logging
import asyncio
import time
from kubernetes import client, config
from azure.identity import ManagedIdentityCredential
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configure logging to INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

# Counter for DNS operations
dns_operations_total = Counter(
    'dns_operator_operations_total',
    'Total number of DNS operations',
    ['operation', 'status']  # operation: create/update/delete, status: success/error
)

# Histogram for DNS operation latency
dns_operation_duration_seconds = Histogram(
    'dns_operator_operation_duration_seconds',
    'Duration of DNS operations in seconds',
    ['operation'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Counter for DNS errors by type
dns_errors_total = Counter(
    'dns_operator_errors_total',
    'Total number of DNS operation errors',
    ['operation', 'error_type']
)

# Gauge for currently managed DNS records
dns_records_managed = Gauge(
    'dns_operator_records_managed',
    'Number of DNS records currently managed by the operator'
)

# Info metric for operator metadata
operator_info = Gauge(
    'dns_operator_info',
    'Operator information',
    ['dns_zone', 'resource_group', 'version']
)

# =============================================================================
# KUBERNETES & AZURE SETUP
# =============================================================================

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

# Set operator info metric
OPERATOR_VERSION = os.environ.get("OPERATOR_VERSION", "0.0.10")
operator_info.labels(
    dns_zone=azure_dns_zone,
    resource_group=azure_dns_resource_group,
    version=OPERATOR_VERSION
).set(1)

# =============================================================================
# DNS OPERATIONS
# =============================================================================

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

    start_time = time.time()
    try:
        # Create or update the A record in Azure DNS Zone
        await dns_client.record_sets.create_or_update(
            azure_dns_resource_group,
            azure_dns_zone,
            host_without_dns_zone,
            "A",
            {"ttl": ttl, "arecords": [{"ipv4_address": ip}]},
        )

        # Record metrics
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation=action).observe(duration)
        dns_operations_total.labels(operation=action, status='success').inc()
        
        if action == 'create':
            dns_records_managed.inc()

        logger.info(f"DNS record {'created' if action == 'create' else 'updated'}: {host_without_dns_zone} -> {ip} (took {duration:.3f}s)")

    except HttpResponseError as e:
        # Record error metrics
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation=action).observe(duration)
        dns_operations_total.labels(operation=action, status='error').inc()
        dns_errors_total.labels(operation=action, error_type='http_response_error').inc()
        
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

    start_time = time.time()
    try:
        # Delete the A record from Azure Public DNS Zone
        await dns_client.record_sets.delete(azure_dns_resource_group, azure_dns_zone, host_without_dns_zone, "A")

        # Record metrics
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation='delete').observe(duration)
        dns_operations_total.labels(operation='delete', status='success').inc()
        dns_records_managed.dec()

        logger.info(f"DNS record deleted: {host_without_dns_zone} (took {duration:.3f}s)")

    except HttpResponseError as f:
        # Record error metrics
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation='delete').observe(duration)
        dns_operations_total.labels(operation='delete', status='error').inc()
        dns_errors_total.labels(operation='delete', error_type='http_response_error').inc()
        
        logger.error(f"Error deleting DNS record {host_without_dns_zone}: {f.message}")


# =============================================================================
# KOPF EVENT HANDLERS
# =============================================================================

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


# =============================================================================
# HTTP ENDPOINTS
# =============================================================================

async def health_check(request):
    return web.Response(text="OK")


async def readiness_check(request):
    return web.Response(text="OK")


async def metrics_handler(request):
    """Prometheus metrics endpoint"""
    return web.Response(
        body=generate_latest(),
        content_type=CONTENT_TYPE_LATEST
    )


app = web.Application()
app.router.add_get("/healthz", health_check)
app.router.add_get("/readyz", readiness_check)
app.router.add_get("/metrics", metrics_handler)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    health_check_server = web._run_app(app, host="0.0.0.0", port=8080)  # nosec
    kopf_operator = kopf.operator()

    await asyncio.gather(health_check_server, kopf_operator)


if __name__ == "__main__":
    asyncio.run(main())
