from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.dry_run import validate_low_risk_autonomous_dry_run_record
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.tools.autonomous_execution_contract import (
    validate_autonomous_tool_execution_contract_decision,
)


LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_DOCS = [
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_POLICY.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_RECEIPT_PLAN.md",
    "docs/autonomy/LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_NON_GOALS.md",
    "docs/autonomy/M92_TO_M93_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M92_PRIOR_MILESTONE_REFS = ("milestone:M69", "milestone:M90", "milestone:M91")


class LowRiskToolAutonomySingleSessionStatus(str, Enum):
    single_session_ready_for_review = "single_session_ready_for_review"


class _LowRiskToolAutonomySingleSessionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LowRiskToolAutonomySingleSessionPolicy(_LowRiskToolAutonomySingleSessionModel):
    policy_ref: str = "low-risk-tool-autonomy-single-session-policy:m92"
    enabled_for_review: bool = True
    review_only: bool = True
    low_risk_only: bool = True
    single_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m91_contract_binding_required: bool = True
    exact_low_risk_dry_run_binding_required: bool = True
    approval_refs_are_identifiers_only: bool = True
    m93_future_only: bool = True
    low_risk_tool_autonomy_enabled: bool = False
    real_tool_execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    execution_enabled: bool = False
    session_start_enabled: bool = False
    additional_session_enabled: bool = False
    background_worker_enabled: bool = False
    multi_tool_enabled: bool = False
    command_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class LowRiskToolAutonomySingleSessionRequest(_LowRiskToolAutonomySingleSessionModel):
    request_ref: str
    single_session_ref: str
    m91_contract_decision_ref: str
    low_risk_dry_run_record_ref: str
    actor_ref: str
    approval_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    safe_tool_ref: str
    safe_execution_scope_ref: str
    audit_ref: str
    replay_ref: str
    safe_session_summary: str
    safe_tool_refs: list[str]
    prior_milestone_refs: list[str]
    m91_contract_decision: Any
    low_risk_dry_run_record: Any
    review_only: bool = True
    low_risk_only: bool = True
    single_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    execution_requested: bool = False
    tool_execution_requested: bool = False
    autonomous_execution_requested: bool = False
    session_start_requested: bool = False
    additional_session_requested: bool = False
    background_worker_requested: bool = False
    multi_tool_requested: bool = False
    command_execution_requested: bool = False
    shell_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_tool_payload: bool = False
    contains_raw_provider_payload: bool = False
    contains_raw_prompt: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.single_session_ref, "single_session_ref"),
            (self.m91_contract_decision_ref, "m91_contract_decision_ref"),
            (self.low_risk_dry_run_record_ref, "low_risk_dry_run_record_ref"),
            (self.actor_ref, "actor_ref"),
            (self.approval_ref, "approval_ref"),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_tool_refs:
            _validate_m61_ref(ref, "safe_tool_ref")
        _validate_safe_payload(self.safe_session_summary)
        return self


class LowRiskToolAutonomySingleSessionReceiptPlan(_LowRiskToolAutonomySingleSessionModel):
    receipt_plan_ref: str
    single_session_ref: str
    m91_contract_decision_ref: str
    low_risk_dry_run_record_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    safe_tool_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_tool_payload: bool = False
    store_raw_provider_payload: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    autonomous_execution_performed: bool = False
    session_start_performed: bool = False
    background_worker_started: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M92 low-risk tool autonomy single-session receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.single_session_ref, "single_session_ref"),
            (self.m91_contract_decision_ref, "m91_contract_decision_ref"),
            (self.low_risk_dry_run_record_ref, "low_risk_dry_run_record_ref"),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class LowRiskToolAutonomySingleSessionDecision(_LowRiskToolAutonomySingleSessionModel):
    decision_ref: str
    request_ref: str
    single_session_ref: str
    m91_contract_decision_ref: str
    low_risk_dry_run_record_ref: str
    actor_ref: str
    approval_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    safe_tool_ref: str
    safe_execution_scope_ref: str
    audit_ref: str
    replay_ref: str
    safe_tool_refs: list[str]
    status: LowRiskToolAutonomySingleSessionStatus = (
        LowRiskToolAutonomySingleSessionStatus.single_session_ready_for_review
    )
    review_only: bool = True
    low_risk_only: bool = True
    single_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    m91_contract_revalidated: bool = True
    low_risk_dry_run_revalidated: bool = True
    single_session_scope_defined: bool = True
    execution_authorized: bool = False
    tool_execution_authorized: bool = False
    autonomous_execution_authorized: bool = False
    session_start_authorized: bool = False
    additional_session_authorized: bool = False
    background_worker_authorized: bool = False
    multi_tool_authorized: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    autonomous_execution_performed: bool = False
    session_start_performed: bool = False
    background_worker_started: bool = False
    command_execution_performed: bool = False
    shell_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
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
    receipt_plan: LowRiskToolAutonomySingleSessionReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.single_session_ref, "single_session_ref"),
            (self.m91_contract_decision_ref, "m91_contract_decision_ref"),
            (self.low_risk_dry_run_record_ref, "low_risk_dry_run_record_ref"),
            (self.actor_ref, "actor_ref"),
            (self.approval_ref, "approval_ref"),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_tool_refs:
            _validate_m61_ref(ref, "safe_tool_ref")
        if not self.reason_codes:
            raise ValueError("M92_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_low_risk_tool_autonomy_single_session_decision(
    request: LowRiskToolAutonomySingleSessionRequest,
    policy: LowRiskToolAutonomySingleSessionPolicy | None = None,
) -> LowRiskToolAutonomySingleSessionDecision:
    active_policy = validate_low_risk_tool_autonomy_single_session_policy(
        policy or LowRiskToolAutonomySingleSessionPolicy()
    )
    validated_request = validate_low_risk_tool_autonomy_single_session_request(request)
    decision = LowRiskToolAutonomySingleSessionDecision(
        decision_ref=f"low-risk-tool-autonomy-single-session-decision:{_ref_suffix(validated_request.single_session_ref)}",
        request_ref=validated_request.request_ref,
        single_session_ref=validated_request.single_session_ref,
        m91_contract_decision_ref=validated_request.m91_contract_decision_ref,
        low_risk_dry_run_record_ref=validated_request.low_risk_dry_run_record_ref,
        actor_ref=validated_request.actor_ref,
        approval_ref=validated_request.approval_ref,
        tool_intent_ref=validated_request.tool_intent_ref,
        tool_runtime_ref=validated_request.tool_runtime_ref,
        capability_ref=validated_request.capability_ref,
        safe_tool_ref=validated_request.safe_tool_ref,
        safe_execution_scope_ref=validated_request.safe_execution_scope_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        safe_tool_refs=list(validated_request.safe_tool_refs),
        review_only=active_policy.review_only,
        low_risk_only=active_policy.low_risk_only,
        single_session_only=active_policy.single_session_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        approval_refs_are_identifiers_only=active_policy.approval_refs_are_identifiers_only,
        reason_codes=[
            "M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_REVIEW_ONLY",
            "M92_EXACT_M91_CONTRACT_BINDING_REQUIRED",
            "M92_EXACT_LOW_RISK_DRY_RUN_BINDING_REQUIRED",
            "M92_SINGLE_SESSION_ONLY",
            "M92_NO_REAL_TOOL_EXECUTION",
            "M93_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M92 defines a low-risk tool autonomy single-session review contract over exact "
            "M91 autonomous tool execution contract and M69 low-risk dry-run records. It "
            "does not authorize real tool execution, autonomous execution, session start, "
            "background workers, command/shell/subprocess, filesystem, network, browser, "
            "plugin, remote, model, memory, context, route, Control Center, dependency, "
            "or production authority."
        ),
        receipt_plan=LowRiskToolAutonomySingleSessionReceiptPlan(
            receipt_plan_ref=f"low-risk-tool-autonomy-single-session-receipt-plan:{_ref_suffix(validated_request.single_session_ref)}",
            single_session_ref=validated_request.single_session_ref,
            m91_contract_decision_ref=validated_request.m91_contract_decision_ref,
            low_risk_dry_run_record_ref=validated_request.low_risk_dry_run_record_ref,
            tool_intent_ref=validated_request.tool_intent_ref,
            tool_runtime_ref=validated_request.tool_runtime_ref,
            capability_ref=validated_request.capability_ref,
            safe_tool_ref=validated_request.safe_tool_ref,
        ),
    )
    return validate_low_risk_tool_autonomy_single_session_decision(decision)


def validate_low_risk_tool_autonomy_single_session_policy(
    policy: LowRiskToolAutonomySingleSessionPolicy,
) -> LowRiskToolAutonomySingleSessionPolicy:
    validated = LowRiskToolAutonomySingleSessionPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M92_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M92_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED") from exc
    return validated


def validate_low_risk_tool_autonomy_single_session_request(
    request: LowRiskToolAutonomySingleSessionRequest,
) -> LowRiskToolAutonomySingleSessionRequest:
    payload = _model_payload(request)
    for field_name, reason in _M92_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = LowRiskToolAutonomySingleSessionRequest.model_validate(payload)
    for field_name, reason in _M92_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M92_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_approval_ref(validated.approval_ref)
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_safe_tool_refs(validated.safe_tool_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED") from exc
    m91_decision = validate_autonomous_tool_execution_contract_decision(
        validated.m91_contract_decision
    )
    dry_run_record = validate_low_risk_autonomous_dry_run_record(
        validated.low_risk_dry_run_record
    )
    _validate_exact_m91_binding(validated, m91_decision)
    _validate_exact_low_risk_dry_run_binding(validated, dry_run_record)
    return validated


def validate_low_risk_tool_autonomy_single_session_decision(
    decision: LowRiskToolAutonomySingleSessionDecision,
) -> LowRiskToolAutonomySingleSessionDecision:
    validated = LowRiskToolAutonomySingleSessionDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M92_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != LowRiskToolAutonomySingleSessionStatus.single_session_ready_for_review:
        raise ValueError("M92_SINGLE_SESSION_READY_STATUS_REQUIRED")
    for field_name, reason in _M92_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if "M92_LOW_RISK_TOOL_AUTONOMY_SINGLE_SESSION_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M92_REASON_CODE_REQUIRED")
    _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED") from exc
    return validated


def _validate_receipt_plan(
    receipt_plan: LowRiskToolAutonomySingleSessionReceiptPlan,
) -> LowRiskToolAutonomySingleSessionReceiptPlan:
    validated = LowRiskToolAutonomySingleSessionReceiptPlan.model_validate(
        _model_payload(receipt_plan)
    )
    for field_name, reason in _M92_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M92_RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    return validated


def _validate_exact_m91_binding(request: LowRiskToolAutonomySingleSessionRequest, decision: Any) -> None:
    for request_value, decision_value, reason in [
        (request.m91_contract_decision_ref, decision.decision_ref, "M92_M91_CONTRACT_BINDING_MISMATCH"),
        (request.actor_ref, decision.actor_ref, "M92_ACTOR_BINDING_MISMATCH"),
        (request.approval_ref, decision.approval_ref, "M92_APPROVAL_REF_BINDING_MISMATCH"),
        (request.tool_intent_ref, decision.tool_intent_ref, "M92_TOOL_INTENT_BINDING_MISMATCH"),
        (request.tool_runtime_ref, decision.tool_runtime_ref, "M92_TOOL_RUNTIME_BINDING_MISMATCH"),
        (request.capability_ref, decision.capability_ref, "M92_CAPABILITY_BINDING_MISMATCH"),
        (request.safe_tool_ref, decision.safe_tool_ref, "M92_SAFE_TOOL_BINDING_MISMATCH"),
        (
            request.safe_execution_scope_ref,
            decision.safe_execution_scope_ref,
            "M92_SAFE_EXECUTION_SCOPE_BINDING_MISMATCH",
        ),
        (request.audit_ref, decision.audit_ref, "M92_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, decision.replay_ref, "M92_REPLAY_BINDING_MISMATCH"),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)


def _validate_exact_low_risk_dry_run_binding(
    request: LowRiskToolAutonomySingleSessionRequest,
    record: Any,
) -> None:
    if request.low_risk_dry_run_record_ref != record.record_ref:
        raise ValueError("M92_LOW_RISK_DRY_RUN_BINDING_MISMATCH")


def _validate_receipt_binding(decision: LowRiskToolAutonomySingleSessionDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value in [
        (receipt.single_session_ref, decision.single_session_ref),
        (receipt.m91_contract_decision_ref, decision.m91_contract_decision_ref),
        (receipt.low_risk_dry_run_record_ref, decision.low_risk_dry_run_record_ref),
        (receipt.tool_intent_ref, decision.tool_intent_ref),
        (receipt.tool_runtime_ref, decision.tool_runtime_ref),
        (receipt.capability_ref, decision.capability_ref),
        (receipt.safe_tool_ref, decision.safe_tool_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M92_RECEIPT_BINDING_MISMATCH")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M92_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M92_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M92_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M92_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M92_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M92_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_tool_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M92_SAFE_TOOL_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M92_SAFE_TOOL_REF_DUPLICATE")
    if len(refs) != 1:
        raise ValueError("M92_SINGLE_TOOL_ONLY")
    for ref in refs:
        _validate_m61_ref(ref, "safe_tool_ref")


def _validate_approval_ref(ref: str) -> None:
    if "approval_test_" in ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    _validate_m61_ref(ref, "approval_ref")


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


_M92_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("low_risk_only", "LOW_RISK_ONLY_REQUIRED"),
    ("single_session_only", "M92_SINGLE_SESSION_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("local_only", "M92_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M92_SAFE_REFS_ONLY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]
_M92_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "M92_REVIEW_ENABLED_REQUIRED"),
    ("exact_m91_contract_binding_required", "M92_EXACT_M91_BINDING_REQUIRED"),
    ("exact_low_risk_dry_run_binding_required", "M92_EXACT_LOW_RISK_DRY_RUN_BINDING_REQUIRED"),
    ("m93_future_only", "M93_FUTURE_ONLY_REQUIRED"),
    *_M92_REQUIRED_TRUE,
]
_M92_DECISION_REQUIRED_TRUE = [
    *_M92_REQUIRED_TRUE,
    ("m91_contract_revalidated", "M92_M91_REVALIDATION_REQUIRED"),
    ("low_risk_dry_run_revalidated", "M92_LOW_RISK_DRY_RUN_REVALIDATION_REQUIRED"),
    ("single_session_scope_defined", "M92_SINGLE_SESSION_SCOPE_REQUIRED"),
]
_M92_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M92_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M92_SAFE_REFS_ONLY_REQUIRED"),
]
_M92_POLICY_DENIALS = [
    ("low_risk_tool_autonomy_enabled", "M92_TOOL_AUTONOMY_ENABLEMENT_DENIED"),
    ("real_tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_enabled", "AUTONOMOUS_EXECUTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("session_start_enabled", "SESSION_START_DENIED"),
    ("additional_session_enabled", "M92_ADDITIONAL_SESSION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("multi_tool_enabled", "M92_MULTI_TOOL_DENIED"),
    ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
_M92_REQUEST_DENIALS = [
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_requested", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_requested", "SESSION_START_DENIED"),
    ("additional_session_requested", "M92_ADDITIONAL_SESSION_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("multi_tool_requested", "M92_MULTI_TOOL_DENIED"),
    ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("model_call_requested", "MODEL_CALL_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("contains_raw_tool_payload", "M92_RAW_TOOL_PAYLOAD_DENIED"),
    ("contains_raw_provider_payload", "M92_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
    ("contains_secret", "SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED"),
]
_M92_DECISION_DENIALS = [
    ("execution_authorized", "EXECUTION_DENIED"),
    ("tool_execution_authorized", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_authorized", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_authorized", "SESSION_START_DENIED"),
    ("additional_session_authorized", "M92_ADDITIONAL_SESSION_DENIED"),
    ("background_worker_authorized", "BACKGROUND_WORKER_DENIED"),
    ("multi_tool_authorized", "M92_MULTI_TOOL_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_performed", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_performed", "SESSION_START_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
_M92_RECEIPT_DENIALS = [
    ("store_raw_tool_payload", "M92_RAW_TOOL_PAYLOAD_DENIED"),
    ("store_raw_provider_payload", "M92_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_LOW_RISK_TOOL_AUTONOMY_CONTENT_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_performed", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_performed", "SESSION_START_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
]
