# Quick Start

Get the Hub and Spoke DNS Operator running in your cluster in minutes.

## Prerequisites

- **Kubernetes** 1.28+
- **Helm** 3.x
- Cloud provider credentials configured (see provider-specific guides)

## Installation

### Step 1: Choose Your Cloud Provider

=== "Azure DNS"

    ```bash
    helm install dns-operator \
      oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
      --set cloudProvider=azure \
      --set azure.subscriptionId="your-subscription-id" \
      --set azure.dnsZone="example.com" \
      --set azure.dnsResourceGroup="rg-dns" \
      --set azure.managedIdentityClientId="your-mi-client-id" \
      --set customIP="203.0.113.1"
    ```

    :material-arrow-right: [Full Azure setup guide](azure-setup.md)

=== "Google Cloud DNS"

    ```bash
    helm install dns-operator \
      oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
      --set cloudProvider=gcp \
      --set gcp.projectId="my-gcp-project" \
      --set gcp.managedZone="my-dns-zone" \
      --set gcp.dnsZone="example.com" \
      --set gcp.serviceAccountKey="gcp-dns-sa-key" \
      --set customIP="203.0.113.1"
    ```

    :material-arrow-right: [Full GCP setup guide](gcp-setup.md)

=== "AWS Route53"

    ```bash
    helm install dns-operator \
      oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
      --set cloudProvider=aws \
      --set aws.hostedZoneId="Z1234567890ABC" \
      --set aws.dnsZone="example.com" \
      --set aws.region="us-east-1" \
      --set customIP="203.0.113.1"
    ```

    :material-arrow-right: [Full AWS setup guide](aws-setup.md)

### Step 2: Verify the Installation

```bash
# Check the operator is running
kubectl get pods -l app.kubernetes.io/name=hub-and-spoke-dns-operator

# Check logs
kubectl logs -l app.kubernetes.io/name=hub-and-spoke-dns-operator -f
```

### Step 3: Test DNS Record Creation

```bash
# Create a test ingress
kubectl create ingress test-app \
  --rule="test.example.com/*=my-service:80"

# Verify the DNS record was created (Azure example)
az network dns record-set a show -g rg-dns -z example.com -n test
```

### Step 4: Clean Up Test

```bash
kubectl delete ingress test-app
# The DNS record will be automatically deleted
```

## What's Next?

- :material-sitemap: [Understand the architecture](architecture.md)
- :material-cog: [Full configuration reference](configuration.md)
- :material-chart-line: [Set up monitoring](metrics.md)
- :material-wrench: [Troubleshooting guide](troubleshooting.md)
