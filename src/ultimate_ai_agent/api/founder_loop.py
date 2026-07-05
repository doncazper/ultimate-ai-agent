from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query

from ultimate_ai_agent.api.dependencies import get_founder_loop_service
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
    WebEvidenceProductSliceRequest,
)
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.memory import (
    ManualMemoryCandidateRequest,
    MemoryContextPackActionProposalRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


router = APIRouter(prefix="/control-center", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_founder_loop_routes_registered"


@router.get("/today/summary", response_model=ResultEnvelope)
def get_control_center_today_summary() -> ResultEnvelope:
    data = get_founder_loop_service().today_summary()
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
        evidence=[
            {"evidence_ref": "evidence-ref:control-center:trust-authority"}
        ],
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
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-retrieval-diagnostics"}],
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
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-citation-integrity"}],
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
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-maintenance-runs"}],
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
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-context-manifest"}],
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
                "code": str(exc)
                or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_ERROR",
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
        evidence=[
            {"evidence_ref": "evidence-ref:control-center:agent-loop-thread"}
        ],
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
        data = get_founder_loop_service().attach_web_evidence(request)
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
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:memory-manual-candidate"}],
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


@router.post("/actions/{action_id}/approve", response_model=ResultEnvelope)
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


@router.post("/actions/{action_id}/edit", response_model=ResultEnvelope)
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


@router.post("/actions/{action_id}/reject", response_model=ResultEnvelope)
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


@router.post("/actions/{action_id}/defer", response_model=ResultEnvelope)
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
    decision: Literal["approve", "edit", "reject", "defer"],
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
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_ACTION_DECISION_ERROR"
        status_code = 404 if code == "FOUNDER_LOOP_ACTION_NOT_FOUND" else 400
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
