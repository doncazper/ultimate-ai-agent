from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    build_default_skill_write_approval_gate,
    validate_skill_write_approval_gate,
)


client = TestClient(app)


def test_skill_write_approval_gate_is_staged_review_only() -> None:
    gate = build_default_skill_write_approval_gate()
    payload = gate.model_dump(mode="json")

    assert payload["schema_version"] == "uaa_skill_write_approval_gate.v1"
    assert payload["status"] == "staged_review_only"
    assert payload["proposal_count"] == 1
    assert payload["file_write_enabled"] is False
    assert payload["direct_skill_write_enabled"] is False
    assert payload["skill_enablement_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["production_authority_enabled"] is False
    assert (
        "blocked-authority:skill-write-no-direct-file-write"
        in payload["blocked_authority_refs"]
    )

    proposal = payload["proposals"][0]
    assert proposal["review_status"] == "awaiting_operator_review"
    assert proposal["diff_previews"]
    assert proposal["file_write_performed"] is False
    assert proposal["skill_enablement_performed"] is False
    assert proposal["runtime_import_performed"] is False
    assert proposal["execution_performed"] is False
    assert proposal["raw_instruction_body_persisted"] is False
    assert proposal["blocked_execution_labels"]
    assert proposal["proof_refs"]
    assert proposal["diff_previews"][0]["raw_diff_persisted"] is False
    assert proposal["diff_previews"][0]["raw_file_content_persisted"] is False


@pytest.mark.parametrize(
    "field",
    [
        "file_write_enabled",
        "direct_skill_write_enabled",
        "skill_enablement_enabled",
        "runtime_import_enabled",
        "execution_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "provider_model_call_enabled",
        "browser_automation_enabled",
        "production_authority_enabled",
    ],
)
def test_skill_write_approval_gate_denies_broad_authority(field: str) -> None:
    gate = build_default_skill_write_approval_gate().model_copy(update={field: True})

    with pytest.raises(ValueError, match="SKILL_WRITE_GATE_.*_DENIED"):
        validate_skill_write_approval_gate(gate)


def test_skill_write_approval_gate_denies_proposal_side_effect_claims() -> None:
    gate = build_default_skill_write_approval_gate()
    proposal = gate.proposals[0].model_copy(update={"file_write_performed": True})
    unsafe = gate.model_copy(update={"proposals": [proposal]})

    with pytest.raises(ValueError, match="SKILL_WRITE_PROPOSAL_.*_DENIED"):
        validate_skill_write_approval_gate(unsafe)


def test_extension_catalog_api_and_cli_expose_skill_write_gate() -> None:
    response = client.get("/extensions/catalog")

    assert response.status_code == 200
    catalog = response.json()["data"]
    assert catalog["skill_write_approval_gate"]["status"] == "staged_review_only"
    assert catalog["skill_write_approval_gate"]["file_write_enabled"] is False

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-skill-write-gate",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    gate = json.loads(result.stdout)
    assert gate["status"] == "staged_review_only"
    assert gate["proposal_count"] == 1
    assert "raw_prompt" not in result.stdout.lower()
    assert "raw_provider_payload" not in result.stdout.lower()


def test_extension_catalog_embeds_same_skill_write_gate() -> None:
    catalog = build_default_inspectable_extension_catalog().model_dump(mode="json")
    gate = build_default_skill_write_approval_gate().model_dump(mode="json")

    assert catalog["skill_write_approval_gate"] == gate
