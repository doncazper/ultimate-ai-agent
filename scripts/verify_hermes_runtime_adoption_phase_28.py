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
    RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_MAPPING_REF,
    RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS,
    build_runtime_doctor_diagnostics_read_model,
)


ROUTE = "/api/runtime/doctor-diagnostics"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_DOCTOR_DIAGNOSTICS.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/doctor_diagnostics.py"
TEST = ROOT / "tests/test_hermes_runtime_doctor_diagnostics.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_doctor_diagnostics_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("doctor diagnostics route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-doctor-diagnostics":
        failures.append("doctor diagnostics CLI ref is stale")
    if read_model.status != "read_only_diagnostics_posture":
        failures.append("doctor diagnostics posture is not read-only")
    if (
        read_model.authority_state_route_ref
        != RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_STATE_ROUTE_REF
    ):
        failures.append("doctor diagnostics AuthorityState route ref drifted")
    if (
        read_model.authority_state_cli_ref
        != RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_STATE_CLI_REF
    ):
        failures.append("doctor diagnostics AuthorityState CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_MAPPING_REF
    ):
        failures.append("doctor diagnostics AuthorityState mapping ref drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("doctor diagnostics read model must allow read-only inspection")
    if (
        "adapter-ref:runtime-doctor-install:not-implemented"
        not in read_model.unsupported_adapter_refs
    ):
        failures.append("doctor diagnostics unsupported install adapter missing")
    if read_model.diagnostic_count < 8:
        failures.append("doctor diagnostics lacks required diagnostic domains")
    if read_model.blocked_count < 1 or read_model.review_count < 1:
        failures.append("doctor diagnostics lacks blocked/review posture")
    unsafe_flags = {
        "install": read_model.install_enabled,
        "service start": read_model.service_start_enabled,
        "credential write": read_model.credential_write_enabled,
        "runtime config mutation": read_model.runtime_config_mutation_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw log persistence": read_model.raw_log_persisted,
        "raw path persistence": read_model.raw_local_path_persisted,
        "provider payload persistence": read_model.provider_payload_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_DOCTOR_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing doctor diagnostics blocked refs: {sorted(missing_blocked)}")
    for item in read_model.diagnostics:
        if item.install_performed or item.service_start_performed:
            failures.append(f"diagnostic item mutates local setup: {item.diagnostic_ref}")
        if item.credential_write_performed or item.runtime_config_mutation_performed:
            failures.append(f"diagnostic item writes runtime config: {item.diagnostic_ref}")
        if item.raw_log_persisted or item.raw_local_path_persisted:
            failures.append(f"diagnostic item persists raw material: {item.diagnostic_ref}")
        if item.provider_payload_persisted:
            failures.append(f"diagnostic item persists provider payload: {item.diagnostic_ref}")

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
        failures.append("API manifest missing doctor diagnostics route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("doctor diagnostics route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("doctor diagnostics route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-doctor-diagnostics",
        "runtime_doctor_diagnostics",
        "redacted_status_only",
        "raw_logs_omitted",
        "service_start_performed",
        "authority_state",
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
            "inspect-doctor-diagnostics",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-doctor-diagnostics",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("doctor diagnostics CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_doctor_diagnostics"]
        authority_state = payload.get("authority_state", {})
        if (
            authority_state.get("mapping_ref")
            != RUNTIME_DOCTOR_DIAGNOSTICS_AUTHORITY_MAPPING_REF
        ):
            failures.append("doctor diagnostics CLI AuthorityState mapping drifted")
        if authority_state.get("decision_outcome") != "allow":
            failures.append("doctor diagnostics CLI AuthorityState outcome drifted")
        if payload["install_performed"] is not False:
            failures.append("doctor diagnostics CLI claims install")
        if payload["service_start_performed"] is not False:
            failures.append("doctor diagnostics CLI claims service start")
        if payload["runtime_config_mutation_performed"] is not False:
            failures.append("doctor diagnostics CLI claims runtime config mutation")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("doctor diagnostics CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 28 doctor diagnostics verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
