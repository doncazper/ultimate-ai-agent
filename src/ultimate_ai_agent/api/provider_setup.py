from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi import Header

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.providers import (
    TinyProviderInvocationRequest,
    build_provider_setup_guide_catalog,
    evaluate_tiny_provider_invocation,
)


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


@router.post("/exact-approved-lanes/tiny", response_model=ResultEnvelope)
def post_control_center_providers_exact_approved_lane_tiny(
    request: TinyProviderInvocationRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias="X-UAA-Idempotency-Key",
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias="X-UAA-Idempotency-Ref",
    ),
) -> ResultEnvelope:
    header_idempotency_ref = x_uaa_idempotency_key or x_uaa_idempotency_ref
    if header_idempotency_ref and header_idempotency_ref != request.idempotency_ref:
        return ResultEnvelope(
            success=False,
            operation="control_center_providers_exact_approved_lane_tiny",
            service="ControlCenterProviderSetupAPI",
            trace_id=request.invocation_ref,
            data={
                "allowed": False,
                "status": "approval_invalid",
                "reason_codes": ["IDEMPOTENCY_REF_MISMATCH"],
                "required_next_action": "submit_matching_exact_idempotency_ref",
            },
            redactions_applied=["provider_invocation_refs_only"],
        )
    decision = evaluate_tiny_provider_invocation(request)
    evidence = [
        {"evidence_ref": request.cost_estimate_ref},
        {"evidence_ref": request.budget_decision_ref},
    ]
    if decision.receipt is not None:
        evidence.insert(0, {"evidence_ref": decision.receipt.receipt_ref})
    return ResultEnvelope(
        success=decision.allowed,
        operation="control_center_providers_exact_approved_lane_tiny",
        service="ControlCenterProviderSetupAPI",
        run_id=request.run_id,
        trace_id=request.invocation_ref,
        data=decision.model_dump(mode="json"),
        evidence=evidence,
        cost_attribution={
            "provider_ref": request.provider_ref,
            "model_ref": request.model_ref,
            "cost_estimate_ref": request.cost_estimate_ref,
            "budget_decision_ref": request.budget_decision_ref,
            "max_approved_usd_ref": request.max_approved_usd_ref,
            "cost_receipt_ref": request.cost_receipt_ref,
            "unknown_paid_cost_blocks": True,
        },
        redactions_applied=[
            "redacted_input_summary_ref_only",
            "redacted_output_summary_ref_only",
            "provider_exchange_content_omitted",
        ],
        rollback_ref=request.safe_disable_ref,
    )


def register_provider_setup_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
