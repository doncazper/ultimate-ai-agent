#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.code import (
    CODING_COCKPIT_PROJECT_MODEL_REF,
    build_coding_cockpit_session_seed,
    build_coding_project_model_read_model,
)


ROOT = Path(__file__).resolve().parents[1]


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 21 verification failed: {message}")


def _assert_project_model(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "uaa-coding-project-model.v1":
        _fail("unexpected coding project model schema")
    if payload.get("project_model_ref") != CODING_COCKPIT_PROJECT_MODEL_REF:
        _fail("project model ref drifted")
    if payload.get("status") != "read_only_project_posture":
        _fail("project model is not read-only posture")
    for flag in (
        "raw_paths_included",
        "raw_content_included",
        "repo_file_read_performed",
        "project_scan_performed",
        "file_write_enabled",
        "shell_subprocess_execution_enabled",
        "git_status_execution_enabled",
        "git_mutation_enabled",
        "dev_server_control_enabled",
        "browser_preview_enabled",
        "browser_automation_enabled",
        "provider_model_call_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ):
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    for flag in ("backend_owned", "read_only", "safe_refs_only"):
        if payload.get(flag) is not True:
            _fail(f"{flag} must remain true")
    capabilities = payload.get("capabilities") or []
    if not isinstance(capabilities, list) or len(capabilities) < 12:
        _fail("project capabilities are missing")
    kinds = {item.get("capability_kind") for item in capabilities if isinstance(item, dict)}
    required_kinds = {
        "workspace",
        "repo",
        "lane",
        "branch",
        "worktree",
        "files",
        "diffs",
        "tests",
        "preview",
        "terminal",
        "git",
        "proof",
    }
    if required_kinds - kinds:
        _fail("project capabilities missing required kinds")
    for capability in capabilities:
        if not isinstance(capability, dict):
            _fail("capability payload is not an object")
        for flag in (
            "file_write_enabled",
            "shell_subprocess_execution_enabled",
            "git_mutation_enabled",
            "browser_automation_enabled",
            "provider_model_call_enabled",
            "background_autonomy_enabled",
        ):
            if capability.get(flag) is not False:
                _fail(f"capability {flag} must remain false")
    serialized = json.dumps(payload).lower()
    for forbidden in ("/users/", "raw_prompt", "raw_response", "provider_payload"):
        if forbidden in serialized:
            _fail(f"project model exposed forbidden marker {forbidden}")


def verify_core() -> None:
    model = build_coding_project_model_read_model()
    _assert_project_model(model.model_dump(mode="json"))
    session = build_coding_cockpit_session_seed()
    session_payload = session.model_dump(mode="json")
    if session_payload["project_model"]["project_model_ref"] != CODING_COCKPIT_PROJECT_MODEL_REF:
        _fail("session does not embed project model")
    if CODING_COCKPIT_PROJECT_MODEL_REF not in session_payload["same_ref_spine"]:
        _fail("session ref spine omits project model")


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    response = TestClient(app).get("/control-center/coding/session")
    if response.status_code != 200:
        _fail(f"GET /control-center/coding/session returned {response.status_code}")
    body = response.json()
    if body.get("success") is not True:
        _fail("API did not return success envelope")
    data = body.get("data") or {}
    if not isinstance(data, dict):
        _fail("API data is not an object")
    _assert_project_model(data.get("project_model") or {})


def verify_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_coding.py",
            "inspect-project-model",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    _assert_project_model(json.loads(result.stdout))


def verify_docs_and_ui() -> None:
    required_files = [
        "docs/runtime/UAA_HERMES_RUNTIME_CODING_PROJECT_MODEL.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/DOCUMENTATION_INDEX.md",
        "apps/control-center/src/components/CodingCockpitPanel.tsx",
    ]
    for relative in required_files:
        text = (ROOT / relative).read_text(encoding="utf-8")
        if "Phase 21" not in text and relative.endswith(".md"):
            _fail(f"{relative} does not mention Phase 21")
        if (
            relative.endswith("CodingCockpitPanel.tsx")
            and "Project posture is backend-owned, read-only, and safe-ref only."
            not in text
        ):
            _fail("Control Center does not render project posture truth label")


def main() -> int:
    verify_core()
    verify_api()
    verify_cli()
    verify_docs_and_ui()
    print("Hermes Runtime Adoption Phase 21 coding project model verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
