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
    RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS,
    RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE,
    build_runtime_hardline_command_blocklist_read_model,
    hardline_block_reason_for_argv,
)


ROUTE = "/api/runtime/hardline-command-blocklist"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_HARDLINE_COMMAND_BLOCKLIST.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_hardline_command_blocklist.py"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_hardline_command_blocklist_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("hardline command blocklist route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-hardline-command-blocklist":
        failures.append("hardline command blocklist CLI ref is stale")
    if not read_model.non_overridable_floor or read_model.override_bypass_permitted:
        failures.append("hardline command floor is not non-overridable")
    if read_model.command_execution_performed:
        failures.append("hardline command posture performed command execution")
    if read_model.raw_command_text_persisted or read_model.raw_command_output_persisted:
        failures.append("hardline command posture persisted raw command material")
    missing_blocked = set(RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")
    if read_model.denied_classification_count < 10:
        failures.append("hardline command test corpus is too small")
    if read_model.allowed_classification_count < 2:
        failures.append("hardline command allowed-shape corpus is missing")
    for argv in [
        ("rm", "-rf", "shape-ref"),
        ("git", "push"),
        ("python", "-c", "shape-ref"),
        ("curl", "https://example.invalid"),
    ]:
        reason = hardline_block_reason_for_argv(argv)
        if not reason or not reason.startswith(RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE):
            failures.append(f"hardline classifier failed for {argv[0]}")
    if hardline_block_reason_for_argv(("make", "frontend-check")) is not None:
        failures.append("hardline classifier denied current frontend check shape")

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
        failures.append("API manifest missing hardline command blocklist route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("hardline command blocklist route side-effect classification is stale")
    elif route.route_classification != "local_sensitive":
        failures.append("hardline command blocklist route classification is stale")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-hardline-command-blocklist",
        "runtime_hardline_command_blocklist",
        "raw_command_text_omitted",
        "runner_invocation_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, TEST]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-strength",
            "Repo-safe",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            ROUTE,
            "inspect-hardline-command-blocklist",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-hardline-command-blocklist",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("hardline command CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        if payload["runtime_hardline_command_blocklist"]["route_ref"] != f"GET {ROUTE}":
            failures.append("hardline command CLI returned stale route ref")
        if payload["runner_invocation_performed"] is not False:
            failures.append("hardline command CLI claims runner invocation")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 25 hardline command blocklist verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
