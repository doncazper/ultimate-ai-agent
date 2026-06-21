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


TRUSTED_RECURRING_WORKFLOW_DOCS = [
    "docs/autonomy/TRUSTED_RECURRING_WORKFLOW.md",
    "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_POLICY.md",
    "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_RECEIPT_PLAN.md",
    "docs/autonomy/TRUSTED_RECURRING_WORKFLOW_NON_GOALS.md",
    "docs/autonomy/M132_TO_M133_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M132_MIN_CADENCE_SECONDS = 3600
M132_MAX_RECURRENCE_OCCURRENCES = 31


class TrustedRecurringWorkflowStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _TrustedRecurringWorkflowModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class TrustedRecurringWorkflowPolicy(_TrustedRecurringWorkflowModel):
    policy_ref: str = "trusted-recurring-workflow-policy:m132"
    contract_only: bool = True
    review_only: bool = True
    trusted_recurring_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    exact_m131_work_session_required: bool = True
    recurring_contract_required: bool = True
    scoped_low_risk_recurring_required: bool = True
    cadence_bound_required: bool = True
    approval_bundle_required: bool = True
    approval_renewal_required: bool = True
    expiration_required: bool = True
    stop_conditions_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    m133_future_only: bool = True
    mode5_runtime_enabled: bool = False
    trusted_recurring_workflow_start_enabled: bool = False
    recurring_runtime_enabled: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    long_running_supervisor_enabled: bool = False
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
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED") from exc
        return self


class TrustedRecurringWorkflowRequest(_TrustedRecurringWorkflowModel):
    request_ref: str
    trusted_workflow_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m131_work_session_decision_ref: str
    recurring_contract_ref: str
    scoped_low_risk_recurring_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    approval_renewal_ref: str
    expiration_ref: str
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
    minimum_interval_seconds: int = Field(ge=M132_MIN_CADENCE_SECONDS)
    max_occurrences: int = Field(gt=0, le=M132_MAX_RECURRENCE_OCCURRENCES)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_goal_summary: str
    contract_only: bool = True
    review_only: bool = True
    trusted_recurring_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    trusted_recurring_workflow_start_requested: bool = False
    recurring_runtime_requested: bool = False
    recurrence_active: bool = False
    scheduler_requested: bool = False
    background_worker_requested: bool = False
    long_running_supervisor_requested: bool = False
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
    def validate_shape(self) -> Any:
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M132_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M132_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M132_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M132_STOP_CONDITION_REF_REQUIRED",
        )
        try:
            _validate_safe_payload({"safe_goal_summary": self.safe_goal_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED") from exc
        return self


class TrustedRecurringWorkflowReceiptPlan(_TrustedRecurringWorkflowModel):
    receipt_plan_ref: str
    trusted_workflow_ref: str
    scope_ref: str
    m131_work_session_decision_ref: str
    recurring_contract_ref: str
    scoped_low_risk_recurring_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    approval_renewal_ref: str
    expiration_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    workflow_started: bool = False
    recurring_runtime_started: bool = False
    scheduler_started: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M132 trusted recurring workflow receipt stores safe refs and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED") from exc
        return self


class TrustedRecurringWorkflowDecision(_TrustedRecurringWorkflowModel):
    decision_ref: str
    request_ref: str
    trusted_workflow_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m131_work_session_decision_ref: str
    recurring_contract_ref: str
    scoped_low_risk_recurring_ref: str
    cadence_ref: str
    approval_bundle_ref: str
    approval_renewal_ref: str
    expiration_ref: str
    stop_condition_refs: list[str]
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: TrustedRecurringWorkflowStatus = TrustedRecurringWorkflowStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    minimum_interval_seconds: int
    max_occurrences: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    trusted_recurring_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m131_work_session_bound: bool = True
    recurring_contract_bound: bool = True
    scoped_low_risk_recurring_bound: bool = True
    cadence_bound: bool = True
    approval_bundle_bound: bool = True
    approval_renewal_bound: bool = True
    expiration_bound: bool = True
    stop_conditions_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    trusted_recurring_workflow_start_authorized: bool = False
    workflow_started: bool = False
    recurrence_active: bool = False
    recurring_runtime_started: bool = False
    scheduler_started: bool = False
    background_worker_started: bool = False
    long_running_supervisor_started: bool = False
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
    receipt_plan: TrustedRecurringWorkflowReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M132_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M132_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M132_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.stop_condition_refs,
            "stop_condition_ref",
            "M132_STOP_CONDITION_REF_REQUIRED",
        )
        if not self.reason_codes:
            raise ValueError("M132_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED") from exc
        return self


def build_trusted_recurring_workflow_decision(
    request: TrustedRecurringWorkflowRequest,
    policy: TrustedRecurringWorkflowPolicy | None = None,
) -> TrustedRecurringWorkflowDecision:
    active_policy = validate_trusted_recurring_workflow_policy(
        policy or TrustedRecurringWorkflowPolicy()
    )
    validated_request = validate_trusted_recurring_workflow_request(request)
    decision = TrustedRecurringWorkflowDecision(
        decision_ref=f"trusted-recurring-workflow-decision:{_ref_suffix(validated_request.trusted_workflow_ref)}",
        request_ref=validated_request.request_ref,
        trusted_workflow_ref=validated_request.trusted_workflow_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        m131_work_session_decision_ref=validated_request.m131_work_session_decision_ref,
        recurring_contract_ref=validated_request.recurring_contract_ref,
        scoped_low_risk_recurring_ref=validated_request.scoped_low_risk_recurring_ref,
        cadence_ref=validated_request.cadence_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        approval_renewal_ref=validated_request.approval_renewal_ref,
        expiration_ref=validated_request.expiration_ref,
        stop_condition_refs=list(validated_request.stop_condition_refs),
        policy_decision_ref=validated_request.policy_decision_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        minimum_interval_seconds=validated_request.minimum_interval_seconds,
        max_occurrences=validated_request.max_occurrences,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        trusted_recurring_workflow_only=active_policy.trusted_recurring_workflow_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        mode5_bound=active_policy.mode5_required,
        m131_work_session_bound=active_policy.exact_m131_work_session_required,
        recurring_contract_bound=active_policy.recurring_contract_required,
        scoped_low_risk_recurring_bound=active_policy.scoped_low_risk_recurring_required,
        cadence_bound=active_policy.cadence_bound_required,
        approval_bundle_bound=active_policy.approval_bundle_required,
        approval_renewal_bound=active_policy.approval_renewal_required,
        expiration_bound=active_policy.expiration_required,
        stop_conditions_bound=active_policy.stop_conditions_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=True,
        reason_codes=[
            "M132_TRUSTED_RECURRING_WORKFLOW_CONTRACT_ONLY",
            "M132_EXACT_RECURRING_SCOPE_REQUIRED",
            "M132_APPROVAL_RENEWAL_REQUIRED",
            "M132_NO_SCHEDULER_OR_RUNTIME",
            "M133_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M132 defines a trusted recurring workflow contract for governed "
            "review only. It binds Mode 5, M131 scoped work-session, M97 "
            "recurring contract, M98 scoped low-risk recurring, cadence, "
            "approval bundle, renewal, expiration, stop condition, risk, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "does not start a workflow, activate recurrence, run a scheduler or "
            "background worker, execute tools, shell, network, browser, plugin, "
            "connector, mobile, remote, model, memory, or context work, add "
            "routes or controls, add dependencies, enable beta, grant production "
            "authority, or implement M133."
        ),
        receipt_plan=TrustedRecurringWorkflowReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            trusted_workflow_ref=validated_request.trusted_workflow_ref,
            scope_ref=validated_request.scope_ref,
            m131_work_session_decision_ref=validated_request.m131_work_session_decision_ref,
            recurring_contract_ref=validated_request.recurring_contract_ref,
            scoped_low_risk_recurring_ref=validated_request.scoped_low_risk_recurring_ref,
            cadence_ref=validated_request.cadence_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            approval_renewal_ref=validated_request.approval_renewal_ref,
            expiration_ref=validated_request.expiration_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_trusted_recurring_workflow_decision(decision)


def validate_trusted_recurring_workflow_policy(
    policy: TrustedRecurringWorkflowPolicy,
) -> TrustedRecurringWorkflowPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, TrustedRecurringWorkflowPolicy):
        raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED")
    validated = TrustedRecurringWorkflowPolicy.model_validate(payload)
    for field_name, reason in _M132_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M132_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_trusted_recurring_workflow_request(
    request: TrustedRecurringWorkflowRequest,
) -> TrustedRecurringWorkflowRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, TrustedRecurringWorkflowRequest):
        raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED")
    for field_name, reason in _M132_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = TrustedRecurringWorkflowRequest.model_validate(payload)
    for field_name, reason in _M132_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M132_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M132_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M132_MODE5_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    return validated


def validate_trusted_recurring_workflow_decision(
    decision: TrustedRecurringWorkflowDecision,
) -> TrustedRecurringWorkflowDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, TrustedRecurringWorkflowDecision):
        raise ValueError("M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED")
    for field_name, reason in _M132_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = TrustedRecurringWorkflowDecision.model_validate(payload)
    for field_name, reason in _M132_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != TrustedRecurringWorkflowStatus.ready_for_review:
        raise ValueError("M132_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M132_MODE5_REQUIRED")
    for field_name, reason in _M132_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M132_SIDE_EFFECTS_DENIED")
    if "M132_TRUSTED_RECURRING_WORKFLOW_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M132_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: TrustedRecurringWorkflowReceiptPlan,
) -> TrustedRecurringWorkflowReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M132_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = TrustedRecurringWorkflowReceiptPlan.model_validate(payload)
    for field_name, reason in _M132_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M132_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M132_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: TrustedRecurringWorkflowDecision,
    receipt: TrustedRecurringWorkflowReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.trusted_workflow_ref, decision.trusted_workflow_ref),
        (receipt.scope_ref, decision.scope_ref),
        (receipt.m131_work_session_decision_ref, decision.m131_work_session_decision_ref),
        (receipt.recurring_contract_ref, decision.recurring_contract_ref),
        (receipt.scoped_low_risk_recurring_ref, decision.scoped_low_risk_recurring_ref),
        (receipt.cadence_ref, decision.cadence_ref),
        (receipt.approval_bundle_ref, decision.approval_bundle_ref),
        (receipt.approval_renewal_ref, decision.approval_renewal_ref),
        (receipt.expiration_ref, decision.expiration_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M132_RECEIPT_BINDING_MISMATCH")


def _validate_ref_list(refs: list[str], field_name: str, reason: str) -> None:
    if not refs:
        raise ValueError(reason)
    if len(set(refs)) != len(refs):
        raise ValueError("M132_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk != AutonomyRiskClass.low:
        raise ValueError("M132_RISK_CEILING_DENIED")


def _request_ref_pairs(request: TrustedRecurringWorkflowRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.trusted_workflow_ref, "trusted_workflow_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (request.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (request.recurring_contract_ref, "recurring_contract_ref"),
        (request.scoped_low_risk_recurring_ref, "scoped_low_risk_recurring_ref"),
        (request.cadence_ref, "cadence_ref"),
        (request.approval_bundle_ref, "approval_bundle_ref"),
        (request.approval_renewal_ref, "approval_renewal_ref"),
        (request.expiration_ref, "expiration_ref"),
        (request.policy_decision_ref, "policy_decision_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _receipt_ref_pairs(receipt: TrustedRecurringWorkflowReceiptPlan) -> list[Any]:
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.trusted_workflow_ref, "trusted_workflow_ref"),
        (receipt.scope_ref, "scope_ref"),
        (receipt.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (receipt.recurring_contract_ref, "recurring_contract_ref"),
        (receipt.scoped_low_risk_recurring_ref, "scoped_low_risk_recurring_ref"),
        (receipt.cadence_ref, "cadence_ref"),
        (receipt.approval_bundle_ref, "approval_bundle_ref"),
        (receipt.approval_renewal_ref, "approval_renewal_ref"),
        (receipt.expiration_ref, "expiration_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: TrustedRecurringWorkflowDecision) -> list[Any]:
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.trusted_workflow_ref, "trusted_workflow_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (decision.m131_work_session_decision_ref, "m131_work_session_decision_ref"),
        (decision.recurring_contract_ref, "recurring_contract_ref"),
        (decision.scoped_low_risk_recurring_ref, "scoped_low_risk_recurring_ref"),
        (decision.cadence_ref, "cadence_ref"),
        (decision.approval_bundle_ref, "approval_bundle_ref"),
        (decision.approval_renewal_ref, "approval_renewal_ref"),
        (decision.expiration_ref, "expiration_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M132_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M132_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M132_REVIEW_ONLY_REQUIRED"),
    ("trusted_recurring_workflow_only", "M132_TRUSTED_RECURRING_WORKFLOW_ONLY_REQUIRED"),
    ("deterministic", "M132_DETERMINISTIC_REQUIRED"),
    ("local_only", "M132_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M132_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M132_EXACT_SCOPE_REQUIRED"),
    ("mode5_required", "M132_MODE5_REQUIRED"),
    ("exact_m131_work_session_required", "M132_M131_WORK_SESSION_REQUIRED"),
    ("recurring_contract_required", "M132_RECURRING_CONTRACT_REQUIRED"),
    ("scoped_low_risk_recurring_required", "M132_SCOPED_LOW_RISK_RECURRING_REQUIRED"),
    ("cadence_bound_required", "M132_CADENCE_BOUND_REQUIRED"),
    ("approval_bundle_required", "M132_APPROVAL_BUNDLE_REQUIRED"),
    ("approval_renewal_required", "M132_APPROVAL_RENEWAL_REQUIRED"),
    ("expiration_required", "M132_EXPIRATION_REQUIRED"),
    ("stop_conditions_required", "M132_STOP_CONDITIONS_REQUIRED"),
    ("audit_replay_required", "M132_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M132_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M132_KILL_SWITCH_REQUIRED"),
    ("m133_future_only", "M133_FUTURE_ONLY_REQUIRED"),
]

_M132_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M132_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M132_REVIEW_ONLY_REQUIRED"),
    ("trusted_recurring_workflow_only", "M132_TRUSTED_RECURRING_WORKFLOW_ONLY_REQUIRED"),
    ("deterministic", "M132_DETERMINISTIC_REQUIRED"),
    ("local_only", "M132_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M132_SAFE_REFS_ONLY_REQUIRED"),
]

_M132_DECISION_REQUIRED_TRUE = [
    *_M132_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M132_EXACT_SCOPE_REQUIRED"),
    ("mode5_bound", "M132_MODE5_REQUIRED"),
    ("m131_work_session_bound", "M132_M131_WORK_SESSION_REQUIRED"),
    ("recurring_contract_bound", "M132_RECURRING_CONTRACT_REQUIRED"),
    ("scoped_low_risk_recurring_bound", "M132_SCOPED_LOW_RISK_RECURRING_REQUIRED"),
    ("cadence_bound", "M132_CADENCE_BOUND_REQUIRED"),
    ("approval_bundle_bound", "M132_APPROVAL_BUNDLE_REQUIRED"),
    ("approval_renewal_bound", "M132_APPROVAL_RENEWAL_REQUIRED"),
    ("expiration_bound", "M132_EXPIRATION_REQUIRED"),
    ("stop_conditions_bound", "M132_STOP_CONDITIONS_REQUIRED"),
    ("audit_replay_bound", "M132_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M132_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M132_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M132_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M132_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M132_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M132_SAFE_REFS_ONLY_REQUIRED"),
]

_M132_DENIALS = {
    "mode5_runtime_enabled": "M132_MODE5_RUNTIME_DENIED",
    "trusted_recurring_workflow_start_enabled": "M132_WORKFLOW_START_DENIED",
    "recurring_runtime_enabled": "M132_RECURRING_RUNTIME_DENIED",
    "scheduler_enabled": "M132_SCHEDULER_DENIED",
    "background_worker_enabled": "M132_BACKGROUND_WORKER_DENIED",
    "long_running_supervisor_enabled": "M133_LONG_RUNNING_SUPERVISOR_DENIED",
    "autonomous_actions_enabled": "M132_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M132_EXECUTION_DENIED",
    "tool_execution_enabled": "M132_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M132_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M132_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M132_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M132_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M132_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M132_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M132_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M132_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M132_DOWNLOAD_DENIED",
    "upload_enabled": "M132_UPLOAD_DENIED",
    "plugin_execution_enabled": "M132_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M132_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M132_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M132_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M132_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M132_MODEL_CALL_DENIED",
    "memory_write_enabled": "M132_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M132_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M132_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M132_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M132_DEPENDENCY_DENIED",
    "beta_release_enabled": "M132_BETA_RELEASE_DENIED",
    "production_authority_granted": "M132_PRODUCTION_AUTHORITY_DENIED",
}

_M132_REQUEST_DENIALS = {
    "mode5_runtime_requested": "M132_MODE5_RUNTIME_DENIED",
    "trusted_recurring_workflow_start_requested": "M132_WORKFLOW_START_DENIED",
    "recurring_runtime_requested": "M132_RECURRING_RUNTIME_DENIED",
    "recurrence_active": "M132_RECURRENCE_ACTIVE_DENIED",
    "scheduler_requested": "M132_SCHEDULER_DENIED",
    "background_worker_requested": "M132_BACKGROUND_WORKER_DENIED",
    "long_running_supervisor_requested": "M133_LONG_RUNNING_SUPERVISOR_DENIED",
    "autonomous_actions_requested": "M132_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M132_EXECUTION_DENIED",
    "tool_execution_requested": "M132_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M132_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M132_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M132_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M132_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M132_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M132_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M132_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M132_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M132_DOWNLOAD_DENIED",
    "upload_requested": "M132_UPLOAD_DENIED",
    "plugin_execution_requested": "M132_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M132_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M132_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M132_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M132_REMOTE_EXECUTION_DENIED",
    "model_call_requested": "M132_MODEL_CALL_DENIED",
    "memory_write_requested": "M132_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M132_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M132_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M132_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M132_DEPENDENCY_DENIED",
    "beta_release_requested": "M132_BETA_RELEASE_DENIED",
    "production_authority_requested": "M132_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M132_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M132_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED",
}

_M132_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M132_MODE5_RUNTIME_DENIED",
    "trusted_recurring_workflow_start_authorized": "M132_WORKFLOW_START_DENIED",
    "workflow_started": "M132_WORKFLOW_START_DENIED",
    "recurrence_active": "M132_RECURRENCE_ACTIVE_DENIED",
    "recurring_runtime_started": "M132_RECURRING_RUNTIME_DENIED",
    "scheduler_started": "M132_SCHEDULER_DENIED",
    "background_worker_started": "M132_BACKGROUND_WORKER_DENIED",
    "long_running_supervisor_started": "M133_LONG_RUNNING_SUPERVISOR_DENIED",
    "autonomous_actions_authorized": "M132_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M132_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M132_EXECUTION_DENIED",
    "execution_performed": "M132_EXECUTION_DENIED",
    "tool_execution_authorized": "M132_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M132_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M132_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M132_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M132_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M132_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M132_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M132_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M132_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M132_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M132_DOWNLOAD_DENIED",
    "upload_performed": "M132_UPLOAD_DENIED",
    "plugin_execution_performed": "M132_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M132_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M132_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M132_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M132_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M132_MODEL_CALL_DENIED",
    "memory_write_performed": "M132_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M132_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M132_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M132_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M132_DEPENDENCY_DENIED",
    "beta_release_enabled": "M132_BETA_RELEASE_DENIED",
    "production_authority_granted": "M132_PRODUCTION_AUTHORITY_DENIED",
}

_M132_RECEIPT_DENIALS = {
    "store_raw_prompt": "M132_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M132_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M132_SECRET_LIKE_TRUSTED_RECURRING_CONTENT_DENIED",
    "workflow_started": "M132_WORKFLOW_START_DENIED",
    "recurring_runtime_started": "M132_RECURRING_RUNTIME_DENIED",
    "scheduler_started": "M132_SCHEDULER_DENIED",
    "execution_performed": "M132_EXECUTION_DENIED",
}
