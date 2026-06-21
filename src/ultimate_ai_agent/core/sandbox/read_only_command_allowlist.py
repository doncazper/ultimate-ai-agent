from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload
from ultimate_ai_agent.core.sandbox.sandboxed_echo_noop_command import (
    SandboxedEchoNoOpCommandDecision,
    SandboxedEchoNoOpCommandStatus,
    validate_sandboxed_echo_noop_command_decision,
)
from ultimate_ai_agent.core.sandbox.shell_dry_run_classifier import ShellDryRunClass


READ_ONLY_COMMAND_ALLOWLIST_DOCS = [
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_POLICY.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_RECEIPT_PLAN.md",
    "docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_NON_GOALS.md",
    "docs/sandbox/M85_TO_M86_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M85_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
    "milestone:M83",
    "milestone:M84",
)


class ReadOnlyCommandAllowlistStatus(str, Enum):
    allowlisted_for_review = "allowlisted_for_review"


class ReadOnlyCommandAllowlistEffect(str, Enum):
    no_effect_review = "no_effect_review"
    read_only_review = "read_only_review"


class _ReadOnlyCommandAllowlistModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ReadOnlyCommandAllowlistEntry(_ReadOnlyCommandAllowlistModel):
    entry_ref: str
    command_ref: str
    safe_command_label: str
    allowed_effect: ReadOnlyCommandAllowlistEffect = (
        ReadOnlyCommandAllowlistEffect.no_effect_review
    )
    safe_argument_profile_ref: str
    reviewed_by_actor_ref: str
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
    no_shell_string: bool = True
    no_raw_command: bool = True
    no_raw_output: bool = True
    command_execution_authorized: bool = False
    shell_execution_authorized: bool = False
    subprocess_execution_authorized: bool = False
    process_spawn_authorized: bool = False
    filesystem_mutation_authorized: bool = False
    network_access_authorized: bool = False
    tool_execution_authorized: bool = False
    browser_automation_authorized: bool = False
    plugin_execution_authorized: bool = False
    remote_execution_authorized: bool = False
    model_call_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    production_authority_authorized: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.entry_ref, "entry_ref"),
            (self.command_ref, "command_ref"),
            (self.safe_argument_profile_ref, "safe_argument_profile_ref"),
            (self.reviewed_by_actor_ref, "reviewed_by_actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_command_label)
        return self


class ReadOnlyCommandAllowlistPolicy(_ReadOnlyCommandAllowlistModel):
    policy_ref: str = "read-only-command-allowlist-policy:m85"
    allowlist_enabled_for_review: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
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


class ReadOnlyCommandAllowlistRequest(_ReadOnlyCommandAllowlistModel):
    request_ref: str
    allowlist_ref: str
    sandboxed_command_ref: str
    sandboxed_echo_noop_decision_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    prior_milestone_refs: list[str]
    sandboxed_echo_noop_decision: SandboxedEchoNoOpCommandDecision
    entries: list[ReadOnlyCommandAllowlistEntry]
    requested_command_ref: str
    safe_purpose: str
    allowlist_review_requested: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
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
            (self.allowlist_ref, "allowlist_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.sandboxed_echo_noop_decision_ref, "sandboxed_echo_noop_decision_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.command_ref, "command_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.requested_command_ref, "requested_command_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_purpose)
        return self


class ReadOnlyCommandAllowlistReceiptPlan(_ReadOnlyCommandAllowlistModel):
    receipt_plan_ref: str
    allowlist_ref: str
    sandboxed_echo_noop_decision_ref: str
    command_proposal_ref: str
    command_ref: str
    store_safe_summary_only: bool = True
    store_allowlist_refs_only: bool = True
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
    safe_summary: str = "M85 read-only command allowlist receipt stores safe refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.sandboxed_echo_noop_decision_ref, "sandboxed_echo_noop_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.command_ref, "command_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class ReadOnlyCommandAllowlistDecision(_ReadOnlyCommandAllowlistModel):
    decision_ref: str
    allowlist_ref: str
    request_ref: str
    sandboxed_command_ref: str
    sandboxed_echo_noop_decision_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    command_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    status: ReadOnlyCommandAllowlistStatus = (
        ReadOnlyCommandAllowlistStatus.allowlisted_for_review
    )
    allowed_effect: ReadOnlyCommandAllowlistEffect
    allowlist_match_found: bool = True
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    read_only_only: bool = True
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
    matched_entry: ReadOnlyCommandAllowlistEntry
    receipt_plan: ReadOnlyCommandAllowlistReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.allowlist_ref, "allowlist_ref"),
            (self.request_ref, "request_ref"),
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


def build_read_only_command_allowlist_decision(
    request: ReadOnlyCommandAllowlistRequest,
    policy: ReadOnlyCommandAllowlistPolicy | None = None,
) -> ReadOnlyCommandAllowlistDecision:
    active_policy = validate_read_only_command_allowlist_policy(
        policy or ReadOnlyCommandAllowlistPolicy()
    )
    validated_request = validate_read_only_command_allowlist_request(request)
    matched_entry = _find_matching_entry(
        validated_request.requested_command_ref,
        validated_request.entries,
    )
    decision = ReadOnlyCommandAllowlistDecision(
        decision_ref=f"read-only-command-allowlist-decision:{_ref_suffix(validated_request.allowlist_ref)}",
        allowlist_ref=validated_request.allowlist_ref,
        request_ref=validated_request.request_ref,
        sandboxed_command_ref=validated_request.sandboxed_command_ref,
        sandboxed_echo_noop_decision_ref=validated_request.sandboxed_echo_noop_decision_ref,
        shell_dry_run_decision_ref=validated_request.shell_dry_run_decision_ref,
        command_proposal_ref=validated_request.command_proposal_ref,
        command_ref=matched_entry.command_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        allowed_effect=matched_entry.allowed_effect,
        allowlist_match_found=active_policy.allowlist_enabled_for_review,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        read_only_only=active_policy.read_only_only,
        reason_codes=[
            "M85_READ_ONLY_COMMAND_ALLOWLIST_CONTRACT_ONLY",
            "M85_EXACT_M84_BINDING_REQUIRED",
            "M85_NO_COMMAND_EXECUTION",
            "M86_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M85 records a read-only command allowlist decision for human review "
            "with safe refs only. It does not authorize or perform command, shell, "
            "subprocess, process, filesystem, network, tool, browser, plugin, "
            "remote, model, memory, context, route, Control Center, dependency, "
            "or production actions."
        ),
        matched_entry=matched_entry,
        receipt_plan=ReadOnlyCommandAllowlistReceiptPlan(
            receipt_plan_ref=f"read-only-command-allowlist-receipt-plan:{_ref_suffix(validated_request.allowlist_ref)}",
            allowlist_ref=validated_request.allowlist_ref,
            sandboxed_echo_noop_decision_ref=validated_request.sandboxed_echo_noop_decision_ref,
            command_proposal_ref=validated_request.command_proposal_ref,
            command_ref=matched_entry.command_ref,
        ),
    )
    return validate_read_only_command_allowlist_decision(decision)


def validate_read_only_command_allowlist_entry(
    entry: ReadOnlyCommandAllowlistEntry,
) -> ReadOnlyCommandAllowlistEntry:
    validated = ReadOnlyCommandAllowlistEntry.model_validate(_model_payload(entry))
    for field_name, reason in _M85_ENTRY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M85_ENTRY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.safe_command_label)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED") from exc
    return validated


def validate_read_only_command_allowlist_policy(
    policy: ReadOnlyCommandAllowlistPolicy,
) -> ReadOnlyCommandAllowlistPolicy:
    validated = ReadOnlyCommandAllowlistPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M85_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M85_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED") from exc
    return validated


def validate_read_only_command_allowlist_request(
    request: ReadOnlyCommandAllowlistRequest,
) -> ReadOnlyCommandAllowlistRequest:
    payload = _model_payload(request)
    for field_name, reason in _M85_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ReadOnlyCommandAllowlistRequest.model_validate(payload)
    for field_name, reason in _M85_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M85_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.allowlist_review_requested:
        raise ValueError("M85_ALLOWLIST_REVIEW_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M85_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_exact_m84_binding(validated)
    entries = [
        validate_read_only_command_allowlist_entry(entry)
        for entry in validated.entries
    ]
    _validate_allowlist_entries(entries)
    _find_matching_entry(validated.requested_command_ref, entries)
    try:
        _validate_safe_payload(validated.safe_purpose)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED") from exc
    return validated


def validate_read_only_command_allowlist_decision(
    decision: ReadOnlyCommandAllowlistDecision,
) -> ReadOnlyCommandAllowlistDecision:
    validated = ReadOnlyCommandAllowlistDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M85_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M85_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ReadOnlyCommandAllowlistStatus.allowlisted_for_review:
        raise ValueError("M85_ALLOWLIST_STATUS_REQUIRED")
    if not validated.allowlist_match_found:
        raise ValueError("M85_ALLOWLIST_MATCH_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M85_SIDE_EFFECTS_DENIED")
    matched_entry = validate_read_only_command_allowlist_entry(validated.matched_entry)
    if matched_entry.command_ref != validated.command_ref:
        raise ValueError("M85_ALLOWLIST_ENTRY_BINDING_MISMATCH")
    if matched_entry.allowed_effect != validated.allowed_effect:
        raise ValueError("M85_ALLOWLIST_ENTRY_BINDING_MISMATCH")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M85_RECEIPT_SAFE_SUMMARY_REQUIRED")
    if not validated.receipt_plan.store_allowlist_refs_only:
        raise ValueError("M85_RECEIPT_REFS_ONLY_REQUIRED")
    for field_name, reason in _M85_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M85_SIDE_EFFECTS_DENIED")
    if validated.receipt_plan.allowlist_ref != validated.allowlist_ref:
        raise ValueError("M85_RECEIPT_BINDING_MISMATCH")
    if (
        validated.receipt_plan.sandboxed_echo_noop_decision_ref
        != validated.sandboxed_echo_noop_decision_ref
    ):
        raise ValueError("M85_RECEIPT_BINDING_MISMATCH")
    if validated.receipt_plan.command_proposal_ref != validated.command_proposal_ref:
        raise ValueError("M85_RECEIPT_BINDING_MISMATCH")
    if validated.receipt_plan.command_ref != validated.command_ref:
        raise ValueError("M85_RECEIPT_BINDING_MISMATCH")
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED") from exc
    return validated


def _validate_exact_m84_binding(request: ReadOnlyCommandAllowlistRequest) -> None:
    decision = validate_sandboxed_echo_noop_command_decision(
        request.sandboxed_echo_noop_decision
    )
    if decision.status != SandboxedEchoNoOpCommandStatus.completed_for_review:
        raise ValueError("M85_M84_SANDBOXED_COMMAND_STATUS_REQUIRED")
    if decision.classification != ShellDryRunClass.no_effect_review:
        raise ValueError("M85_M84_NO_EFFECT_CLASSIFICATION_REQUIRED")
    if request.sandboxed_command_ref != decision.sandboxed_command_ref:
        raise ValueError("M85_M84_BINDING_MISMATCH")
    if request.sandboxed_echo_noop_decision_ref != decision.decision_ref:
        raise ValueError("M85_M84_BINDING_MISMATCH")
    if request.shell_dry_run_decision_ref != decision.shell_dry_run_decision_ref:
        raise ValueError("M85_SHELL_DRY_RUN_BINDING_MISMATCH")
    if request.command_proposal_ref != decision.command_proposal_ref:
        raise ValueError("M85_COMMAND_PROPOSAL_BINDING_MISMATCH")
    if request.command_ref != request.requested_command_ref:
        raise ValueError("M85_COMMAND_REF_BINDING_MISMATCH")
    if request.sandbox_spec_ref != decision.sandbox_spec_ref:
        raise ValueError("M85_SANDBOX_SPEC_BINDING_MISMATCH")
    if request.actor_ref != decision.actor_ref:
        raise ValueError("M85_ACTOR_BINDING_MISMATCH")


def _validate_allowlist_entries(entries: list[ReadOnlyCommandAllowlistEntry]) -> None:
    if not entries:
        raise ValueError("M85_ALLOWLIST_ENTRY_REQUIRED")
    entry_refs = [entry.entry_ref for entry in entries]
    command_refs = [entry.command_ref for entry in entries]
    if len(entry_refs) != len(set(entry_refs)):
        raise ValueError("M85_ALLOWLIST_ENTRY_DUPLICATE")
    if len(command_refs) != len(set(command_refs)):
        raise ValueError("M85_ALLOWLIST_COMMAND_DUPLICATE")


def _find_matching_entry(
    command_ref: str,
    entries: list[ReadOnlyCommandAllowlistEntry],
) -> ReadOnlyCommandAllowlistEntry:
    for entry in entries:
        if entry.command_ref == command_ref:
            return validate_read_only_command_allowlist_entry(entry)
    raise ValueError("M85_ALLOWLIST_ENTRY_NOT_FOUND")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M85_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M85_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M85_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M85_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M85_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M85_PRIOR_MILESTONE_REF_UNEXPECTED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M85_ENTRY_REQUIRED_TRUE = [
    ("deterministic", "DETERMINISTIC_COMMAND_ALLOWLIST_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("read_only_only", "M85_READ_ONLY_ONLY_REQUIRED"),
    ("no_shell_string", "M85_SHELL_STRING_DENIED"),
    ("no_raw_command", "M85_RAW_COMMAND_DENIED"),
    ("no_raw_output", "M85_RAW_OUTPUT_DENIED"),
]


_M85_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M85_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_COMMAND_ALLOWLIST_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("read_only_only", "M85_READ_ONLY_ONLY_REQUIRED"),
]


_M85_ENTRY_DENIALS = [
    ("command_execution_authorized", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_authorized", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_authorized", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_authorized", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_authorized", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_authorized", "NETWORK_ACCESS_DENIED"),
    ("tool_execution_authorized", "TOOL_EXECUTION_DENIED"),
    ("browser_automation_authorized", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_authorized", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_authorized", "REMOTE_EXECUTION_DENIED"),
    ("model_call_authorized", "MODEL_CALL_DENIED"),
    ("memory_write_authorized", "MEMORY_WRITE_DENIED"),
    ("context_injection_authorized", "CONTEXT_INJECTION_DENIED"),
    ("production_authority_authorized", "PRODUCTION_AUTHORITY_DENIED"),
]


_M85_POLICY_DENIALS = [
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


_M85_REQUEST_DENIALS = [
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
    ("contains_shell_string", "M85_SHELL_STRING_DENIED"),
    ("contains_raw_command", "M85_RAW_COMMAND_DENIED"),
    ("contains_raw_output", "M85_RAW_OUTPUT_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED"),
]


_M85_DECISION_DENIALS = [
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


_M85_RECEIPT_DENIALS = [
    ("store_raw_command", "M85_RECEIPT_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M85_RECEIPT_SHELL_STRING_DENIED"),
    ("store_raw_output", "M85_RECEIPT_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("store_secret", "SECRET_LIKE_COMMAND_ALLOWLIST_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
]
