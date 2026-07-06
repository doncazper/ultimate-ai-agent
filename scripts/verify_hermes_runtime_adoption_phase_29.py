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
    RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS,
    build_runtime_session_continuity_read_model,
)


ROUTE = "/api/runtime/session-continuity"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_SESSION_CONTINUITY.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/session_continuity.py"
TEST = ROOT / "tests/test_hermes_runtime_session_continuity.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_session_continuity_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("session continuity route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-session-continuity":
        failures.append("session continuity CLI ref is stale")
    if read_model.status != "read_only_multi_surface_session_continuity_posture":
        failures.append("session continuity posture is not read-only")
    if read_model.surface_count < 5:
        failures.append("session continuity lacks required surfaces")
    if read_model.stale_count < 1 or read_model.conflict_count < 1:
        failures.append("session continuity lacks stale/conflict posture")
    if read_model.blocked_count < 1:
        failures.append("session continuity lacks blocked posture")
    unsafe_flags = {
        "external message gateway": read_model.external_message_gateway_enabled,
        "account sync": read_model.account_sync_enabled,
        "connector write": read_model.connector_write_enabled,
        "remote session": read_model.remote_session_enabled,
        "raw transcript persistence": read_model.raw_transcript_persisted,
        "raw prompt persistence": read_model.raw_prompt_persisted,
        "raw response persistence": read_model.raw_response_persisted,
        "provider payload persistence": read_model.raw_provider_payload_persisted,
        "control center authority mint": read_model.control_center_mints_authority,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing session continuity blocked refs: {sorted(missing_blocked)}")
    for surface in read_model.surfaces:
        if surface.external_message_gateway_enabled or surface.account_sync_enabled:
            failures.append(f"surface enables external sync: {surface.surface_ref}")
        if surface.connector_write_enabled or surface.remote_session_enabled:
            failures.append(f"surface enables remote/connector authority: {surface.surface_ref}")
        if surface.raw_prompt_persisted or surface.raw_response_persisted:
            failures.append(f"surface persists raw turn content: {surface.surface_ref}")
        if surface.raw_provider_payload_persisted or surface.raw_transcript_persisted:
            failures.append(f"surface persists raw runtime material: {surface.surface_ref}")
        if surface.control_center_mints_authority:
            failures.append(f"surface lets Control Center mint authority: {surface.surface_ref}")

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
        failures.append("API manifest missing session continuity route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("session continuity route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("session continuity route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-session-continuity",
        "runtime_session_continuity",
        "redacted_status_only",
        "external_message_gateway_performed",
        "remote_session_performed",
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
            "inspect-session-continuity",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-session-continuity",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("session continuity CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_session_continuity"]
        if payload["external_message_gateway_performed"] is not False:
            failures.append("session continuity CLI claims external message gateway")
        if payload["account_sync_performed"] is not False:
            failures.append("session continuity CLI claims account sync")
        if payload["connector_write_performed"] is not False:
            failures.append("session continuity CLI claims connector write")
        if payload["remote_session_performed"] is not False:
            failures.append("session continuity CLI claims remote session")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("session continuity CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 29 session continuity verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
