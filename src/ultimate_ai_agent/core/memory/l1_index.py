from __future__ import annotations

from datetime import datetime, timezone
from itertools import islice
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory.feature_mine import (
    memory_hrr_readiness,
    validate_query_mode,
)
from ultimate_ai_agent.core.time import utc_now


L1_HOT_MEMORY_INDEX_CONTRACT_REF = (
    "contract-ref:governed-cognitive-memory-spine:l1-hot-local-index:v1"
)
L1_HOT_MEMORY_INDEX_ROUTE_REF = "GET /control-center/memory/l1-index"
L1_HOT_MEMORY_INDEX_STATUS = "implemented_read_only_derived_preview"
L1_HOT_MEMORY_INDEX_BLOCKED_STATE_REFS = (
    "blocked-state:l1-memory-no-hidden-context-injection",
    "blocked-state:l1-memory-no-automatic-recall",
    "blocked-state:l1-memory-no-automatic-memory-writes",
    "blocked-state:l1-memory-no-embeddings",
    "blocked-state:l1-memory-no-vector-db",
    "blocked-state:l1-memory-no-semantic-search",
    "blocked-state:l1-memory-no-background-indexing",
    "blocked-state:l1-memory-no-truth-authority",
    "blocked-state:l1-memory-no-approval-authority",
    "blocked-state:l1-memory-no-action-execution",
    "blocked-state:l1-memory-no-connector-or-crm-sync",
    "blocked-state:l1-memory-no-provider-or-model-calls",
    "blocked-state:l1-memory-no-production-authority",
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
    "context_injection_authorized",
    "automatic_recall_authorized",
    "automatic_memory_write_authorized",
    "source_truth_authority",
    "approval_authority_granted",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "automatic_action_execution_authorized",
    "model_provider_authority_allowed",
    "production_authority_enabled",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "background_indexing_enabled",
    "raw_content_stored",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory index content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _validate_safe_text(value, field_name)


def _safe_ref(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    ref = str(value).strip()
    if not ref:
        return None
    _validate_safe_ref(ref, field_name)
    return ref


def _safe_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    _validate_safe_text(text, field_name)
    return text


def _safe_ref_list(values: Any, field_name: str) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        ref = _safe_ref(value, field_name)
        if ref is not None:
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _safe_tag_refs(values: Any) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        tag = str(value or "").strip().lower().replace("_", "-")
        tag = "".join(
            character if character.isalnum() or character in ".-" else "-"
            for character in tag
        )
        tag = "-".join(part for part in tag.split("-") if part)
        if tag:
            refs.append(f"tag-ref:{tag}")
    return _safe_ref_list(refs, "tag_refs")


def _extract_source_refs(values: Any) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("source_ref") or value.get("source_id")
        else:
            ref = value
        safe = _safe_ref(ref, "source_refs")
        if safe is not None:
            refs.append(safe)
    return list(dict.fromkeys(refs))


def _status(value: Any) -> str:
    return str(value or "").strip()


def _record_ref(record: dict[str, Any]) -> str:
    memory_id = _safe_text(record.get("memory_id"), "memory_id")
    ref = f"memory-record-ref:{memory_id}"
    _validate_safe_ref(ref, "memory_record_ref")
    return ref


def _bounded_limit(limit: int) -> int:
    return max(1, min(int(limit), 50))


class L1HotMemoryPreview(BaseModel):
    contract_ref: str = L1_HOT_MEMORY_INDEX_CONTRACT_REF
    memory_record_ref: str = Field(..., min_length=1)
    memory_id: str = Field(..., min_length=1)
    reviewed_recall_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=320)
    preview_summary: str = Field(..., min_length=1, max_length=320)
    memory_kind: str = Field(..., min_length=1, max_length=80)
    review_state: str = "user_reviewed"
    authority_level: str = "recall_only"
    retention_state: str = "active"
    conflict_state: str = "none"
    stale_state: str = "none"
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    tag_refs: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    match_reasons: list[str] = Field(default_factory=list)
    supporting_ref_groups: dict[str, list[str]] = Field(default_factory=dict)
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    score_components: dict[str, float] = Field(default_factory=dict)
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    query_mode: str = "default"
    safe_query_ref: str | None = None
    epistemic_role: str = "unknown"
    data_classification: str = "unknown"
    sensitivity: str = "unknown"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    trust_score: float = Field(default=0.0, ge=0.0, le=1.0)
    expires_at: datetime | None = None
    checked_at: datetime = Field(default_factory=utc_now)
    context_injection_authorized: bool = False
    automatic_recall_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    source_truth_authority: bool = False
    approval_authority_granted: bool = False
    connector_write_authorized: bool = False
    external_crm_sync_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    model_provider_authority_allowed: bool = False
    production_authority_enabled: bool = False
    embedding_index_enabled: bool = False
    vector_db_enabled: bool = False
    semantic_search_enabled: bool = False
    background_indexing_enabled: bool = False
    raw_content_stored: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L1_HOT_MEMORY_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_preview(self) -> "L1HotMemoryPreview":
        for field_name in [
            "memory_record_ref",
            "reviewed_recall_ref",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "event_refs",
            "metadata_refs",
            "tag_refs",
            "retrieval_strategy_refs",
            "blocked_state_refs",
        ]:
            value = getattr(self, field_name)
            if value is None:
                continue
            if isinstance(value, list):
                for ref in value:
                    _validate_safe_ref(ref, field_name)
            else:
                _validate_safe_ref(value, field_name)
        for text_field in ["memory_id", "safe_summary", "preview_summary", "memory_kind"]:
            _validate_safe_text(str(getattr(self, text_field)), text_field)
        _validate_safe_text(self.query_mode, "query_mode")
        _validate_safe_text(self.epistemic_role, "epistemic_role")
        _validate_safe_text(self.data_classification, "data_classification")
        _validate_safe_text(self.sensitivity, "sensitivity")
        if self.safe_query_ref is not None:
            _validate_safe_ref(self.safe_query_ref, "safe_query_ref")
        for reason in self.match_reasons:
            _validate_safe_text(reason, "match_reasons")
        for group_name, refs in self.supporting_ref_groups.items():
            _validate_safe_text(str(group_name), "supporting_ref_group")
            for ref in refs:
                _validate_safe_ref(ref, "supporting_ref_groups")
        if self.review_state != "user_reviewed":
            raise ValueError("L1 previews require reviewed recall records")
        if self.authority_level != "recall_only":
            raise ValueError("L1 previews are recall-only")
        if self.retention_state != "active":
            raise ValueError("L1 previews require active retention state")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for L1 memory previews")
        if not self.source_refs or not self.evidence_refs or not self.receipt_refs:
            raise ValueError("L1 previews require source, evidence, and receipt refs")
        return self


class L1HotMemoryIndex(BaseModel):
    contract_ref: str = L1_HOT_MEMORY_INDEX_CONTRACT_REF
    route_ref: str = L1_HOT_MEMORY_INDEX_ROUTE_REF
    status: str = L1_HOT_MEMORY_INDEX_STATUS
    query_ref: str | None = None
    safe_query_ref: str | None = None
    query_mode: str = "default"
    generated_at: datetime = Field(default_factory=utc_now)
    scan_limit: int = Field(default=200, ge=1, le=500)
    scanned_record_count: int = Field(default=0, ge=0)
    scan_truncated: bool = False
    indexed_record_count: int = Field(default=0, ge=0)
    preview_count: int = Field(default=0, ge=0)
    previews: list[L1HotMemoryPreview] = Field(default_factory=list)
    skipped_record_refs: list[str] = Field(default_factory=list)
    skipped_record_reasons: dict[str, str] = Field(default_factory=dict)
    skipped_record_count: int = Field(default=0, ge=0)
    safe_refs_only: bool = True
    retrieval_strategy_refs: list[str] = Field(default_factory=list)
    search_index_status: dict[str, Any] = Field(default_factory=dict)
    hrr_readiness: dict[str, Any] = Field(default_factory=memory_hrr_readiness)
    raw_content_stored: bool = False
    context_injection_authorized: bool = False
    automatic_recall_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    source_truth_authority: bool = False
    approval_authority_granted: bool = False
    connector_write_authorized: bool = False
    external_crm_sync_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    model_provider_authority_allowed: bool = False
    production_authority_enabled: bool = False
    embedding_index_enabled: bool = False
    vector_db_enabled: bool = False
    semantic_search_enabled: bool = False
    background_indexing_enabled: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(L1_HOT_MEMORY_INDEX_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_index(self) -> "L1HotMemoryIndex":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.route_ref, "route_ref")
        _validate_safe_text(self.status, "status")
        if self.query_ref is not None:
            _validate_safe_ref(self.query_ref, "query_ref")
        if self.safe_query_ref is not None:
            _validate_safe_ref(self.safe_query_ref, "safe_query_ref")
        _validate_safe_text(self.query_mode, "query_mode")
        for ref in self.retrieval_strategy_refs:
            _validate_safe_ref(ref, "retrieval_strategy_refs")
        for ref in self.skipped_record_refs:
            _validate_safe_ref(ref, "skipped_record_refs")
        for ref, reason_ref in self.skipped_record_reasons.items():
            _validate_safe_ref(ref, "skipped_record_reasons")
            _validate_safe_ref(reason_ref, "skipped_record_reasons")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        for flag in _DENIED_AUTHORITY_FLAGS:
            if bool(getattr(self, flag)):
                raise ValueError(f"{flag} must remain false for L1 memory index")
        if not self.safe_refs_only:
            raise ValueError("L1 memory index must remain safe-ref-only")
        if self.indexed_record_count != len(self.previews):
            raise ValueError("indexed_record_count must match previews")
        if self.preview_count != len(self.previews):
            raise ValueError("preview_count must match previews")
        if self.skipped_record_count != len(self.skipped_record_refs):
            raise ValueError("skipped_record_count must match skipped refs")
        if self.scanned_record_count > self.scan_limit:
            raise ValueError("scanned record count exceeds scan limit")
        if set(self.skipped_record_reasons) != set(self.skipped_record_refs):
            raise ValueError("every skipped record requires one exclusion reason")
        return self


def _eligibility_exclusion_reason(
    record: dict[str, Any],
    *,
    checked_at: datetime,
) -> str | None:
    if _status(record.get("review_state")) != "user_reviewed":
        return "excluded-reason-ref:l1-memory:not-reviewed"
    if _status(record.get("authority_level")) != "recall_only":
        return "excluded-reason-ref:l1-memory:not-recall-only"
    status = _status(record.get("status"))
    if status != "active":
        return "excluded-reason-ref:l1-memory:inactive-status"
    retention_state = _status(record.get("retention_state"))
    if retention_state != "active":
        return "excluded-reason-ref:l1-memory:inactive-retention"
    stale_state = _status(record.get("stale_state"))
    if stale_state != "none":
        return "excluded-reason-ref:l1-memory:stale"
    conflict_state = _status(record.get("conflict_state"))
    if conflict_state != "none":
        return "excluded-reason-ref:l1-memory:conflict"
    expires_at = record.get("expires_at")
    if expires_at:
        try:
            parsed_expiry = datetime.fromisoformat(
                str(expires_at).replace("Z", "+00:00")
            )
        except ValueError:
            return "excluded-reason-ref:l1-memory:expiry-unknown"
        if parsed_expiry.tzinfo is None:
            parsed_expiry = parsed_expiry.replace(tzinfo=timezone.utc)
        if parsed_expiry <= checked_at.astimezone(timezone.utc):
            return "excluded-reason-ref:l1-memory:expired"
    return None


def build_l1_hot_memory_index(
    records: Iterable[dict[str, Any] | Any],
    *,
    query_ref: str | None = None,
    safe_query: str | None = None,
    search_index_status: dict[str, Any] | None = None,
    checked_at: datetime | None = None,
    scan_limit: int = 200,
    limit: int = 20,
) -> L1HotMemoryIndex:
    safe_query_ref, hashed_safe_query_ref, query_mode = validate_query_mode(
        query_ref=query_ref,
        safe_query=safe_query,
    )
    safe_query_text = _safe_text(safe_query, "safe_query") if safe_query else None
    previews: list[L1HotMemoryPreview] = []
    skipped_record_refs: list[str] = []
    skipped_record_reasons: dict[str, str] = {}
    effective_checked_at = checked_at or utc_now()
    if effective_checked_at.tzinfo is None:
        effective_checked_at = effective_checked_at.replace(tzinfo=timezone.utc)
    bounded_scan_limit = max(1, min(int(scan_limit), 500))
    scanned_records = list(islice(records, bounded_scan_limit + 1))
    scan_truncated = len(scanned_records) > bounded_scan_limit
    for record_index, raw_record in enumerate(scanned_records[:bounded_scan_limit]):
        unsafe_record_ref = (
            f"memory-record-ref:unsafe-record-blocked:slot-{record_index:04d}"
        )
        record = (
            raw_record.model_dump(mode="json")
            if hasattr(raw_record, "model_dump")
            else dict(raw_record)
        )
        try:
            record_ref = _record_ref(record)
            exclusion_reason = _eligibility_exclusion_reason(
                record,
                checked_at=effective_checked_at,
            )
            if exclusion_reason is not None:
                skipped_record_refs.append(record_ref)
                skipped_record_reasons[record_ref] = exclusion_reason
                continue
        except ValueError:
            record_ref = unsafe_record_ref
            skipped_record_refs.append(record_ref)
            skipped_record_reasons[record_ref] = (
                "excluded-reason-ref:l1-memory:unsafe-record"
            )
            continue
        try:
            preview = _preview_for_record(
                record,
                query_ref=safe_query_ref,
                safe_query=safe_query_text,
                safe_query_ref=hashed_safe_query_ref,
                query_mode=query_mode,
                checked_at=effective_checked_at,
            )
        except ValueError:
            try:
                record_ref = _record_ref(record)
            except ValueError:
                record_ref = unsafe_record_ref
            skipped_record_refs.append(record_ref)
            skipped_record_reasons[record_ref] = (
                "excluded-reason-ref:l1-memory:invalid-or-ineligible"
            )
            continue
        if preview is not None:
            previews.append(preview)
        else:
            skipped_record_refs.append(record_ref)
            skipped_record_reasons[record_ref] = (
                "excluded-reason-ref:l1-memory:query-no-match"
            )
    ranked_previews = sorted(
        previews,
        key=lambda preview: (-preview.score, preview.memory_record_ref),
    )
    bounded_preview_limit = _bounded_limit(limit)
    for overflow in ranked_previews[bounded_preview_limit:]:
        skipped_record_refs.append(overflow.memory_record_ref)
        skipped_record_reasons[overflow.memory_record_ref] = (
            "excluded-reason-ref:l1-memory:rank-limit"
        )
    previews = ranked_previews[:bounded_preview_limit]
    skipped_record_refs = list(dict.fromkeys(skipped_record_refs))
    skipped_record_reasons = {
        ref: skipped_record_reasons[ref] for ref in skipped_record_refs
    }
    return L1HotMemoryIndex(
        query_ref=safe_query_ref,
        safe_query_ref=hashed_safe_query_ref,
        query_mode=query_mode,
        generated_at=effective_checked_at,
        scan_limit=bounded_scan_limit,
        scanned_record_count=min(len(scanned_records), bounded_scan_limit),
        scan_truncated=scan_truncated,
        indexed_record_count=len(previews),
        preview_count=len(previews),
        previews=previews,
        skipped_record_refs=skipped_record_refs,
        skipped_record_reasons=skipped_record_reasons,
        skipped_record_count=len(skipped_record_refs),
        retrieval_strategy_refs=_retrieval_strategy_refs(
            query_mode=query_mode,
            search_index_status=search_index_status,
        ),
        search_index_status=_search_index_status(search_index_status),
    )


def _preview_for_record(
    record: dict[str, Any],
    *,
    query_ref: str | None,
    safe_query: str | None,
    safe_query_ref: str | None,
    query_mode: str,
    checked_at: datetime,
) -> L1HotMemoryPreview | None:
    if _eligibility_exclusion_reason(record, checked_at=checked_at) is not None:
        raise ValueError("memory record is not L1 eligible")
    recall_metadata = record.get("recall_metadata") or {}
    metadata = record.get("metadata") or {}
    if bool(recall_metadata.get("context_pack_eligible")):
        raise ValueError("context-pack eligible records are not L1 eligible")
    if int(recall_metadata.get("injection_priority") or 0) != 0:
        raise ValueError("injection-prioritized records are not L1 eligible")
    for flag in [
        "context_injection_authorized",
        "source_truth_authority",
        "connector_write_authorized",
        "automatic_action_execution_authorized",
    ]:
        if bool(metadata.get(flag)):
            raise ValueError("authority-bearing memory records are not L1 eligible")

    memory_id = _safe_text(record.get("memory_id"), "memory_id")
    memory_record_ref = f"memory-record-ref:{memory_id}"
    source_refs = _extract_source_refs(record.get("source_refs"))
    evidence_refs = _safe_ref_list(record.get("evidence_refs"), "evidence_refs")
    receipt_refs = _safe_ref_list(record.get("receipt_refs"), "receipt_refs")
    event_refs = _safe_ref_list(record.get("event_refs"), "event_refs")
    metadata_refs = _safe_ref_list(record.get("metadata_refs"), "metadata_refs")
    tag_refs = _safe_tag_refs(record.get("tags"))
    reviewed_recall_ref = _safe_ref(
        metadata.get("reviewed_recall_ref"),
        "reviewed_recall_ref",
    )
    supporting_refs = list(
        dict.fromkeys(
            [
                memory_record_ref,
                *source_refs,
                *evidence_refs,
                *receipt_refs,
                *event_refs,
                *metadata_refs,
                *tag_refs,
                *([reviewed_recall_ref] if reviewed_recall_ref else []),
            ]
        )
    )
    match_reasons = ["reviewed_recall_record"]
    score_components = {
        "reviewed_status": 0.30,
        "source_refs": 0.15 if source_refs else 0.0,
        "evidence_refs": 0.15 if evidence_refs else 0.0,
        "receipt_refs": 0.15 if receipt_refs else 0.0,
        "query_match": 0.0,
        "confidence": max(0.0, min(float(record.get("confidence_score") or 0.0), 1.0)) * 0.10,
        "trust": max(0.0, min(float(record.get("trust_score") or 0.0), 1.0)) * 0.10,
        "stale_penalty": -0.15
        if _status(record.get("stale_state") or "none") != "none"
        else 0.0,
        "conflict_penalty": -0.15
        if _status(record.get("conflict_state") or "none") != "none"
        else 0.0,
    }
    if query_ref is None:
        if safe_query:
            query_tokens = set(_tokenize_query_text(safe_query))
            record_tokens = set(
                _tokenize_query_text(
                    " ".join(
                        [
                            str(record.get("safe_summary") or ""),
                            str(record.get("summary") or ""),
                            str(record.get("memory_kind") or ""),
                            " ".join(record.get("tags") or []),
                            " ".join(supporting_refs),
                        ]
                    )
                )
            )
            if not query_tokens or not query_tokens.intersection(record_tokens):
                return None
            score_components["query_match"] = min(
                0.20,
                len(query_tokens.intersection(record_tokens)) * 0.05,
            )
            match_reasons.append("safe_query_ref_matched_safe_summary_or_refs")
        else:
            match_reasons.append("recent_reviewed_recall_preview")
    elif query_ref in supporting_refs:
        match_reasons.append("query_ref_matched_supporting_ref")
        score_components["query_match"] = 0.20
    else:
        return None
    score = max(0.0, min(1.0, sum(score_components.values())))

    safe_summary = _safe_text(record.get("safe_summary"), "safe_summary")[:320]
    return L1HotMemoryPreview(
        memory_record_ref=memory_record_ref,
        memory_id=memory_id,
        reviewed_recall_ref=reviewed_recall_ref,
        safe_summary=safe_summary,
        preview_summary=safe_summary,
        memory_kind=_safe_text(record.get("memory_kind"), "memory_kind"),
        review_state=_status(record.get("review_state")),
        authority_level=_status(record.get("authority_level")),
        retention_state=_status(record.get("retention_state")),
        conflict_state=_status(record.get("conflict_state") or "none"),
        stale_state=_status(record.get("stale_state") or "none"),
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        receipt_refs=receipt_refs,
        event_refs=event_refs,
        metadata_refs=metadata_refs,
        tag_refs=tag_refs,
        created_at=record.get("created_at"),
        match_reasons=match_reasons,
        supporting_ref_groups={
            "source_refs": source_refs,
            "evidence_refs": evidence_refs,
            "receipt_refs": receipt_refs,
            "event_refs": event_refs,
            "metadata_refs": metadata_refs,
            "tag_refs": tag_refs,
            "record_refs": [memory_record_ref],
        },
        score=score,
        score_components=score_components,
        retrieval_strategy_refs=_retrieval_strategy_refs(query_mode=query_mode),
        query_mode=query_mode,
        safe_query_ref=safe_query_ref,
        epistemic_role=_safe_text(record.get("epistemic_role") or "unknown", "epistemic_role"),
        data_classification=_safe_text(
            record.get("data_classification") or "unknown",
            "data_classification",
        ),
        sensitivity=_safe_text(
            record.get("sensitivity") or "unknown",
            "sensitivity",
        ),
        confidence_score=max(
            0.0,
            min(float(record.get("confidence_score") or 0.0), 1.0),
        ),
        trust_score=max(0.0, min(float(record.get("trust_score") or 0.0), 1.0)),
        expires_at=record.get("expires_at"),
        checked_at=checked_at,
    )


def _retrieval_strategy_refs(
    *,
    query_mode: str,
    search_index_status: dict[str, Any] | None = None,
) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-l1-safe-summary",
        "retrieval-strategy-ref:fcc-mem-022-l1-safe-refs",
        "retrieval-strategy-ref:fcc-mem-022-deterministic-score-components",
    ]
    if query_mode == "query_ref":
        refs.append("retrieval-strategy-ref:fcc-mem-022-query-ref")
    if query_mode == "safe_query":
        refs.append("retrieval-strategy-ref:fcc-mem-022-safe-query-hashed")
    if (search_index_status or {}).get("fts5_enabled"):
        refs.append("retrieval-strategy-ref:fcc-mem-022-local-sqlite-fts5-safe-fields")
    else:
        refs.append("retrieval-strategy-ref:fcc-mem-022-lexical-fallback")
    return list(dict.fromkeys(refs))


def _search_index_status(status: dict[str, Any] | None) -> dict[str, Any]:
    if status:
        return dict(status)
    return {
        "status": "deterministic_lexical_fallback_unavailable_status",
        "fts5_enabled": False,
        "indexed_record_count": 0,
        "safe_summary_refs_only": True,
        "raw_content_indexed": False,
        "embedding_index_enabled": False,
        "vector_db_enabled": False,
        "semantic_search_enabled": False,
        "hrr_enabled": False,
        "algebraic_retrieval_enabled": False,
    }


def _tokenize_query_text(value: str) -> list[str]:
    token = []
    tokens: list[str] = []
    for char in value.lower():
        if char.isalnum():
            token.append(char)
            continue
        if token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return [part for part in tokens if len(part) > 1]
