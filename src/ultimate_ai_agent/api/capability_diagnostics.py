from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ultimate_ai_agent.api.cors import apply_loopback_cors_response_headers
from ultimate_ai_agent.api.request_validation import safe_validation_error_response
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.capabilities import (
    ToolAwareDiagnosticRequest,
    ToolAwareOperatorDiagnostic,
    build_tool_aware_operator_diagnostic,
)
from ultimate_ai_agent.core.capabilities.diagnostics import (
    TAW06_CONTRACT_REF,
    TAW06_MAX_REQUEST_BYTES,
    TAW06_MAX_REQUEST_NESTING_DEPTH,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope


router = APIRouter(
    prefix="/api/capability-diagnostics",
    tags=["capability-diagnostics"],
)
_REGISTERED_ATTR = "_uaa_capability_diagnostic_routes_registered"
_ROUTE = "/api/capability-diagnostics/preview"


class CapabilityDiagnosticBodyTooLargeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    detail: Literal[
        "TAW-06 diagnostic request body exceeds the permitted bound."
    ]
    code: Literal["TAW06_REQUEST_BODY_TOO_LARGE"]
    contract_ref: Literal["contract-ref:taw06:operator-diagnostics:v1"]
    maximum_body_bytes: Literal[262144]


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
            if depth > TAW06_MAX_REQUEST_NESTING_DEPTH:
                return True
        elif value in (ord("]"), ord("}")) and depth > 0:
            depth -= 1
    return False


class CapabilityDiagnosticBodyLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        maximum_body_bytes: int = TAW06_MAX_REQUEST_BYTES,
    ) -> None:
        self.app = app
        self.maximum_body_bytes = maximum_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method", "").upper() != "POST"
            or scope.get("path") != _ROUTE
        ):
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
                await self._reject(scope, receive, send)
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
                await self._reject(scope, receive, send)
                return
            buffered_body.extend(chunk)
            if not message.get("more_body", False):
                break

        body = bytes(buffered_body)
        if _json_nesting_exceeds_limit(body):
            await self._reject_nesting(scope, receive, send)
            return

        replayed = False

        async def replay_receive() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                if disconnected:
                    return {"type": "http.disconnect"}
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "detail": "TAW-06 diagnostic request body exceeds the permitted bound.",
                "code": "TAW06_REQUEST_BODY_TOO_LARGE",
                "contract_ref": TAW06_CONTRACT_REF,
                "maximum_body_bytes": self.maximum_body_bytes,
            },
        )
        apply_loopback_cors_response_headers(response, _request_origin(scope))
        await response(scope, receive, send)

    async def _reject_nesting(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        response = safe_validation_error_response(
            path=_ROUTE,
            errors=[
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": (
                        "TAW-06 diagnostic request exceeds the permitted "
                        "JSON nesting bound."
                    ),
                }
            ],
        )
        apply_loopback_cors_response_headers(response, _request_origin(scope))
        await response(scope, receive, send)


@router.post(
    "/preview",
    response_model=ToolAwareOperatorDiagnostic,
    operation_id="preview_tool_aware_capability_diagnostics",
    summary="Preview redacted tool-aware route and familiarity diagnostics",
    responses={
        422: {
            "model": ResultEnvelope,
            "description": "Diagnostic request validation failed safely.",
        },
        413: {
            "model": CapabilityDiagnosticBodyTooLargeResponse,
            "description": "Diagnostic request body exceeds the bounded input size.",
        }
    },
)
def preview_tool_aware_capability_diagnostics(
    request: ToolAwareDiagnosticRequest,
) -> ToolAwareOperatorDiagnostic:
    return build_tool_aware_operator_diagnostic(request)


def register_capability_diagnostic_routes(app: FastAPI) -> None:
    if not getattr(app.state, _REGISTERED_ATTR, False):
        app.add_middleware(CapabilityDiagnosticBodyLimitMiddleware)
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)


__all__ = [
    "CapabilityDiagnosticBodyTooLargeResponse",
    "register_capability_diagnostic_routes",
    "router",
]
