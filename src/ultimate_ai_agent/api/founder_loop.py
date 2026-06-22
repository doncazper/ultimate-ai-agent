from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, FastAPI, Header, HTTPException

from ultimate_ai_agent.api.dependencies import get_founder_loop_service
from ultimate_ai_agent.api.idempotency import IDEMPOTENCY_KEY_HEADER, IDEMPOTENCY_REF_HEADER
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
)
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.memory import MemoryReviewDecisionRequest
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
        redactions_applied=["safe_refs_only", "bounded_summaries_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "bounded_summaries_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "bounded_summaries_only", "raw_content_omitted"],
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
    )


def _record_memory_review_decision(
    *,
    candidate_ref: str,
    decision: Literal["accept", "correct", "reject"],
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
        status_code = (
            404 if code == "FOUNDER_LOOP_MEMORY_CANDIDATE_NOT_FOUND" else 400
        )
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
        redactions_applied=["safe_refs_only", "receipt_refs_only", "raw_content_omitted"],
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
