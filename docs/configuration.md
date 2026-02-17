# Configuration Reference

Complete reference for all Helm chart values.

## Common Values

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cloudProvider` | string | `azure` | Cloud provider: `azure`, `gcp`, or `aws` |
| `customIP` | string | `""` | Override IP for DNS records (e.g., firewall public IP) |
| `customTTL` | int | `300` | TTL for DNS records in seconds |
| `replicaCount` | int | `1` | Number of operator replicas |
| `image.repository` | string | `ghcr.io/marcus1aleksand/hub-and-spoke-dns-operator` | Container image |
| `image.pullPolicy` | string | `Always` | Image pull policy |
| `imageCredentials` | string | `""` | Image pull secret |
| `fullnameOverride` | string | `""` | Override the full resource name |
| `nameOverride` | string | `""` | Override the chart name |
| `metrics.enabled` | bool | `true` | Enable Prometheus metrics endpoint |
| `metrics.serviceMonitor.enabled` | bool | `false` | Create ServiceMonitor for Prometheus Operator |

## Service Account

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `serviceAccount.create` | bool | `true` | Create a service account |
| `serviceAccount.name` | string | `dnsoperator` | Service account name |
| `deployment.automountServiceAccountToken` | bool | `false` | Automount SA token |

## Azure DNS Values

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `azure.subscriptionId` | string | `""` | Azure subscription ID |
| `azure.dnsZone` | string | `""` | DNS zone name (e.g., `example.com`) |
| `azure.dnsResourceGroup` | string | `""` | Resource group containing the DNS zone |
| `azure.managedIdentityClientId` | string | `""` | Managed Identity client ID |

## Google Cloud DNS Values

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gcp.projectId` | string | `""` | GCP project ID |
| `gcp.managedZone` | string | `""` | Cloud DNS managed zone name |
| `gcp.dnsZone` | string | `""` | DNS zone domain (e.g., `example.com`) |
| `gcp.serviceAccountKey` | string | `""` | K8s secret name containing GCP SA key |

## AWS Route53 Values

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `aws.hostedZoneId` | string | `""` | Route53 hosted zone ID |
| `aws.dnsZone` | string | `""` | DNS zone domain (e.g., `example.com`) |
| `aws.region` | string | `""` | AWS region |
| `aws.accessKeyId` | string | `""` | AWS access key (dev only) |
| `aws.secretAccessKey` | string | `""` | AWS secret key (dev only) |

!!! warning "Production Security"
    Never use `aws.accessKeyId` / `aws.secretAccessKey` in production. Use IRSA (IAM Roles for Service Accounts) instead.

## Example values.yaml

```yaml
cloudProvider: azure

customIP: "203.0.113.1"
customTTL: 300
replicaCount: 1

azure:
  subscriptionId: "00000000-0000-0000-0000-000000000000"
  dnsZone: "example.com"
  dnsResourceGroup: "rg-dns"
  managedIdentityClientId: "00000000-0000-0000-0000-000000000000"

metrics:
  enabled: true
  serviceMonitor:
    enabled: true

serviceAccount:
  create: true
  name: "dnsoperator"
```
