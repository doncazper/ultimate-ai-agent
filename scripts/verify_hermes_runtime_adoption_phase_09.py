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
    RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_MAPPING_REF,
    RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_STATE_CLI_REF,
    RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF,
    build_runtime_capability_discovery_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_toolset_authority(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden_fragments = [
        '"uaa_allows_execution": true',
        '"tool_invocation_enabled": true',
        '"live_tool_invocation_enabled": true',
        '"toolset_config_mutation_enabled": true',
        '"hermes_toolset_enablement_enabled": true',
        '"raw_tool_payload_persisted": true',
        '"production_authority_enabled": true',
    ]
    for fragment in forbidden_fragments:
        if fragment in serialized:
            _fail(f"forbidden toolset authority flag present: {fragment}")


def _assert_toolset_posture(payload: dict[str, Any]) -> None:
    posture = payload.get("toolset_posture")
    if not isinstance(posture, dict):
        _fail("toolset posture missing")
    if posture.get("schema_version") != "runtime_toolset_capability_posture.v1":
        _fail("toolset posture schema drifted")
    if posture.get("status") != "read_only_toolset_capability_posture":
        _fail("toolset posture is not read-only")
    records = posture.get("records")
    if not isinstance(records, list) or len(records) != 8:
        _fail("toolset posture must expose eight toolsets")
    if posture.get("toolset_count") != len(records):
        _fail("toolset count drifted")
    if posture.get("runtime_supported_count") != sum(
        1 for record in records if record.get("runtime_supports_toolset")
    ):
        _fail("runtime supported count drifted")
    if posture.get("uaa_allowed_execution_count") != 0:
        _fail("UAA toolset execution was granted")
    required_allowance_states = {
        "enabled_read_only",
        "configured_metadata_only",
        "approval_required_future_lane",
        "blocked",
        "unsupported",
    }
    actual_allowance_states = {
        record.get("uaa_allowance_status")
        for record in records
        if isinstance(record, dict)
    }
    if actual_allowance_states != required_allowance_states:
        _fail("toolset allowance states are incomplete")
    high_authority_refs = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("side_effect_class") == "high_authority"
    ]
    if not high_authority_refs:
        _fail("high authority toolsets missing")
    for flag in [
        "live_tool_invocation_enabled",
        "toolset_config_mutation_enabled",
        "hermes_toolset_enablement_enabled",
        "raw_tool_payload_persisted",
        "production_authority_enabled",
    ]:
        if posture.get(flag) is not False:
            _fail(f"{flag} must remain false")
    for record in records:
        if not isinstance(record, dict):
            _fail("toolset record is invalid")
        for flag in [
            "uaa_allows_execution",
            "tool_invocation_enabled",
            "toolset_config_mutation_enabled",
            "hermes_toolset_enablement_enabled",
            "raw_tool_payload_persisted",
        ]:
            if record.get(flag) is not False:
                _fail(f"record {record.get('toolset_ref')} enabled {flag}")
        if not record.get("blocked_authority_refs"):
            _fail(f"record {record.get('toolset_ref')} blockers missing")
        if not record.get("next_safe_action_refs"):
            _fail(f"record {record.get('toolset_ref')} next action missing")
    for record in high_authority_refs:
        if "blocked-authority:runtime-high-authority-toolset" not in (
            record.get("blocked_authority_refs") or []
        ):
            _fail(f"high authority blocker missing for {record.get('toolset_ref')}")
    if "proof-ref:hermes-runtime-adoption:phase-09:toolsets" not in (
        posture.get("proof_refs") or []
    ):
        _fail("phase 09 proof ref missing")
    if "blocked-authority:runtime-toolset-invocation" not in (
        posture.get("blocked_authority_refs") or []
    ):
        _fail("toolset invocation blocker missing")


def _assert_authority_state(payload: dict[str, Any]) -> None:
    if payload.get("route_ref") != RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF:
        _fail("capability discovery route ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("capability discovery AuthorityState route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_STATE_CLI_REF
    ):
        _fail("capability discovery AuthorityState CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_CAPABILITY_DISCOVERY_AUTHORITY_MAPPING_REF
    ):
        _fail("capability discovery AuthorityState mapping drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("capability discovery AuthorityState decision must allow read")
    if (
        payload.get("authority_state_status")
        != "implemented_authority_bound_read_model"
    ):
        _fail("capability discovery AuthorityState status drifted")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        payload.get("authority_state_reason_refs") or []
    ):
        _fail("capability discovery AuthorityState reason missing")
    if "adapter-ref:runtime-tool-invocation:not-implemented" not in (
        payload.get("unsupported_adapter_refs") or []
    ):
        _fail("capability discovery unsupported adapter refs missing")


def main() -> None:
    read_model = build_runtime_capability_discovery_read_model()
    core_payload = read_model.model_dump(mode="json")
    _assert_authority_state(core_payload)
    _assert_toolset_posture(core_payload)
    _assert_no_toolset_authority(core_payload)

    client = TestClient(app)
    response = client.get("/api/runtime/capability-discovery")
    if response.status_code != 200:
        _fail(f"capability discovery route returned {response.status_code}")
    body = response.json()
    api_payload = body.get("data")
    if not isinstance(api_payload, dict):
        _fail("capability discovery route did not return data")
    _assert_authority_state(api_payload)
    _assert_toolset_posture(api_payload)
    _assert_no_toolset_authority(api_payload)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-capability-discovery",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    read_model_payload = cli_payload.get("runtime_capability_discovery")
    if not isinstance(read_model_payload, dict):
        _fail("CLI did not return runtime capability discovery data")
    _assert_authority_state(read_model_payload)
    _assert_toolset_posture(read_model_payload)
    _assert_no_toolset_authority(read_model_payload)
    print("Hermes Runtime Adoption Phase 09 toolset posture verification passed.")


if __name__ == "__main__":
    main()
