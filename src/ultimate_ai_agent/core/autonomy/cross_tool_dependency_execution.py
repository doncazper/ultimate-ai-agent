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


CROSS_TOOL_DEPENDENCY_EXECUTION_DOCS = [
    "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION.md",
    "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_POLICY.md",
    "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_RECEIPT_PLAN.md",
    "docs/autonomy/CROSS_TOOL_DEPENDENCY_EXECUTION_NON_GOALS.md",
    "docs/autonomy/M136_TO_M137_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M136_MAX_DEPENDENCY_STEP_REFS = 64
M136_MAX_DEPENDENCY_EDGE_REFS = 128
M136_MAX_TOOL_REFS = 20


class CrossToolDependencyExecutionStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _CrossToolDependencyExecutionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CrossToolDependencyEdge(_CrossToolDependencyExecutionModel):
    edge_ref: str
    upstream_step_ref: str
    downstream_step_ref: str
    dependency_kind_ref: str
    safe_dependency_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.edge_ref, "edge_ref"),
            (self.upstream_step_ref, "upstream_step_ref"),
            (self.downstream_step_ref, "downstream_step_ref"),
            (self.dependency_kind_ref, "dependency_kind_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.upstream_step_ref == self.downstream_step_ref:
            raise ValueError("M136_SELF_DEPENDENCY_DENIED")
        try:
            _validate_safe_payload(self.safe_dependency_summary)
        except ValueError as exc:
            raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED") from exc
        return self


class CrossToolDependencyExecutionPolicy(_CrossToolDependencyExecutionModel):
    policy_ref: str = "cross-tool-dependency-execution-policy:m136"
    contract_only: bool = True
    review_only: bool = True
    cross_tool_dependency_execution_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m135_recovery_planner_required: bool = True
    m134_human_checkpoint_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    dependency_graph_required: bool = True
    acyclic_graph_required: bool = True
    dependency_order_required: bool = True
    cross_tool_scope_required: bool = True
    dry_run_plan_required: bool = True
    human_checkpoint_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m137_future_only: bool = True
    mode5_runtime_enabled: bool = False
    cross_tool_dependency_runtime_enabled: bool = False
    dependency_execution_enabled: bool = False
    dependency_resolver_runtime_enabled: bool = False
    cross_tool_runtime_enabled: bool = False
    parallel_tool_execution_enabled: bool = False
    tool_state_handoff_enabled: bool = False
    tool_output_routing_enabled: bool = False
    recovery_execution_enabled: bool = False
    supervisor_runtime_enabled: bool = False
    checkpoint_scheduler_enabled: bool = False
    human_checkpoint_prompt_enabled: bool = False
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
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED") from exc
        return self


class CrossToolDependencyExecutionRequest(_CrossToolDependencyExecutionModel):
    request_ref: str
    dependency_execution_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    dependency_graph_ref: str
    dependency_step_refs: list[str]
    dependency_edges: list[CrossToolDependencyEdge]
    safe_tool_refs: list[str]
    dry_run_plan_ref: str
    execution_order_ref: str
    dependency_resolution_ref: str
    conflict_policy_ref: str
    failure_policy_ref: str
    recovery_plan_ref: str
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
    max_dependency_steps: int = Field(gt=1, le=M136_MAX_DEPENDENCY_STEP_REFS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_dependency_summary: str
    contract_only: bool = True
    review_only: bool = True
    cross_tool_dependency_execution_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    cross_tool_dependency_runtime_requested: bool = False
    dependency_execution_requested: bool = False
    dependency_resolver_runtime_requested: bool = False
    cross_tool_runtime_requested: bool = False
    parallel_tool_execution_requested: bool = False
    tool_state_handoff_requested: bool = False
    tool_output_routing_requested: bool = False
    recovery_execution_requested: bool = False
    supervisor_runtime_requested: bool = False
    checkpoint_scheduler_requested: bool = False
    human_checkpoint_prompt_requested: bool = False
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
    contains_raw_tool_payload: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M136_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M136_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M136_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.dependency_step_refs,
            "dependency_step_ref",
            "M136_DEPENDENCY_STEP_REF_REQUIRED",
            max_count=M136_MAX_DEPENDENCY_STEP_REFS,
        )
        _validate_ref_list(
            self.safe_tool_refs,
            "safe_tool_ref",
            "M136_SAFE_TOOL_REF_REQUIRED",
            max_count=M136_MAX_TOOL_REFS,
        )
        if len(self.safe_tool_refs) < 2:
            raise ValueError("M136_CROSS_TOOL_SCOPE_REQUIRED")
        try:
            _validate_safe_payload({"safe_dependency_summary": self.safe_dependency_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED") from exc
        _validate_dependency_graph(self.dependency_step_refs, self.dependency_edges)
        return self


class CrossToolDependencyExecutionReceiptPlan(_CrossToolDependencyExecutionModel):
    receipt_plan_ref: str
    dependency_execution_plan_ref: str
    scope_ref: str
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    dependency_graph_ref: str
    dependency_order_refs: list[str]
    safe_tool_refs: list[str]
    dry_run_plan_ref: str
    execution_order_ref: str
    dependency_resolution_ref: str
    conflict_policy_ref: str
    failure_policy_ref: str
    recovery_plan_ref: str
    checkpoint_ref: str
    human_checkpoint_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_dependency_order_refs_only: bool = True
    store_raw_tool_payload: bool = False
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_secret: bool = False
    dependency_execution_performed: bool = False
    dependency_resolver_started: bool = False
    cross_tool_runtime_started: bool = False
    parallel_tool_execution_performed: bool = False
    tool_state_handoff_performed: bool = False
    tool_output_routing_performed: bool = False
    tool_execution_performed: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "M136 cross-tool dependency execution receipt stores safe refs, "
        "dependency order refs, and summaries only."
    )

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _receipt_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(
            self.dependency_order_refs,
            "dependency_order_ref",
            "M136_DEPENDENCY_ORDER_REF_REQUIRED",
            max_count=M136_MAX_DEPENDENCY_STEP_REFS,
        )
        _validate_ref_list(
            self.safe_tool_refs,
            "safe_tool_ref",
            "M136_SAFE_TOOL_REF_REQUIRED",
            max_count=M136_MAX_TOOL_REFS,
        )
        try:
            _validate_safe_payload(self.safe_summary)
        except ValueError as exc:
            raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED") from exc
        return self


class CrossToolDependencyExecutionDecision(_CrossToolDependencyExecutionModel):
    decision_ref: str
    request_ref: str
    dependency_execution_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    dependency_graph_ref: str
    dependency_step_refs: list[str]
    dependency_edges: list[CrossToolDependencyEdge]
    dependency_order_refs: list[str]
    safe_tool_refs: list[str]
    dry_run_plan_ref: str
    execution_order_ref: str
    dependency_resolution_ref: str
    conflict_policy_ref: str
    failure_policy_ref: str
    recovery_plan_ref: str
    checkpoint_ref: str
    human_checkpoint_ref: str
    policy_decision_ref: str
    risk_decision_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    status: CrossToolDependencyExecutionStatus = (
        CrossToolDependencyExecutionStatus.ready_for_review
    )
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_dependency_steps: int
    max_risk_class: AutonomyRiskClass
    contract_only: bool = True
    review_only: bool = True
    cross_tool_dependency_execution_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m135_recovery_planner_bound: bool = True
    m134_human_checkpoint_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    dependency_graph_bound: bool = True
    acyclic_graph_validated: bool = True
    dependency_order_bound: bool = True
    cross_tool_scope_bound: bool = True
    dry_run_plan_bound: bool = True
    human_checkpoint_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    cross_tool_dependency_runtime_authorized: bool = False
    dependency_execution_authorized: bool = False
    dependency_execution_performed: bool = False
    dependency_resolver_runtime_started: bool = False
    cross_tool_runtime_started: bool = False
    parallel_tool_execution_performed: bool = False
    tool_state_handoff_performed: bool = False
    tool_output_routing_performed: bool = False
    recovery_execution_performed: bool = False
    supervisor_runtime_started: bool = False
    checkpoint_scheduler_started: bool = False
    human_checkpoint_prompt_sent: bool = False
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
    receipt_plan: CrossToolDependencyExecutionReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _decision_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_ref", "M136_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M136_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M136_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.dependency_step_refs,
            "dependency_step_ref",
            "M136_DEPENDENCY_STEP_REF_REQUIRED",
            max_count=M136_MAX_DEPENDENCY_STEP_REFS,
        )
        _validate_ref_list(
            self.dependency_order_refs,
            "dependency_order_ref",
            "M136_DEPENDENCY_ORDER_REF_REQUIRED",
            max_count=M136_MAX_DEPENDENCY_STEP_REFS,
        )
        _validate_ref_list(
            self.safe_tool_refs,
            "safe_tool_ref",
            "M136_SAFE_TOOL_REF_REQUIRED",
            max_count=M136_MAX_TOOL_REFS,
        )
        if len(self.safe_tool_refs) < 2:
            raise ValueError("M136_CROSS_TOOL_SCOPE_REQUIRED")
        _validate_dependency_graph(self.dependency_step_refs, self.dependency_edges)
        if self.dependency_order_refs != _dependency_order_refs(
            self.dependency_step_refs, self.dependency_edges
        ):
            raise ValueError("M136_DEPENDENCY_ORDER_MISMATCH")
        if not self.reason_codes:
            raise ValueError("M136_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload(self.safe_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED") from exc
        return self


def build_cross_tool_dependency_execution_decision(
    request: CrossToolDependencyExecutionRequest,
    policy: CrossToolDependencyExecutionPolicy | None = None,
) -> CrossToolDependencyExecutionDecision:
    active_policy = validate_cross_tool_dependency_execution_policy(
        policy or CrossToolDependencyExecutionPolicy()
    )
    validated_request = validate_cross_tool_dependency_execution_request(request)
    dependency_order_refs = _dependency_order_refs(
        validated_request.dependency_step_refs, validated_request.dependency_edges
    )
    decision = CrossToolDependencyExecutionDecision(
        decision_ref=(
            "cross-tool-dependency-execution-decision:"
            f"{_ref_suffix(validated_request.dependency_execution_plan_ref)}"
        ),
        request_ref=validated_request.request_ref,
        dependency_execution_plan_ref=validated_request.dependency_execution_plan_ref,
        mode_ref=validated_request.mode_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        scope_ref=validated_request.scope_ref,
        resource_refs=list(validated_request.resource_refs),
        capability_refs=list(validated_request.capability_refs),
        allowlist_refs=list(validated_request.allowlist_refs),
        m135_recovery_planner_decision_ref=(
            validated_request.m135_recovery_planner_decision_ref
        ),
        m134_human_checkpoint_decision_ref=(
            validated_request.m134_human_checkpoint_decision_ref
        ),
        m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
        m132_trusted_workflow_decision_ref=(
            validated_request.m132_trusted_workflow_decision_ref
        ),
        dependency_graph_ref=validated_request.dependency_graph_ref,
        dependency_step_refs=list(validated_request.dependency_step_refs),
        dependency_edges=list(validated_request.dependency_edges),
        dependency_order_refs=dependency_order_refs,
        safe_tool_refs=list(validated_request.safe_tool_refs),
        dry_run_plan_ref=validated_request.dry_run_plan_ref,
        execution_order_ref=validated_request.execution_order_ref,
        dependency_resolution_ref=validated_request.dependency_resolution_ref,
        conflict_policy_ref=validated_request.conflict_policy_ref,
        failure_policy_ref=validated_request.failure_policy_ref,
        recovery_plan_ref=validated_request.recovery_plan_ref,
        checkpoint_ref=validated_request.checkpoint_ref,
        human_checkpoint_ref=validated_request.human_checkpoint_ref,
        policy_decision_ref=validated_request.policy_decision_ref,
        risk_decision_ref=validated_request.risk_decision_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        max_dependency_steps=validated_request.max_dependency_steps,
        max_risk_class=validated_request.max_risk_class,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        cross_tool_dependency_execution_only=(
            active_policy.cross_tool_dependency_execution_only
        ),
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_scope_bound=active_policy.exact_scope_required,
        mode5_bound=active_policy.mode5_required,
        m135_recovery_planner_bound=active_policy.m135_recovery_planner_required,
        m134_human_checkpoint_bound=active_policy.m134_human_checkpoint_required,
        m133_supervisor_bound=active_policy.m133_supervisor_required,
        m132_trusted_workflow_bound=active_policy.m132_trusted_workflow_required,
        dependency_graph_bound=active_policy.dependency_graph_required,
        acyclic_graph_validated=active_policy.acyclic_graph_required,
        dependency_order_bound=active_policy.dependency_order_required,
        cross_tool_scope_bound=active_policy.cross_tool_scope_required,
        dry_run_plan_bound=active_policy.dry_run_plan_required,
        human_checkpoint_bound=active_policy.human_checkpoint_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        kill_switch_bound=active_policy.kill_switch_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        reason_codes=[
            "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_CONTRACT_ONLY",
            "M136_ACYCLIC_DEPENDENCY_GRAPH_REQUIRED",
            "M136_EXACT_TOOL_SCOPE_REQUIRED",
            "M136_NO_DEPENDENCY_EXECUTION",
            "M137_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M136 defines a cross-tool dependency execution contract for governed "
            "review only. It binds Mode 5, M135 autonomous recovery planner, "
            "M134 human checkpoint, M133 supervisor, M132 trusted workflow, "
            "dependency graph, acyclic dependency edges, deterministic dependency "
            "order refs, safe tool refs, dry-run plan, conflict and failure "
            "policies, recovery, checkpoint, audit, replay, revocation, "
            "kill-switch, and no-effect receipt refs. It does not execute "
            "dependencies, start a resolver or cross-tool runtime, run tools, "
            "handoff state, route tool output, perform recovery, start "
            "schedulers or workers, execute shell, network, browser, plugin, "
            "connector, mobile, remote, model, memory, or context work, add "
            "routes or controls, add dependencies, enable beta, grant production "
            "authority, or implement M137."
        ),
        receipt_plan=CrossToolDependencyExecutionReceiptPlan(
            receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
            dependency_execution_plan_ref=(
                validated_request.dependency_execution_plan_ref
            ),
            scope_ref=validated_request.scope_ref,
            m135_recovery_planner_decision_ref=(
                validated_request.m135_recovery_planner_decision_ref
            ),
            m134_human_checkpoint_decision_ref=(
                validated_request.m134_human_checkpoint_decision_ref
            ),
            m133_supervisor_decision_ref=validated_request.m133_supervisor_decision_ref,
            m132_trusted_workflow_decision_ref=(
                validated_request.m132_trusted_workflow_decision_ref
            ),
            dependency_graph_ref=validated_request.dependency_graph_ref,
            dependency_order_refs=dependency_order_refs,
            safe_tool_refs=list(validated_request.safe_tool_refs),
            dry_run_plan_ref=validated_request.dry_run_plan_ref,
            execution_order_ref=validated_request.execution_order_ref,
            dependency_resolution_ref=validated_request.dependency_resolution_ref,
            conflict_policy_ref=validated_request.conflict_policy_ref,
            failure_policy_ref=validated_request.failure_policy_ref,
            recovery_plan_ref=validated_request.recovery_plan_ref,
            checkpoint_ref=validated_request.checkpoint_ref,
            human_checkpoint_ref=validated_request.human_checkpoint_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
            revocation_ref=validated_request.revocation_ref,
            kill_switch_ref=validated_request.kill_switch_ref,
        ),
    )
    return validate_cross_tool_dependency_execution_decision(decision)


def validate_cross_tool_dependency_execution_policy(
    policy: CrossToolDependencyExecutionPolicy,
) -> CrossToolDependencyExecutionPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, CrossToolDependencyExecutionPolicy):
        raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED")
    validated = CrossToolDependencyExecutionPolicy.model_validate(payload)
    for field_name, reason in _M136_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M136_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_cross_tool_dependency_execution_request(
    request: CrossToolDependencyExecutionRequest,
) -> CrossToolDependencyExecutionRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, CrossToolDependencyExecutionRequest):
        raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED")
    for field_name, reason in _M136_REQUEST_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = CrossToolDependencyExecutionRequest.model_validate(payload)
    for field_name, reason in _M136_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M136_REQUEST_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M136_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M136_MODE5_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    if len(validated.dependency_step_refs) > validated.max_dependency_steps:
        raise ValueError("M136_DEPENDENCY_STEP_LIMIT_DENIED")
    return validated


def validate_cross_tool_dependency_execution_decision(
    decision: CrossToolDependencyExecutionDecision,
) -> CrossToolDependencyExecutionDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, CrossToolDependencyExecutionDecision):
        raise ValueError("M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED")
    for field_name, reason in _M136_DECISION_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = CrossToolDependencyExecutionDecision.model_validate(payload)
    for field_name, reason in _M136_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != CrossToolDependencyExecutionStatus.ready_for_review:
        raise ValueError("M136_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M136_MODE5_REQUIRED")
    for field_name, reason in _M136_DECISION_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M136_SIDE_EFFECTS_DENIED")
    if "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_CONTRACT_ONLY" not in validated.reason_codes:
        raise ValueError("M136_REASON_CODE_REQUIRED")
    _validate_risk_ceiling(validated.max_risk_class)
    if len(validated.dependency_step_refs) > validated.max_dependency_steps:
        raise ValueError("M136_DEPENDENCY_STEP_LIMIT_DENIED")
    receipt = _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated, receipt)
    return validated


def _validate_receipt_plan(
    receipt_plan: CrossToolDependencyExecutionReceiptPlan,
) -> CrossToolDependencyExecutionReceiptPlan:
    payload = _model_payload(receipt_plan)
    for field_name, reason in _M136_RECEIPT_DENIALS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = CrossToolDependencyExecutionReceiptPlan.model_validate(payload)
    for field_name, reason in _M136_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M136_RECEIPT_DENIALS.items():
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M136_SIDE_EFFECTS_DENIED")
    return validated


def _validate_receipt_binding(
    decision: CrossToolDependencyExecutionDecision,
    receipt: CrossToolDependencyExecutionReceiptPlan,
) -> None:
    for receipt_value, decision_value in [
        (receipt.dependency_execution_plan_ref, decision.dependency_execution_plan_ref),
        (receipt.scope_ref, decision.scope_ref),
        (
            receipt.m135_recovery_planner_decision_ref,
            decision.m135_recovery_planner_decision_ref,
        ),
        (
            receipt.m134_human_checkpoint_decision_ref,
            decision.m134_human_checkpoint_decision_ref,
        ),
        (receipt.m133_supervisor_decision_ref, decision.m133_supervisor_decision_ref),
        (
            receipt.m132_trusted_workflow_decision_ref,
            decision.m132_trusted_workflow_decision_ref,
        ),
        (receipt.dependency_graph_ref, decision.dependency_graph_ref),
        (receipt.dependency_order_refs, decision.dependency_order_refs),
        (receipt.safe_tool_refs, decision.safe_tool_refs),
        (receipt.dry_run_plan_ref, decision.dry_run_plan_ref),
        (receipt.execution_order_ref, decision.execution_order_ref),
        (receipt.dependency_resolution_ref, decision.dependency_resolution_ref),
        (receipt.conflict_policy_ref, decision.conflict_policy_ref),
        (receipt.failure_policy_ref, decision.failure_policy_ref),
        (receipt.recovery_plan_ref, decision.recovery_plan_ref),
        (receipt.checkpoint_ref, decision.checkpoint_ref),
        (receipt.human_checkpoint_ref, decision.human_checkpoint_ref),
        (receipt.audit_ref, decision.audit_ref),
        (receipt.replay_ref, decision.replay_ref),
        (receipt.revocation_ref, decision.revocation_ref),
        (receipt.kill_switch_ref, decision.kill_switch_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M136_RECEIPT_BINDING_MISMATCH")


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
        raise ValueError("M136_REF_LIST_TOO_LONG")
    if len(set(refs)) != len(refs):
        raise ValueError("M136_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_dependency_graph(
    step_refs: list[str], dependency_edges: list[CrossToolDependencyEdge]
) -> None:
    if not dependency_edges:
        raise ValueError("M136_DEPENDENCY_EDGE_REF_REQUIRED")
    if len(dependency_edges) > M136_MAX_DEPENDENCY_EDGE_REFS:
        raise ValueError("M136_REF_LIST_TOO_LONG")
    edge_refs = [edge.edge_ref for edge in dependency_edges]
    if len(set(edge_refs)) != len(edge_refs):
        raise ValueError("M136_REF_DUPLICATE")
    step_ref_set = set(step_refs)
    for edge in dependency_edges:
        if edge.upstream_step_ref not in step_ref_set:
            raise ValueError("M136_DEPENDENCY_EDGE_UNKNOWN_STEP")
        if edge.downstream_step_ref not in step_ref_set:
            raise ValueError("M136_DEPENDENCY_EDGE_UNKNOWN_STEP")
    _dependency_order_refs(step_refs, dependency_edges)


def _dependency_order_refs(
    step_refs: list[str], dependency_edges: list[CrossToolDependencyEdge]
) -> list[str]:
    remaining = set(step_refs)
    outgoing: dict[str, set[str]] = {step_ref: set() for step_ref in step_refs}
    incoming_count: dict[str, int] = {step_ref: 0 for step_ref in step_refs}
    for edge in dependency_edges:
        if edge.downstream_step_ref not in outgoing[edge.upstream_step_ref]:
            outgoing[edge.upstream_step_ref].add(edge.downstream_step_ref)
            incoming_count[edge.downstream_step_ref] += 1
    ready = [step_ref for step_ref in step_refs if incoming_count[step_ref] == 0]
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        if current not in remaining:
            continue
        remaining.remove(current)
        ordered.append(current)
        for downstream in sorted(outgoing[current], key=step_refs.index):
            incoming_count[downstream] -= 1
            if incoming_count[downstream] == 0:
                ready.append(downstream)
    if remaining:
        raise ValueError("M136_DEPENDENCY_CYCLE_DENIED")
    return ordered


def _validate_risk_ceiling(risk: AutonomyRiskClass) -> None:
    if risk != AutonomyRiskClass.low:
        raise ValueError("M136_RISK_CEILING_DENIED")


def _request_ref_pairs(request: CrossToolDependencyExecutionRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.dependency_execution_plan_ref, "dependency_execution_plan_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
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
        (request.dependency_graph_ref, "dependency_graph_ref"),
        (request.dry_run_plan_ref, "dry_run_plan_ref"),
        (request.execution_order_ref, "execution_order_ref"),
        (request.dependency_resolution_ref, "dependency_resolution_ref"),
        (request.conflict_policy_ref, "conflict_policy_ref"),
        (request.failure_policy_ref, "failure_policy_ref"),
        (request.recovery_plan_ref, "recovery_plan_ref"),
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


def _receipt_ref_pairs(receipt: CrossToolDependencyExecutionReceiptPlan) -> list[Any]:
    return [
        (receipt.receipt_plan_ref, "receipt_plan_ref"),
        (receipt.dependency_execution_plan_ref, "dependency_execution_plan_ref"),
        (receipt.scope_ref, "scope_ref"),
        (
            receipt.m135_recovery_planner_decision_ref,
            "m135_recovery_planner_decision_ref",
        ),
        (
            receipt.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (receipt.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            receipt.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (receipt.dependency_graph_ref, "dependency_graph_ref"),
        (receipt.dry_run_plan_ref, "dry_run_plan_ref"),
        (receipt.execution_order_ref, "execution_order_ref"),
        (receipt.dependency_resolution_ref, "dependency_resolution_ref"),
        (receipt.conflict_policy_ref, "conflict_policy_ref"),
        (receipt.failure_policy_ref, "failure_policy_ref"),
        (receipt.recovery_plan_ref, "recovery_plan_ref"),
        (receipt.checkpoint_ref, "checkpoint_ref"),
        (receipt.human_checkpoint_ref, "human_checkpoint_ref"),
        (receipt.audit_ref, "audit_ref"),
        (receipt.replay_ref, "replay_ref"),
        (receipt.revocation_ref, "revocation_ref"),
        (receipt.kill_switch_ref, "kill_switch_ref"),
    ]


def _decision_ref_pairs(decision: CrossToolDependencyExecutionDecision) -> list[Any]:
    return [
        (decision.decision_ref, "decision_ref"),
        (decision.request_ref, "request_ref"),
        (decision.dependency_execution_plan_ref, "dependency_execution_plan_ref"),
        (decision.mode_ref, "mode_ref"),
        (decision.actor_ref, "actor_ref"),
        (decision.user_ref, "user_ref"),
        (decision.workspace_ref, "workspace_ref"),
        (decision.scope_ref, "scope_ref"),
        (
            decision.m135_recovery_planner_decision_ref,
            "m135_recovery_planner_decision_ref",
        ),
        (
            decision.m134_human_checkpoint_decision_ref,
            "m134_human_checkpoint_decision_ref",
        ),
        (decision.m133_supervisor_decision_ref, "m133_supervisor_decision_ref"),
        (
            decision.m132_trusted_workflow_decision_ref,
            "m132_trusted_workflow_decision_ref",
        ),
        (decision.dependency_graph_ref, "dependency_graph_ref"),
        (decision.dry_run_plan_ref, "dry_run_plan_ref"),
        (decision.execution_order_ref, "execution_order_ref"),
        (decision.dependency_resolution_ref, "dependency_resolution_ref"),
        (decision.conflict_policy_ref, "conflict_policy_ref"),
        (decision.failure_policy_ref, "failure_policy_ref"),
        (decision.recovery_plan_ref, "recovery_plan_ref"),
        (decision.checkpoint_ref, "checkpoint_ref"),
        (decision.human_checkpoint_ref, "human_checkpoint_ref"),
        (decision.policy_decision_ref, "policy_decision_ref"),
        (decision.risk_decision_ref, "risk_decision_ref"),
        (decision.audit_ref, "audit_ref"),
        (decision.replay_ref, "replay_ref"),
        (decision.revocation_ref, "revocation_ref"),
        (decision.kill_switch_ref, "kill_switch_ref"),
    ]


_M136_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M136_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M136_REVIEW_ONLY_REQUIRED"),
    (
        "cross_tool_dependency_execution_only",
        "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_ONLY_REQUIRED",
    ),
    ("deterministic", "M136_DETERMINISTIC_REQUIRED"),
    ("local_only", "M136_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M136_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_scope_required", "M136_EXACT_SCOPE_REQUIRED"),
    ("mode5_required", "M136_MODE5_REQUIRED"),
    ("m135_recovery_planner_required", "M136_M135_RECOVERY_PLANNER_REQUIRED"),
    ("m134_human_checkpoint_required", "M136_M134_HUMAN_CHECKPOINT_REQUIRED"),
    ("m133_supervisor_required", "M136_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_required", "M136_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("dependency_graph_required", "M136_DEPENDENCY_GRAPH_REQUIRED"),
    ("acyclic_graph_required", "M136_ACYCLIC_GRAPH_REQUIRED"),
    ("dependency_order_required", "M136_DEPENDENCY_ORDER_REF_REQUIRED"),
    ("cross_tool_scope_required", "M136_CROSS_TOOL_SCOPE_REQUIRED"),
    ("dry_run_plan_required", "M136_DRY_RUN_PLAN_REQUIRED"),
    ("human_checkpoint_required", "M136_HUMAN_CHECKPOINT_REQUIRED"),
    ("audit_replay_required", "M136_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M136_REVOCATION_REQUIRED"),
    ("kill_switch_required", "M136_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M136_NO_EFFECT_RECEIPT_REQUIRED"),
    ("m137_future_only", "M137_FUTURE_ONLY_REQUIRED"),
]

_M136_REQUEST_REQUIRED_TRUE = [
    ("contract_only", "M136_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M136_REVIEW_ONLY_REQUIRED"),
    (
        "cross_tool_dependency_execution_only",
        "M136_CROSS_TOOL_DEPENDENCY_EXECUTION_ONLY_REQUIRED",
    ),
    ("deterministic", "M136_DETERMINISTIC_REQUIRED"),
    ("local_only", "M136_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M136_SAFE_REFS_ONLY_REQUIRED"),
]

_M136_DECISION_REQUIRED_TRUE = [
    *_M136_REQUEST_REQUIRED_TRUE,
    ("exact_scope_bound", "M136_EXACT_SCOPE_REQUIRED"),
    ("mode5_bound", "M136_MODE5_REQUIRED"),
    ("m135_recovery_planner_bound", "M136_M135_RECOVERY_PLANNER_REQUIRED"),
    ("m134_human_checkpoint_bound", "M136_M134_HUMAN_CHECKPOINT_REQUIRED"),
    ("m133_supervisor_bound", "M136_M133_SUPERVISOR_REQUIRED"),
    ("m132_trusted_workflow_bound", "M136_M132_TRUSTED_WORKFLOW_REQUIRED"),
    ("dependency_graph_bound", "M136_DEPENDENCY_GRAPH_REQUIRED"),
    ("acyclic_graph_validated", "M136_ACYCLIC_GRAPH_REQUIRED"),
    ("dependency_order_bound", "M136_DEPENDENCY_ORDER_REF_REQUIRED"),
    ("cross_tool_scope_bound", "M136_CROSS_TOOL_SCOPE_REQUIRED"),
    ("dry_run_plan_bound", "M136_DRY_RUN_PLAN_REQUIRED"),
    ("human_checkpoint_bound", "M136_HUMAN_CHECKPOINT_REQUIRED"),
    ("audit_replay_bound", "M136_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M136_REVOCATION_REQUIRED"),
    ("kill_switch_bound", "M136_KILL_SWITCH_REQUIRED"),
    ("no_effect_receipt_required", "M136_NO_EFFECT_RECEIPT_REQUIRED"),
]

_M136_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M136_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M136_SAFE_REFS_ONLY_REQUIRED"),
    ("store_dependency_order_refs_only", "M136_DEPENDENCY_ORDER_REF_REQUIRED"),
]

_M136_DENIALS = {
    "mode5_runtime_enabled": "M136_MODE5_RUNTIME_DENIED",
    "cross_tool_dependency_runtime_enabled": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "dependency_execution_enabled": "M136_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_runtime_enabled": "M136_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_enabled": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "parallel_tool_execution_enabled": "M136_PARALLEL_TOOL_EXECUTION_DENIED",
    "tool_state_handoff_enabled": "M136_TOOL_STATE_HANDOFF_DENIED",
    "tool_output_routing_enabled": "M136_TOOL_OUTPUT_ROUTING_DENIED",
    "recovery_execution_enabled": "M136_RECOVERY_EXECUTION_DENIED",
    "supervisor_runtime_enabled": "M136_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_enabled": "M136_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_enabled": "M136_PROMPT_RUNTIME_DENIED",
    "scheduler_enabled": "M136_SCHEDULER_DENIED",
    "background_worker_enabled": "M136_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_enabled": "M136_AUTONOMOUS_ACTIONS_DENIED",
    "execution_enabled": "M136_EXECUTION_DENIED",
    "tool_execution_enabled": "M136_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M136_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M136_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M136_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M136_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M136_NETWORK_ACCESS_DENIED",
    "browser_automation_enabled": "M136_BROWSER_AUTOMATION_DENIED",
    "browser_form_enabled": "M136_BROWSER_FORM_DENIED",
    "authenticated_browser_enabled": "M136_AUTHENTICATED_BROWSER_DENIED",
    "download_enabled": "M136_DOWNLOAD_DENIED",
    "upload_enabled": "M136_UPLOAD_DENIED",
    "plugin_execution_enabled": "M136_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_enabled": "M136_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M136_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_enabled": "M136_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M136_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M136_MODEL_CALL_DENIED",
    "memory_write_enabled": "M136_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M136_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M136_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M136_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M136_DEPENDENCY_DENIED",
    "beta_release_enabled": "M136_BETA_RELEASE_DENIED",
    "production_authority_granted": "M136_PRODUCTION_AUTHORITY_DENIED",
}

_M136_REQUEST_DENIALS = {
    "mode5_runtime_requested": "M136_MODE5_RUNTIME_DENIED",
    "cross_tool_dependency_runtime_requested": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "dependency_execution_requested": "M136_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_runtime_requested": "M136_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_requested": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "parallel_tool_execution_requested": "M136_PARALLEL_TOOL_EXECUTION_DENIED",
    "tool_state_handoff_requested": "M136_TOOL_STATE_HANDOFF_DENIED",
    "tool_output_routing_requested": "M136_TOOL_OUTPUT_ROUTING_DENIED",
    "recovery_execution_requested": "M136_RECOVERY_EXECUTION_DENIED",
    "supervisor_runtime_requested": "M136_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_requested": "M136_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_requested": "M136_PROMPT_RUNTIME_DENIED",
    "scheduler_requested": "M136_SCHEDULER_DENIED",
    "background_worker_requested": "M136_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_requested": "M136_AUTONOMOUS_ACTIONS_DENIED",
    "execution_requested": "M136_EXECUTION_DENIED",
    "tool_execution_requested": "M136_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M136_SHELL_EXECUTION_DENIED",
    "command_execution_requested": "M136_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_requested": "M136_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_requested": "M136_FILESYSTEM_MUTATION_DENIED",
    "network_access_requested": "M136_NETWORK_ACCESS_DENIED",
    "browser_automation_requested": "M136_BROWSER_AUTOMATION_DENIED",
    "browser_form_requested": "M136_BROWSER_FORM_DENIED",
    "authenticated_browser_requested": "M136_AUTHENTICATED_BROWSER_DENIED",
    "download_requested": "M136_DOWNLOAD_DENIED",
    "upload_requested": "M136_UPLOAD_DENIED",
    "plugin_execution_requested": "M136_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_requested": "M136_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M136_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_requested": "M136_MOBILE_SENSOR_DENIED",
    "remote_execution_requested": "M136_REMOTE_EXECUTION_DENIED",
    "model_call_requested": "M136_MODEL_CALL_DENIED",
    "memory_write_requested": "M136_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M136_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M136_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M136_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M136_DEPENDENCY_DENIED",
    "beta_release_requested": "M136_BETA_RELEASE_DENIED",
    "production_authority_requested": "M136_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_tool_payload": "M136_RAW_TOOL_PAYLOAD_DENIED",
    "contains_raw_prompt": "M136_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M136_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_secret": "M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED",
}

_M136_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M136_MODE5_RUNTIME_DENIED",
    "cross_tool_dependency_runtime_authorized": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "dependency_execution_authorized": "M136_DEPENDENCY_EXECUTION_DENIED",
    "dependency_execution_performed": "M136_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_runtime_started": "M136_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_started": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "parallel_tool_execution_performed": "M136_PARALLEL_TOOL_EXECUTION_DENIED",
    "tool_state_handoff_performed": "M136_TOOL_STATE_HANDOFF_DENIED",
    "tool_output_routing_performed": "M136_TOOL_OUTPUT_ROUTING_DENIED",
    "recovery_execution_performed": "M136_RECOVERY_EXECUTION_DENIED",
    "supervisor_runtime_started": "M136_SUPERVISOR_RUNTIME_DENIED",
    "checkpoint_scheduler_started": "M136_CHECKPOINT_SCHEDULER_DENIED",
    "human_checkpoint_prompt_sent": "M136_PROMPT_RUNTIME_DENIED",
    "scheduler_started": "M136_SCHEDULER_DENIED",
    "background_worker_started": "M136_BACKGROUND_WORKER_DENIED",
    "autonomous_actions_authorized": "M136_AUTONOMOUS_ACTIONS_DENIED",
    "autonomous_actions_performed": "M136_AUTONOMOUS_ACTIONS_DENIED",
    "execution_authorized": "M136_EXECUTION_DENIED",
    "execution_performed": "M136_EXECUTION_DENIED",
    "tool_execution_authorized": "M136_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M136_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M136_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M136_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M136_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M136_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M136_NETWORK_ACCESS_DENIED",
    "browser_automation_performed": "M136_BROWSER_AUTOMATION_DENIED",
    "browser_form_performed": "M136_BROWSER_FORM_DENIED",
    "authenticated_browser_performed": "M136_AUTHENTICATED_BROWSER_DENIED",
    "download_performed": "M136_DOWNLOAD_DENIED",
    "upload_performed": "M136_UPLOAD_DENIED",
    "plugin_execution_performed": "M136_PLUGIN_EXECUTION_DENIED",
    "connector_runtime_performed": "M136_CONNECTOR_RUNTIME_DENIED",
    "account_auth_performed": "M136_ACCOUNT_AUTH_DENIED",
    "mobile_sensor_performed": "M136_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M136_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M136_MODEL_CALL_DENIED",
    "memory_write_performed": "M136_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M136_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M136_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M136_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M136_DEPENDENCY_DENIED",
    "beta_release_enabled": "M136_BETA_RELEASE_DENIED",
    "production_authority_granted": "M136_PRODUCTION_AUTHORITY_DENIED",
}

_M136_RECEIPT_DENIALS = {
    "store_raw_tool_payload": "M136_RAW_TOOL_PAYLOAD_DENIED",
    "store_raw_prompt": "M136_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M136_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_secret": "M136_SECRET_LIKE_DEPENDENCY_CONTENT_DENIED",
    "dependency_execution_performed": "M136_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_started": "M136_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_started": "M136_CROSS_TOOL_RUNTIME_DENIED",
    "parallel_tool_execution_performed": "M136_PARALLEL_TOOL_EXECUTION_DENIED",
    "tool_state_handoff_performed": "M136_TOOL_STATE_HANDOFF_DENIED",
    "tool_output_routing_performed": "M136_TOOL_OUTPUT_ROUTING_DENIED",
    "tool_execution_performed": "M136_TOOL_EXECUTION_DENIED",
    "execution_performed": "M136_EXECUTION_DENIED",
}
