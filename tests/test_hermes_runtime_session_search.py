from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SESSION_SEARCH_CONTRACT_REF,
    RuntimeSessionSearchReadModel,
    build_runtime_session_search_read_model,
)


client = TestClient(app)


def test_runtime_session_search_is_safe_ref_only_and_memory_separate() -> None:
    read_model = build_runtime_session_search_read_model()

    assert read_model.schema_version == "runtime_session_search.v1"
    assert read_model.contract_ref == RUNTIME_SESSION_SEARCH_CONTRACT_REF
    assert read_model.status == "read_only_safe_ref_session_run_search"
    assert read_model.route_ref == "GET /api/runtime/session-search"
    assert read_model.cli_ref == "uaa runtime inspect-session-search"
    assert read_model.query_mode == "safe_ref_match_only"
    assert read_model.result_count == 5
    assert read_model.session_ref_count == 5
    assert read_model.run_ref_count == 4
    assert read_model.attachable_context_ref_count == 5
    assert read_model.raw_transcript_persistence_enabled is False
    assert read_model.raw_prompt_response_exposure_enabled is False
    assert read_model.semantic_provider_call_enabled is False
    assert read_model.embedding_vector_index_enabled is False
    assert read_model.hidden_context_injection_authorized is False
    assert read_model.memory_write_authorized is False
    assert read_model.action_execution_authorized is False
    assert read_model.production_authority_enabled is False
    posture = read_model.memory_separation_posture
    assert posture["status"] == "separate_from_durable_memory"
    assert posture["memory_write_performed"] is False
    assert posture["memory_recall_used_as_truth"] is False
    assert posture["operator_selected_attach_required"] is True
    assert "proof-ref:hermes-runtime-adoption:phase-12:session-search" in (
        read_model.proof_refs
    )
    assert "blocked-authority:session-search-no-memory-write" in (
        read_model.blocked_authority_refs
    )


def test_runtime_session_search_results_do_not_grant_authority() -> None:
    read_model = build_runtime_session_search_read_model()

    for result in read_model.results:
        assert result.raw_transcript_persisted is False
        assert result.raw_prompt_persisted is False
        assert result.raw_response_persisted is False
        assert result.raw_provider_payload_persisted is False
        assert result.semantic_provider_call_performed is False
        assert result.embedding_vector_index_used is False
        assert result.memory_write_performed is False
        assert result.context_injection_authorized is False
        assert result.action_execution_authorized is False
        assert result.production_authority_enabled is False
        assert result.attachable_context_ref.startswith("context-ref:session-search:")
        assert result.why_matched_refs
        assert result.blocked_authority_refs


def test_runtime_session_search_filters_by_safe_query_ref() -> None:
    read_model = build_runtime_session_search_read_model(
        query_ref="run-ref:mock-fallback:proof"
    )

    assert read_model.query_ref == "run-ref:mock-fallback:proof"
    assert read_model.result_count == 1
    assert read_model.results[0].result_kind == "proof_run"
    assert read_model.results[0].run_ref == "run-ref:mock-fallback:proof"


def test_runtime_session_search_rejects_authority_claims() -> None:
    base = build_runtime_session_search_read_model().model_dump()
    base["memory_write_authorized"] = True

    with pytest.raises(ValueError, match="AUTHORITY_DENIED"):
        RuntimeSessionSearchReadModel(**base)

    base = build_runtime_session_search_read_model().model_dump()
    base["results"][0]["context_injection_authorized"] = True

    with pytest.raises(ValueError, match="AUTHORITY_DENIED"):
        RuntimeSessionSearchReadModel(**base)


def test_api_runtime_session_search_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/session-search")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_session_search.v1"
    assert data["result_count"] == 5
    assert data["memory_write_authorized"] is False
    assert data["hidden_context_injection_authorized"] is False
    assert data["raw_transcript_persistence_enabled"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-session-search:phase-12"
    )

    filtered = client.get(
        "/api/runtime/session-search?query_ref=run-ref:mock-fallback:proof"
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["result_count"] == 1

    unsafe = client.get("/api/runtime/session-search?query_ref=raw_prompt")
    assert unsafe.status_code == 200
    unsafe_body = unsafe.json()
    assert unsafe_body["success"] is False
    assert unsafe_body["error"]["code"] == "RUNTIME_SESSION_SEARCH_REF_DENIED"
    assert "raw_prompt" not in unsafe.text


def test_cli_runtime_session_search_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-search",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_session_search"]
    assert payload["execution_performed"] is False
    assert payload["memory_write_performed"] is False
    assert payload["context_injection_performed"] is False
    assert payload["semantic_provider_call_performed"] is False
    assert payload["raw_transcript_omitted"] is True
    assert read_model["route_ref"] == "GET /api/runtime/session-search"
    assert read_model["cli_ref"] == "uaa runtime inspect-session-search"
    assert read_model["result_count"] == 5

    filtered = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-search",
            "--query-ref",
            "run-ref:mock-fallback:proof",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    filtered_payload = json.loads(filtered.stdout)
    assert filtered_payload["runtime_session_search"]["result_count"] == 1
