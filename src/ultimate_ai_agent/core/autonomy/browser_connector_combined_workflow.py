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


BROWSER_CONNECTOR_COMBINED_WORKFLOW_DOCS = [
    "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW.md",
    "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_POLICY.md",
    "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_RECEIPT_PLAN.md",
    "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW_NON_GOALS.md",
    "docs/autonomy/M137_TO_M138_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
M137_MAX_WORKFLOW_STEP_REFS = 64
M137_MAX_BROWSER_PLAN_REFS = 24
M137_MAX_CONNECTOR_PLAN_REFS = 24


class BrowserConnectorCombinedWorkflowStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _BrowserConnectorCombinedWorkflowModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BrowserConnectorCombinedWorkflowPolicy(_BrowserConnectorCombinedWorkflowModel):
    policy_ref: str = "browser-connector-combined-workflow-policy:m137"
    contract_only: bool = True
    review_only: bool = True
    browser_connector_combined_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_required: bool = True
    mode5_required: bool = True
    m136_dependency_execution_required: bool = True
    m135_recovery_planner_required: bool = True
    m134_human_checkpoint_required: bool = True
    m133_supervisor_required: bool = True
    m132_trusted_workflow_required: bool = True
    browser_plan_required: bool = True
    connector_plan_required: bool = True
    combined_dependency_graph_required: bool = True
    dry_run_plan_required: bool = True
    approval_bundle_required: bool = True
    human_checkpoint_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    kill_switch_required: bool = True
    no_effect_receipt_required: bool = True
    m138_future_only: bool = True
    mode5_runtime_enabled: bool = False
    combined_workflow_runtime_enabled: bool = False
    browser_action_enabled: bool = False
    browser_navigation_enabled: bool = False
    browser_click_enabled: bool = False
    browser_form_enabled: bool = False
    browser_download_enabled: bool = False
    browser_upload_enabled: bool = False
    authenticated_browser_enabled: bool = False
    connector_runtime_enabled: bool = False
    connector_read_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    account_auth_enabled: bool = False
    dependency_execution_enabled: bool = False
    dependency_resolver_runtime_enabled: bool = False
    cross_tool_runtime_enabled: bool = False
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
            raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED") from exc
        return self


class BrowserConnectorCombinedWorkflowRequest(_BrowserConnectorCombinedWorkflowModel):
    request_ref: str
    combined_workflow_plan_ref: str
    mode_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    scope_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    m136_dependency_execution_decision_ref: str
    m135_recovery_planner_decision_ref: str
    m134_human_checkpoint_decision_ref: str
    m133_supervisor_decision_ref: str
    m132_trusted_workflow_decision_ref: str
    browser_workflow_ref: str
    browser_observation_ref: str
    browser_action_plan_refs: list[str]
    connector_workflow_ref: str
    connector_account_scope_ref: str
    connector_action_plan_refs: list[str]
    workflow_step_refs: list[str]
    combined_dependency_graph_ref: str
    dependency_order_ref: str
    safe_handoff_ref: str
    dry_run_plan_ref: str
    approval_bundle_ref: str
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
    max_workflow_steps: int = Field(gt=1, le=M137_MAX_WORKFLOW_STEP_REFS)
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    safe_workflow_summary: str
    contract_only: bool = True
    review_only: bool = True
    browser_connector_combined_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mode5_runtime_requested: bool = False
    combined_workflow_runtime_requested: bool = False
    browser_action_requested: bool = False
    browser_navigation_requested: bool = False
    browser_click_requested: bool = False
    browser_form_requested: bool = False
    browser_download_requested: bool = False
    browser_upload_requested: bool = False
    authenticated_browser_requested: bool = False
    connector_runtime_requested: bool = False
    connector_read_runtime_requested: bool = False
    connector_write_requested: bool = False
    connector_send_requested: bool = False
    connector_delete_requested: bool = False
    account_auth_requested: bool = False
    dependency_execution_requested: bool = False
    dependency_resolver_runtime_requested: bool = False
    cross_tool_runtime_requested: bool = False
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
    contains_raw_browser_dom: bool = False
    contains_raw_connector_payload: bool = False
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
        _validate_ref_list(self.resource_refs, "resource_ref", "M137_RESOURCE_REF_REQUIRED")
        _validate_ref_list(
            self.capability_refs, "capability_ref", "M137_CAPABILITY_REF_REQUIRED"
        )
        _validate_ref_list(
            self.allowlist_refs, "allowlist_ref", "M137_ALLOWLIST_REF_REQUIRED"
        )
        _validate_ref_list(
            self.workflow_step_refs,
            "workflow_step_ref",
            "M137_WORKFLOW_STEP_REF_REQUIRED",
            max_count=M137_MAX_WORKFLOW_STEP_REFS,
        )
        _validate_ref_list(
            self.browser_action_plan_refs,
            "browser_action_plan_ref",
            "M137_BROWSER_PLAN_REF_REQUIRED",
            max_count=M137_MAX_BROWSER_PLAN_REFS,
        )
        _validate_ref_list(
            self.connector_action_plan_refs,
            "connector_action_plan_ref",
            "M137_CONNECTOR_PLAN_REF_REQUIRED",
            max_count=M137_MAX_CONNECTOR_PLAN_REFS,
        )
        if len(self.browser_action_plan_refs) < 1:
            raise ValueError("M137_BROWSER_PLAN_REF_REQUIRED")
        if len(self.connector_action_plan_refs) < 1:
            raise ValueError("M137_CONNECTOR_PLAN_REF_REQUIRED")
        if not self.browser_action_plan_refs or not self.connector_action_plan_refs:
            raise ValueError("M137_BROWSER_CONNECTOR_SCOPE_REQUIRED")
        if self.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M137_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M137_RISK_CEILING_DENIED")
        _validate_required_bool(self.contract_only, "M137_CONTRACT_ONLY_REQUIRED")
        _validate_required_bool(self.review_only, "M137_REVIEW_ONLY_REQUIRED")
        _validate_required_bool(
            self.browser_connector_combined_workflow_only,
            "M137_COMBINED_WORKFLOW_ONLY_REQUIRED",
        )
        _validate_required_bool(self.deterministic, "M137_DETERMINISTIC_REQUIRED")
        _validate_required_bool(self.local_only, "M137_LOCAL_ONLY_REQUIRED")
        _validate_required_bool(self.safe_refs_only, "M137_SAFE_REFS_ONLY_REQUIRED")
        try:
            _validate_safe_payload(self.safe_workflow_summary)
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED") from exc
        _deny_enabled(_M137_REQUEST_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M137_SIDE_EFFECTS_DENIED")
        return self


class BrowserConnectorCombinedWorkflowReceiptPlan(
    _BrowserConnectorCombinedWorkflowModel
):
    receipt_plan_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_browser_plan_refs_only: bool = True
    store_connector_plan_refs_only: bool = True
    store_dependency_order_ref_only: bool = True
    store_raw_browser_dom: bool = False
    store_raw_connector_payload: bool = False
    store_raw_prompt: bool = False
    store_raw_provider_payload: bool = False
    store_cookie_or_credential: bool = False
    store_secret: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    combined_workflow_runtime_started: bool = False
    dependency_execution_performed: bool = False
    workflow_step_refs: list[str]
    browser_action_plan_refs: list[str]
    connector_action_plan_refs: list[str]
    dependency_order_ref: str
    safe_receipt_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m61_ref(self.dependency_order_ref, "dependency_order_ref")
        _validate_ref_list(
            self.workflow_step_refs,
            "workflow_step_ref",
            "M137_WORKFLOW_STEP_REF_REQUIRED",
            max_count=M137_MAX_WORKFLOW_STEP_REFS,
        )
        _validate_ref_list(
            self.browser_action_plan_refs,
            "browser_action_plan_ref",
            "M137_BROWSER_PLAN_REF_REQUIRED",
            max_count=M137_MAX_BROWSER_PLAN_REFS,
        )
        _validate_ref_list(
            self.connector_action_plan_refs,
            "connector_action_plan_ref",
            "M137_CONNECTOR_PLAN_REF_REQUIRED",
            max_count=M137_MAX_CONNECTOR_PLAN_REFS,
        )
        try:
            _validate_safe_payload(self.safe_receipt_summary)
        except ValueError as exc:
            raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED") from exc
        for field, reason in _M137_RECEIPT_DENIALS.items():
            if getattr(self, field):
                raise ValueError(reason)
        return self


class BrowserConnectorCombinedWorkflowDecision(
    _BrowserConnectorCombinedWorkflowModel
):
    decision_ref: str
    status: BrowserConnectorCombinedWorkflowStatus = (
        BrowserConnectorCombinedWorkflowStatus.ready_for_review
    )
    selected_mode: AutonomyAuthorityMode = (
        AutonomyAuthorityMode.trusted_recurring_automation
    )
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    contract_only: bool = True
    review_only: bool = True
    browser_connector_combined_workflow_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_scope_bound: bool = True
    mode5_bound: bool = True
    m136_dependency_execution_bound: bool = True
    m135_recovery_planner_bound: bool = True
    m134_human_checkpoint_bound: bool = True
    m133_supervisor_bound: bool = True
    m132_trusted_workflow_bound: bool = True
    browser_plan_bound: bool = True
    connector_plan_bound: bool = True
    combined_dependency_graph_bound: bool = True
    dry_run_plan_bound: bool = True
    approval_bundle_bound: bool = True
    human_checkpoint_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    kill_switch_bound: bool = True
    no_effect_receipt_required: bool = True
    mode5_runtime_authorized: bool = False
    combined_workflow_runtime_authorized: bool = False
    browser_action_authorized: bool = False
    browser_action_performed: bool = False
    browser_navigation_performed: bool = False
    browser_click_performed: bool = False
    browser_form_performed: bool = False
    browser_download_performed: bool = False
    browser_upload_performed: bool = False
    authenticated_browser_used: bool = False
    connector_runtime_authorized: bool = False
    connector_action_authorized: bool = False
    connector_read_performed: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    account_auth_performed: bool = False
    dependency_execution_authorized: bool = False
    dependency_execution_performed: bool = False
    dependency_resolver_runtime_started: bool = False
    cross_tool_runtime_started: bool = False
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
    workflow_step_refs: list[str]
    browser_action_plan_refs: list[str]
    connector_action_plan_refs: list[str]
    dependency_order_ref: str
    receipt_plan: BrowserConnectorCombinedWorkflowReceiptPlan
    safe_decision_summary: str
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(self.dependency_order_ref, "dependency_order_ref")
        _validate_ref_list(
            self.workflow_step_refs,
            "workflow_step_ref",
            "M137_WORKFLOW_STEP_REF_REQUIRED",
            max_count=M137_MAX_WORKFLOW_STEP_REFS,
        )
        _validate_ref_list(
            self.browser_action_plan_refs,
            "browser_action_plan_ref",
            "M137_BROWSER_PLAN_REF_REQUIRED",
            max_count=M137_MAX_BROWSER_PLAN_REFS,
        )
        _validate_ref_list(
            self.connector_action_plan_refs,
            "connector_action_plan_ref",
            "M137_CONNECTOR_PLAN_REF_REQUIRED",
            max_count=M137_MAX_CONNECTOR_PLAN_REFS,
        )
        if self.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
            raise ValueError("M137_MODE5_REQUIRED")
        if self.max_risk_class != AutonomyRiskClass.low:
            raise ValueError("M137_RISK_CEILING_DENIED")
        for field, reason in _M137_DECISION_REQUIRED.items():
            if not getattr(self, field):
                raise ValueError(reason)
        _deny_enabled(_M137_DECISION_DENIALS, _model_payload(self))
        if self.side_effects_performed:
            raise ValueError("M137_SIDE_EFFECTS_DENIED")
        try:
            _validate_safe_payload(self.safe_decision_summary)
        except ValueError as exc:
            raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED") from exc
        return self


def build_browser_connector_combined_workflow_decision(
    request: BrowserConnectorCombinedWorkflowRequest,
    *,
    policy: BrowserConnectorCombinedWorkflowPolicy | None = None,
) -> BrowserConnectorCombinedWorkflowDecision:
    validate_browser_connector_combined_workflow_policy(
        policy or BrowserConnectorCombinedWorkflowPolicy()
    )
    validate_browser_connector_combined_workflow_request(request)
    receipt_plan = BrowserConnectorCombinedWorkflowReceiptPlan(
        receipt_plan_ref=request.no_effect_receipt_plan_ref,
        workflow_step_refs=list(request.workflow_step_refs),
        browser_action_plan_refs=list(request.browser_action_plan_refs),
        connector_action_plan_refs=list(request.connector_action_plan_refs),
        dependency_order_ref=request.dependency_order_ref,
        safe_receipt_summary=(
            "M137 records safe combined browser and connector workflow refs "
            "for review only; no browser or connector action is performed."
        ),
    )
    return BrowserConnectorCombinedWorkflowDecision(
        decision_ref=f"browser-connector-combined-workflow-decision:{_ref_suffix(request.request_ref)}",
        workflow_step_refs=list(request.workflow_step_refs),
        browser_action_plan_refs=list(request.browser_action_plan_refs),
        connector_action_plan_refs=list(request.connector_action_plan_refs),
        dependency_order_ref=request.dependency_order_ref,
        receipt_plan=receipt_plan,
        safe_decision_summary=(
            "M137 is a contract-only combined browser and connector workflow "
            "review envelope; M138 remains future."
        ),
        reason_codes=[
            "M137_BROWSER_CONNECTOR_COMBINED_WORKFLOW_CONTRACT_ONLY",
            "M137_EXACT_BROWSER_CONNECTOR_SCOPE_REQUIRED",
            "M137_NO_BROWSER_OR_CONNECTOR_RUNTIME",
            "M137_NO_COMBINED_WORKFLOW_EXECUTION",
            "M138_REMAINS_FUTURE",
        ],
    )


def validate_browser_connector_combined_workflow_policy(
    policy: BrowserConnectorCombinedWorkflowPolicy,
) -> BrowserConnectorCombinedWorkflowPolicy:
    payload = _model_payload(policy)
    for field, reason in _M137_POLICY_REQUIRED.items():
        if not payload.get(field):
            raise ValueError(reason)
    _deny_enabled(_M137_POLICY_DENIALS, payload)
    if _has_secret_like_extra(payload, BrowserConnectorCombinedWorkflowPolicy):
        raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED")
    validated = BrowserConnectorCombinedWorkflowPolicy.model_validate(payload)
    for field, reason in _M137_POLICY_REQUIRED.items():
        if not getattr(validated, field):
            raise ValueError(reason)
    _deny_enabled(_M137_POLICY_DENIALS, _model_payload(validated))
    return validated


def validate_browser_connector_combined_workflow_request(
    request: BrowserConnectorCombinedWorkflowRequest,
) -> BrowserConnectorCombinedWorkflowRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, BrowserConnectorCombinedWorkflowRequest):
        raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED")
    _deny_enabled(_M137_REQUEST_DENIALS, payload)
    validated = BrowserConnectorCombinedWorkflowRequest.model_validate(payload)
    _deny_enabled(_M137_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M137_SIDE_EFFECTS_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M137_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M137_RISK_CEILING_DENIED")
    if len(validated.workflow_step_refs) > validated.max_workflow_steps:
        raise ValueError("M137_WORKFLOW_STEP_LIMIT_DENIED")
    return validated


def validate_browser_connector_combined_workflow_decision(
    decision: BrowserConnectorCombinedWorkflowDecision,
) -> BrowserConnectorCombinedWorkflowDecision:
    payload = _model_payload(decision)
    if _has_secret_like_extra(payload, BrowserConnectorCombinedWorkflowDecision):
        raise ValueError("M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED")
    _deny_enabled(_M137_DECISION_DENIALS, payload)
    receipt_payload = payload.get("receipt_plan", {})
    if isinstance(receipt_payload, dict):
        _deny_enabled(_M137_RECEIPT_DENIALS, receipt_payload)
    validated = BrowserConnectorCombinedWorkflowDecision.model_validate(payload)
    for field, reason in _M137_DECISION_REQUIRED.items():
        if not getattr(validated, field):
            raise ValueError(reason)
    if validated.status != BrowserConnectorCombinedWorkflowStatus.ready_for_review:
        raise ValueError("M137_STATUS_READY_FOR_REVIEW_REQUIRED")
    if validated.selected_mode != AutonomyAuthorityMode.trusted_recurring_automation:
        raise ValueError("M137_MODE5_REQUIRED")
    if validated.max_risk_class != AutonomyRiskClass.low:
        raise ValueError("M137_RISK_CEILING_DENIED")
    _deny_enabled(_M137_DECISION_DENIALS, _model_payload(validated))
    _validate_m137_receipt_plan(validated.receipt_plan)
    if validated.side_effects_performed:
        raise ValueError("M137_SIDE_EFFECTS_DENIED")
    if (
        "M137_BROWSER_CONNECTOR_COMBINED_WORKFLOW_CONTRACT_ONLY"
        not in validated.reason_codes
    ):
        raise ValueError("M137_REASON_CODE_REQUIRED")
    return validated


def _validate_m137_receipt_plan(
    receipt_plan: BrowserConnectorCombinedWorkflowReceiptPlan,
) -> BrowserConnectorCombinedWorkflowReceiptPlan:
    payload = _model_payload(receipt_plan)
    _deny_enabled(_M137_RECEIPT_DENIALS, payload)
    return BrowserConnectorCombinedWorkflowReceiptPlan.model_validate(payload)


def _request_ref_pairs(request: BrowserConnectorCombinedWorkflowRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.combined_workflow_plan_ref, "combined_workflow_plan_ref"),
        (request.mode_ref, "mode_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.scope_ref, "scope_ref"),
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
        (request.browser_workflow_ref, "browser_workflow_ref"),
        (request.browser_observation_ref, "browser_observation_ref"),
        (request.connector_workflow_ref, "connector_workflow_ref"),
        (request.connector_account_scope_ref, "connector_account_scope_ref"),
        (request.combined_dependency_graph_ref, "combined_dependency_graph_ref"),
        (request.dependency_order_ref, "dependency_order_ref"),
        (request.safe_handoff_ref, "safe_handoff_ref"),
        (request.dry_run_plan_ref, "dry_run_plan_ref"),
        (request.approval_bundle_ref, "approval_bundle_ref"),
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
        raise ValueError("M137_REF_LIST_TOO_LONG")
    seen: set[str] = set()
    for value in values:
        _validate_m61_ref(value, field_name)
        if value in seen:
            raise ValueError("M137_REF_DUPLICATE")
        seen.add(value)


def _validate_required_bool(value: bool, reason: str) -> None:
    if value is not True:
        raise ValueError(reason)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field, reason in denials.items():
        if payload.get(field):
            raise ValueError(reason)


_M137_POLICY_REQUIRED = {
    "contract_only": "M137_CONTRACT_ONLY_REQUIRED",
    "review_only": "M137_REVIEW_ONLY_REQUIRED",
    "browser_connector_combined_workflow_only": "M137_COMBINED_WORKFLOW_ONLY_REQUIRED",
    "deterministic": "M137_DETERMINISTIC_REQUIRED",
    "local_only": "M137_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M137_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_required": "M137_EXACT_SCOPE_REQUIRED",
    "mode5_required": "M137_MODE5_REQUIRED",
    "m136_dependency_execution_required": "M137_M136_BINDING_REQUIRED",
    "m135_recovery_planner_required": "M137_M135_BINDING_REQUIRED",
    "m134_human_checkpoint_required": "M137_M134_BINDING_REQUIRED",
    "m133_supervisor_required": "M137_M133_BINDING_REQUIRED",
    "m132_trusted_workflow_required": "M137_M132_BINDING_REQUIRED",
    "browser_plan_required": "M137_BROWSER_PLAN_REF_REQUIRED",
    "connector_plan_required": "M137_CONNECTOR_PLAN_REF_REQUIRED",
    "combined_dependency_graph_required": "M137_DEPENDENCY_GRAPH_REF_REQUIRED",
    "dry_run_plan_required": "M137_DRY_RUN_PLAN_REQUIRED",
    "approval_bundle_required": "M137_APPROVAL_BUNDLE_REQUIRED",
    "human_checkpoint_required": "M137_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_required": "M137_AUDIT_REPLAY_REQUIRED",
    "revocation_required": "M137_REVOCATION_REQUIRED",
    "kill_switch_required": "M137_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M137_NO_EFFECT_RECEIPT_REQUIRED",
    "m138_future_only": "M138_FUTURE_ONLY_REQUIRED",
}

_M137_POLICY_DENIALS = {
    "mode5_runtime_enabled": "M137_MODE5_RUNTIME_DENIED",
    "combined_workflow_runtime_enabled": "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
    "browser_action_enabled": "M137_BROWSER_ACTION_DENIED",
    "browser_navigation_enabled": "M137_BROWSER_NAVIGATION_DENIED",
    "browser_click_enabled": "M137_BROWSER_CLICK_DENIED",
    "browser_form_enabled": "M137_BROWSER_FORM_DENIED",
    "browser_download_enabled": "M137_BROWSER_DOWNLOAD_DENIED",
    "browser_upload_enabled": "M137_BROWSER_UPLOAD_DENIED",
    "authenticated_browser_enabled": "M137_AUTHENTICATED_BROWSER_DENIED",
    "connector_runtime_enabled": "M137_CONNECTOR_RUNTIME_DENIED",
    "connector_read_runtime_enabled": "M137_CONNECTOR_RUNTIME_DENIED",
    "connector_write_enabled": "M137_CONNECTOR_WRITE_DENIED",
    "connector_send_enabled": "M137_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M137_CONNECTOR_DELETE_DENIED",
    "account_auth_enabled": "M137_ACCOUNT_AUTH_DENIED",
    "dependency_execution_enabled": "M137_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_runtime_enabled": "M137_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_enabled": "M137_CROSS_TOOL_RUNTIME_DENIED",
    "tool_execution_enabled": "M137_TOOL_EXECUTION_DENIED",
    "execution_enabled": "M137_EXECUTION_DENIED",
    "shell_execution_enabled": "M137_SHELL_EXECUTION_DENIED",
    "command_execution_enabled": "M137_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_enabled": "M137_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_enabled": "M137_FILESYSTEM_MUTATION_DENIED",
    "network_access_enabled": "M137_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M137_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_enabled": "M137_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M137_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M137_MODEL_CALL_DENIED",
    "memory_write_enabled": "M137_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M137_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M137_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M137_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M137_DEPENDENCY_DENIED",
    "beta_release_enabled": "M137_BETA_RELEASE_DENIED",
    "production_authority_granted": "M137_PRODUCTION_AUTHORITY_DENIED",
}

_M137_REQUEST_DENIALS = {
    **{key.replace("_enabled", "_requested"): value for key, value in _M137_POLICY_DENIALS.items()},
    "dependency_requested": "M137_DEPENDENCY_DENIED",
    "production_authority_requested": "M137_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_browser_dom": "M137_RAW_BROWSER_DOM_DENIED",
    "contains_raw_connector_payload": "M137_RAW_CONNECTOR_PAYLOAD_DENIED",
    "contains_raw_prompt": "M137_RAW_PROMPT_DENIED",
    "contains_raw_provider_payload": "M137_RAW_PROVIDER_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M137_COOKIE_OR_CREDENTIAL_DENIED",
    "contains_secret": "M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED",
}

_M137_DECISION_REQUIRED = {
    "contract_only": "M137_CONTRACT_ONLY_REQUIRED",
    "review_only": "M137_REVIEW_ONLY_REQUIRED",
    "browser_connector_combined_workflow_only": "M137_COMBINED_WORKFLOW_ONLY_REQUIRED",
    "deterministic": "M137_DETERMINISTIC_REQUIRED",
    "local_only": "M137_LOCAL_ONLY_REQUIRED",
    "safe_refs_only": "M137_SAFE_REFS_ONLY_REQUIRED",
    "exact_scope_bound": "M137_EXACT_SCOPE_REQUIRED",
    "mode5_bound": "M137_MODE5_REQUIRED",
    "m136_dependency_execution_bound": "M137_M136_BINDING_REQUIRED",
    "m135_recovery_planner_bound": "M137_M135_BINDING_REQUIRED",
    "m134_human_checkpoint_bound": "M137_M134_BINDING_REQUIRED",
    "m133_supervisor_bound": "M137_M133_BINDING_REQUIRED",
    "m132_trusted_workflow_bound": "M137_M132_BINDING_REQUIRED",
    "browser_plan_bound": "M137_BROWSER_PLAN_REF_REQUIRED",
    "connector_plan_bound": "M137_CONNECTOR_PLAN_REF_REQUIRED",
    "combined_dependency_graph_bound": "M137_DEPENDENCY_GRAPH_REF_REQUIRED",
    "dry_run_plan_bound": "M137_DRY_RUN_PLAN_REQUIRED",
    "approval_bundle_bound": "M137_APPROVAL_BUNDLE_REQUIRED",
    "human_checkpoint_bound": "M137_HUMAN_CHECKPOINT_REQUIRED",
    "audit_replay_bound": "M137_AUDIT_REPLAY_REQUIRED",
    "revocation_bound": "M137_REVOCATION_REQUIRED",
    "kill_switch_bound": "M137_KILL_SWITCH_REQUIRED",
    "no_effect_receipt_required": "M137_NO_EFFECT_RECEIPT_REQUIRED",
}

_M137_DECISION_DENIALS = {
    "mode5_runtime_authorized": "M137_MODE5_RUNTIME_DENIED",
    "combined_workflow_runtime_authorized": "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
    "browser_action_authorized": "M137_BROWSER_ACTION_DENIED",
    "browser_action_performed": "M137_BROWSER_ACTION_DENIED",
    "browser_navigation_performed": "M137_BROWSER_NAVIGATION_DENIED",
    "browser_click_performed": "M137_BROWSER_CLICK_DENIED",
    "browser_form_performed": "M137_BROWSER_FORM_DENIED",
    "browser_download_performed": "M137_BROWSER_DOWNLOAD_DENIED",
    "browser_upload_performed": "M137_BROWSER_UPLOAD_DENIED",
    "authenticated_browser_used": "M137_AUTHENTICATED_BROWSER_DENIED",
    "connector_runtime_authorized": "M137_CONNECTOR_RUNTIME_DENIED",
    "connector_action_authorized": "M137_CONNECTOR_ACTION_DENIED",
    "connector_read_performed": "M137_CONNECTOR_RUNTIME_DENIED",
    "connector_write_performed": "M137_CONNECTOR_WRITE_DENIED",
    "connector_send_performed": "M137_CONNECTOR_SEND_DENIED",
    "connector_delete_performed": "M137_CONNECTOR_DELETE_DENIED",
    "account_auth_performed": "M137_ACCOUNT_AUTH_DENIED",
    "dependency_execution_authorized": "M137_DEPENDENCY_EXECUTION_DENIED",
    "dependency_execution_performed": "M137_DEPENDENCY_EXECUTION_DENIED",
    "dependency_resolver_runtime_started": "M137_DEPENDENCY_RESOLVER_DENIED",
    "cross_tool_runtime_started": "M137_CROSS_TOOL_RUNTIME_DENIED",
    "tool_execution_authorized": "M137_TOOL_EXECUTION_DENIED",
    "tool_execution_performed": "M137_TOOL_EXECUTION_DENIED",
    "execution_authorized": "M137_EXECUTION_DENIED",
    "execution_performed": "M137_EXECUTION_DENIED",
    "shell_execution_performed": "M137_SHELL_EXECUTION_DENIED",
    "command_execution_performed": "M137_COMMAND_EXECUTION_DENIED",
    "subprocess_execution_performed": "M137_SUBPROCESS_EXECUTION_DENIED",
    "filesystem_mutation_performed": "M137_FILESYSTEM_MUTATION_DENIED",
    "network_access_performed": "M137_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M137_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_performed": "M137_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M137_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M137_MODEL_CALL_DENIED",
    "memory_write_performed": "M137_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M137_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M137_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M137_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M137_DEPENDENCY_DENIED",
    "beta_release_enabled": "M137_BETA_RELEASE_DENIED",
    "production_authority_granted": "M137_PRODUCTION_AUTHORITY_DENIED",
}

_M137_RECEIPT_DENIALS = {
    "store_raw_browser_dom": "M137_RAW_BROWSER_DOM_DENIED",
    "store_raw_connector_payload": "M137_RAW_CONNECTOR_PAYLOAD_DENIED",
    "store_raw_prompt": "M137_RAW_PROMPT_DENIED",
    "store_raw_provider_payload": "M137_RAW_PROVIDER_PAYLOAD_DENIED",
    "store_cookie_or_credential": "M137_COOKIE_OR_CREDENTIAL_DENIED",
    "store_secret": "M137_SECRET_LIKE_WORKFLOW_CONTENT_DENIED",
    "browser_action_performed": "M137_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M137_CONNECTOR_ACTION_DENIED",
    "combined_workflow_runtime_started": "M137_COMBINED_WORKFLOW_RUNTIME_DENIED",
    "dependency_execution_performed": "M137_DEPENDENCY_EXECUTION_DENIED",
}
