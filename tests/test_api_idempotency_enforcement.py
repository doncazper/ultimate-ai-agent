from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.idempotency import api_idempotency_audit_policy_payload
from ultimate_ai_agent.api.manifest import build_api_manifest


def test_global_header_gate_is_not_reported_as_durable_deduplication() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    mutating_routes = [
        route
        for route in manifest["routes"]
        if route["route_classification"] == "mutating_requires_authority"
    ]

    assert mutating_routes
    assert all(
        route["idempotency_enforcement"] == "header_shape_gate_only"
        for route in mutating_routes
    )
    assert all(
        route["durable_idempotency_owner_ref"] is None for route in mutating_routes
    )


def test_exact_web_evidence_lane_reports_its_route_owned_receipt_store() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    route = next(
        route
        for route in manifest["routes"]
        if route["path"] == "/control-center/web-evidence/attach"
    )

    assert route["idempotency_enforcement"] == "route_owned_durable_replay"
    assert route["durable_idempotency_owner_ref"] == (
        "idempotency-owner:control-center-web-evidence-receipt-store:v1"
    )


def test_idempotency_policy_keeps_durable_authority_fail_closed() -> None:
    policy = api_idempotency_audit_policy_payload(mutating_route_count=1)

    assert policy["global_middleware_enforcement"] == "header_shape_gate_only"
    assert policy["durable_dedupe_store_added"] is False
    assert policy["route_owned_durable_replay_required_for_authority"] is True
    assert policy["mutation_authority_granted"] is False
