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
    build_default_skill_bundle_proposal_posture,
    validate_skill_bundle_proposal_posture,
)


DENIED_FLAGS = [
    "bundle_activation_enabled",
    "skill_enablement_enabled",
    "tool_execution_enabled",
    "context_injection_enabled",
    "runtime_import_enabled",
    "provider_model_call_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "browser_automation_enabled",
    "production_authority_enabled",
]


def _fail(message: str) -> None:
    raise SystemExit(
        f"Hermes Runtime Adoption Phase 15 verification failed: {message}"
    )


def _assert_posture(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "uaa_skill_bundle_proposal_posture.v1":
        _fail("unexpected skill bundle posture schema")
    if payload.get("status") != "proposal_only":
        _fail("skill bundle posture is not proposal only")
    for flag in DENIED_FLAGS:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    proposals = payload.get("proposals") or []
    if payload.get("proposal_count") != len(proposals):
        _fail("proposal count mismatch")
    if not proposals:
        _fail("skill bundle proposal missing")
    proposal = proposals[0]
    for required_refs in (
        "skill_refs",
        "context_pack_refs",
        "toolset_refs",
        "verification_refs",
        "blocked_authority_refs",
        "next_safe_action_refs",
    ):
        if not proposal.get(required_refs):
            _fail(f"proposal {required_refs} missing")
    for flag in (
        "activation_performed",
        "skill_enablement_performed",
        "tool_execution_performed",
        "context_injection_performed",
        "runtime_import_performed",
        "provider_model_call_performed",
        "connector_write_performed",
        "shell_execution_performed",
        "browser_automation_performed",
        "production_authority_performed",
    ):
        if proposal.get(flag) is not False:
            _fail(f"proposal {flag} must remain false")


def verify_core() -> None:
    posture = build_default_skill_bundle_proposal_posture()
    validate_skill_bundle_proposal_posture(posture)
    _assert_posture(posture.model_dump(mode="json"))
    catalog = build_default_inspectable_extension_catalog().model_dump(mode="json")
    if catalog.get("skill_bundle_proposal_posture") != posture.model_dump(mode="json"):
        _fail("catalog skill bundle posture drifted from core builder")


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/extensions/catalog")
    if response.status_code != 200:
        _fail(f"GET /extensions/catalog returned {response.status_code}")
    body = response.json()
    _assert_posture(body.get("data", {}).get("skill_bundle_proposal_posture") or {})
    payload = json.dumps(body).lower()
    for forbidden in (
        "raw_prompt",
        "raw_response",
        "raw_provider_payload",
        "/users/",
    ):
        if forbidden in payload:
            _fail(f"API payload exposed forbidden marker {forbidden}")


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-skill-bundles",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    _assert_posture(json.loads(result.stdout))


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 15 skill bundle verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
