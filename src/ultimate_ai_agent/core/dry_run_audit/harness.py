import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M58_DOC_REFS = [
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md",
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md",
    "docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/dry_run_audit/M58_TO_M59_BOUNDARY.md",
]
M58_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class DryRunExecutionAuditStatus(str, Enum):
    reviewed = "reviewed"
    denied = "denied"


class _M58DryRunAuditModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class DryRunExecutionAuditPolicy(_M58DryRunAuditModel):
    policy_ref: str = "dry-run-execution-audit-policy:m58"
    baseline_version: str = "0.62.0"
    dry_run_only: bool = True
    contract_only: bool = True
    local_only: bool = True
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    process_spawn_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    side_effects_enabled: bool = False
    production_authority_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    m59_public_readiness_enabled: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M58_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M58", "version:v0.62.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self) -> Any:
        _validate_m58_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m58_ref(ref, "metadata_ref")
        return self


class DryRunExecutionAuditIntent(_M58DryRunAuditModel):
    intent_ref: str
    operation_ref: str
    target_ref: str
    requested_capability_refs: list[str]
    safe_summary: str
    execution_requested: bool = False
    tool_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    shell_execution_requested: bool = False
    process_spawn_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    remote_execution_requested: bool = False
    side_effects_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_intent_shape(self) -> Any:
        for value, field_name in [
            (self.intent_ref, "intent_ref"),
            (self.operation_ref, "operation_ref"),
            (self.target_ref, "target_ref"),
        ]:
            _validate_m58_ref(value, field_name)
        if not self.requested_capability_refs:
            raise ValueError("DRY_RUN_CAPABILITY_REFS_REQUIRED")
        for ref in self.requested_capability_refs:
            _validate_m58_ref(ref, "requested_capability_ref")
        for ref in self.metadata_refs:
            _validate_m58_ref(ref, "metadata_ref")
        _require_nonempty(self.safe_summary, "safe_summary")
        return self


class DryRunExecutionAuditRequest(_M58DryRunAuditModel):
    request_ref: str
    audit_ref: str
    sandbox_review_ref: str
    intent_refs: list[str]
    intents: list[DryRunExecutionAuditIntent]
    actor_ref: str
    replay_key_ref: str
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.audit_ref, "audit_ref"),
            (self.sandbox_review_ref, "sandbox_review_ref"),
            (self.actor_ref, "actor_ref"),
            (self.replay_key_ref, "replay_key_ref"),
        ]:
            _validate_m58_ref(value, field_name)
        if not self.intent_refs:
            raise ValueError("DRY_RUN_INTENT_REFS_REQUIRED")
        if not self.intents:
            raise ValueError("DRY_RUN_INTENT_MISSING")
        for ref in self.intent_refs:
            _validate_m58_ref(ref, "intent_ref")
        for ref in self.metadata_refs:
            _validate_m58_ref(ref, "metadata_ref")
        return self


class DryRunExecutionAuditEntry(_M58DryRunAuditModel):
    intent_ref: str
    operation_ref: str
    target_ref: str
    dry_run_only: bool = True
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_entry(self) -> Any:
        for value, field_name in [
            (self.intent_ref, "intent_ref"),
            (self.operation_ref, "operation_ref"),
            (self.target_ref, "target_ref"),
        ]:
            _validate_m58_ref(value, field_name)
        if not self.dry_run_only:
            raise ValueError("DRY_RUN_ONLY_REQUIRED")
        if self.execution_performed:
            raise ValueError("EXECUTION_DENIED")
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        for reason in self.reason_codes:
            _require_nonempty(reason, "reason_code")
        _validate_safe_payload(self.safe_summary)
        return self


class DryRunExecutionAuditReceiptPlan(_M58DryRunAuditModel):
    receipt_plan_ref: str
    audit_ref: str
    dry_run_only: bool = True
    audit_recorded: bool = True
    execution_performed: bool = False
    tool_execution_performed: bool = False
    subprocess_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M58 dry-run execution audit receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> Any:
        _validate_m58_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m58_ref(self.audit_ref, "audit_ref")
        if not self.dry_run_only:
            raise ValueError("DRY_RUN_ONLY_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


class DryRunExecutionAuditReport(_M58DryRunAuditModel):
    report_ref: str
    request_ref: str
    audit_ref: str
    sandbox_review_ref: str
    actor_ref: str
    replay_key_ref: str
    status: DryRunExecutionAuditStatus
    dry_run_only: bool = True
    entries: list[DryRunExecutionAuditEntry]
    receipt_plan: DryRunExecutionAuditReceiptPlan | None = None
    execution_performed: bool = False
    tool_execution_performed: bool = False
    subprocess_performed: bool = False
    shell_execution_performed: bool = False
    process_spawn_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=lambda: list(M58_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M58", "version:v0.62.0"])

    @model_validator(mode="after")
    def validate_report(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.request_ref, "request_ref"),
            (self.audit_ref, "audit_ref"),
            (self.sandbox_review_ref, "sandbox_review_ref"),
            (self.actor_ref, "actor_ref"),
            (self.replay_key_ref, "replay_key_ref"),
        ]:
            _validate_m58_ref(value, field_name)
        if not self.dry_run_only:
            raise ValueError("DRY_RUN_ONLY_REQUIRED")
        if not self.entries:
            raise ValueError("DRY_RUN_AUDIT_ENTRIES_REQUIRED")
        for field_name, reason in _PERFORMED_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        return self


def validate_dry_run_execution_audit_policy(
    policy: DryRunExecutionAuditPolicy,
) -> DryRunExecutionAuditPolicy:
    validated = DryRunExecutionAuditPolicy.model_validate(policy.model_dump())
    _validate_safe_payload(validated.metadata)
    if not validated.dry_run_only or not validated.contract_only or not validated.local_only:
        raise ValueError("DRY_RUN_ONLY_REQUIRED")
    for field_name, reason in _ENABLED_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_dry_run_execution_audit_request(
    request: DryRunExecutionAuditRequest,
) -> DryRunExecutionAuditRequest:
    validated = DryRunExecutionAuditRequest.model_validate(request.model_dump())
    _validate_safe_payload(validated.metadata)
    if len(set(validated.intent_refs)) != len(validated.intent_refs):
        raise ValueError("DRY_RUN_INTENT_REF_DUPLICATE")
    intents_by_ref = {intent.intent_ref: intent for intent in validated.intents}
    if len(intents_by_ref) != len(validated.intents):
        raise ValueError("DRY_RUN_INTENT_REF_DUPLICATE")
    for ref in validated.intent_refs:
        if ref not in intents_by_ref:
            raise ValueError("DRY_RUN_INTENT_MISSING")
    for intent in validated.intents:
        _validate_safe_payload(intent.safe_summary)
        _validate_safe_payload(intent.metadata)
        for field_name, reason in _REQUESTED_DENIALS:
            if getattr(intent, field_name):
                raise ValueError(reason)
    return validated


def build_dry_run_execution_audit_report(
    request: DryRunExecutionAuditRequest,
    policy: DryRunExecutionAuditPolicy | None = None,
) -> DryRunExecutionAuditReport:
    validate_dry_run_execution_audit_policy(policy or DryRunExecutionAuditPolicy())
    active_request = validate_dry_run_execution_audit_request(request)
    intents_by_ref = {intent.intent_ref: intent for intent in active_request.intents}
    entries = [
        DryRunExecutionAuditEntry(
            intent_ref=intent_ref,
            operation_ref=intents_by_ref[intent_ref].operation_ref,
            target_ref=intents_by_ref[intent_ref].target_ref,
            reason_codes=["M58_DRY_RUN_AUDIT_ONLY"],
            safe_summary="Dry-run audit recorded declared intent without execution.",
        )
        for intent_ref in active_request.intent_refs
    ]
    return DryRunExecutionAuditReport(
        report_ref=f"dry-run-audit-report:{_ref_suffix(active_request.audit_ref)}",
        request_ref=active_request.request_ref,
        audit_ref=active_request.audit_ref,
        sandbox_review_ref=active_request.sandbox_review_ref,
        actor_ref=active_request.actor_ref,
        replay_key_ref=active_request.replay_key_ref,
        status=DryRunExecutionAuditStatus.reviewed,
        entries=entries,
        receipt_plan=DryRunExecutionAuditReceiptPlan(
            receipt_plan_ref=f"dry-run-audit-receipt:{_ref_suffix(active_request.audit_ref)}",
            audit_ref=active_request.audit_ref,
            safe_summary="M58 records dry-run audit metadata only; no execution is performed.",
        ),
        metadata_refs=[
            active_request.request_ref,
            active_request.audit_ref,
            active_request.sandbox_review_ref,
            active_request.replay_key_ref,
        ],
    )


_ENABLED_DENIALS = [
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_enabled", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("side_effects_enabled", "SIDE_EFFECTS_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
    ("m59_public_readiness_enabled", "M59_PUBLIC_READINESS_DENIED"),
]

_REQUESTED_DENIALS = [
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("subprocess_execution_requested", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_requested", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_requested", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_requested", "NETWORK_ACCESS_DENIED"),
    ("model_call_requested", "MODEL_CALL_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("side_effects_requested", "SIDE_EFFECTS_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
    ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ("contains_secret", "SECRET_LIKE_DRY_RUN_AUDIT_CONTENT_DENIED"),
]

_PERFORMED_DENIALS = [
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("subprocess_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("process_spawn_performed", "PROCESS_SPAWN_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
]


def _validate_m58_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M58_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_payload(value: Any) -> None:
    try:
        validate_safe_tool_payload(value, "dry_run_audit_content")
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_DRY_RUN_AUDIT_CONTENT_DENIED") from exc


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1]
