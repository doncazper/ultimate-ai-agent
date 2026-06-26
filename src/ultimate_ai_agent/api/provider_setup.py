from __future__ import annotations

from fastapi import APIRouter, FastAPI

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.providers import build_provider_setup_guide_catalog


router = APIRouter(prefix="/control-center/providers", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_provider_setup_routes_registered"


@router.get("/setup-guide", response_model=ResultEnvelope)
def get_control_center_providers_setup_guide() -> ResultEnvelope:
    catalog = build_provider_setup_guide_catalog()
    return ResultEnvelope(
        success=True,
        operation="control_center_providers_setup_guide",
        service="ControlCenterProviderSetupAPI",
        trace_id=catalog.catalog_ref,
        data=catalog.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:provider-catalog:cost-literacy"}],
        redactions_applied=catalog.redactions_applied,
    )


def register_provider_setup_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)

