#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.dev import uaa_founder_loop  # noqa: E402
from ultimate_ai_agent.core.control_center.agent_loop import (  # noqa: E402
    AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF,
)
from ultimate_ai_agent.core.control_center.founder_loop import (  # noqa: E402
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


BROAD_AUTHORITY_FLAGS = (
    "ui_mints_authority",
    "mutation_controls_enabled",
)

REQUIRED_SURFACES = {
    "Today",
    "Action Inbox",
    "Plans",
    "Evidence",
    "Memory",
    "Trust",
    "Runtime and Providers",
    "Coding and Work Board",
}


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="uaa-cockpit-parity-") as temp:
        state_dir = Path(temp) / "founder-loop"
        repo = FounderLoopRepository(state_dir)
        thread = FounderLoopControlCenterService(repo).agent_loop_thread()
        matrix = thread.get("operator_decision_matrix") or {}

        cli_buffer = io.StringIO()
        with contextlib.redirect_stdout(cli_buffer):
            exit_code = uaa_founder_loop.main(
                [
                    "--state-dir",
                    str(state_dir),
                    "inspect-cockpit-parity",
                    "--limit",
                    "20",
                ]
            )
        if exit_code != 0:
            failures.append("inspect-cockpit-parity CLI returned non-zero")
            cli_payload = {}
        else:
            cli_payload = json.loads(cli_buffer.getvalue())

    if matrix.get("contract_ref") != AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF:
        failures.append("cockpit parity contract ref drifted")
    for field in [
        "backend_owned",
        "control_center_presentation_only",
        "safe_refs_only",
    ]:
        if matrix.get(field) is not True:
            failures.append(f"cockpit parity {field} must be true")
    if matrix.get("raw_content_included") is not False:
        failures.append("cockpit parity raw content must be omitted")
    for flag in BROAD_AUTHORITY_FLAGS:
        if matrix.get(flag) is not False:
            failures.append(f"cockpit parity broadened {flag}")
    rows = matrix.get("rows") or []
    if matrix.get("row_count") != len(rows):
        failures.append("cockpit parity row count drifted")
    surfaces = {row.get("surface") for row in rows if isinstance(row, dict)}
    missing_surfaces = REQUIRED_SURFACES - surfaces
    if missing_surfaces:
        failures.append(
            f"cockpit parity missing surfaces: {sorted(missing_surfaces)}"
        )
    for row in rows:
        if not isinstance(row, dict):
            failures.append("cockpit parity row is not an object")
            continue
        if row.get("backend_truth_required") is not True:
            failures.append(f"{row.get('surface')} row missing backend truth")
        if row.get("mutation_enabled") is not False:
            failures.append(f"{row.get('surface')} row enabled mutation")
        if not str(row.get("backend_route_ref") or "").startswith("GET "):
            failures.append(f"{row.get('surface')} row missing backend route ref")
        if not str(row.get("cli_ref") or "").startswith("scripts/dev/"):
            failures.append(f"{row.get('surface')} row missing CLI ref")
        if not row.get("safe_action"):
            failures.append(f"{row.get('surface')} row missing safe action text")

    cli_matrix = cli_payload.get("operator_decision_matrix") or {}
    if cli_payload.get("command_ref") != (
        "repo-local-command:founder-loop-cockpit-cli-api-parity"
    ):
        failures.append("cockpit parity CLI command ref drifted")
    if cli_matrix.get("contract_ref") != AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF:
        failures.append("cockpit parity CLI contract ref drifted")
    if cli_payload.get("safe_refs_only") is not True:
        failures.append("cockpit parity CLI safe refs flag missing")
    if cli_payload.get("raw_content_omitted") is not True:
        failures.append("cockpit parity CLI raw content omission missing")

    docs = [
        ROOT / "docs/control_center/UAA_RUNTIME_COCKPIT_CLI_API.md",
        ROOT / "docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md",
    ]
    for doc in docs:
        if not doc.exists():
            failures.append(f"required doc missing: {doc.name}")
            continue
        text = doc.read_text(encoding="utf-8")
        if AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF not in text:
            failures.append(f"cockpit parity contract ref missing from {doc.name}")
        if "inspect-cockpit-parity" not in text:
            failures.append(f"cockpit parity CLI ref missing from {doc.name}")
        if "browser automation" not in text.lower():
            failures.append(f"browser automation blocked language missing from {doc.name}")

    frontend_files = [
        ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx",
        ROOT / "apps/control-center/src/api/types.ts",
        ROOT / "apps/control-center/src/api/client.ts",
    ]
    for file in frontend_files:
        text = file.read_text(encoding="utf-8")
        if "operator_decision_matrix" not in text:
            failures.append(f"operator decision matrix missing from {file.name}")
    panel_text = frontend_files[0].read_text(encoding="utf-8")
    if "Operator decision matrix" not in panel_text:
        failures.append("Control Center cockpit matrix heading missing")
    if "ui_mints_authority" not in panel_text:
        failures.append("Control Center UI authority posture missing")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA runtime cockpit CLI/API verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
