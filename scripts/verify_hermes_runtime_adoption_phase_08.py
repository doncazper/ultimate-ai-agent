#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.providers.control_plane import (  # noqa: E402
    build_model_provider_control_plane_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_authority(payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden = [
        '"live_auxiliary_calls_enabled": true',
        '"live_auxiliary_call_enabled": true',
        '"provider_sdk_use_enabled": true',
        '"provider_sdk_call_enabled": true',
        '"runtime_selection_mutation_enabled": true',
        '"hidden_model_routing_enabled": true',
        '"raw_prompt_persistence_enabled": true',
        '"raw_response_persistence_enabled": true',
        '"raw_prompt_persisted": true',
        '"raw_response_persisted": true',
        '"model_invocation_performed": true',
        '"remote_model_call_enabled": true',
        '"provider_router_execution_enabled": true',
        '"model_router_execution_enabled": true',
    ]
    for fragment in forbidden:
        if fragment in serialized:
            _fail(f"forbidden model slot authority: {fragment}")


def _assert_slots(payload: dict[str, object]) -> None:
    posture = payload.get("model_slot_posture")
    if not isinstance(posture, dict):
        _fail("model slot posture missing")
    if posture.get("schema_version") != "hermes_runtime_model_slot_posture.v1":
        _fail("model slot posture schema drifted")
    if posture.get("status") != "read_only_model_slot_intent":
        _fail("model slot posture must stay read-only")
    if posture.get("trust_lane_ref") != "trust-lane:model-slot-posture":
        _fail("model slot posture Trust binding missing")
    if posture.get("main_slot_ref") != "model-slot-ref:uaa:main-thinking":
        _fail("main model slot ref drifted")
    records = posture.get("records")
    if not isinstance(records, list) or len(records) != 8:
        _fail("model slot posture must expose eight slots")
    if posture.get("slot_count") != len(records):
        _fail("model slot count drifted")
    expected_roles = {
        "main_thinking",
        "summarization",
        "title",
        "approval_scoring",
        "compression",
        "retrieval",
        "vision",
        "review",
    }
    roles = {
        record.get("slot_role")
        for record in records
        if isinstance(record, dict)
    }
    if roles != expected_roles:
        _fail("model slot roles drifted")
    warning_count = 0
    for flag in [
        "live_auxiliary_calls_enabled",
        "provider_sdk_use_enabled",
        "runtime_selection_mutation_enabled",
        "hidden_model_routing_enabled",
        "raw_prompt_persistence_enabled",
        "raw_response_persistence_enabled",
    ]:
        if posture.get(flag) is not False:
            _fail(f"{flag} must remain false")
    for flag in [
        "route_decision_trace_required",
        "cost_estimate_required",
        "approval_profile_mapping_required",
        "model_output_truth_envelope_required",
        "receipts_required_before_execution",
    ]:
        if posture.get(flag) is not True:
            _fail(f"{flag} must remain true")
    for record in records:
        if not isinstance(record, dict):
            _fail("model slot record is invalid")
        warning_refs = record.get("warning_refs")
        if isinstance(warning_refs, list) and warning_refs:
            warning_count += 1
        for flag in [
            "live_auxiliary_call_enabled",
            "provider_sdk_call_enabled",
            "runtime_selection_mutation_enabled",
            "hidden_model_routing_enabled",
            "raw_prompt_persisted",
            "raw_response_persisted",
        ]:
            if record.get(flag) is not False:
                _fail(f"record {record.get('slot_ref')} enabled {flag}")
        if not record.get("blocked_authority_refs"):
            _fail(f"record {record.get('slot_ref')} blockers missing")
        if not record.get("route_decision_trace_ref"):
            _fail(f"record {record.get('slot_ref')} route trace missing")
        if record.get("model_output_truth_ref") not in {
            "truth-boundary-ref:model-output:not-authority",
            "truth-boundary-ref:retrieval-output:not-authority",
        }:
            _fail(f"record {record.get('slot_ref')} truth boundary drifted")
    if posture.get("warning_count") != warning_count:
        _fail("model slot warning count drifted")
    if "proof-ref:hermes-runtime-adoption:phase-08:model-slot-posture" not in (
        posture.get("proof_refs") or []
    ):
        _fail("phase 08 proof ref missing")


def main() -> None:
    read_model = build_model_provider_control_plane_read_model()
    core_payload = read_model.model_dump(mode="json")
    _assert_slots(core_payload)
    _assert_no_authority(core_payload)

    client = TestClient(app)
    response = client.get("/control-center/providers/runtime-control-plane")
    if response.status_code != 200:
        _fail(f"runtime control plane route returned {response.status_code}")
    body = response.json()
    api_payload = body.get("data")
    if not isinstance(api_payload, dict):
        _fail("runtime control plane route did not return data")
    _assert_slots(api_payload)
    _assert_no_authority(api_payload)

    result = subprocess.run(
        [sys.executable, "scripts/inspect_model_provider_control_plane.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    _assert_slots(cli_payload)
    _assert_no_authority(cli_payload)
    print("Hermes Runtime Adoption Phase 08 model slot posture verification passed.")


if __name__ == "__main__":
    main()
