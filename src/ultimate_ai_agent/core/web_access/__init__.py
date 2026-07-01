"""Policy-controlled WebAccessGateway package."""

from .contracts import (
    SourceMetadata,
    WebAccessAdapterKind,
    WebAccessAuditRecord,
    WebAccessAuthorityMode,
    WebAccessEvidenceBundle,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebAccessResult,
    WebAccessRiskClass,
)
from .gateway import WebAccessGateway, create_default_web_access_gateway
from .policy import WebAccessPolicy

__all__ = [
    "SourceMetadata",
    "WebAccessAdapterKind",
    "WebAccessAuditRecord",
    "WebAccessAuthorityMode",
    "WebAccessEvidenceBundle",
    "WebAccessGateway",
    "WebAccessNetworkLane",
    "WebAccessPolicy",
    "WebAccessPolicyDecision",
    "WebAccessPolicyStatus",
    "WebAccessRequest",
    "WebAccessRequestKind",
    "WebAccessResult",
    "WebAccessRiskClass",
    "create_default_web_access_gateway",
]
