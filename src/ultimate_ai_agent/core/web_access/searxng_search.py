"""Exact governed SearXNG read-only search lane.

This module is the sole phase-three SearXNG transport boundary. It evaluates
PolicyEngine, exact LocalApprovalAuthority scope, an exact resource-constrained
AuthorityLease, capability availability, and WebAccessGateway policy
immediately before one bounded loopback GET. Search evidence remains untrusted
and raw provider payloads and queries are never copied into receipts.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal, Mapping, Sequence
from urllib.parse import urlencode, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.capabilities.approval import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capability_availability import (
    CapabilityAvailabilitySnapshot,
    CapabilityInvocationDecision,
    CapabilityInvocationRequest,
    CostPosture,
    IdempotencyPosture,
    InvocationDecisionOutcome,
    build_capability_availability_snapshot,
    evaluate_capability_invocation,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    SourceMetadata,
    WebAccessAdapterKind,
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)
from .gateway import WebAccessGateway
from .hybrid_contracts import (
    WebProviderCapabilityState,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderTransportMethod,
    WebProviderTransportReceipt,
    WebProviderTransportStatus,
    stable_web_hybrid_ref,
)
from .policy import WebAccessPolicy


SEARXNG_SEARCH_CAPABILITY_REF = "capability-ref:web-access:searxng-search"
SEARXNG_SEARCH_PROVIDER_REF = "provider-ref:searxng:self-hosted"
SEARXNG_SEARCH_ADAPTER_REF = "adapter-ref:web-access:searxng-search:v1"
SEARXNG_SEARCH_LANE_REF = "authority-lane-ref:web-access:searxng-search:v1"
SEARXNG_SEARCH_ENDPOINT_REF = "configured-endpoint-ref:searxng:loopback"
SEARXNG_SEARCH_REQUEST_SCHEMA_REF = "schema-ref:searxng-search-request:v1"
SEARXNG_SEARCH_NOT_METERED_BUDGET_REF = "budget-decision-ref:not-metered:searxng-search"
SEARXNG_SEARCH_DEFAULT_ENDPOINT = "http://127.0.0.1:8888"
SEARXNG_SEARCH_MAX_RESPONSE_BYTES = 524_288
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class SearxngSearchCategory(str, Enum):
    general = "general"


class SearxngSearchLanguage(str, Enum):
    en = "en"


class _SearxngModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class SearxngSearchRequest(_SearxngModel):
    request_ref: str
    task_ref: str
    approval_ref: str | None = None
    query: str = Field(..., min_length=1, max_length=240)
    max_results: int = Field(default=5, ge=1, le=10)
    page: Literal[1] = 1
    category: Literal[SearxngSearchCategory.general] = SearxngSearchCategory.general
    language: Literal[SearxngSearchLanguage.en] = SearxngSearchLanguage.en
    safe_search: Literal[1, 2] = 1
    expected_execution_receipt_ref: str

    @field_validator(
        "request_ref",
        "task_ref",
        "approval_ref",
        "expected_execution_receipt_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        if value is not None:
            validate_execution_ref(value, "searxng_search_ref")
        return value

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized or any(
            ord(char) < 32 or ord(char) == 127 for char in normalized
        ):
            raise ValueError("SEARXNG_QUERY_CONTROL_CHARACTER_DENIED")
        return normalized


class SearxngConfiguredEndpoint(_SearxngModel):
    endpoint_ref: Literal["configured-endpoint-ref:searxng:loopback"] = (
        SEARXNG_SEARCH_ENDPOINT_REF
    )
    base_url: str = SEARXNG_SEARCH_DEFAULT_ENDPOINT
    timeout_seconds: float = Field(default=8.0, gt=0, le=15)
    max_response_bytes: int = Field(
        default=SEARXNG_SEARCH_MAX_RESPONSE_BYTES,
        ge=1024,
        le=SEARXNG_SEARCH_MAX_RESPONSE_BYTES,
    )

    @model_validator(mode="after")
    def validate_fixed_loopback_endpoint(self) -> "SearxngConfiguredEndpoint":
        parts = urlsplit(self.base_url)
        if (
            parts.scheme != "http"
            or parts.hostname != "127.0.0.1"
            or parts.username is not None
            or parts.password is not None
            or parts.path not in {"", "/"}
            or parts.query
            or parts.fragment
            or parts.port is None
        ):
            raise ValueError("SEARXNG_CONFIGURED_LOOPBACK_ENDPOINT_REQUIRED")
        return self


class SearxngSearchEvidenceItem(_SearxngModel):
    source_ref: str
    url: str = Field(..., min_length=1, max_length=2048)
    host: str = Field(..., min_length=1, max_length=253)
    title: str = Field(..., max_length=240)
    snippet: str = Field(default="", max_length=500)
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_public_result(self) -> "SearxngSearchEvidenceItem":
        validate_execution_ref(self.source_ref, "searxng_source_ref")
        parts = urlsplit(self.url)
        host = (parts.hostname or "").lower().rstrip(".")
        if (
            parts.scheme not in {"http", "https"}
            or not host
            or parts.username is not None
            or parts.password is not None
            or host != self.host
            or not _public_result_host(host)
        ):
            raise ValueError("SEARXNG_RESULT_URL_UNSAFE")
        if self.source_ref != _source_ref(self.url):
            raise ValueError("SEARXNG_RESULT_SOURCE_REF_MISMATCH")
        return self


class SearxngSearchExecutionResult(_SearxngModel):
    request_ref: str
    task_ref: str
    invocation_decision: CapabilityInvocationDecision
    transport_receipt: WebProviderTransportReceipt
    gateway_audit_ref: str
    status: WebProviderTransportStatus
    evidence: tuple[SearxngSearchEvidenceItem, ...] = ()
    execution_succeeded: bool = False
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False
    raw_query_stored: Literal[False] = False
    raw_page_stored: Literal[False] = False
    raw_provider_payload_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False
    local_path_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "SearxngSearchExecutionResult":
        for value in (self.request_ref, self.task_ref, self.gateway_audit_ref):
            validate_execution_ref(value, "searxng_execution_ref")
        for code in (*self.reason_codes, *self.blocker_codes):
            if not _SAFE_CODE.fullmatch(code):
                raise ValueError("SEARXNG_EXECUTION_CODE_UNSAFE")
        succeeded = self.status == WebProviderTransportStatus.succeeded
        if self.execution_succeeded != succeeded:
            raise ValueError("SEARXNG_EXECUTION_STATUS_MISMATCH")
        if (
            succeeded
            and self.invocation_decision.outcome != InvocationDecisionOutcome.allow
        ):
            raise ValueError("SEARXNG_EXECUTION_WITHOUT_INVOCATION_AUTHORITY")
        if (
            self.status
            not in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.evidence
        ):
            raise ValueError("SEARXNG_NON_SUCCESS_EVIDENCE_DENIED")
        return self


class SearxngSearchTransportError(RuntimeError):
    """Safe transport error carrying only a bounded reason code."""

    def __init__(self, code: str, *, network_call_performed: bool) -> None:
        if not _SAFE_CODE.fullmatch(code):
            raise ValueError("SEARXNG_TRANSPORT_ERROR_CODE_UNSAFE")
        super().__init__(code)
        self.code = code
        self.network_call_performed = network_call_performed


SearxngTransport = Callable[[SearxngSearchRequest], Mapping[str, Any]]


def build_loopback_searxng_transport(
    endpoint: SearxngConfiguredEndpoint | None = None,
) -> SearxngTransport:
    """Build the exact fixed-loopback, no-redirect JSON GET transport."""

    configured = endpoint or SearxngConfiguredEndpoint()
    parts = urlsplit(configured.base_url)
    host = parts.hostname or ""
    port = parts.port or 80

    def transport(request: SearxngSearchRequest) -> Mapping[str, Any]:
        query = urlencode(
            {
                "q": request.query,
                "format": "json",
                "categories": request.category.value,
                "language": request.language.value,
                "safesearch": request.safe_search,
                "pageno": request.page,
            }
        )
        attempted = False
        try:
            attempted = True
            status, content_type, body = _loopback_json_get(
                host=host,
                port=port,
                path=f"/search?{query}",
                timeout_seconds=configured.timeout_seconds,
                max_response_bytes=configured.max_response_bytes,
            )
            if 300 <= status <= 399:
                raise SearxngSearchTransportError(
                    "SEARXNG_REDIRECT_DENIED",
                    network_call_performed=True,
                )
            if status != 200:
                raise SearxngSearchTransportError(
                    "SEARXNG_NON_SUCCESS_STATUS",
                    network_call_performed=True,
                )
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                raise SearxngSearchTransportError(
                    "SEARXNG_JSON_RESPONSE_REQUIRED",
                    network_call_performed=True,
                )
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise SearxngSearchTransportError(
                    "SEARXNG_RESPONSE_JSON_INVALID",
                    network_call_performed=True,
                ) from exc
            if not isinstance(payload, Mapping):
                raise SearxngSearchTransportError(
                    "SEARXNG_RESPONSE_OBJECT_REQUIRED",
                    network_call_performed=True,
                )
            return payload
        except SearxngSearchTransportError:
            raise
        except (OSError, TimeoutError) as exc:
            raise SearxngSearchTransportError(
                "SEARXNG_TRANSPORT_FAILED",
                network_call_performed=attempted,
            ) from exc

    transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    transport.configured_endpoint_ref = configured.endpoint_ref  # type: ignore[attr-defined]
    return transport


def _loopback_json_get(
    *,
    host: str,
    port: int,
    path: str,
    timeout_seconds: float,
    max_response_bytes: int,
) -> tuple[int, str, bytes]:
    request_bytes = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Accept: application/json\r\n"
        "Accept-Encoding: identity\r\n"
        "User-Agent: ultimate-ai-agent-searxng-search/1\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")
    with socket.create_connection((host, port), timeout=timeout_seconds) as connection:
        connection.settimeout(timeout_seconds)
        connection.sendall(request_bytes)
        raw = bytearray()
        header_end = -1
        while header_end < 0:
            chunk = connection.recv(4096)
            if not chunk:
                break
            raw.extend(chunk)
            header_end = raw.find(b"\r\n\r\n")
            if len(raw) > 32_768:
                raise SearxngSearchTransportError(
                    "SEARXNG_RESPONSE_HEADERS_TOO_LARGE",
                    network_call_performed=True,
                )
        if header_end < 0:
            raise SearxngSearchTransportError(
                "SEARXNG_RESPONSE_HEADERS_INVALID",
                network_call_performed=True,
            )
        header_bytes = bytes(raw[:header_end])
        body = bytearray(raw[header_end + 4 :])
        status, headers = _parse_response_headers(header_bytes)
        if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
            raise SearxngSearchTransportError(
                "SEARXNG_RESPONSE_ENCODING_DENIED",
                network_call_performed=True,
            )
        if headers.get("transfer-encoding", "").lower() not in {"", "identity"}:
            raise SearxngSearchTransportError(
                "SEARXNG_TRANSFER_ENCODING_DENIED",
                network_call_performed=True,
            )
        while len(body) <= max_response_bytes:
            chunk = connection.recv(min(4096, max_response_bytes + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
        if len(body) > max_response_bytes:
            raise SearxngSearchTransportError(
                "SEARXNG_RESPONSE_TOO_LARGE",
                network_call_performed=True,
            )
    return status, headers.get("content-type", ""), bytes(body)


def _parse_response_headers(header_bytes: bytes) -> tuple[int, dict[str, str]]:
    try:
        lines = header_bytes.decode("iso-8859-1").split("\r\n")
        status_parts = lines[0].split(None, 2)
        status = int(status_parts[1])
    except (IndexError, UnicodeDecodeError, ValueError) as exc:
        raise SearxngSearchTransportError(
            "SEARXNG_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        ) from exc
    if len(status_parts) < 2 or not status_parts[0].startswith("HTTP/"):
        raise SearxngSearchTransportError(
            "SEARXNG_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        )
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            raise SearxngSearchTransportError(
                "SEARXNG_RESPONSE_HEADERS_INVALID",
                network_call_performed=True,
            )
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return status, headers


def build_searxng_search_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=SEARXNG_SEARCH_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="SearXNG governed read-only search",
        description="Run one bounded read-only public-web discovery request through the web gateway.",
        examples=["Discover a bounded set of public source candidates."],
        anti_examples=[
            "Do not browse interactively, authenticate, download, or mutate."
        ],
        input_schema={
            "type": "object",
            "required": ["query", "max_results"],
            "properties": {
                "query": {"type": "string", "maxLength": 240},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["evidence", "transport_receipt"],
            "additionalProperties": False,
        },
        input_modes=["ephemeral_query"],
        output_modes=["bounded_untrusted_evidence", "redacted_receipt"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.high,
        authority_level=CapabilityAuthorityLevel.read_only,
        approval_required=True,
        deterministic=False,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=True,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        runtime_policy=RuntimePolicy(
            timeout_seconds=15,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            approval_required=True,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.read,
        ),
    )


def searxng_search_snapshot_from_state(
    state: WebProviderCapabilityState,
) -> CapabilityAvailabilitySnapshot:
    if (
        state.provider_ref != SEARXNG_SEARCH_PROVIDER_REF
        or state.deployment != WebProviderDeploymentKind.searxng_self_hosted
        or state.operation != WebProviderOperation.search
    ):
        raise ValueError("SEARXNG_CAPABILITY_STATE_SCOPE_MISMATCH")
    return build_capability_availability_snapshot(
        snapshot_ref=stable_web_hybrid_ref(
            "capability-availability-ref",
            {
                "state_ref": state.state_ref,
                "capability_ref": SEARXNG_SEARCH_CAPABILITY_REF,
            },
        ),
        capability_ref=SEARXNG_SEARCH_CAPABILITY_REF,
        provider_ref=state.provider_ref,
        adapter_ref=SEARXNG_SEARCH_ADAPTER_REF,
        catalog_status=state.catalog_status,
        compatibility_status=state.compatibility_status,
        configuration_status=state.configuration_status,
        health_status=state.health_status,
        authority_posture=state.authority_posture,
        resource_status=state.resource_status,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=state.safe_disable_status,
        checked_at=state.observed_at,
        expires_at=state.expires_at,
        freshness_status=state.freshness_status,
        declared_or_observed_version_ref=state.version_ref,
        reason_codes=list(state.reason_codes),
        blocker_codes=list(state.blocker_codes),
        evidence_refs=[state.state_ref],
        source_ref=state.state_ref,
        safe_summary=(
            "SearXNG environment posture is observed separately from exact request authority."
        ),
    )


def execute_searxng_search(
    request: SearxngSearchRequest,
    *,
    capability_state: WebProviderCapabilityState,
    approval_authority: LocalApprovalAuthority,
    authority_leases: Sequence[AuthorityLease],
    transport: SearxngTransport | None = None,
    endpoint: SearxngConfiguredEndpoint | None = None,
    evaluated_at: datetime | None = None,
) -> SearxngSearchExecutionResult:
    """Evaluate every exact gate and, only if all allow, perform one search."""

    now = evaluated_at or utc_now()
    snapshot = searxng_search_snapshot_from_state(capability_state)
    manifest = build_searxng_search_capability_manifest()
    task = TaskEnvelope(
        task_id=request.task_ref,
        user_request="Execute one exact governed read-only discovery request.",
        objective="Return bounded untrusted source candidates with redacted receipts.",
        selected_capability_ids=[SEARXNG_SEARCH_CAPABILITY_REF],
        context={"approval_ref": request.approval_ref} if request.approval_ref else {},
    )
    policy_context: dict[str, Any] = {
        "coordination_mode": CoordinationMode.direct_tool.value,
    }
    if request.approval_ref:
        policy_context["approval_ref"] = request.approval_ref
    local_approval_decision = approval_authority.validate_approval(
        manifest,
        task,
        policy_context,
    )
    policy_decision = PolicyEngine(approval_authority=approval_authority).can_execute(
        manifest, task, policy_context
    )

    exact_resource_refs = _exact_authority_resource_refs(request)
    authority_action = AuthorityActionRequest(
        action_ref=stable_web_hybrid_ref(
            "authority-action-ref",
            {"request_ref": request.request_ref, "task_ref": request.task_ref},
        ),
        domain=AuthorityDomain.browser,
        capability=AuthorityCapability.read,
        safe_summary="Evaluate one exact SearXNG read-only search attempt.",
        resource_refs=list(exact_resource_refs),
        capability_ref=SEARXNG_SEARCH_CAPABILITY_REF,
        lane_ref=SEARXNG_SEARCH_LANE_REF,
        adapter_ref=SEARXNG_SEARCH_ADAPTER_REF,
        rollback_ref="rollback-ref:web-access:searxng-search:stop-local-stack",
        safe_disable_ref="safe-disable-ref:web-access:searxng-search",
    )
    observed_authority_decision = evaluate_authority_request(
        authority_action,
        list(authority_leases),
        now=now,
    )
    authority_decision = (
        observed_authority_decision
        if _decision_has_exact_resource_scope(
            observed_authority_decision,
            authority_leases,
            exact_resource_refs,
        )
        else None
    )

    invocation_request = CapabilityInvocationRequest(
        request_ref=request.request_ref,
        snapshot_ref=snapshot.snapshot_ref,
        capability_ref=SEARXNG_SEARCH_CAPABILITY_REF,
        provider_ref=SEARXNG_SEARCH_PROVIDER_REF,
        adapter_ref=SEARXNG_SEARCH_ADAPTER_REF,
        task_ref=request.task_ref,
        approval_ref=request.approval_ref,
        authority_lease_required=True,
        local_approval_required=True,
        idempotency_posture=IdempotencyPosture.not_required,
        expected_execution_receipt_ref=request.expected_execution_receipt_ref,
    )
    invocation_decision = evaluate_capability_invocation(
        request=invocation_request,
        snapshot=snapshot,
        policy_decision=policy_decision,
        authority_decision=authority_decision,
        local_approval_decision=local_approval_decision,
        evaluated_at=now,
    )
    if invocation_decision.outcome != InvocationDecisionOutcome.allow:
        receipt = _transport_receipt(
            request=request,
            invocation_decision=invocation_decision,
            status=WebProviderTransportStatus.blocked,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *invocation_decision.blocker_codes,
                        *invocation_decision.reason_codes,
                    )
                )
            ),
            network_call_performed=False,
            evidence=(),
            created_at=now,
        )
        return _execution_result(
            request=request,
            invocation_decision=invocation_decision,
            receipt=receipt,
            evidence=(),
            reason_codes=tuple(invocation_decision.reason_codes),
            blocker_codes=tuple(invocation_decision.blocker_codes),
        )

    selected_transport = transport or build_loopback_searxng_transport(endpoint)
    adapter = _SearxngSearchAdapter(
        search_request=request,
        invocation_decision=invocation_decision,
        transport=selected_transport,
    )
    gateway = WebAccessGateway(
        policy=WebAccessPolicy(allow_searxng_search=True),
        adapters={WebAccessRequestKind.SEARCH: adapter},
    )
    gateway_result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.SEARCH,
            query=request.query,
            method="GET",
            authority_mode=WebAccessAuthorityMode.READ_ONLY,
            network_lane=WebAccessNetworkLane.AGENT_PUBLIC_WEB,
            metadata={
                "page": request.page,
                "max_results": request.max_results,
                "category": request.category.value,
                "language": request.language.value,
                "safe_search": request.safe_search,
            },
            request_id=request.request_ref,
        )
    )
    payload = (
        gateway_result.evidence_bundle.payload
        if gateway_result.evidence_bundle is not None
        else {}
    )
    status = _transport_status(payload, gateway_result.status)
    evidence = (
        tuple(
            SearxngSearchEvidenceItem.model_validate(item)
            for item in payload.get("results", ())
            if isinstance(item, Mapping)
        )
        if status
        in {WebProviderTransportStatus.succeeded, WebProviderTransportStatus.simulated}
        else ()
    )
    reason_codes = _safe_reason_codes(payload.get("reason_codes"))
    network_call_performed = payload.get("network_call_performed") is True
    receipt = _transport_receipt(
        request=request,
        invocation_decision=invocation_decision,
        status=status,
        reason_codes=reason_codes,
        network_call_performed=network_call_performed,
        evidence=evidence,
        created_at=now,
    )
    return _execution_result(
        request=request,
        invocation_decision=invocation_decision,
        receipt=receipt,
        evidence=(
            evidence
            if status
            in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            else ()
        ),
        reason_codes=reason_codes,
        blocker_codes=()
        if status == WebProviderTransportStatus.succeeded
        else reason_codes,
    )


class _SearxngSearchAdapter:
    adapter_kind = WebAccessAdapterKind.SEARCH_API

    def __init__(
        self,
        *,
        search_request: SearxngSearchRequest,
        invocation_decision: CapabilityInvocationDecision,
        transport: SearxngTransport,
    ) -> None:
        self._search_request = search_request
        self._invocation_decision = invocation_decision
        self._transport = transport
        self._use_lock = threading.Lock()
        self._used = False

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        with self._use_lock:
            if self._used:
                return _adapter_failure(
                    "SEARXNG_INVOCATION_DECISION_REPLAY_DENIED",
                    False,
                )
            self._used = True
        invocation_scope_matches = (
            self._invocation_decision.outcome == InvocationDecisionOutcome.allow
            and self._invocation_decision.cache_posture == "not_cacheable"
            and self._invocation_decision.request_ref
            == self._search_request.request_ref
            and self._invocation_decision.capability_ref
            == SEARXNG_SEARCH_CAPABILITY_REF
            and self._invocation_decision.provider_ref == SEARXNG_SEARCH_PROVIDER_REF
            and self._invocation_decision.adapter_ref == SEARXNG_SEARCH_ADAPTER_REF
            and self._invocation_decision.authority_decision_ref is not None
            and self._invocation_decision.approval_decision_ref is not None
        )
        if (
            not decision.allowed
            or request.request_id != self._search_request.request_ref
            or not invocation_scope_matches
        ):
            return _adapter_failure("SEARXNG_GATEWAY_SCOPE_MISMATCH", False)
        live_transport = bool(
            getattr(self._transport, "real_world_transport_performed", False)
        )
        try:
            payload = self._transport(self._search_request)
            evidence = _normalize_search_results(
                payload,
                limit=self._search_request.max_results,
            )
        except SearxngSearchTransportError as exc:
            return _adapter_failure(
                exc.code,
                exc.network_call_performed and live_transport,
            )
        except Exception:  # noqa: BLE001 - provider boundary must not leak details.
            return _adapter_failure("SEARXNG_TRANSPORT_FAILED", live_transport)

        status = (
            WebProviderTransportStatus.succeeded
            if live_transport
            else WebProviderTransportStatus.simulated
        )
        reason = (
            "SEARXNG_SEARCH_COMPLETED"
            if evidence
            else "SEARXNG_SEARCH_COMPLETED_NO_RESULTS"
        )
        return {
            "allowed": True,
            "status": status.value,
            "summary": "SearXNG returned bounded untrusted search evidence.",
            "reason_codes": (reason,),
            "results": [item.model_dump(mode="json") for item in evidence],
            "sources": [
                SourceMetadata(
                    url=item.url,
                    final_url=item.url,
                    host=item.host,
                    source_type="search_result",
                    authority="untrusted_search_evidence",
                    allowed_methods=("GET",),
                    content_untrusted=True,
                    notes=("instructions_denied", "not_fetched_by_search_lane"),
                )
                for item in evidence
            ],
            "network_call_performed": live_transport,
            "raw_query_stored": False,
            "raw_provider_payload_stored": False,
        }


def _adapter_failure(code: str, network_call_performed: bool) -> Mapping[str, Any]:
    return {
        "allowed": False,
        "status": WebProviderTransportStatus.failed.value,
        "summary": "SearXNG search failed closed with no provider payload retained.",
        "reason_codes": (code,),
        "results": [],
        "sources": [],
        "network_call_performed": network_call_performed,
        "raw_query_stored": False,
        "raw_provider_payload_stored": False,
    }


def _normalize_search_results(
    payload: Mapping[str, Any],
    *,
    limit: int,
) -> tuple[SearxngSearchEvidenceItem, ...]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise SearxngSearchTransportError(
            "SEARXNG_RESULTS_LIST_REQUIRED",
            network_call_performed=True,
        )
    normalized: list[SearxngSearchEvidenceItem] = []
    seen: set[str] = set()
    for raw in raw_results:
        if not isinstance(raw, Mapping):
            continue
        url = raw.get("url")
        if not isinstance(url, str) or len(url) > 2048:
            continue
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
        if not _public_result_host(host):
            continue
        source_ref = _source_ref(url)
        if source_ref in seen:
            continue
        title = _bounded_untrusted_text(raw.get("title"), limit=240)
        snippet = _bounded_untrusted_text(
            raw.get("content", raw.get("snippet", "")),
            limit=500,
        )
        try:
            item = SearxngSearchEvidenceItem(
                source_ref=source_ref,
                url=url,
                host=host,
                title=title,
                snippet=snippet,
            )
        except ValueError:
            continue
        normalized.append(item)
        seen.add(source_ref)
        if len(normalized) >= limit:
            break
    return tuple(normalized)


def _public_result_host(host: str) -> bool:
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return "." in host and not host.endswith(".internal")


def _bounded_untrusted_text(value: Any, *, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    normalized = "".join(
        char if ord(char) >= 32 and ord(char) != 127 else " " for char in value
    ).split()
    return " ".join(normalized)[:limit]


def _source_ref(url: str) -> str:
    return f"web-source-ref:sha256:{hashlib.sha256(url.encode('utf-8')).hexdigest()}"


def _exact_authority_resource_refs(
    request: SearxngSearchRequest,
) -> tuple[str, ...]:
    return (
        request.request_ref,
        request.task_ref,
        SEARXNG_SEARCH_CAPABILITY_REF,
        SEARXNG_SEARCH_PROVIDER_REF,
        SEARXNG_SEARCH_ADAPTER_REF,
    )


def _decision_has_exact_resource_scope(
    decision: AuthorityPolicyDecision,
    leases: Sequence[AuthorityLease],
    exact_resource_refs: tuple[str, ...],
) -> bool:
    if not decision.lease_ref:
        return False
    lease = next(
        (item for item in leases if item.lease_ref == decision.lease_ref), None
    )
    if lease is None:
        return False
    required = set(exact_resource_refs)
    for constraint in lease.authority_constraints:
        if (
            AuthorityConstraintKind(constraint.kind)
            != AuthorityConstraintKind.resource_refs
        ):
            continue
        if set(constraint.allowed_refs) != required:
            continue
        return constraint.constraint_ref in decision.applied_constraint_refs
    return False


def _transport_status(
    payload: Mapping[str, Any],
    gateway_status: WebAccessPolicyStatus,
) -> WebProviderTransportStatus:
    if gateway_status != WebAccessPolicyStatus.ALLOWED:
        raw = payload.get("status")
        if raw == WebProviderTransportStatus.failed.value:
            return WebProviderTransportStatus.failed
        return WebProviderTransportStatus.blocked
    try:
        return WebProviderTransportStatus(str(payload.get("status")))
    except ValueError:
        return WebProviderTransportStatus.failed


def _safe_reason_codes(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ("SEARXNG_PROVIDER_RESULT_INVALID",)
    codes = tuple(dict.fromkeys(str(item) for item in value))
    if not codes or any(not _SAFE_CODE.fullmatch(code) for code in codes):
        return ("SEARXNG_PROVIDER_RESULT_INVALID",)
    return codes


def _transport_receipt(
    *,
    request: SearxngSearchRequest,
    invocation_decision: CapabilityInvocationDecision,
    status: WebProviderTransportStatus,
    reason_codes: tuple[str, ...],
    network_call_performed: bool,
    evidence: tuple[SearxngSearchEvidenceItem, ...],
    created_at: datetime,
) -> WebProviderTransportReceipt:
    response_ref = (
        stable_web_hybrid_ref(
            "provider-response-receipt-hash-ref",
            [item.model_dump(mode="json") for item in evidence],
        )
        if status
        in {WebProviderTransportStatus.succeeded, WebProviderTransportStatus.simulated}
        else None
    )
    return WebProviderTransportReceipt(
        receipt_ref=stable_web_hybrid_ref(
            "web-provider-transport-receipt-ref",
            {
                "request_ref": request.request_ref,
                "invocation_decision_ref": invocation_decision.decision_ref,
                "status": status.value,
                "response_ref": response_ref,
            },
        ),
        request_ref=request.request_ref,
        provider_ref=SEARXNG_SEARCH_PROVIDER_REF,
        deployment=WebProviderDeploymentKind.searxng_self_hosted,
        operation=WebProviderOperation.search,
        configured_endpoint_ref=SEARXNG_SEARCH_ENDPOINT_REF,
        target_method="GET",
        provider_transport_method=WebProviderTransportMethod.get,
        request_schema_ref=SEARXNG_SEARCH_REQUEST_SCHEMA_REF,
        status=status,
        response_receipt_hash_ref=response_ref,
        authority_decision_ref=(
            invocation_decision.authority_decision_ref
            or "authority-decision-ref:searxng-search:missing"
        ),
        approval_decision_ref=(
            invocation_decision.approval_decision_ref
            or "approval-decision-ref:searxng-search:missing"
        ),
        budget_decision_ref=SEARXNG_SEARCH_NOT_METERED_BUDGET_REF,
        reason_codes=reason_codes,
        network_call_performed=network_call_performed,
        created_at=created_at,
    )


def _execution_result(
    *,
    request: SearxngSearchRequest,
    invocation_decision: CapabilityInvocationDecision,
    receipt: WebProviderTransportReceipt,
    evidence: tuple[SearxngSearchEvidenceItem, ...],
    reason_codes: tuple[str, ...],
    blocker_codes: tuple[str, ...],
) -> SearxngSearchExecutionResult:
    return SearxngSearchExecutionResult(
        request_ref=request.request_ref,
        task_ref=request.task_ref,
        invocation_decision=invocation_decision,
        transport_receipt=receipt,
        gateway_audit_ref=stable_web_hybrid_ref(
            "web-access-audit-ref",
            {
                "request_ref": request.request_ref,
                "invocation_decision_ref": invocation_decision.decision_ref,
                "transport_receipt_ref": receipt.receipt_ref,
            },
        ),
        status=receipt.status,
        evidence=evidence,
        execution_succeeded=receipt.status == WebProviderTransportStatus.succeeded,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
    )


__all__ = [
    "SEARXNG_SEARCH_ADAPTER_REF",
    "SEARXNG_SEARCH_CAPABILITY_REF",
    "SEARXNG_SEARCH_DEFAULT_ENDPOINT",
    "SEARXNG_SEARCH_ENDPOINT_REF",
    "SEARXNG_SEARCH_LANE_REF",
    "SEARXNG_SEARCH_PROVIDER_REF",
    "SearxngConfiguredEndpoint",
    "SearxngSearchEvidenceItem",
    "SearxngSearchExecutionResult",
    "SearxngSearchRequest",
    "SearxngSearchTransportError",
    "build_loopback_searxng_transport",
    "build_searxng_search_capability_manifest",
    "execute_searxng_search",
    "searxng_search_snapshot_from_state",
]
