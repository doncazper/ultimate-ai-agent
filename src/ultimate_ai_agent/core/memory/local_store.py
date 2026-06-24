import copy
import json
from pathlib import Path
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthorityLevel,
    MemoryConflictState,
    MemoryLayer,
    MemoryProviderKind,
    MemoryRetentionState,
    MemoryReviewState,
    MemorySourcePriority,
    MemoryStatus,
    MemoryWriteDecisionStatus,
)
from ultimate_ai_agent.core.memory.manifests import MemoryProviderManifest, build_default_memory_provider_manifest
from ultimate_ai_agent.core.memory.provider import (
    MemoryDeleteRequest,
    MemoryExportRequest,
    MemoryProvider,
    MemoryProviderWriteRequest,
    build_memory_export_decision,
    build_memory_write_decision,
)
from ultimate_ai_agent.core.memory.records import MemoryLifecycleMetadata, MemoryProvenance, MemoryRecallMetadata, MemoryRecord, MemorySourceRef
from ultimate_ai_agent.core.memory.validation import validate_memory_export_request, validate_memory_record, validate_memory_write_request
from ultimate_ai_agent.core.time import utc_now


class LocalMemoryStore(MemoryProvider):
    """Stdlib-only local/dev memory store for reviewed recall records."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else None
        self._records: Dict[str, MemoryRecord] = {}
        provider_kind = MemoryProviderKind.local_sqlite if self.storage_path else MemoryProviderKind.local_in_memory
        self.manifest: MemoryProviderManifest = build_default_memory_provider_manifest(
            baseline_version=__version__,
            provider_kind=provider_kind,
        )
        self._conn: Optional[sqlite3.Connection] = None
        if self.storage_path is not None:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.storage_path)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    memory_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def put_record(self, request: MemoryProviderWriteRequest) -> Any:
        if not isinstance(request, MemoryProviderWriteRequest):
            raise TypeError("LocalMemoryStore.put_record requires the M24 provider/store MemoryWriteRequest.")
        decision = validate_memory_write_request(request)
        if not decision.allowed:
            return decision

        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        provider_kind = MemoryProviderKind.local_sqlite if self.storage_path else MemoryProviderKind.local_in_memory
        source_refs = [
            MemorySourceRef(
                source_ref=source_ref,
                source_kind="reviewed_memory_source",
                source_priority=MemorySourcePriority.user_reviewed_source,
            )
            for source_ref in request.source_refs
        ]
        provenance = MemoryProvenance(
            provenance_id=f"prov_{uuid.uuid4().hex[:10]}",
            source_refs=source_refs,
            reviewed_by_ref="user_reviewed_m24_contract",
            review_state=MemoryReviewState.user_reviewed,
            evidence_refs=request.evidence_refs,
            event_refs=request.event_refs,
            receipt_refs=request.receipt_refs,
            source_priority=MemorySourcePriority.user_reviewed_source,
        )
        record = MemoryRecord(
            memory_id=memory_id,
            memory_kind=request.memory_kind,
            memory_layer=MemoryLayer.record,
            provider_kind=provider_kind,
            review_state=MemoryReviewState.user_reviewed,
            authority_level=MemoryAuthorityLevel.recall_only,
            source_priority=MemorySourcePriority.user_reviewed_source,
            data_classification=request.data_classification,
            safe_summary=request.safe_summary,
            provenance=provenance,
            source_refs=source_refs,
            evidence_refs=request.evidence_refs,
            event_refs=request.event_refs,
            receipt_refs=request.receipt_refs,
            file_refs=request.file_refs,
            confidence_score=request.confidence_score,
            trust_score=request.trust_score,
            recall_metadata=MemoryRecallMetadata(
                recall_id=f"recall_{uuid.uuid4().hex[:10]}",
                context_pack_eligible=request.context_pack_eligible,
                injection_priority=request.injection_priority,
            ),
            lifecycle=MemoryLifecycleMetadata(dedup_key=request.dedup_key),
            retention_state=MemoryRetentionState.active,
            conflict_state=MemoryConflictState.none,
            stale_state=MemoryConflictState.none,
            tags=request.tags,
            metadata_refs=request.metadata_refs,
            metadata=request.metadata,
            created_at=request.created_at,
        )
        validate_memory_record(record)
        self._save(record)
        return build_memory_write_decision(
            request_id=request.request_id,
            allowed=True,
            status=MemoryWriteDecisionStatus.allowed_for_local_store,
            reason_codes=["MEMORY_RECALL_NOT_AUTHORITY", "REVIEWED_SOURCE_LINKED_MEMORY_STORED"],
            safe_message="Reviewed memory retained locally as recall, not authority.",
            memory_id=memory_id,
        )

    def get_record(self, memory_id: str) -> Optional[MemoryRecord]:
        if self._conn is None:
            record = self._records.get(memory_id)
            return copy.deepcopy(record) if record is not None else None
        row = self._conn.execute("SELECT payload_json FROM memory_records WHERE memory_id = ?", (memory_id,)).fetchone()
        if row is None:
            return None
        return MemoryRecord(**json.loads(row[0]))

    def list_records(self) -> List[MemoryRecord]:
        if self._conn is None:
            return [copy.deepcopy(record) for record in self._records.values()]
        rows = self._conn.execute("SELECT payload_json FROM memory_records ORDER BY memory_id").fetchall()
        return [MemoryRecord(**json.loads(row[0])) for row in rows]

    def mark_deleted(self, request: MemoryDeleteRequest) -> MemoryRecord:
        record = self.get_record(request.memory_id)
        if record is None:
            raise KeyError(request.memory_id)
        record.status = MemoryStatus.deleted
        record.retention_state = MemoryRetentionState.deleted
        record.deletion_ref = request.request_id
        record.updated_at = utc_now()
        record.metadata["deletion_reason"] = request.reason
        record.metadata["user_requested_delete"] = request.user_requested
        self._save(record)
        return record

    def suppress_record(
        self,
        *,
        memory_id: str,
        receipt_ref: str,
        reason: str,
        status: MemoryStatus = MemoryStatus.revoked,
        retention_state: MemoryRetentionState = MemoryRetentionState.blocked,
    ) -> MemoryRecord:
        record = self.get_record(memory_id)
        if record is None:
            raise KeyError(memory_id)
        record.status = status
        record.retention_state = retention_state
        record.conflict_state = MemoryConflictState.superseded
        record.stale_state = MemoryConflictState.stale
        record.updated_at = utc_now()
        if receipt_ref not in record.receipt_refs:
            record.receipt_refs.append(receipt_ref)
        record.metadata["suppression_receipt_ref"] = receipt_ref
        record.metadata["suppression_reason"] = reason
        record.metadata["recall_projection_suppressed"] = True
        if record.lifecycle is not None:
            record.lifecycle.retention_state = retention_state
            record.lifecycle.conflict_state = MemoryConflictState.superseded
            record.lifecycle.stale_state = MemoryConflictState.stale
            record.lifecycle.metadata["suppression_receipt_ref"] = receipt_ref
            record.lifecycle.metadata["suppression_reason"] = reason
        self._save(record)
        return record

    def export_records(self, request: MemoryExportRequest) -> Any:
        decision = validate_memory_export_request(request)
        if not decision.allowed:
            return decision
        records = [
            record
            for record in self.list_records()
            if request.include_deleted or record.retention_state != MemoryRetentionState.deleted
        ]
        safe_records = [
            {
                "memory_id": record.memory_id,
                "memory_kind": record.memory_kind,
                "review_state": record.review_state,
                "authority_level": record.authority_level,
                "source_priority": record.source_priority,
                "safe_summary": record.safe_summary,
                "evidence_refs": record.evidence_refs,
                "event_refs": record.event_refs,
                "receipt_refs": record.receipt_refs,
                "file_refs": record.file_refs,
                "data_classification": record.data_classification,
                "retention_state": record.retention_state,
                "redaction_status": record.redaction_status,
                "confidence_score": record.confidence_score,
                "trust_score": record.trust_score,
            }
            for record in records
        ]
        return build_memory_export_decision(
            request_id=request.request_id,
            allowed=True,
            status=MemoryWriteDecisionStatus.allowed_for_local_store,
            reason_codes=["REDACTED_MEMORY_EXPORT_ALLOWED"],
            safe_message="Memory export is redacted-summary-only.",
            records=safe_records,
        )

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _save(self, record: MemoryRecord) -> None:
        if self._conn is None:
            self._records[record.memory_id] = record
            return
        payload = json.dumps(record.model_dump(mode="json"), sort_keys=True)
        self._conn.execute(
            "INSERT OR REPLACE INTO memory_records (memory_id, payload_json, updated_at) VALUES (?, ?, ?)",
            (record.memory_id, payload, utc_now().isoformat()),
        )
        self._conn.commit()
