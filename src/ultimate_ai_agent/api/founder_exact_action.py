from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime

from fastapi import APIRouter, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ultimate_ai_agent.api.dependencies import get_founder_attention_workflow
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
    idempotency_value_valid,
)
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.control_center.founder_loop_attention_workflow import (
    FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF,
    attention_execution_owner_ref,
    build_attention_workflow_request,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope


router = APIRouter(prefix="/control-center", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_founder_exact_action_routes_registered"
_REDACTIONS = [
    "safe_refs_only",
    "raw_content_omitted",
    "raw_paths_omitted",
    "filesystem_content_omitted",
]
_SAFE_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class FounderExactActionPrepareRequest(BaseModel):
    workflow_ref: str = Field(..., min_length=1)
    today_item_ref: str = Field(..., min_length=1)
    inspected_source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    source_review_receipt_ref: str = Field(..., min_length=1)
    mission_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    lease_ref: str = Field(..., min_length=1)
    start_deadline: datetime
    safe_goal_summary: str | None = Field(
        default=None,
        max_length=320,
        exclude=True,
        description=(
            "Accepted for backward compatibility but ignored; the backend owns "
            "the only durable safe goal summary for this exact lane."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class FounderExactActionApprovalRequest(BaseModel):
    workflow_ref: str = Field(..., min_length=1)
    today_item_ref: str = Field(..., min_length=1)
    inspected_source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    source_review_receipt_ref: str = Field(..., min_length=1)
    proposal_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class FounderExactActionExecuteRequest(FounderExactActionApprovalRequest):
    approval_ref: str = Field(..., min_length=1)


class FounderExactActionSourceReviewRequest(BaseModel):
    today_item_ref: str = Field(..., min_length=1)
    inspected_source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    mission_ref: str = Field(..., min_length=1)
    lease_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


def _stable_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return f"{prefix}:sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def _idempotency_ref(key: str | None, ref: str | None) -> str:
    valid_values = [
        value.strip() for value in (key, ref) if idempotency_value_valid(value)
    ]
    if len(set(valid_values)) > 1:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "API_IDEMPOTENCY_CONFLICT",
                "safe_message": "The supplied idempotency values do not match.",
            },
        )
    if valid_values:
        return valid_values[0]
    supplied_values = [value for value in (key, ref) if value and value.strip()]
    if not supplied_values:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "API_IDEMPOTENCY_REQUIRED",
                "safe_message": "Exact Founder Loop mutations require idempotency.",
            },
        )
    raise HTTPException(
        status_code=400,
        detail={
            "code": "API_IDEMPOTENCY_INVALID",
            "safe_message": "The supplied idempotency value is invalid.",
        },
    )


def _safe_error_code(exc: ValueError, fallback: str) -> str:
    candidate = str(exc)
    return candidate if _SAFE_ERROR_CODE.fullmatch(candidate) else fallback


@router.get(
    "/today/exact-action/{today_item_ref}/status", response_model=ResultEnvelope
)
def get_control_center_today_exact_action_status(
    today_item_ref: str,
) -> ResultEnvelope:
    workflow = get_founder_attention_workflow()
    try:
        source_refs = workflow.required_source_refs(today_item_ref)
        verified = workflow.verified_status(today_item_ref)
        action = verified.action
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FOUNDER_LOOP_ATTENTION_ITEM_NOT_FOUND",
                "safe_message": "The requested Today attention item is unavailable.",
            },
        ) from exc
    target = next(iter(workflow.mission_service.targets.values()))
    return ResultEnvelope(
        success=True,
        operation="control_center_today_exact_action_status",
        service="FounderExactActionAPI",
        trace_id=today_item_ref,
        data={
            "contract_ref": FOUNDER_LOOP_ATTENTION_WORKFLOW_CONTRACT_REF,
            "today_item_ref": today_item_ref,
            "target_ref": target.target_ref,
            "root_ref": target.root_ref,
            "path_ref": target.path_ref,
            "target_label": target.safe_label,
            "required_inspected_source_refs": list(source_refs),
            "workflow_status": action.status,
            "receipt_refs": list(action.receipt_refs),
            "evidence_refs": list(action.evidence_refs),
            "required_authority_domain": "files",
            "required_authority_capability": "read",
            "mission_scoped_lease_required": True,
            "exact_approval_required": verified.exact_approval_required,
            "execution_performed": verified.execution_performed,
            "execution_truth_status": verified.execution_truth_status,
            "approval_truth_status": verified.approval_truth_status,
            "recovery_required": verified.recovery_required,
            "broad_filesystem_authority_enabled": False,
        },
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:exact-action-status"}],
        redactions_applied=list(_REDACTIONS),
    )


@router.post("/today/exact-action/source-review", response_model=ResultEnvelope)
def post_control_center_today_exact_action_source_review(
    request: FounderExactActionSourceReviewRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        receipt = get_founder_attention_workflow().review_source_refs(
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            idempotency_ref=_stable_ref(
                "idempotency-ref:founder-attention-source-review",
                {
                    "today_item_ref": request.today_item_ref,
                    "idempotency_ref": idempotency_ref,
                },
            ),
            mission_ref=request.mission_ref,
            lease_ref=request.lease_ref,
        )
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": _safe_error_code(
                    exc, "FOUNDER_LOOP_ATTENTION_SOURCE_REVIEW_CONFLICT"
                ),
                "safe_message": "The exact source-ref review could not be recorded.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_today_exact_action_source_review",
        service="FounderExactActionAPI",
        trace_id=receipt.source_review_receipt_ref,
        data=receipt.model_dump(mode="json"),
        evidence=[{"evidence_ref": receipt.source_review_receipt_ref}],
        redactions_applied=list(_REDACTIONS),
    )


@router.post("/today/exact-action/prepare", response_model=ResultEnvelope)
def post_control_center_today_exact_action_prepare(
    request: FounderExactActionPrepareRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    workflow = get_founder_attention_workflow()
    target = next(iter(workflow.mission_service.targets.values()))
    try:
        workflow_request = build_attention_workflow_request(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            lease_ref=request.lease_ref,
            start_deadline=request.start_deadline,
            idempotency_ref=idempotency_ref,
            target_ref=target.target_ref,
        )
        prepared = workflow.prepare(workflow_request)
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": _safe_error_code(
                    exc, "FOUNDER_LOOP_ATTENTION_PREPARE_CONFLICT"
                ),
                "safe_message": "The exact Founder Loop action could not be prepared.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_today_exact_action_prepare",
        service="FounderExactActionAPI",
        trace_id=prepared.proposal_ref,
        data={**prepared.model_dump(mode="json"), "execution_performed": False},
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:exact-action-prepared"}],
        redactions_applied=list(_REDACTIONS),
    )


@router.post("/today/exact-action/approve", response_model=ResultEnvelope)
def post_control_center_today_exact_action_approve(
    request: FounderExactActionApprovalRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    approval_ref = _stable_ref(
        "approval-ref:founder-loop-attention",
        {"proposal_ref": request.proposal_ref, "idempotency_ref": idempotency_ref},
    )
    try:
        approval_ref = get_founder_attention_workflow().grant_exact_approval(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=request.proposal_ref,
            approved_by_actor_ref="operator-ref:local-user",
            approval_ref=approval_ref,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": _safe_error_code(
                    exc, "FOUNDER_LOOP_ATTENTION_APPROVAL_CONFLICT"
                ),
                "safe_message": "The exact Founder Loop approval could not be recorded.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_today_exact_action_approve",
        service="FounderExactActionAPI",
        trace_id=approval_ref,
        data={
            "proposal_ref": request.proposal_ref,
            "approval_ref": approval_ref,
            "approval_ref_is_identifier_only": True,
            "exact_scope_recorded_by_python_core": True,
            "execution_scope_validation_pending": True,
            "execution_performed": False,
        },
        evidence=[{"evidence_ref": "evidence-ref:founder-loop:exact-action-approved"}],
        redactions_applied=list(_REDACTIONS),
    )


@router.post("/today/exact-action/execute", response_model=ResultEnvelope)
def post_control_center_today_exact_action_execute(
    request: FounderExactActionExecuteRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        result = get_founder_attention_workflow().execute(
            workflow_ref=request.workflow_ref,
            today_item_ref=request.today_item_ref,
            inspected_source_refs=request.inspected_source_refs,
            source_review_receipt_ref=request.source_review_receipt_ref,
            proposal_ref=request.proposal_ref,
            approval_ref=request.approval_ref,
            owner_ref=attention_execution_owner_ref(
                proposal_ref=request.proposal_ref,
                idempotency_ref=idempotency_ref,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": _safe_error_code(
                    exc, "FOUNDER_LOOP_ATTENTION_EXECUTION_CONFLICT"
                ),
                "safe_message": "The exact Founder Loop action did not complete.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_today_exact_action_execute",
        service="FounderExactActionAPI",
        trace_id=result.completion_ref,
        data=result.model_dump(mode="json"),
        evidence=[{"evidence_ref": result.completion_ref}],
        redactions_applied=list(_REDACTIONS),
    )


def register_founder_exact_action_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
