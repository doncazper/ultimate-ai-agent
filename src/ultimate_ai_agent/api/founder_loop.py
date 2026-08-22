from __future__ import annotations

import sqlite3

from typing import Literal

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from ultimate_ai_agent.api.dependencies import (
    get_founder_loop_service,
    get_news_signals_repository,
)
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
)
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_BLOCKED_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_MODE_REF,
    WebEvidenceProductSliceAuthorityError,
    WebEvidenceProductSliceRequest,
)
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.control_center.backend_truth import (
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.ecosystem.proposals import (
    ProposalExtractionRequest,
    extract_proposal_candidates,
)
from ultimate_ai_agent.core.ecosystem.corrections import (
    AutocorrectConflict,
    AutocorrectError,
    CorrectionProposalRequest,
    CorrectionReviewRequest,
    CorrectionReviewSession,
    build_autocorrect_control_status,
    build_correction_proposal,
)
from ultimate_ai_agent.core.memory import (
    ManualMemoryCandidateRequest,
    MemoryContextPackActionProposalRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopAuthorityError,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopActionRevisionConflict,
)


router = APIRouter(prefix="/control-center", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_founder_loop_routes_registered"
_AUTOCORRECT_REVIEW_SESSION = CorrectionReviewSession()


class FounderLoopActionRevisionConflictDetail(BaseModel):
    code: Literal["FOUNDER_LOOP_ACTION_STALE_REVISION"]
    safe_message: str
    refresh_required: Literal[True]
    current_revision_ref: str
    current_generation_ref: str
    refresh_route_ref: str


class FounderLoopActionRevisionConflictResponse(BaseModel):
    detail: FounderLoopActionRevisionConflictDetail


class FounderLoopActionIdempotencyConflictDetail(BaseModel):
    code: Literal[
        "FOUNDER_LOOP_ACTION_IDEMPOTENCY_CONFLICT",
        "FOUNDER_LOOP_ACTION_IDEMPOTENCY_LEGACY_CONFLICT",
    ]
    safe_message: str


class FounderLoopActionReceiptCapacityConflictDetail(BaseModel):
    code: Literal["FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED"]
    safe_message: str


class FounderLoopActionStateConflictDetail(BaseModel):
    code: Literal["FOUNDER_LOOP_ACTION_TERMINAL_LOCAL_TASK_COMMITTED"]
    safe_message: str


class FounderLoopActionDecisionConflictResponse(BaseModel):
    detail: (
        FounderLoopActionRevisionConflictDetail
        | FounderLoopActionIdempotencyConflictDetail
        | FounderLoopActionReceiptCapacityConflictDetail
        | FounderLoopActionStateConflictDetail
    )


ACTION_DECISION_CONFLICT_RESPONSES = {
    409: {
        "model": FounderLoopActionDecisionConflictResponse,
        "description": (
            "Typed Action decision revision, idempotency, or receipt-capacity "
            "conflict. Only revision conflicts require an authoritative refresh."
        ),
    }
}


@router.get("/backend-truth", response_model=ResultEnvelope)
def get_control_center_backend_truth() -> ResultEnvelope:
    try:
        data = get_founder_loop_service().backend_truth()
    except (FounderLoopStorageError, OSError, sqlite3.Error):
        data = build_control_center_backend_truth(repo=None)
    return ResultEnvelope(
        success=True,
        operation="control_center_backend_truth",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:backend-truth",
        data=data,
        evidence=[{"evidence_ref": data["envelope_integrity_ref"]}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "raw_paths_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/today/summary", response_model=ResultEnvelope)
def get_control_center_today_summary() -> ResultEnvelope:
    data = get_founder_loop_service().today_summary()
    news_signals = get_news_signals_repository().summary(limit=20)
    data["news_signals_projection"] = news_signals["today_projection"]
    return ResultEnvelope(
        success=True,
        operation="control_center_today_summary",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:today-summary",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:today-summary"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
        ],
    )


@router.get("/start-here/summary", response_model=ResultEnvelope)
def get_control_center_start_here_summary() -> ResultEnvelope:
    data = get_founder_loop_service().start_here_summary()
    return ResultEnvelope(
        success=True,
        operation="control_center_start_here_summary",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:start-here-summary",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:control-center:start-here"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/proof/index", response_model=ResultEnvelope)
def get_control_center_proof_index() -> ResultEnvelope:
    data = get_founder_loop_service().proof_index()
    return ResultEnvelope(
        success=True,
        operation="control_center_proof_index",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:proof-index",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:control-center:proof-index"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/proof/{proof_ref}", response_model=ResultEnvelope)
def get_control_center_proof_detail(proof_ref: str) -> ResultEnvelope:
    data = get_founder_loop_service().proof_detail(proof_ref)
    return ResultEnvelope(
        success=True,
        operation="control_center_proof_detail",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:proof-detail",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:control-center:proof-detail"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/trust-authority/matrix", response_model=ResultEnvelope)
def get_control_center_trust_authority_matrix() -> ResultEnvelope:
    data = get_founder_loop_service().trust_authority_matrix()
    return ResultEnvelope(
        success=True,
        operation="control_center_trust_authority_matrix",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:trust-authority-matrix",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:control-center:trust-authority"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/actions/inbox", response_model=ResultEnvelope)
def get_control_center_actions_inbox() -> ResultEnvelope:
    data = get_founder_loop_service().actions_inbox()
    return ResultEnvelope(
        success=True,
        operation="control_center_actions_inbox",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:actions-inbox",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:action-inbox"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
        ],
    )


@router.get("/memory/review", response_model=ResultEnvelope)
def get_control_center_memory_review() -> ResultEnvelope:
    data = get_founder_loop_service().memory_review()
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_review",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-review",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-review"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
        ],
    )


@router.get("/memory/workbench", response_model=ResultEnvelope)
def get_control_center_memory_workbench(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_workbench(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_WORKBENCH_UNSAFE_QUERY_REF",
                "safe_message": "The Memory Workbench query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_workbench",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-workbench",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-workbench"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_context_injection",
        ],
    )


@router.get("/memory/search", response_model=ResultEnvelope)
def get_control_center_memory_search(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    kind: str | None = Query(default=None, max_length=80),
    source_ref: str | None = Query(default=None, max_length=200),
    project_ref: str | None = Query(default=None, max_length=200),
    person_ref: str | None = Query(default=None, max_length=200),
    org_ref: str | None = Query(default=None, max_length=200),
    deal_ref: str | None = Query(default=None, max_length=200),
    review_state: str | None = Query(default=None, max_length=80),
    quality_state: str | None = Query(default=None, max_length=80),
    stale_state: str | None = Query(default=None, max_length=200),
    conflict_state: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_search(
            query_ref=query_ref,
            safe_query=safe_query,
            kind=kind,
            source_ref=source_ref,
            project_ref=project_ref,
            person_ref=person_ref,
            org_ref=org_ref,
            deal_ref=deal_ref,
            review_state=review_state,
            quality_state=quality_state,
            stale_state=stale_state,
            conflict_state=conflict_state,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_SEARCH_UNSAFE_FILTER",
                "safe_message": "The Memory search filter could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_search",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-search",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-search"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_semantic_search",
            "no_vector_db",
        ],
    )


@router.get("/memory/impact-graph", response_model=ResultEnvelope)
def get_control_center_memory_impact_graph(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_impact_graph(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_IMPACT_GRAPH_UNSAFE_QUERY_REF",
                "safe_message": "The Memory impact graph query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_impact_graph",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-impact-graph",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-impact-graph"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_context_injection",
            "no_action_execution",
            "no_connector_or_crm_sync",
        ],
    )


@router.get("/memory/follow-ups", response_model=ResultEnvelope)
def get_control_center_memory_follow_ups(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_follow_up_queue(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_FOLLOW_UPS_UNSAFE_QUERY_REF",
                "safe_message": "The Memory follow-up queue query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_follow_ups",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-follow-ups",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-follow-ups"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_action_execution",
            "no_memory_write",
            "no_connector_or_crm_sync",
        ],
    )


@router.get("/memory/recall-health", response_model=ResultEnvelope)
def get_control_center_memory_recall_health(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_recall_health_v2(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_RECALL_HEALTH_UNSAFE_QUERY_REF",
                "safe_message": "The Memory recall-health query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_recall_health",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-recall-health",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-recall-health"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_truth_authority",
            "no_context_injection",
            "no_model_or_provider_calls",
        ],
    )


@router.get("/memory/retrieval-diagnostics", response_model=ResultEnvelope)
def get_control_center_memory_retrieval_diagnostics(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_retrieval_diagnostics(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_RETRIEVAL_DIAGNOSTICS_UNSAFE_QUERY_REF",
                "safe_message": "The Memory retrieval diagnostics query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_retrieval_diagnostics",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-retrieval-diagnostics",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-retrieval-diagnostics"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_context_injection",
            "no_semantic_search",
            "no_model_or_provider_calls",
        ],
    )


@router.get("/memory/citation-integrity", response_model=ResultEnvelope)
def get_control_center_memory_citation_integrity(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_citation_integrity(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_CITATION_INTEGRITY_UNSAFE_QUERY_REF",
                "safe_message": "The Memory citation integrity query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_citation_integrity",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-citation-integrity",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-citation-integrity"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_context_injection",
            "no_truth_authority",
        ],
    )


@router.get("/memory/quality-issues", response_model=ResultEnvelope)
def get_control_center_memory_quality_issues(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_quality_issues(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_QUALITY_ISSUES_UNSAFE_QUERY_REF",
                "safe_message": "The Memory quality issue query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_quality_issues",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-quality-issues",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-quality-issues"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_memory_write",
            "no_action_execution",
        ],
    )


@router.get("/memory/maintenance-runs", response_model=ResultEnvelope)
def get_control_center_memory_maintenance_runs(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_maintenance_runs(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_MAINTENANCE_RUNS_UNSAFE_QUERY_REF",
                "safe_message": "The Memory maintenance run query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_maintenance_runs",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-maintenance-runs",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-maintenance-runs"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_auto_merge",
            "no_auto_forget",
            "no_memory_write",
        ],
    )


@router.get("/memory/context-manifest", response_model=ResultEnvelope)
def get_control_center_memory_context_manifest(
    query_ref: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_context_manifest(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_CONTEXT_MANIFEST_UNSAFE_QUERY_REF",
                "safe_message": "The Memory context manifest query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_context_manifest",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-context-manifest",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-context-manifest"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_hidden_context_injection",
            "no_model_or_provider_calls",
        ],
    )


@router.get("/memory/l1-index", response_model=ResultEnvelope)
def get_control_center_memory_l1_index(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_l1_hot_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_L1_INDEX_UNSAFE_QUERY_REF",
                "safe_message": "The Memory L1 index query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_l1_index",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-l1-index",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-l1-index"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_context_injection",
        ],
    )


@router.get("/memory/l2-index", response_model=ResultEnvelope)
def get_control_center_memory_l2_index(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_l2_factual_graph_temporal_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_L2_INDEX_UNSAFE_QUERY_REF",
                "safe_message": "The Memory L2 index query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_l2_index",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-l2-index",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-l2-index"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_truth_authority",
            "no_context_injection",
            "no_semantic_extraction",
        ],
    )


@router.get("/memory/l3-index", response_model=ResultEnvelope)
def get_control_center_memory_l3_index(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_l3_identity_session_preference_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_L3_INDEX_UNSAFE_QUERY_REF",
                "safe_message": "The Memory L3 index query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_l3_index",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-l3-index",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-l3-index"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_truth_authority",
            "no_context_injection",
            "no_crm_or_account_sync",
            "proposal_only",
        ],
    )


@router.get("/memory/context-packs", response_model=ResultEnvelope)
def get_control_center_memory_context_packs(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_context_pack_proposals(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_UNSAFE_QUERY_REF",
                "safe_message": "The Memory context-pack proposal query ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_context_packs",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-context-packs",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-context-packs"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "proposal_only",
            "no_hidden_context_injection",
            "no_provider_or_model_calls",
            "no_connector_or_crm_sync",
        ],
    )


@router.get(
    "/memory/context-packs/{context_pack_ref}/preview",
    response_model=ResultEnvelope,
)
def get_control_center_memory_context_pack_preview(
    context_pack_ref: str,
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_context_pack_preview(
            context_pack_ref=context_pack_ref,
        )
    except FounderLoopStorageError as exc:
        status_code = (
            404
            if str(exc) == "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_NOT_FOUND"
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_ERROR",
                "safe_message": (
                    "The Memory context-pack preview could not be inspected safely."
                ),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_UNSAFE_REF",
                "safe_message": (
                    "The Memory context-pack preview ref could not be inspected safely."
                ),
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_context_pack_preview",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-context-pack-preview",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-context-pack-preview"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "read_only_preview",
            "no_runtime_context_injection",
            "no_provider_or_model_calls",
            "no_connector_or_crm_sync",
        ],
    )


@router.post(
    "/memory/context-packs/{context_pack_ref}/action-proposal",
    response_model=ResultEnvelope,
)
def post_control_center_memory_context_pack_action_proposal(
    context_pack_ref: str,
    request: MemoryContextPackActionProposalRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": (
                    str(exc)
                    or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_IDEMPOTENCY_CONFLICT"
                ),
                "safe_message": (
                    "The Memory context-pack Action proposal idempotency key "
                    "already exists with different safe proposal payload refs."
                ),
            },
        ) from exc
    except FounderLoopAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": exc.code,
                "safe_message": (
                    "Memory context-pack Action proposal creation requires an "
                    "active AuthorityLease granting Memory draft. The proposal "
                    "does not execute actions or inject context."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": exc.required_refs,
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_ERROR"
        status_code = (
            404
            if code == "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_NOT_FOUND"
            else 403
            if code == "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_APPROVAL_REQUIRED"
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": (
                    "The Memory context-pack internal Action proposal could not "
                    "be recorded safely."
                ),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_UNSAFE_INPUT",
                "safe_message": (
                    "The Memory context-pack Action proposal request contains "
                    "unsafe refs."
                ),
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_context_pack_action_proposal",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-context-pack-action-proposal",
        data=data,
        evidence=[
            {
                "evidence_ref": (
                    "evidence-ref:founder-loop:memory-context-pack-action-proposal"
                )
            }
        ],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
            "no_action_execution",
            "no_context_injection",
            "no_external_side_effects",
            "authority_decision_refs_only",
        ],
    )


@router.post("/memory/feedback", response_model=ResultEnvelope)
def post_control_center_memory_feedback(
    request: MemoryFeedbackRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().record_memory_feedback(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_MEMORY_FEEDBACK_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Memory feedback idempotency key already exists with "
                    "different safe feedback refs."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_MEMORY_FEEDBACK_ERROR"
        raise HTTPException(
            status_code=404
            if code
            in {
                "FOUNDER_LOOP_MEMORY_FEEDBACK_RECORD_NOT_FOUND",
                "FOUNDER_LOOP_MEMORY_FEEDBACK_TARGET_NOT_FOUND",
            }
            else 400,
            detail={
                "code": code,
                "safe_message": "The Memory feedback receipt could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_FEEDBACK_UNSAFE_INPUT",
                "safe_message": "The Memory feedback request contains unsafe refs.",
            },
        ) from exc
    feedback_redactions = [
        "safe_refs_only",
        "receipt_refs_only",
        "raw_content_omitted",
    ]
    if request.memory_record_ref is None:
        feedback_redactions.append("no_memory_write")
    else:
        feedback_redactions.extend(
            [
                "memory_feedback_metadata_update_only",
                "no_new_memory_record_write",
            ]
        )
    feedback_redactions.extend(
        [
            "no_context_injection",
            "no_action_execution",
            "no_connector_write",
        ]
    )
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_feedback",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-feedback",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-feedback"}],
        redactions_applied=feedback_redactions,
    )


@router.get("/memory/observation-candidates", response_model=ResultEnvelope)
def get_control_center_memory_observation_candidates(
    query_ref: str | None = Query(default=None, max_length=200),
    safe_query: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_observation_candidates(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_OBSERVATION_UNSAFE_QUERY",
                "safe_message": "The Memory observation query could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_observation_candidates",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-observation-candidates",
        data=data,
        evidence=[
            {
                "evidence_ref": (
                    "evidence-ref:founder-loop:memory-observation-candidates"
                )
            }
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_context_injection",
            "no_truth_authority",
        ],
    )


@router.get("/memory/probe", response_model=ResultEnvelope)
def get_control_center_memory_probe(
    entity_ref: str = Query(..., max_length=220),
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_probe(
            entity_ref=entity_ref,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_PROBE_UNSAFE_ENTITY_REF",
                "safe_message": "The Memory probe entity ref could not be inspected safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_probe",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-probe",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-probe"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "inspection_only",
            "no_context_injection",
        ],
    )


@router.get("/memory/contradictions", response_model=ResultEnvelope)
def get_control_center_memory_contradictions(
    limit: int = Query(default=20, ge=1, le=50),
) -> ResultEnvelope:
    data = get_founder_loop_service().memory_contradictions(limit=limit)
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_contradictions",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-contradictions",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-contradictions"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "preview_only",
            "no_context_injection",
            "no_auto_merge",
        ],
    )


@router.get("/memory/review/{candidate_ref}/receipt", response_model=ResultEnvelope)
def get_control_center_memory_review_receipt(candidate_ref: str) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().memory_review_receipt(
            candidate_ref=candidate_ref
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_REF_DENIED",
                "safe_message": "Memory Review receipt lookup requires a safe candidate ref.",
            },
        ) from exc
    if data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_NOT_FOUND",
                "safe_message": "No Memory Review decision receipt exists for this safe candidate ref.",
            },
        )
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_review_receipt",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-review-receipt",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-review-decision"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.get("/evidence/timeline", response_model=ResultEnvelope)
def get_control_center_evidence_timeline() -> ResultEnvelope:
    data = get_founder_loop_service().evidence_timeline()
    return ResultEnvelope(
        success=True,
        operation="control_center_evidence_timeline",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:evidence-timeline",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:evidence-timeline"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
        ],
    )


@router.get("/agent-loop/thread", response_model=ResultEnvelope)
def get_control_center_agent_loop_thread() -> ResultEnvelope:
    data = get_founder_loop_service().agent_loop_thread()
    return ResultEnvelope(
        success=True,
        operation="control_center_agent_loop_thread",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:agent-loop-thread",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:control-center:agent-loop-thread"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "raw_prompt_omitted",
            "raw_response_omitted",
            "raw_provider_payload_omitted",
            "raw_local_paths_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.post("/web-evidence/attach", response_model=ResultEnvelope)
def post_control_center_web_evidence_attach(
    request: WebEvidenceProductSliceRequest,
) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().attach_web_evidence(
            request,
            active_authority_leases=AuthorityLeaseStore().list_leases(active_only=True),
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONTROL_CENTER_WEB_EVIDENCE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The web evidence request ref already points to a different "
                    "receipt fingerprint."
                ),
            },
        ) from exc
    except WebEvidenceProductSliceAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "CONTROL_CENTER_WEB_EVIDENCE_AUTHORITY_DENIED",
                "safe_message": (
                    "Web evidence attach requires an active AuthorityLease "
                    "granting Browser read before WebAccessGateway fetch."
                ),
                "reason_refs": [
                    *exc.decision.reason_refs,
                    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_BLOCKED_REF,
                ],
                "required_refs": {
                    "authority_decision_ref": exc.decision.decision_ref,
                    "required_mode_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_MODE_REF,
                    "required_domain_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF,
                    "required_capability_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF,
                    "safe_disable_ref": exc.decision.safe_disable_ref,
                    "rollback_ref": exc.decision.rollback_ref,
                },
            },
        ) from exc
    except (FounderLoopStorageError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CONTROL_CENTER_WEB_EVIDENCE_REQUEST_BLOCKED",
                "safe_message": (
                    "The web evidence request could not be attached through the "
                    "allowlisted read-only gateway."
                ),
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_web_evidence_attach",
        service="FounderLoopControlCenterAPI",
        trace_id=str(data["receipt_ref"]),
        data=data,
        evidence=[{"evidence_ref": str(data["evidence_ref"])}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_redacted_preview",
            "raw_content_omitted",
            "web_access_gateway_required",
        ],
    )


@router.post("/today/action-envelope", response_model=ResultEnvelope)
def post_control_center_today_action_envelope(
    request: FounderLoopActionEnvelopePromotionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().promote_today_item_to_action_envelope(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_ACTION_ENVELOPE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Today-to-Action envelope idempotency key already exists "
                    "with different safe promotion payload refs."
                ),
            },
        ) from exc
    except FounderLoopAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": exc.code,
                "safe_message": (
                    "Today-to-Action envelope creation requires an active "
                    "AuthorityLease granting Workspace draft. The envelope is "
                    "review-only and does not execute actions."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": exc.required_refs,
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_ERROR"
        status_code = 404 if code == "FOUNDER_LOOP_TODAY_ITEM_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The Today item could not be promoted safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_ACTION_ENVELOPE_UNSAFE_INPUT",
                "safe_message": "The Today-to-Action request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_today_action_envelope",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:today-action-envelope",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:today-action-envelope"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
            "authority_decision_refs_only",
        ],
    )


@router.post("/chat/turns", response_model=ResultEnvelope)
def post_control_center_chat_turn_receipt(
    request: ChatTurnReceiptRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().record_chat_turn_receipt(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_CHAT_TURN_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Chat turn idempotency key already exists with different "
                    "safe receipt payload refs."
                ),
            },
        ) from exc
    except (FounderLoopStorageError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_CHAT_TURN_RECEIPT_ERROR",
                "safe_message": "The Chat turn receipt could not be recorded safely.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_chat_turn_receipt",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:chat-turn-receipt",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:chat-turn-receipt"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.get("/chat/turns/{turn_ref}/receipt", response_model=ResultEnvelope)
def get_control_center_chat_turn_receipt(turn_ref: str) -> ResultEnvelope:
    try:
        data = get_founder_loop_service().chat_turn_receipt(turn_ref=turn_ref)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_CHAT_TURN_REF_UNSAFE",
                "safe_message": "The Chat turn ref could not be inspected safely.",
            },
        ) from exc
    if data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FOUNDER_LOOP_CHAT_TURN_RECEIPT_NOT_FOUND",
                "safe_message": "No Chat turn receipt exists for this safe turn ref.",
            },
        )
    return ResultEnvelope(
        success=True,
        operation="control_center_chat_turn_receipt",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:chat-turn-receipt",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:chat-turn-receipt"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.post("/chat/turns/{turn_ref}/handoff", response_model=ResultEnvelope)
def post_control_center_chat_handoff(
    turn_ref: str,
    request: ChatHandoffRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().record_chat_handoff(
            turn_ref=turn_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_CHAT_HANDOFF_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Chat handoff idempotency key already exists with different "
                    "safe handoff payload refs."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_CHAT_HANDOFF_ERROR"
        status_code = 404 if code == "FOUNDER_LOOP_CHAT_TURN_RECEIPT_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The Chat handoff could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_CHAT_HANDOFF_UNSAFE_INPUT",
                "safe_message": "The Chat handoff request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_chat_handoff",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:chat-handoff",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:chat-handoff"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.post("/memory/review/manual-candidate", response_model=ResultEnvelope)
def post_control_center_memory_review_manual_candidate(
    request: ManualMemoryCandidateRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().record_manual_memory_candidate(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc)
                or "FOUNDER_LOOP_MEMORY_MANUAL_CANDIDATE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The manual Memory candidate idempotency key already exists "
                    "with different safe candidate payload refs."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_MEMORY_MANUAL_CANDIDATE_ERROR",
                "safe_message": "The manual Memory candidate could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_MANUAL_CANDIDATE_UNSAFE_INPUT",
                "safe_message": "The manual Memory candidate contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_manual_candidate",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:memory-manual-candidate",
        data=data,
        evidence=[
            {"evidence_ref": "evidence-ref:founder-loop:memory-manual-candidate"}
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "no_recall_record_created",
        ],
    )


@router.post("/memory/review/{candidate_ref}/accept", response_model=ResultEnvelope)
def post_control_center_memory_review_accept(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/correct", response_model=ResultEnvelope)
def post_control_center_memory_review_correct(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="correct",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/reject", response_model=ResultEnvelope)
def post_control_center_memory_review_reject(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/defer", response_model=ResultEnvelope)
def post_control_center_memory_review_defer(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="defer",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/merge", response_model=ResultEnvelope)
def post_control_center_memory_review_merge(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="merge",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/supersede", response_model=ResultEnvelope)
def post_control_center_memory_review_supersede(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="supersede",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post("/memory/review/{candidate_ref}/expire", response_model=ResultEnvelope)
def post_control_center_memory_review_expire(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="expire",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/memory/review/{candidate_ref}/forget-request",
    response_model=ResultEnvelope,
)
def post_control_center_memory_review_forget_request(
    candidate_ref: str,
    request: MemoryReviewDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="forget_request",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/actions/{action_id}/approve",
    response_model=ResultEnvelope,
    responses=ACTION_DECISION_CONFLICT_RESPONSES,
)
def post_control_center_action_approve_decision(
    action_id: str,
    request: FounderLoopActionDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_action_decision(
        action_id=action_id,
        decision="approve",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/actions/{action_id}/edit",
    response_model=ResultEnvelope,
    responses=ACTION_DECISION_CONFLICT_RESPONSES,
)
def post_control_center_action_edit_decision(
    action_id: str,
    request: FounderLoopActionDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_action_decision(
        action_id=action_id,
        decision="edit",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/actions/{action_id}/reject",
    response_model=ResultEnvelope,
    responses=ACTION_DECISION_CONFLICT_RESPONSES,
)
def post_control_center_action_reject_decision(
    action_id: str,
    request: FounderLoopActionDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_action_decision(
        action_id=action_id,
        decision="reject",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/actions/{action_id}/defer",
    response_model=ResultEnvelope,
    responses=ACTION_DECISION_CONFLICT_RESPONSES,
)
def post_control_center_action_defer_decision(
    action_id: str,
    request: FounderLoopActionDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_action_decision(
        action_id=action_id,
        decision="defer",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.post(
    "/actions/{action_id}/cancel",
    response_model=ResultEnvelope,
    responses=ACTION_DECISION_CONFLICT_RESPONSES,
)
def post_control_center_action_cancel_decision(
    action_id: str,
    request: FounderLoopActionDecisionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    return _record_action_decision(
        action_id=action_id,
        decision="cancel",
        request=request,
        idempotency_key=x_uaa_idempotency_key,
        idempotency_ref=x_uaa_idempotency_ref,
    )


@router.get("/actions/{action_id}/receipt", response_model=ResultEnvelope)
def get_control_center_action_receipt(action_id: str) -> ResultEnvelope:
    data = get_founder_loop_service().action_receipt(action_id=action_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FOUNDER_LOOP_ACTION_RECEIPT_NOT_FOUND",
                "safe_message": "No Action decision receipt exists for this safe action ref.",
            },
        )
    return ResultEnvelope(
        success=True,
        operation="control_center_action_receipt",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:action-receipt",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:action-decision"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.post("/actions/{action_id}/local-task/commit", response_model=ResultEnvelope)
def post_control_center_action_local_task_commit(
    action_id: str,
    request: FounderLoopLocalTaskCommitRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        data = get_founder_loop_service().commit_local_task(
            action_id=action_id,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_LOCAL_TASK_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The local task commit idempotency key already exists with "
                    "different safe task payload refs."
                ),
            },
        ) from exc
    except FounderLoopAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FOUNDER_LOOP_LOCAL_TASK_AUTHORITY_DENIED",
                "safe_message": (
                    "Local task commit requires an active AuthorityLease "
                    "granting Workspace write after exact approval validates."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_LOCAL_TASK_COMMIT_ERROR"
        status_code = (
            404
            if code == "FOUNDER_LOOP_ACTION_NOT_FOUND"
            else 403
            if code
            in {
                "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_REQUIRED",
                "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED",
                "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED",
            }
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The local task commit could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_LOCAL_TASK_UNSAFE_INPUT",
                "safe_message": "The local task commit request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_action_local_task_commit",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:action-local-task-commit",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:local-task-commit"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
            "local_task_refs_only",
        ],
    )


@router.get("/morning-briefing/summary", response_model=ResultEnvelope)
def get_control_center_morning_briefing_summary() -> ResultEnvelope:
    data = get_founder_loop_service().morning_briefing_summary()
    news_signals = get_news_signals_repository().summary(limit=20)
    data["news_signals_projection"] = news_signals["morning_briefing_projection"]
    return ResultEnvelope(
        success=True,
        operation="control_center_morning_briefing_summary",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:morning-briefing",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:morning-briefing"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
        ],
    )


@router.get("/news-signals/summary", response_model=ResultEnvelope)
def get_control_center_news_signals_summary(
    limit: int = Query(default=20, ge=1, le=100),
) -> ResultEnvelope:
    data = get_news_signals_repository().summary(limit=limit)
    return ResultEnvelope(
        success=True,
        operation="control_center_news_signals_summary",
        service="NewsSignalsControlCenterAPI",
        trace_id="news-signals:summary",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:q24:news-signals-read-model"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_source_content_omitted",
            "raw_paths_omitted",
            "external_content_untrusted",
            "read_only_control_center_projection",
        ],
    )


@router.post("/proposal-intelligence/extract", response_model=ResultEnvelope)
def post_control_center_proposal_intelligence_extract(
    request: ProposalExtractionRequest,
) -> ResultEnvelope:
    data = extract_proposal_candidates(request)
    return ResultEnvelope(
        success=True,
        operation="control_center_proposal_intelligence_extract",
        service="ProposalIntelligenceControlCenterAPI",
        trace_id="proposal-intelligence:extract",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:eco-010:deterministic-proposals"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_source_content_omitted",
            "raw_paths_omitted",
            "proposal_only_no_commit",
        ],
    )


@router.get("/autocorrect/status", response_model=ResultEnvelope)
def get_control_center_autocorrect_status() -> ResultEnvelope:
    data = build_autocorrect_control_status()
    return ResultEnvelope(
        success=True,
        operation="control_center_autocorrect_status",
        service="AutocorrectControlCenterAPI",
        trace_id="autocorrect:status",
        data=data.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:queue-v2:Q28:control-status"}],
        redactions_applied=[
            "safe_refs_only",
            "raw_values_omitted",
            "proposal_only_no_commit",
        ],
    )


@router.post("/autocorrect/proposals/preview", response_model=ResultEnvelope)
def post_control_center_autocorrect_proposal_preview(
    request: CorrectionProposalRequest,
) -> ResultEnvelope:
    data = build_correction_proposal(request)
    return ResultEnvelope(
        success=True,
        operation="control_center_autocorrect_proposal_preview",
        service="AutocorrectControlCenterAPI",
        trace_id=data.proposal_ref,
        data=data.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:queue-v2:Q28:proposal-preview"}],
        redactions_applied=[
            "safe_refs_only",
            "content_free_field_diffs_only",
            "raw_values_omitted",
            "proposal_only_no_commit",
        ],
    )


@router.post("/autocorrect/reviews/preview", response_model=ResultEnvelope)
def post_control_center_autocorrect_review_preview(
    request: CorrectionReviewRequest,
) -> ResultEnvelope:
    try:
        data = _AUTOCORRECT_REVIEW_SESSION.review(request)
    except AutocorrectConflict as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc),
                "safe_message": (
                    "The correction review binding changed or reused an idempotency "
                    "reference with a different safe payload."
                ),
            },
        ) from exc
    except AutocorrectError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc),
                "safe_message": (
                    "The bounded process-local correction review registry cannot "
                    "record another preview. Restart or use a durable governed lane."
                ),
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_autocorrect_review_preview",
        service="AutocorrectControlCenterAPI",
        trace_id=data.receipt_ref,
        data=data.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:queue-v2:Q28:review-preview"}],
        redactions_applied=[
            "safe_refs_only",
            "content_free_learning_refs_only",
            "raw_values_omitted",
            "process_local_replay_guard",
            "proposal_only_no_commit",
        ],
    )


@router.get("/sources/readiness", response_model=ResultEnvelope)
def get_control_center_sources_readiness() -> ResultEnvelope:
    data = get_founder_loop_service().source_readiness()
    return ResultEnvelope(
        success=True,
        operation="control_center_sources_readiness",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:sources-readiness",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:source-readiness"}],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "connector_runtime_omitted",
        ],
    )


@router.get("/storage/status", response_model=ResultEnvelope)
def get_control_center_storage_status() -> ResultEnvelope:
    data = get_founder_loop_service().storage_status()
    return ResultEnvelope(
        success=True,
        operation="control_center_storage_status",
        service="FounderLoopControlCenterAPI",
        trace_id="founder-loop:storage-status",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:storage-status"}],
        redactions_applied=["safe_refs_only", "storage_refs_only", "raw_paths_omitted"],
    )


def _record_action_decision(
    *,
    action_id: str,
    decision: Literal["approve", "edit", "reject", "defer", "cancel"],
    request: FounderLoopActionDecisionRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(idempotency_key, idempotency_ref)
    try:
        data = get_founder_loop_service().record_action_decision(
            action_id=action_id,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=AuthorityLeaseStore().list_leases(active_only=True),
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_ACTION_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Action decision idempotency key already exists with "
                    "different safe decision payload refs."
                ),
            },
        ) from exc
    except FounderLoopActionRevisionConflict as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": exc.code,
                "safe_message": (
                    "The Action changed after this decision was prepared; "
                    "refresh the authoritative Action Inbox before retrying."
                ),
                "refresh_required": True,
                "current_revision_ref": exc.current_revision_ref,
                "current_generation_ref": exc.current_generation_ref,
                "refresh_route_ref": exc.refresh_route_ref,
            },
        ) from exc
    except FounderLoopAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": exc.code,
                "safe_message": (
                    "Action Inbox decision receipts require an active "
                    "AuthorityLease granting Workspace write authority."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": exc.required_refs,
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_ACTION_DECISION_ERROR"
        status_code = (
            404
            if code == "FOUNDER_LOOP_ACTION_NOT_FOUND"
            else 409
            if code
            in {
                "FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED",
                "FOUNDER_LOOP_ACTION_TERMINAL_LOCAL_TASK_COMMITTED",
            }
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The Action decision could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_ACTION_DECISION_UNSAFE_INPUT",
                "safe_message": "The Action decision request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_action_decision",
        service="FounderLoopControlCenterAPI",
        trace_id=f"founder-loop:action-decision:{decision}",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:action-decision"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


def _record_memory_review_decision(
    *,
    candidate_ref: str,
    decision: Literal[
        "accept",
        "correct",
        "reject",
        "defer",
        "merge",
        "supersede",
        "forget_request",
    ],
    request: MemoryReviewDecisionRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(idempotency_key, idempotency_ref)
    try:
        data = get_founder_loop_service().record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_MEMORY_DECISION_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Memory Review decision idempotency key already exists "
                    "with different safe decision payload refs."
                ),
            },
        ) from exc
    except FounderLoopAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_MEMORY_WRITE_AUTHORITY_DENIED",
                "safe_message": (
                    "Memory Review accept/correct requires an active AuthorityLease "
                    "granting Memory write after exact approval validates."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_MEMORY_DECISION_ERROR"
        status_code = 404 if code == "FOUNDER_LOOP_MEMORY_CANDIDATE_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The Memory Review decision could not be recorded safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_MEMORY_DECISION_UNSAFE_INPUT",
                "safe_message": "The Memory Review decision request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_memory_review_decision",
        service="FounderLoopControlCenterAPI",
        trace_id=f"founder-loop:memory-review-decision:{decision}",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-review-decision"}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


def _idempotency_key_ref(
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> str:
    value = (idempotency_key or idempotency_ref or "").strip()
    if not value:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "API_IDEMPOTENCY_REQUIRED",
                "safe_message": "Mutating Control Center routes require an idempotency key.",
            },
        )
    return value


def register_founder_loop_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
