from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


MEMORY_WORKBENCH_CONTRACT_REF = "contract-ref:fcc-mem-001-memory-workbench:v1"
MEMORY_RANKING_CONTRACT_REF = (
    "contract-ref:fcc-mem-022-ranked-retrieval-recall-tuning:v1"
)
MEMORY_WORKBENCH_ROUTE_REF = "GET /control-center/memory/workbench"
MEMORY_SEARCH_ROUTE_REF = "GET /control-center/memory/search"
MEMORY_MANUAL_INTAKE_ROUTE_REF = (
    "POST /control-center/memory/review/manual-candidate"
)
MEMORY_MANUAL_INTAKE_CONTRACT_REF = "contract-ref:fcc-mem-001-manual-intake:v1"
MEMORY_WORKBENCH_GROUPS = [
    "needs_review",
    "conflict",
    "duplicate",
    "stale",
    "missing_evidence",
    "reviewed",
    "rejected",
]
MEMORY_WORKBENCH_BLOCKED_STATE_REFS = [
    "blocked-state:memory-workbench-no-delete-execution",
    "blocked-state:memory-workbench-no-export-execution",
    "blocked-state:memory-workbench-no-context-injection",
    "blocked-state:memory-workbench-no-connector-write",
    "blocked-state:memory-workbench-no-semantic-search",
    "blocked-state:memory-workbench-no-vector-db",
    "blocked-state:memory-workbench-no-embeddings",
    "blocked-state:memory-workbench-no-model-provider-call",
    "blocked-state:memory-workbench-no-production-authority",
]
MEMORY_RANKING_BLOCKED_STATE_REFS = [
    "blocked-state:memory-ranking-no-embeddings",
    "blocked-state:memory-ranking-no-vector-db",
    "blocked-state:memory-ranking-no-semantic-provider",
    "blocked-state:memory-ranking-no-model-provider-call",
    "blocked-state:memory-ranking-no-context-injection",
    "blocked-state:memory-ranking-no-prompt-stuffing",
    "blocked-state:memory-ranking-no-memory-write",
    "blocked-state:memory-ranking-no-auto-merge",
    "blocked-state:memory-ranking-no-auto-forget",
    "blocked-state:memory-ranking-no-auto-maintenance",
    "blocked-state:memory-ranking-no-action-execution",
    "blocked-state:memory-ranking-no-connector-write",
    "blocked-state:memory-ranking-no-background-indexing",
    "blocked-state:memory-ranking-no-truth-authority",
    "blocked-state:memory-ranking-no-production-authority",
]
MEMORY_RANKING_COMPONENT_BOUNDS = {
    "lexical_safe_summary_title_match": 20,
    "tag_ref_match": 15,
    "entity_ref_match": 15,
    "relationship_ref_match": 10,
    "recency": 20,
    "reviewed_status": 20,
    "evidence_quality": 20,
    "citation_integrity": 15,
    "duplicate_pressure": 15,
    "conflict_pressure": 15,
    "stale_pressure": 15,
    "missing_evidence_pressure": 15,
    "loop_impact": 20,
    "source_diversity": 10,
    "operator_feedback_quality_issue": 15,
}
MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS = [
    "blocked-state:manual-memory-intake-no-recall-record",
    "blocked-state:manual-memory-intake-no-context-injection",
    "blocked-state:manual-memory-intake-no-connector-write",
    "blocked-state:manual-memory-intake-no-delete-execution",
    "blocked-state:manual-memory-intake-no-export-execution",
    "blocked-state:manual-memory-intake-no-production-authority",
]

MemoryWorkbenchGroup = Literal[
    "needs_review",
    "conflict",
    "duplicate",
    "stale",
    "missing_evidence",
    "reviewed",
    "rejected",
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
    "raw path",
    "raw_path",
    "raw-path",
    "raw log",
    "raw_log",
    "raw-log",
    "account identifier",
    "account_identifier",
    "account-identifier",
    "username",
    "hostname",
    "credential",
    "private key",
    "private_key",
    "api key",
    "api_key",
    "authorization",
    "bearer",
    "oauth",
    "cookie",
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
_REVIEWED_STATES = {"accepted", "corrected", "reviewed"}
_REJECTED_STATES = {"rejected"}
_ATTENTION_STATES = {
    "review_needed",
    "needs_review",
    "deferred",
    "merged",
    "superseded",
    "forget_requested",
}


def _safe_text(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} is required")
    validate_safe_execution_text(text, field_name)
    lowered = text.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe memory workbench text")
    return text


def _safe_ref(value: Any, field_name: str, *, allow_empty: bool = False) -> str | None:
    text = _safe_text(value, field_name, allow_empty=allow_empty)
    if not text:
        return None
    validate_execution_ref(text, field_name)
    return text


def _safe_refs(values: Any, field_name: str) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        ref = _safe_ref(value, field_name, allow_empty=True)
        if ref is not None:
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _state_ref(prefix: str, value: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in ".-" else "-"
        for char in value.lower().replace("_", "-")
    ).strip("-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    return f"{prefix}:{normalized or 'missing'}"


def _short_digest(value: str, *, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[
        :length
    ]


def _payload_fingerprint(payload: dict[str, Any], *, prefix: str) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:{_short_digest(encoded, length=24)}"


def _iso_recency(created_at: Any) -> int:
    if not created_at:
        return 0
    try:
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError:
        return 1
    age_seconds = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds()
    if age_seconds < 60 * 60 * 24:
        return 20
    if age_seconds < 60 * 60 * 24 * 7:
        return 12
    if age_seconds < 60 * 60 * 24 * 30:
        return 6
    return 1


class ManualMemoryCandidateRequest(BaseModel):
    """Backend-owned manual intake request for a review candidate only."""

    candidate_kind: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    reviewer_ref: str = Field(default="actor-ref:local-operator", min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    related_entity_refs: list[str] = Field(default_factory=list)
    tag_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_request(self) -> "ManualMemoryCandidateRequest":
        _safe_text(self.candidate_kind, "candidate_kind")
        _safe_text(self.title, "title")
        _safe_text(self.safe_summary, "safe_summary")
        _safe_text(self.priority, "priority")
        _safe_ref(self.reviewer_ref, "reviewer_ref")
        for field_name in [
            "source_refs",
            "provenance_refs",
            "evidence_refs",
            "missing_evidence_refs",
            "related_entity_refs",
            "tag_refs",
            "metadata_refs",
            "blocked_state_refs",
        ]:
            setattr(self, field_name, _safe_refs(getattr(self, field_name), field_name))
        if not self.provenance_refs:
            raise ValueError("provenance_refs are required for manual memory intake")
        if not self.source_refs:
            raise ValueError("source_refs are required for manual memory intake")
        if not self.evidence_refs and not self.missing_evidence_refs:
            raise ValueError(
                "manual memory intake requires evidence refs or missing evidence posture"
            )
        missing_blocked = [
            ref
            for ref in MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing_blocked:
            raise ValueError("manual memory intake request missing blocked state refs")
        return self


def manual_memory_candidate_payload_for_fingerprint(
    request: ManualMemoryCandidateRequest,
) -> dict[str, Any]:
    return {
        "candidate_kind": request.candidate_kind,
        "title": request.title,
        "safe_summary": request.safe_summary,
        "priority": request.priority,
        "reviewer_ref": request.reviewer_ref,
        "source_refs": list(request.source_refs),
        "provenance_refs": list(request.provenance_refs),
        "evidence_refs": list(request.evidence_refs),
        "missing_evidence_refs": list(request.missing_evidence_refs),
        "related_entity_refs": list(request.related_entity_refs),
        "tag_refs": list(request.tag_refs),
        "metadata_refs": list(request.metadata_refs),
        "blocked_state_refs": list(request.blocked_state_refs),
    }


def manual_memory_candidate_payload_fingerprint_ref(
    payload: dict[str, Any],
) -> str:
    return _payload_fingerprint(payload, prefix="payload-fingerprint:manual-memory-candidate")


def manual_memory_candidate_ref(idempotency_key_ref: str) -> str:
    _safe_ref(idempotency_key_ref, "idempotency_key_ref")
    return f"memory-review:manual-candidate:{_short_digest(idempotency_key_ref, length=12)}"


def build_memory_workbench(
    *,
    candidates: list[dict[str, Any]],
    decision_receipts: list[dict[str, Any]],
    l1_index: dict[str, Any],
    l2_index: dict[str, Any],
    l3_index: dict[str, Any],
    context_packs: dict[str, Any],
    loop_refs: list[str] | None = None,
    query_ref: str | None = None,
) -> dict[str, Any]:
    """Build the FCC-MEM-001 safe-ref-only Memory Workbench read model."""

    loop_ref_set = set(_safe_refs(loop_refs or [], "loop_refs"))
    safe_query_ref = _safe_ref(query_ref, "query_ref", allow_empty=True)
    receipt_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for receipt in decision_receipts:
        for key in ["candidate_ref", "review_ref"]:
            value = receipt.get(key)
            if value:
                receipt_by_candidate.setdefault(str(value), []).append(receipt)

    workbench_items: list[dict[str, Any]] = []
    for candidate in candidates:
        workbench_items.append(
            _candidate_workbench_item(
                candidate,
                receipt_by_candidate=receipt_by_candidate,
                loop_refs=loop_ref_set,
            )
        )

    for preview in l1_index.get("previews", []) or []:
        workbench_items.append(_l1_workbench_item(dict(preview), loop_refs=loop_ref_set))

    duplicate_keys: dict[str, list[str]] = {}
    conflict_keys: dict[str, list[str]] = {}
    for item in workbench_items:
        duplicate_keys.setdefault(str(item["duplicate_key_ref"]), []).append(
            str(item["memory_ref"])
        )
        conflict_keys.setdefault(str(item["conflict_key_ref"]), []).append(
            str(item["memory_ref"])
        )

    for item in workbench_items:
        duplicate_refs = [
            ref
            for ref in duplicate_keys.get(str(item["duplicate_key_ref"]), [])
            if ref != item["memory_ref"]
        ]
        conflict_refs = [
            ref
            for ref in conflict_keys.get(str(item["conflict_key_ref"]), [])
            if ref != item["memory_ref"]
            and ref not in duplicate_refs
            and item["review_state"] not in _REVIEWED_STATES
        ]
        if duplicate_refs:
            item["duplicate_of_refs"] = duplicate_refs
            item["quality_state_refs"].append("business-memory-quality:duplicate")
            item["quality_reason_refs"].append(
                "quality-reason-ref:duplicate-safe-ref-kind-tag-entity-match"
            )
        if conflict_refs:
            item["conflict_with_refs"] = conflict_refs
            item["quality_state_refs"].append("business-memory-quality:conflict")
            item["quality_reason_refs"].append(
                "quality-reason-ref:conflict-kind-related-entity-state-match"
            )
        item["quality_state_refs"] = sorted(set(item["quality_state_refs"]))
        item["quality_reason_refs"] = sorted(set(item["quality_reason_refs"]))
        item["group_ids"] = _groups_for_item(item)
        item.update(
            _ranked_memory_payload(
                item,
                query_ref=safe_query_ref,
                loop_refs=loop_ref_set,
            )
        )

    ranked_items = sorted(
        workbench_items,
        key=lambda item: (-int(item["rank_score"]), str(item["memory_ref"])),
    )
    group_counts = {
        group: sum(1 for item in ranked_items if group in item["group_ids"])
        for group in MEMORY_WORKBENCH_GROUPS
    }
    health = {
        "schema_version": "fcc_mem_001_memory_health.v1",
        "pending_review_count": group_counts["needs_review"],
        "stale_count": group_counts["stale"],
        "conflict_count": group_counts["conflict"],
        "duplicate_count": group_counts["duplicate"],
        "missing_evidence_count": group_counts["missing_evidence"],
        "reviewed_recall_count": group_counts["reviewed"],
        "rejected_count": group_counts["rejected"],
        "needs_attention_refs": [
            item["memory_ref"]
            for item in ranked_items
            if any(
                group in item["group_ids"]
                for group in [
                    "conflict",
                    "duplicate",
                    "stale",
                    "missing_evidence",
                    "needs_review",
                ]
            )
        ],
    }
    read_model = {
        "schema_version": "fcc_mem_001_memory_workbench.v1",
        "contract_ref": MEMORY_WORKBENCH_CONTRACT_REF,
        "route_ref": MEMORY_WORKBENCH_ROUTE_REF,
        "status": "implemented_backend_owned_read_model_safe_refs_only",
        "groups": [
            {"group_id": group, "count": group_counts[group]}
            for group in MEMORY_WORKBENCH_GROUPS
        ],
        "items": ranked_items,
        "health": health,
        "decision_receipts": decision_receipts,
        "l1_preview_refs": [
            str(item.get("memory_record_ref")) for item in l1_index.get("previews", [])
        ],
        "l2_projection_refs": _projection_refs(l2_index),
        "l3_projection_refs": _projection_refs(l3_index),
        "context_pack_refs": [
            str(item.get("context_pack_ref"))
            for item in context_packs.get("proposals", []) or []
        ],
        "ranking": _ranking_read_model(
            ranked_items,
            query_ref=safe_query_ref,
        ),
        "blocked_state_refs": list(MEMORY_WORKBENCH_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "embedding_search_enabled": False,
        "context_injection_authorized": False,
        "memory_truth_authority": False,
        "production_authority_enabled": False,
    }
    return read_model


def filter_memory_workbench(
    *,
    workbench: dict[str, Any],
    query_ref: str | None = None,
    kind: str | None = None,
    source_ref: str | None = None,
    project_ref: str | None = None,
    person_ref: str | None = None,
    org_ref: str | None = None,
    deal_ref: str | None = None,
    review_state: str | None = None,
    quality_state: str | None = None,
    stale_state: str | None = None,
    conflict_state: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Read-only safe-ref search over reviewed summaries and candidate refs."""

    filters = {
        "query_ref": _safe_ref(query_ref, "query_ref", allow_empty=True)
        if query_ref
        else None,
        "kind": _safe_text(kind, "kind", allow_empty=True) if kind else None,
        "source_ref": _safe_ref(source_ref, "source_ref", allow_empty=True)
        if source_ref
        else None,
        "project_ref": _safe_ref(project_ref, "project_ref", allow_empty=True)
        if project_ref
        else None,
        "person_ref": _safe_ref(person_ref, "person_ref", allow_empty=True)
        if person_ref
        else None,
        "org_ref": _safe_ref(org_ref, "org_ref", allow_empty=True)
        if org_ref
        else None,
        "deal_ref": _safe_ref(deal_ref, "deal_ref", allow_empty=True)
        if deal_ref
        else None,
        "review_state": _safe_text(review_state, "review_state", allow_empty=True)
        if review_state
        else None,
        "quality_state": _safe_text(quality_state, "quality_state", allow_empty=True)
        if quality_state
        else None,
        "stale_state": _safe_text(stale_state, "stale_state", allow_empty=True)
        if stale_state
        else None,
        "conflict_state": _safe_text(conflict_state, "conflict_state", allow_empty=True)
        if conflict_state
        else None,
    }
    items = list(workbench.get("items", []) or [])
    filtered = [
        item
        for item in items
        if _matches_filters(item, filters)
    ][: max(1, min(int(limit), 50))]
    return {
        "schema_version": "fcc_mem_001_memory_search.v1",
        "contract_ref": MEMORY_WORKBENCH_CONTRACT_REF,
        "route_ref": MEMORY_SEARCH_ROUTE_REF,
        "filters": {key: value for key, value in filters.items() if value},
        "items": filtered,
        "count": len(filtered),
        "total_workbench_count": len(items),
        "ranking": _ranking_read_model(
            filtered,
            query_ref=filters["query_ref"],
            status="implemented_filtered_ranked_read_model_safe_refs_only",
        ),
        "safe_refs_only": True,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "embedding_search_enabled": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_WORKBENCH_BLOCKED_STATE_REFS),
    }


def _candidate_workbench_item(
    candidate: dict[str, Any],
    *,
    receipt_by_candidate: dict[str, list[dict[str, Any]]],
    loop_refs: set[str],
) -> dict[str, Any]:
    review_ref = _safe_ref(candidate.get("review_ref"), "review_ref") or ""
    memory_ref = _safe_ref(
        candidate.get("business_memory_candidate_ref") or review_ref,
        "business_memory_candidate_ref",
    ) or review_ref
    candidate_kind = _safe_text(candidate.get("candidate_kind"), "candidate_kind")
    source_refs = _safe_refs(candidate.get("source_refs"), "source_refs")
    provenance_refs = _safe_refs(candidate.get("provenance_refs"), "provenance_refs")
    evidence_refs = _safe_refs(candidate.get("evidence_refs"), "evidence_refs")
    related_entity_refs = _related_entity_refs(candidate)
    tag_refs = _tag_refs(candidate)
    receipts = [
        *receipt_by_candidate.get(memory_ref, []),
        *receipt_by_candidate.get(review_ref, []),
    ]
    receipt_refs = _safe_refs(
        [receipt.get("receipt_ref") for receipt in receipts],
        "receipt_refs",
    )
    quality_state_refs = _quality_seed(candidate)
    quality_reason_refs = [
        "quality-reason-ref:backend-memory-review-candidate",
    ]
    if not evidence_refs:
        quality_state_refs.append("business-memory-quality:evidence-missing")
        quality_reason_refs.append("quality-reason-ref:missing-evidence-refs")
    stale_state = _safe_text(candidate.get("stale_state"), "stale_state")
    if _is_stale_state(stale_state):
        quality_state_refs.append("business-memory-quality:stale-expired")
        quality_reason_refs.append("quality-reason-ref:stale-state-or-recheck-posture")
    review_state = _safe_text(candidate.get("review_state"), "review_state")
    if review_state in _REVIEWED_STATES:
        quality_state_refs.append("business-memory-quality:reviewed")
        quality_reason_refs.append("quality-reason-ref:operator-reviewed")
    if candidate.get("missing_contract_refs"):
        quality_reason_refs.append("quality-reason-ref:missing-contract-posture")
    why_shown_refs = _why_shown_refs(
        item_refs=[
            memory_ref,
            review_ref,
            *source_refs,
            *evidence_refs,
            *related_entity_refs,
            *tag_refs,
        ],
        review_state=review_state,
        priority=str(candidate.get("priority", "")),
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        tag_refs=tag_refs,
        loop_refs=loop_refs,
        created_at=candidate.get("created_at"),
    )
    return {
        "memory_ref": memory_ref,
        "review_ref": review_ref,
        "source": "memory_review_queue",
        "title": _safe_text(candidate.get("title"), "title"),
        "safe_summary": _safe_text(candidate.get("safe_summary"), "safe_summary"),
        "candidate_kind": candidate_kind,
        "priority": _safe_text(candidate.get("priority"), "priority"),
        "status": _safe_text(candidate.get("status"), "status"),
        "review_state": review_state,
        "stale_state": stale_state,
        "conflict_state": "candidate_conflicts_detected_if_refs_match",
        "side_effect_class": _safe_text(
            candidate.get("side_effect_class"), "side_effect_class"
        ),
        "authority_boundary": _safe_text(
            candidate.get("authority_boundary"), "authority_boundary"
        ),
        "source_refs": source_refs,
        "provenance_refs": provenance_refs,
        "evidence_refs": evidence_refs,
        "missing_contract_refs": _safe_refs(
            candidate.get("missing_contract_refs"), "missing_contract_refs"
        ),
        "related_entity_refs": related_entity_refs,
        "tag_refs": tag_refs,
        "blocked_state_refs": _normalize_blocked_refs(candidate.get("blocked_states")),
        "receipt_refs": receipt_refs,
        "quality_state_refs": sorted(set(quality_state_refs)),
        "quality_reason_refs": sorted(set(quality_reason_refs)),
        "why_shown_refs": why_shown_refs,
        "duplicate_key_ref": _duplicate_key_ref(
            candidate_kind=candidate_kind,
            source_refs=source_refs,
            related_entity_refs=related_entity_refs,
            tag_refs=tag_refs,
        ),
        "conflict_key_ref": _conflict_key_ref(
            candidate_kind=candidate_kind,
            related_entity_refs=related_entity_refs,
        ),
        "next_safe_action": _safe_text(
            candidate.get("next_safe_action"), "next_safe_action"
        ),
        "created_at": str(candidate.get("created_at") or ""),
    }


def _l1_workbench_item(
    preview: dict[str, Any],
    *,
    loop_refs: set[str],
) -> dict[str, Any]:
    memory_ref = _safe_ref(
        preview.get("memory_record_ref") or preview.get("memory_ref"),
        "memory_record_ref",
    ) or "memory-record-ref:missing"
    source_refs = _safe_refs(preview.get("source_refs"), "source_refs")
    evidence_refs = _safe_refs(preview.get("evidence_refs"), "evidence_refs")
    receipt_refs = _safe_refs(preview.get("receipt_refs"), "receipt_refs")
    candidate_kind = _safe_text(
        preview.get("memory_kind") or preview.get("candidate_kind") or "preference",
        "candidate_kind",
    )
    related_entity_refs = _related_entity_refs(preview)
    tag_refs = _tag_refs(preview)
    why_shown_refs = _why_shown_refs(
        item_refs=[memory_ref, *source_refs, *evidence_refs, *receipt_refs],
        review_state="reviewed",
        priority="medium",
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        tag_refs=tag_refs,
        loop_refs=loop_refs,
        created_at=preview.get("updated_at") or preview.get("created_at"),
    )
    return {
        "memory_ref": memory_ref,
        "review_ref": str(preview.get("review_ref") or memory_ref),
        "source": "l1_reviewed_recall_projection",
        "title": _safe_text(preview.get("safe_title") or "Reviewed recall", "title"),
        "safe_summary": _safe_text(
            preview.get("safe_summary") or "Reviewed recall safe summary.",
            "safe_summary",
        ),
        "candidate_kind": candidate_kind,
        "priority": "medium",
        "status": "reviewed",
        "review_state": "reviewed",
        "stale_state": _safe_text(
            preview.get("stale_state") or "review_receipt_required_before_reuse",
            "stale_state",
        ),
        "conflict_state": "reviewed_projection_no_conflict_execution",
        "side_effect_class": "local_dev_workspace_only",
        "authority_boundary": (
            "Reviewed recall projection is not truth, approval, execution, or context injection."
        ),
        "source_refs": source_refs,
        "provenance_refs": _safe_refs(preview.get("provenance_refs"), "provenance_refs"),
        "evidence_refs": evidence_refs,
        "missing_contract_refs": [],
        "related_entity_refs": related_entity_refs,
        "tag_refs": tag_refs,
        "blocked_state_refs": list(MEMORY_WORKBENCH_BLOCKED_STATE_REFS),
        "receipt_refs": receipt_refs,
        "quality_state_refs": ["business-memory-quality:reviewed"],
        "quality_reason_refs": ["quality-reason-ref:l1-reviewed-recall-projection"],
        "why_shown_refs": why_shown_refs,
        "duplicate_key_ref": _duplicate_key_ref(
            candidate_kind=candidate_kind,
            source_refs=source_refs,
            related_entity_refs=related_entity_refs,
            tag_refs=tag_refs,
        ),
        "conflict_key_ref": _conflict_key_ref(
            candidate_kind=candidate_kind,
            related_entity_refs=related_entity_refs,
        ),
        "next_safe_action": "Inspect the review receipt before using recall refs.",
        "created_at": str(preview.get("created_at") or preview.get("updated_at") or ""),
    }


def _related_entity_refs(item: dict[str, Any]) -> list[str]:
    refs = [
        *list(item.get("business_memory_related_entity_refs") or []),
        *list(item.get("related_entity_refs") or []),
        *list(item.get("metadata_refs") or []),
    ]
    for ref in list(item.get("source_refs") or []):
        if any(marker in str(ref) for marker in ["person", "org", "deal", "project"]):
            refs.append(str(ref))
    return _safe_refs(refs, "related_entity_refs")


def _tag_refs(item: dict[str, Any]) -> list[str]:
    refs = list(item.get("tag_refs") or [])
    for tag in item.get("tags") or []:
        refs.append(_state_ref("tag-ref", str(tag)))
    if item.get("candidate_kind"):
        refs.append(_state_ref("memory-kind-ref", str(item["candidate_kind"])))
    return _safe_refs(refs, "tag_refs")


def _quality_seed(item: dict[str, Any]) -> list[str]:
    refs = [
        str(ref)
        for ref in item.get("business_memory_quality_state_refs") or []
        if str(ref)
    ]
    return _safe_refs(refs, "quality_state_refs")


def _normalize_blocked_refs(values: Any) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        text = str(value)
        refs.append(text if text.startswith("blocked-state:") else f"blocked-state:{text}")
    return _safe_refs(refs, "blocked_state_refs")


def _duplicate_key_ref(
    *,
    candidate_kind: str,
    source_refs: list[str],
    related_entity_refs: list[str],
    tag_refs: list[str],
) -> str:
    payload = "|".join(
        [
            candidate_kind,
            ",".join(sorted(source_refs)),
            ",".join(sorted(related_entity_refs)),
            ",".join(sorted(tag_refs)),
        ]
    )
    return f"duplicate-key-ref:memory-workbench:{_short_digest(payload)}"


def _conflict_key_ref(
    *,
    candidate_kind: str,
    related_entity_refs: list[str],
) -> str:
    entity_key = ",".join(sorted(related_entity_refs)) or "unbound"
    return f"conflict-key-ref:memory-workbench:{_short_digest(candidate_kind + '|' + entity_key)}"


def _is_stale_state(stale_state: str) -> bool:
    lowered = stale_state.lower()
    return any(marker in lowered for marker in ["stale", "expired", "recheck"])


def _why_shown_refs(
    *,
    item_refs: list[str],
    review_state: str,
    priority: str,
    source_refs: list[str],
    evidence_refs: list[str],
    tag_refs: list[str],
    loop_refs: set[str],
    created_at: Any,
) -> list[str]:
    why = ["why-shown-ref:memory-workbench-safe-ref-review"]
    if review_state in _ATTENTION_STATES:
        why.append("why-shown-ref:review-state-needs-attention")
    if review_state in _REVIEWED_STATES:
        why.append("why-shown-ref:reviewed-recall-available")
    if priority.lower() == "high":
        why.append("why-shown-ref:high-priority-review")
    if source_refs:
        why.append("why-shown-ref:source-refs-present")
    if evidence_refs:
        why.append("why-shown-ref:evidence-present")
    else:
        why.append("why-shown-ref:missing-evidence")
    if tag_refs:
        why.append("why-shown-ref:explicit-tags")
    if loop_refs.intersection(set(item_refs)):
        why.append("why-shown-ref:current-loop-relevance")
    if _iso_recency(created_at) >= 12:
        why.append("why-shown-ref:recent-capture")
    return list(dict.fromkeys(why))


def _groups_for_item(item: dict[str, Any]) -> list[MemoryWorkbenchGroup]:
    groups: list[MemoryWorkbenchGroup] = []
    review_state = str(item.get("review_state", "review_needed"))
    quality_refs = set(item.get("quality_state_refs") or [])
    if review_state in _ATTENTION_STATES:
        groups.append("needs_review")
    if "business-memory-quality:conflict" in quality_refs:
        groups.append("conflict")
    if "business-memory-quality:duplicate" in quality_refs:
        groups.append("duplicate")
    if "business-memory-quality:stale-expired" in quality_refs:
        groups.append("stale")
    if "business-memory-quality:evidence-missing" in quality_refs:
        groups.append("missing_evidence")
    if review_state in _REVIEWED_STATES:
        groups.append("reviewed")
    if review_state in _REJECTED_STATES:
        groups.append("rejected")
    if not groups:
        groups.append("needs_review")
    return list(dict.fromkeys(groups))


def _ranked_memory_payload(
    item: dict[str, Any],
    *,
    query_ref: str | None,
    loop_refs: set[str],
) -> dict[str, Any]:
    components = _rank_components(item, query_ref=query_ref, loop_refs=loop_refs)
    rank_score = min(sum(components.values()), sum(MEMORY_RANKING_COMPONENT_BOUNDS.values()))
    excluded_reason_refs = _excluded_reason_refs(item)
    return {
        "rank_score": rank_score,
        "rank_components": components,
        "included_reason_refs": _included_reason_refs(
            item,
            components,
            excluded_reason_refs=excluded_reason_refs,
        ),
        "excluded_reason_refs": excluded_reason_refs,
        "stale_pressure": _pressure_flag(item, "stale"),
        "conflict_pressure": _pressure_flag(item, "conflict"),
        "duplicate_pressure": _pressure_flag(item, "duplicate"),
        "missing_evidence_pressure": _pressure_flag(item, "missing_evidence"),
        "source_mix": _source_mix(item),
        "cache_key": _item_cache_key(item, components),
        "token_estimate": _token_estimate(item),
        "ranking_blocked_authority_refs": list(MEMORY_RANKING_BLOCKED_STATE_REFS),
        "why_ranked_refs": _why_ranked_refs(item, components, excluded_reason_refs),
    }


def _rank_components(
    item: dict[str, Any],
    *,
    query_ref: str | None,
    loop_refs: set[str],
) -> dict[str, int]:
    query_tokens = _ranking_query_tokens(query_ref=query_ref, loop_refs=loop_refs)
    title_summary_tokens = set(
        _tokenize_ranking_text(
            " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("safe_summary") or ""),
                    str(item.get("candidate_kind") or ""),
                ]
            )
        )
    )
    ref_tokens = set(
        _tokenize_ranking_text(
            " ".join(
                [
                    str(item.get("memory_ref") or ""),
                    str(item.get("review_ref") or ""),
                    *list(item.get("source_refs") or []),
                    *list(item.get("evidence_refs") or []),
                    *list(item.get("related_entity_refs") or []),
                    *list(item.get("tag_refs") or []),
                    *list(item.get("receipt_refs") or []),
                ]
            )
        )
    )
    tag_tokens = set(_tokenize_ranking_text(" ".join(item.get("tag_refs") or [])))
    entity_tokens = set(
        _tokenize_ranking_text(" ".join(item.get("related_entity_refs") or []))
    )
    groups = set(item.get("group_ids") or [])
    quality_refs = list(item.get("quality_state_refs") or [])
    evidence_refs = list(item.get("evidence_refs") or [])
    source_refs = list(item.get("source_refs") or [])
    receipt_refs = list(item.get("receipt_refs") or [])
    review_state = str(item.get("review_state") or "")
    exact_loop_refs = {
        str(value)
        for value in [
            item.get("memory_ref"),
            item.get("review_ref"),
            *source_refs,
            *evidence_refs,
            *list(item.get("related_entity_refs") or []),
            *list(item.get("tag_refs") or []),
            *receipt_refs,
        ]
        if value
    }.intersection(loop_refs)
    component_values = {
        "lexical_safe_summary_title_match": len(query_tokens & title_summary_tokens) * 5,
        "tag_ref_match": len(query_tokens & tag_tokens) * 5,
        "entity_ref_match": len(query_tokens & entity_tokens) * 5,
        "relationship_ref_match": len(item.get("related_entity_refs") or []) * 2,
        "recency": _iso_recency(item.get("created_at")),
        "reviewed_status": 20 if review_state in _REVIEWED_STATES else 0,
        "evidence_quality": 20
        if evidence_refs and "missing_evidence" not in groups
        else 8
        if evidence_refs
        else 0,
        "citation_integrity": 15
        if evidence_refs and source_refs and (receipt_refs or review_state in _REVIEWED_STATES)
        else 8
        if evidence_refs and source_refs
        else 0,
        "duplicate_pressure": 15 if "duplicate" in groups else 0,
        "conflict_pressure": 15 if "conflict" in groups else 0,
        "stale_pressure": 15 if "stale" in groups else 0,
        "missing_evidence_pressure": 15 if "missing_evidence" in groups else 0,
        "loop_impact": 20
        if exact_loop_refs
        else 10
        if query_tokens & ref_tokens
        or "why-shown-ref:current-loop-relevance" in item.get("why_shown_refs", [])
        else 0,
        "source_diversity": len(_source_mix(item)) * 2,
        "operator_feedback_quality_issue": min(len(quality_refs) * 4, 15),
    }
    return {
        key: max(0, min(int(component_values.get(key, 0)), bound))
        for key, bound in MEMORY_RANKING_COMPONENT_BOUNDS.items()
    }


def _ranking_read_model(
    ranked_items: list[dict[str, Any]],
    *,
    query_ref: str | None,
    status: str = "implemented_ranked_read_model_safe_refs_only",
) -> dict[str, Any]:
    ranked_candidate_refs = [str(item["memory_ref"]) for item in ranked_items]
    included_ranked_refs = [
        str(item["memory_ref"])
        for item in ranked_items
        if not item.get("excluded_reason_refs")
    ]
    excluded_refs = [
        {
            "memory_ref": str(item["memory_ref"]),
            "reason_refs": list(item.get("excluded_reason_refs") or []),
        }
        for item in ranked_items
        if item.get("excluded_reason_refs")
    ]
    payload_for_cache = {
        "query_ref": query_ref or "query-ref:memory-ranking:default",
        "ranked_refs": ranked_candidate_refs,
        "included_refs": included_ranked_refs,
        "scores": [
            [str(item["memory_ref"]), int(item.get("rank_score", 0))]
            for item in ranked_items
        ],
    }
    return {
        "schema_version": "fcc_mem_022_ranked_retrieval_recall_tuning.v1",
        "contract_ref": MEMORY_RANKING_CONTRACT_REF,
        "status": status,
        "query_ref": query_ref or "query-ref:memory-ranking:default",
        "candidate_count": len(ranked_items),
        "ranked_candidate_refs": ranked_candidate_refs,
        "included_ranked_refs": included_ranked_refs,
        "excluded_refs": excluded_refs,
        "excluded_ref_count": len(excluded_refs),
        "score_component_bounds": dict(MEMORY_RANKING_COMPONENT_BOUNDS),
        "source_mix": _aggregate_source_mix(ranked_items),
        "pressure_counts": {
            "stale": sum(1 for item in ranked_items if item.get("stale_pressure")),
            "conflict": sum(1 for item in ranked_items if item.get("conflict_pressure")),
            "duplicate": sum(1 for item in ranked_items if item.get("duplicate_pressure")),
            "missing_evidence": sum(
                1 for item in ranked_items if item.get("missing_evidence_pressure")
            ),
        },
        "cache_key": _payload_fingerprint(
            payload_for_cache,
            prefix="cache-key:fcc-mem-022-ranking",
        ),
        "cache_hit": False,
        "token_estimate": sum(int(item.get("token_estimate", 0)) for item in ranked_items),
        "rank_signal_refs": _rank_signal_refs(ranked_items),
        "blocked_authority_refs": list(MEMORY_RANKING_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "lexical_tag_ref_only": True,
        "embedding_search_enabled": False,
        "vector_db_enabled": False,
        "semantic_provider_enabled": False,
        "context_injection_authorized": False,
        "memory_write_performed": False,
        "auto_maintenance_performed": False,
        "action_execution_authorized": False,
        "production_authority_enabled": False,
    }


def _excluded_reason_refs(item: dict[str, Any]) -> list[str]:
    reason_refs: list[str] = []
    groups = set(item.get("group_ids") or [])
    review_state = str(item.get("review_state") or "")
    if review_state not in _REVIEWED_STATES:
        reason_refs.append("rank-exclusion-ref:not-reviewed-recall")
    if "conflict" in groups:
        reason_refs.append("rank-exclusion-ref:conflict-pressure")
    if "duplicate" in groups:
        reason_refs.append("rank-exclusion-ref:duplicate-pressure")
    if "missing_evidence" in groups:
        reason_refs.append("rank-exclusion-ref:missing-evidence-pressure")
    if "stale" in groups:
        reason_refs.append("rank-exclusion-ref:stale-pressure")
    if not item.get("evidence_refs"):
        reason_refs.append("rank-exclusion-ref:evidence-missing")
    return list(dict.fromkeys(reason_refs))


def _included_reason_refs(
    item: dict[str, Any],
    components: dict[str, int],
    *,
    excluded_reason_refs: list[str],
) -> list[str]:
    reason_refs = ["rank-include-ref:operator-review-read-model"]
    component_reason_refs = {
        "lexical_safe_summary_title_match": "rank-include-ref:lexical-safe-summary-title-match",
        "tag_ref_match": "rank-include-ref:tag-ref-match",
        "entity_ref_match": "rank-include-ref:entity-ref-match",
        "relationship_ref_match": "rank-include-ref:relationship-ref-match",
        "recency": "rank-include-ref:recency",
        "reviewed_status": "rank-include-ref:reviewed-status",
        "evidence_quality": "rank-include-ref:evidence-quality",
        "citation_integrity": "rank-include-ref:citation-integrity",
        "duplicate_pressure": "rank-include-ref:duplicate-pressure-visible",
        "conflict_pressure": "rank-include-ref:conflict-pressure-visible",
        "stale_pressure": "rank-include-ref:stale-pressure-visible",
        "missing_evidence_pressure": "rank-include-ref:missing-evidence-pressure-visible",
        "loop_impact": "rank-include-ref:loop-impact",
        "source_diversity": "rank-include-ref:source-diversity",
        "operator_feedback_quality_issue": "rank-include-ref:operator-feedback-quality-issue",
    }
    for key, reason_ref in component_reason_refs.items():
        if components.get(key, 0) > 0:
            reason_refs.append(reason_ref)
    if excluded_reason_refs:
        reason_refs.append("rank-include-ref:visible-but-recall-use-blocked")
    return list(dict.fromkeys(reason_refs))


def _why_ranked_refs(
    item: dict[str, Any],
    components: dict[str, int],
    excluded_reason_refs: list[str],
) -> list[str]:
    why = list(item.get("why_shown_refs") or [])
    why.append("why-ranked-ref:fcc-mem-022-lexical-tag-ref-only")
    top_components = [
        key for key, value in sorted(components.items(), key=lambda pair: (-pair[1], pair[0]))
        if value > 0
    ][:5]
    why.extend(f"why-ranked-ref:{key.replace('_', '-')}" for key in top_components)
    if excluded_reason_refs:
        why.append("why-ranked-ref:recall-use-blocked-by-reason-refs")
    return list(dict.fromkeys(why))


def _pressure_flag(item: dict[str, Any], group_id: str) -> int:
    return 1 if group_id in set(item.get("group_ids") or []) else 0


def _source_mix(item: dict[str, Any]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    source = _safe_text(item.get("source") or "unknown", "source")
    counts[f"source:{source}"] = counts.get(f"source:{source}", 0) + 1
    for ref in item.get("source_refs") or []:
        source_kind = str(ref).split(":", 2)[:2]
        key = ":".join(source_kind) if source_kind else "source-ref:unknown"
        counts[key] = counts.get(key, 0) + 1
    return [
        {"source_ref": key, "count": count}
        for key, count in sorted(counts.items())
    ]


def _aggregate_source_mix(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        for entry in item.get("source_mix") or []:
            source_ref = str(entry.get("source_ref") or "")
            if not source_ref:
                continue
            counts[source_ref] = counts.get(source_ref, 0) + int(entry.get("count", 0))
    return [
        {"source_ref": source_ref, "count": count}
        for source_ref, count in sorted(counts.items())
    ]


def _token_estimate(item: dict[str, Any]) -> int:
    text = " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("safe_summary") or ""),
            " ".join(item.get("why_shown_refs") or []),
            " ".join(item.get("quality_reason_refs") or []),
        ]
    )
    return max(1, min(2048, (len(text) + 3) // 4))


def _item_cache_key(item: dict[str, Any], components: dict[str, int]) -> str:
    return _payload_fingerprint(
        {
            "memory_ref": item.get("memory_ref"),
            "review_ref": item.get("review_ref"),
            "components": components,
            "quality_state_refs": item.get("quality_state_refs") or [],
            "why_shown_refs": item.get("why_shown_refs") or [],
        },
        prefix="cache-key:fcc-mem-022-ranking-item",
    )


def _rank_signal_refs(items: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for item in items:
        refs.extend(item.get("included_reason_refs") or [])
        refs.extend(item.get("excluded_reason_refs") or [])
    return sorted(set(refs))


def _ranking_query_tokens(
    *,
    query_ref: str | None,
    loop_refs: set[str],
) -> set[str]:
    query_text = " ".join([query_ref or "", *sorted(loop_refs)])
    return set(_tokenize_ranking_text(query_text))


def _tokenize_ranking_text(value: str) -> list[str]:
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


def _projection_refs(index: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in [
        "facts",
        "graph_relations",
        "temporal_items",
        "items",
        "model_items",
        "proposals",
    ]:
        for item in index.get(key, []) or []:
            if isinstance(item, dict):
                for ref_key in [
                    "fact_ref",
                    "relation_ref",
                    "temporal_ref",
                    "l3_item_ref",
                    "context_pack_ref",
                    "memory_record_ref",
                ]:
                    value = item.get(ref_key)
                    if value:
                        refs.append(str(value))
    return _safe_refs(refs, "projection_refs")


def _matches_filters(item: dict[str, Any], filters: dict[str, str | None]) -> bool:
    if filters["query_ref"]:
        refs = set(
            str(value)
            for value in [
                item.get("memory_ref"),
                item.get("review_ref"),
                *list(item.get("source_refs") or []),
                *list(item.get("evidence_refs") or []),
                *list(item.get("related_entity_refs") or []),
                *list(item.get("tag_refs") or []),
                *list(item.get("receipt_refs") or []),
            ]
            if value
        )
        if filters["query_ref"] not in refs:
            return False
    if filters["kind"] and item.get("candidate_kind") != filters["kind"]:
        return False
    if filters["source_ref"] and filters["source_ref"] not in item.get("source_refs", []):
        return False
    for key in ["project_ref", "person_ref", "org_ref", "deal_ref"]:
        value = filters.get(key)
        if value and value not in item.get("related_entity_refs", []):
            return False
    if filters["review_state"] and item.get("review_state") != filters["review_state"]:
        return False
    if filters["quality_state"]:
        quality_ref = (
            filters["quality_state"]
            if str(filters["quality_state"]).startswith("business-memory-quality:")
            else _state_ref("business-memory-quality", str(filters["quality_state"]))
        )
        if quality_ref not in item.get("quality_state_refs", []):
            return False
    if filters["stale_state"] and filters["stale_state"] != item.get("stale_state"):
        return False
    if filters["conflict_state"]:
        has_conflict = "business-memory-quality:conflict" in item.get(
            "quality_state_refs", []
        )
        if filters["conflict_state"] == "conflict" and not has_conflict:
            return False
        if filters["conflict_state"] == "clear" and has_conflict:
            return False
    return True


__all__ = [
    "MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS",
    "MEMORY_MANUAL_INTAKE_CONTRACT_REF",
    "MEMORY_MANUAL_INTAKE_ROUTE_REF",
    "MEMORY_RANKING_BLOCKED_STATE_REFS",
    "MEMORY_RANKING_COMPONENT_BOUNDS",
    "MEMORY_RANKING_CONTRACT_REF",
    "MEMORY_SEARCH_ROUTE_REF",
    "MEMORY_WORKBENCH_BLOCKED_STATE_REFS",
    "MEMORY_WORKBENCH_CONTRACT_REF",
    "MEMORY_WORKBENCH_GROUPS",
    "MEMORY_WORKBENCH_ROUTE_REF",
    "ManualMemoryCandidateRequest",
    "build_memory_workbench",
    "filter_memory_workbench",
    "manual_memory_candidate_payload_fingerprint_ref",
    "manual_memory_candidate_payload_for_fingerprint",
    "manual_memory_candidate_ref",
]
