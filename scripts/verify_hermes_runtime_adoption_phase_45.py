#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF,
    build_runtime_skill_marketplace_posture_read_model,
)

DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_SKILL_MARKETPLACE_POSTURE.md"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/skill_marketplace_posture.py"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_skill_marketplace_posture.py"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
REPORT = ROOT / "reports/hermes_runtime_adoption/2026-07-06_hermes_runtime_adoption_report.md"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_skill_marketplace_posture_read_model()

    if read_model.status != "signal_review_adaptation_only":
        failures.append("skill marketplace status is not signal/review/adaptation only")
    if read_model.route_ref != RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF:
        failures.append("skill marketplace route ref drifted")
    if read_model.cli_ref != "uaa runtime inspect-skill-marketplace-posture":
        failures.append("skill marketplace CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF
    ):
        failures.append("skill marketplace AuthorityState mapping drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("skill marketplace posture inspection is not allowed")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        read_model.authority_state_reason_refs
    ):
        failures.append("skill marketplace active lease reason missing")
    if not read_model.unsupported_adapter_refs:
        failures.append("skill marketplace unsupported adapter refs missing")
    if read_model.stage_count != 7:
        failures.append("skill marketplace stage count drifted")
    if read_model.blocked_execution_count != 1:
        failures.append("skill marketplace blocked execution count drifted")

    denied_flags = {
        "external popularity trust": read_model.external_popularity_is_trust,
        "external code execution": read_model.external_code_execution_enabled,
        "direct install": read_model.direct_marketplace_install_enabled,
        "runtime import": read_model.runtime_import_enabled,
        "automatic skill write": read_model.automatic_skill_write_enabled,
        "provider call": read_model.provider_call_enabled,
        "browser automation": read_model.browser_automation_enabled,
        "connector write": read_model.connector_write_enabled,
        "raw marketplace payload": read_model.raw_marketplace_payload_persisted,
        "control center authority": read_model.control_center_mints_authority,
    }
    for label, enabled in denied_flags.items():
        if enabled:
            failures.append(f"{label} unexpectedly enabled")

    missing_blocked = set(RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")

    for stage in read_model.stages:
        stage_denied = [
            stage.external_popularity_is_trust,
            stage.external_code_execution_enabled,
            stage.direct_marketplace_install_enabled,
            stage.runtime_import_enabled,
            stage.automatic_skill_write_enabled,
            stage.provider_call_enabled,
            stage.browser_automation_enabled,
            stage.connector_write_enabled,
            stage.raw_marketplace_payload_persisted,
            stage.control_center_mints_authority,
        ]
        if any(stage_denied):
            failures.append(f"stage grants authority: {stage.stage_ref}")

    for path in [DOC, CORE, CLI, TEST, PRODUCT_TRUTH, DOC_INDEX, REPORT]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    doc_text = DOC.read_text(encoding="utf-8")
    for expected in [
        "Full-Strength",
        "Repo-Safe",
        "Blocked / Needs Authority",
        "AuthorityState",
        "Exact Authority Path",
        "discovery signals only, not trust",
        "reviewed UAA-owned adaptation",
        "GET /api/runtime/skill-marketplace-posture",
        "Planning text and external discovery signals do not grant",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-skill-marketplace-posture",
        "runtime_skill_marketplace_posture",
        "authority_state_mapping_ref",
        "authority_state_decision_outcome",
        "external_popularity_trusted",
        "direct_marketplace_install_performed",
        "automatic_skill_write_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    product_truth = PRODUCT_TRUTH.read_text(encoding="utf-8")
    for expected in [
        "Hermes Runtime Adoption Phase 45",
        "UAA_HERMES_RUNTIME_SKILL_MARKETPLACE_POSTURE.md",
        "skill_marketplace_posture.py",
        "inspect-skill-marketplace-posture",
    ]:
        if expected not in product_truth:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime skill marketplace posture" not in DOC_INDEX.read_text(
        encoding="utf-8"
    ):
        failures.append("documentation index missing skill marketplace entry")

    if REPORT.exists():
        report_text = REPORT.read_text(encoding="utf-8")
        for expected in [
            "Phases",
            "PRs And Merge SHAs",
            "Authority Promoted",
            "Authority Still Blocked",
            "Hermes Patterns Borrowed",
            "Hermes Patterns Not Merged",
            "Final Git Status",
        ]:
            if expected not in report_text:
                failures.append(f"final report missing {expected}")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-skill-marketplace-posture", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("skill marketplace CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_skill_marketplace_posture"]
        for field in [
            "external_popularity_trusted",
            "external_code_execution_performed",
            "direct_marketplace_install_performed",
            "runtime_import_performed",
            "automatic_skill_write_performed",
            "provider_call_performed",
            "browser_automation_performed",
            "connector_write_performed",
        ]:
            if payload[field] is not False:
                failures.append(f"CLI claims {field}")
        if read_model_payload["stage_count"] != 7:
            failures.append("CLI returned stale stage count")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF
        ):
            failures.append("CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "allow":
            failures.append("CLI returned stale AuthorityState decision")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 45 skill marketplace verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
