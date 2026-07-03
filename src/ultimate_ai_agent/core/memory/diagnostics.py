from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF = (
    "contract-ref:fcc-mem-016-retrieval-diagnostics:v1"
)
MEMORY_RETRIEVAL_DIAGNOSTICS_ROUTE_REF = (
    "GET /control-center/memory/retrieval-diagnostics"
)
MEMORY_CITATION_INTEGRITY_CONTRACT_REF = (
    "contract-ref:fcc-mem-017-citation-integrity:v1"
)
MEMORY_CITATION_INTEGRITY_ROUTE_REF = (
    "GET /control-center/memory/citation-integrity"
)
MEMORY_FEEDBACK_QUALITY_CONTRACT_REF = (
    "contract-ref:fcc-mem-018-feedback-quality-queue:v1"
)
MEMORY_FEEDBACK_ROUTE_REF = "POST /control-center/memory/feedback"
MEMORY_QUALITY_ISSUES_ROUTE_REF = "GET /control-center/memory/quality-issues"
MEMORY_MAINTENANCE_RUN_CONTRACT_REF = (
    "contract-ref:fcc-mem-019-proposal-only-maintenance-runs:v1"
)
MEMORY_MAINTENANCE_RUN_ROUTE_REF = "GET /control-center/memory/maintenance-runs"
MEMORY_CONTEXT_MANIFEST_CONTRACT_REF = "contract-ref:fcc-mem-020-context-manifest:v1"
MEMORY_CONTEXT_MANIFEST_ROUTE_REF = "GET /control-center/memory/context-manifest"

MEMORY_DIAGNOSTICS_BLOCKED_STATE_REFS = [
    "blocked-state:memory-diagnostics-no-context-injection",
    "blocked-state:memory-diagnostics-no-semantic-search",
    "blocked-state:memory-diagnostics-no-vector-db",
    "blocked-state:memory-diagnostics-no-embeddings",
    "blocked-state:memory-diagnostics-no-provider-model-calls",
    "blocked-state:memory-diagnostics-no-memory-write",
    "blocked-state:memory-diagnostics-no-production-authority",
]
MEMORY_CITATION_INTEGRITY_BLOCKED_STATE_REFS = [
    "blocked-state:memory-citation-integrity-invalid-proposals-blocked",
    "blocked-state:memory-citation-integrity-no-context-injection",
    "blocked-state:memory-citation-integrity-no-truth-authority",
    "blocked-state:memory-citation-integrity-no-provider-model-calls",
    "blocked-state:memory-citation-integrity-no-memory-write",
    "blocked-state:memory-citation-integrity-no-production-authority",
]
MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS = [
    "blocked-state:memory-feedback-no-automatic-memory-write",
    "blocked-state:memory-feedback-no-auto-rerank-authority",
    "blocked-state:memory-feedback-no-delete-execution",
    "blocked-state:memory-feedback-no-context-injection",
    "blocked-state:memory-feedback-no-action-execution",
    "blocked-state:memory-feedback-no-production-authority",
]
MEMORY_MAINTENANCE_RUN_BLOCKED_STATE_REFS = [
    "blocked-state:memory-maintenance-proposal-only",
    "blocked-state:memory-maintenance-no-auto-merge",
    "blocked-state:memory-maintenance-no-auto-supersede",
    "blocked-state:memory-maintenance-no-auto-forget",
    "blocked-state:memory-maintenance-no-auto-write",
    "blocked-state:memory-maintenance-no-delete-execution",
    "blocked-state:memory-maintenance-no-context-injection",
    "blocked-state:memory-maintenance-no-production-authority",
]
MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS = [
    "blocked-state:memory-context-manifest-no-hidden-prompt-injection",
    "blocked-state:memory-context-manifest-no-runtime-prompt-context-injection",
    "blocked-state:memory-context-manifest-no-live-model-context-injection",
    "blocked-state:memory-context-manifest-no-automatic-context-use",
    "blocked-state:memory-context-manifest-no-automatic-memory-inclusion",
    "blocked-state:memory-context-manifest-no-truth-authority",
    "blocked-state:memory-context-manifest-no-action-execution",
    "blocked-state:memory-context-manifest-no-connector-write",
    "blocked-state:memory-context-manifest-no-connector-derived-context-injection",
    "blocked-state:memory-context-manifest-no-browser-web-derived-context-injection",
    "blocked-state:memory-context-manifest-no-shell-file-derived-context-injection",
    "blocked-state:memory-context-manifest-no-raw-payload-persistence",
    "blocked-state:memory-context-manifest-no-memory-write",
    "blocked-state:memory-context-manifest-no-provider-model-calls",
    "blocked-state:memory-context-manifest-no-provider-prompt-context-injection",
    "blocked-state:memory-context-manifest-no-broad-autonomy",
    "blocked-state:memory-context-manifest-no-public-beta-claim",
    "blocked-state:memory-context-manifest-no-public-distribution-claim",
    "blocked-state:memory-context-manifest-no-production-readiness-claim",
    "blocked-state:memory-context-manifest-no-production-authority",
]

MemoryFeedbackKind = Literal[
    "useful",
    "stale",
    "missing",
    "wrong",
    "duplicate",
    "conflict",
    "irrelevant",
    "privacy_concern",
]
MemoryFeedbackTargetKind = Literal[
    "memory_candidate",
    "reviewed_recall",
    "impact_graph_node",
    "context_pack_preview",
    "follow_up_proposal",
    "today_item",
    "action_proposal",
    "evidence_event",
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
    "username",
    "hostname",
    "credential",
    "password",
    "secret",
    "api key",
    "api_key",
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
_DELETED_STATES = {"deleted", "revoked"}
_SUPERSEDED_STATES = {"superseded", "merged"}
_FORGET_STATES = {"forget_requested"}


class MemoryFeedbackRequest(BaseModel):
    """Idempotent operator feedback receipt. Never writes memory automatically."""

    target_ref: str = Field(..., min_length=1)
    target_kind: MemoryFeedbackTargetKind
    feedback_kind: MemoryFeedbackKind
    reviewer_ref: str = Field(default="actor-ref:local-operator", min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_feedback_request(self) -> "MemoryFeedbackRequest":
        _safe_ref(self.target_ref, "target_ref")
        _safe_text(self.target_kind, "target_kind")
        _safe_text(self.feedback_kind, "feedback_kind")
        _safe_ref(self.reviewer_ref, "reviewer_ref")
        for field_name in [
            "evidence_refs",
            "reason_refs",
            "metadata_refs",
            "blocked_state_refs",
        ]:
            setattr(self, field_name, _safe_refs(getattr(self, field_name), field_name))
        if not self.evidence_refs and not self.reason_refs:
            raise ValueError("memory feedback requires evidence refs or reason refs")
        missing_blocked = [
            ref
            for ref in MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS
            if ref not in self.blocked_state_refs
        ]
        if missing_blocked:
            raise ValueError("memory feedback request missing blocked state refs")
        return self


def memory_feedback_payload_for_fingerprint(
    request: MemoryFeedbackRequest,
) -> dict[str, Any]:
    return {
        "target_ref": request.target_ref,
        "target_kind": request.target_kind,
        "feedback_kind": request.feedback_kind,
        "reviewer_ref": request.reviewer_ref,
        "evidence_refs": list(request.evidence_refs),
        "reason_refs": list(request.reason_refs),
        "metadata_refs": list(request.metadata_refs),
        "blocked_state_refs": list(request.blocked_state_refs),
    }


def memory_feedback_payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    return _payload_fingerprint(payload, prefix="payload-fingerprint:memory-feedback")


def memory_feedback_ref(idempotency_key_ref: str) -> str:
    _safe_ref(idempotency_key_ref, "idempotency_key_ref")
    return f"memory-feedback:fcc-mem-018:{_short_digest(idempotency_key_ref, length=12)}"


def memory_feedback_receipt_ref(idempotency_key_ref: str) -> str:
    _safe_ref(idempotency_key_ref, "idempotency_key_ref")
    return f"receipt:memory-feedback:fcc-mem-018:{_short_digest(idempotency_key_ref, length=12)}"


def build_memory_retrieval_diagnostics(
    *,
    workbench: dict[str, Any],
    impact_graph: dict[str, Any],
    context_packs: dict[str, Any],
    feedback_receipts: list[dict[str, Any]],
    limit: int = 20,
) -> dict[str, Any]:
    items = list(workbench.get("items") or [])[: _limit(limit)]
    nodes = list(impact_graph.get("nodes") or [])[: _limit(limit)]
    proposals = list(context_packs.get("proposals") or [])[: _limit(limit)]
    included_refs = _safe_refs(
        [node.get("memory_ref") for node in nodes if node.get("what_this_affects_refs")],
        "included_refs",
    )
    all_memory_refs = _safe_refs(
        [item.get("memory_ref") for item in items],
        "all_memory_refs",
    )
    excluded_refs = [ref for ref in all_memory_refs if ref not in included_refs]
    rank_signals = [_rank_signal_for_item(item, included_refs) for item in items]
    source_mix = _source_mix(items)
    cache_basis = {
        "memory_refs": all_memory_refs,
        "context_pack_refs": _safe_refs(
            [proposal.get("context_pack_ref") for proposal in proposals],
            "context_pack_refs",
        ),
        "feedback_refs": _safe_refs(
            [receipt.get("feedback_ref") for receipt in feedback_receipts],
            "feedback_refs",
        ),
        "rank_signal_refs": _safe_refs(
            [signal.get("rank_signal_ref") for signal in rank_signals],
            "rank_signal_refs",
        ),
    }
    return {
        "schema_version": "fcc_mem_016_retrieval_diagnostics.v1",
        "contract_ref": MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF,
        "route_ref": MEMORY_RETRIEVAL_DIAGNOSTICS_ROUTE_REF,
        "status": "implemented_backend_owned_read_model",
        "generated_at": _utc_iso(),
        "candidate_count": len(items),
        "included_count": len(included_refs),
        "excluded_count": len(excluded_refs),
        "included_refs": included_refs,
        "excluded_refs": _safe_refs(excluded_refs, "excluded_refs"),
        "excluded_reason_refs": _excluded_reason_refs(items, included_refs),
        "rank_signals": rank_signals,
        "source_mix": source_mix,
        "pressure": _pressure_from_workbench(workbench),
        "token_estimate": _token_estimate_for_refs(cache_basis),
        "cache_key_ref": f"cache-key-ref:fcc-mem-016:{_short_digest(_json_text(cache_basis), length=20)}",
        "cache_hit": False,
        "cache_status": "miss_no_runtime_cache_store",
        "cache_reason_refs": [
            "cache-reason-ref:fcc-mem-016:deterministic-key-only",
            "cache-reason-ref:fcc-mem-016:no-runtime-cache-authority",
        ],
        "blocked_reason_refs": list(MEMORY_DIAGNOSTICS_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "context_injection_authorized": False,
        "memory_write_authorized": False,
        "semantic_search_enabled": False,
        "vector_db_enabled": False,
        "embedding_search_enabled": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
    }


def build_memory_citation_integrity(
    *,
    context_packs: dict[str, Any],
    workbench: dict[str, Any],
    decision_receipts: list[dict[str, Any]],
    evidence_timeline: dict[str, Any],
    limit: int = 20,
) -> dict[str, Any]:
    items = list(workbench.get("items") or [])
    proposals = list(context_packs.get("proposals") or [])[: _limit(limit)]
    known = _known_ref_sets(
        items=items,
        workbench=workbench,
        decision_receipts=decision_receipts,
        evidence_timeline=evidence_timeline,
    )
    results = [
        _citation_result_for_proposal(proposal, known)
        for proposal in proposals
    ]
    blocked = [result for result in results if result["status"] == "blocked"]
    proof_events = [_citation_proof_event(result) for result in blocked]
    return {
        "schema_version": "fcc_mem_017_citation_integrity.v1",
        "contract_ref": MEMORY_CITATION_INTEGRITY_CONTRACT_REF,
        "route_ref": MEMORY_CITATION_INTEGRITY_ROUTE_REF,
        "status": (
            "blocked_invalid_context_pack_citations"
            if blocked
            else "implemented_all_visible_context_pack_refs_validated"
        ),
        "generated_at": _utc_iso(),
        "proposal_count": len(results),
        "valid_proposal_count": len(results) - len(blocked),
        "blocked_proposal_count": len(blocked),
        "results": results,
        "evidence_timeline_proof_events": proof_events,
        "citation_validation_rule_refs": [
            "citation-rule-ref:fcc-mem-017:source-ref-exists",
            "citation-rule-ref:fcc-mem-017:evidence-ref-exists",
            "citation-rule-ref:fcc-mem-017:receipt-ref-exists",
            "citation-rule-ref:fcc-mem-017:memory-reviewed",
            "citation-rule-ref:fcc-mem-017:not-deleted",
            "citation-rule-ref:fcc-mem-017:not-superseded-unless-intentional",
            "citation-rule-ref:fcc-mem-017:not-forget-requested",
            "citation-rule-ref:fcc-mem-017:not-orphaned",
        ],
        "blocked_state_refs": list(MEMORY_CITATION_INTEGRITY_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "proposal_only": True,
        "context_injection_authorized": False,
        "memory_write_authorized": False,
        "truth_authority_enabled": False,
        "model_provider_authority_allowed": False,
        "production_authority_enabled": False,
    }


def build_memory_feedback_quality_queue(
    *,
    workbench: dict[str, Any],
    impact_graph: dict[str, Any],
    feedback_receipts: list[dict[str, Any]],
    limit: int = 20,
) -> dict[str, Any]:
    issues = [
        *_issues_from_workbench(workbench),
        *_issues_from_impact_graph(impact_graph),
        *_issues_from_feedback(feedback_receipts),
    ]
    deduped: dict[str, dict[str, Any]] = {}
    for issue in issues:
        deduped.setdefault(str(issue["issue_ref"]), issue)
    ranked = sorted(
        deduped.values(),
        key=lambda issue: (-int(issue.get("rank_score") or 0), str(issue["issue_ref"])),
    )[: _limit(limit)]
    groups = [
        {"group_id": group, "count": sum(group in item["group_ids"] for item in ranked)}
        for group in [
            "useful",
            "stale",
            "missing",
            "wrong",
            "duplicate",
            "conflict",
            "irrelevant",
            "privacy_concern",
        ]
    ]
    return {
        "schema_version": "fcc_mem_018_feedback_quality_queue.v1",
        "contract_ref": MEMORY_FEEDBACK_QUALITY_CONTRACT_REF,
        "route_ref": MEMORY_QUALITY_ISSUES_ROUTE_REF,
        "feedback_route_ref": MEMORY_FEEDBACK_ROUTE_REF,
        "status": "implemented_feedback_receipt_quality_issue_read_model",
        "generated_at": _utc_iso(),
        "issue_count": len(ranked),
        "feedback_count": len(feedback_receipts),
        "groups": groups,
        "issues": ranked,
        "feedback_receipt_refs": _safe_refs(
            [receipt.get("receipt_ref") for receipt in feedback_receipts],
            "feedback_receipt_refs",
        ),
        "blocked_state_refs": list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "proposal_only": True,
        "automatic_memory_write_authorized": False,
        "memory_write_authorized": False,
        "delete_execution_authorized": False,
        "context_injection_authorized": False,
        "action_execution_authorized": False,
        "production_authority_enabled": False,
    }


def build_memory_maintenance_runs(
    *,
    quality_queue: dict[str, Any],
    citation_integrity: dict[str, Any],
    limit: int = 20,
) -> dict[str, Any]:
    issues = list(quality_queue.get("issues") or [])[: _limit(limit)]
    citation_results = [
        result
        for result in citation_integrity.get("results", []) or []
        if result.get("status") == "blocked"
    ]
    proposals = [
        *[_maintenance_proposal_from_issue(issue) for issue in issues],
        *[_maintenance_proposal_from_citation(result) for result in citation_results],
    ]
    proposals = sorted(
        proposals,
        key=lambda proposal: (
            -int(proposal.get("rank_score") or 0),
            str(proposal["maintenance_proposal_ref"]),
        ),
    )[: _limit(limit)]
    run_ref = f"memory-maintenance-run:fcc-mem-019:{_short_digest(_json_text(proposals), length=16)}"
    return {
        "schema_version": "fcc_mem_019_proposal_only_maintenance_run.v1",
        "contract_ref": MEMORY_MAINTENANCE_RUN_CONTRACT_REF,
        "route_ref": MEMORY_MAINTENANCE_RUN_ROUTE_REF,
        "status": "implemented_proposal_only_scan_read_model",
        "run_ref": run_ref,
        "scan_ref": f"memory-quality-scan:fcc-mem-019:{_short_digest(run_ref, length=12)}",
        "generated_at": _utc_iso(),
        "proposal_count": len(proposals),
        "proposals": proposals,
        "blocked_state_refs": list(MEMORY_MAINTENANCE_RUN_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "proposal_only": True,
        "auto_merge_authorized": False,
        "auto_supersede_authorized": False,
        "auto_forget_authorized": False,
        "automatic_memory_write_authorized": False,
        "delete_execution_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
    }


def build_memory_context_manifest(
    *,
    context_packs: dict[str, Any],
    retrieval_diagnostics: dict[str, Any],
    citation_integrity: dict[str, Any],
    quality_queue: dict[str, Any],
    limit: int = 20,
) -> dict[str, Any]:
    citation_by_pack = {
        str(result.get("context_pack_ref")): result
        for result in citation_integrity.get("results", []) or []
    }
    quality_refs = _safe_refs(
        [issue.get("issue_ref") for issue in quality_queue.get("issues", []) or []],
        "quality_issue_refs",
    )
    manifests: list[dict[str, Any]] = []
    for proposal in list(context_packs.get("proposals") or [])[: _limit(limit)]:
        context_pack_ref = _safe_ref(proposal.get("context_pack_ref"), "context_pack_ref")
        proposal_ref = _safe_ref(proposal.get("proposal_ref"), "proposal_ref")
        citation = citation_by_pack.get(context_pack_ref, {})
        included_memory_refs = _safe_refs(
            [
                *list(proposal.get("source_memory_record_refs") or []),
                *list(proposal.get("l1_preview_refs") or []),
            ],
            "included_memory_refs",
        )
        manifest_basis = {
            "context_pack_ref": context_pack_ref,
            "proposal_ref": proposal_ref,
            "included_memory_refs": included_memory_refs,
            "citation_status": citation.get("status", "not_validated"),
            "retrieval_cache_key_ref": retrieval_diagnostics.get("cache_key_ref"),
        }
        manifests.append(
            {
                "schema_version": "fcc_mem_020_context_manifest_item.v1",
                "context_manifest_ref": (
                    "context-manifest-ref:fcc-mem-020:"
                    f"{_short_digest(_json_text(manifest_basis), length=16)}"
                ),
                "context_pack_ref": context_pack_ref,
                "proposal_ref": proposal_ref,
                "included_memory_refs": included_memory_refs,
                "excluded_memory_refs": _safe_refs(
                    retrieval_diagnostics.get("excluded_refs"),
                    "excluded_memory_refs",
                ),
                "why_included_refs": _safe_refs(
                    proposal.get("inclusion_reason_refs")
                    or ["inclusion-reason-ref:context-manifest-reviewed-proposal"],
                    "why_included_refs",
                ),
                "why_excluded_refs": _safe_refs(
                    proposal.get("excluded_ref_reasons", {}).values()
                    if isinstance(proposal.get("excluded_ref_reasons"), dict)
                    else [],
                    "why_excluded_refs",
                )
                or ["excluded-reason-ref:context-manifest:no-extra-exclusions-recorded"],
                "citation_integrity_status": citation.get("status", "not_validated"),
                "citation_integrity_result_ref": citation.get(
                    "citation_integrity_result_ref",
                    "citation-integrity-result-ref:fcc-mem-020:not-validated",
                ),
                "risk_posture_ref": _risk_posture_ref(proposal, citation),
                "token_budget": int(proposal.get("max_context_tokens") or 0),
                "token_estimate": _token_estimate_for_refs(manifest_basis),
                "cache_key_ref": retrieval_diagnostics.get("cache_key_ref"),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
                "safe_disable_refs": [
                    "safe-disable-ref:memory-context-manifest:no-hidden-injection",
                    "safe-disable-ref:memory-context-manifest:disable-before-use",
                ],
                "quality_issue_refs": quality_refs[:5],
                "blocked_state_refs": list(MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS),
                "proposal_only": True,
                "approval_required_before_use": True,
                "context_injection_authorized": False,
                "hidden_prompt_context_authorized": False,
                "runtime_prompt_context_injection_authorized": False,
                "live_model_context_injection_authorized": False,
                "automatic_context_injection_authorized": False,
                "automatic_memory_inclusion_authorized": False,
                "memory_write_authorized": False,
                "action_execution_authorized": False,
                "connector_write_authorized": False,
                "connector_derived_context_injection_authorized": False,
                "browser_web_derived_context_injection_authorized": False,
                "shell_file_derived_context_injection_authorized": False,
                "raw_payload_persistence_enabled": False,
                "model_provider_authority_allowed": False,
                "provider_prompt_context_injection_authorized": False,
                "broad_autonomy_authorized": False,
                "public_beta_claim_authorized": False,
                "public_distribution_claim_authorized": False,
                "production_readiness_claim_authorized": False,
                "production_authority_enabled": False,
            }
        )
    return {
        "schema_version": "fcc_mem_020_context_manifest.v1",
        "contract_ref": MEMORY_CONTEXT_MANIFEST_CONTRACT_REF,
        "route_ref": MEMORY_CONTEXT_MANIFEST_ROUTE_REF,
        "status": "implemented_proposal_only_context_manifest",
        "generated_at": _utc_iso(),
        "manifest_count": len(manifests),
        "manifests": manifests,
        "retrieval_cache_key_ref": retrieval_diagnostics.get("cache_key_ref"),
        "blocked_state_refs": list(MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS),
        "safe_refs_only": True,
        "proposal_only": True,
        "context_injection_authorized": False,
        "hidden_prompt_context_authorized": False,
        "runtime_prompt_context_injection_authorized": False,
        "live_model_context_injection_authorized": False,
        "automatic_context_injection_authorized": False,
        "automatic_memory_inclusion_authorized": False,
        "memory_write_authorized": False,
        "action_execution_authorized": False,
        "connector_write_authorized": False,
        "connector_derived_context_injection_authorized": False,
        "browser_web_derived_context_injection_authorized": False,
        "shell_file_derived_context_injection_authorized": False,
        "raw_payload_persistence_enabled": False,
        "model_provider_authority_allowed": False,
        "provider_prompt_context_injection_authorized": False,
        "broad_autonomy_authorized": False,
        "public_beta_claim_authorized": False,
        "public_distribution_claim_authorized": False,
        "production_readiness_claim_authorized": False,
        "production_authority_enabled": False,
    }


def known_memory_feedback_target_refs(
    *,
    workbench: dict[str, Any],
    impact_graph: dict[str, Any],
    context_packs: dict[str, Any],
    evidence_timeline: dict[str, Any],
) -> list[str]:
    refs: list[str] = []
    for item in workbench.get("items", []) or []:
        refs.extend([str(item.get("memory_ref") or ""), str(item.get("review_ref") or "")])
    for node in impact_graph.get("nodes", []) or []:
        refs.extend([str(node.get("memory_ref") or ""), str(node.get("review_ref") or "")])
        refs.extend(str(ref) for ref in node.get("what_this_affects_refs", []) or [])
    for proposal in context_packs.get("proposals", []) or []:
        refs.extend([str(proposal.get("context_pack_ref") or ""), str(proposal.get("proposal_ref") or "")])
    for event in evidence_timeline.get("events", []) or []:
        refs.append(str(event.get("event_ref") or ""))
    return _safe_refs(refs, "known_memory_feedback_target_refs")


def _safe_text(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} is required")
    validate_safe_execution_text(text, field_name)
    lowered = text.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe memory diagnostics text")
    return text


def _safe_ref(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    text = _safe_text(value, field_name, allow_empty=allow_empty)
    if not text:
        return ""
    validate_execution_ref(text, field_name)
    return text


def _safe_refs(values: Any, field_name: str) -> list[str]:
    refs: list[str] = []
    for value in values or []:
        ref = _safe_ref(value, field_name, allow_empty=True)
        if ref:
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _payload_fingerprint(payload: dict[str, Any], *, prefix: str) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:{_short_digest(encoded, length=24)}"


def _short_digest(value: str, *, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[
        :length
    ]


def _json_text(payload: Any) -> str:
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _limit(value: int) -> int:
    return max(1, min(int(value), 50))


def _state_ref(prefix: str, value: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in ".-" else "-"
        for char in value.lower().replace("_", "-")
    ).strip("-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    return f"{prefix}:{normalized or 'missing'}"


def _token_estimate_for_refs(payload: Any) -> int:
    return max(1, len(_json_text(payload)) // 4)


def _rank_signal_for_item(item: dict[str, Any], included_refs: list[str]) -> dict[str, Any]:
    memory_ref = _safe_ref(item.get("memory_ref"), "memory_ref")
    quality_refs = _safe_refs(item.get("quality_state_refs"), "quality_state_refs")
    why_refs = _safe_refs(item.get("why_shown_refs"), "why_shown_refs")
    return {
        "rank_signal_ref": f"rank-signal-ref:fcc-mem-016:{_short_digest(memory_ref, length=12)}",
        "memory_ref": memory_ref,
        "rank_score": int(item.get("rank_score") or 0),
        "included": memory_ref in included_refs,
        "source_ref": _state_ref("memory-source-ref", str(item.get("source") or "unknown")),
        "quality_state_refs": quality_refs,
        "why_shown_refs": why_refs,
        "pressure_score": _pressure_score(quality_refs),
    }


def _pressure_score(quality_refs: list[str]) -> int:
    score = 0
    if "business-memory-quality:conflict" in quality_refs:
        score += 90
    if "business-memory-quality:duplicate" in quality_refs:
        score += 80
    if "business-memory-quality:evidence-missing" in quality_refs:
        score += 70
    if "business-memory-quality:stale-expired" in quality_refs:
        score += 60
    return score


def _source_mix(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        source_ref = _state_ref("memory-source-ref", str(item.get("source") or "unknown"))
        counts[source_ref] = counts.get(source_ref, 0) + 1
    return [
        {"source_ref": source_ref, "count": count}
        for source_ref, count in sorted(counts.items())
    ]


def _pressure_from_workbench(workbench: dict[str, Any]) -> dict[str, Any]:
    health = dict(workbench.get("health") or {})
    return {
        "stale_pressure": int(health.get("stale_count") or 0),
        "duplicate_pressure": int(health.get("duplicate_count") or 0),
        "conflict_pressure": int(health.get("conflict_count") or 0),
        "missing_evidence_pressure": int(health.get("missing_evidence_count") or 0),
        "pressure_reason_refs": [
            "pressure-reason-ref:fcc-mem-016:memory-workbench-quality-groups",
            "pressure-reason-ref:fcc-mem-016:no-model-scoring",
        ],
    }


def _excluded_reason_refs(items: list[dict[str, Any]], included_refs: list[str]) -> list[str]:
    refs: list[str] = []
    for item in items:
        if item.get("memory_ref") in included_refs:
            continue
        if not item.get("evidence_refs"):
            refs.append("excluded-reason-ref:fcc-mem-016:missing-evidence")
        else:
            refs.append("excluded-reason-ref:fcc-mem-016:not-current-loop-linked")
    return _safe_refs(refs, "excluded_reason_refs")


def _known_ref_sets(
    *,
    items: list[dict[str, Any]],
    workbench: dict[str, Any],
    decision_receipts: list[dict[str, Any]],
    evidence_timeline: dict[str, Any],
) -> dict[str, Any]:
    memory_by_ref: dict[str, dict[str, Any]] = {}
    sources: list[str] = []
    evidence: list[str] = []
    receipts: list[str] = []
    projection_refs: list[str] = []
    for item in items:
        for ref in [item.get("memory_ref"), item.get("review_ref")]:
            if ref:
                memory_by_ref[str(ref)] = item
        sources.extend(str(ref) for ref in item.get("source_refs", []) or [])
        evidence.extend(str(ref) for ref in item.get("evidence_refs", []) or [])
        receipts.extend(str(ref) for ref in item.get("receipt_refs", []) or [])
    projection_refs.extend(
        str(ref)
        for ref in [
            *list(workbench.get("l1_preview_refs") or []),
            *list(workbench.get("l2_projection_refs") or []),
            *list(workbench.get("l3_projection_refs") or []),
        ]
    )
    for receipt in decision_receipts:
        receipts.append(str(receipt.get("receipt_ref") or ""))
        evidence.extend(str(ref) for ref in receipt.get("evidence_refs", []) or [])
        for ref in [receipt.get("reviewed_recall_record_ref"), receipt.get("reviewed_recall_ref")]:
            if ref:
                memory_by_ref[str(ref)] = {
                    "memory_ref": str(ref),
                    "review_state": "reviewed",
                    "source_refs": receipt.get("source_refs", []),
                    "evidence_refs": receipt.get("evidence_refs", []),
                    "receipt_refs": [receipt.get("receipt_ref")],
                }
    for event in evidence_timeline.get("events", []) or []:
        evidence.append(str(event.get("event_ref") or ""))
        evidence.extend(str(ref) for ref in event.get("evidence_refs", []) or [])
    return {
        "memory_by_ref": memory_by_ref,
        "source_refs": set(_safe_refs(sources, "known_source_refs")),
        "evidence_refs": set(_safe_refs(evidence, "known_evidence_refs")),
        "receipt_refs": set(_safe_refs(receipts, "known_receipt_refs")),
        "projection_refs": set(_safe_refs(projection_refs, "known_projection_refs")),
    }


def _citation_result_for_proposal(
    proposal: dict[str, Any],
    known: dict[str, Any],
) -> dict[str, Any]:
    context_pack_ref = _safe_ref(proposal.get("context_pack_ref"), "context_pack_ref")
    proposal_ref = _safe_ref(proposal.get("proposal_ref"), "proposal_ref")
    source_refs = _safe_refs(proposal.get("source_refs"), "source_refs")
    evidence_refs = _safe_refs(proposal.get("evidence_refs"), "evidence_refs")
    receipt_refs = _safe_refs(proposal.get("receipt_refs"), "receipt_refs")
    memory_refs = _safe_refs(
        proposal.get("source_memory_record_refs"),
        "citation_memory_refs",
    )
    projection_refs = _safe_refs(
        [
            *list(proposal.get("l1_preview_refs") or []),
            *list(proposal.get("l2_projection_refs") or []),
            *list(proposal.get("l3_representation_refs") or []),
        ],
        "citation_projection_refs",
    )
    allowed_superseded = set(
        _safe_refs(
            proposal.get("intentionally_included_superseded_refs"),
            "intentionally_included_superseded_refs",
        )
    )
    memory_by_ref = known["memory_by_ref"]
    missing_source_refs = [ref for ref in source_refs if ref not in known["source_refs"]]
    missing_evidence_refs = [ref for ref in evidence_refs if ref not in known["evidence_refs"]]
    missing_receipt_refs = [ref for ref in receipt_refs if ref not in known["receipt_refs"]]
    orphaned_memory_refs = [ref for ref in memory_refs if ref not in memory_by_ref]
    orphaned_projection_refs = [
        ref for ref in projection_refs if ref not in known["projection_refs"]
    ]
    unreviewed_memory_refs: list[str] = []
    deleted_memory_refs: list[str] = []
    superseded_memory_refs: list[str] = []
    forget_requested_memory_refs: list[str] = []
    for ref in memory_refs:
        item = memory_by_ref.get(ref)
        if not item:
            continue
        review_state = str(item.get("review_state") or "").lower()
        if review_state not in _REVIEWED_STATES:
            unreviewed_memory_refs.append(ref)
        if review_state in _DELETED_STATES:
            deleted_memory_refs.append(ref)
        if review_state in _SUPERSEDED_STATES and ref not in allowed_superseded:
            superseded_memory_refs.append(ref)
        if review_state in _FORGET_STATES:
            forget_requested_memory_refs.append(ref)
    invalid_refs = _safe_refs(
        [
            *missing_source_refs,
            *missing_evidence_refs,
            *missing_receipt_refs,
            *orphaned_memory_refs,
            *unreviewed_memory_refs,
            *deleted_memory_refs,
            *superseded_memory_refs,
            *forget_requested_memory_refs,
        ],
        "invalid_citation_refs",
    )
    return {
        "schema_version": "fcc_mem_017_citation_integrity_result.v1",
        "citation_integrity_result_ref": (
            "citation-integrity-result-ref:fcc-mem-017:"
            f"{_short_digest(context_pack_ref + proposal_ref, length=16)}"
        ),
        "context_pack_ref": context_pack_ref,
        "proposal_ref": proposal_ref,
        "status": "blocked" if invalid_refs else "valid",
        "valid_citation_refs": _safe_refs(
            [*source_refs, *evidence_refs, *receipt_refs, *memory_refs],
            "valid_citation_refs",
        )
        + _safe_refs(
            projection_refs,
            "valid_citation_refs",
        )
        if not invalid_refs
        else [],
        "invalid_citation_refs": invalid_refs,
        "missing_source_refs": _safe_refs(missing_source_refs, "missing_source_refs"),
        "missing_evidence_refs": _safe_refs(missing_evidence_refs, "missing_evidence_refs"),
        "missing_receipt_refs": _safe_refs(missing_receipt_refs, "missing_receipt_refs"),
        "orphaned_memory_refs": _safe_refs(orphaned_memory_refs, "orphaned_memory_refs"),
        "orphaned_projection_refs": _safe_refs(
            orphaned_projection_refs,
            "orphaned_projection_refs",
        ),
        "unreviewed_memory_refs": _safe_refs(unreviewed_memory_refs, "unreviewed_memory_refs"),
        "deleted_memory_refs": _safe_refs(deleted_memory_refs, "deleted_memory_refs"),
        "superseded_memory_refs": _safe_refs(superseded_memory_refs, "superseded_memory_refs"),
        "forget_requested_memory_refs": _safe_refs(forget_requested_memory_refs, "forget_requested_memory_refs"),
        "blocks_context_pack_use": bool(invalid_refs),
        "evidence_timeline_event_ref": (
            "evidence-event-ref:fcc-mem-017:blocked-citation:"
            f"{_short_digest(context_pack_ref + proposal_ref, length=12)}"
        )
        if invalid_refs
        else "",
    }


def _citation_proof_event(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "fcc_mem_017_evidence_timeline_proof_event.v1",
        "event_ref": result["evidence_timeline_event_ref"],
        "event_kind": "memory_citation_integrity_blocked",
        "context_pack_ref": result["context_pack_ref"],
        "proposal_ref": result["proposal_ref"],
        "invalid_citation_refs": result["invalid_citation_refs"],
        "changed_refs": [result["citation_integrity_result_ref"]],
        "suppressed_refs": result["invalid_citation_refs"],
        "stayed_blocked_refs": list(MEMORY_CITATION_INTEGRITY_BLOCKED_STATE_REFS),
        "affected_surface_refs": ["surface-ref:memory", "surface-ref:evidence"],
        "safe_refs_only": True,
        "context_injection_authorized": False,
    }


def _issues_from_workbench(workbench: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in workbench.get("items", []) or []:
        memory_ref = _safe_ref(item.get("memory_ref"), "memory_ref")
        quality_refs = set(item.get("quality_state_refs") or [])
        mapping = [
            ("business-memory-quality:stale-expired", "stale", 70),
            ("business-memory-quality:evidence-missing", "missing", 75),
            ("business-memory-quality:duplicate", "duplicate", 80),
            ("business-memory-quality:conflict", "conflict", 90),
        ]
        for quality_ref, group, score in mapping:
            if quality_ref in quality_refs:
                issues.append(
                    _quality_issue(
                        target_ref=memory_ref,
                        target_kind="memory_candidate",
                        issue_kind=group,
                        source_ref=quality_ref,
                        rank_score=score + int(item.get("rank_score") or 0),
                    )
                )
    return issues


def _issues_from_impact_graph(impact_graph: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for node in impact_graph.get("nodes", []) or []:
        if node.get("review_state") == "forget_requested":
            issues.append(
                _quality_issue(
                    target_ref=_safe_ref(node.get("memory_ref"), "memory_ref"),
                    target_kind="impact_graph_node",
                    issue_kind="privacy_concern",
                    source_ref="quality-source-ref:fcc-mem-018:forget-request",
                    rank_score=95,
                )
            )
    return issues


def _issues_from_feedback(feedback_receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _quality_issue(
            target_ref=_safe_ref(receipt.get("target_ref"), "target_ref"),
            target_kind=str(receipt.get("target_kind") or "memory_candidate"),
            issue_kind=str(receipt.get("feedback_kind") or "missing"),
            source_ref=str(receipt.get("feedback_ref") or receipt.get("receipt_ref")),
            rank_score=_feedback_rank_score(str(receipt.get("feedback_kind") or "")),
            feedback_receipt_ref=str(receipt.get("receipt_ref") or ""),
        )
        for receipt in feedback_receipts
    ]


def _quality_issue(
    *,
    target_ref: str,
    target_kind: str,
    issue_kind: str,
    source_ref: str,
    rank_score: int,
    feedback_receipt_ref: str | None = None,
) -> dict[str, Any]:
    issue_ref = (
        "memory-quality-issue:fcc-mem-018:"
        f"{_short_digest(target_ref + issue_kind + source_ref, length=16)}"
    )
    return {
        "schema_version": "fcc_mem_018_quality_issue.v1",
        "issue_ref": issue_ref,
        "target_ref": _safe_ref(target_ref, "target_ref"),
        "target_kind": _safe_text(target_kind, "target_kind"),
        "issue_kind": _safe_text(issue_kind, "issue_kind"),
        "severity": _issue_severity(issue_kind),
        "status": "open",
        "group_ids": [_safe_text(issue_kind, "issue_group")],
        "source_signal_refs": _safe_refs([source_ref], "source_signal_refs"),
        "feedback_receipt_refs": _safe_refs(
            [feedback_receipt_ref] if feedback_receipt_ref else [],
            "feedback_receipt_refs",
        ),
        "why_queued_refs": [
            f"why-queued-ref:fcc-mem-018:{issue_kind}",
            "why-queued-ref:fcc-mem-018:operator-review-required",
        ],
        "rank_score": int(rank_score),
        "proposal_only": True,
        "memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "delete_execution_authorized": False,
        "context_injection_authorized": False,
        "action_execution_authorized": False,
        "production_authority_enabled": False,
    }


def _issue_severity(issue_kind: str) -> str:
    if issue_kind in {"privacy_concern", "wrong", "conflict"}:
        return "high"
    if issue_kind in {"duplicate", "missing", "stale"}:
        return "medium"
    return "low"


def _feedback_rank_score(feedback_kind: str) -> int:
    return {
        "privacy_concern": 100,
        "wrong": 95,
        "conflict": 90,
        "duplicate": 80,
        "missing": 75,
        "stale": 70,
        "irrelevant": 60,
        "useful": 20,
    }.get(feedback_kind, 50)


def _maintenance_proposal_from_issue(issue: dict[str, Any]) -> dict[str, Any]:
    issue_kind = str(issue.get("issue_kind") or "missing")
    kind_map = {
        "duplicate": "merge_review",
        "conflict": "supersede_review",
        "wrong": "supersede_review",
        "privacy_concern": "forget_request_review",
        "stale": "stale_recheck",
        "missing": "missing_evidence_request",
        "irrelevant": "defer_or_reject_review",
        "useful": "ranking_signal_review",
    }
    maintenance_kind = kind_map.get(issue_kind, "quality_review")
    target_ref = _safe_ref(issue.get("target_ref"), "target_ref")
    return {
        "schema_version": "fcc_mem_019_maintenance_proposal.v1",
        "maintenance_proposal_ref": (
            "memory-maintenance-proposal:fcc-mem-019:"
            f"{_short_digest(str(issue.get('issue_ref')) + maintenance_kind, length=16)}"
        ),
        "maintenance_kind": maintenance_kind,
        "source_issue_refs": _safe_refs([issue.get("issue_ref")], "source_issue_refs"),
        "source_memory_refs": _safe_refs([target_ref], "source_memory_refs"),
        "target_ref": target_ref,
        "rank_score": int(issue.get("rank_score") or 0),
        "inbox_envelope_kind": "memory_maintenance_proposal",
        "approval_required_before_mutation": True,
        "proposal_only": True,
        "auto_merge_authorized": False,
        "auto_supersede_authorized": False,
        "auto_forget_authorized": False,
        "automatic_memory_write_authorized": False,
        "delete_execution_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_MAINTENANCE_RUN_BLOCKED_STATE_REFS),
    }


def _maintenance_proposal_from_citation(result: dict[str, Any]) -> dict[str, Any]:
    context_pack_ref = _safe_ref(result.get("context_pack_ref"), "context_pack_ref")
    return {
        "schema_version": "fcc_mem_019_maintenance_proposal.v1",
        "maintenance_proposal_ref": (
            "memory-maintenance-proposal:fcc-mem-019:citation:"
            f"{_short_digest(context_pack_ref, length=16)}"
        ),
        "maintenance_kind": "citation_repair_review",
        "source_issue_refs": _safe_refs(
            [result.get("citation_integrity_result_ref")],
            "source_issue_refs",
        ),
        "source_memory_refs": _safe_refs(
            result.get("invalid_citation_refs"),
            "source_memory_refs",
        ),
        "target_ref": context_pack_ref,
        "rank_score": 85,
        "inbox_envelope_kind": "memory_maintenance_proposal",
        "approval_required_before_mutation": True,
        "proposal_only": True,
        "auto_merge_authorized": False,
        "auto_supersede_authorized": False,
        "auto_forget_authorized": False,
        "automatic_memory_write_authorized": False,
        "delete_execution_authorized": False,
        "context_injection_authorized": False,
        "production_authority_enabled": False,
        "blocked_state_refs": list(MEMORY_MAINTENANCE_RUN_BLOCKED_STATE_REFS),
    }


def _risk_posture_ref(proposal: dict[str, Any], citation: dict[str, Any]) -> str:
    if citation.get("status") == "blocked":
        return "risk-posture-ref:memory-context-manifest:blocked-invalid-citations"
    risk = str(proposal.get("risk_class") or "medium")
    return _state_ref("risk-posture-ref:memory-context-manifest", risk)


__all__ = [
    "MEMORY_CITATION_INTEGRITY_BLOCKED_STATE_REFS",
    "MEMORY_CITATION_INTEGRITY_CONTRACT_REF",
    "MEMORY_CITATION_INTEGRITY_ROUTE_REF",
    "MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS",
    "MEMORY_CONTEXT_MANIFEST_CONTRACT_REF",
    "MEMORY_CONTEXT_MANIFEST_ROUTE_REF",
    "MEMORY_DIAGNOSTICS_BLOCKED_STATE_REFS",
    "MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS",
    "MEMORY_FEEDBACK_QUALITY_CONTRACT_REF",
    "MEMORY_FEEDBACK_ROUTE_REF",
    "MEMORY_MAINTENANCE_RUN_BLOCKED_STATE_REFS",
    "MEMORY_MAINTENANCE_RUN_CONTRACT_REF",
    "MEMORY_MAINTENANCE_RUN_ROUTE_REF",
    "MEMORY_QUALITY_ISSUES_ROUTE_REF",
    "MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF",
    "MEMORY_RETRIEVAL_DIAGNOSTICS_ROUTE_REF",
    "MemoryFeedbackRequest",
    "build_memory_citation_integrity",
    "build_memory_context_manifest",
    "build_memory_feedback_quality_queue",
    "build_memory_maintenance_runs",
    "build_memory_retrieval_diagnostics",
    "known_memory_feedback_target_refs",
    "memory_feedback_payload_fingerprint_ref",
    "memory_feedback_payload_for_fingerprint",
    "memory_feedback_receipt_ref",
    "memory_feedback_ref",
]
