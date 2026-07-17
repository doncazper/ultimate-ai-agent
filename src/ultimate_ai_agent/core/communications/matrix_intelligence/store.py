from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager

from .constants import MatrixIntelligenceOperation
from .contracts import (
    MatrixIntelligenceCommand,
    MatrixIntelligenceProposalDraft,
    MatrixIntelligenceProposalRecord,
    MatrixRoomAIPolicyMode,
    MatrixRoomAIPolicyRecord,
    matrix_intelligence_proposal_fingerprint_ref,
    stable_matrix_intelligence_ref,
)


_LOCK_KEY = "matrix-intelligence-state"


class MatrixIntelligenceStore:
    def __init__(self, state_dir: Path | None = None) -> None:
        configured = os.environ.get("UAA_MATRIX_INTELLIGENCE_STATE_DIR", "").strip()
        self.state_dir = (
            state_dir
            or (Path(configured).expanduser() if configured else None)
            or Path(".uaa") / "matrix-intelligence"
        )
        self.state_path = self.state_dir / "state.json"
        self.lock_manager = FileSingleWriterLockManager(self.state_dir / ".locks")
        self.binding_ref = stable_matrix_intelligence_ref(
            "store-binding-ref:matrix-intelligence",
            {"schema_version": "uaa-matrix-intelligence-store.v1"},
        )

    def read_policy(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
    ) -> MatrixRoomAIPolicyRecord:
        self._require_operation(
            command,
            {
                MatrixIntelligenceOperation.room_ai_policy_read,
                MatrixIntelligenceOperation.context_materialize,
            },
        )
        state = self._read_state()
        key = self._room_key(command.account_ref, command.room_ref)
        payload = state["policies"].get(key)
        if payload is not None:
            record = MatrixRoomAIPolicyRecord.model_validate(payload)
            if record.policy == MatrixRoomAIPolicyMode.scoped_allow and (
                record.expires_at is None or record.expires_at <= now
            ):
                return self._off_policy(command, now=now, reason="expired")
            return record
        return self._off_policy(command, now=now, reason="default")

    def write_policy(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
    ) -> tuple[MatrixRoomAIPolicyRecord, bool]:
        self._require_operation(
            command, {MatrixIntelligenceOperation.room_ai_policy_write}
        )
        assert command.requested_policy is not None
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state_unlocked()
            replay = self._replay(state, command)
            if replay is not None:
                return MatrixRoomAIPolicyRecord.model_validate(replay), True
            policy = command.requested_policy
            record = MatrixRoomAIPolicyRecord(
                policy_ref=command.policy_ref,
                account_ref=command.account_ref,
                room_ref=command.room_ref,
                policy=policy,
                scope_ref=stable_matrix_intelligence_ref(
                    "scope-ref:matrix-room-ai-policy",
                    {
                        "account_ref": command.account_ref,
                        "room_ref": command.room_ref,
                        "request_fingerprint_ref": command.request_fingerprint_ref,
                    },
                ),
                context_grant_ref=(
                    command.context_grant_ref
                    if policy == MatrixRoomAIPolicyMode.scoped_allow
                    else None
                ),
                expires_at=(
                    command.policy_expires_at
                    if policy == MatrixRoomAIPolicyMode.scoped_allow
                    else None
                ),
                updated_at=now,
                receipt_ref=stable_matrix_intelligence_ref(
                    "receipt-ref:matrix-room-ai-policy",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                context_materialization_eligible=(policy != MatrixRoomAIPolicyMode.off),
            )
            key = self._room_key(command.account_ref, command.room_ref)
            state["policies"][key] = record.model_dump(mode="json")
            self._record_idempotency(state, command, record.model_dump(mode="json"))
            self._write_state_unlocked(state)
            return record, False

    def read_proposal(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
    ) -> MatrixIntelligenceProposalRecord:
        self._require_operation(command, {MatrixIntelligenceOperation.proposal_read})
        assert command.proposal_ref is not None
        state = self._read_state()
        payload = state["proposals"].get(command.proposal_ref)
        if payload is None:
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_NOT_FOUND")
        record = MatrixIntelligenceProposalRecord.model_validate(payload)
        self._require_record_scope(command, record)
        if record.expires_at <= now:
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_EXPIRED")
        return record

    def persist_proposal(
        self,
        command: MatrixIntelligenceCommand,
        draft: MatrixIntelligenceProposalDraft,
        *,
        now: datetime,
    ) -> tuple[MatrixIntelligenceProposalRecord, bool]:
        self._require_operation(command, {MatrixIntelligenceOperation.proposal_persist})
        self._require_draft_scope(command, draft)
        fingerprint = matrix_intelligence_proposal_fingerprint_ref(draft)
        if fingerprint != command.proposal_fingerprint_ref:
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_SUBSTITUTION_DENIED")
        if draft.expires_at <= now:
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_EXPIRED")
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state_unlocked()
            replay = self._replay(state, command)
            if replay is not None:
                return MatrixIntelligenceProposalRecord.model_validate(replay), True
            existing = state["proposals"].get(draft.proposal_ref)
            if existing is not None:
                existing_record = MatrixIntelligenceProposalRecord.model_validate(
                    existing
                )
                if existing_record.proposal_fingerprint_ref != fingerprint:
                    raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_REF_REUSE_DENIED")
                return existing_record, True
            record = MatrixIntelligenceProposalRecord(
                **draft.model_dump(),
                created_at=now,
                receipt_ref=stable_matrix_intelligence_ref(
                    "receipt-ref:matrix-intelligence-proposal",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                proposal_fingerprint_ref=fingerprint,
            )
            state["proposals"][draft.proposal_ref] = record.model_dump(mode="json")
            self._record_idempotency(state, command, record.model_dump(mode="json"))
            self._write_state_unlocked(state)
            return record, False

    def delete_proposal(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
    ) -> tuple[str, bool]:
        self._require_operation(command, {MatrixIntelligenceOperation.proposal_delete})
        assert command.proposal_ref is not None
        with self.lock_manager.acquire(_LOCK_KEY):
            state = self._read_state_unlocked()
            replay = self._replay(state, command)
            if replay is not None:
                receipt_ref = str(replay.get("receipt_ref", ""))
                if not receipt_ref:
                    raise ValueError("MATRIX_INTELLIGENCE_DELETE_REPLAY_INVALID")
                return receipt_ref, True
            payload = state["proposals"].get(command.proposal_ref)
            if payload is None:
                raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_NOT_FOUND")
            record = MatrixIntelligenceProposalRecord.model_validate(payload)
            self._require_record_scope(command, record)
            del state["proposals"][command.proposal_ref]
            receipt_ref = stable_matrix_intelligence_ref(
                "receipt-ref:matrix-intelligence-proposal-delete",
                {
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "deleted_at": now.isoformat(),
                },
            )
            result = {"receipt_ref": receipt_ref, "proposal_ref": command.proposal_ref}
            self._record_idempotency(state, command, result)
            state["deletion_receipts"].append(result)
            state["deletion_receipts"] = state["deletion_receipts"][-256:]
            self._write_state_unlocked(state)
            return receipt_ref, False

    def _off_policy(
        self,
        command: MatrixIntelligenceCommand,
        *,
        now: datetime,
        reason: str,
    ) -> MatrixRoomAIPolicyRecord:
        return MatrixRoomAIPolicyRecord(
            policy_ref=command.policy_ref,
            account_ref=command.account_ref,
            room_ref=command.room_ref,
            policy=MatrixRoomAIPolicyMode.off,
            scope_ref=stable_matrix_intelligence_ref(
                "scope-ref:matrix-room-ai-policy-off",
                {
                    "account_ref": command.account_ref,
                    "room_ref": command.room_ref,
                    "reason": reason,
                },
            ),
            updated_at=now,
            receipt_ref=stable_matrix_intelligence_ref(
                "receipt-ref:matrix-room-ai-policy-read",
                {
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "reason": reason,
                },
            ),
            context_materialization_eligible=False,
        )

    @staticmethod
    def _room_key(account_ref: str, room_ref: str) -> str:
        return stable_matrix_intelligence_ref(
            "room-scope-key-ref:matrix-intelligence",
            {"account_ref": account_ref, "room_ref": room_ref},
        )

    @staticmethod
    def _require_operation(
        command: MatrixIntelligenceCommand,
        allowed: set[MatrixIntelligenceOperation],
    ) -> None:
        if command.operation not in allowed:
            raise ValueError("MATRIX_INTELLIGENCE_STORE_OPERATION_MISMATCH")

    @staticmethod
    def _require_draft_scope(
        command: MatrixIntelligenceCommand,
        draft: MatrixIntelligenceProposalDraft,
    ) -> None:
        if (
            draft.proposal_ref != command.proposal_ref
            or draft.account_ref != command.account_ref
            or draft.room_ref != command.room_ref
            or set(draft.source_refs) - set(command.event_refs)
        ):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_SCOPE_MISMATCH")

    @staticmethod
    def _require_record_scope(
        command: MatrixIntelligenceCommand,
        record: MatrixIntelligenceProposalRecord,
    ) -> None:
        if (
            record.proposal_ref != command.proposal_ref
            or record.account_ref != command.account_ref
            or record.room_ref != command.room_ref
        ):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_SCOPE_MISMATCH")

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "schema_version": "uaa-matrix-intelligence-store.v1",
            "policies": {},
            "proposals": {},
            "idempotency": {},
            "deletion_receipts": [],
        }

    def _read_state(self) -> dict[str, Any]:
        with self.lock_manager.acquire(_LOCK_KEY):
            return self._read_state_unlocked()

    def _read_state_unlocked(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state()
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("MATRIX_INTELLIGENCE_STORE_INVALID") from exc
        if payload.get("schema_version") != "uaa-matrix-intelligence-store.v1":
            raise ValueError("MATRIX_INTELLIGENCE_STORE_SCHEMA_INVALID")
        expected = {
            "schema_version",
            "policies",
            "proposals",
            "idempotency",
            "deletion_receipts",
        }
        if (
            set(payload) != expected
            or not all(
                isinstance(payload[name], dict)
                for name in ("policies", "proposals", "idempotency")
            )
            or not isinstance(payload["deletion_receipts"], list)
        ):
            raise ValueError("MATRIX_INTELLIGENCE_STORE_SHAPE_INVALID")
        return payload

    def _write_state_unlocked(self, state: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".matrix-intelligence-",
            suffix=".tmp",
            dir=self.state_dir,
        )
        temporary_path = Path(temporary)
        try:
            os.fchmod(descriptor, 0o600)
            encoded = json.dumps(
                state,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.state_path)
            os.chmod(self.state_path, 0o600)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _replay(
        state: dict[str, Any], command: MatrixIntelligenceCommand
    ) -> dict[str, Any] | None:
        payload = state["idempotency"].get(command.idempotency_ref)
        if payload is None:
            return None
        if payload.get("request_fingerprint_ref") != command.request_fingerprint_ref:
            raise ValueError("MATRIX_INTELLIGENCE_IDEMPOTENCY_SUBSTITUTION_DENIED")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("MATRIX_INTELLIGENCE_IDEMPOTENCY_RECORD_INVALID")
        return result

    @staticmethod
    def _record_idempotency(
        state: dict[str, Any],
        command: MatrixIntelligenceCommand,
        result: dict[str, Any],
    ) -> None:
        state["idempotency"][command.idempotency_ref] = {
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "result": result,
        }


__all__ = ["MatrixIntelligenceStore"]
