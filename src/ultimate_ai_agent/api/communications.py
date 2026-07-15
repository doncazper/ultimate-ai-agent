from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.communications import (
    CommunicationsReceiptNotFound,
    CommunicationsService,
    build_default_communications_service,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope


router = APIRouter(prefix="/control-center/communications", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_communications_routes_registered"
_SERVICE = build_default_communications_service()
_REDACTIONS = [
    "communications_safe_refs_only",
    "raw_message_content_omitted",
    "provider_payload_omitted",
    "identity_and_credential_material_omitted",
]


def get_communications_service() -> CommunicationsService:
    return _SERVICE


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def _envelope(*, operation: str, trace_id: str, data: object) -> ResultEnvelope:
    return ResultEnvelope(
        success=True,
        operation=operation,
        service="CommunicationsService",
        trace_id=trace_id,
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:communications:contract-inspection"}],
        redactions_applied=list(_REDACTIONS),
    )


@router.get(
    "/providers",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_providers",
)
def get_control_center_communications_providers(response: Response) -> ResultEnvelope:
    _no_store(response)
    descriptors = get_communications_service().inspect_provider_posture()
    return _envelope(
        operation="control_center_communications_providers",
        trace_id="communications-trace:providers",
        data=[descriptor.model_dump(mode="json") for descriptor in descriptors],
    )


@router.get(
    "/session-posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_session_posture",
)
def get_control_center_communications_session_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = get_communications_service().inspect_session_posture()
    return _envelope(
        operation="control_center_communications_session_posture",
        trace_id=posture.session_ref,
        data=posture.model_dump(mode="json"),
    )


@router.get(
    "/rooms",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_rooms",
)
def get_control_center_communications_rooms(
    response: Response,
    limit: int = Query(default=25, ge=1, le=50),
) -> ResultEnvelope:
    _no_store(response)
    page = get_communications_service().list_rooms(limit=limit)
    return _envelope(
        operation="control_center_communications_rooms",
        trace_id="communications-trace:rooms",
        data=page.model_dump(mode="json"),
    )


@router.get(
    "/failed-sends",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_failed_sends",
)
def get_control_center_communications_failed_sends(
    response: Response,
    limit: int = Query(default=25, ge=1, le=50),
) -> ResultEnvelope:
    _no_store(response)
    page = get_communications_service().list_failed_sends(limit=limit)
    return _envelope(
        operation="control_center_communications_failed_sends",
        trace_id="communications-trace:failed-sends",
        data=page.model_dump(mode="json"),
    )


@router.get(
    "/security-posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_security_posture",
)
def get_control_center_communications_security_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = get_communications_service().inspect_security_posture()
    return _envelope(
        operation="control_center_communications_security_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.get(
    "/receipts/{receipt_ref}",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_receipt",
)
def get_control_center_communications_receipt(
    receipt_ref: str,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    try:
        receipt = get_communications_service().lookup_receipt(receipt_ref)
    except CommunicationsReceiptNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail="COMMUNICATIONS_RECEIPT_NOT_FOUND",
            headers={"Cache-Control": "no-store"},
        ) from exc
    return _envelope(
        operation="control_center_communications_receipt",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
    )


def register_communications_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
