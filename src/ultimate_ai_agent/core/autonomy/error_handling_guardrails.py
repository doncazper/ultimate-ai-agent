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


ERROR_HANDLING_GUARDRAILS_DOCS = [
    "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS.md",
    "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_POLICY.md",
    "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_NON_GOALS.md",
    "docs/autonomy/M138_TO_M139_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M138_MAX_ERROR_SIGNAL_REFS = 32
M138_MAX_GUARDRAIL_REFS = 24


class ErrorHandlingGuardrailStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _ErrorHandlingGuardrailModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ErrorHandlingGuardrailPolicy(_ErrorHandlingGuardrailModel):
    policy_ref: str = "error-handling-guardrail-policy:m138"
    contract_only: bool = True
    review_only: bool = True
    autonomous_error_handling_guardrails_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m137_browser_connector_workflow_required: bool = True
    m136_dependency_execution_required: bool = True
    m135_recovery_planner_required: bool = True
    m134_human_checkpoint_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    error_signal_required: bool = True
    guardrail_policy_required: bool = True
    retry_policy_required: bool = True
    fallback_policy_required: bool = True
    escalation_policy_required: bool = True
    recovery_plan_required: bool = True
    rollback_plan_required: bool = True
    resume_plan_required: bool = True
    human_checkpoint_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m139_future_only: bool = True
    mode5_runtime_enabled: bool = False
    error_handling_runtime_enabled: bool = False
    error_guardrail_runtime_enabled: bool = False
    autonomous_recovery_execution_enabled: bool = False
    retry_execution_enabled: bool = False
    resume_execution_enabled: bool = False
    rollback_execution_enabled: bool = False
    fallback_action_enabled: bool = False
    escalation_action_enabled: bool = False
    loop_recovery_enabled: bool = False
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
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED") from exc
        return self


class ErrorHandlingGuardrailRequest(_ErrorHandlingGuardrailModel):
    request_ref: str
    guardrail_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m137_combined_workflow_decision_ref: str
    m136_dependency_execution_decision_ref: str
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    error_signal_refs: list[str]
    guardrail_policy_ref: str
    failure_mode_ref: str
    retry_policy_ref: str
    fallback_policy_ref: str
    escalation_policy_ref: str
    recovery_plan_ref: str
    rollback_plan_ref: str
    resume_plan_ref: str
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
    max_error_signals: int = Field(gt=0, le=M138_MAX_ERROR_SIGNAL_REFS)
    max_guardrail_refs: int = Field(gt=0, le=M138_MAX_GUARDRAIL_REFS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_guardrail_summary: str
    contract_only: bool = True
    review_only: bool = True
    autonomous_error_handling_guardrails_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    error_handling_runtime_requested: bool = False
    error_guardrail_runtime_requested: bool = False
    autonomous_recovery_execution_requested: bool = False
    retry_execution_requested: bool = False
    resume_execution_requested: bool = False
    rollback_execution_requested: bool = False
    fallback_action_requested: bool = False
    escalation_action_requested: bool = False
    loop_recovery_requested: bool = False
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
    contains_raw_error_log: bool = False
    contains_raw_stack_trace: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_cookie_or_credential: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M138_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M138_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M138_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.error_signal_refs,
            "error_signal_ref",
            "M138_ERROR_SIGNAL_REF_REQUIRED",
            max_count=M138_MAX_ERROR_SIGNAL_REFS,
        )
        if len(self.error_signal_refs) > self.max_error_signals:
            raise ValueError("M138_ERROR_SIGNAL_LIMIT_DENIED")
        if self.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M138_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M138_RISK_CEILING_DENIED")
        _validate_required_bool(self.contract_only, "M138_CONTRACT_ONLY_REQUIRED")
        _validate_required_bool(self.review_only, "M138_REVIEW_ONLY_REQUIRED")
        _validate_required_bool(
            self.autonomous_error_handling_guardrails_only,
            "M138_ERROR_GUARDRAILS_ONLY_REQUIRED",
        )
        _validate_required_bool(self.deterministic, "M138_DETERMINISTIC_REQUIRED")
        _validate_required_bool(self.local_only, "M138_LOCAL_ONLY_REQUIRED")
        _validate_required_bool(self.safe_refs_only, "M138_SAFE_REFS_ONLY_REQUIRED")
        try:
            _validate_safe_payload(self.safe_guardrail_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED") from exc
        _deny_enabled(_M138_REQUEST_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M138_SIDE_EFFECTS_DENIED")
        return self


class ErrorHandlingGuardrailReceiptPlan(_ErrorHandlingGuardrailModel):
    receipt_plan_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_error_signal_refs_only: bool = True
    store_guardrail_policy_refs_only: bool = True
    store_raw_error_log: bool = False
    store_raw_stack_trace: bool = False
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_cookie_or_credential: bool = False
    store_secret: bool = False
    retry_execution_performed: bool = False
    rollback_execution_performed: bool = False
    resume_execution_performed: bool = False
    recovery_execution_performed: bool = False
    error_handling_runtime_started: bool = False
    error_signal_refs: list[str]
    guardrail_policy_ref: str
    safe_receipt_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m61_ref(self.guardrail_policy_ref, "guardrail_policy_ref")
        _validate_ref_list(
            self.error_signal_refs,
            "error_signal_ref",
            "M138_ERROR_SIGNAL_REF_REQUIRED",
            max_count=M138_MAX_ERROR_SIGNAL_REFS,
        )
        try:
            _validate_safe_payload(self.safe_receipt_summary)
        except ValueError as exc:
            raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED") from exc
        for field, reason in _M138_RECEIPT_DENIALS.items():
            if getattr(self, field):
                raise ValueError(reason)
        return self


class ErrorHandlingGuardrailDecision(_ErrorHandlingGuardrailModel):
    decision_ref: str
    status: ErrorHandlingGuardrailStatus = ErrorHandlingGuardrailStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    contract_only: bool = True
    review_only: bool = True
    autonomous_error_handling_guardrails_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m137_browser_connector_workflow_bound: bool = True
    m136_dependency_execution_bound: bool = True
    m135_recovery_planner_bound: bool = True
    m134_human_checkpoint_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    error_signal_bound: bool = True
    guardrail_policy_bound: bool = True
    retry_policy_bound: bool = True
    fallback_policy_bound: bool = True
    escalation_policy_bound: bool = True
    recovery_plan_bound: bool = True
    rollback_plan_bound: bool = True
    resume_plan_bound: bool = True
    human_checkpoint_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    error_handling_runtime_authorized: bool = False
    error_guardrail_runtime_started: bool = False
    autonomous_recovery_execution_authorized: bool = False
    retry_execution_authorized: bool = False
    retry_execution_performed: bool = False
    resume_execution_performed: bool = False
    rollback_execution_authorized: bool = False
    rollback_execution_performed: bool = False
    fallback_action_performed: bool = False
    escalation_action_performed: bool = False
    loop_recovery_performed: bool = False
    dependency_execution_authorized: bool = False
    dependency_execution_performed: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    connector_write_performed: bool = False
    account_auth_performed: bool = False
    tool_execution_authorized: bool = False
    tool_execution_performed: bool = False
    execution_authorized: bool = False
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
    error_signal_refs: list[str]
    guardrail_policy_ref: str
    recovery_plan_ref: str
    rollback_plan_ref: str
    resume_plan_ref: str
    receipt_plan: ErrorHandlingGuardrailReceiptPlan
    safe_decision_summary: str
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.guardrail_policy_ref, "guardrail_policy_ref"),
            (self.recovery_plan_ref, "recovery_plan_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.resume_plan_ref, "resume_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(
            self.error_signal_refs,
            "error_signal_ref",
            "M138_ERROR_SIGNAL_REF_REQUIRED",
            max_count=M138_MAX_ERROR_SIGNAL_REFS,
        )
        if self.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M138_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M138_RISK_CEILING_DENIED")
        for field, reason in _M138_DECISION_REQUIRED.items():
            if not getattr(self, field):
                raise ValueError(reason)
        _deny_enabled(_M138_DECISION_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M138_SIDE_EFFECTS_DENIED")
        try:
            _validate_safe_payload(self.safe_decision_summary)
        except ValueError as exc:
            raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED") from exc
        return self


def build_error_handling_guardrail_decision(
    request: ErrorHandlingGuardrailRequest,
    *,
    policy: ErrorHandlingGuardrailPolicy | None = None,
) -> ErrorHandlingGuardrailDecision:
    validate_error_handling_guardrail_policy(policy or ErrorHandlingGuardrailPolicy())
    validate_error_handling_guardrail_request(request)
    receipt_plan = ErrorHandlingGuardrailReceiptPlan(
        receipt_plan_ref=request.no_effect_receipt_plan_ref,
        error_signal_refs=list(request.error_signal_refs),
        guardrail_policy_ref=request.guardrail_policy_ref,
        safe_receipt_summary=(
            "M138 records safe autonomous error handling guardrail refs for "
            "review only; no retry, rollback, or recovery execution occurs."
        ),
    )
    return ErrorHandlingGuardrailDecision(
        decision_ref=f"error-handling-guardrail-decision:{_ref_suffix(request.request_ref)}",
        error_signal_refs=list(request.error_signal_refs),
        guardrail_policy_ref=request.guardrail_policy_ref,
        recovery_plan_ref=request.recovery_plan_ref,
        rollback_plan_ref=request.rollback_plan_ref,
        resume_plan_ref=request.resume_plan_ref,
        receipt_plan=receipt_plan,
        safe_decision_summary=(
            "M138 is a contract-only autonomous error handling guardrail "
            "review envelope; M139 remains future."
        ),
        reason_codes=[
            "M138_AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_CONTRACT_ONLY",
            "M138_EXACT_ERROR_SCOPE_REQUIRED",
            "M138_NO_ERROR_HANDLING_RUNTIME",
            "M138_NO_RETRY_OR_ROLLBACK_EXECUTION",
            "M139_REMAINS_FUTURE",
        ],
    )


def validate_error_handling_guardrail_policy(
    policy: ErrorHandlingGuardrailPolicy,
) -> ErrorHandlingGuardrailPolicy:
    payload = _model_payload(policy)
    for field, reason in _M138_POLICY_REQUIRED.items():
        if not payload.get(field):
            raise ValueError(reason)
    _deny_enabled(_M138_POLICY_DENIALS, payload)
    if _has_secret_like_extra(payload, ErrorHandlingGuardrailPolicy):
        raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED")
    validated = ErrorHandlingGuardrailPolicy.model_validate(payload)
    for field, reason in _M138_POLICY_REQUIRED.items():
        if not getattr(validated, field):
            raise ValueError(reason)
    _deny_enabled(_M138_POLICY_DENIALS, _model_payload(validated))
    return validated


def validate_error_handling_guardrail_request(
    request: ErrorHandlingGuardrailRequest,
) -> ErrorHandlingGuardrailRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, ErrorHandlingGuardrailRequest):
        raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED")
    _deny_enabled(_M138_REQUEST_DENIALS, payload)
    validated = ErrorHandlingGuardrailRequest.model_validate(payload)
    _deny_enabled(_M138_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M138_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M138_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M138_RISK_CEILING_DENIED")
    if len(validated.error_signal_refs) > validated.max_error_signals:
        raise ValueError("M138_ERROR_SIGNAL_LIMIT_DENIED")
    return validated


def validate_error_handling_guardrail_decision(
    decision: ErrorHandlingGuardrailDecision,
) -> ErrorHandlingGuardrailDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, ErrorHandlingGuardrailDecision):
        raise ValueError("M138_SECRET_LIKE_ERROR_GUARDRAIL_CONTENT_DENIED")
    _deny_enabled(_M138_DECISION_DENIALS, payload)
    receipt_payload = payload.get("receipt_plan", {})
    if isinstance(receipt_payload, dict):
        _deny_enabled(_M138_RECEIPT_DENIALS, receipt_payload)
    validated = ErrorHandlingGuardrailDecision.model_validate(payload)
    for field, reason in _M138_DECISION_REQUIRED.items():
        if not getattr(validated, field):
            raise ValueError(reason)
    if validated.status != ErrorHandlingGuardrailStatus.ready_for_review:
        raise ValueError("M138_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M138_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M138_RISK_CEILING_DENIED")
    _deny_enabled(_M138_DECISION_DENIALS, _model_payload(validated))
    _validate_m138_receipt_plan(validated.receipt_plan)
    if validated.side_effects_performed:
        raise ValueError("M138_SIDE_EFFECTS_DENIED")
    if (
        "M138_AUTONOMOUS_ERROR_HANDLING_GUARDRAILS_CONTRACT_ONLY"
        not in validated.reason_codes
    ):
        raise ValueError("M138_REASON_CODE_REQUIRED")
    return validated


def _validate_m138_receipt_plan(
    receipt_plan: ErrorHandlingGuardrailReceiptPlan,
) -> ErrorHandlingGuardrailReceiptPlan:
    payload = _model_payload(receipt_plan)
    _deny_enabled(_M138_RECEIPT_DENIALS, payload)
    return ErrorHandlingGuardrailReceiptPlan.model_validate(payload)


def _request_ref_pairs(request: ErrorHandlingGuardrailRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.guardrail_plan_ref, "guardrail_plan_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (
            request.m137_combined_workflow_decision_ref,
            "m137_combined_workflow_decision_ref",
        ),
        (
            request.m136_dependency_execution_decision_ref,
            "m136_dependency_execution_decision_ref",
        ),
        (
            request.m135_recovery_planner_decision_ref,
            "m135_recovery_planner_decision_ref",
        ),
        (
            request.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (request.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            request.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (request.guardrail_policy_ref, "guardrail_policy_ref"),
        (request.failure_mode_ref, "failure_mode_ref"),
        (request.retry_policy_ref, "retry_policy_ref"),
        (request.fallback_policy_ref, "fallback_policy_ref"),
        (request.escalation_policy_ref, "escalation_policy_ref"),
        (request.recovery_plan_ref, "recovery_plan_ref"),
        (request.rollback_plan_ref, "rollback_plan_ref"),
        (request.resume_plan_ref, "resume_plan_ref"),
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


_M138_POLICY_REQUIRED = {
    "contract_only": "M138_CONTRACT_ONLY_REQUIRED",
    "review_only": "M138_REVIEW_ONLY_REQUIRED",
    "autonomous_error_handling_guardrails_only": "M138_ERROR_GUARDRAILS_ONLY_REQUIRED",
    "deterministic": "M138_DETERMINISTIC_REQUIRED",
    "local_only": "M138_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M138_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_required": "M138_EXACT_SCOPE_REQUIRED",
    "mode5_required": "M138_MODE5_REQUIRED",
    "m137_browser_connector_workflow_required": "M138_M137_BOUNDARY_REQUIRED",
    "m136_dependency_execution_required": "M138_M136_BOUNDARY_REQUIRED",
    "m135_recovery_planner_required": "M138_M135_BOUNDARY_REQUIRED",
    "m134_human_checkpoint_required": "M138_M134_BOUNDARY_REQUIRED",
    "m133_supervisor_required": "M138_M133_BOUNDARY_REQUIRED",
    "m132_trusted_workflow_required": "M138_M132_BOUNDARY_REQUIRED",
    "error_signal_required": "M138_ERROR_SIGNAL_REF_REQUIRED",
    "guardrail_policy_required": "M138_GUARDRAIL_POLICY_REQUIRED",
    "retry_policy_required": "M138_RETRY_POLICY_REQUIRED",
    "fallback_policy_required": "M138_FALLBACK_POLICY_REQUIRED",
    "escalation_policy_required": "M138_ESCALATION_POLICY_REQUIRED",
    "recovery_plan_required": "M138_RECOVERY_PLAN_REQUIRED",
    "rollback_plan_required": "M138_ROLLBACK_PLAN_REQUIRED",
    "resume_plan_required": "M138_RESUME_PLAN_REQUIRED",
    "human_checkpoint_required": "M138_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_required": "M138_AUDIT_REPLAY_REQUIRED",
    "revocation_required": "M138_REVOCATION_REQUIRED",
    "kill_switch_required": "M138_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M138_NO_EFFECT_RECEIPT_REQUIRED",
    "m139_future_only": "M139_REMAINS_FUTURE",
}

_M138_POLICY_DENIALS = {
    "mode5_runtime_enabled": "M138_MODE5_RUNTIME_DENIED",
    "error_handling_runtime_enabled": "M138_ERROR_HANDLING_RUNTIME_DENIED",
    "error_guardrail_runtime_enabled": "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
    "autonomous_recovery_execution_enabled": "M138_RECOVERY_EXECUTION_DENIED",
    "retry_execution_enabled": "M138_RETRY_EXECUTION_DENIED",
    "resume_execution_enabled": "M138_RESUME_EXECUTION_DENIED",
    "rollback_execution_enabled": "M138_ROLLBACK_EXECUTION_DENIED",
    "fallback_action_enabled": "M138_FALLBACK_ACTION_DENIED",
    "escalation_action_enabled": "M138_ESCALATION_ACTION_DENIED",
    "loop_recovery_enabled": "M138_LOOP_RECOVERY_DENIED",
    "dependency_execution_enabled": "M138_DEPENDENCY_EXECUTION_DENIED",
    "browser_action_enabled": "M138_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M138_CONNECTOR_ACTION_DENIED",
    "connector_write_enabled": "M138_CONNECTOR_WRITE_DENIED",
    "account_auth_enabled": "M138_ACCOUNT_AUTH_DENIED",
    "tool_execution_enabled": "M138_TOOL_EXECUTION_DENIED",
    "execution_enabled": "M138_EXECUTION_DENIED",
    "shell_execution_enabled": "M138_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M138_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M138_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M138_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M138_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M138_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_enabled": "M138_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M138_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M138_MODEL_CALL_DENIED",
    "memory_write_enabled": "M138_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M138_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M138_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M138_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M138_DEPENDENCY_DENIED",
    "beta_release_enabled": "M138_BETA_RELEASE_DENIED",
    "production_authority_granted": "M138_PRODUCTION_AUTHORITY_DENIED",
}

_M138_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M138_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "dependency_requested": "M138_DEPENDENCY_DENIED",
    "production_authority_requested": "M138_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_error_log": "M138_RAW_ERROR_LOG_DENIED",
    "contains_raw_stack_trace": "M138_RAW_STACK_TRACE_DENIED",
    "contains_raw_prompt": "M138_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M138_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M138_COOKIE_OR_CREDENTIAL_DENIED",
    "contains_secret": "M138_SECRET_DENIED",
}

_M138_DECISION_REQUIRED = {
    "contract_only": "M138_CONTRACT_ONLY_REQUIRED",
    "review_only": "M138_REVIEW_ONLY_REQUIRED",
    "autonomous_error_handling_guardrails_only": "M138_ERROR_GUARDRAILS_ONLY_REQUIRED",
    "deterministic": "M138_DETERMINISTIC_REQUIRED",
    "local_only": "M138_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M138_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_bound": "M138_EXACT_SCOPE_REQUIRED",
    "mode5_bound": "M138_MODE5_REQUIRED",
    "m137_browser_connector_workflow_bound": "M138_M137_BOUNDARY_REQUIRED",
    "m136_dependency_execution_bound": "M138_M136_BOUNDARY_REQUIRED",
    "m135_recovery_planner_bound": "M138_M135_BOUNDARY_REQUIRED",
    "m134_human_checkpoint_bound": "M138_M134_BOUNDARY_REQUIRED",
    "m133_supervisor_bound": "M138_M133_BOUNDARY_REQUIRED",
    "m132_trusted_workflow_bound": "M138_M132_BOUNDARY_REQUIRED",
    "error_signal_bound": "M138_ERROR_SIGNAL_REF_REQUIRED",
    "guardrail_policy_bound": "M138_GUARDRAIL_POLICY_REQUIRED",
    "retry_policy_bound": "M138_RETRY_POLICY_REQUIRED",
    "fallback_policy_bound": "M138_FALLBACK_POLICY_REQUIRED",
    "escalation_policy_bound": "M138_ESCALATION_POLICY_REQUIRED",
    "recovery_plan_bound": "M138_RECOVERY_PLAN_REQUIRED",
    "rollback_plan_bound": "M138_ROLLBACK_PLAN_REQUIRED",
    "resume_plan_bound": "M138_RESUME_PLAN_REQUIRED",
    "human_checkpoint_bound": "M138_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_bound": "M138_AUDIT_REPLAY_REQUIRED",
    "revocation_bound": "M138_REVOCATION_REQUIRED",
    "kill_switch_bound": "M138_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M138_NO_EFFECT_RECEIPT_REQUIRED",
}

_M138_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M138_MODE5_RUNTIME_DENIED",
    "error_handling_runtime_authorized": "M138_ERROR_HANDLING_RUNTIME_DENIED",
    "error_guardrail_runtime_started": "M138_ERROR_GUARDRAIL_RUNTIME_DENIED",
    "autonomous_recovery_execution_authorized": "M138_RECOVERY_EXECUTION_DENIED",
    "retry_execution_authorized": "M138_RETRY_EXECUTION_DENIED",
    "retry_execution_performed": "M138_RETRY_EXECUTION_DENIED",
    "resume_execution_performed": "M138_RESUME_EXECUTION_DENIED",
    "rollback_execution_authorized": "M138_ROLLBACK_EXECUTION_DENIED",
    "rollback_execution_performed": "M138_ROLLBACK_EXECUTION_DENIED",
    "fallback_action_performed": "M138_FALLBACK_ACTION_DENIED",
    "escalation_action_performed": "M138_ESCALATION_ACTION_DENIED",
    "loop_recovery_performed": "M138_LOOP_RECOVERY_DENIED",
    "dependency_execution_authorized": "M138_DEPENDENCY_EXECUTION_DENIED",
    "dependency_execution_performed": "M138_DEPENDENCY_EXECUTION_DENIED",
    "browser_action_performed": "M138_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M138_CONNECTOR_ACTION_DENIED",
    "connector_write_performed": "M138_CONNECTOR_WRITE_DENIED",
    "account_auth_performed": "M138_ACCOUNT_AUTH_DENIED",
    "tool_execution_authorized": "M138_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M138_TOOL_EXECUTION_DENIED",
    "execution_authorized": "M138_EXECUTION_DENIED",
    "execution_performed": "M138_EXECUTION_DENIED",
    "shell_execution_performed": "M138_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M138_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M138_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M138_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M138_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M138_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_performed": "M138_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M138_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M138_MODEL_CALL_DENIED",
    "memory_write_performed": "M138_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M138_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M138_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M138_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M138_DEPENDENCY_DENIED",
    "beta_release_enabled": "M138_BETA_RELEASE_DENIED",
    "production_authority_granted": "M138_PRODUCTION_AUTHORITY_DENIED",
}

_M138_RECEIPT_DENIALS = {
    "store_raw_error_log": "M138_RAW_ERROR_LOG_DENIED",
    "store_raw_stack_trace": "M138_RAW_STACK_TRACE_DENIED",
    "store_raw_prompt": "M138_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M138_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_cookie_or_credential": "M138_COOKIE_OR_CREDENTIAL_DENIED",
    "store_secret": "M138_SECRET_DENIED",
    "retry_execution_performed": "M138_RETRY_EXECUTION_DENIED",
    "rollback_execution_performed": "M138_ROLLBACK_EXECUTION_DENIED",
    "resume_execution_performed": "M138_RESUME_EXECUTION_DENIED",
    "recovery_execution_performed": "M138_RECOVERY_EXECUTION_DENIED",
    "error_handling_runtime_started": "M138_ERROR_HANDLING_RUNTIME_DENIED",
}
