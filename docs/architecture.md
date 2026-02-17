# Architecture

## Overview

The Hub and Spoke DNS Operator is a Kubernetes operator built with [kopf](https://kopf.readthedocs.io/) that automates DNS record management for Ingress resources across multi-cloud environments.

## Hub-and-Spoke Network Model

In enterprise environments, Kubernetes clusters often run in **spoke networks** connected to a central **hub network** that provides shared services like firewalls, VPN gateways, and DNS.

```mermaid
graph TB
    subgraph Hub["Hub Network"]
        FW["Firewall<br/>Public IP: 203.0.113.1"]
        DNS["DNS Zone<br/>example.com"]
    end

    subgraph Spoke1["Spoke 1"]
        K8S1["K8s Cluster"]
        OP1["DNS Operator"]
        ING1["Ingress<br/>app1.example.com"]
    end

    subgraph Spoke2["Spoke 2"]
        K8S2["K8s Cluster"]
        OP2["DNS Operator"]
        ING2["Ingress<br/>app2.example.com"]
    end

    FW -->|NAT| K8S1
    FW -->|NAT| K8S2
    OP1 -->|"A record: app1 → 203.0.113.1"| DNS
    OP2 -->|"A record: app2 → 203.0.113.1"| DNS
    K8S1 --> ING1
    K8S2 --> ING2
    OP1 -.->|watches| ING1
    OP2 -.->|watches| ING2
```

## Component Design

### Provider Abstraction

The operator uses a **provider pattern** to support multiple cloud DNS services through a unified interface:

```
DNSProvider (Abstract Base)
├── AzureDNSProvider  — Azure DNS Zones via azure-mgmt-dns
├── GCPDNSProvider    — Google Cloud DNS via google-cloud-dns
└── AWSDNSProvider    — AWS Route53 via boto3
```

The `CLOUD_PROVIDER` environment variable selects which provider is instantiated at startup. All providers implement the same `create_or_update_record()` and `delete_record()` interface.

### Event Flow

```mermaid
sequenceDiagram
    participant K8s as Kubernetes API
    participant Op as DNS Operator
    participant DNS as Cloud DNS Provider

    K8s->>Op: Ingress ADDED event
    Op->>Op: Extract host, resolve IP
    Op->>DNS: create_or_update_record(host, ip, ttl)
    DNS-->>Op: Success
    Op->>Op: Increment Prometheus metrics

    K8s->>Op: Ingress MODIFIED event
    Op->>DNS: create_or_update_record(host, ip, ttl)

    K8s->>Op: Ingress DELETED event
    Op->>DNS: delete_record(host)
```

### Custom IP Logic

When `customIP` is set, the operator uses it instead of the Ingress's load balancer IP — **except** when the Ingress uses `nginx-internal` ingress class (indicating internal-only traffic that shouldn't get the public firewall IP).

## Observability

The operator exposes Prometheus metrics on `:8080/metrics` with dimensions for `operation`, `status`, and `provider`, enabling per-cloud-provider monitoring dashboards.
