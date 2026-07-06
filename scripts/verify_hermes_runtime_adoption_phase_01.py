#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    build_runtime_delegation_adapter_read_model,
)


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_delegation_adapter_read_model()
    if read_model.runtime_kind != "hermes_agent":
        failures.append("Phase 01 runtime kind must be hermes_agent.")
    if not read_model.uaa_controls_authority:
        failures.append("UAA must remain authority owner.")
    if read_model.control_center_talks_directly_to_runtime:
        failures.append("Control Center must not talk directly to Hermes.")
    denied_flags = {
        "live_run_submission_enabled": read_model.live_run_submission_enabled,
        "runtime_model_calls_enabled": read_model.runtime_model_calls_enabled,
        "provider_sdk_calls_enabled": read_model.provider_sdk_calls_enabled,
        "tool_execution_enabled": read_model.tool_execution_enabled,
        "shell_execution_enabled": read_model.shell_execution_enabled,
        "browser_automation_enabled": read_model.browser_automation_enabled,
        "connector_write_enabled": read_model.connector_write_enabled,
        "background_autonomy_enabled": read_model.background_autonomy_enabled,
        "production_authority_enabled": read_model.production_authority_enabled,
        "raw_provider_payload_persisted": read_model.raw_provider_payload_persisted,
        "raw_local_path_persisted": read_model.raw_local_path_persisted,
    }
    for flag, value in denied_flags.items():
        if value:
            failures.append(f"{flag} must remain false.")
    if "blocked-authority:runtime-delegation-live-run-submission" not in (
        read_model.blocked_reason_refs
    ):
        failures.append("Live run submission blocker is missing.")

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-delegation-adapter",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if cli.returncode != 0:
        failures.append("CLI inspection failed.")
    else:
        payload = json.loads(cli.stdout)
        if payload.get("execution_performed") is not False:
            failures.append("CLI payload must prove no execution was performed.")
        if payload.get("runtime_delegation_adapter", {}).get("adapter_ref") != (
            read_model.adapter_ref
        ):
            failures.append("CLI and core adapter refs diverged.")

    if failures:
        print("Hermes runtime adoption Phase 01 verifier failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: Hermes runtime adoption Phase 01 delegation adapter is readiness-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
