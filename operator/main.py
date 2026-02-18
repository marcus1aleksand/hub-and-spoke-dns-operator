import os
import kopf
import logging
import asyncio
import time
from kubernetes import client, config
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging to INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

dns_operations_total = Counter(
    'dns_operator_operations_total',
    'Total number of DNS operations',
    ['operation', 'status', 'provider']
)

dns_operation_duration_seconds = Histogram(
    'dns_operator_operation_duration_seconds',
    'Duration of DNS operations in seconds',
    ['operation', 'provider'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

dns_errors_total = Counter(
    'dns_operator_errors_total',
    'Total number of DNS operation errors',
    ['operation', 'error_type', 'provider']
)

dns_records_managed = Gauge(
    'dns_operator_records_managed',
    'Number of DNS records currently managed by the operator'
)

operator_info = Gauge(
    'dns_operator_info',
    'Operator information',
    ['dns_zone', 'provider', 'version']
)

# =============================================================================
# CLOUD PROVIDER FACTORY
# =============================================================================


def create_dns_provider():
    """Create the appropriate DNS provider based on CLOUD_PROVIDER env var.

    Supported values: azure (default), gcp, aws
    """
    provider_name = os.environ.get("CLOUD_PROVIDER", "azure").lower()

    if provider_name == "azure":
        from providers.azure import AzureDNSProvider
        return AzureDNSProvider()
    elif provider_name == "gcp":
        from providers.gcp import GCPDNSProvider
        return GCPDNSProvider()
    elif provider_name == "aws":
        from providers.aws import AWSDNSProvider
        return AWSDNSProvider()
    else:
        raise ValueError(f"Unsupported cloud provider: {provider_name}. Use 'azure', 'gcp', or 'aws'.")


# =============================================================================
# KUBERNETES & DNS PROVIDER SETUP
# =============================================================================

config.load_incluster_config()
api_client = client.NetworkingV1Api()

# Initialize cloud DNS provider
dns_provider = create_dns_provider()

# Get DNS zone for metrics (provider-agnostic)
dns_zone = (
    os.environ.get("AZURE_DNS_ZONE")
    or os.environ.get("GCP_DNS_ZONE")
    or os.environ.get("AWS_DNS_ZONE", "unknown")
)

custom_ip_from_values = os.environ.get("CUSTOM_IP", None)

OPERATOR_VERSION = os.environ.get("OPERATOR_VERSION", "0.1.5")
operator_info.labels(
    dns_zone=dns_zone,
    provider=dns_provider.provider_name,
    version=OPERATOR_VERSION
).set(1)

# =============================================================================
# DNS OPERATIONS
# =============================================================================


async def create_or_update_dns_record(ingress, action):
    domain = ingress["spec"]["rules"][0]["host"]
    provider_name = dns_provider.provider_name

    # Check for custom IP annotation and ingressclass
    use_custom_ip = custom_ip_from_values and (
        ingress["metadata"]["annotations"].get("kubernetes.io/ingress.class") != "nginx-internal"
        and ingress["spec"].get("ingressClassName") != "nginx-internal"
    )
    ip = custom_ip_from_values if use_custom_ip else ingress["status"]["loadBalancer"]["ingress"][0]["ip"]
    ttl = int(os.environ.get("CUSTOM_TTL", 300))

    start_time = time.time()
    try:
        await dns_provider.create_or_update_record(domain, ip, ttl)

        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation=action, provider=provider_name).observe(duration)
        dns_operations_total.labels(operation=action, status='success', provider=provider_name).inc()

        if action == 'create':
            dns_records_managed.inc()

        verb = 'created' if action == 'create' else 'updated'
        logger.info(f"[{provider_name}] DNS record {verb}: {domain} -> {ip} ({duration:.3f}s)")

    except Exception as e:
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation=action, provider=provider_name).observe(duration)
        dns_operations_total.labels(operation=action, status='error', provider=provider_name).inc()
        dns_errors_total.labels(operation=action, error_type=type(e).__name__, provider=provider_name).inc()

        action_verb = 'creating' if action == 'create' else 'updating'
        logger.error(f"[{provider_name}] Error {action_verb} DNS record {domain}: {e}")


async def delete_dns_record(ingress):
    domain = ingress["spec"]["rules"][0]["host"]
    provider_name = dns_provider.provider_name

    start_time = time.time()
    try:
        await dns_provider.delete_record(domain)

        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation='delete', provider=provider_name).observe(duration)
        dns_operations_total.labels(operation='delete', status='success', provider=provider_name).inc()
        dns_records_managed.dec()

        logger.info(f"[{provider_name}] DNS record deleted: {domain} ({duration:.3f}s)")

    except Exception as e:
        duration = time.time() - start_time
        dns_operation_duration_seconds.labels(operation='delete', provider=provider_name).observe(duration)
        dns_operations_total.labels(operation='delete', status='error', provider=provider_name).inc()
        dns_errors_total.labels(operation='delete', error_type=type(e).__name__, provider=provider_name).inc()

        logger.error(f"[{provider_name}] Error deleting DNS record {domain}: {e}")


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
        content_type="text/plain",
        charset="utf-8",
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
