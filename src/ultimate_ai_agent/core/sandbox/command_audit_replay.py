from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload
from ultimate_ai_agent.core.sandbox.shell_approval_gate import (
    ShellApprovalGateDecision,
    validate_shell_approval_gate_decision,
)


SANDBOXED_COMMAND_AUDIT_REPLAY_DOCS = [
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_POLICY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_RECEIPT_PLAN.md",
    "docs/sandbox/SANDBOXED_COMMAND_AUDIT_REPLAY_NON_GOALS.md",
    "docs/sandbox/M87_TO_M88_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M87_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
    "milestone:M83",
    "milestone:M84",
    "milestone:M85",
    "milestone:M86",
)


class SandboxedCommandAuditReplayStatus(str, Enum):
    ready_for_review = "ready_for_review"


class _SandboxedCommandAuditReplayModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class SandboxedCommandAuditReplayStep(_SandboxedCommandAuditReplayModel):
    step_ref: str
    event_ref: str
    source_decision_ref: str
    safe_summary: str
    reason_codes: list[str]
    replay_view_only: bool = True
    safe_refs_only: bool = True
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    replay_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    tool_execution_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    contains_shell_string: bool = False
    contains_raw_command: bool = False
    contains_raw_output: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.step_ref, "step_ref"),
            (self.event_ref, "event_ref"),
            (self.source_decision_ref, "source_decision_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M87_REASON_CODE_REQUIRED")
        return self


class SandboxedCommandAuditReplayPolicy(_SandboxedCommandAuditReplayModel):
    policy_ref: str = "sandboxed-command-audit-replay-policy:m87"
    audit_replay_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    replay_view_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_shell_approval_gate_binding_required: bool = True
    exact_replay_step_binding_required: bool = True
    replay_runner_enabled: bool = False
    replay_execution_enabled: bool = False
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
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class SandboxedCommandAuditReplayRequest(_SandboxedCommandAuditReplayModel):
    request_ref: str
    replay_view_ref: str
    shell_approval_gate_decision_ref: str
    read_only_command_allowlist_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    allowlist_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    replay_step_refs: list[str]
    prior_milestone_refs: list[str]
    shell_approval_gate_decision: ShellApprovalGateDecision
    replay_steps: list[SandboxedCommandAuditReplayStep]
    safe_purpose: str
    audit_replay_review_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    replay_view_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    replay_runner_requested: bool = False
    replay_execution_requested: bool = False
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
    contains_shell_string: bool = False
    contains_raw_command: bool = False
    contains_raw_output: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.replay_view_ref, "replay_view_ref"),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (
                self.read_only_command_allowlist_decision_ref,
                "read_only_command_allowlist_decision_ref",
            ),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.replay_step_refs:
            _validate_m61_ref(ref, "replay_step_ref")
        _validate_safe_payload(self.safe_purpose)
        return self


class SandboxedCommandAuditReplayReceiptPlan(_SandboxedCommandAuditReplayModel):
    receipt_plan_ref: str
    replay_view_ref: str
    shell_approval_gate_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    command_ref: str
    sandbox_spec_ref: str
    audit_ref: str
    replay_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_replay_step_refs_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_output: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    replay_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M87 sandboxed command audit replay receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.replay_view_ref, "replay_view_ref"),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class SandboxedCommandAuditReplayDecision(_SandboxedCommandAuditReplayModel):
    decision_ref: str
    replay_view_ref: str
    request_ref: str
    shell_approval_gate_decision_ref: str
    read_only_command_allowlist_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    allowlist_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    replay_step_refs: list[str]
    status: SandboxedCommandAuditReplayStatus = (
        SandboxedCommandAuditReplayStatus.ready_for_review
    )
    contract_only: bool = True
    review_only: bool = True
    replay_view_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    shell_approval_gate_decision_revalidated: bool = True
    replay_steps_bound: bool = True
    replay_runner_started: bool = False
    replay_execution_performed: bool = False
    command_execution_authorized: bool = False
    shell_execution_authorized: bool = False
    subprocess_execution_authorized: bool = False
    process_spawn_authorized: bool = False
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
    receipt_plan: SandboxedCommandAuditReplayReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.replay_view_ref, "replay_view_ref"),
            (self.request_ref, "request_ref"),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (
                self.read_only_command_allowlist_decision_ref,
                "read_only_command_allowlist_decision_ref",
            ),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.replay_step_refs:
            _validate_m61_ref(ref, "replay_step_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M87_REASON_CODE_REQUIRED")
        return self


def build_sandboxed_command_audit_replay(
    request: SandboxedCommandAuditReplayRequest,
    policy: SandboxedCommandAuditReplayPolicy | None = None,
) -> SandboxedCommandAuditReplayDecision:
    active_policy = validate_sandboxed_command_audit_replay_policy(
        policy or SandboxedCommandAuditReplayPolicy()
    )
    validated_request = validate_sandboxed_command_audit_replay_request(request)
    decision = SandboxedCommandAuditReplayDecision(
        decision_ref=f"sandboxed-command-audit-replay-decision:{_ref_suffix(validated_request.replay_view_ref)}",
        replay_view_ref=validated_request.replay_view_ref,
        request_ref=validated_request.request_ref,
        shell_approval_gate_decision_ref=validated_request.shell_approval_gate_decision_ref,
        read_only_command_allowlist_decision_ref=(
            validated_request.read_only_command_allowlist_decision_ref
        ),
        approval_bundle_ref=validated_request.approval_bundle_ref,
        approval_ref=validated_request.approval_ref,
        allowlist_ref=validated_request.allowlist_ref,
        command_ref=validated_request.command_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        replay_step_refs=list(validated_request.replay_step_refs),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        replay_view_only=active_policy.replay_view_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        reason_codes=[
            "M87_SANDBOXED_COMMAND_AUDIT_REPLAY_VIEW_ONLY",
            "M87_EXACT_M86_SHELL_APPROVAL_GATE_BINDING_REQUIRED",
            "M87_SAFE_REPLAY_STEPS_ONLY",
            "M87_NO_REPLAY_RUNNER",
            "M88_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M87 reviews a sandboxed command audit replay view over an exact M86 "
            "shell approval gate decision. It stores safe refs and safe summaries "
            "only, starts no replay runner, performs no command, shell, subprocess, "
            "process, filesystem, network, tool, browser, plugin, remote, model, "
            "memory, context, route, Control Center, dependency, or production action."
        ),
        receipt_plan=SandboxedCommandAuditReplayReceiptPlan(
            receipt_plan_ref=f"sandboxed-command-audit-replay-receipt-plan:{_ref_suffix(validated_request.replay_view_ref)}",
            replay_view_ref=validated_request.replay_view_ref,
            shell_approval_gate_decision_ref=validated_request.shell_approval_gate_decision_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            approval_ref=validated_request.approval_ref,
            command_ref=validated_request.command_ref,
            sandbox_spec_ref=validated_request.sandbox_spec_ref,
            audit_ref=validated_request.audit_ref,
            replay_ref=validated_request.replay_ref,
        ),
    )
    return validate_sandboxed_command_audit_replay_decision(decision)


def validate_sandboxed_command_audit_replay_policy(
    policy: SandboxedCommandAuditReplayPolicy,
) -> SandboxedCommandAuditReplayPolicy:
    validated = SandboxedCommandAuditReplayPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M87_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M87_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED") from exc
    return validated


def validate_sandboxed_command_audit_replay_request(
    request: SandboxedCommandAuditReplayRequest,
) -> SandboxedCommandAuditReplayRequest:
    payload = _model_payload(request)
    for field_name, reason in _M87_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = SandboxedCommandAuditReplayRequest.model_validate(payload)
    for field_name, reason in _M87_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M87_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.audit_replay_review_requested:
        raise ValueError("M87_AUDIT_REPLAY_REVIEW_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M87_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_approval_ref(validated.approval_ref)
    _validate_exact_m86_binding(validated)
    _validate_replay_steps(validated)
    try:
        _validate_safe_payload(validated.safe_purpose)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED") from exc
    return validated


def validate_sandboxed_command_audit_replay_decision(
    decision: SandboxedCommandAuditReplayDecision,
) -> SandboxedCommandAuditReplayDecision:
    validated = SandboxedCommandAuditReplayDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M87_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M87_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != SandboxedCommandAuditReplayStatus.ready_for_review:
        raise ValueError("M87_AUDIT_REPLAY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M87_SIDE_EFFECTS_DENIED")
    if len(validated.replay_step_refs) != len(set(validated.replay_step_refs)):
        raise ValueError("M87_REPLAY_STEP_REF_DUPLICATE")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M87_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_safe_refs_only:
        raise ValueError("M87_RECEIPT_REFS_ONLY_REQUIRED")
    if not validated.receipt_plan.store_replay_step_refs_only:
        raise ValueError("M87_RECEIPT_REPLAY_STEP_REFS_ONLY_REQUIRED")
    for field_name, reason in _M87_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M87_SIDE_EFFECTS_DENIED")
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED") from exc
    return validated


def validate_sandboxed_command_audit_replay_step(
    step: SandboxedCommandAuditReplayStep,
) -> SandboxedCommandAuditReplayStep:
    validated = SandboxedCommandAuditReplayStep.model_validate(_model_payload(step))
    for field_name, reason in _M87_STEP_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M87_STEP_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M87_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m86_binding(request: SandboxedCommandAuditReplayRequest) -> None:
    gate = validate_shell_approval_gate_decision(request.shell_approval_gate_decision)
    if request.shell_approval_gate_decision_ref != gate.decision_ref:
        raise ValueError("M87_M86_GATE_DECISION_BINDING_MISMATCH")
    for request_value, gate_value, reason in [
        (
            request.read_only_command_allowlist_decision_ref,
            gate.read_only_command_allowlist_decision_ref,
            "M87_M85_ALLOWLIST_DECISION_BINDING_MISMATCH",
        ),
        (request.approval_bundle_ref, gate.approval_bundle_ref, "M87_APPROVAL_BUNDLE_BINDING_MISMATCH"),
        (request.approval_ref, gate.approval_ref, "M87_APPROVAL_REF_BINDING_MISMATCH"),
        (request.allowlist_ref, gate.allowlist_ref, "M87_ALLOWLIST_BINDING_MISMATCH"),
        (request.command_ref, gate.command_ref, "M87_COMMAND_BINDING_MISMATCH"),
        (request.sandbox_spec_ref, gate.sandbox_spec_ref, "M87_SANDBOX_SPEC_BINDING_MISMATCH"),
        (request.actor_ref, gate.actor_ref, "M87_ACTOR_BINDING_MISMATCH"),
    ]:
        if request_value != gate_value:
            raise ValueError(reason)


def _validate_replay_steps(request: SandboxedCommandAuditReplayRequest) -> None:
    if not request.replay_step_refs or not request.replay_steps:
        raise ValueError("M87_REPLAY_STEPS_REQUIRED")
    if len(request.replay_step_refs) != len(set(request.replay_step_refs)):
        raise ValueError("M87_REPLAY_STEP_REF_DUPLICATE")
    step_refs = [step.step_ref for step in request.replay_steps]
    if len(step_refs) != len(set(step_refs)):
        raise ValueError("M87_REPLAY_STEP_REF_DUPLICATE")
    if request.replay_step_refs != step_refs:
        raise ValueError("M87_REPLAY_STEP_REF_BINDING_MISMATCH")
    for step in request.replay_steps:
        validated_step = validate_sandboxed_command_audit_replay_step(step)
        if validated_step.source_decision_ref != request.shell_approval_gate_decision_ref:
            raise ValueError("M87_REPLAY_STEP_SOURCE_BINDING_MISMATCH")


def _validate_receipt_binding(decision: SandboxedCommandAuditReplayDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value, reason in [
        (receipt.replay_view_ref, decision.replay_view_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.shell_approval_gate_decision_ref,
            decision.shell_approval_gate_decision_ref,
            "M87_RECEIPT_BINDING_MISMATCH",
        ),
        (receipt.approval_bundle_ref, decision.approval_bundle_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (receipt.approval_ref, decision.approval_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (receipt.command_ref, decision.command_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (receipt.sandbox_spec_ref, decision.sandbox_spec_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (receipt.audit_ref, decision.audit_ref, "M87_RECEIPT_BINDING_MISMATCH"),
        (receipt.replay_ref, decision.replay_ref, "M87_RECEIPT_BINDING_MISMATCH"),
    ]:
        if receipt_value != decision_value:
            raise ValueError(reason)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M87_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M87_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M87_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M87_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M87_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M87_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_approval_ref(ref: str) -> None:
    if ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M87_REQUIRED_TRUE = [
    ("contract_only", "M87_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("replay_view_only", "M87_REPLAY_VIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_SANDBOXED_COMMAND_AUDIT_REPLAY_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M87_SAFE_REFS_ONLY_REQUIRED"),
]

_M87_POLICY_REQUIRED_TRUE = _M87_REQUIRED_TRUE + [
    ("audit_replay_enabled_for_review", "M87_AUDIT_REPLAY_REVIEW_REQUIRED"),
    (
        "exact_shell_approval_gate_binding_required",
        "M87_EXACT_M86_SHELL_APPROVAL_GATE_BINDING_REQUIRED",
    ),
    ("exact_replay_step_binding_required", "M87_EXACT_REPLAY_STEP_BINDING_REQUIRED"),
]

_M87_DECISION_REQUIRED_TRUE = _M87_REQUIRED_TRUE + [
    (
        "shell_approval_gate_decision_revalidated",
        "M87_SHELL_APPROVAL_GATE_REVALIDATION_REQUIRED",
    ),
    ("replay_steps_bound", "M87_REPLAY_STEP_BINDING_REQUIRED"),
]

_M87_STEP_REQUIRED_TRUE = [
    ("replay_view_only", "M87_REPLAY_VIEW_ONLY_REQUIRED"),
    ("safe_refs_only", "M87_SAFE_REFS_ONLY_REQUIRED"),
]

_M87_POLICY_DENIALS = [
    ("replay_runner_enabled", "M87_REPLAY_RUNNER_DENIED"),
    ("replay_execution_enabled", "M87_REPLAY_EXECUTION_DENIED"),
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

_M87_REQUEST_DENIALS = [
    ("replay_runner_requested", "M87_REPLAY_RUNNER_DENIED"),
    ("replay_execution_requested", "M87_REPLAY_EXECUTION_DENIED"),
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
    ("contains_shell_string", "M87_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M87_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M87_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "M87_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M87_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED"),
]

_M87_STEP_DENIALS = [
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("replay_execution_performed", "M87_REPLAY_EXECUTION_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("contains_shell_string", "M87_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M87_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M87_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "M87_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M87_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED"),
]

_M87_DECISION_DENIALS = [
    ("replay_runner_started", "M87_REPLAY_RUNNER_DENIED"),
    ("replay_execution_performed", "M87_REPLAY_EXECUTION_DENIED"),
    ("command_execution_authorized", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_authorized", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_authorized", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_authorized", "PROCESS_SPAWN_DENIED"),
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

_M87_RECEIPT_DENIALS = [
    ("store_raw_command", "M87_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M87_SHELL_STRING_DENIED"),
    ("store_raw_output", "M87_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "M87_RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_SANDBOXED_COMMAND_AUDIT_REPLAY_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("replay_execution_performed", "M87_REPLAY_EXECUTION_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
