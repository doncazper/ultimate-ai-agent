from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.sandbox.command_proposal import (
    CommandProposalDecision,
    CommandProposalStatus,
    validate_command_proposal_decision,
)
from ultimate_ai_agent.core.sandbox.runtime_spec import _model_payload


SHELL_DRY_RUN_CLASSIFIER_DOCS = [
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_POLICY.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_RECEIPT_PLAN.md",
    "docs/sandbox/SHELL_DRY_RUN_CLASSIFIER_NON_GOALS.md",
    "docs/sandbox/M83_TO_M84_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M83_PRIOR_MILESTONE_REFS = (
    "milestone:M57",
    "milestone:M58",
    "milestone:M80",
    "milestone:M81",
    "milestone:M82",
)


class ShellDryRunClassificationStatus(str, Enum):
    classified_for_review = "classified_for_review"


class ShellDryRunClass(str, Enum):
    no_effect_review = "no_effect_review"
    read_only_candidate = "read_only_candidate"
    mutating_candidate_future = "mutating_candidate_future"
    unsupported_future = "unsupported_future"


class _ShellDryRunClassifierModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ShellDryRunClassifierPolicy(_ShellDryRunClassifierModel):
    policy_ref: str = "shell-dry-run-classifier-policy:m83"
    classifier_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    dry_run_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    process_spawn_enabled: bool = False
    command_execution_enabled: bool = False
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


class ShellDryRunClassifierRequest(_ShellDryRunClassifierModel):
    request_ref: str
    classifier_ref: str
    command_proposal_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    prior_milestone_refs: list[str]
    command_proposal: CommandProposalDecision
    classifier_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    dry_run_execution_requested: bool = False
    shell_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    process_spawn_requested: bool = False
    command_execution_requested: bool = False
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
    safe_summary: str = "Classify a shell dry-run candidate for human review only."
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.classifier_ref, "classifier_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class ShellDryRunClassifierReceiptPlan(_ShellDryRunClassifierModel):
    receipt_plan_ref: str
    classifier_ref: str
    command_proposal_ref: str
    store_safe_summary_only: bool = True
    store_raw_command: bool = False
    store_shell_string: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    dry_run_execution_performed: bool = False
    shell_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    process_spawn_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M83 shell dry-run classifier receipt stores safe metadata only."

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m61_ref(self.classifier_ref, "classifier_ref")
        _validate_m61_ref(self.command_proposal_ref, "command_proposal_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class ShellDryRunClassifierDecision(_ShellDryRunClassifierModel):
    decision_ref: str
    classifier_ref: str
    request_ref: str
    command_proposal_ref: str
    sandbox_spec_ref: str
    baseline_ref: str
    actor_ref: str
    status: ShellDryRunClassificationStatus = ShellDryRunClassificationStatus.classified_for_review
    classification: ShellDryRunClass
    classifier_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    dry_run_classification_allowed: bool = True
    dry_run_execution_authorized: bool = False
    command_execution_authorized: bool = False
    shell_execution_authorized: bool = False
    subprocess_execution_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    command_execution_performed: bool = False
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
    receipt_plan: ShellDryRunClassifierReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.classifier_ref, "classifier_ref"),
            (self.request_ref, "request_ref"),
            (self.command_proposal_ref, "command_proposal_ref"),
            (self.sandbox_spec_ref, "sandbox_spec_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_shell_dry_run_classification(
    request: ShellDryRunClassifierRequest,
    policy: ShellDryRunClassifierPolicy | None = None,
) -> ShellDryRunClassifierDecision:
    active_policy = validate_shell_dry_run_classifier_policy(
        policy or ShellDryRunClassifierPolicy()
    )
    validated_request = validate_shell_dry_run_classifier_request(request)
    classification = _classify_command_proposal(validated_request.command_proposal)
    decision = ShellDryRunClassifierDecision(
        decision_ref=f"shell-dry-run-classifier-decision:{_ref_suffix(validated_request.classifier_ref)}",
        classifier_ref=validated_request.classifier_ref,
        request_ref=validated_request.request_ref,
        command_proposal_ref=validated_request.command_proposal_ref,
        sandbox_spec_ref=validated_request.sandbox_spec_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        classification=classification,
        classifier_only=active_policy.classifier_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        reason_codes=[
            "M83_SHELL_DRY_RUN_CLASSIFIER_CONTRACT_ONLY",
            "M83_NO_SHELL_EXECUTION",
            "M84_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M83 classifies an already validated command proposal for human "
            "review only. It does not execute commands, perform shell dry runs, "
            "start subprocesses, spawn processes, mutate files, access networks, "
            "execute tools, automate browsers, call models, write memory, inject "
            "context, add routes, add Control Center controls, add dependencies, "
            "or grant production authority."
        ),
        receipt_plan=ShellDryRunClassifierReceiptPlan(
            receipt_plan_ref=(
                f"shell-dry-run-classifier-receipt-plan:{_ref_suffix(validated_request.classifier_ref)}"
            ),
            classifier_ref=validated_request.classifier_ref,
            command_proposal_ref=validated_request.command_proposal_ref,
        ),
    )
    return validate_shell_dry_run_classifier_decision(decision)


def validate_shell_dry_run_classifier_policy(
    policy: ShellDryRunClassifierPolicy,
) -> ShellDryRunClassifierPolicy:
    validated = ShellDryRunClassifierPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M83_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M83_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED") from exc
    return validated


def validate_shell_dry_run_classifier_request(
    request: ShellDryRunClassifierRequest,
) -> ShellDryRunClassifierRequest:
    payload = _model_payload(request)
    for field_name, reason in _M83_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ShellDryRunClassifierRequest.model_validate(payload)
    for field_name, reason in _M83_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M83_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M83_SIDE_EFFECTS_DENIED")
    if validated.command_proposal_ref != validated.command_proposal.proposal_ref:
        raise ValueError("M83_COMMAND_PROPOSAL_BINDING_MISMATCH")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    validate_command_proposal_decision(validated.command_proposal)
    try:
        _validate_safe_payload(validated.safe_summary)
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED") from exc
    return validated


def validate_shell_dry_run_classifier_decision(
    decision: ShellDryRunClassifierDecision,
) -> ShellDryRunClassifierDecision:
    validated = ShellDryRunClassifierDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M83_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M83_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ShellDryRunClassificationStatus.classified_for_review:
        raise ValueError("M83_CLASSIFICATION_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M83_SIDE_EFFECTS_DENIED")
    if not validated.receipt_plan.store_safe_summary_only:
        raise ValueError("M83_RECEIPT_SAFE_SUMMARY_REQUIRED")
    for field_name, reason in _M83_RECEIPT_DENIALS:
        if getattr(validated.receipt_plan, field_name):
            raise ValueError(reason)
    if validated.receipt_plan.side_effects_performed:
        raise ValueError("M83_SIDE_EFFECTS_DENIED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED") from exc
    return validated


def _classify_command_proposal(proposal: CommandProposalDecision) -> ShellDryRunClass:
    validated = validate_command_proposal_decision(proposal)
    if validated.status != CommandProposalStatus.proposed_for_review:
        raise ValueError("M83_COMMAND_PROPOSAL_STATUS_REQUIRED")
    classifier_hint = f"{validated.command_ref} {validated.proposal_ref}".lower()
    if any(fragment in classifier_hint for fragment in ("write", "delete", "mutate", "move", "chmod")):
        return ShellDryRunClass.mutating_candidate_future
    if any(fragment in classifier_hint for fragment in ("read", "list", "inspect", "metadata")):
        return ShellDryRunClass.read_only_candidate
    return ShellDryRunClass.no_effect_review


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M83_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M83_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M83_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M83_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M83_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M83_PRIOR_MILESTONE_REF_UNEXPECTED")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_M83_REQUIRED_TRUE = [
    ("classifier_only", "CLASSIFIER_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_CLASSIFIER_REQUIRED"),
    ("local_only", "LOCAL_ONLY_REQUIRED"),
]


_M83_POLICY_DENIALS = [
    ("dry_run_execution_enabled", "DRY_RUN_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
    ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
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


_M83_REQUEST_DENIALS = [
    ("dry_run_execution_requested", "DRY_RUN_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
    ("command_execution_requested", "COMMAND_EXECUTION_DENIED"),
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
    ("contains_shell_string", "M83_SHELL_STRING_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED"),
]


_M83_DECISION_DENIALS = [
    ("dry_run_execution_authorized", "DRY_RUN_EXECUTION_DENIED"),
    ("command_execution_authorized", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_authorized", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
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


_M83_RECEIPT_DENIALS = [
    ("store_raw_command", "M83_RECEIPT_RAW_COMMAND_DENIED"),
    ("store_shell_string", "M83_RECEIPT_SHELL_STRING_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("store_secret", "SECRET_LIKE_SHELL_DRY_RUN_CLASSIFIER_CONTENT_DENIED"),
    ("dry_run_execution_performed", "DRY_RUN_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
]
