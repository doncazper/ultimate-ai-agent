#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
    build_default_skill_write_approval_gate,
    validate_skill_write_approval_gate,
)


DENIED_FLAGS = [
    "file_write_enabled",
    "direct_skill_write_enabled",
    "skill_enablement_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "provider_model_call_enabled",
    "browser_automation_enabled",
    "production_authority_enabled",
]


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 14 verification failed: {message}")


def _assert_gate(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "uaa_skill_write_approval_gate.v1":
        _fail("unexpected skill write gate schema")
    if payload.get("status") != "staged_review_only":
        _fail("skill write gate is not staged review only")
    for flag in DENIED_FLAGS:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    proposals = payload.get("proposals") or []
    if payload.get("proposal_count") != len(proposals):
        _fail("proposal count mismatch")
    if not proposals:
        _fail("staged proposal missing")
    proposal = proposals[0]
    for flag in (
        "file_write_performed",
        "skill_enablement_performed",
        "runtime_import_performed",
        "execution_performed",
        "raw_instruction_body_persisted",
    ):
        if proposal.get(flag) is not False:
            _fail(f"proposal {flag} must remain false")
    if not proposal.get("diff_previews"):
        _fail("proposal diff preview missing")
    if not proposal.get("blocked_execution_labels"):
        _fail("proposal blocked execution labels missing")


def verify_core() -> None:
    gate = build_default_skill_write_approval_gate()
    validate_skill_write_approval_gate(gate)
    _assert_gate(gate.model_dump(mode="json"))
    catalog = build_default_inspectable_extension_catalog().model_dump(mode="json")
    if catalog.get("skill_write_approval_gate") != gate.model_dump(mode="json"):
        _fail("catalog skill write gate drifted from core builder")


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/extensions/catalog")
    if response.status_code != 200:
        _fail(f"GET /extensions/catalog returned {response.status_code}")
    body = response.json()
    _assert_gate(body.get("data", {}).get("skill_write_approval_gate") or {})
    payload = json.dumps(body).lower()
    for forbidden in ("raw_prompt", "raw_response", "raw_provider_payload", "/users/"):
        if forbidden in payload:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-skill-write-gate",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    _assert_gate(json.loads(result.stdout))


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 14 skill write gate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
