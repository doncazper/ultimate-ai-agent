from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SESSION_LINEAGE_CONTRACT_REF,
    RuntimeSessionLineageReadModel,
    build_runtime_session_lineage_read_model,
)


client = TestClient(app)


def test_session_lineage_posture_is_read_only_safe_ref_model() -> None:
    read_model = build_runtime_session_lineage_read_model()

    assert read_model.schema_version == "runtime_session_lineage.v1"
    assert read_model.contract_ref == RUNTIME_SESSION_LINEAGE_CONTRACT_REF
    assert read_model.status == "read_only_session_lineage_and_fork_posture"
    assert read_model.route_ref == "GET /api/runtime/session-lineage"
    assert read_model.cli_ref == "uaa runtime inspect-session-lineage"
    assert read_model.node_count == 7
    assert read_model.fork_count == 3
    assert read_model.root_count == 1
    assert read_model.parent_child_link_count == 6
    assert read_model.max_lineage_depth == 3
    assert read_model.raw_transcript_clone_enabled is False
    assert read_model.hidden_context_injection_enabled is False
    assert read_model.runtime_dispatch_enabled is False
    assert read_model.provider_model_call_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-session-lineage:"
    )


def test_session_lineage_nodes_and_forks_do_not_clone_or_dispatch() -> None:
    read_model = build_runtime_session_lineage_read_model()
    node_kinds = {node.node_kind for node in read_model.nodes}
    fork_statuses = {fork.status for fork in read_model.forks}

    assert node_kinds == {
        "user_request",
        "coding_task",
        "runtime_run",
        "proof_record",
        "review_branch",
        "retry_branch",
        "comparison_branch",
    }
    assert fork_statuses == {
        "promotion_ready",
        "read_only_lineage",
        "blocked_raw_clone",
    }
    for node in read_model.nodes:
        assert node.raw_transcript_cloned is False
        assert node.raw_prompt_persisted is False
        assert node.raw_response_persisted is False
        assert node.hidden_context_injected is False
        assert node.runtime_dispatch_performed is False
        assert node.provider_model_call_performed is False
        assert node.shell_execution_performed is False
        assert node.browser_automation_performed is False
        assert node.connector_write_performed is False
        assert node.production_authority_enabled is False
        assert set(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS).issubset(
            set(node.blocked_authority_refs)
        )
    for fork in read_model.forks:
        assert fork.explicit_operator_intent_required is True
        assert fork.redacted_fork_envelope_required is True
        assert fork.proof_binding_required is True
        assert fork.raw_transcript_cloned is False
        assert fork.hidden_context_injected is False
        assert fork.runtime_dispatch_performed is False
        assert fork.provider_model_call_performed is False
        assert fork.production_authority_enabled is False
        assert fork.redacted_fork_envelope_ref.startswith("fork-envelope-ref:")
        assert fork.retrieval_log_ref.startswith("retrieval-log-ref:")


@pytest.mark.parametrize(
    "field",
    [
        "raw_transcript_clone_enabled",
        "hidden_context_injection_enabled",
        "runtime_dispatch_enabled",
        "provider_model_call_enabled",
        "production_authority_enabled",
    ],
)
def test_session_lineage_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_session_lineage_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_SESSION_LINEAGE_AUTHORITY_DENIED"):
        RuntimeSessionLineageReadModel(**payload)


def test_session_lineage_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/session-lineage")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_session_lineage"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/session-lineage"
    assert data["raw_transcript_clone_enabled"] is False
    assert data["runtime_dispatch_enabled"] is False
    assert data["node_count"] == 7
    assert data["fork_count"] == 3
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_transcript_payload" not in serialized
    assert "raw_prompt_payload" not in serialized


def test_session_lineage_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-lineage",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_session_lineage"]
    assert payload["safe_refs_only"] is True
    assert payload["raw_transcripts_omitted"] is True
    assert payload["hidden_context_injection_performed"] is False
    assert payload["runtime_dispatch_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/session-lineage"
    assert read_model["cli_ref"] == "uaa runtime inspect-session-lineage"
    assert read_model["node_count"] == 7
