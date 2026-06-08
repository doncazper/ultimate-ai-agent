import pytest

import ultimate_ai_agent.core.mobile_companion as mobile_companion


def _source_record():
    return mobile_companion.build_mobile_kill_switch_revocation_record(
        source_report=mobile_companion.build_mobile_approval_renewal_ux_report()
    )


def test_m109_mobile_sensor_audit_ledger_is_review_only_and_non_authoritative() -> None:
    source_record = _source_record()
    record = mobile_companion.build_mobile_sensor_audit_ledger_record(source_record=source_record)

    assert record.status == mobile_companion.MobileSensorAuditLedgerStatus.review_only_contract
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.device_bound is True
    assert record.sensor_scope_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_record_ref == source_record.record_ref
    assert record.source_baseline_ref == source_record.source_baseline_ref
    assert record.actor_ref == source_record.actor_ref
    assert record.sensor_audit_entries
    assert record.sensor_access_performed is False
    assert record.sensor_read_enabled is False
    assert record.raw_sensor_payload_enabled is False
    assert record.location_access_enabled is False
    assert record.camera_access_enabled is False
    assert record.photos_access_enabled is False
    assert record.microphone_access_enabled is False
    assert record.background_collection_enabled is False
    assert record.notification_delivery_enabled is False
    assert record.push_trigger_enabled is False
    assert record.network_sync_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.production_authority_enabled is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M109_MOBILE_SENSOR_AUDIT_LEDGER",
        "M109_REVIEW_ONLY_SENSOR_AUDIT",
        "M109_SAFE_SENSOR_REFS_ONLY",
        "M109_NO_SENSOR_ACCESS",
        "M109_NO_RAW_SENSOR_PAYLOAD",
        "M110_REMAINS_FUTURE",
    ]


def test_m109_mobile_sensor_audit_ledger_uses_safe_refs_only() -> None:
    record = mobile_companion.build_mobile_sensor_audit_ledger_record(source_record=_source_record())

    assert record.ledger_ref == "mobile-sensor-audit-ledger:m109"
    assert record.source_record_ref.startswith("mobile-kill-switch-revocation-record:")
    assert record.safe_device_ref.startswith("safe-device-ref:")
    assert record.sensor_scope_ref.startswith("safe-sensor-scope-ref:")
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert all(entry.startswith("safe-sensor-audit-entry-ref:") for entry in record.sensor_audit_entries)
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "raw sensor" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
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
    ],
)
def test_m109_policy_denies_sensor_audit_runtime_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        mobile_companion.validate_mobile_sensor_audit_ledger_policy(
            mobile_companion.MobileSensorAuditLedgerPolicy(**{field: True})
        )


def test_m109_record_denies_model_copy_runtime_flags() -> None:
    record = mobile_companion.build_mobile_sensor_audit_ledger_record(source_record=_source_record())

    for update, reason in [
        ({"review_only": False}, "M109_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M109_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M109_ACTOR_BINDING_REQUIRED"),
        ({"device_bound": False}, "M109_DEVICE_BINDING_REQUIRED"),
        ({"sensor_scope_bound": False}, "M109_SENSOR_SCOPE_BINDING_REQUIRED"),
        ({"sensor_audit_entries": []}, "M109_SENSOR_AUDIT_ENTRY_REQUIRED"),
        ({"sensor_access_performed": True}, "SENSOR_ACCESS_DENIED"),
        ({"sensor_read_enabled": True}, "SENSOR_READ_DENIED"),
        ({"raw_sensor_payload_enabled": True}, "RAW_SENSOR_PAYLOAD_DENIED"),
        ({"location_access_enabled": True}, "LOCATION_ACCESS_DENIED"),
        ({"camera_access_enabled": True}, "CAMERA_ACCESS_DENIED"),
        ({"photos_access_enabled": True}, "PHOTOS_ACCESS_DENIED"),
        ({"microphone_access_enabled": True}, "MICROPHONE_ACCESS_DENIED"),
        ({"background_collection_enabled": True}, "BACKGROUND_COLLECTION_DENIED"),
        ({"raw_audit_payload_enabled": True}, "RAW_AUDIT_PAYLOAD_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["read location sensor"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            mobile_companion.validate_mobile_sensor_audit_ledger_record(record.model_copy(update=update))


def test_m109_record_denies_binding_drift_and_secret_metadata() -> None:
    record = mobile_companion.build_mobile_sensor_audit_ledger_record(source_record=_source_record())

    for update, reason in [
        ({"source_record_ref": "mobile-kill-switch-revocation-record:other"}, "M109_SOURCE_RECORD_BINDING_MISMATCH"),
        ({"source_baseline_ref": "baseline:other"}, "M109_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M109_ACTOR_BINDING_MISMATCH"),
        ({"safe_device_ref": "unsafe-device-ref:m109"}, "M109_SAFE_DEVICE_REF_REQUIRED"),
        ({"sensor_scope_ref": "sensor-scope:m109"}, "M109_SAFE_SENSOR_SCOPE_REF_REQUIRED"),
        ({"metadata": {"sensor_token": "abc123supersecret"}}, "SECRET_LIKE_M109_SENSOR_AUDIT_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            mobile_companion.validate_mobile_sensor_audit_ledger_record(record.model_copy(update=update))


def test_m109_requires_safe_source_record() -> None:
    source_record = _source_record().model_copy(update={"kill_switch_activated": True})

    with pytest.raises(ValueError, match="KILL_SWITCH_ACTIVATION_DENIED"):
        mobile_companion.build_mobile_sensor_audit_ledger_record(source_record=source_record)
