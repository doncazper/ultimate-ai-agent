from __future__ import annotations

import hashlib
import os
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    TrustMode,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.tools.runtime.http_fetch import (
    DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES,
    ReadOnlyHttpFetchOutput,
    ReadOnlyHttpFetchPolicy,
    ReadOnlyHttpFetchRequest,
    build_read_only_http_fetch_output_via_web_access_gateway,
    normalize_http_fetch_target,
)
from ultimate_ai_agent.core.web_access.read_only_http_fetch_transport import (
    build_read_only_real_world_http_fetch_transport,
)


WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF = (
    "contract-ref:web-evidence-product-slice:v1"
)
WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF = "POST /control-center/web-evidence/attach"
WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_SAFE_REF = (
    "route-ref:control-center-web-evidence-attach"
)
WEB_EVIDENCE_PRODUCT_SLICE_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py attach-web-evidence"
)
WEB_EVIDENCE_PRODUCT_SLICE_SOURCE = "python_core_web_evidence_product_slice"
WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF = "proof-ref:web-evidence:product-slice"
WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF = (
    "safe-disable:web-evidence-product-slice:env-and-route-off"
)
WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF = (
    "rollback:web-evidence-product-slice:suppress-local-receipt"
)
WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:web-evidence:no-unrestricted-browsing",
    "blocked-state:web-evidence:no-browser-actions",
    "blocked-state:web-evidence:no-auth-session-state",
    "blocked-state:web-evidence:no-downloads-or-uploads",
    "blocked-state:web-evidence:no-post-put-patch-delete",
    "blocked-state:web-evidence:no-raw-body-persistence",
    "blocked-state:web-evidence:no-context-injection",
    "blocked-state:web-evidence:no-memory-write",
    "blocked-state:web-evidence:no-provider-model-call",
    "blocked-state:web-evidence:no-connector-write",
    "blocked-state:web-evidence:no-production-authority",
)
WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV = "UAA_WEB_EVIDENCE_PRODUCT_SLICE_DISABLED"
WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV = (
    "UAA_WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS"
)
WEB_EVIDENCE_PRODUCT_SLICE_IDEMPOTENCY_POSTURE_REF = (
    "idempotency:web-evidence-product-slice:request-ref-payload"
)
WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_LANE_REF = (
    "lane-ref:web-evidence-product-slice"
)
WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_BLOCKED_REF = (
    "blocked-state:web-evidence:browser-read-authority-required"
)
WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_MODE_REF = "authority-mode-ref:read-only"
WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF = "authority-domain-ref:browser"
WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF = (
    "authority-capability-ref:read"
)


class WebEvidenceProductSliceAuthorityError(ValueError):
    def __init__(self, decision: AuthorityPolicyDecision) -> None:
        super().__init__("WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DENIED")
        self.decision = decision


class WebEvidenceProductSliceRequest(BaseModel):
    """Operator request for one allowlisted read-only web evidence preview."""

    request_ref: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1, max_length=1000)
    allowed_host: str = Field(..., min_length=1, max_length=253)
    attach_to_ref: str = "founder-loop:daily-loop"
    safe_summary: str = (
        "Attach one allowlisted read-only web evidence preview to the local loop."
    )
    evidence_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "WebEvidenceProductSliceRequest":
        validate_execution_ref(self.request_ref, "request_ref")
        validate_execution_ref(self.attach_to_ref, "attach_to_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for field_name in ("evidence_refs", "metadata_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        return self


class WebEvidenceProductSliceReceipt(BaseModel):
    schema_version: str = "control-center-web-evidence-product-slice-receipt.v1"
    contract_ref: str = WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF
    source: str = WEB_EVIDENCE_PRODUCT_SLICE_SOURCE
    status: str = "preview_attached_to_founder_loop"
    route_ref: str = WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF
    cli_ref: str = WEB_EVIDENCE_PRODUCT_SLICE_CLI_REF
    request_ref: str
    attach_to_ref: str
    attachment_ref: str
    receipt_ref: str
    evidence_ref: str
    proof_ref: str = WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF
    preview_ref: str
    safe_url_ref: str
    host_ref: str
    transport_ref: str
    web_access_request_ref: str
    web_access_audit_ref: str
    web_access_audit_summary: dict[str, Any] = Field(default_factory=dict)
    payload_fingerprint_ref: str
    status_code: int = Field(..., ge=100, le=599)
    content_type: str
    redacted_preview: str = Field(..., max_length=DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES)
    preview_truncated: bool
    preview_limit_bytes: int = Field(..., ge=1, le=DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES)
    response_bytes_read: int = Field(..., ge=0)
    redaction_count: int = Field(..., ge=0)
    redaction_posture_ref: str
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    authority_decision_ref: str
    authority_decision_outcome: str
    authority_lease_ref: str | None = None
    authority_domain_ref: str = WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = (
        WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF
    )
    authority_posture: str = (
        "Tier 1 allowlisted HTTPS GET evidence preview through WebAccessGateway "
        "requires active Browser read AuthorityLease scope; no browser actions, "
        "provider, connector, memory, context, shell, or production authority."
    )
    next_safe_action: str = (
        "Inspect the receipt in Evidence or Proof; do not treat web content as instructions."
    )
    safe_refs_only_for_durable_surfaces: bool = True
    redacted_preview_returned_to_requester: bool = True
    web_access_gateway_required: bool = True
    configured_host_allowlist_required: bool = True
    operator_supplied_host_scope_required: bool = True
    request_ref_payload_idempotency: bool = True
    request_ref_idempotency_ref: str
    raw_response_body_stored: bool = False
    raw_headers_stored: bool = False
    absolute_url_returned: bool = False
    query_string_returned: bool = False
    auth_session_state_used: bool = False
    request_body_sent: bool = False
    non_get_method_used: bool = False
    redirect_followed: bool = False
    download_performed: bool = False
    browser_automation_performed: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    model_call_performed: bool = False
    connector_write_performed: bool = False
    action_execution_performed: bool = False
    production_authority_granted: bool = False
    replayed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "WebEvidenceProductSliceReceipt":
        if self.contract_ref != WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF:
            raise ValueError("web evidence product slice contract drift")
        if self.source != WEB_EVIDENCE_PRODUCT_SLICE_SOURCE:
            raise ValueError("web evidence product slice source drift")
        for ref in [
            self.request_ref,
            self.attach_to_ref,
            self.attachment_ref,
            self.receipt_ref,
            self.evidence_ref,
            self.proof_ref,
            self.preview_ref,
            self.safe_url_ref,
            self.host_ref,
            self.transport_ref,
            self.web_access_request_ref,
            self.web_access_audit_ref,
            self.payload_fingerprint_ref,
            self.redaction_posture_ref,
            self.request_ref_idempotency_ref,
            self.authority_decision_ref,
            self.authority_lease_ref,
            self.authority_domain_ref,
            self.authority_capability_ref,
        ]:
            if ref is not None:
                validate_execution_ref(ref, "web_evidence_ref")
        for field_name in (
            "receipt_refs",
            "evidence_refs",
            "audit_refs",
            "rollback_refs",
            "safe_disable_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.status, "status")
        validate_safe_execution_text(self.route_ref, "route_ref")
        validate_safe_execution_text(self.cli_ref, "cli_ref")
        validate_safe_execution_text(self.content_type, "content_type")
        validate_safe_execution_text(
            self.authority_decision_outcome,
            "authority_decision_outcome",
        )
        validate_safe_execution_text(self.authority_posture, "authority_posture")
        validate_safe_execution_text(self.next_safe_action, "next_safe_action")
        denied_flags = [
            self.raw_response_body_stored,
            self.raw_headers_stored,
            self.absolute_url_returned,
            self.query_string_returned,
            self.auth_session_state_used,
            self.request_body_sent,
            self.non_get_method_used,
            self.redirect_followed,
            self.download_performed,
            self.browser_automation_performed,
            self.context_injection_performed,
            self.memory_write_performed,
            self.model_call_performed,
            self.connector_write_performed,
            self.action_execution_performed,
            self.production_authority_granted,
        ]
        if any(denied_flags):
            raise ValueError("web evidence product slice must remain read-only")
        if not (
            self.safe_refs_only_for_durable_surfaces
            and self.redacted_preview_returned_to_requester
            and self.web_access_gateway_required
            and self.configured_host_allowlist_required
            and self.operator_supplied_host_scope_required
            and self.request_ref_payload_idempotency
        ):
            raise ValueError("web evidence product slice required posture drifted")
        if self.receipt_ref not in self.receipt_refs:
            raise ValueError("web evidence receipt refs must include receipt_ref")
        if self.evidence_ref not in self.evidence_refs:
            raise ValueError("web evidence evidence refs must include evidence_ref")
        if self.web_access_audit_ref not in self.audit_refs:
            raise ValueError("web evidence audit refs must include WebAccess audit ref")
        if not _is_safe_web_access_audit_summary(
            self.web_access_audit_summary,
            web_access_request_ref=self.web_access_request_ref,
            safe_url_ref=self.safe_url_ref,
            host_ref=self.host_ref,
        ):
            raise ValueError("web evidence audit summary drifted")
        if self.authority_decision_outcome != AuthorityDecisionOutcome.allow.value:
            raise ValueError("web evidence requires an allowed authority decision")
        if not self.authority_lease_ref:
            raise ValueError("web evidence authority lease ref required")
        return self

    def durable_record(self) -> dict[str, Any]:
        """Return storage-safe metadata only; page text is intentionally omitted."""

        return {
            "schema_version": self.schema_version,
            "contract_ref": self.contract_ref,
            "source": self.source,
            "status": self.status,
            "route_ref": self.route_ref,
            "cli_ref": self.cli_ref,
            "request_ref": self.request_ref,
            "attach_to_ref": self.attach_to_ref,
            "attachment_ref": self.attachment_ref,
            "receipt_ref": self.receipt_ref,
            "evidence_ref": self.evidence_ref,
            "proof_ref": self.proof_ref,
            "preview_ref": self.preview_ref,
            "safe_url_ref": self.safe_url_ref,
            "host_ref": self.host_ref,
            "transport_ref": self.transport_ref,
            "web_access_request_ref": self.web_access_request_ref,
            "web_access_audit_ref": self.web_access_audit_ref,
            "web_access_audit_summary": self.web_access_audit_summary,
            "payload_fingerprint_ref": self.payload_fingerprint_ref,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "preview_truncated": self.preview_truncated,
            "preview_limit_bytes": self.preview_limit_bytes,
            "response_bytes_read": self.response_bytes_read,
            "redaction_count": self.redaction_count,
            "redaction_posture_ref": self.redaction_posture_ref,
            "receipt_refs": self.receipt_refs,
            "evidence_refs": self.evidence_refs,
            "audit_refs": self.audit_refs,
            "rollback_refs": self.rollback_refs,
            "safe_disable_refs": self.safe_disable_refs,
            "blocked_authority_refs": self.blocked_authority_refs,
            "authority_decision_ref": self.authority_decision_ref,
            "authority_decision_outcome": self.authority_decision_outcome,
            "authority_lease_ref": self.authority_lease_ref,
            "authority_domain_ref": self.authority_domain_ref,
            "authority_capability_ref": self.authority_capability_ref,
            "authority_posture": self.authority_posture,
            "next_safe_action": self.next_safe_action,
            "durable_preview_text_storage": "omitted_use_preview_ref",
            "response_body_storage": "omitted",
            "header_storage": "omitted",
            "absolute_url_storage": "omitted",
            "safe_refs_only_for_durable_surfaces": True,
            "web_access_gateway_required": True,
            "configured_host_allowlist_required": True,
            "operator_supplied_host_scope_required": True,
            "request_ref_payload_idempotency": True,
            "request_ref_idempotency_ref": self.request_ref_idempotency_ref,
            "replayed": self.replayed,
        }


def build_web_evidence_product_slice_receipt(
    request: WebEvidenceProductSliceRequest,
    *,
    transport: Any | None = None,
    active_authority_leases: list[AuthorityLease] | None = None,
) -> WebEvidenceProductSliceReceipt:
    scoped_host = _enforce_product_slice_runtime_policy(request)
    authority_decision = evaluate_web_evidence_product_slice_authority(
        request,
        scoped_host=scoped_host,
        active_authority_leases=active_authority_leases,
    )
    if authority_decision.outcome != AuthorityDecisionOutcome.allow.value:
        raise WebEvidenceProductSliceAuthorityError(authority_decision)
    output = _fetch_output(request, transport=transport, scoped_host=scoped_host)
    suffix = _short_digest(
        "|".join(
            [
                request.request_ref,
                request.attach_to_ref,
                output.safe_url_ref,
                output.web_access_request_ref,
            ]
        )
    )
    redaction_count = output.redaction_summary.redaction_count
    receipt_ref = f"receipt:web-evidence-product-slice:{suffix}"
    evidence_ref = f"evidence-ref:web-evidence-product-slice:{suffix}"
    audit_refs = [output.web_access_audit_ref]
    return WebEvidenceProductSliceReceipt(
        request_ref=request.request_ref,
        attach_to_ref=request.attach_to_ref,
        attachment_ref=f"web-evidence-attachment:{suffix}",
        receipt_ref=receipt_ref,
        evidence_ref=evidence_ref,
        preview_ref=f"web-evidence-preview:{_short_digest(output.redacted_preview)}",
        safe_url_ref=output.safe_url_ref,
        host_ref=output.host_ref,
        transport_ref=output.transport_ref,
        web_access_request_ref=output.web_access_request_ref,
        web_access_audit_ref=output.web_access_audit_ref,
        web_access_audit_summary=output.web_access_audit_summary,
        payload_fingerprint_ref=web_evidence_payload_fingerprint_ref(
            {
                "request_ref": request.request_ref,
                "attach_to_ref": request.attach_to_ref,
                "safe_url_ref": output.safe_url_ref,
                "host_ref": output.host_ref,
                "status_code": output.status_code,
                "preview_ref": f"web-evidence-preview:{_short_digest(output.redacted_preview)}",
            }
        ),
        status_code=output.status_code,
        content_type=output.content_type,
        redacted_preview=output.redacted_preview,
        preview_truncated=output.preview_truncated,
        preview_limit_bytes=output.preview_limit_bytes,
        response_bytes_read=output.response_bytes_read,
        redaction_count=redaction_count,
        redaction_posture_ref=(
            "redaction-posture:web-evidence:sensitive-values-withheld"
            if redaction_count
            else "redaction-posture:web-evidence:no-sensitive-patterns-detected"
        ),
        request_ref_idempotency_ref=(
            f"idempotency-ref:web-evidence-product-slice:{suffix}"
        ),
        receipt_refs=[receipt_ref],
        evidence_refs=[
            evidence_ref,
            *request.evidence_refs,
            "evidence-ref:web-evidence-product-slice:gateway-fetch",
        ],
        audit_refs=audit_refs,
        rollback_refs=[WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF],
        safe_disable_refs=[WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF],
        blocked_authority_refs=list(WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS),
        authority_decision_ref=authority_decision.decision_ref,
        authority_decision_outcome=authority_decision.outcome,
        authority_lease_ref=authority_decision.lease_ref,
    )


def build_web_evidence_product_slice_authority_request(
    request: WebEvidenceProductSliceRequest,
    *,
    scoped_host: str | None = None,
) -> AuthorityActionRequest:
    host = scoped_host or _request_host(
        request.url,
        scope_policy=ReadOnlyHttpFetchPolicy(
            policy_ref="http-fetch-policy:web-evidence-product-slice-authority",
            allowed_hosts=(request.allowed_host,),
        ),
    )
    action_ref = (
        "authority-action-ref:web-evidence-product-slice:"
        f"{_short_digest([request.request_ref, host])}"
    )
    return AuthorityActionRequest(
        action_ref=action_ref,
        domain=AuthorityDomain.browser,
        capability=AuthorityCapability.read,
        safe_summary=(
            "Attach one allowlisted WebAccessGateway HTTPS GET preview as "
            "redacted web evidence."
        ),
        resource_refs=[
            request.request_ref,
            request.attach_to_ref,
            WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
            WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_SAFE_REF,
            f"web-evidence-host-ref:{_short_digest(host)}",
        ],
        route_ref=WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
        lane_ref=WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_LANE_REF,
        adapter_ref="adapter-ref:web-access-gateway:https-get-preview",
        requested_mode=TrustMode.read_only,
        constraints={
            "configured_host_ref": f"web-evidence-host-ref:{_short_digest(host)}",
            "https_get_only": True,
            "browser_actions_allowed": False,
            "auth_session_state_allowed": False,
            "download_upload_allowed": False,
            "mutation_methods_allowed": False,
            "raw_body_persistence_allowed": False,
        },
        draft_fallback_available=False,
        rollback_ref=WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF,
        safe_disable_ref=WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF,
    )


def evaluate_web_evidence_product_slice_authority(
    request: WebEvidenceProductSliceRequest,
    *,
    scoped_host: str | None = None,
    active_authority_leases: list[AuthorityLease] | None = None,
) -> AuthorityPolicyDecision:
    leases = active_authority_leases or build_default_authority_leases()
    return evaluate_authority_request(
        build_web_evidence_product_slice_authority_request(
            request,
            scoped_host=scoped_host,
        ),
        leases,
    )


def web_evidence_payload_fingerprint_ref(payload: Mapping[str, Any]) -> str:
    return f"payload-fingerprint:web-evidence-product-slice:{_short_digest(payload)}"


def _fetch_output(
    request: WebEvidenceProductSliceRequest,
    *,
    transport: Any | None,
    scoped_host: str | None = None,
) -> ReadOnlyHttpFetchOutput:
    scoped_host = scoped_host or _enforce_product_slice_runtime_policy(request)
    fetch_request = ReadOnlyHttpFetchRequest(
        request_ref=request.request_ref.replace(
            "web-evidence-request:",
            "http-fetch-request:",
        ),
        url=request.url,
        allowed_host_policy_ref="http-fetch-policy:web-evidence-product-slice",
        safe_summary=request.safe_summary,
        authority_refs=[
            WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
            "authority-tier:tier-1-local-read-preview",
        ],
        metadata={
            "attach_to_ref": request.attach_to_ref,
            "product_slice_ref": WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
        },
    )
    policy = ReadOnlyHttpFetchPolicy(
        policy_ref="http-fetch-policy:web-evidence-product-slice",
        allowed_hosts=(scoped_host,),
        max_preview_bytes=2048,
        max_response_bytes=65536,
        timeout_seconds=5,
    )
    return build_read_only_http_fetch_output_via_web_access_gateway(
        invocation_id=f"tool-runtime-invocation:web-evidence-product-slice-{_short_digest(request.request_ref)}",
        request=fetch_request,
        policy=policy,
        transport=transport or build_read_only_real_world_http_fetch_transport(),
    )


def configured_web_evidence_product_slice_allowed_hosts() -> tuple[str, ...]:
    raw_value = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, "")
    hosts = tuple(host.strip() for host in raw_value.split(",") if host.strip())
    if not hosts:
        return tuple()
    return ReadOnlyHttpFetchPolicy(
        policy_ref="http-fetch-policy:web-evidence-product-slice-env-allowlist",
        allowed_hosts=hosts,
    ).allowed_hosts


def web_evidence_product_slice_disabled() -> bool:
    value = os.environ.get(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _enforce_product_slice_runtime_policy(
    request: WebEvidenceProductSliceRequest,
) -> str:
    if web_evidence_product_slice_disabled():
        raise ValueError("WEB_EVIDENCE_PRODUCT_SLICE_DISABLED")
    configured_hosts = configured_web_evidence_product_slice_allowed_hosts()
    if not configured_hosts:
        raise ValueError("WEB_EVIDENCE_PRODUCT_SLICE_CONFIGURED_ALLOWLIST_REQUIRED")
    scope_policy = ReadOnlyHttpFetchPolicy(
        policy_ref="http-fetch-policy:web-evidence-product-slice-request-scope",
        allowed_hosts=(request.allowed_host,),
    )
    scoped_host = scope_policy.allowed_hosts[0]
    request_host = _request_host(request.url, scope_policy=scope_policy)
    if scoped_host != request_host:
        raise ValueError("WEB_EVIDENCE_PRODUCT_SLICE_HOST_SCOPE_MISMATCH")
    if scoped_host not in configured_hosts:
        raise ValueError("WEB_EVIDENCE_PRODUCT_SLICE_HOST_NOT_CONFIGURED")
    return scoped_host


def _request_host(url: str, *, scope_policy: ReadOnlyHttpFetchPolicy) -> str:
    fetch_request = ReadOnlyHttpFetchRequest(
        request_ref="http-fetch-request:web-evidence-product-slice-host-check",
        url=url,
        allowed_host_policy_ref=scope_policy.policy_ref,
        safe_summary="Validate web evidence host scope through the read-only fetch boundary.",
    )
    return normalize_http_fetch_target(fetch_request, scope_policy).host


def _is_safe_web_access_audit_summary(
    value: Mapping[str, Any],
    *,
    web_access_request_ref: str,
    safe_url_ref: str,
    host_ref: str,
) -> bool:
    if not value:
        return False
    forbidden_keys = {"url", "final_url", "absolute_url", "raw_url"}
    if any(key in value for key in forbidden_keys):
        return False
    required = {
        "schema_version": "web-access-audit-summary.v1",
        "request_ref": web_access_request_ref,
        "safe_url_ref": safe_url_ref,
        "host_ref": host_ref,
        "adapter_kind": "local_fetch",
        "network_lane": "tool_runtime_read_only_fetch",
        "authority_mode": "read_only",
        "risk_class": "low",
        "policy_status": "allowed",
        "content_untrusted": True,
        "raw_url_omitted": True,
        "raw_headers_omitted": True,
        "raw_body_omitted": True,
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            return False
    if not isinstance(value.get("timestamp"), str) or not value["timestamp"]:
        return False
    for field_name in ("policy_reason_refs", "source_metadata_refs"):
        refs = value.get(field_name)
        if not isinstance(refs, list) or not refs:
            return False
        for ref in refs:
            if not isinstance(ref, str):
                return False
            validate_execution_ref(ref, field_name)
    return True


def _short_digest(value: Any) -> str:
    if not isinstance(value, str):
        value = repr(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
