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
    assert payload["callable_catalog_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["network_access_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["mobile_control_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert "plugin_runtime_import" in payload["blocked_capabilities"]
    assert "arbitrary_plugin_execution" in payload["blocked_capabilities"]
    assert "connector_writes" in payload["blocked_capabilities"]

    reviewed_entry = payload["entries"][0]
    assert reviewed_entry["provenance"]["provenance_status"] == "reviewed"
    assert reviewed_entry["file_hashes"]
    assert all(item["file_ref"].startswith("file-ref:") for item in reviewed_entry["file_hashes"])
    assert reviewed_entry["declared_capabilities"][0]["capability_ref"].startswith("capability:")
    assert reviewed_entry["activation_status"] == "future_scoped"

    blocked_entry = payload["entries"][1]
    assert blocked_entry["provenance"]["provenance_status"] == "unknown"
    assert blocked_entry["blocked_state"] == "unknown"
    assert blocked_entry["activation_status"] == "blocked"
    assert blocked_entry["blocker_refs"]


@pytest.mark.parametrize(
    "field",
    [
        "callable_catalog_enabled",
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
def test_inspectable_extension_catalog_validation_denies_runtime_authority(field: str) -> None:
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
    assert paths["/extensions/catalog"]["get"]["operationId"] == "get_extensions_catalog"
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
    assert schema["properties"]["callable_catalog_enabled"]["const"] is False
    assert schema["properties"]["runtime_import_enabled"]["const"] is False
    assert schema["properties"]["execution_enabled"]["const"] is False
    assert schema["properties"]["connector_writes_enabled"]["const"] is False
