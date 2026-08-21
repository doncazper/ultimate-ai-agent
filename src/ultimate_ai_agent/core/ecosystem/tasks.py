"""Canonical local Tasks core for ECO-002.

Tasks owns task truth.  The durable mission subsystem continues to own mission
execution state; this module stores only exact safe-ref bindings to that truth.
Recurrence materialization is explicit and never starts a scheduler or worker.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import sqlite3
import stat
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.local_data import (
    DeleteRecord,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_TASK_SCHEMA_VERSION = "uaa-eco-002-task.v1"
ECO_TASK_MUTATION_ACTION = "ecosystem.tasks.apply"
ECO_TASK_RECORD_KIND_REF = "record-kind-ref:canonical-task"
ECO_TASK_OCCURRENCE_RECORD_KIND_REF = "record-kind-ref:task-occurrence"
ECO_TASK_RETENTION_REF = "retention-ref:tasks-operator-managed"
ECO_TASK_MODULE_REF = "module-ref:tasks"
_ALL_TASKS_SEARCH_TERM = "entity-kind:canonical-task"
_MAX_LEGACY_DATABASE_BYTES = 64 * 1024 * 1024
_MAX_LEGACY_CANDIDATES = 10_000
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")


class TaskError(RuntimeError):
    """Fail-closed canonical Task error with a stable non-sensitive code."""


class TaskConflict(TaskError):
    pass


class TaskStatus(str, Enum):
    inbox = "inbox"
    ready = "ready"
    waiting = "waiting"
    completed = "completed"


class TaskPriority(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


class TaskView(str, Enum):
    all = "all"
    inbox = "inbox"
    today = "today"
    upcoming = "upcoming"
    anytime = "anytime"
    waiting = "waiting"
    flagged = "flagged"
    completed = "completed"
    overdue = "overdue"


class TaskRecurrenceCadence(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class _TaskModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_TASK_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_TASK_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _canonical_timestamp(value: str, code: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(code) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{code}_TIMEZONE_REQUIRED")
    return (
        parsed.astimezone(timezone.utc)
        .isoformat(timespec="auto")
        .replace("+00:00", "Z")
    )


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _hashed_search_term(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode()).hexdigest()}"


class TaskChecklistItem(_TaskModel):
    item_ref: str
    text: str = Field(..., repr=False)
    completed: bool = False

    @field_validator("item_ref")
    @classmethod
    def validate_item_ref(cls, value: str) -> str:
        return _validate_ref(value, "checklist_item_ref")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _private_text(
            value, maximum=2_048, code="ECO_TASK_CHECKLIST_TEXT_INVALID"
        )


class TaskRecurrenceRule(_TaskModel):
    cadence: TaskRecurrenceCadence
    interval: int = Field(default=1, ge=1, le=365)
    anchor_at: str
    timezone_name: str = Field(..., min_length=1, max_length=128)
    weekdays: tuple[int, ...] = Field(default=(), max_length=7)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    end_at: str | None = None
    materialization_mode: Literal["explicit_only"] = "explicit_only"
    background_execution_enabled: Literal[False] = False

    @field_validator("anchor_at")
    @classmethod
    def validate_anchor(cls, value: str) -> str:
        return _canonical_timestamp(value, "ECO_TASK_RECURRENCE_ANCHOR_INVALID")

    @field_validator("end_at")
    @classmethod
    def validate_end(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _canonical_timestamp(value, "ECO_TASK_RECURRENCE_END_INVALID")

    @model_validator(mode="after")
    def validate_rule(self) -> "TaskRecurrenceRule":
        try:
            ZoneInfo(self.timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("ECO_TASK_RECURRENCE_TIMEZONE_INVALID") from exc
        if len(self.weekdays) != len(set(self.weekdays)) or any(
            weekday < 0 or weekday > 6 for weekday in self.weekdays
        ):
            raise ValueError("ECO_TASK_RECURRENCE_WEEKDAYS_INVALID")
        if self.cadence != TaskRecurrenceCadence.weekly and self.weekdays:
            raise ValueError("ECO_TASK_RECURRENCE_WEEKDAYS_NOT_APPLICABLE")
        if self.cadence != TaskRecurrenceCadence.monthly and self.day_of_month:
            raise ValueError("ECO_TASK_RECURRENCE_MONTH_DAY_NOT_APPLICABLE")
        if self.end_at is not None and self.end_at < self.anchor_at:
            raise ValueError("ECO_TASK_RECURRENCE_END_BEFORE_ANCHOR")
        return self


class TaskMissionBinding(_TaskModel):
    mission_ref: str
    run_ref: str
    plan_ref: str
    owner_ref: str
    binding_evidence_ref: str
    handoff_ref: str | None = None
    recovery_ref: str | None = None
    mission_execution_state_owned_by_tasks: Literal[False] = False

    @model_validator(mode="after")
    def validate_refs(self) -> "TaskMissionBinding":
        for field_name in (
            "mission_ref",
            "run_ref",
            "plan_ref",
            "owner_ref",
            "binding_evidence_ref",
            "handoff_ref",
            "recovery_ref",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _validate_ref(value, field_name)
        return self


class CanonicalTask(_TaskModel):
    schema_version: Literal["uaa-eco-002-task.v1"] = ECO_TASK_SCHEMA_VERSION
    workspace_ref: str
    task_ref: str
    title: str = Field(..., repr=False)
    notes: str | None = Field(default=None, repr=False)
    status: TaskStatus = TaskStatus.inbox
    priority: TaskPriority = TaskPriority.none
    flagged: bool = False
    archived: bool = False
    project_ref: str | None = None
    parent_task_ref: str | None = None
    occurrence_of_ref: str | None = None
    waiting_on_ref: str | None = None
    dependency_refs: tuple[str, ...] = Field(default=(), max_length=64)
    checklist: tuple[TaskChecklistItem, ...] = Field(default=(), max_length=128)
    tag_refs: tuple[str, ...] = Field(default=(), max_length=64)
    context_refs: tuple[str, ...] = Field(default=(), max_length=32)
    provenance_refs: tuple[str, ...] = Field(default=(), max_length=32)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=64)
    start_at: str | None = None
    due_at: str | None = None
    completed_at: str | None = None
    recurrence: TaskRecurrenceRule | None = None
    mission_binding: TaskMissionBinding | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("workspace_ref", "task_ref")
    @classmethod
    def validate_required_refs(cls, value: str, info: Any) -> str:
        return _validate_ref(value, info.field_name)

    @field_validator(
        "project_ref",
        "parent_task_ref",
        "occurrence_of_ref",
        "waiting_on_ref",
    )
    @classmethod
    def validate_optional_refs(cls, value: str | None, info: Any) -> str | None:
        if value is not None:
            _validate_ref(value, info.field_name)
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _private_text(value, maximum=4_096, code="ECO_TASK_TITLE_INVALID")

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _private_text(value, maximum=64_000, code="ECO_TASK_NOTES_INVALID")

    @field_validator("start_at", "due_at", "completed_at")
    @classmethod
    def validate_timestamps(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _canonical_timestamp(
            value, f"ECO_TASK_{info.field_name.upper()}_INVALID"
        )

    @field_validator(
        "dependency_refs",
        "tag_refs",
        "context_refs",
        "provenance_refs",
        "evidence_refs",
    )
    @classmethod
    def validate_ref_groups(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        return _validate_refs(value, info.field_name)

    @model_validator(mode="after")
    def validate_task(self) -> "CanonicalTask":
        if self.task_ref in self.dependency_refs:
            raise ValueError("ECO_TASK_SELF_DEPENDENCY_DENIED")
        if self.parent_task_ref == self.task_ref:
            raise ValueError("ECO_TASK_SELF_PARENT_DENIED")
        if self.occurrence_of_ref == self.task_ref:
            raise ValueError("ECO_TASK_SELF_OCCURRENCE_DENIED")
        if self.parent_task_ref is not None and self.occurrence_of_ref is not None:
            raise ValueError("ECO_TASK_PARENT_AND_OCCURRENCE_CONFLICT")
        checklist_refs = [item.item_ref for item in self.checklist]
        if len(checklist_refs) != len(set(checklist_refs)):
            raise ValueError("ECO_TASK_DUPLICATE_CHECKLIST_ITEM_REF")
        if self.status == TaskStatus.completed and self.completed_at is None:
            raise ValueError("ECO_TASK_COMPLETED_AT_REQUIRED")
        if self.status != TaskStatus.completed and self.completed_at is not None:
            raise ValueError("ECO_TASK_COMPLETED_AT_NOT_APPLICABLE")
        if (
            self.status == TaskStatus.waiting
            and self.waiting_on_ref is None
            and not self.dependency_refs
        ):
            raise ValueError("ECO_TASK_WAITING_REASON_REQUIRED")
        if self.occurrence_of_ref is not None and (
            self.recurrence is not None or self.mission_binding is not None
        ):
            raise ValueError("ECO_TASK_OCCURRENCE_CANNOT_OWN_RULE_OR_MISSION")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "task-summary-ref",
            {
                "task_ref": self.task_ref,
                "status": self.status.value,
                "archived": self.archived,
                "version": self.version,
            },
        )

    @property
    def record_kind_ref(self) -> str:
        if self.occurrence_of_ref is not None:
            return ECO_TASK_OCCURRENCE_RECORD_KIND_REF
        return ECO_TASK_RECORD_KIND_REF


class TaskQuery(_TaskModel):
    workspace_ref: str
    view: TaskView = TaskView.all
    as_of: str
    timezone_name: str = Field(default="UTC", min_length=1, max_length=128)
    project_ref: str | None = None
    tag_ref: str | None = None

    @field_validator("workspace_ref")
    @classmethod
    def validate_workspace(cls, value: str) -> str:
        return _validate_ref(value, "workspace_ref")

    @field_validator("project_ref", "tag_ref")
    @classmethod
    def validate_filters(cls, value: str | None, info: Any) -> str | None:
        if value is not None:
            _validate_ref(value, info.field_name)
        return value

    @field_validator("as_of")
    @classmethod
    def validate_as_of(cls, value: str) -> str:
        return _canonical_timestamp(value, "ECO_TASK_QUERY_AS_OF_INVALID")

    @field_validator("timezone_name")
    @classmethod
    def validate_timezone_name(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("ECO_TASK_QUERY_TIMEZONE_INVALID") from exc
        return value


class TaskListResult(_TaskModel):
    query: TaskQuery
    tasks: tuple[CanonicalTask, ...]
    result_ref: str
    external_read_performed: Literal[False] = False
    background_work_started: Literal[False] = False

    @field_validator("result_ref")
    @classmethod
    def validate_result_ref(cls, value: str) -> str:
        return _validate_ref(value, "result_ref")


class TaskOccurrencePlan(_TaskModel):
    parent_task_ref: str
    parent_version: int = Field(..., ge=1)
    occurrence: CanonicalTask
    operation_ref: str
    idempotency_ref: str
    resource_refs: tuple[str, ...]
    plan_ref: str
    scheduler_started: Literal[False] = False
    background_work_started: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> "TaskOccurrencePlan":
        for field_name in (
            "parent_task_ref",
            "operation_ref",
            "idempotency_ref",
            "plan_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.resource_refs, "resource_refs")
        return self


class LegacyLocalTaskCandidate(_TaskModel):
    local_task_ref: str
    item_ref: str
    status_ref: str
    receipt_ref: str

    @model_validator(mode="after")
    def validate_candidate(self) -> "LegacyLocalTaskCandidate":
        for field_name in ("local_task_ref", "item_ref", "status_ref", "receipt_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        return self


class LegacyLocalTaskMigrationPreview(_TaskModel):
    source_format_ref: Literal["source-format-ref:founder-loop-local-tasks:v1"] = (
        "source-format-ref:founder-loop-local-tasks:v1"
    )
    source_fingerprint_ref: str
    candidates: tuple[LegacyLocalTaskCandidate, ...]
    preview_ref: str
    writes_performed: Literal[False] = False
    private_task_content_recovered: Literal[False] = False

    @field_validator("source_fingerprint_ref", "preview_ref")
    @classmethod
    def validate_preview_refs(cls, value: str, info: Any) -> str:
        return _validate_ref(value, info.field_name)


class FounderLoopLocalTaskCompatibilityReader:
    """Read only the bounded safe-ref legacy task inventory; never cut over."""

    def preview(self, database_path: Path) -> LegacyLocalTaskMigrationPreview:
        if (
            not database_path.is_absolute()
            or database_path == Path(database_path.anchor)
            or database_path.is_symlink()
        ):
            raise ValueError("ECO_TASK_MIGRATION_SOURCE_PATH_INVALID")
        try:
            stat_before = database_path.stat()
        except OSError:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_UNAVAILABLE") from None
        if not stat.S_ISREG(stat_before.st_mode):
            raise ValueError("ECO_TASK_MIGRATION_SOURCE_PATH_INVALID")
        if stat_before.st_size > _MAX_LEGACY_DATABASE_BYTES:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_SIZE_LIMIT_EXCEEDED")
        try:
            with database_path.open("rb") as source:
                source_bytes = source.read(_MAX_LEGACY_DATABASE_BYTES + 1)
        except OSError:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_UNAVAILABLE") from None
        if len(source_bytes) > _MAX_LEGACY_DATABASE_BYTES:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_SIZE_LIMIT_EXCEEDED")
        fingerprint = hashlib.sha256(source_bytes).hexdigest()
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                f"{database_path.as_uri()}?mode=ro&immutable=1", uri=True
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(local_tasks)")
            }
            required = {"local_task_ref", "item_ref", "status", "receipt_ref"}
            if not required.issubset(columns):
                raise TaskError("ECO_TASK_MIGRATION_SOURCE_SCHEMA_INVALID")
            rows = connection.execute(
                "SELECT local_task_ref, item_ref, status, receipt_ref "
                "FROM local_tasks ORDER BY local_task_ref LIMIT ?",
                (_MAX_LEGACY_CANDIDATES + 1,),
            ).fetchall()
        except sqlite3.Error:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_SCHEMA_INVALID") from None
        finally:
            if connection is not None:
                connection.close()
        try:
            stat_after = database_path.stat()
        except OSError:
            raise TaskError("ECO_TASK_MIGRATION_SOURCE_UNAVAILABLE") from None
        if (
            stat_before.st_ino != stat_after.st_ino
            or stat_before.st_size != stat_after.st_size
            or stat_before.st_mtime_ns != stat_after.st_mtime_ns
        ):
            raise TaskConflict("ECO_TASK_MIGRATION_SOURCE_CHANGED")
        if len(rows) > _MAX_LEGACY_CANDIDATES:
            raise TaskError("ECO_TASK_MIGRATION_CANDIDATE_LIMIT_EXCEEDED")
        candidates = tuple(
            LegacyLocalTaskCandidate(
                local_task_ref=row[0],
                item_ref=row[1],
                status_ref=row[2],
                receipt_ref=row[3],
            )
            for row in rows
        )
        source_fingerprint_ref = f"source-fingerprint-ref:sha256:{fingerprint}"
        preview_ref = _stable_ref(
            "task-migration-preview-ref",
            {
                "source_fingerprint_ref": source_fingerprint_ref,
                "candidate_refs": [
                    candidate.local_task_ref for candidate in candidates
                ],
            },
        )
        return LegacyLocalTaskMigrationPreview(
            source_fingerprint_ref=source_fingerprint_ref,
            candidates=candidates,
            preview_ref=preview_ref,
        )

    @staticmethod
    def prepare_candidate(
        *,
        candidate: LegacyLocalTaskCandidate,
        workspace_ref: str,
        task_ref: str,
        title: str,
    ) -> CanonicalTask:
        """Require operator-supplied private title; legacy rows contain none."""

        return CanonicalTask(
            workspace_ref=workspace_ref,
            task_ref=task_ref,
            title=title,
            status=TaskStatus.inbox,
            provenance_refs=(
                candidate.local_task_ref,
                candidate.item_ref,
                candidate.receipt_ref,
            ),
        )


class TaskRepository:
    """Canonical Task repository on the shared encrypted ECO-001 data plane."""

    def __init__(self, platform: EcosystemLocalDataPlatform) -> None:
        self.platform = platform

    @staticmethod
    def mutation_resource_refs(
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operation_ref: str,
        task_ref: str,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((workspace_ref, idempotency_ref, operation_ref, task_ref))
        )

    def create(
        self,
        *,
        task: CanonicalTask,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        _request_context_ref: str | None = None,
    ) -> UnitOfWorkReceipt:
        request_context_ref = _request_context_ref or self._request_context_ref(
            "create",
            {
                "task": task.model_dump(mode="json"),
                "operation_ref": operation_ref,
            },
        )
        return self._create(
            task=task,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=request_context_ref,
        )

    def _create(
        self,
        *,
        task: CanonicalTask,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        if task.version != 1:
            raise TaskConflict("ECO_TASK_CREATE_VERSION_INVALID")
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=task.workspace_ref,
                task_ref=task.task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            try:
                self.platform.read(
                    workspace_ref=task.workspace_ref, record_ref=task.task_ref
                )
            except EcosystemLocalDataError as exc:
                if str(exc) != "ECO_RECORD_NOT_FOUND":
                    raise
                self._validate_candidate(task, replacing_ref=None)
            return self.platform._apply_registered_domain(
                workspace_ref=task.workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(self._put(task, operation_ref, expected_version=0),),
                approval=approval,
                requested_action=ECO_TASK_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def save(
        self,
        *,
        task: CanonicalTask,
        operation_ref: str,
        idempotency_ref: str,
        expected_version: int,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "save",
            {
                "task": task.model_dump(mode="json"),
                "operation_ref": operation_ref,
                "expected_version": expected_version,
            },
        )
        return self._save(
            task=task,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            expected_version=expected_version,
            approval=approval,
            allow_archive_transition=False,
            request_context_ref=request_context_ref,
        )

    def _save(
        self,
        *,
        task: CanonicalTask,
        operation_ref: str,
        idempotency_ref: str,
        expected_version: int,
        approval: ApprovalValidationRequest,
        allow_archive_transition: bool,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        if task.version != expected_version + 1:
            raise TaskConflict("ECO_TASK_NEXT_VERSION_INVALID")
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=task.workspace_ref,
                task_ref=task.task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            current = self.read(
                workspace_ref=task.workspace_ref, task_ref=task.task_ref
            )
            operation = self._put(
                task, operation_ref, expected_version=expected_version
            )
            if current.version == task.version:
                return self.platform._apply_registered_domain(
                    workspace_ref=task.workspace_ref,
                    idempotency_ref=idempotency_ref,
                    operations=(operation,),
                    approval=approval,
                    requested_action=ECO_TASK_MUTATION_ACTION,
                    request_context_ref=request_context_ref,
                )
            if current.version != expected_version:
                raise TaskConflict("ECO_TASK_STALE_VERSION")
            if current.archived != task.archived:
                if not allow_archive_transition:
                    raise TaskConflict("ECO_TASK_ARCHIVE_TRANSITION_REQUIRES_LIFECYCLE")
                if task.archived:
                    self._ensure_no_active_references(task.workspace_ref, task.task_ref)
            self._validate_candidate(task, replacing_ref=task.task_ref)
            return self.platform._apply_registered_domain(
                workspace_ref=task.workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(operation,),
                approval=approval,
                requested_action=ECO_TASK_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def read(self, *, workspace_ref: str, task_ref: str) -> CanonicalTask:
        record = self.platform.read(workspace_ref=workspace_ref, record_ref=task_ref)
        try:
            task = CanonicalTask.model_validate(record.private_payload)
        except Exception as exc:
            raise TaskError("ECO_TASK_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            task.workspace_ref != workspace_ref
            or task.task_ref != task_ref
            or task.version != record.version
            or record.module_ref != ECO_TASK_MODULE_REF
            or task.record_kind_ref != record.record_kind_ref
            or task.safe_summary_ref != record.safe_summary_ref
        ):
            raise TaskError("ECO_TASK_RECORD_BINDING_INVALID")
        return task

    def query(self, query: TaskQuery) -> TaskListResult:
        tasks = self._all_tasks(query.workspace_ref)
        as_of = datetime.fromisoformat(query.as_of)
        query_zone = ZoneInfo(query.timezone_name)
        local_day = as_of.astimezone(query_zone).date()
        end_of_day = datetime.combine(
            local_day,
            time.max,
            tzinfo=query_zone,
        ).astimezone(timezone.utc)

        def included(task: CanonicalTask) -> bool:
            if query.project_ref is not None and task.project_ref != query.project_ref:
                return False
            if query.tag_ref is not None and query.tag_ref not in task.tag_refs:
                return False
            if query.view == TaskView.all:
                return True
            if query.view.value in {"inbox", "waiting", "completed"}:
                return task.status.value == query.view.value
            if query.view == TaskView.flagged:
                return task.flagged and task.status != TaskStatus.completed
            boundary = task.due_at or task.start_at
            if query.view == TaskView.anytime:
                return (
                    task.status != TaskStatus.completed
                    and task.start_at is None
                    and task.due_at is None
                )
            if boundary is None or task.status == TaskStatus.completed:
                return False
            parsed = datetime.fromisoformat(boundary)
            if query.view == TaskView.today:
                return parsed <= end_of_day
            if query.view == TaskView.upcoming:
                return parsed > end_of_day
            if query.view == TaskView.overdue:
                return parsed < as_of
            return False

        selected = tuple(sorted(filter(included, tasks), key=self._sort_key))
        result_ref = _stable_ref(
            "task-query-result-ref",
            {
                "query": query.model_dump(mode="json"),
                "task_versions": [(task.task_ref, task.version) for task in selected],
            },
        )
        return TaskListResult(query=query, tasks=selected, result_ref=result_ref)

    def capture(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        title: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        provenance_refs: tuple[str, ...] = (),
    ) -> UnitOfWorkReceipt:
        """Quick-capture one encrypted Inbox task through the exact write lane."""

        task = CanonicalTask(
            workspace_ref=workspace_ref,
            task_ref=task_ref,
            title=title,
            provenance_refs=provenance_refs,
        )
        return self.create(
            task=task,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )

    def complete(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        completed_at: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        canonical_completed_at = _canonical_timestamp(
            completed_at, "ECO_TASK_COMPLETED_AT_INVALID"
        )
        request_context_ref = self._request_context_ref(
            "complete",
            {
                "workspace_ref": workspace_ref,
                "task_ref": task_ref,
                "completed_at": canonical_completed_at,
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            task_ref=task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=request_context_ref,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, task_ref=task_ref)
        if current.status == TaskStatus.completed:
            if current.completed_at != canonical_completed_at:
                raise TaskConflict("ECO_TASK_COMPLETE_TIMESTAMP_CONFLICT")
            return self._save(
                task=current,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                expected_version=current.version - 1,
                approval=approval,
                allow_archive_transition=False,
                request_context_ref=request_context_ref,
            )
        updated = CanonicalTask.model_validate(
            {
                **current.model_dump(mode="json"),
                "status": TaskStatus.completed.value,
                "completed_at": completed_at,
                "version": current.version + 1,
            }
        )
        return self._save(
            task=updated,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            expected_version=current.version,
            approval=approval,
            allow_archive_transition=False,
            request_context_ref=request_context_ref,
        )

    def reopen(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "reopen",
            {
                "workspace_ref": workspace_ref,
                "task_ref": task_ref,
                "operation_ref": operation_ref,
            },
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            task_ref=task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=request_context_ref,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, task_ref=task_ref)
        if current.status != TaskStatus.completed:
            return self._save(
                task=current,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                expected_version=current.version - 1,
                approval=approval,
                allow_archive_transition=False,
                request_context_ref=request_context_ref,
            )
        updated = CanonicalTask.model_validate(
            {
                **current.model_dump(mode="json"),
                "status": TaskStatus.ready.value,
                "completed_at": None,
                "version": current.version + 1,
            }
        )
        return self._save(
            task=updated,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            expected_version=current.version,
            approval=approval,
            allow_archive_transition=False,
            request_context_ref=request_context_ref,
        )

    def archive(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "archive",
            {
                "workspace_ref": workspace_ref,
                "task_ref": task_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
            },
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=workspace_ref,
                task_ref=task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            current = self.read(workspace_ref=workspace_ref, task_ref=task_ref)
            if current.archived and current.version == expected_version + 1:
                return self._save(
                    task=current,
                    operation_ref=operation_ref,
                    idempotency_ref=idempotency_ref,
                    expected_version=expected_version,
                    approval=approval,
                    allow_archive_transition=True,
                    request_context_ref=request_context_ref,
                )
            if current.version != expected_version:
                raise TaskConflict("ECO_TASK_STALE_VERSION")
            if current.archived:
                raise TaskConflict("ECO_TASK_ALREADY_ARCHIVED")
            updated = CanonicalTask.model_validate(
                {
                    **current.model_dump(mode="json"),
                    "archived": True,
                    "version": current.version + 1,
                }
            )
            return self._save(
                task=updated,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                expected_version=expected_version,
                approval=approval,
                allow_archive_transition=True,
                request_context_ref=request_context_ref,
            )

    def restore(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "restore",
            {
                "workspace_ref": workspace_ref,
                "task_ref": task_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
            },
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=workspace_ref,
                task_ref=task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            current = self.read(workspace_ref=workspace_ref, task_ref=task_ref)
            if not current.archived and current.version == expected_version + 1:
                return self._save(
                    task=current,
                    operation_ref=operation_ref,
                    idempotency_ref=idempotency_ref,
                    expected_version=expected_version,
                    approval=approval,
                    allow_archive_transition=True,
                    request_context_ref=request_context_ref,
                )
            if current.version != expected_version:
                raise TaskConflict("ECO_TASK_STALE_VERSION")
            if not current.archived:
                raise TaskConflict("ECO_TASK_NOT_ARCHIVED")
            updated = CanonicalTask.model_validate(
                {
                    **current.model_dump(mode="json"),
                    "archived": False,
                    "version": current.version + 1,
                }
            )
            return self._save(
                task=updated,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                expected_version=expected_version,
                approval=approval,
                allow_archive_transition=True,
                request_context_ref=request_context_ref,
            )

    def delete(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "delete",
            {
                "workspace_ref": workspace_ref,
                "task_ref": task_ref,
                "expected_version": expected_version,
                "operation_ref": operation_ref,
            },
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=workspace_ref,
                task_ref=task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            self._ensure_no_active_references(workspace_ref, task_ref)
            operation = DeleteRecord(
                operation_ref=operation_ref,
                record_ref=task_ref,
                expected_version=expected_version,
            )
            try:
                current = self.read(workspace_ref=workspace_ref, task_ref=task_ref)
            except EcosystemLocalDataError as exc:
                if str(exc) != "ECO_RECORD_NOT_FOUND":
                    raise
                return self.platform._apply_registered_domain(
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    operations=(operation,),
                    approval=approval,
                    requested_action=ECO_TASK_MUTATION_ACTION,
                    request_context_ref=request_context_ref,
                )
            if current.version != expected_version:
                raise TaskConflict("ECO_TASK_STALE_VERSION")
            if not current.archived:
                raise TaskConflict("ECO_TASK_DELETE_REQUIRES_ARCHIVE")
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(operation,),
                approval=approval,
                requested_action=ECO_TASK_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def plan_next_occurrence(
        self,
        *,
        workspace_ref: str,
        parent_task_ref: str,
        after: str,
        idempotency_ref: str,
    ) -> TaskOccurrencePlan:
        parent = self.read(workspace_ref=workspace_ref, task_ref=parent_task_ref)
        if parent.recurrence is None or parent.occurrence_of_ref is not None:
            raise TaskConflict("ECO_TASK_RECURRENCE_RULE_REQUIRED")
        scheduled_for = self._next_occurrence(parent.recurrence, after)
        occurrence_ref = _stable_ref(
            "task-occurrence-ref",
            {
                "parent_task_ref": parent.task_ref,
                "scheduled_for": scheduled_for,
            },
        )
        operation_ref = _stable_ref(
            "operation-ref:task-occurrence-materialize",
            {"occurrence_ref": occurrence_ref},
        )
        occurrence = CanonicalTask(
            workspace_ref=workspace_ref,
            task_ref=occurrence_ref,
            title=parent.title,
            notes=parent.notes,
            status=TaskStatus.ready,
            priority=parent.priority,
            flagged=parent.flagged,
            project_ref=parent.project_ref,
            occurrence_of_ref=parent.task_ref,
            checklist=tuple(
                TaskChecklistItem(item_ref=item.item_ref, text=item.text)
                for item in parent.checklist
            ),
            tag_refs=parent.tag_refs,
            context_refs=parent.context_refs,
            provenance_refs=tuple(
                dict.fromkeys(parent.provenance_refs + (parent.task_ref,))
            ),
            start_at=scheduled_for,
            due_at=scheduled_for,
        )
        resource_refs = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operation_ref=operation_ref,
            task_ref=occurrence_ref,
        )
        plan_ref = _stable_ref(
            "task-occurrence-plan-ref",
            {
                "parent_task_ref": parent.task_ref,
                "parent_version": parent.version,
                "occurrence_ref": occurrence_ref,
                "resource_refs": resource_refs,
            },
        )
        return TaskOccurrencePlan(
            parent_task_ref=parent.task_ref,
            parent_version=parent.version,
            occurrence=occurrence,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=resource_refs,
            plan_ref=plan_ref,
        )

    def materialize_occurrence(
        self,
        *,
        plan: TaskOccurrencePlan,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = self._request_context_ref(
            "materialize_occurrence",
            {
                "plan_ref": plan.plan_ref,
                "parent_task_ref": plan.parent_task_ref,
                "parent_version": plan.parent_version,
                "task": plan.occurrence.model_dump(mode="json"),
                "operation_ref": plan.operation_ref,
            },
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self._replay(
                workspace_ref=plan.occurrence.workspace_ref,
                task_ref=plan.occurrence.task_ref,
                operation_ref=plan.operation_ref,
                idempotency_ref=plan.idempotency_ref,
                approval=approval,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            parent = self.read(
                workspace_ref=plan.occurrence.workspace_ref,
                task_ref=plan.parent_task_ref,
            )
            if parent.version != plan.parent_version:
                raise TaskConflict("ECO_TASK_RECURRENCE_PLAN_STALE")
            return self.create(
                task=plan.occurrence,
                operation_ref=plan.operation_ref,
                idempotency_ref=plan.idempotency_ref,
                approval=approval,
                _request_context_ref=request_context_ref,
            )

    def _put(
        self,
        task: CanonicalTask,
        operation_ref: str,
        *,
        expected_version: int,
    ) -> PutRecord:
        return PutRecord(
            operation_ref=operation_ref,
            record_ref=task.task_ref,
            expected_version=expected_version,
            module_ref=ECO_TASK_MODULE_REF,
            record_kind_ref=task.record_kind_ref,
            safe_summary_ref=task.safe_summary_ref,
            private_payload=task.model_dump(mode="json"),
            search_terms=self._search_terms(task),
            retention_ref=ECO_TASK_RETENTION_REF,
            expires_at=None,
        )

    @staticmethod
    def _request_context_ref(kind: str, material: dict[str, Any]) -> str:
        return _stable_ref(
            "task-request-context-ref",
            {"kind": kind, "material": material},
        )

    def _replay(
        self,
        *,
        workspace_ref: str,
        task_ref: str,
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
                task_ref=task_ref,
            ),
            approval=approval,
            requested_action=ECO_TASK_MUTATION_ACTION,
            request_context_ref=request_context_ref,
        )

    @staticmethod
    def _search_terms(task: CanonicalTask) -> tuple[str, ...]:
        terms = [
            _ALL_TASKS_SEARCH_TERM,
            f"task-status:{task.status.value}",
        ]
        if task.project_ref:
            terms.append(_hashed_search_term("task-project", task.project_ref))
        if task.mission_binding:
            terms.append(
                _hashed_search_term("task-mission", task.mission_binding.mission_ref)
            )
        terms.extend(_hashed_search_term("task-tag", ref) for ref in task.tag_refs)
        return tuple(terms)

    def _all_tasks(
        self, workspace_ref: str, *, include_archived: bool = False
    ) -> tuple[CanonicalTask, ...]:
        refs = self.platform.search(
            workspace_ref=workspace_ref, term=_ALL_TASKS_SEARCH_TERM
        )
        tasks = tuple(
            self.read(workspace_ref=workspace_ref, task_ref=ref) for ref in refs
        )
        if include_archived:
            return tasks
        return tuple(task for task in tasks if not task.archived)

    def _validate_candidate(
        self, task: CanonicalTask, *, replacing_ref: str | None
    ) -> None:
        all_tasks = {
            item.task_ref: item
            for item in self._all_tasks(task.workspace_ref, include_archived=True)
        }
        if replacing_ref is None and task.task_ref in all_tasks:
            raise TaskConflict("ECO_TASK_ALREADY_EXISTS")
        tasks = {ref: item for ref, item in all_tasks.items() if not item.archived}
        if not task.archived:
            tasks[task.task_ref] = task
        elif replacing_ref is not None:
            tasks.pop(task.task_ref, None)
        for required_ref in (
            *task.dependency_refs,
            *(() if task.parent_task_ref is None else (task.parent_task_ref,)),
            *(() if task.occurrence_of_ref is None else (task.occurrence_of_ref,)),
        ):
            if required_ref not in tasks:
                raise TaskConflict("ECO_TASK_RELATED_TASK_NOT_FOUND")
        mission_refs: dict[str, str] = {}
        for item in tasks.values():
            if item.mission_binding is None:
                continue
            existing = mission_refs.setdefault(
                item.mission_binding.mission_ref, item.task_ref
            )
            if existing != item.task_ref:
                raise TaskConflict("ECO_TASK_MISSION_ALREADY_OWNED")
        dependencies = {ref: set(item.dependency_refs) for ref, item in tasks.items()}
        self._ensure_acyclic(
            dependencies, conflict_code="ECO_TASK_DEPENDENCY_CYCLE_DENIED"
        )
        hierarchy = {
            ref: {
                related_ref
                for related_ref in (item.parent_task_ref, item.occurrence_of_ref)
                if related_ref is not None
            }
            for ref, item in tasks.items()
        }
        self._ensure_acyclic(
            hierarchy, conflict_code="ECO_TASK_PARENT_CYCLE_DENIED"
        )

    @staticmethod
    def _ensure_acyclic(edges: dict[str, set[str]], *, conflict_code: str) -> None:
        dependencies = {ref: set(required) for ref, required in edges.items()}
        ready = sorted(ref for ref, refs in dependencies.items() if not refs)
        visited: list[str] = []
        while ready:
            current = ready.pop(0)
            visited.append(current)
            for ref, unresolved in dependencies.items():
                if current in unresolved:
                    unresolved.remove(current)
                    if not unresolved and ref not in visited + ready:
                        ready.append(ref)
                        ready.sort()
        if len(visited) != len(dependencies):
            raise TaskConflict(conflict_code)

    def _ensure_no_active_references(self, workspace_ref: str, task_ref: str) -> None:
        for item in self._all_tasks(workspace_ref):
            if item.task_ref == task_ref:
                continue
            if (
                task_ref in item.dependency_refs
                or item.parent_task_ref == task_ref
                or item.occurrence_of_ref == task_ref
            ):
                raise TaskConflict("ECO_TASK_ACTIVE_REFERENCE_BLOCKS_REMOVAL")

    @staticmethod
    def _sort_key(task: CanonicalTask) -> tuple[Any, ...]:
        priority_order = {
            TaskPriority.high: 0,
            TaskPriority.medium: 1,
            TaskPriority.low: 2,
            TaskPriority.none: 3,
        }
        return (
            task.due_at or task.start_at or "9999-12-31T23:59:59Z",
            priority_order[task.priority],
            task.task_ref,
        )

    @staticmethod
    def _next_occurrence(rule: TaskRecurrenceRule, after: str) -> str:
        after_utc = datetime.fromisoformat(
            _canonical_timestamp(after, "ECO_TASK_RECURRENCE_AFTER_INVALID")
        )
        zone = ZoneInfo(rule.timezone_name)
        anchor = datetime.fromisoformat(rule.anchor_at).astimezone(zone)
        after_local = after_utc.astimezone(zone)
        candidate: datetime | None = None
        if rule.cadence == TaskRecurrenceCadence.daily:
            elapsed = max(0, (after_local.date() - anchor.date()).days)
            increments = elapsed // rule.interval
            candidate_date = anchor.date() + timedelta(days=increments * rule.interval)
            candidate = datetime.combine(candidate_date, anchor.timetz(), tzinfo=zone)
            if candidate <= after_local or candidate < anchor:
                candidate_date += timedelta(days=rule.interval)
                candidate = datetime.combine(
                    candidate_date, anchor.timetz(), tzinfo=zone
                )
        elif rule.cadence == TaskRecurrenceCadence.weekly:
            weekdays = set(rule.weekdays or (anchor.weekday(),))
            cursor = max(anchor.date(), after_local.date())
            for _ in range(3_660):
                weeks = (cursor - anchor.date()).days // 7
                possible = datetime.combine(cursor, anchor.timetz(), tzinfo=zone)
                if (
                    cursor.weekday() in weekdays
                    and weeks % rule.interval == 0
                    and possible >= anchor
                    and possible > after_local
                ):
                    candidate = possible
                    break
                cursor += timedelta(days=1)
        else:
            month_index = anchor.year * 12 + anchor.month - 1
            after_index = after_local.year * 12 + after_local.month - 1
            increments = max(0, (after_index - month_index) // rule.interval)
            for offset in range(increments, increments + 1_200):
                index = month_index + offset * rule.interval
                year, zero_month = divmod(index, 12)
                month = zero_month + 1
                day = min(
                    rule.day_of_month or anchor.day,
                    calendar.monthrange(year, month)[1],
                )
                possible = datetime.combine(
                    date(year, month, day),
                    time(
                        anchor.hour,
                        anchor.minute,
                        anchor.second,
                        anchor.microsecond,
                    ),
                    tzinfo=zone,
                )
                if possible >= anchor and possible > after_local:
                    candidate = possible
                    break
        if candidate is None:
            raise TaskError("ECO_TASK_RECURRENCE_SEARCH_LIMIT_EXCEEDED")
        result = (
            candidate.astimezone(timezone.utc)
            .isoformat(timespec="auto")
            .replace("+00:00", "Z")
        )
        if rule.end_at is not None and datetime.fromisoformat(
            result
        ) > datetime.fromisoformat(rule.end_at):
            raise TaskConflict("ECO_TASK_RECURRENCE_ENDED")
        return result


__all__ = [
    "CanonicalTask",
    "ECO_TASK_MUTATION_ACTION",
    "ECO_TASK_SCHEMA_VERSION",
    "FounderLoopLocalTaskCompatibilityReader",
    "LegacyLocalTaskCandidate",
    "LegacyLocalTaskMigrationPreview",
    "TaskChecklistItem",
    "TaskConflict",
    "TaskError",
    "TaskListResult",
    "TaskMissionBinding",
    "TaskOccurrencePlan",
    "TaskPriority",
    "TaskQuery",
    "TaskRecurrenceCadence",
    "TaskRecurrenceRule",
    "TaskRepository",
    "TaskStatus",
    "TaskView",
]
