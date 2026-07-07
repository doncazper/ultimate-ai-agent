#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS,
    RUNTIME_REMOTE_EXECUTION_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_REMOTE_EXECUTION_POSTURE_ROUTE_REF,
    build_runtime_remote_execution_posture_read_model,
)

DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_REMOTE_EXECUTION_POSTURE.md"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/remote_execution_posture.py"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_remote_execution_posture.py"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_remote_execution_posture_read_model()

    if read_model.status != "capability_map_only":
        failures.append("remote execution status is not capability-map-only")
    if read_model.route_ref != RUNTIME_REMOTE_EXECUTION_POSTURE_ROUTE_REF:
        failures.append("remote execution route ref drifted")
    if read_model.cli_ref != "uaa runtime inspect-remote-execution-posture":
        failures.append("remote execution CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_REMOTE_EXECUTION_POSTURE_AUTHORITY_MAPPING_REF
    ):
        failures.append("remote execution AuthorityState mapping drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("remote execution posture inspection is not allowed")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("remote execution active lease reason missing")
    if not read_model.unsupported_adapter_refs:
        failures.append("remote execution unsupported adapter refs missing")
    if read_model.backend_count != 6:
        failures.append("remote execution backend count drifted")
    if read_model.blocked_backend_count != read_model.backend_count:
        failures.append("not every execution backend is blocked")

    denied_flags = {
        "remote execution": read_model.remote_execution_enabled,
        "ssh": read_model.ssh_enabled,
        "cloud sandbox": read_model.cloud_sandbox_enabled,
        "remote shell": read_model.remote_shell_enabled,
        "file sync": read_model.file_sync_enabled,
        "remote secret": read_model.remote_secret_access_enabled,
        "remote process": read_model.remote_process_control_enabled,
        "credential material": read_model.credential_material_persisted,
        "control center authority": read_model.control_center_mints_authority,
    }
    for label, enabled in denied_flags.items():
        if enabled:
            failures.append(f"{label} unexpectedly enabled")

    missing_blocked = set(RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")

    for backend in read_model.backends:
        if backend.status != "blocked_until_authority":
            failures.append(f"backend not blocked: {backend.backend_ref}")
        backend_denied = [
            backend.remote_execution_enabled,
            backend.ssh_enabled,
            backend.cloud_sandbox_enabled,
            backend.remote_shell_enabled,
            backend.file_sync_enabled,
            backend.remote_secret_access_enabled,
            backend.remote_process_control_enabled,
            backend.credential_material_persisted,
            backend.control_center_mints_authority,
        ]
        if any(backend_denied):
            failures.append(f"backend grants authority: {backend.backend_ref}")

    for path in [DOC, CORE, CLI, TEST, PRODUCT_TRUTH, DOC_INDEX]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    doc_text = DOC.read_text(encoding="utf-8")
    for expected in [
        "Full-Strength",
        "Repo-Safe",
        "Blocked / Needs Authority",
        "AuthorityState",
        "Exact Authority Path",
        "SSH",
        "cloud sandboxes",
        "remote shells",
        "file sync",
        "remote secrets",
        "GET /api/runtime/remote-execution-posture",
        "Planning text and capability-map visibility do not grant",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-remote-execution-posture",
        "runtime_remote_execution_posture",
        "authority_state_mapping_ref",
        "authority_state_decision_outcome",
        "remote_execution_performed",
        "ssh_performed",
        "remote_shell_performed",
        "file_sync_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    product_truth = PRODUCT_TRUTH.read_text(encoding="utf-8")
    for expected in [
        "Hermes Runtime Adoption Phase 43",
        "UAA_HERMES_RUNTIME_REMOTE_EXECUTION_POSTURE.md",
        "remote_execution_posture.py",
        "inspect-remote-execution-posture",
    ]:
        if expected not in product_truth:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime remote execution posture" not in DOC_INDEX.read_text(
        encoding="utf-8"
    ):
        failures.append("documentation index missing remote execution entry")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-remote-execution-posture", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("remote execution CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_remote_execution_posture"]
        for field in [
            "remote_execution_performed",
            "ssh_performed",
            "cloud_sandbox_performed",
            "remote_shell_performed",
            "file_sync_performed",
            "remote_secret_access_performed",
            "remote_process_control_performed",
        ]:
            if payload[field] is not False:
                failures.append(f"CLI claims {field}")
        if read_model_payload["backend_count"] != 6:
            failures.append("CLI returned stale backend count")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_REMOTE_EXECUTION_POSTURE_AUTHORITY_MAPPING_REF
        ):
            failures.append("CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("CLI returned stale AuthorityState decision")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 43 remote execution verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
