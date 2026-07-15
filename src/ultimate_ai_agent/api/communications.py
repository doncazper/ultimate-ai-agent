from __future__ import annotations

from pathlib import Path
from typing import Callable

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, StrictBool, model_validator

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.communications import (
    CommunicationsReceiptNotFound,
    CommunicationsService,
    build_default_communications_service,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.hygiene.envelopes import (
    ErrorCategory,
    ErrorEnvelope,
    Severity,
)
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.communications.matrix_harness import (
    MATRIX_HARNESS_LANES,
    DockerMatrixHarnessBackend,
    MatrixHarnessAuthorityDispatchAdapter,
    MatrixHarnessCommand,
    MatrixHarnessOperation,
    build_matrix_harness_dispatch_request,
    capture_exact_matrix_harness_approval,
    default_matrix_harness_backend_config,
    execute_matrix_harness_command,
)


router = APIRouter(prefix="/control-center/communications", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_communications_routes_registered"
_SERVICE = build_default_communications_service()
_HARNESS_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_REPO_ROOT = Path(__file__).resolve().parents[3]
_REDACTIONS = [
    "communications_safe_refs_only",
    "raw_message_content_omitted",
    "provider_payload_omitted",
    "identity_and_credential_material_omitted",
]


class MatrixHarnessOperationRequest(BaseModel):
    command: MatrixHarnessCommand
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_confirmation(self) -> "MatrixHarnessOperationRequest":
        lane = MATRIX_HARNESS_LANES[self.command.operation]
        if self.confirmed and not lane.approval_required:
            raise ValueError("MATRIX_HARNESS_READ_CONFIRMATION_FORBIDDEN")
        return self


MatrixHarnessOperationHandler = Callable[
    [MatrixHarnessOperationRequest],
    object,
]


def _execute_matrix_harness_operation(
    payload: MatrixHarnessOperationRequest,
) -> object:
    store = AuthorityLeaseStore()
    backend = DockerMatrixHarnessBackend(
        default_matrix_harness_backend_config(_REPO_ROOT),
        kill_switch_engaged=authority_lease_kill_switch_engaged,
    )
    lane = MATRIX_HARNESS_LANES[payload.command.operation]
    approval_ref: str | None = None
    if lane.approval_required and payload.confirmed:
        adapter = MatrixHarnessAuthorityDispatchAdapter(
            operation=payload.command.operation,
            backend=backend,
            authority_leases_provider=lambda: store.list_leases(active_only=False),
        )
        approval_ref = capture_exact_matrix_harness_approval(
            build_matrix_harness_dispatch_request(
                payload.command,
                adapter=adapter,
            ),
            approval_authority=_HARNESS_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    return execute_matrix_harness_command(
        payload.command,
        repo_root=_REPO_ROOT,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,
        lease_store=store,
        approval_authority=_HARNESS_APPROVAL_AUTHORITY,
    )


_HARNESS_OPERATION_HANDLER: MatrixHarnessOperationHandler = (
    _execute_matrix_harness_operation
)


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


def _run_harness_operation(
    operation: MatrixHarnessOperation,
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_HARNESS_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    try:
        result = _HARNESS_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_HARNESS_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = f"control_center_communications_harness_{operation.value}"
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status is None or status == "succeeded":
        return _envelope(
            operation=operation_name,
            trace_id=payload.command.dispatch_ref,
            data=data,
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_HARNESS_OPERATION_NOT_SUCCEEDED",
            category=(
                ErrorCategory.authorization_error
                if status in {"denied", "cancelled_before_start"}
                else ErrorCategory.tool_error
            ),
            safe_message="The exact Matrix harness operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=list(_REDACTIONS),
    )


def _require_harness_idempotency_binding(
    payload: MatrixHarnessOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_HARNESS_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
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


@router.post(
    "/harness/inspect",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_inspect",
)
def post_control_center_communications_harness_inspect(
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_harness_operation(MatrixHarnessOperation.inspect, payload, response)


@router.post(
    "/harness/smoke",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_smoke",
)
def post_control_center_communications_harness_smoke(
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_harness_operation(MatrixHarnessOperation.smoke, payload, response)


@router.post(
    "/harness/start",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_start",
)
def post_control_center_communications_harness_start(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.start, payload, response)


@router.post(
    "/harness/fixture-seed",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_fixture_seed",
)
def post_control_center_communications_harness_fixture_seed(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(
        MatrixHarnessOperation.fixture_seed,
        payload,
        response,
    )


@router.post(
    "/harness/stop",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_stop",
)
def post_control_center_communications_harness_stop(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.stop, payload, response)


@router.post(
    "/harness/reset",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_reset",
)
def post_control_center_communications_harness_reset(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.reset, payload, response)


def register_communications_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
