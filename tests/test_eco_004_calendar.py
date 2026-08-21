from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MUTATION_ACTION,
    CalendarConflict,
    CalendarEvent,
    CalendarParticipant,
    CalendarPortableBundle,
    CalendarRecurrenceFrequency,
    CalendarRecurrenceRule,
    CalendarReminder,
    CalendarRepository,
    CalendarSet,
    CalendarView,
    LocalCalendar,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
)
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MUTATION_ACTION,
    CanonicalTask,
    TaskRepository,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now


WORKSPACE = "workspace-ref:calendar-test"
SET_REF = "calendar-set-ref:primary"
CALENDAR_REF = "calendar-ref:work"
_COUNTER = itertools.count(1)


def _approval(
    authority: LocalApprovalAuthority,
    *,
    action: str,
    resources: tuple[str, ...],
):
    suffix = next(_COUNTER)
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco004_{suffix}",
        run_id="run_eco_004_tests",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco004_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco004_test",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-004 local Calendar mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-004-test",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval_eco004_{suffix}",
    )
    return request.to_validation_request(grant.approval_ref)


def _repositories(
    tmp_path: Path,
) -> tuple[CalendarRepository, TaskRepository, LocalApprovalAuthority, Path]:
    authority = LocalApprovalAuthority()
    database_path = (tmp_path / "ecosystem.sqlite3").resolve()
    platform = EcosystemLocalDataPlatform(
        database_path=database_path,
        crypto_backend=InMemoryLocalDataCryptoBackend(),
        approval_authority=authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    key_ref = "key-version-ref:calendar-v1"
    platform.create_workspace(
        workspace_ref=WORKSPACE,
        key_version_ref=key_ref,
        approval=_approval(
            authority,
            action="ecosystem.local_data.create_workspace",
            resources=(WORKSPACE, key_ref),
        ),
    )
    tasks = TaskRepository(platform)
    return (
        CalendarRepository(platform, task_repository=tasks),
        tasks,
        authority,
        database_path,
    )


def _calendar_set() -> CalendarSet:
    return CalendarSet(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        name="Private calendar set",
        calendars=(
            LocalCalendar(
                calendar_ref=CALENDAR_REF,
                name="Private work calendar",
                timezone="America/Los_Angeles",
            ),
        ),
    )


def _calendar_approval(
    authority: LocalApprovalAuthority,
    *,
    operation_ref: str,
    idempotency_ref: str,
    record_ref: str = SET_REF,
):
    return _approval(
        authority,
        action=ECO_CALENDAR_MUTATION_ACTION,
        resources=CalendarRepository.mutation_resource_refs(
            workspace_ref=WORKSPACE,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            record_ref=record_ref,
        ),
    )


def _create_set(
    repository: CalendarRepository,
    authority: LocalApprovalAuthority,
    calendar_set: CalendarSet | None = None,
):
    calendar_set = calendar_set or _calendar_set()
    operation_ref = f"operation-ref:create-{calendar_set.calendar_set_ref}"
    idempotency_ref = f"idempotency-ref:create-{calendar_set.calendar_set_ref}"
    return repository.create_calendar_set(
        calendar_set=calendar_set,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_calendar_approval(
            authority,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            record_ref=calendar_set.calendar_set_ref,
        ),
    )


def _event(
    *,
    event_ref: str = "event-ref:planning",
    hour: int = 9,
    duration_hours: int = 1,
) -> CalendarEvent:
    zone = ZoneInfo("America/Los_Angeles")
    starts_at = datetime(2026, 3, 7, hour, 0, tzinfo=zone)
    return CalendarEvent(
        event_ref=event_ref,
        calendar_ref=CALENDAR_REF,
        title="Private planning session",
        description="Private event notes",
        location="Private office",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=duration_hours),
        timezone="America/Los_Angeles",
        participant_items=(
            CalendarParticipant(
                participant_ref="participant-ref:one",
                display_name="Private participant",
                address="private@example.invalid",
            ),
        ),
        reminder_items=(
            CalendarReminder(
                reminder_ref="reminder-ref:one",
                minutes_before=15,
            ),
        ),
    )


def _add_event(
    repository: CalendarRepository,
    authority: LocalApprovalAuthority,
    event: CalendarEvent,
    *,
    expected_version: int = 1,
):
    operation_ref = f"operation-ref:add-{event.event_ref}"
    idempotency_ref = f"idempotency-ref:add-{event.event_ref}"
    return repository.add_event(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        event=event,
        expected_version=expected_version,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_calendar_approval(
            authority,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )


def _task_approval(
    authority: LocalApprovalAuthority,
    *,
    task_ref: str,
    operation_ref: str,
    idempotency_ref: str,
):
    return _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=TaskRepository.mutation_resource_refs(
            workspace_ref=WORKSPACE,
            task_ref=task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )


def test_calendar_core_is_encrypted_replayable_and_domain_action_bound(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, database_path = _repositories(tmp_path)
    receipt = _create_set(repository, authority)
    assert receipt.replayed is False
    assert (
        repository.read(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)
        == _calendar_set()
    )
    at_rest = database_path.read_bytes()
    wal = database_path.with_name(f"{database_path.name}-wal")
    if wal.exists():
        at_rest += wal.read_bytes()
    assert b"Private calendar set" not in at_rest
    assert b"Private work calendar" not in at_rest

    replay = _create_set(repository, authority)
    assert replay.replayed is True
    assert replay.receipt_ref == receipt.receipt_ref

    bypass = _calendar_set().model_copy(
        update={"calendar_set_ref": "calendar-set-ref:bypass"}
    )
    operation = PutRecord(
        operation_ref="operation-ref:bypass",
        module_ref="module-ref:calendar",
        record_ref=bypass.calendar_set_ref,
        record_kind_ref="record-kind-ref:calendar-set",
        safe_summary_ref=bypass.safe_summary_ref,
        private_payload=bypass.model_dump(mode="json"),
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_DOMAIN_ACTION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref="idempotency-ref:bypass",
            operations=(operation,),
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=(
                    WORKSPACE,
                    "idempotency-ref:bypass",
                    operation.operation_ref,
                    bypass.calendar_set_ref,
                ),
            ),
        )
    with pytest.raises(
        EcosystemLocalDataError,
        match="ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION",
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref="idempotency-ref:raw-calendar-action",
            operations=(operation,),
            approval=_approval(
                authority,
                action=ECO_CALENDAR_MUTATION_ACTION,
                resources=(
                    WORKSPACE,
                    "idempotency-ref:raw-calendar-action",
                    operation.operation_ref,
                    bypass.calendar_set_ref,
                ),
            ),
            requested_action=ECO_CALENDAR_MUTATION_ACTION,
            request_context_ref="calendar-request-context-ref:raw-denied",
        )


def test_calendar_and_event_crud_is_versioned_and_undoable(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    _add_event(repository, authority, _event())
    stored = repository.read(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)
    assert stored.version == 2
    assert len(stored.events) == 1
    assert stored.events[0].reminder_items[0].delivery_posture == "intent_only"

    archive_operation = "operation-ref:archive-event"
    archive_idempotency = "idempotency-ref:archive-event"
    repository.archive_event(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        event_ref="event-ref:planning",
        expected_version=2,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=_calendar_approval(
            authority,
            operation_ref=archive_operation,
            idempotency_ref=archive_idempotency,
        ),
    )
    assert (
        repository.read(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)
        .events[0]
        .archived
    )

    undo_operation = "operation-ref:undo-archive"
    undo_idempotency = "idempotency-ref:undo-archive"
    repository.undo(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        expected_version=3,
        operation_ref=undo_operation,
        idempotency_ref=undo_idempotency,
        approval=_calendar_approval(
            authority,
            operation_ref=undo_operation,
            idempotency_ref=undo_idempotency,
        ),
    )
    restored = repository.read(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)
    assert restored.version == 4
    assert restored.events[0].archived is False

    with pytest.raises(CalendarConflict, match="ECO_CALENDAR_STALE_VERSION"):
        repository.add_calendar(
            workspace_ref=WORKSPACE,
            calendar_set_ref=SET_REF,
            calendar_item=LocalCalendar(
                calendar_ref="calendar-ref:personal", name="Personal"
            ),
            expected_version=3,
            operation_ref="operation-ref:stale",
            idempotency_ref="idempotency-ref:stale",
            approval=_calendar_approval(
                authority,
                operation_ref="operation-ref:stale",
                idempotency_ref="idempotency-ref:stale",
            ),
        )


def test_daily_recurrence_preserves_wall_time_across_dst_and_views(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    recurring = _event().model_copy(
        update={
            "recurrence": CalendarRecurrenceRule(
                frequency=CalendarRecurrenceFrequency.daily,
                interval=1,
                count=3,
                timezone="America/Los_Angeles",
            )
        }
    )
    _add_event(repository, authority, recurring)
    occurrence_items = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 3, 7, tzinfo=timezone.utc),
        ends_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
    )
    assert [item.occurrence.starts_at.hour for item in occurrence_items] == [9, 9, 9]
    assert [item.occurrence.starts_at.utcoffset() for item in occurrence_items] == [
        timedelta(hours=-8),
        timedelta(hours=-7),
        timedelta(hours=-7),
    ]

    day_view = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 8, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    assert len(day_view.occurrence_items) == 1
    assert day_view.range_ends_at.astimezone(
        timezone.utc
    ) - day_view.range_starts_at.astimezone(timezone.utc) == timedelta(hours=23)


def test_conflicts_are_deterministic_and_adjacent_events_do_not_conflict(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    _add_event(repository, authority, _event(duration_hours=2))
    _add_event(
        repository,
        authority,
        _event(event_ref="event-ref:overlap", hour=10),
        expected_version=2,
    )
    _add_event(
        repository,
        authority,
        _event(event_ref="event-ref:adjacent", hour=11),
        expected_version=3,
    )
    result = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 7, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    assert len(result.occurrence_items) == 3
    assert len(result.conflict_items) == 1
    assert result.conflict_items[0].overlap_ends_at.hour == 11


def test_weekly_and_monthly_recurrence_are_bounded_and_skip_invalid_month_days(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    zone = ZoneInfo("America/Los_Angeles")
    weekly_start = datetime(2020, 1, 6, 9, tzinfo=zone)
    weekly = CalendarEvent(
        event_ref="event-ref:weekly",
        calendar_ref=CALENDAR_REF,
        title="Weekly",
        starts_at=weekly_start,
        ends_at=weekly_start + timedelta(hours=1),
        timezone="America/Los_Angeles",
        recurrence=CalendarRecurrenceRule(
            frequency=CalendarRecurrenceFrequency.weekly,
            interval=1,
            weekdays=(0, 2),
            timezone="America/Los_Angeles",
        ),
    )
    _add_event(repository, authority, weekly)
    monthly_start = datetime(2026, 1, 31, 12, tzinfo=zone)
    monthly = CalendarEvent(
        event_ref="event-ref:monthly",
        calendar_ref=CALENDAR_REF,
        title="Month end",
        starts_at=monthly_start,
        ends_at=monthly_start + timedelta(hours=1),
        timezone="America/Los_Angeles",
        recurrence=CalendarRecurrenceRule(
            frequency=CalendarRecurrenceFrequency.monthly,
            month_day=31,
            count=3,
            timezone="America/Los_Angeles",
        ),
    )
    _add_event(repository, authority, monthly, expected_version=2)

    weekly_occurrences = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 1, 5, tzinfo=zone),
        ends_at=datetime(2026, 1, 12, tzinfo=zone),
        calendar_refs=(CALENDAR_REF,),
    )
    weekly_days = [
        item.occurrence.starts_at.weekday()
        for item in weekly_occurrences
        if item.event.event_ref == "event-ref:weekly"
    ]
    assert weekly_days == [0, 2]

    monthly_occurrences = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 1, 1, tzinfo=zone),
        ends_at=datetime(2026, 6, 1, tzinfo=zone),
    )
    monthly_dates = [
        item.occurrence.starts_at.date()
        for item in monthly_occurrences
        if item.event.event_ref == "event-ref:monthly"
    ]
    assert monthly_dates == [
        datetime(2026, 1, 31).date(),
        datetime(2026, 3, 31).date(),
        datetime(2026, 5, 31).date(),
    ]


def test_nonexistent_dst_wall_time_moves_forward_without_losing_series(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    zone = ZoneInfo("America/Los_Angeles")
    starts_at = datetime(2026, 3, 7, 2, 30, tzinfo=zone)
    event = CalendarEvent(
        event_ref="event-ref:dst-gap",
        calendar_ref=CALENDAR_REF,
        title="DST gap",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
        timezone="America/Los_Angeles",
        recurrence=CalendarRecurrenceRule(
            frequency=CalendarRecurrenceFrequency.daily,
            count=3,
            timezone="America/Los_Angeles",
        ),
    )
    _add_event(repository, authority, event)
    occurrences = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 3, 7, tzinfo=zone),
        ends_at=datetime(2026, 3, 10, tzinfo=zone),
    )
    assert [item.occurrence.starts_at.hour for item in occurrences] == [2, 3, 2]
    assert [item.occurrence.starts_at.minute for item in occurrences] == [30, 30, 30]


def test_fold_aware_event_duration_uses_elapsed_instants(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    zone = ZoneInfo("America/Los_Angeles")
    event = CalendarEvent(
        event_ref="event-ref:fall-fold",
        calendar_ref=CALENDAR_REF,
        title="Fall fold",
        starts_at=datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0),
        ends_at=datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=1),
        timezone="America/Los_Angeles",
    )
    _add_event(repository, authority, event)
    occurrence = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 11, 1, tzinfo=zone),
        ends_at=datetime(2026, 11, 2, tzinfo=zone),
    )[0].occurrence
    assert occurrence.ends_at.astimezone(
        timezone.utc
    ) - occurrence.starts_at.astimezone(timezone.utc) == timedelta(hours=1)
    assert occurrence.ends_at.fold == 1


def test_monthly_recurrence_starts_after_anchor_and_seeks_century_old_series(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    zone = ZoneInfo("America/Los_Angeles")
    starts_at = datetime(2026, 1, 20, 9, tzinfo=zone)
    offset_event = CalendarEvent(
        event_ref="event-ref:monthly-offset",
        calendar_ref=CALENDAR_REF,
        title="Monthly offset",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        timezone="America/Los_Angeles",
        recurrence=CalendarRecurrenceRule(
            frequency=CalendarRecurrenceFrequency.monthly,
            month_day=15,
            count=2,
            timezone="America/Los_Angeles",
        ),
    )
    _add_event(repository, authority, offset_event)
    old_start = datetime(1900, 1, 15, 9, tzinfo=zone)
    old_event = CalendarEvent(
        event_ref="event-ref:century-old",
        calendar_ref=CALENDAR_REF,
        title="Century old",
        starts_at=old_start,
        ends_at=old_start + timedelta(hours=1),
        timezone="America/Los_Angeles",
        recurrence=CalendarRecurrenceRule(
            frequency=CalendarRecurrenceFrequency.monthly,
            month_day=15,
            timezone="America/Los_Angeles",
        ),
    )
    _add_event(repository, authority, old_event, expected_version=2)
    occurrences = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 1, 1, tzinfo=zone),
        ends_at=datetime(2026, 4, 1, tzinfo=zone),
    )
    offset_dates = [
        item.occurrence.starts_at.date()
        for item in occurrences
        if item.event.event_ref == offset_event.event_ref
    ]
    old_dates = [
        item.occurrence.starts_at.date()
        for item in occurrences
        if item.event.event_ref == old_event.event_ref
    ]
    assert offset_dates == [datetime(2026, 2, 15).date(), datetime(2026, 3, 15).date()]
    assert old_dates == [
        datetime(2026, 1, 15).date(),
        datetime(2026, 2, 15).date(),
        datetime(2026, 3, 15).date(),
    ]


def test_save_and_update_cannot_bypass_exact_lifecycle_actions(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    event = _event()
    _add_event(repository, authority, event)
    current = repository.read(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)

    removed_event_set = CalendarSet.model_validate(
        {
            **current.model_dump(mode="json"),
            "events": [],
            "version": 3,
            "undo_stack": [],
        }
    )
    operation_ref = "operation-ref:bypass-save-remove"
    idempotency_ref = "idempotency-ref:bypass-save-remove"
    with pytest.raises(
        CalendarConflict, match="ECO_CALENDAR_SAVE_EVENT_IDENTITY_CHANGE_DENIED"
    ):
        repository.save(
            calendar_set=removed_event_set,
            expected_version=2,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_calendar_approval(
                authority,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )

    archived_event = CalendarEvent.model_validate(
        {**event.model_dump(mode="json"), "archived": True}
    )
    archived_event_set = CalendarSet.model_validate(
        {
            **current.model_dump(mode="json"),
            "events": [archived_event.model_dump(mode="json")],
            "version": 3,
            "undo_stack": [],
        }
    )
    operation_ref = "operation-ref:bypass-save-archive"
    idempotency_ref = "idempotency-ref:bypass-save-archive"
    with pytest.raises(
        CalendarConflict,
        match="ECO_CALENDAR_EVENT_LIFECYCLE_REQUIRES_EXACT_ACTION",
    ):
        repository.save(
            calendar_set=archived_event_set,
            expected_version=2,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_calendar_approval(
                authority,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )

    operation_ref = "operation-ref:bypass-update-archive"
    idempotency_ref = "idempotency-ref:bypass-update-archive"
    with pytest.raises(
        CalendarConflict,
        match="ECO_CALENDAR_EVENT_LIFECYCLE_REQUIRES_EXACT_ACTION",
    ):
        repository.update_event(
            workspace_ref=WORKSPACE,
            calendar_set_ref=SET_REF,
            event=archived_event,
            expected_version=2,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_calendar_approval(
                authority,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )

    operation_ref = "operation-ref:archive-calendar-with-event"
    idempotency_ref = "idempotency-ref:archive-calendar-with-event"
    with pytest.raises(
        CalendarConflict, match="ECO_CALENDAR_ARCHIVE_REQUIRES_NO_ACTIVE_EVENTS"
    ):
        repository.archive_calendar(
            workspace_ref=WORKSPACE,
            calendar_set_ref=SET_REF,
            calendar_ref=CALENDAR_REF,
            expected_version=2,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_calendar_approval(
                authority,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )


def test_view_result_ref_changes_with_local_calendar_content(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    event = _event()
    _add_event(repository, authority, event)
    before = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 7, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    updated = CalendarEvent.model_validate(
        {**event.model_dump(mode="json"), "title": "Updated local title"}
    )
    operation_ref = "operation-ref:update-local-event"
    idempotency_ref = "idempotency-ref:update-local-event"
    repository.update_event(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        event=updated,
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_calendar_approval(
            authority,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    after = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 7, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    assert after.result_ref != before.result_ref
    assert after.occurrence_items[0].event.title == "Updated local title"


def test_task_time_block_keeps_ref_only_and_resolves_canonical_truth(
    tmp_path: Path,
) -> None:
    repository, tasks, authority, _database_path = _repositories(tmp_path)
    task = CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref="task-ref:calendar-block",
        title="Canonical private task title",
    )
    operation_ref = "operation-ref:create-task"
    idempotency_ref = "idempotency-ref:create-task"
    tasks.create(
        task=task,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    _create_set(repository, authority)
    zone = ZoneInfo("America/Los_Angeles")
    block = CalendarEvent(
        event_ref="event-ref:task-block",
        calendar_ref=CALENDAR_REF,
        task_ref=task.task_ref,
        starts_at=datetime(2026, 3, 7, 13, tzinfo=zone),
        ends_at=datetime(2026, 3, 7, 14, tzinfo=zone),
        timezone="America/Los_Angeles",
    )
    _add_event(repository, authority, block)
    projection = repository.occurrences(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        starts_at=datetime(2026, 3, 7, tzinfo=timezone.utc),
        ends_at=datetime(2026, 3, 8, tzinfo=timezone.utc),
    )[0]
    assert projection.event.title is None
    assert projection.event.description is None
    assert projection.canonical_task == task
    assert projection.canonical_owner_ref == "canonical-owner-ref:tasks"

    before_view = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 7, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    updated_task = CanonicalTask.model_validate(
        {
            **task.model_dump(mode="json"),
            "title": "Updated canonical title",
            "version": 2,
        }
    )
    update_operation = "operation-ref:update-task"
    update_idempotency = "idempotency-ref:update-task"
    tasks.save(
        task=updated_task,
        expected_version=1,
        operation_ref=update_operation,
        idempotency_ref=update_idempotency,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=update_operation,
            idempotency_ref=update_idempotency,
        ),
    )
    after_view = repository.view(
        workspace_ref=WORKSPACE,
        calendar_set_ref=SET_REF,
        view=CalendarView.day,
        anchor=datetime(2026, 3, 7, 20, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )
    assert after_view.result_ref != before_view.result_ref
    assert after_view.occurrence_items[0].canonical_task == updated_task

    with pytest.raises(
        ValueError, match="ECO_CALENDAR_TASK_BLOCK_CANNOT_COPY_TASK_TRUTH"
    ):
        CalendarEvent.model_validate(
            {**block.model_dump(mode="json"), "title": "Copied title"}
        )


def test_import_export_preview_and_new_set_round_trip(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_set(repository, authority)
    _add_event(repository, authority, _event())
    bundle = repository.export_bundle(workspace_ref=WORKSPACE, calendar_set_ref=SET_REF)
    assert isinstance(bundle, CalendarPortableBundle)
    preview = repository.preview_import(bundle)
    assert preview.calendar_count == 1
    assert preview.event_count == 1
    assert preview.task_block_count == 0

    imported_ref = "calendar-set-ref:imported"
    operation_ref = "operation-ref:import-calendar"
    idempotency_ref = "idempotency-ref:import-calendar"
    repository.import_bundle(
        workspace_ref=WORKSPACE,
        calendar_set_ref=imported_ref,
        bundle=bundle,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_calendar_approval(
            authority,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            record_ref=imported_ref,
        ),
    )
    imported = repository.read(workspace_ref=WORKSPACE, calendar_set_ref=imported_ref)
    assert imported.name == bundle.name
    assert imported.calendars == bundle.calendars
    assert imported.events == bundle.events


def test_invalid_timezone_range_all_day_and_query_bounds_fail_closed() -> None:
    with pytest.raises(ValueError, match="ECO_CALENDAR_TIMEZONE_INVALID"):
        LocalCalendar(calendar_ref="calendar-ref:bad", name="Bad", timezone="Not/AZone")
    with pytest.raises(ValueError, match="ECO_CALENDAR_EVENT_RANGE_INVALID"):
        CalendarEvent(
            event_ref="event-ref:bad-range",
            calendar_ref=CALENDAR_REF,
            title="Bad range",
            starts_at=datetime(2026, 1, 1, 10, tzinfo=timezone.utc),
            ends_at=datetime(2026, 1, 1, 9, tzinfo=timezone.utc),
            timezone="UTC",
        )
    with pytest.raises(ValueError, match="ECO_CALENDAR_ALL_DAY_BOUNDARY_INVALID"):
        CalendarEvent(
            event_ref="event-ref:bad-all-day",
            calendar_ref=CALENDAR_REF,
            title="Bad all day",
            starts_at=datetime(2026, 1, 1, 10, tzinfo=timezone.utc),
            ends_at=datetime(2026, 1, 2, 10, tzinfo=timezone.utc),
            timezone="UTC",
            all_day=True,
        )
