from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.dry_run_promotion import (
    validate_multi_tool_dry_run_promotion_decision,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


LOW_RISK_BROWSER_CLICK_DOCS = [
    "docs/browser/LOW_RISK_BROWSER_CLICKS.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_POLICY.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_AUTHORITY_BOUNDARY.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_RECEIPT_PLAN.md",
    "docs/browser/LOW_RISK_BROWSER_CLICK_NON_GOALS.md",
    "docs/browser/M94_TO_M95_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M94_PRIOR_MILESTONE_REFS = (
    "milestone:M73",
    "milestone:M75",
    "milestone:M91",
    "milestone:M92",
    "milestone:M93",
)


class LowRiskBrowserClickStatus(str, Enum):
    click_allowed_for_scoped_session = "click_allowed_for_scoped_session"
    click_completed = "click_completed"


class _LowRiskBrowserClickModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LowRiskBrowserClickPolicy(_LowRiskBrowserClickModel):
    policy_ref: str = "low-risk-browser-click-policy:m94"
    enabled_for_review: bool = True
    low_risk_click_allowed_by_policy: bool = True
    scoped_session_required: bool = True
    allowlisted_page_required: bool = True
    allowlisted_action_required: bool = True
    exact_m93_promotion_binding_required: bool = True
    exact_click_approval_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    review_redacted_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    form_submission_allowed: bool = False
    typing_allowed: bool = False
    purchase_allowed: bool = False
    download_allowed: bool = False
    upload_allowed: bool = False
    authentication_allowed: bool = False
    account_change_allowed: bool = False
    destructive_action_allowed: bool = False
    credential_or_cookie_access_allowed: bool = False
    raw_dom_allowed: bool = False
    screenshot_allowed: bool = False
    broad_navigation_allowed: bool = False
    external_network_allowed: bool = False
    shell_execution_allowed: bool = False
    plugin_execution_allowed: bool = False
    model_call_allowed: bool = False
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


class LowRiskBrowserClickRequest(_LowRiskBrowserClickModel):
    request_ref: str
    click_ref: str
    m93_promotion_decision_ref: str
    m93_promotion_decision: Any
    actor_ref: str
    click_approval_ref: str
    scoped_session_ref: str
    allowed_page_ref: str
    allowed_action_ref: str
    observed_page_ref: str
    dry_run_plan_ref: str
    safe_target_ref: str
    low_risk_classification_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    prior_milestone_refs: list[str]
    safe_click_summary: str
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    form_submission_requested: bool = False
    typing_requested: bool = False
    purchase_requested: bool = False
    download_requested: bool = False
    upload_requested: bool = False
    authentication_requested: bool = False
    account_change_requested: bool = False
    destructive_action_requested: bool = False
    credential_or_cookie_access_requested: bool = False
    raw_dom_requested: bool = False
    screenshot_requested: bool = False
    broad_navigation_requested: bool = False
    external_network_requested: bool = False
    shell_execution_requested: bool = False
    plugin_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_dom: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.click_ref, "click_ref"),
            (self.m93_promotion_decision_ref, "m93_promotion_decision_ref"),
            (self.actor_ref, "actor_ref"),
            (self.click_approval_ref, "click_approval_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.allowed_page_ref, "allowed_page_ref"),
            (self.allowed_action_ref, "allowed_action_ref"),
            (self.observed_page_ref, "observed_page_ref"),
            (self.dry_run_plan_ref, "dry_run_plan_ref"),
            (self.safe_target_ref, "safe_target_ref"),
            (self.low_risk_classification_ref, "low_risk_classification_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_click_summary)
        return self


class LowRiskBrowserClickReceiptPlan(_LowRiskBrowserClickModel):
    receipt_plan_ref: str
    click_ref: str
    m93_promotion_decision_ref: str
    click_approval_ref: str
    scoped_session_ref: str
    allowed_page_ref: str
    allowed_action_ref: str
    safe_target_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_dom: bool = False
    store_screenshot: bool = False
    store_credentials_or_cookies: bool = False
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    form_submission_performed: bool = False
    typing_performed: bool = False
    purchase_performed: bool = False
    download_performed: bool = False
    upload_performed: bool = False
    authentication_performed: bool = False
    account_change_performed: bool = False
    destructive_action_performed: bool = False
    credential_or_cookie_access_performed: bool = False
    broad_navigation_performed: bool = False
    external_network_performed: bool = False
    shell_execution_performed: bool = False
    plugin_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M94 low-risk browser click receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.click_ref, "click_ref"),
            (self.m93_promotion_decision_ref, "m93_promotion_decision_ref"),
            (self.click_approval_ref, "click_approval_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.allowed_page_ref, "allowed_page_ref"),
            (self.allowed_action_ref, "allowed_action_ref"),
            (self.safe_target_ref, "safe_target_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.revocation_ref, "revocation_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class LowRiskBrowserClickDecision(_LowRiskBrowserClickModel):
    decision_ref: str
    request_ref: str
    click_ref: str
    m93_promotion_decision_ref: str
    actor_ref: str
    click_approval_ref: str
    scoped_session_ref: str
    allowed_page_ref: str
    allowed_action_ref: str
    safe_target_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: LowRiskBrowserClickStatus = LowRiskBrowserClickStatus.click_allowed_for_scoped_session
    low_risk_click_allowed: bool = True
    scoped_session_bound: bool = True
    allowlisted_page_bound: bool = True
    allowlisted_action_bound: bool = True
    exact_m93_promotion_bound: bool = True
    exact_click_approval_bound: bool = True
    audit_bound: bool = True
    revocation_bound: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    click_performed: bool = False
    form_submission_performed: bool = False
    typing_performed: bool = False
    purchase_performed: bool = False
    download_performed: bool = False
    upload_performed: bool = False
    authentication_performed: bool = False
    account_change_performed: bool = False
    destructive_action_performed: bool = False
    credential_or_cookie_access_performed: bool = False
    raw_dom_returned: bool = False
    screenshot_returned: bool = False
    broad_navigation_performed: bool = False
    external_network_performed: bool = False
    shell_execution_performed: bool = False
    plugin_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    receipt_plan: LowRiskBrowserClickReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.click_ref, "click_ref"),
            (self.m93_promotion_decision_ref, "m93_promotion_decision_ref"),
            (self.actor_ref, "actor_ref"),
            (self.click_approval_ref, "click_approval_ref"),
            (self.scoped_session_ref, "scoped_session_ref"),
            (self.allowed_page_ref, "allowed_page_ref"),
            (self.allowed_action_ref, "allowed_action_ref"),
            (self.safe_target_ref, "safe_target_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("M94_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


class LowRiskBrowserClickTransportResponse(_LowRiskBrowserClickModel):
    click_completed: bool
    safe_result_ref: str
    safe_summary: str
    raw_dom_returned: bool = False
    screenshot_returned: bool = False
    form_submission_performed: bool = False
    typing_performed: bool = False
    purchase_performed: bool = False
    download_performed: bool = False
    upload_performed: bool = False
    authentication_performed: bool = False
    account_change_performed: bool = False
    destructive_action_performed: bool = False
    credential_or_cookie_access_performed: bool = False
    broad_navigation_performed: bool = False
    external_network_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.safe_result_ref, "safe_result_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class LowRiskBrowserClickResult(_LowRiskBrowserClickModel):
    result_ref: str
    decision_ref: str
    click_ref: str
    status: LowRiskBrowserClickStatus = LowRiskBrowserClickStatus.click_completed
    click_performed: bool = True
    safe_result_ref: str
    safe_summary: str
    raw_dom_returned: bool = False
    screenshot_returned: bool = False
    form_submission_performed: bool = False
    typing_performed: bool = False
    purchase_performed: bool = False
    download_performed: bool = False
    upload_performed: bool = False
    authentication_performed: bool = False
    account_change_performed: bool = False
    destructive_action_performed: bool = False
    credential_or_cookie_access_performed: bool = False
    broad_navigation_performed: bool = False
    external_network_performed: bool = False
    shell_execution_performed: bool = False
    plugin_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.result_ref, "result_ref"),
            (self.decision_ref, "decision_ref"),
            (self.click_ref, "click_ref"),
            (self.safe_result_ref, "safe_result_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


LowRiskBrowserClickTransport = Callable[
    [LowRiskBrowserClickDecision], LowRiskBrowserClickTransportResponse
]


def build_low_risk_browser_click_decision(
    request: LowRiskBrowserClickRequest,
    policy: LowRiskBrowserClickPolicy | None = None,
) -> LowRiskBrowserClickDecision:
    active_policy = validate_low_risk_browser_click_policy(policy or LowRiskBrowserClickPolicy())
    validated_request = validate_low_risk_browser_click_request(request)
    decision = LowRiskBrowserClickDecision(
        decision_ref=f"low-risk-browser-click-decision:{_ref_suffix(validated_request.click_ref)}",
        request_ref=validated_request.request_ref,
        click_ref=validated_request.click_ref,
        m93_promotion_decision_ref=validated_request.m93_promotion_decision_ref,
        actor_ref=validated_request.actor_ref,
        click_approval_ref=validated_request.click_approval_ref,
        scoped_session_ref=validated_request.scoped_session_ref,
        allowed_page_ref=validated_request.allowed_page_ref,
        allowed_action_ref=validated_request.allowed_action_ref,
        safe_target_ref=validated_request.safe_target_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        low_risk_click_allowed=active_policy.low_risk_click_allowed_by_policy,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        approval_refs_are_identifiers_only=active_policy.approval_refs_are_identifiers_only,
        reason_codes=[
            "M94_LOW_RISK_BROWSER_CLICK_ALLOWED",
            "M94_ALLOWLISTED_PAGE_REQUIRED",
            "M94_ALLOWLISTED_ACTION_REQUIRED",
            "M94_SCOPED_SESSION_REQUIRED",
            "M94_AUDIT_AND_REVOCATION_REQUIRED",
            "M95_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M94 allows only an exact-bound low-risk browser click in a scoped session through "
            "an injected transport. Forms, typing, purchases, downloads, uploads, sign-in flows, "
            "account changes, destructive actions, browser state handles, raw DOM, broad navigation, "
            "external network authority, routes, dependencies, and production authority remain blocked."
        ),
        receipt_plan=LowRiskBrowserClickReceiptPlan(
            receipt_plan_ref=f"low-risk-browser-click-receipt-plan:{_ref_suffix(validated_request.click_ref)}",
            click_ref=validated_request.click_ref,
            m93_promotion_decision_ref=validated_request.m93_promotion_decision_ref,
            click_approval_ref=validated_request.click_approval_ref,
            scoped_session_ref=validated_request.scoped_session_ref,
            allowed_page_ref=validated_request.allowed_page_ref,
            allowed_action_ref=validated_request.allowed_action_ref,
            safe_target_ref=validated_request.safe_target_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
        ),
    )
    return validate_low_risk_browser_click_decision(decision)


def perform_low_risk_browser_click(
    decision: LowRiskBrowserClickDecision,
    transport: LowRiskBrowserClickTransport | None,
) -> LowRiskBrowserClickResult:
    validated_decision = validate_low_risk_browser_click_decision(decision)
    if transport is None:
        raise ValueError("M94_BROWSER_CLICK_TRANSPORT_REQUIRED")
    response = LowRiskBrowserClickTransportResponse.model_validate(_model_payload(transport(validated_decision)))
    if not response.click_completed:
        raise ValueError("M94_BROWSER_CLICK_NOT_COMPLETED")
    _validate_transport_response(response)
    result = LowRiskBrowserClickResult(
        result_ref=f"low-risk-browser-click-result:{_ref_suffix(validated_decision.click_ref)}",
        decision_ref=validated_decision.decision_ref,
        click_ref=validated_decision.click_ref,
        safe_result_ref=response.safe_result_ref,
        safe_summary=response.safe_summary,
        reason_codes=[
            "M94_LOW_RISK_BROWSER_CLICK_COMPLETED",
            "M94_SAFE_RESULT_ONLY",
            "M94_AUDIT_AND_REVOCATION_REQUIRED",
        ],
    )
    return validate_low_risk_browser_click_result(result)


def validate_low_risk_browser_click_policy(
    policy: LowRiskBrowserClickPolicy,
) -> LowRiskBrowserClickPolicy:
    validated = LowRiskBrowserClickPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M94_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M94_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED") from exc
    return validated


def validate_low_risk_browser_click_request(
    request: LowRiskBrowserClickRequest,
) -> LowRiskBrowserClickRequest:
    payload = _model_payload(request)
    for field_name, reason in _M94_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = LowRiskBrowserClickRequest.model_validate(payload)
    for field_name, reason in _M94_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M94_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_click_approval_ref(validated.click_approval_ref)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED") from exc
    m93_decision = validate_multi_tool_dry_run_promotion_decision(
        validated.m93_promotion_decision
    )
    _validate_exact_m93_binding(validated, m93_decision)
    return validated


def validate_low_risk_browser_click_decision(
    decision: LowRiskBrowserClickDecision,
) -> LowRiskBrowserClickDecision:
    validated = LowRiskBrowserClickDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M94_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != LowRiskBrowserClickStatus.click_allowed_for_scoped_session:
        raise ValueError("M94_CLICK_ALLOWED_STATUS_REQUIRED")
    for field_name, reason in _M94_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if "M94_LOW_RISK_BROWSER_CLICK_ALLOWED" not in validated.reason_codes:
        raise ValueError("M94_REASON_CODE_REQUIRED")
    _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED") from exc
    return validated


def validate_low_risk_browser_click_result(
    result: LowRiskBrowserClickResult,
) -> LowRiskBrowserClickResult:
    validated = LowRiskBrowserClickResult.model_validate(_model_payload(result))
    if validated.status != LowRiskBrowserClickStatus.click_completed:
        raise ValueError("M94_CLICK_COMPLETED_STATUS_REQUIRED")
    if not validated.click_performed:
        raise ValueError("M94_CLICK_COMPLETION_REQUIRED")
    for field_name, reason in _M94_RESULT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if "M94_LOW_RISK_BROWSER_CLICK_COMPLETED" not in validated.reason_codes:
        raise ValueError("M94_RESULT_REASON_CODE_REQUIRED")
    return validated


def _validate_receipt_plan(
    receipt_plan: LowRiskBrowserClickReceiptPlan,
) -> LowRiskBrowserClickReceiptPlan:
    validated = LowRiskBrowserClickReceiptPlan.model_validate(_model_payload(receipt_plan))
    for field_name, reason in _M94_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M94_RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    return validated


def _validate_exact_m93_binding(request: LowRiskBrowserClickRequest, decision: Any) -> None:
    for request_value, decision_value, reason in [
        (request.m93_promotion_decision_ref, decision.decision_ref, "M94_M93_PROMOTION_BINDING_MISMATCH"),
        (request.actor_ref, decision.actor_ref, "M94_ACTOR_BINDING_MISMATCH"),
        (request.scoped_session_ref, decision.safe_execution_scope_ref, "M94_SCOPED_SESSION_BINDING_MISMATCH"),
        (request.audit_ref, decision.audit_ref, "M94_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, decision.replay_ref, "M94_REPLAY_BINDING_MISMATCH"),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)
    if not decision.promotion_allowed_for_review:
        raise ValueError("M94_M93_PROMOTION_NOT_REVIEW_READY")


def _validate_receipt_binding(decision: LowRiskBrowserClickDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value in [
        (receipt.click_ref, decision.click_ref),
        (receipt.m93_promotion_decision_ref, decision.m93_promotion_decision_ref),
        (receipt.click_approval_ref, decision.click_approval_ref),
        (receipt.scoped_session_ref, decision.scoped_session_ref),
        (receipt.allowed_page_ref, decision.allowed_page_ref),
        (receipt.allowed_action_ref, decision.allowed_action_ref),
        (receipt.safe_target_ref, decision.safe_target_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M94_RECEIPT_BINDING_MISMATCH")


def _validate_transport_response(response: LowRiskBrowserClickTransportResponse) -> None:
    for field_name, reason in _M94_TRANSPORT_DENIALS:
        if getattr(response, field_name):
            raise ValueError(reason)
    if response.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M94_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M94_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M94_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M94_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M94_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M94_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_click_approval_ref(ref: str) -> None:
    lower = ref.lower()
    if "approval_test_" in lower:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if "*" in ref or "wildcard" in lower or lower.endswith(":all"):
        raise ValueError("M94_WILDCARD_APPROVAL_DENIED")
    if "click" not in lower or "m94" not in lower:
        raise ValueError("M94_EXACT_CLICK_APPROVAL_REQUIRED")
    _validate_m61_ref(ref, "click_approval_ref")


def _model_payload(model: Any) -> dict[str, Any]:
    if isinstance(model, BaseModel):
        payload = dict(model.__dict__)
        payload.update(getattr(model, "__pydantic_extra__", None) or {})
        return payload
    if isinstance(model, dict):
        return dict(model)
    raise TypeError(f"unsupported model payload type: {type(model)!r}")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


_M94_REQUIRED_TRUE = [
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("local_only", "M94_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M94_SAFE_REFS_ONLY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]
_M94_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "M94_REVIEW_ENABLED_REQUIRED"),
    ("low_risk_click_allowed_by_policy", "M94_LOW_RISK_CLICK_POLICY_REQUIRED"),
    ("scoped_session_required", "M94_SCOPED_SESSION_REQUIRED"),
    ("allowlisted_page_required", "M94_ALLOWLISTED_PAGE_REQUIRED"),
    ("allowlisted_action_required", "M94_ALLOWLISTED_ACTION_REQUIRED"),
    ("exact_m93_promotion_binding_required", "M94_EXACT_M93_BINDING_REQUIRED"),
    ("exact_click_approval_required", "M94_EXACT_CLICK_APPROVAL_REQUIRED"),
    ("audit_required", "M94_AUDIT_REQUIRED"),
    ("revocation_required", "M94_REVOCATION_REQUIRED"),
    ("review_redacted_only", "M94_REDACTED_REVIEW_REQUIRED"),
    *_M94_REQUIRED_TRUE,
]
_M94_DECISION_REQUIRED_TRUE = [
    ("low_risk_click_allowed", "M94_LOW_RISK_CLICK_REQUIRED"),
    ("scoped_session_bound", "M94_SCOPED_SESSION_REQUIRED"),
    ("allowlisted_page_bound", "M94_ALLOWLISTED_PAGE_REQUIRED"),
    ("allowlisted_action_bound", "M94_ALLOWLISTED_ACTION_REQUIRED"),
    ("exact_m93_promotion_bound", "M94_EXACT_M93_BINDING_REQUIRED"),
    ("exact_click_approval_bound", "M94_EXACT_CLICK_APPROVAL_REQUIRED"),
    ("audit_bound", "M94_AUDIT_REQUIRED"),
    ("revocation_bound", "M94_REVOCATION_REQUIRED"),
    *_M94_REQUIRED_TRUE,
]
_M94_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M94_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M94_SAFE_REFS_ONLY_REQUIRED"),
]
_M94_UNSAFE_ACTIONS = [
    ("form_submission", "FORM_SUBMISSION_DENIED"),
    ("typing", "TYPING_DENIED"),
    ("purchase", "PURCHASE_DENIED"),
    ("download", "DOWNLOAD_DENIED"),
    ("upload", "UPLOAD_DENIED"),
    ("authentication", "AUTHENTICATION_DENIED"),
    ("account_change", "ACCOUNT_CHANGE_DENIED"),
    ("destructive_action", "DESTRUCTIVE_ACTION_DENIED"),
    ("credential_or_cookie_access", "CREDENTIAL_OR_COOKIE_ACCESS_DENIED"),
    ("raw_dom", "RAW_DOM_DENIED"),
    ("screenshot", "SCREENSHOT_DENIED"),
    ("broad_navigation", "BROAD_NAVIGATION_DENIED"),
    ("external_network", "EXTERNAL_NETWORK_DENIED"),
    ("shell_execution", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution", "PLUGIN_EXECUTION_DENIED"),
    ("model_call", "MODEL_CALL_DENIED"),
    ("memory_write", "MEMORY_WRITE_DENIED"),
    ("context_injection", "CONTEXT_INJECTION_DENIED"),
    ("backend_route", "BACKEND_ROUTE_DENIED"),
    ("control_center_control", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority", "PRODUCTION_AUTHORITY_DENIED"),
]
_M94_UNSAFE_PERFORMED_ACTIONS = [
    ("form_submission", "FORM_SUBMISSION_DENIED"),
    ("typing", "TYPING_DENIED"),
    ("purchase", "PURCHASE_DENIED"),
    ("download", "DOWNLOAD_DENIED"),
    ("upload", "UPLOAD_DENIED"),
    ("authentication", "AUTHENTICATION_DENIED"),
    ("account_change", "ACCOUNT_CHANGE_DENIED"),
    ("destructive_action", "DESTRUCTIVE_ACTION_DENIED"),
    ("credential_or_cookie_access", "CREDENTIAL_OR_COOKIE_ACCESS_DENIED"),
    ("broad_navigation", "BROAD_NAVIGATION_DENIED"),
    ("external_network", "EXTERNAL_NETWORK_DENIED"),
]
_M94_POLICY_DENIALS = [
    *[(f"{field}_allowed", reason) for field, reason in _M94_UNSAFE_ACTIONS[:13]],
    ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
    ("model_call_allowed", "MODEL_CALL_DENIED"),
    ("memory_write_allowed", "MEMORY_WRITE_DENIED"),
    ("context_injection_allowed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_allowed", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_allowed", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_allowed", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
]
_M94_REQUEST_DENIALS = [
    *[(f"{field}_requested", reason) for field, reason in _M94_UNSAFE_ACTIONS],
    ("contains_raw_dom", "RAW_DOM_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED"),
]
_M94_DECISION_DENIALS = [
    ("click_performed", "M94_CLICK_NOT_ALLOWED_IN_DECISION"),
    *[(f"{field}_performed", reason) for field, reason in _M94_UNSAFE_PERFORMED_ACTIONS],
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
    ("raw_dom_returned", "RAW_DOM_DENIED"),
    ("screenshot_returned", "SCREENSHOT_DENIED"),
]
_M94_RECEIPT_DENIALS = [
    ("store_raw_dom", "RAW_DOM_DENIED"),
    ("store_screenshot", "SCREENSHOT_DENIED"),
    ("store_credentials_or_cookies", "CREDENTIAL_OR_COOKIE_ACCESS_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_DENIED"),
    ("store_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_DENIED"),
    ("store_secret", "SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED"),
    *[(f"{field}_performed", reason) for field, reason in _M94_UNSAFE_PERFORMED_ACTIONS],
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
_M94_TRANSPORT_DENIALS = [
    ("raw_dom_returned", "RAW_DOM_DENIED"),
    ("screenshot_returned", "SCREENSHOT_DENIED"),
    *[(f"{field}_performed", reason) for field, reason in _M94_UNSAFE_PERFORMED_ACTIONS],
]
_M94_RESULT_DENIALS = [
    ("raw_dom_returned", "RAW_DOM_DENIED"),
    ("screenshot_returned", "SCREENSHOT_DENIED"),
    *[(f"{field}_performed", reason) for field, reason in _M94_UNSAFE_PERFORMED_ACTIONS],
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
