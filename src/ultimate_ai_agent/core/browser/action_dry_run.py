from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
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


BROWSER_ACTION_DRY_RUN_PLANNER_REF = "browser-action-planner:m75-dry-run"
BROWSER_ACTION_DRY_RUN_PLANNER_NAME = "browser_action_dry_run_planner"
BROWSER_ACTION_DRY_RUN_PLANNER_DOCS = [
    "docs/browser/BROWSER_ACTION_DRY_RUN_PLANNER.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_POLICY.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_RESULT_CONTRACT.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_AUTHORITY_BOUNDARY.md",
    "docs/browser/BROWSER_ACTION_DRY_RUN_RECEIPT_PLAN.md",
    "docs/browser/M75_TO_M76_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class BrowserActionDryRunActionKind(str, Enum):
    navigate = "navigate"
    click = "click"
    form_fill = "form_fill"
    type_text = "type_text"
    select_option = "select_option"
    observe_again = "observe_again"


class BrowserActionDryRunPlannerStatus(str, Enum):
    plan_ready = "plan_ready"
    denied = "denied"


class _BrowserActionDryRunModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BrowserActionDryRunPlannerPolicy(_BrowserActionDryRunModel):
    policy_ref: str = "browser-action-policy:m75-dry-run"
    planner_enabled: bool = True
    dry_run_only: bool = True
    safe_ref_only: bool = True
    deterministic: bool = True
    browser_action_execution_allowed: bool = False
    browser_session_start_allowed: bool = False
    navigation_execution_allowed: bool = False
    click_execution_allowed: bool = False
    form_fill_execution_allowed: bool = False
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
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class BrowserActionDryRunStep(_BrowserActionDryRunModel):
    step_ref: str
    action_kind: BrowserActionDryRunActionKind
    safe_target_ref: str
    safe_intent: str
    action_execution_performed: bool = False
    browser_session_started: bool = False
    navigation_performed: bool = False
    click_performed: bool = False
    form_fill_performed: bool = False
    screenshot_returned: bool = False
    raw_dom_returned: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.step_ref, "step_ref")
        _validate_safe_payload(self.safe_intent)
        return self


class BrowserActionDryRunPlannerRequest(_BrowserActionDryRunModel):
    plan_ref: str
    actor_ref: str
    target_ref: str
    source_observation_ref: str
    safe_url_ref: str
    safe_summary: str
    steps: list[BrowserActionDryRunStep]
    approval_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    browser_action_execution_requested: bool = False
    browser_session_start_requested: bool = False
    navigation_execution_requested: bool = False
    click_execution_requested: bool = False
    form_fill_execution_requested: bool = False
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
            (self.plan_ref, "plan_ref"),
            (self.actor_ref, "actor_ref"),
            (self.target_ref, "target_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.safe_url_ref, "safe_url_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class BrowserActionDryRunReceiptPlan(_BrowserActionDryRunModel):
    receipt_ref: str
    plan_ref: str
    dry_run_only: bool = True
    browser_action_execution_performed: bool = False
    browser_session_started: bool = False
    navigation_performed: bool = False
    click_performed: bool = False
    form_fill_performed: bool = False
    screenshot_stored: bool = False
    raw_dom_stored: bool = False
    authenticated_profile_used: bool = False
    cookies_or_credentials_used: bool = False
    network_call_performed: bool = False
    tool_execution_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_used: bool = False
    control_center_control_used: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)


class BrowserActionDryRunPlan(_BrowserActionDryRunModel):
    plan_ref: str
    actor_ref: str
    target_ref: str
    source_observation_ref: str
    safe_url_ref: str
    status: BrowserActionDryRunPlannerStatus
    plan_valid_for_review: bool
    dry_run_only: bool = True
    source_observation_content_untrusted: bool = True
    web_content_instruction_use_allowed: bool = False
    planned_steps: list[BrowserActionDryRunStep] = Field(default_factory=list)
    receipt_plan: BrowserActionDryRunReceiptPlan
    browser_action_execution_allowed: bool = False
    browser_action_execution_performed: bool = False
    browser_session_started: bool = False
    navigation_performed: bool = False
    click_performed: bool = False
    form_fill_performed: bool = False
    screenshot_returned: bool = False
    raw_dom_returned: bool = False
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
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.plan_ref, "plan_ref"),
            (self.actor_ref, "actor_ref"),
            (self.target_ref, "target_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.safe_url_ref, "safe_url_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("BROWSER_ACTION_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_message)
        if not self.source_observation_content_untrusted:
            raise ValueError("BROWSER_ACTION_SOURCE_OBSERVATION_MUST_BE_UNTRUSTED")
        if self.web_content_instruction_use_allowed:
            raise ValueError("BROWSER_ACTION_WEB_CONTENT_INSTRUCTION_USE_DENIED")
        return self


def validate_browser_action_dry_run_policy(
    policy: BrowserActionDryRunPlannerPolicy,
) -> BrowserActionDryRunPlannerPolicy:
    payload = _model_payload(policy)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not payload.get(field_name):
            raise ValueError(reason)
    for field_name, reason in _POLICY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = BrowserActionDryRunPlannerPolicy.model_validate(payload)
    _validate_browser_action_metadata(validated.metadata)
    return validated


def _build_browser_action_dry_run_plan(
    request: BrowserActionDryRunPlannerRequest,
    policy: BrowserActionDryRunPlannerPolicy | None = None,
) -> BrowserActionDryRunPlan:
    try:
        active_policy = validate_browser_action_dry_run_policy(
            policy or BrowserActionDryRunPlannerPolicy()
        )
    except ValueError as exc:
        return _denied_plan_from_request(request, [_safe_reason(str(exc), "BROWSER_ACTION_POLICY_INVALID")])

    _ = active_policy
    reasons = browser_action_dry_run_request_reason_codes(request)
    step_refs: set[str] = set()
    for step in request.steps:
        step_payload = _model_payload(step)
        step_ref = step_payload.get("step_ref")
        if step_ref in step_refs:
            reasons.append("DUPLICATE_BROWSER_ACTION_STEP_REF_DENIED")
        step_refs.add(step_ref)
        reasons.extend(browser_action_dry_run_step_reason_codes(step))
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        return _denied_plan_from_request(request, reasons)

    return BrowserActionDryRunPlan(
        plan_ref=request.plan_ref,
        actor_ref=request.actor_ref,
        target_ref=request.target_ref,
        source_observation_ref=request.source_observation_ref,
        safe_url_ref=request.safe_url_ref,
        status=BrowserActionDryRunPlannerStatus.plan_ready,
        plan_valid_for_review=True,
        planned_steps=sorted(request.steps, key=lambda step: step.step_ref),
        receipt_plan=_receipt_plan(request),
        reason_codes=[
            "M75_BROWSER_ACTION_DRY_RUN_PLAN",
            "BROWSER_ACTION_DRY_RUN_ONLY",
            "M76_REMAINS_FUTURE",
        ],
        safe_message="BROWSER_ACTION_DRY_RUN_PLAN_READY_FOR_REVIEW",
    )


@dataclass(frozen=True)
class _BrowserActionDryRunWebAccessAdapter:
    planner_request: BrowserActionDryRunPlannerRequest
    policy: BrowserActionDryRunPlannerPolicy
    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.LOCAL_BROWSER_ACTION_DRY_RUN

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        if request.kind != WebAccessRequestKind.BROWSER_ACTION_DRY_RUN:
            plan = _denied_plan_from_request(
                self.planner_request,
                ["BROWSER_ACTION_DRY_RUN_GATEWAY_KIND_MISMATCH"],
            )
            return _blocked_browser_action_dry_run_adapter_result(plan)
        if not _web_access_request_matches_planner(request, self.planner_request):
            plan = _denied_plan_from_request(
                self.planner_request,
                ["BROWSER_ACTION_DRY_RUN_GATEWAY_METADATA_MISMATCH"],
            )
            return _blocked_browser_action_dry_run_adapter_result(plan)

        plan = _build_browser_action_dry_run_plan(self.planner_request, self.policy)
        if plan.status != BrowserActionDryRunPlannerStatus.plan_ready or not plan.plan_valid_for_review:
            return _blocked_browser_action_dry_run_adapter_result(plan)

        return {
            "adapter_ref": "web-access-adapter:browser-action-dry-run.v1",
            "allowed": True,
            "status": plan.status.value,
            "plan_ref": plan.plan_ref,
            "target_ref": plan.target_ref,
            "safe_url_ref": plan.safe_url_ref,
            "source_observation_ref": plan.source_observation_ref,
            "source_observation_content_untrusted": True,
            "web_content_instruction_use_allowed": False,
            "output": plan.model_dump(mode="python"),
            "summary": plan.safe_message,
            "source_refs": [
                {
                    "source_observation_ref": plan.source_observation_ref,
                    "target_ref": plan.target_ref,
                    "safe_url_ref": plan.safe_url_ref,
                    "content_untrusted": True,
                }
            ],
        }


def build_browser_action_dry_run_plan_via_web_access_gateway(
    request: BrowserActionDryRunPlannerRequest,
    policy: BrowserActionDryRunPlannerPolicy | None = None,
) -> BrowserActionDryRunPlan:
    """Route M75 browser dry-run planning through WebAccessGateway."""

    active_policy = policy or BrowserActionDryRunPlannerPolicy()
    adapter = _BrowserActionDryRunWebAccessAdapter(
        planner_request=request,
        policy=active_policy,
    )
    result = WebAccessGateway(
        policy=WebAccessPolicy(allow_browser_action_dry_run=True),
        adapters={WebAccessRequestKind.BROWSER_ACTION_DRY_RUN: adapter},
    ).execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
            method="GET",
            authority_mode=WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN,
            network_lane=WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN,
            actor=request.actor_ref,
            session_id=request.plan_ref,
            metadata=_web_access_metadata_from_request(request),
        )
    )
    plan = _plan_from_web_access_payload(result.evidence_bundle.payload if result.evidence_bundle else None)
    if plan is not None:
        return plan
    if result.status != WebAccessPolicyStatus.ALLOWED:
        reasons = _browser_action_dry_run_reasons_from_web_access_result(result.decision.reasons)
        reasons.extend(_browser_action_dry_run_preflight_reason_codes(request))
        return _denied_plan_from_request(
            request,
            list(dict.fromkeys(reasons)),
        )
    return _denied_plan_from_request(request, ["BROWSER_ACTION_DRY_RUN_GATEWAY_OUTPUT_MISSING"])


def _web_access_metadata_from_request(request: BrowserActionDryRunPlannerRequest) -> Mapping[str, Any]:
    return {
        "adapter_ref": "web-access-adapter:browser-action-dry-run.v1",
        "browser_action_planner_ref": BROWSER_ACTION_DRY_RUN_PLANNER_REF,
        "plan_ref": request.plan_ref,
        "target_ref": request.target_ref,
        "source_observation_ref": request.source_observation_ref,
        "safe_url_ref": request.safe_url_ref,
        "source_observation_content_untrusted": True,
        "web_content_instruction_use_allowed": False,
        "browser_action_execution": request.browser_action_execution_requested,
        "browser_session_start": request.browser_session_start_requested,
        "navigation_execution": request.navigation_execution_requested,
        "click_execution": request.click_execution_requested,
        "form_fill_execution": request.form_fill_execution_requested,
        "screenshot": request.screenshot_requested,
        "raw_dom": request.raw_dom_requested,
        "uses_auth": request.authenticated_profile_requested,
        "cookies": request.cookies_or_credentials_requested,
        "download": request.download_or_upload_requested,
        "upload": request.download_or_upload_requested,
        "remote_browser": request.remote_browser_requested,
        "network_interception": request.network_interception_requested,
        "network_call": request.network_call_requested,
        "model_call": request.model_call_requested,
        "tool_execution": request.tool_execution_requested,
        "memory_write": request.memory_write_requested,
        "context_injection": request.context_injection_requested,
        "backend_route": request.backend_route_requested,
        "control_center_control": request.control_center_control_requested,
        "production_authority": request.production_authority_requested,
        "step_action_execution_performed": any(step.action_execution_performed for step in request.steps),
        "step_browser_session_started": any(step.browser_session_started for step in request.steps),
        "step_navigation_performed": any(step.navigation_performed for step in request.steps),
        "step_click_performed": any(step.click_performed for step in request.steps),
        "step_form_fill_performed": any(step.form_fill_performed for step in request.steps),
        "step_screenshot_returned": any(step.screenshot_returned for step in request.steps),
        "step_raw_dom_returned": any(step.raw_dom_returned for step in request.steps),
    }


def _blocked_browser_action_dry_run_adapter_result(plan: BrowserActionDryRunPlan) -> Mapping[str, Any]:
    return {
        "adapter_ref": "web-access-adapter:browser-action-dry-run.v1",
        "allowed": False,
        "status": "denied",
        "reason_codes": plan.reason_codes,
        "plan_ref": plan.plan_ref,
        "target_ref": plan.target_ref,
        "safe_url_ref": plan.safe_url_ref,
        "source_observation_ref": plan.source_observation_ref,
        "source_observation_content_untrusted": True,
        "web_content_instruction_use_allowed": False,
        "output": plan.model_dump(mode="python"),
        "source_refs": [
            {
                "source_observation_ref": plan.source_observation_ref,
                "target_ref": plan.target_ref,
                "safe_url_ref": plan.safe_url_ref,
                "content_untrusted": True,
            }
        ],
    }


def _web_access_request_matches_planner(
    request: WebAccessRequest,
    planner_request: BrowserActionDryRunPlannerRequest,
) -> bool:
    expected = {
        "plan_ref": planner_request.plan_ref,
        "target_ref": planner_request.target_ref,
        "source_observation_ref": planner_request.source_observation_ref,
        "safe_url_ref": planner_request.safe_url_ref,
    }
    return all(request.metadata.get(key) == value for key, value in expected.items())


def _plan_from_web_access_payload(payload: Mapping[str, Any] | None) -> BrowserActionDryRunPlan | None:
    if not payload:
        return None
    output_payload = payload.get("output")
    if not isinstance(output_payload, Mapping):
        return None
    return BrowserActionDryRunPlan.model_validate(output_payload)


def _browser_action_dry_run_preflight_reason_codes(
    request: BrowserActionDryRunPlannerRequest,
) -> list[str]:
    reasons = browser_action_dry_run_request_reason_codes(request)
    for step in request.steps:
        reasons.extend(browser_action_dry_run_step_reason_codes(step))
    return list(dict.fromkeys(reasons))


def _browser_action_dry_run_reasons_from_web_access_result(reasons: tuple[str, ...]) -> list[str]:
    mapped: list[str] = []
    for reason in reasons:
        if reason.startswith("adapter_reason:"):
            mapped.append(_safe_reason(reason.split(":", 1)[1], "BROWSER_ACTION_DRY_RUN_GATEWAY_DENIED"))
        elif reason == "browser_action_dry_run_not_enabled":
            mapped.append("BROWSER_ACTION_DRY_RUN_GATEWAY_NOT_ENABLED")
        elif reason == "browser_action_dry_run_authority_mode_required":
            mapped.append("BROWSER_ACTION_DRY_RUN_AUTHORITY_MODE_REQUIRED")
        elif reason == "browser_action_dry_run_lane_required":
            mapped.append("BROWSER_ACTION_DRY_RUN_GATEWAY_LANE_REQUIRED")
        elif reason == "browser_action_dry_run_raw_url_denied":
            mapped.append("RAW_ABSOLUTE_URL_DENIED")
        elif reason == "browser_action_dry_run_safe_url_ref_required":
            mapped.append("BROWSER_ACTION_SAFE_REF_ONLY_REQUIRED")
        elif reason == "browser_action_dry_run_observation_ref_required":
            mapped.append("BROWSER_ACTION_OBSERVATION_REF_REQUIRED")
        elif reason == "browser_action_dry_run_plan_ref_required":
            mapped.append("BROWSER_ACTION_PLAN_REF_REQUIRED")
        elif reason in {
            "browser_action_dry_run_execution_denied",
            "browser_action_dry_run_step_execution_denied",
        }:
            mapped.append("BROWSER_ACTION_EXECUTION_DENIED")
        elif reason in {
            "browser_action_dry_run_session_start_denied",
            "browser_action_dry_run_step_session_start_denied",
        }:
            mapped.append("BROWSER_SESSION_START_DENIED")
        elif reason in {
            "browser_action_dry_run_navigation_execution_denied",
            "browser_action_dry_run_step_navigation_denied",
        }:
            mapped.append("BROWSER_NAVIGATION_EXECUTION_DENIED")
        elif reason in {
            "browser_action_dry_run_click_execution_denied",
            "browser_action_dry_run_step_click_denied",
        }:
            mapped.append("BROWSER_CLICK_EXECUTION_DENIED")
        elif reason in {
            "browser_action_dry_run_form_fill_execution_denied",
            "browser_action_dry_run_step_form_fill_denied",
        }:
            mapped.append("FORM_FILL_EXECUTION_DENIED")
        elif reason in {
            "browser_action_dry_run_screenshot_denied",
            "browser_action_dry_run_step_screenshot_denied",
        }:
            mapped.append("SCREENSHOT_DENIED")
        elif reason in {
            "browser_action_dry_run_raw_dom_denied",
            "browser_action_dry_run_step_raw_dom_denied",
        }:
            mapped.append("RAW_DOM_DENIED")
        elif reason == "browser_action_dry_run_authenticated_profile_denied":
            mapped.append("AUTHENTICATED_PROFILE_DENIED")
        elif reason == "browser_action_dry_run_cookies_or_credentials_denied":
            mapped.append("COOKIES_OR_CREDENTIALS_DENIED")
        elif reason == "browser_action_dry_run_download_or_upload_denied":
            mapped.append("DOWNLOAD_OR_UPLOAD_DENIED")
        elif reason == "browser_action_dry_run_remote_browser_denied":
            mapped.append("REMOTE_BROWSER_DENIED")
        elif reason == "browser_action_dry_run_network_interception_denied":
            mapped.append("NETWORK_INTERCEPTION_DENIED")
        elif reason == "browser_action_dry_run_network_call_denied":
            mapped.append("NETWORK_CALL_DENIED")
        elif reason == "browser_action_dry_run_model_call_denied":
            mapped.append("MODEL_CALL_DENIED")
        elif reason == "browser_action_dry_run_tool_execution_denied":
            mapped.append("TOOL_EXECUTION_DENIED")
        elif reason == "browser_action_dry_run_memory_write_denied":
            mapped.append("MEMORY_WRITE_DENIED")
        elif reason == "browser_action_dry_run_context_injection_denied":
            mapped.append("CONTEXT_INJECTION_DENIED")
        elif reason == "browser_action_dry_run_backend_route_denied":
            mapped.append("BACKEND_ROUTE_DENIED")
        elif reason == "browser_action_dry_run_control_center_control_denied":
            mapped.append("CONTROL_CENTER_CONTROL_DENIED")
        elif reason == "browser_action_dry_run_production_authority_denied":
            mapped.append("PRODUCTION_AUTHORITY_DENIED")
        elif reason.startswith("method_not_allowed:"):
            mapped.append("BROWSER_ACTION_DRY_RUN_NON_GET_METHOD_DENIED")
    return list(dict.fromkeys(mapped or ["BROWSER_ACTION_DRY_RUN_GATEWAY_DENIED"]))


def browser_action_dry_run_request_reason_codes(
    request: BrowserActionDryRunPlannerRequest,
) -> list[str]:
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
            reasons.append("AUTHORITY_REF_NOT_BROWSER_ACTION_AUTHORITY")
    if not payload.get("steps"):
        reasons.append("BROWSER_ACTION_STEP_REQUIRED")
    try:
        BrowserActionDryRunPlannerRequest.model_validate(payload)
        _validate_browser_action_metadata(payload.get("metadata", {}))
    except ValueError as exc:
        reason = _safe_reason(str(exc), "BROWSER_ACTION_REQUEST_INVALID")
        if "SECRET" in reason or "PRIVATE" in reason or "SAFE" in reason:
            reason = "SECRET_LIKE_BROWSER_ACTION_CONTENT_DENIED"
        reasons.append(reason)
    return list(dict.fromkeys(reasons))


def browser_action_dry_run_step_reason_codes(step: BrowserActionDryRunStep) -> list[str]:
    payload = _model_payload(step)
    reasons: list[str] = []
    for field_name, reason in _STEP_DENIALS:
        if payload.get(field_name):
            reasons.append(reason)
    try:
        BrowserActionDryRunStep.model_validate(payload)
        _validate_m61_ref(str(payload.get("safe_target_ref", "")), "safe_target_ref")
        _validate_safe_payload(payload.get("safe_intent", ""))
    except ValueError:
        reasons.append("SECRET_LIKE_BROWSER_ACTION_CONTENT_DENIED")
    if payload.get("side_effects_performed"):
        reasons.append("BROWSER_ACTION_SIDE_EFFECTS_DENIED")
    return list(dict.fromkeys(reasons))


def _denied_plan_from_request(
    request: BrowserActionDryRunPlannerRequest,
    reason_codes: list[str],
) -> BrowserActionDryRunPlan:
    return BrowserActionDryRunPlan(
        plan_ref=request.plan_ref,
        actor_ref=request.actor_ref,
        target_ref=request.target_ref,
        source_observation_ref=request.source_observation_ref,
        safe_url_ref=request.safe_url_ref,
        status=BrowserActionDryRunPlannerStatus.denied,
        plan_valid_for_review=False,
        planned_steps=[],
        receipt_plan=_receipt_plan(request),
        reason_codes=list(dict.fromkeys(reason_codes)),
        safe_message="BROWSER_ACTION_DRY_RUN_PLAN_DENIED",
    )


def _receipt_plan(request: BrowserActionDryRunPlannerRequest) -> BrowserActionDryRunReceiptPlan:
    return BrowserActionDryRunReceiptPlan(
        receipt_ref=f"browser-action-dry-run-receipt:{_ref_suffix(request.plan_ref)}",
        plan_ref=request.plan_ref,
    )


def _validate_browser_action_metadata(value: Any) -> None:
    if isinstance(value, str):
        _validate_safe_payload(value)
        return
    if isinstance(value, list):
        for item in value:
            _validate_browser_action_metadata(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_safe_payload(str(key))
            _validate_browser_action_metadata(item)
        return
    _validate_safe_payload(value)


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump(mode="python", round_trip=True)
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    return payload


def _safe_reason(value: str, fallback: str) -> str:
    reason = value.strip().split("\n", 1)[0]
    if reason.isupper() and " " not in reason:
        return reason
    return fallback


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


_POLICY_REQUIRED_TRUE = [
    ("planner_enabled", "BROWSER_ACTION_PLANNER_REQUIRED"),
    ("dry_run_only", "BROWSER_ACTION_DRY_RUN_ONLY_REQUIRED"),
    ("safe_ref_only", "BROWSER_ACTION_SAFE_REF_ONLY_REQUIRED"),
    ("deterministic", "BROWSER_ACTION_DETERMINISTIC_REQUIRED"),
]

_POLICY_DENIALS = [
    ("browser_action_execution_allowed", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_session_start_allowed", "BROWSER_SESSION_START_DENIED"),
    ("navigation_execution_allowed", "BROWSER_NAVIGATION_EXECUTION_DENIED"),
    ("click_execution_allowed", "BROWSER_CLICK_EXECUTION_DENIED"),
    ("form_fill_execution_allowed", "FORM_FILL_EXECUTION_DENIED"),
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
    ("browser_action_execution_requested", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_session_start_requested", "BROWSER_SESSION_START_DENIED"),
    ("navigation_execution_requested", "BROWSER_NAVIGATION_EXECUTION_DENIED"),
    ("click_execution_requested", "BROWSER_CLICK_EXECUTION_DENIED"),
    ("form_fill_execution_requested", "FORM_FILL_EXECUTION_DENIED"),
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

_STEP_DENIALS = [
    ("action_execution_performed", "BROWSER_ACTION_EXECUTION_DENIED"),
    ("browser_session_started", "BROWSER_SESSION_START_DENIED"),
    ("navigation_performed", "BROWSER_NAVIGATION_EXECUTION_DENIED"),
    ("click_performed", "BROWSER_CLICK_EXECUTION_DENIED"),
    ("form_fill_performed", "FORM_FILL_EXECUTION_DENIED"),
    ("screenshot_returned", "SCREENSHOT_DENIED"),
    ("raw_dom_returned", "RAW_DOM_DENIED"),
]
