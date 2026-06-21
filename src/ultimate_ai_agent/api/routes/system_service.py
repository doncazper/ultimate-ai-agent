from __future__ import annotations
from typing import Any

from fastapi import APIRouter, FastAPI, Response

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.runtime_readiness import RuntimeHealthStatus, build_runtime_health_status


router = APIRouter(tags=["system"])
_REGISTERED_ATTR = "_uaa_system_service_routes_registered"


@router.get("/health", response_model=RuntimeHealthStatus)
def get_health() -> Any:
    return build_runtime_health_status()


@router.get("/version")
def get_version() -> Response:
    return {"version": __version__}


def register_system_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
