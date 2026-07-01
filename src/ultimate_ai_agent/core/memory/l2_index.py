from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.l1_index import L1HotMemoryIndex, L1HotMemoryPreview
from ultimate_ai_agent.core.memory.feature_mine import memory_hrr_readiness
from ultimate_ai_agent.core.time import utc_now


L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF = (
    "contract-ref:governed-cognitive-memory-spine:l2-factual-graph-temporal-index:v1"
)
L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF = "GET /control-center/memory/l2-index"
L2_FACTUAL_GRAPH_TEMPORAL_INDEX_STATUS = "implemented_read_only_derived_preview"
L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS = (
    "blocked-state:l2-memory-no-truth-authority",
    "blocked-state:l2-memory-no-hidden-context-injection",
    "blocked-state:l2-memory-no-automatic-recall",
    "blocked-state:l2-memory-no-automatic-memory-writes",
    "blocked-state:l2-memory-no-embeddings",
    "blocked-state:l2-memory-no-vector-db",
    "blocked-state:l2-memory-no-semantic-search",
    "blocked-state:l2-memory-no-llm-entity-extraction",
    "blocked-state:l2-memory-no-provider-or-model-calls",
    "blocked-state:l2-memory-no-background-indexing",
    "blocked-state:l2-memory-no-context-pack-injection",
    "blocked-state:l2-memory-no-connector-writes",
    "blocked-state:l2-memory-no-crm-sync",
    "blocked-state:l2-memory-no-account-sync",
    "blocked-state:l2-memory-no-action-execution",
    "blocked-state:l2-memory-no-phase4-identity-session-modeling",
    "blocked-state:l2-memory-no-production-authority",
)

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
    "llm_entity_extraction_enabled",
    "background_indexing_enabled",
    "context_pack_injection_authorized",
    "phase4_identity_session_modeling_enabled",
    "raw_content_stored",
)

L2DerivationReason = Literal[
    "derived_from_l1_reviewed_recall_preview",
    "safe_summary_bounded_preview_only",
    "source_evidence_receipt_refs_preserved",
    "deterministic_ref_projection_not_semantic_extraction",
    "temporal_anchor_from_reviewed_record_timestamp_or_receipt_ref",
]


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe L2 memory content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _validate_safe_text(value, field_name)


def _safe_suffix(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return digest


def _safe_date_anchor(created_at: datetime | None, fallback_ref: str | None) -> str:
    if created_at is not None:
        return f"temporal-anchor-ref:l2-reviewed-date:{created_at.date().isoformat()}"
    if fallback_ref:
        return f"temporal-anchor-ref:l2-receipt:{_safe_suffix(fallback_ref)}"
    return "temporal-anchor-ref:l2-review-time:unknown"


def _supporting_refs(preview: L1HotMemoryPreview) -> list[str]:
    refs: list[str] = [
        preview.memory_record_ref,
        *([preview.reviewed_recall_ref] if preview.reviewed_recall_ref else []),
        *preview.source_refs,
        *preview.evidence_refs,
        *preview.receipt_refs,
        *preview.event_refs,
        *preview.metadata_refs,
        *preview.tag_refs,
    ]
    return list(dict.fromkeys(refs))


def _require_ref_list(values: Iterable[str], field_name: str) -> None:
    values = list(values)
    if not values:
        raise ValueError(f"{field_name} is required for L2 memory items")
    for ref in values:
        _validate_safe_ref(ref, field_name)


def _validate_common_item(instance: Any, label: str) -> None:
    for field_name in [
        "memory_record_ref",
        "reviewed_recall_ref",
        "source_refs",
        "evidence_refs",
        "receipt_refs",
        "event_refs",
        "metadata_refs",
        "tag_refs",
        "supporting_refs",
        "retrieval_strategy_refs",
        "blocked_state_refs",
    ]:
        value = getattr(instance, field_name, None)
        if value is None:
            continue
        if isinstance(value, list):
            for ref in value:
                _validate_safe_ref(ref, field_name)
        else:
            _validate_safe_ref(value, field_name)
    for text_field in ["safe_summary", "stale_state", "conflict_state"]:
        _validate_safe_text(str(getattr(instance, text_field)), text_field)
    for reason in instance.derivation_reasons:
        _validate_safe_text(str(reason), "derivation_reasons")
    if getattr(instance, "safe_query_ref", None) is not None:
        _validate_safe_ref(str(instance.safe_query_ref), "safe_query_ref")
    _validate_safe_text(str(getattr(instance, "query_mode", "default")), "query_mode")
    _require_ref_list(instance.source_refs, "source_refs")
    _require_ref_list(instance.evidence_refs, "evidence_refs")
    _require_ref_list(instance.receipt_refs, "receipt_refs")
    _require_ref_list(instance.supporting_refs, "supporting_refs")
    for flag in _DENIED_AUTHORITY_FLAGS:
        if bool(getattr(instance, flag)):
            raise ValueError(f"{flag} must remain false for L2 {label}")


class _L2AuthorityPosture(BaseModel):
    truth_authority_enabled: bool = False
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
    llm_entity_extraction_enabled: bool = False
    background_indexing_enabled: bool = False
    context_pack_injection_authorized: bool = False
    phase4_identity_session_modeling_enabled: bool = False
    raw_content_stored: bool = False


class L2MemoryFactItem(_L2AuthorityPosture):
    contract_ref: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    fact_ref: str = Field(..., min_length=1)
    memory_record_ref: str = Field(..., min_length=1)
    reviewed_recall_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=320)
    fact_kind: str = "reviewed_recall_summary_ref_projection"
    fact_subject_ref: str = Field(..., min_length=1)
    fact_value_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    tag_refs: list[str] = Field(default_factory=list)
    derivation_reasons: list[L2DerivationReason] = Field(default_factory=list)
    supporting_refs: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    query_mode: str = "default"
    safe_query_ref: str | None = None
    stale_state: str = "none"
    conflict_state: str = "none"
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_fact_item(self) -> "L2MemoryFactItem":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_ref(self.fact_ref, "fact_ref")
        _validate_safe_ref(self.fact_subject_ref, "fact_subject_ref")
        _validate_safe_ref(self.fact_value_ref, "fact_value_ref")
        _validate_safe_text(self.fact_kind, "fact_kind")
        _validate_common_item(self, "fact item")
        return self


class L2MemoryGraphRelation(_L2AuthorityPosture):
    contract_ref: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    relation_ref: str = Field(..., min_length=1)
    memory_record_ref: str = Field(..., min_length=1)
    reviewed_recall_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=320)
    relation_kind: str = "reviewed_recall_supported_by_ref"
    source_node_ref: str = Field(..., min_length=1)
    target_node_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    tag_refs: list[str] = Field(default_factory=list)
    derivation_reasons: list[L2DerivationReason] = Field(default_factory=list)
    supporting_refs: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    query_mode: str = "default"
    safe_query_ref: str | None = None
    stale_state: str = "none"
    conflict_state: str = "none"
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_graph_relation(self) -> "L2MemoryGraphRelation":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_ref(self.relation_ref, "relation_ref")
        _validate_safe_ref(self.source_node_ref, "source_node_ref")
        _validate_safe_ref(self.target_node_ref, "target_node_ref")
        _validate_safe_text(self.relation_kind, "relation_kind")
        _validate_common_item(self, "graph relation")
        return self


class L2MemoryTemporalItem(_L2AuthorityPosture):
    contract_ref: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    temporal_ref: str = Field(..., min_length=1)
    memory_record_ref: str = Field(..., min_length=1)
    reviewed_recall_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=320)
    temporal_kind: str = "reviewed_recall_timeline_anchor"
    temporal_anchor_ref: str = Field(..., min_length=1)
    reviewed_record_created_at: datetime | None = None
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    tag_refs: list[str] = Field(default_factory=list)
    derivation_reasons: list[L2DerivationReason] = Field(default_factory=list)
    supporting_refs: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    query_mode: str = "default"
    safe_query_ref: str | None = None
    stale_state: str = "none"
    conflict_state: str = "none"
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_temporal_item(self) -> "L2MemoryTemporalItem":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_ref(self.temporal_ref, "temporal_ref")
        _validate_safe_ref(self.temporal_anchor_ref, "temporal_anchor_ref")
        _validate_safe_text(self.temporal_kind, "temporal_kind")
        _validate_common_item(self, "temporal item")
        return self


class L2FactualGraphTemporalIndex(_L2AuthorityPosture):
    contract_ref: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_CONTRACT_REF
    route_ref: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_ROUTE_REF
    status: str = L2_FACTUAL_GRAPH_TEMPORAL_INDEX_STATUS
    source_l1_contract_ref: str
    source_l1_route_ref: str
    query_ref: str | None = None
    safe_query_ref: str | None = None
    query_mode: str = "default"
    generated_at: datetime = Field(default_factory=utc_now)
    source_l1_preview_count: int = Field(default=0, ge=0)
    fact_count: int = Field(default=0, ge=0)
    relation_count: int = Field(default=0, ge=0)
    temporal_count: int = Field(default=0, ge=0)
    facts: list[L2MemoryFactItem] = Field(default_factory=list)
    graph_relations: list[L2MemoryGraphRelation] = Field(default_factory=list)
    temporal_items: list[L2MemoryTemporalItem] = Field(default_factory=list)
    skipped_l1_preview_refs: list[str] = Field(default_factory=list)
    skipped_l1_preview_count: int = Field(default=0, ge=0)
    safe_refs_only: bool = True
    deterministic_projection_only: bool = True
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    search_index_status: dict[str, Any] = Field(default_factory=dict)
    hrr_readiness: dict[str, Any] = Field(default_factory=memory_hrr_readiness)
    semantic_extraction_used: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L2_FACTUAL_GRAPH_TEMPORAL_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_index(self) -> "L2FactualGraphTemporalIndex":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.route_ref, "route_ref")
        _validate_safe_text(self.status, "status")
        _validate_safe_ref(self.source_l1_contract_ref, "source_l1_contract_ref")
        _validate_safe_text(self.source_l1_route_ref, "source_l1_route_ref")
        if self.query_ref is not None:
            _validate_safe_ref(self.query_ref, "query_ref")
        if self.safe_query_ref is not None:
            _validate_safe_ref(self.safe_query_ref, "safe_query_ref")
        _validate_safe_text(self.query_mode, "query_mode")
        for ref in self.retrieval_strategy_refs:
            _validate_safe_ref(ref, "retrieval_strategy_refs")
        for ref in self.skipped_l1_preview_refs:
            _validate_safe_ref(ref, "skipped_l1_preview_refs")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for L2 memory index")
        if not self.safe_refs_only:
            raise ValueError("L2 memory index must remain safe-ref-only")
        if not self.deterministic_projection_only:
            raise ValueError("L2 memory index must remain deterministic projection only")
        if self.semantic_extraction_used:
            raise ValueError("L2 memory index must not use semantic extraction")
        if self.fact_count != len(self.facts):
            raise ValueError("fact_count must match facts")
        if self.relation_count != len(self.graph_relations):
            raise ValueError("relation_count must match graph_relations")
        if self.temporal_count != len(self.temporal_items):
            raise ValueError("temporal_count must match temporal_items")
        if self.skipped_l1_preview_count != len(self.skipped_l1_preview_refs):
            raise ValueError("skipped_l1_preview_count must match skipped refs")
        return self


def build_l2_factual_graph_temporal_index(
    l1_index: L1HotMemoryIndex | dict[str, Any],
    *,
    query_ref: str | None = None,
    safe_query: str | None = None,
    limit: int = 20,
) -> L2FactualGraphTemporalIndex:
    source_index = (
        l1_index
        if isinstance(l1_index, L1HotMemoryIndex)
        else L1HotMemoryIndex(**l1_index)
    )
    if query_ref is not None:
        _validate_safe_ref(query_ref, "query_ref")

    facts: list[L2MemoryFactItem] = []
    relations: list[L2MemoryGraphRelation] = []
    temporal_items: list[L2MemoryTemporalItem] = []
    skipped_refs: list[str] = []
    for preview in source_index.previews[: max(1, min(int(limit), 50))]:
        try:
            fact, relation, temporal = _items_for_preview(preview)
        except ValueError:
            skipped_refs.append(preview.memory_record_ref)
            continue
        facts.append(fact)
        relations.append(relation)
        temporal_items.append(temporal)

    skipped_refs.extend(source_index.skipped_record_refs)
    skipped_refs = list(dict.fromkeys(skipped_refs))
    return L2FactualGraphTemporalIndex(
        source_l1_contract_ref=source_index.contract_ref,
        source_l1_route_ref=source_index.route_ref,
        query_ref=query_ref or source_index.query_ref,
        safe_query_ref=source_index.safe_query_ref,
        query_mode=source_index.query_mode,
        source_l1_preview_count=source_index.preview_count,
        fact_count=len(facts),
        relation_count=len(relations),
        temporal_count=len(temporal_items),
        facts=facts,
        graph_relations=relations,
        temporal_items=temporal_items,
        skipped_l1_preview_refs=skipped_refs,
        skipped_l1_preview_count=len(skipped_refs),
        retrieval_strategy_refs=_retrieval_strategy_refs(source_index),
        search_index_status=dict(source_index.search_index_status),
    )


def _items_for_preview(
    preview: L1HotMemoryPreview,
) -> tuple[L2MemoryFactItem, L2MemoryGraphRelation, L2MemoryTemporalItem]:
    preview = L1HotMemoryPreview(**preview.model_dump(mode="python"))
    supporting_refs = _supporting_refs(preview)
    base_suffix = _safe_suffix(preview.memory_record_ref, preview.safe_summary)
    reasons: list[L2DerivationReason] = [
        "derived_from_l1_reviewed_recall_preview",
        "safe_summary_bounded_preview_only",
        "source_evidence_receipt_refs_preserved",
        "deterministic_ref_projection_not_semantic_extraction",
    ]
    target_node_ref = (
        preview.source_refs[0]
        if preview.source_refs
        else preview.evidence_refs[0]
        if preview.evidence_refs
        else preview.receipt_refs[0]
    )
    fact = L2MemoryFactItem(
        fact_ref=f"fact-ref:l2-reviewed-recall:{base_suffix}",
        memory_record_ref=preview.memory_record_ref,
        reviewed_recall_ref=preview.reviewed_recall_ref,
        safe_summary=preview.safe_summary,
        fact_subject_ref=preview.reviewed_recall_ref or preview.memory_record_ref,
        fact_value_ref=f"safe-summary-ref:l2-reviewed-recall:{base_suffix}",
        source_refs=preview.source_refs,
        evidence_refs=preview.evidence_refs,
        receipt_refs=preview.receipt_refs,
        event_refs=preview.event_refs,
        metadata_refs=preview.metadata_refs,
        tag_refs=preview.tag_refs,
        derivation_reasons=reasons,
        supporting_refs=supporting_refs,
        score_components=dict(preview.score_components),
        retrieval_strategy_refs=_retrieval_strategy_refs_from_preview(preview),
        query_mode=preview.query_mode,
        safe_query_ref=preview.safe_query_ref,
        stale_state=preview.stale_state,
        conflict_state=preview.conflict_state,
    )
    relation = L2MemoryGraphRelation(
        relation_ref=f"relation-ref:l2-reviewed-recall-supported-by:{base_suffix}",
        memory_record_ref=preview.memory_record_ref,
        reviewed_recall_ref=preview.reviewed_recall_ref,
        safe_summary=preview.safe_summary,
        source_node_ref=preview.reviewed_recall_ref or preview.memory_record_ref,
        target_node_ref=target_node_ref,
        source_refs=preview.source_refs,
        evidence_refs=preview.evidence_refs,
        receipt_refs=preview.receipt_refs,
        event_refs=preview.event_refs,
        metadata_refs=preview.metadata_refs,
        tag_refs=preview.tag_refs,
        derivation_reasons=reasons,
        supporting_refs=supporting_refs,
        score_components=dict(preview.score_components),
        retrieval_strategy_refs=_retrieval_strategy_refs_from_preview(preview),
        query_mode=preview.query_mode,
        safe_query_ref=preview.safe_query_ref,
        stale_state=preview.stale_state,
        conflict_state=preview.conflict_state,
    )
    temporal_reasons: list[L2DerivationReason] = [
        *reasons,
        "temporal_anchor_from_reviewed_record_timestamp_or_receipt_ref",
    ]
    temporal = L2MemoryTemporalItem(
        temporal_ref=f"temporal-ref:l2-reviewed-recall:{base_suffix}",
        memory_record_ref=preview.memory_record_ref,
        reviewed_recall_ref=preview.reviewed_recall_ref,
        safe_summary=preview.safe_summary,
        temporal_anchor_ref=_safe_date_anchor(
            preview.created_at,
            preview.receipt_refs[0] if preview.receipt_refs else None,
        ),
        reviewed_record_created_at=preview.created_at,
        source_refs=preview.source_refs,
        evidence_refs=preview.evidence_refs,
        receipt_refs=preview.receipt_refs,
        event_refs=preview.event_refs,
        metadata_refs=preview.metadata_refs,
        tag_refs=preview.tag_refs,
        derivation_reasons=temporal_reasons,
        supporting_refs=supporting_refs,
        score_components=dict(preview.score_components),
        retrieval_strategy_refs=_retrieval_strategy_refs_from_preview(preview),
        query_mode=preview.query_mode,
        safe_query_ref=preview.safe_query_ref,
        stale_state=preview.stale_state,
        conflict_state=preview.conflict_state,
    )
    return fact, relation, temporal


def _retrieval_strategy_refs(source_index: L1HotMemoryIndex) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-l2-safe-ref-projection",
        *source_index.retrieval_strategy_refs,
    ]
    return list(dict.fromkeys(refs))


def _retrieval_strategy_refs_from_preview(preview: L1HotMemoryPreview) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-l2-from-l1-preview",
        *preview.retrieval_strategy_refs,
    ]
    return list(dict.fromkeys(refs))
