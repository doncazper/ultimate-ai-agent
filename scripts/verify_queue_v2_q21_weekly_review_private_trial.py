#!/usr/bin/env python3
"""Verify Q21 Weekly CEO Review and private-trial completion evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.readiness import (  # noqa: E402
    PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES,
    PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF,
    build_private_product_loop_trial_script,
)


REPORT = ROOT / "docs/control_center/queue_v2_q21_private_trial_report_v1.json"
DOC = ROOT / "docs/control_center/QUEUE_V2_Q21_WEEKLY_REVIEW_PRIVATE_TRIAL.md"
BOARD = ROOT / "docs/kanban/current_board.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
WEEKLY_CLI = ROOT / "scripts/inspect_weekly_ceo_review.py"

REQUIRED_SURFACES = list(PRIVATE_PRODUCT_LOOP_TRIAL_REQUIRED_SURFACES)
ALLOWED_DISPOSITIONS = {
    "accepted",
    "accepted_with_limit",
    "revised_owned_follow_up",
    "blocked_owned_follow_up",
}
DENIED_FLAGS = (
    "connector_read_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "action_execution_enabled",
    "memory_write_authorized",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "runtime_authority_added",
)
UNSAFE_MARKERS = (
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "authorization:",
    "bearer ",
    "password",
    "private_key",
    "/users/",
    "/home/",
)


def _load_report() -> dict[str, Any]:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _report_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("schema_version") != (
        "queue-v2-q21-weekly-review-private-trial-report.v1"
    ):
        failures.append("Q21 report schema drifted")
    if report.get("task_ref") != (
        "dev-task:queue-v2-q21-weekly-ceo-review-private-trial"
    ):
        failures.append("Q21 report task ref drifted")
    if report.get("status") != "completed_with_owned_follow_ups":
        failures.append("Q21 report status is not completion truth")
    if report.get("private_trial_contract_ref") != (
        PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    ):
        failures.append("Q21 private-trial contract ref drifted")
    if report.get("local_private_only") is not True:
        failures.append("Q21 report is not local/private")
    if report.get("safe_refs_only") is not True:
        failures.append("Q21 report is not safe-ref-only")
    if report.get("raw_content_included") is not False:
        failures.append("Q21 report permits raw content")
    if report.get("raw_paths_included") is not False:
        failures.append("Q21 report permits raw paths")
    if report.get("raw_logs_included") is not False:
        failures.append("Q21 report permits raw logs")
    if report.get("credential_material_included") is not False:
        failures.append("Q21 report permits credential material")
    for flag in DENIED_FLAGS:
        if report.get(flag) is not False:
            failures.append(f"Q21 report enables {flag}")

    results = report.get("surface_results")
    if not isinstance(results, list):
        failures.append("Q21 surface results are missing")
        results = []
    surfaces = [row.get("surface") for row in results if isinstance(row, dict)]
    if surfaces != REQUIRED_SURFACES:
        failures.append(f"Q21 surface order drifted: {surfaces}")
    for row in results:
        if not isinstance(row, dict):
            failures.append("Q21 surface result is malformed")
            continue
        disposition = row.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            failures.append(f"Q21 surface disposition invalid: {disposition}")
        evidence_refs = row.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            failures.append(f"Q21 surface lacks evidence: {row.get('surface')}")
        if disposition != "accepted" and not row.get("follow_up_ref"):
            failures.append(
                f"Q21 non-accepted surface lacks follow-up: {row.get('surface')}"
            )

    gaps = report.get("material_gaps")
    if not isinstance(gaps, list) or not gaps:
        failures.append("Q21 material gaps are missing")
        gaps = []
    gap_refs: set[str] = set()
    for gap in gaps:
        if not isinstance(gap, dict):
            failures.append("Q21 gap row is malformed")
            continue
        gap_ref = gap.get("gap_ref")
        if not isinstance(gap_ref, str) or not gap_ref.startswith("gap-ref:"):
            failures.append("Q21 gap ref is invalid")
        elif gap_ref in gap_refs:
            failures.append(f"Q21 duplicate gap ref: {gap_ref}")
        else:
            gap_refs.add(gap_ref)
        if not str(gap.get("owner_ref", "")).startswith("owner-ref:"):
            failures.append(f"Q21 gap lacks owner: {gap_ref}")
        if not gap.get("evidence_refs"):
            failures.append(f"Q21 gap lacks evidence: {gap_ref}")
        if not gap.get("next_safe_action"):
            failures.append(f"Q21 gap lacks next safe action: {gap_ref}")
    resolved = set(report.get("resolved_in_q21_refs", []))
    if not resolved <= gap_refs:
        failures.append("Q21 resolved refs are not material gap refs")

    serialized = json.dumps(report, sort_keys=True).lower()
    for marker in UNSAFE_MARKERS:
        if marker in serialized:
            failures.append(f"Q21 report contains unsafe marker {marker!r}")
    return failures


def _weekly_cli_failures() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="queue-v2-q21-") as temp_dir:
        missing_state = Path(temp_dir) / "missing-founder-loop"
        completed = subprocess.run(
            [
                sys.executable,
                str(WEEKLY_CLI),
                "--state-dir",
                str(missing_state),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        review = payload.get("weekly_ceo_review_v1_read_model", {})
        if payload.get("storage_state") != "state_not_found_no_write":
            failures.append("Q21 Weekly Review missing-state posture drifted")
        if missing_state.exists():
            failures.append("Q21 Weekly Review created missing state")
        if review.get("status") != "state_not_found_no_write":
            failures.append("Q21 Weekly Review did not preserve empty-state truth")
        if review.get("unresolved_refs") != ["weekly-review-ref:state-not-found"]:
            failures.append("Q21 Weekly Review empty-state unresolved ref drifted")
        for flag in DENIED_FLAGS:
            if flag in review and review.get(flag) is not False:
                failures.append(f"Q21 Weekly Review enables {flag}")
    return failures


def _static_failures() -> list[str]:
    failures: list[str] = []
    required_files = (REPORT, DOC, BOARD, INDEX, WEEKLY_CLI)
    for path in required_files:
        if not path.is_file():
            failures.append(f"missing Q21 artifact: {path.relative_to(ROOT)}")
    if failures:
        return failures
    required_refs = (
        "report-ref:queue-v2:q21:weekly-review-private-trial:v1",
        "dev-task:queue-v2-q21-weekly-ceo-review-private-trial",
        "owner-ref:founder-loop-bootstrap",
        "owner-ref:control-center-private-trial",
        "owner-ref:control-center-ux",
        "owner-ref:weekly-ceo-review-verifier",
    )
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in (DOC, BOARD, INDEX)
    )
    for required in required_refs:
        if required not in combined_docs:
            failures.append(f"Q21 docs omit {required}")
    trial_script = build_private_product_loop_trial_script()
    if [step.surface for step in trial_script.manual_steps] != REQUIRED_SURFACES:
        failures.append("Q21 report surface order drifted from Product Loop 012")
    return failures


def verify() -> list[str]:
    failures = _static_failures()
    if REPORT.is_file():
        failures.extend(_report_failures(_load_report()))
    failures.extend(_weekly_cli_failures())
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q21 Weekly CEO Review and private-trial report verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
