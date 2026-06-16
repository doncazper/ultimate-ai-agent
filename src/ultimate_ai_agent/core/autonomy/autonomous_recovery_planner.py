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


AUTONOMOUS_RECOVERY_PLANNER_DOCS = [
    "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER.md",
    "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_POLICY.md",
    "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMOUS_RECOVERY_PLANNER_NON_GOALS.md",
    "docs/autonomy/M135_TO_M136_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M135_MAX_RECOVERY_WINDOW_SECONDS = 86_400
M135_MAX_RECOVERY_STEP_REFS = 32


class AutonomousRecoveryPlannerStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _AutonomousRecoveryPlannerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomousRecoveryPlannerPolicy(_AutonomousRecoveryPlannerModel):
    policy_ref: str = "autonomous-recovery-planner-policy:m135"
    contract_only: bool = True
    review_only: bool = True
    autonomous_recovery_planner_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m134_human_checkpoint_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    recovery_plan_required: bool = True
    failure_signal_required: bool = True
    recovery_trigger_required: bool = True
    rollback_plan_required: bool = True
    resume_plan_required: bool = True
    human_checkpoint_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m136_future_only: bool = True
    mode5_runtime_enabled: bool = False
    recovery_planner_runtime_enabled: bool = False
    recovery_execution_enabled: bool = False
    retry_execution_enabled: bool = False
    resume_execution_enabled: bool = False
    rollback_execution_enabled: bool = False
    supervisor_runtime_enabled: bool = False
    checkpoint_scheduler_enabled: bool = False
    human_checkpoint_scheduler_enabled: bool = False
    human_checkpoint_prompt_enabled: bool = False
    notification_delivery_enabled: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    autonomous_actions_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    command_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    browser_automation_enabled: bool = False
    browser_form_enabled: bool = False
    authenticated_browser_enabled: bool = False
    download_enabled: bool = False
    upload_enabled: bool = False
    plugin_execution_enabled: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
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
            raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED") from exc
        return self


class AutonomousRecoveryPlannerRequest(_AutonomousRecoveryPlannerModel):
    request_ref: str
    recovery_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    failure_signal_ref: str
    recovery_trigger_ref: str
    recovery_strategy_ref: str
    recovery_step_refs: list[str]
    rollback_plan_ref: str
    resume_plan_ref: str
    checkpoint_ref: str
    human_checkpoint_ref: str
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    requested_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_recovery_window_seconds: int = Field(
        gt=0, le=M135_MAX_RECOVERY_WINDOW_SECONDS
    )
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_recovery_summary: str
    contract_only: bool = True
    review_only: bool = True
    autonomous_recovery_planner_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    recovery_planner_runtime_requested: bool = False
    recovery_execution_requested: bool = False
    retry_execution_requested: bool = False
    resume_execution_requested: bool = False
    rollback_execution_requested: bool = False
    supervisor_runtime_requested: bool = False
    checkpoint_scheduler_requested: bool = False
    human_checkpoint_scheduler_requested: bool = False
    human_checkpoint_prompt_requested: bool = False
    notification_delivery_requested: bool = False
    scheduler_requested: bool = False
    background_worker_requested: bool = False
    autonomous_actions_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    command_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    browser_automation_requested: bool = False
    browser_form_requested: bool = False
    authenticated_browser_requested: bool = False
    download_requested: bool = False
    upload_requested: bool = False
    plugin_execution_requested: bool = False
    connector_runtime_requested: bool = False
    account_auth_requested: bool = False
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
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M135_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M135_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M135_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.recovery_step_refs,
            "recovery_step_ref",
            "M135_RECOVERY_STEP_REF_REQUIRED",
            max_count=M135_MAX_RECOVERY_STEP_REFS,
        )
        try:
            _validate_safe_payload({"safe_recovery_summary": self.safe_recovery_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED") from exc
        return self


class AutonomousRecoveryPlannerReceiptPlan(_AutonomousRecoveryPlannerModel):
    receipt_plan_ref: str
    recovery_plan_ref: str
    scope_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    failure_signal_ref: str
    recovery_trigger_ref: str
    rollback_plan_ref: str
    resume_plan_ref: str
    checkpoint_ref: str
    human_checkpoint_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    recovery_executed: bool = False
    retry_executed: bool = False
    resume_executed: bool = False
    rollback_executed: bool = False
    supervisor_started: bool = False
    checkpoint_scheduled: bool = False
    prompt_sent: bool = False
    notification_delivered: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M135 autonomous recovery planner receipt stores safe refs and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED") from exc
        return self


class AutonomousRecoveryPlannerDecision(_AutonomousRecoveryPlannerModel):
    decision_ref: str
    request_ref: str
    recovery_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    failure_signal_ref: str
    recovery_trigger_ref: str
    recovery_strategy_ref: str
    recovery_step_refs: list[str]
    rollback_plan_ref: str
    resume_plan_ref: str
    checkpoint_ref: str
    human_checkpoint_ref: str
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: AutonomousRecoveryPlannerStatus = (
        AutonomousRecoveryPlannerStatus.ready_for_review
    )
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_recovery_window_seconds: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    autonomous_recovery_planner_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m134_human_checkpoint_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    recovery_plan_bound: bool = True
    failure_signal_bound: bool = True
    recovery_trigger_bound: bool = True
    recovery_strategy_bound: bool = True
    recovery_steps_bound: bool = True
    rollback_plan_bound: bool = True
    resume_plan_bound: bool = True
    checkpoint_bound: bool = True
    human_checkpoint_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    recovery_planner_runtime_authorized: bool = False
    recovery_execution_authorized: bool = False
    recovery_execution_performed: bool = False
    retry_execution_performed: bool = False
    resume_execution_performed: bool = False
    rollback_execution_performed: bool = False
    supervisor_runtime_started: bool = False
    checkpoint_scheduler_started: bool = False
    human_checkpoint_scheduler_started: bool = False
    human_checkpoint_prompt_sent: bool = False
    notification_delivered: bool = False
    scheduler_started: bool = False
    background_worker_started: bool = False
    autonomous_actions_authorized: bool = False
    autonomous_actions_performed: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    tool_execution_authorized: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    browser_automation_performed: bool = False
    browser_form_performed: bool = False
    authenticated_browser_performed: bool = False
    download_performed: bool = False
    upload_performed: bool = False
    plugin_execution_performed: bool = False
    connector_runtime_performed: bool = False
    account_auth_performed: bool = False
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
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    receipt_plan: AutonomousRecoveryPlannerReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M135_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M135_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M135_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.recovery_step_refs,
            "recovery_step_ref",
            "M135_RECOVERY_STEP_REF_REQUIRED",
            max_count=M135_MAX_RECOVERY_STEP_REFS,
        )
        if not self.reason_codes:
            raise ValueError("M135_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED") from exc
        return self


def build_autonomous_recovery_planner_decision(
    request: AutonomousRecoveryPlannerRequest,
    policy: AutonomousRecoveryPlannerPolicy | None = None,
) -> AutonomousRecoveryPlannerDecision:
    active_policy = validate_autonomous_recovery_planner_policy(
        policy or AutonomousRecoveryPlannerPolicy()
    )
    validated_request = validate_autonomous_recovery_planner_request(request)
    decision = AutonomousRecoveryPlannerDecision(
        decision_ref=(
            "autonomous-recovery-planner-decision:"
            f"{_ref_suffix(validated_request.recovery_plan_ref)}"
        ),
        request_ref=validated_request.request_ref,
        recovery_plan_ref=validated_request.recovery_plan_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        m134_human_checkpoint_decision_ref=(
            validated_request.m134_human_checkpoint_decision_ref
        ),
        m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
        m132_trusted_workflow_decision_ref=(
            validated_request.m132_trusted_workflow_decision_ref
        ),
        failure_signal_ref=validated_request.failure_signal_ref,
        recovery_trigger_ref=validated_request.recovery_trigger_ref,
        recovery_strategy_ref=validated_request.recovery_strategy_ref,
        recovery_step_refs=list(validated_request.recovery_step_refs),
        rollback_plan_ref=validated_request.rollback_plan_ref,
        resume_plan_ref=validated_request.resume_plan_ref,
        checkpoint_ref=validated_request.checkpoint_ref,
        human_checkpoint_ref=validated_request.human_checkpoint_ref,
        policy_decision_ref=validated_request.policy_decision_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        max_recovery_window_seconds=validated_request.max_recovery_window_seconds,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        autonomous_recovery_planner_only=(
            active_policy.autonomous_recovery_planner_only
        ),
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        mode5_bound=active_policy.mode5_required,
        m134_human_checkpoint_bound=active_policy.m134_human_checkpoint_required,
        m133_supervisor_bound=active_policy.m133_supervisor_required,
        m132_trusted_workflow_bound=active_policy.m132_trusted_workflow_required,
        recovery_plan_bound=active_policy.recovery_plan_required,
        failure_signal_bound=active_policy.failure_signal_required,
        recovery_trigger_bound=active_policy.recovery_trigger_required,
        recovery_strategy_bound=True,
        recovery_steps_bound=True,
        rollback_plan_bound=active_policy.rollback_plan_required,
        resume_plan_bound=active_policy.resume_plan_required,
        checkpoint_bound=True,
        human_checkpoint_bound=active_policy.human_checkpoint_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        reason_codes=[
            "M135_AUTONOMOUS_RECOVERY_PLANNER_CONTRACT_ONLY",
            "M135_EXACT_RECOVERY_SCOPE_REQUIRED",
            "M135_HUMAN_CHECKPOINT_BINDING_REQUIRED",
            "M135_NO_RECOVERY_EXECUTION",
            "M136_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M135 defines an autonomous recovery planner contract for governed "
            "review only. It binds Mode 5, M134 human checkpoint scheduling "
            "decision, M133 supervisor decision, M132 trusted workflow decision, "
            "failure signal, recovery trigger, recovery strategy, recovery "
            "steps, rollback plan, resume plan, checkpoint, human checkpoint, "
            "risk, audit, replay, revocation, kill-switch, and no-effect "
            "receipt refs. It does not execute recovery, retry, resume, or "
            "rollback work, start supervisor runtime, schedule checkpoints, send "
            "prompts or notifications, run schedulers or background workers, "
            "execute tools, shell, network, browser, plugin, connector, mobile, "
            "remote, model, memory, or context work, add routes or controls, add "
            "dependencies, enable beta, grant production authority, or implement M136."
        ),
        receipt_plan=AutonomousRecoveryPlannerReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            recovery_plan_ref=validated_request.recovery_plan_ref,
            scope_ref=validated_request.scope_ref,
            m134_human_checkpoint_decision_ref=(
                validated_request.m134_human_checkpoint_decision_ref
            ),
            m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
            m132_trusted_workflow_decision_ref=(
                validated_request.m132_trusted_workflow_decision_ref
            ),
            failure_signal_ref=validated_request.failure_signal_ref,
            recovery_trigger_ref=validated_request.recovery_trigger_ref,
            rollback_plan_ref=validated_request.rollback_plan_ref,
            resume_plan_ref=validated_request.resume_plan_ref,
            checkpoint_ref=validated_request.checkpoint_ref,
            human_checkpoint_ref=validated_request.human_checkpoint_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_autonomous_recovery_planner_decision(decision)


def validate_autonomous_recovery_planner_policy(
    policy: AutonomousRecoveryPlannerPolicy,
) -> AutonomousRecoveryPlannerPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, AutonomousRecoveryPlannerPolicy):
        raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED")
    validated = AutonomousRecoveryPlannerPolicy.model_validate(payload)
    for field_name, reason in _M135_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M135_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_autonomous_recovery_planner_request(
    request: AutonomousRecoveryPlannerRequest,
) -> AutonomousRecoveryPlannerRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, AutonomousRecoveryPlannerRequest):
        raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED")
    for field_name, reason in _M135_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = AutonomousRecoveryPlannerRequest.model_validate(payload)
    for field_name, reason in _M135_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M135_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M135_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M135_MODE5_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    return validated


def validate_autonomous_recovery_planner_decision(
    decision: AutonomousRecoveryPlannerDecision,
) -> AutonomousRecoveryPlannerDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, AutonomousRecoveryPlannerDecision):
        raise ValueError("M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED")
    for field_name, reason in _M135_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = AutonomousRecoveryPlannerDecision.model_validate(payload)
    for field_name, reason in _M135_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != AutonomousRecoveryPlannerStatus.ready_for_review:
        raise ValueError("M135_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M135_MODE5_REQUIRED")
    for field_name, reason in _M135_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M135_SIDE_EFFECTS_DENIED")
    if "M135_AUTONOMOUS_RECOVERY_PLANNER_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M135_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: AutonomousRecoveryPlannerReceiptPlan,
) -> AutonomousRecoveryPlannerReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M135_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = AutonomousRecoveryPlannerReceiptPlan.model_validate(payload)
    for field_name, reason in _M135_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M135_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M135_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: AutonomousRecoveryPlannerDecision,
    receipt: AutonomousRecoveryPlannerReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.recovery_plan_ref, decision.recovery_plan_ref),
        (receipt.scope_ref, decision.scope_ref),
        (
            receipt.m134_human_checkpoint_decision_ref,
            decision.m134_human_checkpoint_decision_ref,
        ),
        (receipt.m133_supervisor_decision_ref, decision.m133_supervisor_decision_ref),
        (
            receipt.m132_trusted_workflow_decision_ref,
            decision.m132_trusted_workflow_decision_ref,
        ),
        (receipt.failure_signal_ref, decision.failure_signal_ref),
        (receipt.recovery_trigger_ref, decision.recovery_trigger_ref),
        (receipt.rollback_plan_ref, decision.rollback_plan_ref),
        (receipt.resume_plan_ref, decision.resume_plan_ref),
        (receipt.checkpoint_ref, decision.checkpoint_ref),
        (receipt.human_checkpoint_ref, decision.human_checkpoint_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M135_RECEIPT_BINDING_MISMATCH")


def _validate_ref_list(
    refs: list[str],
    field_name: str,
    reason: str,
    *,
    max_count: int | None = None,
) -> None:
    if not refs:
        raise ValueError(reason)
    if max_count is not None and len(refs) > max_count:
        raise ValueError("M135_REF_LIST_TOO_LONG")
    if len(set(refs)) != len(refs):
        raise ValueError("M135_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk != AutonomyRiskClass.low:
        raise ValueError("M135_RISK_CEILING_DENIED")


def _request_ref_pairs(request: AutonomousRecoveryPlannerRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.recovery_plan_ref, "recovery_plan_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (
            request.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (request.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            request.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (request.failure_signal_ref, "failure_signal_ref"),
        (request.recovery_trigger_ref, "recovery_trigger_ref"),
        (request.recovery_strategy_ref, "recovery_strategy_ref"),
        (request.rollback_plan_ref, "rollback_plan_ref"),
        (request.resume_plan_ref, "resume_plan_ref"),
        (request.checkpoint_ref, "checkpoint_ref"),
        (request.human_checkpoint_ref, "human_checkpoint_ref"),
        (request.policy_decision_ref, "policy_decision_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _receipt_ref_pairs(receipt: AutonomousRecoveryPlannerReceiptPlan):
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.recovery_plan_ref, "recovery_plan_ref"),
        (receipt.scope_ref, "scope_ref"),
        (
            receipt.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (receipt.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            receipt.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (receipt.failure_signal_ref, "failure_signal_ref"),
        (receipt.recovery_trigger_ref, "recovery_trigger_ref"),
        (receipt.rollback_plan_ref, "rollback_plan_ref"),
        (receipt.resume_plan_ref, "resume_plan_ref"),
        (receipt.checkpoint_ref, "checkpoint_ref"),
        (receipt.human_checkpoint_ref, "human_checkpoint_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: AutonomousRecoveryPlannerDecision):
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.recovery_plan_ref, "recovery_plan_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (
            decision.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (decision.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            decision.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (decision.failure_signal_ref, "failure_signal_ref"),
        (decision.recovery_trigger_ref, "recovery_trigger_ref"),
        (decision.recovery_strategy_ref, "recovery_strategy_ref"),
        (decision.rollback_plan_ref, "rollback_plan_ref"),
        (decision.resume_plan_ref, "resume_plan_ref"),
        (decision.checkpoint_ref, "checkpoint_ref"),
        (decision.human_checkpoint_ref, "human_checkpoint_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M135_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M135_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M135_REVIEW_ONLY_REQUIRED"),
    ("autonomous_recovery_planner_only", "M135_RECOVERY_PLANNER_ONLY_REQUIRED"),
    ("deterministic", "M135_DETERMINISTIC_REQUIRED"),
    ("local_only", "M135_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M135_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M135_EXACT_SCOPE_REQUIRED"),
    ("mode5_required", "M135_MODE5_REQUIRED"),
    ("m134_human_checkpoint_required", "M135_M134_HUMAN_CHECKPOINT_REQUIRED"),
    ("m133_supervisor_required", "M135_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_required", "M135_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("recovery_plan_required", "M135_RECOVERY_PLAN_REQUIRED"),
    ("failure_signal_required", "M135_FAILURE_SIGNAL_REQUIRED"),
    ("recovery_trigger_required", "M135_RECOVERY_TRIGGER_REQUIRED"),
    ("rollback_plan_required", "M135_ROLLBACK_PLAN_REQUIRED"),
    ("resume_plan_required", "M135_RESUME_PLAN_REQUIRED"),
    ("human_checkpoint_required", "M135_HUMAN_CHECKPOINT_REQUIRED"),
    ("audit_replay_required", "M135_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M135_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M135_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M135_NO_EFFECT_RECEIPT_REQUIRED"),
    ("m136_future_only", "M136_FUTURE_ONLY_REQUIRED"),
]

_M135_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M135_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M135_REVIEW_ONLY_REQUIRED"),
    ("autonomous_recovery_planner_only", "M135_RECOVERY_PLANNER_ONLY_REQUIRED"),
    ("deterministic", "M135_DETERMINISTIC_REQUIRED"),
    ("local_only", "M135_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M135_SAFE_REFS_ONLY_REQUIRED"),
]

_M135_DECISION_REQUIRED_TRUE = [
    *_M135_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M135_EXACT_SCOPE_REQUIRED"),
    ("mode5_bound", "M135_MODE5_REQUIRED"),
    ("m134_human_checkpoint_bound", "M135_M134_HUMAN_CHECKPOINT_REQUIRED"),
    ("m133_supervisor_bound", "M135_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_bound", "M135_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("recovery_plan_bound", "M135_RECOVERY_PLAN_REQUIRED"),
    ("failure_signal_bound", "M135_FAILURE_SIGNAL_REQUIRED"),
    ("recovery_trigger_bound", "M135_RECOVERY_TRIGGER_REQUIRED"),
    ("recovery_strategy_bound", "M135_RECOVERY_STRATEGY_REQUIRED"),
    ("recovery_steps_bound", "M135_RECOVERY_STEP_REF_REQUIRED"),
    ("rollback_plan_bound", "M135_ROLLBACK_PLAN_REQUIRED"),
    ("resume_plan_bound", "M135_RESUME_PLAN_REQUIRED"),
    ("checkpoint_bound", "M135_CHECKPOINT_REQUIRED"),
    ("human_checkpoint_bound", "M135_HUMAN_CHECKPOINT_REQUIRED"),
    ("audit_replay_bound", "M135_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M135_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M135_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M135_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M135_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M135_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M135_SAFE_REFS_ONLY_REQUIRED"),
]

_M135_DENIALS = {
    "mode5_runtime_enabled": "M135_MODE5_RUNTIME_DENIED",
    "recovery_planner_runtime_enabled": "M135_RECOVERY_PLANNER_RUNTIME_DENIED",
    "recovery_execution_enabled": "M135_RECOVERY_EXECUTION_DENIED",
    "retry_execution_enabled": "M135_RETRY_EXECUTION_DENIED",
    "resume_execution_enabled": "M135_RESUME_EXECUTION_DENIED",
    "rollback_execution_enabled": "M135_ROLLBACK_EXECUTION_DENIED",
    "supervisor_runtime_enabled": "M135_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_enabled": "M135_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_scheduler_enabled": "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_enabled": "M135_PROMPT_RUNTIME_DENIED",
    "notification_delivery_enabled": "M135_NOTIFICATION_DELIVERY_DENIED",
    "scheduler_enabled": "M135_SCHEDULER_DENIED",
    "background_worker_enabled": "M135_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_enabled": "M135_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M135_EXECUTION_DENIED",
    "tool_execution_enabled": "M135_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M135_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M135_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M135_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M135_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M135_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M135_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M135_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M135_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M135_DOWNLOAD_DENIED",
    "upload_enabled": "M135_UPLOAD_DENIED",
    "plugin_execution_enabled": "M135_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M135_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M135_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M135_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M135_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M135_MODEL_CALL_DENIED",
    "memory_write_enabled": "M135_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M135_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M135_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M135_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M135_DEPENDENCY_DENIED",
    "beta_release_enabled": "M135_BETA_RELEASE_DENIED",
    "production_authority_granted": "M135_PRODUCTION_AUTHORITY_DENIED",
}

_M135_REQUEST_DENIALS = {
    "mode5_runtime_requested": "M135_MODE5_RUNTIME_DENIED",
    "recovery_planner_runtime_requested": "M135_RECOVERY_PLANNER_RUNTIME_DENIED",
    "recovery_execution_requested": "M135_RECOVERY_EXECUTION_DENIED",
    "retry_execution_requested": "M135_RETRY_EXECUTION_DENIED",
    "resume_execution_requested": "M135_RESUME_EXECUTION_DENIED",
    "rollback_execution_requested": "M135_ROLLBACK_EXECUTION_DENIED",
    "supervisor_runtime_requested": "M135_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_requested": "M135_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_scheduler_requested": "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_requested": "M135_PROMPT_RUNTIME_DENIED",
    "notification_delivery_requested": "M135_NOTIFICATION_DELIVERY_DENIED",
    "scheduler_requested": "M135_SCHEDULER_DENIED",
    "background_worker_requested": "M135_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_requested": "M135_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M135_EXECUTION_DENIED",
    "tool_execution_requested": "M135_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M135_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M135_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M135_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M135_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M135_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M135_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M135_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M135_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M135_DOWNLOAD_DENIED",
    "upload_requested": "M135_UPLOAD_DENIED",
    "plugin_execution_requested": "M135_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M135_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M135_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M135_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M135_REMOTE_EXECUTION_DENIED",
    "model_call_requested": "M135_MODEL_CALL_DENIED",
    "memory_write_requested": "M135_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M135_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M135_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M135_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M135_DEPENDENCY_DENIED",
    "beta_release_requested": "M135_BETA_RELEASE_DENIED",
    "production_authority_requested": "M135_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M135_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M135_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED",
}

_M135_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M135_MODE5_RUNTIME_DENIED",
    "recovery_planner_runtime_authorized": "M135_RECOVERY_PLANNER_RUNTIME_DENIED",
    "recovery_execution_authorized": "M135_RECOVERY_EXECUTION_DENIED",
    "recovery_execution_performed": "M135_RECOVERY_EXECUTION_DENIED",
    "retry_execution_performed": "M135_RETRY_EXECUTION_DENIED",
    "resume_execution_performed": "M135_RESUME_EXECUTION_DENIED",
    "rollback_execution_performed": "M135_ROLLBACK_EXECUTION_DENIED",
    "supervisor_runtime_started": "M135_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_started": "M135_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_scheduler_started": "M135_HUMAN_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_sent": "M135_PROMPT_RUNTIME_DENIED",
    "notification_delivered": "M135_NOTIFICATION_DELIVERY_DENIED",
    "scheduler_started": "M135_SCHEDULER_DENIED",
    "background_worker_started": "M135_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_authorized": "M135_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M135_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M135_EXECUTION_DENIED",
    "execution_performed": "M135_EXECUTION_DENIED",
    "tool_execution_authorized": "M135_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M135_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M135_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M135_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M135_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M135_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M135_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M135_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M135_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M135_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M135_DOWNLOAD_DENIED",
    "upload_performed": "M135_UPLOAD_DENIED",
    "plugin_execution_performed": "M135_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M135_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M135_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M135_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M135_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M135_MODEL_CALL_DENIED",
    "memory_write_performed": "M135_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M135_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M135_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M135_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M135_DEPENDENCY_DENIED",
    "beta_release_enabled": "M135_BETA_RELEASE_DENIED",
    "production_authority_granted": "M135_PRODUCTION_AUTHORITY_DENIED",
}

_M135_RECEIPT_DENIALS = {
    "store_raw_prompt": "M135_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M135_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M135_SECRET_LIKE_RECOVERY_CONTENT_DENIED",
    "recovery_executed": "M135_RECOVERY_EXECUTION_DENIED",
    "retry_executed": "M135_RETRY_EXECUTION_DENIED",
    "resume_executed": "M135_RESUME_EXECUTION_DENIED",
    "rollback_executed": "M135_ROLLBACK_EXECUTION_DENIED",
    "supervisor_started": "M135_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduled": "M135_CHECKPOINT_SCHEDULER_DENIED",
    "prompt_sent": "M135_PROMPT_RUNTIME_DENIED",
    "notification_delivered": "M135_NOTIFICATION_DELIVERY_DENIED",
    "execution_performed": "M135_EXECUTION_DENIED",
}
