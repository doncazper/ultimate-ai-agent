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
    RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF,
    RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS,
    build_runtime_slash_command_registry_read_model,
)


ROUTE = "/api/runtime/slash-command-registry"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_SLASH_COMMAND_REGISTRY.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/slash_command_registry.py"
TEST = ROOT / "tests/test_hermes_runtime_slash_command_registry.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_slash_command_registry_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("slash command registry route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-slash-command-registry":
        failures.append("slash command registry CLI ref is stale")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF
    ):
        failures.append("slash command registry authority mapping ref is stale")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("slash command registry metadata read should be allowed")
    if read_model.authority_state_status != "implemented_authority_bound_read_model":
        failures.append("slash command registry authority status is not implemented")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("slash command registry lacks active-lease reason")
    if read_model.unsupported_adapter_refs:
        failures.append("slash command registry metadata should not list adapters")
    if read_model.status != "metadata_registry_all_commands_disabled":
        failures.append("slash command registry posture is not metadata-only")
    if read_model.command_count != 6:
        failures.append("slash command registry lacks expected commands")
    if read_model.disabled_count != 2:
        failures.append("slash command registry disabled count drifted")
    if read_model.blocked_count != 1:
        failures.append("slash command registry blocked count drifted")
    unsafe_flags = {
        "chat trigger": read_model.chat_trigger_enabled,
        "runtime invocation": read_model.runtime_invocation_enabled,
        "state mutation": read_model.state_mutation_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "provider call": read_model.provider_call_enabled,
        "browser automation": read_model.browser_automation_enabled,
        "connector write": read_model.connector_write_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw prompt persistence": read_model.raw_prompt_persisted,
        "raw response persistence": read_model.raw_response_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(
            f"missing slash command blocked refs: {sorted(missing_blocked)}"
        )
    for command in read_model.commands:
        if command.chat_trigger_enabled or command.runtime_invocation_enabled:
            failures.append(f"command executes or invokes runtime: {command.command_ref}")
        if command.state_mutation_enabled or command.shell_execution_enabled:
            failures.append(f"command mutates state or shell: {command.command_ref}")
        if command.provider_call_enabled or command.browser_automation_enabled:
            failures.append(f"command calls provider/browser: {command.command_ref}")
        if command.connector_write_enabled:
            failures.append(f"command writes connector: {command.command_ref}")
        if command.raw_prompt_persisted or command.raw_response_persisted:
            failures.append(f"command persists raw prompt/response: {command.command_ref}")

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
        failures.append("API manifest missing slash command registry route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("slash command registry route side-effect drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("slash command registry route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-slash-command-registry",
        "runtime_slash_command_registry",
        "metadata_only",
        "command_execution_performed",
        "runtime_invocation_performed",
        "connector_write_performed",
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
            "AuthorityState",
            "Exact Authority Path",
            RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF,
            ROUTE,
            "inspect-slash-command-registry",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-slash-command-registry",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("slash command registry CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_slash_command_registry"]
        for flag in [
            "command_execution_performed",
            "runtime_invocation_performed",
            "state_mutation_performed",
            "shell_execution_performed",
            "provider_call_performed",
            "browser_automation_performed",
            "connector_write_performed",
        ]:
            if payload[flag] is not False:
                failures.append(f"slash command CLI claims {flag}")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("slash command CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF
        ):
            failures.append("slash command CLI returned stale authority mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("slash command CLI should show allowed metadata read")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 36 slash command registry verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
