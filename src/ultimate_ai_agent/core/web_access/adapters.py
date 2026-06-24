"""Adapters behind the WebAccessGateway boundary.

This module intentionally avoids adding provider dependencies. Provider shells
are metadata/diagnostic contracts only until a later scoped milestone grants
exact runtime authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .contracts import (
    WebAccessAdapterKind,
    WebAccessPolicyDecision,
    WebAccessRequest,
    WebAccessRequestKind,
)


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


class DisabledProviderShellStatus(str, Enum):
    """Provider shell status labels that do not imply runtime authority."""

    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class DisabledProviderShellContract:
    """Metadata-only provider shell contract.

    A shell records the future adapter shape without importing provider SDKs,
    loading credentials, opening browser sessions, starting scrape jobs, or
    making network calls.
    """

    provider_ref: str
    provider_label: str
    adapter_kind: WebAccessAdapterKind
    supported_request_kinds: tuple[WebAccessRequestKind, ...]
    status: DisabledProviderShellStatus = DisabledProviderShellStatus.DISABLED
    configured: bool = False
    credentials_configured: bool = False
    provider_sdk_import_allowed: bool = False
    callable_runtime_authority: bool = False
    network_calls_allowed: bool = False
    browser_sessions_allowed: bool = False
    scrape_jobs_allowed: bool = False
    remote_execution_allowed: bool = False
    diagnostic_only: bool = True
    content_untrusted: bool = True

    def __post_init__(self) -> None:
        if not self.provider_ref.startswith("web-provider-shell:"):
            raise ValueError("WEB_PROVIDER_SHELL_REF_REQUIRED")
        if not self.provider_label:
            raise ValueError("WEB_PROVIDER_SHELL_LABEL_REQUIRED")
        if not self.supported_request_kinds:
            raise ValueError("WEB_PROVIDER_SHELL_REQUEST_KIND_REQUIRED")
        if any(not isinstance(kind, WebAccessRequestKind) for kind in self.supported_request_kinds):
            raise ValueError("WEB_PROVIDER_SHELL_REQUEST_KIND_INVALID")
        if self.configured:
            raise ValueError("WEB_PROVIDER_SHELL_MUST_NOT_BE_CONFIGURED")
        if self.credentials_configured:
            raise ValueError("WEB_PROVIDER_SHELL_CREDENTIALS_DENIED")
        if self.provider_sdk_import_allowed:
            raise ValueError("WEB_PROVIDER_SHELL_SDK_IMPORT_DENIED")
        if self.callable_runtime_authority:
            raise ValueError("WEB_PROVIDER_SHELL_CALLABLE_RUNTIME_DENIED")
        if self.network_calls_allowed:
            raise ValueError("WEB_PROVIDER_SHELL_NETWORK_CALL_DENIED")
        if self.browser_sessions_allowed:
            raise ValueError("WEB_PROVIDER_SHELL_BROWSER_SESSION_DENIED")
        if self.scrape_jobs_allowed:
            raise ValueError("WEB_PROVIDER_SHELL_SCRAPE_JOB_DENIED")
        if self.remote_execution_allowed:
            raise ValueError("WEB_PROVIDER_SHELL_REMOTE_EXECUTION_DENIED")
        if not self.diagnostic_only:
            raise ValueError("WEB_PROVIDER_SHELL_DIAGNOSTIC_ONLY_REQUIRED")
        if not self.content_untrusted:
            raise ValueError("WEB_PROVIDER_SHELL_CONTENT_UNTRUSTED_REQUIRED")

    def diagnostic_payload(self, request: WebAccessRequest) -> Mapping[str, Any]:
        """Return redacted diagnostics that cannot be mistaken for authority."""

        return {
            "provider_ref": self.provider_ref,
            "provider_label": self.provider_label,
            "adapter_kind": self.adapter_kind.value,
            "request_kind": request.kind.value,
            "supported_request_kinds": [
                kind.value for kind in self.supported_request_kinds
            ],
            "supported_request_kind_matched": request.kind in self.supported_request_kinds,
            "status": self.status.value,
            "configured": False,
            "credentials_configured": False,
            "provider_sdk_import_allowed": False,
            "provider_sdk_imported": False,
            "provider_sdk_call_performed": False,
            "callable_runtime_authority": False,
            "network_calls_allowed": False,
            "network_call_performed": False,
            "browser_sessions_allowed": False,
            "browser_session_started": False,
            "scrape_jobs_allowed": False,
            "scrape_job_started": False,
            "search_call_performed": False,
            "remote_execution_allowed": False,
            "remote_execution_performed": False,
            "diagnostic_only": True,
            "content_untrusted": True,
        }


@dataclass(frozen=True)
class DisabledProviderAdapterShell:
    """Disabled adapter shell for future provider integrations."""

    contract: DisabledProviderShellContract

    @property
    def adapter_kind(self) -> WebAccessAdapterKind:
        return self.contract.adapter_kind

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        payload = dict(self.contract.diagnostic_payload(request))
        reason_codes = [
            "WEB_PROVIDER_ADAPTER_SHELL_DISABLED",
            "WEB_PROVIDER_RUNTIME_AUTHORITY_NOT_GRANTED",
            "WEB_PROVIDER_DIAGNOSTIC_ONLY",
        ]
        if request.kind not in self.contract.supported_request_kinds:
            reason_codes.append("WEB_PROVIDER_SHELL_REQUEST_KIND_UNSUPPORTED")
        payload.update(
            {
                "allowed": False,
                "reason_codes": reason_codes,
                "summary": "Provider adapter shell is disabled and diagnostic-only.",
            }
        )
        return payload


def disabled_provider_adapter_shell_catalog() -> tuple[DisabledProviderShellContract, ...]:
    """Return metadata-only provider shells for future WebAccessGateway work."""

    return (
        DisabledProviderShellContract(
            provider_ref="web-provider-shell:search-neutral",
            provider_label="Search provider shell",
            adapter_kind=WebAccessAdapterKind.SEARCH_API,
            supported_request_kinds=(WebAccessRequestKind.SEARCH,),
        ),
        DisabledProviderShellContract(
            provider_ref="web-provider-shell:firecrawl",
            provider_label="Firecrawl provider shell",
            adapter_kind=WebAccessAdapterKind.FIRECRAWL,
            supported_request_kinds=(
                WebAccessRequestKind.SEARCH,
                WebAccessRequestKind.EXTRACT_SCHEMA,
            ),
        ),
        DisabledProviderShellContract(
            provider_ref="web-provider-shell:browserbase-observe",
            provider_label="Browserbase observe provider shell",
            adapter_kind=WebAccessAdapterKind.BROWSERBASE_OBSERVE,
            supported_request_kinds=(WebAccessRequestKind.BROWSER_OBSERVE,),
        ),
    )


def disabled_provider_adapter_shells() -> Mapping[str, DisabledProviderAdapterShell]:
    """Return disabled shells keyed by provider shell ref."""

    return {
        contract.provider_ref: DisabledProviderAdapterShell(contract=contract)
        for contract in disabled_provider_adapter_shell_catalog()
    }
