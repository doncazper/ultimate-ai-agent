import uuid
from datetime import datetime
from typing import Dict, List, Optional

from ultimate_ai_agent.core.memory.decisions import MemoryReadDecision, MemorySearchResult, MemoryWriteDecision
from ultimate_ai_agent.core.memory.enums import MemorySensitivity, MemoryStatus, MemoryWriteDisposition
from ultimate_ai_agent.core.memory.policies import MemoryRetrievalPolicy
from ultimate_ai_agent.core.memory.records import MemoryRecord
from ultimate_ai_agent.core.memory.requests import MemoryReadRequest, MemoryWriteRequest
from ultimate_ai_agent.core.memory.retrieval import score_memory
from ultimate_ai_agent.core.memory.validation import validate_memory_record


SENSITIVE_REQUIRES_CONSENT = {
    MemorySensitivity.sensitive_personal,
    MemorySensitivity.regulated,
    MemorySensitivity.third_party_confidential,
    MemorySensitivity.tcb_protected,
}


class MemoryStore:
    """Local/dev-only in-memory memory store."""

    def __init__(self):
        self._records: Dict[str, MemoryRecord] = {}
        self._idempotency: Dict[str, str] = {}

    def add_memory(self, record: MemoryRecord) -> MemoryRecord:
        validate_memory_record(record)
        self._records[record.memory_id] = record
        return record

    def write_memory(self, request: MemoryWriteRequest) -> MemoryWriteDecision:
        if not request.idempotency_key:
            return self._write_denied(request, ["IDEMPOTENCY_KEY_REQUIRED"], "Memory writes require idempotency_key.")
        if request.idempotency_key in self._idempotency:
            memory_id = self._idempotency[request.idempotency_key]
            return MemoryWriteDecision(
                decision_id=f"mwd_{uuid.uuid4().hex[:8]}",
                request_id=request.request_id,
                disposition=MemoryWriteDisposition.retain,
                allowed=True,
                reason_codes=["IDEMPOTENT_REPLAY"],
                safe_message="Memory write already retained for this idempotency key.",
                memory_id=memory_id,
                event_ref=request.event_ref,
            )
        if request.sensitivity == MemorySensitivity.credential_secret:
            return self._write_denied(request, ["CREDENTIAL_SECRET_REJECTED"], "Credential secrets cannot be stored in memory.")
        if request.sensitivity in SENSITIVE_REQUIRES_CONSENT and not request.consent_ref:
            return self._write_denied(request, ["CONSENT_REQUIRED"], "Sensitive memory writes require consent.")

        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        try:
            record = MemoryRecord(
                memory_id=memory_id,
                memory_type=request.memory_type,
                scope=request.scope,
                scope_id=request.scope_id,
                user_id=request.user_id,
                project_id=request.project_id,
                authority=request.authority,
                sensitivity=request.sensitivity,
                content=request.content,
                summary=request.summary,
                tags=request.tags,
                source_refs=request.source_refs,
                supersedes=request.proposed_supersedes,
                event_ref=request.event_ref,
                created_at=request.created_at,
            )
            validate_memory_record(record)
        except ValueError as exc:
            reason = "SOURCE_REF_REQUIRED" if "source_refs" in str(exc) else "MEMORY_VALIDATION_FAILED"
            return self._write_denied(request, [reason], str(exc))

        self._records[memory_id] = record
        self._idempotency[request.idempotency_key] = memory_id
        return MemoryWriteDecision(
            decision_id=f"mwd_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            disposition=MemoryWriteDisposition.retain,
            allowed=True,
            reason_codes=["MEMORY_RETAINED"],
            safe_message="Memory retained as source-scoped recall, not authority.",
            memory_id=memory_id,
            event_ref=request.event_ref,
        )

    def get_memory(self, memory_id: Optional[str]) -> Optional[MemoryRecord]:
        if memory_id is None:
            return None
        return self._records.get(memory_id)

    def list_memories(
        self,
        scope=None,
        scope_id: Optional[str] = None,
        memory_type=None,
        status=None,
    ) -> List[MemoryRecord]:
        records = list(self._records.values())
        if scope is not None:
            records = [record for record in records if record.scope == scope]
        if scope_id is not None:
            records = [record for record in records if record.scope_id == scope_id]
        if memory_type is not None:
            records = [record for record in records if record.memory_type == memory_type]
        if status is not None:
            records = [record for record in records if record.status == status]
        return records

    def search(self, request: MemoryReadRequest, policy: Optional[MemoryRetrievalPolicy] = None) -> MemoryReadDecision:
        policy = policy or MemoryRetrievalPolicy(max_results=request.max_results)
        if request.scope in ["user", "organization"] and not request.consent_ref and policy.require_consent_for_sensitive:
            return MemoryReadDecision(
                decision_id=f"mrd_{uuid.uuid4().hex[:8]}",
                request_id=request.request_id,
                allowed=False,
                reason_codes=["CONSENT_REQUIRED"],
                safe_message="Sensitive memory scopes require consent.",
            )

        results = []
        for record in self._records.values():
            if record.scope != request.scope:
                continue
            if request.scope_id and record.scope_id != request.scope_id:
                continue
            if request.memory_types and record.memory_type not in request.memory_types:
                continue
            if record.status in [MemoryStatus.deleted, MemoryStatus.revoked]:
                continue
            if not request.include_superseded and record.status in policy.exclude_statuses:
                continue
            if record.sensitivity not in policy.include_sensitivity_levels:
                continue
            if record.sensitivity in SENSITIVE_REQUIRES_CONSENT and not request.consent_ref:
                continue
            score, reasons = score_memory(record, request.query, request.tags)
            if request.query or request.tags:
                if score <= 0:
                    continue
            else:
                score = 1.0
                reasons = ["recent"]
            results.append(
                MemorySearchResult(
                    memory_id=record.memory_id,
                    score=score,
                    match_reasons=reasons,
                    record_summary=record.summary or record.content,
                    source_refs=record.source_refs,
                    sensitivity=record.sensitivity,
                    status=record.status,
                )
            )

        limit = min(request.max_results, policy.max_results)
        results.sort(key=lambda item: (-item.score, item.memory_id))
        return MemoryReadDecision(
            decision_id=f"mrd_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            allowed=True,
            results=results[:limit],
            reason_codes=["MEMORY_QUERY_PREVIEWED"],
            safe_message="Memory results are recall only; canonical sources outrank memory.",
            event_ref=request.event_ref if hasattr(request, "event_ref") else None,
        )

    def supersede_memory(self, old_memory_id: str, new_record: MemoryRecord, reason: str) -> MemoryRecord:
        old = self._records[old_memory_id]
        new_record.supersedes.append(old_memory_id)
        new_record.metadata["supersession_reason"] = reason
        self.add_memory(new_record)
        old.status = MemoryStatus.superseded
        old.superseded_by = new_record.memory_id
        old.updated_at = datetime.utcnow()
        return new_record

    def correct_memory(self, old_memory_id: str, corrected_record: MemoryRecord, reason: str) -> MemoryRecord:
        old = self._records[old_memory_id]
        corrected_record.correction_of = old_memory_id
        corrected_record.supersedes.append(old_memory_id)
        corrected_record.metadata["correction_reason"] = reason
        self.add_memory(corrected_record)
        old.status = MemoryStatus.corrected
        old.superseded_by = corrected_record.memory_id
        old.updated_at = datetime.utcnow()
        return corrected_record

    def delete_memory(self, memory_id: str, deletion_ref: str, reason: str) -> MemoryRecord:
        record = self._records[memory_id]
        record.status = MemoryStatus.deleted
        record.deletion_ref = deletion_ref
        record.metadata["deletion_reason"] = reason
        record.updated_at = datetime.utcnow()
        return record

    def quarantine_memory(self, memory_id: str, reason: str) -> MemoryRecord:
        record = self._records[memory_id]
        record.status = MemoryStatus.quarantined
        record.metadata["quarantine_reason"] = reason
        record.updated_at = datetime.utcnow()
        return record

    def _write_denied(self, request: MemoryWriteRequest, reason_codes: List[str], safe_message: str) -> MemoryWriteDecision:
        return MemoryWriteDecision(
            decision_id=f"mwd_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            disposition=MemoryWriteDisposition.reject,
            allowed=False,
            reason_codes=reason_codes,
            safe_message=safe_message,
            event_ref=request.event_ref,
        )
