# Google Cloud DNS Setup Guide

## Prerequisites

- GCP project with Cloud DNS API enabled
- GKE cluster (or any K8s cluster with GCP access)
- Helm 3.x installed

## Step 1: Enable Cloud DNS API

```bash
gcloud services enable dns.googleapis.com
```

## Step 2: Create a Managed Zone

```bash
gcloud dns managed-zones create my-dns-zone \
  --dns-name="example.com." \
  --description="Production DNS zone"
```

## Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create dns-operator \
  --display-name="Hub and Spoke DNS Operator"

# Grant DNS admin role
gcloud projects add-iam-policy-binding my-gcp-project \
  --member="serviceAccount:dns-operator@my-gcp-project.iam.gserviceaccount.com" \
  --role="roles/dns.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=dns-operator@my-gcp-project.iam.gserviceaccount.com

# Store as Kubernetes secret
kubectl create secret generic gcp-dns-sa-key --from-file=key.json=key.json
```

## Step 4: Install the Operator

```bash
helm install dns-operator oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
  --set cloudProvider=gcp \
  --set gcp.projectId="my-gcp-project" \
  --set gcp.managedZone="my-dns-zone" \
  --set gcp.dnsZone="example.com" \
  --set gcp.serviceAccountKey="gcp-dns-sa-key" \
  --set customIP="203.0.113.1"
```

## Step 5: Verify

```bash
kubectl create ingress test --rule="test.example.com/*=svc:80"
gcloud dns record-sets list --zone=my-dns-zone --filter="name=test.example.com."
```

## Using Workload Identity (Recommended for GKE)

Instead of a service account key, use GKE Workload Identity:

```bash
# Bind K8s SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  dns-operator@my-gcp-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-gcp-project.svc.id.goog[default/dnsoperator]"

# Annotate the K8s service account (via Helm values or kubectl)
kubectl annotate serviceaccount dnsoperator \
  iam.gke.io/gcp-service-account=dns-operator@my-gcp-project.iam.gserviceaccount.com
```

When using Workload Identity, omit the `gcp.serviceAccountKey` value.
