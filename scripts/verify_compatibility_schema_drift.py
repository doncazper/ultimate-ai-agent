#!/usr/bin/env python3
from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def _writeable_model_schema(model: type[Any], *, schema_id: str | None = None) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}
    if schema_id:
        schema = {"$schema": schema["$schema"], "$id": schema_id, **{k: v for k, v in schema.items() if k != "$schema"}}
    return schema


def _assert_schema_matches_model(path: Path, model: type[Any], *, schema_id: str | None = None) -> None:
    actual = _load_json(path)
    expected = _writeable_model_schema(model, schema_id=schema_id)
    if actual != expected:
        _fail_with_diff(path, actual, expected)
    _assert_contract_posture(path, actual, model)


def _assert_contract_posture(path: Path, schema: dict[str, Any], model: type[Any]) -> None:
    relative = path.relative_to(ROOT)
    if schema.get("additionalProperties") is not False:
        _fail(f"{relative} must forbid additional properties")
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        _fail(f"{relative} must define object properties")
    model_fields = {_schema_field_name(field_name, field_info) for field_name, field_info in model.model_fields.items()}
    schema_fields = set(properties)
    if schema_fields != model_fields:
        _fail(f"{relative} property drift: schema={sorted(schema_fields)} model={sorted(model_fields)}")
    required = schema.get("required", [])
    if not isinstance(required, list):
        _fail(f"{relative} required must be a list")
    for field_name, field_info in model.model_fields.items():
        schema_field_name = _schema_field_name(field_name, field_info)
        if field_info.is_required() and schema_field_name not in required:
            _fail(f"{relative} missing required field from model: {schema_field_name}")


def _assert_extension_activation_wrapper(path: Path) -> None:
    from ultimate_ai_agent.core.extension_catalog.contracts import (
        ExtensionActivationGrantRecord,
        ExtensionActivationRevocationRecord,
    )

    schema = _load_json(path)
    relative = path.relative_to(ROOT)
    if schema.get("title") != "uaa_extension_activation_grant":
        _fail(f"{relative} must remain the extension activation wrapper schema")
    if schema.get("additionalProperties") is not False:
        _fail(f"{relative} wrapper must forbid additional properties")
    required = set(schema.get("required", []))
    expected_required = {
        "schema_version",
        "grant_record",
        "revocation_record",
        "runtime_import_enabled",
        "execution_enabled",
        "safe_summary",
    }
    if required != expected_required:
        _fail(f"{relative} wrapper required drift: {sorted(required)}")
    properties = schema.get("properties", {})
    if properties.get("runtime_import_enabled", {}).get("const") is not False:
        _fail(f"{relative} wrapper must keep runtime_import_enabled false")
    if properties.get("execution_enabled", {}).get("const") is not False:
        _fail(f"{relative} wrapper must keep execution_enabled false")

    defs = schema.get("$defs", {})
    grant_def = defs.get("activation_grant_record")
    revocation_def = defs.get("activation_revocation_record")
    if not isinstance(grant_def, dict) or not isinstance(revocation_def, dict):
        _fail(f"{relative} must define grant and revocation wrapper records")
    _assert_wrapper_record_fields(
        relative,
        "activation_grant_record",
        grant_def,
        ExtensionActivationGrantRecord,
    )
    _assert_wrapper_record_fields(
        relative,
        "activation_revocation_record",
        revocation_def,
        ExtensionActivationRevocationRecord,
    )


def _schema_field_name(field_name: str, field_info: Any) -> str:
    return str(field_info.alias or field_name)


def _assert_wrapper_record_fields(
    relative: Path,
    def_name: str,
    record_schema: dict[str, Any],
    model: type[Any],
) -> None:
    if record_schema.get("additionalProperties") is not False:
        _fail(f"{relative} $defs.{def_name} must forbid additional properties")
    properties = record_schema.get("properties", {})
    if not isinstance(properties, dict):
        _fail(f"{relative} $defs.{def_name} must define properties")
    missing_properties = sorted(set(model.model_fields) - set(properties))
    if missing_properties:
        _fail(f"{relative} $defs.{def_name} missing model fields: {missing_properties}")
    required = set(record_schema.get("required", []))
    model_required = {field_name for field_name, field_info in model.model_fields.items() if field_info.is_required()}
    missing_required = sorted(model_required - required)
    if missing_required:
        _fail(f"{relative} $defs.{def_name} must require wrapper fields: {missing_required}")
    for field_name in (
        "runtime_import_enabled",
        "execution_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "mobile_control_enabled",
        "public_distribution_claimed",
    ):
        if field_name in properties and properties[field_name].get("const") is not False:
            _fail(f"{relative} $defs.{def_name}.{field_name} must be const false")


def _fail_with_diff(path: Path, actual: dict[str, Any], expected: dict[str, Any]) -> None:
    actual_text = json.dumps(actual, indent=2, sort_keys=True).splitlines()
    expected_text = json.dumps(expected, indent=2, sort_keys=True).splitlines()
    diff = "\n".join(
        difflib.unified_diff(
            actual_text,
            expected_text,
            fromfile=f"{path.relative_to(ROOT)} (checked-in)",
            tofile=f"{path.relative_to(ROOT)} (live-model)",
            lineterm="",
        )
    )
    _fail(f"{path.relative_to(ROOT)} does not match live model schema:\n{diff}")


def _fail(message: str) -> None:
    raise SystemExit(f"Compatibility schema drift verification failed: {message}")


def main() -> None:
    from ultimate_ai_agent.core.adapters import A2AAgentCardV1, AgentRuntimeAdapterManifest, UAAA2AAgentCardMetadataImport
    from ultimate_ai_agent.core.providers import ProviderManifest

    _assert_schema_matches_model(
        ROOT / "docs/schemas/a2a_agent_card_minimal.schema.json",
        UAAA2AAgentCardMetadataImport,
    )
    _assert_schema_matches_model(
        ROOT / "docs/schemas/a2a_agent_card_v1.schema.json",
        A2AAgentCardV1,
    )
    _assert_schema_matches_model(
        ROOT / "docs/schemas/agent_runtime_adapter_manifest.schema.json",
        AgentRuntimeAdapterManifest,
    )
    _assert_schema_matches_model(
        ROOT / "docs/schemas/provider_manifest.schema.json",
        ProviderManifest,
        schema_id="https://ultimate-ai-agent.local/schemas/provider_manifest.schema.json",
    )
    _assert_extension_activation_wrapper(ROOT / "docs/schemas/extension_activation_grant.schema.json")
    print("Compatibility schema drift verification passed")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
