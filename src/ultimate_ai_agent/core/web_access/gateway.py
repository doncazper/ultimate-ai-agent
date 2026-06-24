"""Central WebAccessGateway boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .adapters import GovernedWebEvidenceAdapter, NullWebAccessAdapter
from .audit import build_audit_record, build_source_metadata
from .contracts import (
    SourceMetadata,
    WebAccessAdapter,
    WebAccessAdapterKind,
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
            evidence_bundle=adapter_result,
            content_untrusted=True,
        )


def create_default_web_access_gateway() -> WebAccessGateway:
    """Create the first-slice gateway.

    Read-only fetch is policy-disabled by default. Governed web evidence routes
    through its wrapper when available and remains constrained by the existing
    governed evidence policy/transport.
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
                normalized.append(item)
            elif isinstance(item, Mapping):
                url = item.get("url") or item.get("final_url") or request.url
                if isinstance(url, str):
                    normalized.append(build_source_metadata(request, final_url=url))
        if normalized:
            return tuple(normalized)
    return (build_source_metadata(request),)


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
