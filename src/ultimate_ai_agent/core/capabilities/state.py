from __future__ import annotations

import json
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.models import Artifact, TaskPlan, TelemetryEvent, _assert_secret_clean
from ultimate_ai_agent.core.time import utc_now


COORDINATOR_STATE_SCHEMA_VERSION = "capability-coordinator-state/v1"


class CoordinatorAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"coord_audit_{uuid.uuid4().hex[:16]}")
    event_name: str = Field(..., min_length=1)
    trace_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    capability_id: str | None = None
    status: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_secret_free(self):
        _assert_secret_clean(self.model_dump(mode="json"), "coordinator_audit_event")
        return self


class CoordinatorRunRecord(BaseModel):
    trace_id: str
    plan_id: str
    status: str
    user_request: str
    plan: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: utc_now().isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_secret_free(self):
        _assert_secret_clean(self.model_dump(mode="json"), "coordinator_run_record")
        return self


class CoordinatorStateDocument(BaseModel):
    schema_version: str = COORDINATOR_STATE_SCHEMA_VERSION
    runs: dict[str, CoordinatorRunRecord] = Field(default_factory=dict)
    audit_events: list[CoordinatorAuditEvent] = Field(default_factory=list)
    telemetry_events: list[TelemetryEvent] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CoordinatorStateStore(Protocol):
    def save_plan(self, trace_id: str, plan: TaskPlan) -> None:
        ...

    def save_artifact(self, trace_id: str, plan_id: str, artifact: Artifact) -> None:
        ...

    def mark_run(self, trace_id: str, plan_id: str, status: str, reason_codes: list[str] | None = None) -> None:
        ...

    def record_audit_event(self, event: CoordinatorAuditEvent) -> None:
        ...

    def record_telemetry_event(self, event: TelemetryEvent) -> None:
        ...

    def list_audit_events(self, limit: int | None = None) -> list[CoordinatorAuditEvent]:
        ...


class InMemoryCoordinatorStateStore:
    def __init__(self):
        self.document = CoordinatorStateDocument()

    def save_plan(self, trace_id: str, plan: TaskPlan) -> None:
        self.document.runs[trace_id] = CoordinatorRunRecord(
            trace_id=trace_id,
            plan_id=plan.plan_id,
            status="planned",
            user_request=plan.user_request,
            plan=plan.model_dump(mode="json"),
            reason_codes=list(plan.reason_codes),
        )

    def save_artifact(self, trace_id: str, plan_id: str, artifact: Artifact) -> None:
        run = self.document.runs.get(trace_id)
        if run is None:
            run = CoordinatorRunRecord(trace_id=trace_id, plan_id=plan_id, status="running", user_request="unknown")
        artifacts = [*run.artifacts, artifact.model_dump(mode="json")]
        self.document.runs[trace_id] = run.model_copy(update={"artifacts": artifacts})

    def mark_run(self, trace_id: str, plan_id: str, status: str, reason_codes: list[str] | None = None) -> None:
        run = self.document.runs.get(trace_id)
        if run is None:
            run = CoordinatorRunRecord(trace_id=trace_id, plan_id=plan_id, status=status, user_request="unknown")
        self.document.runs[trace_id] = run.model_copy(
            update={
                "status": status,
                "reason_codes": reason_codes or run.reason_codes,
                "completed_at": utc_now().isoformat() if status in {"succeeded", "failed", "cancelled"} else run.completed_at,
            }
        )

    def record_audit_event(self, event: CoordinatorAuditEvent) -> None:
        self.document.audit_events.append(event)

    def record_telemetry_event(self, event: TelemetryEvent) -> None:
        self.document.telemetry_events.append(event)

    def list_audit_events(self, limit: int | None = None) -> list[CoordinatorAuditEvent]:
        events = list(self.document.audit_events)
        return events[-limit:] if limit is not None else events


class FileCoordinatorStateStore(InMemoryCoordinatorStateStore):
    def __init__(self, path: str | Path, *, max_audit_events: int = 10000, max_telemetry_events: int = 10000):
        self.path = Path(path)
        self.max_audit_events = max_audit_events
        self.max_telemetry_events = max_telemetry_events
        self._lock = threading.RLock()
        self.document = self._load()

    def save_plan(self, trace_id: str, plan: TaskPlan) -> None:
        with self._transaction() as document:
            document.runs[trace_id] = CoordinatorRunRecord(
                trace_id=trace_id,
                plan_id=plan.plan_id,
                status="planned",
                user_request=plan.user_request,
                plan=plan.model_dump(mode="json"),
                reason_codes=list(plan.reason_codes),
            )

    def save_artifact(self, trace_id: str, plan_id: str, artifact: Artifact) -> None:
        with self._transaction() as document:
            run = document.runs.get(trace_id)
            if run is None:
                run = CoordinatorRunRecord(trace_id=trace_id, plan_id=plan_id, status="running", user_request="unknown")
            document.runs[trace_id] = run.model_copy(
                update={"artifacts": [*run.artifacts, artifact.model_dump(mode="json")]}
            )

    def mark_run(self, trace_id: str, plan_id: str, status: str, reason_codes: list[str] | None = None) -> None:
        with self._transaction() as document:
            run = document.runs.get(trace_id)
            if run is None:
                run = CoordinatorRunRecord(trace_id=trace_id, plan_id=plan_id, status=status, user_request="unknown")
            document.runs[trace_id] = run.model_copy(
                update={
                    "status": status,
                    "reason_codes": reason_codes or run.reason_codes,
                    "completed_at": utc_now().isoformat()
                    if status in {"succeeded", "failed", "cancelled"}
                    else run.completed_at,
                }
            )

    def record_audit_event(self, event: CoordinatorAuditEvent) -> None:
        with self._transaction() as document:
            document.audit_events = [*document.audit_events, event][-self.max_audit_events :]

    def record_telemetry_event(self, event: TelemetryEvent) -> None:
        with self._transaction() as document:
            document.telemetry_events = [*document.telemetry_events, event][-self.max_telemetry_events :]

    def list_audit_events(self, limit: int | None = None) -> list[CoordinatorAuditEvent]:
        self.document = self._load()
        events = list(self.document.audit_events)
        return events[-limit:] if limit is not None else events

    @contextmanager
    def _transaction(self) -> Iterator[CoordinatorStateDocument]:
        with self._locked_file():
            document = self._load()
            yield document
            self._write(document)
            self.document = document

    def _load(self) -> CoordinatorStateDocument:
        if not self.path.exists():
            return CoordinatorStateDocument()
        return CoordinatorStateDocument.model_validate(json.loads(self.path.read_text(encoding="utf-8")))

    def _write(self, document: CoordinatorStateDocument) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}.tmp")
        temp_path.write_text(json.dumps(document.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(self.path)

    @contextmanager
    def _locked_file(self) -> Iterator[None]:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.path.with_suffix(".lock")
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                try:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                except (ImportError, OSError):
                    pass
                try:
                    yield
                finally:
                    try:
                        import fcntl

                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    except (ImportError, OSError):
                        pass
