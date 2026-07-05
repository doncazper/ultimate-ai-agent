from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from collections import Counter
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.time import utc_now


DEFAULT_DEBUG_PREVIEW_CHARS = 512
DEFAULT_EXTREME_DEBUG_PREVIEW_CHARS = 2048
MAX_EXTREME_DEBUG_PREVIEW_CHARS = 4096
EXTREME_LOGGING_ENABLED_ENV = "UAA_EXTREME_LOGGING_ENABLED"
EXTREME_LOG_ROOT_ENV = "UAA_EXTREME_LOG_ROOT"
EXTREME_LOG_PREVIEW_CHARS_ENV = "UAA_EXTREME_LOG_PREVIEW_CHARS"
DEFAULT_EXTREME_LOG_RELATIVE_PATH = Path("observability") / "extreme_debug.jsonl"

PEM_BLOCK_RE = re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.DOTALL)
BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|client[_-]?secret|auth[_-]?token|authorization|cookie|password|secret|token)"
    r"\s*[:=]\s*(['\"]?)[^\s,'\"}]+"
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
LOCAL_PATH_RE = re.compile(r"(?<!\w)(/Users/[^\s]+|/home/[^\s]+|/var/[^\s]+|/etc/[^\s]+|[A-Za-z]:\\[^\s]+)")

RAW_FIELD_MARKERS = {
    "raw_prompt",
    "raw_prompt_body",
    "raw_terminal",
    "raw_terminal_output",
    "raw_provider_payload",
    "raw_response",
    "raw_body",
    "raw_content",
}


class DebugLogCategory(str, Enum):
    gateway = "gateway"
    user = "user"
    prompt = "prompt"
    error = "error"
    session = "session"
    terminal = "terminal"
    system = "system"
    security = "security"


class DebugLogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class DebugLogRedactionStatus(str, Enum):
    reference_only = "reference_only"
    bounded_preview = "bounded_preview"
    redacted_preview = "redacted_preview"


class RedactedDebugText(BaseModel):
    preview: str
    sha256: str
    original_length: int = Field(..., ge=0)
    preview_length: int = Field(..., ge=0)
    truncated: bool = False
    redactions_applied: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class DebugLogRecord(BaseModel):
    log_id: str = Field(default_factory=lambda: f"log_{uuid.uuid4().hex}", min_length=1)
    category: DebugLogCategory
    level: DebugLogLevel = DebugLogLevel.info
    created_at: datetime = Field(default_factory=utc_now)
    session_id: str = Field(..., min_length=1)
    run_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    correlation_id: str | None = None
    source: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    safe_preview: str | None = None
    content_sha256: str | None = None
    original_content_length: int | None = Field(default=None, ge=0)
    truncated: bool = False
    raw_content_stored: bool = False
    redaction_status: DebugLogRedactionStatus = DebugLogRedactionStatus.reference_only
    redactions_applied: list[str] = Field(default_factory=list)
    status: str = Field(default="recorded", min_length=1)
    outcome: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    route: str | None = None
    method: str | None = None
    status_code: int | None = Field(default=None, ge=100, le=599)
    user_ref: str | None = None
    prompt_ref: str | None = None
    terminal_ref: str | None = None
    command_ref: str | None = None
    exit_code: int | None = None
    error_type: str | None = None
    error_code: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("source", "message", "safe_preview", mode="after")
    @classmethod
    def validate_safe_text(cls, value: str | None) -> str | None:
        if value is not None and scan_payload_for_secrets(value):
            raise ValueError("DEBUG_LOG_UNREDACTED_CREDENTIAL_DENIED")
        return value

    @model_validator(mode="after")
    def validate_debug_log_record(self) -> Any:
        if self.raw_content_stored:
            raise ValueError("DEBUG_LOG_RAW_CONTENT_DENIED")
        _assert_no_raw_field_markers(self.metadata)
        if scan_payload_for_secrets(self.metadata):
            raise ValueError("DEBUG_LOG_UNREDACTED_CREDENTIAL_DENIED")
        if self.safe_preview and self.redaction_status == DebugLogRedactionStatus.reference_only:
            raise ValueError("DEBUG_LOG_PREVIEW_REQUIRES_REDACTION_STATUS")
        if self.content_sha256 and len(self.content_sha256) != 64:
            raise ValueError("DEBUG_LOG_CONTENT_SHA256_INVALID")
        return self


class DebugLogSummary(BaseModel):
    total_records: int = Field(..., ge=0)
    category_counts: dict[str, int] = Field(default_factory=dict)
    level_counts: dict[str, int] = Field(default_factory=dict)
    session_ids: list[str] = Field(default_factory=list)
    error_count: int = Field(default=0, ge=0)
    latest_log_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ExtremeDebugLoggingSettings(BaseModel):
    schema_version: str = "uaa.extreme_debug_logging_settings.v1"
    enabled: bool
    mode: str
    env_flag_ref: str = "env-ref:UAA_EXTREME_LOGGING_ENABLED"
    root_env_ref: str = "env-ref:UAA_EXTREME_LOG_ROOT"
    preview_env_ref: str = "env-ref:UAA_EXTREME_LOG_PREVIEW_CHARS"
    local_log_ref: str = "debug-log-ref:local-extreme-jsonl"
    default_disabled: bool = True
    bounded_preview_chars: int = Field(..., ge=32, le=MAX_EXTREME_DEBUG_PREVIEW_CHARS)
    max_preview_chars_cap: int = MAX_EXTREME_DEBUG_PREVIEW_CHARS
    redacted_only: bool = True
    safe_refs_only: bool = True
    raw_content_stored: bool = False
    raw_prompt_stored: bool = False
    raw_response_stored: bool = False
    raw_provider_payload_stored: bool = False
    raw_terminal_output_stored: bool = False
    raw_local_path_stored: bool = False
    external_export_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_extreme_settings(self) -> "ExtremeDebugLoggingSettings":
        if self.mode not in {"disabled", "enabled"}:
            raise ValueError("EXTREME_DEBUG_LOGGING_MODE_INVALID")
        if self.enabled != (self.mode == "enabled"):
            raise ValueError("EXTREME_DEBUG_LOGGING_MODE_MISMATCH")
        if not self.default_disabled:
            raise ValueError("EXTREME_DEBUG_LOGGING_DEFAULT_MUST_BE_DISABLED")
        if not self.redacted_only or not self.safe_refs_only:
            raise ValueError("EXTREME_DEBUG_LOGGING_REDACTION_REQUIRED")
        if any(
            [
                self.raw_content_stored,
                self.raw_prompt_stored,
                self.raw_response_stored,
                self.raw_provider_payload_stored,
                self.raw_terminal_output_stored,
                self.raw_local_path_stored,
                self.external_export_enabled,
                self.production_authority_enabled,
            ]
        ):
            raise ValueError("EXTREME_DEBUG_LOGGING_UNSAFE_AUTHORITY_DENIED")
        return self


class DebugLogStore:
    """Append-only local debug log store with redacted, bounded JSONL records."""

    def __init__(self, filepath: str | Path | None = None, *, max_preview_chars: int = DEFAULT_DEBUG_PREVIEW_CHARS) -> None:
        if max_preview_chars < 32:
            raise ValueError("DEBUG_LOG_PREVIEW_TOO_SMALL")
        self.filepath = Path(filepath) if filepath else None
        self.max_preview_chars = max_preview_chars
        self._records: list[DebugLogRecord] = []
        self._log_ids: set[str] = set()
        if self.filepath:
            self._load_from_file()

    def _load_from_file(self) -> None:
        if not self.filepath or not self.filepath.exists():
            return
        with self.filepath.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                record = DebugLogRecord.model_validate(json.loads(stripped))
                self._append_in_memory(record)

    def append(self, record: DebugLogRecord) -> DebugLogRecord:
        self._append_in_memory(record)
        if self.filepath:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with self.filepath.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json() + "\n")
        return record

    def _append_in_memory(self, record: DebugLogRecord) -> None:
        if record.log_id in self._log_ids:
            raise ValueError(f"Duplicate debug log_id detected: {record.log_id}")
        self._records.append(record)
        self._log_ids.add(record.log_id)

    def list_records(
        self,
        *,
        session_id: str | None = None,
        run_id: str | None = None,
        category: DebugLogCategory | str | None = None,
        level: DebugLogLevel | str | None = None,
    ) -> list[DebugLogRecord]:
        category_value = category.value if isinstance(category, DebugLogCategory) else category
        level_value = level.value if isinstance(level, DebugLogLevel) else level
        records = self._records
        if session_id is not None:
            records = [record for record in records if record.session_id == session_id]
        if run_id is not None:
            records = [record for record in records if record.run_id == run_id]
        if category_value is not None:
            records = [record for record in records if record.category == category_value]
        if level_value is not None:
            records = [record for record in records if record.level == level_value]
        return list(records)

    def latest(self, limit: int = 50) -> list[DebugLogRecord]:
        if limit < 1:
            raise ValueError("DEBUG_LOG_LATEST_LIMIT_INVALID")
        return list(self._records[-limit:])

    def summary(self, *, session_id: str | None = None) -> DebugLogSummary:
        records = self.list_records(session_id=session_id) if session_id else list(self._records)
        category_counts = Counter(str(record.category) for record in records)
        level_counts = Counter(str(record.level) for record in records)
        session_ids = sorted({record.session_id for record in records})
        return DebugLogSummary(
            total_records=len(records),
            category_counts=dict(category_counts),
            level_counts=dict(level_counts),
            session_ids=session_ids,
            error_count=sum(
                1
                for record in records
                if record.category == DebugLogCategory.error.value or record.level in {DebugLogLevel.error.value, DebugLogLevel.critical.value}
            ),
            latest_log_ids=[record.log_id for record in records[-10:]],
        )

    def log_gateway(
        self,
        *,
        session_id: str,
        source: str,
        method: str,
        route: str,
        status_code: int,
        latency_ms: int | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        return self.append(
            DebugLogRecord(
                category=DebugLogCategory.gateway,
                level=DebugLogLevel.info if status_code < 500 else DebugLogLevel.error,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                source=source,
                message=message or f"{method.upper()} {route} completed with status {status_code}",
                method=method.upper(),
                route=route,
                status_code=status_code,
                latency_ms=latency_ms,
                status="completed",
                outcome=str(status_code),
                metadata=metadata or {},
            )
        )

    def log_user(
        self,
        *,
        session_id: str,
        source: str,
        user_ref: str,
        action_summary: str,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        redacted = redact_debug_text(action_summary, max_chars=self.max_preview_chars)
        return self.append(
            _record_from_redacted_text(
                category=DebugLogCategory.user,
                level=DebugLogLevel.info,
                session_id=session_id,
                run_id=run_id,
                source=source,
                message="User action recorded as a redacted bounded preview.",
                redacted=redacted,
                user_ref=user_ref,
                metadata=metadata,
            )
        )

    def log_prompt(
        self,
        *,
        session_id: str,
        source: str,
        prompt_ref: str,
        prompt_text: str | None = None,
        prompt_summary: str | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        if prompt_text is None:
            return self.append(
                DebugLogRecord(
                    category=DebugLogCategory.prompt,
                    level=DebugLogLevel.info,
                    session_id=session_id,
                    run_id=run_id,
                    trace_id=trace_id,
                    source=source,
                    message=prompt_summary or "Prompt referenced without raw prompt storage.",
                    prompt_ref=prompt_ref,
                    redaction_status=DebugLogRedactionStatus.reference_only,
                    metadata=metadata or {},
                )
            )
        redacted = redact_debug_text(prompt_text, max_chars=self.max_preview_chars)
        return self.append(
            _record_from_redacted_text(
                category=DebugLogCategory.prompt,
                level=DebugLogLevel.info,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                source=source,
                message=prompt_summary or "Prompt captured as a redacted bounded preview.",
                redacted=redacted,
                prompt_ref=prompt_ref,
                metadata=metadata,
            )
        )

    def log_error(
        self,
        *,
        session_id: str,
        source: str,
        safe_message: str,
        error_type: str | None = None,
        error_code: str | None = None,
        details_text: str | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        redacted = redact_debug_text(details_text or safe_message, max_chars=self.max_preview_chars)
        return self.append(
            _record_from_redacted_text(
                category=DebugLogCategory.error,
                level=DebugLogLevel.error,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                source=source,
                message=safe_message,
                redacted=redacted,
                status="failed",
                error_type=error_type,
                error_code=error_code,
                metadata=metadata,
            )
        )

    def log_session(
        self,
        *,
        session_id: str,
        source: str,
        session_status: str,
        message: str | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        return self.append(
            DebugLogRecord(
                category=DebugLogCategory.session,
                level=DebugLogLevel.info,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                source=source,
                message=message or f"Session state changed to {session_status}",
                status=session_status,
                outcome=session_status,
                metadata=metadata or {},
            )
        )

    def log_terminal(
        self,
        *,
        session_id: str,
        source: str,
        command_ref: str,
        terminal_ref: str | None = None,
        output_text: str | None = None,
        exit_code: int | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DebugLogRecord:
        if output_text is None:
            return self.append(
                DebugLogRecord(
                    category=DebugLogCategory.terminal,
                    level=DebugLogLevel.info if exit_code in {None, 0} else DebugLogLevel.error,
                    session_id=session_id,
                    run_id=run_id,
                    trace_id=trace_id,
                    source=source,
                    message="Terminal command referenced without raw output storage.",
                    command_ref=command_ref,
                    terminal_ref=terminal_ref,
                    exit_code=exit_code,
                    latency_ms=latency_ms,
                    status="completed" if exit_code in {None, 0} else "failed",
                    outcome=str(exit_code) if exit_code is not None else None,
                    metadata=metadata or {},
                )
            )
        redacted = redact_debug_text(output_text, max_chars=self.max_preview_chars)
        return self.append(
            _record_from_redacted_text(
                category=DebugLogCategory.terminal,
                level=DebugLogLevel.info if exit_code in {None, 0} else DebugLogLevel.error,
                session_id=session_id,
                run_id=run_id,
                trace_id=trace_id,
                source=source,
                message="Terminal output captured as a redacted bounded preview.",
                redacted=redacted,
                terminal_ref=terminal_ref,
                command_ref=command_ref,
                exit_code=exit_code,
                latency_ms=latency_ms,
                status="completed" if exit_code in {None, 0} else "failed",
                outcome=str(exit_code) if exit_code is not None else None,
                metadata=metadata,
            )
        )


def extreme_logging_enabled() -> bool:
    return os.environ.get(EXTREME_LOGGING_ENABLED_ENV, "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
        "extreme",
    }


def extreme_debug_log_root() -> Path:
    return Path(os.environ.get(EXTREME_LOG_ROOT_ENV, ".uaa"))


def extreme_debug_log_path(root: str | Path | None = None) -> Path:
    base = Path(root) if root is not None else extreme_debug_log_root()
    return base / DEFAULT_EXTREME_LOG_RELATIVE_PATH


def extreme_debug_preview_chars() -> int:
    raw_value = os.environ.get(EXTREME_LOG_PREVIEW_CHARS_ENV)
    if raw_value is None:
        return DEFAULT_EXTREME_DEBUG_PREVIEW_CHARS
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_EXTREME_DEBUG_PREVIEW_CHARS
    return max(32, min(parsed, MAX_EXTREME_DEBUG_PREVIEW_CHARS))


def build_extreme_debug_logging_settings() -> ExtremeDebugLoggingSettings:
    enabled = extreme_logging_enabled()
    return ExtremeDebugLoggingSettings(
        enabled=enabled,
        mode="enabled" if enabled else "disabled",
        bounded_preview_chars=extreme_debug_preview_chars(),
    )


def get_default_extreme_debug_log_store() -> DebugLogStore:
    return _cached_extreme_debug_log_store(
        str(extreme_debug_log_path()),
        extreme_debug_preview_chars(),
    )


def clear_extreme_debug_log_store_cache() -> None:
    _cached_extreme_debug_log_store.cache_clear()


@lru_cache(maxsize=8)
def _cached_extreme_debug_log_store(filepath: str, max_preview_chars: int) -> DebugLogStore:
    return DebugLogStore(filepath, max_preview_chars=max_preview_chars)


def record_extreme_gateway_debug_log(
    *,
    session_id: str,
    source: str,
    method: str,
    route: str,
    status_code: int,
    latency_ms: int | None = None,
    run_id: str | None = None,
    trace_id: str | None = None,
    message: str | None = None,
    metadata: dict[str, Any] | None = None,
    store: DebugLogStore | None = None,
    fail_closed: bool = False,
) -> DebugLogRecord | None:
    if not extreme_logging_enabled():
        return None
    active_store = store or get_default_extreme_debug_log_store()
    safe_route = _safe_route_pattern(route)
    safe_metadata = {
        "diagnostic_profile": "extreme",
        "redacted_only": True,
        "http_content_omitted": True,
        "query_values_omitted": True,
        "header_values_omitted": True,
    }
    if metadata:
        safe_metadata.update(metadata)
    try:
        return active_store.log_gateway(
            session_id=session_id,
            source=source,
            method=method,
            route=safe_route,
            status_code=status_code,
            latency_ms=latency_ms,
            run_id=run_id,
            trace_id=trace_id,
            message=message or "Extreme diagnostic gateway metadata recorded safely.",
            metadata=safe_metadata,
        )
    except (ValueError, OSError):
        if fail_closed:
            raise
    return None


def _safe_route_pattern(route: str) -> str:
    candidate = str(route or "").split("?", 1)[0].split("#", 1)[0].strip()
    if (
        not candidate
        or scan_payload_for_secrets(candidate)
        or LOCAL_PATH_RE.search(candidate)
        or PEM_BLOCK_RE.search(candidate)
    ):
        return "redacted_route"
    if len(candidate) > 160:
        return candidate[:146] + "...[truncated]"
    return candidate


def redact_debug_text(value: str, *, max_chars: int = DEFAULT_DEBUG_PREVIEW_CHARS) -> RedactedDebugText:
    if max_chars < 32:
        raise ValueError("DEBUG_LOG_PREVIEW_TOO_SMALL")
    original = value or ""
    redacted = original
    applied: list[str] = []
    replacements = [
        ("pem_block", PEM_BLOCK_RE, "[REDACTED_PEM_BLOCK]"),
        ("bearer_value", BEARER_RE, "Bearer [REDACTED_CREDENTIAL]"),
        ("credential_assignment", CREDENTIAL_ASSIGNMENT_RE, lambda match: f"{match.group(1)}=[REDACTED_CREDENTIAL]"),
        ("email", EMAIL_RE, "[REDACTED_EMAIL]"),
        ("local_path", LOCAL_PATH_RE, "[REDACTED_PATH]"),
    ]
    for name, pattern, replacement in replacements:
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            applied.append(name)
    truncated = len(redacted) > max_chars
    if truncated:
        suffix = "...[truncated]"
        redacted = redacted[: max_chars - len(suffix)] + suffix
    return RedactedDebugText(
        preview=redacted,
        sha256=hashlib.sha256(original.encode("utf-8")).hexdigest(),
        original_length=len(original),
        preview_length=len(redacted),
        truncated=truncated,
        redactions_applied=applied,
    )


def _record_from_redacted_text(
    *,
    category: DebugLogCategory,
    level: DebugLogLevel,
    session_id: str,
    source: str,
    message: str,
    redacted: RedactedDebugText,
    run_id: str | None = None,
    trace_id: str | None = None,
    status: str = "recorded",
    outcome: str | None = None,
    user_ref: str | None = None,
    prompt_ref: str | None = None,
    terminal_ref: str | None = None,
    command_ref: str | None = None,
    exit_code: int | None = None,
    error_type: str | None = None,
    error_code: str | None = None,
    latency_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> DebugLogRecord:
    return DebugLogRecord(
        category=category,
        level=level,
        session_id=session_id,
        run_id=run_id,
        trace_id=trace_id,
        source=source,
        message=message,
        safe_preview=redacted.preview,
        content_sha256=redacted.sha256,
        original_content_length=redacted.original_length,
        truncated=redacted.truncated,
        raw_content_stored=False,
        redaction_status=(
            DebugLogRedactionStatus.redacted_preview
            if redacted.redactions_applied
            else DebugLogRedactionStatus.bounded_preview
        ),
        redactions_applied=redacted.redactions_applied,
        status=status,
        outcome=outcome,
        user_ref=user_ref,
        prompt_ref=prompt_ref,
        terminal_ref=terminal_ref,
        command_ref=command_ref,
        exit_code=exit_code,
        error_type=error_type,
        error_code=error_code,
        latency_ms=latency_ms,
        metadata=metadata or {},
    )


def _assert_no_raw_field_markers(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in RAW_FIELD_MARKERS:
                raise ValueError("DEBUG_LOG_RAW_FIELD_DENIED")
            _assert_no_raw_field_markers(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_raw_field_markers(item)
