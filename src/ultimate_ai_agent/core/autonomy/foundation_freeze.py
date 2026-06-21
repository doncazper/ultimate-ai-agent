from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


AUTONOMY_FOUNDATION_FREEZE_DOCS = [
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE.md",
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_FOUNDATION_FREEZE_NON_GOALS.md",
    "docs/autonomy/M70_TO_M71_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_AUTONOMY_FOUNDATION_MILESTONE_REFS = tuple(
    f"milestone:M{index}" for index in range(61, 70)
)


class AutonomyFoundationFreezeStatus(str, Enum):
    frozen = "frozen"


class _AutonomyFoundationFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyFoundationFreezePolicy(_AutonomyFoundationFreezeModel):
    policy_ref: str = "autonomy-foundation-freeze-policy:m70"
    freeze_only: bool = True
    review_only: bool = True
    autonomy_foundation_only: bool = True
    deterministic: bool = True
    policy_activation_enabled: bool = False
    session_start_enabled: bool = False
    low_risk_dry_run_execution_enabled: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_enabled: bool = False
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
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class AutonomyFoundationFreezeRequest(_AutonomyFoundationFreezeModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    safe_summary: str
    freeze_only: bool = True
    review_only: bool = True
    autonomy_foundation_only: bool = True
    deterministic: bool = True
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    low_risk_dry_run_execution_requested: bool = False
    autonomous_actions_requested: bool = False
    background_worker_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    network_tool_requested: bool = False
    browser_automation_requested: bool = False
    plugin_execution_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    model_provider_call_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class AutonomyFoundationFreezeReport(_AutonomyFoundationFreezeModel):
    report_ref: str
    freeze_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    status: AutonomyFoundationFreezeStatus = AutonomyFoundationFreezeStatus.frozen
    freeze_only: bool = True
    review_only: bool = True
    autonomy_foundation_only: bool = True
    deterministic: bool = True
    policy_activation_performed: bool = False
    session_start_performed: bool = False
    low_risk_dry_run_execution_performed: bool = False
    autonomous_actions_performed: bool = False
    background_worker_started: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    network_tool_performed: bool = False
    browser_automation_performed: bool = False
    plugin_execution_performed: bool = False
    mobile_sensor_performed: bool = False
    remote_execution_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    model_provider_call_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.request_ref, "request_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_autonomy_foundation_freeze_report(
    request: AutonomyFoundationFreezeRequest,
    policy: AutonomyFoundationFreezePolicy | None = None,
) -> AutonomyFoundationFreezeReport:
    active_policy = validate_autonomy_foundation_freeze_policy(
        policy or AutonomyFoundationFreezePolicy()
    )
    validated_request = validate_autonomy_foundation_freeze_request(request)
    report = AutonomyFoundationFreezeReport(
        report_ref=f"autonomy-foundation-freeze-report:{_ref_suffix(validated_request.freeze_ref)}",
        freeze_ref=validated_request.freeze_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_milestone_refs=list(validated_request.accepted_milestone_refs),
        checklist_refs=list(validated_request.checklist_refs),
        freeze_only=active_policy.freeze_only,
        review_only=active_policy.review_only,
        autonomy_foundation_only=active_policy.autonomy_foundation_only,
        deterministic=active_policy.deterministic,
        side_effects_performed=[],
        reason_codes=[
            "M70_AUTONOMY_FOUNDATION_FREEZE_REVIEW_ONLY",
            "M70_NO_NEW_AUTONOMY_AUTHORITY",
        ],
        safe_summary=(
            "M70 freezes the accepted M61-M69 autonomy foundation for review only. "
            "It adds no policy activation, session start, low-risk dry-run execution, "
            "autonomous action, background worker, route, dependency, context injection, "
            "memory write, model/provider call, or production authority."
        ),
    )
    return validate_autonomy_foundation_freeze_report(report)


def validate_autonomy_foundation_freeze_policy(
    policy: AutonomyFoundationFreezePolicy,
) -> AutonomyFoundationFreezePolicy:
    validated = AutonomyFoundationFreezePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _FREEZE_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _FREEZE_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_autonomy_foundation_freeze_request(
    request: AutonomyFoundationFreezeRequest,
) -> AutonomyFoundationFreezeRequest:
    payload = _model_payload(request)
    for field_name, reason in _FREEZE_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, AutonomyFoundationFreezeRequest):
        raise ValueError("SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED")
    validated = AutonomyFoundationFreezeRequest.model_validate(payload)
    for field_name, reason in _FREEZE_REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _FREEZE_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_autonomy_foundation_freeze_report(
    report: AutonomyFoundationFreezeReport,
) -> AutonomyFoundationFreezeReport:
    validated = AutonomyFoundationFreezeReport.model_validate(_model_payload(report))
    for field_name, reason in _FREEZE_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _FREEZE_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != AutonomyFoundationFreezeStatus.frozen:
        raise ValueError("AUTONOMY_FOUNDATION_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED") from exc
    return validated


def _validate_accepted_milestones(refs: list[str]) -> None:
    if not refs:
        raise ValueError("AUTONOMY_FOUNDATION_ACCEPTED_MILESTONES_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("AUTONOMY_FOUNDATION_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_milestone_ref")
    missing = [ref for ref in REQUIRED_AUTONOMY_FOUNDATION_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("AUTONOMY_FOUNDATION_MILESTONE_REF_REQUIRED")
    unexpected = [
        ref for ref in refs if ref not in REQUIRED_AUTONOMY_FOUNDATION_MILESTONE_REFS
    ]
    if unexpected:
        raise ValueError("AUTONOMY_FOUNDATION_MILESTONE_REF_UNEXPECTED")


def _validate_checklist_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("AUTONOMY_FOUNDATION_CHECKLIST_REF_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("AUTONOMY_FOUNDATION_CHECKLIST_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "checklist_ref")


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump()
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    for key, value in getattr(model, "__dict__", {}).items():
        if key not in payload:
            payload[key] = value
    return payload


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


_FREEZE_POLICY_REQUIRED_TRUE = [
    ("freeze_only", "FREEZE_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("autonomy_foundation_only", "AUTONOMY_FOUNDATION_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REVIEW_REQUIRED"),
]


_FREEZE_POLICY_DENIALS = [
    ("policy_activation_enabled", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_enabled", "AUTONOMY_SESSION_START_DENIED"),
    ("low_risk_dry_run_execution_enabled", "LOW_RISK_DRY_RUN_EXECUTION_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
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
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]


_FREEZE_REQUEST_REQUIRED_TRUE = list(_FREEZE_POLICY_REQUIRED_TRUE)


_FREEZE_REQUEST_DENIALS = [
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("low_risk_dry_run_execution_requested", "LOW_RISK_DRY_RUN_EXECUTION_DENIED"),
    ("autonomous_actions_requested", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("network_tool_requested", "NETWORK_TOOL_DENIED"),
    ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_requested", "MODEL_PROVIDER_CALL_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]


_FREEZE_REPORT_REQUIRED_TRUE = list(_FREEZE_POLICY_REQUIRED_TRUE)


_FREEZE_REPORT_DENIALS = [
    ("policy_activation_performed", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_performed", "AUTONOMY_SESSION_START_DENIED"),
    ("low_risk_dry_run_execution_performed", "LOW_RISK_DRY_RUN_EXECUTION_DENIED"),
    ("autonomous_actions_performed", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("network_tool_performed", "NETWORK_TOOL_DENIED"),
    ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_performed", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_performed", "MODEL_PROVIDER_CALL_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
