from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.web_access.contracts import (
    WebAccessAdapterKind,
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)
from ultimate_ai_agent.core.web_access.gateway import WebAccessGateway
from ultimate_ai_agent.core.web_access.policy import WebAccessPolicy


BROWSER_OBSERVE_ONLY_ADAPTER_REF = "browser-adapter:m74-observe-only"
BROWSER_OBSERVE_ONLY_ADAPTER_NAME = "browser_observe_only_adapter"
BROWSER_OBSERVE_ONLY_ADAPTER_DOCS = [
    "docs/browser/BROWSER_OBSERVE_ONLY_ADAPTER.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_POLICY.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_RESULT_CONTRACT.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_OBSERVE_ONLY_RECEIPT_PLAN.md",
    "docs/browser/M74_TO_M75_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
DEFAULT_BROWSER_OBSERVE_TEXT_PREVIEW_CHARS = 2048

_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)\b(api[_-]?key|authorization|cookie|password|secret|token|client[_-]?secret)\b\s*[:=]\s*[^\s]+"
)
_BEARER_TOKEN_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}")
_PRIVATE_KEY_MARKER_RE = re.compile(r"-----" + r"BEGIN [A-Z ]*PRIVATE KEY" + r"-----")
_HIGH_ENTROPY_RE = re.compile(r"\b[A-Za-z0-9_/-]{32,}\b")


class BrowserObserveOnlyStatus(str, Enum):
    observation_ready = "observation_ready"
    denied = "denied"
    transport_unavailable = "transport_unavailable"


class _BrowserObserveOnlyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BrowserObserveOnlyRedactionSummary(_BrowserObserveOnlyModel):
    redaction_count: int = 0
    categories: list[str] = Field(default_factory=list)
    sensitive_values_returned: bool = False

    @model_validator(mode="after")
    def validate_summary(self) -> Any:
        allowed = {"secret_assignment", "bearer_token", "private_key_marker", "high_entropy_token"}
        if self.redaction_count < 0:
            raise ValueError("BROWSER_OBSERVE_REDACTION_COUNT_INVALID")
        if any(category not in allowed for category in self.categories):
            raise ValueError("BROWSER_OBSERVE_REDACTION_CATEGORY_INVALID")
        if self.sensitive_values_returned:
            raise ValueError("BROWSER_OBSERVE_REDACTION_SUMMARY_MUST_NOT_RETURN_SENSITIVE_VALUES")
        return self


class BrowserObserveOnlyPolicy(_BrowserObserveOnlyModel):
    policy_ref: str = "browser-observe-policy:m74-observe-only"
    observe_only_allowed: bool = True
    injected_observation_required: bool = True
    redaction_required: bool = True
    safe_ref_only: bool = True
    deterministic: bool = True
    browser_automation_allowed: bool = False
    navigation_allowed: bool = False
    click_allowed: bool = False
    form_fill_allowed: bool = False
    screenshot_allowed: bool = False
    raw_dom_allowed: bool = False
    authenticated_profile_allowed: bool = False
    cookies_or_credentials_allowed: bool = False
    download_or_upload_allowed: bool = False
    remote_browser_allowed: bool = False
    network_interception_allowed: bool = False
    network_call_allowed: bool = False
    model_call_allowed: bool = False
    tool_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_change_allowed: bool = False
    production_authority_allowed: bool = False
    max_text_preview_chars: int = DEFAULT_BROWSER_OBSERVE_TEXT_PREVIEW_CHARS
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        for field_name, reason in _POLICY_REQUIRED_TRUE:
            if not getattr(self, field_name):
                raise ValueError(reason)
        for field_name, reason in _POLICY_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if not 1 <= self.max_text_preview_chars <= DEFAULT_BROWSER_OBSERVE_TEXT_PREVIEW_CHARS:
            raise ValueError("BROWSER_OBSERVE_TEXT_PREVIEW_LIMIT_INVALID")
        _validate_browser_observe_metadata(self.metadata)
        return self


class BrowserObserveOnlyRequest(_BrowserObserveOnlyModel):
    request_ref: str
    target_ref: str
    safe_url_ref: str
    safe_summary: str
    approval_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    navigation_requested: bool = False
    click_requested: bool = False
    form_fill_requested: bool = False
    screenshot_requested: bool = False
    raw_dom_requested: bool = False
    authenticated_profile_requested: bool = False
    cookies_or_credentials_requested: bool = False
    download_or_upload_requested: bool = False
    remote_browser_requested: bool = False
    network_interception_requested: bool = False
    network_call_requested: bool = False
    model_call_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    production_authority_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.target_ref, "target_ref"),
            (self.safe_url_ref, "safe_url_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if self.approval_ref is not None and not self.approval_ref.startswith("approval_test"):
            _validate_m61_ref(self.approval_ref, "approval_ref")
        for ref in self.authority_refs:
            _validate_m61_ref(ref, "authority_ref")
        return self


class BrowserObserveOnlyObservation(_BrowserObserveOnlyModel):
    title: str
    safe_url_ref: str
    text_preview: str
    visible_text_bytes: int
    raw_dom: str | None = None
    screenshot_bytes: bytes | None = None
    raw_absolute_url: str | None = None
    authenticated_profile_used: bool = False
    cookies_or_credentials_used: bool = False
    navigation_performed: bool = False
    click_performed: bool = False
    form_fill_performed: bool = False
    network_interception_performed: bool = False
    network_call_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_safe_payload(self.title)
        _validate_m61_ref(self.safe_url_ref, "safe_url_ref")
        if self.visible_text_bytes < 0:
            raise ValueError("BROWSER_OBSERVE_VISIBLE_TEXT_BYTES_INVALID")
        return self


class BrowserObserveOnlyOutput(_BrowserObserveOnlyModel):
    output_ref: str
    request_ref: str
    target_ref: str
    safe_url_ref: str
    status: BrowserObserveOnlyStatus
    observe_allowed: bool
    observe_performed: bool = False
    safe_title: str = ""
    redacted_text_preview: str = ""
    redaction_summary: BrowserObserveOnlyRedactionSummary = Field(
        default_factory=BrowserObserveOnlyRedactionSummary
    )
    preview_truncated: bool = False
    visible_text_bytes: int = 0
    browser_automation_performed: bool = False
    navigation_performed: bool = False
    click_performed: bool = False
    form_fill_performed: bool = False
    screenshot_returned: bool = False
    screenshot_stored: bool = False
    raw_dom_returned: bool = False
    raw_dom_stored: bool = False
    raw_absolute_url_returned: bool = False
    authenticated_profile_used: bool = False
    cookies_or_credentials_used: bool = False
    download_or_upload_performed: bool = False
    remote_browser_control_performed: bool = False
    network_interception_performed: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_used: bool = False
    control_center_control_used: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_message: str

    @model_validator(mode="after")
    def validate_output(self) -> Any:
        for value, field_name in [
            (self.output_ref, "output_ref"),
            (self.request_ref, "request_ref"),
            (self.target_ref, "target_ref"),
            (self.safe_url_ref, "safe_url_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_title)
        _validate_safe_payload(self.safe_message)
        if not self.reason_codes:
            raise ValueError("BROWSER_OBSERVE_REASON_CODE_REQUIRED")
        if self.status == BrowserObserveOnlyStatus.observation_ready:
            if not self.observe_allowed or not self.observe_performed:
                raise ValueError("BROWSER_OBSERVE_OUTPUT_INVALID")
            if _contains_unredacted_sensitive_preview(self.redacted_text_preview):
                raise ValueError("BROWSER_OBSERVE_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT")
        if self.status != BrowserObserveOnlyStatus.observation_ready and self.observe_allowed:
            raise ValueError("DENIED_BROWSER_OBSERVE_CANNOT_BE_ALLOWED")
        for field_name, reason in _OUTPUT_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("BROWSER_OBSERVE_SIDE_EFFECTS_DENIED")
        return self


BrowserObserveTransport = Callable[[BrowserObserveOnlyRequest, BrowserObserveOnlyPolicy], BrowserObserveOnlyObservation]


class BrowserObserveOnlyAdapter:
    def __init__(self, policy: BrowserObserveOnlyPolicy | None = None) -> None:
        self.policy = policy or BrowserObserveOnlyPolicy()

    def observe(
        self,
        request: BrowserObserveOnlyRequest,
        *,
        observe_transport: BrowserObserveTransport | None = None,
    ) -> BrowserObserveOnlyOutput:
        return build_browser_observe_only_output_via_web_access_gateway(
            request=request,
            policy=self.policy,
            observe_transport=observe_transport,
        )


def _build_browser_observe_only_output(
    *,
    request: BrowserObserveOnlyRequest,
    policy: BrowserObserveOnlyPolicy | None = None,
    observe_transport: BrowserObserveTransport | None,
) -> BrowserObserveOnlyOutput:
    active_policy = policy or BrowserObserveOnlyPolicy()
    denied_reasons = browser_observe_policy_reason_codes(active_policy)
    denied_reasons.extend(browser_observe_request_reason_codes(request))
    denied_reasons = list(dict.fromkeys(denied_reasons))
    if denied_reasons:
        return _decision_output(
            request=request,
            status=BrowserObserveOnlyStatus.denied,
            observe_allowed=False,
            reason_codes=denied_reasons,
            safe_message="BROWSER_OBSERVE_ONLY_REQUEST_DENIED",
        )
    if observe_transport is None:
        return _decision_output(
            request=request,
            status=BrowserObserveOnlyStatus.transport_unavailable,
            observe_allowed=False,
            reason_codes=["BROWSER_OBSERVE_TRANSPORT_REQUIRED"],
            safe_message="BROWSER_OBSERVE_ONLY_TRANSPORT_REQUIRED",
        )

    observation = BrowserObserveOnlyObservation.model_validate(observe_transport(request, active_policy))
    observation_reasons = browser_observe_observation_reason_codes(observation)
    if observation_reasons:
        return _decision_output(
            request=request,
            status=BrowserObserveOnlyStatus.denied,
            observe_allowed=False,
            reason_codes=observation_reasons,
            safe_message="BROWSER_OBSERVE_ONLY_OBSERVATION_DENIED",
        )

    preview_text = observation.text_preview[: active_policy.max_text_preview_chars]
    redacted_preview, redaction_summary = _redact(preview_text)
    return BrowserObserveOnlyOutput(
        output_ref=f"browser-observe-output:{_ref_suffix(request.request_ref)}",
        request_ref=request.request_ref,
        target_ref=request.target_ref,
        safe_url_ref=observation.safe_url_ref,
        status=BrowserObserveOnlyStatus.observation_ready,
        observe_allowed=True,
        observe_performed=True,
        safe_title=observation.title,
        redacted_text_preview=redacted_preview,
        redaction_summary=redaction_summary,
        preview_truncated=len(observation.text_preview) > active_policy.max_text_preview_chars,
        visible_text_bytes=observation.visible_text_bytes,
        reason_codes=[
            "BROWSER_OBSERVE_ONLY_ADAPTER_OUTPUT",
            "M74_OBSERVE_ONLY_ADAPTER",
            "M75_REMAINS_FUTURE",
        ],
        safe_message="BROWSER_OBSERVE_ONLY_REDACTED_PREVIEW_RETURNED",
    )


@dataclass(frozen=True)
class _BrowserObserveOnlyWebAccessAdapter:
    observe_request: BrowserObserveOnlyRequest
    policy: BrowserObserveOnlyPolicy
    observe_transport: BrowserObserveTransport | None
    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.LOCAL_BROWSER_OBSERVE

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        if request.kind != WebAccessRequestKind.BROWSER_OBSERVE:
            output = _decision_output(
                request=self.observe_request,
                status=BrowserObserveOnlyStatus.denied,
                observe_allowed=False,
                reason_codes=["BROWSER_OBSERVE_GATEWAY_KIND_MISMATCH"],
                safe_message="BROWSER_OBSERVE_ONLY_REQUEST_DENIED",
            )
            return _blocked_browser_observe_adapter_result(output)

        output = _build_browser_observe_only_output(
            request=self.observe_request,
            policy=self.policy,
            observe_transport=self.observe_transport,
        )
        if output.status != BrowserObserveOnlyStatus.observation_ready or not output.observe_allowed:
            return _blocked_browser_observe_adapter_result(output)

        return {
            "adapter_ref": "web-access-adapter:browser-observe-only.v1",
            "allowed": True,
            "status": output.status.value,
            "target_ref": output.target_ref,
            "safe_url_ref": output.safe_url_ref,
            "output": output.model_dump(mode="python"),
            "preview": output.redacted_text_preview,
            "source_refs": [
                {
                    "target_ref": output.target_ref,
                    "safe_url_ref": output.safe_url_ref,
                    "content_untrusted": True,
                }
            ],
        }


def build_browser_observe_only_output_via_web_access_gateway(
    *,
    request: BrowserObserveOnlyRequest,
    policy: BrowserObserveOnlyPolicy | None = None,
    observe_transport: BrowserObserveTransport | None,
) -> BrowserObserveOnlyOutput:
    """Route the M74 injected observe-only adapter through WebAccessGateway."""

    active_policy = policy or BrowserObserveOnlyPolicy()
    adapter = _BrowserObserveOnlyWebAccessAdapter(
        observe_request=request,
        policy=active_policy,
        observe_transport=observe_transport,
    )
    gateway = WebAccessGateway(
        policy=WebAccessPolicy(allow_browser_observe=True),
        adapters={WebAccessRequestKind.BROWSER_OBSERVE: adapter},
    )
    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.BROWSER_OBSERVE,
            method="GET",
            authority_mode=WebAccessAuthorityMode.BROWSER_OBSERVE_ONLY,
            network_lane=WebAccessNetworkLane.BROWSER_OBSERVE_ONLY,
            actor="browser_observe_adapter",
            session_id=request.request_ref,
            metadata={
                "adapter_ref": "web-access-adapter:browser-observe-only.v1",
                "browser_adapter_ref": BROWSER_OBSERVE_ONLY_ADAPTER_REF,
                "request_ref": request.request_ref,
                "target_ref": request.target_ref,
                "safe_url_ref": request.safe_url_ref,
                "request_body": False,
                "raw_dom": request.raw_dom_requested,
                "screenshot": request.screenshot_requested,
                "navigation": request.navigation_requested,
                "click": request.click_requested,
                "form_fill": request.form_fill_requested,
                "uses_auth": request.authenticated_profile_requested,
                "cookies": request.cookies_or_credentials_requested,
                "download": request.download_or_upload_requested,
                "upload": request.download_or_upload_requested,
                "network_interception": request.network_interception_requested,
                "network_call": request.network_call_requested,
                "model_call": request.model_call_requested,
                "tool_execution": request.tool_execution_requested,
                "memory_write": request.memory_write_requested,
                "context_injection": request.context_injection_requested,
                "backend_route": request.backend_route_requested,
                "control_center_control": request.control_center_control_requested,
                "production_authority": request.production_authority_requested,
            },
        )
    )
    output = _output_from_web_access_payload(result.evidence_bundle.payload if result.evidence_bundle else None)
    if output is not None:
        return output
    if result.status != WebAccessPolicyStatus.ALLOWED:
        return _decision_output(
            request=request,
            status=BrowserObserveOnlyStatus.denied,
            observe_allowed=False,
            reason_codes=_browser_observe_reasons_from_web_access_result(result.decision.reasons),
            safe_message="BROWSER_OBSERVE_ONLY_REQUEST_DENIED",
        )
    return _decision_output(
        request=request,
        status=BrowserObserveOnlyStatus.denied,
        observe_allowed=False,
        reason_codes=["BROWSER_OBSERVE_GATEWAY_OUTPUT_MISSING"],
        safe_message="BROWSER_OBSERVE_ONLY_REQUEST_DENIED",
    )


def _blocked_browser_observe_adapter_result(output: BrowserObserveOnlyOutput) -> Mapping[str, Any]:
    return {
        "adapter_ref": "web-access-adapter:browser-observe-only.v1",
        "allowed": False,
        "status": "denied",
        "reason_codes": output.reason_codes,
        "output": output.model_dump(mode="python"),
        "source_refs": [
            {
                "target_ref": output.target_ref,
                "safe_url_ref": output.safe_url_ref,
                "content_untrusted": True,
            }
        ],
    }


def _output_from_web_access_payload(payload: Mapping[str, Any] | None) -> BrowserObserveOnlyOutput | None:
    if not payload:
        return None
    output_payload = payload.get("output")
    if not isinstance(output_payload, Mapping):
        return None
    return BrowserObserveOnlyOutput.model_validate(output_payload)


def _browser_observe_reasons_from_web_access_result(reasons: tuple[str, ...]) -> list[str]:
    mapped: list[str] = []
    for reason in reasons:
        if reason.startswith("adapter_reason:"):
            mapped.append(_safe_reason(reason.split(":", 1)[1], "BROWSER_OBSERVE_GATEWAY_DENIED"))
        elif reason == "browser_observe_not_enabled":
            mapped.append("BROWSER_OBSERVE_GATEWAY_NOT_ENABLED")
        elif reason == "browser_observe_authority_mode_required":
            mapped.append("BROWSER_OBSERVE_AUTHORITY_MODE_REQUIRED")
        elif reason == "browser_observe_lane_required":
            mapped.append("BROWSER_OBSERVE_GATEWAY_LANE_REQUIRED")
        elif reason == "browser_observe_raw_url_denied":
            mapped.append("RAW_ABSOLUTE_URL_DENIED")
        elif reason == "browser_observe_safe_url_ref_required":
            mapped.append("BROWSER_OBSERVE_SAFE_REF_ONLY_REQUIRED")
        elif reason == "browser_observe_control_or_raw_content_denied":
            mapped.append("BROWSER_OBSERVE_CONTROL_OR_RAW_CONTENT_DENIED")
        elif reason == "browser_observe_navigation_denied":
            mapped.append("BROWSER_NAVIGATION_DENIED")
        elif reason == "browser_observe_click_denied":
            mapped.append("BROWSER_CLICK_DENIED")
        elif reason == "browser_observe_form_fill_denied":
            mapped.append("FORM_FILL_DENIED")
        elif reason == "browser_observe_screenshot_denied":
            mapped.append("SCREENSHOT_DENIED")
        elif reason == "browser_observe_raw_dom_denied":
            mapped.append("RAW_DOM_DENIED")
        elif reason == "browser_observe_authenticated_profile_denied":
            mapped.append("AUTHENTICATED_PROFILE_DENIED")
        elif reason == "browser_observe_cookies_or_credentials_denied":
            mapped.append("COOKIES_OR_CREDENTIALS_DENIED")
        elif reason == "browser_observe_download_or_upload_denied":
            mapped.append("DOWNLOAD_OR_UPLOAD_DENIED")
        elif reason == "browser_observe_network_interception_denied":
            mapped.append("NETWORK_INTERCEPTION_DENIED")
        elif reason == "browser_observe_network_call_denied":
            mapped.append("NETWORK_CALL_DENIED")
        elif reason == "browser_observe_model_call_denied":
            mapped.append("MODEL_CALL_DENIED")
        elif reason == "browser_observe_tool_execution_denied":
            mapped.append("TOOL_EXECUTION_DENIED")
        elif reason == "browser_observe_memory_write_denied":
            mapped.append("MEMORY_WRITE_DENIED")
        elif reason == "browser_observe_context_injection_denied":
            mapped.append("CONTEXT_INJECTION_DENIED")
        elif reason == "browser_observe_backend_route_denied":
            mapped.append("BACKEND_ROUTE_DENIED")
        elif reason == "browser_observe_control_center_control_denied":
            mapped.append("CONTROL_CENTER_CONTROL_DENIED")
        elif reason == "browser_observe_production_authority_denied":
            mapped.append("PRODUCTION_AUTHORITY_DENIED")
        elif reason == "browser_observe_request_body_denied":
            mapped.append("REQUEST_BODY_DENIED")
        elif reason.startswith("method_not_allowed:"):
            mapped.append("BROWSER_OBSERVE_NON_GET_METHOD_DENIED")
    return list(dict.fromkeys(mapped or ["BROWSER_OBSERVE_GATEWAY_DENIED"]))


def browser_observe_policy_reason_codes(policy: BrowserObserveOnlyPolicy) -> list[str]:
    payload = _model_payload(policy)
    reasons: list[str] = []
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not payload.get(field_name):
            reasons.append(reason)
    for field_name, reason in _POLICY_DENIALS:
        if payload.get(field_name):
            reasons.append(reason)
    try:
        BrowserObserveOnlyPolicy.model_validate(payload)
    except ValueError as exc:
        reasons.append(_safe_reason(str(exc), "BROWSER_OBSERVE_POLICY_INVALID"))
    return list(dict.fromkeys(reasons))


def browser_observe_request_reason_codes(request: BrowserObserveOnlyRequest) -> list[str]:
    payload = _model_payload(request)
    reasons: list[str] = []
    for field_name, reason in _REQUEST_DENIALS:
        if payload.get(field_name):
            reasons.append(reason)
    approval_ref = payload.get("approval_ref")
    if approval_ref:
        reasons.append("APPROVAL_REF_NOT_AUTHORITY")
        if str(approval_ref).startswith("approval_test"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    for ref in payload.get("authority_refs", []):
        if str(ref).startswith("approval_test"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
        if str(ref).split(":", 1)[0] in {
            "approval",
            "task-plan",
            "context-pack",
            "memory",
            "tool-intent",
            "model",
            "runtime",
            "openwebui",
            "control-center",
        }:
            reasons.append("AUTHORITY_REF_NOT_BROWSER_OBSERVE_AUTHORITY")
    if _has_secret_like_extra(payload, BrowserObserveOnlyRequest):
        reasons.append("SECRET_LIKE_BROWSER_OBSERVE_CONTENT_DENIED")
    try:
        BrowserObserveOnlyRequest.model_validate(payload)
        _validate_browser_observe_metadata(payload.get("metadata", {}))
    except ValueError as exc:
        reason = _safe_reason(str(exc), "BROWSER_OBSERVE_REQUEST_INVALID")
        if "SECRET_LIKE" in reason:
            reason = "SECRET_LIKE_BROWSER_OBSERVE_CONTENT_DENIED"
        reasons.append(reason)
    return list(dict.fromkeys(reasons))


def browser_observe_observation_reason_codes(observation: BrowserObserveOnlyObservation) -> list[str]:
    reasons: list[str] = []
    for field_name, reason in _OBSERVATION_DENIALS:
        if getattr(observation, field_name):
            reasons.append(reason)
    if observation.side_effects_performed:
        reasons.append("BROWSER_OBSERVE_SIDE_EFFECTS_DENIED")
    return list(dict.fromkeys(reasons))


def _decision_output(
    *,
    request: BrowserObserveOnlyRequest,
    status: BrowserObserveOnlyStatus,
    observe_allowed: bool,
    reason_codes: list[str],
    safe_message: str,
) -> BrowserObserveOnlyOutput:
    return BrowserObserveOnlyOutput(
        output_ref=f"browser-observe-output:{_ref_suffix(request.request_ref)}",
        request_ref=request.request_ref,
        target_ref=request.target_ref,
        safe_url_ref=request.safe_url_ref,
        status=status,
        observe_allowed=observe_allowed,
        reason_codes=reason_codes,
        safe_message=safe_message,
    )


def _redact(value: str) -> tuple[str, BrowserObserveOnlyRedactionSummary]:
    categories: list[str] = []
    redacted = value
    for pattern, replacement, category in [
        (_PRIVATE_KEY_MARKER_RE, "[REDACTED:PRIVATE_KEY_MARKER]", "private_key_marker"),
        (_BEARER_TOKEN_RE, "[REDACTED:BEARER_TOKEN]", "bearer_token"),
        (_SECRET_ASSIGNMENT_RE, "[REDACTED:SECRET_ASSIGNMENT]", "secret_assignment"),
        (_HIGH_ENTROPY_RE, "[REDACTED:HIGH_ENTROPY_TOKEN]", "high_entropy_token"),
    ]:
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            categories.extend([category] * count)
    return redacted, BrowserObserveOnlyRedactionSummary(
        redaction_count=len(categories),
        categories=categories,
    )


def _contains_unredacted_sensitive_preview(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in [
            _SECRET_ASSIGNMENT_RE,
            _BEARER_TOKEN_RE,
            _PRIVATE_KEY_MARKER_RE,
            _HIGH_ENTROPY_RE,
        ]
    )


def _validate_browser_observe_metadata(value: Any) -> None:
    if isinstance(value, str):
        _validate_safe_payload(value)
        return
    if isinstance(value, list):
        for item in value:
            _validate_browser_observe_metadata(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_safe_payload(str(key))
            _validate_browser_observe_metadata(item)
        return
    _validate_safe_payload(value)


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump(mode="python", round_trip=True)
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    return payload


def _has_secret_like_extra(payload: dict[str, Any], model_type: type[BaseModel]) -> bool:
    allowed = set(model_type.model_fields)
    for key, value in payload.items():
        if key in allowed:
            continue
        try:
            _validate_browser_observe_metadata({key: value})
        except ValueError:
            return True
    return False


def _safe_reason(value: str, fallback: str) -> str:
    reason = value.strip().split("\n", 1)[0]
    if reason.isupper() and " " not in reason:
        return reason
    return fallback


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


_POLICY_REQUIRED_TRUE = [
    ("observe_only_allowed", "BROWSER_OBSERVE_ONLY_REQUIRED"),
    ("injected_observation_required", "BROWSER_OBSERVE_TRANSPORT_REQUIRED"),
    ("redaction_required", "BROWSER_OBSERVE_REDACTION_REQUIRED"),
    ("safe_ref_only", "BROWSER_OBSERVE_SAFE_REF_ONLY_REQUIRED"),
    ("deterministic", "BROWSER_OBSERVE_DETERMINISTIC_REQUIRED"),
]

_POLICY_DENIALS = [
    ("browser_automation_allowed", "BROWSER_AUTOMATION_DENIED"),
    ("navigation_allowed", "BROWSER_NAVIGATION_DENIED"),
    ("click_allowed", "BROWSER_CLICK_DENIED"),
    ("form_fill_allowed", "FORM_FILL_DENIED"),
    ("screenshot_allowed", "SCREENSHOT_DENIED"),
    ("raw_dom_allowed", "RAW_DOM_DENIED"),
    ("authenticated_profile_allowed", "AUTHENTICATED_PROFILE_DENIED"),
    ("cookies_or_credentials_allowed", "COOKIES_OR_CREDENTIALS_DENIED"),
    ("download_or_upload_allowed", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_allowed", "REMOTE_BROWSER_DENIED"),
    ("network_interception_allowed", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_allowed", "NETWORK_CALL_DENIED"),
    ("model_call_allowed", "MODEL_CALL_DENIED"),
    ("tool_execution_allowed", "TOOL_EXECUTION_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]

_REQUEST_DENIALS = [
    ("navigation_requested", "BROWSER_NAVIGATION_DENIED"),
    ("click_requested", "BROWSER_CLICK_DENIED"),
    ("form_fill_requested", "FORM_FILL_DENIED"),
    ("screenshot_requested", "SCREENSHOT_DENIED"),
    ("raw_dom_requested", "RAW_DOM_DENIED"),
    ("authenticated_profile_requested", "AUTHENTICATED_PROFILE_DENIED"),
    ("cookies_or_credentials_requested", "COOKIES_OR_CREDENTIALS_DENIED"),
    ("download_or_upload_requested", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_requested", "REMOTE_BROWSER_DENIED"),
    ("network_interception_requested", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_requested", "NETWORK_CALL_DENIED"),
    ("model_call_requested", "MODEL_CALL_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_OBSERVATION_DENIALS = [
    ("raw_dom", "RAW_DOM_DENIED"),
    ("screenshot_bytes", "SCREENSHOT_BYTES_DENIED"),
    ("raw_absolute_url", "RAW_ABSOLUTE_URL_DENIED"),
    ("authenticated_profile_used", "AUTHENTICATED_PROFILE_DENIED"),
    ("cookies_or_credentials_used", "COOKIES_OR_CREDENTIALS_DENIED"),
    ("navigation_performed", "BROWSER_NAVIGATION_DENIED"),
    ("click_performed", "BROWSER_CLICK_DENIED"),
    ("form_fill_performed", "FORM_FILL_DENIED"),
    ("network_interception_performed", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_performed", "NETWORK_CALL_DENIED"),
]

_OUTPUT_DENIALS = [
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("navigation_performed", "BROWSER_NAVIGATION_DENIED"),
    ("click_performed", "BROWSER_CLICK_DENIED"),
    ("form_fill_performed", "FORM_FILL_DENIED"),
    ("screenshot_returned", "SCREENSHOT_DENIED"),
    ("screenshot_stored", "SCREENSHOT_DENIED"),
    ("raw_dom_returned", "RAW_DOM_DENIED"),
    ("raw_dom_stored", "RAW_DOM_DENIED"),
    ("raw_absolute_url_returned", "RAW_ABSOLUTE_URL_DENIED"),
    ("authenticated_profile_used", "AUTHENTICATED_PROFILE_DENIED"),
    ("cookies_or_credentials_used", "COOKIES_OR_CREDENTIALS_DENIED"),
    ("download_or_upload_performed", "DOWNLOAD_OR_UPLOAD_DENIED"),
    ("remote_browser_control_performed", "REMOTE_BROWSER_DENIED"),
    ("network_interception_performed", "NETWORK_INTERCEPTION_DENIED"),
    ("network_call_performed", "NETWORK_CALL_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_used", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_used", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
