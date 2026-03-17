"""
GitOps Controllers for hub-and-spoke-dns-operator

This package contains controllers for GitOps-based DNS management.
"""

from .gitops import (
    GitOpsController,
    FluxIntegration,
    DNSRecordSpec,
    DNSRecordStatus,
    RecordType,
    RecordStatus,
)

__all__ = [
    "GitOpsController",
    "FluxIntegration",
    "DNSRecordSpec",
    "DNSRecordStatus",
    "RecordType",
    "RecordStatus",
]
