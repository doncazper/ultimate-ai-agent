from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    _ref_suffix,
    _validate_m61_ref,
    _validate_safe_payload,
)


SCOPED_AUTONOMY_SESSION_DOCS = [
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_CONTRACTS.md",
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_SCOPE_POLICY.md",
    "docs/autonomy/SCOPED_AUTONOMY_SESSION_NON_GOALS.md",
    "docs/autonomy/M62_TO_M63_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
M62_MAX_SESSION_DURATION_SECONDS = 7200


class _ScopedAutonomySessionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ScopedAutonomySessionScope(_ScopedAutonomySessionModel):
    scope_ref: str
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    max_duration_seconds: int = Field(gt=0)
    risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    revocation_ref: str
    audit_ref: str
    replay_ref: str
    disabled_by_default: bool = True
    dry_run_only: bool = True
    session_start_enabled: bool = False
    session_activation_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    background_worker_enabled: bool = False
    production_authority_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.scope_ref, "scope_ref"),
            (self.actor_ref, "actor_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for refs, field_name, reason in [
            (self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED"),
            (self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED"),
            (self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED"),
        ]:
            if not refs:
                raise ValueError(reason)
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        return self


class ScopedAutonomySessionRequest(_ScopedAutonomySessionModel):
    session_request_ref: str
    requested_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.dry_run_plan
    scope: ScopedAutonomySessionScope
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    start_requested: bool = False
    session_active: bool = False
    execution_requested: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    context_injection_enabled: bool = False
    memory_write_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.session_request_ref, "session_request_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class ScopedAutonomySessionDecision(_ScopedAutonomySessionModel):
    decision_ref: str
    session_request_ref: str
    scope_ref: str
    selected_mode: AutonomyAuthorityMode
    contract_valid_for_review: bool = True
    session_started: bool = False
    session_active: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(self.session_request_ref, "session_request_ref")
        _validate_m61_ref(self.scope_ref, "scope_ref")
        if self.session_started or self.session_active:
            raise ValueError("AUTONOMY_SESSION_ACTIVATION_DENIED")
        if self.execution_performed:
            raise ValueError("EXECUTION_DENIED")
        if self.side_effects_performed:
            raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_scoped_autonomy_session_scope(
    scope: ScopedAutonomySessionScope,
) -> ScopedAutonomySessionScope:
    validated = ScopedAutonomySessionScope.model_validate(scope.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_SESSION_CONTENT_DENIED") from exc
    if validated.max_duration_seconds > M62_MAX_SESSION_DURATION_SECONDS:
        raise ValueError("SESSION_DURATION_BOUND_EXCEEDED")
    for field_name, reason in _SCOPE_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _SCOPE_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_scoped_autonomy_session_request(
    request: ScopedAutonomySessionRequest,
) -> ScopedAutonomySessionRequest:
    validated = ScopedAutonomySessionRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_SESSION_CONTENT_DENIED") from exc
    validate_scoped_autonomy_session_scope(validated.scope)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if validated.requested_mode in {
        AutonomyAuthorityMode.scoped_autonomy_window,
        AutonomyAuthorityMode.trusted_recurring_automation,
        AutonomyAuthorityMode.production_authority_later,
    }:
        raise ValueError("AUTONOMY_MODE_FUTURE_MILESTONE_DENIED")
    if validated.requested_mode == AutonomyAuthorityMode.ask_before_every_action:
        raise ValueError("AUTONOMY_MODE_ENABLEMENT_DENIED")
    for field_name, reason in _REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_scoped_autonomy_session_decision(
    request: ScopedAutonomySessionRequest,
) -> ScopedAutonomySessionDecision:
    validated = validate_scoped_autonomy_session_request(request)
    return ScopedAutonomySessionDecision(
        decision_ref=f"autonomy-session-decision:{_ref_suffix(validated.session_request_ref)}",
        session_request_ref=validated.session_request_ref,
        scope_ref=validated.scope.scope_ref,
        selected_mode=validated.requested_mode,
        contract_valid_for_review=True,
        session_started=False,
        session_active=False,
        execution_performed=False,
        side_effects_performed=[],
        reason_codes=["M62_SCOPED_AUTONOMY_SESSION_CONTRACT_REVIEW_ONLY"],
        safe_summary="M62 validates scoped autonomy session contracts only; no session is started.",
    )


_SCOPE_REQUIRED_TRUE = [
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("dry_run_only", "DRY_RUN_FIRST_REQUIRED"),
]

_SCOPE_DENIALS = [
    ("session_start_enabled", "AUTONOMY_SESSION_START_DENIED"),
    ("session_activation_enabled", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
]

_REQUEST_DENIALS = [
    ("start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
]
