from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyRiskClass,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.risk import (
    AutonomyRiskClassificationDecision,
    validate_autonomy_risk_classification_decision,
)


LOW_RISK_AUTONOMOUS_DRY_RUN_DOCS = [
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN.md",
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_CONTRACTS.md",
    "docs/autonomy/LOW_RISK_AUTONOMOUS_DRY_RUN_NON_GOALS.md",
    "docs/autonomy/M69_TO_M70_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _LowRiskAutonomousDryRunModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LowRiskAutonomousDryRunStep(_LowRiskAutonomousDryRunModel):
    step_ref: str
    intent_ref: str
    capability_ref: str
    resource_ref: str
    risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    dry_run_outcome_ref: str
    review_only: bool = True
    dry_run_only: bool = True
    deterministic: bool = True
    authority_granted: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.step_ref, "step_ref"),
            (self.intent_ref, "intent_ref"),
            (self.capability_ref, "capability_ref"),
            (self.resource_ref, "resource_ref"),
            (self.dry_run_outcome_ref, "dry_run_outcome_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class LowRiskAutonomousDryRunRequest(_LowRiskAutonomousDryRunModel):
    dry_run_request_ref: str
    risk_decision: AutonomyRiskClassificationDecision
    risk_decision_ref: str
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    bundle_ref: str
    revocation_record_ref: str
    source_scope_ref: str
    audit_ref: str
    replay_ref: str
    steps: list[LowRiskAutonomousDryRunStep]
    review_only: bool = True
    dry_run_only: bool = True
    low_risk_only: bool = True
    deterministic: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    low_risk_dry_run_authority_granted: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    session_active: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_test_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_common_refs(
            self.dry_run_request_ref,
            self.risk_decision_ref,
            self.actor_ref,
            self.bundle_ref,
            self.revocation_record_ref,
            self.source_scope_ref,
            self.audit_ref,
            self.replay_ref,
        )
        _validate_ref_list(self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED")
        _validate_ref_list(self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED")
        _validate_ref_list(self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED")
        if not self.steps:
            raise ValueError("LOW_RISK_DRY_RUN_STEP_REQUIRED")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class LowRiskAutonomousDryRunRecord(_LowRiskAutonomousDryRunModel):
    record_ref: str
    dry_run_request: LowRiskAutonomousDryRunRequest
    dry_run_request_ref: str
    risk_decision_ref: str
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    bundle_ref: str
    revocation_record_ref: str
    source_scope_ref: str
    audit_ref: str
    replay_ref: str
    step_refs: list[str]
    derived_risk_class: AutonomyRiskClass
    dry_run_valid_for_review: bool = True
    review_only: bool = True
    dry_run_only: bool = True
    low_risk_only: bool = True
    deterministic: bool = True
    approval_refs_are_identifiers_only: bool = True
    authority_granted: bool = False
    low_risk_dry_run_authority_granted: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    session_active: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_test_ref: str | None = None
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_common_refs(
            self.record_ref,
            self.risk_decision_ref,
            self.actor_ref,
            self.bundle_ref,
            self.revocation_record_ref,
            self.source_scope_ref,
            self.audit_ref,
            self.replay_ref,
        )
        _validate_m61_ref(self.dry_run_request_ref, "dry_run_request_ref")
        _validate_ref_list(self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED")
        _validate_ref_list(self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED")
        _validate_ref_list(self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED")
        _validate_ref_list(self.step_refs, "step_ref", "LOW_RISK_DRY_RUN_STEP_REQUIRED")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


def build_low_risk_autonomous_dry_run_record(
    request: LowRiskAutonomousDryRunRequest,
) -> LowRiskAutonomousDryRunRecord:
    validated = validate_low_risk_autonomous_dry_run_request(request)
    return validate_low_risk_autonomous_dry_run_record(
        LowRiskAutonomousDryRunRecord(
            record_ref=f"low-risk-autonomous-dry-run-record:{_ref_suffix(validated.dry_run_request_ref)}",
            dry_run_request=validated,
            dry_run_request_ref=validated.dry_run_request_ref,
            risk_decision_ref=validated.risk_decision_ref,
            actor_ref=validated.actor_ref,
            resource_refs=list(validated.resource_refs),
            capability_refs=list(validated.capability_refs),
            allowlist_refs=list(validated.allowlist_refs),
            bundle_ref=validated.bundle_ref,
            revocation_record_ref=validated.revocation_record_ref,
            source_scope_ref=validated.source_scope_ref,
            audit_ref=validated.audit_ref,
            replay_ref=validated.replay_ref,
            step_refs=[step.step_ref for step in validated.steps],
            derived_risk_class=AutonomyRiskClass.low,
            dry_run_valid_for_review=True,
            review_only=True,
            dry_run_only=True,
            low_risk_only=True,
            deterministic=True,
            approval_refs_are_identifiers_only=True,
            authority_granted=False,
            low_risk_dry_run_authority_granted=False,
            execution_requested=False,
            execution_performed=False,
            side_effects_performed=[],
            reason_codes=[
                "M69_LOW_RISK_AUTONOMOUS_DRY_RUN_REVIEW_ONLY",
                "M69_LOW_RISK_ONLY",
                "M69_DRY_RUN_NO_AUTHORITY",
            ],
            safe_summary=(
                "M69 records a low-risk autonomous dry run for review only. It requires an exact-bound "
                "M68 low-risk classifier decision and performs no policy activation, session start, "
                "execution, tool use, memory write, context injection, model call, or side effect."
            ),
        )
    )


def validate_low_risk_autonomous_dry_run_step(
    step: LowRiskAutonomousDryRunStep,
) -> LowRiskAutonomousDryRunStep:
    validated = LowRiskAutonomousDryRunStep.model_validate(step.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED") from exc
    for field_name, reason in _DRY_RUN_STEP_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.risk_class != AutonomyRiskClass.low:
        raise ValueError("LOW_RISK_DRY_RUN_STEP_RISK_DENIED")
    for field_name, reason in _DRY_RUN_STEP_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    return validated


def validate_low_risk_autonomous_dry_run_request(
    request: LowRiskAutonomousDryRunRequest,
) -> LowRiskAutonomousDryRunRequest:
    validated = LowRiskAutonomousDryRunRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED") from exc
    try:
        risk_decision = validate_autonomy_risk_classification_decision(validated.risk_decision)
    except ValueError as exc:
        if "SECRET_LIKE" in str(exc):
            raise ValueError("SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED") from exc
        raise
    if risk_decision.derived_risk_class != AutonomyRiskClass.low:
        raise ValueError("LOW_RISK_DRY_RUN_RISK_CEILING_DENIED")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _DRY_RUN_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DRY_RUN_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    for step in validated.steps:
        validate_low_risk_autonomous_dry_run_step(step)
    _validate_request_bindings(validated, risk_decision)
    return validated


def validate_low_risk_autonomous_dry_run_record(
    record: LowRiskAutonomousDryRunRecord,
) -> LowRiskAutonomousDryRunRecord:
    validated = LowRiskAutonomousDryRunRecord.model_validate(record.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_LOW_RISK_DRY_RUN_CONTENT_DENIED") from exc
    request = validate_low_risk_autonomous_dry_run_request(validated.dry_run_request)
    if validated.derived_risk_class != AutonomyRiskClass.low:
        raise ValueError("LOW_RISK_DRY_RUN_RISK_CEILING_DENIED")
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _DRY_RUN_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DRY_RUN_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    _validate_record_bindings(validated, request)
    return validated


def _validate_request_bindings(
    request: LowRiskAutonomousDryRunRequest,
    risk_decision: AutonomyRiskClassificationDecision,
) -> None:
    if request.risk_decision_ref != risk_decision.decision_ref:
        raise ValueError("LOW_RISK_DRY_RUN_RISK_DECISION_BINDING_MISMATCH_DENIED")
    if request.actor_ref != risk_decision.actor_ref:
        raise ValueError("LOW_RISK_DRY_RUN_ACTOR_BINDING_MISMATCH_DENIED")
    if request.resource_refs != risk_decision.resource_refs:
        raise ValueError("LOW_RISK_DRY_RUN_RESOURCE_BINDING_MISMATCH_DENIED")
    if request.capability_refs != risk_decision.capability_refs:
        raise ValueError("LOW_RISK_DRY_RUN_CAPABILITY_BINDING_MISMATCH_DENIED")
    if request.allowlist_refs != risk_decision.allowlist_refs:
        raise ValueError("LOW_RISK_DRY_RUN_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if request.bundle_ref != risk_decision.bundle_ref:
        raise ValueError("LOW_RISK_DRY_RUN_BUNDLE_BINDING_MISMATCH_DENIED")
    if request.revocation_record_ref != risk_decision.revocation_record_ref:
        raise ValueError("LOW_RISK_DRY_RUN_REVOCATION_BINDING_MISMATCH_DENIED")
    if request.source_scope_ref != risk_decision.source_scope_ref:
        raise ValueError("LOW_RISK_DRY_RUN_SCOPE_BINDING_MISMATCH_DENIED")
    if request.audit_ref != risk_decision.audit_ref:
        raise ValueError("LOW_RISK_DRY_RUN_AUDIT_BINDING_MISMATCH_DENIED")
    if request.replay_ref != risk_decision.replay_ref:
        raise ValueError("LOW_RISK_DRY_RUN_REPLAY_BINDING_MISMATCH_DENIED")


def _validate_record_bindings(
    record: LowRiskAutonomousDryRunRecord,
    request: LowRiskAutonomousDryRunRequest,
) -> None:
    if record.dry_run_request_ref != request.dry_run_request_ref:
        raise ValueError("LOW_RISK_DRY_RUN_REQUEST_BINDING_MISMATCH_DENIED")
    if record.risk_decision_ref != request.risk_decision_ref:
        raise ValueError("LOW_RISK_DRY_RUN_RISK_DECISION_BINDING_MISMATCH_DENIED")
    if record.actor_ref != request.actor_ref:
        raise ValueError("LOW_RISK_DRY_RUN_ACTOR_BINDING_MISMATCH_DENIED")
    if record.resource_refs != request.resource_refs:
        raise ValueError("LOW_RISK_DRY_RUN_RESOURCE_BINDING_MISMATCH_DENIED")
    if record.capability_refs != request.capability_refs:
        raise ValueError("LOW_RISK_DRY_RUN_CAPABILITY_BINDING_MISMATCH_DENIED")
    if record.allowlist_refs != request.allowlist_refs:
        raise ValueError("LOW_RISK_DRY_RUN_ALLOWLIST_BINDING_MISMATCH_DENIED")
    if record.bundle_ref != request.bundle_ref:
        raise ValueError("LOW_RISK_DRY_RUN_BUNDLE_BINDING_MISMATCH_DENIED")
    if record.revocation_record_ref != request.revocation_record_ref:
        raise ValueError("LOW_RISK_DRY_RUN_REVOCATION_BINDING_MISMATCH_DENIED")
    if record.source_scope_ref != request.source_scope_ref:
        raise ValueError("LOW_RISK_DRY_RUN_SCOPE_BINDING_MISMATCH_DENIED")
    if record.audit_ref != request.audit_ref:
        raise ValueError("LOW_RISK_DRY_RUN_AUDIT_BINDING_MISMATCH_DENIED")
    if record.replay_ref != request.replay_ref:
        raise ValueError("LOW_RISK_DRY_RUN_REPLAY_BINDING_MISMATCH_DENIED")
    if record.step_refs != [step.step_ref for step in request.steps]:
        raise ValueError("LOW_RISK_DRY_RUN_STEP_BINDING_MISMATCH_DENIED")


def _validate_common_refs(*refs: str) -> None:
    field_names = [
        "record_or_request_ref",
        "risk_decision_ref",
        "actor_ref",
        "bundle_ref",
        "revocation_record_ref",
        "source_scope_ref",
        "audit_ref",
        "replay_ref",
    ]
    for ref, field_name in zip(refs, field_names, strict=True):
        _validate_m61_ref(ref, field_name)


def _validate_ref_list(refs: list[str], field_name: str, empty_reason: str) -> None:
    if not refs:
        raise ValueError(empty_reason)
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1]


_DRY_RUN_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("dry_run_only", "DRY_RUN_ONLY_REQUIRED"),
    ("low_risk_only", "LOW_RISK_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]


_DRY_RUN_DENIALS = [
    ("authority_granted", "LOW_RISK_DRY_RUN_AUTHORITY_DENIED"),
    ("low_risk_dry_run_authority_granted", "LOW_RISK_DRY_RUN_AUTHORITY_DENIED"),
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]


_DRY_RUN_STEP_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("dry_run_only", "DRY_RUN_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
]


_DRY_RUN_STEP_DENIALS = [
    ("authority_granted", "LOW_RISK_DRY_RUN_STEP_AUTHORITY_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
]


_DRY_RUN_RECORD_REQUIRED_TRUE = [
    ("dry_run_valid_for_review", "REVIEW_ONLY_REQUIRED"),
    *_DRY_RUN_REQUIRED_TRUE,
]


_DRY_RUN_RECORD_DENIALS = list(_DRY_RUN_DENIALS)
