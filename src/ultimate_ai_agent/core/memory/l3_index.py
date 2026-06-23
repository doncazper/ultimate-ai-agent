from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.l2_index import (
    L2FactualGraphTemporalIndex,
    L2MemoryFactItem,
    L2MemoryGraphRelation,
    L2MemoryTemporalItem,
)
from ultimate_ai_agent.core.time import utc_now


L3_IDENTITY_SESSION_MODELING_CONTRACT_REF = (
    "contract-ref:governed-cognitive-memory-spine:l3-identity-session-modeling:v1"
)
L3_IDENTITY_SESSION_MODELING_ROUTE_REF = "GET /control-center/memory/l3-index"
L3_IDENTITY_SESSION_MODELING_STATUS = "implemented_read_only_representation_proposals"
L3_IDENTITY_SESSION_MODELING_BLOCKED_STATE_REFS = (
    "blocked-state:l3-memory-no-truth-authority",
    "blocked-state:l3-memory-no-approval-authority",
    "blocked-state:l3-memory-no-action-execution",
    "blocked-state:l3-memory-no-connector-writes",
    "blocked-state:l3-memory-no-crm-sync",
    "blocked-state:l3-memory-no-account-sync",
    "blocked-state:l3-memory-no-hidden-context-injection",
    "blocked-state:l3-memory-no-automatic-memory-writes",
    "blocked-state:l3-memory-no-provider-or-model-calls",
    "blocked-state:l3-memory-no-llm-extraction",
    "blocked-state:l3-memory-no-embeddings",
    "blocked-state:l3-memory-no-vector-db",
    "blocked-state:l3-memory-no-semantic-search",
    "blocked-state:l3-memory-no-background-indexing",
    "blocked-state:l3-memory-no-context-pack-injection",
    "blocked-state:l3-memory-phase5-context-packs-not-implemented",
    "blocked-state:l3-memory-phase6-execution-hooks-future-blocked",
    "blocked-state:l3-memory-no-production-authority",
)

L3MemoryKind = Literal[
    "identity",
    "session",
    "preference",
    "commitment",
    "relationship",
    "workspace",
    "peer",
    "representation",
]

L3DerivationReasonRef = Literal[
    "derivation-reason-ref:l3-derived-from-reviewed-l2-safe-ref-projection",
    "derivation-reason-ref:l3-source-evidence-receipt-refs-preserved",
    "derivation-reason-ref:l3-representation-proposal-only",
    "derivation-reason-ref:l3-no-truth-authority",
    "derivation-reason-ref:l3-no-hidden-context-injection",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw-prompt",
    "raw response",
    "raw_response",
    "raw-response",
    "provider payload",
    "provider_payload",
    "provider-payload",
    "raw provider",
    "raw_provider",
    "raw-provider",
    "raw transcript",
    "raw_transcript",
    "raw-transcript",
    "raw source",
    "raw_source",
    "raw-source",
    "raw file",
    "raw_file",
    "raw-file",
    "raw path",
    "raw_path",
    "raw-path",
    "raw log",
    "raw_log",
    "raw-log",
    "private ui content",
    "private_ui_content",
    "private-ui-content",
    "username",
    "username:",
    "hostname",
    "hostname:",
    "credential",
    "credential material",
    "credential_material",
    "credential-material",
    "password",
    "secret",
    "api key",
    "api_key",
    "token",
    "raw private content",
    "raw_private_content",
    "raw-private-content",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)

_DENIED_AUTHORITY_FLAGS = (
    "truth_authority_enabled",
    "crm_truth_authority_enabled",
    "context_injection_authorized",
    "automatic_recall_authorized",
    "automatic_memory_write_authorized",
    "approval_authority_granted",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "automatic_action_execution_authorized",
    "model_provider_authority_allowed",
    "production_authority_enabled",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "llm_extraction_enabled",
    "background_indexing_enabled",
    "context_pack_injection_authorized",
    "phase5_context_pack_proposals_enabled",
    "phase6_execution_hooks_enabled",
    "raw_content_stored",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe L3 memory content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _validate_safe_text(value, field_name)


def _safe_suffix(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _unique_refs(*groups: Iterable[str]) -> list[str]:
    refs: list[str] = []
    for group in groups:
        for ref in group:
            _validate_safe_ref(ref, "supporting_refs")
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _state_ref(prefix: str, value: str) -> str:
    safe = str(value or "none").strip().lower().replace("_", "-")
    safe = "".join(char if char.isalnum() or char in ".-" else "-" for char in safe)
    safe = "-".join(part for part in safe.split("-") if part) or "none"
    ref = f"{prefix}:{safe}"
    _validate_safe_ref(ref, prefix)
    return ref


class _L3AuthorityPosture(BaseModel):
    truth_authority_enabled: bool = False
    crm_truth_authority_enabled: bool = False
    context_injection_authorized: bool = False
    automatic_recall_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    approval_authority_granted: bool = False
    connector_write_authorized: bool = False
    external_crm_sync_authorized: bool = False
    account_sync_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    model_provider_authority_allowed: bool = False
    production_authority_enabled: bool = False
    embedding_index_enabled: bool = False
    vector_db_enabled: bool = False
    semantic_search_enabled: bool = False
    llm_extraction_enabled: bool = False
    background_indexing_enabled: bool = False
    context_pack_injection_authorized: bool = False
    phase5_context_pack_proposals_enabled: bool = False
    phase6_execution_hooks_enabled: bool = False
    raw_content_stored: bool = False


class L3MemoryModelItem(_L3AuthorityPosture):
    contract_ref: str = L3_IDENTITY_SESSION_MODELING_CONTRACT_REF
    l3_item_ref: str = Field(..., min_length=1)
    l3_kind: L3MemoryKind
    subject_ref: str = Field(..., min_length=1)
    workspace_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_summary_ref: str = Field(..., min_length=1)
    supporting_memory_record_refs: list[str] = Field(default_factory=list)
    supporting_l1_preview_refs: list[str] = Field(default_factory=list)
    supporting_l2_item_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    derivation_reason_refs: list[L3DerivationReasonRef] = Field(default_factory=list)
    confidence_posture: str = "confidence-posture:l3-review-required"
    stale_state_refs: list[str] = Field(default_factory=list)
    conflict_state_refs: list[str] = Field(default_factory=list)
    review_required: bool = True
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L3_IDENTITY_SESSION_MODELING_BLOCKED_STATE_REFS)
    )
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_l3_item(self) -> "L3MemoryModelItem":
        for field_name in [
            "contract_ref",
            "l3_item_ref",
            "subject_ref",
            "workspace_ref",
            "session_ref",
            "safe_summary_ref",
            "confidence_posture",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.l3_kind, "l3_kind")
        for field_name in [
            "supporting_memory_record_refs",
            "supporting_l1_preview_refs",
            "supporting_l2_item_refs",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "derivation_reason_refs",
            "stale_state_refs",
            "conflict_state_refs",
            "blocked_state_refs",
        ]:
            refs = getattr(self, field_name)
            for ref in refs:
                _validate_safe_ref(str(ref), field_name)
        for field_name in [
            "supporting_memory_record_refs",
            "supporting_l1_preview_refs",
            "supporting_l2_item_refs",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "derivation_reason_refs",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required for L3 memory items")
        if not self.review_required:
            raise ValueError("L3 memory items must remain review-required")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for L3 memory items")
        return self


class L3IdentitySessionPreferenceIndex(_L3AuthorityPosture):
    contract_ref: str = L3_IDENTITY_SESSION_MODELING_CONTRACT_REF
    route_ref: str = L3_IDENTITY_SESSION_MODELING_ROUTE_REF
    status: str = L3_IDENTITY_SESSION_MODELING_STATUS
    source_l2_contract_ref: str
    source_l2_route_ref: str
    query_ref: str | None = None
    generated_at: datetime = Field(default_factory=utc_now)
    source_l2_fact_count: int = Field(default=0, ge=0)
    source_l2_relation_count: int = Field(default=0, ge=0)
    source_l2_temporal_count: int = Field(default=0, ge=0)
    item_count: int = Field(default=0, ge=0)
    items: list[L3MemoryModelItem] = Field(default_factory=list)
    skipped_l2_item_refs: list[str] = Field(default_factory=list)
    skipped_l2_item_count: int = Field(default=0, ge=0)
    safe_refs_only: bool = True
    representation_proposal_only: bool = True
    deterministic_projection_only: bool = True
    semantic_extraction_used: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L3_IDENTITY_SESSION_MODELING_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_l3_index(self) -> "L3IdentitySessionPreferenceIndex":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.route_ref, "route_ref")
        _validate_safe_text(self.status, "status")
        _validate_safe_ref(self.source_l2_contract_ref, "source_l2_contract_ref")
        _validate_safe_text(self.source_l2_route_ref, "source_l2_route_ref")
        if self.query_ref is not None:
            _validate_safe_ref(self.query_ref, "query_ref")
        for ref in self.skipped_l2_item_refs:
            _validate_safe_ref(ref, "skipped_l2_item_refs")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for L3 memory index")
        if not self.safe_refs_only:
            raise ValueError("L3 memory index must remain safe-ref-only")
        if not self.representation_proposal_only:
            raise ValueError("L3 memory index must remain proposal-only")
        if not self.deterministic_projection_only:
            raise ValueError("L3 memory index must remain deterministic projection only")
        if self.semantic_extraction_used:
            raise ValueError("L3 memory index must not use semantic extraction")
        if self.item_count != len(self.items):
            raise ValueError("item_count must match items")
        if self.skipped_l2_item_count != len(self.skipped_l2_item_refs):
            raise ValueError("skipped_l2_item_count must match skipped refs")
        return self


def build_l3_identity_session_preference_index(
    l2_index: L2FactualGraphTemporalIndex | dict[str, Any],
    *,
    query_ref: str | None = None,
    limit: int = 20,
) -> L3IdentitySessionPreferenceIndex:
    source_index = (
        l2_index
        if isinstance(l2_index, L2FactualGraphTemporalIndex)
        else L2FactualGraphTemporalIndex(**l2_index)
    )
    if query_ref is not None:
        _validate_safe_ref(query_ref, "query_ref")

    relation_by_memory_ref = {
        relation.memory_record_ref: relation
        for relation in source_index.graph_relations
    }
    temporal_by_memory_ref = {
        temporal.memory_record_ref: temporal
        for temporal in source_index.temporal_items
    }
    items: list[L3MemoryModelItem] = []
    skipped_refs: list[str] = []
    for fact in source_index.facts[: max(1, min(int(limit), 50))]:
        try:
            relation = relation_by_memory_ref[fact.memory_record_ref]
            temporal = temporal_by_memory_ref[fact.memory_record_ref]
            item = _item_for_fact_relation_temporal(fact, relation, temporal)
        except (KeyError, ValueError):
            skipped_refs.append(getattr(fact, "fact_ref", "l2-item-ref:unsafe-blocked"))
            continue
        items.append(item)

    skipped_refs.extend(source_index.skipped_l1_preview_refs)
    skipped_refs = list(dict.fromkeys(skipped_refs))
    return L3IdentitySessionPreferenceIndex(
        source_l2_contract_ref=source_index.contract_ref,
        source_l2_route_ref=source_index.route_ref,
        query_ref=query_ref or source_index.query_ref,
        source_l2_fact_count=source_index.fact_count,
        source_l2_relation_count=source_index.relation_count,
        source_l2_temporal_count=source_index.temporal_count,
        item_count=len(items),
        items=items,
        skipped_l2_item_refs=skipped_refs,
        skipped_l2_item_count=len(skipped_refs),
    )


def _item_for_fact_relation_temporal(
    fact: L2MemoryFactItem,
    relation: L2MemoryGraphRelation,
    temporal: L2MemoryTemporalItem,
) -> L3MemoryModelItem:
    fact = L2MemoryFactItem(**fact.model_dump(mode="python"))
    relation = L2MemoryGraphRelation(**relation.model_dump(mode="python"))
    temporal = L2MemoryTemporalItem(**temporal.model_dump(mode="python"))
    if fact.memory_record_ref != relation.memory_record_ref:
        raise ValueError("L3 relation must match fact memory record ref")
    if fact.memory_record_ref != temporal.memory_record_ref:
        raise ValueError("L3 temporal item must match fact memory record ref")
    l3_kind = _kind_for_refs([*fact.tag_refs, *fact.metadata_refs, fact.fact_kind])
    suffix = _safe_suffix(fact.fact_ref, relation.relation_ref, temporal.temporal_ref)
    source_refs = _unique_refs(fact.source_refs, relation.source_refs, temporal.source_refs)
    evidence_refs = _unique_refs(
        fact.evidence_refs,
        relation.evidence_refs,
        temporal.evidence_refs,
    )
    receipt_refs = _unique_refs(fact.receipt_refs, relation.receipt_refs, temporal.receipt_refs)
    l2_refs = _unique_refs(
        [fact.fact_ref],
        [relation.relation_ref],
        [temporal.temporal_ref],
    )
    memory_record_refs = _unique_refs([fact.memory_record_ref])
    l1_preview_refs = [f"l1-preview-ref:{_safe_suffix(fact.memory_record_ref)}"]
    subject_ref = fact.fact_subject_ref
    workspace_ref = _workspace_ref(fact)
    session_ref = f"session-ref:l3-reviewed-recall:{suffix}"
    stale_state_refs = [_state_ref("stale-state-ref", fact.stale_state)]
    conflict_state_refs = [_state_ref("conflict-state-ref", fact.conflict_state)]
    derivation_reason_refs: list[L3DerivationReasonRef] = [
        "derivation-reason-ref:l3-derived-from-reviewed-l2-safe-ref-projection",
        "derivation-reason-ref:l3-source-evidence-receipt-refs-preserved",
        "derivation-reason-ref:l3-representation-proposal-only",
        "derivation-reason-ref:l3-no-truth-authority",
        "derivation-reason-ref:l3-no-hidden-context-injection",
    ]
    return L3MemoryModelItem(
        l3_item_ref=f"l3-item-ref:{l3_kind}:{suffix}",
        l3_kind=l3_kind,
        subject_ref=subject_ref,
        workspace_ref=workspace_ref,
        session_ref=session_ref,
        safe_summary_ref=fact.fact_value_ref,
        supporting_memory_record_refs=memory_record_refs,
        supporting_l1_preview_refs=l1_preview_refs,
        supporting_l2_item_refs=l2_refs,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        receipt_refs=receipt_refs,
        derivation_reason_refs=derivation_reason_refs,
        stale_state_refs=stale_state_refs,
        conflict_state_refs=conflict_state_refs,
    )


def _kind_for_refs(refs: Iterable[str]) -> L3MemoryKind:
    joined = " ".join(str(ref).lower() for ref in refs)
    for kind in [
        "identity",
        "session",
        "preference",
        "commitment",
        "relationship",
        "workspace",
        "peer",
    ]:
        if kind in joined:
            return kind  # type: ignore[return-value]
    return "representation"


def _workspace_ref(fact: L2MemoryFactItem) -> str:
    for ref in [*fact.metadata_refs, *fact.tag_refs, *fact.source_refs]:
        lowered = ref.lower()
        if "workspace" in lowered:
            return ref
    return "workspace-ref:local-founder-loop"
