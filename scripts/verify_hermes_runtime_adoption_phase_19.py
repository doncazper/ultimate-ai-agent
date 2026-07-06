#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS,
    build_runtime_session_lineage_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 19 verification failed: {message}")


def _assert_read_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_session_lineage.v1":
        _fail("unexpected session lineage schema")
    if payload.get("status") != "read_only_session_lineage_and_fork_posture":
        _fail("session lineage posture is not read-only")
    if payload.get("route_ref") != "GET /api/runtime/session-lineage":
        _fail("route ref drifted")
    for flag in (
        "raw_transcript_clone_enabled",
        "hidden_context_injection_enabled",
        "runtime_dispatch_enabled",
        "provider_model_call_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    blockers = set(payload.get("blocked_authority_refs") or [])
    if set(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS) - blockers:
        _fail("missing session lineage blocked authority refs")
    nodes = payload.get("nodes") or []
    forks = payload.get("forks") or []
    if payload.get("node_count") != len(nodes):
        _fail("node count mismatch")
    if payload.get("fork_count") != len(forks):
        _fail("fork count mismatch")
    if not nodes or not forks:
        _fail("session lineage nodes or forks missing")
    for node in nodes:
        for flag in (
            "raw_transcript_cloned",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "hidden_context_injected",
            "runtime_dispatch_performed",
            "provider_model_call_performed",
            "shell_execution_performed",
            "browser_automation_performed",
            "connector_write_performed",
            "production_authority_enabled",
        ):
            if node.get(flag) is not False:
                _fail(f"node {flag} must remain false")
    for fork in forks:
        for flag in (
            "raw_transcript_cloned",
            "hidden_context_injected",
            "runtime_dispatch_performed",
            "provider_model_call_performed",
            "production_authority_enabled",
        ):
            if fork.get(flag) is not False:
                _fail(f"fork {flag} must remain false")
        if fork.get("explicit_operator_intent_required") is not True:
            _fail("fork must require explicit operator intent")
        if fork.get("redacted_fork_envelope_required") is not True:
            _fail("fork must require redacted envelope")
        if fork.get("proof_binding_required") is not True:
            _fail("fork must require proof binding")


def verify_core() -> None:
    _assert_read_model(build_runtime_session_lineage_read_model().model_dump(mode="json"))


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/api/runtime/session-lineage")
    if response.status_code != 200:
        _fail(f"GET /api/runtime/session-lineage returned {response.status_code}")
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    _assert_read_model(body.get("data") or {})
    serialized = json.dumps(body).lower()
    for forbidden in ("/users/", "raw_transcript_payload", "raw_prompt_payload"):
        if forbidden in serialized:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-lineage",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    _assert_read_model(payload.get("runtime_session_lineage") or {})
    if payload.get("runtime_dispatch_performed") is not False:
        _fail("CLI claimed runtime dispatch")
    if payload.get("hidden_context_injection_performed") is not False:
        _fail("CLI claimed hidden context injection")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 19 session lineage verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
