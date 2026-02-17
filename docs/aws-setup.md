# AWS Route53 Setup Guide

## Prerequisites

- AWS account with Route53 access
- EKS cluster (or any K8s cluster with AWS access)
- Helm 3.x installed

## Step 1: Create a Hosted Zone

```bash
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "$(date +%s)"

# Note the hosted zone ID from output (e.g., Z1234567890ABC)
```

## Step 2: Create IAM Policy

```bash
cat > dns-operator-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:ChangeResourceRecordSets",
        "route53:ListResourceRecordSets"
      ],
      "Resource": "arn:aws:route53:::hostedzone/Z1234567890ABC"
    },
    {
      "Effect": "Allow",
      "Action": "route53:ListHostedZones",
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name DNSOperatorPolicy \
  --policy-document file://dns-operator-policy.json
```

## Step 3: Configure Authentication

### Option A: IRSA (Recommended for EKS)

```bash
eksctl create iamserviceaccount \
  --name dnsoperator \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::123456789012:policy/DNSOperatorPolicy \
  --approve --override-existing-serviceaccounts
```

Then install with `serviceAccount.create=false`:

```bash
helm install dns-operator oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
  --set cloudProvider=aws \
  --set aws.hostedZoneId="Z1234567890ABC" \
  --set aws.dnsZone="example.com" \
  --set aws.region="us-east-1" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=dnsoperator \
  --set customIP="203.0.113.1"
```

### Option B: Access Keys (Development Only)

```bash
helm install dns-operator oci://ghcr.io/marcus1aleksand/helm-charts/hub-and-spoke-dns-operator \
  --set cloudProvider=aws \
  --set aws.hostedZoneId="Z1234567890ABC" \
  --set aws.dnsZone="example.com" \
  --set aws.region="us-east-1" \
  --set aws.accessKeyId="AKIA..." \
  --set aws.secretAccessKey="..." \
  --set customIP="203.0.113.1"
```

> ⚠️ **Warning:** Never use access keys in production. Use IRSA or EC2 instance roles instead.

## Step 4: Verify

```bash
kubectl create ingress test --rule="test.example.com/*=svc:80"
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --query "ResourceRecordSets[?Name=='test.example.com.']"
```
