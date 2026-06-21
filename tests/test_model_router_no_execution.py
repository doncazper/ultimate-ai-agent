import ast
from pathlib import Path

from tests.m7_helpers import actor, classification, cloud_profile, route_request
from ultimate_ai_agent.core.hygiene.temporal_context import FreshnessClass, StalenessPolicy, TemporalContext
from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter


def test_model_router_is_decision_only_and_serializes_safely() -> None:
    decision = ModelRouter().route(route_request(profiles=[cloud_profile()]))
    payload = decision.model_dump(mode="json")

    assert decision.status == ModelRouteStatus.selected
    assert payload["selected_model_id"] == "cloud_reasoner_model"
    assert "raw_secret" not in str(payload)


def test_model_router_source_has_no_provider_or_network_imports() -> None:
    forbidden_modules = {
        "openai",
        "anthropic",
        "google.generativeai",
        "ollama",
        "requests",
        "httpx",
        "urllib.request",
        "subprocess",
        "socket",
    }

    for path in (Path("src") / "ultimate_ai_agent" / "core" / "model_router").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in forbidden_modules


def test_route_decision_can_be_referenced_by_event_ledger_metadata() -> None:
    decision = ModelRouter().route(route_request(profiles=[cloud_profile()]))

    event = EventLedgerEvent(
        event_id="evt_model_route_selected",
        event_type="model_router",
        event_name=EventName.model_route_selected,
        run_id=decision.run_id,
        trace_id="trace_m7",
        span_id="span_m7",
        correlation_id="corr_m7",
        actor_context=actor(),
        temporal_context=TemporalContext(
            freshness_class=FreshnessClass.static,
            staleness_policy=StalenessPolicy.allow_with_label,
        ),
        data_classification=classification(),
        event_source="ModelRouter",
        subject=decision.selected_profile_id or "none",
        action="route_preview",
        outcome=decision.status,
        status="success",
        severity="info",
        model_routing_ref=decision.decision_id,
        metadata=decision.model_dump(mode="json"),
    )

    assert event.model_routing_ref == decision.decision_id
    assert event.metadata["status"] == "selected"


def test_cloud_route_does_not_imply_consent_or_credential_resolution() -> None:
    decision = ModelRouter().route(route_request(profiles=[cloud_profile(credential_ref="cred_cloud")], credential_availability={"cred_cloud": True}))

    assert decision.status == ModelRouteStatus.selected
    assert decision.consent_refs == []
    assert "cred_cloud" not in decision.model_dump_json()
