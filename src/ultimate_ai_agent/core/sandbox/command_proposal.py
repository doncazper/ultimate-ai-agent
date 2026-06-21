from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


COMMAND_PROPOSAL_DOCS = [
    "docs/sandbox/COMMAND_PROPOSAL_CONTRACTS.md",
    "docs/sandbox/COMMAND_PROPOSAL_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/COMMAND_PROPOSAL_RECEIPT_PLAN.md",
    "docs/sandbox/COMMAND_PROPOSAL_NON_GOALS.md",
    "docs/sandbox/M82_TO_M83_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M82_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
)


class CommandProposalStatus(str, Enum):
    proposed_for_review = "proposed_for_review"


class CommandProposalEffect(str, Enum):
    no_effect = "no_effect"


class _CommandProposalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CommandProposalPolicy(_CommandProposalModel):
    policy_ref: str = "command-proposal-policy:m82"
    proposal_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    structured_args_only: bool = True
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


class CommandProposalRequest(_CommandProposalModel):
    request_ref: str
    proposal_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    prior_milestone_refs: list[str]
    command_ref: str
    safe_purpose: str
    safe_command_label: str
    argv_preview: list[str]
    expected_effect: CommandProposalEffect = CommandProposalEffect.no_effect
    proposal_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    structured_args_only: bool = True
    execution_requested: bool = False
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
            (self.proposal_ref, "proposal_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.command_ref, "command_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_purpose)
        _validate_safe_payload(self.safe_command_label)
        return self


class CommandProposalReceiptPlan(_CommandProposalModel):
    receipt_plan_ref: str
    proposal_ref: str
    store_safe_summary_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M82 command proposal receipt stores safe metadata only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m61_ref(self.proposal_ref, "proposal_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class CommandProposalDecision(_CommandProposalModel):
    decision_ref: str
    proposal_ref: str
    request_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    command_ref: str
    status: CommandProposalStatus = CommandProposalStatus.proposed_for_review
    expected_effect: CommandProposalEffect = CommandProposalEffect.no_effect
    proposal_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    structured_args_only: bool = True
    execution_authorized: bool = False
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
    receipt_plan: CommandProposalReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.proposal_ref, "proposal_ref"),
            (self.request_ref, "request_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.command_ref, "command_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_command_proposal(
    request: CommandProposalRequest,
    policy: CommandProposalPolicy | None = None,
) -> CommandProposalDecision:
    active_policy = validate_command_proposal_policy(policy or CommandProposalPolicy())
    validated_request = validate_command_proposal_request(request)
    decision = CommandProposalDecision(
        decision_ref=f"command-proposal-decision:{_ref_suffix(validated_request.proposal_ref)}",
        proposal_ref=validated_request.proposal_ref,
        request_ref=validated_request.request_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        command_ref=validated_request.command_ref,
        expected_effect=validated_request.expected_effect,
        proposal_only=active_policy.proposal_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        structured_args_only=active_policy.structured_args_only,
        side_effects_performed=[],
        reason_codes=[
            "M82_COMMAND_PROPOSAL_CONTRACT_ONLY",
            "M82_NO_COMMAND_EXECUTION",
            "M83_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M82 creates a structured command proposal decision for review only. "
            "It does not execute commands, start subprocesses, use shell execution, "
            "spawn processes, mutate files, access networks, execute tools, automate "
            "browsers, call models, write memory, inject context, add routes, add "
            "Control Center controls, add dependencies, or grant production authority."
        ),
        receipt_plan=CommandProposalReceiptPlan(
            receipt_plan_ref=f"command-proposal-receipt-plan:{_ref_suffix(validated_request.proposal_ref)}",
            proposal_ref=validated_request.proposal_ref,
        ),
    )
    return validate_command_proposal_decision(decision)


def validate_command_proposal_policy(policy: CommandProposalPolicy) -> CommandProposalPolicy:
    validated = CommandProposalPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M82_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M82_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def validate_command_proposal_request(request: CommandProposalRequest) -> CommandProposalRequest:
    payload = _model_payload(request)
    for field_name, reason in _M82_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, CommandProposalRequest):
        raise ValueError("SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED")
    validated = CommandProposalRequest.model_validate(payload)
    for field_name, reason in _M82_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M82_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.expected_effect != CommandProposalEffect.no_effect:
        raise ValueError("M82_NO_EFFECT_COMMAND_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M82_SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_argv_preview(validated.argv_preview)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def validate_command_proposal_decision(
    decision: CommandProposalDecision,
) -> CommandProposalDecision:
    validated = CommandProposalDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M82_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M82_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != CommandProposalStatus.proposed_for_review:
        raise ValueError("M82_COMMAND_PROPOSAL_STATUS_REQUIRED")
    if validated.expected_effect != CommandProposalEffect.no_effect:
        raise ValueError("M82_NO_EFFECT_COMMAND_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M82_SIDE_EFFECTS_DENIED")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M82_RECEIPT_SAFE_SUMMARY_REQUIRED")
    for field_name, reason in _M82_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M82_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED") from exc
    return validated


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M82_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M82_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M82_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M82_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M82_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M82_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_argv_preview(argv_preview: list[str]) -> None:
    if not argv_preview:
        raise ValueError("M82_ARGV_PREVIEW_REQUIRED")
    if len(argv_preview) > 16:
        raise ValueError("M82_ARGV_PREVIEW_TOO_LONG")
    for token in argv_preview:
        if not token or not isinstance(token, str):
            raise ValueError("M82_ARGV_TOKEN_REQUIRED")
        if token.startswith(("/", "~")) or token.startswith("\\"):
            raise ValueError("M82_RAW_OR_ABSOLUTE_PATH_DENIED")
        if any(fragment in token for fragment in _SHELL_FRAGMENTS):
            raise ValueError("M82_SHELL_STRING_DENIED")
        _validate_safe_payload(token)


def _has_secret_like_extra(payload: dict[str, Any], model_type: type[BaseModel]) -> bool:
    allowed_fields = set(model_type.model_fields)
    extra_payload = {key: value for key, value in payload.items() if key not in allowed_fields}
    if not extra_payload:
        return False
    try:
        _validate_safe_payload(extra_payload)
    except ValueError:
        return True
    return False


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_SHELL_FRAGMENTS = ("&&", "||", ";", "|", "$(", "`", ">", "<", "\n", "\r")


_M82_REQUIRED_TRUE = [
    ("proposal_only", "PROPOSAL_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_PROPOSAL_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
    ("structured_args_only", "STRUCTURED_ARGS_ONLY_REQUIRED"),
]


_M82_POLICY_DENIALS = [
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


_M82_REQUEST_DENIALS = [
    ("execution_requested", "EXECUTION_REQUEST_DENIED"),
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
    ("contains_shell_string", "M82_SHELL_STRING_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED"),
]


_M82_DECISION_DENIALS = [
    ("execution_authorized", "EXECUTION_AUTHORITY_DENIED"),
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


_M82_RECEIPT_DENIALS = [
    ("store_raw_command", "M82_RECEIPT_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M82_RECEIPT_SHELL_STRING_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("store_secret", "SECRET_LIKE_COMMAND_PROPOSAL_CONTENT_DENIED"),
]
