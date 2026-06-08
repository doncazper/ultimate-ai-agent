import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileKillSwitchRevocationPolicy,
    MobileKillSwitchRevocationStatus,
    build_mobile_approval_renewal_ux_report,
    build_mobile_kill_switch_revocation_record,
    validate_mobile_kill_switch_revocation_policy,
    validate_mobile_kill_switch_revocation_record,
)


def test_m108_mobile_kill_switch_revocation_is_review_only_and_non_authoritative() -> None:
    source_report = build_mobile_approval_renewal_ux_report()
    record = build_mobile_kill_switch_revocation_record(source_report=source_report)

    assert record.status == MobileKillSwitchRevocationStatus.review_only_contract
    assert record.contract_only is True
    assert record.review_only is True
    assert record.safe_refs_required is True
    assert record.actor_bound is True
    assert record.device_bound is True
    assert record.approval_bound is True
    assert record.revocation_bound is True
    assert record.audit_required is True
    assert record.replay_safe is True
    assert record.source_report_ref == source_report.report_ref
    assert record.source_baseline_ref == source_report.baseline_ref
    assert record.actor_ref == source_report.actor_ref
    assert record.revocation_requested is True
    assert record.kill_switch_requested is True
    assert record.revocation_performed is False
    assert record.kill_switch_activated is False
    assert record.session_stopped is False
    assert record.approval_revoked is False
    assert record.notification_delivery_enabled is False
    assert record.push_trigger_enabled is False
    assert record.background_worker_enabled is False
    assert record.scheduler_enabled is False
    assert record.daemon_enabled is False
    assert record.device_token_handling_enabled is False
    assert record.external_service_enabled is False
    assert record.network_sync_enabled is False
    assert record.raw_approval_payload_enabled is False
    assert record.memory_write_enabled is False
    assert record.context_injection_enabled is False
    assert record.execution_enabled is False
    assert record.production_authority_enabled is False
    assert record.side_effects_performed == []
    assert record.reason_codes == [
        "M108_MOBILE_KILL_SWITCH_REVOCATION",
        "M108_REVIEW_ONLY_REVOCATION_RECORD",
        "M108_SAFE_REVOCATION_REFS_ONLY",
        "M108_NO_KILL_SWITCH_EXECUTION",
        "M108_NO_REVOCATION_EXECUTION",
        "M109_REMAINS_FUTURE",
    ]


def test_m108_mobile_kill_switch_revocation_uses_safe_refs_only() -> None:
    record = build_mobile_kill_switch_revocation_record(
        source_report=build_mobile_approval_renewal_ux_report()
    )

    assert record.record_ref == "mobile-kill-switch-revocation-record:m108"
    assert record.source_report_ref.startswith("mobile-approval-renewal-ux-report:")
    assert record.safe_device_ref.startswith("safe-device-ref:")
    assert record.approval_ref.startswith("approval-ref:m108:")
    assert record.safe_revocation_reason_ref.startswith("safe-revocation-reason-ref:")
    assert record.safe_kill_switch_reason_ref.startswith("safe-kill-switch-reason-ref:")
    assert record.revocation_ref.startswith("revocation-ref:")
    assert record.audit_ref.startswith("audit-ref:")
    assert record.replay_ref.startswith("replay-ref:")
    assert "secret" not in record.safe_summary.lower()
    assert "token" not in record.safe_summary.lower()
    assert "raw approval" not in record.safe_summary.lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("revocation_execution_enabled", "REVOCATION_EXECUTION_DENIED"),
        ("kill_switch_execution_enabled", "KILL_SWITCH_EXECUTION_DENIED"),
        ("approval_revocation_enabled", "APPROVAL_REVOCATION_DENIED"),
        ("session_stop_enabled", "SESSION_STOP_DENIED"),
        ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
        ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "SCHEDULER_DENIED"),
        ("daemon_enabled", "DAEMON_DENIED"),
        ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
        ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
        ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
        ("raw_approval_payload_enabled", "RAW_APPROVAL_PAYLOAD_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ],
)
def test_m108_policy_denies_runtime_revocation_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_kill_switch_revocation_policy(
            MobileKillSwitchRevocationPolicy(**{field: True})
        )


def test_m108_record_denies_model_copy_runtime_flags() -> None:
    record = build_mobile_kill_switch_revocation_record(
        source_report=build_mobile_approval_renewal_ux_report()
    )

    for update, reason in [
        ({"review_only": False}, "M108_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_required": False}, "M108_SAFE_REFS_REQUIRED"),
        ({"actor_bound": False}, "M108_ACTOR_BINDING_REQUIRED"),
        ({"device_bound": False}, "M108_DEVICE_BINDING_REQUIRED"),
        ({"approval_bound": False}, "M108_APPROVAL_BINDING_REQUIRED"),
        ({"revocation_bound": False}, "M108_REVOCATION_BINDING_REQUIRED"),
        ({"revocation_performed": True}, "REVOCATION_ACTION_DENIED"),
        ({"kill_switch_activated": True}, "KILL_SWITCH_ACTIVATION_DENIED"),
        ({"session_stopped": True}, "SESSION_STOP_DENIED"),
        ({"approval_revoked": True}, "APPROVAL_REVOCATION_DENIED"),
        ({"revocation_execution_enabled": True}, "REVOCATION_EXECUTION_DENIED"),
        ({"kill_switch_execution_enabled": True}, "KILL_SWITCH_EXECUTION_DENIED"),
        ({"raw_approval_payload_enabled": True}, "RAW_APPROVAL_PAYLOAD_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["stopped mobile session"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_kill_switch_revocation_record(record.model_copy(update=update))


def test_m108_record_denies_binding_drift_and_secret_metadata() -> None:
    record = build_mobile_kill_switch_revocation_record(
        source_report=build_mobile_approval_renewal_ux_report()
    )

    for update, reason in [
        ({"source_report_ref": "mobile-approval-renewal-ux-report:other"}, "M108_SOURCE_REPORT_BINDING_MISMATCH"),
        ({"source_baseline_ref": "baseline:other"}, "M108_BASELINE_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M108_ACTOR_BINDING_MISMATCH"),
        ({"approval_ref": "approval_test_:m108"}, "APPROVAL_TEST_REF_DENIED"),
        ({"metadata": {"approval_token": "abc123supersecret"}}, "SECRET_LIKE_M108_KILL_SWITCH_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_kill_switch_revocation_record(record.model_copy(update=update))


def test_m108_requires_safe_source_report() -> None:
    source_report = build_mobile_approval_renewal_ux_report().model_copy(
        update={"approval_renewal_execution_enabled": True}
    )

    with pytest.raises(ValueError, match="APPROVAL_RENEWAL_EXECUTION_DENIED"):
        build_mobile_kill_switch_revocation_record(source_report=source_report)
