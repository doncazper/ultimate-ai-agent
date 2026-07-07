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
    RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF,
    RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS,
    build_runtime_interrupt_redirect_read_model,
)


ROUTE = "/api/runtime/interrupt-redirect"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_INTERRUPT_REDIRECT.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/interrupt_redirect.py"
TEST = ROOT / "tests/test_hermes_runtime_interrupt_redirect.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_interrupt_redirect_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("interrupt redirect route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-interrupt-redirect":
        failures.append("interrupt redirect CLI ref is stale")
    if read_model.status != "run_control_proposal_only":
        failures.append("interrupt redirect posture is not proposal-only")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF
    ):
        failures.append("interrupt redirect AuthorityState mapping is stale")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("interrupt redirect AuthorityState decision must allow read")
    if read_model.authority_state_status != "implemented_authority_bound_read_model":
        failures.append("interrupt redirect AuthorityState status drifted")
    if (
        "reason-ref:authority:active-lease-grants-domain-capability"
        not in read_model.authority_state_reason_refs
    ):
        failures.append("interrupt redirect AuthorityState reason is missing")
    if read_model.unsupported_adapter_refs:
        failures.append("interrupt redirect should not expose unsupported adapters")
    if read_model.proposal_count != 5:
        failures.append("interrupt redirect lacks expected actions")
    if read_model.read_only_proposal_count != 2:
        failures.append("interrupt redirect proposal count drifted")
    if read_model.approval_required_future_lane_count != 2:
        failures.append("interrupt redirect future lane count drifted")
    if read_model.blocked_count != 1:
        failures.append("interrupt redirect blocked count drifted")

    unsafe_flags = {
        "live stop POST": read_model.live_stop_post_enabled,
        "process kill": read_model.process_kill_enabled,
        "runtime mutation": read_model.runtime_mutation_enabled,
        "background autonomy": read_model.background_autonomy_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "provider call": read_model.provider_call_enabled,
        "browser automation": read_model.browser_automation_enabled,
        "connector write": read_model.connector_write_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw runtime payload persistence": read_model.raw_runtime_payload_persisted,
        "raw log persistence": read_model.raw_log_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")

    missing_blocked = set(RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing interrupt redirect blockers: {sorted(missing_blocked)}")

    for proposal in read_model.proposals:
        if proposal.live_stop_post_enabled or proposal.process_kill_enabled:
            failures.append(f"proposal can stop/kill runtime: {proposal.action_ref}")
        if proposal.runtime_mutation_enabled or proposal.background_autonomy_enabled:
            failures.append(f"proposal mutates runtime/autonomy: {proposal.action_ref}")
        if proposal.shell_execution_enabled or proposal.provider_call_enabled:
            failures.append(f"proposal executes shell/provider: {proposal.action_ref}")
        if proposal.browser_automation_enabled or proposal.connector_write_enabled:
            failures.append(f"proposal has browser/connector authority: {proposal.action_ref}")
        if proposal.raw_runtime_payload_persisted or proposal.raw_log_persisted:
            failures.append(f"proposal persists raw runtime data: {proposal.action_ref}")

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
        failures.append("API manifest missing interrupt redirect route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("interrupt redirect route side-effect drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("interrupt redirect route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-interrupt-redirect",
        "runtime_interrupt_redirect",
        "proposal_only",
        "live_stop_post_performed",
        "process_kill_performed",
        "runtime_mutation_performed",
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
            RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF,
            ROUTE,
            "inspect-interrupt-redirect",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-interrupt-redirect",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("interrupt redirect CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_interrupt_redirect"]
        for flag in [
            "live_stop_post_performed",
            "process_kill_performed",
            "runtime_mutation_performed",
            "background_autonomy_performed",
            "shell_execution_performed",
            "provider_call_performed",
            "browser_automation_performed",
            "connector_write_performed",
        ]:
            if payload[flag] is not False:
                failures.append(f"interrupt redirect CLI claims {flag}")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("interrupt redirect CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF
        ):
            failures.append("interrupt redirect CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("interrupt redirect CLI returned unsafe AuthorityState decision")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 37 interrupt redirect verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
