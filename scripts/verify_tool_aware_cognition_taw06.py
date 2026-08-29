from __future__ import annotations

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.capabilities import (
    AwarenessEvidenceStatus,
    ChatShadowEvidence,
    DiagnosticOperatorStatus,
    build_tool_aware_operator_diagnostic,
    evaluate_chat_shadow,
)


TAW06_ROUTE = "/api/capability-diagnostics/preview"


def verify() -> None:
    decision = evaluate_chat_shadow(
        ChatShadowEvidence(awareness_status=AwarenessEvidenceStatus.over_budget)
    )
    diagnostic = build_tool_aware_operator_diagnostic(decision)
    if (
        diagnostic.operator_status != DiagnosticOperatorStatus.evidence_unavailable
        or not diagnostic.safe_disable_engaged
        or diagnostic.source_inspection.operator_visible_route_ref
        != diagnostic.source_inspection.legacy_route_ref
        or not diagnostic.routine_machinery_hidden_from_ordinary_chat
        or not diagnostic.relevant_limitations_disclosed
    ):
        raise RuntimeError("TAW-06 verifier detected diagnostic posture drift")
    if (
        any(
            (
                diagnostic.operator_visible_route_changed,
                diagnostic.model_context_changed,
                diagnostic.raw_operator_content_included,
                diagnostic.raw_model_content_included,
                diagnostic.raw_provider_payload_included,
                diagnostic.raw_local_paths_included,
                diagnostic.provider_call_performed,
                diagnostic.proposal_constructed,
                diagnostic.approval_granted,
                diagnostic.execution_performed,
                diagnostic.connector_call_performed,
                diagnostic.external_write_performed,
                diagnostic.authority_granted,
                diagnostic.production_authority_granted,
                diagnostic.control_center_surface_added,
            )
        )
        or diagnostic.model_call_count != 0
        or diagnostic.second_ordinary_chat_model_call_count != 0
    ):
        raise RuntimeError("TAW-06 verifier detected authority expansion")
    manifest = build_api_manifest(app)
    route = next(
        (
            item
            for item in manifest.routes
            if item.path == TAW06_ROUTE and item.method == "POST"
        ),
        None,
    )
    if (
        route is None
        or route.operation_id != "preview_tool_aware_capability_diagnostics"
        or route.side_effect_class != "validation_only"
        or route.route_classification != "local_sensitive"
        or not route.protected_route
        or route.idempotency_required
        or app.openapi()["paths"][TAW06_ROUTE]["post"]["operationId"]
        != route.operation_id
    ):
        raise RuntimeError("TAW-06 verifier detected API contract drift")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-06 operator diagnostics verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
