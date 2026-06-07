from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


LOCATION_SENSOR_OFF_BY_DEFAULT_DOCS = [
    "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT.md",
    "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_POLICY.md",
    "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_AUTHORITY_BOUNDARY.md",
    "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_RECEIPT_PLAN.md",
    "docs/mobile/LOCATION_SENSOR_OFF_BY_DEFAULT_NON_GOALS.md",
    "docs/mobile/M102_TO_M103_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class LocationSensorAccuracyClass(str, Enum):
    not_requested = "not_requested"
    approximate_candidate = "approximate_candidate"
    precise_candidate = "precise_candidate"


class LocationSensorUseClass(str, Enum):
    foreground_review_candidate = "foreground_review_candidate"
    background_prohibited = "background_prohibited"
    unknown = "unknown"


class LocationSensorOffByDefaultStatus(str, Enum):
    contract_only = "contract_only"


class _LocationSensorOffByDefaultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LocationSensorOffByDefaultPolicy(_LocationSensorOffByDefaultModel):
    policy_ref: str = "location-sensor-off-by-default-policy:m102"
    contract_only: bool = True
    location_sensor_default_off_required: bool = True
    location_permission_scope_required: bool = True
    foreground_only_review_required: bool = True
    precise_location_separate_approval_required: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    runtime_location_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_location_enabled: bool = False
    raw_coordinates_enabled: bool = False
    location_history_enabled: bool = False
    geofence_enabled: bool = False
    location_export_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class LocationSensorScopeContract(_LocationSensorOffByDefaultModel):
    scope_ref: str
    sensor_ref: str = "mobile-sensor-contract:m101:location"
    actor_ref: str
    device_ref: str
    purpose_ref: str
    use_class: LocationSensorUseClass = LocationSensorUseClass.foreground_review_candidate
    accuracy_class: LocationSensorAccuracyClass = LocationSensorAccuracyClass.not_requested
    disabled_by_default: bool = True
    exact_scope_required: bool = True
    foreground_only: bool = True
    separate_precise_approval_required: bool = True
    consent_required: bool = True
    revocable: bool = True
    audit_required: bool = True
    runtime_location_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_location_enabled: bool = False
    raw_coordinates_enabled: bool = False
    location_history_enabled: bool = False
    geofence_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.scope_ref, "scope_ref"),
            (self.sensor_ref, "sensor_ref"),
            (self.actor_ref, "actor_ref"),
            (self.device_ref, "device_ref"),
            (self.purpose_ref, "purpose_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class LocationSensorOffByDefaultReport(_LocationSensorOffByDefaultModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: LocationSensorOffByDefaultStatus = LocationSensorOffByDefaultStatus.contract_only
    contract_only: bool = True
    location_sensor_default_off: bool = True
    location_permission_scope_defined: bool = True
    foreground_only_review_defined: bool = True
    precise_location_separate_approval_required: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    scope_contracts: list[LocationSensorScopeContract]
    runtime_location_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_location_enabled: bool = False
    raw_coordinates_enabled: bool = False
    location_history_enabled: bool = False
    geofence_enabled: bool = False
    location_export_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_location_sensor_off_by_default_report(
    policy: LocationSensorOffByDefaultPolicy | None = None,
) -> LocationSensorOffByDefaultReport:
    active_policy = validate_location_sensor_off_by_default_policy(
        policy or LocationSensorOffByDefaultPolicy()
    )
    scope_contract = LocationSensorScopeContract(
        scope_ref="location-sensor-scope:m102:foreground-review-candidate",
        actor_ref="actor:location-sensor-contract-reviewer",
        device_ref="device:mobile-companion-contract",
        purpose_ref="location-purpose:m102:future-foreground-review",
    )
    report = LocationSensorOffByDefaultReport(
        report_ref="location-sensor-off-by-default-report:m102",
        baseline_ref="baseline:v1.5.0",
        actor_ref="actor:location-sensor-contract-reviewer",
        contract_only=active_policy.contract_only,
        scope_contracts=[scope_contract],
        side_effects_performed=[],
        reason_codes=[
            "M102_LOCATION_SENSOR_OFF_BY_DEFAULT",
            "M102_LOCATION_PERMISSION_SCOPE_DEFINED",
            "M102_FOREGROUND_ONLY_REVIEW_DEFINED",
            "M102_PRECISE_LOCATION_SEPARATE_APPROVAL_REQUIRED",
            "M102_NO_RUNTIME_LOCATION_ACCESS",
            "M103_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M102 defines an off-by-default location sensor contract for future "
            "foreground review only. It adds no runtime location access, native "
            "permission prompt, background location, raw coordinates, location "
            "history, geofence behavior, backend routes, Control Center controls, "
            "dependencies, memory writes, context injection, execution, M103 work, "
            "or production authority."
        ),
    )
    return validate_location_sensor_off_by_default_report(report)


def validate_location_sensor_off_by_default_policy(
    policy: LocationSensorOffByDefaultPolicy,
) -> LocationSensorOffByDefaultPolicy:
    validated = LocationSensorOffByDefaultPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M102_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M102_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m102_metadata(validated.metadata)
    return validated


def validate_location_sensor_scope_contract(
    contract: LocationSensorScopeContract,
) -> LocationSensorScopeContract:
    payload = _model_payload(contract)
    for field_name, reason in _M102_SCOPE_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, LocationSensorScopeContract):
        raise ValueError("SECRET_LIKE_M102_LOCATION_CONTENT_DENIED")
    validated = LocationSensorScopeContract.model_validate(payload)
    for field_name, reason in _M102_SCOPE_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M102_SCOPE_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.use_class != LocationSensorUseClass.foreground_review_candidate:
        raise ValueError("BACKGROUND_OR_UNKNOWN_LOCATION_USE_DENIED")
    if validated.accuracy_class != LocationSensorAccuracyClass.not_requested:
        raise ValueError("LOCATION_ACCURACY_REQUEST_DENIED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m102_metadata(validated.metadata)
    return validated


def validate_location_sensor_off_by_default_report(
    report: LocationSensorOffByDefaultReport,
) -> LocationSensorOffByDefaultReport:
    payload = _model_payload(report)
    for field_name, reason in _M102_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, LocationSensorOffByDefaultReport):
        raise ValueError("SECRET_LIKE_M102_LOCATION_CONTENT_DENIED")
    validated = LocationSensorOffByDefaultReport.model_validate(payload)
    for field_name, reason in _M102_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M102_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != LocationSensorOffByDefaultStatus.contract_only:
        raise ValueError("M102_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_location_scope_contracts(validated.scope_contracts)
    _validate_m102_metadata(validated.metadata)
    return validated


def _validate_location_scope_contracts(contracts: list[LocationSensorScopeContract]) -> None:
    if not contracts:
        raise ValueError("M102_LOCATION_PERMISSION_SCOPE_REQUIRED")
    seen_refs: set[str] = set()
    for contract in contracts:
        validated = validate_location_sensor_scope_contract(contract)
        if validated.scope_ref in seen_refs:
            raise ValueError("M102_LOCATION_SCOPE_REF_DUPLICATE")
        seen_refs.add(validated.scope_ref)


def _validate_m102_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M102_LOCATION_CONTENT_DENIED") from exc


_M102_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("location_sensor_default_off_required", "M102_LOCATION_DEFAULT_OFF_REQUIRED"),
    ("location_permission_scope_required", "M102_LOCATION_PERMISSION_SCOPE_REQUIRED"),
    ("foreground_only_review_required", "M102_FOREGROUND_ONLY_REVIEW_REQUIRED"),
    ("precise_location_separate_approval_required", "M102_PRECISE_APPROVAL_REQUIRED"),
    ("consent_required", "M102_CONSENT_REQUIRED"),
    ("revocation_required", "M102_REVOCATION_REQUIRED"),
    ("audit_required", "M102_AUDIT_REQUIRED"),
]

_M102_DENIALS = [
    ("runtime_location_access_enabled", "RUNTIME_LOCATION_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_location_enabled", "BACKGROUND_LOCATION_DENIED"),
    ("raw_coordinates_enabled", "RAW_COORDINATES_DENIED"),
    ("location_history_enabled", "LOCATION_HISTORY_DENIED"),
    ("geofence_enabled", "GEOFENCE_DENIED"),
    ("location_export_enabled", "LOCATION_EXPORT_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M102_SCOPE_REQUIRED_TRUE = [
    ("disabled_by_default", "M102_LOCATION_DEFAULT_OFF_REQUIRED"),
    ("exact_scope_required", "M102_EXACT_SCOPE_REQUIRED"),
    ("foreground_only", "M102_FOREGROUND_ONLY_REVIEW_REQUIRED"),
    ("separate_precise_approval_required", "M102_PRECISE_APPROVAL_REQUIRED"),
    ("consent_required", "M102_CONSENT_REQUIRED"),
    ("revocable", "M102_REVOCATION_REQUIRED"),
    ("audit_required", "M102_AUDIT_REQUIRED"),
]

_M102_SCOPE_DENIALS = [
    ("runtime_location_access_enabled", "RUNTIME_LOCATION_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_location_enabled", "BACKGROUND_LOCATION_DENIED"),
    ("raw_coordinates_enabled", "RAW_COORDINATES_DENIED"),
    ("location_history_enabled", "LOCATION_HISTORY_DENIED"),
    ("geofence_enabled", "GEOFENCE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M102_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("location_sensor_default_off", "M102_LOCATION_DEFAULT_OFF_REQUIRED"),
    ("location_permission_scope_defined", "M102_LOCATION_PERMISSION_SCOPE_REQUIRED"),
    ("foreground_only_review_defined", "M102_FOREGROUND_ONLY_REVIEW_REQUIRED"),
    ("precise_location_separate_approval_required", "M102_PRECISE_APPROVAL_REQUIRED"),
    ("consent_required", "M102_CONSENT_REQUIRED"),
    ("revocation_required", "M102_REVOCATION_REQUIRED"),
    ("audit_required", "M102_AUDIT_REQUIRED"),
]

_M102_REPORT_DENIALS = [
    ("runtime_location_access_enabled", "RUNTIME_LOCATION_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_location_enabled", "BACKGROUND_LOCATION_DENIED"),
    ("raw_coordinates_enabled", "RAW_COORDINATES_DENIED"),
    ("location_history_enabled", "LOCATION_HISTORY_DENIED"),
    ("geofence_enabled", "GEOFENCE_DENIED"),
    ("location_export_enabled", "LOCATION_EXPORT_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
