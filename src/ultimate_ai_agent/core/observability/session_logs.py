from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


SESSION_EVENT_SCHEMA_VERSION = "uaa.session_event.v1"
SESSION_LOG_ROOT_ENV = "UAA_SESSION_LOG_ROOT"
SESSION_LOG_ENABLED_ENV = "UAA_SESSION_LOG_ENABLED"
DEFAULT_SESSION_LOG_RELATIVE_PATH = Path("observability") / "session_events.jsonl"
DEFAULT_SESSION_LOG_LIMIT = 50
MAX_SESSION_LOG_LIMIT = 500
MAX_SAFE_TEXT_CHARS = 320
MAX_METADATA_TEXT_CHARS = 512
MAX_METADATA_KEYS = 32
MAX_METADATA_LIST_ITEMS = 50

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,159}$")
EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
HASH_RE = re.compile(r"^(?:sha256|stack-sha256):[a-f0-9]{64}$")
LOCAL_PRIVATE_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")

UNSAFE_METADATA_KEY_MARKERS = (
    "raw",
    "body",
    "payload",
    "prompt",
    "completion",
    "response_text",
    "request_text",
    "stdout",
    "stderr",
    "terminal_output",
    "shell_output",
    "file_content",
    "file_text",
    "cookie",
    "authorization",
    "auth",
    "token",
    "secret",
    "api_key",
    "password",
    "credential",
    "private_key",
    "access_key",
    "refresh_token",
    "id_token",
)

KNOWN_SERVICES = {
    "api",
    "backend",
    "capability_registry",
    "control_center",
    "dev_launcher",
    "event_ledger",
    "extension_catalog",
    "file_workbench",
    "foundation_gate",
    "frontend",
    "kernel",
    "local_model",
    "openwebui",
    "receipt_store",
    "runtime_readiness",
    "task_decomposition",
    "unknown",
}

KNOWN_SURFACES = {
    "api",
    "capability_execution",
    "control_center",
    "dev_service",
    "event_ledger",
    "frontend_client",
    "kernel",
    "launcher",
    "local_model",
    "receipt",
    "runtime",
    "system",
    "task_decomposition",
}

KNOWN_STATUSES = {
    "blocked",
    "completed",
    "denied",
    "failed",
    "recorded",
    "ready",
    "requested",
    "running",
    "skipped",
    "started",
    "succeeded",
    "timeout",
    "waiting_approval",
}

KNOWN_LIFECYCLE_STATES = {
    "blocked",
    "completed",
    "denied",
    "exited",
    "failed",
    "normal",
    "ready",
    "requested",
    "running",
    "skipped",
    "slow",
    "started",
    "stopped",
    "succeeded",
    "timeout",
    "waiting_approval",
}

KNOWN_SEVERITIES = {"debug", "info", "warning", "error", "critical"}


class SessionLogValidationError(ValueError):
    """Safe validation error for rejected session log records."""


class SessionLogStorageError(ValueError):
    """Safe storage error for local session log writes."""


class SessionEvent(BaseModel):
    schema_version: str = SESSION_EVENT_SCHEMA_VERSION
    event_id: str = Field(default_factory=lambda: f"session-event:{uuid.uuid4().hex}", min_length=1)
    session_id: str = Field(..., min_length=1)
    run_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    correlation_id: str | None = None
    service: str = Field(..., min_length=1)
    surface: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    lifecycle_state: str | None = None
    status: str = Field(..., min_length=1)
    severity: str = "info"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    observed_at: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = Field(default=None, ge=0)
    safe_summary: str = Field(..., min_length=1, max_length=MAX_SAFE_TEXT_CHARS)
    reason_codes: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_summary: str | None = Field(default=None, max_length=MAX_SAFE_TEXT_CHARS)
    stack_hash: str | None = None
    prompt_ref: str | None = None
    prompt_hash: str | None = None
    prompt_template_id: str | None = None
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    redaction_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "event_id",
        "session_id",
        "run_id",
        "trace_id",
        "span_id",
        "parent_span_id",
        "correlation_id",
        "error_code",
        "prompt_ref",
        "prompt_template_id",
        mode="after",
    )
    @classmethod
    def validate_safe_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _validate_safe_identifier(value)
        return value

    @field_validator("service", mode="after")
    @classmethod
    def validate_service(cls, value: str) -> str:
        if value not in KNOWN_SERVICES:
            raise ValueError("SESSION_LOG_SERVICE_UNSUPPORTED")
        return value

    @field_validator("surface", mode="after")
    @classmethod
    def validate_surface(cls, value: str) -> str:
        if value not in KNOWN_SURFACES:
            raise ValueError("SESSION_LOG_SURFACE_UNSUPPORTED")
        return value

    @field_validator("event_type", mode="after")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if not EVENT_TYPE_RE.match(value):
            raise ValueError("SESSION_LOG_EVENT_TYPE_UNSUPPORTED")
        _validate_safe_text(value, "event_type", max_chars=128)
        return value

    @field_validator("status", mode="after")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in KNOWN_STATUSES:
            raise ValueError("SESSION_LOG_STATUS_UNSUPPORTED")
        return value

    @field_validator("lifecycle_state", mode="after")
    @classmethod
    def validate_lifecycle_state(cls, value: str | None) -> str | None:
        if value is not None and value not in KNOWN_LIFECYCLE_STATES:
            raise ValueError("SESSION_LOG_LIFECYCLE_UNSUPPORTED")
        return value

    @field_validator("severity", mode="after")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in KNOWN_SEVERITIES:
            raise ValueError("SESSION_LOG_SEVERITY_UNSUPPORTED")
        return value

    @field_validator("safe_summary", "error_summary", mode="after")
    @classmethod
    def validate_summary_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _validate_safe_text(value, "summary", max_chars=MAX_SAFE_TEXT_CHARS)
        return value

    @field_validator("reason_codes", mode="after")
    @classmethod
    def validate_reason_codes(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_identifier(value)
        return list(dict.fromkeys(values))

    @field_validator("input_refs", "output_refs", "evidence_refs", "receipt_refs", mode="after")
    @classmethod
    def validate_refs(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_identifier(value)
        return list(dict.fromkeys(values))

    @field_validator("stack_hash", "prompt_hash", mode="after")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not HASH_RE.match(value):
            raise ValueError("SESSION_LOG_HASH_INVALID")
        return value

    @model_validator(mode="after")
    def validate_session_event(self) -> Any:
        if self.schema_version != SESSION_EVENT_SCHEMA_VERSION:
            raise ValueError("SESSION_LOG_SCHEMA_VERSION_UNSUPPORTED")
        _validate_metadata_payload(self.metadata, "metadata")
        _validate_metadata_payload(self.redaction_summary, "redaction_summary")
        return self


class SessionEventSummary(BaseModel):
    schema_version: str
    event_id: str
    session_id: str
    run_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    correlation_id: str | None = None
    service: str
    surface: str
    event_type: str
    lifecycle_state: str | None = None
    status: str
    severity: str
    observed_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    safe_summary: str
    reason_codes: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_summary: str | None = None
    stack_hash: str | None = None
    prompt_ref: str | None = None
    prompt_hash: str | None = None
    prompt_template_id: str | None = None
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    redaction_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class SessionLogListResult(BaseModel):
    schema_version: str = "uaa.session_log_list.v1"
    log_ref: str
    limit: int
    returned_count: int
    skipped_malformed_count: int = 0
    events: list[SessionEventSummary] = Field(default_factory=list)
    bounded: bool = True
    safe_summary_only: bool = True
    raw_records_exposed: bool = False

    model_config = ConfigDict(extra="forbid")


class ClientErrorReport(BaseModel):
    component: str = Field(..., min_length=1, max_length=80)
    surface: str = Field(..., min_length=1, max_length=80)
    route_name: str | None = Field(default=None, max_length=120)
    safe_error_message: str = Field(..., min_length=1, max_length=MAX_SAFE_TEXT_CHARS)
    stack_hash: str | None = None
    runtime_category: str | None = Field(default=None, max_length=80)
    timestamp: datetime | None = None
    correlation_id: str | None = None
    session_id: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("component", "surface", "route_name", "runtime_category", mode="after")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _validate_safe_label(value, max_chars=120)
        return value

    @field_validator("safe_error_message", mode="after")
    @classmethod
    def validate_error_message(cls, value: str) -> str:
        _validate_safe_text(value, "safe_error_message", max_chars=MAX_SAFE_TEXT_CHARS)
        return value

    @field_validator("stack_hash", mode="after")
    @classmethod
    def validate_stack_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not HASH_RE.match(value):
            raise ValueError("CLIENT_ERROR_STACK_HASH_INVALID")
        return value

    @field_validator("correlation_id", "session_id", mode="after")
    @classmethod
    def validate_optional_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _validate_safe_identifier(value)
        return value


class SessionLogStore:
    """Durable local JSONL store for redacted UAA-managed session events."""

    def __init__(self, root: str | Path | None = None, *, filepath: str | Path | None = None) -> None:
        if filepath is not None:
            self.filepath = Path(filepath)
            self.root = self.filepath.parent.parent
        else:
            self.root = Path(root) if root is not None else default_session_log_root()
            self.filepath = self.root / DEFAULT_SESSION_LOG_RELATIVE_PATH
        self._lock = threading.RLock()
        self._events: list[SessionEvent] = []
        self._event_ids: set[str] = set()
        self._malformed_line_count = 0
        self._load_from_file()

    @property
    def log_ref(self) -> str:
        return "session-log:local-jsonl"

    @property
    def malformed_line_count(self) -> int:
        return self._malformed_line_count

    def append(self, event: SessionEvent | dict[str, Any]) -> SessionEvent:
        with self._lock:
            validated = _coerce_session_event(event)
            if validated.event_id in self._event_ids:
                raise SessionLogValidationError("SESSION_LOG_DUPLICATE_EVENT_ID")
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self.filepath.open("a", encoding="utf-8") as handle:
                    handle.write(validated.model_dump_json() + "\n")
            except OSError as exc:
                raise SessionLogStorageError("SESSION_LOG_APPEND_FAILED") from exc
            self._append_in_memory(validated)
            return validated.model_copy(deep=True)

    def list_events(
        self,
        *,
        session_id: str | None = None,
        run_id: str | None = None,
        event_type: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        surface: str | None = None,
        service: str | None = None,
        observed_after: datetime | None = None,
        observed_before: datetime | None = None,
        limit: int = DEFAULT_SESSION_LOG_LIMIT,
    ) -> SessionLogListResult:
        bounded_limit = min(max(limit, 1), MAX_SESSION_LOG_LIMIT)
        with self._lock:
            events = list(self._events)
            malformed_line_count = self._malformed_line_count
        if session_id is not None:
            events = [event for event in events if event.session_id == session_id]
        if run_id is not None:
            events = [event for event in events if event.run_id == run_id]
        if event_type is not None:
            events = [event for event in events if event.event_type == event_type]
        if severity is not None:
            events = [event for event in events if event.severity == severity]
        if status is not None:
            events = [event for event in events if event.status == status]
        if surface is not None:
            events = [event for event in events if event.surface == surface]
        if service is not None:
            events = [event for event in events if event.service == service]
        if observed_after is not None:
            events = [event for event in events if event.observed_at >= observed_after]
        if observed_before is not None:
            events = [event for event in events if event.observed_at <= observed_before]
        events.sort(key=lambda event: (event.observed_at, event.completed_at or event.observed_at, event.event_id))
        selected = events[-bounded_limit:]
        return SessionLogListResult(
            log_ref=self.log_ref,
            limit=bounded_limit,
            returned_count=len(selected),
            skipped_malformed_count=malformed_line_count,
            events=[safe_summary_projection(event) for event in selected],
        )

    def recent_failures(self, *, limit: int = DEFAULT_SESSION_LOG_LIMIT) -> SessionLogListResult:
        return self.list_events(status="failed", limit=limit)

    def slow_actions(self, *, limit: int = DEFAULT_SESSION_LOG_LIMIT) -> SessionLogListResult:
        bounded_limit = min(max(limit, 1), MAX_SESSION_LOG_LIMIT)
        with self._lock:
            events = [
                event
                for event in self._events
                if event.lifecycle_state in {"slow", "timeout"} or event.status == "timeout"
            ]
            malformed_line_count = self._malformed_line_count
        events.sort(key=lambda event: (event.observed_at, event.event_id))
        selected = events[-bounded_limit:]
        return SessionLogListResult(
            log_ref=self.log_ref,
            limit=bounded_limit,
            returned_count=len(selected),
            skipped_malformed_count=malformed_line_count,
            events=[safe_summary_projection(event) for event in selected],
        )

    def _load_from_file(self) -> None:
        if not self.filepath.exists():
            return
        with self.filepath.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = SessionEvent.model_validate(json.loads(stripped))
                except (json.JSONDecodeError, ValidationError, ValueError):
                    self._malformed_line_count += 1
                    continue
                if event.event_id in self._event_ids:
                    self._malformed_line_count += 1
                    continue
                self._append_in_memory(event)

    def _append_in_memory(self, event: SessionEvent) -> None:
        self._events.append(event)
        self._event_ids.add(event.event_id)


def default_session_log_root() -> Path:
    return Path(os.environ.get(SESSION_LOG_ROOT_ENV, ".uaa"))


def session_logging_enabled() -> bool:
    return os.environ.get(SESSION_LOG_ENABLED_ENV, "1").strip().lower() not in {"0", "false", "no", "off"}


def get_default_session_log_store() -> SessionLogStore:
    return _cached_default_store(str(default_session_log_root()))


def clear_default_session_log_store_cache() -> None:
    _cached_default_store.cache_clear()


@lru_cache(maxsize=8)
def _cached_default_store(root: str) -> SessionLogStore:
    return SessionLogStore(root=Path(root))


def record_session_event(
    event: SessionEvent | dict[str, Any] | None = None,
    *,
    store: SessionLogStore | None = None,
    fail_closed: bool = True,
    **fields: Any,
) -> SessionEvent | None:
    if not session_logging_enabled():
        return None
    active_store = store or get_default_session_log_store()
    payload: SessionEvent | dict[str, Any]
    if event is not None and fields:
        raise SessionLogValidationError("SESSION_LOG_EVENT_AMBIGUOUS")
    payload = event if event is not None else fields
    try:
        return active_store.append(payload)
    except (SessionLogValidationError, SessionLogStorageError):
        if fail_closed:
            raise
    except (ValidationError, ValueError) as exc:
        if fail_closed:
            raise SessionLogValidationError("SESSION_LOG_EVENT_UNSAFE") from exc
    return None


def record_client_error_report(report: ClientErrorReport, *, store: SessionLogStore | None = None) -> SessionEvent | None:
    session_id = report.session_id or "control-center-session:local"
    correlation_id = report.correlation_id or build_safe_ref("correlation", report.component, report.surface)
    return record_session_event(
        store=store,
        session_id=session_id,
        correlation_id=correlation_id,
        service="control_center",
        surface="frontend_client",
        event_type="control_center.client_error",
        lifecycle_state="failed",
        status="failed",
        severity="error",
        observed_at=report.timestamp or utc_now(),
        safe_summary="Control Center client error recorded as a redacted summary.",
        error_code="CONTROL_CENTER_CLIENT_ERROR",
        error_summary=report.safe_error_message,
        stack_hash=report.stack_hash,
        redaction_summary={
            "status": "summary_only",
            "stack_trace_stored": False,
            "dom_snapshot_stored": False,
            "storage_snapshot_stored": False,
            "client_sensitive_material_stored": False,
        },
        metadata={
            "component": report.component,
            "surface_name": report.surface,
            "route_name": report.route_name or "unspecified",
            "runtime_category": report.runtime_category or "unknown",
        },
    )


def safe_summary_projection(event: SessionEvent) -> SessionEventSummary:
    return SessionEventSummary(
        schema_version=event.schema_version,
        event_id=event.event_id,
        session_id=event.session_id,
        run_id=event.run_id,
        trace_id=event.trace_id,
        span_id=event.span_id,
        parent_span_id=event.parent_span_id,
        correlation_id=event.correlation_id,
        service=event.service,
        surface=event.surface,
        event_type=event.event_type,
        lifecycle_state=event.lifecycle_state,
        status=event.status,
        severity=event.severity,
        observed_at=event.observed_at,
        started_at=event.started_at,
        completed_at=event.completed_at,
        duration_ms=event.duration_ms,
        safe_summary=event.safe_summary,
        reason_codes=list(event.reason_codes),
        error_code=event.error_code,
        error_summary=event.error_summary,
        stack_hash=event.stack_hash,
        prompt_ref=event.prompt_ref,
        prompt_hash=event.prompt_hash,
        prompt_template_id=event.prompt_template_id,
        input_refs=list(event.input_refs),
        output_refs=list(event.output_refs),
        evidence_refs=list(event.evidence_refs),
        receipt_refs=list(event.receipt_refs),
        redaction_summary=dict(event.redaction_summary),
        metadata=dict(event.metadata),
    )


def build_safe_ref(prefix: str, *parts: object) -> str:
    _validate_safe_label(prefix, max_chars=40)
    seed = "|".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def hash_sensitive_stack(value: str) -> str:
    return f"stack-sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def classify_duration(duration_ms: float | None, *, slow_ms: float = 1_000.0) -> str:
    if duration_ms is None:
        return "normal"
    if duration_ms >= slow_ms:
        return "slow"
    return "normal"


def _coerce_session_event(event: SessionEvent | dict[str, Any]) -> SessionEvent:
    try:
        if isinstance(event, SessionEvent):
            return SessionEvent.model_validate(event.model_dump())
        return SessionEvent.model_validate(event)
    except (ValidationError, ValueError) as exc:
        raise SessionLogValidationError("SESSION_LOG_EVENT_UNSAFE") from exc


def _validate_safe_identifier(value: str) -> None:
    _validate_safe_text(value, "identifier", max_chars=160, allow_slash=False)
    if not SAFE_ID_RE.match(value):
        raise ValueError("SESSION_LOG_IDENTIFIER_UNSAFE")


def _validate_safe_label(value: str, *, max_chars: int) -> None:
    _validate_safe_text(value, "label", max_chars=max_chars, allow_slash=False)
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.: @-]{0,159}$", value):
        raise ValueError("SESSION_LOG_LABEL_UNSAFE")


def _validate_safe_text(
    value: str,
    field_name: str,
    *,
    max_chars: int,
    allow_slash: bool = False,
) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} required")
    if len(value) > max_chars:
        raise ValueError(f"{field_name} too long")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{field_name} must be single line")
    if not allow_slash and ("/" in value or "\\" in value):
        raise ValueError(f"{field_name} contains path-like content")
    if LOCAL_PRIVATE_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains private local path")
    if scan_payload_for_secrets(value) or contains_obvious_secret(value):
        raise ValueError(f"{field_name} contains unsafe content")


def _validate_metadata_payload(value: Any, field_name: str) -> None:
    _validate_metadata_value(value, field_name, depth=0)


def _validate_metadata_value(value: Any, field_name: str, *, depth: int) -> None:
    if depth > 4:
        raise ValueError("SESSION_LOG_METADATA_DEPTH_DENIED")
    if isinstance(value, str):
        if len(value) > MAX_METADATA_TEXT_CHARS:
            raise ValueError("SESSION_LOG_METADATA_TEXT_TOO_LONG")
        if "\n" in value or "\r" in value:
            raise ValueError("SESSION_LOG_METADATA_MULTILINE_DENIED")
        if LOCAL_PRIVATE_PATH_RE.search(value):
            raise ValueError("SESSION_LOG_METADATA_PRIVATE_PATH_DENIED")
        if scan_payload_for_secrets(value) or contains_obvious_secret(value):
            raise ValueError("SESSION_LOG_METADATA_SECRET_DENIED")
        return
    if isinstance(value, bool) or isinstance(value, int) or isinstance(value, float) or value is None:
        return
    if isinstance(value, list):
        if len(value) > MAX_METADATA_LIST_ITEMS:
            raise ValueError("SESSION_LOG_METADATA_LIST_TOO_LONG")
        for item in value:
            _validate_metadata_value(item, field_name, depth=depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_METADATA_KEYS:
            raise ValueError("SESSION_LOG_METADATA_TOO_MANY_KEYS")
        for key, item in value.items():
            _validate_metadata_key(str(key), field_name)
            _validate_metadata_value(item, field_name, depth=depth + 1)
        return
    raise ValueError("SESSION_LOG_METADATA_TYPE_DENIED")


def _validate_metadata_key(key: str, field_name: str) -> None:
    if not key or len(key) > 80:
        raise ValueError("SESSION_LOG_METADATA_KEY_INVALID")
    normalized = key.lower().replace("-", "_")
    if any(marker in normalized for marker in UNSAFE_METADATA_KEY_MARKERS):
        raise ValueError(f"SESSION_LOG_{field_name.upper()}_KEY_UNSAFE")
    if scan_payload_for_secrets(key) or contains_obvious_secret(key):
        raise ValueError(f"SESSION_LOG_{field_name.upper()}_KEY_UNSAFE")


def load_session_event_lines(filepath: str | Path) -> Iterable[SessionEvent]:
    store = SessionLogStore(filepath=filepath)
    return list(store._events)
