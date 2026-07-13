from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.memory.enums import (
    MemoryDataClassification,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRecordKind,
    MemoryRetentionState,
    MemoryStatus,
)
from ultimate_ai_agent.core.memory.feature_mine import (
    epistemic_role_for_candidate_kind,
)
from ultimate_ai_agent.core.memory.local_store import LocalMemoryStore
from ultimate_ai_agent.core.memory.feature_mine import (
    MEMORY_FEEDBACK_AUTHORITY_ACTION_REF,
    MEMORY_FEEDBACK_AUTHORITY_LANE_REF,
    MEMORY_FEEDBACK_CONTRACT_REF,
    MEMORY_FEEDBACK_EXACT_SCOPE_REF,
    MEMORY_FEEDBACK_ROLLBACK_REF,
    MEMORY_FEEDBACK_ROUTE_REF,
    MEMORY_FEEDBACK_SAFE_DISABLE_POSTURE_REF,
    MEMORY_FEEDBACK_SAFE_DISABLE_REF,
    MemoryFeedbackReceipt,
    MemoryFeedbackRequest,
    trust_delta_for_feedback,
)
from ultimate_ai_agent.core.memory.provider import MemoryProviderWriteRequest
from ultimate_ai_agent.core.memory.review_decisions import (
    FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_REVIEW_AUTHORITY_ACTION_REF,
    MEMORY_REVIEW_AUTHORITY_LANE_REF,
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_LIFECYCLE_AUTHORITY_ACTION_REF,
    MEMORY_REVIEW_LIFECYCLE_AUTHORITY_LANE_REF,
    MEMORY_REVIEW_LIFECYCLE_SCOPE_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
    MemoryReviewDecisionKind,
    MemoryReviewDecisionReceipt,
    MemoryReviewDecisionRequest,
    memory_review_reviewed_recall_ref,
)


class MemoryReviewRuntimeError(RuntimeError):
    """Raised when a governed memory-review runtime write cannot complete."""


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def ensure_memory_runtime_operation_tables(conn: sqlite3.Connection) -> None:
    """Create append-first operation ledgers outside the broad Founder Loop schema."""

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS memory_review_suppression_operations (
            key_ref TEXT PRIMARY KEY, candidate_ref TEXT NOT NULL,
            review_ref TEXT NOT NULL, decision TEXT NOT NULL,
            payload_fingerprint_ref TEXT NOT NULL, receipt_ref TEXT NOT NULL,
            approval_ref TEXT NOT NULL, approval_scope_ref TEXT NOT NULL,
            authority_decision_ref TEXT NOT NULL,
            authority_decision_outcome TEXT NOT NULL,
            authority_lease_ref TEXT NOT NULL, authority_action_ref TEXT NOT NULL,
            authority_lane_ref TEXT NOT NULL, authority_scope_ref TEXT NOT NULL,
            safe_disable_ref TEXT NOT NULL, safe_disable_posture_ref TEXT NOT NULL,
            safe_disable_enabled INTEGER NOT NULL, rollback_ref TEXT NOT NULL,
            suppressed_recall_record_refs_json TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, settled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS memory_feedback_update_operations (
            key_ref TEXT PRIMARY KEY, memory_record_ref TEXT NOT NULL,
            feedback_kind TEXT NOT NULL, payload_fingerprint_ref TEXT NOT NULL,
            receipt_ref TEXT NOT NULL, approval_ref TEXT NOT NULL,
            approval_scope_ref TEXT NOT NULL, authority_decision_ref TEXT NOT NULL,
            authority_decision_outcome TEXT NOT NULL,
            authority_lease_ref TEXT NOT NULL, authority_action_ref TEXT NOT NULL,
            authority_lane_ref TEXT NOT NULL, authority_scope_ref TEXT NOT NULL,
            safe_disable_ref TEXT NOT NULL, safe_disable_posture_ref TEXT NOT NULL,
            safe_disable_enabled INTEGER NOT NULL, rollback_ref TEXT NOT NULL,
            status TEXT NOT NULL, created_at TEXT NOT NULL, settled_at TEXT
        );
        """
    )
    existing = {
        str(row[1])
        for row in conn.execute(
            "PRAGMA table_info(memory_review_suppression_operations)"
        ).fetchall()
    }
    additions = {
        "approval_scope_ref": "TEXT",
        "authority_decision_ref": "TEXT",
        "authority_decision_outcome": "TEXT",
        "authority_lease_ref": "TEXT",
        "authority_action_ref": "TEXT",
        "authority_lane_ref": "TEXT",
        "authority_scope_ref": "TEXT",
        "safe_disable_ref": "TEXT",
        "safe_disable_posture_ref": "TEXT",
        "safe_disable_enabled": "INTEGER",
        "rollback_ref": "TEXT",
    }
    for column_name, column_type in additions.items():
        if column_name not in existing:
            conn.execute(
                "ALTER TABLE memory_review_suppression_operations "
                f"ADD COLUMN {column_name} {column_type}"
            )


def evaluate_memory_review_write_authority(
    *,
    active_authority_leases: Sequence[AuthorityLease],
    candidate_ref: str,
    review_ref: str,
    decision: MemoryReviewDecisionKind,
    idempotency_key_ref: str,
    payload_fingerprint_ref: str,
    lifecycle_suppression: bool = False,
    suppression_record_refs: Sequence[str] = (),
) -> AuthorityPolicyDecision:
    """Evaluate one exact memory-review write without caching authority."""

    return evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=(
                MEMORY_REVIEW_LIFECYCLE_AUTHORITY_ACTION_REF
                if lifecycle_suppression
                else MEMORY_REVIEW_AUTHORITY_ACTION_REF
            ),
            domain=AuthorityDomain.memory,
            capability=AuthorityCapability.write,
            safe_summary=(
                "Evaluate exact Memory Review lifecycle suppression write."
                if lifecycle_suppression
                else "Evaluate Memory write authority for exact Memory Review "
                "accept/correct reviewed recall write."
            ),
            resource_refs=[
                candidate_ref,
                review_ref,
                FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
                (
                    MEMORY_REVIEW_LIFECYCLE_SCOPE_REF
                    if lifecycle_suppression
                    else MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
                ),
                idempotency_key_ref,
                payload_fingerprint_ref,
                *sorted(set(suppression_record_refs)),
            ],
            route_ref=(
                "POST /control-center/memory/review/{candidate_ref}/"
                f"{str(decision).replace('_', '-')}"
            ),
            lane_ref=(
                MEMORY_REVIEW_LIFECYCLE_AUTHORITY_LANE_REF
                if lifecycle_suppression
                else MEMORY_REVIEW_AUTHORITY_LANE_REF
            ),
            requested_mode=TrustMode.ask_before_changes,
            draft_fallback_available=True,
            rollback_ref=MEMORY_REVIEW_WRITE_ROLLBACK_REF,
            safe_disable_ref=MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
        ),
        list(active_authority_leases),
    )


def evaluate_memory_feedback_write_authority(
    *,
    active_authority_leases: Sequence[AuthorityLease],
    memory_record_ref: str,
    idempotency_key_ref: str,
    payload_fingerprint_ref: str,
) -> AuthorityPolicyDecision:
    """Evaluate one exact reviewed-recall metadata update without caching authority."""

    return evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=MEMORY_FEEDBACK_AUTHORITY_ACTION_REF,
            domain=AuthorityDomain.memory,
            capability=AuthorityCapability.write,
            safe_summary=(
                "Evaluate exact Memory feedback metadata update authority for one "
                "reviewed recall record."
            ),
            resource_refs=[
                memory_record_ref,
                MEMORY_FEEDBACK_CONTRACT_REF,
                MEMORY_FEEDBACK_EXACT_SCOPE_REF,
                idempotency_key_ref,
                payload_fingerprint_ref,
            ],
            route_ref=MEMORY_FEEDBACK_ROUTE_REF,
            lane_ref=MEMORY_FEEDBACK_AUTHORITY_LANE_REF,
            requested_mode=TrustMode.ask_before_changes,
            draft_fallback_available=True,
            rollback_ref=MEMORY_FEEDBACK_ROLLBACK_REF,
            safe_disable_ref=MEMORY_FEEDBACK_SAFE_DISABLE_REF,
        ),
        list(active_authority_leases),
    )


def memory_feedback_update_operation(
    *,
    idempotency_key_ref: str,
    memory_record_ref: str,
    feedback_kind: str,
    payload_fingerprint_ref: str,
    receipt_ref: str,
    approval: Mapping[str, Any],
    authority_decision: AuthorityPolicyDecision,
    safe_disable_enabled: bool,
    created_at: str,
) -> dict[str, Any]:
    return {
        "key_ref": idempotency_key_ref,
        "memory_record_ref": memory_record_ref,
        "feedback_kind": feedback_kind,
        "payload_fingerprint_ref": payload_fingerprint_ref,
        "receipt_ref": receipt_ref,
        "approval_ref": approval["approval_ref"],
        "approval_scope_ref": approval["approval_scope_ref"],
        "authority_decision_ref": authority_decision.decision_ref,
        "authority_decision_outcome": authority_decision.outcome,
        "authority_lease_ref": authority_decision.lease_ref,
        "authority_action_ref": MEMORY_FEEDBACK_AUTHORITY_ACTION_REF,
        "authority_lane_ref": MEMORY_FEEDBACK_AUTHORITY_LANE_REF,
        "authority_scope_ref": MEMORY_FEEDBACK_EXACT_SCOPE_REF,
        "safe_disable_ref": MEMORY_FEEDBACK_SAFE_DISABLE_REF,
        "safe_disable_posture_ref": MEMORY_FEEDBACK_SAFE_DISABLE_POSTURE_REF,
        "safe_disable_enabled": int(safe_disable_enabled),
        "rollback_ref": MEMORY_FEEDBACK_ROLLBACK_REF,
        "created_at": created_at,
    }


def build_memory_feedback_receipt(
    *,
    request: MemoryFeedbackRequest,
    receipt_ref: str,
    idempotency_key_ref: str,
    payload_fingerprint_ref: str,
    approval: Mapping[str, Any],
    authority_decision: AuthorityPolicyDecision,
    safe_disable_enabled: bool,
    updated_record: Any,
) -> dict[str, Any]:
    return MemoryFeedbackReceipt(
        receipt_ref=receipt_ref,
        memory_record_ref=str(request.memory_record_ref),
        feedback_kind=request.feedback_kind,
        reviewer_ref=request.reviewer_ref,
        idempotency_key_ref=idempotency_key_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        approval_ref=approval["approval_ref"],
        approval_scope_ref=approval["approval_scope_ref"],
        approval_status=approval["approval_status"],
        approval_reason_refs=approval["approval_reason_refs"],
        authority_decision_ref=authority_decision.decision_ref,
        authority_decision_outcome=authority_decision.outcome,
        authority_lease_ref=str(authority_decision.lease_ref),
        source_refs=request.source_refs,
        evidence_refs=request.evidence_refs,
        note_ref=request.note_ref,
        trust_delta=trust_delta_for_feedback(request.feedback_kind),
        trust_score_after=updated_record.trust_score,
        stale_state_after=_enum_value(updated_record.stale_state),
        conflict_state_after=_enum_value(updated_record.conflict_state),
        blocked_state_refs=list(request.blocked_state_refs),
        safe_disable_enabled=safe_disable_enabled,
    ).model_dump(mode="json")


def memory_feedback_pre_start_is_valid(
    *,
    approval_grant: Any,
    memory_record_ref: str,
    idempotency_key_ref: str,
    payload_fingerprint_ref: str,
    authority_decision: AuthorityPolicyDecision,
    fresh_authority_decision: AuthorityPolicyDecision,
    safe_disable_enabled: bool,
    checked_at: datetime,
) -> bool:
    required_resources = {
        memory_record_ref,
        MEMORY_FEEDBACK_EXACT_SCOPE_REF,
        idempotency_key_ref,
        payload_fingerprint_ref,
    }
    return bool(
        safe_disable_enabled
        and approval_grant is not None
        and approval_grant.revoked_at is None
        and (
            approval_grant.expires_at is None or approval_grant.expires_at > checked_at
        )
        and required_resources.issubset(set(approval_grant.approved_resource_refs))
        and "record-memory-feedback-metadata-update" in approval_grant.approved_actions
        and fresh_authority_decision.outcome == authority_decision.outcome
        and fresh_authority_decision.decision_ref == authority_decision.decision_ref
        and fresh_authority_decision.lease_ref == authority_decision.lease_ref
    )


def write_memory_review_recall_record(
    *,
    storage_path: Path,
    candidate: dict[str, Any],
    decision: MemoryReviewDecisionKind,
    request: MemoryReviewDecisionRequest,
    receipt_ref: str,
    evidence_ref: str,
    reviewed_recall_ref: str,
) -> str:
    """Write the deterministic reviewed-recall projection for one decision."""

    safe_summary = str(candidate.get("safe_summary") or "").strip()
    if decision == "correct":
        safe_summary = (
            "Reviewed memory correction recorded from bounded corrected safe "
            f"summary: {request.corrected_safe_summary}"
        )
    memory_request = MemoryProviderWriteRequest(
        request_id=f"memory-review-recall-write:{receipt_ref}",
        provider_ref="provider-ref:local-memory-store:memory-review",
        memory_kind=(
            MemoryRecordKind.correction
            if decision == "correct"
            else MemoryRecordKind.structured_fact
        ),
        memory_layer=MemoryLayer.record,
        epistemic_role=epistemic_role_for_candidate_kind(
            str(candidate.get("candidate_kind") or "unknown")
        ),
        provider_kind=MemoryProviderKind.local_sqlite,
        safe_summary=safe_summary,
        source_refs=request.source_refs,
        evidence_refs=list(dict.fromkeys([*request.evidence_refs, evidence_ref])),
        event_refs=[evidence_ref],
        receipt_refs=[receipt_ref],
        user_reviewed=True,
        automatic_write=False,
        data_classification=MemoryDataClassification.internal,
        confidence_score=0.7,
        trust_score=0.7,
        dedup_key=reviewed_recall_ref,
        context_pack_eligible=False,
        injection_priority=0,
        tags=["memory-review-decision", f"memory-review-decision:{decision}"],
        metadata_refs=list(
            dict.fromkeys(
                ref
                for ref in [
                    reviewed_recall_ref,
                    str(candidate.get("review_ref") or ""),
                    str(candidate.get("business_memory_candidate_ref") or ""),
                    *request.metadata_refs,
                ]
                if ref
            )
        ),
        metadata={
            "authority_boundary_ref": (
                "memory-review-recall-record-is-not-truth-or-context-injection"
            ),
            "decision": decision,
            "reviewed_recall_ref": reviewed_recall_ref,
            "context_injection_authorized": False,
            "source_truth_authority": False,
            "connector_write_authorized": False,
            "automatic_action_execution_authorized": False,
        },
    )
    store = LocalMemoryStore(storage_path=storage_path)
    try:
        decision_result = store.put_record(
            memory_request,
            initial_status=MemoryStatus.pending_review,
            initial_retention_state=MemoryRetentionState.blocked,
        )
    finally:
        store.close()
    if not getattr(decision_result, "allowed", False) or not decision_result.memory_id:
        raise MemoryReviewRuntimeError("FOUNDER_LOOP_MEMORY_RECALL_RECORD_DENIED")
    return f"memory-record-ref:{decision_result.memory_id}"


def activate_memory_review_recall_record(
    *,
    storage_path: Path,
    record_ref: str,
    receipt_ref: str,
) -> None:
    memory_id = str(record_ref).removeprefix("memory-record-ref:")
    store = LocalMemoryStore(storage_path=storage_path)
    try:
        store.activate_prepared_record(memory_id=memory_id, receipt_ref=receipt_ref)
    finally:
        store.close()


def memory_review_recall_search_index_status(*, storage_path: Path) -> dict[str, Any]:
    store = LocalMemoryStore(storage_path=storage_path)
    try:
        return store.search_index_status()
    finally:
        store.close()


def memory_review_recall_record_refs_for_candidate(
    *,
    storage_path: Path,
    candidate: dict[str, Any],
    candidate_ref: str,
) -> list[str]:
    match_refs = {
        candidate_ref,
        str(candidate.get("review_ref") or ""),
        str(candidate.get("business_memory_candidate_ref") or ""),
        memory_review_reviewed_recall_ref(candidate_ref),
    }
    match_refs = {ref for ref in match_refs if ref}
    store = LocalMemoryStore(storage_path=storage_path)
    try:
        if store.record_count() > 500:
            raise MemoryReviewRuntimeError(
                "FOUNDER_LOOP_MEMORY_SUPPRESSION_LOOKUP_INCOMPLETE"
            )
        matched: list[str] = []
        for record in store.list_records(limit=500):
            record_refs = [
                *record.metadata_refs,
                *record.receipt_refs,
                *[str(value) for value in record.metadata.values() if value],
            ]
            if match_refs.intersection(record_refs):
                matched.append(f"memory-record-ref:{record.memory_id}")
        return list(dict.fromkeys(matched))
    finally:
        store.close()


def suppress_memory_review_recall_records_after_terminal_decision(
    *,
    storage_path: Path,
    receipt: MemoryReviewDecisionReceipt,
) -> None:
    if receipt.decision not in {
        "reject",
        "merge",
        "supersede",
        "expire",
        "forget_request",
    }:
        return
    if not receipt.suppressed_recall_record_refs:
        return
    store = LocalMemoryStore(storage_path=storage_path)
    try:
        for record_ref in receipt.suppressed_recall_record_refs:
            memory_id = str(record_ref).removeprefix("memory-record-ref:")
            status = (
                MemoryStatus.superseded
                if receipt.decision in {"merge", "supersede"}
                else MemoryStatus.revoked
            )
            retention_state = (
                MemoryRetentionState.deletion_requested
                if receipt.decision == "forget_request"
                else MemoryRetentionState.expired
                if receipt.decision == "expire"
                else MemoryRetentionState.blocked
            )
            store.suppress_record(
                memory_id=memory_id,
                receipt_ref=receipt.receipt_ref,
                reason=f"memory-review-terminal-decision:{receipt.decision}",
                status=status,
                retention_state=retention_state,
            )
    finally:
        store.close()


def load_memory_review_suppression_operation(
    *,
    fetch_all: Callable[[str, tuple[Any, ...]], Sequence[Mapping[str, Any]]],
    idempotency_key_ref: str,
) -> dict[str, Any] | None:
    rows = fetch_all(
        """
        SELECT key_ref, candidate_ref, review_ref, decision,
               payload_fingerprint_ref, receipt_ref, approval_ref,
               approval_scope_ref, authority_decision_ref,
               authority_decision_outcome, authority_lease_ref,
               authority_action_ref, authority_lane_ref, authority_scope_ref,
               safe_disable_ref, safe_disable_posture_ref, safe_disable_enabled,
               rollback_ref,
               suppressed_recall_record_refs_json, status, created_at, settled_at
        FROM memory_review_suppression_operations
        WHERE key_ref = ?
        LIMIT 1
        """,
        (idempotency_key_ref,),
    )
    if not rows:
        return None
    payload = dict(rows[0])
    payload["suppressed_recall_record_refs"] = list(
        json.loads(str(payload.pop("suppressed_recall_record_refs_json")))
    )
    return payload


def validate_prepared_suppression_authority_binding(
    *,
    prepared: Mapping[str, Any],
    receipt: MemoryReviewDecisionReceipt,
) -> None:
    fields = (
        "approval_ref",
        "approval_scope_ref",
        "authority_decision_ref",
        "authority_decision_outcome",
        "authority_lease_ref",
        "authority_action_ref",
        "authority_lane_ref",
        "authority_scope_ref",
        "safe_disable_ref",
        "safe_disable_posture_ref",
        "rollback_ref",
    )
    if (
        any(prepared[field] != getattr(receipt, field) for field in fields)
        or bool(prepared["safe_disable_enabled"]) != receipt.safe_disable_enabled
    ):
        raise MemoryReviewRuntimeError(
            "FOUNDER_LOOP_MEMORY_SUPPRESSION_AUTHORITY_BINDING_CONFLICT"
        )


def prepare_memory_review_suppression_operation(
    *,
    conn: sqlite3.Connection,
    idempotency_key_ref: str,
    candidate_ref: str,
    review_ref: str,
    decision: MemoryReviewDecisionKind,
    payload_fingerprint_ref: str,
    receipt_ref: str,
    approval_ref: str,
    approval_scope_ref: str,
    authority_decision_ref: str,
    authority_decision_outcome: str,
    authority_lease_ref: str,
    authority_action_ref: str,
    authority_lane_ref: str,
    authority_scope_ref: str,
    safe_disable_ref: str,
    safe_disable_posture_ref: str,
    safe_disable_enabled: bool,
    rollback_ref: str,
    suppressed_recall_record_refs: Sequence[str],
    created_at: datetime,
) -> None:
    refs_json = json.dumps(
        list(suppressed_recall_record_refs), sort_keys=True, separators=(",", ":")
    )
    conn.execute(
        """
        INSERT INTO memory_review_suppression_operations (
            key_ref, candidate_ref, review_ref, decision,
            payload_fingerprint_ref, receipt_ref, approval_ref,
            approval_scope_ref, authority_decision_ref,
            authority_decision_outcome, authority_lease_ref,
            authority_action_ref, authority_lane_ref, authority_scope_ref,
            safe_disable_ref, safe_disable_posture_ref, safe_disable_enabled,
            rollback_ref,
            suppressed_recall_record_refs_json, status, created_at, settled_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  'prepared', ?, NULL)
        ON CONFLICT(key_ref) DO NOTHING
        """,
        (
            idempotency_key_ref,
            candidate_ref,
            review_ref,
            decision,
            payload_fingerprint_ref,
            receipt_ref,
            approval_ref,
            approval_scope_ref,
            authority_decision_ref,
            authority_decision_outcome,
            authority_lease_ref,
            authority_action_ref,
            authority_lane_ref,
            authority_scope_ref,
            safe_disable_ref,
            safe_disable_posture_ref,
            int(safe_disable_enabled),
            rollback_ref,
            refs_json,
            created_at.isoformat(),
        ),
    )
    row = conn.execute(
        """
        SELECT candidate_ref, review_ref, decision, payload_fingerprint_ref,
               receipt_ref, approval_ref, approval_scope_ref,
               authority_decision_ref, authority_decision_outcome,
               authority_lease_ref, authority_action_ref, authority_lane_ref,
               authority_scope_ref, safe_disable_ref, safe_disable_posture_ref,
               safe_disable_enabled, rollback_ref,
               suppressed_recall_record_refs_json
        FROM memory_review_suppression_operations WHERE key_ref = ?
        """,
        (idempotency_key_ref,),
    ).fetchone()
    expected = (
        candidate_ref,
        review_ref,
        decision,
        payload_fingerprint_ref,
        receipt_ref,
        approval_ref,
        approval_scope_ref,
        authority_decision_ref,
        authority_decision_outcome,
        authority_lease_ref,
        authority_action_ref,
        authority_lane_ref,
        authority_scope_ref,
        safe_disable_ref,
        safe_disable_posture_ref,
        int(safe_disable_enabled),
        rollback_ref,
        refs_json,
    )
    if row is None or tuple(row) != expected:
        raise MemoryReviewRuntimeError(
            "FOUNDER_LOOP_MEMORY_SUPPRESSION_IDEMPOTENCY_CONFLICT"
        )


def settle_memory_review_suppression_operation(
    *,
    conn: sqlite3.Connection,
    idempotency_key_ref: str,
    receipt_ref: str,
    settled_at: datetime,
) -> None:
    cursor = conn.execute(
        """
        UPDATE memory_review_suppression_operations
        SET status = 'settled', settled_at = ?
        WHERE key_ref = ? AND receipt_ref = ? AND status IN ('prepared', 'settled')
        """,
        (settled_at.isoformat(), idempotency_key_ref, receipt_ref),
    )
    if cursor.rowcount != 1:
        raise MemoryReviewRuntimeError(
            "FOUNDER_LOOP_MEMORY_SUPPRESSION_OPERATION_NOT_PREPARED"
        )


def load_memory_feedback_update_operation(
    *,
    fetch_all: Callable[[str, tuple[Any, ...]], Sequence[Mapping[str, Any]]],
    idempotency_key_ref: str,
) -> dict[str, Any] | None:
    rows = fetch_all(
        """
        SELECT * FROM memory_feedback_update_operations
        WHERE key_ref = ? LIMIT 1
        """,
        (idempotency_key_ref,),
    )
    return dict(rows[0]) if rows else None


def prepare_memory_feedback_update_operation(
    *,
    conn: sqlite3.Connection,
    operation: Mapping[str, Any],
) -> None:
    fields = (
        "key_ref",
        "memory_record_ref",
        "feedback_kind",
        "payload_fingerprint_ref",
        "receipt_ref",
        "approval_ref",
        "approval_scope_ref",
        "authority_decision_ref",
        "authority_decision_outcome",
        "authority_lease_ref",
        "authority_action_ref",
        "authority_lane_ref",
        "authority_scope_ref",
        "safe_disable_ref",
        "safe_disable_posture_ref",
        "safe_disable_enabled",
        "rollback_ref",
        "created_at",
    )
    values = tuple(operation[field] for field in fields)
    conn.execute(
        f"""
        INSERT INTO memory_feedback_update_operations ({", ".join(fields)}, status,
            settled_at)
        VALUES ({", ".join("?" for _ in fields)}, 'prepared', NULL)
        ON CONFLICT(key_ref) DO NOTHING
        """,
        values,
    )
    bound_fields = fields[:-1]
    row = conn.execute(
        f"SELECT {', '.join(bound_fields)} FROM memory_feedback_update_operations "
        "WHERE key_ref = ?",
        (operation["key_ref"],),
    ).fetchone()
    if row is None or tuple(row) != values[:-1]:
        raise MemoryReviewRuntimeError(
            "FOUNDER_LOOP_MEMORY_FEEDBACK_IDEMPOTENCY_CONFLICT"
        )


def persist_memory_feedback_receipt(
    *,
    conn: sqlite3.Connection,
    receipt: Mapping[str, Any],
) -> None:
    receipt_json = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    conn.execute(
        """
        INSERT INTO memory_feedback_receipts (
            receipt_ref, memory_record_ref, feedback_kind,
            payload_fingerprint_ref, receipt_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            receipt["receipt_ref"],
            receipt["memory_record_ref"],
            receipt["feedback_kind"],
            receipt["payload_fingerprint_ref"],
            receipt_json,
            receipt["created_at"],
        ),
    )
    conn.execute(
        """
        INSERT INTO memory_feedback_replays (
            key_ref, memory_record_ref, payload_fingerprint_ref,
            receipt_ref, receipt_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            receipt["idempotency_key_ref"],
            receipt["memory_record_ref"],
            receipt["payload_fingerprint_ref"],
            receipt["receipt_ref"],
            receipt_json,
            receipt["created_at"],
        ),
    )
    cursor = conn.execute(
        """
        UPDATE memory_feedback_update_operations
        SET status = 'settled', settled_at = ?
        WHERE key_ref = ? AND receipt_ref = ? AND status IN ('prepared', 'settled')
        """,
        (
            receipt["created_at"],
            receipt["idempotency_key_ref"],
            receipt["receipt_ref"],
        ),
    )
    if cursor.rowcount != 1:
        raise MemoryReviewRuntimeError(
            "FOUNDER_LOOP_MEMORY_FEEDBACK_OPERATION_NOT_PREPARED"
        )


def update_memory_review_projection_after_decision(
    *,
    conn: sqlite3.Connection,
    candidate: dict[str, Any],
    receipt: MemoryReviewDecisionReceipt,
    related_candidates: Sequence[dict[str, Any]] = (),
) -> None:
    review_state = {
        "accept": "accepted",
        "correct": "corrected",
        "reject": "rejected",
        "defer": "deferred",
        "merge": "merged",
        "supersede": "superseded",
        "expire": "expired",
        "forget_request": "forget_requested",
    }[receipt.decision]
    confidence_posture = {
        "accept": "reviewed_recall_safe_ref_only",
        "correct": "corrected_summary_ref_reviewed",
        "reject": "rejected_candidate_preserved",
        "defer": "deferred_pending_operator_review",
        "merge": "merge_receipt_recorded_no_silent_deletion",
        "supersede": "supersede_receipt_recorded_old_refs_preserved",
        "expire": "expiry_receipt_recorded_recall_suppressed",
        "forget_request": "forget_request_receipt_recorded_delete_execution_blocked",
    }[receipt.decision]
    next_safe_action = {
        "accept": (
            "Use reviewed recall refs only after scoped retrieval/context policy; "
            "context injection remains blocked."
        ),
        "correct": (
            "Review the corrected safe summary ref; memory writes and context "
            "injection remain blocked."
        ),
        "reject": (
            "Keep the rejected candidate preserved as blocked review state so "
            "stale refs do not silently return."
        ),
        "defer": (
            "Revisit the memory candidate later; no recall record or memory write "
            "was created."
        ),
        "merge": (
            "Inspect merge receipt refs and preserve source candidates until a "
            "scoped memory write policy exists."
        ),
        "supersede": (
            "Inspect supersede receipt refs; old candidates remain preserved and "
            "delete execution stays blocked."
        ),
        "expire": (
            "Keep expired recall excluded; deletion and context injection remain "
            "separately blocked."
        ),
        "forget_request": (
            "Review the forget-request receipt; delete and export execution remain "
            "blocked until a scoped retention milestone exists."
        ),
    }[receipt.decision]
    evidence_refs = list(
        dict.fromkeys(
            [
                *list(candidate.get("evidence_refs") or []),
                *receipt.evidence_refs,
                receipt.receipt_ref,
            ]
        )
    )
    blocked_states = list(
        dict.fromkeys(
            [
                *list(candidate.get("blocked_states") or []),
                *[
                    ref.removeprefix("blocked-state:")
                    for ref in receipt.blocked_state_refs
                ],
            ]
        )
    )
    conn.execute(
        """
        UPDATE memory_review_queue
        SET status = ?, review_state = ?, correction_posture = ?,
            rejection_posture = ?, confidence_posture = ?, stale_state = ?,
            blocked_states_json = ?, next_safe_action = ?, evidence_refs_json = ?
        WHERE review_ref = ?
        """,
        (
            review_state,
            review_state,
            (
                "corrected_summary_ref_recorded_no_raw_content"
                if receipt.decision == "correct"
                else "merge_receipt_refs_recorded_no_raw_content"
                if receipt.decision == "merge"
                else "supersede_receipt_refs_recorded_no_raw_content"
                if receipt.decision == "supersede"
                else str(candidate.get("correction_posture"))
            ),
            (
                "rejected_candidate_preserved_with_receipt"
                if receipt.decision == "reject"
                else "forget_request_recorded_delete_execution_blocked"
                if receipt.decision == "forget_request"
                else str(candidate.get("rejection_posture"))
            ),
            confidence_posture,
            "recheck_memory_decision_receipt_before_recall",
            json.dumps(blocked_states, sort_keys=True, separators=(",", ":")),
            next_safe_action,
            json.dumps(evidence_refs, sort_keys=True, separators=(",", ":")),
            receipt.review_ref,
        ),
    )
    if receipt.decision not in {"merge", "supersede"}:
        return
    related_review_state = "merged" if receipt.decision == "merge" else "superseded"
    related_confidence_posture = (
        "merged_by_receipt_ref_no_silent_deletion"
        if receipt.decision == "merge"
        else "superseded_by_receipt_ref_no_silent_deletion"
    )
    correction_posture = (
        "merge_peer_receipt_ref_recorded_no_raw_content"
        if receipt.decision == "merge"
        else "superseded_by_receipt_ref_recorded_no_raw_content"
    )
    related_next_safe_action = (
        "Inspect the merge receipt before using either candidate; both records "
        "remain preserved and delete/export execution is blocked."
        if receipt.decision == "merge"
        else "Inspect the supersede receipt before using the older candidate; the "
        "old record remains preserved and delete/export execution is blocked."
    )
    for related_candidate in related_candidates:
        related_review_ref = str(related_candidate.get("review_ref") or "")
        if not related_review_ref or related_review_ref == receipt.review_ref:
            continue
        related_evidence_refs = list(
            dict.fromkeys(
                [
                    *list(related_candidate.get("evidence_refs") or []),
                    *receipt.evidence_refs,
                    receipt.receipt_ref,
                ]
            )
        )
        related_blocked_states = list(
            dict.fromkeys(
                [
                    *list(related_candidate.get("blocked_states") or []),
                    *[
                        ref.removeprefix("blocked-state:")
                        for ref in receipt.blocked_state_refs
                    ],
                ]
            )
        )
        conn.execute(
            """
            UPDATE memory_review_queue
            SET status = ?, review_state = ?, correction_posture = ?,
                confidence_posture = ?, stale_state = ?, blocked_states_json = ?,
                next_safe_action = ?, evidence_refs_json = ?
            WHERE review_ref = ?
            """,
            (
                related_review_state,
                related_review_state,
                correction_posture,
                related_confidence_posture,
                "recheck_memory_decision_receipt_before_recall",
                json.dumps(
                    related_blocked_states, sort_keys=True, separators=(",", ":")
                ),
                related_next_safe_action,
                json.dumps(
                    related_evidence_refs, sort_keys=True, separators=(",", ":")
                ),
                related_review_ref,
            ),
        )


def memory_workbench_loop_refs(
    *,
    actions: Sequence[Mapping[str, Any]],
    plans: Sequence[Mapping[str, Any]],
    briefings: Sequence[Mapping[str, Any]],
    turn_receipts: Sequence[Mapping[str, Any]],
    handoff_receipts: Sequence[Mapping[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for action in actions:
        refs.extend(
            str(ref)
            for ref in [
                action.get("item_ref"),
                action.get("approval_envelope_ref"),
                action.get("action_envelope_ref"),
                *(action.get("evidence_refs") or []),
                *(action.get("receipt_refs") or []),
            ]
            if ref
        )
    for plan in plans:
        refs.extend(
            str(ref)
            for ref in [plan.get("plan_ref"), *(plan.get("evidence_refs") or [])]
            if ref
        )
    for briefing in briefings:
        refs.extend(
            str(ref)
            for ref in [
                briefing.get("briefing_ref"),
                *(briefing.get("source_refs") or []),
                *(briefing.get("evidence_refs") or []),
            ]
            if ref
        )
    for receipt in turn_receipts:
        refs.extend(
            str(ref)
            for ref in [
                receipt.get("turn_ref"),
                receipt.get("receipt_ref"),
                receipt.get("evidence_ref"),
                *(receipt.get("evidence_refs") or []),
            ]
            if ref
        )
    for receipt in handoff_receipts:
        refs.extend(
            str(ref)
            for ref in [
                receipt.get("handoff_ref"),
                receipt.get("created_ref"),
                receipt.get("receipt_ref"),
                *(receipt.get("evidence_refs") or []),
            ]
            if ref
        )
    safe_refs: list[str] = []
    for ref in refs:
        try:
            validate_execution_ref(ref, "memory_workbench_loop_ref")
        except ValueError:
            continue
        safe_refs.append(ref)
    return list(dict.fromkeys(safe_refs))
