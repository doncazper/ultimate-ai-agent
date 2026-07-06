from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS,
    RUNTIME_VIRTUAL_PROVIDER_MOA_CONTRACT_REF,
    RuntimeVirtualProviderMoaReadModel,
    build_runtime_virtual_provider_moa_read_model,
)


client = TestClient(app)


def test_virtual_provider_moa_is_read_only_preset_posture() -> None:
    read_model = build_runtime_virtual_provider_moa_read_model()

    assert read_model.schema_version == "runtime_virtual_provider_moa.v1"
    assert read_model.contract_ref == RUNTIME_VIRTUAL_PROVIDER_MOA_CONTRACT_REF
    assert read_model.status == "read_only_virtual_provider_preset_posture"
    assert read_model.route_ref == "GET /api/runtime/virtual-provider-moa"
    assert read_model.cli_ref == "uaa runtime inspect-virtual-provider-moa"
    assert read_model.preset_count == 3
    assert read_model.agent_slot_count == 7
    assert read_model.ready_preset_count == 1
    assert read_model.blocked_preset_count == 1
    assert read_model.live_model_fanout_enabled is False
    assert read_model.provider_sdk_enabled is False
    assert read_model.external_runtime_dispatch_enabled is False
    assert read_model.hidden_advisor_prompts_enabled is False
    assert read_model.raw_prompt_persistence_enabled is False
    assert read_model.raw_response_persistence_enabled is False
    assert read_model.output_authority_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_VIRTUAL_PROVIDER_MOA_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-virtual-provider-moa:"
    )


def test_virtual_provider_moa_presets_and_slots_do_not_fan_out() -> None:
    read_model = build_runtime_virtual_provider_moa_read_model()
    roles = {slot.role for preset in read_model.presets for slot in preset.slots}

    assert roles == {
        "codex_implementer",
        "claude_reviewer",
        "hermes_researcher",
        "local_verifier",
        "uaa_supervisor",
        "security_reviewer",
    }
    for preset in read_model.presets:
        assert preset.per_agent_output_envelopes_required is True
        assert preset.comparison_proof_required is True
        assert preset.live_model_fanout_enabled is False
        assert preset.provider_sdk_enabled is False
        assert preset.external_runtime_dispatch_enabled is False
        assert preset.hidden_advisor_prompts_enabled is False
        assert preset.raw_prompt_persistence_enabled is False
        assert preset.raw_response_persistence_enabled is False
        assert preset.output_authority_enabled is False
        assert preset.production_authority_enabled is False
        for slot in preset.slots:
            assert slot.configured_for_live_call is False
            assert slot.provider_sdk_call_enabled is False
            assert slot.external_runtime_dispatch_enabled is False
            assert slot.hidden_advisor_prompt_enabled is False
            assert slot.raw_prompt_persisted is False
            assert slot.raw_response_persisted is False
            assert slot.output_authoritative is False
            assert slot.production_authority_enabled is False
            assert slot.output_envelope_ref.startswith("agent-output-envelope-ref:")


@pytest.mark.parametrize(
    "field",
    [
        "live_model_fanout_enabled",
        "provider_sdk_enabled",
        "external_runtime_dispatch_enabled",
        "hidden_advisor_prompts_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "output_authority_enabled",
        "production_authority_enabled",
    ],
)
def test_virtual_provider_moa_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_virtual_provider_moa_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_VIRTUAL_PROVIDER_MOA_AUTHORITY_DENIED"):
        RuntimeVirtualProviderMoaReadModel(**payload)


def test_virtual_provider_moa_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/virtual-provider-moa")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_virtual_provider_moa"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/virtual-provider-moa"
    assert data["live_model_fanout_enabled"] is False
    assert data["provider_sdk_enabled"] is False
    assert data["preset_count"] == 3
    assert data["agent_slot_count"] == 7
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_payload" not in serialized
    assert "raw_response_payload" not in serialized


def test_virtual_provider_moa_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-virtual-provider-moa",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_virtual_provider_moa"]
    assert payload["safe_refs_only"] is True
    assert payload["live_model_fanout_performed"] is False
    assert payload["provider_sdk_call_performed"] is False
    assert payload["external_runtime_dispatch_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/virtual-provider-moa"
    assert read_model["cli_ref"] == "uaa runtime inspect-virtual-provider-moa"
    assert read_model["preset_count"] == 3
