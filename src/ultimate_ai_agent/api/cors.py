from __future__ import annotations

import os
import re
from collections.abc import Mapping

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware


LOOPBACK_CORS_POLICY_REF = "cors:p1-082:loopback:v1"
CONTROL_CENTER_CORS_ORIGIN_ENV = "UAA_CONTROL_CENTER_CORS_ORIGIN"
_EXACT_LOOPBACK_ORIGIN_RE = re.compile(
    r"^http" r"://(?:localhost|127\.0\.0\.1|\[::1\]):([1-9][0-9]{0,4})$"
)

CONTROL_CENTER_LOOPBACK_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://[::1]:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://[::1]:4173",
)

CONTROL_CENTER_LOOPBACK_CORS_METHODS: tuple[str, ...] = ("GET", "POST")
CONTROL_CENTER_LOOPBACK_CORS_HEADERS: tuple[str, ...] = (
    "Authorization",
    "Content-Type",
    "X-UAA-Idempotency-Key",
    "X-UAA-Idempotency-Ref",
    "X-UAA-Control-Center-Mutation-Binding",
    "X-UAA-Expected-Backend-Revision-Ref",
    "X-UAA-Expected-Backend-Instance-Ref",
    "X-UAA-Expected-Backend-Truth-Ref",
    "X-Requested-With",
)
CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS: tuple[str, ...] = (
    "Retry-After",
    "X-UAA-Backend-Instance-Ref",
    "X-UAA-Backend-Revision-Ref",
    "X-UAA-Rate-Limit-Policy",
    "X-UAA-Security-Headers-Policy",
)


def control_center_loopback_cors_origins(
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    configured = (env or os.environ).get(
        CONTROL_CENTER_CORS_ORIGIN_ENV,
        "",
    ).strip()
    match = _EXACT_LOOPBACK_ORIGIN_RE.fullmatch(configured)
    if match is None or int(match.group(1)) > 65535:
        return CONTROL_CENTER_LOOPBACK_CORS_ORIGINS
    return tuple(
        dict.fromkeys([*CONTROL_CENTER_LOOPBACK_CORS_ORIGINS, configured])
    )


def configure_loopback_cors(app: FastAPI) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(control_center_loopback_cors_origins()),
        allow_methods=list(CONTROL_CENTER_LOOPBACK_CORS_METHODS),
        allow_headers=list(CONTROL_CENTER_LOOPBACK_CORS_HEADERS),
        expose_headers=list(CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS),
        allow_credentials=False,
        max_age=600,
    )
    return app


def apply_loopback_cors_response_headers(response: Response, origin: str | None) -> Response:
    if origin not in control_center_loopback_cors_origins():
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Expose-Headers"] = ", ".join(
        CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS
    )
    response.headers.add_vary_header("Origin")
    return response
