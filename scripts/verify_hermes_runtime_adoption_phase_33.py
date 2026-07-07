#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS,
    RUNTIME_WORKTREE_PER_AGENT_LANE_AUTHORITY_MAPPING_REFS,
    build_runtime_worktree_per_agent_read_model,
)


ROUTE = "/api/runtime/worktree-per-agent"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_WORKTREE_PER_AGENT.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/worktree_per_agent.py"
TEST = ROOT / "tests/test_hermes_runtime_worktree_per_agent.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_worktree_per_agent_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("worktree-per-agent route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-worktree-per-agent":
        failures.append("worktree-per-agent CLI ref is stale")
    if read_model.status != "read_only_worktree_lane_posture":
        failures.append("worktree-per-agent posture is not read-only")
    if read_model.lane_count != 3:
        failures.append("worktree-per-agent lacks expected lane proposals")
    if read_model.mutation_blocked_count < 1:
        failures.append("worktree-per-agent lacks blocked mutation posture")
    if set(read_model.authority_state_mapping_refs) != set(
        RUNTIME_WORKTREE_PER_AGENT_LANE_AUTHORITY_MAPPING_REFS.values()
    ):
        failures.append("worktree-per-agent AuthorityState mappings drifted")
    if read_model.authority_state_allowed_count != 3:
        failures.append("worktree-per-agent AuthorityState decisions should allow read lanes")
    unsafe_flags = {
        "git worktree create": read_model.git_worktree_create_enabled,
        "git worktree delete": read_model.git_worktree_delete_enabled,
        "branch mutation": read_model.branch_mutation_enabled,
        "file write": read_model.file_write_enabled,
        "commit": read_model.commit_enabled,
        "push": read_model.push_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "provider call": read_model.provider_call_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw path persistence": read_model.raw_path_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(
            f"missing worktree-per-agent blocked refs: {sorted(missing_blocked)}"
        )
    for lane in read_model.lanes:
        if lane.git_worktree_create_enabled or lane.git_worktree_delete_enabled:
            failures.append(f"lane exposes worktree mutation: {lane.lane_ref}")
        if lane.branch_mutation_enabled or lane.file_write_enabled:
            failures.append(f"lane exposes branch/file mutation: {lane.lane_ref}")
        if lane.commit_enabled or lane.push_enabled:
            failures.append(f"lane exposes commit/push: {lane.lane_ref}")
        if lane.shell_execution_enabled or lane.provider_call_enabled:
            failures.append(f"lane exposes shell/provider: {lane.lane_ref}")
        if lane.raw_path_persisted:
            failures.append(f"lane persists raw path: {lane.lane_ref}")

    manifest = build_api_manifest(app)
    route = next(
        (
            item
            for item in manifest.routes
            if item.path == ROUTE and item.method == "GET"
        ),
        None,
    )
    if route is None:
        failures.append("API manifest missing worktree-per-agent route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("worktree-per-agent route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("worktree-per-agent route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-worktree-per-agent",
        "runtime_worktree_per_agent",
        "proposal_only",
        "git_worktree_create_performed",
        "branch_mutation_performed",
        "push_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, CORE, TEST, UI]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-Strength",
            "Repo-Safe",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            ROUTE,
            "inspect-worktree-per-agent",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-worktree-per-agent",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("worktree-per-agent CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_worktree_per_agent"]
        authority_state = payload.get("authority_state")
        if not isinstance(authority_state, dict):
            failures.append("worktree-per-agent CLI missing authority state")
        elif set(authority_state.get("mapping_refs") or []) != set(
            RUNTIME_WORKTREE_PER_AGENT_LANE_AUTHORITY_MAPPING_REFS.values()
        ):
            failures.append("worktree-per-agent CLI authority mappings drifted")
        elif authority_state.get("allowed_count") != 3:
            failures.append("worktree-per-agent CLI authority decisions drifted")
        if payload["git_worktree_create_performed"] is not False:
            failures.append("worktree-per-agent CLI claims create")
        if payload["branch_mutation_performed"] is not False:
            failures.append("worktree-per-agent CLI claims branch mutation")
        if payload["file_write_performed"] is not False:
            failures.append("worktree-per-agent CLI claims file write")
        if payload["push_performed"] is not False:
            failures.append("worktree-per-agent CLI claims push")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("worktree-per-agent CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 33 worktree-per-agent verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
