# Troubleshooting

Common issues and their solutions.

## Operator Not Starting

### Pod in CrashLoopBackOff

```bash
kubectl logs -l app.kubernetes.io/name=hub-and-spoke-dns-operator
```

**Common causes:**

- Missing or invalid cloud provider credentials
- Incorrect `cloudProvider` value
- DNS zone doesn't exist or is inaccessible

### Authentication Errors

=== "Azure"

    ```
    DefaultAzureCredential failed: ManagedIdentityCredential authentication unavailable
    ```

    **Fix:** Ensure Managed Identity is properly assigned and has `DNS Zone Contributor` role on the DNS zone.

    ```bash
    az role assignment list --assignee <managed-identity-client-id> --scope <dns-zone-id>
    ```

=== "GCP"

    ```
    google.auth.exceptions.DefaultCredentialsError
    ```

    **Fix:** Verify the Kubernetes secret exists and contains a valid service account key:

    ```bash
    kubectl get secret gcp-dns-sa-key -o jsonpath='{.data.key\.json}' | base64 -d | jq .
    ```

=== "AWS"

    ```
    botocore.exceptions.NoCredentialsError
    ```

    **Fix:** Verify IRSA is configured correctly:

    ```bash
    kubectl describe sa dnsoperator | grep -i annotation
    ```

## DNS Records Not Created

1. **Check operator logs** for event processing:
    ```bash
    kubectl logs -l app.kubernetes.io/name=hub-and-spoke-dns-operator -f
    ```

2. **Verify the Ingress** has a hostname:
    ```bash
    kubectl get ingress -o wide
    ```

3. **Check permissions** — the operator needs read access to Ingress resources:
    ```bash
    kubectl auth can-i watch ingresses --as=system:serviceaccount:default:dnsoperator
    ```

## DNS Records Not Deleted

Records should be deleted when the corresponding Ingress is removed. If not:

1. Check logs for deletion events
2. Verify the operator was running when the Ingress was deleted
3. Manually clean up orphaned records if necessary

## Metrics Not Available

```bash
# Port-forward to the metrics endpoint
kubectl port-forward deploy/dns-operator 8080:8080
curl http://localhost:8080/metrics
```

If metrics are empty, ensure `metrics.enabled=true` in your Helm values.

## Getting Help

- :material-github: [Open an issue](https://github.com/marcus1aleksand/hub-and-spoke-dns-operator/issues)
- :material-file-document: [Check the docs](index.md)
