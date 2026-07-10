"""Contracts for the policy-controlled hybrid WebAccessGateway.

This module is intentionally side-effect free. It defines the boundary that all
agent-facing public-web access must use. Concrete network/browser providers live
behind adapters and are not imported here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Protocol
from uuid import uuid4


class WebAccessAuthorityMode(str, Enum):
    """Authority mode for a web-access request."""

    OFF = "off"
    READ_ONLY = "read_only"
    BROWSER_OBSERVE_ONLY = "browser_observe_only"
    BROWSER_ACTION_DRY_RUN = "browser_action_dry_run"
    SCOPED_BROWSER_ACTION_BLOCKED = "scoped_browser_action_blocked"


class WebAccessRequestKind(str, Enum):
    """Logical operations at the web gateway boundary."""

    GOVERNED_WEB_EVIDENCE = "governed_web_evidence"
    READ_ONLY_FETCH = "read_only_fetch"
    SEARCH = "search"
    EXTRACT_MARKDOWN = "extract_markdown"
    EXTRACT_SCHEMA = "extract_schema"
    BROWSER_OBSERVE = "browser_observe"
    BROWSER_ACTION_DRY_RUN = "browser_action_dry_run"
    BROWSER_CLICK = "browser_click"
    FORM_FILL = "form_fill"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    AUTHENTICATED_SESSION = "authenticated_session"


class WebAccessAdapterKind(str, Enum):
    """Provider/runtime categories behind the gateway."""

    NONE = "none"
    LOCAL_FETCH = "local_fetch"
    LOCAL_BROWSER_OBSERVE = "local_browser_observe"
    LOCAL_BROWSER_ACTION_DRY_RUN = "local_browser_action_dry_run"
    GOVERNED_WEB_EVIDENCE = "governed_web_evidence"
    SEARCH_API = "search_api"
    FIRECRAWL = "firecrawl"
    PLAYWRIGHT_OBSERVE = "playwright_observe"
    BROWSERBASE_OBSERVE = "browserbase_observe"


class WebAccessRiskClass(str, Enum):
    """Coarse security classification for the requested operation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WebAccessPolicyStatus(str, Enum):
    """Policy decision status."""

    ALLOWED = "allowed"
    DENIED = "denied"
    APPROVAL_REQUIRED = "approval_required"
    NOT_IMPLEMENTED = "not_implemented"


class WebAccessNetworkLane(str, Enum):
    """Network lanes used to avoid over-broad direct-HTTP migration."""

    AGENT_PUBLIC_WEB = "agent_public_web"
    GOVERNED_WEB_EVIDENCE = "governed_web_evidence"
    LOCAL_MODEL_LOOPBACK = "local_model_loopback"
    MODEL_ACQUISITION = "model_acquisition"
    TOOL_RUNTIME_READ_ONLY_FETCH = "tool_runtime_read_only_fetch"
    BROWSER_OBSERVE_ONLY = "browser_observe_only"
    BROWSER_ACTION_DRY_RUN = "browser_action_dry_run"


@dataclass(frozen=True)
class SourceMetadata:
    """Source metadata that travels with every web result."""

    url: str | None = None
    final_url: str | None = None
    host: str | None = None
    source_type: str = "web"
    authority: str | None = None
    freshness: str | None = None
    robots_terms_posture: str = "unknown"
    allowed_methods: tuple[str, ...] = ("GET",)
    fetched_at: datetime | None = None
    content_hash: str | None = None
    content_untrusted: bool = True
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WebAccessPolicyDecision:
    """Decision produced before any adapter is invoked."""

    status: WebAccessPolicyStatus
    risk_class: WebAccessRiskClass
    reasons: tuple[str, ...] = ()
    allowed_methods: tuple[str, ...] = ()
    requires_approval: bool = False

    @property
    def allowed(self) -> bool:
        return self.status == WebAccessPolicyStatus.ALLOWED


@dataclass(frozen=True)
class WebAccessAuditRecord:
    """Normalized audit shape for every gateway request."""

    request_id: str
    timestamp: datetime
    request_kind: WebAccessRequestKind
    url: str | None
    adapter_kind: WebAccessAdapterKind
    network_lane: WebAccessNetworkLane
    authority_mode: WebAccessAuthorityMode
    risk_class: WebAccessRiskClass
    policy_status: WebAccessPolicyStatus
    policy_reasons: tuple[str, ...] = ()
    source_metadata: tuple[SourceMetadata, ...] = ()
    actor: str | None = None
    session_id: str | None = None
    redacted_preview: str | None = None
    content_untrusted: bool = True


@dataclass(frozen=True)
class WebAccessEvidenceBundle:
    """Quarantined adapter payload.

    Web evidence is data only. Keeping the provider payload behind this wrapper
    prevents downstream code from treating adapter keys such as "instructions",
    "tools", "policy", "memory", or "browser" as authority by accident.
    """

    payload: Mapping[str, Any] = field(default_factory=dict)
    content_untrusted: bool = True
    instruction_use_allowed: bool = False
    blocked_instruction_channels: tuple[str, ...] = (
        "tool",
        "shell",
        "browser",
        "connector",
        "memory",
        "policy",
    )


@dataclass(frozen=True)
class WebAccessRequest:
    """Request accepted by WebAccessGateway."""

    kind: WebAccessRequestKind
    url: str | None = None
    query: str | None = None
    method: str = "GET"
    authority_mode: WebAccessAuthorityMode = WebAccessAuthorityMode.READ_ONLY
    network_lane: WebAccessNetworkLane = WebAccessNetworkLane.AGENT_PUBLIC_WEB
    allowed_domains: tuple[str, ...] = ()
    actor: str | None = None
    session_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"web-access-request:{uuid4().hex}")

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", self.method.upper())


@dataclass(frozen=True)
class WebAccessResult:
    """Result returned by WebAccessGateway for allowed, denied, and error paths."""

    request_id: str
    status: WebAccessPolicyStatus
    decision: WebAccessPolicyDecision
    audit: WebAccessAuditRecord
    source_metadata: tuple[SourceMetadata, ...] = ()
    evidence_bundle: WebAccessEvidenceBundle | None = None
    error: str | None = None
    content_untrusted: bool = True


class WebAccessAdapter(Protocol):
    """Protocol all gateway adapters must implement."""

    adapter_kind: WebAccessAdapterKind

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        """Execute an already-authorized request and return adapter data."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
