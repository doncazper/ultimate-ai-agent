from __future__ import annotations

from fastapi import FastAPI
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
    "Content-Type",
    "X-Requested-With",
)
CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS: tuple[str, ...] = (
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
