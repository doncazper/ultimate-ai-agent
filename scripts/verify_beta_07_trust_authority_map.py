#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.local_auth import (  # noqa: E402
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
)
from ultimate_ai_agent.core.control_center.founder_loop import (  # noqa: E402
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.trust_authority import (  # noqa: E402
    TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS,
    TRUST_AUTHORITY_MATRIX_CONTRACT_REF,
    TRUST_AUTHORITY_MATRIX_ROUTE_REF,
    TrustAuthorityMatrixReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/trust_authority.py"
API = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_ROUTES = ROOT / "apps/control-center/src/routes.tsx"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/TrustAuthorityPanel.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
FOCUSED_TEST = ROOT / "tests/test_trust_authority_matrix.py"
VERIFIER_TEST = ROOT / "tests/test_beta_07_trust_authority_map_verifier.py"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
BOARD = ROOT / "docs/kanban/current_board.md"

FORBIDDEN_TEXT = [
    "raw prompt",
    "raw response",
    "provider payload",
    "api key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/etc/",
]

DENIED_FLAGS = [
    "broad_approval_enabled",
    "standing_authority_enabled",
    "runtime_context_injection_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
    "control_center_grants_authority",
    "raw_content_included",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _merge_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        merged.append(value)
    return merged


def _assert_safe_payload(payload: dict[str, Any], failures: list[str], label: str) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for snippet in FORBIDDEN_TEXT:
        if snippet in text:
            failures.append(f"{label} contains forbidden snippet {snippet!r}")
    for flag in DENIED_FLAGS:
        if f'"{flag}": true' in text:
            failures.append(f"{label} enables forbidden authority {flag}")


def _assert_matrix(matrix: dict[str, Any], failures: list[str], label: str) -> None:
    parsed = TrustAuthorityMatrixReadModel(**matrix)
    if parsed.contract_ref != TRUST_AUTHORITY_MATRIX_CONTRACT_REF:
        failures.append(f"{label} contract ref drifted")
    if parsed.route_ref != TRUST_AUTHORITY_MATRIX_ROUTE_REF:
        failures.append(f"{label} route ref drifted")
    if not parsed.backend_owned or not parsed.local_read_model_only:
        failures.append(f"{label} must stay backend-owned local read model")
    if not parsed.safe_refs_only or parsed.raw_content_included:
        failures.append(f"{label} must stay safe-ref only")
    if parsed.control_center_grants_authority:
        failures.append(f"{label} must not grant authority from Control Center")

    for lane in parsed.lanes:
        if not lane.cli_inspection_refs:
            failures.append(f"{label} lane missing CLI refs: {lane.lane_ref}")
        if not lane.safe_disable_refs:
            failures.append(f"{label} lane missing safe-disable refs: {lane.lane_ref}")
        if not lane.rollback_refs:
            failures.append(f"{label} lane missing rollback refs: {lane.lane_ref}")
        if not lane.promotion_path_refs:
            failures.append(f"{label} lane missing promotion refs: {lane.lane_ref}")
        if lane.rollback_execution_enabled:
            failures.append(f"{label} lane enables rollback execution: {lane.lane_ref}")
        if lane.tier == 2 and lane.operator_posture != "review_only":
            failures.append(f"{label} tier 2 lane must remain review_only: {lane.lane_ref}")
        if lane.tier >= 3 and (not lane.requires_safe_disable or not lane.requires_rollback_posture):
            failures.append(f"{label} mutation lane missing safe-disable/rollback posture: {lane.lane_ref}")
        if lane.tier >= 4 and lane.authority_state == "available_now":
            failures.append(
                f"{label} tier 4/5 lane must be blocked or approval-required: {lane.lane_ref}"
            )
        if lane.tier >= 4 and lane.authority_state == "approval_required":
            if (
                not lane.requires_exact_approval
                or not lane.requires_safe_disable
                or not lane.requires_rollback_posture
            ):
                failures.append(
                    f"{label} tier 4/5 lane missing exact safeguards: {lane.lane_ref}"
                )
        for cli_ref in lane.cli_inspection_refs:
            if cli_ref not in TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS:
                failures.append(f"{label} unregistered CLI ref: {cli_ref}")

    if len(parsed.authority_capability_catalog) != len(parsed.lanes):
        failures.append(f"{label} capability catalog must map every lane")
    if parsed.authority_capability_catalog_refs != [
        entry.catalog_ref for entry in parsed.authority_capability_catalog
    ]:
        failures.append(f"{label} capability catalog refs drifted")
    if [entry.source_lane_ref for entry in parsed.authority_capability_catalog] != [
        lane.lane_ref for lane in parsed.lanes
    ]:
        failures.append(f"{label} capability catalog source lane refs drifted")
    catalog_by_lane = {
        entry.source_lane_ref: entry for entry in parsed.authority_capability_catalog
    }
    for lane in parsed.lanes:
        entry = catalog_by_lane.get(lane.lane_ref)
        if entry is None:
            failures.append(f"{label} missing capability entry for {lane.lane_ref}")
            continue
        if (
            entry.authority_domain_ref != lane.authority_domain_ref
            or entry.authority_capability_ref != lane.authority_capability_ref
            or entry.required_authority_mode != lane.required_authority_mode
            or entry.authority_lease_requirement_ref
            != lane.authority_lease_requirement_ref
        ):
            failures.append(f"{label} capability entry drifted for {lane.lane_ref}")
        if (
            not entry.active_lease_required
            or not entry.unknown_authority_denied
            or not entry.safe_refs_only
            or entry.control_center_grants_authority
            or entry.execution_claimed
        ):
            failures.append(f"{label} capability entry grants authority: {lane.lane_ref}")

    lanes = parsed.lanes
    parity = {
        "cli_inspection_refs": [ref for lane in lanes for ref in lane.cli_inspection_refs],
        "safe_disable_refs": [ref for lane in lanes for ref in lane.safe_disable_refs],
        "rollback_refs": [ref for lane in lanes for ref in lane.rollback_refs],
        "promotion_path_refs": [ref for lane in lanes for ref in lane.promotion_path_refs],
        "blocked_authority_refs": [ref for lane in lanes for ref in lane.blocked_authority_refs],
    }
    for field, values in parity.items():
        if getattr(parsed, field) != _merge_unique(values):
            failures.append(f"{label} aggregate {field} drifted from lanes")

    expected_available = {
        lane.lane_ref for lane in lanes if lane.authority_state == "available_now"
    }
    expected_approval = {
        lane.lane_ref for lane in lanes if lane.authority_state == "approval_required"
    }
    expected_planned = {
        lane.lane_ref for lane in lanes if lane.authority_state == "planned"
    }
    expected_blocked = {
        lane.lane_ref for lane in lanes if lane.authority_state == "blocked"
    }
    if set(parsed.available_now_lane_refs) != expected_available:
        failures.append(f"{label} available lane refs drifted")
    if set(parsed.approval_required_lane_refs) != expected_approval:
        failures.append(f"{label} approval lane refs drifted")
    if set(parsed.planned_lane_refs) != expected_planned:
        failures.append(f"{label} planned lane refs drifted")
    if set(parsed.blocked_lane_refs) != expected_blocked:
        failures.append(f"{label} blocked lane refs drifted")

    _assert_safe_payload(matrix, failures, label)


def _runtime_failures() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        service = FounderLoopControlCenterService(repo)
        service_matrix = service.trust_authority_matrix()
        _assert_matrix(service_matrix, failures, "service matrix")

    api_client = TestClient(app)
    old_dev_bypass = os.environ.get(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV)
    os.environ[LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV] = "1"
    try:
        response = api_client.get("/control-center/trust-authority/matrix")
    finally:
        if old_dev_bypass is None:
            os.environ.pop(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, None)
        else:
            os.environ[LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV] = old_dev_bypass
    if response.status_code != 200:
        failures.append(f"Trust route returned {response.status_code}")
    else:
        route_payload = response.json()
        if route_payload.get("success") is not True:
            failures.append("Trust route envelope success drifted")
        route_matrix = route_payload.get("data")
        if isinstance(route_matrix, dict):
            _assert_matrix(route_matrix, failures, "route matrix")
        else:
            failures.append("Trust route did not return matrix data")
        _assert_safe_payload(route_payload, failures, "route envelope")

    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--state-dir",
                str(Path(temp_dir) / "state"),
                "inspect-trust-authority",
                "--limit",
                "5",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        failures.append(f"Trust CLI failed: {result.stderr.strip()}")
    else:
        cli_payload = json.loads(result.stdout)
        if cli_payload.get("command_ref") != "repo-local-command:founder-loop-trust-authority":
            failures.append("Trust CLI command ref drifted")
        if cli_payload.get("safe_refs_only") is not True:
            failures.append("Trust CLI must stay safe-ref only")
        if cli_payload.get("raw_content_omitted") is not True:
            failures.append("Trust CLI must omit raw content")
        cli_matrix = cli_payload.get("trust_authority_matrix")
        if isinstance(cli_matrix, dict):
            _assert_matrix(cli_matrix, failures, "CLI matrix")
        else:
            failures.append("Trust CLI did not return matrix data")
        _assert_safe_payload(cli_payload, failures, "CLI payload")

    if "route_matrix" in locals() and "cli_matrix" in locals() and isinstance(route_matrix, dict) and isinstance(cli_matrix, dict):
        for field in [
            "available_now_lane_refs",
            "approval_required_lane_refs",
            "blocked_lane_refs",
            "cli_inspection_refs",
            "safe_disable_refs",
            "rollback_refs",
            "promotion_path_refs",
            "blocked_authority_refs",
        ]:
            if route_matrix.get(field) != cli_matrix.get(field):
                failures.append(f"route/CLI {field} drifted")

    failures.extend(_cli_ref_failures())
    return failures


def _cli_ref_failures() -> list[str]:
    failures: list[str] = []
    help_result = subprocess.run(
        [sys.executable, str(CLI), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    help_text = help_result.stdout
    for cli_ref in TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS:
        parts = cli_ref.split()
        if len(parts) < 2 or parts[0] != "python":
            failures.append(f"Trust CLI ref is not parser-backed python command: {cli_ref}")
            continue
        path = ROOT / parts[1]
        if not path.exists():
            failures.append(f"Trust CLI ref path missing: {cli_ref}")
            continue
        if parts[1] == "scripts/dev/uaa_founder_loop.py":
            command = parts[2] if len(parts) > 2 else ""
            if command and command not in help_text:
                failures.append(f"Trust CLI parser missing command {command!r}")
    return failures


def _static_failures() -> list[str]:
    failures: list[str] = []
    for path in [
        CONTRACT,
        API,
        CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_ROUTES,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        FOCUSED_TEST,
        VERIFIER_TEST,
        RELEASE_SURFACE,
        TRUTH_PACKET,
        BOARD,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        return failures

    _require(
        CONTRACT,
        [
            "TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS",
            "operator_posture",
            "safe_disable_refs",
            "rollback_refs",
            "promotion_path_refs",
            "rollback_execution_enabled",
            "Tier 4 and Tier 5 authority requires exact approval",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "TRUST_AUTHORITY_STATES",
            "TRUST_AUTHORITY_LANE_KINDS",
            "isExpectedTrustOperatorPosture",
            "hasTrustAuthorityMatrixRefParity",
            "rollback_execution_enabled === false",
        ],
        failures,
    )
    _require(
        FRONTEND_ROUTES,
        [
            "isTrustAuthorityAuthoritative",
            "TRUST_AUTHORITY_MATRIX_MOCK_FALLBACK",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Posture",
            "Safe-disable and rollback",
            "Capability path",
            "CLI and verifiers",
            "Mock Fallback Compatibility Refs",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "renders Trust safe-disable, rollback, capability path, and CLI refs from backend",
            "keeps Trust backend-owned when an unrelated endpoint degrades",
            "fails closed for unsafe Trust authority matrix payloads",
            "TRUST_AUTHORITY_MATRIX_MOCK_FALLBACK",
        ],
        failures,
    )
    for doc in [RELEASE_SURFACE, TRUTH_PACKET, BOARD]:
        _require(
            doc,
            [
                "Beta 07 Trust authority map",
                "scripts/verify_beta_07_trust_authority_map.py",
                "safe-disable",
                "rollback",
                "promotion",
                "No broad runtime authority",
            ],
            failures,
        )
    return failures


def main() -> int:
    failures = [*_static_failures(), *_runtime_failures()]
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Beta 07 Trust authority map verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
