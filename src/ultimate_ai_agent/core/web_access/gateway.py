"""Central WebAccessGateway boundary."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping

from .adapters import GovernedWebEvidenceAdapter, NullWebAccessAdapter
from .audit import build_audit_record, build_source_metadata
from .contracts import (
    SourceMetadata,
    WebAccessAdapter,
    WebAccessAdapterKind,
    WebAccessEvidenceBundle,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebAccessResult,
)
from .policy import WebAccessPolicy


@dataclass
class WebAccessGateway:
    """Single boundary for agent-facing web access.

    The gateway evaluates policy before invoking any adapter and returns a
    normalized result/audit record for both allowed and denied requests.
    """

    policy: WebAccessPolicy = field(default_factory=WebAccessPolicy)
    adapters: Mapping[WebAccessRequestKind, WebAccessAdapter] = field(default_factory=dict)
    default_adapter: WebAccessAdapter = field(default_factory=NullWebAccessAdapter)

    def execute(self, request: WebAccessRequest) -> WebAccessResult:
        decision = self.policy.evaluate(request)
        adapter = self.adapters.get(request.kind, self.default_adapter)

        if not decision.allowed:
            audit = build_audit_record(
                request=request,
                decision=decision,
                adapter_kind=getattr(adapter, "adapter_kind", WebAccessAdapterKind.NONE),
            )
            return WebAccessResult(
                request_id=request.request_id,
                status=decision.status,
                decision=decision,
                audit=audit,
                error=";".join(decision.reasons),
                content_untrusted=True,
            )

        try:
            adapter_result = adapter.execute(request, decision)
        except NotImplementedError as exc:
            not_impl = type(decision)(
                status=WebAccessPolicyStatus.NOT_IMPLEMENTED,
                risk_class=decision.risk_class,
                reasons=(str(exc),),
                allowed_methods=decision.allowed_methods,
                requires_approval=False,
            )
            audit = build_audit_record(
                request=request,
                decision=not_impl,
                adapter_kind=getattr(adapter, "adapter_kind", WebAccessAdapterKind.NONE),
            )
            return WebAccessResult(
                request_id=request.request_id,
                status=WebAccessPolicyStatus.NOT_IMPLEMENTED,
                decision=not_impl,
                audit=audit,
                error=str(exc),
                content_untrusted=True,
            )

        sources = _normalize_sources(request, adapter_result)
        preview = _preview_from_adapter_result(adapter_result)
        evidence_bundle = _quarantine_adapter_result(adapter_result)
        adapter_block = _adapter_block_decision(decision, adapter_result)
        if adapter_block is not None:
            audit = build_audit_record(
                request=request,
                decision=adapter_block,
                adapter_kind=getattr(adapter, "adapter_kind", WebAccessAdapterKind.NONE),
                source_metadata=sources,
                redacted_preview=preview,
            )
            return WebAccessResult(
                request_id=request.request_id,
                status=adapter_block.status,
                decision=adapter_block,
                audit=audit,
                source_metadata=sources,
                evidence_bundle=evidence_bundle,
                error=";".join(adapter_block.reasons),
                content_untrusted=True,
            )

        audit = build_audit_record(
            request=request,
            decision=decision,
            adapter_kind=getattr(adapter, "adapter_kind", WebAccessAdapterKind.NONE),
            source_metadata=sources,
            redacted_preview=preview,
        )
        return WebAccessResult(
            request_id=request.request_id,
            status=WebAccessPolicyStatus.ALLOWED,
            decision=decision,
            audit=audit,
            source_metadata=sources,
            evidence_bundle=evidence_bundle,
            content_untrusted=True,
        )


def create_default_web_access_gateway() -> WebAccessGateway:
    """Create the first-slice gateway.

    Read-only fetch and browser observe are policy-disabled by default.
    Governed web evidence routes through its wrapper when available and remains
    constrained by the existing governed evidence policy/transport.
    """

    return WebAccessGateway(
        policy=WebAccessPolicy(allow_governed_web_evidence=True, allow_read_only_fetch=False),
        adapters={
            WebAccessRequestKind.GOVERNED_WEB_EVIDENCE: GovernedWebEvidenceAdapter(),
        },
    )


def _normalize_sources(
    request: WebAccessRequest,
    adapter_result: Mapping[str, object],
) -> tuple[SourceMetadata, ...]:
    raw_sources = adapter_result.get("sources")
    if isinstance(raw_sources, list):
        normalized: list[SourceMetadata] = []
        for item in raw_sources:
            if isinstance(item, SourceMetadata):
                normalized.append(_force_untrusted_source(item))
            elif isinstance(item, Mapping):
                url = item.get("url") or item.get("final_url") or request.url
                if isinstance(url, str):
                    normalized.append(build_source_metadata(request, final_url=url))
        if normalized:
            return tuple(normalized)
    return (build_source_metadata(request),)


def _force_untrusted_source(source: SourceMetadata) -> SourceMetadata:
    if source.content_untrusted:
        return source
    return replace(source, content_untrusted=True)


def _quarantine_adapter_result(adapter_result: Mapping[str, object]) -> WebAccessEvidenceBundle:
    return WebAccessEvidenceBundle(payload=adapter_result, content_untrusted=True)


def _adapter_block_decision(
    decision: WebAccessPolicyDecision,
    adapter_result: Mapping[str, object],
) -> WebAccessPolicyDecision | None:
    adapter_allowed = adapter_result.get("allowed")
    adapter_status = adapter_result.get("status")
    if adapter_allowed is not False and adapter_status not in {"blocked", "denied"}:
        return None

    reasons = ["adapter_policy_blocked"]
    reason_codes = adapter_result.get("reason_codes")
    if isinstance(reason_codes, (list, tuple)):
        reasons.extend(f"adapter_reason:{str(reason)}" for reason in reason_codes)
    elif isinstance(adapter_status, str):
        reasons.append(f"adapter_status:{adapter_status}")

    return type(decision)(
        status=WebAccessPolicyStatus.DENIED,
        risk_class=decision.risk_class,
        reasons=tuple(reasons),
        allowed_methods=decision.allowed_methods,
        requires_approval=False,
    )


def _preview_from_adapter_result(adapter_result: Mapping[str, object]) -> str | None:
    for key in ("preview", "summary", "text", "markdown"):
        value = adapter_result.get(key)
        if isinstance(value, str):
            return value
    preview = adapter_result.get("preview")
    if isinstance(preview, Mapping):
        text_preview = preview.get("text_preview")
        if isinstance(text_preview, str):
            return text_preview
    return None
