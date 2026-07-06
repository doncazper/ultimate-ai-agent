from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    build_default_skill_bundle_proposal_posture,
    validate_skill_bundle_proposal_posture,
)


client = TestClient(app)


def test_skill_bundle_proposal_posture_is_metadata_only() -> None:
    posture = build_default_skill_bundle_proposal_posture()
    payload = posture.model_dump(mode="json")

    assert payload["schema_version"] == "uaa_skill_bundle_proposal_posture.v1"
    assert payload["status"] == "proposal_only"
    assert payload["proposal_count"] == 1
    assert payload["bundle_activation_enabled"] is False
    assert payload["skill_enablement_enabled"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["context_injection_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["production_authority_enabled"] is False
    assert "blocked-authority:skill-bundle-no-activation" in payload[
        "blocked_authority_refs"
    ]

    proposal = payload["proposals"][0]
    assert proposal["proposal_status"] == "proposal_only"
    assert proposal["skill_refs"]
    assert proposal["context_pack_refs"]
    assert proposal["toolset_refs"]
    assert proposal["verification_refs"]
    assert proposal["blocked_authority_refs"]
    assert proposal["activation_performed"] is False
    assert proposal["skill_enablement_performed"] is False
    assert proposal["tool_execution_performed"] is False
    assert proposal["context_injection_performed"] is False
    assert proposal["runtime_import_performed"] is False
    assert proposal["provider_model_call_performed"] is False
    assert proposal["connector_write_performed"] is False
    assert proposal["shell_execution_performed"] is False
    assert proposal["browser_automation_performed"] is False
    assert proposal["production_authority_performed"] is False


@pytest.mark.parametrize(
    "field",
    [
        "bundle_activation_enabled",
        "skill_enablement_enabled",
        "tool_execution_enabled",
        "context_injection_enabled",
        "runtime_import_enabled",
        "provider_model_call_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "browser_automation_enabled",
        "production_authority_enabled",
    ],
)
def test_skill_bundle_posture_denies_runtime_authority(field: str) -> None:
    posture = build_default_skill_bundle_proposal_posture().model_copy(
        update={field: True}
    )

    with pytest.raises(ValueError, match="SKILL_BUNDLE_POSTURE_.*_DENIED"):
        validate_skill_bundle_proposal_posture(posture)


def test_skill_bundle_posture_denies_proposal_side_effect_claims() -> None:
    posture = build_default_skill_bundle_proposal_posture()
    proposal = posture.proposals[0].model_copy(
        update={"tool_execution_performed": True}
    )
    unsafe = posture.model_copy(update={"proposals": [proposal]})

    with pytest.raises(ValueError, match="SKILL_BUNDLE_PROPOSAL_.*_DENIED"):
        validate_skill_bundle_proposal_posture(unsafe)


def test_extension_catalog_api_and_cli_expose_skill_bundle_posture() -> None:
    response = client.get("/extensions/catalog")

    assert response.status_code == 200
    catalog = response.json()["data"]
    posture = catalog["skill_bundle_proposal_posture"]
    assert posture["status"] == "proposal_only"
    assert posture["bundle_activation_enabled"] is False
    assert posture["tool_execution_enabled"] is False

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-skill-bundles",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_posture = json.loads(result.stdout)
    assert cli_posture["status"] == "proposal_only"
    assert cli_posture["proposal_count"] == 1
    assert "raw_prompt" not in result.stdout.lower()
    assert "raw_provider_payload" not in result.stdout.lower()


def test_extension_catalog_embeds_same_skill_bundle_posture() -> None:
    catalog = build_default_inspectable_extension_catalog().model_dump(mode="json")
    posture = build_default_skill_bundle_proposal_posture().model_dump(mode="json")

    assert catalog["skill_bundle_proposal_posture"] == posture
