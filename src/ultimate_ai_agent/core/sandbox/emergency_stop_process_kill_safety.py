from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.mutating_command_proposal import (
    MutatingCommandProposalDecision,
    validate_mutating_command_proposal_decision,
)
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


EMERGENCY_STOP_PROCESS_KILL_SAFETY_DOCS = [
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_POLICY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_RECEIPT_PLAN.md",
    "docs/sandbox/EMERGENCY_STOP_PROCESS_KILL_SAFETY_NON_GOALS.md",
    "docs/sandbox/M89_TO_M90_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M89_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
    "milestone:M83",
    "milestone:M84",
    "milestone:M85",
    "milestone:M86",
    "milestone:M87",
    "milestone:M88",
)


class EmergencyStopProcessKillSafetyStatus(str, Enum):
    reviewed_for_safety = "reviewed_for_safety"


class _EmergencyStopProcessKillSafetyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class EmergencyStopProcessKillSafetyPolicy(_EmergencyStopProcessKillSafetyModel):
    policy_ref: str = "emergency-stop-process-kill-safety-policy:m89"
    emergency_stop_process_kill_safety_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_mutating_command_proposal_binding_required: bool = True
    safe_process_target_ref_required: bool = True
    emergency_stop_execution_enabled: bool = False
    process_kill_enabled: bool = False
    process_signal_enabled: bool = False
    command_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    process_spawn_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    tool_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    background_worker_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class EmergencyStopProcessKillSafetyRequest(_EmergencyStopProcessKillSafetyModel):
    request_ref: str
    emergency_stop_safety_ref: str
    process_kill_safety_ref: str
    mutating_command_proposal_decision_ref: str
    sandboxed_command_audit_replay_decision_ref: str
    shell_approval_gate_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    mutation_intent_ref: str
    mutation_scope_ref: str
    safe_target_process_ref: str
    safe_emergency_scope_ref: str
    safe_stop_summary: str
    safe_reason_refs: list[str]
    prior_milestone_refs: list[str]
    mutating_command_proposal_decision: MutatingCommandProposalDecision
    emergency_stop_process_kill_safety_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    emergency_stop_requested: bool = False
    process_kill_requested: bool = False
    process_signal_requested: bool = False
    command_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    shell_execution_requested: bool = False
    process_spawn_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    tool_execution_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    background_worker_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_pid: bool = False
    contains_raw_signal: bool = False
    contains_shell_string: bool = False
    contains_raw_command: bool = False
    contains_raw_output: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.emergency_stop_safety_ref, "emergency_stop_safety_ref"),
            (self.process_kill_safety_ref, "process_kill_safety_ref"),
            (self.mutating_command_proposal_decision_ref, "mutating_command_proposal_decision_ref"),
            (
                self.sandboxed_command_audit_replay_decision_ref,
                "sandboxed_command_audit_replay_decision_ref",
            ),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.mutation_intent_ref, "mutation_intent_ref"),
            (self.mutation_scope_ref, "mutation_scope_ref"),
            (self.safe_target_process_ref, "safe_target_process_ref"),
            (self.safe_emergency_scope_ref, "safe_emergency_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_reason_refs:
            _validate_m61_ref(ref, "safe_reason_ref")
        _validate_safe_payload(self.safe_stop_summary)
        return self


class EmergencyStopProcessKillSafetyReceiptPlan(_EmergencyStopProcessKillSafetyModel):
    receipt_plan_ref: str
    emergency_stop_safety_ref: str
    process_kill_safety_ref: str
    mutating_command_proposal_decision_ref: str
    command_ref: str
    sandbox_spec_ref: str
    safe_target_process_ref: str
    safe_emergency_scope_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_process_target_ref_only: bool = True
    store_raw_pid: bool = False
    store_raw_signal: bool = False
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_output: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    emergency_stop_performed: bool = False
    process_kill_performed: bool = False
    process_signal_performed: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    filesystem_mutation_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M89 emergency stop and process kill safety receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.emergency_stop_safety_ref, "emergency_stop_safety_ref"),
            (self.process_kill_safety_ref, "process_kill_safety_ref"),
            (self.mutating_command_proposal_decision_ref, "mutating_command_proposal_decision_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.safe_target_process_ref, "safe_target_process_ref"),
            (self.safe_emergency_scope_ref, "safe_emergency_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class EmergencyStopProcessKillSafetyDecision(_EmergencyStopProcessKillSafetyModel):
    decision_ref: str
    request_ref: str
    emergency_stop_safety_ref: str
    process_kill_safety_ref: str
    mutating_command_proposal_decision_ref: str
    sandboxed_command_audit_replay_decision_ref: str
    shell_approval_gate_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    mutation_intent_ref: str
    mutation_scope_ref: str
    safe_target_process_ref: str
    safe_emergency_scope_ref: str
    safe_reason_refs: list[str]
    status: EmergencyStopProcessKillSafetyStatus = (
        EmergencyStopProcessKillSafetyStatus.reviewed_for_safety
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    mutating_command_proposal_decision_revalidated: bool = True
    process_target_ref_bound: bool = True
    emergency_scope_ref_bound: bool = True
    emergency_stop_authorized: bool = False
    emergency_stop_performed: bool = False
    process_kill_authorized: bool = False
    process_kill_performed: bool = False
    process_signal_authorized: bool = False
    process_signal_performed: bool = False
    command_execution_authorized: bool = False
    shell_execution_authorized: bool = False
    subprocess_execution_authorized: bool = False
    process_spawn_authorized: bool = False
    filesystem_mutation_authorized: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    tool_execution_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    background_worker_started: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    receipt_plan: EmergencyStopProcessKillSafetyReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.emergency_stop_safety_ref, "emergency_stop_safety_ref"),
            (self.process_kill_safety_ref, "process_kill_safety_ref"),
            (self.mutating_command_proposal_decision_ref, "mutating_command_proposal_decision_ref"),
            (
                self.sandboxed_command_audit_replay_decision_ref,
                "sandboxed_command_audit_replay_decision_ref",
            ),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.mutation_intent_ref, "mutation_intent_ref"),
            (self.mutation_scope_ref, "mutation_scope_ref"),
            (self.safe_target_process_ref, "safe_target_process_ref"),
            (self.safe_emergency_scope_ref, "safe_emergency_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_reason_refs:
            _validate_m61_ref(ref, "safe_reason_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M89_REASON_CODE_REQUIRED")
        return self


def build_emergency_stop_process_kill_safety(
    request: EmergencyStopProcessKillSafetyRequest,
    policy: EmergencyStopProcessKillSafetyPolicy | None = None,
) -> EmergencyStopProcessKillSafetyDecision:
    active_policy = validate_emergency_stop_process_kill_safety_policy(
        policy or EmergencyStopProcessKillSafetyPolicy()
    )
    validated_request = validate_emergency_stop_process_kill_safety_request(request)
    decision = EmergencyStopProcessKillSafetyDecision(
        decision_ref=f"emergency-stop-process-kill-safety-decision:{_ref_suffix(validated_request.emergency_stop_safety_ref)}",
        request_ref=validated_request.request_ref,
        emergency_stop_safety_ref=validated_request.emergency_stop_safety_ref,
        process_kill_safety_ref=validated_request.process_kill_safety_ref,
        mutating_command_proposal_decision_ref=validated_request.mutating_command_proposal_decision_ref,
        sandboxed_command_audit_replay_decision_ref=(
            validated_request.sandboxed_command_audit_replay_decision_ref
        ),
        shell_approval_gate_decision_ref=validated_request.shell_approval_gate_decision_ref,
        approval_bundle_ref=validated_request.approval_bundle_ref,
        approval_ref=validated_request.approval_ref,
        command_ref=validated_request.command_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        mutation_intent_ref=validated_request.mutation_intent_ref,
        mutation_scope_ref=validated_request.mutation_scope_ref,
        safe_target_process_ref=validated_request.safe_target_process_ref,
        safe_emergency_scope_ref=validated_request.safe_emergency_scope_ref,
        safe_reason_refs=list(validated_request.safe_reason_refs),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        reason_codes=[
            "M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_REVIEW_ONLY",
            "M89_EXACT_M88_MUTATING_PROPOSAL_BINDING_REQUIRED",
            "M89_SAFE_PROCESS_TARGET_REF_REQUIRED",
            "M89_NO_PROCESS_KILL_EXECUTION",
            "M90_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M89 reviews emergency stop and process kill safety as safe metadata over "
            "an exact M88 mutating command proposal decision. It grants no emergency "
            "stop, process kill, process signal, command, shell, subprocess, process "
            "spawn, filesystem, network, tool, browser, plugin, remote, model, memory, "
            "context, route, Control Center, dependency, or production authority."
        ),
        receipt_plan=EmergencyStopProcessKillSafetyReceiptPlan(
            receipt_plan_ref=f"emergency-stop-process-kill-safety-receipt-plan:{_ref_suffix(validated_request.emergency_stop_safety_ref)}",
            emergency_stop_safety_ref=validated_request.emergency_stop_safety_ref,
            process_kill_safety_ref=validated_request.process_kill_safety_ref,
            mutating_command_proposal_decision_ref=validated_request.mutating_command_proposal_decision_ref,
            command_ref=validated_request.command_ref,
            sandbox_spec_ref=validated_request.sandbox_spec_ref,
            safe_target_process_ref=validated_request.safe_target_process_ref,
            safe_emergency_scope_ref=validated_request.safe_emergency_scope_ref,
        ),
    )
    return validate_emergency_stop_process_kill_safety_decision(decision)


def validate_emergency_stop_process_kill_safety_policy(
    policy: EmergencyStopProcessKillSafetyPolicy,
) -> EmergencyStopProcessKillSafetyPolicy:
    validated = EmergencyStopProcessKillSafetyPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M89_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M89_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED") from exc
    return validated


def validate_emergency_stop_process_kill_safety_request(
    request: EmergencyStopProcessKillSafetyRequest,
) -> EmergencyStopProcessKillSafetyRequest:
    payload = _model_payload(request)
    for field_name, reason in _M89_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = EmergencyStopProcessKillSafetyRequest.model_validate(payload)
    for field_name, reason in _M89_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M89_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.emergency_stop_process_kill_safety_requested:
        raise ValueError("M89_EMERGENCY_STOP_PROCESS_KILL_SAFETY_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M89_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_approval_ref(validated.approval_ref)
    _validate_safe_reason_refs(validated.safe_reason_refs)
    _validate_exact_m88_binding(validated)
    try:
        _validate_safe_payload(validated.safe_stop_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED") from exc
    return validated


def validate_emergency_stop_process_kill_safety_decision(
    decision: EmergencyStopProcessKillSafetyDecision,
) -> EmergencyStopProcessKillSafetyDecision:
    validated = EmergencyStopProcessKillSafetyDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M89_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M89_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != EmergencyStopProcessKillSafetyStatus.reviewed_for_safety:
        raise ValueError("M89_EMERGENCY_STOP_PROCESS_KILL_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M89_SIDE_EFFECTS_DENIED")
    _validate_safe_reason_refs(validated.safe_reason_refs)
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M89_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_safe_refs_only:
        raise ValueError("M89_RECEIPT_REFS_ONLY_REQUIRED")
    if not validated.receipt_plan.store_process_target_ref_only:
        raise ValueError("M89_RECEIPT_PROCESS_TARGET_REF_ONLY_REQUIRED")
    for field_name, reason in _M89_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M89_SIDE_EFFECTS_DENIED")
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m88_binding(request: EmergencyStopProcessKillSafetyRequest) -> None:
    proposal = validate_mutating_command_proposal_decision(
        request.mutating_command_proposal_decision
    )
    if request.mutating_command_proposal_decision_ref != proposal.decision_ref:
        raise ValueError("M89_M88_MUTATING_PROPOSAL_BINDING_MISMATCH")
    for request_value, proposal_value, reason in [
        (
            request.sandboxed_command_audit_replay_decision_ref,
            proposal.sandboxed_command_audit_replay_decision_ref,
            "M89_M87_AUDIT_REPLAY_BINDING_MISMATCH",
        ),
        (
            request.shell_approval_gate_decision_ref,
            proposal.shell_approval_gate_decision_ref,
            "M89_M86_GATE_DECISION_BINDING_MISMATCH",
        ),
        (request.approval_bundle_ref, proposal.approval_bundle_ref, "M89_APPROVAL_BUNDLE_BINDING_MISMATCH"),
        (request.approval_ref, proposal.approval_ref, "M89_APPROVAL_REF_BINDING_MISMATCH"),
        (request.command_ref, proposal.command_ref, "M89_COMMAND_BINDING_MISMATCH"),
        (request.sandbox_spec_ref, proposal.sandbox_spec_ref, "M89_SANDBOX_SPEC_BINDING_MISMATCH"),
        (request.actor_ref, proposal.actor_ref, "M89_ACTOR_BINDING_MISMATCH"),
        (request.audit_ref, proposal.audit_ref, "M89_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, proposal.replay_ref, "M89_REPLAY_BINDING_MISMATCH"),
        (request.mutation_intent_ref, proposal.mutation_intent_ref, "M89_MUTATION_SCOPE_BINDING_MISMATCH"),
        (request.mutation_scope_ref, proposal.mutation_scope_ref, "M89_MUTATION_SCOPE_BINDING_MISMATCH"),
    ]:
        if request_value != proposal_value:
            raise ValueError(reason)
    if not request.safe_target_process_ref.endswith("safe-ref"):
        raise ValueError("M89_PROCESS_TARGET_BINDING_MISMATCH")
    if not request.safe_emergency_scope_ref.endswith("safe-ref"):
        raise ValueError("M89_EMERGENCY_SCOPE_BINDING_MISMATCH")


def _validate_receipt_binding(decision: EmergencyStopProcessKillSafetyDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value, reason in [
        (receipt.emergency_stop_safety_ref, decision.emergency_stop_safety_ref, "M89_RECEIPT_BINDING_MISMATCH"),
        (receipt.process_kill_safety_ref, decision.process_kill_safety_ref, "M89_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.mutating_command_proposal_decision_ref,
            decision.mutating_command_proposal_decision_ref,
            "M89_RECEIPT_BINDING_MISMATCH",
        ),
        (receipt.command_ref, decision.command_ref, "M89_RECEIPT_BINDING_MISMATCH"),
        (receipt.sandbox_spec_ref, decision.sandbox_spec_ref, "M89_RECEIPT_BINDING_MISMATCH"),
        (receipt.safe_target_process_ref, decision.safe_target_process_ref, "M89_RECEIPT_BINDING_MISMATCH"),
        (receipt.safe_emergency_scope_ref, decision.safe_emergency_scope_ref, "M89_RECEIPT_BINDING_MISMATCH"),
    ]:
        if receipt_value != decision_value:
            raise ValueError(reason)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M89_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M89_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M89_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M89_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M89_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M89_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_reason_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M89_SAFE_REASON_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M89_SAFE_REASON_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "safe_reason_ref")


def _validate_approval_ref(ref: str) -> None:
    if "approval_test_" in ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    _validate_m61_ref(ref, "approval_ref")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


_M89_REQUIRED_TRUE = [
    ("contract_only", "M89_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M89_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M89_DETERMINISTIC_REQUIRED"),
    ("local_only", "M89_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M89_SAFE_REFS_ONLY_REQUIRED"),
]
_M89_POLICY_REQUIRED_TRUE = [
    ("emergency_stop_process_kill_safety_enabled_for_review", "M89_REVIEW_ENABLED_REQUIRED"),
    ("exact_mutating_command_proposal_binding_required", "M89_EXACT_M88_BINDING_REQUIRED"),
    ("safe_process_target_ref_required", "M89_SAFE_PROCESS_TARGET_REF_REQUIRED"),
    *_M89_REQUIRED_TRUE,
]
_M89_DECISION_REQUIRED_TRUE = [
    *_M89_REQUIRED_TRUE,
    ("mutating_command_proposal_decision_revalidated", "M89_M88_DECISION_REVALIDATION_REQUIRED"),
    ("process_target_ref_bound", "M89_PROCESS_TARGET_BOUND_REQUIRED"),
    ("emergency_scope_ref_bound", "M89_EMERGENCY_SCOPE_BOUND_REQUIRED"),
]
_M89_POLICY_DENIALS = [
    ("emergency_stop_execution_enabled", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_enabled", "M89_PROCESS_KILL_DENIED"),
    ("process_signal_enabled", "M89_PROCESS_SIGNAL_DENIED"),
    ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
_M89_REQUEST_DENIALS = [
    ("emergency_stop_requested", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_requested", "M89_PROCESS_KILL_DENIED"),
    ("process_signal_requested", "M89_PROCESS_SIGNAL_DENIED"),
    ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("model_call_requested", "MODEL_CALL_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("contains_pid", "M89_RAW_PID_DENIED"),
    ("contains_raw_signal", "M89_RAW_SIGNAL_DENIED"),
    ("contains_shell_string", "M89_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M89_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M89_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "M89_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M89_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED"),
]
_M89_DECISION_DENIALS = [
    ("emergency_stop_authorized", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("emergency_stop_performed", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_authorized", "M89_PROCESS_KILL_DENIED"),
    ("process_kill_performed", "M89_PROCESS_KILL_DENIED"),
    ("process_signal_authorized", "M89_PROCESS_SIGNAL_DENIED"),
    ("process_signal_performed", "M89_PROCESS_SIGNAL_DENIED"),
    ("command_execution_authorized", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_authorized", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_authorized", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_authorized", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_authorized", "FILESYSTEM_MUTATION_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
_M89_RECEIPT_DENIALS = [
    ("store_raw_pid", "M89_RAW_PID_DENIED"),
    ("store_raw_signal", "M89_RAW_SIGNAL_DENIED"),
    ("store_raw_command", "M89_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M89_SHELL_STRING_DENIED"),
    ("store_raw_output", "M89_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "M89_RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_EMERGENCY_STOP_CONTENT_DENIED"),
    ("emergency_stop_performed", "M89_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_performed", "M89_PROCESS_KILL_DENIED"),
    ("process_signal_performed", "M89_PROCESS_SIGNAL_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
