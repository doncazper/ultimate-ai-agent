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
from ultimate_ai_agent.core.memory.feature_mine import (
    MEMORY_SAFE_QUERY_BLOCKED_STATE_REFS,
    memory_hrr_readiness,
    validate_query_mode,
)


MEMORY_WORKBENCH_CONTRACT_REF = "contract-ref:fcc-mem-001-memory-workbench:v1"
MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF = (
    "contract-ref:memory-merge-supersede-posture:v1"
)
MEMORY_LEARNING_POSTURE_CONTRACT_REF = (
    "contract-ref:goatcitadel-catchup-memory-learning-posture:v1"
)
MEMORY_RANKING_CONTRACT_REF = (
    "contract-ref:fcc-mem-022-ranked-retrieval-recall-tuning:v1"
)
MEMORY_WORKBENCH_ROUTE_REF = "GET /control-center/memory/workbench"
MEMORY_SEARCH_ROUTE_REF = "GET /control-center/memory/search"
MEMORY_IMPACT_GRAPH_CONTRACT_REF = (
    "contract-ref:fcc-mem-015-memory-impact-graph:v1"
)
MEMORY_IMPACT_GRAPH_ROUTE_REF = "GET /control-center/memory/impact-graph"
MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF = (
    "contract-ref:fcc-mem-015-memory-follow-up-queue:v1"
)
MEMORY_FOLLOW_UP_QUEUE_ROUTE_REF = "GET /control-center/memory/follow-ups"
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
MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS = [
    "blocked-state:memory-lifecycle-no-hard-delete",
    "blocked-state:memory-lifecycle-no-export-execution",
    "blocked-state:memory-lifecycle-no-auto-merge",
    "blocked-state:memory-lifecycle-no-auto-supersede",
    "blocked-state:memory-lifecycle-no-auto-forget",
    "blocked-state:memory-lifecycle-no-hidden-memory-write",
    "blocked-state:memory-lifecycle-no-context-injection",
    "blocked-state:memory-lifecycle-no-connector-write",
    "blocked-state:memory-lifecycle-no-model-provider-call",
    "blocked-state:memory-lifecycle-no-production-authority",
]
MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS = [
    "blocked-state:memory-learning-no-broad-memory-write",
    "blocked-state:memory-learning-no-automatic-memory-write",
    "blocked-state:memory-learning-no-hidden-context-injection",
    "blocked-state:memory-learning-no-memory-as-truth-authority",
    "blocked-state:memory-learning-no-policy-override",
    "blocked-state:memory-learning-no-action-execution",
    "blocked-state:memory-learning-no-connector-write",
    "blocked-state:memory-learning-no-model-provider-call",
    "blocked-state:memory-learning-no-live-web-fetch",
    "blocked-state:memory-learning-no-background-autonomy",
    "blocked-state:memory-learning-no-hard-delete",
    "blocked-state:memory-learning-no-export-execution",
    "blocked-state:memory-learning-no-production-authority",
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
MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS = [
    "blocked-state:memory-impact-graph-no-truth-authority",
    "blocked-state:memory-impact-graph-no-context-injection",
    "blocked-state:memory-impact-graph-no-action-execution",
    "blocked-state:memory-impact-graph-no-connector-write",
    "blocked-state:memory-impact-graph-no-crm-sync",
    "blocked-state:memory-impact-graph-no-semantic-search",
    "blocked-state:memory-impact-graph-no-vector-db",
    "blocked-state:memory-impact-graph-no-model-provider-call",
    "blocked-state:memory-impact-graph-no-delete-export-execution",
    "blocked-state:memory-impact-graph-no-production-authority",
]
MEMORY_FOLLOW_UP_QUEUE_BLOCKED_STATE_REFS = [
    "blocked-state:memory-follow-up-queue-proposal-only",
    "blocked-state:memory-follow-up-queue-no-action-execution",
    "blocked-state:memory-follow-up-queue-no-scheduling",
    "blocked-state:memory-follow-up-queue-no-connector-write",
    "blocked-state:memory-follow-up-queue-no-crm-sync",
    "blocked-state:memory-follow-up-queue-no-context-injection",
    "blocked-state:memory-follow-up-queue-no-memory-write",
    "blocked-state:memory-follow-up-queue-no-production-authority",
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
    safe_query: str | None = None,
    search_index_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the FCC-MEM-001 safe-ref-only Memory Workbench read model."""

    loop_ref_set = set(_safe_refs(loop_refs or [], "loop_refs"))
    safe_query_ref, hashed_safe_query_ref, query_mode = validate_query_mode(
        query_ref=query_ref,
        safe_query=safe_query,
    )
    safe_query_text = _safe_text(safe_query, "safe_query") if safe_query else None
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
        item.update(_lifecycle_item_posture(item))
        item.update(
            _ranked_memory_payload(
                item,
                query_ref=safe_query_ref,
                safe_query=safe_query_text,
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
    lifecycle_posture = _memory_lifecycle_posture(
        ranked_items,
        decision_receipts=decision_receipts,
    )
    ranking = _ranking_read_model(
        ranked_items,
        query_ref=safe_query_ref,
        safe_query_ref=hashed_safe_query_ref,
        query_mode=query_mode,
    )
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
        "lifecycle_posture": lifecycle_posture,
        "learning_posture": _memory_learning_posture(
            ranked_items,
            decision_receipts=decision_receipts,
            context_packs=context_packs,
            lifecycle_posture=lifecycle_posture,
            ranking=ranking,
            search_index_status=search_index_status,
        ),
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
        "ranking": ranking,
        "safe_query_ref": hashed_safe_query_ref,
        "query_mode": query_mode,
        "retrieval_strategy_refs": _retrieval_strategy_refs(
            query_mode=query_mode,
            search_index_status=search_index_status,
        ),
        "search_index_status": _search_index_status(search_index_status),
        "hrr_readiness": memory_hrr_readiness(),
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


def _memory_learning_posture(
    items: list[dict[str, Any]],
    *,
    decision_receipts: list[dict[str, Any]],
    context_packs: dict[str, Any],
    lifecycle_posture: dict[str, Any],
    ranking: dict[str, Any],
    search_index_status: dict[str, Any] | None,
) -> dict[str, Any]:
    lifecycle_counts = _memory_learning_lifecycle_counts(
        items,
        decision_receipts=decision_receipts,
    )
    accepted_receipts = _receipt_refs_for_decisions(decision_receipts, ["accept"])
    corrected_receipts = _receipt_refs_for_decisions(decision_receipts, ["correct"])
    rejected_receipts = _receipt_refs_for_decisions(decision_receipts, ["reject"])
    forget_receipts = _receipt_refs_for_decisions(
        decision_receipts,
        ["forget_request"],
    )
    proposal_refs = _safe_refs(
        [
            proposal.get("proposal_ref") or proposal.get("context_pack_ref")
            for proposal in context_packs.get("proposals", []) or []
        ],
        "memory_learning_context_pack_proposal_refs",
    )
    context_pack_refs = _safe_refs(
        [
            proposal.get("context_pack_ref")
            for proposal in context_packs.get("proposals", []) or []
        ],
        "memory_learning_context_pack_refs",
    )
    reviewed_recall_refs = _safe_refs(
        [
            item.get("memory_ref")
            for item in items
            if item.get("source") == "reviewed_recall"
            or "reviewed" in item.get("group_ids", [])
        ],
        "memory_learning_reviewed_recall_refs",
    )
    attention_refs = _safe_refs(
        [
            item.get("memory_ref")
            for item in items
            if any(
                group_id in item.get("group_ids", [])
                for group_id in [
                    "needs_review",
                    "conflict",
                    "duplicate",
                    "stale",
                    "missing_evidence",
                ]
            )
        ],
        "memory_learning_attention_refs",
    )
    quality_issue_refs = _safe_refs(
        [
            ref
            for item in items
            for ref in item.get("quality_state_refs", []) or []
        ],
        "memory_learning_quality_issue_refs",
    )
    provenance_refs = _safe_refs(
        [
            ref
            for item in items
            for ref in [
                *list(item.get("source_refs") or []),
                *list(item.get("provenance_refs") or []),
                *list(item.get("evidence_refs") or []),
                *list(item.get("receipt_refs") or []),
            ]
        ],
        "memory_learning_provenance_refs",
    )
    search_status = _search_index_status(search_index_status)
    return {
        "schema_version": "goatcitadel-catchup-memory-learning-posture.v1",
        "contract_ref": MEMORY_LEARNING_POSTURE_CONTRACT_REF,
        "route_ref": MEMORY_WORKBENCH_ROUTE_REF,
        "status": "implemented_backend_owned_learning_posture_read_model",
        "source": "python_core_memory_workbench_learning_posture",
        "backend_owned": True,
        "control_center_presentation_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "proposal_first_intake": True,
        "review_required_before_recall": True,
        "feedback_receipts_supported": True,
        "correction_receipts_supported": True,
        "rejection_receipts_supported": True,
        "forget_request_receipts_supported": True,
        "forget_execution_authorized": False,
        "broad_memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "hidden_context_injection_authorized": False,
        "automatic_context_injection_authorized": False,
        "memory_truth_authority": False,
        "policy_override_authorized": False,
        "action_execution_authorized": False,
        "connector_write_authorized": False,
        "model_provider_call_authorized": False,
        "live_web_fetch_authorized": False,
        "background_autonomy_authorized": False,
        "hard_delete_authorized": False,
        "export_execution_authorized": False,
        "production_authority_enabled": False,
        "lifecycle_state_counts": lifecycle_counts,
        "lifecycle_state_refs": [
            _state_ref("memory-learning-lifecycle-state", state)
            for state in [
                "proposed",
                "active",
                "needs_review",
                "corrected",
                "rejected",
                "stale",
                "forgotten",
                "blocked",
            ]
        ],
        "feedback_flow_refs": [
            "flow-ref:memory-learning:review-candidate",
            "flow-ref:memory-learning:accept-reviewed-recall",
            "flow-ref:memory-learning:correct-safe-summary",
            "flow-ref:memory-learning:reject-candidate",
            "flow-ref:memory-learning:defer-recheck",
            "flow-ref:memory-learning:merge-duplicate",
            "flow-ref:memory-learning:supersede-conflict",
            "flow-ref:memory-learning:forget-request-receipt",
            "flow-ref:memory-learning:feedback-quality-signal",
        ],
        "quality_control_refs": [
            "quality-control-ref:memory-learning:dedupe",
            "quality-control-ref:memory-learning:source-provenance",
            "quality-control-ref:memory-learning:confidence-quality-labels",
            "quality-control-ref:memory-learning:staleness",
            "quality-control-ref:memory-learning:conflict-handling",
            "quality-control-ref:memory-learning:safe-refs-redaction",
        ],
        "context_pack_posture": {
            "status": context_packs.get("status")
            or "implemented_read_only_context_pack_proposals",
            "proposal_count": int(context_packs.get("context_pack_count") or 0),
            "proposal_refs": proposal_refs,
            "context_pack_refs": context_pack_refs,
            "separates_facts_assumptions_memories_unknowns": True,
            "context_injection_authorized": False,
            "hidden_prompt_context_authorized": False,
            "prompt_context_written": False,
            "provider_model_call_performed": False,
            "action_execution_authorized": False,
        },
        "receipt_posture": {
            "decision_receipt_count": len(decision_receipts),
            "accepted_receipt_refs": accepted_receipts,
            "corrected_receipt_refs": corrected_receipts,
            "rejected_receipt_refs": rejected_receipts,
            "forget_request_receipt_refs": forget_receipts,
            "reviewed_recall_refs": reviewed_recall_refs,
            "receipt_backed_decision_kinds": list(
                lifecycle_posture.get("receipt_backed_decision_kinds") or []
            ),
        },
        "quality_posture": {
            "attention_refs": attention_refs,
            "quality_issue_refs": quality_issue_refs,
            "ranking_contract_ref": ranking.get("contract_ref"),
            "ranking_strategy_refs": list(
                ranking.get("retrieval_strategy_refs") or []
            ),
            "search_index_status": search_status,
            "semantic_search_enabled": False,
            "vector_db_enabled": False,
            "embedding_search_enabled": False,
        },
        "provenance_posture": {
            "provenance_refs": provenance_refs[:80],
            "provenance_ref_count": len(provenance_refs),
            "source_refs_required": True,
            "evidence_refs_required": True,
            "receipt_refs_required_for_reviewed_recall": True,
            "safe_summary_only": True,
        },
        "next_safe_action": (
            "Review memory candidates, context-pack proposal refs, quality "
            "signals, and receipt refs before any exact-scoped memory decision."
        ),
        "blocked_state_refs": list(MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS),
    }


def _memory_learning_lifecycle_counts(
    items: list[dict[str, Any]],
    *,
    decision_receipts: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {
        "proposed": 0,
        "active": 0,
        "needs_review": 0,
        "corrected": 0,
        "rejected": 0,
        "stale": 0,
        "forgotten": 0,
        "blocked": 0,
    }
    for item in items:
        review_state = str(item.get("review_state") or "")
        groups = {str(group_id) for group_id in item.get("group_ids", []) or []}
        if item.get("source") == "review_candidate" or review_state in {
            "review_needed",
            "needs_review",
            "deferred",
        }:
            counts["proposed"] += 1
        if item.get("source") == "reviewed_recall" or review_state in {
            "accepted",
            "reviewed",
            "corrected",
        }:
            counts["active"] += 1
        if "needs_review" in groups or review_state in {"review_needed", "needs_review"}:
            counts["needs_review"] += 1
        if review_state == "corrected":
            counts["corrected"] += 1
        if "rejected" in groups or review_state == "rejected":
            counts["rejected"] += 1
        if "stale" in groups or str(item.get("stale_state") or "none") != "none":
            counts["stale"] += 1
        if review_state in {"forget_requested", "revoked", "forgotten"}:
            counts["forgotten"] += 1
        if item.get("blocked_state_refs") or item.get("missing_contract_refs"):
            counts["blocked"] += 1
    if any(receipt.get("decision") == "correct" for receipt in decision_receipts):
        counts["corrected"] = max(
            counts["corrected"],
            len(
                [
                    receipt
                    for receipt in decision_receipts
                    if receipt.get("decision") == "correct"
                ]
            ),
        )
    if any(receipt.get("decision") == "reject" for receipt in decision_receipts):
        counts["rejected"] = max(
            counts["rejected"],
            len(
                [
                    receipt
                    for receipt in decision_receipts
                    if receipt.get("decision") == "reject"
                ]
            ),
        )
    if any(
        receipt.get("decision") == "forget_request"
        for receipt in decision_receipts
    ):
        counts["forgotten"] = max(
            counts["forgotten"],
            len(
                [
                    receipt
                    for receipt in decision_receipts
                    if receipt.get("decision") == "forget_request"
                ]
            ),
        )
    return counts


def _receipt_refs_for_decisions(
    decision_receipts: list[dict[str, Any]],
    decisions: list[str],
) -> list[str]:
    decision_set = set(decisions)
    return _safe_refs(
        [
            receipt.get("receipt_ref")
            for receipt in decision_receipts
            if receipt.get("decision") in decision_set
        ],
        "memory_learning_decision_receipt_refs",
    )


def _lifecycle_item_posture(item: dict[str, Any]) -> dict[str, Any]:
    review_state = str(item.get("review_state") or "review_needed")
    group_ids = [str(group_id) for group_id in item.get("group_ids", []) or []]
    state_refs = [
        _state_ref("memory-lifecycle-state", review_state),
        *[
            _state_ref("memory-lifecycle-state", group_id)
            for group_id in group_ids
            if group_id in {"conflict", "duplicate", "stale", "missing_evidence"}
        ],
    ]
    available_decisions = ["accept", "correct", "reject", "defer", "forget_request"]
    if item.get("duplicate_of_refs"):
        available_decisions.append("merge")
    if item.get("conflict_with_refs"):
        available_decisions.append("supersede")
    return {
        "lifecycle_state_refs": sorted(set(state_refs)),
        "available_lifecycle_decisions": available_decisions,
        "lifecycle_receipt_refs": _safe_refs(
            item.get("receipt_refs"),
            "lifecycle_receipt_refs",
        ),
        "reversible_review_posture": (
            "later_receipt_can_update_review_posture_no_rollback_execution"
        ),
        "hard_delete_authorized": False,
        "automatic_merge_authorized": False,
        "automatic_supersede_authorized": False,
        "automatic_forget_authorized": False,
        "hidden_memory_write_authorized": False,
    }


def _memory_lifecycle_posture(
    items: list[dict[str, Any]],
    *,
    decision_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    receipt_refs_by_decision = {
        decision: _safe_refs(
            [
                receipt.get("receipt_ref")
                for receipt in decision_receipts
                if receipt.get("decision") == decision
            ],
            f"{decision}_receipt_refs",
        )
        for decision in [
            "correct",
            "defer",
            "merge",
            "supersede",
            "forget_request",
        ]
    }
    duplicate_items = [
        item for item in items if "duplicate" in item.get("group_ids", [])
    ]
    stale_items = [item for item in items if "stale" in item.get("group_ids", [])]
    conflict_items = [
        item for item in items if "conflict" in item.get("group_ids", [])
    ]
    corrected_items = [
        item for item in items if item.get("review_state") == "corrected"
    ]
    merged_items = [
        item for item in items if item.get("review_state") == "merged"
    ]
    superseded_items = [
        item for item in items if item.get("review_state") == "superseded"
    ]
    forget_requested_items = [
        item for item in items if item.get("review_state") == "forget_requested"
    ]
    lanes = [
        _memory_lifecycle_lane(
            lane_id="duplicate_review",
            label="Duplicate review",
            decision_kind="merge",
            item_refs=_memory_lifecycle_item_refs(duplicate_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="merge",
                items=duplicate_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="stale_review",
            label="Stale review",
            decision_kind="defer",
            item_refs=_memory_lifecycle_item_refs(stale_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="defer",
                items=stale_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="conflict_review",
            label="Conflict review",
            decision_kind="supersede",
            item_refs=_memory_lifecycle_item_refs(conflict_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="supersede",
                items=conflict_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="corrected",
            label="Corrected",
            decision_kind="correct",
            item_refs=_memory_lifecycle_item_refs(corrected_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="correct",
                items=corrected_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="merged",
            label="Merged",
            decision_kind="merge",
            item_refs=_memory_lifecycle_item_refs(merged_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="merge",
                items=merged_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="superseded",
            label="Superseded",
            decision_kind="supersede",
            item_refs=_memory_lifecycle_item_refs(superseded_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="supersede",
                items=superseded_items,
            ),
        ),
        _memory_lifecycle_lane(
            lane_id="forget_requested",
            label="Forget request",
            decision_kind="forget_request",
            item_refs=_memory_lifecycle_item_refs(forget_requested_items),
            receipt_refs=_memory_lifecycle_receipt_refs_for_items(
                decision_receipts,
                decision="forget_request",
                items=forget_requested_items,
            ),
        ),
    ]
    return {
        "schema_version": "product-loop-002-memory-merge-supersede-posture.v1",
        "contract_ref": MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
        "status": "implemented_review_only_receipt_backed_posture",
        "lanes": lanes,
        "decision_receipt_refs_by_kind": receipt_refs_by_decision,
        "receipt_truncation_posture": "bounded_by_workbench_limit_safe_refs_only",
        "receipt_backed_decision_kinds": [
            decision
            for decision, refs in receipt_refs_by_decision.items()
            if refs
        ],
        "review_only": True,
        "safe_refs_only": True,
        "reversible_review_posture": (
            "merge_supersede_forget_are_review_posture_no_destructive_execution"
        ),
        "hard_delete_authorized": False,
        "memory_export_authorized": False,
        "automatic_merge_authorized": False,
        "automatic_supersede_authorized": False,
        "automatic_forget_authorized": False,
        "hidden_memory_write_authorized": False,
        "context_injection_authorized": False,
        "connector_write_authorized": False,
        "model_provider_call_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS),
    }


def _memory_lifecycle_item_refs(items: list[dict[str, Any]]) -> list[str]:
    return _safe_refs([item.get("memory_ref") for item in items], "lane_item_refs")


def _memory_lifecycle_receipt_refs_for_items(
    decision_receipts: list[dict[str, Any]],
    *,
    decision: str,
    items: list[dict[str, Any]],
) -> list[str]:
    item_refs = _memory_lifecycle_item_ref_set(items)
    if not item_refs:
        return []
    return _safe_refs(
        [
            receipt.get("receipt_ref")
            for receipt in decision_receipts
            if receipt.get("decision") == decision
            and item_refs.intersection(_memory_lifecycle_receipt_ref_set(receipt))
        ],
        f"{decision}_lane_receipt_refs",
    )


def _memory_lifecycle_item_ref_set(items: list[dict[str, Any]]) -> set[str]:
    refs: list[str] = []
    for item in items:
        refs.extend(
            [
                str(item.get("memory_ref") or ""),
                str(item.get("review_ref") or ""),
                *[str(ref) for ref in item.get("duplicate_of_refs") or []],
                *[str(ref) for ref in item.get("conflict_with_refs") or []],
            ]
        )
    return set(_safe_refs(refs, "lifecycle_item_ref_set"))


def _memory_lifecycle_receipt_ref_set(receipt: dict[str, Any]) -> set[str]:
    refs = [
        str(receipt.get("candidate_ref") or ""),
        str(receipt.get("review_ref") or ""),
        *[str(ref) for ref in receipt.get("merge_refs") or []],
        *[str(ref) for ref in receipt.get("supersedes_refs") or []],
    ]
    return set(_safe_refs(refs, "lifecycle_receipt_ref_set"))


def _memory_lifecycle_lane(
    *,
    lane_id: str,
    label: str,
    decision_kind: str,
    item_refs: list[str],
    receipt_refs: list[str],
) -> dict[str, Any]:
    safe_item_refs = _safe_refs(item_refs, f"{lane_id}_item_refs")
    safe_receipt_refs = _safe_refs(receipt_refs, f"{lane_id}_receipt_refs")
    return {
        "lane_id": lane_id,
        "label": label,
        "posture_ref": _state_ref("memory-lifecycle-posture", lane_id),
        "decision_kind": decision_kind,
        "count": len(safe_item_refs),
        "item_refs": safe_item_refs,
        "receipt_refs": safe_receipt_refs,
        "receipt_backed": bool(safe_receipt_refs),
        "review_only": True,
        "blocked_state_refs": list(MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS),
    }


def filter_memory_workbench(
    *,
    workbench: dict[str, Any],
    query_ref: str | None = None,
    safe_query: str | None = None,
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

    safe_query_ref, hashed_safe_query_ref, query_mode = validate_query_mode(
        query_ref=query_ref,
        safe_query=safe_query,
    )
    safe_query_text = _safe_text(safe_query, "safe_query") if safe_query else None
    filters = {
        "query_ref": safe_query_ref,
        "safe_query": safe_query_text,
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
        "filters": {
            key: value
            for key, value in filters.items()
            if value and key != "safe_query"
        },
        "safe_query_ref": hashed_safe_query_ref,
        "query_mode": query_mode,
        "items": filtered,
        "count": len(filtered),
        "total_workbench_count": len(items),
        "ranking": _ranking_read_model(
            filtered,
            query_ref=filters["query_ref"],
            safe_query_ref=hashed_safe_query_ref,
            query_mode=query_mode,
            status="implemented_filtered_ranked_read_model_safe_refs_only",
        ),
        "retrieval_strategy_refs": _retrieval_strategy_refs(
            query_mode=query_mode,
            search_index_status=workbench.get("search_index_status"),
        ),
        "search_index_status": _search_index_status(
            workbench.get("search_index_status")
        ),
        "hrr_readiness": memory_hrr_readiness(),
        "safe_refs_only": True,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "embedding_search_enabled": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_WORKBENCH_BLOCKED_STATE_REFS),
    }


def build_memory_impact_graph(
    *,
    workbench: dict[str, Any],
    today_summary: dict[str, Any],
    actions_inbox: dict[str, Any],
    morning_briefing: dict[str, Any],
    evidence_timeline: dict[str, Any],
    context_packs: dict[str, Any],
    limit: int = 20,
) -> dict[str, Any]:
    """Build FCC-MEM-015 safe-ref-only impact graph from existing read models."""

    workbench_items = list(workbench.get("items", []) or [])[: max(1, min(limit, 50))]
    memory_to_loop_items = list(today_summary.get("memory_to_loop_items") or [])
    today_action_proposals = list(
        today_summary.get("memory_derived_action_proposals") or []
    )
    inbox_action_proposals = list(
        actions_inbox.get("memory_derived_action_proposals") or []
    )
    action_proposals = _dedupe_payloads_by_ref(
        [*today_action_proposals, *inbox_action_proposals],
        ref_key="proposal_ref",
    )
    briefing_sections = list(morning_briefing.get("daily_loop_sections") or [])
    briefing_memory_items = list(morning_briefing.get("memory_why_shown_items") or [])
    evidence_events = list(evidence_timeline.get("events") or [])
    context_pack_proposals = list(context_packs.get("proposals") or [])

    nodes: list[dict[str, Any]] = []
    for item in workbench_items:
        memory_ref = _safe_ref(
            item.get("memory_ref") or item.get("review_ref"),
            "memory_ref",
            allow_empty=True,
        ) or ""
        review_ref = _safe_ref(
            item.get("review_ref") or memory_ref,
            "review_ref",
            allow_empty=True,
        ) or memory_ref
        if not memory_ref:
            continue
        match_refs = _safe_refs(
            [
                memory_ref,
                review_ref,
                *list(item.get("source_refs") or []),
                *list(item.get("evidence_refs") or []),
                *list(item.get("receipt_refs") or []),
            ],
            "memory_impact_match_refs",
        )
        loop_matches = [
            loop_item
            for loop_item in memory_to_loop_items
            if _payload_mentions_any(loop_item, match_refs)
        ]
        action_matches = [
            proposal
            for proposal in action_proposals
            if _payload_mentions_any(proposal, match_refs)
        ]
        briefing_matches = [
            section
            for section in briefing_sections
            if _payload_mentions_any(section, match_refs)
        ]
        briefing_item_matches = [
            memory_item
            for memory_item in briefing_memory_items
            if _payload_mentions_any(memory_item, match_refs)
        ]
        event_matches = [
            event for event in evidence_events if _payload_mentions_any(event, match_refs)
        ]
        context_pack_matches = [
            proposal
            for proposal in context_pack_proposals
            if _payload_mentions_any(proposal, match_refs)
            or str(proposal.get("context_pack_ref") or "")
            in list(workbench.get("context_pack_refs") or [])
        ]
        today_item_refs = _refs_from_payloads(
            [loop for loop in loop_matches if loop.get("surface") == "Today"],
            ["loop_item_ref"],
        )
        action_proposal_refs = _refs_from_payloads(action_matches, ["proposal_ref"])
        briefing_refs = list(
            dict.fromkeys(
                [
                    *_refs_from_payloads(briefing_matches, ["section_ref"]),
                    *_refs_from_payloads(briefing_item_matches, ["loop_item_ref"]),
                ]
            )
        )
        evidence_event_refs = _refs_from_payloads(event_matches, ["event_ref"])
        context_pack_refs = _refs_from_payloads(
            context_pack_matches,
            ["context_pack_ref", "proposal_ref"],
        )
        relationship_refs = _relationship_refs(item)
        commitment_refs = _refs_containing(
            [
                *list(item.get("related_entity_refs") or []),
                *list(item.get("tag_refs") or []),
                *list(today_summary.get("follow_up_commitment_refs") or []),
            ],
            ["commitment", "follow-up"],
        )
        promise_refs = _refs_containing(
            [
                *list(item.get("related_entity_refs") or []),
                *list(item.get("tag_refs") or []),
                *list(item.get("missing_contract_refs") or []),
            ],
            ["promise"],
        )
        what_this_affects_refs = list(
            dict.fromkeys(
                [
                    *today_item_refs,
                    *action_proposal_refs,
                    *briefing_refs,
                    *evidence_event_refs,
                    *context_pack_refs,
                ]
            )
        )
        nodes.append(
            {
                "schema_version": "fcc_mem_015_memory_impact_node.v1",
                "memory_ref": memory_ref,
                "review_ref": review_ref,
                "review_state": _safe_text(
                    item.get("review_state") or "unknown",
                    "review_state",
                ),
                "candidate_kind": _safe_text(
                    item.get("candidate_kind") or "unknown",
                    "candidate_kind",
                ),
                "relationship_refs": relationship_refs,
                "commitment_refs": commitment_refs,
                "promise_refs": promise_refs,
                "source_refs": _safe_refs(item.get("source_refs"), "source_refs"),
                "provenance_refs": _safe_refs(
                    item.get("provenance_refs"),
                    "provenance_refs",
                ),
                "evidence_refs": _safe_refs(item.get("evidence_refs"), "evidence_refs"),
                "today_item_refs": today_item_refs,
                "action_proposal_refs": action_proposal_refs,
                "briefing_refs": briefing_refs,
                "evidence_event_refs": evidence_event_refs,
                "context_pack_refs": context_pack_refs,
                "why_shown_refs": _safe_refs(
                    [
                        *list(item.get("why_shown_refs") or []),
                        "why-shown-ref:fcc-mem-015:impact-graph-ref-overlap",
                    ],
                    "why_shown_refs",
                ),
                "what_this_affects_refs": what_this_affects_refs,
                "stale_state_refs": _safe_refs(
                    [
                        _state_ref(
                            "stale-ref",
                            str(item.get("stale_state") or "recheck-memory-impact"),
                        )
                    ],
                    "stale_state_refs",
                ),
                "quality_state_refs": _safe_refs(
                    item.get("quality_state_refs"),
                    "quality_state_refs",
                ),
                "blocked_state_refs": _safe_refs(
                    [
                        *list(item.get("blocked_state_refs") or []),
                        *MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS,
                    ],
                    "blocked_state_refs",
                ),
                "changed_refs": _decision_answer_refs(
                    event_matches,
                    answer_key="changed",
                ),
                "suppressed_refs": _suppressed_refs_for_memory(
                    memory_ref=memory_ref,
                    review_ref=review_ref,
                    decision_receipts=list(workbench.get("decision_receipts") or []),
                ),
                "stayed_blocked_refs": _safe_refs(
                    MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS,
                    "stayed_blocked_refs",
                ),
                "affected_surface_refs": _affected_surface_refs(
                    today_item_refs=today_item_refs,
                    action_proposal_refs=action_proposal_refs,
                    briefing_refs=briefing_refs,
                    evidence_event_refs=evidence_event_refs,
                    context_pack_refs=context_pack_refs,
                ),
                "next_safe_action": (
                    "Review affected loop refs before creating follow-up or "
                    "Action Inbox proposal work."
                ),
            }
        )

    context_pack_previews = _context_pack_preview_cards(
        context_pack_proposals=context_pack_proposals,
        all_memory_refs=[str(item.get("memory_ref")) for item in workbench_items],
    )
    health_v2 = build_recall_health_v2(
        workbench=workbench,
        impact_nodes=nodes,
        decision_receipts=list(workbench.get("decision_receipts") or []),
    )
    follow_up_queue = build_memory_follow_up_queue(
        impact_graph_nodes=nodes,
        workbench=workbench,
    )
    return {
        "schema_version": "fcc_mem_015_memory_impact_graph.v1",
        "contract_ref": MEMORY_IMPACT_GRAPH_CONTRACT_REF,
        "route_ref": MEMORY_IMPACT_GRAPH_ROUTE_REF,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "implemented_backend_owned_safe_ref_impact_graph",
        "safe_refs_only": True,
        "node_count": len(nodes),
        "nodes": nodes,
        "health_v2": health_v2,
        "follow_up_queue": follow_up_queue,
        "context_pack_previews": context_pack_previews,
        "blocked_state_refs": list(MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS),
        "memory_truth_authority": False,
        "context_injection_authorized": False,
        "action_execution_authorized": False,
        "connector_write_authorized": False,
        "crm_sync_authorized": False,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "embedding_search_enabled": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
    }


def build_recall_health_v2(
    *,
    workbench: dict[str, Any],
    impact_nodes: list[dict[str, Any]],
    decision_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    health = dict(workbench.get("health") or {})
    defer_receipts = [
        receipt for receipt in decision_receipts if receipt.get("decision") == "defer"
    ]
    forget_receipts = [
        receipt
        for receipt in decision_receipts
        if receipt.get("decision") == "forget_request"
    ]
    suppressed_refs = [
        ref
        for receipt in decision_receipts
        for ref in receipt.get("suppressed_recall_record_refs", []) or []
    ]
    top_nodes = sorted(
        impact_nodes,
        key=lambda node: (
            -len(node.get("what_this_affects_refs") or []),
            str(node.get("memory_ref") or ""),
        ),
    )
    relationship_refs = list(
        dict.fromkeys(
            ref
            for node in top_nodes
            for ref in node.get("relationship_refs", []) or []
        )
    )
    commitment_refs = list(
        dict.fromkeys(
            ref
            for node in top_nodes
            for ref in [
                *list(node.get("commitment_refs") or []),
                *list(node.get("promise_refs") or []),
            ]
        )
    )
    return {
        "schema_version": "fcc_mem_015_recall_health_v2.v1",
        "reviewed_recall_count": int(health.get("reviewed_recall_count") or 0),
        "pending_review_count": int(health.get("pending_review_count") or 0),
        "stale_pressure": int(health.get("stale_count") or 0),
        "duplicate_pressure": int(health.get("duplicate_count") or 0),
        "conflict_pressure": int(health.get("conflict_count") or 0),
        "missing_evidence_pressure": int(health.get("missing_evidence_count") or 0),
        "defer_aging_count": len(defer_receipts),
        "defer_aging_refs": _refs_from_payloads(defer_receipts, ["receipt_ref"]),
        "forget_request_aging_count": len(forget_receipts),
        "forget_request_aging_refs": _refs_from_payloads(
            forget_receipts,
            ["receipt_ref", "forget_request_ref"],
        ),
        "merge_supersede_suppression_count": len(set(suppressed_refs)),
        "suppressed_recall_record_refs": _safe_refs(
            suppressed_refs,
            "suppressed_recall_record_refs",
        ),
        "top_memory_refs_driving_current_loop": _safe_refs(
            [node.get("memory_ref") for node in top_nodes[:5]],
            "top_memory_refs_driving_current_loop",
        ),
        "top_relationship_refs_needing_attention": relationship_refs[:5],
        "top_commitment_refs_needing_attention": commitment_refs[:5],
        "health_reason_refs": _safe_refs(
            [
                "health-reason-ref:fcc-mem-015:workbench-health-counts",
                "health-reason-ref:fcc-mem-015:impact-graph-affected-ref-count",
                "health-reason-ref:fcc-mem-015:lifecycle-receipt-aging",
                "health-reason-ref:fcc-mem-015:merge-supersede-suppression",
            ],
            "health_reason_refs",
        ),
        "safe_refs_only": True,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
    }


def build_memory_follow_up_queue(
    *,
    impact_graph_nodes: list[dict[str, Any]],
    workbench: dict[str, Any],
) -> dict[str, Any]:
    decision_receipts = list(workbench.get("decision_receipts") or [])
    receipt_by_review_ref = {
        str(receipt.get("review_ref") or receipt.get("candidate_ref")): receipt
        for receipt in decision_receipts
    }
    candidates: list[dict[str, Any]] = []
    for node in impact_graph_nodes:
        review_ref = str(node.get("review_ref") or node.get("memory_ref"))
        receipt = receipt_by_review_ref.get(review_ref, {})
        groups = _follow_up_groups_for_node(node, receipt)
        follow_up_ref = (
            "memory-follow-up:fcc-mem-015:"
            f"{_short_digest(str(node.get('memory_ref') or review_ref), length=12)}"
        )
        candidates.append(
            {
                "schema_version": "fcc_mem_015_follow_up_candidate.v1",
                "follow_up_ref": follow_up_ref,
                "source_memory_refs": _safe_refs(
                    [node.get("memory_ref"), node.get("review_ref")],
                    "source_memory_refs",
                ),
                "relationship_refs": _safe_refs(
                    node.get("relationship_refs"),
                    "relationship_refs",
                ),
                "commitment_refs": _safe_refs(
                    [
                        *list(node.get("commitment_refs") or []),
                        *list(node.get("promise_refs") or []),
                    ],
                    "commitment_refs",
                ),
                "action_proposal_ref": _safe_ref(
                    (node.get("action_proposal_refs") or [None])[0],
                    "action_proposal_ref",
                    allow_empty=True,
                ),
                "why_shown_refs": _safe_refs(
                    [
                        *list(node.get("why_shown_refs") or []),
                        "why-shown-ref:fcc-mem-015:proposal-only-follow-up",
                    ],
                    "why_shown_refs",
                ),
                "what_this_affects_refs": _safe_refs(
                    node.get("what_this_affects_refs"),
                    "what_this_affects_refs",
                ),
                "group_ids": groups,
                "rank_score": len(node.get("what_this_affects_refs") or []) * 10
                + len(groups),
                "proposal_only": True,
                "approval_required_before_action": True,
                "action_execution_authorized": False,
                "connector_write_authorized": False,
                "memory_write_authorized": False,
                "context_injection_authorized": False,
                "production_authority_enabled": False,
                "blocked_state_refs": list(MEMORY_FOLLOW_UP_QUEUE_BLOCKED_STATE_REFS),
                "next_safe_action": (
                    "Review this proposal in Action Inbox before any later "
                    "approved action lane."
                ),
            }
        )
    candidates = sorted(
        candidates,
        key=lambda candidate: (
            -int(candidate.get("rank_score") or 0),
            str(candidate.get("follow_up_ref") or ""),
        ),
    )
    groups = [
        {"group_id": group, "count": sum(group in item["group_ids"] for item in candidates)}
        for group in [
            "relationship",
            "commitment",
            "stale_promise",
            "missing_evidence",
            "recently_corrected_preference",
            "deferred_review",
            "forget_request_follow_up",
        ]
    ]
    return {
        "schema_version": "fcc_mem_015_memory_follow_up_queue.v1",
        "contract_ref": MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF,
        "route_ref": MEMORY_FOLLOW_UP_QUEUE_ROUTE_REF,
        "status": "implemented_proposal_only_follow_up_queue",
        "groups": groups,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "blocked_state_refs": list(MEMORY_FOLLOW_UP_QUEUE_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "proposal_only": True,
        "action_execution_authorized": False,
        "connector_write_authorized": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }


def _json_text(payload: Any) -> str:
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def _payload_mentions_any(payload: Any, refs: list[str]) -> bool:
    text = _json_text(payload)
    return any(ref and ref in text for ref in refs)


def _dedupe_payloads_by_ref(
    payloads: list[dict[str, Any]],
    *,
    ref_key: str,
) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        ref = str(payload.get(ref_key) or "")
        if ref and ref not in deduped:
            deduped[ref] = payload
    return list(deduped.values())


def _refs_from_payloads(
    payloads: list[dict[str, Any]],
    keys: list[str],
) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                refs.extend(str(item) for item in value if item)
            elif value:
                refs.append(str(value))
    return _safe_refs(refs, "derived_refs")


def _refs_containing(values: list[Any], markers: list[str]) -> list[str]:
    refs = [
        str(value)
        for value in values
        if value and any(marker in str(value).lower() for marker in markers)
    ]
    return _safe_refs(refs, "matching_refs")


def _relationship_refs(item: dict[str, Any]) -> list[str]:
    values = [
        *list(item.get("related_entity_refs") or []),
        *list(item.get("source_refs") or []),
        *list(item.get("tag_refs") or []),
    ]
    relationship_refs = [
        str(value)
        for value in values
        if any(
            marker in str(value).lower()
            for marker in ["person", "org", "deal", "relationship", "project"]
        )
    ]
    return _safe_refs(relationship_refs, "relationship_refs")


def _decision_answer_refs(
    events: list[dict[str, Any]],
    *,
    answer_key: str,
) -> list[str]:
    refs: list[str] = []
    marker = answer_key.replace("_", "-")
    for event in events:
        for key in [
            "answer_refs",
            "changed_refs",
            "suppressed_refs",
            "stayed_blocked_refs",
        ]:
            refs.extend(str(ref) for ref in event.get(key, []) or [] if marker in str(ref))
        event_ref = str(event.get("event_ref") or "")
        if event_ref and marker in event_ref:
            refs.append(event_ref)
    if not refs:
        refs.append(f"memory-lifecycle-answer-ref:{marker}:not-recorded")
    return _safe_refs(refs, "decision_answer_refs")


def _suppressed_refs_for_memory(
    *,
    memory_ref: str,
    review_ref: str,
    decision_receipts: list[dict[str, Any]],
) -> list[str]:
    refs: list[str] = []
    for receipt in decision_receipts:
        if str(receipt.get("candidate_ref") or "") not in {memory_ref, review_ref} and str(
            receipt.get("review_ref") or ""
        ) not in {memory_ref, review_ref}:
            continue
        refs.extend(str(ref) for ref in receipt.get("suppressed_recall_record_refs", []) or [])
        for key in [
            "merged_from_candidate_refs",
            "superseded_candidate_refs",
            "duplicate_candidate_refs",
            "conflict_candidate_refs",
        ]:
            refs.extend(str(ref) for ref in receipt.get(key, []) or [])
    return _safe_refs(refs, "suppressed_refs")


def _affected_surface_refs(
    *,
    today_item_refs: list[str],
    action_proposal_refs: list[str],
    briefing_refs: list[str],
    evidence_event_refs: list[str],
    context_pack_refs: list[str],
) -> list[str]:
    refs: list[str] = []
    if today_item_refs:
        refs.append("surface-ref:today")
    if action_proposal_refs:
        refs.append("surface-ref:actions")
    if briefing_refs:
        refs.append("surface-ref:briefing")
    if evidence_event_refs:
        refs.append("surface-ref:evidence")
    if context_pack_refs:
        refs.append("surface-ref:context-pack-preview")
    return _safe_refs(refs, "affected_surface_refs")


def _context_pack_preview_cards(
    *,
    context_pack_proposals: list[dict[str, Any]],
    all_memory_refs: list[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for proposal in context_pack_proposals:
        context_pack_ref = _safe_ref(
            proposal.get("context_pack_ref"),
            "context_pack_ref",
            allow_empty=True,
        ) or ""
        proposal_ref = _safe_ref(
            proposal.get("proposal_ref"),
            "proposal_ref",
            allow_empty=True,
        ) or ""
        matching_memory_refs = [
            ref for ref in all_memory_refs if ref and _payload_mentions_any(proposal, [ref])
        ]
        cards.append(
            {
                "schema_version": "fcc_mem_015_context_pack_preview.v1",
                "context_pack_ref": context_pack_ref,
                "proposal_ref": proposal_ref,
                "included_memory_refs": _safe_refs(
                    matching_memory_refs,
                    "included_memory_refs",
                ),
                "excluded_reason_refs": _safe_refs(
                    proposal.get("excluded_reason_refs")
                    or [
                        "context-pack-exclusion-ref:fcc-mem-015:no-context-injection",
                        "context-pack-exclusion-ref:fcc-mem-015:approval-required",
                    ],
                    "excluded_reason_refs",
                ),
                "why_previewed_refs": _safe_refs(
                    [
                        "why-previewed-ref:fcc-mem-015:inspectable-context-pack",
                        "why-previewed-ref:fcc-mem-015:proposal-artifact-only",
                    ],
                    "why_previewed_refs",
                ),
                "safe_refs_only": True,
                "proposal_only": True,
                "context_injection_authorized": False,
                "memory_write_authorized": False,
                "production_authority_enabled": False,
            }
        )
    return cards


def _follow_up_groups_for_node(
    node: dict[str, Any],
    receipt: dict[str, Any],
) -> list[str]:
    groups: list[str] = []
    if node.get("relationship_refs"):
        groups.append("relationship")
    if node.get("commitment_refs"):
        groups.append("commitment")
    if node.get("promise_refs") or any(
        "promise" in str(ref).lower() for ref in node.get("stale_state_refs", []) or []
    ):
        groups.append("stale_promise")
    if "business-memory-quality:evidence-missing" in node.get("quality_state_refs", []):
        groups.append("missing_evidence")
    if receipt.get("decision") == "correct":
        groups.append("recently_corrected_preference")
    if receipt.get("decision") == "defer" or node.get("review_state") == "deferred":
        groups.append("deferred_review")
    if receipt.get("decision") == "forget_request":
        groups.append("forget_request_follow_up")
    if not groups:
        groups.append("relationship")
    return list(dict.fromkeys(groups))


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
        [
            receipt.get("receipt_ref")
            for receipt in receipts
            if receipt.get("receipt_ref")
        ]
        + [
            ref
            for ref in evidence_refs
            if str(ref).startswith("receipt:memory-review:")
        ],
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
    safe_query: str | None,
    loop_refs: set[str],
) -> dict[str, Any]:
    components = _rank_components(
        item,
        query_ref=query_ref,
        safe_query=safe_query,
        loop_refs=loop_refs,
    )
    rank_score = min(sum(components.values()), sum(MEMORY_RANKING_COMPONENT_BOUNDS.values()))
    excluded_reason_refs = _excluded_reason_refs(item)
    return {
        "rank_score": rank_score,
        "rank_components": components,
        "score_components": components,
        "retrieval_strategy_refs": _item_retrieval_strategy_refs(
            item,
            query_ref=query_ref,
            safe_query=safe_query,
        ),
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
    safe_query: str | None,
    loop_refs: set[str],
) -> dict[str, int]:
    query_tokens = _ranking_query_tokens(
        query_ref=query_ref,
        safe_query=safe_query,
        loop_refs=loop_refs,
    )
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
    safe_query_ref: str | None = None,
    query_mode: str = "default",
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
        "safe_query_ref": safe_query_ref,
        "query_mode": query_mode,
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
        "retrieval_strategy_refs": _retrieval_strategy_refs(query_mode=query_mode),
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
        "safe_query_blocked_authority_refs": list(MEMORY_SAFE_QUERY_BLOCKED_STATE_REFS),
        "hrr_readiness": memory_hrr_readiness(),
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
    safe_query: str | None = None,
    loop_refs: set[str],
) -> set[str]:
    query_text = " ".join([query_ref or "", safe_query or "", *sorted(loop_refs)])
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
    if filters.get("safe_query"):
        query_tokens = set(_tokenize_ranking_text(str(filters["safe_query"])))
        item_tokens = set(
            _tokenize_ranking_text(
                " ".join(
                    [
                        str(item.get("title") or ""),
                        str(item.get("safe_summary") or ""),
                        str(item.get("candidate_kind") or ""),
                        *list(item.get("source_refs") or []),
                        *list(item.get("evidence_refs") or []),
                        *list(item.get("related_entity_refs") or []),
                        *list(item.get("tag_refs") or []),
                        *list(item.get("receipt_refs") or []),
                    ]
                )
            )
        )
        if query_tokens and not query_tokens.intersection(item_tokens):
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


def _retrieval_strategy_refs(
    *,
    query_mode: str,
    search_index_status: dict[str, Any] | None = None,
) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-safe-summary-lexical",
        "retrieval-strategy-ref:fcc-mem-022-safe-ref-match",
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


def _item_retrieval_strategy_refs(
    item: dict[str, Any],
    *,
    query_ref: str | None,
    safe_query: str | None,
) -> list[str]:
    refs = [
        "retrieval-strategy-ref:fcc-mem-022-ranked-workbench-item",
        "retrieval-strategy-ref:fcc-mem-022-safe-summary-and-refs",
    ]
    if query_ref:
        refs.append("retrieval-strategy-ref:fcc-mem-022-query-ref")
    if safe_query:
        refs.append("retrieval-strategy-ref:fcc-mem-022-safe-query-hashed")
    if item.get("source") == "l1_reviewed_recall_projection":
        refs.append("retrieval-strategy-ref:fcc-mem-022-reviewed-l1-projection")
    return refs


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


__all__ = [
    "MEMORY_FOLLOW_UP_QUEUE_BLOCKED_STATE_REFS",
    "MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF",
    "MEMORY_FOLLOW_UP_QUEUE_ROUTE_REF",
    "MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS",
    "MEMORY_IMPACT_GRAPH_CONTRACT_REF",
    "MEMORY_IMPACT_GRAPH_ROUTE_REF",
    "MEMORY_LIFECYCLE_POSTURE_BLOCKED_STATE_REFS",
    "MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF",
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
    "build_memory_follow_up_queue",
    "build_memory_impact_graph",
    "build_memory_workbench",
    "build_recall_health_v2",
    "filter_memory_workbench",
    "manual_memory_candidate_payload_fingerprint_ref",
    "manual_memory_candidate_payload_for_fingerprint",
    "manual_memory_candidate_ref",
]
