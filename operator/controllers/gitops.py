"""
GitOps Controller for hub-and-spoke-dns-operator

This module provides GitOps/Flux-compatible DNS record management.
DNS records can be defined as Kubernetes Custom Resources and managed
through Git repositories using Flux CD.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RecordType(Enum):
    """DNS record types supported by the operator"""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"
    MX = "MX"


class RecordStatus(Enum):
    """Status of a DNS record"""
    PENDING = "pending"
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ERROR = "error"


@dataclass
class DNSRecordSpec:
    """Specification for a DNS record"""
    name: str
    record_type: RecordType
    value: str
    ttl: int = 300
    priority: Optional[int] = None  # For MX records
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DNSRecordStatus:
    """Status of a DNS record resource"""
    observed_generation: int = 0
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: Optional[str] = None
    message: Optional[str] = None


class GitOpsController:
    """
    GitOps Controller for DNS Records.
    
    This controller watches DNSRecord custom resources and reconciles them
    with the actual DNS provider. It works seamlessly with Flux CD,
    enabling GitOps-based DNS management.
    
    Example DNSRecord resource:
    ```yaml
    apiVersion: dns.example.com/v1alpha1
    kind: DNSRecord
    metadata:
      name: my-app.example.com
      namespace: dns
    spec:
      recordType: A
      value: 1.2.3.4
      ttl: 300
      labels:
        environment: production
        app: my-app
    ```
    """
    
    def __init__(self, dns_provider):
        self.dns_provider = dns_provider
        self.provider_name = dns_provider.provider_name
        self._initialized = True
        logger.info(f"[GitOps] Controller initialized for provider: {self.provider_name}")
    
    async def reconcile(self, record_spec: DNSRecordSpec, dry_run: bool = False) -> DNSRecordStatus:
        """
        Reconcile a DNS record to match the desired state.
        
        Args:
            record_spec: The desired DNS record specification
            dry_run: If True, don't actually make changes
            
        Returns:
            DNSRecordStatus with the current state
        """
        try:
            if dry_run:
                logger.info(f"[GitOps] Dry-run: would {record_spec.record_type} record {record_spec.name} -> {record_spec.value}")
                return DNSRecordStatus(
                    observed_generation=1,
                    conditions=[{
                        "type": "DryRun",
                        "status": "True",
                        "message": "Dry-run mode - no changes made"
                    }],
                    message="Dry-run successful"
                )
            
            # Apply the DNS record
            await self.dns_provider.create_or_update_record(
                name=record_spec.name,
                ip=record_spec.value,
                ttl=record_spec.ttl,
                record_type=record_spec.record_type.value
            )
            
            logger.info(f"[GitOps] Reconciled {record_spec.record_type} record: {record_spec.name} -> {record_spec.value}")
            
            return DNSRecordStatus(
                observed_generation=1,
                conditions=[{
                    "type": "Ready",
                    "status": "True",
                    "message": f"Record {record_spec.name} successfully reconciled"
                }],
                message="Reconciliation successful"
            )
            
        except Exception as e:
            logger.error(f"[GitOps] Error reconciling record {record_spec.name}: {e}")
            return DNSRecordStatus(
                observed_generation=1,
                conditions=[{
                    "type": "Ready",
                    "status": "False",
                    "message": str(e)
                }],
                message=f"Error: {str(e)}"
            )
    
    async def delete(self, record_spec: DNSRecordSpec, dry_run: bool = False) -> DNSRecordStatus:
        """
        Delete a DNS record.
        
        Args:
            record_spec: The DNS record to delete
            dry_run: If True, don't actually delete
            
        Returns:
            DNSRecordStatus with the current state
        """
        try:
            if dry_run:
                logger.info(f"[GitOps] Dry-run: would delete record {record_spec.name}")
                return DNSRecordStatus(
                    observed_generation=1,
                    conditions=[{
                        "type": "DryRun",
                        "status": "True",
                        "message": "Dry-run mode - no changes made"
                    }],
                    message="Dry-run successful"
                )
            
            await self.dns_provider.delete_record(record_spec.name)
            
            logger.info(f"[GitOps] Deleted record: {record_spec.name}")
            
            return DNSRecordStatus(
                observed_generation=1,
                conditions=[{
                    "type": "Ready",
                    "status": "True",
                    "message": f"Record {record_spec.name} successfully deleted"
                }],
                message="Deletion successful"
            )
            
        except Exception as e:
            logger.error(f"[GitOps] Error deleting record {record_spec.name}: {e}")
            return DNSRecordStatus(
                observed_generation=1,
                conditions=[{
                    "type": "Ready",
                    "status": "False",
                    "message": str(e)
                }],
                message=f"Error: {str(e)}"
            )
    
    async def validate_record(self, record_spec: DNSRecordSpec) -> tuple[bool, Optional[str]]:
        """
        Validate a DNS record specification.
        
        Args:
            record_spec: The record to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate name
        if not record_spec.name or len(record_spec.name) > 253:
            return False, "Invalid DNS name: must be 1-253 characters"
        
        # Validate TTL
        if record_spec.ttl < 0 or record_spec.ttl > 2147483647:
            return False, "Invalid TTL: must be 0-2147483647"
        
        # Validate value based on record type
        if record_spec.record_type == RecordType.A:
            parts = record_spec.value.split('.')
            if len(parts) != 4:
                return False, "Invalid A record value: must be IPv4 address"
            try:
                for part in parts:
                    if not 0 <= int(part) <= 255:
                        return False, "Invalid A record value: octets must be 0-255"
            except ValueError:
                return False, "Invalid A record value: must be numeric IPv4"
        
        elif record_spec.record_type == RecordType.AAAA:
            # Basic IPv6 validation
            if ':' not in record_spec.value:
                return False, "Invalid AAAA record value: must be IPv6 address"
        
        elif record_spec.record_type == RecordType.CNAME:
            if not record_spec.value.endswith('.'):
                return False, "CNAME value should end with '.' for FQDN"
        
        elif record_spec.record_type == RecordType.MX:
            if record_spec.priority is None:
                return False, "MX records require a priority"
        
        return True, None


class FluxIntegration:
    """
    Flux CD Integration for GitOps DNS management.
    
    This class provides utilities for integrating with Flux CD's
    GitOps toolkit, enabling automatic reconciliation of DNS records
    from Git repositories.
    """
    
    @staticmethod
    def generate_flux_source() -> str:
        """
        Generate a Flux GitRepository source for DNS records.
        
        Returns:
            YAML manifest for Flux GitRepository
        """
        return """apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: dns-records
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/<org>/dns-records
  ref:
    branch: main
"""
    
    @staticmethod
    def generate_flux_kustomization() -> str:
        """
        Generate a Flux Kustomization for DNS records.
        
        Returns:
            YAML manifest for Flux Kustomization
        """
        return """apiVersion: kustomize.toolkit.fluxcd.io/v1
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
"""
    
    @staticmethod
    def generate_dnsrecord_crd() -> str:
        """
        Generate the DNSRecord CRD manifest.
        
        Returns:
            YAML manifest for DNSRecord CRD
        """
        return """apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  annotations:
    controller-gen.kubebuilder.io/version: v0.14.0
  name: dnsrecords.dns.example.com
spec:
  group: dns.example.com
  names:
    kind: DNSRecord
    listKind: DNSRecordList
    plural: dnsrecords
    singular: dnsrecord
  scope: Namespaced
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required:
                - recordType
                - value
              properties:
                recordType:
                  type: string
                  enum: [A, AAAA, CNAME, TXT, MX]
                value:
                  type: string
                ttl:
                  type: integer
                  default: 300
                priority:
                  type: integer
                labels:
                  type: object
                  additionalProperties:
                    type: string
            status:
              type: object
              properties:
                conditions:
                  type: array
                  items:
                    type: object
                lastUpdated:
                  type: string
                message:
                  type: string
"""

    @staticmethod
    def generate_example_dnsrecord() -> str:
        """
        Generate an example DNSRecord manifest.
        
        Returns:
            YAML manifest for example DNSRecord
        """
        return """apiVersion: dns.example.com/v1alpha1
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
  labels:
    environment: production
    app: my-app
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
"""
