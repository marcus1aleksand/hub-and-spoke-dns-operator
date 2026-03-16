# CNAME Record Support

The hub-and-spoke-dns-operator supports both A records and CNAME records.

## Overview

By default, the operator creates A records pointing to the LoadBalancer IP. With CNAME support, you can:

- Point to external hostnames (e.g., services outside your cluster)
- Use CNAME records instead of A records for dynamic DNS

## Usage

### Method 1: Explicit Annotation

Set the `hub-dns-operator.io/record-type` annotation to `CNAME`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    hub-dns-operator.io/record-type: CNAME
    hub-dns-operator.io/target-hostname: my-backend.example.com
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

### Method 2: Auto-Detection

If you specify a hostname as the target (via `hub-dns-operator.io/target-hostname`), the operator automatically detects it's a CNAME:

```yaml
annotations:
  hub-dns-operator.io/target-hostname: external-service.herokuapp.com
```

The operator will create a CNAME record pointing to `external-service.herokuapp.com`.

### Method 3: Using Custom IP with CNAME

You can combine with custom IP annotation:

```yaml
annotations:
  hub-dns-operator.io/record-type: CNAME
  hub-dns-operator.io/target-hostname: my-cdn.cloudfront.net
spec:
  # ... ingress spec
```

## Annotations Reference

| Annotation | Description | Values |
|------------|-------------|--------|
| `hub-dns-operator.io/record-type` | Explicitly set record type | `A` (default), `CNAME` |
| `hub-dns-operator.io/target-hostname` | Explicit target hostname (for CNAME) | Hostname string |
| `hub-dns-operator.io/target-source` | Where to get target value | `loadbalancer` (default), `annotation` |

## Important Notes

### CNAME Exclusivity (RFC 1034)

Per RFC 1034, a CNAME record cannot coexist with other records at the same name. The operator handles this by:

1. When creating a CNAME, first deletes any existing A record at the same name
2. When creating an A record, first deletes any existing CNAME at the same name

This ensures clean record management and avoids DNS resolution issues.

### Auto-Detection Logic

The operator uses the following logic to determine record type:

1. If `hub-dns-operator.io/record-type` is explicitly set → use that value
2. If `hub-dns-operator.io/target-hostname` is set → use CNAME
3. If target value looks like a hostname (contains letters, not IP format) → use CNAME
4. Otherwise → use A record

### TTL

CNAME records use the same TTL setting as A records (default: 300 seconds, configurable via `CUSTOM_TTL` environment variable).
