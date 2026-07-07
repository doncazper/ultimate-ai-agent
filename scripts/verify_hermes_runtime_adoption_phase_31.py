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
    RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF,
    RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS,
    build_runtime_background_jobs_read_model,
)


ROUTE = "/api/runtime/background-jobs"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_BACKGROUND_JOBS.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/background_jobs.py"
TEST = ROOT / "tests/test_hermes_runtime_background_jobs.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_background_jobs_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("background jobs route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-background-jobs":
        failures.append("background jobs CLI ref is stale")
    if read_model.status != "durable_job_proposal_posture":
        failures.append("background jobs posture is not durable proposal state")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
    ):
        failures.append("background jobs AuthorityState mapping is stale")
    if read_model.authority_state_decision_outcome != "deny":
        failures.append("background jobs AuthorityState decision must deny by default")
    if (
        "reason-ref:authority:adapter-unsupported"
        not in read_model.authority_state_reason_refs
    ):
        failures.append("background jobs AuthorityState reason must name unsupported adapter")
    if "adapter-ref:background-worker-runtime:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("background jobs must expose unsupported worker adapter ref")
    if read_model.job_count != 4:
        failures.append("background jobs lacks expected job proposals")
    if read_model.reviewable_job_count < 3:
        failures.append("background jobs lacks reviewable proposal posture")
    if read_model.execution_blocked_count < 1:
        failures.append("background jobs lacks blocked execution posture")
    unsafe_flags = {
        "pause": read_model.pause_enabled,
        "resume": read_model.resume_enabled,
        "run now": read_model.run_now_enabled,
        "scheduler": read_model.scheduler_enabled,
        "background worker": read_model.background_worker_enabled,
        "autonomous background execution": (
            read_model.autonomous_background_execution_enabled
        ),
        "autonomous retry": read_model.autonomous_retry_enabled,
        "external delivery": read_model.external_delivery_enabled,
        "provider call": read_model.provider_call_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "connector write": read_model.connector_write_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw job payload persistence": read_model.raw_job_payload_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing background job blocked refs: {sorted(missing_blocked)}")
    for job in read_model.jobs:
        if job.pause_enabled or job.resume_enabled or job.run_now_enabled:
            failures.append(f"job exposes execution control: {job.job_ref}")
        if job.scheduler_enabled or job.background_worker_enabled:
            failures.append(f"job enables scheduler/worker: {job.job_ref}")
        if job.autonomous_retry_enabled or job.external_delivery_enabled:
            failures.append(f"job enables autonomous delivery: {job.job_ref}")
        if job.provider_call_enabled or job.shell_execution_enabled:
            failures.append(f"job enables provider/shell authority: {job.job_ref}")
        if job.connector_write_enabled or job.raw_job_payload_persisted:
            failures.append(f"job writes externally or persists raw payload: {job.job_ref}")

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
        failures.append("API manifest missing background jobs route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("background jobs route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("background jobs route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-background-jobs",
        "runtime_background_jobs",
        "proposal_only",
        "scheduler_started",
        "background_worker_started",
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
            "Exact Authority Path",
            ROUTE,
            "inspect-background-jobs",
            "lane-ref:background-autonomy-scoped",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-background-jobs",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("background jobs CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_background_jobs"]
        authority_state = payload.get("authority_state")
        if not isinstance(authority_state, dict):
            failures.append("background jobs CLI missing authority state")
        elif (
            authority_state.get("mapping_ref")
            != RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
        ):
            failures.append("background jobs CLI authority mapping drifted")
        elif authority_state.get("decision_outcome") != "deny":
            failures.append("background jobs CLI authority decision drifted")
        if payload["scheduler_started"] is not False:
            failures.append("background jobs CLI claims scheduler start")
        if payload["background_worker_started"] is not False:
            failures.append("background jobs CLI claims worker start")
        if payload["run_now_performed"] is not False:
            failures.append("background jobs CLI claims run now")
        if payload["connector_write_performed"] is not False:
            failures.append("background jobs CLI claims connector write")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("background jobs CLI returned stale route ref")
        if (
            read_model_payload["authority_state_mapping_ref"]
            != RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
        ):
            failures.append("background jobs CLI returned stale AuthorityState mapping")
        if read_model_payload["authority_state_decision_outcome"] != "deny":
            failures.append("background jobs CLI returned unsafe AuthorityState outcome")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 31 background jobs verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
