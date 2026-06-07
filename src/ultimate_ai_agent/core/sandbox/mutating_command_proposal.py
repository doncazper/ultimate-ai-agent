from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.command_audit_replay import (
    SandboxedCommandAuditReplayDecision,
    validate_sandboxed_command_audit_replay_decision,
)
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


MUTATING_COMMAND_PROPOSAL_DOCS = [
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_POLICY.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_RECEIPT_PLAN.md",
    "docs/sandbox/MUTATING_COMMAND_PROPOSAL_NON_GOALS.md",
    "docs/sandbox/M88_TO_M89_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M88_PRIOR_MILESTONE_REFS = (
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
)


class MutatingCommandProposalStatus(str, Enum):
    proposed_for_review = "proposed_for_review"


class _MutatingCommandProposalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MutatingCommandProposalPolicy(_MutatingCommandProposalModel):
    policy_ref: str = "mutating-command-proposal-policy:m88"
    mutating_command_proposal_enabled_for_review: bool = True
    contract_only: bool = True
    proposal_only: bool = True
    review_only: bool = True
    mutating_command_review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_audit_replay_binding_required: bool = True
    safe_mutation_scope_required: bool = True
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


class MutatingCommandProposalRequest(_MutatingCommandProposalModel):
    request_ref: str
    mutating_proposal_ref: str
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
    safe_mutation_summary: str
    safe_argument_refs: list[str]
    prior_milestone_refs: list[str]
    sandboxed_command_audit_replay_decision: SandboxedCommandAuditReplayDecision
    mutating_command_proposal_requested: bool = True
    contract_only: bool = True
    proposal_only: bool = True
    review_only: bool = True
    mutating_command_review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
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
            (self.mutating_proposal_ref, "mutating_proposal_ref"),
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
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_argument_refs:
            _validate_m61_ref(ref, "safe_argument_ref")
        _validate_safe_payload(self.safe_mutation_summary)
        return self


class MutatingCommandProposalReceiptPlan(_MutatingCommandProposalModel):
    receipt_plan_ref: str
    mutating_proposal_ref: str
    sandboxed_command_audit_replay_decision_ref: str
    shell_approval_gate_decision_ref: str
    approval_bundle_ref: str
    approval_ref: str
    command_ref: str
    sandbox_spec_ref: str
    mutation_intent_ref: str
    mutation_scope_ref: str
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_mutation_scope_ref_only: bool = True
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
    safe_summary: str = "M88 mutating command proposal receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.mutating_proposal_ref, "mutating_proposal_ref"),
            (
                self.sandboxed_command_audit_replay_decision_ref,
                "sandboxed_command_audit_replay_decision_ref",
            ),
            (self.shell_approval_gate_decision_ref, "shell_approval_gate_decision_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.approval_ref, "approval_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.mutation_intent_ref, "mutation_intent_ref"),
            (self.mutation_scope_ref, "mutation_scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class MutatingCommandProposalDecision(_MutatingCommandProposalModel):
    decision_ref: str
    mutating_proposal_ref: str
    request_ref: str
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
    safe_argument_refs: list[str]
    status: MutatingCommandProposalStatus = MutatingCommandProposalStatus.proposed_for_review
    contract_only: bool = True
    proposal_only: bool = True
    review_only: bool = True
    mutating_command_review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    audit_replay_decision_revalidated: bool = True
    mutation_scope_bound: bool = True
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
    receipt_plan: MutatingCommandProposalReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.mutating_proposal_ref, "mutating_proposal_ref"),
            (self.request_ref, "request_ref"),
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
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_argument_refs:
            _validate_m61_ref(ref, "safe_argument_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M88_REASON_CODE_REQUIRED")
        return self


def build_mutating_command_proposal(
    request: MutatingCommandProposalRequest,
    policy: MutatingCommandProposalPolicy | None = None,
) -> MutatingCommandProposalDecision:
    active_policy = validate_mutating_command_proposal_policy(
        policy or MutatingCommandProposalPolicy()
    )
    validated_request = validate_mutating_command_proposal_request(request)
    decision = MutatingCommandProposalDecision(
        decision_ref=f"mutating-command-proposal-decision:{_ref_suffix(validated_request.mutating_proposal_ref)}",
        mutating_proposal_ref=validated_request.mutating_proposal_ref,
        request_ref=validated_request.request_ref,
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
        safe_argument_refs=list(validated_request.safe_argument_refs),
        contract_only=active_policy.contract_only,
        proposal_only=active_policy.proposal_only,
        review_only=active_policy.review_only,
        mutating_command_review_only=active_policy.mutating_command_review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        reason_codes=[
            "M88_MUTATING_COMMAND_PROPOSAL_REVIEW_ONLY",
            "M88_EXACT_M87_AUDIT_REPLAY_BINDING_REQUIRED",
            "M88_SAFE_MUTATION_SCOPE_REQUIRED",
            "M88_NO_COMMAND_EXECUTION",
            "M89_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M88 reviews a mutating command proposal as safe metadata over an exact "
            "M87 sandboxed command audit replay decision. It grants no command, shell, "
            "subprocess, process, filesystem, network, tool, browser, plugin, remote, "
            "model, memory, context, route, Control Center, dependency, or production "
            "authority."
        ),
        receipt_plan=MutatingCommandProposalReceiptPlan(
            receipt_plan_ref=f"mutating-command-proposal-receipt-plan:{_ref_suffix(validated_request.mutating_proposal_ref)}",
            mutating_proposal_ref=validated_request.mutating_proposal_ref,
            sandboxed_command_audit_replay_decision_ref=(
                validated_request.sandboxed_command_audit_replay_decision_ref
            ),
            shell_approval_gate_decision_ref=validated_request.shell_approval_gate_decision_ref,
            approval_bundle_ref=validated_request.approval_bundle_ref,
            approval_ref=validated_request.approval_ref,
            command_ref=validated_request.command_ref,
            sandbox_spec_ref=validated_request.sandbox_spec_ref,
            mutation_intent_ref=validated_request.mutation_intent_ref,
            mutation_scope_ref=validated_request.mutation_scope_ref,
        ),
    )
    return validate_mutating_command_proposal_decision(decision)


def validate_mutating_command_proposal_policy(
    policy: MutatingCommandProposalPolicy,
) -> MutatingCommandProposalPolicy:
    validated = MutatingCommandProposalPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M88_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M88_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def validate_mutating_command_proposal_request(
    request: MutatingCommandProposalRequest,
) -> MutatingCommandProposalRequest:
    payload = _model_payload(request)
    for field_name, reason in _M88_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = MutatingCommandProposalRequest.model_validate(payload)
    for field_name, reason in _M88_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M88_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.mutating_command_proposal_requested:
        raise ValueError("M88_MUTATING_COMMAND_PROPOSAL_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M88_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_approval_ref(validated.approval_ref)
    _validate_safe_argument_refs(validated.safe_argument_refs)
    _validate_exact_m87_binding(validated)
    try:
        _validate_safe_payload(validated.safe_mutation_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def validate_mutating_command_proposal_decision(
    decision: MutatingCommandProposalDecision,
) -> MutatingCommandProposalDecision:
    validated = MutatingCommandProposalDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M88_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M88_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MutatingCommandProposalStatus.proposed_for_review:
        raise ValueError("M88_MUTATING_COMMAND_PROPOSAL_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M88_SIDE_EFFECTS_DENIED")
    _validate_safe_argument_refs(validated.safe_argument_refs)
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M88_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_safe_refs_only:
        raise ValueError("M88_RECEIPT_REFS_ONLY_REQUIRED")
    if not validated.receipt_plan.store_mutation_scope_ref_only:
        raise ValueError("M88_RECEIPT_MUTATION_SCOPE_REF_ONLY_REQUIRED")
    for field_name, reason in _M88_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M88_SIDE_EFFECTS_DENIED")
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m87_binding(request: MutatingCommandProposalRequest) -> None:
    replay = validate_sandboxed_command_audit_replay_decision(
        request.sandboxed_command_audit_replay_decision
    )
    if request.sandboxed_command_audit_replay_decision_ref != replay.decision_ref:
        raise ValueError("M88_M87_AUDIT_REPLAY_BINDING_MISMATCH")
    for request_value, replay_value, reason in [
        (
            request.shell_approval_gate_decision_ref,
            replay.shell_approval_gate_decision_ref,
            "M88_M86_GATE_DECISION_BINDING_MISMATCH",
        ),
        (request.approval_bundle_ref, replay.approval_bundle_ref, "M88_APPROVAL_BUNDLE_BINDING_MISMATCH"),
        (request.approval_ref, replay.approval_ref, "M88_APPROVAL_REF_BINDING_MISMATCH"),
        (request.command_ref, replay.command_ref, "M88_COMMAND_BINDING_MISMATCH"),
        (request.sandbox_spec_ref, replay.sandbox_spec_ref, "M88_SANDBOX_SPEC_BINDING_MISMATCH"),
        (request.actor_ref, replay.actor_ref, "M88_ACTOR_BINDING_MISMATCH"),
        (request.audit_ref, replay.audit_ref, "M88_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, replay.replay_ref, "M88_REPLAY_BINDING_MISMATCH"),
    ]:
        if request_value != replay_value:
            raise ValueError(reason)
    if not request.mutation_intent_ref.endswith("review-only"):
        raise ValueError("M88_MUTATION_SCOPE_BINDING_MISMATCH")
    if not request.mutation_scope_ref.endswith("safe-summary"):
        raise ValueError("M88_MUTATION_SCOPE_BINDING_MISMATCH")


def _validate_receipt_binding(decision: MutatingCommandProposalDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value, reason in [
        (receipt.mutating_proposal_ref, decision.mutating_proposal_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (
            receipt.sandboxed_command_audit_replay_decision_ref,
            decision.sandboxed_command_audit_replay_decision_ref,
            "M88_RECEIPT_BINDING_MISMATCH",
        ),
        (
            receipt.shell_approval_gate_decision_ref,
            decision.shell_approval_gate_decision_ref,
            "M88_RECEIPT_BINDING_MISMATCH",
        ),
        (receipt.approval_bundle_ref, decision.approval_bundle_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (receipt.approval_ref, decision.approval_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (receipt.command_ref, decision.command_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (receipt.sandbox_spec_ref, decision.sandbox_spec_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (receipt.mutation_intent_ref, decision.mutation_intent_ref, "M88_RECEIPT_BINDING_MISMATCH"),
        (receipt.mutation_scope_ref, decision.mutation_scope_ref, "M88_RECEIPT_BINDING_MISMATCH"),
    ]:
        if receipt_value != decision_value:
            raise ValueError(reason)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M88_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M88_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M88_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M88_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M88_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M88_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_argument_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M88_SAFE_ARGUMENT_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M88_SAFE_ARGUMENT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "safe_argument_ref")


def _validate_approval_ref(ref: str) -> None:
    if ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M88_REQUIRED_TRUE = [
    ("contract_only", "M88_CONTRACT_ONLY_REQUIRED"),
    ("proposal_only", "M88_PROPOSAL_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("mutating_command_review_only", "M88_MUTATING_COMMAND_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_MUTATING_COMMAND_PROPOSAL_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M88_SAFE_REFS_ONLY_REQUIRED"),
]

_M88_POLICY_REQUIRED_TRUE = _M88_REQUIRED_TRUE + [
    ("mutating_command_proposal_enabled_for_review", "M88_MUTATING_COMMAND_PROPOSAL_REQUIRED"),
    ("exact_audit_replay_binding_required", "M88_EXACT_M87_AUDIT_REPLAY_BINDING_REQUIRED"),
    ("safe_mutation_scope_required", "M88_SAFE_MUTATION_SCOPE_REQUIRED"),
]

_M88_DECISION_REQUIRED_TRUE = _M88_REQUIRED_TRUE + [
    ("audit_replay_decision_revalidated", "M88_AUDIT_REPLAY_REVALIDATION_REQUIRED"),
    ("mutation_scope_bound", "M88_MUTATION_SCOPE_BINDING_REQUIRED"),
]

_M88_POLICY_DENIALS = [
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

_M88_REQUEST_DENIALS = [
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
    ("contains_shell_string", "M88_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M88_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M88_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "M88_RAW_PROMPT_DENIED"),
    ("contains_raw_provider_payload", "M88_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_secret", "SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED"),
]

_M88_DECISION_DENIALS = [
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

_M88_RECEIPT_DENIALS = [
    ("store_raw_command", "M88_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M88_SHELL_STRING_DENIED"),
    ("store_raw_output", "M88_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "M88_RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_MUTATING_COMMAND_PROPOSAL_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
