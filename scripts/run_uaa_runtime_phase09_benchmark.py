#!/usr/bin/env python3
"""Run the finite, redacted Phase 09 runtime capability scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase09_scenario_results.json"
)
RUNNER_SCHEMA_VERSION = "uaa-runtime-capability-phase09-runner.v2"


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    component_id: str
    expected_status: str
    blocker_code: str | None
    evidence_refs: tuple[str, ...]
    test_verifier_refs: tuple[str, ...]
    pytest_nodes: tuple[str, ...] = ()
    verifier_scripts: tuple[str, ...] = ()
    frontend_commands: tuple[tuple[str, ...], ...] = ()


SCENARIOS = (
    ScenarioSpec(
        "scenario:ambiguous-intent",
        "reasoning_task_understanding",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/intent/reasoning_truth.py",),
        ("repo-ref:uaa:tests/test_phase01_reasoning_truth.py",),
        pytest_nodes=(
            "tests/test_phase01_reasoning_truth.py::test_low_confidence_generates_operator_question_without_model",
            "tests/test_phase01_reasoning_truth.py::test_instruction_shaped_content_is_untrusted_and_never_persisted",
        ),
    ),
    ScenarioSpec(
        "scenario:plan-revision",
        "reasoning_task_understanding",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/planning/revisions.py",),
        ("repo-ref:uaa:tests/test_phase01_reasoning_truth.py",),
        pytest_nodes=(
            "tests/test_phase01_reasoning_truth.py::test_immutable_plan_replay_rejects_membership_order_and_target_changes",
            "tests/test_phase01_reasoning_truth.py::test_explicit_plan_revision_binds_exact_predecessor_and_invalidates_authority",
        ),
    ),
    ScenarioSpec(
        "scenario:dag-replay-crash",
        "planning_orchestration",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/execution/mission_orchestrator.py",),
        ("repo-ref:uaa:tests/test_authority_mission_orchestrator_hardening.py",),
        pytest_nodes=(
            "tests/test_authority_mission_orchestrator_hardening.py::test_multi_branch_success_and_partial_crash_resume",
            "tests/test_authority_mission_orchestrator_hardening.py::test_supplied_child_first_still_executes_stable_topological_order",
        ),
    ),
    ScenarioSpec(
        "scenario:approval-expiry",
        "autonomy_authority",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/execution/durable_mission_worker.py",),
        ("repo-ref:uaa:tests/test_authority_mission_approval_wait.py",),
        pytest_nodes=(
            "tests/test_authority_mission_approval_wait.py::test_revoked_or_expired_approval_never_starts",
            "tests/test_authority_mission_approval_wait.py::test_approval_wait_expiry_fails_terminal_without_dispatch",
        ),
    ),
    ScenarioSpec(
        "scenario:cancellation-race",
        "planning_orchestration",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/execution/durable_mission_controls.py",),
        ("repo-ref:uaa:tests/test_authority_mission_controls.py",),
        pytest_nodes=(
            "tests/test_authority_mission_controls.py::test_cancellation_after_claim_wins_inside_locked_prestart_boundary",
            "tests/test_authority_mission_controls.py::test_durable_start_wins_race_and_cancellation_becomes_recovery_required",
        ),
    ),
    ScenarioSpec(
        "scenario:budget-exhaustion-settlement",
        "planning_orchestration",
        "passed",
        None,
        (
            "repo-ref:uaa:src/ultimate_ai_agent/core/execution/mission_completion.py",
            "repo-ref:uaa:src/ultimate_ai_agent/core/authority/dispatcher.py",
        ),
        (
            "repo-ref:uaa:tests/test_authority_mission_orchestrator_hardening.py",
            "repo-ref:uaa:tests/test_authority_dispatcher_settlement_reconciliation.py",
        ),
        pytest_nodes=(
            "tests/test_authority_mission_orchestrator_hardening.py::test_cumulative_operation_budget_blocks_later_step",
            "tests/test_authority_dispatcher_settlement_reconciliation.py::test_settled_start_reconciles_terminal_truth_without_second_invocation",
        ),
    ),
    ScenarioSpec(
        "scenario:exact-tool-idempotency",
        "action_tool_calling",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/authority/dispatcher.py",),
        ("repo-ref:uaa:tests/test_authority_dispatcher_approval_and_start.py",),
        pytest_nodes=(
            "tests/test_authority_dispatcher_approval_and_start.py::test_concurrent_dispatch_replay_invokes_adapter_exactly_once",
        ),
    ),
    ScenarioSpec(
        "scenario:sandbox-escape-denial",
        "code_implementation_assistance",
        "blocked",
        "SANDBOX_FACILITY_NOT_PROVEN",
        ("repo-ref:uaa:src/ultimate_ai_agent/core/runtime_gateway/remote_execution_posture.py",),
        (
            "repo-ref:uaa:tests/test_hermes_runtime_remote_execution_posture.py",
            "repo-ref:uaa:tests/test_m81_runtime_sandbox_spec.py",
            "repo-ref:uaa:tests/test_m57_gate_integration.py",
        ),
        pytest_nodes=(
            "tests/test_hermes_runtime_remote_execution_posture.py::test_remote_execution_is_capability_map_only",
            "tests/test_hermes_runtime_remote_execution_posture.py::test_remote_execution_backend_map_is_blocked",
            "tests/test_hermes_runtime_remote_execution_posture.py::test_remote_execution_cli_uses_same_read_model",
            "tests/test_m81_runtime_sandbox_spec.py::test_m81_runtime_sandbox_spec_is_spec_only_and_no_authority",
            "tests/test_m57_gate_integration.py::test_m57_route_guard_rejects_runtime_sandbox_execution_routes",
        ),
    ),
    ScenarioSpec(
        "scenario:memory-correction",
        "memory_context_management",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/memory/review_runtime.py",),
        ("repo-ref:uaa:tests/test_governed_memory_context_phase03.py",),
        pytest_nodes=(
            "tests/test_governed_memory_context_phase03.py::test_correction_replaces_lineage_and_receipt_is_content_free",
        ),
    ),
    ScenarioSpec(
        "scenario:web-citation-injection",
        "research_web_external",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/web_access/research_aggregation.py",),
        ("repo-ref:uaa:tests/test_web_research_aggregation.py",),
        pytest_nodes=(
            "tests/test_web_research_aggregation.py::test_aggregation_is_deterministic_bounded_and_non_authoritative",
            "tests/test_web_research_aggregation.py::test_prompt_injection_shaped_summary_remains_untrusted_data",
        ),
    ),
    ScenarioSpec(
        "scenario:provider-stale-unavailable",
        "model_provider_management",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/capability_availability/read_model.py",),
        (
            "repo-ref:uaa:tests/test_web_research_aggregation.py",
            "repo-ref:uaa:tests/test_capability_availability.py",
        ),
        pytest_nodes=(
            "tests/test_web_research_aggregation.py::test_unknown_stale_degraded_and_missing_metered_budget_fail_closed",
            "tests/test_capability_availability.py::test_stale_and_unhealthy_health_fail_closed",
        ),
    ),
    ScenarioSpec(
        "scenario:receipt-tamper-surface-parity",
        "evidence_audit_observability",
        "passed",
        None,
        ("repo-ref:uaa:src/ultimate_ai_agent/core/execution/portable_mission_evidence.py",),
        (
            "repo-ref:uaa:tests/test_portable_mission_evidence.py",
            "repo-ref:uaa:tests/test_authority_mission_completion_surfaces.py",
            "repo-ref:uaa:tests/test_runtime_agent_loop_spine.py",
            "repo-ref:uaa:apps/control-center/src/components/AuthorityMissionInspectionPanel.test.tsx",
            "repo-ref:uaa:scripts/verify_uaa_runtime_cockpit_cli_api.py",
        ),
        pytest_nodes=(
            "tests/test_portable_mission_evidence.py::test_portable_bundle_rejects_tamper_target_and_unknown_fields",
            "tests/test_portable_mission_evidence.py::test_portable_bundle_rejects_reorder_replay_and_truncation",
            "tests/test_portable_mission_evidence.py::test_portable_verifier_rejects_rehashed_cross_run_substitution",
            "tests/test_authority_mission_completion_surfaces.py::test_completion_api_and_cli_expose_the_same_backend_owned_truth",
            "tests/test_runtime_agent_loop_spine.py::test_cockpit_parity_cli_inspects_same_operator_matrix",
        ),
        verifier_scripts=("scripts/verify_uaa_runtime_cockpit_cli_api.py",),
        frontend_commands=((
            "npm",
            "--prefix",
            "apps/control-center",
            "test",
            "--",
            "--run",
            "src/components/AuthorityMissionInspectionPanel.test.tsx",
            "-t",
            "renders invalid completion evidence as unverified",
            "--reporter=dot",
        ),),
    ),
)


def scenario_execution_fingerprint(spec: ScenarioSpec) -> str:
    payload = {
        "runner_schema_version": RUNNER_SCHEMA_VERSION,
        "scenario_id": spec.scenario_id,
        "component_id": spec.component_id,
        "expected_status": spec.expected_status,
        "blocker_code": spec.blocker_code,
        "evidence_refs": spec.evidence_refs,
        "test_verifier_refs": spec.test_verifier_refs,
        "pytest_nodes": spec.pytest_nodes,
        "verifier_scripts": spec.verifier_scripts,
        "frontend_commands": spec.frontend_commands,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def scenario_registry_fingerprint() -> str:
    encoded = json.dumps(
        [scenario_execution_fingerprint(spec) for spec in SCENARIOS],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _trusted_executable(name: str) -> str:
    candidate = sys.executable if name == sys.executable else shutil.which(name)
    if not candidate:
        raise OSError("scenario executable unavailable")
    resolved = Path(candidate).resolve(strict=True)
    if not resolved.is_file():
        raise OSError("scenario executable is not a regular file")
    return str(resolved)


def _run_command(command: list[str], *, basetemp: Path | None = None) -> int:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in ("src", env.get("PYTHONPATH")) if part
    )
    if basetemp is not None:
        command = [*command, "--basetemp", str(basetemp)]
    try:
        command = [_trusted_executable(command[0]), *command[1:]]
    except OSError:
        return 127
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=180)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
        return 124


def run_scenarios() -> dict[str, object]:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="uaa-phase09-benchmark-") as temp:
        temp_root = Path(temp)
        for index, spec in enumerate(SCENARIOS):
            started = time.monotonic()
            return_code = 0
            if spec.pytest_nodes:
                return_code = _run_command(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-q",
                        "-p",
                        "no:cacheprovider",
                        *spec.pytest_nodes,
                    ],
                    basetemp=temp_root / f"scenario-{index + 1:02d}",
                )
            if return_code == 0:
                for verifier_script in spec.verifier_scripts:
                    return_code = _run_command([sys.executable, verifier_script])
                    if return_code != 0:
                        break
            if return_code == 0:
                for frontend_command in spec.frontend_commands:
                    return_code = _run_command(list(frontend_command))
                    if return_code != 0:
                        break
            duration_seconds = max(round(time.monotonic() - started, 3), 0.001)
            status = spec.expected_status if return_code == 0 else "failed"
            results.append(
                {
                    "scenario_id": spec.scenario_id,
                    "scenario_version": "1.0",
                    "component_id": spec.component_id,
                    "status": status,
                    "confidence": "high" if spec.scenario_id != "scenario:receipt-tamper-surface-parity" else "medium",
                    "evidence_refs": list(spec.evidence_refs),
                    "test_verifier_refs": list(spec.test_verifier_refs),
                    "duration_seconds": duration_seconds,
                    "blocker_code": spec.blocker_code if return_code == 0 else "SCENARIO_VERIFICATION_FAILED",
                    "redaction_status": "safe_refs_only",
                    "execution_fingerprint": scenario_execution_fingerprint(spec),
                }
            )
    return {
        "schema_version": "uaa_runtime_capability_phase09_scenarios.v1",
        "benchmark_ref": "benchmark-ref:runtime-capability-foundation:phase09-scenarios",
        "status": "passed_with_truthful_blocked_sandbox" if all(
            result["status"] in {"passed", "blocked"} for result in results
        ) else "failed",
        "scenario_count": len(results),
        "registry_fingerprint": scenario_registry_fingerprint(),
        "scenarios": results,
        "redaction": {
            "safe_refs_only": True,
            "raw_content_persisted": False,
            "local_paths_persisted": False,
            "machine_identity_persisted": False,
        },
    }


def _write_result(output: Path, payload: dict[str, object]) -> None:
    if payload.get("status") != "passed_with_truthful_blocked_sandbox":
        raise ValueError("FAILED_RESULTS_MUST_NOT_REPLACE_ACCEPTED_EVIDENCE")
    if output != DEFAULT_OUTPUT:
        raise ValueError("CANONICAL_OUTPUT_ONLY")
    output_parent = output.parent
    parent_stat = os.lstat(output_parent)
    if not stat.S_ISDIR(parent_stat.st_mode) or output_parent.resolve() != DEFAULT_OUTPUT.parent.resolve():
        raise ValueError("OUTPUT_PARENT_INVALID")
    try:
        output_stat = os.lstat(output)
    except FileNotFoundError:
        output_stat = None
    if output_stat is not None and (stat.S_ISLNK(output_stat.st_mode) or not stat.S_ISREG(output_stat.st_mode)):
        raise ValueError("OUTPUT_MUST_BE_REGULAR_FILE")
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    directory_fd = os.open(output_parent, directory_flags)
    temp_name = f".phase09-{os.getpid()}-{time.time_ns()}.tmp"
    try:
        opened_parent_stat = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(opened_parent_stat.st_mode)
            or opened_parent_stat.st_dev != parent_stat.st_dev
            or opened_parent_stat.st_ino != parent_stat.st_ino
        ):
            raise ValueError("OUTPUT_PARENT_CHANGED")
        descriptor = os.open(
            temp_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temp_name,
            output.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    finally:
        try:
            os.unlink(temp_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-canonical",
        action="store_true",
        help="Replace the canonical result only after every accepted scenario passes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the bounded content-free scenario result as JSON.",
    )
    args = parser.parse_args(argv)
    payload = run_scenarios()
    passed = payload["status"] == "passed_with_truthful_blocked_sandbox"
    if passed and args.update_canonical:
        _write_result(DEFAULT_OUTPUT, payload)
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            "UAA Phase 09 benchmark scenarios completed: "
            f"{payload['scenario_count']} scenarios; "
            f"status={payload['status']}; raw outputs omitted; "
            f"canonical_updated={passed and args.update_canonical}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
