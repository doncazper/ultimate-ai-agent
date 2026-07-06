from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    validate_inspectable_extension_catalog,
)


client = TestClient(app)


def test_progressive_skill_disclosure_is_metadata_first_and_non_callable() -> None:
    catalog = build_default_inspectable_extension_catalog().model_dump(mode="json")

    assert catalog["progressive_disclosure_enabled"] is True
    assert catalog["metadata_first_index_enabled"] is True
    assert catalog["automatic_instruction_loading_enabled"] is False
    assert catalog["full_instruction_auto_load_enabled"] is False
    assert catalog["hidden_skill_activation_enabled"] is False
    assert catalog["skill_runtime_import_enabled"] is False
    assert catalog["external_marketplace_fetch_enabled"] is False
    assert (
        "compact-skill-index:uaa-owned-progressive-disclosure"
        in catalog["compact_skill_index_refs"]
    )

    skill_entries = [
        entry
        for entry in catalog["entries"]
        if entry["package_identity"]["package_kind"] == "skill"
    ]
    assert skill_entries
    skill = skill_entries[0]
    assert skill["progressive_disclosure_status"] == "metadata_indexed"
    assert skill["full_instruction_load_posture"] == (
        "operator_selected_review_required"
    )
    assert skill["metadata_first"] is True
    assert skill["operator_selected_before_full_instruction"] is True
    assert skill["automatic_instruction_loading_enabled"] is False
    assert skill["hidden_activation_enabled"] is False
    assert skill["callable_posture"] == "inspectable_only"
    assert skill["safe_adoption_posture"] == "repo_owned_metadata_only"


@pytest.mark.parametrize(
    "field",
    [
        "automatic_instruction_loading_enabled",
        "full_instruction_auto_load_enabled",
        "hidden_skill_activation_enabled",
        "skill_runtime_import_enabled",
        "external_marketplace_fetch_enabled",
    ],
)
def test_progressive_skill_disclosure_denies_broad_root_authority(field: str) -> None:
    catalog = build_default_inspectable_extension_catalog().model_copy(
        update={field: True}
    )

    with pytest.raises(ValueError, match="EXTENSION_CATALOG_.*_DENIED"):
        validate_inspectable_extension_catalog(catalog)


def test_progressive_skill_disclosure_denies_hidden_entry_loading() -> None:
    catalog = build_default_inspectable_extension_catalog()
    entries = [entry.model_copy() for entry in catalog.entries]
    entries[1] = entries[1].model_copy(
        update={"automatic_instruction_loading_enabled": True}
    )
    unsafe = catalog.model_copy(update={"entries": entries})

    with pytest.raises(ValueError, match="AUTO_INSTRUCTION_LOAD_DENIED"):
        validate_inspectable_extension_catalog(unsafe)


def test_extension_catalog_api_and_cli_expose_progressive_skill_metadata() -> None:
    response = client.get("/extensions/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    catalog = body["data"]
    assert catalog["progressive_disclosure_enabled"] is True
    assert catalog["skill_runtime_import_enabled"] is False
    assert "raw_prompt" not in json.dumps(catalog).lower()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_catalog = json.loads(result.stdout)
    assert cli_catalog["progressive_disclosure_enabled"] is True
    assert cli_catalog["full_instruction_auto_load_enabled"] is False
    assert any(
        entry["package_identity"]["package_kind"] == "skill"
        for entry in cli_catalog["entries"]
    )
