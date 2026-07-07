#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS,
    RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF,
    build_runtime_plugin_metadata_posture_read_model,
)

DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_PLUGIN_METADATA_POSTURE.md"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/plugin_metadata_posture.py"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_plugin_metadata_posture.py"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_plugin_metadata_posture_read_model()

    if read_model.status != "metadata_contract_only":
        failures.append("plugin metadata status is not metadata-only")
    if read_model.route_ref != RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF:
        failures.append("plugin metadata route ref drifted")
    if read_model.cli_ref != "uaa runtime inspect-plugin-metadata-posture":
        failures.append("plugin metadata CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF
    ):
        failures.append("plugin metadata AuthorityState mapping drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("plugin metadata posture inspection is not allowed")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("plugin metadata active lease reason missing")
    if not read_model.unsupported_adapter_refs:
        failures.append("plugin metadata unsupported adapter refs missing")
    if read_model.surface_count != 7:
        failures.append("plugin metadata surface count drifted")
    if read_model.blocked_surface_count != read_model.surface_count:
        failures.append("not every plugin surface is blocked")

    denied_flags = {
        "runtime import": read_model.runtime_import_enabled,
        "hook execution": read_model.hook_execution_enabled,
        "package install": read_model.package_install_enabled,
        "marketplace execution": read_model.marketplace_content_execution_enabled,
        "plugin code": read_model.plugin_code_execution_enabled,
        "connector write": read_model.connector_write_enabled,
        "provider call": read_model.provider_call_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "raw manifest": read_model.raw_manifest_persisted,
        "control center authority": read_model.control_center_mints_authority,
    }
    for label, enabled in denied_flags.items():
        if enabled:
            failures.append(f"{label} unexpectedly enabled")

    missing_blocked = set(RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")

    for surface in read_model.surfaces:
        if surface.status != "blocked_until_grant":
            failures.append(f"surface not blocked: {surface.surface_ref}")
        surface_denied = [
            surface.runtime_import_enabled,
            surface.hook_execution_enabled,
            surface.package_install_enabled,
            surface.marketplace_content_execution_enabled,
            surface.plugin_code_execution_enabled,
            surface.connector_write_enabled,
            surface.provider_call_enabled,
            surface.shell_execution_enabled,
            surface.raw_manifest_persisted,
            surface.control_center_mints_authority,
        ]
        if any(surface_denied):
            failures.append(f"surface grants authority: {surface.surface_ref}")

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
        "plugin runtime import",
        "hook execution",
        "package installation",
        "marketplace content execution",
        "GET /api/runtime/plugin-metadata-posture",
        "Planning text and metadata visibility do not grant",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-plugin-metadata-posture",
        "runtime_plugin_metadata_posture",
        "authority_state_mapping_ref",
        "authority_state_decision_outcome",
        "runtime_import_performed",
        "hook_execution_performed",
        "package_install_performed",
        "plugin_code_execution_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    product_truth = PRODUCT_TRUTH.read_text(encoding="utf-8")
    for expected in [
        "Hermes Runtime Adoption Phase 44",
        "UAA_HERMES_RUNTIME_PLUGIN_METADATA_POSTURE.md",
        "plugin_metadata_posture.py",
        "inspect-plugin-metadata-posture",
    ]:
        if expected not in product_truth:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime plugin metadata posture" not in DOC_INDEX.read_text(
        encoding="utf-8"
    ):
        failures.append("documentation index missing plugin metadata entry")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-plugin-metadata-posture", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("plugin metadata CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_plugin_metadata_posture"]
        for field in [
            "runtime_import_performed",
            "hook_execution_performed",
            "package_install_performed",
            "marketplace_content_execution_performed",
            "plugin_code_execution_performed",
            "connector_write_performed",
            "provider_call_performed",
            "shell_execution_performed",
        ]:
            if payload[field] is not False:
                failures.append(f"CLI claims {field}")
        if read_model_payload["surface_count"] != 7:
            failures.append("CLI returned stale surface count")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF
        ):
            failures.append("CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("CLI returned stale AuthorityState decision")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 44 plugin metadata verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
