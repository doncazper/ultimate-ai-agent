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


HUMAN_CHECKPOINT_SCHEDULING_DOCS = [
    "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING.md",
    "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_POLICY.md",
    "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_RECEIPT_PLAN.md",
    "docs/autonomy/HUMAN_CHECKPOINT_SCHEDULING_NON_GOALS.md",
    "docs/autonomy/M134_TO_M135_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M134_MAX_CHECKPOINT_WINDOW_SECONDS = 604_800
M134_MAX_REVIEWER_REFS = 20


class HumanCheckpointSchedulingStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _HumanCheckpointSchedulingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class HumanCheckpointSchedulingPolicy(_HumanCheckpointSchedulingModel):
    policy_ref: str = "human-checkpoint-scheduling-policy:m134"
    contract_only: bool = True
    review_only: bool = True
    human_checkpoint_scheduling_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    scheduling_plan_required: bool = True
    checkpoint_window_required: bool = True
    reviewer_refs_required: bool = True
    consent_ref_required: bool = True
    expiration_required: bool = True
    escalation_plan_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m135_future_only: bool = True
    mode5_runtime_enabled: bool = False
    human_checkpoint_scheduler_enabled: bool = False
    human_checkpoint_prompt_enabled: bool = False
    notification_delivery_enabled: bool = False
    reminder_runtime_enabled: bool = False
    calendar_write_enabled: bool = False
    approval_capture_enabled: bool = False
    escalation_runtime_enabled: bool = False
    supervisor_runtime_enabled: bool = False
    recovery_execution_enabled: bool = False
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
            raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED") from exc
        return self


class HumanCheckpointSchedulingRequest(_HumanCheckpointSchedulingModel):
    request_ref: str
    checkpoint_schedule_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    checkpoint_plan_ref: str
    schedule_plan_ref: str
    checkpoint_window_ref: str
    reviewer_refs: list[str]
    consent_ref: str
    expiration_ref: str
    reminder_plan_ref: str
    escalation_plan_ref: str
    pause_condition_refs: list[str]
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
    max_checkpoint_window_seconds: int = Field(
        gt=0, le=M134_MAX_CHECKPOINT_WINDOW_SECONDS
    )
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_checkpoint_summary: str
    contract_only: bool = True
    review_only: bool = True
    human_checkpoint_scheduling_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    human_checkpoint_scheduler_requested: bool = False
    human_checkpoint_prompt_requested: bool = False
    notification_delivery_requested: bool = False
    reminder_runtime_requested: bool = False
    calendar_write_requested: bool = False
    approval_capture_requested: bool = False
    escalation_runtime_requested: bool = False
    supervisor_runtime_requested: bool = False
    recovery_execution_requested: bool = False
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
        _validate_ref_list(self.resource_refs, "resource_ref", "M134_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M134_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M134_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.reviewer_refs,
            "reviewer_ref",
            "M134_REVIEWER_REF_REQUIRED",
            max_count=M134_MAX_REVIEWER_REFS,
        )
        _validate_ref_list(
            self.pause_condition_refs,
            "pause_condition_ref",
            "M134_PAUSE_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M134_STOP_CONDITION_REF_REQUIRED",
        )
        try:
            _validate_safe_payload({"safe_checkpoint_summary": self.safe_checkpoint_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED") from exc
        return self


class HumanCheckpointSchedulingReceiptPlan(_HumanCheckpointSchedulingModel):
    receipt_plan_ref: str
    checkpoint_schedule_ref: str
    scope_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    checkpoint_plan_ref: str
    schedule_plan_ref: str
    checkpoint_window_ref: str
    consent_ref: str
    expiration_ref: str
    reminder_plan_ref: str
    escalation_plan_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    checkpoint_scheduled: bool = False
    prompt_sent: bool = False
    notification_delivered: bool = False
    calendar_written: bool = False
    approval_captured: bool = False
    escalation_started: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M134 human checkpoint scheduling receipt stores safe refs and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED") from exc
        return self


class HumanCheckpointSchedulingDecision(_HumanCheckpointSchedulingModel):
    decision_ref: str
    request_ref: str
    checkpoint_schedule_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    checkpoint_plan_ref: str
    schedule_plan_ref: str
    checkpoint_window_ref: str
    reviewer_refs: list[str]
    consent_ref: str
    expiration_ref: str
    reminder_plan_ref: str
    escalation_plan_ref: str
    pause_condition_refs: list[str]
    stop_condition_refs: list[str]
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: HumanCheckpointSchedulingStatus = HumanCheckpointSchedulingStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_checkpoint_window_seconds: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    human_checkpoint_scheduling_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    checkpoint_plan_bound: bool = True
    schedule_plan_bound: bool = True
    checkpoint_window_bound: bool = True
    reviewer_bound: bool = True
    consent_bound: bool = True
    expiration_bound: bool = True
    reminder_plan_bound: bool = True
    escalation_plan_bound: bool = True
    pause_stop_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    human_checkpoint_scheduler_authorized: bool = False
    checkpoint_scheduled: bool = False
    human_checkpoint_prompt_sent: bool = False
    notification_delivered: bool = False
    reminder_runtime_started: bool = False
    calendar_written: bool = False
    approval_captured: bool = False
    escalation_runtime_started: bool = False
    supervisor_runtime_started: bool = False
    recovery_execution_performed: bool = False
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
    receipt_plan: HumanCheckpointSchedulingReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M134_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M134_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M134_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.reviewer_refs,
            "reviewer_ref",
            "M134_REVIEWER_REF_REQUIRED",
            max_count=M134_MAX_REVIEWER_REFS,
        )
        _validate_ref_list(
            self.pause_condition_refs,
            "pause_condition_ref",
            "M134_PAUSE_CONDITION_REF_REQUIRED",
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M134_STOP_CONDITION_REF_REQUIRED",
        )
        if not self.reason_codes:
            raise ValueError("M134_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED") from exc
        return self


def build_human_checkpoint_scheduling_decision(
    request: HumanCheckpointSchedulingRequest,
    policy: HumanCheckpointSchedulingPolicy | None = None,
) -> HumanCheckpointSchedulingDecision:
    active_policy = validate_human_checkpoint_scheduling_policy(
        policy or HumanCheckpointSchedulingPolicy()
    )
    validated_request = validate_human_checkpoint_scheduling_request(request)
    decision = HumanCheckpointSchedulingDecision(
        decision_ref=(
            "human-checkpoint-scheduling-decision:"
            f"{_ref_suffix(validated_request.checkpoint_schedule_ref)}"
        ),
        request_ref=validated_request.request_ref,
        checkpoint_schedule_ref=validated_request.checkpoint_schedule_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
        m132_trusted_workflow_decision_ref=validated_request.m132_trusted_workflow_decision_ref,
        checkpoint_plan_ref=validated_request.checkpoint_plan_ref,
        schedule_plan_ref=validated_request.schedule_plan_ref,
        checkpoint_window_ref=validated_request.checkpoint_window_ref,
        reviewer_refs=list(validated_request.reviewer_refs),
        consent_ref=validated_request.consent_ref,
        expiration_ref=validated_request.expiration_ref,
        reminder_plan_ref=validated_request.reminder_plan_ref,
        escalation_plan_ref=validated_request.escalation_plan_ref,
        pause_condition_refs=list(validated_request.pause_condition_refs),
        stop_condition_refs=list(validated_request.stop_condition_refs),
        policy_decision_ref=validated_request.policy_decision_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        max_checkpoint_window_seconds=validated_request.max_checkpoint_window_seconds,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        human_checkpoint_scheduling_only=active_policy.human_checkpoint_scheduling_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        mode5_bound=active_policy.mode5_required,
        m133_supervisor_bound=active_policy.m133_supervisor_required,
        m132_trusted_workflow_bound=active_policy.m132_trusted_workflow_required,
        checkpoint_plan_bound=True,
        schedule_plan_bound=active_policy.scheduling_plan_required,
        checkpoint_window_bound=active_policy.checkpoint_window_required,
        reviewer_bound=active_policy.reviewer_refs_required,
        consent_bound=active_policy.consent_ref_required,
        expiration_bound=active_policy.expiration_required,
        reminder_plan_bound=True,
        escalation_plan_bound=active_policy.escalation_plan_required,
        pause_stop_bound=True,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        reason_codes=[
            "M134_HUMAN_CHECKPOINT_SCHEDULING_CONTRACT_ONLY",
            "M134_EXACT_CHECKPOINT_SCOPE_REQUIRED",
            "M134_HUMAN_REVIEWER_REFS_REQUIRED",
            "M134_NO_SCHEDULER_OR_PROMPT_RUNTIME",
            "M135_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M134 defines a human checkpoint scheduling contract for governed "
            "review only. It binds Mode 5, M133 supervisor decision, M132 "
            "trusted workflow decision, checkpoint plan, schedule plan, "
            "checkpoint window, reviewer, consent, expiration, reminder plan, "
            "escalation plan, pause, stop, risk, audit, replay, revocation, "
            "kill-switch, and no-effect receipt refs. It does not schedule a "
            "checkpoint, send prompts, deliver notifications, start reminder or "
            "escalation runtime, write calendars, capture approvals, run "
            "supervisor or recovery work, run schedulers or background workers, "
            "execute tools, shell, network, browser, plugin, connector, mobile, "
            "remote, model, memory, or context work, add routes or controls, add "
            "dependencies, enable beta, grant production authority, or implement M135."
        ),
        receipt_plan=HumanCheckpointSchedulingReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            checkpoint_schedule_ref=validated_request.checkpoint_schedule_ref,
            scope_ref=validated_request.scope_ref,
            m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
            m132_trusted_workflow_decision_ref=validated_request.m132_trusted_workflow_decision_ref,
            checkpoint_plan_ref=validated_request.checkpoint_plan_ref,
            schedule_plan_ref=validated_request.schedule_plan_ref,
            checkpoint_window_ref=validated_request.checkpoint_window_ref,
            consent_ref=validated_request.consent_ref,
            expiration_ref=validated_request.expiration_ref,
            reminder_plan_ref=validated_request.reminder_plan_ref,
            escalation_plan_ref=validated_request.escalation_plan_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_human_checkpoint_scheduling_decision(decision)


def validate_human_checkpoint_scheduling_policy(
    policy: HumanCheckpointSchedulingPolicy,
) -> HumanCheckpointSchedulingPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, HumanCheckpointSchedulingPolicy):
        raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED")
    validated = HumanCheckpointSchedulingPolicy.model_validate(payload)
    for field_name, reason in _M134_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M134_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_human_checkpoint_scheduling_request(
    request: HumanCheckpointSchedulingRequest,
) -> HumanCheckpointSchedulingRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, HumanCheckpointSchedulingRequest):
        raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED")
    for field_name, reason in _M134_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = HumanCheckpointSchedulingRequest.model_validate(payload)
    for field_name, reason in _M134_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M134_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M134_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M134_MODE5_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    return validated


def validate_human_checkpoint_scheduling_decision(
    decision: HumanCheckpointSchedulingDecision,
) -> HumanCheckpointSchedulingDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, HumanCheckpointSchedulingDecision):
        raise ValueError("M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED")
    for field_name, reason in _M134_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = HumanCheckpointSchedulingDecision.model_validate(payload)
    for field_name, reason in _M134_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != HumanCheckpointSchedulingStatus.ready_for_review:
        raise ValueError("M134_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M134_MODE5_REQUIRED")
    for field_name, reason in _M134_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M134_SIDE_EFFECTS_DENIED")
    if "M134_HUMAN_CHECKPOINT_SCHEDULING_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M134_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: HumanCheckpointSchedulingReceiptPlan,
) -> HumanCheckpointSchedulingReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M134_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = HumanCheckpointSchedulingReceiptPlan.model_validate(payload)
    for field_name, reason in _M134_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M134_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M134_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: HumanCheckpointSchedulingDecision,
    receipt: HumanCheckpointSchedulingReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.checkpoint_schedule_ref, decision.checkpoint_schedule_ref),
        (receipt.scope_ref, decision.scope_ref),
        (receipt.m133_supervisor_decision_ref, decision.m133_supervisor_decision_ref),
        (
            receipt.m132_trusted_workflow_decision_ref,
            decision.m132_trusted_workflow_decision_ref,
        ),
        (receipt.checkpoint_plan_ref, decision.checkpoint_plan_ref),
        (receipt.schedule_plan_ref, decision.schedule_plan_ref),
        (receipt.checkpoint_window_ref, decision.checkpoint_window_ref),
        (receipt.consent_ref, decision.consent_ref),
        (receipt.expiration_ref, decision.expiration_ref),
        (receipt.reminder_plan_ref, decision.reminder_plan_ref),
        (receipt.escalation_plan_ref, decision.escalation_plan_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M134_RECEIPT_BINDING_MISMATCH")


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
        raise ValueError("M134_REF_LIST_TOO_LONG")
    if len(set(refs)) != len(refs):
        raise ValueError("M134_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk != AutonomyRiskClass.low:
        raise ValueError("M134_RISK_CEILING_DENIED")


def _request_ref_pairs(request: HumanCheckpointSchedulingRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.checkpoint_schedule_ref, "checkpoint_schedule_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (request.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            request.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (request.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (request.schedule_plan_ref, "schedule_plan_ref"),
        (request.checkpoint_window_ref, "checkpoint_window_ref"),
        (request.consent_ref, "consent_ref"),
        (request.expiration_ref, "expiration_ref"),
        (request.reminder_plan_ref, "reminder_plan_ref"),
        (request.escalation_plan_ref, "escalation_plan_ref"),
        (request.policy_decision_ref, "policy_decision_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _receipt_ref_pairs(receipt: HumanCheckpointSchedulingReceiptPlan):
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.checkpoint_schedule_ref, "checkpoint_schedule_ref"),
        (receipt.scope_ref, "scope_ref"),
        (receipt.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            receipt.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (receipt.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (receipt.schedule_plan_ref, "schedule_plan_ref"),
        (receipt.checkpoint_window_ref, "checkpoint_window_ref"),
        (receipt.consent_ref, "consent_ref"),
        (receipt.expiration_ref, "expiration_ref"),
        (receipt.reminder_plan_ref, "reminder_plan_ref"),
        (receipt.escalation_plan_ref, "escalation_plan_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: HumanCheckpointSchedulingDecision):
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.checkpoint_schedule_ref, "checkpoint_schedule_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (decision.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            decision.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (decision.checkpoint_plan_ref, "checkpoint_plan_ref"),
        (decision.schedule_plan_ref, "schedule_plan_ref"),
        (decision.checkpoint_window_ref, "checkpoint_window_ref"),
        (decision.consent_ref, "consent_ref"),
        (decision.expiration_ref, "expiration_ref"),
        (decision.reminder_plan_ref, "reminder_plan_ref"),
        (decision.escalation_plan_ref, "escalation_plan_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M134_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M134_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M134_REVIEW_ONLY_REQUIRED"),
    ("human_checkpoint_scheduling_only", "M134_HUMAN_CHECKPOINT_ONLY_REQUIRED"),
    ("deterministic", "M134_DETERMINISTIC_REQUIRED"),
    ("local_only", "M134_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M134_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M134_EXACT_SCOPE_REQUIRED"),
    ("mode5_required", "M134_MODE5_REQUIRED"),
    ("m133_supervisor_required", "M134_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_required", "M134_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("scheduling_plan_required", "M134_SCHEDULE_PLAN_REQUIRED"),
    ("checkpoint_window_required", "M134_CHECKPOINT_WINDOW_REQUIRED"),
    ("reviewer_refs_required", "M134_REVIEWER_REF_REQUIRED"),
    ("consent_ref_required", "M134_CONSENT_REF_REQUIRED"),
    ("expiration_required", "M134_EXPIRATION_REQUIRED"),
    ("escalation_plan_required", "M134_ESCALATION_PLAN_REQUIRED"),
    ("audit_replay_required", "M134_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M134_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M134_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M134_NO_EFFECT_RECEIPT_REQUIRED"),
    ("m135_future_only", "M135_FUTURE_ONLY_REQUIRED"),
]

_M134_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M134_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M134_REVIEW_ONLY_REQUIRED"),
    ("human_checkpoint_scheduling_only", "M134_HUMAN_CHECKPOINT_ONLY_REQUIRED"),
    ("deterministic", "M134_DETERMINISTIC_REQUIRED"),
    ("local_only", "M134_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M134_SAFE_REFS_ONLY_REQUIRED"),
]

_M134_DECISION_REQUIRED_TRUE = [
    *_M134_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M134_EXACT_SCOPE_REQUIRED"),
    ("mode5_bound", "M134_MODE5_REQUIRED"),
    ("m133_supervisor_bound", "M134_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_bound", "M134_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("checkpoint_plan_bound", "M134_CHECKPOINT_PLAN_REQUIRED"),
    ("schedule_plan_bound", "M134_SCHEDULE_PLAN_REQUIRED"),
    ("checkpoint_window_bound", "M134_CHECKPOINT_WINDOW_REQUIRED"),
    ("reviewer_bound", "M134_REVIEWER_REF_REQUIRED"),
    ("consent_bound", "M134_CONSENT_REF_REQUIRED"),
    ("expiration_bound", "M134_EXPIRATION_REQUIRED"),
    ("reminder_plan_bound", "M134_REMINDER_PLAN_REQUIRED"),
    ("escalation_plan_bound", "M134_ESCALATION_PLAN_REQUIRED"),
    ("pause_stop_bound", "M134_PAUSE_STOP_REQUIRED"),
    ("audit_replay_bound", "M134_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M134_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M134_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M134_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M134_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M134_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M134_SAFE_REFS_ONLY_REQUIRED"),
]

_M134_DENIALS = {
    "mode5_runtime_enabled": "M134_MODE5_RUNTIME_DENIED",
    "human_checkpoint_scheduler_enabled": "M134_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_enabled": "M134_PROMPT_RUNTIME_DENIED",
    "notification_delivery_enabled": "M134_NOTIFICATION_DELIVERY_DENIED",
    "reminder_runtime_enabled": "M134_REMINDER_RUNTIME_DENIED",
    "calendar_write_enabled": "M134_CALENDAR_WRITE_DENIED",
    "approval_capture_enabled": "M134_APPROVAL_CAPTURE_DENIED",
    "escalation_runtime_enabled": "M134_ESCALATION_RUNTIME_DENIED",
    "supervisor_runtime_enabled": "M134_SUPERVISOR_RUNTIME_DENIED",
    "recovery_execution_enabled": "M135_RECOVERY_EXECUTION_DENIED",
    "scheduler_enabled": "M134_SCHEDULER_DENIED",
    "background_worker_enabled": "M134_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_enabled": "M134_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M134_EXECUTION_DENIED",
    "tool_execution_enabled": "M134_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M134_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M134_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M134_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M134_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M134_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M134_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M134_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M134_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M134_DOWNLOAD_DENIED",
    "upload_enabled": "M134_UPLOAD_DENIED",
    "plugin_execution_enabled": "M134_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M134_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M134_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M134_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M134_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M134_MODEL_CALL_DENIED",
    "memory_write_enabled": "M134_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M134_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M134_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M134_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M134_DEPENDENCY_DENIED",
    "beta_release_enabled": "M134_BETA_RELEASE_DENIED",
    "production_authority_granted": "M134_PRODUCTION_AUTHORITY_DENIED",
}

_M134_REQUEST_DENIALS = {
    "mode5_runtime_requested": "M134_MODE5_RUNTIME_DENIED",
    "human_checkpoint_scheduler_requested": "M134_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_requested": "M134_PROMPT_RUNTIME_DENIED",
    "notification_delivery_requested": "M134_NOTIFICATION_DELIVERY_DENIED",
    "reminder_runtime_requested": "M134_REMINDER_RUNTIME_DENIED",
    "calendar_write_requested": "M134_CALENDAR_WRITE_DENIED",
    "approval_capture_requested": "M134_APPROVAL_CAPTURE_DENIED",
    "escalation_runtime_requested": "M134_ESCALATION_RUNTIME_DENIED",
    "supervisor_runtime_requested": "M134_SUPERVISOR_RUNTIME_DENIED",
    "recovery_execution_requested": "M135_RECOVERY_EXECUTION_DENIED",
    "scheduler_requested": "M134_SCHEDULER_DENIED",
    "background_worker_requested": "M134_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_requested": "M134_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M134_EXECUTION_DENIED",
    "tool_execution_requested": "M134_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M134_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M134_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M134_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M134_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M134_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M134_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M134_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M134_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M134_DOWNLOAD_DENIED",
    "upload_requested": "M134_UPLOAD_DENIED",
    "plugin_execution_requested": "M134_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M134_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M134_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M134_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M134_REMOTE_EXECUTION_DENIED",
    "model_call_requested": "M134_MODEL_CALL_DENIED",
    "memory_write_requested": "M134_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M134_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M134_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M134_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M134_DEPENDENCY_DENIED",
    "beta_release_requested": "M134_BETA_RELEASE_DENIED",
    "production_authority_requested": "M134_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M134_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M134_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED",
}

_M134_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M134_MODE5_RUNTIME_DENIED",
    "human_checkpoint_scheduler_authorized": "M134_CHECKPOINT_SCHEDULER_DENIED",
    "checkpoint_scheduled": "M134_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_sent": "M134_PROMPT_RUNTIME_DENIED",
    "notification_delivered": "M134_NOTIFICATION_DELIVERY_DENIED",
    "reminder_runtime_started": "M134_REMINDER_RUNTIME_DENIED",
    "calendar_written": "M134_CALENDAR_WRITE_DENIED",
    "approval_captured": "M134_APPROVAL_CAPTURE_DENIED",
    "escalation_runtime_started": "M134_ESCALATION_RUNTIME_DENIED",
    "supervisor_runtime_started": "M134_SUPERVISOR_RUNTIME_DENIED",
    "recovery_execution_performed": "M135_RECOVERY_EXECUTION_DENIED",
    "scheduler_started": "M134_SCHEDULER_DENIED",
    "background_worker_started": "M134_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_authorized": "M134_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M134_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M134_EXECUTION_DENIED",
    "execution_performed": "M134_EXECUTION_DENIED",
    "tool_execution_authorized": "M134_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M134_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M134_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M134_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M134_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M134_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M134_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M134_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M134_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M134_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M134_DOWNLOAD_DENIED",
    "upload_performed": "M134_UPLOAD_DENIED",
    "plugin_execution_performed": "M134_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M134_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M134_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M134_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M134_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M134_MODEL_CALL_DENIED",
    "memory_write_performed": "M134_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M134_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M134_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M134_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M134_DEPENDENCY_DENIED",
    "beta_release_enabled": "M134_BETA_RELEASE_DENIED",
    "production_authority_granted": "M134_PRODUCTION_AUTHORITY_DENIED",
}

_M134_RECEIPT_DENIALS = {
    "store_raw_prompt": "M134_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M134_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M134_SECRET_LIKE_CHECKPOINT_CONTENT_DENIED",
    "checkpoint_scheduled": "M134_CHECKPOINT_SCHEDULER_DENIED",
    "prompt_sent": "M134_PROMPT_RUNTIME_DENIED",
    "notification_delivered": "M134_NOTIFICATION_DELIVERY_DENIED",
    "calendar_written": "M134_CALENDAR_WRITE_DENIED",
    "approval_captured": "M134_APPROVAL_CAPTURE_DENIED",
    "escalation_started": "M134_ESCALATION_RUNTIME_DENIED",
    "execution_performed": "M134_EXECUTION_DENIED",
}
