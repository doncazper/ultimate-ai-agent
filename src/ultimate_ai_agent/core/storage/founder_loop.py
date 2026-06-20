from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.time import utc_now


FOUNDER_LOOP_SCHEMA_VERSION = "founder_loop_storage.v1"
FOUNDER_LOOP_STATE_DIR_ENV = "UAA_FOUNDER_LOOP_STATE_DIR"
DEFAULT_FOUNDER_LOOP_STATE_DIR = Path(".uaa") / "founder_loop"

UNSAFE_STORAGE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "environment dump",
    "environment_dump",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)
UNSAFE_STORAGE_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "hostname",
    "password",
    "private_key",
    "provider_payload",
    "raw_log",
    "raw_path",
    "raw_prompt",
    "raw_response",
    "secret",
    "serial",
    "token",
    "username",
)


class FounderLoopStorageError(Exception):
    """Base error for storage-backed Founder Loop state."""


class FounderLoopStorageDuplicateError(FounderLoopStorageError):
    """Raised when a duplicate idempotency key is denied."""


class JsonlLogKind(str, Enum):
    audit = "audit"
    transcript = "transcript"
    realtime = "realtime"
    receipt = "receipt"


class FounderLoopActionRecord(BaseModel):
    item_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    surface: str = Field(..., min_length=1, max_length=80)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="review_ready", min_length=1, max_length=80)
    side_effect_class: str = Field(default="validation_only", min_length=1, max_length=80)
    approval_required: bool = True
    blocked_state: str | None = Field(default=None, max_length=160)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopActionRecord":
        _validate_safe_ref(self.item_ref, "item_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "action_record")
        return self


class FounderLoopPlanRecord(BaseModel):
    plan_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    status: str = Field(default="partial_backend_not_product_ready", min_length=1, max_length=80)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    next_step_summary: str = Field(..., min_length=1, max_length=500)
    evidence_refs: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopPlanRecord":
        _validate_safe_ref(self.plan_ref, "plan_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "plan_record")
        return self


class FounderLoopMemoryReviewRecord(BaseModel):
    review_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    status: str = Field(default="review_needed", min_length=1, max_length=80)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopMemoryReviewRecord":
        _validate_safe_ref(self.review_ref, "review_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "memory_review_record")
        return self


class FounderLoopBriefingRecord(BaseModel):
    briefing_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    status: str = Field(default="active", min_length=1, max_length=80)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopBriefingRecord":
        _validate_safe_ref(self.briefing_ref, "briefing_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "briefing_record")
        return self


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_STORAGE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe Founder Loop storage text")


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_safe_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(fragment in normalized_key for fragment in UNSAFE_STORAGE_KEY_FRAGMENTS):
                raise ValueError(f"{field_name} contains unsafe Founder Loop storage key")
            _validate_safe_payload(str(key), field_name)
            _validate_safe_payload(item, field_name)


def _json_dumps(value: Any) -> str:
    _validate_safe_payload(value, "json_payload")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utc_iso() -> str:
    return utc_now().isoformat()


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    if "evidence_refs_json" in payload:
        payload["evidence_refs"] = json.loads(payload.pop("evidence_refs_json") or "[]")
    return payload


class FounderLoopRepository:
    """Stdlib SQLite plus JSONL repository for the first Founder Loop state."""

    def __init__(self, state_dir: Path, *, seed_defaults: bool = True) -> None:
        self.state_dir = state_dir
        self.db_path = self.state_dir / "founder_loop.sqlite3"
        self.logs_dir = self.state_dir / "logs"
        self.seed_defaults = seed_defaults
        self._ensure_storage()

    @classmethod
    def from_env(cls, *, seed_defaults: bool = True) -> "FounderLoopRepository":
        configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_FOUNDER_LOOP_STATE_DIR
        return cls(state_dir=state_dir, seed_defaults=seed_defaults)

    def storage_status(self) -> dict[str, Any]:
        counts = {
            "action_inbox": self._count("action_inbox"),
            "briefing_items": self._count("briefing_items"),
            "plan_summaries": self._count("plan_summaries"),
            "memory_review_queue": self._count("memory_review_queue"),
            "idempotency_keys": self._count("idempotency_keys"),
            "route_state_snapshots": self._count("route_state_snapshots"),
            "evidence_refs": self._count("evidence_refs"),
        }
        log_refs = {
            kind.value: f"founder-loop-log:{kind.value}"
            for kind in JsonlLogKind
        }
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "migration_version": self._schema_version(),
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "sqlite_state_ref": "founder-loop-sqlite:local-state",
            "jsonl_log_refs": log_refs,
            "counts": counts,
            "safe_refs_only": True,
            "raw_content_stored": False,
            "postgres_sync_required": False,
            "postgres_sync_status": "adapter_boundary_only",
            "backup_manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "updated_at": _utc_iso(),
        }

    def today_summary(self, *, limit: int = 6) -> dict[str, Any]:
        actions = self.list_action_inbox(limit=limit)
        plans = self.list_plan_summaries(limit=3)
        memory_items = self.list_memory_review_queue(limit=3)
        briefing_items = self.list_briefing_items(limit=3)
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_partial_loop",
            "surface": "Today",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "approval_required_before_mutation": True,
            "sections": {
                "action_inbox_count": len(actions),
                "plan_count": len(plans),
                "memory_review_count": len(memory_items),
                "briefing_count": len(briefing_items),
            },
            "actions": actions,
            "plans": plans,
            "memory_review_queue": memory_items,
            "briefing_items": briefing_items,
            "evidence_refs": ["evidence-ref:founder-loop:today-summary"],
            "blocked_states": [
                "no_action_execution_route",
                "no_connector_write_route",
                "no_runtime_model_call_route",
            ],
        }

    def actions_inbox(self, *, limit: int = 50) -> dict[str, Any]:
        items = self.list_action_inbox(limit=limit)
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_review_queue",
            "surface": "Actions",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "items": items,
            "approval_required_before_mutation": True,
            "mutating_controls_enabled": False,
            "disabled_state_label": "Exact backend approval contract required",
            "evidence_refs": ["evidence-ref:founder-loop:action-inbox"],
        }

    def morning_briefing(self, *, limit: int = 10) -> dict[str, Any]:
        items = self.list_briefing_items(limit=limit)
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_briefing_skeleton",
            "surface": "Morning Briefing",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "items": items,
            "evidence_refs": ["evidence-ref:founder-loop:morning-briefing"],
            "blocked_states": [
                "no_email_read_authority",
                "no_calendar_read_authority",
                "no_notification_delivery",
            ],
        }

    def list_action_inbox(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   side_effect_class, approval_required, blocked_state,
                   evidence_refs_json, created_at, updated_at
            FROM action_inbox
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_plan_summaries(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT plan_ref, title, status, safe_summary, next_step_summary,
                   evidence_refs_json, updated_at
            FROM plan_summaries
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_memory_review_queue(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT review_ref, title, safe_summary, status, evidence_refs_json, created_at
            FROM memory_review_queue
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_briefing_items(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT briefing_ref, title, safe_summary, status, evidence_refs_json, created_at
            FROM briefing_items
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def upsert_action(self, record: FounderLoopActionRecord) -> None:
        self._execute(
            """
            INSERT INTO action_inbox (
                item_ref, title, safe_summary, surface, priority, status,
                side_effect_class, approval_required, blocked_state,
                evidence_refs_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                surface = excluded.surface,
                priority = excluded.priority,
                status = excluded.status,
                side_effect_class = excluded.side_effect_class,
                approval_required = excluded.approval_required,
                blocked_state = excluded.blocked_state,
                evidence_refs_json = excluded.evidence_refs_json,
                updated_at = excluded.updated_at
            """,
            (
                record.item_ref,
                record.title,
                record.safe_summary,
                record.surface,
                record.priority,
                record.status,
                record.side_effect_class,
                int(record.approval_required),
                record.blocked_state,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )

    def upsert_plan(self, record: FounderLoopPlanRecord) -> None:
        self._execute(
            """
            INSERT INTO plan_summaries (
                plan_ref, title, status, safe_summary, next_step_summary,
                evidence_refs_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_ref) DO UPDATE SET
                title = excluded.title,
                status = excluded.status,
                safe_summary = excluded.safe_summary,
                next_step_summary = excluded.next_step_summary,
                evidence_refs_json = excluded.evidence_refs_json,
                updated_at = excluded.updated_at
            """,
            (
                record.plan_ref,
                record.title,
                record.status,
                record.safe_summary,
                record.next_step_summary,
                _json_dumps(record.evidence_refs),
                record.updated_at.isoformat(),
            ),
        )

    def upsert_memory_review(self, record: FounderLoopMemoryReviewRecord) -> None:
        self._execute(
            """
            INSERT INTO memory_review_queue (
                review_ref, title, safe_summary, status, evidence_refs_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                status = excluded.status,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.review_ref,
                record.title,
                record.safe_summary,
                record.status,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def upsert_briefing_item(self, record: FounderLoopBriefingRecord) -> None:
        self._execute(
            """
            INSERT INTO briefing_items (
                briefing_ref, title, safe_summary, status, evidence_refs_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(briefing_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                status = excluded.status,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.briefing_ref,
                record.title,
                record.safe_summary,
                record.status,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def record_idempotency_key(self, *, key_ref: str, scope_ref: str, receipt_ref: str) -> None:
        _validate_safe_ref(key_ref, "key_ref")
        _validate_safe_ref(scope_ref, "scope_ref")
        _validate_safe_ref(receipt_ref, "receipt_ref")
        try:
            self._execute(
                """
                INSERT INTO idempotency_keys (key_ref, scope_ref, receipt_ref, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key_ref, scope_ref, receipt_ref, _utc_iso()),
            )
        except sqlite3.IntegrityError as exc:
            raise FounderLoopStorageDuplicateError("FOUNDER_LOOP_IDEMPOTENCY_DUPLICATE") from exc

    def append_log(self, kind: JsonlLogKind, payload: dict[str, Any]) -> dict[str, str]:
        _validate_safe_payload(payload, f"{kind.value}_log")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        path = self.logs_dir / f"{kind.value}.jsonl"
        record = {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "kind": kind.value,
            "event_ref": payload.get("event_ref", f"founder-loop-log:{kind.value}"),
            "safe_summary": payload.get("safe_summary", "Founder Loop redacted event recorded."),
            "evidence_refs": payload.get("evidence_refs", []),
            "created_at": _utc_iso(),
        }
        _validate_safe_payload(record, f"{kind.value}_log_record")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_json_dumps(record) + "\n")
        return {
            "log_ref": f"founder-loop-log:{kind.value}",
            "event_ref": str(record["event_ref"]),
        }

    def backup_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "required_artifact_refs": [
                "founder-loop-sqlite:local-state",
                "founder-loop-log:audit",
                "founder-loop-log:transcript",
                "founder-loop-log:realtime",
                "founder-loop-log:receipt",
            ],
            "raw_paths_included": False,
            "raw_logs_included": False,
            "safe_refs_only": True,
        }

    def _ensure_storage(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS storage_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_inbox (
                    item_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    surface TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL,
                    approval_required INTEGER NOT NULL,
                    blocked_state TEXT,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plan_summaries (
                    plan_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    next_step_summary TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_queue (
                    review_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS briefing_items (
                    briefing_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key_ref TEXT PRIMARY KEY,
                    scope_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS route_state_snapshots (
                    snapshot_ref TEXT PRIMARY KEY,
                    route_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_refs (
                    evidence_ref TEXT PRIMARY KEY,
                    safe_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                INSERT INTO storage_metadata (key, value, updated_at)
                VALUES ('schema_version', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (FOUNDER_LOOP_SCHEMA_VERSION, _utc_iso()),
            )
        if self.seed_defaults:
            self._seed_defaults_if_empty()

    def _seed_defaults_if_empty(self) -> None:
        if self._count("action_inbox") == 0:
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:setup-assistant-hardening",
                    title="Setup Assistant hardening review",
                    safe_summary=(
                        "Dry-run setup envelopes are available for review only; installer and "
                        "background-service authority remain blocked."
                    ),
                    surface="Actions",
                    priority="high",
                    status="review_ready",
                    side_effect_class="validation_only",
                    approval_required=True,
                    blocked_state="Mutation requires exact approval, idempotency, rollback, and receipt refs.",
                    evidence_refs=["evidence-ref:founder-loop:setup-assistant"],
                )
            )
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:morning-briefing-skeleton",
                    title="Morning Briefing skeleton review",
                    safe_summary=(
                        "Briefing items are storage-backed summaries only; email and calendar reads "
                        "remain future contracts."
                    ),
                    surface="Today",
                    priority="medium",
                    status="review_ready",
                    side_effect_class="local_dev_workspace_only",
                    approval_required=False,
                    blocked_state="Connector reads and notification delivery are not scoped.",
                    evidence_refs=["evidence-ref:founder-loop:briefing"],
                )
            )
        if self._count("plan_summaries") == 0:
            self.upsert_plan(
                FounderLoopPlanRecord(
                    plan_ref="plan-summary:founder-loop-v1",
                    title="Founder Loop v1 product spine",
                    safe_summary=(
                        "Today, Actions, Plans, Memory, Evidence, and Settings are the active "
                        "single-user operator loop."
                    ),
                    next_step_summary=(
                        "Keep the loop storage-backed and review-gated before adding broader "
                        "runtime surfaces."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:product-spine"],
                )
            )
        if self._count("memory_review_queue") == 0:
            self.upsert_memory_review(
                FounderLoopMemoryReviewRecord(
                    review_ref="memory-review:founder-loop-preferences",
                    title="Founder Loop memory review",
                    safe_summary=(
                        "Memory remains a review queue with safe summaries; recall is not treated "
                        "as truth or execution authority."
                    ),
                    status="review_needed",
                    evidence_refs=["evidence-ref:founder-loop:memory"],
                )
            )
        if self._count("briefing_items") == 0:
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:api-boundary-modularization",
                    title="API boundary modularization",
                    safe_summary=(
                        "New Founder Loop summaries use router and repository seams while the "
                        "legacy FastAPI module remains a compatibility boundary."
                    ),
                    status="active",
                    evidence_refs=["evidence-ref:founder-loop:api-boundary"],
                )
            )
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:storage-state-first-loop",
                    title="Storage-backed first loop",
                    safe_summary=(
                        "SQLite stores indexed loop state and JSONL logs are reserved for "
                        "redacted append-only receipts, audits, transcripts, and realtime events."
                    ),
                    status="active",
                    evidence_refs=["evidence-ref:founder-loop:storage"],
                )
            )
        if self._count("evidence_refs") == 0:
            self._execute(
                """
                INSERT INTO evidence_refs (evidence_ref, safe_summary, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    "evidence-ref:founder-loop:seed",
                    "Initial storage-backed Founder Loop safe refs.",
                    _utc_iso(),
                ),
            )

    def _schema_version(self) -> str:
        rows = self._fetch_all(
            "SELECT value FROM storage_metadata WHERE key = 'schema_version' LIMIT 1",
            (),
        )
        return str(rows[0]["value"]) if rows else FOUNDER_LOOP_SCHEMA_VERSION

    def _count(self, table: str) -> int:
        allowed = {
            "action_inbox",
            "briefing_items",
            "plan_summaries",
            "memory_review_queue",
            "idempotency_keys",
            "route_state_snapshots",
            "evidence_refs",
        }
        if table not in allowed:
            raise FounderLoopStorageError("FOUNDER_LOOP_TABLE_REF_DENIED")
        rows = self._fetch_all(f"SELECT COUNT(*) AS count FROM {table}", ())
        return int(rows[0]["count"])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _bounded_limit(limit: int) -> int:
        return max(1, min(int(limit), 100))
