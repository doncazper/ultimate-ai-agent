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
    RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS,
    RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF,
    build_runtime_approval_bridge_read_model,
)


ROUTE = "/api/runtime/approval-bridge"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_FAIL_CLOSED_APPROVAL_TIMEOUTS.md"
APPROVAL_DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_APPROVAL_BRIDGE.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
COMMAND_CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/command.py"
TEST = ROOT / "tests/test_hermes_runtime_approval_bridge.py"
CONTRACT_TEST = ROOT / "tests/test_governed_runtime_contracts.py"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_approval_bridge_read_model()
    posture = read_model.fail_closed_timeout_posture

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("approval bridge route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-approval-bridge":
        failures.append("approval bridge CLI ref is stale")
    if (
        read_model.authority_state_mapping_ref
        != "lane-ref:runtime-approval-bridge-read-model"
    ):
        failures.append("approval bridge AuthorityState mapping ref drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("approval bridge read-only authority decision drifted")
    if "adapter-ref:runtime-approval-resolution-send:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("approval bridge unsupported adapter refs drifted")
    if posture.policy_ref != RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF:
        failures.append("fail-closed policy ref drifted")
    if not posture.expired_waits_default_to_deny:
        failures.append("expired waits do not default to deny")
    if not posture.ambiguous_waits_default_to_deny:
        failures.append("ambiguous waits do not default to deny")
    if not posture.explicit_expiration_required:
        failures.append("explicit expiration is not required")
    unsafe_flags = {
        "auto approve": posture.auto_approve_enabled,
        "approve all": posture.approve_all_enabled,
        "standing broad authority": posture.standing_broad_authority_enabled,
        "expired grant reuse": posture.expired_grant_reuse_enabled,
        "ambiguous grant": posture.ambiguous_grant_enabled,
        "approval resolution sent": posture.approval_resolution_sent,
        "control center authority mint": posture.control_center_mints_authority,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing fail-closed blocked refs: {sorted(missing_blocked)}")

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
        failures.append("API manifest missing approval bridge route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("approval bridge route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("approval bridge route classification drifted")

    command_text = COMMAND_CORE.read_text(encoding="utf-8")
    if "RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_EXPIRED" not in command_text:
        failures.append("command core missing expired approval denial")
    if "RuntimeInvocationStatus.approval_expired.value" not in command_text:
        failures.append("command core does not check expired approval status")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "fail_closed_timeout_posture",
        "fail_closed_timeout_policy_ref",
        "auto_approve_enabled",
        "approve_all_enabled",
        "standing_broad_authority_enabled",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, APPROVAL_DOC, TEST, CONTRACT_TEST]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-Strength",
            "Repo-Safe",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            "fail-closed",
            "approve-all",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-approval-bridge",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("approval bridge CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_approval_bridge"]
        cli_posture = read_model_payload["fail_closed_timeout_posture"]
        if payload["execution_performed"] is not False:
            failures.append("approval bridge CLI claims execution")
        if payload["approval_resolution_sent"] is not False:
            failures.append("approval bridge CLI claims approval resolution")
        if payload["approve_all_enabled"] is not False:
            failures.append("approval bridge CLI claims approve-all")
        if (
            payload.get("authority_state", {}).get("mapping_ref")
            != "lane-ref:runtime-approval-bridge-read-model"
        ):
            failures.append("approval bridge CLI mapping ref drifted")
        if cli_posture["policy_ref"] != RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF:
            failures.append("approval bridge CLI returned stale policy ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 26 fail-closed approval verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
