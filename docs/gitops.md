# GitOps Integration

The hub-and-spoke-dns-operator supports GitOps-based DNS management through Flux CD. This enables declarative DNS record management using Kubernetes Custom Resources defined in Git repositories.

## Overview

With GitOps integration, you can:
- Define DNS records as Kubernetes Custom Resources (CRs)
- Manage DNS records through Git repositories
- Use Flux CD for automatic reconciliation
- Enable Git-based versioning and rollback for DNS changes

## Quick Start

### 1. Install the Operator with GitOps Support

The DNSRecord CRD is installed by default. To disable it:

```bash
helm install dns-operator . --set gitops.crd.create=false
```

### 2. Create DNS Records

Define DNS records as Custom Resources:

```yaml
# dns-records/production.yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: my-app-example-com
  namespace: dns
  labels:
    app: my-app
    environment: production
spec:
  recordType: A
  value: 1.2.3.4
  ttl: 300
---
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: api-example-com
  namespace: dns
spec:
  recordType: CNAME
  value: my-app.example.com.
  ttl: 300
```

### 3. Apply the Records

```bash
kubectl apply -f dns-records/production.yaml
```

## Flux CD Integration

### 1. Create a Git Repository for DNS Records

Create a repository with your DNS record definitions:

```bash
git init dns-records
cd dns-records
mkdir -p dns-records
# Add your DNSRecord YAML files here
```

### 2. Install Flux CD

If Flux is not already installed:

```bash
flux install
```

### 3. Create a GitRepository Source

```yaml
# flux-gitrepository.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: dns-records
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/<your-org>/dns-records
  ref:
    branch: main
```

### 4. Create a Kustomization

```yaml
# flux-kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: dns-records
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: dns-records
  path: ./dns-records
  prune: true
  validation: client
  targetNamespace: dns
```

### 5. Commit and Push

```bash
git add .
git commit -m "Add DNS records"
git push origin main
```

Flux will automatically reconcile any changes to your DNS records.

## Supported Record Types

| Type | Description | Example |
|------|-------------|---------|
| A | IPv4 address | `example.com -> 1.2.3.4` |
| AAAA | IPv6 address | `ipv6.example.com -> 2001:db8::1` |
| CNAME | Canonical name | `www.example.com -> example.com.` |
| TXT | Text record | `verification.example.com -> "google-site-verification=..."` |
| MX | Mail exchange | `example.com -> 10 mail.example.com.` |

## DNSRecord CRD Specification

```yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: <record-name>  # Unique name for the record
  namespace: dns        # Target namespace
spec:
  recordType: A        # Record type (A, AAAA, CNAME, TXT, MX)
  value: "1.2.3.4"     # Record value (IP address or FQDN)
  ttl: 300             # Time-to-live in seconds (default: 300)
  priority: 10         # Priority for MX records (optional)
  labels:             # Optional labels for organization
    environment: production
    app: my-app
```

## Examples

### A Record (IPv4)

```yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: web-example-com
  namespace: dns
spec:
  recordType: A
  value: 203.0.113.10
  ttl: 600
```

### CNAME Record

```yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: www-example-com
  namespace: dns
spec:
  recordType: CNAME
  value: example.com.
  ttl: 300
```

### MX Record

```yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: mail-example-com
  namespace: dns
spec:
  recordType: MX
  value: mail.example.com.
  ttl: 3600
  priority: 10
```

### TXT Record

```yaml
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: spf-example-com
  namespace: dns
spec:
  recordType: TXT
  value: "v=spf1 include:_spf.example.com ~all"
  ttl: 3600
```

## Best Practices

1. **Use Namespaces**: Create a dedicated namespace for DNS records (e.g., `dns`)

2. **Label Records**: Use labels for organization and filtering:
   ```yaml
   labels:
     environment: production
     app: my-app
     team: platform
   ```

3. **Set Appropriate TTLs**:
   - Low TTL (60-300): For records that change frequently
   - High TTL (3600+): For stable records

4. **Version Control**: Keep all DNSRecord definitions in Git for audit trails

5. **Use Flux**: Let Flux handle reconciliation for automatic healing

## Troubleshooting

### Check DNSRecord Status

```bash
kubectl get dnsrecord -n dns
kubectl describe dnsrecord <name> -n dns
```

### Check Operator Logs

```bash
kubectl logs -n dns-operator -l app=dns-operator
```

### Manual Reconciliation

```bash
# Force reconciliation of a specific record
kubectl annotate dnsrecord <name> -n dns reconcile.weave.works/force="true"
```

## Migration from Ingress-based DNS

If you're migrating from ingress-based DNS management:

1. Export existing DNS records from your ingresses
2. Create corresponding DNSRecord resources
3. Remove the ingress annotations (if any)
4. Flux will reconcile the new records

Example migration:

```yaml
# Before (Ingress annotation)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    dns.example.com/managed: "true"

# After (DNSRecord CR)
apiVersion: dns.example.com/v1alpha1
kind: DNSRecord
metadata:
  name: my-app-example-com
  namespace: dns
spec:
  recordType: A
  value: 1.2.3.4
  ttl: 300
```
