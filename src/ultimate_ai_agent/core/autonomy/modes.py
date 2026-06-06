import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


AUTONOMY_MODE_CHARTER_DOCS = [
    "docs/autonomy/AUTONOMY_MODE_CHARTER.md",
    "docs/autonomy/AUTHORITY_LEVELS.md",
    "docs/autonomy/CAPABILITY_TOGGLE_REGISTRY.md",
    "docs/autonomy/AUTONOMY_CONSENT_REVOCATION_POLICY.md",
    "docs/autonomy/M61_TO_M62_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
M61_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
M61_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|private[_-]?key|authorization|cookie|oauth|bearer)",
    re.IGNORECASE,
)


class AutonomyAuthorityMode(str, Enum):
    off = "mode_0_off"
    observe_only = "mode_1_observe_only"
    dry_run_plan = "mode_2_dry_run_plan"
    ask_before_every_action = "mode_3_ask_before_every_action"
    scoped_autonomy_window = "mode_4_scoped_autonomy_window"
    trusted_recurring_automation = "mode_5_trusted_recurring_automation"
    production_authority_later = "mode_6_production_authority_later"


class AutonomyRiskClass(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class _AutonomyModeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyCapabilityToggle(_AutonomyModeModel):
    toggle_ref: str
    capability_ref: str
    requested_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.off
    actor_ref: str
    scope_ref: str
    resource_refs: list[str]
    duration_seconds: int = Field(default=0, ge=0)
    risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    approval_ref: str | None = None
    revocation_ref: str
    audit_ref: str
    enabled: bool = False
    dry_run_only: bool = True
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
    approval_test_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.toggle_ref, "toggle_ref"),
            (self.capability_ref, "capability_ref"),
            (self.actor_ref, "actor_ref"),
            (self.scope_ref, "scope_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.resource_refs:
            raise ValueError("RESOURCE_BINDING_REQUIRED")
        for ref in self.resource_refs:
            _validate_m61_ref(ref, "resource_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class AutonomyModeCharter(_AutonomyModeModel):
    charter_ref: str = "autonomy-mode-charter:m61"
    default_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.off
    available_modes: list[AutonomyAuthorityMode] = Field(
        default_factory=lambda: list(AutonomyAuthorityMode)
    )
    capability_exists: bool = True
    disabled_by_default: bool = True
    dry_run_first: bool = True
    limited_allowlist_required: bool = True
    explicit_approval_required: bool = True
    scoped_autonomy_window_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    production_authority_enabled: bool = False
    global_autonomy_switch_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    background_worker_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    backend_routes_enabled: bool = False
    dependencies_added: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(AUTONOMY_MODE_CHARTER_DOCS))
    roadmap_refs: list[str] = Field(default_factory=lambda: ["roadmap:M61-M100"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.charter_ref, "charter_ref")
        if set(self.available_modes) != set(AutonomyAuthorityMode):
            raise ValueError("AUTONOMY_AUTHORITY_MODES_INCOMPLETE")
        for ref in self.roadmap_refs:
            _validate_m61_ref(ref, "roadmap_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        return self


class AutonomyModeDecision(_AutonomyModeModel):
    decision_ref: str
    charter_ref: str
    toggle_ref: str
    selected_mode: AutonomyAuthorityMode
    allowed: bool = False
    dry_run_only: bool = True
    reason_codes: list[str]
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str

    @model_validator(mode="after")
    def validate_decision(self):
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(self.charter_ref, "charter_ref")
        _validate_m61_ref(self.toggle_ref, "toggle_ref")
        if self.side_effects_performed:
            raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_autonomy_mode_charter(charter: AutonomyModeCharter) -> AutonomyModeCharter:
    validated = AutonomyModeCharter.model_validate(charter.model_dump())
    _validate_safe_payload(validated.metadata)
    if validated.default_mode != AutonomyAuthorityMode.off:
        raise ValueError("AUTONOMY_DEFAULT_MODE_OFF_REQUIRED")
    for field_name, reason in _CHARTER_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _CHARTER_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_autonomy_capability_toggle(
    toggle: AutonomyCapabilityToggle,
) -> AutonomyCapabilityToggle:
    validated = AutonomyCapabilityToggle.model_validate(toggle.model_dump())
    _validate_safe_payload(validated.metadata)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if validated.enabled:
        raise ValueError("AUTONOMY_TOGGLE_ENABLEMENT_DENIED")
    if not validated.dry_run_only:
        raise ValueError("AUTONOMY_DRY_RUN_FIRST_REQUIRED")
    if validated.requested_mode in {
        AutonomyAuthorityMode.scoped_autonomy_window,
        AutonomyAuthorityMode.trusted_recurring_automation,
        AutonomyAuthorityMode.production_authority_later,
    }:
        raise ValueError("AUTONOMY_MODE_FUTURE_MILESTONE_DENIED")
    if validated.requested_mode != AutonomyAuthorityMode.off:
        raise ValueError("AUTONOMY_MODE_ENABLEMENT_DENIED")
    for field_name, reason in _TOGGLE_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_autonomy_mode_decision(
    toggle: AutonomyCapabilityToggle,
    charter: AutonomyModeCharter | None = None,
) -> AutonomyModeDecision:
    active_charter = validate_autonomy_mode_charter(charter or AutonomyModeCharter())
    active_toggle = validate_autonomy_capability_toggle(toggle)
    reason_codes = ["M61_AUTONOMY_MODE_CHARTER_DEFAULT_OFF"]
    if active_toggle.requested_mode != AutonomyAuthorityMode.off:
        reason_codes.append("M61_AUTONOMY_MODE_REQUEST_REVIEW_ONLY")
    return AutonomyModeDecision(
        decision_ref=f"autonomy-mode-decision:{_ref_suffix(active_toggle.toggle_ref)}",
        charter_ref=active_charter.charter_ref,
        toggle_ref=active_toggle.toggle_ref,
        selected_mode=AutonomyAuthorityMode.off,
        allowed=False,
        dry_run_only=True,
        reason_codes=reason_codes,
        safe_summary="M61 records autonomy authority levels only; no autonomy or execution is enabled.",
    )


_CHARTER_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("global_autonomy_switch_enabled", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
]

_CHARTER_REQUIRED_TRUE = [
    ("capability_exists", "CAPABILITY_EXISTENCE_STAGE_REQUIRED"),
    ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
    ("dry_run_first", "DRY_RUN_FIRST_REQUIRED"),
    ("limited_allowlist_required", "LIMITED_ALLOWLIST_REQUIRED"),
    ("explicit_approval_required", "EXPLICIT_APPROVAL_REQUIRED"),
    ("scoped_autonomy_window_required", "SCOPED_AUTONOMY_WINDOW_REQUIRED"),
    ("audit_replay_required", "AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "REVOCATION_REQUIRED"),
]

_TOGGLE_DENIALS = [
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


def _validate_m61_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M61_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_payload(value: Any) -> None:
    _deny_secret_like_keys(value)
    try:
        validate_safe_tool_payload(value, "autonomy_mode_content")
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_CONTENT_DENIED") from exc


def _deny_secret_like_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if M61_SECRET_KEY_RE.search(str(key)):
                raise ValueError("SECRET_LIKE_AUTONOMY_CONTENT_DENIED")
            _deny_secret_like_keys(item)
    elif isinstance(value, list):
        for item in value:
            _deny_secret_like_keys(item)


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1]
