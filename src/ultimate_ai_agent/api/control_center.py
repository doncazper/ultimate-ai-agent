from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Query, Request

from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.control_center import (
    ControlCenterActionPreviewRequest,
    build_control_center_dashboard,
    build_control_center_manifest,
    preview_control_center_action,
)
from ultimate_ai_agent.core.control_center.operational_status import (
    build_control_center_local_models_status,
    build_control_center_settings_status,
)
from ultimate_ai_agent.core.code import (
    build_coding_cockpit_session_seed,
    build_coding_patch_proposal_preview,
    build_coding_workspace_context_preview,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.macos_setup_assistant import (
    build_default_macos_setup_assistant_plan,
)
from ultimate_ai_agent.core.task_decomposition import api_safety as task_decomposition_api_safety
from ultimate_ai_agent.core.task_decomposition.runtime import TaskDecompositionService


router = APIRouter(prefix="/control-center", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_control_center_routes_registered"
_TaskDecompositionServiceGetter = Callable[[], TaskDecompositionService]
_task_decomposition_service_getter: _TaskDecompositionServiceGetter | None = None


def register_control_center_routes(
    app: FastAPI,
    *,
    task_decomposition_service_getter: _TaskDecompositionServiceGetter,
) -> None:
    global _task_decomposition_service_getter
    _task_decomposition_service_getter = task_decomposition_service_getter
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)


@router.get("/manifest", response_model=ResultEnvelope)
def get_control_center_manifest() -> ResultEnvelope:
    manifest = build_control_center_manifest()
    return ResultEnvelope(
        success=True,
        operation="control_center_manifest",
        service="ControlCenterAPI",
        trace_id="system",
        data=manifest.model_dump(mode="json"),
    )


@router.get("/dashboard", response_model=ResultEnvelope)
def get_control_center_dashboard(request: Request) -> ResultEnvelope:
    api_manifest = build_api_manifest(request.app)
    control_center_route_count = sum(
        1 for route in api_manifest.routes if route.path.startswith("/control-center")
    )
    dashboard = build_control_center_dashboard(
        api_route_count=api_manifest.route_count,
        control_center_route_count=control_center_route_count,
        foundation_gate_status="not_run_by_endpoint",
    )
    return ResultEnvelope(
        success=True,
        operation="control_center_dashboard",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.model_dump(mode="json"),
    )


@router.get("/status", response_model=ResultEnvelope)
def get_control_center_status() -> ResultEnvelope:
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_status",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.system_status.model_dump(mode="json"),
    )


@router.get("/coding/session", response_model=ResultEnvelope)
def get_control_center_coding_session() -> ResultEnvelope:
    session = build_coding_cockpit_session_seed()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_session",
        service="ControlCenterCodingAPI",
        trace_id=session.session_ref,
        data=session.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-cockpit-read-model"}],
        redactions_applied=session.redactions_applied,
    )


@router.get("/coding/context", response_model=ResultEnvelope)
def get_control_center_coding_context() -> ResultEnvelope:
    context = build_coding_workspace_context_preview()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_context",
        service="ControlCenterCodingAPI",
        trace_id=context.context_pack_ref,
        data=context.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-context-pack-read-model"}],
        redactions_applied=context.redactions_applied,
    )


@router.get("/coding/patch-proposal", response_model=ResultEnvelope)
def get_control_center_coding_patch_proposal() -> ResultEnvelope:
    proposal = build_coding_patch_proposal_preview()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_patch_proposal",
        service="ControlCenterCodingAPI",
        trace_id=proposal.patch_proposal_ref,
        data=proposal.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-patch-proposal-read-model"}],
        redactions_applied=proposal.redactions_applied,
    )


@router.get("/routes", response_model=ResultEnvelope)
def get_control_center_routes(request: Request) -> ResultEnvelope:
    api_manifest = build_api_manifest(request.app)
    control_center_routes = [
        route.model_dump(mode="json")
        for route in api_manifest.routes
        if route.path.startswith("/control-center")
    ]
    return ResultEnvelope(
        success=True,
        operation="control_center_routes",
        service="ControlCenterAPI",
        trace_id="system",
        data={
            "route_count": len(control_center_routes),
            "routes": control_center_routes,
            "read_only_preview_only": True,
        },
    )


@router.get("/approvals/summary", response_model=ResultEnvelope)
def get_control_center_approvals_summary() -> ResultEnvelope:
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_approvals_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.approval_summary.model_dump(mode="json"),
    )


@router.get("/approvals/queue", response_model=ResultEnvelope)
def get_control_center_approvals_queue(
    run_ref: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> ResultEnvelope:
    queue = _task_decomposition_service().run_attached_approval_queue(run_ref, limit=limit)
    return ResultEnvelope(
        success=True,
        operation="control_center_approvals_queue",
        service="ControlCenterAPI",
        trace_id=run_ref or "control-center:approvals-queue",
        data=_safe_task_decomposition_payload(queue),
        redactions_applied=[
            "safe_refs_only",
            "approval_refs_identifier_only",
            "raw_payloads_omitted",
            "read_only_control_center_projection",
        ],
    )


@router.get("/runs/observability", response_model=ResultEnvelope)
def get_control_center_runs_observability(
    run_ref: str | None = None,
    lifecycle_limit: int = Query(default=50, ge=1, le=200),
    related_limit: int = Query(default=50, ge=1, le=200),
) -> ResultEnvelope:
    observability = _task_decomposition_service().run_observability(
        run_ref,
        lifecycle_limit=lifecycle_limit,
        related_limit=related_limit,
    )
    return ResultEnvelope(
        success=True,
        operation="control_center_runs_observability",
        service="ControlCenterAPI",
        trace_id=run_ref or "control-center:runs-observability",
        data=_safe_task_decomposition_payload(observability),
        redactions_applied=[
            "safe_refs_only",
            "redacted_summaries_only",
            "raw_payloads_omitted",
            "read_only_control_center_projection",
            "runtime_authority_blocked",
        ],
    )


@router.get("/runtime-readiness/summary", response_model=ResultEnvelope)
def get_control_center_runtime_readiness_summary() -> ResultEnvelope:
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_runtime_readiness_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.runtime_readiness_summary.model_dump(mode="json"),
    )


@router.get("/settings/status", response_model=ResultEnvelope)
def get_control_center_settings_status() -> ResultEnvelope:
    status = build_control_center_settings_status()
    return ResultEnvelope(
        success=True,
        operation="control_center_settings_status",
        service="ControlCenterAPI",
        trace_id="control-center:settings-status",
        data=status.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:control-center:settings-status"}],
        redactions_applied=status.redactions_applied,
    )


@router.get("/local-models/status", response_model=ResultEnvelope)
def get_control_center_local_models_status() -> ResultEnvelope:
    status = build_control_center_local_models_status()
    return ResultEnvelope(
        success=True,
        operation="control_center_local_models_status",
        service="ControlCenterAPI",
        trace_id="control-center:local-models-status",
        data=status.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:control-center:local-models-status"}],
        redactions_applied=status.redactions_applied,
    )


@router.get("/foundation-gate/summary", response_model=ResultEnvelope)
def get_control_center_foundation_gate_summary() -> ResultEnvelope:
    dashboard = build_control_center_dashboard(foundation_gate_status="not_run_by_endpoint")
    return ResultEnvelope(
        success=True,
        operation="control_center_foundation_gate_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.foundation_gate_summary.model_dump(mode="json"),
    )


@router.get("/setup-assistant/summary", response_model=ResultEnvelope)
def get_control_center_setup_assistant_summary() -> ResultEnvelope:
    plan = build_default_macos_setup_assistant_plan()
    return ResultEnvelope(
        success=True,
        operation="control_center_setup_assistant_summary",
        service="ControlCenterAPI",
        trace_id=plan.plan_ref,
        data=plan.model_dump(mode="json"),
        redactions_applied=["setup_summary_only", "raw_logs_omitted"],
    )


@router.post("/actions/preview", response_model=ResultEnvelope)
def post_control_center_action_preview(
    request: ControlCenterActionPreviewRequest,
) -> ResultEnvelope:
    decision = preview_control_center_action(request)
    return ResultEnvelope(
        success=decision.allowed,
        operation="control_center_action_preview",
        service="ControlCenterAPI",
        trace_id=request.request_id,
        data=decision.model_dump(mode="json"),
        redactions_applied=decision.metadata.get("redactions_applied", []),
    )


def _task_decomposition_service() -> TaskDecompositionService:
    if _task_decomposition_service_getter is None:
        return TaskDecompositionService.from_env()
    return _task_decomposition_service_getter()


def _safe_task_decomposition_payload(
    payload: object,
    *,
    redact_read_refs: bool = False,
) -> object:
    return task_decomposition_api_safety.sanitize_task_decomposition_api_payload(
        payload,
        redact_read_refs=redact_read_refs,
    )
