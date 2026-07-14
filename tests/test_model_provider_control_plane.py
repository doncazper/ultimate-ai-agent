from __future__ import annotations

import json
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.providers.control_plane import (
    DelegatedRuntimeModelCatalogPosture,
    MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF,
    ModelSlotPostureReadModel,
    build_model_provider_control_plane_read_model,
)


LOCAL_TEST_BEARER = "model-provider-control-plane-local-bearer"


def test_model_provider_control_plane_unifies_governed_runtime_posture() -> None:
    read_model = build_model_provider_control_plane_read_model()
    payload = read_model.model_dump(mode="json")

    assert read_model.schema_version == "model_provider_control_plane.v1"
    assert read_model.route_ref == MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    assert read_model.backend_owned is True
    assert read_model.read_only is True
    assert read_model.safe_refs_only is True
    assert read_model.status == "governed_control_plane_wired"
    assert read_model.authority.exact_tiny_provider_lane_available is True
    assert read_model.authority.exact_credential_validation_lane_available is True
    assert read_model.authority.local_llama_cpp_gateway_available is True
    assert read_model.authority.provider_sdk_call_enabled is False
    assert read_model.authority.live_provider_network_call_enabled_by_default is False
    assert len(read_model.provider_adapters) >= 2
    assert all(
        adapter.receipt_store_required_before_network
        for adapter in read_model.provider_adapters
    )
    assert read_model.network_allowlists.default_network_denied is True
    assert read_model.network_allowlists.endpoint_refs
    assert read_model.model_metadata_discovery.provider_model_refs
    assert (
        read_model.model_metadata_discovery.live_provider_model_discovery_enabled
        is False
    )
    assert read_model.cost_hooks.unknown_paid_cost_blocks is True
    assert (
        read_model.local_llama_cpp_lifecycle.process_start_performed_by_read_model
        is False
    )
    assert (
        read_model.local_llama_cpp_lifecycle.model_call_performed_by_read_model is False
    )
    assert read_model.router_traces[0].status == "trace_only_no_execution"
    assert read_model.router_traces[0].model_execution_performed is False
    assert read_model.router_traces[0].provider_execution_performed is False
    assert read_model.router_traces[0].reason_codes
    delegated_catalog = read_model.delegated_runtime_model_catalog
    assert delegated_catalog.schema_version == "delegated_runtime_model_catalog.v1"
    assert delegated_catalog.status == "read_only_runtime_model_availability"
    assert delegated_catalog.runtime_profiles_route_ref == "GET /api/runtime/profiles"
    assert delegated_catalog.model_count == len(delegated_catalog.records)
    assert delegated_catalog.runtime_reported_available_count >= 1
    assert delegated_catalog.uaa_authorized_model_count == 0
    assert delegated_catalog.runtime_says_available_is_not_authority is True
    assert delegated_catalog.uaa_may_invoke_any_listed_model is False
    assert delegated_catalog.provider_sdk_call_enabled is False
    assert delegated_catalog.remote_model_call_enabled is False
    assert delegated_catalog.credential_collection_enabled is False
    assert delegated_catalog.billing_authority_granted is False
    assert all(
        record.uaa_invocation_allowed is False
        and record.provider_sdk_call_enabled is False
        and record.live_provider_network_call_performed is False
        and record.raw_provider_payload_persisted is False
        for record in delegated_catalog.records
    )
    model_slot_posture = read_model.model_slot_posture
    assert model_slot_posture.schema_version == "hermes_runtime_model_slot_posture.v1"
    assert model_slot_posture.status == "read_only_model_slot_intent"
    assert model_slot_posture.trust_lane_ref == "trust-lane:model-slot-posture"
    assert model_slot_posture.slot_count == 8
    assert model_slot_posture.slot_count == len(model_slot_posture.records)
    assert model_slot_posture.warning_count >= 3
    assert model_slot_posture.main_slot_ref == "model-slot-ref:uaa:main-thinking"
    assert len(model_slot_posture.auxiliary_slot_refs) == 7
    assert model_slot_posture.live_auxiliary_calls_enabled is False
    assert model_slot_posture.provider_sdk_use_enabled is False
    assert model_slot_posture.runtime_selection_mutation_enabled is False
    assert model_slot_posture.hidden_model_routing_enabled is False
    assert model_slot_posture.raw_prompt_persistence_enabled is False
    assert model_slot_posture.raw_response_persistence_enabled is False
    assert model_slot_posture.route_decision_trace_required is True
    assert model_slot_posture.cost_estimate_required is True
    assert model_slot_posture.approval_profile_mapping_required is True
    assert model_slot_posture.model_output_truth_envelope_required is True
    assert model_slot_posture.receipts_required_before_execution is True
    assert {record.slot_role for record in model_slot_posture.records} == {
        "main_thinking",
        "summarization",
        "title",
        "approval_scoring",
        "compression",
        "retrieval",
        "vision",
        "review",
    }
    assert all(
        record.live_auxiliary_call_enabled is False
        and record.provider_sdk_call_enabled is False
        and record.hidden_model_routing_enabled is False
        and record.runtime_selection_mutation_enabled is False
        and record.raw_prompt_persisted is False
        and record.raw_response_persisted is False
        and record.route_decision_trace_required is True
        and record.cost_estimate_required is True
        and record.receipt_required_before_execution is True
        for record in model_slot_posture.records
    )
    assert read_model.role_provider_evidence.schema_version == (
        "role_based_model_provider_evidence.v1"
    )
    assert read_model.role_provider_evidence.role_count == 7
    assert read_model.role_provider_evidence.model_invocation_performed is False
    routing = read_model.provider_routing_intelligence
    assert routing.schema_version == "provider_routing_intelligence.v1"
    assert routing.proposal_only is True
    assert routing.request_scoped_invocation_decision_required is True
    assert routing.approval_refs_are_identifiers_only is True
    assert routing.invocation_authorized is False
    assert routing.provider_call_performed is False
    posture = read_model.model_provider_research_posture
    assert posture.schema_version == "model_provider_research_posture.v1"
    assert posture.provider_count == len(posture.provider_postures)
    assert posture.provider_postures
    assert posture.provider_sdk_call_enabled is False
    assert posture.remote_model_call_enabled is False
    assert posture.live_web_fetch_enabled is False
    assert posture.browser_automation_enabled is False
    assert posture.model_output_truth.status == "proposal_and_evidence_not_authority"
    assert posture.model_output_truth.generated_text_is_verified_fact is False
    assert posture.model_output_truth.memory_write_from_model_output_enabled is False
    assert (
        posture.model_output_truth.action_authority_from_model_output_enabled is False
    )
    assert posture.external_information.status == "web_access_gateway_deny_by_default"
    assert posture.external_information.web_access_gateway_required is True
    assert posture.external_information.fetched_content_untrusted is True
    assert posture.external_information.browser_action_enabled_by_control_plane is False
    assert "raw prompt" not in json.dumps(payload).lower()
    assert "raw response" not in json.dumps(payload).lower()
    assert "provider payload persisted" not in json.dumps(payload).lower()


def test_model_provider_control_plane_route_is_protected_read_only_and_safe(
    monkeypatch,
) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = TestClient(app)

    response = client.get(
        "/control-center/providers/runtime-control-plane",
        headers={"Authorization": f"Bearer {LOCAL_TEST_BEARER}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_providers_runtime_control_plane"
    assert "raw_credentials_omitted" in body["redactions_applied"]
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["authority"]["provider_sdk_call_enabled"] is False
    assert data["authority"]["live_provider_network_call_enabled_by_default"] is False
    assert data["secret_status"]["secret_material_visible"] is False
    assert data["network_allowlists"]["endpoint_refs"]
    assert (
        data["local_llama_cpp_lifecycle"]["process_start_performed_by_read_model"]
        is False
    )
    assert data["router_traces"][0]["model_execution_performed"] is False
    assert data["delegated_runtime_model_catalog"]["schema_version"] == (
        "delegated_runtime_model_catalog.v1"
    )
    assert data["delegated_runtime_model_catalog"]["uaa_authorized_model_count"] == 0
    assert (
        data["delegated_runtime_model_catalog"][
            "runtime_says_available_is_not_authority"
        ]
        is True
    )
    assert data["delegated_runtime_model_catalog"]["remote_model_call_enabled"] is False
    assert data["model_slot_posture"]["schema_version"] == (
        "hermes_runtime_model_slot_posture.v1"
    )
    assert data["model_slot_posture"]["slot_count"] == 8
    assert data["model_slot_posture"]["hidden_model_routing_enabled"] is False
    assert data["model_slot_posture"]["live_auxiliary_calls_enabled"] is False
    assert data["model_slot_posture"]["records"][0]["raw_prompt_persisted"] is False
    assert (
        data["role_provider_evidence"]["schema_version"]
        == "role_based_model_provider_evidence.v1"
    )
    assert data["role_provider_evidence"]["provider_sdk_call_enabled"] is False
    assert data["provider_routing_intelligence"]["proposal_only"] is True
    assert data["provider_routing_intelligence"]["invocation_authorized"] is False
    assert data["model_provider_research_posture"]["provider_sdk_call_enabled"] is False
    assert data["model_provider_research_posture"]["live_web_fetch_enabled"] is False
    assert (
        data["model_provider_research_posture"]["external_information"][
            "fetched_content_untrusted"
        ]
        is True
    )


def test_model_provider_control_plane_route_manifest_posture() -> None:
    manifest = build_api_manifest(app)
    route = next(
        route
        for route in manifest.routes
        if route.path == "/control-center/providers/runtime-control-plane"
        and route.method == "GET"
    )

    assert route.operation_id == "get_control_center_providers_runtime_control_plane"
    assert route.side_effect_class == "validation_only"
    assert route.route_classification == "local_readonly"
    assert route.approval_posture == "not_required_for_route_classification"
    assert "control_center_model_provider_control_plane_read_model" in (
        manifest.capabilities_declared
    )
    assert "control_center_model_provider_control_plane_as_runtime_authority" in (
        manifest.capabilities_blocked
    )


def test_delegated_runtime_model_catalog_rejects_invocation_authority() -> None:
    catalog = (
        build_model_provider_control_plane_read_model().delegated_runtime_model_catalog
    )
    payload = catalog.model_dump(mode="python")
    payload["uaa_may_invoke_any_listed_model"] = True

    try:
        DelegatedRuntimeModelCatalogPosture(**payload)
    except ValueError as exc:
        assert "AUTHORITY_DRIFT" in str(exc)
    else:
        raise AssertionError("delegated runtime catalog accepted invocation authority")

    payload = catalog.model_dump(mode="python")
    payload["records"][0]["uaa_invocation_allowed"] = True

    try:
        DelegatedRuntimeModelCatalogPosture(**payload)
    except ValueError as exc:
        assert "AUTHORITY_DRIFT" in str(exc)
    else:
        raise AssertionError("delegated runtime model accepted invocation authority")


def test_model_slot_posture_rejects_hidden_routing_and_raw_prompt_persistence() -> None:
    posture = build_model_provider_control_plane_read_model().model_slot_posture
    payload = posture.model_dump(mode="python")
    payload["hidden_model_routing_enabled"] = True

    try:
        ModelSlotPostureReadModel(**payload)
    except ValueError as exc:
        assert "AUTHORITY_DRIFT" in str(exc)
    else:
        raise AssertionError("model slot posture accepted hidden routing")

    payload = posture.model_dump(mode="python")
    payload["records"][0]["live_auxiliary_call_enabled"] = True

    try:
        ModelSlotPostureReadModel(**payload)
    except ValueError as exc:
        assert "AUTHORITY_DRIFT" in str(exc)
    else:
        raise AssertionError("model slot posture accepted auxiliary model call")

    payload = posture.model_dump(mode="python")
    payload["records"][0]["raw_prompt_persisted"] = True

    try:
        ModelSlotPostureReadModel(**payload)
    except ValueError as exc:
        assert "AUTHORITY_DRIFT" in str(exc)
    else:
        raise AssertionError("model slot posture accepted raw prompt persistence")


def test_model_provider_control_plane_cli_uses_same_safe_schema() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py", "--json"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == "model_provider_control_plane.v1"
    assert payload["backend_owned"] is True
    assert payload["read_only"] is True
    assert payload["authority"]["provider_sdk_call_enabled"] is False
    assert payload["authority"]["local_llama_cpp_lifecycle_contract_available"] is True
    assert len(payload["provider_adapters"]) >= 2
    assert payload["router_traces"][0]["status"] == "trace_only_no_execution"
    assert payload["delegated_runtime_model_catalog"]["model_count"] >= 1
    assert (
        payload["delegated_runtime_model_catalog"]["uaa_may_invoke_any_listed_model"]
        is False
    )
    assert payload["model_slot_posture"]["slot_count"] == 8
    assert payload["model_slot_posture"]["warning_count"] >= 3
    assert payload["model_slot_posture"]["hidden_model_routing_enabled"] is False
    assert (
        payload["model_slot_posture"]["records"][0]["live_auxiliary_call_enabled"]
        is False
    )
    assert payload["role_provider_evidence"]["role_count"] == 7
    assert payload["role_provider_evidence"]["model_invocation_performed"] is False
    assert payload["model_provider_research_posture"]["provider_count"] >= 1
    assert (
        payload["model_provider_research_posture"]["model_output_truth"][
            "generated_text_is_verified_fact"
        ]
        is False
    )
