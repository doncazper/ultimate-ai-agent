"""Encrypted standalone local Calendar core for ECO-004.

Calendar sets own manual calendars and events. Task time blocks retain only a
canonical Task ref and resolve current truth through ``TaskRepository``. This
module has no route, UI, account adapter, scheduler, network, or connector
runtime; reminder records are intent-only local posture.
"""

from __future__ import annotations

import calendar as month_calendar
import hashlib
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Iterator, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.local_data import (
    ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES,
    EcosystemConflict,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.ecosystem.tasks import CanonicalTask, TaskRepository
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_CALENDAR_SCHEMA_VERSION = "uaa-eco-004-calendar-set.v1"
ECO_CALENDAR_BUNDLE_SCHEMA_VERSION = "uaa-eco-004-calendar-bundle.v1"
ECO_CALENDAR_MUTATION_ACTION = "ecosystem.calendar.apply"
ECO_CALENDAR_MODULE_REF = "module-ref:calendar"
ECO_CALENDAR_RECORD_KIND_REF = "record-kind-ref:calendar-set"
ECO_CALENDAR_RETENTION_REF = "retention-ref:calendar-operator-managed"
_ALL_CALENDAR_SETS_SEARCH_TERM = "entity-kind:calendar-set"
_MAX_UNDO_DEPTH = 20
_MAX_QUERY_DAYS = 370
_MAX_OCCURRENCES = 25_000
_MAX_CONFLICTS = 10_000
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")


class CalendarError(RuntimeError):
    """Fail-closed Calendar error with a stable, non-sensitive code."""


class CalendarConflict(CalendarError):
    pass


class CalendarRecurrenceFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class CalendarParticipantStatus(str, Enum):
    needs_action = "needs_action"
    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"


class CalendarView(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    agenda = "agenda"


class _CalendarModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_CALENDAR_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_CALENDAR_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _zone(value: str, code: str = "ECO_CALENDAR_TIMEZONE_INVALID") -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError):
        raise ValueError(code) from None


def _aware(value: datetime, code: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(code)
    return value


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validation_code(exc: ValueError) -> str:
    match = re.search(r"ECO_CALENDAR_[A-Z0-9_]+", str(exc))
    return (
        match.group(0)
        if match is not None
        else "ECO_CALENDAR_MUTATION_INVARIANT_DENIED"
    )


def _localize(day: date, wall_time: time, zone: ZoneInfo) -> datetime:
    """Resolve a wall-clock value, moving a nonexistent DST time forward."""
    naive = datetime.combine(day, wall_time.replace(tzinfo=None))
    candidate = naive.replace(tzinfo=zone, fold=wall_time.fold)
    normalized = candidate.astimezone(timezone.utc).astimezone(zone)
    if normalized.replace(tzinfo=None) != naive:
        return normalized
    return candidate


class LocalCalendar(_CalendarModel):
    calendar_ref: str
    name: str = Field(..., repr=False)
    timezone: str = "UTC"
    color_ref: str | None = None
    archived: bool = False

    @model_validator(mode="after")
    def validate_calendar(self) -> "LocalCalendar":
        _validate_ref(self.calendar_ref, "calendar_ref")
        _private_text(self.name, maximum=512, code="ECO_CALENDAR_NAME_INVALID")
        _zone(self.timezone)
        if self.color_ref is not None:
            _validate_ref(self.color_ref, "color_ref")
        return self


class CalendarParticipant(_CalendarModel):
    participant_ref: str
    display_name: str = Field(..., repr=False)
    address: str | None = Field(default=None, repr=False)
    status: CalendarParticipantStatus = CalendarParticipantStatus.needs_action

    @model_validator(mode="after")
    def validate_participant(self) -> "CalendarParticipant":
        _validate_ref(self.participant_ref, "participant_ref")
        _private_text(
            self.display_name,
            maximum=512,
            code="ECO_CALENDAR_PARTICIPANT_NAME_INVALID",
        )
        if self.address is not None:
            _private_text(
                self.address,
                maximum=2_048,
                code="ECO_CALENDAR_PARTICIPANT_ADDRESS_INVALID",
            )
        return self


class CalendarReminder(_CalendarModel):
    reminder_ref: str
    minutes_before: int = Field(ge=0, le=525_600)
    delivery_posture: Literal["intent_only"] = "intent_only"

    @field_validator("reminder_ref")
    @classmethod
    def validate_reminder_ref(cls, value: str) -> str:
        return _validate_ref(value, "reminder_ref")


class CalendarRecurrenceRule(_CalendarModel):
    frequency: CalendarRecurrenceFrequency
    interval: int = Field(default=1, ge=1, le=365)
    timezone: str
    weekdays: tuple[int, ...] = Field(default=(), max_length=7)
    month_day: int | None = Field(default=None, ge=1, le=31)
    count: int | None = Field(default=None, ge=1, le=100_000)
    until: datetime | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> "CalendarRecurrenceRule":
        _zone(self.timezone, "ECO_CALENDAR_RECURRENCE_TIMEZONE_INVALID")
        if len(self.weekdays) != len(set(self.weekdays)) or any(
            day < 0 or day > 6 for day in self.weekdays
        ):
            raise ValueError("ECO_CALENDAR_RECURRENCE_WEEKDAYS_INVALID")
        if self.frequency != CalendarRecurrenceFrequency.weekly and self.weekdays:
            raise ValueError("ECO_CALENDAR_RECURRENCE_WEEKDAYS_NOT_APPLICABLE")
        if (
            self.frequency != CalendarRecurrenceFrequency.monthly
            and self.month_day is not None
        ):
            raise ValueError("ECO_CALENDAR_RECURRENCE_MONTH_DAY_NOT_APPLICABLE")
        if self.until is not None:
            _aware(self.until, "ECO_CALENDAR_RECURRENCE_UNTIL_INVALID")
        return self


class CalendarEvent(_CalendarModel):
    event_ref: str
    calendar_ref: str
    title: str | None = Field(default=None, repr=False)
    description: str | None = Field(default=None, repr=False)
    location: str | None = Field(default=None, repr=False)
    starts_at: datetime
    ends_at: datetime
    timezone: str
    all_day: bool = False
    participant_items: tuple[CalendarParticipant, ...] = Field(
        default=(), max_length=1_000
    )
    reminder_items: tuple[CalendarReminder, ...] = Field(default=(), max_length=64)
    recurrence: CalendarRecurrenceRule | None = None
    task_ref: str | None = None
    archived: bool = False

    @model_validator(mode="after")
    def validate_event(self) -> "CalendarEvent":
        _validate_ref(self.event_ref, "event_ref")
        _validate_ref(self.calendar_ref, "calendar_ref")
        zone = _zone(self.timezone)
        _aware(self.starts_at, "ECO_CALENDAR_START_INVALID")
        _aware(self.ends_at, "ECO_CALENDAR_END_INVALID")
        if _utc(self.ends_at) <= _utc(self.starts_at):
            raise ValueError("ECO_CALENDAR_EVENT_RANGE_INVALID")
        if self.task_ref is None:
            if self.title is None:
                raise ValueError("ECO_CALENDAR_EVENT_TITLE_REQUIRED")
            _private_text(
                self.title, maximum=2_048, code="ECO_CALENDAR_EVENT_TITLE_INVALID"
            )
        else:
            _validate_ref(self.task_ref, "task_ref")
            if self.title is not None or self.description is not None:
                raise ValueError("ECO_CALENDAR_TASK_BLOCK_CANNOT_COPY_TASK_TRUTH")
        for value, maximum, code in (
            (self.description, 65_536, "ECO_CALENDAR_EVENT_DESCRIPTION_INVALID"),
            (self.location, 8_192, "ECO_CALENDAR_EVENT_LOCATION_INVALID"),
        ):
            if value is not None:
                _private_text(value, maximum=maximum, code=code)
        participant_refs = tuple(
            item.participant_ref for item in self.participant_items
        )
        reminder_refs = tuple(item.reminder_ref for item in self.reminder_items)
        _validate_refs(participant_refs, "participant_ref")
        _validate_refs(reminder_refs, "reminder_ref")
        if self.recurrence is not None and self.recurrence.timezone != self.timezone:
            raise ValueError("ECO_CALENDAR_RECURRENCE_EVENT_TIMEZONE_MISMATCH")
        if self.recurrence is not None and self.recurrence.until is not None:
            if _utc(self.recurrence.until) < _utc(self.starts_at):
                raise ValueError("ECO_CALENDAR_RECURRENCE_UNTIL_BEFORE_START")
        if self.all_day:
            local_start = self.starts_at.astimezone(zone)
            local_end = self.ends_at.astimezone(zone)
            if local_start.time() != time.min or local_end.time() != time.min:
                raise ValueError("ECO_CALENDAR_ALL_DAY_BOUNDARY_INVALID")
        return self


class CalendarSetSnapshot(_CalendarModel):
    name: str = Field(..., repr=False)
    calendars: tuple[LocalCalendar, ...]
    events: tuple[CalendarEvent, ...] = ()
    archived: bool = False


class CalendarSet(_CalendarModel):
    schema_version: Literal["uaa-eco-004-calendar-set.v1"] = ECO_CALENDAR_SCHEMA_VERSION
    workspace_ref: str
    calendar_set_ref: str
    name: str = Field(..., repr=False)
    calendars: tuple[LocalCalendar, ...] = Field(..., min_length=1, max_length=256)
    events: tuple[CalendarEvent, ...] = Field(default=(), max_length=10_000)
    archived: bool = False
    version: int = Field(default=1, ge=1)
    undo_stack: tuple[CalendarSetSnapshot, ...] = Field(
        default=(), max_length=_MAX_UNDO_DEPTH, repr=False
    )

    @model_validator(mode="after")
    def validate_set(self) -> "CalendarSet":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.calendar_set_ref, "calendar_set_ref")
        _private_text(self.name, maximum=512, code="ECO_CALENDAR_SET_NAME_INVALID")
        calendar_refs = tuple(item.calendar_ref for item in self.calendars)
        event_refs = tuple(item.event_ref for item in self.events)
        _validate_refs(calendar_refs, "calendar_ref")
        _validate_refs(event_refs, "event_ref")
        calendars = {item.calendar_ref: item for item in self.calendars}
        for event in self.events:
            calendar_item = calendars.get(event.calendar_ref)
            if calendar_item is None:
                raise ValueError("ECO_CALENDAR_EVENT_CALENDAR_NOT_FOUND")
            if not event.archived and calendar_item.archived:
                raise ValueError("ECO_CALENDAR_ACTIVE_EVENT_IN_ARCHIVED_CALENDAR")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "calendar-set-summary-ref",
            {
                "calendar_set_ref": self.calendar_set_ref,
                "version": self.version,
                "calendar_count": len(self.calendars),
                "event_count": len(self.events),
                "archived": self.archived,
            },
        )

    def snapshot(self) -> CalendarSetSnapshot:
        return CalendarSetSnapshot(
            name=self.name,
            calendars=self.calendars,
            events=self.events,
            archived=self.archived,
        )


class CalendarPortableBundle(_CalendarModel):
    schema_version: Literal["uaa-eco-004-calendar-bundle.v1"] = (
        ECO_CALENDAR_BUNDLE_SCHEMA_VERSION
    )
    name: str = Field(..., repr=False)
    calendars: tuple[LocalCalendar, ...]
    events: tuple[CalendarEvent, ...] = ()

    @model_validator(mode="after")
    def validate_bundle(self) -> "CalendarPortableBundle":
        _private_text(self.name, maximum=512, code="ECO_CALENDAR_SET_NAME_INVALID")
        CalendarSet(
            workspace_ref="workspace-ref:portable-validation",
            calendar_set_ref="calendar-set-ref:portable-validation",
            name=self.name,
            calendars=self.calendars,
            events=self.events,
        )
        return self

    @property
    def bundle_ref(self) -> str:
        return _stable_ref("calendar-bundle-ref", self.model_dump(mode="json"))


class CalendarImportPreview(_CalendarModel):
    bundle_ref: str
    calendar_count: int
    event_count: int
    task_block_count: int


class CalendarOccurrence(_CalendarModel):
    occurrence_ref: str
    event_ref: str
    calendar_ref: str
    starts_at: datetime
    ends_at: datetime
    timezone: str


class CalendarEventProjection(_CalendarModel):
    event: CalendarEvent = Field(..., repr=False)
    occurrence: CalendarOccurrence
    canonical_task: CanonicalTask | None = Field(default=None, repr=False)
    canonical_owner_ref: str
    field_provenance_refs: tuple[str, ...]
    projection_state: Literal["current", "archived", "missing"] = "current"


class CalendarOccurrenceConflict(_CalendarModel):
    first_occurrence_ref: str
    second_occurrence_ref: str
    overlap_starts_at: datetime
    overlap_ends_at: datetime


class CalendarViewResult(_CalendarModel):
    view: CalendarView
    timezone: str
    range_starts_at: datetime
    range_ends_at: datetime
    occurrence_items: tuple[CalendarEventProjection, ...]
    conflict_items: tuple[CalendarOccurrenceConflict, ...]
    result_ref: str


class CalendarRepository:
    """Exact governed repository for local Calendar Set aggregates."""

    def __init__(
        self,
        platform: EcosystemLocalDataPlatform,
        *,
        task_repository: TaskRepository | None = None,
    ) -> None:
        if task_repository is not None and task_repository.platform is not platform:
            raise ValueError("ECO_CALENDAR_TASK_REPOSITORY_PLATFORM_MISMATCH")
        self.platform = platform
        self.task_repository = task_repository

    @staticmethod
    def mutation_resource_refs(
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operation_ref: str,
        record_ref: str,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((workspace_ref, idempotency_ref, operation_ref, record_ref))
        )

    def create_calendar_set(
        self,
        *,
        calendar_set: CalendarSet,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if calendar_set.version != 1 or calendar_set.undo_stack:
            raise CalendarConflict("ECO_CALENDAR_CREATE_VERSION_INVALID")
        context = self._request_context_ref(
            "create_calendar_set",
            {
                "calendar_set": calendar_set.model_dump(mode="json"),
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=calendar_set.workspace_ref,
            record_ref=calendar_set.calendar_set_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        self._ensure_missing(calendar_set.workspace_ref, calendar_set.calendar_set_ref)
        self._validate_task_refs(calendar_set)
        return self._apply(
            workspace_ref=calendar_set.workspace_ref,
            record=calendar_set,
            expected_version=0,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def read(self, *, workspace_ref: str, calendar_set_ref: str) -> CalendarSet:
        record = self.platform.read(
            workspace_ref=workspace_ref, record_ref=calendar_set_ref
        )
        try:
            calendar_set = CalendarSet.model_validate(record.private_payload)
        except Exception as exc:
            raise CalendarError("ECO_CALENDAR_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_CALENDAR_MODULE_REF
            or record.record_kind_ref != ECO_CALENDAR_RECORD_KIND_REF
            or calendar_set.workspace_ref != workspace_ref
            or calendar_set.calendar_set_ref != calendar_set_ref
            or calendar_set.version != record.version
            or calendar_set.safe_summary_ref != record.safe_summary_ref
        ):
            raise CalendarError("ECO_CALENDAR_RECORD_BINDING_INVALID")
        return calendar_set

    def list_sets(
        self, *, workspace_ref: str, include_archived: bool = False
    ) -> tuple[CalendarSet, ...]:
        items = tuple(
            self.read(workspace_ref=workspace_ref, calendar_set_ref=record_ref)
            for record_ref in self.platform.search(
                workspace_ref=workspace_ref, term=_ALL_CALENDAR_SETS_SEARCH_TERM
            )
        )
        return tuple(
            sorted(
                (item for item in items if include_archived or not item.archived),
                key=lambda item: item.calendar_set_ref,
            )
        )

    def save(
        self,
        *,
        calendar_set: CalendarSet,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if calendar_set.version != expected_version + 1:
            raise CalendarConflict("ECO_CALENDAR_NEXT_VERSION_INVALID")
        desired = calendar_set.snapshot()
        return self._mutate(
            workspace_ref=calendar_set.workspace_ref,
            calendar_set_ref=calendar_set.calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="save",
            mutation_material={"desired": desired.model_dump(mode="json")},
            transform=lambda _current: desired,
        )

    def add_calendar(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        calendar_item: LocalCalendar,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            if any(
                item.calendar_ref == calendar_item.calendar_ref
                for item in current.calendars
            ):
                raise CalendarConflict("ECO_CALENDAR_ALREADY_EXISTS")
            return self._snapshot(
                current, calendars=(*current.calendars, calendar_item)
            )

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="add_calendar",
            mutation_material={"calendar": calendar_item.model_dump(mode="json")},
            transform=transform,
        )

    def update_calendar(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        calendar_item: LocalCalendar,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            if not any(
                item.calendar_ref == calendar_item.calendar_ref
                for item in current.calendars
            ):
                raise CalendarConflict("ECO_CALENDAR_NOT_FOUND")
            calendars = tuple(
                calendar_item
                if item.calendar_ref == calendar_item.calendar_ref
                else item
                for item in current.calendars
            )
            return self._snapshot(current, calendars=calendars)

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="update_calendar",
            mutation_material={"calendar": calendar_item.model_dump(mode="json")},
            transform=transform,
        )

    def delete_calendar(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        calendar_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        _validate_ref(calendar_ref, "calendar_ref")

        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            item = next(
                (
                    item
                    for item in current.calendars
                    if item.calendar_ref == calendar_ref
                ),
                None,
            )
            if item is None:
                raise CalendarConflict("ECO_CALENDAR_NOT_FOUND")
            if not item.archived:
                raise CalendarConflict("ECO_CALENDAR_DELETE_REQUIRES_ARCHIVE")
            if any(event.calendar_ref == calendar_ref for event in current.events):
                raise CalendarConflict("ECO_CALENDAR_DELETE_REQUIRES_EMPTY")
            calendars = tuple(
                item for item in current.calendars if item.calendar_ref != calendar_ref
            )
            if not calendars:
                raise CalendarConflict("ECO_CALENDAR_SET_REQUIRES_CALENDAR")
            return self._snapshot(current, calendars=calendars)

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="delete_calendar",
            mutation_material={"calendar_ref": calendar_ref},
            transform=transform,
        )

    def add_event(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        event: CalendarEvent,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            if any(item.event_ref == event.event_ref for item in current.events):
                raise CalendarConflict("ECO_CALENDAR_EVENT_ALREADY_EXISTS")
            return self._snapshot(current, events=(*current.events, event))

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="add_event",
            mutation_material={"event": event.model_dump(mode="json")},
            transform=transform,
        )

    def quick_create_event(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        event: CalendarEvent,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        """Structured quick-create uses the same exact mutation as normal create."""
        return self.add_event(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            event=event,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def update_event(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        event: CalendarEvent,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            if not any(item.event_ref == event.event_ref for item in current.events):
                raise CalendarConflict("ECO_CALENDAR_EVENT_NOT_FOUND")
            events = tuple(
                event if item.event_ref == event.event_ref else item
                for item in current.events
            )
            return self._snapshot(current, events=events)

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="update_event",
            mutation_material={"event": event.model_dump(mode="json")},
            transform=transform,
        )

    def archive_event(self, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._set_event_archive_state(archived=True, **kwargs)

    def restore_event(self, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._set_event_archive_state(archived=False, **kwargs)

    def _set_event_archive_state(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        event_ref: str,
        archived: bool,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        _validate_ref(event_ref, "event_ref")

        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            event = next(
                (item for item in current.events if item.event_ref == event_ref), None
            )
            if event is None:
                raise CalendarConflict("ECO_CALENDAR_EVENT_NOT_FOUND")
            if event.archived == archived:
                code = (
                    "ECO_CALENDAR_EVENT_ALREADY_ARCHIVED"
                    if archived
                    else "ECO_CALENDAR_EVENT_NOT_ARCHIVED"
                )
                raise CalendarConflict(code)
            updated = CalendarEvent.model_validate(
                {**event.model_dump(mode="json"), "archived": archived}
            )
            events = tuple(
                updated if item.event_ref == event_ref else item
                for item in current.events
            )
            return self._snapshot(current, events=events)

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="archive_event" if archived else "restore_event",
            mutation_material={"event_ref": event_ref},
            transform=transform,
        )

    def delete_event(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        event_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        _validate_ref(event_ref, "event_ref")

        def transform(current: CalendarSet) -> CalendarSetSnapshot:
            event = next(
                (item for item in current.events if item.event_ref == event_ref), None
            )
            if event is None:
                raise CalendarConflict("ECO_CALENDAR_EVENT_NOT_FOUND")
            if not event.archived:
                raise CalendarConflict("ECO_CALENDAR_EVENT_DELETE_REQUIRES_ARCHIVE")
            return self._snapshot(
                current,
                events=tuple(
                    item for item in current.events if item.event_ref != event_ref
                ),
            )

        return self._mutate(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="delete_event",
            mutation_material={"event_ref": event_ref},
            transform=transform,
        )

    def undo(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        context = self._request_context_ref(
            "undo",
            {
                "workspace_ref": workspace_ref,
                "calendar_set_ref": calendar_set_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            record_ref=calendar_set_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(
            workspace_ref=workspace_ref, calendar_set_ref=calendar_set_ref
        )
        if current.version != expected_version:
            raise CalendarConflict("ECO_CALENDAR_STALE_VERSION")
        if not current.undo_stack:
            raise CalendarConflict("ECO_CALENDAR_UNDO_EMPTY")
        updated = self._build_set(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            version=current.version + 1,
            undo_stack=current.undo_stack[:-1],
            snapshot=current.undo_stack[-1],
        )
        if (
            self._record_plaintext_size(updated)
            > ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES
        ):
            raise CalendarConflict("ECO_CALENDAR_PRIVATE_PAYLOAD_LIMIT_EXCEEDED")
        return self._apply(
            workspace_ref=workspace_ref,
            record=updated,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def export_bundle(
        self, *, workspace_ref: str, calendar_set_ref: str
    ) -> CalendarPortableBundle:
        item = self.read(workspace_ref=workspace_ref, calendar_set_ref=calendar_set_ref)
        return CalendarPortableBundle(
            name=item.name, calendars=item.calendars, events=item.events
        )

    @staticmethod
    def preview_import(bundle: CalendarPortableBundle) -> CalendarImportPreview:
        return CalendarImportPreview(
            bundle_ref=bundle.bundle_ref,
            calendar_count=len(bundle.calendars),
            event_count=len(bundle.events),
            task_block_count=sum(event.task_ref is not None for event in bundle.events),
        )

    def import_bundle(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        bundle: CalendarPortableBundle,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        return self.create_calendar_set(
            calendar_set=CalendarSet(
                workspace_ref=workspace_ref,
                calendar_set_ref=calendar_set_ref,
                name=bundle.name,
                calendars=bundle.calendars,
                events=bundle.events,
            ),
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def occurrences(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        starts_at: datetime,
        ends_at: datetime,
        calendar_refs: tuple[str, ...] = (),
        include_archived: bool = False,
    ) -> tuple[CalendarEventProjection, ...]:
        _aware(starts_at, "ECO_CALENDAR_QUERY_START_INVALID")
        _aware(ends_at, "ECO_CALENDAR_QUERY_END_INVALID")
        if _utc(ends_at) <= _utc(starts_at):
            raise CalendarConflict("ECO_CALENDAR_QUERY_RANGE_INVALID")
        if _utc(ends_at) - _utc(starts_at) > timedelta(days=_MAX_QUERY_DAYS):
            raise CalendarConflict("ECO_CALENDAR_QUERY_RANGE_TOO_LARGE")
        _validate_refs(calendar_refs, "calendar_ref")
        calendar_set = self.read(
            workspace_ref=workspace_ref, calendar_set_ref=calendar_set_ref
        )
        if calendar_refs and not set(calendar_refs).issubset(
            {item.calendar_ref for item in calendar_set.calendars}
        ):
            raise CalendarConflict("ECO_CALENDAR_FILTER_CALENDAR_NOT_FOUND")
        projections: list[CalendarEventProjection] = []
        for event in calendar_set.events:
            if event.archived and not include_archived:
                continue
            if calendar_refs and event.calendar_ref not in calendar_refs:
                continue
            for occurrence in self._event_occurrences(event, starts_at, ends_at):
                projections.append(
                    self._project_event(workspace_ref, event, occurrence)
                )
                if len(projections) > _MAX_OCCURRENCES:
                    raise CalendarError("ECO_CALENDAR_OCCURRENCE_LIMIT_EXCEEDED")
        return tuple(
            sorted(
                projections,
                key=lambda item: (
                    item.occurrence.starts_at,
                    item.occurrence.ends_at,
                    item.event.event_ref,
                ),
            )
        )

    def view(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        view: CalendarView,
        anchor: datetime,
        timezone_name: str,
        calendar_refs: tuple[str, ...] = (),
    ) -> CalendarViewResult:
        _aware(anchor, "ECO_CALENDAR_VIEW_ANCHOR_INVALID")
        zone = _zone(timezone_name)
        local_anchor = anchor.astimezone(zone)
        if view == CalendarView.day:
            start_day = local_anchor.date()
            end_day = start_day + timedelta(days=1)
        elif view == CalendarView.week:
            start_day = local_anchor.date() - timedelta(days=local_anchor.weekday())
            end_day = start_day + timedelta(days=7)
        elif view == CalendarView.month:
            start_day = local_anchor.date().replace(day=1)
            if start_day.month == 12:
                end_day = date(start_day.year + 1, 1, 1)
            else:
                end_day = date(start_day.year, start_day.month + 1, 1)
        else:
            start_day = local_anchor.date()
            end_day = start_day + timedelta(days=30)
        range_start = _localize(start_day, time.min, zone)
        range_end = _localize(end_day, time.min, zone)
        occurrence_items = self.occurrences(
            workspace_ref=workspace_ref,
            calendar_set_ref=calendar_set_ref,
            starts_at=range_start,
            ends_at=range_end,
            calendar_refs=calendar_refs,
        )
        conflict_items = self.detect_conflicts(occurrence_items)
        return CalendarViewResult(
            view=view,
            timezone=timezone_name,
            range_starts_at=range_start,
            range_ends_at=range_end,
            occurrence_items=occurrence_items,
            conflict_items=conflict_items,
            result_ref=_stable_ref(
                "calendar-view-result-ref",
                {
                    "calendar_set_ref": calendar_set_ref,
                    "view": view.value,
                    "timezone": timezone_name,
                    "range_start": range_start.isoformat(),
                    "range_end": range_end.isoformat(),
                    "occurrence_refs": [
                        item.occurrence.occurrence_ref for item in occurrence_items
                    ],
                    "task_versions": [
                        (
                            item.event.task_ref,
                            item.canonical_task.version
                            if item.canonical_task is not None
                            else None,
                        )
                        for item in occurrence_items
                        if item.event.task_ref is not None
                    ],
                    "conflict_count": len(conflict_items),
                },
            ),
        )

    @staticmethod
    def detect_conflicts(
        occurrence_items: tuple[CalendarEventProjection, ...],
    ) -> tuple[CalendarOccurrenceConflict, ...]:
        ordered = sorted(
            occurrence_items,
            key=lambda item: (item.occurrence.starts_at, item.occurrence.ends_at),
        )
        conflicts: list[CalendarOccurrenceConflict] = []
        for index, first in enumerate(ordered):
            for second in ordered[index + 1 :]:
                if second.occurrence.starts_at >= first.occurrence.ends_at:
                    break
                if second.event.event_ref == first.event.event_ref:
                    continue
                conflicts.append(
                    CalendarOccurrenceConflict(
                        first_occurrence_ref=first.occurrence.occurrence_ref,
                        second_occurrence_ref=second.occurrence.occurrence_ref,
                        overlap_starts_at=max(
                            first.occurrence.starts_at, second.occurrence.starts_at
                        ),
                        overlap_ends_at=min(
                            first.occurrence.ends_at, second.occurrence.ends_at
                        ),
                    )
                )
                if len(conflicts) > _MAX_CONFLICTS:
                    raise CalendarError("ECO_CALENDAR_CONFLICT_LIMIT_EXCEEDED")
        return tuple(conflicts)

    def _mutate(
        self,
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        mutation_kind: str,
        mutation_material: dict[str, Any],
        transform: Callable[[CalendarSet], CalendarSetSnapshot],
    ) -> UnitOfWorkReceipt:
        context = self._request_context_ref(
            mutation_kind,
            {
                "workspace_ref": workspace_ref,
                "calendar_set_ref": calendar_set_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
                "mutation": mutation_material,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            record_ref=calendar_set_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(
            workspace_ref=workspace_ref, calendar_set_ref=calendar_set_ref
        )
        if current.version != expected_version:
            raise CalendarConflict("ECO_CALENDAR_STALE_VERSION")
        snapshot = transform(current)
        updated = self._with_bounded_undo(current=current, snapshot=snapshot)
        self._validate_new_task_refs(current=current, updated=updated)
        return self._apply(
            workspace_ref=workspace_ref,
            record=updated,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    @staticmethod
    def _snapshot(calendar_set: CalendarSet, **updates: Any) -> CalendarSetSnapshot:
        material = calendar_set.snapshot().model_dump(mode="json")
        material.update(updates)
        try:
            return CalendarSetSnapshot.model_validate(material)
        except ValueError as exc:
            raise CalendarConflict(_validation_code(exc)) from exc

    @staticmethod
    def _build_set(
        *,
        workspace_ref: str,
        calendar_set_ref: str,
        version: int,
        undo_stack: tuple[CalendarSetSnapshot, ...],
        snapshot: CalendarSetSnapshot,
    ) -> CalendarSet:
        try:
            return CalendarSet(
                workspace_ref=workspace_ref,
                calendar_set_ref=calendar_set_ref,
                version=version,
                undo_stack=undo_stack,
                **snapshot.model_dump(mode="json"),
            )
        except ValueError as exc:
            raise CalendarConflict(_validation_code(exc)) from exc

    @staticmethod
    def _record_plaintext_size(calendar_set: CalendarSet) -> int:
        return len(
            json.dumps(
                {
                    "private_payload": calendar_set.model_dump(mode="json"),
                    "search_terms": [_ALL_CALENDAR_SETS_SEARCH_TERM],
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )

    def _with_bounded_undo(
        self, *, current: CalendarSet, snapshot: CalendarSetSnapshot
    ) -> CalendarSet:
        history = list((*current.undo_stack, current.snapshot())[-_MAX_UNDO_DEPTH:])
        while True:
            updated = self._build_set(
                workspace_ref=current.workspace_ref,
                calendar_set_ref=current.calendar_set_ref,
                version=current.version + 1,
                undo_stack=tuple(history),
                snapshot=snapshot,
            )
            if (
                self._record_plaintext_size(updated)
                <= ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES
            ):
                return updated
            if not history:
                raise CalendarConflict("ECO_CALENDAR_PRIVATE_PAYLOAD_LIMIT_EXCEEDED")
            history.pop(0)

    def _validate_task_refs(self, calendar_set: CalendarSet) -> None:
        task_events = [
            event
            for event in calendar_set.events
            if event.task_ref is not None and not event.archived
        ]
        if not task_events:
            return
        if self.task_repository is None:
            raise CalendarConflict("ECO_CALENDAR_TASK_REPOSITORY_REQUIRED")
        for event in task_events:
            task = self.task_repository.read(
                workspace_ref=calendar_set.workspace_ref, task_ref=event.task_ref
            )
            if task.archived:
                raise CalendarConflict("ECO_CALENDAR_ACTIVE_TASK_BLOCK_ARCHIVED")

    def _validate_new_task_refs(
        self, *, current: CalendarSet, updated: CalendarSet
    ) -> None:
        current_refs = {
            event.event_ref: event.task_ref
            for event in current.events
            if event.task_ref is not None and not event.archived
        }
        new_events = tuple(
            event
            for event in updated.events
            if event.task_ref is not None
            and not event.archived
            and current_refs.get(event.event_ref) != event.task_ref
        )
        if new_events:
            self._validate_task_refs(updated.model_copy(update={"events": new_events}))

    def _project_event(
        self,
        workspace_ref: str,
        event: CalendarEvent,
        occurrence: CalendarOccurrence,
    ) -> CalendarEventProjection:
        if event.task_ref is None:
            return CalendarEventProjection(
                event=event,
                occurrence=occurrence,
                canonical_owner_ref="canonical-owner-ref:calendar",
                field_provenance_refs=(event.calendar_ref, event.event_ref),
            )
        if self.task_repository is None:
            raise CalendarError("ECO_CALENDAR_TASK_REPOSITORY_REQUIRED")
        try:
            task = self.task_repository.read(
                workspace_ref=workspace_ref,
                task_ref=event.task_ref,
            )
        except EcosystemLocalDataError as exc:
            if str(exc) != "ECO_RECORD_NOT_FOUND":
                raise
            return CalendarEventProjection(
                event=event,
                occurrence=occurrence,
                canonical_owner_ref="canonical-owner-ref:tasks",
                field_provenance_refs=(event.task_ref,),
                projection_state="missing",
            )
        return CalendarEventProjection(
            event=event,
            occurrence=occurrence,
            canonical_task=task,
            canonical_owner_ref="canonical-owner-ref:tasks",
            field_provenance_refs=(task.task_ref, task.safe_summary_ref),
            projection_state="archived" if task.archived else "current",
        )

    @staticmethod
    def _event_occurrences(
        event: CalendarEvent, starts_at: datetime, ends_at: datetime
    ) -> Iterator[CalendarOccurrence]:
        duration = event.ends_at - event.starts_at
        for index, candidate in enumerate(
            CalendarRepository._recurrence_starts(event, starts_at - duration, ends_at)
        ):
            occurrence_end = candidate + duration
            if occurrence_end <= starts_at or candidate >= ends_at:
                continue
            yield CalendarOccurrence(
                occurrence_ref=_stable_ref(
                    "calendar-occurrence-ref",
                    {"event_ref": event.event_ref, "starts_at": candidate.isoformat()},
                ),
                event_ref=event.event_ref,
                calendar_ref=event.calendar_ref,
                starts_at=candidate,
                ends_at=occurrence_end,
                timezone=event.timezone,
            )
            if index >= _MAX_OCCURRENCES:
                raise CalendarError("ECO_CALENDAR_OCCURRENCE_LIMIT_EXCEEDED")

    @staticmethod
    def _recurrence_starts(
        event: CalendarEvent, query_start: datetime, query_end: datetime
    ) -> Iterator[datetime]:
        if event.recurrence is None:
            yield event.starts_at
            return
        rule = event.recurrence
        zone = _zone(rule.timezone)
        anchor = event.starts_at.astimezone(zone)
        wall_time = anchor.timetz()

        def acceptable(candidate: datetime) -> bool:
            return rule.until is None or candidate <= rule.until

        if rule.frequency == CalendarRecurrenceFrequency.daily:
            query_day = query_start.astimezone(zone).date()
            elapsed_days = max(0, (query_day - anchor.date()).days - 1)
            sequence_index = elapsed_days // rule.interval
            offset = sequence_index * rule.interval
            while True:
                if rule.count is not None and sequence_index >= rule.count:
                    return
                candidate = _localize(
                    anchor.date() + timedelta(days=offset), wall_time, zone
                )
                if candidate >= query_end or not acceptable(candidate):
                    return
                yield candidate
                sequence_index += 1
                offset += rule.interval
        elif rule.frequency == CalendarRecurrenceFrequency.weekly:
            weekdays = tuple(sorted(rule.weekdays or (anchor.weekday(),)))
            first_week = anchor.date() - timedelta(days=anchor.weekday())
            first_weekdays = tuple(
                weekday for weekday in weekdays if weekday >= anchor.weekday()
            )
            query_day = query_start.astimezone(zone).date()
            elapsed_weeks = max(0, (query_day - first_week).days // 7 - 1)
            sequence_week = elapsed_weeks // rule.interval
            while True:
                week_start = first_week + timedelta(weeks=sequence_week * rule.interval)
                eligible_weekdays = first_weekdays if sequence_week == 0 else weekdays
                prior_count = (
                    0
                    if sequence_week == 0
                    else len(first_weekdays) + (sequence_week - 1) * len(weekdays)
                )
                for weekday_index, weekday in enumerate(eligible_weekdays):
                    ordinal = prior_count + weekday_index
                    if rule.count is not None and ordinal >= rule.count:
                        return
                    candidate = _localize(
                        week_start + timedelta(days=weekday), wall_time, zone
                    )
                    if candidate >= query_end or not acceptable(candidate):
                        return
                    yield candidate
                sequence_week += 1
        else:
            month_offset = 0
            target_day = rule.month_day or anchor.day
            emitted = 0
            while True:
                month_index = anchor.month - 1 + month_offset
                year = anchor.year + month_index // 12
                month = month_index % 12 + 1
                if target_day <= month_calendar.monthrange(year, month)[1]:
                    candidate = _localize(
                        date(year, month, target_day), wall_time, zone
                    )
                    if candidate >= query_end or not acceptable(candidate):
                        return
                    yield candidate
                    emitted += 1
                    if rule.count is not None and emitted >= rule.count:
                        return
                month_offset += rule.interval
                if month_offset > 12 * 100:
                    raise CalendarError("ECO_CALENDAR_RECURRENCE_SCAN_LIMIT_EXCEEDED")

    def _ensure_missing(self, workspace_ref: str, record_ref: str) -> None:
        try:
            self.platform.read(workspace_ref=workspace_ref, record_ref=record_ref)
        except EcosystemLocalDataError as exc:
            if str(exc) == "ECO_RECORD_NOT_FOUND":
                return
            raise
        raise CalendarConflict("ECO_CALENDAR_RECORD_ALREADY_EXISTS")

    def _apply(
        self,
        *,
        workspace_ref: str,
        record: CalendarSet,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        try:
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(
                    PutRecord(
                        operation_ref=operation_ref,
                        module_ref=ECO_CALENDAR_MODULE_REF,
                        record_ref=record.calendar_set_ref,
                        record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
                        safe_summary_ref=record.safe_summary_ref,
                        private_payload=record.model_dump(mode="json"),
                        search_terms=(_ALL_CALENDAR_SETS_SEARCH_TERM,),
                        expected_version=expected_version,
                        retention_ref=ECO_CALENDAR_RETENTION_REF,
                    ),
                ),
                approval=approval,
                requested_action=ECO_CALENDAR_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
        except EcosystemConflict as exc:
            if str(exc) == "ECO_STALE_RECORD_VERSION":
                raise CalendarConflict("ECO_CALENDAR_STALE_VERSION") from exc
            raise
        except ValueError as exc:
            if str(exc) == "ECO_PRIVATE_PAYLOAD_LIMIT_EXCEEDED":
                raise CalendarConflict(
                    "ECO_CALENDAR_PRIVATE_PAYLOAD_LIMIT_EXCEEDED"
                ) from exc
            raise

    def _replay(
        self,
        *,
        workspace_ref: str,
        record_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt | None:
        return self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=self.mutation_resource_refs(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                record_ref=record_ref,
            ),
            approval=approval,
            requested_action=ECO_CALENDAR_MUTATION_ACTION,
            request_context_ref=request_context_ref,
        )

    @staticmethod
    def _request_context_ref(kind: str, material: dict[str, Any]) -> str:
        return _stable_ref(
            "calendar-request-context-ref", {"kind": kind, "material": material}
        )


__all__ = [
    "ECO_CALENDAR_BUNDLE_SCHEMA_VERSION",
    "ECO_CALENDAR_MUTATION_ACTION",
    "ECO_CALENDAR_SCHEMA_VERSION",
    "CalendarConflict",
    "CalendarError",
    "CalendarEvent",
    "CalendarEventProjection",
    "CalendarImportPreview",
    "CalendarOccurrence",
    "CalendarOccurrenceConflict",
    "CalendarParticipant",
    "CalendarParticipantStatus",
    "CalendarPortableBundle",
    "CalendarRecurrenceFrequency",
    "CalendarRecurrenceRule",
    "CalendarReminder",
    "CalendarRepository",
    "CalendarSet",
    "CalendarSetSnapshot",
    "CalendarView",
    "CalendarViewResult",
    "LocalCalendar",
]
