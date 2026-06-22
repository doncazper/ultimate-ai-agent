from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware


LOOPBACK_CORS_POLICY_REF = "cors:p1-082:loopback:v1"

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
    "X-Requested-With",
)
CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS: tuple[str, ...] = (
    "Retry-After",
    "X-UAA-Rate-Limit-Policy",
    "X-UAA-Security-Headers-Policy",
)


def configure_loopback_cors(app: FastAPI) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(CONTROL_CENTER_LOOPBACK_CORS_ORIGINS),
        allow_methods=list(CONTROL_CENTER_LOOPBACK_CORS_METHODS),
        allow_headers=list(CONTROL_CENTER_LOOPBACK_CORS_HEADERS),
        expose_headers=list(CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS),
        allow_credentials=False,
        max_age=600,
    )
    return app


def apply_loopback_cors_response_headers(response: Response, origin: str | None) -> Response:
    if origin not in CONTROL_CENTER_LOOPBACK_CORS_ORIGINS:
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Expose-Headers"] = ", ".join(
        CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS
    )
    response.headers.add_vary_header("Origin")
    return response
