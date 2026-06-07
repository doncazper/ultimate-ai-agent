from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_SENSOR_CONTRACT_REVIEW_DOCS = [
    "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW.md",
    "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_POLICY.md",
    "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_NON_GOALS.md",
    "docs/mobile/M101_TO_M102_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileSensorCapabilityClass(str, Enum):
    location = "location"
    camera = "camera"
    photos = "photos"
    microphone = "microphone"
    motion_activity = "motion_activity"
    bluetooth = "bluetooth"
    nfc = "nfc"
    local_network = "local_network"
    biometrics = "biometrics"
    clipboard = "clipboard"
    unknown = "unknown"


class MobileSensorRiskClass(str, Enum):
    sensitive = "sensitive"
    regulated = "regulated"
    prohibited_unknown = "prohibited_unknown"


class MobileSensorContractReviewStatus(str, Enum):
    contract_only = "contract_only"


class _MobileSensorContractReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileSensorContractReviewPolicy(_MobileSensorContractReviewModel):
    policy_ref: str = "mobile-sensor-contract-review-policy:m101"
    contract_only: bool = True
    sensor_taxonomy_required: bool = True
    permission_state_contract_required: bool = True
    sensor_risk_classification_required: bool = True
    consent_revocation_required: bool = True
    audit_required: bool = True
    sensors_default_off_required: bool = True
    unknown_sensor_denied_required: bool = True
    runtime_sensor_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_collection_enabled: bool = False
    location_sensor_enabled: bool = False
    camera_sensor_enabled: bool = False
    photos_sensor_enabled: bool = False
    microphone_sensor_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    backend_route_enabled: bool = False
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


class MobileSensorCapabilityContract(_MobileSensorContractReviewModel):
    sensor_ref: str
    capability_class: MobileSensorCapabilityClass
    safe_label: str
    safe_purpose_summary: str
    risk_class: MobileSensorRiskClass = MobileSensorRiskClass.sensitive
    default_off: bool = True
    explicit_consent_required: bool = True
    revocable: bool = True
    audit_required: bool = True
    runtime_sensor_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_collection_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.sensor_ref, "sensor_ref")
        _validate_safe_payload(self.safe_label)
        _validate_safe_payload(self.safe_purpose_summary)
        return self


class MobileSensorPermissionStateContract(_MobileSensorContractReviewModel):
    state_ref: str
    sensor_ref: str
    actor_ref: str
    device_ref: str
    disabled_by_default: bool = True
    runtime_permission_granted: bool = False
    native_prompt_shown: bool = False
    exact_scope_required: bool = True
    actor_bound: bool = True
    resource_bound: bool = True
    non_transferable: bool = True
    revocable: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.state_ref, "state_ref"),
            (self.sensor_ref, "sensor_ref"),
            (self.actor_ref, "actor_ref"),
            (self.device_ref, "device_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobileSensorContractReviewReport(_MobileSensorContractReviewModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobileSensorContractReviewStatus = (
        MobileSensorContractReviewStatus.contract_only
    )
    contract_only: bool = True
    sensor_taxonomy_defined: bool = True
    permission_state_contract_defined: bool = True
    sensor_risk_classification_defined: bool = True
    consent_revocation_required: bool = True
    audit_required: bool = True
    sensors_default_off: bool = True
    unknown_sensor_denied: bool = True
    capability_contracts: list[MobileSensorCapabilityContract]
    permission_state_contracts: list[MobileSensorPermissionStateContract]
    runtime_sensor_access_enabled: bool = False
    native_permission_prompt_enabled: bool = False
    background_collection_enabled: bool = False
    location_sensor_enabled: bool = False
    camera_sensor_enabled: bool = False
    photos_sensor_enabled: bool = False
    microphone_sensor_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    backend_route_added: bool = False
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


def build_mobile_sensor_contract_review_report(
    policy: MobileSensorContractReviewPolicy | None = None,
) -> MobileSensorContractReviewReport:
    active_policy = validate_mobile_sensor_contract_review_policy(
        policy or MobileSensorContractReviewPolicy()
    )
    capability_contracts = _default_sensor_capability_contracts()
    permission_state_contracts = [
        MobileSensorPermissionStateContract(
            state_ref=f"mobile-sensor-permission-state:m101:{contract.capability_class.value}",
            sensor_ref=contract.sensor_ref,
            actor_ref="actor:mobile-sensor-contract-reviewer",
            device_ref="device:mobile-companion-contract",
        )
        for contract in capability_contracts
    ]
    report = MobileSensorContractReviewReport(
        report_ref="mobile-sensor-contract-review-report:m101",
        baseline_ref="baseline:v1.4.1",
        actor_ref="actor:mobile-sensor-contract-reviewer",
        contract_only=active_policy.contract_only,
        capability_contracts=capability_contracts,
        permission_state_contracts=permission_state_contracts,
        side_effects_performed=[],
        reason_codes=[
            "M101_MOBILE_SENSOR_CONTRACT_REVIEW_ONLY",
            "M101_SENSOR_TAXONOMY_DEFINED",
            "M101_PERMISSION_STATE_CONTRACT_DEFINED",
            "M101_SENSOR_RISK_CLASSIFICATION_DEFINED",
            "M101_SENSORS_DEFAULT_OFF",
            "M101_UNKNOWN_SENSOR_DENIED",
            "M102_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M101 defines mobile sensor capability classes, permission-state contracts, "
            "risk classification, consent, revocation, and audit requirements. It adds "
            "no runtime sensor access, native permission prompts, background collection, "
            "backend routes, dependencies, memory writes, context injection, execution, "
            "M102 work, or production authority."
        ),
    )
    return validate_mobile_sensor_contract_review_report(report)


def validate_mobile_sensor_contract_review_policy(
    policy: MobileSensorContractReviewPolicy,
) -> MobileSensorContractReviewPolicy:
    validated = MobileSensorContractReviewPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M101_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M101_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m101_metadata(validated.metadata)
    return validated


def validate_mobile_sensor_capability_contract(
    contract: MobileSensorCapabilityContract,
) -> MobileSensorCapabilityContract:
    payload = _model_payload(contract)
    for field_name, reason in _M101_CAPABILITY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileSensorCapabilityContract):
        raise ValueError("SECRET_LIKE_M101_SENSOR_CONTENT_DENIED")
    validated = MobileSensorCapabilityContract.model_validate(payload)
    for field_name, reason in _M101_CAPABILITY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M101_CAPABILITY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.capability_class == MobileSensorCapabilityClass.unknown:
        raise ValueError("UNKNOWN_SENSOR_DENIED")
    if validated.risk_class == MobileSensorRiskClass.prohibited_unknown:
        raise ValueError("UNKNOWN_SENSOR_DENIED")
    _validate_m101_metadata(validated.metadata)
    return validated


def validate_mobile_sensor_permission_state_contract(
    contract: MobileSensorPermissionStateContract,
) -> MobileSensorPermissionStateContract:
    payload = _model_payload(contract)
    for field_name, reason in _M101_PERMISSION_STATE_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileSensorPermissionStateContract):
        raise ValueError("SECRET_LIKE_M101_SENSOR_CONTENT_DENIED")
    validated = MobileSensorPermissionStateContract.model_validate(payload)
    for field_name, reason in _M101_PERMISSION_STATE_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m101_metadata(validated.metadata)
    return validated


def validate_mobile_sensor_contract_review_report(
    report: MobileSensorContractReviewReport,
) -> MobileSensorContractReviewReport:
    payload = _model_payload(report)
    for field_name, reason in _M101_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileSensorContractReviewReport):
        raise ValueError("SECRET_LIKE_M101_SENSOR_CONTENT_DENIED")
    validated = MobileSensorContractReviewReport.model_validate(payload)
    for field_name, reason in _M101_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M101_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileSensorContractReviewStatus.contract_only:
        raise ValueError("M101_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_capability_contracts(validated.capability_contracts)
    _validate_permission_state_contracts(
        validated.permission_state_contracts,
        [contract.sensor_ref for contract in validated.capability_contracts],
    )
    _validate_m101_metadata(validated.metadata)
    return validated


def _default_sensor_capability_contracts() -> list[MobileSensorCapabilityContract]:
    return [
        MobileSensorCapabilityContract(
            sensor_ref=f"mobile-sensor-contract:m101:{capability.value}",
            capability_class=capability,
            safe_label=capability.value.replace("_", " ").title(),
            safe_purpose_summary=(
                f"{capability.value.replace('_', ' ').title()} is classified for future "
                "permission review only. M101 does not access device sensors or prompt OS permissions."
            ),
            risk_class=(
                MobileSensorRiskClass.regulated
                if capability in {MobileSensorCapabilityClass.location, MobileSensorCapabilityClass.biometrics}
                else MobileSensorRiskClass.sensitive
            ),
        )
        for capability in MobileSensorCapabilityClass
        if capability != MobileSensorCapabilityClass.unknown
    ]


def _validate_capability_contracts(
    contracts: list[MobileSensorCapabilityContract],
) -> None:
    if not contracts:
        raise ValueError("M101_SENSOR_TAXONOMY_REQUIRED")
    seen_refs: set[str] = set()
    seen_classes: set[MobileSensorCapabilityClass] = set()
    for contract in contracts:
        validated = validate_mobile_sensor_capability_contract(contract)
        if validated.sensor_ref in seen_refs:
            raise ValueError("M101_SENSOR_REF_DUPLICATE")
        if validated.capability_class in seen_classes:
            raise ValueError("M101_SENSOR_CLASS_DUPLICATE")
        seen_refs.add(validated.sensor_ref)
        seen_classes.add(validated.capability_class)
    expected = set(MobileSensorCapabilityClass) - {MobileSensorCapabilityClass.unknown}
    if seen_classes != expected:
        raise ValueError("M101_SENSOR_CLASS_REQUIRED")


def _validate_permission_state_contracts(
    contracts: list[MobileSensorPermissionStateContract],
    sensor_refs: list[str],
) -> None:
    if not contracts:
        raise ValueError("M101_PERMISSION_STATE_CONTRACT_REQUIRED")
    seen_refs: set[str] = set()
    seen_sensor_refs: set[str] = set()
    for contract in contracts:
        validated = validate_mobile_sensor_permission_state_contract(contract)
        if validated.state_ref in seen_refs:
            raise ValueError("M101_PERMISSION_STATE_REF_DUPLICATE")
        if validated.sensor_ref in seen_sensor_refs:
            raise ValueError("M101_PERMISSION_STATE_SENSOR_REF_DUPLICATE")
        seen_refs.add(validated.state_ref)
        seen_sensor_refs.add(validated.sensor_ref)
    if seen_sensor_refs != set(sensor_refs):
        raise ValueError("M101_PERMISSION_STATE_BINDING_REQUIRED")


def _validate_m101_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M101_SENSOR_CONTENT_DENIED") from exc


_M101_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("sensor_taxonomy_required", "M101_SENSOR_TAXONOMY_REQUIRED"),
    ("permission_state_contract_required", "M101_PERMISSION_STATE_CONTRACT_REQUIRED"),
    ("sensor_risk_classification_required", "M101_RISK_CLASSIFICATION_REQUIRED"),
    ("consent_revocation_required", "M101_CONSENT_REVOCATION_REQUIRED"),
    ("audit_required", "M101_AUDIT_REQUIRED"),
    ("sensors_default_off_required", "M101_SENSORS_DEFAULT_OFF_REQUIRED"),
    ("unknown_sensor_denied_required", "UNKNOWN_SENSOR_DENIED"),
]

_M101_POLICY_DENIALS = [
    ("runtime_sensor_access_enabled", "RUNTIME_SENSOR_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("location_sensor_enabled", "LOCATION_SENSOR_DENIED"),
    ("camera_sensor_enabled", "CAMERA_SENSOR_DENIED"),
    ("photos_sensor_enabled", "PHOTOS_SENSOR_DENIED"),
    ("microphone_sensor_enabled", "MICROPHONE_SENSOR_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M101_CAPABILITY_REQUIRED_TRUE = [
    ("default_off", "M101_SENSORS_DEFAULT_OFF_REQUIRED"),
    ("explicit_consent_required", "M101_EXPLICIT_CONSENT_REQUIRED"),
    ("revocable", "M101_REVOCATION_REQUIRED"),
    ("audit_required", "M101_AUDIT_REQUIRED"),
]

_M101_CAPABILITY_DENIALS = [
    ("runtime_sensor_access_enabled", "RUNTIME_SENSOR_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M101_PERMISSION_STATE_REQUIRED_TRUE = [
    ("disabled_by_default", "M101_SENSORS_DEFAULT_OFF_REQUIRED"),
    ("exact_scope_required", "M101_EXACT_SCOPE_REQUIRED"),
    ("actor_bound", "M101_ACTOR_BOUND_REQUIRED"),
    ("resource_bound", "M101_RESOURCE_BOUND_REQUIRED"),
    ("non_transferable", "M101_NON_TRANSFERABLE_REQUIRED"),
    ("revocable", "M101_REVOCATION_REQUIRED"),
    ("replay_safe", "M101_REPLAY_SAFE_REQUIRED"),
]

_M101_PERMISSION_STATE_DENIALS = [
    ("runtime_permission_granted", "RUNTIME_SENSOR_ACCESS_DENIED"),
    ("native_prompt_shown", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M101_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("sensor_taxonomy_defined", "M101_SENSOR_TAXONOMY_REQUIRED"),
    ("permission_state_contract_defined", "M101_PERMISSION_STATE_CONTRACT_REQUIRED"),
    ("sensor_risk_classification_defined", "M101_RISK_CLASSIFICATION_REQUIRED"),
    ("consent_revocation_required", "M101_CONSENT_REVOCATION_REQUIRED"),
    ("audit_required", "M101_AUDIT_REQUIRED"),
    ("sensors_default_off", "M101_SENSORS_DEFAULT_OFF_REQUIRED"),
    ("unknown_sensor_denied", "UNKNOWN_SENSOR_DENIED"),
]

_M101_REPORT_DENIALS = [
    ("runtime_sensor_access_enabled", "RUNTIME_SENSOR_ACCESS_DENIED"),
    ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("location_sensor_enabled", "LOCATION_SENSOR_DENIED"),
    ("camera_sensor_enabled", "CAMERA_SENSOR_DENIED"),
    ("photos_sensor_enabled", "PHOTOS_SENSOR_DENIED"),
    ("microphone_sensor_enabled", "MICROPHONE_SENSOR_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
