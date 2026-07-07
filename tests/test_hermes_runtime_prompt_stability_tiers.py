from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF,
    RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_CLI_REF,
    RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS,
    RUNTIME_PROMPT_STABILITY_CONTRACT_REF,
    RuntimePromptStabilityTier,
    RuntimePromptStabilityTiersReadModel,
    build_runtime_prompt_stability_tiers_read_model,
)


client = TestClient(app)


def test_prompt_stability_tiers_are_read_only_prompt_contract_posture() -> None:
    read_model = build_runtime_prompt_stability_tiers_read_model()

    assert read_model.schema_version == "runtime_prompt_stability_tiers.v1"
    assert read_model.contract_ref == RUNTIME_PROMPT_STABILITY_CONTRACT_REF
    assert read_model.status == "read_only_prompt_contract_posture"
    assert read_model.route_ref == "GET /api/runtime/prompt-stability-tiers"
    assert read_model.cli_ref == "uaa runtime inspect-prompt-stability-tiers"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert (
        "adapter-ref:prompt-stability-model-call:not-implemented"
        in read_model.unsupported_adapter_refs
    )
    assert read_model.tier_count == 5
    assert read_model.stable_cache_candidate_count == 1
    assert read_model.semi_stable_ref_set_count == 2
    assert read_model.volatile_no_cache_count == 1
    assert read_model.operator_scoped_no_cache_count == 1
    assert read_model.safe_prompt_manifest_required is True
    assert read_model.prompt_hashes_required is True
    assert read_model.redacted_receipt_required is True
    assert read_model.proof_link_required is True
    assert read_model.raw_prompt_persistence_enabled is False
    assert read_model.hidden_prompt_injection_enabled is False
    assert read_model.context_injection_enabled is False
    assert read_model.model_call_enabled is False
    assert read_model.cache_write_enabled is False
    assert read_model.model_output_authority_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-prompt-stability:"
    )


def test_prompt_stability_tiers_never_store_raw_or_enable_injection() -> None:
    read_model = build_runtime_prompt_stability_tiers_read_model()

    assert {tier.tier_kind for tier in read_model.tiers} == {
        "stable_identity_policy",
        "durable_context_refs",
        "retrieval_refs",
        "volatile_runtime_state",
        "operator_turn_ref",
    }
    for tier in read_model.tiers:
        assert tier.raw_prompt_persisted is False
        assert tier.raw_response_persisted is False
        assert tier.provider_payload_persisted is False
        assert tier.hidden_prompt_injection_enabled is False
        assert tier.context_injection_enabled is False
        assert tier.model_call_performed is False
        assert tier.provider_sdk_call_performed is False
        assert tier.cache_write_enabled is False
        assert tier.model_output_authoritative is False
        assert tier.production_authority_enabled is False
        assert set(RUNTIME_PROMPT_STABILITY_BLOCKED_AUTHORITY_REFS).issubset(
            set(tier.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "provider_payload_persistence_enabled",
        "hidden_prompt_injection_enabled",
        "context_injection_enabled",
        "model_call_enabled",
        "provider_sdk_enabled",
        "model_output_authority_enabled",
        "cache_write_enabled",
        "production_authority_enabled",
    ],
)
def test_prompt_stability_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_prompt_stability_tiers_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_PROMPT_STABILITY_AUTHORITY_DENIED"):
        RuntimePromptStabilityTiersReadModel(**payload)


def test_prompt_stability_rejects_authority_mapping_drift() -> None:
    payload = build_runtime_prompt_stability_tiers_read_model().model_dump(mode="json")
    payload["authority_state_mapping_ref"] = "lane-ref:wrong-prompt-stability"

    with pytest.raises(
        ValueError,
        match="RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_MISMATCH",
    ):
        RuntimePromptStabilityTiersReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "hidden_prompt_injection_enabled",
        "context_injection_enabled",
        "model_call_performed",
        "provider_sdk_call_performed",
        "model_output_authoritative",
        "cache_write_enabled",
        "production_authority_enabled",
    ],
)
def test_prompt_stability_tier_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_prompt_stability_tiers_read_model()
        .tiers[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_PROMPT_STABILITY_TIER_AUTHORITY_DENIED",
    ):
        RuntimePromptStabilityTier(**payload)


def test_prompt_stability_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/prompt-stability-tiers")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_prompt_stability_tiers"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/prompt-stability-tiers"
    assert data["authority_state_mapping_ref"] == (
        RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["raw_prompt_persistence_enabled"] is False
    assert data["hidden_prompt_injection_enabled"] is False
    assert data["model_output_authority_enabled"] is False
    assert data["tier_count"] == 5
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_payload" not in serialized
    assert "raw_response_payload" not in serialized
    assert "provider_payload_value" not in serialized


def test_prompt_stability_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-prompt-stability-tiers",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_prompt_stability_tiers"]
    authority_state = payload["authority_state"]
    assert payload["safe_refs_only"] is True
    assert (
        authority_state["mapping_ref"]
        == RUNTIME_PROMPT_STABILITY_AUTHORITY_MAPPING_REF
    )
    assert authority_state["decision_outcome"] == "allow"
    assert payload["hidden_prompt_injection_performed"] is False
    assert payload["context_injection_performed"] is False
    assert payload["model_call_performed"] is False
    assert payload["cache_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/prompt-stability-tiers"
    assert read_model["cli_ref"] == "uaa runtime inspect-prompt-stability-tiers"
    assert (
        read_model["authority_state_cli_ref"]
        == RUNTIME_PROMPT_STABILITY_AUTHORITY_STATE_CLI_REF
    )
    assert read_model["tier_count"] == 5
