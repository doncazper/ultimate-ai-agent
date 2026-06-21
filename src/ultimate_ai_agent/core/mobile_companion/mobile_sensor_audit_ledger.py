from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.mobile_companion.mobile_kill_switch_revocation import (
    MobileKillSwitchRevocationRecord,
    validate_mobile_kill_switch_revocation_record,
)


MOBILE_SENSOR_AUDIT_LEDGER_DOCS = [
    "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER.md",
    "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_POLICY.md",
    "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_SENSOR_AUDIT_LEDGER_NON_GOALS.md",
    "docs/mobile/M109_TO_M110_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileSensorAuditLedgerStatus(str, Enum):
    review_only_contract = "review_only_contract"


class _MobileSensorAuditLedgerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileSensorAuditLedgerPolicy(_MobileSensorAuditLedgerModel):
    policy_ref: str = "mobile-sensor-audit-ledger-policy:m109"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    device_binding_required: bool = True
    sensor_scope_binding_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    sensor_access_enabled: bool = False
    sensor_read_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    background_collection_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_audit_payload_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    native_mobile_ui_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileSensorAuditLedgerRecord(_MobileSensorAuditLedgerModel):
    ledger_ref: str
    source_record: MobileKillSwitchRevocationRecord
    source_record_ref: str
    source_baseline_ref: str
    actor_ref: str
    safe_device_ref: str
    sensor_scope_ref: str
    audit_ref: str
    replay_ref: str
    sensor_audit_entries: list[str]
    status: MobileSensorAuditLedgerStatus = (
        MobileSensorAuditLedgerStatus.review_only_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    device_bound: bool = True
    sensor_scope_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    sensor_access_performed: bool = False
    sensor_access_enabled: bool = False
    sensor_read_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    background_collection_enabled: bool = False
    notification_delivery_enabled: bool = False
    push_trigger_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_audit_payload_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    native_mobile_ui_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.ledger_ref, "ledger_ref"),
            (self.source_record_ref, "source_record_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.sensor_scope_ref, "sensor_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for entry_ref in self.sensor_audit_entries:
            _validate_m61_ref(entry_ref, "sensor_audit_entries")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_mobile_sensor_audit_ledger_record(
    *,
    source_record: MobileKillSwitchRevocationRecord,
    policy: MobileSensorAuditLedgerPolicy | None = None,
) -> MobileSensorAuditLedgerRecord:
    active_policy = validate_mobile_sensor_audit_ledger_policy(
        policy or MobileSensorAuditLedgerPolicy()
    )
    validated_source = validate_mobile_kill_switch_revocation_record(source_record)
    record = MobileSensorAuditLedgerRecord(
        ledger_ref="mobile-sensor-audit-ledger:m109",
        source_record=validated_source,
        source_record_ref=validated_source.record_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        safe_device_ref="safe-device-ref:m109:mobile-companion",
        sensor_scope_ref="safe-sensor-scope-ref:m109:mobile-companion",
        audit_ref="audit-ref:m109:mobile-sensor-audit-ledger",
        replay_ref="replay-ref:m109:mobile-sensor-audit-ledger",
        sensor_audit_entries=[
            "safe-sensor-audit-entry-ref:m109:location-off",
            "safe-sensor-audit-entry-ref:m109:camera-photos-off",
            "safe-sensor-audit-entry-ref:m109:background-collection-off",
        ],
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        device_bound=active_policy.device_binding_required,
        sensor_scope_bound=active_policy.sensor_scope_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M109_MOBILE_SENSOR_AUDIT_LEDGER",
            "M109_REVIEW_ONLY_SENSOR_AUDIT",
            "M109_SAFE_SENSOR_REFS_ONLY",
            "M109_NO_SENSOR_ACCESS",
            "M109_NO_RAW_SENSOR_PAYLOAD",
            "M110_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M109 records mobile sensor audit ledger entries for review only "
            "using safe refs. It does not access sensors, read sensor data, "
            "store payloads, collect in the background, sync over a network, "
            "write memory, inject context, execute, add routes, add controls, "
            "or grant production authority."
        ),
    )
    return validate_mobile_sensor_audit_ledger_record(record)


def validate_mobile_sensor_audit_ledger_policy(
    policy: MobileSensorAuditLedgerPolicy,
) -> MobileSensorAuditLedgerPolicy:
    validated = MobileSensorAuditLedgerPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M109_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M109_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m109_metadata(validated.metadata)
    return validated


def validate_mobile_sensor_audit_ledger_record(
    record: MobileSensorAuditLedgerRecord,
) -> MobileSensorAuditLedgerRecord:
    payload = _model_payload(record)
    for field_name, reason in _M109_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileSensorAuditLedgerRecord):
        raise ValueError("SECRET_LIKE_M109_SENSOR_AUDIT_CONTENT_DENIED")
    source_payload = payload.get("source_record")
    if isinstance(source_payload, dict):
        source_payload = MobileKillSwitchRevocationRecord.model_validate(source_payload)
    try:
        source_record = validate_mobile_kill_switch_revocation_record(source_payload)
    except ValueError:
        raise
    validated = MobileSensorAuditLedgerRecord.model_validate(payload)
    for field_name, reason in _M109_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.sensor_audit_entries:
        raise ValueError("M109_SENSOR_AUDIT_ENTRY_REQUIRED")
    for field_name, reason in _M109_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileSensorAuditLedgerStatus.review_only_contract:
        raise ValueError("M109_REVIEW_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m109_bindings(validated, source_record)
    _validate_m109_metadata(validated.metadata)
    return validated


def _validate_m109_bindings(
    record: MobileSensorAuditLedgerRecord,
    source_record: MobileKillSwitchRevocationRecord,
) -> None:
    if record.source_record_ref != source_record.record_ref:
        raise ValueError("M109_SOURCE_RECORD_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M109_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M109_ACTOR_BINDING_MISMATCH")
    if not record.safe_device_ref.startswith("safe-device-ref:"):
        raise ValueError("M109_SAFE_DEVICE_REF_REQUIRED")
    if not record.sensor_scope_ref.startswith("safe-sensor-scope-ref:"):
        raise ValueError("M109_SAFE_SENSOR_SCOPE_REF_REQUIRED")
    for entry_ref in record.sensor_audit_entries:
        if not entry_ref.startswith("safe-sensor-audit-entry-ref:"):
            raise ValueError("M109_SAFE_SENSOR_AUDIT_ENTRY_REF_REQUIRED")


def _validate_m109_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M109_SENSOR_AUDIT_CONTENT_DENIED") from exc


_M109_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M109_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M109_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M109_ACTOR_BINDING_REQUIRED"),
    ("device_binding_required", "M109_DEVICE_BINDING_REQUIRED"),
    ("sensor_scope_binding_required", "M109_SENSOR_SCOPE_BINDING_REQUIRED"),
    ("audit_required", "M109_AUDIT_REQUIRED"),
    ("replay_required", "M109_REPLAY_REQUIRED"),
]

_M109_POLICY_DENIALS = [
    ("sensor_access_enabled", "SENSOR_ACCESS_DENIED"),
    ("sensor_read_enabled", "SENSOR_READ_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_audit_payload_enabled", "RAW_AUDIT_PAYLOAD_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
]

_M109_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M109_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M109_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M109_ACTOR_BINDING_REQUIRED"),
    ("device_bound", "M109_DEVICE_BINDING_REQUIRED"),
    ("sensor_scope_bound", "M109_SENSOR_SCOPE_BINDING_REQUIRED"),
    ("audit_required", "M109_AUDIT_REQUIRED"),
    ("replay_safe", "M109_REPLAY_REQUIRED"),
]

_M109_RECORD_DENIALS = [
    ("sensor_access_performed", "SENSOR_ACCESS_DENIED"),
    ("sensor_access_enabled", "SENSOR_ACCESS_DENIED"),
    ("sensor_read_enabled", "SENSOR_READ_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_audit_payload_enabled", "RAW_AUDIT_PAYLOAD_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]
