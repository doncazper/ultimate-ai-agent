from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF,
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_CLI_REF,
    RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_CONTEXT_REFERENCES_BLOCKED_AUTHORITY_REFS,
    RUNTIME_CONTEXT_REFERENCES_CONTRACT_REF,
    RuntimeContextReferencePostureReadModel,
    build_runtime_context_references_read_model,
)


client = TestClient(app)


def test_runtime_context_references_are_safe_ref_preview_only() -> None:
    read_model = build_runtime_context_references_read_model()

    assert read_model.schema_version == "runtime_context_references.v1"
    assert read_model.contract_ref == RUNTIME_CONTEXT_REFERENCES_CONTRACT_REF
    assert read_model.status == "read_only_context_reference_preview"
    assert read_model.route_ref == "GET /api/runtime/context-references"
    assert read_model.cli_ref == "uaa runtime inspect-context-references"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_reason_refs
    assert (
        "adapter-ref:context-references-live-url-fetch:not-implemented"
        in read_model.unsupported_adapter_refs
    )
    assert read_model.reference_count == 11
    assert read_model.included_count == 9
    assert read_model.candidate_count == 1
    assert read_model.blocked_count == 1
    assert read_model.estimated_token_count == 1400
    assert read_model.token_budget_limit == 4000
    assert read_model.token_budget_remaining == 2600
    assert read_model.preview_hash_ref.startswith(
        "snapshot-hash-ref:runtime-context-references:"
    )
    assert read_model.live_url_fetch_enabled is False
    assert read_model.raw_path_persistence_enabled is False
    assert read_model.raw_file_content_persistence_enabled is False
    assert read_model.automatic_context_injection_enabled is False
    assert read_model.hidden_prompt_context_enabled is False
    assert read_model.secret_config_reads_enabled is False
    assert read_model.provider_model_call_enabled is False
    assert read_model.connector_writes_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.browser_automation_enabled is False
    assert read_model.production_authority_enabled is False
    assert (
        "blocked-authority:context-references-no-live-url-fetch"
        in read_model.blocked_authority_refs
    )
    assert read_model.blocked_authority_refs == (
        RUNTIME_CONTEXT_REFERENCES_BLOCKED_AUTHORITY_REFS
    )

    kinds = {ref.ref_kind for ref in read_model.references}
    assert kinds == {
        "file",
        "folder",
        "diff",
        "url_evidence",
        "run",
        "proof",
        "task",
        "memory",
        "crm_object",
        "issue",
    }


def test_runtime_context_reference_items_do_not_fetch_or_inject() -> None:
    read_model = build_runtime_context_references_read_model()

    for ref in read_model.references:
        assert ref.why_included_refs
        assert ref.live_url_fetch_performed is False
        assert ref.raw_path_persisted is False
        assert ref.raw_file_content_persisted is False
        assert ref.raw_prompt_persisted is False
        assert ref.raw_response_persisted is False
        assert ref.raw_provider_payload_persisted is False
        assert ref.secret_config_read_performed is False
        assert ref.automatic_context_injection_performed is False
        assert ref.provider_model_call_performed is False
        assert ref.connector_write_performed is False
        assert ref.shell_execution_performed is False
        assert ref.browser_automation_performed is False
        assert ref.production_authority_performed is False
        assert "/Users/" not in ref.context_ref
        assert "raw_prompt" not in ref.safe_summary.lower()

    blocked = [ref for ref in read_model.references if ref.status == "blocked"]
    assert blocked
    assert blocked[0].preview_available is False
    assert "blocked-authority:context-references-no-protected-config-read" in (
        blocked[0].blocked_authority_refs
    )


@pytest.mark.parametrize(
    "field",
    [
        "live_url_fetch_enabled",
        "raw_path_persistence_enabled",
        "raw_file_content_persistence_enabled",
        "automatic_context_injection_enabled",
        "hidden_prompt_context_enabled",
        "secret_config_reads_enabled",
        "provider_model_call_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "browser_automation_enabled",
        "production_authority_enabled",
    ],
)
def test_runtime_context_references_deny_authority_flags(field: str) -> None:
    payload = build_runtime_context_references_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_CONTEXT_REFERENCES_AUTHORITY_DENIED"):
        RuntimeContextReferencePostureReadModel(**payload)


def test_runtime_context_references_reject_kind_prefix_mismatch() -> None:
    payload = build_runtime_context_references_read_model().model_dump(mode="json")
    payload["references"][0]["context_ref"] = "memory-ref:wrong-kind"

    with pytest.raises(ValueError, match="KIND_PREFIX_MISMATCH"):
        RuntimeContextReferencePostureReadModel(**payload)


def test_runtime_context_references_reject_authority_mapping_drift() -> None:
    payload = build_runtime_context_references_read_model().model_dump(mode="json")
    payload["authority_state_mapping_ref"] = "lane-ref:wrong-context-references"

    with pytest.raises(
        ValueError,
        match="RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_MISMATCH",
    ):
        RuntimeContextReferencePostureReadModel(**payload)


def test_api_runtime_context_references_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/context-references")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_context_references"
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-context-references:phase-16"
    )

    data = body["data"]
    assert data["schema_version"] == "runtime_context_references.v1"
    assert (
        data["authority_state_mapping_ref"]
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["reference_count"] == 11
    assert data["live_url_fetch_enabled"] is False
    assert data["automatic_context_injection_enabled"] is False
    assert data["secret_config_reads_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_provider_payload material" not in serialized


def test_cli_runtime_context_references_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-context-references",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_context_references"]
    authority_state = payload["authority_state"]
    assert (
        authority_state["mapping_ref"]
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_MAPPING_REF
    )
    assert authority_state["decision_outcome"] == "allow"
    assert payload["live_url_fetch_performed"] is False
    assert payload["automatic_context_injection_performed"] is False
    assert payload["secret_config_read_performed"] is False
    assert payload["provider_model_call_performed"] is False
    assert payload["raw_paths_omitted"] is True
    assert payload["raw_file_content_omitted"] is True
    assert read_model["route_ref"] == "GET /api/runtime/context-references"
    assert read_model["cli_ref"] == "uaa runtime inspect-context-references"
    assert (
        read_model["authority_state_cli_ref"]
        == RUNTIME_CONTEXT_REFERENCES_AUTHORITY_STATE_CLI_REF
    )
    assert read_model["reference_count"] == 11
