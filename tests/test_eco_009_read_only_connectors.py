from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.connectors.read_only_platform import (
    CalendarMetadataSnapshotAdapter,
    CalendarMetadataSnapshotRow,
    ConnectorReadPlatform,
    ConnectorReadPolicy,
    ConnectorReadRequest,
    ConnectorReadStatus,
    ConnectorSourceState,
    build_eco009_connector_read_platform_posture,
)


NOW = datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc)
WORKSPACE_REF = "workspace-ref:eco-009:test"
SOURCE_REF = "connector-source-ref:eco-009:calendar-test"


def _rows(count: int = 3) -> tuple[CalendarMetadataSnapshotRow, ...]:
    return tuple(
        CalendarMetadataSnapshotRow(
            event_ref=f"calendar-event-ref:test-{index}",
            starts_at=NOW + timedelta(hours=index),
            ends_at=NOW + timedelta(hours=index + 1),
            availability_ref="availability-ref:busy",
            provenance_ref="provenance-ref:caller-supplied-redacted-fixture",
            source_revision_ref="source-revision-ref:test-v1",
        )
        for index in range(count)
    )


def _platform(
    *,
    count: int = 3,
    policy: ConnectorReadPolicy | None = None,
) -> ConnectorReadPlatform:
    platform = ConnectorReadPlatform(policy=policy)
    platform.register_calendar_snapshot(
        CalendarMetadataSnapshotAdapter(
            source_ref=SOURCE_REF,
            workspace_ref=WORKSPACE_REF,
            rows=_rows(count),
            provenance_ref="provenance-ref:caller-supplied-redacted-fixture",
        )
    )
    return platform


def _request(
    request_ref: str = "request-ref:eco-009:test-1",
    **updates: object,
) -> ConnectorReadRequest:
    payload: dict[str, object] = {
        "request_ref": request_ref,
        "workspace_ref": WORKSPACE_REF,
        "source_ref": SOURCE_REF,
        "field_refs": ("event_ref", "starts_at", "ends_at", "availability_ref"),
        "starts_at": NOW,
        "ends_at": NOW + timedelta(days=1),
        "limit": 2,
    }
    payload.update(updates)
    return ConnectorReadRequest.model_validate(payload)


def test_bounded_snapshot_read_returns_only_requested_metadata() -> None:
    platform = _platform()

    outcome = platform.read(_request(), now=NOW)

    assert outcome.status == ConnectorReadStatus.completed
    assert len(outcome.items) == 2
    assert set(outcome.items[0].field_values) == {
        "event_ref",
        "starts_at",
        "ends_at",
        "availability_ref",
    }
    assert outcome.next_cursor_ref is not None
    assert outcome.external_read_performed is False
    assert outcome.network_access_performed is False
    assert outcome.account_auth_performed is False
    assert outcome.connector_write_performed is False
    assert outcome.raw_content_included is False
    assert outcome.model_call_performed is False
    assert outcome.production_authority_granted is False


def test_cursor_is_bound_and_expires() -> None:
    platform = _platform()
    first = platform.read(_request(), now=NOW)
    assert first.next_cursor_ref is not None

    second = platform.read(
        _request(
            "request-ref:eco-009:test-2",
            cursor_ref=first.next_cursor_ref,
        ),
        now=NOW + timedelta(seconds=1),
    )
    assert second.status == ConnectorReadStatus.completed
    assert len(second.items) == 1
    assert second.next_cursor_ref is None

    changed_scope = platform.read(
        _request(
            "request-ref:eco-009:test-3",
            cursor_ref=first.next_cursor_ref,
            field_refs=("event_ref",),
        ),
        now=NOW + timedelta(seconds=2),
    )
    assert changed_scope.status == ConnectorReadStatus.invalid_cursor

    expired = platform.read(
        _request(
            "request-ref:eco-009:test-4",
            cursor_ref=first.next_cursor_ref,
        ),
        now=NOW + timedelta(minutes=16),
    )
    assert expired.status == ConnectorReadStatus.invalid_cursor


def test_request_ref_is_idempotent_and_conflicts_fail_closed() -> None:
    platform = _platform()
    request = _request()

    first = platform.read(request, now=NOW)
    replay = platform.read(request, now=NOW + timedelta(seconds=5))
    conflict = platform.read(
        _request(field_refs=("event_ref",)),
        now=NOW + timedelta(seconds=6),
    )

    assert replay == first
    assert conflict.status == ConnectorReadStatus.invalid_scope
    assert conflict.items == ()
    assert conflict.reason_refs == ("reason-ref:eco-009:request-ref-conflict",)


@pytest.mark.parametrize(
    ("platform", "read_request", "status", "reason_ref"),
    [
        (
            ConnectorReadPlatform(),
            _request(),
            ConnectorReadStatus.source_not_configured,
            "reason-ref:eco-009:source-not-configured",
        ),
        (
            _platform(),
            _request(workspace_ref="workspace-ref:eco-009:other"),
            ConnectorReadStatus.invalid_scope,
            "reason-ref:eco-009:workspace-binding-mismatch",
        ),
        (
            _platform(policy=ConnectorReadPolicy(max_page_size=1)),
            _request(limit=2),
            ConnectorReadStatus.invalid_scope,
            "reason-ref:eco-009:request-bounds-exceeded",
        ),
    ],
)
def test_invalid_or_unavailable_source_requests_fail_closed(
    platform: ConnectorReadPlatform,
    read_request: ConnectorReadRequest,
    status: ConnectorReadStatus,
    reason_ref: str,
) -> None:
    outcome = platform.read(read_request, now=NOW)

    assert outcome.status == status
    assert outcome.reason_refs == (reason_ref,)
    assert outcome.items == ()
    assert outcome.external_read_performed is False
    assert outcome.connector_write_performed is False


def test_revocation_and_safe_disable_fail_closed() -> None:
    revoked = _platform()
    successful = revoked.read(_request(), now=NOW)
    assert successful.status == ConnectorReadStatus.completed
    revoked.revoke_source(SOURCE_REF, "revocation-ref:eco-009:test")
    revoked_outcome = revoked.read(_request(), now=NOW)
    assert revoked_outcome.status == ConnectorReadStatus.source_revoked
    assert revoked_outcome.items == ()
    assert revoked.descriptors()[0].state == ConnectorSourceState.revoked

    disabled = _platform()
    completed = disabled.read(_request(), now=NOW)
    assert completed.status == ConnectorReadStatus.completed
    disabled.set_safe_disable("safe-disable-ref:eco-009:test")
    disabled_outcome = disabled.read(_request(), now=NOW)
    assert disabled_outcome.status == ConnectorReadStatus.safe_disabled
    assert disabled_outcome.items == ()
    assert build_eco009_connector_read_platform_posture(disabled)[
        "safe_disable_active"
    ] is True


def test_rate_limit_is_exact_and_bounded() -> None:
    platform = _platform(
        policy=ConnectorReadPolicy(max_reads_per_minute=1),
    )
    completed = platform.read(_request(), now=NOW)
    limited = platform.read(
        _request("request-ref:eco-009:test-2"),
        now=NOW + timedelta(seconds=1),
    )

    assert completed.status == ConnectorReadStatus.completed
    assert limited.status == ConnectorReadStatus.rate_limited
    assert limited.items == ()


def test_request_and_snapshot_schema_exclude_raw_content_and_unsafe_refs() -> None:
    with pytest.raises(ValidationError):
        CalendarMetadataSnapshotRow(
            event_ref="calendar-event-ref:test",
            starts_at=NOW,
            ends_at=NOW + timedelta(hours=1),
            availability_ref="availability-ref:busy",
            provenance_ref="/Users/example/private.json",
            source_revision_ref="source-revision-ref:test",
        )

    with pytest.raises(ValidationError):
        CalendarMetadataSnapshotRow.model_validate(
            {
                **_rows(1)[0].model_dump(),
                "raw_title": "Private appointment",
            }
        )

    raw_field = _platform().read(
        _request(field_refs=("event_ref", "raw_title")),
        now=NOW,
    )
    assert raw_field.status == ConnectorReadStatus.invalid_scope
    assert raw_field.reason_refs == ("reason-ref:eco-009:field-scope-not-allowed",)
    assert raw_field.items == ()


def test_posture_is_truthful_when_inactive_ready_and_revoked() -> None:
    inactive = build_eco009_connector_read_platform_posture()
    assert inactive["status"] == "implemented_inactive_no_snapshot_source"
    assert inactive["configured_source_count"] == 0

    platform = _platform()
    ready = build_eco009_connector_read_platform_posture(platform)
    assert ready["status"] == "snapshot_source_ready"
    assert ready["configured_source_count"] == 1
    assert ready["ready_source_count"] == 1
    assert ready["safe_disable_active"] is False
    assert ready["fixture_or_caller_supplied_snapshot_only"] is True
    for blocked_flag in (
        "live_account_connected",
        "network_access_enabled",
        "account_auth_enabled",
        "background_sync_enabled",
        "raw_content_enabled",
        "connector_write_enabled",
        "production_authority_enabled",
    ):
        assert ready[blocked_flag] is False

    platform.revoke_source(SOURCE_REF, "revocation-ref:eco-009:test")
    revoked = build_eco009_connector_read_platform_posture(platform)
    assert revoked["status"] == "implemented_inactive_no_snapshot_source"
    assert revoked["revoked_source_count"] == 1
