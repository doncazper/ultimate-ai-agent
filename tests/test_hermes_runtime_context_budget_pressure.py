from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_MAPPING_REF,
    RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_STATE_CLI_REF,
    RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_CONTEXT_BUDGET_PRESSURE_CONTRACT_REF,
    RuntimeContextBudgetPressureReadModel,
    RuntimeContextBudgetProposal,
    RuntimeContextBudgetSegment,
    build_runtime_context_budget_pressure_read_model,
)


client = TestClient(app)


def test_context_budget_pressure_is_read_only_posture() -> None:
    read_model = build_runtime_context_budget_pressure_read_model()

    assert read_model.schema_version == "runtime_context_budget_pressure.v1"
    assert read_model.contract_ref == RUNTIME_CONTEXT_BUDGET_PRESSURE_CONTRACT_REF
    assert read_model.status == "read_only_context_budget_pressure_posture"
    assert read_model.route_ref == "GET /api/runtime/context-budget-pressure"
    assert read_model.cli_ref == "uaa runtime inspect-context-budget-pressure"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert (
        "adapter-ref:context-budget-model-summarization:not-implemented"
        in read_model.unsupported_adapter_refs
    )
    assert read_model.pressure_level == "warning"
    assert read_model.segment_count == 4
    assert read_model.proposal_count == 3
    assert read_model.warning_count == 2
    assert read_model.critical_count == 1
    assert read_model.trimming_proposal_count == 1
    assert read_model.summarization_proposal_count == 1
    assert read_model.ask_operator_proposal_count == 1
    assert read_model.compression_proposal_required is True
    assert read_model.operator_approval_required is True
    assert read_model.source_coverage_required is True
    assert read_model.retrieval_log_required is True
    assert read_model.summary_receipt_required is True
    assert read_model.hidden_compression_enabled is False
    assert read_model.automatic_context_mutation_enabled is False
    assert read_model.model_summarization_enabled is False
    assert read_model.context_injection_enabled is False
    assert read_model.cache_write_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-context-budget:"
    )


def test_context_budget_segments_and_proposals_deny_hidden_work() -> None:
    read_model = build_runtime_context_budget_pressure_read_model()

    for segment in read_model.segments:
        assert segment.hidden_compression_enabled is False
        assert segment.automatic_context_mutation_enabled is False
        assert segment.model_summarization_call_performed is False
        assert segment.summary_receipt_created is False
        assert segment.raw_context_persisted is False
        assert segment.raw_prompt_persisted is False
        assert segment.raw_response_persisted is False
        assert segment.provider_payload_persisted is False
        assert segment.context_injection_performed is False
        assert segment.provider_sdk_call_performed is False
        assert segment.cache_write_performed is False
        assert segment.production_authority_enabled is False
        assert set(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS).issubset(
            set(segment.blocked_authority_refs)
        )

    for proposal in read_model.proposals:
        assert proposal.approval_required is True
        assert proposal.source_coverage_required is True
        assert proposal.retrieval_log_required is True
        assert proposal.summary_receipt_required is True
        assert proposal.auto_applied is False
        assert proposal.hidden_compression_performed is False
        assert proposal.automatic_context_mutation_performed is False
        assert proposal.model_summarization_call_performed is False
        assert proposal.summary_receipt_created is False
        assert proposal.raw_context_persisted is False
        assert proposal.context_injection_performed is False
        assert proposal.provider_sdk_call_performed is False
        assert proposal.cache_write_performed is False
        assert proposal.production_authority_enabled is False


@pytest.mark.parametrize(
    "field",
    [
        "hidden_compression_enabled",
        "automatic_context_mutation_enabled",
        "model_summarization_enabled",
        "raw_context_persistence_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
        "provider_payload_persistence_enabled",
        "context_injection_enabled",
        "provider_sdk_enabled",
        "cache_write_enabled",
        "production_authority_enabled",
    ],
)
def test_context_budget_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_context_budget_pressure_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_CONTEXT_BUDGET_AUTHORITY_DENIED"):
        RuntimeContextBudgetPressureReadModel(**payload)


def test_context_budget_rejects_authority_mapping_drift() -> None:
    payload = build_runtime_context_budget_pressure_read_model().model_dump(mode="json")
    payload["authority_state_mapping_ref"] = "lane-ref:wrong-context-budget"

    with pytest.raises(
        ValueError,
        match="RUNTIME_CONTEXT_BUDGET_AUTHORITY_MAPPING_MISMATCH",
    ):
        RuntimeContextBudgetPressureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "hidden_compression_enabled",
        "automatic_context_mutation_enabled",
        "model_summarization_call_performed",
        "summary_receipt_created",
        "raw_context_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "context_injection_performed",
        "provider_sdk_call_performed",
        "cache_write_performed",
        "production_authority_enabled",
    ],
)
def test_context_budget_segment_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_context_budget_pressure_read_model()
        .segments[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_CONTEXT_BUDGET_SEGMENT_AUTHORITY_DENIED",
    ):
        RuntimeContextBudgetSegment(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "auto_applied",
        "hidden_compression_performed",
        "automatic_context_mutation_performed",
        "model_summarization_call_performed",
        "summary_receipt_created",
        "raw_context_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "context_injection_performed",
        "provider_sdk_call_performed",
        "cache_write_performed",
        "production_authority_enabled",
    ],
)
def test_context_budget_proposal_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_context_budget_pressure_read_model()
        .proposals[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_CONTEXT_BUDGET_PROPOSAL_AUTHORITY_DENIED",
    ):
        RuntimeContextBudgetProposal(**payload)


def test_context_budget_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/context-budget-pressure")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_context_budget_pressure"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/context-budget-pressure"
    assert data["authority_state_mapping_ref"] == (
        RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["pressure_level"] == "warning"
    assert data["hidden_compression_enabled"] is False
    assert data["automatic_context_mutation_enabled"] is False
    assert data["model_summarization_enabled"] is False
    assert data["context_injection_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_context_payload" not in serialized
    assert "raw_prompt_payload" not in serialized
    assert "provider_payload_value" not in serialized


def test_context_budget_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-context-budget-pressure",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_context_budget_pressure"]
    authority_state = payload["authority_state"]
    assert payload["safe_refs_only"] is True
    assert (
        authority_state["mapping_ref"]
        == RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_MAPPING_REF
    )
    assert authority_state["decision_outcome"] == "allow"
    assert payload["hidden_compression_performed"] is False
    assert payload["automatic_context_mutation_performed"] is False
    assert payload["model_summarization_call_performed"] is False
    assert payload["context_injection_performed"] is False
    assert payload["cache_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/context-budget-pressure"
    assert read_model["cli_ref"] == "uaa runtime inspect-context-budget-pressure"
    assert (
        read_model["authority_state_cli_ref"]
        == RUNTIME_CONTEXT_BUDGET_PRESSURE_AUTHORITY_STATE_CLI_REF
    )
    assert read_model["segment_count"] == 4
