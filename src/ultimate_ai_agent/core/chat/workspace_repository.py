from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Literal

from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.storage.founder_loop import (
    DEFAULT_FOUNDER_LOOP_STATE_DIR,
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
    JsonlLogKind,
)
from ultimate_ai_agent.core.time import utc_now

from .workspace import (
    CHAT_WORKSPACE_MAX_REVISION,
    CHAT_WORKSPACE_MAX_THREADS,
    ChatDraftCheckpointRequest,
    ChatThreadLifecycleRequest,
    ChatThreadMutationReceipt,
    ChatThreadReadModel,
    build_chat_workspace_read_model,
    chat_workspace_mutation_ref,
    chat_workspace_payload_fingerprint_ref,
    validate_chat_thread_ref,
)


class ChatWorkspaceRepository:
    """Content-free Chat state isolated from the long-lived Founder Loop store."""

    def __init__(
        self,
        state_dir: Path,
        *,
        ensure_storage: bool = True,
        read_only: bool = False,
    ) -> None:
        self._founder_loop = FounderLoopRepository(
            state_dir,
            seed_defaults=False,
            ensure_storage=ensure_storage,
            read_only=read_only,
        )
        self.state_dir = state_dir
        self.db_path = self._founder_loop.db_path
        self.read_only = read_only
        if ensure_storage:
            self._ensure_storage()

    @classmethod
    def from_env(
        cls,
        *,
        ensure_storage: bool = True,
        read_only: bool = False,
    ) -> "ChatWorkspaceRepository":
        configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_FOUNDER_LOOP_STATE_DIR
        return cls(
            state_dir,
            ensure_storage=ensure_storage,
            read_only=read_only,
        )

    def workspace(self) -> dict[str, Any]:
        rows = self._fetch_all(
            """
            SELECT thread_ref, display_name, state, revision, draft_present,
                   draft_character_count, draft_fingerprint_ref, created_at, updated_at
            FROM chat_thread_states
            ORDER BY CASE state WHEN 'active' THEN 0 ELSE 1 END,
                     updated_at DESC, thread_ref ASC
            """,
            (),
        )
        return build_chat_workspace_read_model(
            [self._thread_read_model(row) for row in rows]
        ).model_dump(mode="json")

    def record_draft_checkpoint(
        self,
        *,
        thread_ref: str,
        request: ChatDraftCheckpointRequest,
        idempotency_key_ref: str,
        approval_refs: dict[str, str],
    ) -> dict[str, Any]:
        validate_chat_thread_ref(thread_ref)
        validate_execution_ref(idempotency_key_ref, "idempotency_key_ref")
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        now = utc_now().isoformat()
        replayed_receipt: dict[str, Any] | None = None
        receipt: ChatThreadMutationReceipt | None = None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            replay = self._replay_row(conn, idempotency_key_ref)
            if replay is not None:
                replayed_receipt = self._validated_replay(
                    replay,
                    expected_thread_ref=thread_ref,
                    expected_payload_fingerprint_ref=payload_fingerprint_ref,
                    expected_idempotency_key_ref=idempotency_key_ref,
                    expected_mutation_kind="draft_checkpoint",
                    expected_lifecycle_action=None,
                    expected_revision=request.expected_revision + 1,
                )
                evidence_event_ref = str(replayed_receipt["receipt_ref"])
            else:
                row = self._thread_row(conn, thread_ref)
                if row is not None and str(row["state"]) == "archived":
                    raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_THREAD_ARCHIVED")
                if row is None:
                    if request.expected_revision != 0:
                        raise FounderLoopStorageError(
                            "FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT"
                        )
                    existing_count = int(
                        conn.execute(
                            "SELECT COUNT(*) AS count FROM chat_thread_states"
                        ).fetchone()["count"]
                    )
                    if existing_count >= CHAT_WORKSPACE_MAX_THREADS:
                        raise FounderLoopStorageError(
                            "FOUNDER_LOOP_CHAT_WORKSPACE_CAPACITY_REACHED"
                        )
                    display_name = f"Conversation {existing_count + 1}"
                    revision = 1
                    created_at = now
                    conn.execute(
                        """
                        INSERT INTO chat_thread_states (
                            thread_ref, display_name, state, revision, draft_present,
                            draft_character_count, draft_fingerprint_ref,
                            created_at, updated_at
                        ) VALUES (?, ?, 'active', ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            thread_ref,
                            display_name,
                            revision,
                            int(request.draft_present),
                            request.draft_character_count,
                            request.draft_fingerprint_ref,
                            created_at,
                            now,
                        ),
                    )
                else:
                    self._require_revision(row, request.expected_revision)
                    display_name = str(row["display_name"])
                    revision = int(row["revision"]) + 1
                    created_at = str(row["created_at"])
                    conn.execute(
                        """
                        UPDATE chat_thread_states
                        SET revision = ?, draft_present = ?, draft_character_count = ?,
                            draft_fingerprint_ref = ?, updated_at = ?
                        WHERE thread_ref = ?
                        """,
                        (
                            revision,
                            int(request.draft_present),
                            request.draft_character_count,
                            request.draft_fingerprint_ref,
                            now,
                            thread_ref,
                        ),
                    )
                thread = self._build_thread(
                    thread_ref=thread_ref,
                    display_name=display_name,
                    state="active",
                    revision=revision,
                    draft_present=request.draft_present,
                    draft_character_count=request.draft_character_count,
                    draft_fingerprint_ref=request.draft_fingerprint_ref,
                    created_at=created_at,
                    updated_at=now,
                )
                receipt = self._receipt(
                    mutation_kind="draft_checkpoint",
                    lifecycle_action=None,
                    thread=thread,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    approval_refs=approval_refs,
                    created_at=now,
                )
                self._store_replay(conn, receipt)
                evidence_event_ref = receipt.receipt_ref
                self._store_outbox(
                    conn,
                    event_ref=evidence_event_ref,
                    log_kind=JsonlLogKind.receipt,
                    payload={
                        "event_ref": receipt.receipt_ref,
                        "safe_summary": receipt.safe_summary,
                        "evidence_refs": [
                            receipt.evidence_ref,
                            receipt.approval_ref,
                            receipt.exact_approval_scope_ref,
                            receipt.approval_validation_ref,
                            *request.metadata_refs,
                        ],
                    },
                )
        self._flush_outbox_event(evidence_event_ref)
        if replayed_receipt is not None:
            return replayed_receipt
        assert receipt is not None
        return receipt.model_dump(mode="json")

    def record_lifecycle(
        self,
        *,
        thread_ref: str,
        request: ChatThreadLifecycleRequest,
        idempotency_key_ref: str,
        approval_refs: dict[str, str],
    ) -> dict[str, Any]:
        validate_chat_thread_ref(thread_ref)
        validate_execution_ref(idempotency_key_ref, "idempotency_key_ref")
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        now = utc_now().isoformat()
        replayed_receipt: dict[str, Any] | None = None
        receipt: ChatThreadMutationReceipt | None = None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            replay = self._replay_row(conn, idempotency_key_ref)
            if replay is not None:
                replayed_receipt = self._validated_replay(
                    replay,
                    expected_thread_ref=thread_ref,
                    expected_payload_fingerprint_ref=payload_fingerprint_ref,
                    expected_idempotency_key_ref=idempotency_key_ref,
                    expected_mutation_kind="lifecycle",
                    expected_lifecycle_action=request.action,
                    expected_revision=request.expected_revision + 1,
                )
                evidence_event_ref = str(replayed_receipt["audit_ref"])
            else:
                row = self._thread_row(conn, thread_ref)
                if row is None:
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_CHAT_THREAD_NOT_FOUND"
                    )
                self._require_revision(row, request.expected_revision)
                current_state = str(row["state"])
                if request.action == "archive" and current_state != "active":
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_CHAT_THREAD_ALREADY_ARCHIVED"
                    )
                if request.action == "recover" and current_state != "archived":
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_CHAT_THREAD_ALREADY_ACTIVE"
                    )
                target_state = (
                    "archived" if request.action == "archive" else "active"
                )
                revision = int(row["revision"]) + 1
                conn.execute(
                    """
                    UPDATE chat_thread_states
                    SET state = ?, revision = ?, updated_at = ?
                    WHERE thread_ref = ?
                    """,
                    (target_state, revision, now, thread_ref),
                )
                thread = self._build_thread(
                    thread_ref=thread_ref,
                    display_name=str(row["display_name"]),
                    state=target_state,
                    revision=revision,
                    draft_present=bool(row["draft_present"]),
                    draft_character_count=int(row["draft_character_count"]),
                    draft_fingerprint_ref=str(row["draft_fingerprint_ref"]),
                    created_at=str(row["created_at"]),
                    updated_at=now,
                )
                receipt = self._receipt(
                    mutation_kind="lifecycle",
                    lifecycle_action=request.action,
                    thread=thread,
                    idempotency_key_ref=idempotency_key_ref,
                    payload_fingerprint_ref=payload_fingerprint_ref,
                    approval_refs=approval_refs,
                    created_at=now,
                )
                self._store_replay(conn, receipt)
                evidence_event_ref = receipt.audit_ref
                self._store_outbox(
                    conn,
                    event_ref=evidence_event_ref,
                    log_kind=JsonlLogKind.audit,
                    payload={
                        "event_ref": receipt.audit_ref,
                        "safe_summary": receipt.safe_summary,
                        "evidence_refs": [
                            receipt.evidence_ref,
                            receipt.approval_ref,
                            receipt.exact_approval_scope_ref,
                            receipt.approval_validation_ref,
                            *request.metadata_refs,
                        ],
                    },
                )
        self._flush_outbox_event(evidence_event_ref)
        if replayed_receipt is not None:
            return replayed_receipt
        assert receipt is not None
        return receipt.model_dump(mode="json")

    def _ensure_storage(self) -> None:
        if self.read_only:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_WORKSPACE_READ_ONLY")
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chat_thread_states (
                    thread_ref TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    draft_present INTEGER NOT NULL,
                    draft_character_count INTEGER NOT NULL,
                    draft_fingerprint_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_thread_mutation_replays (
                    key_ref TEXT PRIMARY KEY,
                    thread_ref TEXT NOT NULL,
                    payload_fingerprint_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_workspace_evidence_outbox (
                    event_ref TEXT PRIMARY KEY,
                    log_kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return self._founder_loop._connect()

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _thread_row(
        conn: sqlite3.Connection, thread_ref: str
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT thread_ref, display_name, state, revision, draft_present,
                   draft_character_count, draft_fingerprint_ref, created_at, updated_at
            FROM chat_thread_states WHERE thread_ref = ? LIMIT 1
            """,
            (thread_ref,),
        ).fetchone()

    @staticmethod
    def _replay_row(
        conn: sqlite3.Connection, idempotency_key_ref: str
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT payload_fingerprint_ref, receipt_json
            FROM chat_thread_mutation_replays WHERE key_ref = ? LIMIT 1
            """,
            (idempotency_key_ref,),
        ).fetchone()

    @staticmethod
    def _require_revision(row: sqlite3.Row, expected_revision: int) -> None:
        revision = int(row["revision"])
        if expected_revision != revision:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT")
        if revision >= CHAT_WORKSPACE_MAX_REVISION:
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_THREAD_REVISION_EXHAUSTED")

    @staticmethod
    def _build_thread(
        *,
        thread_ref: str,
        display_name: str,
        state: Literal["active", "archived"],
        revision: int,
        draft_present: bool,
        draft_character_count: int,
        draft_fingerprint_ref: str,
        created_at: str,
        updated_at: str,
    ) -> ChatThreadReadModel:
        return ChatThreadReadModel(
            thread_ref=thread_ref,
            display_name=display_name,
            state=state,
            revision=revision,
            draft_present=draft_present,
            draft_character_count=draft_character_count,
            draft_fingerprint_ref=draft_fingerprint_ref,
            draft_recovery_state=(
                "metadata_only_reentry_required" if draft_present else "empty"
            ),
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _thread_read_model(cls, row: sqlite3.Row) -> ChatThreadReadModel:
        state = str(row["state"])
        if state not in {"active", "archived"}:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_STORED_STATE_INVALID"
            )
        return cls._build_thread(
            thread_ref=str(row["thread_ref"]),
            display_name=str(row["display_name"]),
            state=state,
            revision=int(row["revision"]),
            draft_present=bool(row["draft_present"]),
            draft_character_count=int(row["draft_character_count"]),
            draft_fingerprint_ref=str(row["draft_fingerprint_ref"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _receipt(
        *,
        mutation_kind: Literal["draft_checkpoint", "lifecycle"],
        lifecycle_action: Literal["archive", "recover"] | None,
        thread: ChatThreadReadModel,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        approval_refs: dict[str, str],
        created_at: str,
    ) -> ChatThreadMutationReceipt:
        kind = lifecycle_action or mutation_kind
        return ChatThreadMutationReceipt(
            mutation_kind=mutation_kind,
            lifecycle_action=lifecycle_action,
            thread=thread,
            receipt_ref=chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=thread.thread_ref,
                revision=thread.revision,
                suffix="receipt",
            ),
            audit_ref=chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=thread.thread_ref,
                revision=thread.revision,
                suffix="audit",
            ),
            evidence_ref=chat_workspace_mutation_ref(
                kind=kind,
                thread_ref=thread.thread_ref,
                revision=thread.revision,
                suffix="evidence-ref",
            ),
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval_ref=approval_refs["approval_ref"],
            exact_approval_scope_ref=approval_refs["exact_approval_scope_ref"],
            approval_validation_ref=approval_refs["approval_validation_ref"],
            safe_summary=(
                "Chat draft checkpoint metadata recorded without a draft body."
                if mutation_kind == "draft_checkpoint"
                else "Chat thread lifecycle state recorded without execution."
            ),
            created_at=created_at,
        )

    @staticmethod
    def _store_replay(
        conn: sqlite3.Connection, receipt: ChatThreadMutationReceipt
    ) -> None:
        payload = receipt.model_dump(mode="json")
        conn.execute(
            """
            INSERT INTO chat_thread_mutation_replays (
                key_ref, thread_ref, payload_fingerprint_ref, receipt_json, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                receipt.idempotency_key_ref,
                receipt.thread.thread_ref,
                receipt.payload_fingerprint_ref,
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                receipt.created_at,
            ),
        )

    @staticmethod
    def _store_outbox(
        conn: sqlite3.Connection,
        *,
        event_ref: str,
        log_kind: JsonlLogKind,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO chat_workspace_evidence_outbox (
                event_ref, log_kind, payload_json, created_at, delivered_at
            ) VALUES (?, ?, ?, ?, NULL)
            """,
            (
                event_ref,
                log_kind.value,
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                utc_now().isoformat(),
            ),
        )

    def _flush_outbox_event(self, event_ref: str) -> None:
        try:
            with FileSingleWriterLockManager(
                self.state_dir / ".locks"
            ).acquire("chat-workspace-evidence-outbox"):
                self._flush_outbox_event_locked(event_ref)
        except OSError as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_LOCK_UNAVAILABLE"
            ) from exc

    def _flush_outbox_event_locked(self, event_ref: str) -> None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT log_kind, payload_json, delivered_at
                FROM chat_workspace_evidence_outbox
                WHERE event_ref = ?
                LIMIT 1
                """,
                (event_ref,),
            ).fetchone()
        if row is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_OUTBOX_MISSING"
            )
        if row["delivered_at"] is not None:
            return
        try:
            log_kind = JsonlLogKind(str(row["log_kind"]))
            payload = json.loads(str(row["payload_json"]))
            if not isinstance(payload, dict) or payload.get("event_ref") != event_ref:
                raise ValueError("invalid outbox payload")
        except (TypeError, ValueError) as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_OUTBOX_CORRUPT"
            ) from exc
        if not self._log_contains_event(log_kind, event_ref):
            try:
                self._founder_loop.append_log(log_kind, payload)
            except OSError as exc:
                raise FounderLoopStorageError(
                    "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_PENDING"
                ) from exc
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE chat_workspace_evidence_outbox
                SET delivered_at = ?
                WHERE event_ref = ? AND delivered_at IS NULL
                """,
                (utc_now().isoformat(), event_ref),
            )

    def _log_contains_event(
        self,
        log_kind: JsonlLogKind,
        event_ref: str,
    ) -> bool:
        path = self._founder_loop.logs_dir / f"{log_kind.value}.jsonl"
        if not path.exists():
            return False
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except (TypeError, ValueError):
                        continue
                    if isinstance(record, dict) and record.get("event_ref") == event_ref:
                        return True
        except OSError as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_LOG_UNAVAILABLE"
            ) from exc
        return False

    @staticmethod
    def _validated_replay(
        replay: sqlite3.Row,
        *,
        expected_thread_ref: str,
        expected_payload_fingerprint_ref: str,
        expected_idempotency_key_ref: str,
        expected_mutation_kind: Literal["draft_checkpoint", "lifecycle"],
        expected_lifecycle_action: Literal["archive", "recover"] | None,
        expected_revision: int,
    ) -> dict[str, Any]:
        if replay["payload_fingerprint_ref"] != expected_payload_fingerprint_ref:
            raise FounderLoopStorageDuplicateError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_IDEMPOTENCY_CONFLICT"
            )
        try:
            receipt = ChatThreadMutationReceipt.model_validate(
                {**json.loads(str(replay["receipt_json"])), "replayed": True}
            )
        except (TypeError, ValueError) as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT"
            ) from exc
        if (
            receipt.thread.thread_ref != expected_thread_ref
            or receipt.thread.revision != expected_revision
            or receipt.payload_fingerprint_ref != expected_payload_fingerprint_ref
            or receipt.idempotency_key_ref != expected_idempotency_key_ref
            or receipt.mutation_kind != expected_mutation_kind
            or receipt.lifecycle_action != expected_lifecycle_action
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT"
            )
        return receipt.model_dump(mode="json")
