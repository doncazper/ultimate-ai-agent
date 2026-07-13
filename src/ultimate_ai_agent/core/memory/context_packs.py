from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.l1_index import L1HotMemoryIndex
from ultimate_ai_agent.core.memory.l2_index import L2FactualGraphTemporalIndex
from ultimate_ai_agent.core.memory.l3_index import (
    L3IdentitySessionPreferenceIndex,
    L3MemoryModelItem,
)
from ultimate_ai_agent.core.memory.feature_mine import memory_hrr_readiness
from ultimate_ai_agent.core.time import utc_now


CONTEXT_PACK_PROPOSAL_CONTRACT_REF = (
    "contract-ref:governed-cognitive-memory-spine:context-pack-proposals:v1"
)
CONTEXT_PACK_PROPOSAL_ROUTE_REF = "GET /control-center/memory/context-packs"
CONTEXT_PACK_PROPOSAL_STATUS = "implemented_read_only_context_pack_proposals"
CONTEXT_PACK_PROPOSAL_BLOCKED_STATE_REFS = (
    "blocked-state:context-pack-no-hidden-context-injection",
    "blocked-state:context-pack-no-prompt-stuffing",
    "blocked-state:context-pack-no-automatic-context-injection",
    "blocked-state:context-pack-no-truth-authority",
    "blocked-state:context-pack-no-approval-authority",
    "blocked-state:context-pack-no-action-execution",
    "blocked-state:context-pack-no-connector-writes",
    "blocked-state:context-pack-no-crm-sync",
    "blocked-state:context-pack-no-account-sync",
    "blocked-state:context-pack-no-provider-or-model-calls",
    "blocked-state:context-pack-no-embeddings",
    "blocked-state:context-pack-no-vector-db",
    "blocked-state:context-pack-no-semantic-search",
    "blocked-state:context-pack-no-background-indexing",
    "blocked-state:context-pack-no-phase6-execution-hooks",
    "blocked-state:context-pack-no-public-beta",
    "blocked-state:context-pack-no-production-authority",
)

ContextPackRiskClass = Literal["low", "medium", "high"]
ContextPackInclusionReasonRef = Literal[
    "inclusion-reason-ref:context-pack-reviewed-l1-preview",
    "inclusion-reason-ref:context-pack-reviewed-l2-safe-projection",
    "inclusion-reason-ref:context-pack-reviewed-l3-representation-proposal",
    "inclusion-reason-ref:context-pack-source-evidence-receipt-linked",
    "inclusion-reason-ref:context-pack-review-required-not-injected",
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
    "prompt context",
    "prompt_context",
    "hidden context",
    "hidden_context",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)

_DENIED_AUTHORITY_FLAGS = (
    "context_injection_authorized",
    "hidden_prompt_context_authorized",
    "automatic_context_injection_authorized",
    "prompt_context_written",
    "truth_authority_enabled",
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
    "background_indexing_enabled",
    "phase6_execution_hooks_enabled",
    "raw_content_stored",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe context-pack content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _validate_safe_text(value, field_name)


def _safe_suffix(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def _unique_refs(*groups: Iterable[str]) -> list[str]:
    refs: list[str] = []
    for group in groups:
        for ref in group:
            _validate_safe_ref(str(ref), "supporting_refs")
            refs.append(str(ref))
    return list(dict.fromkeys(refs))


def _state_refs(prefix: str, values: Iterable[str]) -> list[str]:
    refs: list[str] = []
    for value in values:
        safe = str(value or "none").strip().lower().replace("_", "-")
        safe = "".join(char if char.isalnum() or char in ".-" else "-" for char in safe)
        safe = "-".join(part for part in safe.split("-") if part) or "none"
        ref = f"{prefix}:{safe}"
        _validate_safe_ref(ref, prefix)
        refs.append(ref)
    return list(dict.fromkeys(refs))


class _ContextPackAuthorityPosture(BaseModel):
    context_injection_authorized: bool = False
    hidden_prompt_context_authorized: bool = False
    automatic_context_injection_authorized: bool = False
    prompt_context_written: bool = False
    truth_authority_enabled: bool = False
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
    background_indexing_enabled: bool = False
    phase6_execution_hooks_enabled: bool = False
    raw_content_stored: bool = False


class ContextPackProposal(_ContextPackAuthorityPosture):
    contract_ref: str = CONTEXT_PACK_PROPOSAL_CONTRACT_REF
    context_pack_ref: str = Field(..., min_length=1)
    proposal_ref: str = Field(..., min_length=1)
    purpose_ref: str = Field(..., min_length=1)
    source_memory_record_refs: list[str] = Field(default_factory=list)
    l1_preview_refs: list[str] = Field(default_factory=list)
    l2_projection_refs: list[str] = Field(default_factory=list)
    l3_representation_refs: list[str] = Field(default_factory=list)
    included_summary_refs: list[str] = Field(default_factory=list)
    inclusion_reason_refs: list[ContextPackInclusionReasonRef] = Field(default_factory=list)
    excluded_ref_reasons: dict[str, str] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    observed_ref: str | None = None
    observer_ref: str | None = None
    representation_scope_ref: str | None = None
    score_components: dict[str, float] = Field(default_factory=dict)
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    query_mode: str = "default"
    safe_query_ref: str | None = None
    stale_state_refs: list[str] = Field(default_factory=list)
    conflict_state_refs: list[str] = Field(default_factory=list)
    risk_class: ContextPackRiskClass = "medium"
    approval_requirement_refs: list[str] = Field(
        default_factory=lambda: [
            "approval-requirement-ref:context-pack-exact-review-before-use",
            "approval-requirement-ref:context-pack-no-hidden-injection",
        ]
    )
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(CONTEXT_PACK_PROPOSAL_BLOCKED_STATE_REFS)
    )
    evidence_answer_refs: list[str] = Field(
        default_factory=lambda: [
            "evidence-answer-ref:context-pack-what-memory-refs-were-proposed",
            "evidence-answer-ref:context-pack-why-included",
            "evidence-answer-ref:context-pack-what-was-excluded",
            "evidence-answer-ref:context-pack-what-remains-blocked",
            "evidence-answer-ref:context-pack-not-context-injection",
        ]
    )
    proposal_only: bool = True
    review_required: bool = True
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_context_pack(self) -> "ContextPackProposal":
        for field_name in [
            "contract_ref",
            "context_pack_ref",
            "proposal_ref",
            "purpose_ref",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.risk_class, "risk_class")
        for field_name in [
            "source_memory_record_refs",
            "l1_preview_refs",
            "l2_projection_refs",
            "l3_representation_refs",
            "included_summary_refs",
            "inclusion_reason_refs",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "retrieval_strategy_refs",
            "stale_state_refs",
            "conflict_state_refs",
            "approval_requirement_refs",
            "blocked_state_refs",
            "evidence_answer_refs",
        ]:
            refs = getattr(self, field_name)
            for ref in refs:
                _validate_safe_ref(str(ref), field_name)
        for field_name in [
            "observed_ref",
            "observer_ref",
            "representation_scope_ref",
            "safe_query_ref",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                _validate_safe_ref(str(value), field_name)
        _validate_safe_text(self.query_mode, "query_mode")
        for ref, reason in self.excluded_ref_reasons.items():
            _validate_safe_ref(str(ref), "excluded_ref_reasons")
            _validate_safe_ref(str(reason), "excluded_ref_reasons")
        for field_name in [
            "source_memory_record_refs",
            "l1_preview_refs",
            "l2_projection_refs",
            "l3_representation_refs",
            "included_summary_refs",
            "inclusion_reason_refs",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "approval_requirement_refs",
            "blocked_state_refs",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required for context-pack proposals")
        if not self.proposal_only:
            raise ValueError("context packs must remain proposal-only")
        if not self.review_required:
            raise ValueError("context packs must remain review-required")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for context-pack proposals")
        return self


class ContextPackProposalIndex(_ContextPackAuthorityPosture):
    contract_ref: str = CONTEXT_PACK_PROPOSAL_CONTRACT_REF
    route_ref: str = CONTEXT_PACK_PROPOSAL_ROUTE_REF
    status: str = CONTEXT_PACK_PROPOSAL_STATUS
    source_l1_contract_ref: str
    source_l2_contract_ref: str
    source_l3_contract_ref: str
    query_ref: str | None = None
    safe_query_ref: str | None = None
    query_mode: str = "default"
    generated_at: datetime = Field(default_factory=utc_now)
    source_l1_preview_count: int = Field(default=0, ge=0)
    source_l2_projection_count: int = Field(default=0, ge=0)
    source_l3_representation_count: int = Field(default=0, ge=0)
    context_pack_count: int = Field(default=0, ge=0)
    proposals: list[ContextPackProposal] = Field(default_factory=list)
    skipped_ref_reasons: dict[str, str] = Field(default_factory=dict)
    safe_refs_only: bool = True
    proposal_only: bool = True
    derived_from_reviewed_memory_only: bool = True
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    search_index_status: dict[str, Any] = Field(default_factory=dict)
    hrr_readiness: dict[str, Any] = Field(default_factory=memory_hrr_readiness)
    context_injection_performed: bool = False
    provider_model_call_performed: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(CONTEXT_PACK_PROPOSAL_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_context_pack_index(self) -> "ContextPackProposalIndex":
        for field_name in [
            "contract_ref",
            "source_l1_contract_ref",
            "source_l2_contract_ref",
            "source_l3_contract_ref",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.route_ref, "route_ref")
        _validate_safe_text(self.status, "status")
        if self.query_ref is not None:
            _validate_safe_ref(self.query_ref, "query_ref")
        if self.safe_query_ref is not None:
            _validate_safe_ref(self.safe_query_ref, "safe_query_ref")
        _validate_safe_text(self.query_mode, "query_mode")
        for ref in self.retrieval_strategy_refs:
            _validate_safe_ref(ref, "retrieval_strategy_refs")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        for ref, reason in self.skipped_ref_reasons.items():
            _validate_safe_ref(str(ref), "skipped_ref_reasons")
            _validate_safe_ref(str(reason), "skipped_ref_reasons")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for context-pack index")
        if not self.safe_refs_only:
            raise ValueError("context-pack index must remain safe-ref-only")
        if not self.proposal_only:
            raise ValueError("context-pack index must remain proposal-only")
        if not self.derived_from_reviewed_memory_only:
            raise ValueError("context-pack index must derive from reviewed memory only")
        if self.context_injection_performed:
            raise ValueError("context-pack index must not inject context")
        if self.provider_model_call_performed:
            raise ValueError("context-pack index must not call providers or models")
        if self.context_pack_count != len(self.proposals):
            raise ValueError("context_pack_count must match proposals")
        return self


def build_context_pack_proposal_index(
    l1_index: L1HotMemoryIndex | dict[str, Any],
    l2_index: L2FactualGraphTemporalIndex | dict[str, Any],
    l3_index: L3IdentitySessionPreferenceIndex | dict[str, Any],
    *,
    query_ref: str | None = None,
    safe_query: str | None = None,
    limit: int = 20,
) -> ContextPackProposalIndex:
    source_l1 = l1_index if isinstance(l1_index, L1HotMemoryIndex) else L1HotMemoryIndex(**l1_index)
    source_l2 = (
        l2_index
        if isinstance(l2_index, L2FactualGraphTemporalIndex)
        else L2FactualGraphTemporalIndex(**l2_index)
    )
    source_l3 = (
        l3_index
        if isinstance(l3_index, L3IdentitySessionPreferenceIndex)
        else L3IdentitySessionPreferenceIndex(**l3_index)
    )
    if query_ref is not None:
        _validate_safe_ref(query_ref, "query_ref")

    proposals: list[ContextPackProposal] = []
    skipped: dict[str, str] = {}
    max_items = max(1, min(int(limit), 50))
    for item in source_l3.items[:max_items]:
        try:
            proposals.append(_proposal_from_l3_item(item, query_ref=query_ref))
        except ValueError:
            skipped[getattr(item, "l3_item_ref", "l3-item-ref:unsafe-blocked")] = (
                "excluded-reason-ref:context-pack-unsafe-or-authority-bearing"
            )

    for ref, reason_ref in source_l1.skipped_record_reasons.items():
        skipped.setdefault(ref, reason_ref)
    for ref in [
        *source_l2.skipped_l1_preview_refs,
        *source_l3.skipped_l2_item_refs,
    ]:
        skipped.setdefault(
            ref,
            "excluded-reason-ref:context-pack-filtered-by-reviewed-memory-source-lanes",
        )

    return ContextPackProposalIndex(
        source_l1_contract_ref=source_l1.contract_ref,
        source_l2_contract_ref=source_l2.contract_ref,
        source_l3_contract_ref=source_l3.contract_ref,
        query_ref=query_ref or source_l3.query_ref or source_l2.query_ref or source_l1.query_ref,
        safe_query_ref=source_l3.safe_query_ref,
        query_mode=source_l3.query_mode,
        source_l1_preview_count=source_l1.indexed_record_count,
        source_l2_projection_count=(
            source_l2.fact_count + source_l2.relation_count + source_l2.temporal_count
        ),
        source_l3_representation_count=source_l3.item_count,
        context_pack_count=len(proposals),
        proposals=proposals,
        skipped_ref_reasons=skipped,
        retrieval_strategy_refs=_retrieval_strategy_refs(source_l3),
        search_index_status=dict(source_l3.search_index_status),
    )


def _proposal_from_l3_item(
    item: L3MemoryModelItem,
    *,
    query_ref: str | None,
) -> ContextPackProposal:
    item = L3MemoryModelItem(**item.model_dump(mode="python"))
    suffix = _safe_suffix(item.l3_item_ref, *(item.receipt_refs or ["receipt-ref:none"]))
    purpose_ref = query_ref or f"purpose-ref:context-pack:{item.l3_kind}:review-proposal"
    stale_state_refs = _unique_refs(item.stale_state_refs) or _state_refs(
        "stale-state-ref",
        ["none"],
    )
    conflict_state_refs = _unique_refs(item.conflict_state_refs) or _state_refs(
        "conflict-state-ref",
        ["none"],
    )
    return ContextPackProposal(
        context_pack_ref=f"context-pack-ref:proposal:{suffix}",
        proposal_ref=f"proposal-ref:context-pack:{suffix}",
        purpose_ref=purpose_ref,
        source_memory_record_refs=_unique_refs(item.supporting_memory_record_refs),
        l1_preview_refs=_unique_refs(item.supporting_l1_preview_refs),
        l2_projection_refs=_unique_refs(item.supporting_l2_item_refs),
        l3_representation_refs=_unique_refs([item.l3_item_ref]),
        included_summary_refs=_unique_refs([item.safe_summary_ref]),
        inclusion_reason_refs=[
            "inclusion-reason-ref:context-pack-reviewed-l1-preview",
            "inclusion-reason-ref:context-pack-reviewed-l2-safe-projection",
            "inclusion-reason-ref:context-pack-reviewed-l3-representation-proposal",
            "inclusion-reason-ref:context-pack-source-evidence-receipt-linked",
            "inclusion-reason-ref:context-pack-review-required-not-injected",
        ],
        excluded_ref_reasons={},
        source_refs=_unique_refs(item.source_refs),
        evidence_refs=_unique_refs(item.evidence_refs),
        receipt_refs=_unique_refs(item.receipt_refs),
        observed_ref=item.observed_ref,
        observer_ref=item.observer_ref,
        representation_scope_ref=item.representation_scope_ref,
        score_components=dict(item.score_components),
        retrieval_strategy_refs=_retrieval_strategy_refs_from_l3_item(item),
        query_mode=item.query_mode,
        safe_query_ref=item.safe_query_ref,
        stale_state_refs=stale_state_refs,
        conflict_state_refs=conflict_state_refs,
        risk_class="medium",
    )


def _retrieval_strategy_refs(source_l3: L3IdentitySessionPreferenceIndex) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-context-pack-proposal-only",
        *source_l3.retrieval_strategy_refs,
    ]
    return list(dict.fromkeys(refs))


def _retrieval_strategy_refs_from_l3_item(item: L3MemoryModelItem) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-context-pack-from-l3-proposal",
        *item.retrieval_strategy_refs,
    ]
    return list(dict.fromkeys(refs))
