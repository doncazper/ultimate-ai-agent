from __future__ import annotations

from fastapi import APIRouter, FastAPI

from ultimate_ai_agent.api.dependencies import get_founder_loop_service
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope


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


def register_founder_loop_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
