import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M57_DOC_REFS = [
    "docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md",
    "docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md",
    "docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md",
    "docs/sandbox/M57_TO_M58_BOUNDARY.md",
]
M57_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class RuntimeSandboxArchitectureStatus(str, Enum):
    reviewed = "reviewed"
    denied = "denied"


class _M57SandboxModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RuntimeSandboxArchitecturePolicy(_M57SandboxModel):
    policy_ref: str = "runtime-sandbox-architecture-policy:m57"
    baseline_version: str = "0.61.0"
    architecture_review_only: bool = True
    contract_only: bool = True
    local_only: bool = True
    sandbox_runtime_enabled: bool = False
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
    side_effects_enabled: bool = False
    production_authority_enabled: bool = False
    m58_dry_run_harness_enabled: bool = False
    dependencies_added: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M57_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M57", "version:v0.61.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self):
        _validate_m57_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m57_ref(ref, "metadata_ref")
        return self


class RuntimeSandboxArchitectureRequest(_M57SandboxModel):
    request_ref: str
    review_ref: str
    architecture_ref: str
    boundary_refs: list[str]
    threat_model_refs: list[str]
    audit_requirement_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    sandbox_runtime_requested: bool = False
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
    side_effects_requested: bool = False
    production_authority_requested: bool = False
    m58_dry_run_harness_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.review_ref, "review_ref"),
            (self.architecture_ref, "architecture_ref"),
        ]:
            _validate_m57_ref(value, field_name)
        if not self.boundary_refs:
            raise ValueError("SANDBOX_BOUNDARY_REFS_REQUIRED")
        if not self.threat_model_refs:
            raise ValueError("SANDBOX_THREAT_MODEL_REFS_REQUIRED")
        for ref in self.boundary_refs:
            _validate_m57_ref(ref, "boundary_ref")
        for ref in self.threat_model_refs:
            _validate_m57_ref(ref, "threat_model_ref")
        for ref in self.audit_requirement_refs:
            _validate_m57_ref(ref, "audit_requirement_ref")
        for ref in self.metadata_refs:
            _validate_m57_ref(ref, "metadata_ref")
        _require_nonempty(self.safe_summary, "safe_summary")
        return self


class RuntimeSandboxArchitectureReceiptPlan(_M57SandboxModel):
    receipt_plan_ref: str
    review_ref: str
    architecture_review_only: bool = True
    runtime_sandbox_enabled: bool = False
    execution_performed: bool = False
    subprocess_performed: bool = False
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
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M57 runtime sandbox architecture review receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self):
        _validate_m57_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m57_ref(self.review_ref, "review_ref")
        if not self.architecture_review_only:
            raise ValueError("M57_ARCHITECTURE_REVIEW_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


class RuntimeSandboxArchitectureDecision(_M57SandboxModel):
    review_ref: str
    request_ref: str
    architecture_ref: str
    status: RuntimeSandboxArchitectureStatus
    architecture_review_only: bool = True
    runtime_sandbox_enabled: bool = False
    boundary_refs: list[str]
    threat_model_refs: list[str]
    audit_requirement_refs: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    receipt_plan: RuntimeSandboxArchitectureReceiptPlan | None = None
    execution_performed: bool = False
    subprocess_performed: bool = False
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
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=lambda: list(M57_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M57", "version:v0.61.0"])

    @model_validator(mode="after")
    def validate_decision(self):
        for value, field_name in [
            (self.review_ref, "review_ref"),
            (self.request_ref, "request_ref"),
            (self.architecture_ref, "architecture_ref"),
        ]:
            _validate_m57_ref(value, field_name)
        if not self.architecture_review_only:
            raise ValueError("M57_ARCHITECTURE_REVIEW_ONLY_REQUIRED")
        for ref in self.boundary_refs:
            _validate_m57_ref(ref, "boundary_ref")
        for ref in self.threat_model_refs:
            _validate_m57_ref(ref, "threat_model_ref")
        for ref in self.audit_requirement_refs:
            _validate_m57_ref(ref, "audit_requirement_ref")
        for reason in self.reason_codes:
            _require_nonempty(reason, "reason_code")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        return self


def validate_runtime_sandbox_architecture_policy(
    policy: RuntimeSandboxArchitecturePolicy,
) -> RuntimeSandboxArchitecturePolicy:
    validated = RuntimeSandboxArchitecturePolicy.model_validate(policy.model_dump())
    _validate_safe_payload(validated.metadata)
    if not validated.architecture_review_only or not validated.contract_only or not validated.local_only:
        raise ValueError("M57_ARCHITECTURE_REVIEW_ONLY_REQUIRED")
    for field_name, reason in _ENABLED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_runtime_sandbox_architecture_request(
    request: RuntimeSandboxArchitectureRequest,
) -> RuntimeSandboxArchitectureRequest:
    validated = RuntimeSandboxArchitectureRequest.model_validate(request.model_dump())
    _validate_safe_payload(validated.safe_summary)
    _validate_safe_payload(validated.metadata)
    for field_name, reason in _REQUESTED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_runtime_sandbox_architecture_review(
    request: RuntimeSandboxArchitectureRequest,
    policy: RuntimeSandboxArchitecturePolicy | None = None,
) -> RuntimeSandboxArchitectureDecision:
    active_policy = validate_runtime_sandbox_architecture_policy(
        policy or RuntimeSandboxArchitecturePolicy()
    )
    active_request = validate_runtime_sandbox_architecture_request(request)
    return RuntimeSandboxArchitectureDecision(
        review_ref=active_request.review_ref,
        request_ref=active_request.request_ref,
        architecture_ref=active_request.architecture_ref,
        status=RuntimeSandboxArchitectureStatus.reviewed,
        boundary_refs=list(dict.fromkeys(active_request.boundary_refs)),
        threat_model_refs=list(dict.fromkeys(active_request.threat_model_refs)),
        audit_requirement_refs=list(dict.fromkeys(active_request.audit_requirement_refs)),
        reason_codes=["M57_RUNTIME_SANDBOX_ARCHITECTURE_REVIEW_ONLY"],
        receipt_plan=RuntimeSandboxArchitectureReceiptPlan(
            receipt_plan_ref=f"sandbox-architecture-receipt:{_ref_suffix(active_request.review_ref)}",
            review_ref=active_request.review_ref,
            safe_summary="M57 records architecture review metadata only; no runtime sandbox is executed.",
        ),
        metadata_refs=[
            *active_policy.metadata_refs,
            active_request.request_ref,
            active_request.review_ref,
        ],
    )


_ENABLED_DENIALS = [
    ("sandbox_runtime_enabled", "SANDBOX_RUNTIME_DENIED"),
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
    ("side_effects_enabled", "SIDE_EFFECTS_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("m58_dry_run_harness_enabled", "M58_DRY_RUN_HARNESS_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
]

_REQUESTED_DENIALS = [
    ("sandbox_runtime_requested", "SANDBOX_RUNTIME_DENIED"),
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
    ("side_effects_requested", "SIDE_EFFECTS_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ("m58_dry_run_harness_requested", "M58_DRY_RUN_HARNESS_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_SANDBOX_METADATA_DENIED"),
]

_PERFORMED_DENIALS = [
    ("runtime_sandbox_enabled", "SANDBOX_RUNTIME_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("subprocess_performed", "SUBPROCESS_EXECUTION_DENIED"),
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
]


def _validate_m57_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M57_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_payload(value: Any) -> None:
    try:
        validate_safe_tool_payload(value, "sandbox_metadata")
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_SANDBOX_METADATA_DENIED") from exc


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1]
