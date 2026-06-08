import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileBackgroundStatusSyncChannel,
    MobileBackgroundStatusSyncPolicy,
    MobileBackgroundStatusSyncStatus,
    build_mobile_background_read_only_status_sync_report,
    validate_mobile_background_status_snapshot,
    validate_mobile_background_status_sync_policy,
    validate_mobile_background_status_sync_report,
)


def test_m106_status_sync_is_read_only_contract_and_no_background_runtime() -> None:
    report = build_mobile_background_read_only_status_sync_report()

    assert report.status == MobileBackgroundStatusSyncStatus.read_only_contract
    assert report.contract_only is True
    assert report.read_only is True
    assert report.safe_refs_required is True
    assert report.no_background_collection is True
    assert report.no_background_execution is True
    assert report.status_snapshots
    assert report.background_worker_enabled is False
    assert report.scheduler_enabled is False
    assert report.daemon_enabled is False
    assert report.os_background_fetch_enabled is False
    assert report.os_background_permission_prompt_enabled is False
    assert report.push_trigger_enabled is False
    assert report.device_token_handling_enabled is False
    assert report.external_service_enabled is False
    assert report.network_sync_enabled is False
    assert report.raw_status_payload_enabled is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M106_MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC",
        "M106_SAFE_STATUS_REFS_ONLY",
        "M106_READ_ONLY_CONTRACT",
        "M106_NO_BACKGROUND_WORKER",
        "M106_NO_NETWORK_SYNC",
        "M107_REMAINS_FUTURE",
    ]


def test_m106_status_snapshots_are_safe_refs_only() -> None:
    report = build_mobile_background_read_only_status_sync_report()

    assert {snapshot.channel for snapshot in report.status_snapshots} == {
        MobileBackgroundStatusSyncChannel.local_status_snapshot,
        MobileBackgroundStatusSyncChannel.sync_health_snapshot,
    }
    for snapshot in report.status_snapshots:
        assert snapshot.status_snapshot_ref.startswith("background-status-snapshot:m106:")
        assert snapshot.background_task_plan_ref.startswith("background-task-plan:m105:")
        assert snapshot.safe_device_ref.startswith("safe-device-ref:")
        assert snapshot.safe_status_ref.startswith("safe-background-status-ref:")
        assert snapshot.safe_status_summary_ref.startswith("safe-background-status-summary:")
        assert snapshot.safe_observed_at_ref.startswith("safe-observed-at-ref:")
        assert snapshot.audit_ref.startswith("audit-ref:")
        assert snapshot.read_only is True
        assert snapshot.safe_refs_only is True
        assert snapshot.no_background_collection is True
        assert snapshot.background_worker_enabled is False
        assert snapshot.network_sync_enabled is False
        assert snapshot.raw_status_payload_enabled is False
        assert snapshot.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "SCHEDULER_DENIED"),
        ("daemon_enabled", "DAEMON_DENIED"),
        ("os_background_fetch_enabled", "OS_BACKGROUND_FETCH_DENIED"),
        ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
        ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
        ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
        ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
        ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
        ("raw_status_payload_enabled", "RAW_STATUS_PAYLOAD_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m106_policy_denies_runtime_sync_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_background_status_sync_policy(
            MobileBackgroundStatusSyncPolicy(**{field: True})
        )


def test_m106_status_snapshot_denies_model_copy_runtime_flags() -> None:
    report = build_mobile_background_read_only_status_sync_report()
    snapshot = report.status_snapshots[0]

    for update, reason in [
        ({"read_only": False}, "M106_READ_ONLY_REQUIRED"),
        ({"safe_refs_only": False}, "M106_SAFE_REFS_REQUIRED"),
        ({"no_background_collection": False}, "M106_NO_BACKGROUND_COLLECTION_REQUIRED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"network_sync_enabled": True}, "NETWORK_SYNC_DENIED"),
        ({"raw_status_payload_enabled": True}, "RAW_STATUS_PAYLOAD_DENIED"),
        ({"side_effects_performed": ["synced in background"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_background_status_snapshot(snapshot.model_copy(update=update))


def test_m106_report_revalidates_model_copy_runtime_flags() -> None:
    report = build_mobile_background_read_only_status_sync_report()

    for update, reason in [
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"daemon_enabled": True}, "DAEMON_DENIED"),
        ({"os_background_fetch_enabled": True}, "OS_BACKGROUND_FETCH_DENIED"),
        ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
        ({"device_token_handling_enabled": True}, "DEVICE_TOKEN_HANDLING_DENIED"),
        ({"external_service_enabled": True}, "EXTERNAL_SERVICE_DENIED"),
        ({"network_sync_enabled": True}, "NETWORK_SYNC_DENIED"),
        ({"raw_status_payload_enabled": True}, "RAW_STATUS_PAYLOAD_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["performed sync"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_background_status_sync_report(report.model_copy(update=update))


def test_m106_rejects_duplicate_refs_and_secret_metadata() -> None:
    report = build_mobile_background_read_only_status_sync_report()
    duplicate = report.model_copy(
        update={
            "status_snapshots": [
                report.status_snapshots[0],
                report.status_snapshots[0],
            ]
        }
    )

    with pytest.raises(ValueError, match="M106_STATUS_SNAPSHOT_REF_DUPLICATE"):
        validate_mobile_background_status_sync_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M106_BACKGROUND_STATUS_CONTENT_DENIED"):
        validate_mobile_background_status_sync_report(
            report.model_copy(update={"metadata": {"status_token": "abc123supersecret"}})
        )
