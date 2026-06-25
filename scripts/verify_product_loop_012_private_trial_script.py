#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.readiness import (  # noqa: E402
    PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES,
    PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF,
    PrivateProductLoopTrialScript,
    build_private_product_loop_trial_script,
)


ARTIFACT = ROOT / "docs/control_center/private_product_loop_trial_script_v1.json"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_012_PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
CLI = ROOT / "scripts/inspect_product_loop_trial_script.py"
FOCUSED_TEST = ROOT / "tests/test_product_loop_012_private_trial_script.py"
API_APP = ROOT / "src/ultimate_ai_agent/api"
BACKEND_FILES = [
    ROOT / "src/ultimate_ai_agent/core/readiness/private_operator_trial.py",
    ROOT / "src/ultimate_ai_agent/core/readiness/__init__.py",
]

DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "connector_write_enabled",
    "connector_runtime_enabled",
    "provider_model_authority_allowed",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "provider_sdk_call_enabled",
    "live_web_enabled",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "shell_browser_execution_enabled",
    "telemetry_export_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "action_execution_enabled",
    "code_apply_execution_enabled",
    "runtime_authority_added",
    "backend_route_added",
]

UNSAFE_MARKERS = [
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw log",
    "raw_log",
    "username",
    "hostname",
    "api key",
    "authorization",
    "password",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]

DOC_PHRASES = [
    "Product Loop 012",
    "Private product loop trial script",
    "scripts/inspect_product_loop_trial_script.py",
    "local/private",
    "safe-ref-only",
    "manual operator review",
    "no public beta",
    "no public distribution",
    "no telemetry export",
    "no connector runtime",
    "no provider/model calls",
    "no live web",
    "no shell/browser execution",
    "no production authority",
]


def _fail(message: str) -> None:
    raise SystemExit(f"Product Loop 012 verifier failed: {message}")


def _read(path: Path) -> str:
    if not path.exists():
        _fail(f"missing required file {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _normalize(path: Path) -> str:
    return " ".join(_read(path).split())


def _assert_script_contract() -> dict[str, Any]:
    artifact_text = _read(ARTIFACT)
    _assert_artifact_self_describing(json.loads(artifact_text))
    artifact = PrivateProductLoopTrialScript.model_validate_json(artifact_text)
    built = build_private_product_loop_trial_script()
    if artifact.model_dump(mode="json") != built.model_dump(mode="json"):
        _fail("checked-in trial script drifted from builder")
    payload = artifact.model_dump(mode="json")
    if payload["contract_ref"] != PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF:
        _fail("trial script contract ref drifted")
    surfaces = [step["surface"] for step in payload["manual_steps"]]
    if surfaces != PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES:
        _fail(f"trial script surface order drifted: {surfaces}")
    ledger_surfaces = [item["surface"] for item in payload["acceptance_ledger"]]
    if ledger_surfaces != PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES:
        _fail(f"trial script ledger surface order drifted: {ledger_surfaces}")
    if set(PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_BLOCKED_REFS) - set(
        payload["blocked_state_refs"]
    ):
        _fail("trial script missing required blocked refs")
    if any(item["review_state"] != "pending_operator_review" for item in payload["acceptance_ledger"]):
        _fail("trial script ledger must keep findings pending")
    _assert_denied_flags(payload)
    _assert_no_unsafe_markers(payload)
    _assert_model_rejects_authority(payload)
    return payload


def _assert_artifact_self_describing(raw: dict[str, Any]) -> None:
    required_top_level = [
        "script_ref",
        "contract_ref",
        "milestone_ref",
        "status",
        "blocked_state_refs",
        "local_private_only",
        "safe_refs_only",
        "manual_operator_review_required",
        *DENIED_FLAGS,
    ]
    for field_name in required_top_level:
        if field_name not in raw:
            _fail(f"trial script artifact omits top-level {field_name}")
    for step in raw.get("manual_steps", []):
        for field_name in [
            "step_state",
            "blocked_state_refs",
            "local_private_only",
            "safe_refs_only",
            "manual_operator_review_required",
            *DENIED_FLAGS,
        ]:
            if field_name not in step:
                _fail(f"trial script artifact step omits {field_name}")
    for item in raw.get("acceptance_ledger", []):
        for field_name in [
            "review_state",
            "blocked_state_refs",
            "local_private_only",
            "safe_refs_only",
            "manual_operator_review_required",
            *DENIED_FLAGS,
        ]:
            if field_name not in item:
                _fail(f"trial script artifact ledger item omits {field_name}")


def _assert_denied_flags(payload: dict[str, Any]) -> None:
    rows = [payload, *payload["manual_steps"], *payload["acceptance_ledger"]]
    for row in rows:
        for flag in DENIED_FLAGS:
            if flag in row and row[flag] is not False:
                _fail(f"trial script enables denied flag {flag}")
        if row.get("local_private_only") is not True:
            _fail("trial script row must stay local/private")
        if row.get("safe_refs_only") is not True:
            _fail("trial script row must stay safe-ref-only")
        if row.get("manual_operator_review_required") is not True:
            _fail("trial script row must require manual operator review")


def _assert_no_unsafe_markers(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in UNSAFE_MARKERS:
        if marker in serialized:
            _fail(f"trial script contains unsafe marker {marker!r}")


def _assert_model_rejects_authority(payload: dict[str, Any]) -> None:
    unsafe = json.loads(json.dumps(payload))
    unsafe["connector_runtime_enabled"] = True
    try:
        PrivateProductLoopTrialScript(**unsafe)
    except ValueError:
        pass
    else:
        _fail("trial script accepted connector runtime authority")

    unsafe = json.loads(json.dumps(payload))
    unsafe["manual_steps"][0]["safe_checklist_summary"] = "raw prompt material"
    try:
        PrivateProductLoopTrialScript(**unsafe)
    except ValueError:
        pass
    else:
        _fail("trial script accepted raw/private content")


def _assert_cli(payload: dict[str, Any]) -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "--json"],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    cli_payload = json.loads(completed.stdout)
    if cli_payload["contract_ref"] != payload["contract_ref"]:
        _fail("CLI contract ref drifted from artifact")
    if cli_payload["surfaces"] != PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES:
        _fail("CLI surface list drifted")
    if set(cli_payload["denied_flags"]) != set(DENIED_FLAGS):
        _fail("CLI denied flag set is incomplete")
    if any(cli_payload["denied_flags"].values()):
        _fail("CLI reported an enabled denied authority flag")
    if len(cli_payload["acceptance_ledger"]) != len(
        PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES
    ):
        _fail("CLI acceptance ledger surface count drifted")
    human = subprocess.run(
        [sys.executable, str(CLI)],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout
    if "{" in human or '"manual_steps"' in human:
        _fail("CLI default output must be a human checklist, not raw JSON")
    for phrase in [
        "Manual checklist:",
        "Acceptance ledger:",
        "Denied authority:",
        "local/private",
    ]:
        if phrase not in human:
            _fail(f"CLI human output missing phrase {phrase!r}")


def _assert_docs() -> None:
    for path in [DOC, INDEX, BOARD, TRUTH_PACKET, GAP_MAP]:
        text = _normalize(path)
        for phrase in DOC_PHRASES:
            if phrase not in text:
                _fail(f"{path.relative_to(ROOT)} missing phrase: {phrase}")
    for path in [DOC, INDEX, BOARD, TRUTH_PACKET, GAP_MAP]:
        lowered = _normalize(path).lower()
        for forbidden in [
            "public beta is ready",
            "public distribution is ready",
            "production ready",
            "production authority is granted",
            "provider/model calls are enabled",
            "connector runtime is enabled",
        ]:
            if forbidden in lowered:
                _fail(f"{path.relative_to(ROOT)} contains forbidden claim {forbidden!r}")


def _assert_static_files() -> None:
    for path in [CLI, FOCUSED_TEST, ARTIFACT, DOC, *BACKEND_FILES]:
        text = _read(path)
        for forbidden in ["requests.", "httpx.", "openai.", "playwright", "selenium"]:
            if forbidden in text:
                _fail(f"{path.relative_to(ROOT)} contains forbidden runtime snippet")
    api_text = "\n".join(path.read_text(encoding="utf-8") for path in API_APP.rglob("*.py"))
    if "product-loop-012" in api_text or "product_loop_trial" in api_text:
        _fail("Product Loop 012 must not add an API route")


def main() -> int:
    payload = _assert_script_contract()
    _assert_cli(payload)
    _assert_docs()
    _assert_static_files()
    print("Product Loop 012 private trial script verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
