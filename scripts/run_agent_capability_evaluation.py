#!/usr/bin/env python3
"""Run bounded, content-free UAA capability evaluation verifiers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.run_uaa_runtime_phase09_benchmark import (  # noqa: E402
    SCENARIOS as PHASE09_SCENARIOS,
    scenario_execution_fingerprint,
    scenario_registry_fingerprint,
)
from ultimate_ai_agent.core.evals import (  # noqa: E402
    CAPABILITY_COMPONENT_IDS,
    AgentCapabilityEvaluationReport,
    CapabilityEvaluationStatus,
    CapabilityScenarioObservation,
    build_agent_capability_evaluation_report,
)


NETWORK_SANDBOX_PROFILE = "(version 1)(allow default)(deny network*)"
MAX_CAPTURE_BYTES = 1_000_000
SUITE_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class AdditionalScenario:
    scenario_ref: str
    component_id: str
    command_ref: str
    command: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    verifier_refs: tuple[str, ...]
    recovery_expected: bool = False
    replay_expected: bool = False


@dataclass(frozen=True)
class ScenarioCommandResult:
    return_code: int
    duration_ms: int
    failure_code: str
    output: bytes = b""


ADDITIONAL_SCENARIOS = (
    AdditionalScenario(
        scenario_ref="scenario:learning-feedback-replay",
        component_id="learning_adaptation",
        command_ref="command-ref:pytest:memory-feedback-replay",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_governed_memory_context_phase03.py::test_concurrent_feedback_applies_once",
        ),
        evidence_refs=("evidence-ref:agent-eval:learning-feedback-replay",),
        verifier_refs=("verifier-ref:pytest:governed-memory-context",),
        replay_expected=True,
    ),
    AdditionalScenario(
        scenario_ref="scenario:communication-handoff-truth",
        component_id="communication_interaction",
        command_ref="command-ref:pytest:chat-loop-handoff",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_chat_to_loop_handoff_v1.py::test_chat_to_loop_handoff_read_model_classifies_reviewable_outcomes",
        ),
        evidence_refs=("evidence-ref:agent-eval:communication-handoff",),
        verifier_refs=("verifier-ref:pytest:chat-loop-handoff",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:safety-tamper-denial",
        component_id="safety_security_failure",
        command_ref="command-ref:pytest:mission-control-tamper",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_authority_mission_controls.py::test_hash_chain_tampering_fails_closed",
        ),
        evidence_refs=("evidence-ref:agent-eval:safety-tamper-denial",),
        verifier_refs=("verifier-ref:pytest:authority-mission-controls",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:cockpit-coherent-loop",
        component_id="ux_ai_cockpit",
        command_ref="command-ref:vitest:cockpit-coherent-loop",
        command=(
            "npm", "--prefix", "apps/control-center", "test", "--", "--run",
            "src/App.test.tsx", "-t",
            "renders one coherent backend-owned dogfood loop across shared surfaces",
            "--reporter=dot",
        ),
        evidence_refs=("evidence-ref:agent-eval:cockpit-coherent-loop",),
        verifier_refs=("verifier-ref:vitest:control-center-app",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:cli-api-cockpit-parity",
        component_id="cli_api_parity",
        command_ref="command-ref:verifier:runtime-cockpit-parity",
        command=("{python}", "scripts/verify_uaa_runtime_cockpit_cli_api.py"),
        evidence_refs=("evidence-ref:agent-eval:cli-api-parity",),
        verifier_refs=("verifier-ref:runtime-cockpit-cli-api",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:extension-inspectable-not-callable",
        component_id="extensibility_ecosystem",
        command_ref="command-ref:pytest:extension-non-callable",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_inspectable_extension_catalog.py::test_default_inspectable_extension_catalog_is_read_only_and_non_callable",
        ),
        evidence_refs=("evidence-ref:agent-eval:extension-non-callable",),
        verifier_refs=("verifier-ref:pytest:inspectable-extension-catalog",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:product-loop-terminal-receipt",
        component_id="productized_agent_loop",
        command_ref="command-ref:pytest:founder-loop-terminal-receipt",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_founder_loop_filesystem_mission.py::test_founder_loop_metadata_mission_completes_end_to_end_with_review_candidate",
        ),
        evidence_refs=("evidence-ref:agent-eval:product-loop-terminal-receipt",),
        verifier_refs=("verifier-ref:pytest:founder-loop-filesystem-mission",),
        replay_expected=True,
    ),
    AdditionalScenario(
        scenario_ref="scenario:web-hybrid-preservation-tests",
        component_id="research_web_external",
        command_ref="command-ref:pytest:web-hybrid-preservation",
        command=(
            "{python}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_web_hybrid_contracts.py",
            "tests/test_web_hybrid_execution.py",
            "tests/test_web_hybrid_ledger_router.py",
            "tests/test_runtime_agent_loop_web_hybrid_truth.py",
        ),
        evidence_refs=("evidence-ref:agent-eval:web-hybrid-preservation",),
        verifier_refs=("verifier-ref:pytest:web-hybrid-preservation",),
    ),
    AdditionalScenario(
        scenario_ref="scenario:web-hybrid-contract-verifier",
        component_id="research_web_external",
        command_ref="command-ref:verifier:web-hybrid-contracts",
        command=("{python}", "scripts/verify_web_hybrid_contracts.py"),
        evidence_refs=("evidence-ref:agent-eval:web-hybrid-contract-verifier",),
        verifier_refs=("verifier-ref:web-hybrid-contracts",),
    ),
)


def _scenario_fingerprint(scenario: AdditionalScenario) -> str:
    payload = {
        "scenario_ref": scenario.scenario_ref,
        "component_id": scenario.component_id,
        "command_ref": scenario.command_ref,
        "command": scenario.command,
        "evidence_refs": scenario.evidence_refs,
        "verifier_refs": scenario.verifier_refs,
        "recovery_expected": scenario.recovery_expected,
        "replay_expected": scenario.replay_expected,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"fingerprint-ref:agent-capability-scenario:sha256:{hashlib.sha256(encoded).hexdigest()}"


def evaluation_registry_fingerprint() -> str:
    payload = {
        "schema_version": "uaa-agent-capability-evaluation-registry.v1",
        "phase09_registry_fingerprint": scenario_registry_fingerprint(),
        "additional_scenario_fingerprints": [
            _scenario_fingerprint(scenario) for scenario in ADDITIONAL_SCENARIOS
        ],
        "network_sandbox_profile": NETWORK_SANDBOX_PROFILE,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"fingerprint-ref:agent-capability-registry:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_registry() -> None:
    refs = [scenario.scenario_ref for scenario in ADDITIONAL_SCENARIOS]
    if len(refs) != len(set(refs)):
        raise ValueError("additional capability scenario refs must be unique")
    covered = {scenario.component_id for scenario in PHASE09_SCENARIOS}
    covered.update(scenario.component_id for scenario in ADDITIONAL_SCENARIOS)
    if covered != set(CAPABILITY_COMPONENT_IDS):
        raise ValueError("capability evaluation registry must cover all 16 components")
    for scenario in ADDITIONAL_SCENARIOS:
        if scenario.component_id not in CAPABILITY_COMPONENT_IDS:
            raise ValueError("additional capability scenario has unknown component")
        if scenario.command[0] not in {"{python}", "npm"}:
            raise ValueError("additional capability scenario executable is not allowlisted")
        for part in scenario.command:
            if part.startswith(("tests/", "scripts/")):
                relative = part.split("::", 1)[0]
                path = ROOT / relative
                if not path.is_file() or path.is_symlink():
                    raise ValueError("additional capability scenario target is missing or unsafe")
        if any("live" in part.lower() for part in scenario.command):
            raise ValueError("live-provider tests are denied in capability evaluation")


def _trusted_executable(name: str) -> str:
    candidate = sys.executable if name == "{python}" else shutil.which(name)
    if not candidate:
        raise OSError(f"trusted executable unavailable: {name}")
    resolved = Path(candidate).resolve(strict=True)
    file_stat = os.stat(resolved)
    if not stat.S_ISREG(file_stat.st_mode):
        raise OSError(f"trusted executable is not a regular file: {name}")
    return str(Path(candidate).absolute())


def _sandbox_prefix() -> tuple[str, ...]:
    if sys.platform != "darwin":
        raise OSError("macOS network isolation is required for this evaluation")
    sandbox = Path("/usr/bin/sandbox-exec")
    if not sandbox.is_file() or sandbox.is_symlink():
        raise OSError("macOS network isolation facility is unavailable")
    return (str(sandbox), "-p", NETWORK_SANDBOX_PROFILE)


def _child_environment(temp_root: Path) -> dict[str, str]:
    python_dir = str(Path(_trusted_executable("{python}")).parent)
    npm_dir = str(Path(_trusted_executable("npm")).parent)
    node_dir = str(Path(_trusted_executable("node")).parent)
    home = temp_root / "home"
    home.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": os.pathsep.join((python_dir, npm_dir, node_dir, "/usr/bin", "/bin")),
        "HOME": str(home),
        "TMPDIR": str(temp_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CI": "true",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": "src",
        "UAA_AGENT_EVAL_OFFLINE": "1",
        "npm_config_offline": "true",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "",
    }


def _terminate(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("capability evaluation process tree did not terminate") from exc


def _run_command(
    command: tuple[str, ...],
    *,
    basetemp: Path,
    timeout_seconds: int = 180,
    capture_output: bool = False,
) -> ScenarioCommandResult:
    try:
        executable = _trusted_executable(command[0])
        resolved = [executable, *(part.format(python=sys.executable) for part in command[1:])]
        if "pytest" in resolved:
            resolved.extend(("--basetemp", str(basetemp)))
        argv = [*_sandbox_prefix(), *resolved]
        environment = _child_environment(basetemp.parent)
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return ScenarioCommandResult(127, 0, "spawn_failed")
    deadline = time.monotonic() + timeout_seconds
    output = bytearray()
    output_open = capture_output
    selector = selectors.DefaultSelector()
    if process.stdout is not None:
        selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while process.poll() is None or output_open:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate(process)
                return_code = 124
                failure_code = "timeout"
                output.clear()
                break
            if not capture_output:
                try:
                    return_code = process.wait(timeout=remaining)
                    failure_code = "none" if return_code == 0 else "assertion_failed"
                except subprocess.TimeoutExpired:
                    _terminate(process)
                    return_code = 124
                    failure_code = "timeout"
                break
            events = selector.select(timeout=min(remaining, 0.1))
            for key, _ in events:
                chunk = os.read(key.fd, 64 * 1024)
                if not chunk:
                    selector.unregister(key.fileobj)
                    output_open = False
                    continue
                output.extend(chunk)
                if len(output) > MAX_CAPTURE_BYTES:
                    _terminate(process)
                    output.clear()
                    return_code = 1
                    failure_code = "output_limit_exceeded"
                    output_open = False
                    break
            else:
                continue
            break
        else:
            return_code = process.returncode if process.returncode is not None else 1
            failure_code = "none" if return_code == 0 else "assertion_failed"
        if process.returncode is not None and failure_code not in {
            "timeout",
            "output_limit_exceeded",
        }:
            return_code = process.returncode
            failure_code = "none" if return_code == 0 else "assertion_failed"
    finally:
        selector.close()
        if process.stdout is not None:
            process.stdout.close()
    duration_ms = max(1, round((time.monotonic() - started) * 1000))
    return ScenarioCommandResult(return_code, duration_ms, failure_code, bytes(output))


def _phase09_payload(*, temp_root: Path, timeout_seconds: int) -> dict[str, object]:
    result = _run_command(
        ("{python}", "scripts/run_uaa_runtime_phase09_benchmark.py", "--json"),
        basetemp=temp_root / "phase09",
        timeout_seconds=timeout_seconds,
        capture_output=True,
    )
    if result.failure_code != "none":
        raise RuntimeError(f"Phase 09 verifier transport failed: {result.failure_code}")
    try:
        payload = json.loads(result.output.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Phase 09 verifier emitted invalid content-free JSON") from exc
    if payload.get("schema_version") != "uaa_runtime_capability_phase09_scenarios.v1":
        raise ValueError("Phase 09 schema drift")
    if payload.get("status") != "passed_with_truthful_blocked_sandbox":
        raise ValueError("Phase 09 overall status is not accepted")
    if payload.get("scenario_count") != len(PHASE09_SCENARIOS):
        raise ValueError("Phase 09 scenario count drift")
    if payload.get("registry_fingerprint") != scenario_registry_fingerprint():
        raise ValueError("Phase 09 registry fingerprint drift")
    redaction = payload.get("redaction")
    if redaction != {
        "safe_refs_only": True,
        "raw_content_persisted": False,
        "local_paths_persisted": False,
        "machine_identity_persisted": False,
    }:
        raise ValueError("Phase 09 redaction posture drift")
    return payload


def _phase09_observations(payload: dict[str, object]) -> list[CapabilityScenarioObservation]:
    results = payload.get("scenarios")
    if not isinstance(results, list) or len(results) != len(PHASE09_SCENARIOS):
        raise ValueError("Phase 09 scenario results drift")
    observations: list[CapabilityScenarioObservation] = []
    for spec, result in zip(PHASE09_SCENARIOS, results, strict=True):
        if not isinstance(result, dict):
            raise ValueError("Phase 09 scenario result is not an object")
        expected_result = {
            "scenario_id": spec.scenario_id,
            "component_id": spec.component_id,
            "evidence_refs": list(spec.evidence_refs),
            "test_verifier_refs": list(spec.test_verifier_refs),
            "execution_fingerprint": scenario_execution_fingerprint(spec),
        }
        for key, expected in expected_result.items():
            if result.get(key) != expected:
                raise ValueError(f"Phase 09 scenario binding drift: {key}")
        expected_status = CapabilityEvaluationStatus(spec.expected_status)
        observed_status = CapabilityEvaluationStatus(str(result.get("status")))
        observations.append(
            CapabilityScenarioObservation(
                scenario_ref=spec.scenario_id,
                component_id=spec.component_id,
                expected_status=expected_status,
                observed_status=observed_status,
                evidence_refs=spec.evidence_refs,
                verifier_refs=spec.test_verifier_refs,
                execution_fingerprint_ref=scenario_execution_fingerprint(spec),
                duration_ms=max(1, round(float(result["duration_seconds"]) * 1000)),
                failure_code=("none" if observed_status != CapabilityEvaluationStatus.failed else "assertion_failed"),
                recovery_expected=spec.scenario_id in {
                    "scenario:dag-replay-crash",
                    "scenario:cancellation-race",
                    "scenario:budget-exhaustion-settlement",
                },
                replay_expected=spec.scenario_id in {
                    "scenario:dag-replay-crash",
                    "scenario:budget-exhaustion-settlement",
                    "scenario:exact-tool-idempotency",
                    "scenario:receipt-tamper-surface-parity",
                },
            )
        )
    return observations


def run_agent_capability_evaluation() -> AgentCapabilityEvaluationReport:
    _validate_registry()
    suite_started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="uaa-agent-capability-eval-") as temp:
        temp_root = Path(temp)
        payload = _phase09_payload(temp_root=temp_root, timeout_seconds=600)
        observations = _phase09_observations(payload)
        for index, scenario in enumerate(ADDITIONAL_SCENARIOS):
            remaining = SUITE_TIMEOUT_SECONDS - round(time.monotonic() - suite_started)
            if remaining <= 0:
                command_result = ScenarioCommandResult(124, 0, "timeout")
            else:
                command_result = _run_command(
                    scenario.command,
                    basetemp=temp_root / f"scenario-{index + 1:02d}",
                    timeout_seconds=min(180, remaining),
                )
            observed_status = (
                CapabilityEvaluationStatus.passed
                if command_result.failure_code == "none"
                else CapabilityEvaluationStatus.failed
            )
            observations.append(
                CapabilityScenarioObservation(
                    scenario_ref=scenario.scenario_ref,
                    component_id=scenario.component_id,
                    expected_status=CapabilityEvaluationStatus.passed,
                    observed_status=observed_status,
                    evidence_refs=scenario.evidence_refs,
                    verifier_refs=(*scenario.verifier_refs, scenario.command_ref),
                    execution_fingerprint_ref=_scenario_fingerprint(scenario),
                    duration_ms=command_result.duration_ms,
                    failure_code=command_result.failure_code,
                    recovery_expected=scenario.recovery_expected,
                    replay_expected=scenario.replay_expected,
                )
            )
    return build_agent_capability_evaluation_report(
        report_ref="evaluation-report:uaa-agent-capability:20260712",
        benchmark_ref="benchmark-ref:uaa-goat-comparison:20260712",
        registry_fingerprint_ref=evaluation_registry_fingerprint(),
        observations=tuple(observations),
    )


def evaluation_report_projection(report: AgentCapabilityEvaluationReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "contract_ref": report.contract_ref,
        "report_ref": report.report_ref,
        "benchmark_ref": report.benchmark_ref,
        "registry_fingerprint_ref": report.registry_fingerprint_ref,
        "status": report.status.value,
        "scenario_count": report.scenario_count,
        "component_ids": list(report.component_ids),
        "safe_outcome_adherence_rate": report.safe_outcome_adherence_rate,
        "verification_pass_rate": report.verification_pass_rate,
        "passed_unblocked_verifier_rate": report.passed_unblocked_verifier_rate,
        "passed_unblocked_verifier_count": report.passed_unblocked_verifier_count,
        "task_completion_rate": report.task_completion_rate,
        "task_completion_count": report.task_completion_count,
        "task_completion_posture": report.task_completion_posture,
        "blocked_safe_outcome_count": report.blocked_safe_outcome_count,
        "correctness_rate": report.correctness_rate,
        "recovery_success_rate": report.recovery_success_rate,
        "evidence_completeness_rate": report.evidence_completeness_rate,
        "replay_correctness_rate": report.replay_correctness_rate,
        "operator_intervention_count": report.operator_intervention_count,
        "false_completion_count": report.false_completion_count,
        "unsupported_claim_count": report.unsupported_claim_count,
        "authority_policy_violation_count": report.authority_policy_violation_count,
        "observations": [
            {
                "scenario_ref": item.scenario_ref,
                "component_id": item.component_id,
                "expected_status": item.expected_status.value,
                "observed_status": item.observed_status.value,
                "execution_fingerprint_ref": item.execution_fingerprint_ref,
                "failure_code": item.failure_code,
            }
            for item in report.observations
        ],
        "content_free": report.content_free,
        "authority_granted": report.authority_granted,
    }


def evaluation_report_projection_digest(report: AgentCapabilityEvaluationReport) -> str:
    encoded = json.dumps(
        evaluation_report_projection(report),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _metric(value: float | int | None, *, percentage: bool = False) -> str:
    if value is None:
        return "not measured"
    return f"{value:.0%}" if percentage else str(value)


def _human_report(report: AgentCapabilityEvaluationReport) -> str:
    return "\n".join(
        (
            "UAA agent capability evaluation",
            f"  Status: {report.status.value}",
            f"  Components covered: {report.component_count}/16",
            f"  Scenario verifiers: {report.scenario_count}",
            f"  Safe-outcome adherence: {report.safe_outcome_adherence_rate:.0%}",
            f"  Verifier pass rate: {report.verification_pass_rate:.0%}",
            f"  Passed unblocked verifiers: {report.passed_unblocked_verifier_count}/{report.scenario_count} ({report.passed_unblocked_verifier_rate:.0%})",
            "  Task completion: not measured",
            f"  Truthfully blocked safe outcomes: {report.blocked_safe_outcome_count}",
            f"  Correctness: {_metric(report.correctness_rate, percentage=True)}",
            f"  Recovery success: {_metric(report.recovery_success_rate, percentage=True)}",
            f"  Evidence completeness: {_metric(report.evidence_completeness_rate, percentage=True)}",
            f"  Replay correctness: {_metric(report.replay_correctness_rate, percentage=True)}",
            f"  Operator interventions: {_metric(report.operator_intervention_count)}",
            f"  False completions: {_metric(report.false_completion_count)}",
            f"  Unsupported claims: {_metric(report.unsupported_claim_count)}",
            f"  Authority-policy violations: {_metric(report.authority_policy_violation_count)}",
            "  Cross-repository empirical winner: not measured",
            "  Observed product-experience winner: not measured",
            "  Network posture: macOS sandbox denied",
            "  Authority granted by evaluation: no",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit content-free JSON.")
    output.add_argument(
        "--projection-json",
        action="store_true",
        help="Emit the deterministic content-free report projection and digest.",
    )
    args = parser.parse_args(argv)
    report = run_agent_capability_evaluation()
    if args.projection_json:
        print(
            json.dumps(
                {
                    "report_projection": evaluation_report_projection(report),
                    "report_projection_digest": evaluation_report_projection_digest(report),
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(_human_report(report))
    return 0 if report.status == CapabilityEvaluationStatus.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ADDITIONAL_SCENARIOS",
    "evaluation_registry_fingerprint",
    "evaluation_report_projection",
    "evaluation_report_projection_digest",
    "run_agent_capability_evaluation",
]
