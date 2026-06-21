from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload
from ultimate_ai_agent.core.sandbox.shell_dry_run_classifier import (
    ShellDryRunClassificationStatus,
    ShellDryRunClass,
    ShellDryRunClassifierDecision,
    validate_shell_dry_run_classifier_decision,
)


SANDBOXED_ECHO_NOOP_COMMAND_DOCS = [
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_POLICY.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_RECEIPT_PLAN.md",
    "docs/sandbox/SANDBOXED_ECHO_NOOP_COMMAND_NON_GOALS.md",
    "docs/sandbox/M84_TO_M85_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M84_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
    "milestone:M83",
)


class SandboxedEchoNoOpCommandStatus(str, Enum):
    completed_for_review = "completed_for_review"


class _SandboxedEchoNoOpCommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class SandboxedEchoNoOpCommandPolicy(_SandboxedEchoNoOpCommandModel):
    policy_ref: str = "sandboxed-echo-noop-command-policy:m84"
    sandboxed_echo_noop_enabled: bool = True
    in_process_only: bool = True
    deterministic: bool = True
    local_only: bool = True
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


class SandboxedEchoNoOpCommandRequest(_SandboxedEchoNoOpCommandModel):
    request_ref: str
    sandboxed_command_ref: str
    shell_dry_run_classifier_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    prior_milestone_refs: list[str]
    safe_echo_text: str = "Sandboxed echo/no-op command completed with safe metadata only."
    shell_dry_run_classification: ShellDryRunClassifierDecision
    sandboxed_echo_noop_requested: bool = True
    in_process_only: bool = True
    deterministic: bool = True
    local_only: bool = True
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
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.shell_dry_run_classifier_ref, "shell_dry_run_classifier_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class SandboxedEchoNoOpCommandReceiptPlan(_SandboxedEchoNoOpCommandModel):
    receipt_plan_ref: str
    sandboxed_command_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    store_safe_summary_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_output: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    command_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M84 sandboxed echo/no-op command receipt stores safe metadata only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class SandboxedEchoNoOpCommandDecision(_SandboxedEchoNoOpCommandModel):
    decision_ref: str
    sandboxed_command_ref: str
    request_ref: str
    shell_dry_run_classifier_ref: str
    shell_dry_run_decision_ref: str
    command_proposal_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    status: SandboxedEchoNoOpCommandStatus = SandboxedEchoNoOpCommandStatus.completed_for_review
    classification: ShellDryRunClass = ShellDryRunClass.no_effect_review
    sandboxed_echo_noop_allowed: bool = True
    in_process_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_echo_text: str
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
    receipt_plan: SandboxedEchoNoOpCommandReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.sandboxed_command_ref, "sandboxed_command_ref"),
            (self.request_ref, "request_ref"),
            (self.shell_dry_run_classifier_ref, "shell_dry_run_classifier_ref"),
            (self.shell_dry_run_decision_ref, "shell_dry_run_decision_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        _validate_safe_payload(self.safe_echo_text)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_sandboxed_echo_noop_command(
    request: SandboxedEchoNoOpCommandRequest,
    policy: SandboxedEchoNoOpCommandPolicy | None = None,
) -> SandboxedEchoNoOpCommandDecision:
    active_policy = validate_sandboxed_echo_noop_command_policy(
        policy or SandboxedEchoNoOpCommandPolicy()
    )
    validated_request = validate_sandboxed_echo_noop_command_request(request)
    decision = SandboxedEchoNoOpCommandDecision(
        decision_ref=f"sandboxed-echo-noop-command-decision:{_ref_suffix(validated_request.sandboxed_command_ref)}",
        sandboxed_command_ref=validated_request.sandboxed_command_ref,
        request_ref=validated_request.request_ref,
        shell_dry_run_classifier_ref=validated_request.shell_dry_run_classifier_ref,
        shell_dry_run_decision_ref=validated_request.shell_dry_run_decision_ref,
        command_proposal_ref=validated_request.command_proposal_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        classification=ShellDryRunClass.no_effect_review,
        sandboxed_echo_noop_allowed=active_policy.sandboxed_echo_noop_enabled,
        in_process_only=active_policy.in_process_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_echo_text=validated_request.safe_echo_text,
        reason_codes=[
            "M84_SANDBOXED_ECHO_NOOP_COMMAND_ONLY",
            "M84_IN_PROCESS_ONLY",
            "M84_NO_SHELL_OR_SUBPROCESS_EXECUTION",
            "M85_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M84 completes an in-process sandboxed echo/no-op command for human "
            "review with safe metadata only. It does not execute shell commands, "
            "start subprocesses, spawn processes, mutate files, access networks, "
            "execute tools, automate browsers, call models, write memory, inject "
            "context, add routes, add Control Center controls, add dependencies, "
            "or grant production authority."
        ),
        receipt_plan=SandboxedEchoNoOpCommandReceiptPlan(
            receipt_plan_ref=(
                f"sandboxed-echo-noop-command-receipt-plan:{_ref_suffix(validated_request.sandboxed_command_ref)}"
            ),
            sandboxed_command_ref=validated_request.sandboxed_command_ref,
            shell_dry_run_decision_ref=validated_request.shell_dry_run_decision_ref,
            command_proposal_ref=validated_request.command_proposal_ref,
        ),
    )
    return validate_sandboxed_echo_noop_command_decision(decision)


def validate_sandboxed_echo_noop_command_policy(
    policy: SandboxedEchoNoOpCommandPolicy,
) -> SandboxedEchoNoOpCommandPolicy:
    validated = SandboxedEchoNoOpCommandPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M84_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M84_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED") from exc
    return validated


def validate_sandboxed_echo_noop_command_request(
    request: SandboxedEchoNoOpCommandRequest,
) -> SandboxedEchoNoOpCommandRequest:
    payload = _model_payload(request)
    for field_name, reason in _M84_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = SandboxedEchoNoOpCommandRequest.model_validate(payload)
    for field_name, reason in _M84_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M84_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.sandboxed_echo_noop_requested:
        raise ValueError("SANDBOXED_ECHO_NOOP_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M84_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_shell_dry_run_binding(validated)
    try:
        _validate_safe_payload(validated.safe_echo_text)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED") from exc
    return validated


def validate_sandboxed_echo_noop_command_decision(
    decision: SandboxedEchoNoOpCommandDecision,
) -> SandboxedEchoNoOpCommandDecision:
    validated = SandboxedEchoNoOpCommandDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M84_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M84_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != SandboxedEchoNoOpCommandStatus.completed_for_review:
        raise ValueError("M84_SANDBOXED_ECHO_NOOP_STATUS_REQUIRED")
    if validated.classification != ShellDryRunClass.no_effect_review:
        raise ValueError("M84_NO_EFFECT_CLASSIFICATION_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M84_SIDE_EFFECTS_DENIED")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M84_RECEIPT_SAFE_SUMMARY_REQUIRED")
    for field_name, reason in _M84_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M84_SIDE_EFFECTS_DENIED")
    if validated.receipt_plan.sandboxed_command_ref != validated.sandboxed_command_ref:
        raise ValueError("M84_RECEIPT_BINDING_MISMATCH")
    if validated.receipt_plan.shell_dry_run_decision_ref != validated.shell_dry_run_decision_ref:
        raise ValueError("M84_RECEIPT_BINDING_MISMATCH")
    if validated.receipt_plan.command_proposal_ref != validated.command_proposal_ref:
        raise ValueError("M84_RECEIPT_BINDING_MISMATCH")
    try:
        _validate_safe_payload(validated.safe_echo_text)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED") from exc
    return validated


def _validate_shell_dry_run_binding(request: SandboxedEchoNoOpCommandRequest) -> None:
    classification = validate_shell_dry_run_classifier_decision(
        request.shell_dry_run_classification
    )
    if classification.status != ShellDryRunClassificationStatus.classified_for_review:
        raise ValueError("M84_SHELL_DRY_RUN_STATUS_REQUIRED")
    if classification.classification != ShellDryRunClass.no_effect_review:
        raise ValueError("M84_NO_EFFECT_CLASSIFICATION_REQUIRED")
    if request.shell_dry_run_classifier_ref != classification.classifier_ref:
        raise ValueError("M84_SHELL_DRY_RUN_BINDING_MISMATCH")
    if request.shell_dry_run_decision_ref != classification.decision_ref:
        raise ValueError("M84_SHELL_DRY_RUN_BINDING_MISMATCH")
    if request.command_proposal_ref != classification.command_proposal_ref:
        raise ValueError("M84_COMMAND_PROPOSAL_BINDING_MISMATCH")
    if request.sandbox_spec_ref != classification.sandbox_spec_ref:
        raise ValueError("M84_SANDBOX_SPEC_BINDING_MISMATCH")
    if request.actor_ref != classification.actor_ref:
        raise ValueError("M84_ACTOR_BINDING_MISMATCH")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M84_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M84_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M84_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M84_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M84_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M84_PRIOR_MILESTONE_REF_UNEXPECTED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M84_REQUIRED_TRUE = [
    ("in_process_only", "IN_PROCESS_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_SANDBOXED_ECHO_NOOP_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
]


_M84_POLICY_DENIALS = [
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


_M84_REQUEST_DENIALS = [
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
    ("contains_shell_string", "M84_SHELL_STRING_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED"),
]


_M84_DECISION_DENIALS = [
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


_M84_RECEIPT_DENIALS = [
    ("store_raw_command", "M84_RECEIPT_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M84_RECEIPT_SHELL_STRING_DENIED"),
    ("store_raw_output", "M84_RECEIPT_RAW_OUTPUT_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("store_secret", "SECRET_LIKE_SANDBOXED_ECHO_NOOP_CONTENT_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
]
