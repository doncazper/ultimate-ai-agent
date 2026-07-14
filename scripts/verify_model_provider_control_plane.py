#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV
from ultimate_ai_agent.core.providers.control_plane import (
    MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF,
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.providers.routing_intelligence import (
    PROVIDER_ROUTING_MAX_OBSERVATIONS,
    PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    ProviderRoutingProposal,
)


ROOT = Path(__file__).resolve().parents[1]
LOCAL_TEST_BEARER = "model-provider-local-bearer"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_no_authority(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden_enabled_fragments = [
        '"broad_provider_runtime_enabled": true',
        '"provider_sdk_call_enabled": true',
        '"live_provider_network_call_enabled_by_default": true',
        '"network_call_enabled_by_default": true',
        '"provider_router_execution_enabled": true',
        '"model_router_execution_enabled": true',
        '"local_llama_cpp_process_started_by_control_plane": true',
        '"remote_model_call_enabled": true',
        '"uaa_may_invoke_any_listed_model": true',
        '"uaa_invocation_allowed": true',
        '"live_provider_discovery_enabled": true',
        '"live_provider_network_call_performed": true',
        '"credential_collection_enabled": true',
        '"credential_material_visible": true',
        '"billing_authority_granted": true',
        '"model_output_authority_enabled": true',
        '"raw_provider_payload_persisted": true',
        '"live_auxiliary_calls_enabled": true',
        '"live_auxiliary_call_enabled": true',
        '"provider_sdk_use_enabled": true',
        '"runtime_selection_mutation_enabled": true',
        '"hidden_model_routing_enabled": true',
        '"raw_prompt_persistence_enabled": true',
        '"raw_response_persistence_enabled": true',
        '"raw_prompt_persisted": true',
        '"raw_response_persisted": true',
        '"local_model_call_performed": true',
        '"model_invocation_performed": true',
        '"process_start_performed_by_read_model": true',
        '"model_call_performed_by_read_model": true',
        '"shell_execution_enabled": true',
        '"background_autonomy_enabled": true',
        '"production_authority_enabled": true',
        '"raw_prompt_response_provider_payload_persisted": true',
        '"prompt_content_persisted": true',
        '"response_content_persisted": true',
    ]
    for fragment in forbidden_enabled_fragments:
        _assert(fragment not in serialized, f"forbidden enabled authority: {fragment}")


def _assert_provider_routing_truth(routing: ProviderRoutingProposal) -> None:
    _assert(routing.proposal_only, "provider routing must remain proposal-only")
    _assert(not routing.invocation_authorized, "provider routing minted authority")
    _assert(
        not routing.provider_call_performed,
        "provider routing performed a provider call",
    )
    _assert(
        routing.observed_candidate_count <= PROVIDER_ROUTING_MAX_OBSERVATIONS,
        "provider routing observation cap drifted",
    )
    _assert(
        routing.presented_candidate_count <= PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
        "provider routing presentation cap drifted",
    )
    _assert(
        len(routing.request_fingerprint_ref.rsplit(":", 1)[-1]) == 64,
        "provider routing request fingerprint is incomplete",
    )
    _assert(
        len(routing.observation_set_fingerprint_ref.rsplit(":", 1)[-1]) == 64,
        "provider routing observation-set fingerprint is incomplete",
    )
    for candidate in routing.candidates:
        _assert(
            candidate.availability_snapshot.authority_posture.value == "blocked",
            "provider readiness observation minted invocation authority",
        )
        _assert(
            candidate.availability_snapshot.runtime_readiness_status.value != "ready",
            "default provider readiness invented runtime readiness",
        )


def main() -> int:
    read_model = build_model_provider_control_plane_read_model()
    payload = read_model.model_dump(mode="json")
    _assert(read_model.backend_owned, "read model must be backend owned")
    _assert(read_model.read_only, "read model must be read-only")
    _assert(read_model.safe_refs_only, "read model must be safe refs only")
    _assert(
        read_model.route_ref == MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF,
        "route ref drifted",
    )
    _assert(len(read_model.provider_adapters) >= 2, "provider adapters missing")
    _assert(read_model.network_allowlists.endpoint_refs, "endpoint refs missing")
    _assert(read_model.cost_hooks.unknown_paid_cost_blocks, "cost block missing")
    _assert(
        read_model.local_llama_cpp_lifecycle.loopback_only,
        "llama.cpp lifecycle must be loopback-only",
    )
    _assert(read_model.router_traces, "router traces missing")
    _assert_provider_routing_truth(read_model.provider_routing_intelligence)
    _assert(
        read_model.role_provider_evidence.role_count == 7,
        "role provider evidence missing roles",
    )
    delegated_catalog = read_model.delegated_runtime_model_catalog
    _assert(
        delegated_catalog.schema_version == "delegated_runtime_model_catalog.v1",
        "delegated runtime model catalog schema drifted",
    )
    _assert(
        delegated_catalog.runtime_says_available_is_not_authority,
        "runtime availability must remain separate from UAA invocation authority",
    )
    _assert(
        delegated_catalog.uaa_authorized_model_count == 0,
        "delegated catalog must not authorize model invocation",
    )
    _assert(
        not delegated_catalog.uaa_may_invoke_any_listed_model,
        "delegated catalog must not grant model invocation",
    )
    _assert(
        delegated_catalog.runtime_profile_count >= 1,
        "delegated catalog must bind to UAA runtime profiles",
    )
    _assert(
        delegated_catalog.model_count == len(delegated_catalog.records),
        "delegated catalog count drifted",
    )
    for record in delegated_catalog.records:
        _assert(
            not record.uaa_invocation_allowed,
            "delegated model record must not authorize invocation",
        )
        _assert(
            not record.provider_sdk_call_enabled,
            "delegated model record must not enable provider SDK calls",
        )
        _assert(
            not record.live_provider_network_call_performed,
            "delegated model record must not perform provider network calls",
        )
        _assert(
            record.blocked_authority_refs,
            "delegated model record must explain blocked authority",
        )
    model_slot_posture = read_model.model_slot_posture
    _assert(
        model_slot_posture.schema_version == "hermes_runtime_model_slot_posture.v1",
        "model slot posture schema drifted",
    )
    _assert(
        model_slot_posture.slot_count == 8,
        "model slot posture must expose all configured/intended slots",
    )
    _assert(
        model_slot_posture.warning_count >= 3,
        "model slot posture warnings missing",
    )
    _assert(
        not model_slot_posture.hidden_model_routing_enabled,
        "model slot posture must not enable hidden routing",
    )
    _assert(
        not model_slot_posture.live_auxiliary_calls_enabled,
        "model slot posture must not enable auxiliary calls",
    )
    _assert(
        not model_slot_posture.provider_sdk_use_enabled,
        "model slot posture must not enable provider SDK use",
    )
    for record in model_slot_posture.records:
        _assert(
            not record.live_auxiliary_call_enabled,
            "model slot record must not enable auxiliary calls",
        )
        _assert(
            not record.hidden_model_routing_enabled,
            "model slot record must not enable hidden routing",
        )
        _assert(
            not record.raw_prompt_persisted,
            "model slot record must not persist raw prompts",
        )
        _assert(
            record.blocked_authority_refs,
            "model slot record blockers missing",
        )
    _assert_no_authority(payload)

    client = TestClient(app)
    os.environ[LOCAL_API_BEARER_ENV] = LOCAL_TEST_BEARER
    response = client.get(
        "/control-center/providers/runtime-control-plane",
        headers={"Authorization": f"Bearer {LOCAL_TEST_BEARER}"},
    )
    _assert(response.status_code == 200, "runtime control plane endpoint failed")
    envelope = response.json()
    api_payload = envelope.get("data") or envelope.get("result")
    _assert(isinstance(api_payload, dict), "endpoint did not return payload")
    _assert(api_payload["contract_ref"] == read_model.contract_ref, "contract mismatch")
    _assert(
        api_payload["role_provider_evidence"]["schema_version"]
        == "role_based_model_provider_evidence.v1",
        "API role provider evidence missing",
    )
    _assert(
        api_payload["delegated_runtime_model_catalog"]["schema_version"]
        == "delegated_runtime_model_catalog.v1",
        "API delegated runtime model catalog missing",
    )
    _assert(
        api_payload["delegated_runtime_model_catalog"]["uaa_authorized_model_count"]
        == 0,
        "API delegated runtime model catalog authorized a model",
    )
    _assert(
        api_payload["model_slot_posture"]["schema_version"]
        == "hermes_runtime_model_slot_posture.v1",
        "API model slot posture missing",
    )
    _assert(
        api_payload["model_slot_posture"]["slot_count"] == 8,
        "API model slot posture count drifted",
    )
    _assert_no_authority(api_payload)

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_model_provider_control_plane.py",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(cli.stdout)
    _assert(
        cli_payload["contract_ref"] == read_model.contract_ref, "CLI contract mismatch"
    )
    _assert(
        cli_payload["role_provider_evidence"]["role_count"] == 7,
        "CLI role provider evidence missing",
    )
    _assert(
        cli_payload["delegated_runtime_model_catalog"]["schema_version"]
        == "delegated_runtime_model_catalog.v1",
        "CLI delegated runtime model catalog missing",
    )
    _assert(
        cli_payload["delegated_runtime_model_catalog"]["uaa_authorized_model_count"]
        == 0,
        "CLI delegated runtime model catalog authorized a model",
    )
    _assert(
        cli_payload["model_slot_posture"]["schema_version"]
        == "hermes_runtime_model_slot_posture.v1",
        "CLI model slot posture missing",
    )
    _assert(
        cli_payload["provider_routing_intelligence"]["proposal_only"] is True,
        "CLI provider routing intelligence is not proposal-only",
    )
    _assert(
        cli_payload["provider_routing_intelligence"]["invocation_authorized"] is False,
        "CLI provider routing intelligence minted authority",
    )
    _assert(
        cli_payload["model_slot_posture"]["slot_count"] == 8,
        "CLI model slot posture count drifted",
    )
    _assert_no_authority(cli_payload)
    print("model_provider_control_plane: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
