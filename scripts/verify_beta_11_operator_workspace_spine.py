#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.operator_workspace_spine import (
    OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS,
    OPERATOR_WORKSPACE_SPINE_CLI_REF,
    OPERATOR_WORKSPACE_SPINE_CONTRACT_REF,
    OPERATOR_WORKSPACE_SPINE_PROOF_REF,
    OPERATOR_WORKSPACE_SPINE_ROUTE_REF,
    build_operator_workspace_spine_read_model,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parent.parent
LANE_DOC = ROOT / "docs/control_center/OPERATOR_WORKSPACE_SPINE.md"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
FRONTEND_ROUTES = ROOT / "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md"
AUTHORITY_BOARD = ROOT / "docs/control_center/AUTHORITY_GRADUATION_BOARD.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_VERIFIER = ROOT / "scripts/verify_control_center_frontend.py"

DENIED_FIELDS = (
    "file_write_enabled",
    "git_mutation_enabled",
    "shell_subprocess_execution_enabled",
    "browser_automation_enabled",
    "dev_server_start_enabled",
    "provider_model_call_enabled",
    "connector_write_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
    "raw_path_persistence_enabled",
    "raw_log_persistence_enabled",
)
FORBIDDEN_ROUTES = (
    "/control-center/git/commit",
    "/control-center/git/push",
    "/control-center/git/pull",
    "/control-center/git/checkout",
    "/control-center/workspace/apply",
    "/control-center/workspace/run",
    "/control-center/operator-workspace/run",
    "/control-center/operator-workspace/git/commit",
    "/control-center/coworker/dispatch",
)


def _append_core_failures(failures: list[str]) -> None:
    read_model = build_operator_workspace_spine_read_model()
    payload = read_model.model_dump(mode="json")
    if read_model.contract_ref != OPERATOR_WORKSPACE_SPINE_CONTRACT_REF:
        failures.append("operator workspace contract drift")
    if read_model.source != "python_core_operator_workspace_spine_read_model":
        failures.append("operator workspace source drift")
    if read_model.route_ref != OPERATOR_WORKSPACE_SPINE_ROUTE_REF:
        failures.append("operator workspace route ref drift")
    if read_model.cli_ref != OPERATOR_WORKSPACE_SPINE_CLI_REF:
        failures.append("operator workspace CLI ref drift")
    if OPERATOR_WORKSPACE_SPINE_PROOF_REF not in read_model.proof_refs:
        failures.append("operator workspace proof ref missing")
    if [lane.lane_kind for lane in read_model.lanes] != [
        "workspace_status",
        "git_posture",
        "preview_status",
        "run_logs",
        "coworker_handoff",
    ]:
        failures.append("operator workspace lane order drift")
    for field in DENIED_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"operator workspace enables {field}")
    for ref in OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS:
        if ref not in read_model.blocked_authority_refs:
            failures.append(f"operator workspace missing blocked ref: {ref}")
    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in ("/Users/", "/home/", "-----BEGIN", "api_key", "access-token"):
        if forbidden in serialized:
            failures.append(f"operator workspace serialized unsafe fragment: {forbidden}")


def _append_cli_failures(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/inspect_operator_workspace_spine.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if payload.get("source") != "python_core_operator_workspace_spine_read_model":
        failures.append("operator workspace CLI source drift")
    for field in DENIED_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"operator workspace CLI enables {field}")
    for field in (
        "real_workspace_runtime_performed",
        "git_mutation_performed",
        "shell_subprocess_performed",
        "browser_automation_performed",
        "dev_server_started",
        "coworker_dispatch_performed",
        "provider_or_connector_runtime_performed",
    ):
        if payload.get(field) is not False:
            failures.append(f"operator workspace CLI claims runtime: {field}")


def _append_control_center_failures(failures: list[str]) -> None:
    with TemporaryDirectory() as directory:
        service = FounderLoopControlCenterService(
            FounderLoopRepository(Path(directory) / "founder-loop.sqlite3")
        )
        today = service.today_summary()
        read_model = today.get("operator_workspace_spine_read_model", {})
        if read_model.get("contract_ref") != OPERATOR_WORKSPACE_SPINE_CONTRACT_REF:
            failures.append("Today missing operator workspace spine contract")
        if read_model.get("source") != "python_core_operator_workspace_spine_read_model":
            failures.append("Today operator workspace source drift")
        for field in DENIED_FIELDS:
            if read_model.get(field) is not False:
                failures.append(f"Today operator workspace enables {field}")

        proof_detail = service.proof_detail(OPERATOR_WORKSPACE_SPINE_PROOF_REF)
        record = proof_detail.get("record", {})
        if record.get("proof_kind") != "operator_workspace_spine":
            failures.append("Proof Detail missing operator workspace kind")
        if OPERATOR_WORKSPACE_SPINE_ROUTE_REF not in record.get("backend_route_refs", []):
            failures.append("Proof Detail missing operator workspace route ref")
        if "blocked-state:operator-workspace:no-git-mutation" not in record.get(
            "blocked_authority_refs",
            [],
        ):
            failures.append("Proof Detail missing Git mutation blocker")
        for field in (
            "raw_content_included",
            "provider_model_call_enabled",
            "runtime_model_call_enabled",
            "connector_write_enabled",
            "shell_subprocess_execution_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ):
            if record.get(field) is not False:
                failures.append(f"Proof Detail enables {field}")

        trust = build_trust_authority_matrix_read_model(today_summary=today)
        lane = next(
            (
                item
                for item in trust.get("lanes", [])
                if item.get("lane_ref") == "trust-lane:operator-workspace-spine"
            ),
            None,
        )
        if lane is None:
            failures.append("Trust matrix missing operator workspace lane")
        else:
            if OPERATOR_WORKSPACE_SPINE_CLI_REF not in lane.get(
                "cli_inspection_refs",
                [],
            ):
                failures.append("Trust matrix missing operator workspace CLI ref")
            if OPERATOR_WORKSPACE_SPINE_PROOF_REF not in lane.get("proof_refs", []):
                failures.append("Trust matrix missing operator workspace proof ref")
            if "blocked-state:operator-workspace:no-git-mutation" not in lane.get(
                "blocked_authority_refs",
                [],
            ):
                failures.append("Trust matrix missing Git mutation blocker")

    route_paths = {route.path for route in build_api_manifest(app).routes}
    for route in FORBIDDEN_ROUTES:
        if route in route_paths:
            failures.append(f"unexpected operator workspace mutation route: {route}")


def _append_static_failures(failures: list[str]) -> None:
    required_fragments = {
        LANE_DOC: [
            "Full-strength version",
            "Repo-safe beta-11 version",
            "Blocked / needs authority",
            "Exact promotion path",
            "workspace status, Git posture, preview status, run logs, and coworker handoff",
        ],
        RELEASE_SURFACE: [
            "Operator Workspace Spine",
            "no Git mutation",
            "scripts/verify_beta_11_operator_workspace_spine.py",
        ],
        FRONTEND_ROUTES: [
            "Operator Workspace Spine",
            "GET /control-center/today/summary#operator_workspace_spine",
        ],
        AUTHORITY_BOARD: [
            "Operator Workspace Spine",
            "no Git mutation",
        ],
        TRUTH_PACKET: [
            "Operator Workspace Spine",
            "workspace status, Git posture, preview status",
        ],
        CURRENT_BOARD: [
            "Beta 11 Operator Workspace Spine",
            "docs/control_center/OPERATOR_WORKSPACE_SPINE.md",
        ],
        FRONTEND_TEST: [
            "renders backend-owned Operator Workspace Spine",
            "renders operator workspace spine proof",
            "git commit|commit changes|push branch",
        ],
        FRONTEND_PANEL: [
            "Backend-owned Operator Workspace Spine",
            "Full Strength Goal",
            "Repo-Safe Scope",
            "Blocked Authority",
            "Exact promotion path",
        ],
        FRONTEND_VERIFIER: [
            "/control-center/git/commit",
            "Push branch",
            "Dispatch coworker",
        ],
    }
    for path, fragments in required_fragments.items():
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        compact = " ".join(text.split())
        for fragment in fragments:
            if fragment not in text and fragment not in compact:
                failures.append(
                    f"{path.relative_to(ROOT)} missing beta-11 fragment: {fragment}"
                )


def validate_beta_11_operator_workspace_spine() -> list[str]:
    failures: list[str] = []
    _append_core_failures(failures)
    _append_cli_failures(failures)
    _append_control_center_failures(failures)
    _append_static_failures(failures)
    return failures


def main() -> int:
    failures = validate_beta_11_operator_workspace_spine()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Beta 11 operator workspace spine verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
