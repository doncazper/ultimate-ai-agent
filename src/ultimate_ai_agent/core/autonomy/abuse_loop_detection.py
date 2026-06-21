from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
    _ref_suffix,
)
from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    _validate_m61_ref,
    _validate_safe_payload,
)


ABUSE_LOOP_DETECTION_DOCS = [
    "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION.md",
    "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_POLICY.md",
    "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMY_ABUSE_LOOP_DETECTION_NON_GOALS.md",
    "docs/autonomy/M139_TO_M140_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M139_MAX_SIGNAL_REFS = 32
M139_MAX_PATTERN_REFS = 24


class AbuseLoopDetectionStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _AbuseLoopDetectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AbuseLoopDetectionPolicy(_AbuseLoopDetectionModel):
    policy_ref: str = "abuse-loop-detection-policy:m139"
    contract_only: bool = True
    review_only: bool = True
    autonomy_abuse_loop_detection_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m138_error_guardrail_required: bool = True
    m137_browser_connector_workflow_required: bool = True
    m136_dependency_execution_required: bool = True
    m135_recovery_planner_required: bool = True
    m134_human_checkpoint_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    abuse_signal_required: bool = True
    loop_signal_required: bool = True
    pattern_policy_required: bool = True
    threshold_policy_required: bool = True
    intervention_plan_required: bool = True
    escalation_plan_required: bool = True
    human_checkpoint_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m140_future_only: bool = True
    abuse_detection_runtime_enabled: bool = False
    loop_detection_runtime_enabled: bool = False
    loop_monitor_enabled: bool = False
    detector_runtime_enabled: bool = False
    loop_intervention_enabled: bool = False
    autonomous_recovery_execution_enabled: bool = False
    retry_execution_enabled: bool = False
    resume_execution_enabled: bool = False
    rollback_execution_enabled: bool = False
    dependency_execution_enabled: bool = False
    browser_action_enabled: bool = False
    connector_action_enabled: bool = False
    connector_write_enabled: bool = False
    account_auth_enabled: bool = False
    tool_execution_enabled: bool = False
    execution_enabled: bool = False
    shell_execution_enabled: bool = False
    command_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED") from exc
        return self


class AbuseLoopDetectionRequest(_AbuseLoopDetectionModel):
    request_ref: str
    detection_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m138_error_guardrail_decision_ref: str
    m137_combined_workflow_decision_ref: str
    m136_dependency_execution_decision_ref: str
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    abuse_signal_refs: list[str]
    loop_signal_refs: list[str]
    pattern_policy_ref: str
    threshold_policy_ref: str
    intervention_plan_ref: str
    escalation_plan_ref: str
    human_checkpoint_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    requested_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_signal_refs: int = Field(gt=0, le=M139_MAX_SIGNAL_REFS)
    max_pattern_refs: int = Field(gt=0, le=M139_MAX_PATTERN_REFS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_detection_summary: str
    contract_only: bool = True
    review_only: bool = True
    autonomy_abuse_loop_detection_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    abuse_detection_runtime_requested: bool = False
    loop_detection_runtime_requested: bool = False
    loop_monitor_requested: bool = False
    detector_runtime_requested: bool = False
    loop_intervention_requested: bool = False
    autonomous_recovery_execution_requested: bool = False
    retry_execution_requested: bool = False
    resume_execution_requested: bool = False
    rollback_execution_requested: bool = False
    dependency_execution_requested: bool = False
    browser_action_requested: bool = False
    connector_action_requested: bool = False
    connector_write_requested: bool = False
    account_auth_requested: bool = False
    tool_execution_requested: bool = False
    execution_requested: bool = False
    shell_execution_requested: bool = False
    command_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    plugin_execution_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_abuse_log: bool = False
    contains_raw_loop_trace: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_cookie_or_credential: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M139_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M139_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M139_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.abuse_signal_refs,
            "abuse_signal_ref",
            "M139_ABUSE_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        _validate_ref_list(
            self.loop_signal_refs,
            "loop_signal_ref",
            "M139_LOOP_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        if len(self.abuse_signal_refs) + len(self.loop_signal_refs) > self.max_signal_refs:
            raise ValueError("M139_SIGNAL_LIMIT_DENIED")
        if self.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M139_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M139_RISK_CEILING_DENIED")
        _validate_required_bool(self.contract_only, "M139_CONTRACT_ONLY_REQUIRED")
        _validate_required_bool(self.review_only, "M139_REVIEW_ONLY_REQUIRED")
        _validate_required_bool(
            self.autonomy_abuse_loop_detection_only,
            "M139_ABUSE_LOOP_DETECTION_ONLY_REQUIRED",
        )
        _validate_required_bool(self.deterministic, "M139_DETERMINISTIC_REQUIRED")
        _validate_required_bool(self.local_only, "M139_LOCAL_ONLY_REQUIRED")
        _validate_required_bool(self.safe_refs_only, "M139_SAFE_REFS_ONLY_REQUIRED")
        try:
            _validate_safe_payload(self.safe_detection_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED") from exc
        _deny_enabled(_M139_REQUEST_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M139_SIDE_EFFECTS_DENIED")
        return self


class AbuseLoopDetectionReceiptPlan(_AbuseLoopDetectionModel):
    receipt_plan_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_abuse_signal_refs_only: bool = True
    store_loop_signal_refs_only: bool = True
    store_policy_refs_only: bool = True
    store_raw_abuse_log: bool = False
    store_raw_loop_trace: bool = False
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_cookie_or_credential: bool = False
    store_secret: bool = False
    detector_runtime_started: bool = False
    loop_intervention_performed: bool = False
    recovery_execution_performed: bool = False
    abuse_signal_refs: list[str]
    loop_signal_refs: list[str]
    pattern_policy_ref: str
    threshold_policy_ref: str
    safe_receipt_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m61_ref(self.pattern_policy_ref, "pattern_policy_ref")
        _validate_m61_ref(self.threshold_policy_ref, "threshold_policy_ref")
        _validate_ref_list(
            self.abuse_signal_refs,
            "abuse_signal_ref",
            "M139_ABUSE_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        _validate_ref_list(
            self.loop_signal_refs,
            "loop_signal_ref",
            "M139_LOOP_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        try:
            _validate_safe_payload(self.safe_receipt_summary)
        except ValueError as exc:
            raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED") from exc
        _deny_enabled(_M139_RECEIPT_DENIALS, _model_payload(self))
        return self


class AbuseLoopDetectionDecision(_AbuseLoopDetectionModel):
    decision_ref: str
    status: AbuseLoopDetectionStatus = AbuseLoopDetectionStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    contract_only: bool = True
    review_only: bool = True
    autonomy_abuse_loop_detection_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m138_error_guardrail_bound: bool = True
    m137_browser_connector_workflow_bound: bool = True
    m136_dependency_execution_bound: bool = True
    m135_recovery_planner_bound: bool = True
    m134_human_checkpoint_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    abuse_signal_bound: bool = True
    loop_signal_bound: bool = True
    pattern_policy_bound: bool = True
    threshold_policy_bound: bool = True
    intervention_plan_bound: bool = True
    escalation_plan_bound: bool = True
    human_checkpoint_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    abuse_detection_runtime_authorized: bool = False
    loop_detection_runtime_authorized: bool = False
    loop_monitor_started: bool = False
    detector_runtime_started: bool = False
    loop_intervention_authorized: bool = False
    loop_intervention_performed: bool = False
    autonomous_recovery_execution_authorized: bool = False
    retry_execution_performed: bool = False
    resume_execution_performed: bool = False
    rollback_execution_performed: bool = False
    dependency_execution_performed: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    connector_write_performed: bool = False
    account_auth_performed: bool = False
    tool_execution_performed: bool = False
    execution_performed: bool = False
    shell_execution_performed: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    plugin_execution_performed: bool = False
    mobile_sensor_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    abuse_signal_refs: list[str]
    loop_signal_refs: list[str]
    pattern_policy_ref: str
    threshold_policy_ref: str
    intervention_plan_ref: str
    receipt_plan: AbuseLoopDetectionReceiptPlan
    safe_decision_summary: str
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.pattern_policy_ref, "pattern_policy_ref"),
            (self.threshold_policy_ref, "threshold_policy_ref"),
            (self.intervention_plan_ref, "intervention_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(
            self.abuse_signal_refs,
            "abuse_signal_ref",
            "M139_ABUSE_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        _validate_ref_list(
            self.loop_signal_refs,
            "loop_signal_ref",
            "M139_LOOP_SIGNAL_REF_REQUIRED",
            max_count=M139_MAX_SIGNAL_REFS,
        )
        if self.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M139_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M139_RISK_CEILING_DENIED")
        for field, reason in _M139_DECISION_REQUIRED.items():
            if not getattr(self, field):
                raise ValueError(reason)
        _deny_enabled(_M139_DECISION_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M139_SIDE_EFFECTS_DENIED")
        try:
            _validate_safe_payload(self.safe_decision_summary)
        except ValueError as exc:
            raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED") from exc
        return self


def build_abuse_loop_detection_decision(
    request: AbuseLoopDetectionRequest,
    *,
    policy: AbuseLoopDetectionPolicy | None = None,
) -> AbuseLoopDetectionDecision:
    validate_abuse_loop_detection_policy(policy or AbuseLoopDetectionPolicy())
    validate_abuse_loop_detection_request(request)
    receipt_plan = AbuseLoopDetectionReceiptPlan(
        receipt_plan_ref=request.no_effect_receipt_plan_ref,
        abuse_signal_refs=list(request.abuse_signal_refs),
        loop_signal_refs=list(request.loop_signal_refs),
        pattern_policy_ref=request.pattern_policy_ref,
        threshold_policy_ref=request.threshold_policy_ref,
        safe_receipt_summary=(
            "M139 records safe autonomy abuse and loop detection refs for "
            "review only; no detector runtime or intervention occurs."
        ),
    )
    return AbuseLoopDetectionDecision(
        decision_ref=f"abuse-loop-detection-decision:{_ref_suffix(request.request_ref)}",
        abuse_signal_refs=list(request.abuse_signal_refs),
        loop_signal_refs=list(request.loop_signal_refs),
        pattern_policy_ref=request.pattern_policy_ref,
        threshold_policy_ref=request.threshold_policy_ref,
        intervention_plan_ref=request.intervention_plan_ref,
        receipt_plan=receipt_plan,
        safe_decision_summary=(
            "M139 is a contract-only autonomy abuse/loop detection review "
            "envelope; M140 remains future."
        ),
        reason_codes=[
            "M139_AUTONOMY_ABUSE_LOOP_DETECTION_CONTRACT_ONLY",
            "M139_EXACT_DETECTION_SCOPE_REQUIRED",
            "M139_NO_ABUSE_OR_LOOP_RUNTIME",
            "M139_NO_INTERVENTION_OR_RECOVERY_EXECUTION",
            "M140_REMAINS_FUTURE",
        ],
    )


def validate_abuse_loop_detection_policy(
    policy: AbuseLoopDetectionPolicy,
) -> AbuseLoopDetectionPolicy:
    payload = _model_payload(policy)
    for field, reason in _M139_POLICY_REQUIRED.items():
        if not payload.get(field):
            raise ValueError(reason)
    _deny_enabled(_M139_POLICY_DENIALS, payload)
    if _has_secret_like_extra(payload, AbuseLoopDetectionPolicy):
        raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED")
    validated = AbuseLoopDetectionPolicy.model_validate(payload)
    _deny_enabled(_M139_POLICY_DENIALS, _model_payload(validated))
    return validated


def validate_abuse_loop_detection_request(
    request: AbuseLoopDetectionRequest,
) -> AbuseLoopDetectionRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, AbuseLoopDetectionRequest):
        raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED")
    _deny_enabled(_M139_REQUEST_DENIALS, payload)
    validated = AbuseLoopDetectionRequest.model_validate(payload)
    _deny_enabled(_M139_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M139_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M139_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M139_RISK_CEILING_DENIED")
    if len(validated.abuse_signal_refs) + len(validated.loop_signal_refs) > validated.max_signal_refs:
        raise ValueError("M139_SIGNAL_LIMIT_DENIED")
    return validated


def validate_abuse_loop_detection_decision(
    decision: AbuseLoopDetectionDecision,
) -> AbuseLoopDetectionDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, AbuseLoopDetectionDecision):
        raise ValueError("M139_SECRET_LIKE_ABUSE_LOOP_CONTENT_DENIED")
    _deny_enabled(_M139_DECISION_DENIALS, payload)
    receipt_payload = payload.get("receipt_plan", {})
    if isinstance(receipt_payload, dict):
        _deny_enabled(_M139_RECEIPT_DENIALS, receipt_payload)
    validated = AbuseLoopDetectionDecision.model_validate(payload)
    for field, reason in _M139_DECISION_REQUIRED.items():
        if not getattr(validated, field):
            raise ValueError(reason)
    if validated.status != AbuseLoopDetectionStatus.ready_for_review:
        raise ValueError("M139_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M139_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M139_RISK_CEILING_DENIED")
    _deny_enabled(_M139_DECISION_DENIALS, _model_payload(validated))
    _validate_m139_receipt_plan(validated.receipt_plan)
    if validated.side_effects_performed:
        raise ValueError("M139_SIDE_EFFECTS_DENIED")
    if "M139_AUTONOMY_ABUSE_LOOP_DETECTION_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M139_REASON_CODE_REQUIRED")
    return validated


def _validate_m139_receipt_plan(
    receipt_plan: AbuseLoopDetectionReceiptPlan,
) -> AbuseLoopDetectionReceiptPlan:
    payload = _model_payload(receipt_plan)
    _deny_enabled(_M139_RECEIPT_DENIALS, payload)
    return AbuseLoopDetectionReceiptPlan.model_validate(payload)


def _request_ref_pairs(request: AbuseLoopDetectionRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.detection_plan_ref, "detection_plan_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (request.m138_error_guardrail_decision_ref, "m138_error_guardrail_decision_ref"),
        (request.m137_combined_workflow_decision_ref, "m137_combined_workflow_decision_ref"),
        (request.m136_dependency_execution_decision_ref, "m136_dependency_execution_decision_ref"),
        (request.m135_recovery_planner_decision_ref, "m135_recovery_planner_decision_ref"),
        (request.m134_human_checkpoint_decision_ref, "m134_human_checkpoint_decision_ref"),
        (request.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (request.m132_trusted_workflow_decision_ref, "m132_trusted_workflow_decision_ref"),
        (request.pattern_policy_ref, "pattern_policy_ref"),
        (request.threshold_policy_ref, "threshold_policy_ref"),
        (request.intervention_plan_ref, "intervention_plan_ref"),
        (request.escalation_plan_ref, "escalation_plan_ref"),
        (request.human_checkpoint_ref, "human_checkpoint_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _validate_ref_list(
    values: list[str],
    field_name: str,
    required_reason: str,
    *,
    max_count: int | None = None,
) -> None:
    if not values:
        raise ValueError(required_reason)
    if max_count is not None and len(values) > max_count:
        raise ValueError(required_reason)
    for value in values:
        _validate_m61_ref(value, field_name)


def _validate_required_bool(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field, reason in denials.items():
        if payload.get(field):
            raise ValueError(reason)


_M139_POLICY_REQUIRED = {
    "contract_only": "M139_CONTRACT_ONLY_REQUIRED",
    "review_only": "M139_REVIEW_ONLY_REQUIRED",
    "autonomy_abuse_loop_detection_only": "M139_ABUSE_LOOP_DETECTION_ONLY_REQUIRED",
    "deterministic": "M139_DETERMINISTIC_REQUIRED",
    "local_only": "M139_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M139_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_required": "M139_EXACT_SCOPE_REQUIRED",
    "mode5_required": "M139_MODE5_REQUIRED",
    "m138_error_guardrail_required": "M139_M138_BOUNDARY_REQUIRED",
    "m137_browser_connector_workflow_required": "M139_M137_BOUNDARY_REQUIRED",
    "m136_dependency_execution_required": "M139_M136_BOUNDARY_REQUIRED",
    "m135_recovery_planner_required": "M139_M135_BOUNDARY_REQUIRED",
    "m134_human_checkpoint_required": "M139_M134_BOUNDARY_REQUIRED",
    "m133_supervisor_required": "M139_M133_BOUNDARY_REQUIRED",
    "m132_trusted_workflow_required": "M139_M132_BOUNDARY_REQUIRED",
    "abuse_signal_required": "M139_ABUSE_SIGNAL_REF_REQUIRED",
    "loop_signal_required": "M139_LOOP_SIGNAL_REF_REQUIRED",
    "pattern_policy_required": "M139_PATTERN_POLICY_REQUIRED",
    "threshold_policy_required": "M139_THRESHOLD_POLICY_REQUIRED",
    "intervention_plan_required": "M139_INTERVENTION_PLAN_REQUIRED",
    "escalation_plan_required": "M139_ESCALATION_PLAN_REQUIRED",
    "human_checkpoint_required": "M139_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_required": "M139_AUDIT_REPLAY_REQUIRED",
    "revocation_required": "M139_REVOCATION_REQUIRED",
    "kill_switch_required": "M139_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M139_NO_EFFECT_RECEIPT_REQUIRED",
    "m140_future_only": "M140_REMAINS_FUTURE",
}

_M139_POLICY_DENIALS = {
    "abuse_detection_runtime_enabled": "M139_ABUSE_DETECTION_RUNTIME_DENIED",
    "loop_detection_runtime_enabled": "M139_LOOP_DETECTION_RUNTIME_DENIED",
    "loop_monitor_enabled": "M139_LOOP_MONITOR_DENIED",
    "detector_runtime_enabled": "M139_DETECTOR_RUNTIME_DENIED",
    "loop_intervention_enabled": "M139_LOOP_INTERVENTION_DENIED",
    "autonomous_recovery_execution_enabled": "M139_RECOVERY_EXECUTION_DENIED",
    "retry_execution_enabled": "M139_RETRY_EXECUTION_DENIED",
    "resume_execution_enabled": "M139_RESUME_EXECUTION_DENIED",
    "rollback_execution_enabled": "M139_ROLLBACK_EXECUTION_DENIED",
    "dependency_execution_enabled": "M139_DEPENDENCY_EXECUTION_DENIED",
    "browser_action_enabled": "M139_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M139_CONNECTOR_ACTION_DENIED",
    "connector_write_enabled": "M139_CONNECTOR_WRITE_DENIED",
    "account_auth_enabled": "M139_ACCOUNT_AUTH_DENIED",
    "tool_execution_enabled": "M139_TOOL_EXECUTION_DENIED",
    "execution_enabled": "M139_EXECUTION_DENIED",
    "shell_execution_enabled": "M139_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M139_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M139_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M139_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M139_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M139_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_enabled": "M139_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M139_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M139_MODEL_CALL_DENIED",
    "memory_write_enabled": "M139_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M139_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M139_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M139_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M139_DEPENDENCY_DENIED",
    "beta_release_enabled": "M139_BETA_RELEASE_DENIED",
    "production_authority_granted": "M139_PRODUCTION_AUTHORITY_DENIED",
}

_M139_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M139_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "dependency_requested": "M139_DEPENDENCY_DENIED",
    "beta_release_requested": "M139_BETA_RELEASE_DENIED",
    "production_authority_requested": "M139_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_abuse_log": "M139_RAW_ABUSE_LOG_DENIED",
    "contains_raw_loop_trace": "M139_RAW_LOOP_TRACE_DENIED",
    "contains_raw_prompt": "M139_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M139_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M139_COOKIE_OR_CREDENTIAL_DENIED",
    "contains_secret": "M139_SECRET_DENIED",
}

_M139_DECISION_REQUIRED = {
    "contract_only": "M139_CONTRACT_ONLY_REQUIRED",
    "review_only": "M139_REVIEW_ONLY_REQUIRED",
    "autonomy_abuse_loop_detection_only": "M139_ABUSE_LOOP_DETECTION_ONLY_REQUIRED",
    "deterministic": "M139_DETERMINISTIC_REQUIRED",
    "local_only": "M139_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M139_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_bound": "M139_EXACT_SCOPE_REQUIRED",
    "mode5_bound": "M139_MODE5_REQUIRED",
    "m138_error_guardrail_bound": "M139_M138_BOUNDARY_REQUIRED",
    "m137_browser_connector_workflow_bound": "M139_M137_BOUNDARY_REQUIRED",
    "m136_dependency_execution_bound": "M139_M136_BOUNDARY_REQUIRED",
    "m135_recovery_planner_bound": "M139_M135_BOUNDARY_REQUIRED",
    "m134_human_checkpoint_bound": "M139_M134_BOUNDARY_REQUIRED",
    "m133_supervisor_bound": "M139_M133_BOUNDARY_REQUIRED",
    "m132_trusted_workflow_bound": "M139_M132_BOUNDARY_REQUIRED",
    "abuse_signal_bound": "M139_ABUSE_SIGNAL_REF_REQUIRED",
    "loop_signal_bound": "M139_LOOP_SIGNAL_REF_REQUIRED",
    "pattern_policy_bound": "M139_PATTERN_POLICY_REQUIRED",
    "threshold_policy_bound": "M139_THRESHOLD_POLICY_REQUIRED",
    "intervention_plan_bound": "M139_INTERVENTION_PLAN_REQUIRED",
    "escalation_plan_bound": "M139_ESCALATION_PLAN_REQUIRED",
    "human_checkpoint_bound": "M139_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_bound": "M139_AUDIT_REPLAY_REQUIRED",
    "revocation_bound": "M139_REVOCATION_REQUIRED",
    "kill_switch_bound": "M139_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M139_NO_EFFECT_RECEIPT_REQUIRED",
}

_M139_DECISION_DENIALS = {
    "abuse_detection_runtime_authorized": "M139_ABUSE_DETECTION_RUNTIME_DENIED",
    "loop_detection_runtime_authorized": "M139_LOOP_DETECTION_RUNTIME_DENIED",
    "loop_monitor_started": "M139_LOOP_MONITOR_DENIED",
    "detector_runtime_started": "M139_DETECTOR_RUNTIME_DENIED",
    "loop_intervention_authorized": "M139_LOOP_INTERVENTION_DENIED",
    "loop_intervention_performed": "M139_LOOP_INTERVENTION_DENIED",
    "autonomous_recovery_execution_authorized": "M139_RECOVERY_EXECUTION_DENIED",
    "retry_execution_performed": "M139_RETRY_EXECUTION_DENIED",
    "resume_execution_performed": "M139_RESUME_EXECUTION_DENIED",
    "rollback_execution_performed": "M139_ROLLBACK_EXECUTION_DENIED",
    "dependency_execution_performed": "M139_DEPENDENCY_EXECUTION_DENIED",
    "browser_action_performed": "M139_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M139_CONNECTOR_ACTION_DENIED",
    "connector_write_performed": "M139_CONNECTOR_WRITE_DENIED",
    "account_auth_performed": "M139_ACCOUNT_AUTH_DENIED",
    "tool_execution_performed": "M139_TOOL_EXECUTION_DENIED",
    "execution_performed": "M139_EXECUTION_DENIED",
    "shell_execution_performed": "M139_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M139_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M139_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M139_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M139_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M139_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_performed": "M139_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M139_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M139_MODEL_CALL_DENIED",
    "memory_write_performed": "M139_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M139_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M139_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M139_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M139_DEPENDENCY_DENIED",
    "beta_release_enabled": "M139_BETA_RELEASE_DENIED",
    "production_authority_granted": "M139_PRODUCTION_AUTHORITY_DENIED",
}

_M139_RECEIPT_DENIALS = {
    "store_raw_abuse_log": "M139_RAW_ABUSE_LOG_DENIED",
    "store_raw_loop_trace": "M139_RAW_LOOP_TRACE_DENIED",
    "store_raw_prompt": "M139_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M139_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_cookie_or_credential": "M139_COOKIE_OR_CREDENTIAL_DENIED",
    "store_secret": "M139_SECRET_DENIED",
    "detector_runtime_started": "M139_DETECTOR_RUNTIME_DENIED",
    "loop_intervention_performed": "M139_LOOP_INTERVENTION_DENIED",
    "recovery_execution_performed": "M139_RECOVERY_EXECUTION_DENIED",
}
