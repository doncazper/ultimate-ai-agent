from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.emergency_stop_process_kill_safety import (
    EmergencyStopProcessKillSafetyDecision,
    validate_emergency_stop_process_kill_safety_decision,
)
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


SHELL_SUBPROCESS_HARDENING_FREEZE_DOCS = [
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_NON_GOALS.md",
    "docs/sandbox/M90_TO_M91_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M90_PRIOR_MILESTONE_REFS = (
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
    "milestone:M89",
)


class ShellSubprocessHardeningFreezeStatus(str, Enum):
    frozen_for_review = "frozen_for_review"


class _ShellSubprocessHardeningFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ShellSubprocessHardeningFreezePolicy(_ShellSubprocessHardeningFreezeModel):
    policy_ref: str = "shell-subprocess-hardening-freeze-policy:m90"
    shell_subprocess_hardening_freeze_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m89_safety_binding_required: bool = True
    shell_boundary_freeze_required: bool = True
    subprocess_boundary_freeze_required: bool = True
    process_spawn_boundary_freeze_required: bool = True
    emergency_boundary_freeze_required: bool = True
    command_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    process_spawn_enabled: bool = False
    emergency_stop_execution_enabled: bool = False
    process_kill_enabled: bool = False
    process_signal_enabled: bool = False
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


class ShellSubprocessHardeningFreezeRequest(_ShellSubprocessHardeningFreezeModel):
    request_ref: str
    hardening_freeze_ref: str
    emergency_stop_process_kill_safety_decision_ref: str
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
    safe_freeze_summary: str
    safe_hardening_refs: list[str]
    prior_milestone_refs: list[str]
    emergency_stop_process_kill_safety_decision: EmergencyStopProcessKillSafetyDecision
    shell_subprocess_hardening_freeze_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    command_execution_requested: bool = False
    shell_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    process_spawn_requested: bool = False
    emergency_stop_requested: bool = False
    process_kill_requested: bool = False
    process_signal_requested: bool = False
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
    contains_shell_string: bool = False
    contains_raw_command: bool = False
    contains_raw_output: bool = False
    contains_pid: bool = False
    contains_raw_signal: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.hardening_freeze_ref, "hardening_freeze_ref"),
            (
                self.emergency_stop_process_kill_safety_decision_ref,
                "emergency_stop_process_kill_safety_decision_ref",
            ),
            (
                self.mutating_command_proposal_decision_ref,
                "mutating_command_proposal_decision_ref",
            ),
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
        for ref in self.safe_hardening_refs:
            _validate_m61_ref(ref, "safe_hardening_ref")
        _validate_safe_payload(self.safe_freeze_summary)
        return self


class ShellSubprocessHardeningFreezeReceiptPlan(_ShellSubprocessHardeningFreezeModel):
    receipt_plan_ref: str
    hardening_freeze_ref: str
    emergency_stop_process_kill_safety_decision_ref: str
    command_ref: str
    sandbox_spec_ref: str
    safe_target_process_ref: str
    safe_emergency_scope_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_output: bool = False
    store_raw_pid: bool = False
    store_raw_signal: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    command_execution_performed: bool = False
    shell_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    process_spawn_performed: bool = False
    emergency_stop_performed: bool = False
    process_kill_performed: bool = False
    process_signal_performed: bool = False
    filesystem_mutation_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M90 shell and subprocess hardening freeze receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.hardening_freeze_ref, "hardening_freeze_ref"),
            (
                self.emergency_stop_process_kill_safety_decision_ref,
                "emergency_stop_process_kill_safety_decision_ref",
            ),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.safe_target_process_ref, "safe_target_process_ref"),
            (self.safe_emergency_scope_ref, "safe_emergency_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class ShellSubprocessHardeningFreezeDecision(_ShellSubprocessHardeningFreezeModel):
    decision_ref: str
    request_ref: str
    hardening_freeze_ref: str
    emergency_stop_process_kill_safety_decision_ref: str
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
    safe_hardening_refs: list[str]
    status: ShellSubprocessHardeningFreezeStatus = (
        ShellSubprocessHardeningFreezeStatus.frozen_for_review
    )
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    m89_safety_decision_revalidated: bool = True
    shell_boundary_frozen: bool = True
    subprocess_boundary_frozen: bool = True
    process_spawn_boundary_frozen: bool = True
    emergency_stop_boundary_frozen: bool = True
    command_execution_authorized: bool = False
    shell_execution_authorized: bool = False
    subprocess_execution_authorized: bool = False
    process_spawn_authorized: bool = False
    emergency_stop_authorized: bool = False
    process_kill_authorized: bool = False
    process_signal_authorized: bool = False
    filesystem_mutation_authorized: bool = False
    command_execution_performed: bool = False
    shell_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    process_spawn_performed: bool = False
    emergency_stop_performed: bool = False
    process_kill_performed: bool = False
    process_signal_performed: bool = False
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
    receipt_plan: ShellSubprocessHardeningFreezeReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.hardening_freeze_ref, "hardening_freeze_ref"),
            (
                self.emergency_stop_process_kill_safety_decision_ref,
                "emergency_stop_process_kill_safety_decision_ref",
            ),
            (
                self.mutating_command_proposal_decision_ref,
                "mutating_command_proposal_decision_ref",
            ),
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
        for ref in self.safe_hardening_refs:
            _validate_m61_ref(ref, "safe_hardening_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M90_REASON_CODE_REQUIRED")
        return self


def build_shell_subprocess_hardening_freeze(
    request: ShellSubprocessHardeningFreezeRequest,
    policy: ShellSubprocessHardeningFreezePolicy | None = None,
) -> ShellSubprocessHardeningFreezeDecision:
    active_policy = validate_shell_subprocess_hardening_freeze_policy(
        policy or ShellSubprocessHardeningFreezePolicy()
    )
    validated_request = validate_shell_subprocess_hardening_freeze_request(request)
    decision = ShellSubprocessHardeningFreezeDecision(
        decision_ref=f"shell-subprocess-hardening-freeze-decision:{_ref_suffix(validated_request.hardening_freeze_ref)}",
        request_ref=validated_request.request_ref,
        hardening_freeze_ref=validated_request.hardening_freeze_ref,
        emergency_stop_process_kill_safety_decision_ref=(
            validated_request.emergency_stop_process_kill_safety_decision_ref
        ),
        mutating_command_proposal_decision_ref=(
            validated_request.mutating_command_proposal_decision_ref
        ),
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
        safe_hardening_refs=list(validated_request.safe_hardening_refs),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        freeze_only=active_policy.freeze_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        reason_codes=[
            "M90_SHELL_SUBPROCESS_HARDENING_FREEZE_REVIEW_ONLY",
            "M90_EXACT_M89_SAFETY_BINDING_REQUIRED",
            "M90_NO_SHELL_SUBPROCESS_EXECUTION",
            "M90_NO_PROCESS_OR_EMERGENCY_EXECUTION",
            "M91_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M90 freezes shell, subprocess, command, process spawn, emergency stop, "
            "process kill, and process signal boundaries as review-only metadata over "
            "an exact M89 safety decision. It grants no command, shell, subprocess, "
            "process, emergency, filesystem, network, tool, browser, plugin, remote, "
            "model, memory, context, route, Control Center, dependency, or production "
            "authority."
        ),
        receipt_plan=ShellSubprocessHardeningFreezeReceiptPlan(
            receipt_plan_ref=f"shell-subprocess-hardening-freeze-receipt-plan:{_ref_suffix(validated_request.hardening_freeze_ref)}",
            hardening_freeze_ref=validated_request.hardening_freeze_ref,
            emergency_stop_process_kill_safety_decision_ref=(
                validated_request.emergency_stop_process_kill_safety_decision_ref
            ),
            command_ref=validated_request.command_ref,
            sandbox_spec_ref=validated_request.sandbox_spec_ref,
            safe_target_process_ref=validated_request.safe_target_process_ref,
            safe_emergency_scope_ref=validated_request.safe_emergency_scope_ref,
        ),
    )
    return validate_shell_subprocess_hardening_freeze_decision(decision)


def validate_shell_subprocess_hardening_freeze_policy(
    policy: ShellSubprocessHardeningFreezePolicy,
) -> ShellSubprocessHardeningFreezePolicy:
    validated = ShellSubprocessHardeningFreezePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M90_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M90_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_shell_subprocess_hardening_freeze_request(
    request: ShellSubprocessHardeningFreezeRequest,
) -> ShellSubprocessHardeningFreezeRequest:
    payload = _model_payload(request)
    for field_name, reason in _M90_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ShellSubprocessHardeningFreezeRequest.model_validate(payload)
    for field_name, reason in _M90_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M90_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.shell_subprocess_hardening_freeze_requested:
        raise ValueError("M90_SHELL_SUBPROCESS_HARDENING_FREEZE_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M90_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_approval_ref(validated.approval_ref)
    _validate_safe_hardening_refs(validated.safe_hardening_refs)
    _validate_exact_m89_binding(validated)
    try:
        _validate_safe_payload(validated.safe_freeze_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_shell_subprocess_hardening_freeze_decision(
    decision: ShellSubprocessHardeningFreezeDecision,
) -> ShellSubprocessHardeningFreezeDecision:
    validated = ShellSubprocessHardeningFreezeDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M90_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M90_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ShellSubprocessHardeningFreezeStatus.frozen_for_review:
        raise ValueError("M90_SHELL_SUBPROCESS_HARDENING_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M90_SIDE_EFFECTS_DENIED")
    _validate_safe_hardening_refs(validated.safe_hardening_refs)
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M90_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_safe_refs_only:
        raise ValueError("M90_RECEIPT_REFS_ONLY_REQUIRED")
    for field_name, reason in _M90_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M90_SIDE_EFFECTS_DENIED")
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m89_binding(request: ShellSubprocessHardeningFreezeRequest) -> None:
    m89_decision = validate_emergency_stop_process_kill_safety_decision(
        request.emergency_stop_process_kill_safety_decision
    )
    if request.emergency_stop_process_kill_safety_decision_ref != m89_decision.decision_ref:
        raise ValueError("M90_M89_SAFETY_BINDING_MISMATCH")
    for request_value, decision_value, reason in [
        (
            request.mutating_command_proposal_decision_ref,
            m89_decision.mutating_command_proposal_decision_ref,
            "M90_M88_MUTATING_PROPOSAL_BINDING_MISMATCH",
        ),
        (
            request.sandboxed_command_audit_replay_decision_ref,
            m89_decision.sandboxed_command_audit_replay_decision_ref,
            "M90_M87_AUDIT_REPLAY_BINDING_MISMATCH",
        ),
        (
            request.shell_approval_gate_decision_ref,
            m89_decision.shell_approval_gate_decision_ref,
            "M90_M86_GATE_DECISION_BINDING_MISMATCH",
        ),
        (request.approval_bundle_ref, m89_decision.approval_bundle_ref, "M90_APPROVAL_BUNDLE_BINDING_MISMATCH"),
        (request.approval_ref, m89_decision.approval_ref, "M90_APPROVAL_REF_BINDING_MISMATCH"),
        (request.command_ref, m89_decision.command_ref, "M90_COMMAND_BINDING_MISMATCH"),
        (request.sandbox_spec_ref, m89_decision.sandbox_spec_ref, "M90_SANDBOX_SPEC_BINDING_MISMATCH"),
        (request.actor_ref, m89_decision.actor_ref, "M90_ACTOR_BINDING_MISMATCH"),
        (request.audit_ref, m89_decision.audit_ref, "M90_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, m89_decision.replay_ref, "M90_REPLAY_BINDING_MISMATCH"),
        (request.mutation_intent_ref, m89_decision.mutation_intent_ref, "M90_MUTATION_SCOPE_BINDING_MISMATCH"),
        (request.mutation_scope_ref, m89_decision.mutation_scope_ref, "M90_MUTATION_SCOPE_BINDING_MISMATCH"),
        (
            request.safe_target_process_ref,
            m89_decision.safe_target_process_ref,
            "M90_PROCESS_TARGET_BINDING_MISMATCH",
        ),
        (
            request.safe_emergency_scope_ref,
            m89_decision.safe_emergency_scope_ref,
            "M90_EMERGENCY_SCOPE_BINDING_MISMATCH",
        ),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)


def _validate_receipt_binding(decision: ShellSubprocessHardeningFreezeDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value, reason in [
        (receipt.hardening_freeze_ref, decision.hardening_freeze_ref, "M90_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.emergency_stop_process_kill_safety_decision_ref,
            decision.emergency_stop_process_kill_safety_decision_ref,
            "M90_RECEIPT_BINDING_MISMATCH",
        ),
        (receipt.command_ref, decision.command_ref, "M90_RECEIPT_BINDING_MISMATCH"),
        (receipt.sandbox_spec_ref, decision.sandbox_spec_ref, "M90_RECEIPT_BINDING_MISMATCH"),
        (receipt.safe_target_process_ref, decision.safe_target_process_ref, "M90_RECEIPT_BINDING_MISMATCH"),
        (receipt.safe_emergency_scope_ref, decision.safe_emergency_scope_ref, "M90_RECEIPT_BINDING_MISMATCH"),
    ]:
        if receipt_value != decision_value:
            raise ValueError(reason)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M90_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M90_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M90_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M90_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M90_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M90_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_hardening_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M90_SAFE_HARDENING_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M90_SAFE_HARDENING_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "safe_hardening_ref")


def _validate_approval_ref(ref: str) -> None:
    if "approval_test_" in ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    _validate_m61_ref(ref, "approval_ref")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


_M90_REQUIRED_TRUE = [
    ("contract_only", "M90_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M90_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M90_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M90_DETERMINISTIC_REQUIRED"),
    ("local_only", "M90_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M90_SAFE_REFS_ONLY_REQUIRED"),
]
_M90_POLICY_REQUIRED_TRUE = [
    ("shell_subprocess_hardening_freeze_enabled_for_review", "M90_REVIEW_ENABLED_REQUIRED"),
    ("exact_m89_safety_binding_required", "M90_EXACT_M89_BINDING_REQUIRED"),
    ("shell_boundary_freeze_required", "M90_SHELL_BOUNDARY_FREEZE_REQUIRED"),
    ("subprocess_boundary_freeze_required", "M90_SUBPROCESS_BOUNDARY_FREEZE_REQUIRED"),
    ("process_spawn_boundary_freeze_required", "M90_PROCESS_SPAWN_BOUNDARY_FREEZE_REQUIRED"),
    ("emergency_boundary_freeze_required", "M90_EMERGENCY_BOUNDARY_FREEZE_REQUIRED"),
    *_M90_REQUIRED_TRUE,
]
_M90_DECISION_REQUIRED_TRUE = [
    *_M90_REQUIRED_TRUE,
    ("m89_safety_decision_revalidated", "M90_M89_DECISION_REVALIDATION_REQUIRED"),
    ("shell_boundary_frozen", "M90_SHELL_BOUNDARY_FREEZE_REQUIRED"),
    ("subprocess_boundary_frozen", "M90_SUBPROCESS_BOUNDARY_FREEZE_REQUIRED"),
    ("process_spawn_boundary_frozen", "M90_PROCESS_SPAWN_BOUNDARY_FREEZE_REQUIRED"),
    ("emergency_stop_boundary_frozen", "M90_EMERGENCY_BOUNDARY_FREEZE_REQUIRED"),
]
_COMMON_POLICY_DENIALS = [
    ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
    ("emergency_stop_execution_enabled", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_enabled", "M90_PROCESS_KILL_DENIED"),
    ("process_signal_enabled", "M90_PROCESS_SIGNAL_DENIED"),
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
_M90_POLICY_DENIALS = _COMMON_POLICY_DENIALS
_M90_REQUEST_DENIALS = [
    ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
    ("emergency_stop_requested", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_requested", "M90_PROCESS_KILL_DENIED"),
    ("process_signal_requested", "M90_PROCESS_SIGNAL_DENIED"),
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
    ("contains_shell_string", "M90_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M90_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M90_RAW_OUTPUT_DENIED"),
    ("contains_pid", "M90_RAW_PID_DENIED"),
    ("contains_raw_signal", "M90_RAW_SIGNAL_DENIED"),
    ("contains_raw_prompt", "M90_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M90_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED"),
]
_M90_DECISION_DENIALS = [
    ("command_execution_authorized", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_authorized", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_authorized", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_authorized", "PROCESS_SPAWN_DENIED"),
    ("emergency_stop_authorized", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_authorized", "M90_PROCESS_KILL_DENIED"),
    ("process_signal_authorized", "M90_PROCESS_SIGNAL_DENIED"),
    ("filesystem_mutation_authorized", "FILESYSTEM_MUTATION_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("emergency_stop_performed", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_performed", "M90_PROCESS_KILL_DENIED"),
    ("process_signal_performed", "M90_PROCESS_SIGNAL_DENIED"),
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
_M90_RECEIPT_DENIALS = [
    ("store_raw_command", "M90_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M90_SHELL_STRING_DENIED"),
    ("store_raw_output", "M90_RAW_OUTPUT_DENIED"),
    ("store_raw_pid", "M90_RAW_PID_DENIED"),
    ("store_raw_signal", "M90_RAW_SIGNAL_DENIED"),
    ("store_raw_prompt", "M90_RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_SHELL_SUBPROCESS_FREEZE_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("emergency_stop_performed", "M90_EMERGENCY_STOP_EXECUTION_DENIED"),
    ("process_kill_performed", "M90_PROCESS_KILL_DENIED"),
    ("process_signal_performed", "M90_PROCESS_SIGNAL_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
