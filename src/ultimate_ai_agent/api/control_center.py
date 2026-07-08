from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query, Request

from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.control_center import (
    ControlCenterActionPreviewRequest,
    build_control_center_dashboard,
    build_control_center_manifest,
    build_work_board_read_model,
    preview_control_center_action,
)
from ultimate_ai_agent.core.control_center.capability_surface import (
    build_control_center_capability_surface_read_model,
)
from ultimate_ai_agent.core.control_center.operational_status import (
    build_control_center_local_models_status,
    build_control_center_settings_status,
)
from ultimate_ai_agent.core.control_center.work_board import (
    WorkBoardApprovalError,
    WorkBoardAuthorityError,
    WorkBoardCardCreateRequest,
    WorkBoardReorderRequest,
    WorkBoardStateStore,
    WorkBoardStorageConflictError,
    WorkBoardTaskCreateRequest,
    prepare_work_board_card_create_approval,
    prepare_work_board_reorder_approval,
    prepare_work_board_task_create_approval,
)
from ultimate_ai_agent.core.code import (
    build_coding_cockpit_session_seed,
    build_coding_git_review,
    build_coding_live_preview,
    build_coding_multi_agent_review,
    build_coding_patch_apply_readiness,
    build_coding_patch_proposal_preview,
    build_coding_test_command_readiness,
    build_coding_workspace_context_preview,
)
from ultimate_ai_agent.core.decision_router import (
    TurnRouterPreviewRequest,
    build_turn_router_preview,
)
from ultimate_ai_agent.core.crm import (
    CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
    CrmLocalAuthorityError,
    CrmLocalCommandCenterDuplicateError,
    CrmLocalCommandCenterError,
    CrmLocalMutationRequest,
    CrmLocalStore,
    build_crm_local_command_center_read_model,
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


@router.get("/coding/patch-apply-readiness", response_model=ResultEnvelope)
def get_control_center_coding_patch_apply_readiness() -> ResultEnvelope:
    readiness = build_coding_patch_apply_readiness()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_patch_apply_readiness",
        service="ControlCenterCodingAPI",
        trace_id=readiness.readiness_ref,
        data=readiness.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-patch-apply-readiness"}],
        redactions_applied=readiness.redactions_applied,
    )


@router.get("/coding/test-command-readiness", response_model=ResultEnvelope)
def get_control_center_coding_test_command_readiness() -> ResultEnvelope:
    readiness = build_coding_test_command_readiness()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_test_command_readiness",
        service="ControlCenterCodingAPI",
        trace_id=readiness.readiness_ref,
        data=readiness.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-test-command-readiness"}],
        redactions_applied=readiness.redactions_applied,
    )


@router.get("/coding/git-review", response_model=ResultEnvelope)
def get_control_center_coding_git_review() -> ResultEnvelope:
    review = build_coding_git_review()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_git_review",
        service="ControlCenterCodingAPI",
        trace_id=review.git_review_ref,
        data=review.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-git-review"}],
        redactions_applied=review.redactions_applied,
    )


@router.get("/coding/live-preview", response_model=ResultEnvelope)
def get_control_center_coding_live_preview() -> ResultEnvelope:
    preview = build_coding_live_preview()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_live_preview",
        service="ControlCenterCodingAPI",
        trace_id=preview.live_preview_ref,
        data=preview.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-live-preview"}],
        redactions_applied=preview.redactions_applied,
    )


@router.get("/coding/multi-agent-review", response_model=ResultEnvelope)
def get_control_center_coding_multi_agent_review() -> ResultEnvelope:
    review = build_coding_multi_agent_review()
    return ResultEnvelope(
        success=True,
        operation="control_center_coding_multi_agent_review",
        service="ControlCenterCodingAPI",
        trace_id=review.review_ref,
        data=review.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:coding-multi-agent-review"}],
        redactions_applied=review.redactions_applied,
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


@router.get("/capabilities/surface", response_model=ResultEnvelope)
def get_control_center_capability_surface(request: Request) -> ResultEnvelope:
    api_manifest = build_api_manifest(request.app)
    surface = build_control_center_capability_surface_read_model(
        live_api_routes=api_manifest.routes,
    )
    return ResultEnvelope(
        success=True,
        operation="control_center_capability_surface",
        service="ControlCenterAPI",
        trace_id=surface.read_model_ref,
        data=surface.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:control-center-capability-surface"}],
        redactions_applied=surface.redactions_applied,
    )


@router.get("/crm/summary", response_model=ResultEnvelope)
def get_control_center_crm_summary() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_summary",
        trace_id=crm.contract_ref,
        data=crm.model_dump(mode="json"),
        evidence_ref="evidence-ref:crm-local-command-center:summary",
    )


@router.get("/crm/relationships", response_model=ResultEnvelope)
def get_control_center_crm_relationships() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_relationships",
        trace_id=crm.contract_ref,
        data={
            "contract_ref": crm.contract_ref,
            "authority_posture": crm.authority_posture.model_dump(mode="json"),
            "storage_status": crm.storage_status.model_dump(mode="json"),
            "people": [item.model_dump(mode="json") for item in crm.people],
            "organizations": [
                item.model_dump(mode="json") for item in crm.organizations
            ],
            "relationships": [
                item.model_dump(mode="json") for item in crm.relationships
            ],
            "communication_drafts": [
                item.model_dump(mode="json") for item in crm.communication_drafts
            ],
            "ai_proposals": [
                item.model_dump(mode="json") for item in crm.ai_proposals
            ],
        },
        evidence_ref="evidence-ref:crm-local-command-center:relationships",
    )


@router.get("/crm/timeline", response_model=ResultEnvelope)
def get_control_center_crm_timeline() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_timeline",
        trace_id=crm.contract_ref,
        data={
            "contract_ref": crm.contract_ref,
            "timeline_events": [
                item.model_dump(mode="json") for item in crm.timeline_events
            ],
            "reports": [item.model_dump(mode="json") for item in crm.reports],
        },
        evidence_ref="evidence-ref:crm-local-command-center:timeline",
    )


@router.get("/crm/follow-ups", response_model=ResultEnvelope)
def get_control_center_crm_follow_ups() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_follow_ups",
        trace_id=crm.contract_ref,
        data={
            "contract_ref": crm.contract_ref,
            "follow_ups": [item.model_dump(mode="json") for item in crm.follow_ups],
            "authority_posture": crm.authority_posture.model_dump(mode="json"),
        },
        evidence_ref="evidence-ref:crm-local-command-center:follow-ups",
    )


@router.get("/crm/pipelines", response_model=ResultEnvelope)
def get_control_center_crm_pipelines() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_pipelines",
        trace_id=crm.contract_ref,
        data={
            "contract_ref": crm.contract_ref,
            "pipelines": [item.model_dump(mode="json") for item in crm.pipelines],
            "opportunities": [
                item.model_dump(mode="json") for item in crm.opportunities
            ],
            "authority_posture": crm.authority_posture.model_dump(mode="json"),
        },
        evidence_ref="evidence-ref:crm-local-command-center:pipelines",
    )


@router.get("/crm/smart-lists", response_model=ResultEnvelope)
def get_control_center_crm_smart_lists() -> ResultEnvelope:
    crm = build_crm_local_command_center_read_model()
    return _crm_result_envelope(
        operation="control_center_crm_smart_lists",
        trace_id=crm.contract_ref,
        data={
            "contract_ref": crm.contract_ref,
            "smart_lists": [
                item.model_dump(mode="json") for item in crm.smart_lists
            ],
            "connector_read_lanes": crm.connector_read_lanes.model_dump(mode="json"),
            "sends_writes_authority_plan": (
                crm.sends_writes_authority_plan.model_dump(mode="json")
            ),
            "import_export_posture": crm.import_export_posture.model_dump(
                mode="json"
            ),
        },
        evidence_ref="evidence-ref:crm-local-command-center:smart-lists",
    )


@router.post("/crm/local-mutations", response_model=ResultEnvelope)
def post_control_center_crm_local_mutation(
    request: CrmLocalMutationRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _crm_idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    try:
        receipt = CrmLocalStore.from_env().record_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
        )
    except CrmLocalCommandCenterDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "CRM_LOCAL_MUTATION_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The CRM local mutation idempotency ref already has a "
                    "different safe payload fingerprint."
                ),
            },
        ) from exc
    except CrmLocalAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": str(exc) or "CRM_LOCAL_MUTATION_AUTHORITY_DENIED",
                "safe_message": (
                    "CRM local mutation requires an active AuthorityLease "
                    "granting Contacts write after exact approval validates."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except CrmLocalCommandCenterError as exc:
        code = str(exc) or "CRM_LOCAL_MUTATION_ERROR"
        raise HTTPException(
            status_code=403,
            detail={
                "code": code,
                "safe_message": (
                    "The exact local-only CRM mutation could not be recorded safely."
                ),
            },
        ) from exc
    return _crm_result_envelope(
        operation="control_center_crm_local_mutation",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
        evidence_ref="evidence-ref:crm-local-command-center:local-mutation",
    )


@router.get("/work-board", response_model=ResultEnvelope)
def get_control_center_work_board() -> ResultEnvelope:
    board = build_work_board_read_model()
    return ResultEnvelope(
        success=True,
        operation="control_center_work_board",
        service="ControlCenterWorkBoardAPI",
        trace_id=board.board_ref,
        data=board.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:work-board-read-model"}],
        redactions_applied=board.redactions_applied,
    )


@router.post("/work-board/reorder", response_model=ResultEnvelope)
def post_control_center_work_board_reorder(
    request: WorkBoardReorderRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _work_board_idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    base_board = build_work_board_read_model()
    try:
        receipt = WorkBoardStateStore().persist_reorder(
            request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
        )
    except WorkBoardStorageConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "WORK_BOARD_REORDER_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Work Board reorder idempotency ref already exists with "
                    "different safe card order refs."
                ),
            },
        ) from exc
    except WorkBoardApprovalError as exc:
        required_refs = dict(exc.required_refs)
        if not required_refs:
            try:
                approval_preview = prepare_work_board_reorder_approval(
                    request,
                    columns=base_board.columns,
                    cards=base_board.cards,
                    idempotency_ref=idempotency_ref,
                )
                required_refs = {
                    "approval_ref": approval_preview.expected_approval_ref,
                    "exact_scope_ref": approval_preview.exact_scope_ref,
                    "action_envelope_ref": approval_preview.action_envelope_ref,
                }
            except ValueError:
                required_refs = {}
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_REORDER_APPROVAL_DENIED",
                "safe_message": (
                    "Work Board reorder requires an exact approved approval "
                    "ref, scope ref, and action envelope before persistence."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": required_refs,
            },
        ) from exc
    except WorkBoardAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_REORDER_AUTHORITY_DENIED",
                "safe_message": (
                    "Work Board reorder requires an active AuthorityLease "
                    "granting Workspace write after exact approval validates."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "WORK_BOARD_REORDER_UNSAFE_INPUT",
                "safe_message": "The Work Board reorder request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_work_board_reorder",
        service="ControlCenterWorkBoardAPI",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
        evidence=[{"evidence_ref": receipt.evidence_ref}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.post("/work-board/cards", response_model=ResultEnvelope)
def post_control_center_work_board_card_create(
    request: WorkBoardCardCreateRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _work_board_idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    base_board = build_work_board_read_model()
    try:
        receipt = WorkBoardStateStore().persist_card_create(
            request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
        )
    except WorkBoardStorageConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "WORK_BOARD_CARD_CREATE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Work Board card create idempotency ref already exists "
                    "with a different safe card payload."
                ),
            },
        ) from exc
    except WorkBoardApprovalError as exc:
        required_refs = dict(exc.required_refs)
        if not required_refs:
            try:
                approval_preview = prepare_work_board_card_create_approval(
                    request,
                    columns=base_board.columns,
                    cards=base_board.cards,
                    idempotency_ref=idempotency_ref,
                )
                required_refs = {
                    "approval_ref": approval_preview.expected_approval_ref,
                    "exact_scope_ref": approval_preview.exact_scope_ref,
                    "action_envelope_ref": approval_preview.action_envelope_ref,
                    "card_ref": approval_preview.card_ref,
                }
            except ValueError:
                required_refs = {}
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_CARD_CREATE_APPROVAL_DENIED",
                "safe_message": (
                    "Work Board card create requires an exact approved approval "
                    "ref, scope ref, and action envelope before persistence."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": required_refs,
            },
        ) from exc
    except WorkBoardAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_CARD_CREATE_AUTHORITY_DENIED",
                "safe_message": (
                    "Work Board card create requires an active AuthorityLease "
                    "granting Workspace write after exact approval validates."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "WORK_BOARD_CARD_CREATE_UNSAFE_INPUT",
                "safe_message": "The Work Board card create request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_work_board_card_create",
        service="ControlCenterWorkBoardAPI",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
        evidence=[{"evidence_ref": receipt.evidence_ref}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
    )


@router.post("/work-board/tasks", response_model=ResultEnvelope)
def post_control_center_work_board_task_create(
    request: WorkBoardTaskCreateRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_ref = _work_board_idempotency_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    base_board = build_work_board_read_model()
    try:
        receipt = WorkBoardStateStore().persist_task_create(
            request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
        )
    except WorkBoardStorageConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "WORK_BOARD_TASK_CREATE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Work Board task create idempotency ref already exists "
                    "with a different safe card payload, or the card already has "
                    "a local task record."
                ),
            },
        ) from exc
    except WorkBoardApprovalError as exc:
        required_refs = dict(exc.required_refs)
        if not required_refs:
            try:
                approval_preview = prepare_work_board_task_create_approval(
                    request,
                    cards=base_board.cards,
                    idempotency_ref=idempotency_ref,
                )
                required_refs = {
                    "approval_ref": approval_preview.expected_approval_ref,
                    "exact_scope_ref": approval_preview.exact_scope_ref,
                    "action_envelope_ref": approval_preview.action_envelope_ref,
                    "local_task_ref": approval_preview.local_task_ref,
                }
            except ValueError:
                required_refs = {}
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_TASK_CREATE_APPROVAL_DENIED",
                "safe_message": (
                    "Work Board task create requires an exact approved approval "
                    "ref, scope ref, and action envelope before local task record "
                    "persistence."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": required_refs,
            },
        ) from exc
    except WorkBoardAuthorityError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "WORK_BOARD_TASK_CREATE_AUTHORITY_DENIED",
                "safe_message": (
                    "Work Board task create requires an active AuthorityLease "
                    "granting Workspace write after exact approval validates. "
                    "It only records a local task ref; no execution or external "
                    "sync is performed."
                ),
                "reason_refs": exc.reason_refs,
                "required_refs": dict(exc.required_refs),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "WORK_BOARD_TASK_CREATE_UNSAFE_INPUT",
                "safe_message": "The Work Board task create request contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_work_board_task_create",
        service="ControlCenterWorkBoardAPI",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
        evidence=[{"evidence_ref": receipt.evidence_ref}],
        redactions_applied=[
            "safe_refs_only",
            "receipt_refs_only",
            "raw_content_omitted",
        ],
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


@router.post("/turn-router/preview", response_model=ResultEnvelope)
def post_control_center_turn_router_preview(
    request: TurnRouterPreviewRequest,
) -> ResultEnvelope:
    preview = build_turn_router_preview(request)
    return ResultEnvelope(
        success=True,
        operation="control_center_turn_router_preview",
        service="ControlCenterAPI",
        trace_id=preview.preview_ref,
        data=preview.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:turn-router-preview:no-effect"}],
        redactions_applied=preview.redactions_applied,
    )


def _crm_result_envelope(
    *,
    operation: str,
    trace_id: str,
    data: object,
    evidence_ref: str,
) -> ResultEnvelope:
    return ResultEnvelope(
        success=True,
        operation=operation,
        service="ControlCenterCrmAPI",
        trace_id=trace_id,
        data=data,
        evidence=[
            {
                "evidence_ref": evidence_ref,
                "contract_ref": CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
            }
        ],
        redactions_applied=[
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_contact_details_omitted",
            "raw_message_bodies_omitted",
            "raw_paths_omitted",
            "provider_payloads_omitted",
        ],
    )


def _crm_idempotency_ref(
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> str:
    value = (idempotency_key or idempotency_ref or "").strip()
    if not value:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "API_IDEMPOTENCY_REQUIRED",
                "safe_message": (
                    "CRM local mutations require an idempotency key or scoped ref."
                ),
            },
        )
    return value


def _task_decomposition_service() -> TaskDecompositionService:
    if _task_decomposition_service_getter is None:
        return TaskDecompositionService.from_env()
    return _task_decomposition_service_getter()


def _work_board_idempotency_ref(
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> str:
    value = (idempotency_key or idempotency_ref or "").strip()
    if value:
        return value
    raise HTTPException(
        status_code=428,
        detail={
            "code": "WORK_BOARD_REORDER_IDEMPOTENCY_REQUIRED",
            "safe_message": "Work Board reorder requires an idempotency ref.",
        },
    )


def _safe_task_decomposition_payload(
    payload: object,
    *,
    redact_read_refs: bool = False,
) -> object:
    return task_decomposition_api_safety.sanitize_task_decomposition_api_payload(
        payload,
        redact_read_refs=redact_read_refs,
    )
