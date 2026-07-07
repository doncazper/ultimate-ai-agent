#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_MAPPING_REF,
    RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_STATE_CLI_REF,
    RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS,
    build_runtime_checkpoint_rollback_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 18 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_checkpoint_rollback.v1":
        _fail("unexpected checkpoint rollback schema")
    if payload.get("status") != "read_only_checkpoint_rollback_posture":
        _fail("checkpoint rollback posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/checkpoint-rollback":
        _fail("route ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("authority state route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_STATE_CLI_REF
    ):
        _fail("authority state CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_MAPPING_REF
    ):
        _fail("authority state mapping ref drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("authority state decision outcome drifted")
    if not payload.get("authority_state_reason_refs"):
        _fail("authority state reason refs missing")
    unsupported = set(payload.get("unsupported_adapter_refs") or [])
    if "adapter-ref:checkpoint-rollback-execution-route:not-implemented" not in unsupported:
        _fail("rollback execution unsupported adapter ref missing")
    for flag in (
        "broad_filesystem_snapshot_enabled",
        "rollback_execution_route_enabled",
        "git_mutation_enabled",
        "raw_content_persistence_enabled",
        "raw_path_persistence_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing checkpoint rollback blocked authority refs")
    lanes = payload.get("lanes") or []
    if payload.get("lane_count") != len(lanes):
        _fail("lane count mismatch")
    if not lanes:
        _fail("checkpoint rollback lanes missing")
    for lane in lanes:
        for flag in (
            "api_rollback_execution_enabled",
            "control_center_rollback_execution_enabled",
            "broad_filesystem_snapshot_enabled",
            "git_mutation_enabled",
            "raw_content_persisted",
            "raw_path_persisted",
            "provider_model_call_performed",
            "shell_execution_performed",
            "browser_automation_performed",
            "production_authority_enabled",
        ):
            if lane.get(flag) is not False:
                _fail(f"lane {flag} must remain false")


def verify_core() -> None:
    _assert_read_model(
        build_runtime_checkpoint_rollback_read_model().model_dump(mode="json")
    )


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/checkpoint-rollback")
    if response.status_code != 200:
        _fail(f"GET /api/runtime/checkpoint-rollback returned {response.status_code}")
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    _assert_read_model(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in ("/users/", "raw_content_payload", "target_path"):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-checkpoint-rollback",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_read_model(payload.get("runtime_checkpoint_rollback") or {})
    authority_state = payload.get("authority_state") or {}
    if (
        authority_state.get("mapping_ref")
        != RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_MAPPING_REF
    ):
        _fail("CLI authority mapping ref drifted")
    if authority_state.get("decision_outcome") != "allow":
        _fail("CLI authority decision outcome drifted")
    if payload.get("rollback_execution_performed") is not False:
        _fail("CLI claimed rollback execution")
    if payload.get("broad_filesystem_snapshot_performed") is not False:
        _fail("CLI claimed broad filesystem snapshot")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 18 checkpoint rollback verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
