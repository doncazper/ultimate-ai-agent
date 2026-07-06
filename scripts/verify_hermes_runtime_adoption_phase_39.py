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
    RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS,
    build_runtime_result_classification_read_model,
)


ROUTE = "/api/runtime/result-classification"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_RESULT_CLASSIFICATION.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/result_classification.py"
TEST = ROOT / "tests/test_hermes_runtime_result_classification.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_result_classification_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("result classification route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-result-classification":
        failures.append("result classification CLI ref is stale")
    if read_model.status != "taxonomy_read_model_only":
        failures.append("result classification posture is not taxonomy-only")
    if read_model.classification_count != 7:
        failures.append("result classification lacks expected taxonomy")
    for label, count in {
        "evidence": read_model.evidence_count,
        "mutation": read_model.mutation_count,
        "warning": read_model.warning_count,
        "blocked": read_model.blocked_count,
        "proposal": read_model.proposal_count,
        "diagnostic": read_model.diagnostic_count,
        "untrusted": read_model.untrusted_data_count,
    }.items():
        if count != 1:
            failures.append(f"{label} classification count drifted")

    unsafe_flags = {
        "tool output as truth": read_model.tool_output_as_truth_enabled,
        "action authority": read_model.action_authority_enabled,
        "mutation without receipt": read_model.mutation_without_receipt_enabled,
        "unverified evidence promotion": (
            read_model.unverified_evidence_promotion_enabled
        ),
        "raw output persistence": read_model.raw_output_persisted,
        "provider payload persistence": read_model.provider_payload_persisted,
        "control center authority mint": read_model.control_center_mints_authority,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")

    missing_blocked = set(RUNTIME_RESULT_CLASSIFICATION_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(
            f"missing result classification blockers: {sorted(missing_blocked)}"
        )

    for record in read_model.classifications:
        if record.tool_output_as_truth_enabled or record.action_authority_enabled:
            failures.append(f"record grants truth/action: {record.classification_ref}")
        if record.mutation_without_receipt_enabled:
            failures.append(f"record allows mutation without receipt: {record.classification_ref}")
        if record.raw_output_persisted or record.provider_payload_persisted:
            failures.append(f"record persists raw output: {record.classification_ref}")

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
        failures.append("API manifest missing result classification route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("result classification route side-effect drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("result classification route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-result-classification",
        "runtime_result_classification",
        "classification_only",
        "tool_output_as_truth",
        "action_authority_granted",
        "mutation_without_receipt_allowed",
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
            "inspect-result-classification",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-result-classification", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("result classification CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        if payload["tool_output_as_truth"] is not False:
            failures.append("CLI claims tool output as truth")
        if payload["action_authority_granted"] is not False:
            failures.append("CLI claims action authority")
        if payload["runtime_result_classification"]["route_ref"] != f"GET {ROUTE}":
            failures.append("CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 39 result classification verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
