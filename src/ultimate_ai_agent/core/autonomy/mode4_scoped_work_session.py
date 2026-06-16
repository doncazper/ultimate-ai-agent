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


MODE4_SCOPED_WORK_SESSION_DOCS = [
    "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION.md",
    "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_POLICY.md",
    "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMY_MODE4_SCOPED_WORK_SESSION_NON_GOALS.md",
    "docs/autonomy/M131_TO_M132_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M131_MAX_WORK_SESSION_SECONDS = 7200


class Mode4ScopedWorkSessionStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _Mode4ScopedWorkSessionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class Mode4ScopedWorkSessionPolicy(_Mode4ScopedWorkSessionModel):
    policy_ref: str = "mode4-scoped-work-session-policy:m131"
    contract_only: bool = True
    review_only: bool = True
    scoped_work_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    actor_bound_required: bool = True
    resource_bound_required: bool = True
    capability_bound_required: bool = True
    allowlist_bound_required: bool = True
    duration_bound_required: bool = True
    policy_decision_required: bool = True
    approval_bundle_required: bool = True
    risk_decision_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    m132_future_only: bool = True
    mode4_runtime_enabled: bool = False
    scoped_work_session_start_enabled: bool = False
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
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    trusted_recurring_workflow_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED") from exc
        return self


class Mode4ScopedWorkSessionRequest(_Mode4ScopedWorkSessionModel):
    request_ref: str
    work_session_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    policy_decision_ref: str
    approval_bundle_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    requested_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.scoped_autonomy_window
    max_duration_seconds: int = Field(gt=0, le=M131_MAX_WORK_SESSION_SECONDS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.medium
    safe_goal_summary: str
    contract_only: bool = True
    review_only: bool = True
    scoped_work_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode4_runtime_requested: bool = False
    scoped_work_session_start_requested: bool = False
    session_active: bool = False
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
    background_worker_requested: bool = False
    scheduler_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    trusted_recurring_workflow_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M131_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M131_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M131_ALLOWLIST_REF_REQUIRED"
        )
        try:
            _validate_safe_payload({"safe_goal_summary": self.safe_goal_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED") from exc
        return self


class Mode4ScopedWorkSessionReceiptPlan(_Mode4ScopedWorkSessionModel):
    receipt_plan_ref: str
    work_session_ref: str
    scope_ref: str
    policy_decision_ref: str
    approval_bundle_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    session_started: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M131 Mode 4 scoped work-session receipt stores safe refs and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED") from exc
        return self


class Mode4ScopedWorkSessionDecision(_Mode4ScopedWorkSessionModel):
    decision_ref: str
    request_ref: str
    work_session_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    policy_decision_ref: str
    approval_bundle_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: Mode4ScopedWorkSessionStatus = Mode4ScopedWorkSessionStatus.ready_for_review
    selected_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.scoped_autonomy_window
    max_duration_seconds: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    scoped_work_session_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    actor_bound: bool = True
    resource_bound: bool = True
    capability_bound: bool = True
    allowlist_bound: bool = True
    policy_decision_bound: bool = True
    approval_bundle_bound: bool = True
    risk_decision_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode4_runtime_authorized: bool = False
    scoped_work_session_start_authorized: bool = False
    session_started: bool = False
    session_active: bool = False
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
    background_worker_started: bool = False
    scheduler_started: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    trusted_recurring_workflow_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    receipt_plan: Mode4ScopedWorkSessionReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M131_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M131_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M131_ALLOWLIST_REF_REQUIRED"
        )
        if not self.reason_codes:
            raise ValueError("M131_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED") from exc
        return self


def build_mode4_scoped_work_session_decision(
    request: Mode4ScopedWorkSessionRequest,
    policy: Mode4ScopedWorkSessionPolicy | None = None,
) -> Mode4ScopedWorkSessionDecision:
    active_policy = validate_mode4_scoped_work_session_policy(
        policy or Mode4ScopedWorkSessionPolicy()
    )
    validated_request = validate_mode4_scoped_work_session_request(request)
    decision = Mode4ScopedWorkSessionDecision(
        decision_ref=f"mode4-scoped-work-session-decision:{_ref_suffix(validated_request.work_session_ref)}",
        request_ref=validated_request.request_ref,
        work_session_ref=validated_request.work_session_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        policy_decision_ref=validated_request.policy_decision_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        max_duration_seconds=validated_request.max_duration_seconds,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        scoped_work_session_only=active_policy.scoped_work_session_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        actor_bound=active_policy.actor_bound_required,
        resource_bound=active_policy.resource_bound_required,
        capability_bound=active_policy.capability_bound_required,
        allowlist_bound=active_policy.allowlist_bound_required,
        policy_decision_bound=active_policy.policy_decision_required,
        approval_bundle_bound=active_policy.approval_bundle_required,
        risk_decision_bound=active_policy.risk_decision_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=active_policy.duration_bound_required,
        reason_codes=[
            "M131_MODE4_SCOPED_WORK_SESSION_CONTRACT_ONLY",
            "M131_EXACT_SCOPE_REQUIRED",
            "M131_APPROVAL_BUNDLE_REQUIRED",
            "M131_NO_SESSION_START_OR_EXECUTION",
            "M132_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M131 defines a Mode 4 scoped work-session contract for governed "
            "review only. It binds actor, user, workspace, scope, resource, "
            "capability, allowlist, policy, approval bundle, risk, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "does not start a session, perform autonomous actions, execute "
            "tools, shell, network, browser, plugin, connector, mobile, remote, "
            "background, scheduler, model, memory, or context work, add routes "
            "or controls, add dependencies, enable beta, grant production "
            "authority, or implement M132."
        ),
        receipt_plan=Mode4ScopedWorkSessionReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            work_session_ref=validated_request.work_session_ref,
            scope_ref=validated_request.scope_ref,
            policy_decision_ref=validated_request.policy_decision_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            risk_decision_ref=validated_request.risk_decision_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_mode4_scoped_work_session_decision(decision)


def validate_mode4_scoped_work_session_policy(
    policy: Mode4ScopedWorkSessionPolicy,
) -> Mode4ScopedWorkSessionPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, Mode4ScopedWorkSessionPolicy):
        raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED")
    validated = Mode4ScopedWorkSessionPolicy.model_validate(payload)
    for field_name, reason in _M131_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M131_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_mode4_scoped_work_session_request(
    request: Mode4ScopedWorkSessionRequest,
) -> Mode4ScopedWorkSessionRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, Mode4ScopedWorkSessionRequest):
        raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED")
    for field_name, reason in _M131_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = Mode4ScopedWorkSessionRequest.model_validate(payload)
    for field_name, reason in _M131_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M131_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M131_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.scoped_autonomy_window:
        raise ValueError("M131_MODE4_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    return validated


def validate_mode4_scoped_work_session_decision(
    decision: Mode4ScopedWorkSessionDecision,
) -> Mode4ScopedWorkSessionDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, Mode4ScopedWorkSessionDecision):
        raise ValueError("M131_SECRET_LIKE_MODE4_CONTENT_DENIED")
    for field_name, reason in _M131_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = Mode4ScopedWorkSessionDecision.model_validate(payload)
    for field_name, reason in _M131_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != Mode4ScopedWorkSessionStatus.ready_for_review:
        raise ValueError("M131_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.scoped_autonomy_window:
        raise ValueError("M131_MODE4_REQUIRED")
    for field_name, reason in _M131_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M131_SIDE_EFFECTS_DENIED")
    if "M131_MODE4_SCOPED_WORK_SESSION_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M131_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: Mode4ScopedWorkSessionReceiptPlan,
) -> Mode4ScopedWorkSessionReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M131_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = Mode4ScopedWorkSessionReceiptPlan.model_validate(payload)
    for field_name, reason in _M131_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M131_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M131_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: Mode4ScopedWorkSessionDecision,
    receipt: Mode4ScopedWorkSessionReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.work_session_ref, decision.work_session_ref),
        (receipt.scope_ref, decision.scope_ref),
        (receipt.policy_decision_ref, decision.policy_decision_ref),
        (receipt.approval_bundle_ref, decision.approval_bundle_ref),
        (receipt.risk_decision_ref, decision.risk_decision_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M131_RECEIPT_BINDING_MISMATCH")


def _validate_ref_list(refs: list[str], field_name: str, reason: str) -> None:
    if not refs:
        raise ValueError(reason)
    if len(set(refs)) != len(refs):
        raise ValueError("M131_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk in {AutonomyRiskClass.high, AutonomyRiskClass.critical}:
        raise ValueError("M131_RISK_CEILING_DENIED")


def _request_ref_pairs(request: Mode4ScopedWorkSessionRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.work_session_ref, "work_session_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
        (request.policy_decision_ref, "policy_decision_ref"),
        (request.approval_bundle_ref, "approval_bundle_ref"),
        (request.risk_decision_ref, "risk_decision_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _receipt_ref_pairs(receipt: Mode4ScopedWorkSessionReceiptPlan):
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.work_session_ref, "work_session_ref"),
        (receipt.scope_ref, "scope_ref"),
        (receipt.policy_decision_ref, "policy_decision_ref"),
        (receipt.approval_bundle_ref, "approval_bundle_ref"),
        (receipt.risk_decision_ref, "risk_decision_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: Mode4ScopedWorkSessionDecision):
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.work_session_ref, "work_session_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.approval_bundle_ref, "approval_bundle_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M131_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M131_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M131_REVIEW_ONLY_REQUIRED"),
    ("scoped_work_session_only", "M131_SCOPED_WORK_SESSION_ONLY_REQUIRED"),
    ("deterministic", "M131_DETERMINISTIC_REQUIRED"),
    ("local_only", "M131_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M131_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M131_EXACT_SCOPE_REQUIRED"),
    ("actor_bound_required", "M131_ACTOR_BOUND_REQUIRED"),
    ("resource_bound_required", "M131_RESOURCE_BOUND_REQUIRED"),
    ("capability_bound_required", "M131_CAPABILITY_BOUND_REQUIRED"),
    ("allowlist_bound_required", "M131_ALLOWLIST_BOUND_REQUIRED"),
    ("duration_bound_required", "M131_DURATION_BOUND_REQUIRED"),
    ("policy_decision_required", "M131_POLICY_DECISION_REQUIRED"),
    ("approval_bundle_required", "M131_APPROVAL_BUNDLE_REQUIRED"),
    ("risk_decision_required", "M131_RISK_DECISION_REQUIRED"),
    ("audit_replay_required", "M131_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M131_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M131_KILL_SWITCH_REQUIRED"),
    ("m132_future_only", "M132_FUTURE_ONLY_REQUIRED"),
]

_M131_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M131_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M131_REVIEW_ONLY_REQUIRED"),
    ("scoped_work_session_only", "M131_SCOPED_WORK_SESSION_ONLY_REQUIRED"),
    ("deterministic", "M131_DETERMINISTIC_REQUIRED"),
    ("local_only", "M131_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M131_SAFE_REFS_ONLY_REQUIRED"),
]

_M131_DECISION_REQUIRED_TRUE = [
    *_M131_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M131_EXACT_SCOPE_REQUIRED"),
    ("actor_bound", "M131_ACTOR_BOUND_REQUIRED"),
    ("resource_bound", "M131_RESOURCE_BOUND_REQUIRED"),
    ("capability_bound", "M131_CAPABILITY_BOUND_REQUIRED"),
    ("allowlist_bound", "M131_ALLOWLIST_BOUND_REQUIRED"),
    ("policy_decision_bound", "M131_POLICY_DECISION_REQUIRED"),
    ("approval_bundle_bound", "M131_APPROVAL_BUNDLE_REQUIRED"),
    ("risk_decision_bound", "M131_RISK_DECISION_REQUIRED"),
    ("audit_replay_bound", "M131_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M131_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M131_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M131_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M131_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M131_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M131_SAFE_REFS_ONLY_REQUIRED"),
]

_M131_DENIALS = {
    "mode4_runtime_enabled": "M131_MODE4_RUNTIME_DENIED",
    "scoped_work_session_start_enabled": "M131_SESSION_START_DENIED",
    "autonomous_actions_enabled": "M131_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M131_EXECUTION_DENIED",
    "tool_execution_enabled": "M131_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M131_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M131_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M131_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M131_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M131_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M131_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M131_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M131_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M131_DOWNLOAD_DENIED",
    "upload_enabled": "M131_UPLOAD_DENIED",
    "plugin_execution_enabled": "M131_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M131_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M131_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M131_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M131_REMOTE_EXECUTION_DENIED",
    "background_worker_enabled": "M131_BACKGROUND_WORKER_DENIED",
    "scheduler_enabled": "M131_SCHEDULER_DENIED",
    "model_call_enabled": "M131_MODEL_CALL_DENIED",
    "memory_write_enabled": "M131_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M131_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M131_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M131_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M131_DEPENDENCY_DENIED",
    "beta_release_enabled": "M131_BETA_RELEASE_DENIED",
    "production_authority_granted": "M131_PRODUCTION_AUTHORITY_DENIED",
    "trusted_recurring_workflow_enabled": "M132_TRUSTED_RECURRING_WORKFLOW_DENIED",
}

_M131_REQUEST_DENIALS = {
    "mode4_runtime_requested": "M131_MODE4_RUNTIME_DENIED",
    "scoped_work_session_start_requested": "M131_SESSION_START_DENIED",
    "session_active": "M131_SESSION_ACTIVE_DENIED",
    "autonomous_actions_requested": "M131_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M131_EXECUTION_DENIED",
    "tool_execution_requested": "M131_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M131_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M131_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M131_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M131_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M131_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M131_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M131_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M131_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M131_DOWNLOAD_DENIED",
    "upload_requested": "M131_UPLOAD_DENIED",
    "plugin_execution_requested": "M131_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M131_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M131_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M131_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M131_REMOTE_EXECUTION_DENIED",
    "background_worker_requested": "M131_BACKGROUND_WORKER_DENIED",
    "scheduler_requested": "M131_SCHEDULER_DENIED",
    "model_call_requested": "M131_MODEL_CALL_DENIED",
    "memory_write_requested": "M131_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M131_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M131_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M131_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M131_DEPENDENCY_DENIED",
    "beta_release_requested": "M131_BETA_RELEASE_DENIED",
    "production_authority_requested": "M131_PRODUCTION_AUTHORITY_DENIED",
    "trusted_recurring_workflow_requested": "M132_TRUSTED_RECURRING_WORKFLOW_DENIED",
    "contains_raw_prompt": "M131_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M131_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M131_SECRET_LIKE_MODE4_CONTENT_DENIED",
}

_M131_DECISION_DENIALS = {
    "mode4_runtime_authorized": "M131_MODE4_RUNTIME_DENIED",
    "scoped_work_session_start_authorized": "M131_SESSION_START_DENIED",
    "session_started": "M131_SESSION_START_DENIED",
    "session_active": "M131_SESSION_ACTIVE_DENIED",
    "autonomous_actions_authorized": "M131_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M131_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M131_EXECUTION_DENIED",
    "execution_performed": "M131_EXECUTION_DENIED",
    "tool_execution_authorized": "M131_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M131_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M131_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M131_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M131_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M131_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M131_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M131_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M131_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M131_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M131_DOWNLOAD_DENIED",
    "upload_performed": "M131_UPLOAD_DENIED",
    "plugin_execution_performed": "M131_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M131_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M131_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M131_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M131_REMOTE_EXECUTION_DENIED",
    "background_worker_started": "M131_BACKGROUND_WORKER_DENIED",
    "scheduler_started": "M131_SCHEDULER_DENIED",
    "model_call_performed": "M131_MODEL_CALL_DENIED",
    "memory_write_performed": "M131_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M131_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M131_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M131_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M131_DEPENDENCY_DENIED",
    "beta_release_enabled": "M131_BETA_RELEASE_DENIED",
    "production_authority_granted": "M131_PRODUCTION_AUTHORITY_DENIED",
    "trusted_recurring_workflow_enabled": "M132_TRUSTED_RECURRING_WORKFLOW_DENIED",
}

_M131_RECEIPT_DENIALS = {
    "store_raw_prompt": "M131_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M131_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M131_SECRET_LIKE_MODE4_CONTENT_DENIED",
    "session_started": "M131_SESSION_START_DENIED",
    "execution_performed": "M131_EXECUTION_DENIED",
}
