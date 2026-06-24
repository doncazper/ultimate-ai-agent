"""Adapters behind the WebAccessGateway boundary.

This first PR intentionally avoids adding new provider dependencies. The primary
adapter is a thin wrapper around the repo's existing governed web evidence flow.
Browser/search/provider adapters should be added in later milestone PRs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import WebAccessAdapterKind, WebAccessPolicyDecision, WebAccessRequest


@dataclass(frozen=True)
class NullWebAccessAdapter:
    """Adapter used when no runtime is enabled."""

    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.NONE

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        raise NotImplementedError("No WebAccess adapter is configured for this request.")


@dataclass(frozen=True)
class GovernedWebEvidenceAdapter:
    """Thin wrapper around `core.network.governed_web_evidence`.

    The existing governed web evidence module already enforces HTTPS-only,
    allowlisted hosts, bounded redacted previews, raw-body/header omission, no
    cookies/session state, no downloads, no browser automation, and no context
    injection. This adapter places that path behind the central WebAccessGateway
    policy/audit boundary.
    """

    policy: Any | None = None
    transport: Any | None = None
    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.GOVERNED_WEB_EVIDENCE

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        (
            GovernedWebEvidenceRequest,
            fetch_governed_web_evidence,
            governed_web_evidence_policy_from_env,
        ) = self._load_governed_web_evidence_symbols()

        governed_request = GovernedWebEvidenceRequest(
            request_ref=_safe_ref("web-access-request", request.request_id),
            run_id=_safe_ref("web-access-run", request.session_id or "local"),
            actor_ref=_safe_ref("actor", request.actor or "local-operator"),
            purpose=str(
                request.metadata.get(
                    "purpose",
                    "WebAccessGateway governed web evidence request.",
                )
            ),
            url=request.url or "",
            citation_requested=True,
            raw_body_requested=False,
            raw_headers_requested=False,
            download_requested=False,
            browser_automation_requested=False,
            unrestricted_network_requested=False,
            credential_material_requested=False,
            session_state_requested=False,
            hidden_network_requested=False,
            context_injection_requested=False,
            memory_write_requested=False,
            provider_model_call_requested=False,
        )
        policy = self.policy or governed_web_evidence_policy_from_env()
        result = fetch_governed_web_evidence(
            governed_request,
            policy=policy,
            transport=self.transport,
        )
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")
        if isinstance(result, Mapping):
            return result
        return {"evidence": result, "url": request.url}

    @staticmethod
    def _load_governed_web_evidence_symbols():  # type: ignore[no-untyped-def]
        try:
            from ultimate_ai_agent.core.network.governed_web_evidence import (  # noqa: PLC0415
                GovernedWebEvidenceRequest,
                fetch_governed_web_evidence,
                governed_web_evidence_policy_from_env,
            )
        except ImportError as exc:  # pragma: no cover - depends on host repo shape.
            raise NotImplementedError(
                "Could not import governed web evidence symbols. Adapt this wrapper "
                "to the existing governed_web_evidence.py names/signatures without "
                "bypassing WebAccessGateway policy or audit."
            ) from exc
        return GovernedWebEvidenceRequest, fetch_governed_web_evidence, governed_web_evidence_policy_from_env


def _safe_ref(prefix: str, value: str) -> str:
    """Return a repo-compatible structured safe ref."""

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256-{digest}"
