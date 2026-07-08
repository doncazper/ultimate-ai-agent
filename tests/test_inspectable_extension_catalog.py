import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    validate_inspectable_extension_catalog,
)


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_default_inspectable_extension_catalog_is_read_only_and_non_callable() -> None:
    catalog = build_default_inspectable_extension_catalog()
    payload = catalog.model_dump(mode="json")

    assert payload["schema_version"] == "uaa_inspectable_extension_catalog.v1"
    assert payload["catalog_status"] == "read_only_inspection"
    assert payload["read_only"] is True
    assert payload["inspectable_catalog_enabled"] is True
    assert payload["progressive_disclosure_enabled"] is True
    assert payload["metadata_first_index_enabled"] is True
    assert payload["callable_catalog_enabled"] is False
    assert payload["automatic_instruction_loading_enabled"] is False
    assert payload["full_instruction_auto_load_enabled"] is False
    assert payload["hidden_skill_activation_enabled"] is False
    assert payload["skill_runtime_import_enabled"] is False
    assert payload["external_marketplace_fetch_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["network_access_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["mobile_control_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert "plugin_runtime_import" in payload["blocked_capabilities"]
    assert "automatic_skill_instruction_loading" in payload["blocked_capabilities"]
    assert "hidden_skill_activation" in payload["blocked_capabilities"]
    assert "external_marketplace_fetch" in payload["blocked_capabilities"]
    assert "arbitrary_plugin_execution" in payload["blocked_capabilities"]
    assert "connector_writes" in payload["blocked_capabilities"]
    assert (
        "compact-skill-index:uaa-owned-progressive-disclosure"
        in payload["compact_skill_index_refs"]
    )
    assert (
        "progressive-disclosure:metadata-first-index"
        in payload["progressive_disclosure_refs"]
    )
    assert payload["skill_write_approval_gate"]["status"] == "staged_review_only"
    assert payload["skill_write_approval_gate"]["file_write_enabled"] is False
    assert payload["skill_bundle_proposal_posture"]["status"] == "proposal_only"
    assert payload["skill_bundle_proposal_posture"]["proposal_count"] == 1
    assert (
        payload["skill_bundle_proposal_posture"]["bundle_activation_enabled"] is False
    )
    assert payload["skill_bundle_proposal_posture"]["tool_execution_enabled"] is False
    assert "doc:runtime-extensibility-final" in payload["docs_refs"]
    assert "doc:hermes-runtime-progressive-skill-disclosure" in payload["docs_refs"]
    assert "doc:hermes-runtime-skill-bundle-proposals" in payload["docs_refs"]
    assert (
        "doc:runtime-extensibility-final"
        in payload["developer_guidance_refs"]
    )
    assert (
        "verifier:runtime-extensibility-final"
        in payload["final_hardening_refs"]
    )

    reviewed_entry = payload["entries"][0]
    assert reviewed_entry["compact_skill_index_ref"].startswith("compact-skill-index:")
    assert reviewed_entry["metadata_summary_ref"].startswith("skill-metadata:")
    assert reviewed_entry["provenance"]["provenance_status"] == "reviewed"
    assert reviewed_entry["file_hashes"]
    assert all(
        item["file_ref"].startswith("file-ref:")
        for item in reviewed_entry["file_hashes"]
    )
    assert reviewed_entry["declared_capabilities"][0]["capability_ref"].startswith(
        "capability:"
    )
    assert reviewed_entry["activation_status"] == "future_scoped"
    assert reviewed_entry["visibility_status"] == "implemented"
    assert reviewed_entry["trust_posture"] == "reviewed_metadata"
    assert reviewed_entry["callable_posture"] == "inspectable_only"
    assert reviewed_entry["required_grant_refs"] == [
        "grant-request:extension-metadata-inspection"
    ]
    assert reviewed_entry["review_evidence_refs"]
    assert reviewed_entry["safe_adoption_posture"] == "repo_owned_metadata_only"
    assert reviewed_entry["progressive_disclosure_status"] == "metadata_indexed"
    assert (
        reviewed_entry["full_instruction_load_posture"]
        == "operator_selected_review_required"
    )
    assert reviewed_entry["metadata_first"] is True
    assert reviewed_entry["operator_selected_before_full_instruction"] is True
    assert reviewed_entry["automatic_instruction_loading_enabled"] is False
    assert reviewed_entry["hidden_activation_enabled"] is False
    assert "runtime import" in reviewed_entry["blocked_reason"]

    skill_entry = payload["entries"][1]
    assert skill_entry["package_identity"]["package_kind"] == "skill"
    assert skill_entry["progressive_disclosure_status"] == "metadata_indexed"
    assert skill_entry["callable_posture"] == "inspectable_only"
    assert skill_entry["trust_posture"] == "reviewed_metadata"
    assert skill_entry["metadata_first"] is True
    assert skill_entry["operator_selected_before_full_instruction"] is True
    assert skill_entry["automatic_instruction_loading_enabled"] is False
    assert skill_entry["hidden_activation_enabled"] is False
    assert "full instruction loading" in skill_entry["blocked_reason"]

    blocked_entry = payload["entries"][2]
    assert blocked_entry["provenance"]["provenance_status"] == "unknown"
    assert blocked_entry["blocked_state"] == "unknown"
    assert blocked_entry["activation_status"] == "blocked"
    assert blocked_entry["blocker_refs"]
    assert blocked_entry["visibility_status"] == "blocked"
    assert blocked_entry["trust_posture"] == "unknown_blocked"
    assert blocked_entry["callable_posture"] == "blocked_runtime"
    assert blocked_entry["required_grant_refs"] == ["grant-request:unknown-runtime"]
    assert blocked_entry["safe_adoption_posture"] == "blocked_until_scoped_milestone"
    assert blocked_entry["progressive_disclosure_status"] == "blocked"
    assert blocked_entry["full_instruction_load_posture"] == "blocked_runtime_import"


@pytest.mark.parametrize(
    "field",
    [
        "callable_catalog_enabled",
        "automatic_instruction_loading_enabled",
        "full_instruction_auto_load_enabled",
        "hidden_skill_activation_enabled",
        "skill_runtime_import_enabled",
        "external_marketplace_fetch_enabled",
        "runtime_import_enabled",
        "execution_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "mobile_control_enabled",
        "public_distribution_claimed",
    ],
)
def test_inspectable_extension_catalog_validation_denies_runtime_authority(
    field: str,
) -> None:
    catalog = build_default_inspectable_extension_catalog().model_copy(
        update={field: True}
    )

    with pytest.raises(ValueError, match=f"EXTENSION_CATALOG_{field.upper()}_DENIED"):
        validate_inspectable_extension_catalog(catalog)


def test_extension_catalog_route_returns_safe_read_only_metadata() -> None:
    response = client.get("/extensions/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "inspect_extension_catalog"
    assert body["service"] == "ExtensionCatalogAPI"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "raw_package_content_omitted",
    ]

    catalog = body["data"]
    assert catalog["callable_catalog_enabled"] is False
    assert catalog["runtime_import_enabled"] is False
    assert catalog["execution_enabled"] is False
    catalog_text = json.dumps(catalog).lower()
    assert "/users/" not in catalog_text
    assert "docs/" not in catalog_text
    assert "raw_prompt" not in catalog_text
    assert "raw_provider_payload" not in catalog_text


def test_extension_catalog_openapi_route_is_get_only_and_not_runtime_catalog() -> None:
    paths = app.openapi()["paths"]

    assert "/extensions/catalog" in paths
    assert sorted(paths["/extensions/catalog"].keys()) == ["get"]
    assert (
        paths["/extensions/catalog"]["get"]["operationId"] == "get_extensions_catalog"
    )
    for forbidden in [
        "/extensions/catalog/execute",
        "/extensions/catalog/import",
        "/extensions/catalog/activate",
        "/extensions/catalog/revoke",
        "/extensions/catalog/apply",
        "/extensions/catalog/install",
    ]:
        assert forbidden not in paths


def test_inspectable_extension_catalog_schema_pins_disabled_runtime_fields() -> None:
    schema = json.loads(
        (ROOT / "docs/schemas/inspectable_extension_catalog.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["title"] == "uaa_inspectable_extension_catalog"
    assert schema["properties"]["catalog_status"]["const"] == "read_only_inspection"
    assert schema["properties"]["read_only"]["const"] is True
    assert schema["properties"]["progressive_disclosure_enabled"]["const"] is True
    assert schema["properties"]["metadata_first_index_enabled"]["const"] is True
    assert schema["properties"]["callable_catalog_enabled"]["const"] is False
    assert (
        schema["properties"]["automatic_instruction_loading_enabled"]["const"] is False
    )
    assert schema["properties"]["full_instruction_auto_load_enabled"]["const"] is False
    assert schema["properties"]["hidden_skill_activation_enabled"]["const"] is False
    assert schema["properties"]["skill_runtime_import_enabled"]["const"] is False
    assert schema["properties"]["external_marketplace_fetch_enabled"]["const"] is False
    assert schema["properties"]["runtime_import_enabled"]["const"] is False
    assert schema["properties"]["execution_enabled"]["const"] is False
    assert schema["properties"]["connector_writes_enabled"]["const"] is False
    entry = schema["$defs"]["catalog_entry"]
    for field in [
        "visibility_status",
        "trust_posture",
        "callable_posture",
        "compact_skill_index_ref",
        "metadata_summary_ref",
        "required_grant_refs",
        "blocked_reason",
        "review_evidence_refs",
        "safe_adoption_posture",
        "progressive_disclosure_status",
        "full_instruction_load_posture",
        "metadata_first",
        "operator_selected_before_full_instruction",
        "automatic_instruction_loading_enabled",
        "hidden_activation_enabled",
    ]:
        assert field in entry["required"]
        assert field in entry["properties"]
    assert "skill_write_approval_gate" in schema["required"]
    assert "skill_bundle_proposal_posture" in schema["required"]
    gate = schema["$defs"]["skill_write_approval_gate"]
    assert gate["properties"]["status"]["const"] == "staged_review_only"
    assert gate["properties"]["file_write_enabled"]["const"] is False
    assert gate["properties"]["runtime_import_enabled"]["const"] is False
    posture = schema["$defs"]["skill_bundle_proposal_posture"]
    assert posture["properties"]["status"]["const"] == "proposal_only"
    assert posture["properties"]["bundle_activation_enabled"]["const"] is False
    assert posture["properties"]["tool_execution_enabled"]["const"] is False
