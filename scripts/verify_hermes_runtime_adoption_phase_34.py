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
    RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF,
    RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS,
    build_runtime_lsp_diagnostics_read_model,
)


ROUTE = "/api/runtime/lsp-diagnostics"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_LSP_DIAGNOSTICS.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/lsp_diagnostics.py"
TEST = ROOT / "tests/test_hermes_runtime_lsp_diagnostics.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_lsp_diagnostics_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("LSP diagnostics route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-lsp-diagnostics":
        failures.append("LSP diagnostics CLI ref is stale")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF
    ):
        failures.append("LSP diagnostics authority mapping ref is stale")
    if read_model.authority_state_decision_outcome != "deny":
        failures.append("LSP diagnostics authority decision must deny by default")
    if read_model.authority_state_status != "planned_unsupported_adapter":
        failures.append("LSP diagnostics authority status must remain unsupported")
    if "reason-ref:authority:adapter-unsupported" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("LSP diagnostics authority decision lacks adapter reason")
    if "adapter-ref:lsp-server-launch:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("LSP diagnostics server launch adapter ref missing")
    if read_model.status != "diagnostic_evidence_placeholder_posture":
        failures.append("LSP diagnostics posture is not evidence-only")
    if read_model.diagnostic_count != 3:
        failures.append("LSP diagnostics lacks expected diagnostic contracts")
    if read_model.proof_ready_count != 1:
        failures.append("LSP diagnostics lacks proof-ready placeholder count")
    if read_model.execution_blocked_count != 1:
        failures.append("LSP diagnostics lacks blocked execution posture")
    unsafe_flags = {
        "language server": read_model.language_server_started,
        "dependency install": read_model.dependency_install_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "file read": read_model.file_read_enabled,
        "file write": read_model.file_write_enabled,
        "provider call": read_model.provider_call_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw path persistence": read_model.raw_path_persisted,
        "raw diagnostic payload persistence": (
            read_model.raw_diagnostic_payload_persisted
        ),
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_LSP_DIAGNOSTICS_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing LSP diagnostics blocked refs: {sorted(missing_blocked)}")
    for diagnostic in read_model.diagnostics:
        if diagnostic.language_server_started or diagnostic.dependency_install_enabled:
            failures.append(f"diagnostic exposes LSP/install: {diagnostic.diagnostic_ref}")
        if diagnostic.shell_execution_enabled or diagnostic.provider_call_enabled:
            failures.append(f"diagnostic exposes shell/provider: {diagnostic.diagnostic_ref}")
        if diagnostic.file_read_enabled or diagnostic.file_write_enabled:
            failures.append(f"diagnostic exposes file access: {diagnostic.diagnostic_ref}")
        if diagnostic.raw_path_persisted or diagnostic.raw_diagnostic_payload_persisted:
            failures.append(f"diagnostic persists raw data: {diagnostic.diagnostic_ref}")

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
        failures.append("API manifest missing LSP diagnostics route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("LSP diagnostics route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("LSP diagnostics route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-lsp-diagnostics",
        "runtime_lsp_diagnostics",
        "evidence_only",
        "raw_diagnostic_payloads_omitted",
        "language_server_started",
        "file_read_performed",
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
            RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF,
            ROUTE,
            "inspect-lsp-diagnostics",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-lsp-diagnostics",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("LSP diagnostics CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_lsp_diagnostics"]
        authority_state = payload.get("authority_state")
        if not isinstance(authority_state, dict):
            failures.append("LSP diagnostics CLI missing authority state")
        elif (
            authority_state.get("mapping_ref")
            != RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF
        ):
            failures.append("LSP diagnostics CLI authority mapping drifted")
        elif authority_state.get("decision_outcome") != "deny":
            failures.append("LSP diagnostics CLI authority decision drifted")
        if payload["language_server_started"] is not False:
            failures.append("LSP diagnostics CLI claims server launch")
        if payload["dependency_install_performed"] is not False:
            failures.append("LSP diagnostics CLI claims dependency install")
        if payload["shell_execution_performed"] is not False:
            failures.append("LSP diagnostics CLI claims shell execution")
        if payload["file_read_performed"] is not False:
            failures.append("LSP diagnostics CLI claims file read")
        if payload["file_write_performed"] is not False:
            failures.append("LSP diagnostics CLI claims file write")
        if payload["provider_call_performed"] is not False:
            failures.append("LSP diagnostics CLI claims provider call")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("LSP diagnostics CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_LSP_DIAGNOSTICS_AUTHORITY_MAPPING_REF
        ):
            failures.append("LSP diagnostics CLI returned stale authority mapping")
        if read_model_payload["authority_state_decision_outcome"] != "deny":
            failures.append("LSP diagnostics CLI should show denied authority")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 34 LSP diagnostics verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
