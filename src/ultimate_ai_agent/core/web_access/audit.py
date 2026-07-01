"""Audit helpers for WebAccessGateway."""

from __future__ import annotations

from urllib.parse import urlparse

from .contracts import (
    SourceMetadata,
    WebAccessAdapterKind,
    WebAccessAuditRecord,
    WebAccessPolicyDecision,
    WebAccessRequest,
    utc_now,
)


def build_source_metadata(request: WebAccessRequest, *, final_url: str | None = None) -> SourceMetadata:
    url = final_url or request.url
    parsed = urlparse(url or "")
    return SourceMetadata(
        url=request.url,
        final_url=final_url or request.url,
        host=(parsed.hostname or None),
        source_type=request.kind.value,
        allowed_methods=("GET",),
        fetched_at=utc_now(),
        content_untrusted=True,
    )


def build_audit_record(
    *,
    request: WebAccessRequest,
    decision: WebAccessPolicyDecision,
    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.NONE,
    source_metadata: tuple[SourceMetadata, ...] = (),
    redacted_preview: str | None = None,
) -> WebAccessAuditRecord:
    return WebAccessAuditRecord(
        request_id=request.request_id,
        timestamp=utc_now(),
        request_kind=request.kind,
        url=request.url,
        adapter_kind=adapter_kind,
        network_lane=request.network_lane,
        authority_mode=request.authority_mode,
        risk_class=decision.risk_class,
        policy_status=decision.status,
        policy_reasons=decision.reasons,
        source_metadata=source_metadata,
        actor=request.actor,
        session_id=request.session_id,
        redacted_preview=redact_preview(redacted_preview),
        content_untrusted=True,
    )


def redact_preview(value: str | None, *, max_len: int = 500) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[:max_len]}..."
