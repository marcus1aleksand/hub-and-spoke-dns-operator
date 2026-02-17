# Azure DNS Setup Guide

## Prerequisites

- Azure subscription with a DNS Zone
- AKS cluster with Managed Identity (or Workload Identity) enabled
- Helm 3.x installed

## Step 1: Create Azure DNS Zone

```bash
az group create --name rg-dns --location eastus
az network dns zone create --resource-group rg-dns --name example.com
```

## Step 2: Configure Managed Identity

```bash
# Get the managed identity principal ID
IDENTITY_CLIENT_ID=$(az aks show -g rg-k8s -n my-cluster \
  --query "identityProfile.kubeletidentity.clientId" -o tsv)

# Assign DNS Zone Contributor role
DNS_ZONE_ID=$(az network dns zone show -g rg-dns -n example.com --query id -o tsv)
az role assignment create \
  --assignee $IDENTITY_CLIENT_ID \
  --role "DNS Zone Contributor" \
  --scope $DNS_ZONE_ID
```

## Step 3: Install the Operator

```bash
helm install dns-operator oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
  --set cloudProvider=azure \
  --set azure.subscriptionId="$(az account show --query id -o tsv)" \
  --set azure.dnsZone="example.com" \
  --set azure.dnsResourceGroup="rg-dns" \
  --set azure.managedIdentityClientId="$IDENTITY_CLIENT_ID" \
  --set customIP="203.0.113.1" \
  --set customTTL=300
```

## Step 4: Verify

Create a test ingress and verify the DNS record:

```bash
kubectl create ingress test --rule="test.example.com/*=svc:80"
az network dns record-set a show -g rg-dns -z example.com -n test
```

## Migration from v0.1.x

If upgrading from v0.1.x (Azure-only), the only change is:
- A new `cloudProvider: azure` value is added (defaults to `azure`, so no action needed)
- The `serviceAccount.name` default changed from `azurednsoperator` to `dnsoperator`

Your existing values files will continue to work without changes.
