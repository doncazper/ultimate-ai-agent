"""Authenticated synthetic Finance routes; exact Core authority owns mutations."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ultimate_ai_agent.api.contracts import ApiRouteClassification
from ultimate_ai_agent.api.cors import apply_loopback_cors_response_headers
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
    idempotency_header_failure,
)
from ultimate_ai_agent.core.finance.workspace import (
    FINANCE_WORKSPACE_CONTRACT_REF,
    FINANCE_WORKSPACE_MAX_BODY_BYTES,
    FINANCE_WORKSPACE_MAX_DEPTH,
    FinanceWorkspace,
    FinanceWorkspaceCommitResult,
    FinanceWorkspaceIntent,
    FinanceWorkspacePreparation,
    FinanceWorkspaceView,
    finance_workspace_body_within_limits,
    finance_workspace_error_code,
)


FINANCE_WORKSPACE_PATH = "/control-center/finance/workspace"
FINANCE_WORKSPACE_POST_PATHS = frozenset(
    f"{FINANCE_WORKSPACE_PATH}/{action}" for action in ("preview", "refresh", "commit")
)


class FinanceWorkspaceBodyLimitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: Literal["FINANCE_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED"] = (
        "FINANCE_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED"
    )
    detail: Literal["The Finance request exceeds the permitted local input bound."] = (
        "The Finance request exceeds the permitted local input bound."
    )
    contract_ref: Literal["contract-ref:finance/FIN-003:synthetic-in-app:v1"] = (
        FINANCE_WORKSPACE_CONTRACT_REF
    )
    maximum_body_bytes: Literal[131072] = FINANCE_WORKSPACE_MAX_BODY_BYTES
    maximum_json_nesting_depth: Literal[32] = FINANCE_WORKSPACE_MAX_DEPTH


def get_finance_workspace() -> FinanceWorkspace:
    return FinanceWorkspace.from_env()


def _idempotency_binding(request: Request, expected: str) -> None:
    failure = idempotency_header_failure(
        request.headers,
        route_classification=ApiRouteClassification.mutating_requires_authority,
    )
    if failure is not None:
        raise HTTPException(
            status_code=failure.status_code,
            detail={"code": failure.code, "message": failure.safe_message},
        )
    actual = request.headers.get(IDEMPOTENCY_KEY_HEADER) or request.headers.get(
        IDEMPOTENCY_REF_HEADER
    )
    if actual != expected:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "FINANCE_WORKSPACE_IDEMPOTENCY_MISMATCH",
                "message": "The request must retain the exact reviewed idempotency binding.",
            },
        )


def _raise_workspace_error(exc: Exception, *, commit_attempted: bool = False) -> None:
    code = finance_workspace_error_code(exc)
    status = (
        503
        if code
        in {"FINANCE_WORKSPACE_REQUEST_FAILED", "FINANCE_WORKSPACE_HELPER_UNAVAILABLE"}
        else 409
    )
    raise HTTPException(
        status_code=status,
        detail={
            "code": code,
            "message": "Finance could not confirm this save. Inspect current history or retry the same reviewed action."
            if commit_attempted
            else "Finance could not prepare this request. Reload the workspace and check its current setup and revision.",
            "commit_outcome": "unconfirmed" if commit_attempted else "not_attempted",
        },
    ) from None


router = APIRouter(prefix=FINANCE_WORKSPACE_PATH, tags=["control-center"])
_BODY_LIMIT_RESPONSES = {
    413: {
        "model": FinanceWorkspaceBodyLimitResponse,
        "description": "Finance raw byte or JSON nesting bound exceeded before decoding.",
    }
}


def _workspace_request_headers(
    x_uaa_expected_backend_revision_ref: str = Header(
        alias="X-UAA-Expected-Backend-Revision-Ref"
    ),
    x_uaa_expected_backend_instance_ref: str = Header(
        alias="X-UAA-Expected-Backend-Instance-Ref"
    ),
    x_uaa_expected_backend_truth_ref: str = Header(
        alias="X-UAA-Expected-Backend-Truth-Ref"
    ),
    x_uaa_control_center_mutation_binding: Literal["backend-truth.v1"] = Header(
        alias="X-UAA-Control-Center-Mutation-Binding"
    ),
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
        description="Either idempotency alias is required and must equal the exact request binding.",
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
        description="Alias of the idempotency key; supplied aliases must agree.",
    ),
) -> None:
    """Publish headers enforced by middleware and the exact-body binding gate."""


@router.get(
    "",
    response_model=FinanceWorkspaceView,
    operation_id="get_control_center_finance_workspace",
    summary="Inspect the protected synthetic Finance workspace",
)
def get_workspace(
    item_offset: int = Query(default=0, ge=0, le=10_000),
    history_offset: int = Query(default=0, ge=0, le=4096),
    limit: int = Query(default=50, ge=1, le=100),
    workspace: FinanceWorkspace = Depends(get_finance_workspace),
) -> FinanceWorkspaceView:
    return workspace.read_view(
        item_offset=item_offset, history_offset=history_offset, limit=limit
    )


@router.post(
    "/preview",
    response_model=FinanceWorkspacePreparation,
    operation_id="preview_control_center_finance_workspace_mutation",
    dependencies=[Depends(_workspace_request_headers)],
    summary="Preview one exact synthetic Finance change",
    responses=_BODY_LIMIT_RESPONSES,
)
def preview_workspace(
    intent: FinanceWorkspaceIntent,
    request: Request,
    workspace: FinanceWorkspace = Depends(get_finance_workspace),
) -> FinanceWorkspacePreparation:
    _idempotency_binding(request, intent.idempotency_ref)
    try:
        return workspace.prepare(intent)
    except (OSError, RuntimeError, ValueError) as exc:
        _raise_workspace_error(exc)


@router.post(
    "/refresh",
    response_model=FinanceWorkspacePreparation,
    operation_id="refresh_control_center_finance_workspace_preparation",
    dependencies=[Depends(_workspace_request_headers)],
    summary="Re-present the same synthetic review intent without saving",
    responses=_BODY_LIMIT_RESPONSES,
)
def refresh_workspace(
    preparation: FinanceWorkspacePreparation,
    request: Request,
    workspace: FinanceWorkspace = Depends(get_finance_workspace),
) -> FinanceWorkspacePreparation:
    _idempotency_binding(request, preparation.bundle.request.idempotency_ref)
    try:
        return workspace.refresh_preparation(preparation)
    except (OSError, RuntimeError, ValueError) as exc:
        _raise_workspace_error(exc)


@router.post(
    "/commit",
    response_model=FinanceWorkspaceCommitResult,
    operation_id="commit_control_center_finance_workspace_mutation",
    dependencies=[Depends(_workspace_request_headers)],
    summary="Confirm and save one exact synthetic Finance change",
    responses=_BODY_LIMIT_RESPONSES,
)
def commit_workspace(
    preparation: FinanceWorkspacePreparation,
    request: Request,
    x_uaa_operator_confirmed: str | None = Header(
        default=None, alias="X-UAA-Operator-Confirmed"
    ),
    workspace: FinanceWorkspace = Depends(get_finance_workspace),
) -> FinanceWorkspaceCommitResult:
    _idempotency_binding(request, preparation.bundle.request.idempotency_ref)
    if x_uaa_operator_confirmed != "true":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FINANCE_OPERATOR_CONFIRMATION_REQUIRED",
                "message": "Review and explicitly confirm this exact change before saving.",
                "commit_outcome": "not_attempted",
            },
        )
    try:
        result = workspace.commit(preparation, confirmed=True)
        return FinanceWorkspaceCommitResult.model_validate(result)
    except (OSError, RuntimeError, ValueError) as exc:
        _raise_workspace_error(exc, commit_attempted=True)


class FinanceWorkspaceBodyLimitMiddleware:
    """Bound raw request bytes and structure before FastAPI JSON decoding."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in FINANCE_WORKSPACE_POST_PATHS
        ):
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > FINANCE_WORKSPACE_MAX_BODY_BYTES:
                await self._reject(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        if not finance_workspace_body_within_limits(body):
            await self._reject(scope, receive, send)
            return
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content=FinanceWorkspaceBodyLimitResponse().model_dump(),
            headers={"Cache-Control": "no-store"},
        )
        origin = next(
            (
                value.decode("latin-1")
                for name, value in scope.get("headers", ())
                if name.lower() == b"origin"
            ),
            None,
        )
        apply_loopback_cors_response_headers(response, origin)
        await response(scope, receive, send)


def register_finance_workspace_routes(app: FastAPI) -> None:
    app.include_router(router)
    app.add_middleware(FinanceWorkspaceBodyLimitMiddleware)
