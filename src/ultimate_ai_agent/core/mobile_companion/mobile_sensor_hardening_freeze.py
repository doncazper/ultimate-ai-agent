from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.mobile_companion.mobile_sensor_audit_ledger import (
    MobileSensorAuditLedgerRecord,
    validate_mobile_sensor_audit_ledger_record,
)


MOBILE_SENSOR_HARDENING_FREEZE_DOCS = [
    "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE.md",
    "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_POLICY.md",
    "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_SENSOR_HARDENING_FREEZE_NON_GOALS.md",
    "docs/mobile/M110_TO_M111_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileSensorHardeningFreezeStatus(str, Enum):
    freeze_only_contract = "freeze_only_contract"


class _MobileSensorHardeningFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileSensorHardeningFreezePolicy(_MobileSensorHardeningFreezeModel):
    policy_ref: str = "mobile-sensor-hardening-freeze-policy:m110"
    contract_only: bool = True
    review_only_required: bool = True
    freeze_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    device_binding_required: bool = True
    sensor_scope_binding_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    hardening_runtime_enabled: bool = False
    sensor_access_enabled: bool = False
    sensor_read_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    background_collection_enabled: bool = False
    native_mobile_ui_enabled: bool = False
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
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileSensorHardeningFreezeRecord(_MobileSensorHardeningFreezeModel):
    freeze_ref: str
    source_record: MobileSensorAuditLedgerRecord
    source_ledger_ref: str
    source_baseline_ref: str
    actor_ref: str
    safe_device_ref: str
    sensor_scope_ref: str
    hardening_checklist_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: MobileSensorHardeningFreezeStatus = (
        MobileSensorHardeningFreezeStatus.freeze_only_contract
    )
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    device_bound: bool = True
    sensor_scope_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    hardening_runtime_enabled: bool = False
    sensor_access_performed: bool = False
    sensor_access_enabled: bool = False
    sensor_read_enabled: bool = False
    raw_sensor_payload_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    background_collection_enabled: bool = False
    native_mobile_ui_enabled: bool = False
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
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.freeze_ref, "freeze_ref"),
            (self.source_ledger_ref, "source_ledger_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.sensor_scope_ref, "sensor_scope_ref"),
            (self.hardening_checklist_ref, "hardening_checklist_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for checkpoint_ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(checkpoint_ref, "accepted_checkpoint_refs")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_mobile_sensor_hardening_freeze_record(
    *,
    source_record: MobileSensorAuditLedgerRecord,
    policy: MobileSensorHardeningFreezePolicy | None = None,
) -> MobileSensorHardeningFreezeRecord:
    active_policy = validate_mobile_sensor_hardening_freeze_policy(
        policy or MobileSensorHardeningFreezePolicy()
    )
    validated_source = validate_mobile_sensor_audit_ledger_record(source_record)
    record = MobileSensorHardeningFreezeRecord(
        freeze_ref="mobile-sensor-hardening-freeze:m110",
        source_record=validated_source,
        source_ledger_ref=validated_source.ledger_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        safe_device_ref=validated_source.safe_device_ref,
        sensor_scope_ref=validated_source.sensor_scope_ref,
        hardening_checklist_ref="hardening-checklist-ref:m110:mobile-sensor-freeze",
        audit_ref="audit-ref:m110:mobile-sensor-hardening-freeze",
        replay_ref="replay-ref:m110:mobile-sensor-hardening-freeze",
        accepted_checkpoint_refs=[
            "checkpoint:m101",
            "checkpoint:m102",
            "checkpoint:m103",
            "checkpoint:m104",
            "checkpoint:m105",
            "checkpoint:m106",
            "checkpoint:m107",
            "checkpoint:m108",
            "checkpoint:m109",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m110:mobile-sensor-hardening-freeze:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        freeze_only=active_policy.freeze_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        device_bound=active_policy.device_binding_required,
        sensor_scope_bound=active_policy.sensor_scope_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M110_MOBILE_SENSOR_HARDENING_FREEZE",
            "M110_FREEZE_ONLY_SENSOR_HARDENING",
            "M110_SAFE_REFS_ONLY",
            "M110_NO_SENSOR_ACCESS",
            "M110_NO_RUNTIME_AUTHORITY",
            "M111_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M110 freezes the mobile sensor contract surface for review only "
            "using safe refs, hardening checklist refs, audit refs, replay refs, "
            "and a no-effect receipt plan. It does not access sensors, read "
            "sensor data, store payloads, collect in the background, create "
            "native mobile UI, sync over a network, write memory, inject "
            "context, execute, add routes, add controls, add dependencies, "
            "or grant production authority."
        ),
    )
    return validate_mobile_sensor_hardening_freeze_record(record)


def validate_mobile_sensor_hardening_freeze_policy(
    policy: MobileSensorHardeningFreezePolicy,
) -> MobileSensorHardeningFreezePolicy:
    validated = MobileSensorHardeningFreezePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M110_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M110_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m110_metadata(validated.metadata)
    return validated


def validate_mobile_sensor_hardening_freeze_record(
    record: MobileSensorHardeningFreezeRecord,
) -> MobileSensorHardeningFreezeRecord:
    payload = _model_payload(record)
    for field_name, reason in _M110_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileSensorHardeningFreezeRecord):
        raise ValueError("SECRET_LIKE_M110_SENSOR_HARDENING_CONTENT_DENIED")
    source_payload = payload.get("source_record")
    if isinstance(source_payload, dict):
        source_payload = MobileSensorAuditLedgerRecord.model_validate(source_payload)
    source_record = validate_mobile_sensor_audit_ledger_record(source_payload)
    validated = MobileSensorHardeningFreezeRecord.model_validate(payload)
    for field_name, reason in _M110_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if not validated.accepted_checkpoint_refs:
        raise ValueError("M110_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for field_name, reason in _M110_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileSensorHardeningFreezeStatus.freeze_only_contract:
        raise ValueError("M110_FREEZE_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m110_bindings(validated, source_record)
    _validate_m110_metadata(validated.metadata)
    return validated


def _validate_m110_bindings(
    record: MobileSensorHardeningFreezeRecord,
    source_record: MobileSensorAuditLedgerRecord,
) -> None:
    if record.source_ledger_ref != source_record.ledger_ref:
        raise ValueError("M110_SOURCE_LEDGER_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M110_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M110_ACTOR_BINDING_MISMATCH")
    if not record.safe_device_ref.startswith("safe-device-ref:"):
        raise ValueError("M110_SAFE_DEVICE_REF_REQUIRED")
    if not record.sensor_scope_ref.startswith("safe-sensor-scope-ref:"):
        raise ValueError("M110_SAFE_SENSOR_SCOPE_REF_REQUIRED")
    if record.safe_device_ref != source_record.safe_device_ref:
        raise ValueError("M110_SAFE_DEVICE_BINDING_MISMATCH")
    if record.sensor_scope_ref != source_record.sensor_scope_ref:
        raise ValueError("M110_SENSOR_SCOPE_BINDING_MISMATCH")
    if not record.hardening_checklist_ref.startswith("hardening-checklist-ref:"):
        raise ValueError("M110_HARDENING_CHECKLIST_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M110_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M110_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m110_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M110_SENSOR_HARDENING_CONTENT_DENIED") from exc


_M110_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M110_REVIEW_ONLY_REQUIRED"),
    ("freeze_only_required", "M110_FREEZE_ONLY_REQUIRED"),
    ("safe_refs_required", "M110_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M110_ACTOR_BINDING_REQUIRED"),
    ("device_binding_required", "M110_DEVICE_BINDING_REQUIRED"),
    ("sensor_scope_binding_required", "M110_SENSOR_SCOPE_BINDING_REQUIRED"),
    ("audit_required", "M110_AUDIT_REQUIRED"),
    ("replay_required", "M110_REPLAY_REQUIRED"),
]

_M110_POLICY_DENIALS = [
    ("hardening_runtime_enabled", "HARDENING_RUNTIME_DENIED"),
    ("sensor_access_enabled", "SENSOR_ACCESS_DENIED"),
    ("sensor_read_enabled", "SENSOR_READ_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
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
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M110_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M110_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M110_FREEZE_ONLY_REQUIRED"),
    ("safe_refs_required", "M110_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M110_ACTOR_BINDING_REQUIRED"),
    ("device_bound", "M110_DEVICE_BINDING_REQUIRED"),
    ("sensor_scope_bound", "M110_SENSOR_SCOPE_BINDING_REQUIRED"),
    ("audit_required", "M110_AUDIT_REQUIRED"),
    ("replay_safe", "M110_REPLAY_REQUIRED"),
]

_M110_RECORD_DENIALS = [
    ("hardening_runtime_enabled", "HARDENING_RUNTIME_DENIED"),
    ("sensor_access_performed", "SENSOR_ACCESS_DENIED"),
    ("sensor_access_enabled", "SENSOR_ACCESS_DENIED"),
    ("sensor_read_enabled", "SENSOR_READ_DENIED"),
    ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
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
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]
