# Hub and Spoke DNS Operator

[![Downloads](https://img.shields.io/badge/Downloads-2k+-blue?style=for-the-badge&logo=github&label=Downloads)](https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/pkgs/container/hub-and-spoke-dns-operator)

Welcome to the documentation for the **Hub and Spoke DNS Operator** — a multi-cloud Kubernetes operator that automatically manages DNS records for Ingress resources.

## Documentation

- **[Architecture](architecture.md)** — How the operator works, design patterns, and event flow
- **[Azure Setup](azure-setup.md)** — Deploy with Azure DNS Zones
- **[GCP Setup](gcp-setup.md)** — Deploy with Google Cloud DNS
- **[AWS Setup](aws-setup.md)** — Deploy with AWS Route53

## Quick Links

- [GitHub Repository](https://github.com/marcus1aleksand/hub-and-spoke-dns-operator)
- [Helm Chart](https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/tree/main/charts)
- [Container Image](https://ghcr.io/marcus1aleksand/hub-and-spoke-dns-operator)

## Supported Providers

| Provider | Service | Auth Method |
|----------|---------|-------------|
| **Azure** | Azure DNS Zones | Managed Identity / Workload Identity |
| **GCP** | Cloud DNS | Service Account / Workload Identity |
| **AWS** | Route53 | IRSA / IAM Roles |
