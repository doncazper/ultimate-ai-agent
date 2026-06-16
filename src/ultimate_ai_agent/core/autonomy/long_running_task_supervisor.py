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


LONG_RUNNING_TASK_SUPERVISOR_DOCS = [
    "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR.md",
    "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_POLICY.md",
    "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_RECEIPT_PLAN.md",
    "docs/autonomy/LONG_RUNNING_TASK_SUPERVISOR_NON_GOALS.md",
    "docs/autonomy/M133_TO_M134_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M133_MAX_SUPERVISOR_WINDOW_SECONDS = 86_400
M133_MAX_CHECKPOINT_REFS = 64


class LongRunningTaskSupervisorStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _LongRunningTaskSupervisorModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LongRunningTaskSupervisorPolicy(_LongRunningTaskSupervisorModel):
    policy_ref: str = "long-running-task-supervisor-policy:m133"
    contract_only: bool = True
    review_only: bool = True
    long_running_supervisor_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m132_trusted_workflow_required: bool = True
    m131_work_session_required: bool = True
    supervisor_plan_required: bool = True
    task_state_required: bool = True
    heartbeat_plan_required: bool = True
    checkpoint_plan_required: bool = True
    context_budget_required: bool = True
    pause_resume_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m134_future_only: bool = True
    mode5_runtime_enabled: bool = False
    supervisor_runtime_enabled: bool = False
    long_running_supervisor_start_enabled: bool = False
    task_supervision_enabled: bool = False
    heartbeat_monitor_enabled: bool = False
    checkpoint_scheduler_enabled: bool = False
    resume_execution_enabled: bool = False
    recovery_execution_enabled: bool = False
    human_checkpoint_scheduling_enabled: bool = False
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
            raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED") from exc
        return self


class LongRunningTaskSupervisorRequest(_LongRunningTaskSupervisorModel):
    request_ref: str
    supervisor_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m132_trusted_workflow_decision_ref: str
    m131_work_session_decision_ref: str
    supervisor_plan_ref: str
    task_ref: str
    run_state_ref: str
    heartbeat_plan_ref: str
    checkpoint_plan_ref: str
    checkpoint_refs: list[str]
    context_budget_ref: str
    pause_condition_refs: list[str]
    resume_condition_refs: list[str]
    stop_condition_refs: list[str]
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
    max_supervisor_window_seconds: int = Field(gt=0, le=M133_MAX_SUPERVISOR_WINDOW_SECONDS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_task_summary: str
    contract_only: bool = True
    review_only: bool = True
    long_running_supervisor_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    supervisor_runtime_requested: bool = False
    long_running_supervisor_start_requested: bool = False
    task_supervision_requested: bool = False
    heartbeat_monitor_requested: bool = False
    checkpoint_scheduler_requested: bool = False
    resume_execution_requested: bool = False
    recovery_execution_requested: bool = False
    human_checkpoint_scheduling_requested: bool = False
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
        _validate_ref_list(self.resource_refs, "resource_ref", "M133_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M133_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M133_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.checkpoint_refs,
            "checkpoint_ref",
            "M133_CHECKPOINT_REF_REQUIRED",
            max_count=M133_MAX_CHECKPOINT_REFS,
        )
        _validate_ref_list(
            self.pause_condition_refs,
            "pause_condition_ref",
            "M133_PAUSE_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.resume_condition_refs,
            "resume_condition_ref",
            "M133_RESUME_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M133_STOP_CONDITION_REF_REQUIRED",
        )
        try:
            _validate_safe_payload({"safe_task_summary": self.safe_task_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED") from exc
        return self


class LongRunningTaskSupervisorReceiptPlan(_LongRunningTaskSupervisorModel):
    receipt_plan_ref: str
    supervisor_ref: str
    scope_ref: str
    m132_trusted_workflow_decision_ref: str
    m131_work_session_decision_ref: str
    supervisor_plan_ref: str
    task_ref: str
    run_state_ref: str
    heartbeat_plan_ref: str
    checkpoint_plan_ref: str
    context_budget_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    supervisor_started: bool = False
    heartbeat_monitor_started: bool = False
    checkpoint_scheduler_started: bool = False
    resume_execution_performed: bool = False
    recovery_execution_performed: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M133 long-running task supervisor receipt stores safe refs and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED") from exc
        return self


class LongRunningTaskSupervisorDecision(_LongRunningTaskSupervisorModel):
    decision_ref: str
    request_ref: str
    supervisor_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m132_trusted_workflow_decision_ref: str
    m131_work_session_decision_ref: str
    supervisor_plan_ref: str
    task_ref: str
    run_state_ref: str
    heartbeat_plan_ref: str
    checkpoint_plan_ref: str
    checkpoint_refs: list[str]
    context_budget_ref: str
    pause_condition_refs: list[str]
    resume_condition_refs: list[str]
    stop_condition_refs: list[str]
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: LongRunningTaskSupervisorStatus = LongRunningTaskSupervisorStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_supervisor_window_seconds: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    long_running_supervisor_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    m131_work_session_bound: bool = True
    supervisor_plan_bound: bool = True
    task_state_bound: bool = True
    heartbeat_plan_bound: bool = True
    checkpoint_plan_bound: bool = True
    context_budget_bound: bool = True
    pause_resume_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    supervisor_runtime_authorized: bool = False
    long_running_supervisor_start_authorized: bool = False
    supervisor_started: bool = False
    task_supervision_active: bool = False
    heartbeat_monitor_started: bool = False
    checkpoint_scheduler_started: bool = False
    resume_execution_performed: bool = False
    recovery_execution_performed: bool = False
    human_checkpoint_scheduling_performed: bool = False
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
    receipt_plan: LongRunningTaskSupervisorReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M133_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M133_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M133_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.checkpoint_refs,
            "checkpoint_ref",
            "M133_CHECKPOINT_REF_REQUIRED",
            max_count=M133_MAX_CHECKPOINT_REFS,
        )
        _validate_ref_list(
            self.pause_condition_refs,
            "pause_condition_ref",
            "M133_PAUSE_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.resume_condition_refs,
            "resume_condition_ref",
            "M133_RESUME_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M133_STOP_CONDITION_REF_REQUIRED",
        )
        if not self.reason_codes:
            raise ValueError("M133_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED") from exc
        return self


def build_long_running_task_supervisor_decision(
    request: LongRunningTaskSupervisorRequest,
    policy: LongRunningTaskSupervisorPolicy | None = None,
) -> LongRunningTaskSupervisorDecision:
    active_policy = validate_long_running_task_supervisor_policy(
        policy or LongRunningTaskSupervisorPolicy()
    )
    validated_request = validate_long_running_task_supervisor_request(request)
    decision = LongRunningTaskSupervisorDecision(
        decision_ref=f"long-running-task-supervisor-decision:{_ref_suffix(validated_request.supervisor_ref)}",
        request_ref=validated_request.request_ref,
        supervisor_ref=validated_request.supervisor_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        m132_trusted_workflow_decision_ref=validated_request.m132_trusted_workflow_decision_ref,
        m131_work_session_decision_ref=validated_request.m131_work_session_decision_ref,
        supervisor_plan_ref=validated_request.supervisor_plan_ref,
        task_ref=validated_request.task_ref,
        run_state_ref=validated_request.run_state_ref,
        heartbeat_plan_ref=validated_request.heartbeat_plan_ref,
        checkpoint_plan_ref=validated_request.checkpoint_plan_ref,
        checkpoint_refs=list(validated_request.checkpoint_refs),
        context_budget_ref=validated_request.context_budget_ref,
        pause_condition_refs=list(validated_request.pause_condition_refs),
        resume_condition_refs=list(validated_request.resume_condition_refs),
        stop_condition_refs=list(validated_request.stop_condition_refs),
        policy_decision_ref=validated_request.policy_decision_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        max_supervisor_window_seconds=validated_request.max_supervisor_window_seconds,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        long_running_supervisor_only=active_policy.long_running_supervisor_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        mode5_bound=active_policy.mode5_required,
        m132_trusted_workflow_bound=active_policy.m132_trusted_workflow_required,
        m131_work_session_bound=active_policy.m131_work_session_required,
        supervisor_plan_bound=active_policy.supervisor_plan_required,
        task_state_bound=active_policy.task_state_required,
        heartbeat_plan_bound=active_policy.heartbeat_plan_required,
        checkpoint_plan_bound=active_policy.checkpoint_plan_required,
        context_budget_bound=active_policy.context_budget_required,
        pause_resume_bound=active_policy.pause_resume_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        reason_codes=[
            "M133_LONG_RUNNING_TASK_SUPERVISOR_CONTRACT_ONLY",
            "M133_EXACT_SUPERVISOR_SCOPE_REQUIRED",
            "M133_HEARTBEAT_AND_CHECKPOINT_REFS_REQUIRED",
            "M133_NO_SUPERVISOR_RUNTIME",
            "M134_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M133 defines a long-running task supervisor contract for governed "
            "review only. It binds Mode 5, M132 trusted workflow, M131 scoped "
            "work-session, supervisor plan, task state, heartbeat plan, "
            "checkpoint plan, context budget, pause, resume, stop, risk, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "does not start a supervisor, monitor heartbeats, schedule "
            "checkpoints, resume or recover work, schedule human checkpoints, "
            "run schedulers or background workers, execute tools, shell, "
            "network, browser, plugin, connector, mobile, remote, model, memory, "
            "or context work, add routes or controls, add dependencies, enable "
            "beta, grant production authority, or implement M134."
        ),
        receipt_plan=LongRunningTaskSupervisorReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            supervisor_ref=validated_request.supervisor_ref,
            scope_ref=validated_request.scope_ref,
            m132_trusted_workflow_decision_ref=validated_request.m132_trusted_workflow_decision_ref,
            m131_work_session_decision_ref=validated_request.m131_work_session_decision_ref,
            supervisor_plan_ref=validated_request.supervisor_plan_ref,
            task_ref=validated_request.task_ref,
            run_state_ref=validated_request.run_state_ref,
            heartbeat_plan_ref=validated_request.heartbeat_plan_ref,
            checkpoint_plan_ref=validated_request.checkpoint_plan_ref,
            context_budget_ref=validated_request.context_budget_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_long_running_task_supervisor_decision(decision)


def validate_long_running_task_supervisor_policy(
    policy: LongRunningTaskSupervisorPolicy,
) -> LongRunningTaskSupervisorPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, LongRunningTaskSupervisorPolicy):
        raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED")
    validated = LongRunningTaskSupervisorPolicy.model_validate(payload)
    for field_name, reason in _M133_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M133_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_long_running_task_supervisor_request(
    request: LongRunningTaskSupervisorRequest,
) -> LongRunningTaskSupervisorRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, LongRunningTaskSupervisorRequest):
        raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED")
    for field_name, reason in _M133_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = LongRunningTaskSupervisorRequest.model_validate(payload)
    for field_name, reason in _M133_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M133_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M133_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M133_MODE5_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    return validated


def validate_long_running_task_supervisor_decision(
    decision: LongRunningTaskSupervisorDecision,
) -> LongRunningTaskSupervisorDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, LongRunningTaskSupervisorDecision):
        raise ValueError("M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED")
    for field_name, reason in _M133_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = LongRunningTaskSupervisorDecision.model_validate(payload)
    for field_name, reason in _M133_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != LongRunningTaskSupervisorStatus.ready_for_review:
        raise ValueError("M133_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M133_MODE5_REQUIRED")
    for field_name, reason in _M133_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M133_SIDE_EFFECTS_DENIED")
    if "M133_LONG_RUNNING_TASK_SUPERVISOR_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M133_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: LongRunningTaskSupervisorReceiptPlan,
) -> LongRunningTaskSupervisorReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M133_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = LongRunningTaskSupervisorReceiptPlan.model_validate(payload)
    for field_name, reason in _M133_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M133_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M133_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: LongRunningTaskSupervisorDecision,
    receipt: LongRunningTaskSupervisorReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.supervisor_ref, decision.supervisor_ref),
        (receipt.scope_ref, decision.scope_ref),
        (
            receipt.m132_trusted_workflow_decision_ref,
            decision.m132_trusted_workflow_decision_ref,
        ),
        (receipt.m131_work_session_decision_ref, decision.m131_work_session_decision_ref),
        (receipt.supervisor_plan_ref, decision.supervisor_plan_ref),
        (receipt.task_ref, decision.task_ref),
        (receipt.run_state_ref, decision.run_state_ref),
        (receipt.heartbeat_plan_ref, decision.heartbeat_plan_ref),
        (receipt.checkpoint_plan_ref, decision.checkpoint_plan_ref),
        (receipt.context_budget_ref, decision.context_budget_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M133_RECEIPT_BINDING_MISMATCH")


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
        raise ValueError("M133_REF_LIST_TOO_LONG")
    if len(set(refs)) != len(refs):
        raise ValueError("M133_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk != AutonomyRiskClass.low:
        raise ValueError("M133_RISK_CEILING_DENIED")


def _request_ref_pairs(request: LongRunningTaskSupervisorRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.supervisor_ref, "supervisor_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (
            request.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (request.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (request.supervisor_plan_ref, "supervisor_plan_ref"),
        (request.task_ref, "task_ref"),
        (request.run_state_ref, "run_state_ref"),
        (request.heartbeat_plan_ref, "heartbeat_plan_ref"),
        (request.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (request.context_budget_ref, "context_budget_ref"),
        (request.policy_decision_ref, "policy_decision_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _receipt_ref_pairs(receipt: LongRunningTaskSupervisorReceiptPlan):
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.supervisor_ref, "supervisor_ref"),
        (receipt.scope_ref, "scope_ref"),
        (
            receipt.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (receipt.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (receipt.supervisor_plan_ref, "supervisor_plan_ref"),
        (receipt.task_ref, "task_ref"),
        (receipt.run_state_ref, "run_state_ref"),
        (receipt.heartbeat_plan_ref, "heartbeat_plan_ref"),
        (receipt.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (receipt.context_budget_ref, "context_budget_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: LongRunningTaskSupervisorDecision):
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.supervisor_ref, "supervisor_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (
            decision.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (decision.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (decision.supervisor_plan_ref, "supervisor_plan_ref"),
        (decision.task_ref, "task_ref"),
        (decision.run_state_ref, "run_state_ref"),
        (decision.heartbeat_plan_ref, "heartbeat_plan_ref"),
        (decision.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (decision.context_budget_ref, "context_budget_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M133_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M133_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M133_REVIEW_ONLY_REQUIRED"),
    ("long_running_supervisor_only", "M133_LONG_RUNNING_SUPERVISOR_ONLY_REQUIRED"),
    ("deterministic", "M133_DETERMINISTIC_REQUIRED"),
    ("local_only", "M133_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M133_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M133_EXACT_SCOPE_REQUIRED"),
    ("mode5_required", "M133_MODE5_REQUIRED"),
    ("m132_trusted_workflow_required", "M133_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("m131_work_session_required", "M133_M131_WORK_SESSION_REQUIRED"),
    ("supervisor_plan_required", "M133_SUPERVISOR_PLAN_REQUIRED"),
    ("task_state_required", "M133_TASK_STATE_REQUIRED"),
    ("heartbeat_plan_required", "M133_HEARTBEAT_PLAN_REQUIRED"),
    ("checkpoint_plan_required", "M133_CHECKPOINT_PLAN_REQUIRED"),
    ("context_budget_required", "M133_CONTEXT_BUDGET_REQUIRED"),
    ("pause_resume_required", "M133_PAUSE_RESUME_REQUIRED"),
    ("audit_replay_required", "M133_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M133_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M133_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M133_NO_EFFECT_RECEIPT_REQUIRED"),
    ("m134_future_only", "M134_FUTURE_ONLY_REQUIRED"),
]

_M133_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M133_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M133_REVIEW_ONLY_REQUIRED"),
    ("long_running_supervisor_only", "M133_LONG_RUNNING_SUPERVISOR_ONLY_REQUIRED"),
    ("deterministic", "M133_DETERMINISTIC_REQUIRED"),
    ("local_only", "M133_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M133_SAFE_REFS_ONLY_REQUIRED"),
]

_M133_DECISION_REQUIRED_TRUE = [
    *_M133_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M133_EXACT_SCOPE_REQUIRED"),
    ("mode5_bound", "M133_MODE5_REQUIRED"),
    ("m132_trusted_workflow_bound", "M133_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("m131_work_session_bound", "M133_M131_WORK_SESSION_REQUIRED"),
    ("supervisor_plan_bound", "M133_SUPERVISOR_PLAN_REQUIRED"),
    ("task_state_bound", "M133_TASK_STATE_REQUIRED"),
    ("heartbeat_plan_bound", "M133_HEARTBEAT_PLAN_REQUIRED"),
    ("checkpoint_plan_bound", "M133_CHECKPOINT_PLAN_REQUIRED"),
    ("context_budget_bound", "M133_CONTEXT_BUDGET_REQUIRED"),
    ("pause_resume_bound", "M133_PAUSE_RESUME_REQUIRED"),
    ("audit_replay_bound", "M133_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M133_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M133_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M133_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M133_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M133_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M133_SAFE_REFS_ONLY_REQUIRED"),
]

_M133_DENIALS = {
    "mode5_runtime_enabled": "M133_MODE5_RUNTIME_DENIED",
    "supervisor_runtime_enabled": "M133_SUPERVISOR_RUNTIME_DENIED",
    "long_running_supervisor_start_enabled": "M133_SUPERVISOR_START_DENIED",
    "task_supervision_enabled": "M133_TASK_SUPERVISION_DENIED",
    "heartbeat_monitor_enabled": "M133_HEARTBEAT_MONITOR_DENIED",
    "checkpoint_scheduler_enabled": "M133_CHECKPOINT_SCHEDULER_DENIED",
    "resume_execution_enabled": "M133_RESUME_EXECUTION_DENIED",
    "recovery_execution_enabled": "M135_RECOVERY_EXECUTION_DENIED",
    "human_checkpoint_scheduling_enabled": "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
    "scheduler_enabled": "M133_SCHEDULER_DENIED",
    "background_worker_enabled": "M133_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_enabled": "M133_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M133_EXECUTION_DENIED",
    "tool_execution_enabled": "M133_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M133_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M133_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M133_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M133_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M133_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M133_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M133_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M133_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M133_DOWNLOAD_DENIED",
    "upload_enabled": "M133_UPLOAD_DENIED",
    "plugin_execution_enabled": "M133_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M133_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M133_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M133_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M133_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M133_MODEL_CALL_DENIED",
    "memory_write_enabled": "M133_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M133_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M133_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M133_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M133_DEPENDENCY_DENIED",
    "beta_release_enabled": "M133_BETA_RELEASE_DENIED",
    "production_authority_granted": "M133_PRODUCTION_AUTHORITY_DENIED",
}

_M133_REQUEST_DENIALS = {
    "mode5_runtime_requested": "M133_MODE5_RUNTIME_DENIED",
    "supervisor_runtime_requested": "M133_SUPERVISOR_RUNTIME_DENIED",
    "long_running_supervisor_start_requested": "M133_SUPERVISOR_START_DENIED",
    "task_supervision_requested": "M133_TASK_SUPERVISION_DENIED",
    "heartbeat_monitor_requested": "M133_HEARTBEAT_MONITOR_DENIED",
    "checkpoint_scheduler_requested": "M133_CHECKPOINT_SCHEDULER_DENIED",
    "resume_execution_requested": "M133_RESUME_EXECUTION_DENIED",
    "recovery_execution_requested": "M135_RECOVERY_EXECUTION_DENIED",
    "human_checkpoint_scheduling_requested": "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
    "scheduler_requested": "M133_SCHEDULER_DENIED",
    "background_worker_requested": "M133_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_requested": "M133_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M133_EXECUTION_DENIED",
    "tool_execution_requested": "M133_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M133_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M133_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M133_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M133_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M133_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M133_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M133_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M133_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M133_DOWNLOAD_DENIED",
    "upload_requested": "M133_UPLOAD_DENIED",
    "plugin_execution_requested": "M133_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M133_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M133_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M133_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M133_REMOTE_EXECUTION_DENIED",
    "model_call_requested": "M133_MODEL_CALL_DENIED",
    "memory_write_requested": "M133_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M133_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M133_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M133_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M133_DEPENDENCY_DENIED",
    "beta_release_requested": "M133_BETA_RELEASE_DENIED",
    "production_authority_requested": "M133_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M133_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M133_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED",
}

_M133_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M133_MODE5_RUNTIME_DENIED",
    "supervisor_runtime_authorized": "M133_SUPERVISOR_RUNTIME_DENIED",
    "long_running_supervisor_start_authorized": "M133_SUPERVISOR_START_DENIED",
    "supervisor_started": "M133_SUPERVISOR_START_DENIED",
    "task_supervision_active": "M133_TASK_SUPERVISION_DENIED",
    "heartbeat_monitor_started": "M133_HEARTBEAT_MONITOR_DENIED",
    "checkpoint_scheduler_started": "M133_CHECKPOINT_SCHEDULER_DENIED",
    "resume_execution_performed": "M133_RESUME_EXECUTION_DENIED",
    "recovery_execution_performed": "M135_RECOVERY_EXECUTION_DENIED",
    "human_checkpoint_scheduling_performed": "M134_HUMAN_CHECKPOINT_SCHEDULING_DENIED",
    "scheduler_started": "M133_SCHEDULER_DENIED",
    "background_worker_started": "M133_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_authorized": "M133_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M133_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M133_EXECUTION_DENIED",
    "execution_performed": "M133_EXECUTION_DENIED",
    "tool_execution_authorized": "M133_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M133_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M133_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M133_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M133_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M133_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M133_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M133_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M133_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M133_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M133_DOWNLOAD_DENIED",
    "upload_performed": "M133_UPLOAD_DENIED",
    "plugin_execution_performed": "M133_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M133_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M133_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M133_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M133_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M133_MODEL_CALL_DENIED",
    "memory_write_performed": "M133_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M133_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M133_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M133_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M133_DEPENDENCY_DENIED",
    "beta_release_enabled": "M133_BETA_RELEASE_DENIED",
    "production_authority_granted": "M133_PRODUCTION_AUTHORITY_DENIED",
}

_M133_RECEIPT_DENIALS = {
    "store_raw_prompt": "M133_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M133_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M133_SECRET_LIKE_SUPERVISOR_CONTENT_DENIED",
    "supervisor_started": "M133_SUPERVISOR_START_DENIED",
    "heartbeat_monitor_started": "M133_HEARTBEAT_MONITOR_DENIED",
    "checkpoint_scheduler_started": "M133_CHECKPOINT_SCHEDULER_DENIED",
    "resume_execution_performed": "M133_RESUME_EXECUTION_DENIED",
    "recovery_execution_performed": "M135_RECOVERY_EXECUTION_DENIED",
    "execution_performed": "M133_EXECUTION_DENIED",
}
