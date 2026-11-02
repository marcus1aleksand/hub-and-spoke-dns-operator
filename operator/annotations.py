"""Annotation parsing utilities for DNS record management."""

import os
from providers.base import RecordType, looks_like_hostname

# Default target source - can be "loadbalancer" (default) or "annotation"
DEFAULT_TARGET_SOURCE = os.environ.get("DEFAULT_TARGET_SOURCE", "loadbalancer")

# Annotation keys
ANNOTATION_RECORD_TYPE = "hub-dns-operator.io/record-type"
ANNOTATION_TARGET_HOSTNAME = "hub-dns-operator.io/target-hostname"
ANNOTATION_TARGET_SOURCE = "hub-dns-operator.io/target-source"


def get_record_type(annotations: dict) -> RecordType:
    """Determine record type from annotations or auto-detect.

    Priority:
    1. Explicit annotation: hub-dns-operator.io/record-type: CNAME
    2. Default to A record (auto-detect happens later based on target value)
    """
    explicit = annotations.get(ANNOTATION_RECORD_TYPE, "").upper()
    if explicit == "CNAME":
        return RecordType.CNAME
    # Default to A record (auto-detect happens based on target value)
    return RecordType.A


def resolve_record_type(annotations: dict, target_value: str) -> RecordType:
    """Resolve the effective record type for an ingress.

    An explicit "hub-dns-operator.io/record-type: CNAME" annotation always
    wins. Otherwise the type is auto-detected from the target value: a
    hostname target can only be produced by the target-hostname annotation
    (the load balancer path always yields an IP address), so a hostname
    target means the record has to be a CNAME.

    The create and the delete code path both use this helper so that a record
    is always removed with the same type it was created with. Without it a
    CNAME created from the target-hostname annotation was deleted as an A
    record, which left the CNAME behind in the DNS zone.
    """
    if get_record_type(annotations) == RecordType.CNAME:
        return RecordType.CNAME
    if looks_like_hostname(target_value):
        return RecordType.CNAME
    return RecordType.A


def get_target_value(ingress: dict, annotations: dict) -> str:
    """Get the target value for the DNS record.

    Can come from:
    1. hub-dns-operator.io/target-hostname annotation (for CNAME)
    2. status.loadBalancer.ingress[0].ip (default)
    """
    # Check for explicit hostname annotation first
    target_hostname = annotations.get(ANNOTATION_TARGET_HOSTNAME)
    if target_hostname:
        return target_hostname

    # Default: use loadBalancer IP
    if "status" in ingress and "loadBalancer" in ingress["status"]:
        if "ingress" in ingress["status"]["loadBalancer"]:
            ingress_list = ingress["status"]["loadBalancer"]["ingress"]
            if ingress_list and "ip" in ingress_list[0]:
                return ingress_list[0]["ip"]

    raise ValueError("No target value found for DNS record")
