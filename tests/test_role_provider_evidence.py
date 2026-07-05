from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV
from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.providers.role_evidence import (
    ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CONTRACT_REF,
    ModelProviderRole,
    RoleBasedModelProviderEvidenceReadModel,
)


LOCAL_TEST_BEARER = "role-provider-evidence-local-bearer"


def test_role_provider_evidence_covers_agent_roles_without_invocation() -> None:
    evidence = build_model_provider_control_plane_read_model().role_provider_evidence

    assert evidence.schema_version == "role_based_model_provider_evidence.v1"
    assert evidence.contract_ref == ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CONTRACT_REF
    assert evidence.status == "advisory_evidence_only"
    assert evidence.role_count == len(ModelProviderRole)
    assert {item.role for item in evidence.role_evidence} == set(ModelProviderRole)
    assert evidence.advisory_only is True
    assert evidence.provider_sdk_call_enabled is False
    assert evidence.remote_model_call_enabled is False
    assert evidence.local_model_call_performed is False
    assert evidence.model_invocation_performed is False
    assert evidence.provider_payload_persisted is False
    assert evidence.provider_output_authoritative is False


def test_role_provider_evidence_selects_local_advisory_and_blocks_remote() -> None:
    evidence = build_model_provider_control_plane_read_model().role_provider_evidence

    for role in evidence.role_evidence:
        selected = [
            candidate
            for candidate in role.candidates
            if candidate.candidate_ref == role.selected_candidate_ref
        ][0]
        assert selected.local_remote_posture == "local_loopback"
        assert selected.selected_for_role is True
        assert selected.model_invocation_performed is False
        assert selected.provider_sdk_call_performed is False
        remote_candidates = [
            candidate
            for candidate in role.candidates
            if candidate.local_remote_posture == "remote_provider_reference"
        ]
        assert remote_candidates
        assert all(
            candidate.authority_status == "remote_provider_blocked"
            for candidate in remote_candidates
        )
        assert all(candidate.authority_adjusted_score == 0 for candidate in remote_candidates)
        assert all(
            "REMOTE_PROVIDER_AUTHORITY_BLOCKED" in candidate.reason_codes
            for candidate in remote_candidates
        )
        assert role.remote_provider_candidates_blocked is True
        assert role.no_invocation_authorized is True


def test_role_provider_evidence_rejects_authority_drift() -> None:
    evidence = build_model_provider_control_plane_read_model().role_provider_evidence
    payload = evidence.model_dump(mode="python")
    payload["provider_sdk_call_enabled"] = True

    with pytest.raises(ValidationError, match="ROLE_PROVIDER_EVIDENCE_AUTHORITY_DENIED"):
        RoleBasedModelProviderEvidenceReadModel.model_validate(payload)

    payload = evidence.model_dump(mode="python")
    payload["role_evidence"][0]["candidates"][1]["model_invocation_performed"] = True

    with pytest.raises(ValidationError, match="ROLE_PROVIDER_CANDIDATE_AUTHORITY_DENIED"):
        RoleBasedModelProviderEvidenceReadModel.model_validate(payload)

    payload = evidence.model_dump(mode="python")
    remote_candidate = payload["role_evidence"][0]["candidates"][1]
    payload["role_evidence"][0]["selected_candidate_ref"] = remote_candidate["candidate_ref"]
    remote_candidate["selected_for_role"] = True

    with pytest.raises(ValidationError, match="ROLE_PROVIDER_CANDIDATE_REMOTE_SELECTION_DENIED"):
        RoleBasedModelProviderEvidenceReadModel.model_validate(payload)


def test_role_provider_evidence_is_visible_in_control_center_api(monkeypatch) -> None:
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    client = TestClient(app)

    response = client.get(
        "/control-center/providers/runtime-control-plane",
        headers={"Authorization": f"Bearer {LOCAL_TEST_BEARER}"},
    )

    assert response.status_code == 200
    body = response.json()
    evidence = body["data"]["role_provider_evidence"]
    assert evidence["schema_version"] == "role_based_model_provider_evidence.v1"
    assert evidence["role_count"] == len(ModelProviderRole)
    assert evidence["provider_sdk_call_enabled"] is False
    assert evidence["model_invocation_performed"] is False
    assert "raw_prompt_response_provider_payload_omitted" in body["redactions_applied"]


def test_role_provider_evidence_cli_uses_same_safe_schema() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-role-provider-evidence",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    evidence = payload["role_provider_evidence"]

    assert payload["safe_refs_only"] is True
    assert payload["execution_performed"] is False
    assert payload["provider_model_call_performed"] is False
    assert evidence["role_count"] == len(ModelProviderRole)
    assert evidence["provider_sdk_call_enabled"] is False
    assert evidence["remote_model_call_enabled"] is False
    assert "raw prompt" not in result.stdout.lower()
    assert "raw response" not in result.stdout.lower()
    assert "provider payload content" not in result.stdout.lower()
    assert "sk-" not in result.stdout.lower()
