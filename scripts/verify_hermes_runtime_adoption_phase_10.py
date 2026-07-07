#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_REF,
    RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_CLI_REF,
    RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_TOOL_REGISTRY_ROUTE_REF,
    build_runtime_tool_registry_availability_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_tool_authority(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden_fragments = [
        '"uaa_allows_invocation": true',
        '"execution_enabled": true',
        '"tool_invocation_enabled": true',
        '"remote_discovery_enabled": true',
        '"remote_discovery_performed": true',
        '"live_web_fetch_enabled": true',
        '"live_web_fetch_performed": true',
        '"provider_model_call_enabled": true',
        '"provider_model_call_performed": true',
        '"plugin_import_enabled": true',
        '"connector_write_activation_enabled": true',
        '"raw_tool_payload_persisted": true',
        '"production_authority_enabled": true',
    ]
    for fragment in forbidden_fragments:
        if fragment in serialized:
            _fail(f"forbidden tool registry authority flag present: {fragment}")


def _assert_registry(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "runtime_tool_registry_availability.v1":
        _fail("tool registry schema drifted")
    if payload.get("status") != "read_only_tool_registry_availability":
        _fail("tool registry must stay read-only")
    if payload.get("route_ref") != RUNTIME_TOOL_REGISTRY_ROUTE_REF:
        _fail("tool registry route ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("tool registry AuthorityState route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_CLI_REF
    ):
        _fail("tool registry AuthorityState CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_REF
    ):
        _fail("tool registry AuthorityState mapping drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("tool registry AuthorityState decision must allow read")
    if payload.get("authority_state_status") != "implemented_authority_bound_read_model":
        _fail("tool registry AuthorityState status drifted")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        payload.get("authority_state_reason_refs") or []
    ):
        _fail("tool registry AuthorityState reason missing")
    if "adapter-ref:runtime-tool-invocation:not-implemented" not in (
        payload.get("unsupported_adapter_refs") or []
    ):
        _fail("tool registry unsupported adapter refs missing")
    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) != 12:
        _fail("tool registry must expose twelve entries")
    if payload.get("tool_count") != len(entries):
        _fail("tool registry count drifted")
    if payload.get("invocation_enabled_count") != 0:
        _fail("tool invocation was granted")
    if payload.get("preview_available_count") != 4:
        _fail("UAA-native preview count drifted")
    statuses = {
        entry.get("availability_status") for entry in entries if isinstance(entry, dict)
    }
    if statuses != {
        "available_metadata_only",
        "configured_disabled",
        "approval_required_future_lane",
        "blocked",
        "unsupported",
    }:
        _fail("availability statuses are incomplete")
    high_authority_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("authority_class") == "blocked_high_authority"
    ]
    if not high_authority_entries:
        _fail("high-authority registry entries missing")
    for flag in [
        "tool_invocation_enabled",
        "remote_discovery_enabled",
        "live_web_fetch_enabled",
        "provider_model_call_enabled",
        "plugin_import_enabled",
        "connector_write_activation_enabled",
        "raw_tool_payload_persisted",
        "production_authority_enabled",
    ]:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    for entry in entries:
        if not isinstance(entry, dict):
            _fail("tool registry entry is invalid")
        for flag in [
            "uaa_allows_invocation",
            "execution_enabled",
            "remote_discovery_performed",
            "live_web_fetch_performed",
            "provider_model_call_performed",
            "plugin_import_enabled",
            "connector_write_activation_enabled",
            "raw_tool_payload_persisted",
        ]:
            if entry.get(flag) is not False:
                _fail(f"entry {entry.get('tool_ref')} enabled {flag}")
        if not entry.get("blocked_authority_refs"):
            _fail(f"entry {entry.get('tool_ref')} blockers missing")
        if not entry.get("next_safe_action_refs"):
            _fail(f"entry {entry.get('tool_ref')} next safe action missing")
    for entry in high_authority_entries:
        if "blocked-authority:runtime-tool-registry-high-authority" not in (
            entry.get("blocked_authority_refs") or []
        ):
            _fail(f"high authority blocker missing for {entry.get('tool_ref')}")
    if "proof-ref:hermes-runtime-adoption:phase-10:tool-registry" not in (
        payload.get("proof_refs") or []
    ):
        _fail("phase 10 proof ref missing")


def main() -> None:
    read_model = build_runtime_tool_registry_availability_read_model()
    core_payload = read_model.model_dump(mode="json")
    _assert_registry(core_payload)
    _assert_no_tool_authority(core_payload)

    client = TestClient(app)
    response = client.get("/api/runtime/tool-registry")
    if response.status_code != 200:
        _fail(f"tool registry route returned {response.status_code}")
    body = response.json()
    api_payload = body.get("data")
    if not isinstance(api_payload, dict):
        _fail("tool registry route did not return data")
    _assert_registry(api_payload)
    _assert_no_tool_authority(api_payload)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-tool-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    read_model_payload = cli_payload.get("runtime_tool_registry")
    if not isinstance(read_model_payload, dict):
        _fail("CLI did not return runtime tool registry data")
    _assert_registry(read_model_payload)
    _assert_no_tool_authority(read_model_payload)
    print("Hermes Runtime Adoption Phase 10 tool registry verification passed.")


if __name__ == "__main__":
    main()
