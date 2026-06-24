from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.enums import MemoryEpistemicRole
from ultimate_ai_agent.core.time import utc_now


MEMORY_FEEDBACK_CONTRACT_REF = "contract-ref:fcc-mem-022-feedback:v1"
MEMORY_FEEDBACK_ROUTE_REF = "POST /control-center/memory/feedback"
MEMORY_OBSERVATION_CANDIDATE_CONTRACT_REF = (
    "contract-ref:fcc-mem-022-observation-candidates:v1"
)
MEMORY_OBSERVATION_CANDIDATE_ROUTE_REF = (
    "GET /control-center/memory/observation-candidates"
)
MEMORY_PROBE_CONTRACT_REF = "contract-ref:fcc-mem-022-memory-probe:v1"
MEMORY_PROBE_ROUTE_REF = "GET /control-center/memory/probe"
MEMORY_CONTRADICTION_PREVIEW_CONTRACT_REF = (
    "contract-ref:fcc-mem-022-contradiction-previews:v1"
)
MEMORY_CONTRADICTION_PREVIEW_ROUTE_REF = "GET /control-center/memory/contradictions"
MEMORY_HRR_READINESS_CONTRACT_REF = "contract-ref:fcc-mem-hrr-001-readiness:v1"
MEMORY_HRR_REQUIRED_MILESTONE_REF = (
    "milestone-ref:fcc-mem-hrr-001-explicit-authority"
)

MEMORY_SAFE_QUERY_BLOCKED_STATE_REFS = [
    "blocked-state:memory-safe-query-no-raw-content-echo",
    "blocked-state:memory-safe-query-no-context-injection",
    "blocked-state:memory-safe-query-no-semantic-provider",
    "blocked-state:memory-safe-query-no-vector-db",
    "blocked-state:memory-safe-query-no-hrr-retrieval",
]
MEMORY_FEEDBACK_BLOCKED_STATE_REFS = [
    "blocked-state:memory-feedback-no-recall-record-create",
    "blocked-state:memory-feedback-no-delete-execution",
    "blocked-state:memory-feedback-no-export-execution",
    "blocked-state:memory-feedback-no-context-injection",
    "blocked-state:memory-feedback-no-action-execution",
    "blocked-state:memory-feedback-no-connector-write",
    "blocked-state:memory-feedback-no-provider-model-call",
    "blocked-state:memory-feedback-no-cloud-sync",
    "blocked-state:memory-feedback-no-production-authority",
]
MEMORY_OBSERVATION_BLOCKED_STATE_REFS = [
    "blocked-state:memory-observations-no-truth-authority",
    "blocked-state:memory-observations-no-automatic-opinion",
    "blocked-state:memory-observations-no-context-injection",
    "blocked-state:memory-observations-no-action-execution",
    "blocked-state:memory-observations-no-provider-model-call",
    "blocked-state:memory-observations-no-vector-db",
    "blocked-state:memory-observations-no-hrr-retrieval",
    "blocked-state:memory-observations-no-production-authority",
]
MEMORY_PROBE_BLOCKED_STATE_REFS = [
    "blocked-state:memory-probe-inspection-only",
    "blocked-state:memory-probe-no-context-injection",
    "blocked-state:memory-probe-no-action-execution",
    "blocked-state:memory-probe-no-connector-write",
    "blocked-state:memory-probe-no-provider-model-call",
    "blocked-state:memory-probe-no-vector-db",
    "blocked-state:memory-probe-no-hrr-retrieval",
    "blocked-state:memory-probe-no-production-authority",
]
MEMORY_CONTRADICTION_BLOCKED_STATE_REFS = [
    "blocked-state:memory-contradictions-preview-only",
    "blocked-state:memory-contradictions-no-auto-merge",
    "blocked-state:memory-contradictions-no-auto-forget",
    "blocked-state:memory-contradictions-no-truth-authority",
    "blocked-state:memory-contradictions-no-context-injection",
    "blocked-state:memory-contradictions-no-action-execution",
    "blocked-state:memory-contradictions-no-provider-model-call",
    "blocked-state:memory-contradictions-no-hrr-retrieval",
    "blocked-state:memory-contradictions-no-production-authority",
]
MEMORY_HRR_BLOCKED_STATE_REFS = [
    "blocked-state:memory-hrr-explicit-milestone-required",
    "blocked-state:memory-hrr-disabled-in-fcc-mem-022",
    "blocked-state:memory-hrr-no-algebraic-retrieval",
    "blocked-state:memory-hrr-no-ranking-influence",
    "blocked-state:memory-hrr-no-vector-db",
    "blocked-state:memory-hrr-no-embeddings-provider",
    "blocked-state:memory-hrr-no-raw-content-input",
    "blocked-state:memory-hrr-no-context-injection",
    "blocked-state:memory-hrr-no-action-execution",
    "blocked-state:memory-hrr-no-production-authority",
]

MemoryFeedbackKind = Literal[
    "helpful",
    "unhelpful",
    "stale",
    "conflict",
    "not_relevant",
]

_UNSAFE_TEXT_FRAGMENTS = (
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
    "credential",
    "private key",
    "api key",
    "authorization",
    "bearer",
    "cookie",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


def _safe_text(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} is required")
    validate_safe_execution_text(text, field_name)
    lowered = text.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe memory feature-mine text")
    return text


def _safe_ref(value: Any, field_name: str, *, allow_empty: bool = False) -> str | None:
    text = _safe_text(value, field_name, allow_empty=allow_empty)
    if not text:
        return None
    validate_execution_ref(text, field_name)
    return text


def _safe_refs(values: Iterable[Any] | None, field_name: str) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        ref = _safe_ref(value, field_name, allow_empty=True)
        if ref is not None:
            refs.append(ref)
    return list(dict.fromkeys(refs))


def short_digest(value: str, *, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:length]


def safe_query_ref_for_query(safe_query: str) -> str:
    query = _safe_text(safe_query, "safe_query")
    return f"safe-query-ref:fcc-mem-022:{short_digest(query, length=16)}"


def validate_query_mode(
    *,
    query_ref: str | None,
    safe_query: str | None,
) -> tuple[str | None, str | None, str]:
    if query_ref and safe_query:
        raise ValueError("query_ref and safe_query are mutually exclusive")
    if query_ref:
        return _safe_ref(query_ref, "query_ref"), None, "query_ref"
    if safe_query:
        return None, safe_query_ref_for_query(safe_query), "safe_query"
    return None, None, "default"


def memory_hrr_readiness() -> dict[str, Any]:
    return {
        "schema_version": "fcc_mem_hrr_001_readiness.v1",
        "contract_ref": MEMORY_HRR_READINESS_CONTRACT_REF,
        "status": "blocked_pending_explicit_milestone",
        "required_milestone_ref": MEMORY_HRR_REQUIRED_MILESTONE_REF,
        "hrr_enabled": False,
        "algebraic_retrieval_enabled": False,
        "ranking_influence_enabled": False,
        "shadow_mode_enabled": False,
        "raw_content_input_enabled": False,
        "embedding_provider_enabled": False,
        "vector_db_enabled": False,
        "context_injection_authorized": False,
        "action_execution_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_HRR_BLOCKED_STATE_REFS),
    }


def memory_feature_flags() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "raw_content_stored": False,
        "context_injection_authorized": False,
        "automatic_recall_authorized": False,
        "automatic_memory_write_authorized": False,
        "truth_authority_enabled": False,
        "approval_authority_granted": False,
        "connector_write_authorized": False,
        "external_crm_sync_authorized": False,
        "automatic_action_execution_authorized": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
        "embedding_index_enabled": False,
        "vector_db_enabled": False,
        "semantic_search_enabled": False,
        "hrr_enabled": False,
        "algebraic_retrieval_enabled": False,
    }


class MemoryFeedbackRequest(BaseModel):
    memory_record_ref: str = Field(..., min_length=1, max_length=220)
    feedback_kind: MemoryFeedbackKind
    reviewer_ref: str = Field(
        default="actor-ref:local-operator",
        min_length=1,
        max_length=220,
    )
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    note_ref: str | None = Field(default=None, max_length=220)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_FEEDBACK_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "MemoryFeedbackRequest":
        _safe_ref(self.memory_record_ref, "memory_record_ref")
        if not self.memory_record_ref.startswith("memory-record-ref:"):
            raise ValueError("memory_record_ref must identify a reviewed recall record")
        _safe_text(self.feedback_kind, "feedback_kind")
        _safe_ref(self.reviewer_ref, "reviewer_ref")
        self.source_refs = _safe_refs(self.source_refs, "source_refs")
        self.evidence_refs = _safe_refs(self.evidence_refs, "evidence_refs")
        self.blocked_state_refs = _safe_refs(
            self.blocked_state_refs,
            "blocked_state_refs",
        )
        if self.note_ref is not None:
            self.note_ref = _safe_ref(self.note_ref, "note_ref")
        missing = [
            ref
            for ref in MEMORY_FEEDBACK_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing:
            raise ValueError("memory feedback request missing blocked state refs")
        if not self.source_refs or not self.evidence_refs:
            raise ValueError("memory feedback requires source and evidence refs")
        return self


class MemoryFeedbackReceipt(BaseModel):
    schema_version: str = "fcc_mem_022_memory_feedback_receipt.v1"
    contract_ref: str = MEMORY_FEEDBACK_CONTRACT_REF
    route_ref: str = MEMORY_FEEDBACK_ROUTE_REF
    receipt_ref: str
    memory_record_ref: str
    feedback_kind: MemoryFeedbackKind
    reviewer_ref: str
    idempotency_key_ref: str
    payload_fingerprint_ref: str
    approval_ref: str
    approval_status: str
    approval_reason_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    note_ref: str | None = None
    trust_delta: float = 0.0
    trust_score_after: float
    stale_state_after: str
    conflict_state_after: str
    blocked_state_refs: list[str] = Field(default_factory=list)
    receipt_recorded: bool = True
    reviewed_recall_record_created: bool = False
    memory_delete_performed: bool = False
    memory_export_performed: bool = False
    context_injection_authorized: bool = False
    connector_write_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    production_authority_enabled: bool = False
    replayed: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    model_config = ConfigDict(extra="forbid")


def memory_feedback_payload_for_fingerprint(
    request: MemoryFeedbackRequest,
) -> dict[str, Any]:
    return {
        "memory_record_ref": request.memory_record_ref,
        "feedback_kind": request.feedback_kind,
        "reviewer_ref": request.reviewer_ref,
        "source_refs": list(request.source_refs),
        "evidence_refs": list(request.evidence_refs),
        "note_ref": request.note_ref,
        "blocked_state_refs": list(request.blocked_state_refs),
    }


def memory_feedback_payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"payload-fingerprint:memory-feedback:{short_digest(encoded, length=24)}"


def memory_feedback_receipt_ref(
    memory_record_ref: str,
    idempotency_key_ref: str,
) -> str:
    _safe_ref(memory_record_ref, "memory_record_ref")
    _safe_ref(idempotency_key_ref, "idempotency_key_ref")
    return (
        "receipt:memory-feedback:"
        f"{short_digest(memory_record_ref, length=10)}:"
        f"{short_digest(idempotency_key_ref, length=10)}"
    )


def trust_delta_for_feedback(feedback_kind: str) -> float:
    if feedback_kind == "helpful":
        return 0.05
    if feedback_kind in {"unhelpful", "not_relevant"}:
        return -0.10
    return 0.0


def epistemic_role_for_candidate_kind(candidate_kind: str) -> MemoryEpistemicRole:
    normalized = str(candidate_kind or "").strip().lower().replace("-", "_")
    if normalized in {"profile", "profiles", "project", "projects", "organization", "organizations", "deal", "deals"}:
        return MemoryEpistemicRole.world_fact
    if normalized in {
        "decision",
        "decisions",
        "promise",
        "promises",
        "follow_up",
        "follow_ups",
        "followup",
        "followups",
        "commitment",
        "commitments",
    }:
        return MemoryEpistemicRole.experience_fact
    if normalized in {"preference", "preferences", "relationship", "relationships"}:
        return MemoryEpistemicRole.observation
    return MemoryEpistemicRole.unknown


def bounded_observation_summary(role: str, proof_count: int) -> str:
    safe_role = _safe_text(role or "unknown", "epistemic_role")
    return (
        f"Observation candidate for {safe_role} refs supported by "
        f"{max(0, int(proof_count))} reviewed records."
    )


def refs_intersect(entity_ref: str, *groups: Iterable[str]) -> bool:
    _safe_ref(entity_ref, "entity_ref")
    for group in groups:
        if entity_ref in {str(ref) for ref in group}:
            return True
    return False


__all__ = [
    "MEMORY_CONTRADICTION_BLOCKED_STATE_REFS",
    "MEMORY_CONTRADICTION_PREVIEW_CONTRACT_REF",
    "MEMORY_CONTRADICTION_PREVIEW_ROUTE_REF",
    "MEMORY_FEEDBACK_BLOCKED_STATE_REFS",
    "MEMORY_FEEDBACK_CONTRACT_REF",
    "MEMORY_FEEDBACK_ROUTE_REF",
    "MEMORY_HRR_BLOCKED_STATE_REFS",
    "MEMORY_HRR_READINESS_CONTRACT_REF",
    "MEMORY_HRR_REQUIRED_MILESTONE_REF",
    "MEMORY_OBSERVATION_BLOCKED_STATE_REFS",
    "MEMORY_OBSERVATION_CANDIDATE_CONTRACT_REF",
    "MEMORY_OBSERVATION_CANDIDATE_ROUTE_REF",
    "MEMORY_PROBE_BLOCKED_STATE_REFS",
    "MEMORY_PROBE_CONTRACT_REF",
    "MEMORY_PROBE_ROUTE_REF",
    "MEMORY_SAFE_QUERY_BLOCKED_STATE_REFS",
    "MemoryFeedbackKind",
    "MemoryFeedbackReceipt",
    "MemoryFeedbackRequest",
    "bounded_observation_summary",
    "epistemic_role_for_candidate_kind",
    "memory_feature_flags",
    "memory_feedback_payload_fingerprint_ref",
    "memory_feedback_payload_for_fingerprint",
    "memory_feedback_receipt_ref",
    "memory_hrr_readiness",
    "refs_intersect",
    "safe_query_ref_for_query",
    "short_digest",
    "trust_delta_for_feedback",
    "validate_query_mode",
]
