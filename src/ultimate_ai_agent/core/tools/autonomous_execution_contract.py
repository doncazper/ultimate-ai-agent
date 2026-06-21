from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


AUTONOMOUS_TOOL_EXECUTION_CONTRACT_DOCS = [
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_CONTRACT_POLICY.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_RECEIPT_PLAN.md",
    "docs/tools/AUTONOMOUS_TOOL_EXECUTION_NON_GOALS.md",
    "docs/tools/M91_TO_M92_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M91_PRIOR_MILESTONE_REFS = (
    "milestone:M53",
    "milestone:M61",
    "milestone:M62",
    "milestone:M63",
    "milestone:M66",
    "milestone:M67",
    "milestone:M68",
    "milestone:M70",
    "milestone:M80",
    "milestone:M90",
)
M91_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class AutonomousToolExecutionContractStatus(str, Enum):
    contract_ready_for_review = "contract_ready_for_review"


class _AutonomousToolExecutionContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomousToolExecutionContractPolicy(_AutonomousToolExecutionContractModel):
    policy_ref: str = "autonomous-tool-execution-contract-policy:m91"
    autonomous_tool_execution_contract_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m90_hardening_binding_required: bool = True
    approval_refs_are_identifiers_only: bool = True
    m92_future_only: bool = True
    autonomous_tool_execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    execution_enabled: bool = False
    session_start_enabled: bool = False
    background_worker_enabled: bool = False
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


class AutonomousToolExecutionContractRequest(_AutonomousToolExecutionContractModel):
    request_ref: str
    contract_ref: str
    shell_subprocess_hardening_freeze_decision_ref: str
    emergency_stop_process_kill_safety_decision_ref: str
    command_ref: str
    sandbox_spec_ref: str
    approval_bundle_ref: str
    approval_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    autonomy_session_ref: str
    safe_execution_scope_ref: str
    safe_tool_ref: str
    safe_contract_summary: str
    safe_contract_refs: list[str]
    prior_milestone_refs: list[str]
    shell_subprocess_hardening_freeze_decision: Any
    autonomous_tool_execution_contract_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    dry_run_plan_only: bool = True
    execution_requested: bool = False
    tool_execution_requested: bool = False
    autonomous_execution_requested: bool = False
    session_start_requested: bool = False
    background_worker_requested: bool = False
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
            (self.contract_ref, "contract_ref"),
            (
                self.shell_subprocess_hardening_freeze_decision_ref,
                "shell_subprocess_hardening_freeze_decision_ref",
            ),
            (
                self.emergency_stop_process_kill_safety_decision_ref,
                "emergency_stop_process_kill_safety_decision_ref",
            ),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.autonomy_session_ref, "autonomy_session_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_contract_refs:
            _validate_m61_ref(ref, "safe_contract_ref")
        _validate_safe_payload(self.safe_contract_summary)
        return self


class AutonomousToolExecutionContractReceiptPlan(_AutonomousToolExecutionContractModel):
    receipt_plan_ref: str
    contract_ref: str
    shell_subprocess_hardening_freeze_decision_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    safe_execution_scope_ref: str
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
    safe_summary: str = "M91 autonomous tool execution contract receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.contract_ref, "contract_ref"),
            (
                self.shell_subprocess_hardening_freeze_decision_ref,
                "shell_subprocess_hardening_freeze_decision_ref",
            ),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class AutonomousToolExecutionContractDecision(_AutonomousToolExecutionContractModel):
    decision_ref: str
    request_ref: str
    contract_ref: str
    shell_subprocess_hardening_freeze_decision_ref: str
    emergency_stop_process_kill_safety_decision_ref: str
    command_ref: str
    sandbox_spec_ref: str
    approval_bundle_ref: str
    approval_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    tool_intent_ref: str
    tool_runtime_ref: str
    capability_ref: str
    autonomy_session_ref: str
    safe_execution_scope_ref: str
    safe_tool_ref: str
    safe_contract_refs: list[str]
    status: AutonomousToolExecutionContractStatus = (
        AutonomousToolExecutionContractStatus.contract_ready_for_review
    )
    autonomous_tool_execution_contract_defined: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    dry_run_plan_only: bool = True
    m90_hardening_freeze_revalidated: bool = True
    execution_authorized: bool = False
    tool_execution_authorized: bool = False
    autonomous_execution_authorized: bool = False
    session_start_authorized: bool = False
    background_worker_authorized: bool = False
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
    receipt_plan: AutonomousToolExecutionContractReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.contract_ref, "contract_ref"),
            (
                self.shell_subprocess_hardening_freeze_decision_ref,
                "shell_subprocess_hardening_freeze_decision_ref",
            ),
            (
                self.emergency_stop_process_kill_safety_decision_ref,
                "emergency_stop_process_kill_safety_decision_ref",
            ),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.tool_intent_ref, "tool_intent_ref"),
            (self.tool_runtime_ref, "tool_runtime_ref"),
            (self.capability_ref, "capability_ref"),
            (self.autonomy_session_ref, "autonomy_session_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.safe_tool_ref, "safe_tool_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_contract_refs:
            _validate_m61_ref(ref, "safe_contract_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M91_REASON_CODE_REQUIRED")
        return self


def build_autonomous_tool_execution_contract(
    request: AutonomousToolExecutionContractRequest,
    policy: AutonomousToolExecutionContractPolicy | None = None,
) -> AutonomousToolExecutionContractDecision:
    active_policy = validate_autonomous_tool_execution_contract_policy(
        policy or AutonomousToolExecutionContractPolicy()
    )
    validated_request = validate_autonomous_tool_execution_contract_request(request)
    decision = AutonomousToolExecutionContractDecision(
        decision_ref=f"autonomous-tool-execution-contract-decision:{_ref_suffix(validated_request.contract_ref)}",
        request_ref=validated_request.request_ref,
        contract_ref=validated_request.contract_ref,
        shell_subprocess_hardening_freeze_decision_ref=(
            validated_request.shell_subprocess_hardening_freeze_decision_ref
        ),
        emergency_stop_process_kill_safety_decision_ref=(
            validated_request.emergency_stop_process_kill_safety_decision_ref
        ),
        command_ref=validated_request.command_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        approval_ref=validated_request.approval_ref,
        actor_ref=validated_request.actor_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        tool_intent_ref=validated_request.tool_intent_ref,
        tool_runtime_ref=validated_request.tool_runtime_ref,
        capability_ref=validated_request.capability_ref,
        autonomy_session_ref=validated_request.autonomy_session_ref,
        safe_execution_scope_ref=validated_request.safe_execution_scope_ref,
        safe_tool_ref=validated_request.safe_tool_ref,
        safe_contract_refs=list(validated_request.safe_contract_refs),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        approval_refs_are_identifiers_only=active_policy.approval_refs_are_identifiers_only,
        reason_codes=[
            "M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_REVIEW_ONLY",
            "M91_EXACT_M90_HARDENING_BINDING_REQUIRED",
            "M91_NO_REAL_TOOL_EXECUTION",
            "M91_NO_AUTONOMOUS_SESSION_START",
            "M92_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M91 defines autonomous tool execution contract metadata for review only over "
            "an exact M90 shell/subprocess hardening freeze decision. It grants no "
            "execution, tool execution, autonomous session start, background worker, "
            "command, shell, subprocess, filesystem, network, browser, plugin, remote, "
            "model, memory, context, route, Control Center, dependency, or production authority."
        ),
        receipt_plan=AutonomousToolExecutionContractReceiptPlan(
            receipt_plan_ref=f"autonomous-tool-execution-contract-receipt-plan:{_ref_suffix(validated_request.contract_ref)}",
            contract_ref=validated_request.contract_ref,
            shell_subprocess_hardening_freeze_decision_ref=(
                validated_request.shell_subprocess_hardening_freeze_decision_ref
            ),
            tool_intent_ref=validated_request.tool_intent_ref,
            tool_runtime_ref=validated_request.tool_runtime_ref,
            capability_ref=validated_request.capability_ref,
            safe_execution_scope_ref=validated_request.safe_execution_scope_ref,
            safe_tool_ref=validated_request.safe_tool_ref,
        ),
    )
    return validate_autonomous_tool_execution_contract_decision(decision)


def validate_autonomous_tool_execution_contract_policy(
    policy: AutonomousToolExecutionContractPolicy,
) -> AutonomousToolExecutionContractPolicy:
    validated = AutonomousToolExecutionContractPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M91_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M91_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED") from exc
    return validated


def validate_autonomous_tool_execution_contract_request(
    request: AutonomousToolExecutionContractRequest,
) -> AutonomousToolExecutionContractRequest:
    payload = _model_payload(request)
    for field_name, reason in _M91_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = AutonomousToolExecutionContractRequest.model_validate(payload)
    for field_name, reason in _M91_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M91_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_approval_ref(validated.approval_ref)
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_safe_contract_refs(validated.safe_contract_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED") from exc
    from ultimate_ai_agent.core.sandbox.shell_subprocess_hardening_freeze import (
        validate_shell_subprocess_hardening_freeze_decision,
    )

    m90_decision = validate_shell_subprocess_hardening_freeze_decision(
        validated.shell_subprocess_hardening_freeze_decision
    )
    _validate_exact_m90_binding(validated, m90_decision)
    return validated


def validate_autonomous_tool_execution_contract_decision(
    decision: AutonomousToolExecutionContractDecision,
) -> AutonomousToolExecutionContractDecision:
    validated = AutonomousToolExecutionContractDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M91_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != AutonomousToolExecutionContractStatus.contract_ready_for_review:
        raise ValueError("M91_CONTRACT_READY_STATUS_REQUIRED")
    for field_name, reason in _M91_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if "M91_AUTONOMOUS_TOOL_EXECUTION_CONTRACT_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M91_REASON_CODE_REQUIRED")
    _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED") from exc
    return validated


def _validate_receipt_plan(
    receipt_plan: AutonomousToolExecutionContractReceiptPlan,
) -> AutonomousToolExecutionContractReceiptPlan:
    validated = AutonomousToolExecutionContractReceiptPlan.model_validate(_model_payload(receipt_plan))
    for field_name, reason in _M91_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M91_RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    return validated


def _validate_exact_m90_binding(
    request: AutonomousToolExecutionContractRequest,
    m90_decision: Any,
) -> None:
    for request_value, decision_value, reason in [
        (
            request.shell_subprocess_hardening_freeze_decision_ref,
            m90_decision.decision_ref,
            "M91_M90_HARDENING_BINDING_MISMATCH",
        ),
        (
            request.emergency_stop_process_kill_safety_decision_ref,
            m90_decision.emergency_stop_process_kill_safety_decision_ref,
            "M91_M90_HARDENING_BINDING_MISMATCH",
        ),
        (request.command_ref, m90_decision.command_ref, "M91_COMMAND_BINDING_MISMATCH"),
        (request.sandbox_spec_ref, m90_decision.sandbox_spec_ref, "M91_SANDBOX_BINDING_MISMATCH"),
        (
            request.approval_bundle_ref,
            m90_decision.approval_bundle_ref,
            "M91_APPROVAL_BUNDLE_BINDING_MISMATCH",
        ),
        (request.approval_ref, m90_decision.approval_ref, "M91_APPROVAL_REF_BINDING_MISMATCH"),
        (request.actor_ref, m90_decision.actor_ref, "M91_ACTOR_BINDING_MISMATCH"),
        (request.audit_ref, m90_decision.audit_ref, "M91_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, m90_decision.replay_ref, "M91_REPLAY_BINDING_MISMATCH"),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)


def _validate_receipt_binding(decision: AutonomousToolExecutionContractDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value in [
        (receipt.contract_ref, decision.contract_ref),
        (
            receipt.shell_subprocess_hardening_freeze_decision_ref,
            decision.shell_subprocess_hardening_freeze_decision_ref,
        ),
        (receipt.tool_intent_ref, decision.tool_intent_ref),
        (receipt.tool_runtime_ref, decision.tool_runtime_ref),
        (receipt.capability_ref, decision.capability_ref),
        (receipt.safe_execution_scope_ref, decision.safe_execution_scope_ref),
        (receipt.safe_tool_ref, decision.safe_tool_ref),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M91_RECEIPT_BINDING_MISMATCH")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M91_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M91_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M91_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M91_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M91_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M91_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_contract_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M91_SAFE_CONTRACT_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M91_SAFE_CONTRACT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "safe_contract_ref")


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


def _validate_m61_ref(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    if not M91_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name.upper()}_MUST_BE_SAFE_REF")


def _validate_safe_payload(value: Any) -> None:
    validate_safe_tool_payload(value, "payload")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


_M91_REQUIRED_TRUE = [
    ("autonomous_tool_execution_contract_requested", "M91_CONTRACT_REQUEST_REQUIRED"),
    ("contract_only", "M91_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M91_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M91_DETERMINISTIC_REQUIRED"),
    ("local_only", "M91_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M91_SAFE_REFS_ONLY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REFS_IDENTIFIER_ONLY_REQUIRED"),
    ("dry_run_plan_only", "M91_DRY_RUN_PLAN_ONLY_REQUIRED"),
]
_M91_POLICY_REQUIRED_TRUE = [
    ("autonomous_tool_execution_contract_enabled_for_review", "M91_REVIEW_ENABLED_REQUIRED"),
    ("exact_m90_hardening_binding_required", "M91_EXACT_M90_BINDING_REQUIRED"),
    ("m92_future_only", "M92_FUTURE_ONLY_REQUIRED"),
    *_M91_REQUIRED_TRUE[1:6],
    ("approval_refs_are_identifiers_only", "APPROVAL_REFS_IDENTIFIER_ONLY_REQUIRED"),
]
_M91_DECISION_REQUIRED_TRUE = [
    ("autonomous_tool_execution_contract_defined", "M91_CONTRACT_DEFINED_REQUIRED"),
    ("contract_only", "M91_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M91_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M91_DETERMINISTIC_REQUIRED"),
    ("local_only", "M91_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M91_SAFE_REFS_ONLY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REFS_IDENTIFIER_ONLY_REQUIRED"),
    ("dry_run_plan_only", "M91_DRY_RUN_PLAN_ONLY_REQUIRED"),
    ("m90_hardening_freeze_revalidated", "M91_M90_REVALIDATION_REQUIRED"),
]
_M91_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M91_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M91_SAFE_REFS_ONLY_REQUIRED"),
]
_M91_POLICY_DENIALS = [
    ("autonomous_tool_execution_enabled", "AUTONOMOUS_EXECUTION_DENIED"),
    ("autonomous_execution_enabled", "AUTONOMOUS_EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("session_start_enabled", "SESSION_START_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
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
_M91_REQUEST_DENIALS = [
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_requested", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_requested", "SESSION_START_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
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
    ("contains_raw_tool_payload", "M91_RAW_TOOL_PAYLOAD_DENIED"),
    ("contains_raw_provider_payload", "M91_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
    ("contains_secret", "SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED"),
]
_M91_DECISION_DENIALS = [
    ("execution_authorized", "EXECUTION_DENIED"),
    ("tool_execution_authorized", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_authorized", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_authorized", "SESSION_START_DENIED"),
    ("background_worker_authorized", "BACKGROUND_WORKER_DENIED"),
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
_M91_RECEIPT_DENIALS = [
    ("store_raw_tool_payload", "M91_RAW_TOOL_PAYLOAD_DENIED"),
    ("store_raw_provider_payload", "M91_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_AUTONOMOUS_TOOL_EXECUTION_CONTENT_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_performed", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_performed", "SESSION_START_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
]
