# Metrics & Monitoring

The operator exposes Prometheus metrics on port `8080` at `/metrics`.

## Available Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `dns_operator_operations_total` | Counter | `operation`, `status`, `provider` | Total DNS operations performed |
| `dns_operator_operation_duration_seconds` | Histogram | `operation`, `provider` | Duration of DNS operations |
| `dns_operator_errors_total` | Counter | `error_type` | DNS operation errors by type |
| `dns_operator_records_managed` | Gauge | — | Number of currently managed DNS records |
| `dns_operator_info` | Gauge | `zone`, `provider`, `version` | Operator metadata |

## Prometheus ServiceMonitor

Enable the ServiceMonitor to auto-discover metrics with the Prometheus Operator:

```yaml
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
```

## Example PromQL Queries

```promql
# DNS operations per minute by provider
rate(dns_operator_operations_total[5m])

# Error rate
rate(dns_operator_errors_total[5m])

# Average operation latency (p95)
histogram_quantile(0.95, rate(dns_operator_operation_duration_seconds_bucket[5m]))

# Currently managed records
dns_operator_records_managed
```

## Grafana Dashboard

You can create a Grafana dashboard with panels for:

- **Operations rate** — `rate(dns_operator_operations_total[5m])` by operation type
- **Error rate** — `rate(dns_operator_errors_total[5m])` by error type
- **Latency** — p50/p95/p99 of `dns_operator_operation_duration_seconds`
- **Managed records** — `dns_operator_records_managed` gauge
