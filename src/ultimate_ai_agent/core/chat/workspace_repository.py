from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
    ApprovalRequest,
    LocalApprovalAuthority,
)
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
    CHAT_WORKSPACE_APPROVAL_TTL_MINUTES,
    CHAT_WORKSPACE_MAX_ACTIVE_APPROVALS,
    CHAT_WORKSPACE_MAX_REVISION,
    CHAT_WORKSPACE_MAX_THREADS,
    CHAT_WORKSPACE_MAX_MUTATION_RECORDS,
    ChatCheckpointSnapshot,
    ChatWorkspaceApprovalCaptureRequest,
    ChatWorkspaceApprovalReceipt,
    ChatDraftCheckpointRequest,
    ChatThreadLifecycleRequest,
    ChatThreadMutationReceipt,
    ChatThreadReadModel,
    build_chat_workspace_approval_request,
    build_chat_workspace_read_model,
    chat_workspace_approval_refs,
    chat_workspace_checkpoint_ref,
    chat_workspace_mutation_ref,
    chat_workspace_payload_fingerprint_ref,
    validate_chat_thread_ref,
    validate_chat_workspace_idempotency_ref,
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
        if self.read_only and not self._workspace_schema_exists():
            return build_chat_workspace_read_model([]).model_dump(mode="json")
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

    def capture_approval(
        self,
        *,
        thread_ref: str,
        request: ChatWorkspaceApprovalCaptureRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        validate_chat_thread_ref(thread_ref)
        validate_chat_workspace_idempotency_ref(idempotency_key_ref)
        approval_idempotency_key_ref = idempotency_key_ref
        mutation_idempotency_key_ref = request.mutation_idempotency_key_ref
        mutation_request = request.mutation_request()
        lifecycle_action = (
            mutation_request.action
            if isinstance(mutation_request, ChatThreadLifecycleRequest)
            else None
        )
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {
                "thread_ref": thread_ref,
                **mutation_request.model_dump(mode="json"),
            }
        )
        approval_request = build_chat_workspace_approval_request(
            mutation_kind=request.mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=mutation_idempotency_key_ref,
            approval_idempotency_key_ref=approval_idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        refs = chat_workspace_approval_refs(
            mutation_kind=request.mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=mutation_idempotency_key_ref,
            approval_idempotency_key_ref=approval_idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        now = utc_now()
        expires_at = now + timedelta(minutes=CHAT_WORKSPACE_APPROVAL_TTL_MINUTES)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT approval_ref, approval_request_json, approval_grant_json,
                       mutation_kind, lifecycle_action, thread_ref,
                       idempotency_key_ref, payload_fingerprint_ref,
                       created_at, expires_at
                FROM chat_workspace_approval_grants
                WHERE idempotency_key_ref = ?
                LIMIT 1
                """,
                (approval_idempotency_key_ref,),
            ).fetchone()
            if row is not None:
                if (
                    str(row["mutation_kind"]) != request.mutation_kind
                    or row["lifecycle_action"] != lifecycle_action
                    or str(row["thread_ref"]) != thread_ref
                    or str(row["payload_fingerprint_ref"]) != payload_fingerprint_ref
                ):
                    raise FounderLoopStorageDuplicateError(
                        "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_IDEMPOTENCY_CONFLICT"
                    )
                grant = self._validated_approval_row(
                    row,
                    expected_request=approval_request,
                    expected_refs=refs,
                    expected_mutation_kind=request.mutation_kind,
                    expected_lifecycle_action=lifecycle_action,
                    expected_thread_ref=thread_ref,
                    expected_approval_idempotency_key_ref=(
                        approval_idempotency_key_ref
                    ),
                    expected_payload_fingerprint_ref=payload_fingerprint_ref,
                    now=now,
                    allow_expired_replay=True,
                )
            else:
                active_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) AS count
                        FROM chat_workspace_approval_grants
                        WHERE expires_at > ?
                        """,
                        (now.isoformat(),),
                    ).fetchone()["count"]
                )
                if active_count >= CHAT_WORKSPACE_MAX_ACTIVE_APPROVALS:
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_CAPACITY_REACHED"
                    )
                history_count = int(
                    conn.execute(
                        "SELECT COUNT(*) AS count FROM chat_workspace_approval_grants"
                    ).fetchone()["count"]
                )
                if history_count >= CHAT_WORKSPACE_MAX_MUTATION_RECORDS:
                    raise FounderLoopStorageError(
                        "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_HISTORY_CAPACITY_REACHED"
                    )
                authority = LocalApprovalAuthority()
                authority.create_request(approval_request)
                grant = authority.grant(
                    approval_request.approval_request_id,
                    approved_by_actor_id="operator-ref:local-user",
                    approval_ref=refs["approval_ref"],
                    expires_at=expires_at,
                )
                conn.execute(
                    """
                    INSERT INTO chat_workspace_approval_grants (
                        approval_ref, approval_request_json, approval_grant_json,
                        mutation_kind, lifecycle_action, thread_ref,
                        idempotency_key_ref, payload_fingerprint_ref,
                        created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        grant.approval_ref,
                        json.dumps(
                            approval_request.model_dump(mode="json"),
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            grant.model_dump(mode="json"),
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        request.mutation_kind,
                        lifecycle_action,
                        thread_ref,
                        idempotency_key_ref,
                        payload_fingerprint_ref,
                        grant.created_at.isoformat(),
                        grant.expires_at.isoformat(),
                    ),
                )
        return ChatWorkspaceApprovalReceipt(
            mutation_kind=request.mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=mutation_idempotency_key_ref,
            approval_idempotency_key_ref=approval_idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval_request_ref=refs["approval_request_ref"],
            approval_ref=refs["approval_ref"],
            exact_approval_scope_ref=refs["exact_approval_scope_ref"],
            approval_validation_ref=refs["approval_validation_ref"],
            expires_at=grant.expires_at.isoformat(),
        ).model_dump(mode="json")

    def load_exact_approval_grant(
        self,
        *,
        approval_ref: str,
        mutation_kind: Literal["draft_checkpoint", "lifecycle"],
        lifecycle_action: Literal["archive", "recover"] | None,
        thread_ref: str,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        allow_expired_replay: bool = False,
    ) -> tuple[ApprovalGrant, ApprovalRequest, dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT approval_ref, approval_request_json, approval_grant_json,
                       mutation_kind, lifecycle_action, thread_ref,
                       idempotency_key_ref, payload_fingerprint_ref,
                       created_at, expires_at
                FROM chat_workspace_approval_grants
                WHERE approval_ref = ?
                LIMIT 1
                """,
                (approval_ref,),
            ).fetchone()
        if row is None:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_REQUIRED"
            )
        approval_idempotency_key_ref = str(row["idempotency_key_ref"])
        approval_request = build_chat_workspace_approval_request(
            mutation_kind=mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=idempotency_key_ref,
            approval_idempotency_key_ref=approval_idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        refs = chat_workspace_approval_refs(
            mutation_kind=mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=idempotency_key_ref,
            approval_idempotency_key_ref=approval_idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        if approval_ref != refs["approval_ref"]:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_SCOPE_MISMATCH"
            )
        grant = self._validated_approval_row(
            row,
            expected_request=approval_request,
            expected_refs=refs,
            expected_mutation_kind=mutation_kind,
            expected_lifecycle_action=lifecycle_action,
            expected_thread_ref=thread_ref,
            expected_approval_idempotency_key_ref=approval_idempotency_key_ref,
            expected_payload_fingerprint_ref=payload_fingerprint_ref,
            now=utc_now(),
            allow_expired_replay=allow_expired_replay,
        )
        return grant, approval_request, refs

    def exact_replay(
        self,
        *,
        thread_ref: str,
        request: ChatDraftCheckpointRequest | ChatThreadLifecycleRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any] | None:
        validate_chat_thread_ref(thread_ref)
        validate_chat_workspace_idempotency_ref(idempotency_key_ref)
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        mutation_kind: Literal["draft_checkpoint", "lifecycle"] = (
            "lifecycle"
            if isinstance(request, ChatThreadLifecycleRequest)
            else "draft_checkpoint"
        )
        lifecycle_action = (
            request.action if isinstance(request, ChatThreadLifecycleRequest) else None
        )
        with self._connect() as conn:
            replay = self._replay_row(conn, idempotency_key_ref)
        if replay is None:
            return None
        return self._validated_replay(
            replay,
            expected_thread_ref=thread_ref,
            expected_payload_fingerprint_ref=payload_fingerprint_ref,
            expected_idempotency_key_ref=idempotency_key_ref,
            expected_mutation_kind=mutation_kind,
            expected_lifecycle_action=lifecycle_action,
            expected_revision=request.expected_revision + 1,
        )

    def record_draft_checkpoint(
        self,
        *,
        thread_ref: str,
        request: ChatDraftCheckpointRequest,
        idempotency_key_ref: str,
        approval_refs: dict[str, str],
    ) -> dict[str, Any]:
        validate_chat_thread_ref(thread_ref)
        validate_chat_workspace_idempotency_ref(idempotency_key_ref)
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        now = utc_now().isoformat()
        replayed_receipt: dict[str, Any] | None = None
        receipt: ChatThreadMutationReceipt | None = None
        previous_checkpoint: ChatCheckpointSnapshot | None = None
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
                self._require_mutation_capacity(conn)
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
                    previous_thread = self._thread_read_model(row)
                    previous_checkpoint = ChatCheckpointSnapshot(
                        checkpoint_ref=chat_workspace_checkpoint_ref(previous_thread),
                        thread=previous_thread,
                    )
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
                    previous_checkpoint=previous_checkpoint,
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
                            *(
                                [previous_checkpoint.checkpoint_ref]
                                if previous_checkpoint is not None
                                else []
                            ),
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
        validate_chat_workspace_idempotency_ref(idempotency_key_ref)
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
                self._require_mutation_capacity(conn)
                row = self._thread_row(conn, thread_ref)
                if row is None:
                    raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_THREAD_NOT_FOUND")
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
                target_state = "archived" if request.action == "archive" else "active"
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
                    previous_checkpoint=None,
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
                    delivery_attempted_at TEXT,
                    delivered_at TEXT
                );
                CREATE TABLE IF NOT EXISTS chat_workspace_approval_grants (
                    approval_ref TEXT PRIMARY KEY,
                    approval_request_json TEXT NOT NULL,
                    approval_grant_json TEXT NOT NULL,
                    mutation_kind TEXT NOT NULL,
                    lifecycle_action TEXT,
                    thread_ref TEXT NOT NULL,
                    idempotency_key_ref TEXT NOT NULL UNIQUE,
                    payload_fingerprint_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            outbox_columns = {
                str(row["name"])
                for row in conn.execute(
                    "PRAGMA table_info(chat_workspace_evidence_outbox)"
                ).fetchall()
            }
            if "delivery_attempted_at" not in outbox_columns:
                conn.execute(
                    "ALTER TABLE chat_workspace_evidence_outbox "
                    "ADD COLUMN delivery_attempted_at TEXT"
                )
                conn.execute(
                    """
                    UPDATE chat_workspace_evidence_outbox
                    SET delivery_attempted_at = created_at
                    WHERE delivered_at IS NULL
                    """
                )

    @staticmethod
    def _validated_approval_row(
        row: sqlite3.Row,
        *,
        expected_request: ApprovalRequest,
        expected_refs: dict[str, str],
        expected_mutation_kind: Literal["draft_checkpoint", "lifecycle"],
        expected_lifecycle_action: Literal["archive", "recover"] | None,
        expected_thread_ref: str,
        expected_approval_idempotency_key_ref: str,
        expected_payload_fingerprint_ref: str,
        now: datetime,
        allow_expired_replay: bool = False,
    ) -> ApprovalGrant:
        try:
            stored_request = ApprovalRequest.model_validate(
                json.loads(str(row["approval_request_json"]))
            )
            grant = ApprovalGrant.model_validate(
                json.loads(str(row["approval_grant_json"]))
            )
        except (TypeError, ValueError) as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_CORRUPT"
            ) from exc
        if (
            stored_request.model_dump(
                mode="json",
                exclude={"created_at": True, "actor_context": {"created_at": True}},
            )
            != expected_request.model_dump(
                mode="json",
                exclude={"created_at": True, "actor_context": {"created_at": True}},
            )
            or str(row["approval_ref"]) != expected_refs["approval_ref"]
            or str(row["mutation_kind"]) != expected_mutation_kind
            or row["lifecycle_action"] != expected_lifecycle_action
            or str(row["thread_ref"]) != expected_thread_ref
            or str(row["idempotency_key_ref"]) != expected_approval_idempotency_key_ref
            or str(row["payload_fingerprint_ref"]) != expected_payload_fingerprint_ref
            or str(row["created_at"]) != grant.created_at.isoformat()
            or str(row["expires_at"])
            != (grant.expires_at.isoformat() if grant.expires_at else "")
            or grant.expires_at is None
            or grant.expires_at <= grant.created_at
            or grant.expires_at - grant.created_at
            > timedelta(minutes=CHAT_WORKSPACE_APPROVAL_TTL_MINUTES)
            or grant.approval_ref != expected_refs["approval_ref"]
            or grant.approval_request_id != expected_request.approval_request_id
            or grant.run_id != expected_request.run_id
            or grant.subject_type != expected_request.subject_type
            or grant.subject_id != expected_request.subject_id
            or grant.granted_to_actor_id != expected_request.actor_context.actor_id
            or grant.approved_by_actor_id != "operator-ref:local-user"
            or grant.approved_actions != [expected_request.requested_action]
            or grant.approved_resource_refs != expected_request.resource_refs
            or grant.risk_level != expected_request.risk_level
            or grant.data_classification != expected_request.data_classification
            or grant.purpose != expected_request.purpose
            or grant.event_ref != expected_request.event_ref
            or grant.trace_id != expected_request.trace_id
            or grant.metadata != {"approval_mode": "local_dev"}
        ):
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_CORRUPT"
            )
        authority = LocalApprovalAuthority()
        authority.create_request(expected_request)
        authority.load_grant_for_validation(grant)
        decision = authority.validate_at_trusted_time(
            expected_request.to_validation_request(grant.approval_ref),
            current_time=now,
        )
        if not decision.allowed:
            if allow_expired_replay and "APPROVAL_EXPIRED" in decision.reason_codes:
                return grant
            code = (
                "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_EXPIRED"
                if "APPROVAL_EXPIRED" in decision.reason_codes
                else "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_DENIED"
            )
            raise FounderLoopStorageError(code)
        return grant

    def _workspace_schema_exists(self) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'chat_thread_states'
                LIMIT 1
                """
            ).fetchone()
        return row is not None

    def _connect(self) -> sqlite3.Connection:
        return self._founder_loop._connect()

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _thread_row(conn: sqlite3.Connection, thread_ref: str) -> sqlite3.Row | None:
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
    def _require_mutation_capacity(conn: sqlite3.Connection) -> None:
        count = int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM chat_thread_mutation_replays"
            ).fetchone()["count"]
        )
        if count >= CHAT_WORKSPACE_MAX_MUTATION_RECORDS:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_MUTATION_CAPACITY_REACHED"
            )

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
        previous_checkpoint: ChatCheckpointSnapshot | None,
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
            previous_checkpoint=previous_checkpoint,
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
            approval_idempotency_key_ref=approval_refs["approval_idempotency_key_ref"],
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
                event_ref, log_kind, payload_json, created_at,
                delivery_attempted_at, delivered_at
            ) VALUES (?, ?, ?, ?, NULL, NULL)
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
            with FileSingleWriterLockManager(self.state_dir / ".locks").acquire(
                "chat-workspace-evidence-outbox"
            ):
                self._flush_outbox_event_locked(event_ref)
        except OSError as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_LOCK_UNAVAILABLE"
            ) from exc

    def _flush_outbox_event_locked(self, event_ref: str) -> None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT log_kind, payload_json, delivery_attempted_at, delivered_at
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
        requires_recovery_scan = row["delivery_attempted_at"] is not None
        try:
            log_kind = JsonlLogKind(str(row["log_kind"]))
            payload = json.loads(str(row["payload_json"]))
            if not isinstance(payload, dict) or payload.get("event_ref") != event_ref:
                raise ValueError("invalid outbox payload")
        except (TypeError, ValueError) as exc:
            raise FounderLoopStorageError(
                "FOUNDER_LOOP_CHAT_WORKSPACE_EVIDENCE_OUTBOX_CORRUPT"
            ) from exc
        if not requires_recovery_scan:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE chat_workspace_evidence_outbox
                    SET delivery_attempted_at = ?
                    WHERE event_ref = ? AND delivery_attempted_at IS NULL
                    """,
                    (utc_now().isoformat(), event_ref),
                )
        if not requires_recovery_scan or not self._log_contains_event(
            log_kind, event_ref
        ):
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
                    if (
                        isinstance(record, dict)
                        and record.get("event_ref") == event_ref
                    ):
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
            raise FounderLoopStorageError("FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT")
        return receipt.model_dump(mode="json")
