from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ultimate_ai_agent.api.cors import apply_loopback_cors_response_headers
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
    idempotency_value_valid,
)
from ultimate_ai_agent.api.request_validation import safe_validation_error_response
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.chat.workspace import (
    CHAT_WORKSPACE_CONTRACT_REF,
    CHAT_WORKSPACE_MAX_REQUEST_BYTES,
    CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH,
    ChatDraftCheckpointRequest,
    ChatThreadLifecycleRequest,
    ChatWorkspaceApprovalCaptureRequest,
)
from ultimate_ai_agent.core.chat.workspace_service import (
    ChatWorkspaceApprovalError,
    ChatWorkspaceControlCenterService,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.storage import (
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


router = APIRouter(prefix="/control-center/chat", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_chat_workspace_routes_registered"
CHAT_WORKSPACE_MUTATION_ROUTE_RE = re.compile(
    r"^/control-center/chat/threads/[^/]+/(?:approval|draft-checkpoint|lifecycle)$"
)
CHAT_WORKSPACE_READ_ROUTE = "/control-center/chat/workspace"
CHAT_WORKSPACE_APPROVAL_HEADER = "x-uaa-approval-ref"


class ChatWorkspaceBodyTooLargeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    detail: Literal[
        "The content-free Chat workspace request exceeds the permitted local bound."
    ]
    code: Literal["CHAT_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED"]
    contract_ref: Literal["contract-ref:chat-content-free-workspace:v1"]
    maximum_body_bytes: Literal[8192]
    maximum_json_nesting_depth: Literal[16]


def get_chat_workspace_service() -> ChatWorkspaceControlCenterService:
    return ChatWorkspaceControlCenterService.from_env(
        approval_authority=LocalApprovalAuthority()
    )


def _request_origin(scope: Scope) -> str | None:
    for name, value in scope.get("headers", ()):
        if name.lower() == b"origin":
            try:
                return value.decode("ascii")
            except UnicodeDecodeError:
                return None
    return None


def _json_nesting_exceeds_limit(body: bytes) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for value in body:
        if in_string:
            if escaped:
                escaped = False
            elif value == ord("\\"):
                escaped = True
            elif value == ord('"'):
                in_string = False
            continue
        if value == ord('"'):
            in_string = True
        elif value in (ord("["), ord("{")):
            depth += 1
            if depth > CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH:
                return True
        elif value in (ord("]"), ord("}")) and depth > 0:
            depth -= 1
    return False


def _no_store_send(send: Send) -> Send:
    async def no_store_send(message: Message) -> None:
        if message["type"] == "http.response.start":
            headers = [
                (name, value)
                for name, value in message.get("headers", [])
                if name.lower() != b"cache-control"
            ]
            headers.append((b"cache-control", b"no-store"))
            message = {**message, "headers": headers}
        await send(message)

    return no_store_send


class ChatWorkspacePrivateBoundaryMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        maximum_body_bytes: int = CHAT_WORKSPACE_MAX_REQUEST_BYTES,
    ) -> None:
        self.app = app
        self.maximum_body_bytes = maximum_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        is_read = scope["type"] == "http" and path == CHAT_WORKSPACE_READ_ROUTE
        is_mutation = (
            scope["type"] == "http"
            and scope.get("method", "").upper() == "POST"
            and CHAT_WORKSPACE_MUTATION_ROUTE_RE.fullmatch(path) is not None
        )
        if not is_read and not is_mutation:
            await self.app(scope, receive, send)
            return

        send = _no_store_send(send)
        if is_read:
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", ()):
            if name.lower() != b"content-length":
                continue
            try:
                content_length = int(value)
            except ValueError:
                break
            if content_length > self.maximum_body_bytes:
                await self._reject_size(scope, receive, send)
                return

        buffered_body = bytearray()
        disconnected = False
        received_bytes = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                disconnected = True
                break
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            received_bytes += len(chunk)
            if received_bytes > self.maximum_body_bytes:
                await self._reject_size(scope, receive, send)
                return
            buffered_body.extend(chunk)
            if not message.get("more_body", False):
                break

        body = bytes(buffered_body)
        if _json_nesting_exceeds_limit(body):
            response = safe_validation_error_response(
                path=path,
                errors=[
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": (
                            "The content-free Chat workspace request exceeds "
                            "the permitted JSON nesting bound."
                        ),
                    }
                ],
            )
            apply_loopback_cors_response_headers(response, _request_origin(scope))
            await response(scope, receive, send)
            return

        replayed = False

        async def replay_receive() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                if disconnected:
                    return {"type": "http.disconnect"}
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    async def _reject_size(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "detail": (
                    "The content-free Chat workspace request exceeds the "
                    "permitted local bound."
                ),
                "code": "CHAT_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED",
                "contract_ref": CHAT_WORKSPACE_CONTRACT_REF,
                "maximum_body_bytes": self.maximum_body_bytes,
                "maximum_json_nesting_depth": (
                    CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH
                ),
            },
        )
        apply_loopback_cors_response_headers(response, _request_origin(scope))
        await response(scope, receive, send)


@router.get("/workspace", response_model=ResultEnvelope)
def get_control_center_chat_workspace() -> ResultEnvelope:
    data = get_chat_workspace_service().workspace()
    return ResultEnvelope(
        success=True,
        operation="control_center_chat_workspace",
        service="ChatWorkspaceControlCenterAPI",
        trace_id="chat-workspace:read-model",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:chat-workspace:read-model"}],
        redactions_applied=[
            "draft_metadata_only",
            "draft_body_omitted",
            "safe_refs_only",
        ],
    )


@router.post(
    "/threads/{thread_ref}/approval",
    response_model=ResultEnvelope,
    responses={
        413: {
            "model": ChatWorkspaceBodyTooLargeResponse,
            "description": "Chat workspace request exceeds the bounded input size.",
        }
    },
)
def post_control_center_chat_workspace_approval(
    thread_ref: str,
    request: ChatWorkspaceApprovalCaptureRequest,
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
        data = get_chat_workspace_service().capture_approval(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc),
                "safe_message": (
                    "The Chat workspace approval idempotency key already exists "
                    "for another exact request."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_ERROR"
        status_code = 503 if "CAPACITY" in code else 409
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The exact Chat workspace approval was not captured.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_CHAT_WORKSPACE_APPROVAL_UNSAFE_INPUT",
                "safe_message": "The Chat workspace approval contains unsafe refs.",
            },
        ) from exc
    return ResultEnvelope(
        success=True,
        operation="control_center_chat_workspace_approval",
        service="ChatWorkspaceControlCenterAPI",
        trace_id=str(data["approval_validation_ref"]),
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:chat-workspace:approval"}],
        redactions_applied=[
            "draft_metadata_only",
            "draft_body_not_received",
            "exact_approval_refs_only",
            "safe_refs_only",
        ],
    )


@router.post(
    "/threads/{thread_ref}/draft-checkpoint",
    response_model=ResultEnvelope,
    responses={
        413: {
            "model": ChatWorkspaceBodyTooLargeResponse,
            "description": "Chat workspace request exceeds the bounded input size.",
        }
    },
)
def post_control_center_chat_draft_checkpoint(
    thread_ref: str,
    request: ChatDraftCheckpointRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
    x_uaa_approval_ref: str | None = Header(
        default=None,
        alias=CHAT_WORKSPACE_APPROVAL_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    approval_ref = _required_approval_ref(x_uaa_approval_ref)
    try:
        data = get_chat_workspace_service().record_draft_checkpoint(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            approval_ref=approval_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_CHAT_WORKSPACE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Chat workspace idempotency key already exists with different "
                    "content-free draft metadata."
                ),
            },
        ) from exc
    except ChatWorkspaceApprovalError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": str(exc),
                "safe_message": (
                    "The exact local Chat metadata approval did not validate."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_CHAT_DRAFT_CHECKPOINT_ERROR"
        status_code = (
            503
            if "EVIDENCE" in code
            else 409
            if code
            in {
                "FOUNDER_LOOP_CHAT_THREAD_ARCHIVED",
                "FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT",
                "FOUNDER_LOOP_CHAT_THREAD_REVISION_EXHAUSTED",
                "FOUNDER_LOOP_CHAT_WORKSPACE_CAPACITY_REACHED",
                "FOUNDER_LOOP_CHAT_WORKSPACE_MUTATION_CAPACITY_REACHED",
                "FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT",
            }
            else 400
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": (
                    "The Chat draft checkpoint could not be recorded safely."
                ),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_CHAT_DRAFT_CHECKPOINT_UNSAFE_INPUT",
                "safe_message": "The Chat draft metadata contains unsafe refs.",
            },
        ) from exc
    return _mutation_envelope("draft_checkpoint", data)


@router.post(
    "/threads/{thread_ref}/lifecycle",
    response_model=ResultEnvelope,
    responses={
        413: {
            "model": ChatWorkspaceBodyTooLargeResponse,
            "description": "Chat workspace request exceeds the bounded input size.",
        }
    },
)
def post_control_center_chat_thread_lifecycle(
    thread_ref: str,
    request: ChatThreadLifecycleRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_KEY_HEADER,
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias=IDEMPOTENCY_REF_HEADER,
    ),
    x_uaa_approval_ref: str | None = Header(
        default=None,
        alias=CHAT_WORKSPACE_APPROVAL_HEADER,
    ),
) -> ResultEnvelope:
    idempotency_key_ref = _idempotency_key_ref(
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )
    approval_ref = _required_approval_ref(x_uaa_approval_ref)
    try:
        data = get_chat_workspace_service().record_lifecycle(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            approval_ref=approval_ref,
        )
    except FounderLoopStorageDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": str(exc) or "FOUNDER_LOOP_CHAT_WORKSPACE_IDEMPOTENCY_CONFLICT",
                "safe_message": (
                    "The Chat workspace idempotency key already exists with a "
                    "different lifecycle request."
                ),
            },
        ) from exc
    except ChatWorkspaceApprovalError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "code": str(exc),
                "safe_message": (
                    "The exact local Chat metadata approval did not validate."
                ),
            },
        ) from exc
    except FounderLoopStorageError as exc:
        code = str(exc) or "FOUNDER_LOOP_CHAT_THREAD_LIFECYCLE_ERROR"
        if code == "FOUNDER_LOOP_CHAT_THREAD_NOT_FOUND":
            status_code = 404
        elif "EVIDENCE" in code:
            status_code = 503
        elif code in {
            "FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT",
            "FOUNDER_LOOP_CHAT_THREAD_REVISION_EXHAUSTED",
            "FOUNDER_LOOP_CHAT_WORKSPACE_MUTATION_CAPACITY_REACHED",
            "FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT",
        }:
            status_code = 409
        else:
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": code,
                "safe_message": "The Chat thread lifecycle could not be updated safely.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FOUNDER_LOOP_CHAT_THREAD_LIFECYCLE_UNSAFE_INPUT",
                "safe_message": "The Chat lifecycle request contains unsafe refs.",
            },
        ) from exc
    return _mutation_envelope("lifecycle", data)


def _mutation_envelope(kind: str, data: dict[str, object]) -> ResultEnvelope:
    return ResultEnvelope(
        success=True,
        operation=f"control_center_chat_{kind}",
        service="ChatWorkspaceControlCenterAPI",
        trace_id=f"chat-workspace:{kind}",
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:chat-workspace:mutation"}],
        redactions_applied=[
            "draft_metadata_only",
            "draft_body_not_received",
            "approval_refs_only",
            "safe_refs_only",
        ],
    )


def _idempotency_key_ref(
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> str:
    supplied = [
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None
    ]
    if not supplied:
        raise HTTPException(
            status_code=428,
            detail={
                "code": "API_IDEMPOTENCY_REQUIRED",
                "safe_message": (
                    "Mutating Control Center routes require an idempotency key."
                ),
            },
        )
    if any(not idempotency_value_valid(value) for value in supplied):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "API_IDEMPOTENCY_INVALID",
                "safe_message": "The supplied idempotency value is invalid.",
            },
        )
    if len(set(supplied)) > 1:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "API_IDEMPOTENCY_CONFLICT",
                "safe_message": "The supplied idempotency values do not match.",
            },
        )
    return supplied[0]


def _required_approval_ref(approval_ref: str | None) -> str:
    if approval_ref is None or not approval_ref.strip():
        raise HTTPException(
            status_code=428,
            detail={
                "code": "CHAT_WORKSPACE_APPROVAL_REQUIRED",
                "safe_message": (
                    "Capture one exact Chat workspace approval before mutation."
                ),
            },
        )
    return approval_ref.strip()


def register_chat_workspace_routes(app: FastAPI) -> None:
    if not getattr(app.state, _REGISTERED_ATTR, False):
        app.add_middleware(ChatWorkspacePrivateBoundaryMiddleware)
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
