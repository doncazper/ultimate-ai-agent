from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy import (
    ScopedApprovalBundle,
    validate_scoped_approval_bundle,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.read_only_command_allowlist import (
    ReadOnlyCommandAllowlistDecision,
    validate_read_only_command_allowlist_decision,
)
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


SHELL_APPROVAL_GATE_DOCS = [
    "docs/sandbox/SHELL_APPROVAL_GATE.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_POLICY.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_APPROVAL_GATE_NON_GOALS.md",
    "docs/sandbox/M86_TO_M87_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M86_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
    "milestone:M83",
    "milestone:M84",
    "milestone:M85",
)


class ShellApprovalGateStatus(str, Enum):
    approved_for_review = "approved_for_review"


class _ShellApprovalGateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ShellApprovalGatePolicy(_ShellApprovalGateModel):
    policy_ref: str = "shell-approval-gate-policy:m86"
    gate_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
    approval_ref_identifier_only: bool = True
    exact_allowlist_binding_required: bool = True
    exact_approval_bundle_binding_required: bool = True
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


class ShellApprovalGateRequest(_ShellApprovalGateModel):
    request_ref: str
    gate_ref: str
    read_only_command_allowlist_decision_ref: str
    allowlist_ref: str
    sandboxed_command_ref: str
    sandboxed_echo_noop_decision_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    approval_bundle_ref: str
    approval_ref: str
    revocation_ref: str
    audit_ref: str
    replay_ref: str
    prior_milestone_refs: list[str]
    read_only_command_allowlist_decision: ReadOnlyCommandAllowlistDecision
    approval_bundle: ScopedApprovalBundle
    safe_purpose: str
    approval_gate_review_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
    approval_ref_identifier_only: bool = True
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
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.gate_ref, "gate_ref"),
            (
                self.read_only_command_allowlist_decision_ref,
                "read_only_command_allowlist_decision_ref",
            ),
            (self.allowlist_ref, "allowlist_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.sandboxed_echo_noop_decision_ref, "sandboxed_echo_noop_decision_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_purpose)
        return self


class ShellApprovalGateReceiptPlan(_ShellApprovalGateModel):
    receipt_plan_ref: str
    gate_ref: str
    read_only_command_allowlist_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    allowlist_ref: str
    command_ref: str
    sandbox_spec_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_output: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    filesystem_mutation_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M86 shell approval gate receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.gate_ref, "gate_ref"),
            (
                self.read_only_command_allowlist_decision_ref,
                "read_only_command_allowlist_decision_ref",
            ),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class ShellApprovalGateDecision(_ShellApprovalGateModel):
    decision_ref: str
    gate_ref: str
    request_ref: str
    read_only_command_allowlist_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    allowlist_ref: str
    sandboxed_command_ref: str
    sandboxed_echo_noop_decision_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    status: ShellApprovalGateStatus = ShellApprovalGateStatus.approved_for_review
    approval_valid_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
    approval_ref_is_identifier_only: bool = True
    approval_bound_to_allowlist: bool = True
    approval_bound_to_command: bool = True
    approval_bound_to_actor: bool = True
    approval_bound_to_sandbox: bool = True
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
    receipt_plan: ShellApprovalGateReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.gate_ref, "gate_ref"),
            (self.request_ref, "request_ref"),
            (
                self.read_only_command_allowlist_decision_ref,
                "read_only_command_allowlist_decision_ref",
            ),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.sandboxed_echo_noop_decision_ref, "sandboxed_echo_noop_decision_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_shell_approval_gate_decision(
    request: ShellApprovalGateRequest,
    policy: ShellApprovalGatePolicy | None = None,
) -> ShellApprovalGateDecision:
    active_policy = validate_shell_approval_gate_policy(policy or ShellApprovalGatePolicy())
    validated_request = validate_shell_approval_gate_request(request)
    decision = ShellApprovalGateDecision(
        decision_ref=f"shell-approval-gate-decision:{_ref_suffix(validated_request.gate_ref)}",
        gate_ref=validated_request.gate_ref,
        request_ref=validated_request.request_ref,
        read_only_command_allowlist_decision_ref=(
            validated_request.read_only_command_allowlist_decision_ref
        ),
        approval_bundle_ref=validated_request.approval_bundle_ref,
        approval_ref=validated_request.approval_ref,
        allowlist_ref=validated_request.allowlist_ref,
        sandboxed_command_ref=validated_request.sandboxed_command_ref,
        sandboxed_echo_noop_decision_ref=(
            validated_request.sandboxed_echo_noop_decision_ref
        ),
        shell_dry_run_decision_ref=validated_request.shell_dry_run_decision_ref,
        command_proposal_ref=validated_request.command_proposal_ref,
        command_ref=validated_request.command_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        approval_valid_for_review=active_policy.gate_enabled_for_review,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        read_only_only=active_policy.read_only_only,
        approval_ref_is_identifier_only=active_policy.approval_ref_identifier_only,
        reason_codes=[
            "M86_SHELL_APPROVAL_GATE_REVIEW_ONLY",
            "M86_EXACT_M85_ALLOWLIST_BINDING_REQUIRED",
            "M86_APPROVAL_BUNDLE_EXACT_SCOPE_REQUIRED",
            "M86_NO_SHELL_EXECUTION",
            "M87_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M86 validates a shell approval gate decision for human review only. "
            "It binds an identifier-only approval bundle to an exact M85 read-only "
            "command allowlist decision and grants no command, shell, subprocess, "
            "process, filesystem, network, tool, browser, plugin, remote, model, "
            "memory, context, route, Control Center, dependency, or production authority."
        ),
        receipt_plan=ShellApprovalGateReceiptPlan(
            receipt_plan_ref=f"shell-approval-gate-receipt-plan:{_ref_suffix(validated_request.gate_ref)}",
            gate_ref=validated_request.gate_ref,
            read_only_command_allowlist_decision_ref=(
                validated_request.read_only_command_allowlist_decision_ref
            ),
            approval_bundle_ref=validated_request.approval_bundle_ref,
            approval_ref=validated_request.approval_ref,
            allowlist_ref=validated_request.allowlist_ref,
            command_ref=validated_request.command_ref,
            sandbox_spec_ref=validated_request.sandbox_spec_ref,
        ),
    )
    return validate_shell_approval_gate_decision(decision)


def validate_shell_approval_gate_policy(
    policy: ShellApprovalGatePolicy,
) -> ShellApprovalGatePolicy:
    validated = ShellApprovalGatePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M86_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M86_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED") from exc
    return validated


def validate_shell_approval_gate_request(
    request: ShellApprovalGateRequest,
) -> ShellApprovalGateRequest:
    payload = _model_payload(request)
    for field_name, reason in _M86_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ShellApprovalGateRequest.model_validate(payload)
    for field_name, reason in _M86_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M86_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.approval_gate_review_requested:
        raise ValueError("M86_APPROVAL_GATE_REVIEW_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M86_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_approval_ref(validated.approval_ref)
    _validate_exact_m85_binding(validated)
    _validate_exact_approval_bundle_binding(validated)
    try:
        _validate_safe_payload(validated.safe_purpose)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED") from exc
    return validated


def validate_shell_approval_gate_decision(
    decision: ShellApprovalGateDecision,
) -> ShellApprovalGateDecision:
    validated = ShellApprovalGateDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M86_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M86_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ShellApprovalGateStatus.approved_for_review:
        raise ValueError("M86_SHELL_APPROVAL_GATE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M86_SIDE_EFFECTS_DENIED")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M86_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_safe_refs_only:
        raise ValueError("M86_RECEIPT_REFS_ONLY_REQUIRED")
    for field_name, reason in _M86_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M86_SIDE_EFFECTS_DENIED")
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m85_binding(request: ShellApprovalGateRequest) -> None:
    allowlist_decision = validate_read_only_command_allowlist_decision(
        request.read_only_command_allowlist_decision
    )
    if (
        request.read_only_command_allowlist_decision_ref
        != allowlist_decision.decision_ref
    ):
        raise ValueError("M86_M85_ALLOWLIST_DECISION_BINDING_MISMATCH")
    for request_value, decision_value, reason in [
        (request.allowlist_ref, allowlist_decision.allowlist_ref, "M86_ALLOWLIST_BINDING_MISMATCH"),
        (
            request.sandboxed_command_ref,
            allowlist_decision.sandboxed_command_ref,
            "M86_SANDBOXED_COMMAND_BINDING_MISMATCH",
        ),
        (
            request.sandboxed_echo_noop_decision_ref,
            allowlist_decision.sandboxed_echo_noop_decision_ref,
            "M86_SANDBOXED_ECHO_NOOP_BINDING_MISMATCH",
        ),
        (
            request.shell_dry_run_decision_ref,
            allowlist_decision.shell_dry_run_decision_ref,
            "M86_SHELL_DRY_RUN_BINDING_MISMATCH",
        ),
        (
            request.command_proposal_ref,
            allowlist_decision.command_proposal_ref,
            "M86_COMMAND_PROPOSAL_BINDING_MISMATCH",
        ),
        (request.command_ref, allowlist_decision.command_ref, "M86_COMMAND_BINDING_MISMATCH"),
        (
            request.sandbox_spec_ref,
            allowlist_decision.sandbox_spec_ref,
            "M86_SANDBOX_SPEC_BINDING_MISMATCH",
        ),
        (request.actor_ref, allowlist_decision.actor_ref, "M86_ACTOR_BINDING_MISMATCH"),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)


def _validate_exact_approval_bundle_binding(request: ShellApprovalGateRequest) -> None:
    bundle = validate_scoped_approval_bundle(request.approval_bundle)
    if request.approval_bundle_ref != bundle.bundle_ref:
        raise ValueError("M86_APPROVAL_BUNDLE_BINDING_MISMATCH")
    if request.approval_ref not in bundle.approval_refs:
        raise ValueError("M86_APPROVAL_REF_BINDING_MISMATCH")
    if request.actor_ref != bundle.actor_ref:
        raise ValueError("M86_ACTOR_BINDING_MISMATCH")
    if request.command_ref not in bundle.resource_refs:
        raise ValueError("M86_COMMAND_BINDING_MISMATCH")
    if request.sandbox_spec_ref not in bundle.resource_refs:
        raise ValueError("M86_SANDBOX_SPEC_BINDING_MISMATCH")
    if request.allowlist_ref not in bundle.allowlist_refs:
        raise ValueError("M86_ALLOWLIST_BINDING_MISMATCH")
    if "capability:shell-approval-gate-review" not in bundle.capability_refs:
        raise ValueError("M86_APPROVAL_CAPABILITY_BINDING_MISMATCH")
    if request.revocation_ref != bundle.revocation_ref:
        raise ValueError("M86_REVOCATION_BINDING_MISMATCH")
    if request.audit_ref != bundle.audit_ref:
        raise ValueError("M86_AUDIT_BINDING_MISMATCH")
    if request.replay_ref != bundle.replay_ref:
        raise ValueError("M86_REPLAY_BINDING_MISMATCH")


def _validate_receipt_binding(decision: ShellApprovalGateDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value, reason in [
        (receipt.gate_ref, decision.gate_ref, "M86_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.read_only_command_allowlist_decision_ref,
            decision.read_only_command_allowlist_decision_ref,
            "M86_RECEIPT_BINDING_MISMATCH",
        ),
        (
            receipt.approval_bundle_ref,
            decision.approval_bundle_ref,
            "M86_RECEIPT_BINDING_MISMATCH",
        ),
        (receipt.approval_ref, decision.approval_ref, "M86_RECEIPT_BINDING_MISMATCH"),
        (receipt.allowlist_ref, decision.allowlist_ref, "M86_RECEIPT_BINDING_MISMATCH"),
        (receipt.command_ref, decision.command_ref, "M86_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.sandbox_spec_ref,
            decision.sandbox_spec_ref,
            "M86_RECEIPT_BINDING_MISMATCH",
        ),
    ]:
        if receipt_value != decision_value:
            raise ValueError(reason)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M86_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M86_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M86_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M86_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M86_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M86_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_approval_ref(ref: str) -> None:
    if ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M86_REQUIRED_TRUE = [
    ("contract_only", "M86_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_SHELL_APPROVAL_GATE_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("read_only_only", "M86_READ_ONLY_ONLY_REQUIRED"),
]

_M86_DECISION_REQUIRED_TRUE = _M86_REQUIRED_TRUE + [
    ("approval_valid_for_review", "M86_APPROVAL_VALID_FOR_REVIEW_REQUIRED"),
    ("approval_ref_is_identifier_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
    ("approval_bound_to_allowlist", "M86_ALLOWLIST_BINDING_REQUIRED"),
    ("approval_bound_to_command", "M86_COMMAND_BINDING_REQUIRED"),
    ("approval_bound_to_actor", "ACTOR_BINDING_REQUIRED"),
    ("approval_bound_to_sandbox", "M86_SANDBOX_SPEC_BINDING_REQUIRED"),
]

_M86_POLICY_DENIALS = [
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

_M86_REQUEST_DENIALS = [
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
    ("contains_shell_string", "M86_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M86_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M86_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "M86_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M86_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED"),
]

_M86_DECISION_DENIALS = [
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

_M86_RECEIPT_DENIALS = [
    ("store_raw_command", "M86_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M86_SHELL_STRING_DENIED"),
    ("store_raw_output", "M86_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "M86_RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_SHELL_APPROVAL_GATE_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
