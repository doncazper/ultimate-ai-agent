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
    RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF,
    RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS,
    build_runtime_subagent_isolation_read_model,
)


ROUTE = "/api/runtime/subagent-isolation"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_SUBAGENT_ISOLATION.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/subagent_isolation.py"
TEST = ROOT / "tests/test_hermes_runtime_subagent_isolation.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_subagent_isolation_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("subagent isolation route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-subagent-isolation":
        failures.append("subagent isolation CLI ref is stale")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
    ):
        failures.append("subagent isolation authority mapping ref is stale")
    if read_model.authority_state_decision_outcome != "deny":
        failures.append("subagent isolation authority decision must deny by default")
    if read_model.authority_state_status != "planned_unsupported_adapter":
        failures.append("subagent isolation authority status must remain unsupported")
    if "reason-ref:authority:adapter-unsupported" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("subagent isolation authority decision lacks adapter reason")
    if "adapter-ref:subagent-live-dispatch:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("subagent isolation live dispatch adapter ref missing")
    if read_model.status != "identity_isolation_readiness":
        failures.append("subagent isolation posture is not readiness state")
    if read_model.role_count != 3:
        failures.append("subagent isolation lacks expected role contracts")
    if read_model.review_artifact_count < 3:
        failures.append("subagent isolation lacks review artifacts")
    if read_model.blocked_dispatch_count < 1:
        failures.append("subagent isolation lacks blocked dispatch posture")
    unsafe_flags = {
        "live dispatch": read_model.live_dispatch_enabled,
        "background fanout": read_model.background_fanout_enabled,
        "cross-agent memory transfer": (
            read_model.cross_agent_memory_transfer_enabled
        ),
        "tool sharing": read_model.tool_sharing_enabled,
        "autonomous delegation": read_model.autonomous_delegation_enabled,
        "provider call": read_model.provider_call_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "connector write": read_model.connector_write_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw transcript persistence": read_model.raw_transcript_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(
            f"missing subagent isolation blocked refs: {sorted(missing_blocked)}"
        )
    for role in read_model.roles:
        if role.live_dispatch_enabled or role.background_fanout_enabled:
            failures.append(f"role exposes dispatch/fanout: {role.role_ref}")
        if role.cross_agent_memory_transfer_enabled or role.tool_sharing_enabled:
            failures.append(f"role shares memory/tools: {role.role_ref}")
        if role.provider_call_enabled or role.shell_execution_enabled:
            failures.append(f"role enables provider/shell authority: {role.role_ref}")
        if role.connector_write_enabled or role.raw_transcript_persisted:
            failures.append(
                f"role writes externally or persists raw transcript: {role.role_ref}"
            )
    for artifact in read_model.review_artifacts:
        if artifact.raw_agent_output_persisted or artifact.executable_authority:
            failures.append(f"artifact became executable/raw: {artifact.artifact_ref}")

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
        failures.append("API manifest missing subagent isolation route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("subagent isolation route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("subagent isolation route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-subagent-isolation",
        "runtime_subagent_isolation",
        "readiness_only",
        "live_dispatch_performed",
        "background_fanout_performed",
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
            RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF,
            ROUTE,
            "inspect-subagent-isolation",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-subagent-isolation",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("subagent isolation CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_subagent_isolation"]
        if payload["live_dispatch_performed"] is not False:
            failures.append("subagent isolation CLI claims live dispatch")
        if payload["background_fanout_performed"] is not False:
            failures.append("subagent isolation CLI claims fanout")
        if payload["tool_sharing_performed"] is not False:
            failures.append("subagent isolation CLI claims tool sharing")
        if payload["connector_write_performed"] is not False:
            failures.append("subagent isolation CLI claims connector write")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("subagent isolation CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
        ):
            failures.append("subagent isolation CLI returned stale authority mapping")
        if read_model_payload["authority_state_decision_outcome"] != "deny":
            failures.append("subagent isolation CLI should show denied authority")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 32 subagent isolation verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
