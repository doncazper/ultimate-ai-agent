#!/usr/bin/env python3
"""Run the deterministic, revision-bound Capability Evaluation Lab V1."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts import run_agent_capability_evaluation as bounded_runner  # noqa: E402
from ultimate_ai_agent.core.evals.capability_lab import (  # noqa: E402
    CapabilityEvaluationCaseResult,
    CapabilityEvaluationLabCase,
    CapabilityEvaluationLabManifest,
    CapabilityEvaluationRunReceipt,
    CapabilityLabFailureAttribution,
    CapabilityLabGateStatus,
    CapabilityLabObservedStatus,
    build_capability_evaluation_run_receipt,
    capability_evaluation_case_evidence_digest,
    capability_evaluation_manifest_digest,
)


DEFAULT_MANIFEST = ROOT / "docs/evals/capability_evaluation_lab_v1.json"


@dataclass(frozen=True)
class CapabilityLabScenario:
    case_ref: str
    subject_ref: str
    claim_ref: str
    verifier_ref: str
    command: tuple[str, ...]
    pinned_evidence_path: str | None


SCENARIOS = (
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:uaa-native-contracts:v1",
        subject_ref="subject-ref:uaa-native",
        claim_ref="claim-ref:uaa-native:bounded-capability-evaluation",
        verifier_ref="verifier-ref:capability-lab:uaa-native-contracts",
        command=(
            "{python}",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_agent_capability_evaluation.py::test_report_separates_verifier_outcomes_from_unmeasured_task_completion",
            "tests/test_agent_capability_evaluation.py::test_runner_registry_closes_coverage_and_preserves_web_hybrid",
        ),
        pinned_evidence_path=None,
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:hermes-trajectory-contract:v1",
        subject_ref="subject-ref:hermes",
        claim_ref="claim-ref:hermes:trajectory-evidence-contract",
        verifier_ref="verifier-ref:capability-lab:hermes-trajectory-contract",
        command=("{python}", "scripts/verify_hermes_runtime_adoption_phase_40.py"),
        pinned_evidence_path="docs/runtime/hermes_runtime_trajectory_eval_manifest.json",
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:openclaw-parity-pack:v1",
        subject_ref="subject-ref:openclaw",
        claim_ref="claim-ref:openclaw:parity-evidence-contract",
        verifier_ref="verifier-ref:capability-lab:openclaw-parity-pack",
        command=("{python}", "scripts/verify_uaa_parity_gap_closure_prompt_pack.py"),
        pinned_evidence_path="docs/prompts/uaa_parity_gap_closure/prompt_bundle_manifest.json",
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:goat-comparison-contract:v1",
        subject_ref="subject-ref:goatcitadel",
        claim_ref="claim-ref:goatcitadel:bounded-comparison-evidence",
        verifier_ref="verifier-ref:capability-lab:goat-comparison-contract",
        command=("{python}", "scripts/verify_goat_comparison_findings.py"),
        pinned_evidence_path="docs/benchmarks/runtime_capability_foundation/goat_comparison_20260712.json",
    ),
)


def _file_digest(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError("capability lab evidence source is missing or unsafe")
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load_manifest(path: Path = DEFAULT_MANIFEST) -> CapabilityEvaluationLabManifest:
    if not path.is_file() or path.is_symlink():
        raise ValueError("capability lab manifest is missing or unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("capability lab manifest is unreadable") from exc
    manifest = CapabilityEvaluationLabManifest.model_validate(payload)
    _validate_registry(manifest)
    return manifest


def _validate_registry(manifest: CapabilityEvaluationLabManifest) -> None:
    scenario_by_ref = {scenario.case_ref: scenario for scenario in SCENARIOS}
    if len(scenario_by_ref) != len(SCENARIOS):
        raise ValueError("capability lab scenario refs must be unique")
    if tuple(scenario_by_ref) != manifest.case_refs:
        raise ValueError("capability lab executable registry coverage drift")
    for case in manifest.cases:
        scenario = scenario_by_ref[case.case_ref]
        if (
            case.subject_ref != scenario.subject_ref
            or case.claim_ref != scenario.claim_ref
        ):
            raise ValueError("capability lab subject or claim binding drift")
        if case.verifier_ref != scenario.verifier_ref:
            raise ValueError("capability lab verifier binding drift")
        if scenario.command[0] != "{python}":
            raise ValueError("capability lab executable is not allowlisted")
        if any("live" in part.lower() for part in scenario.command):
            raise ValueError("live evaluation command is denied")
        for part in scenario.command:
            if part.startswith(("scripts/", "tests/")):
                relative = part.split("::", 1)[0]
                target = ROOT / relative
                if not target.is_file() or target.is_symlink():
                    raise ValueError("capability lab verifier target is unsafe")
        if scenario.pinned_evidence_path is None:
            if case.source_revision_binding != "evaluator_revision":
                raise ValueError("UAA-native case must bind the evaluator revision")
        else:
            if case.source_revision_binding != "pinned":
                raise ValueError("external comparison contract must remain pinned")
            observed_digest = _file_digest(scenario.pinned_evidence_path)
            if observed_digest != case.source_evidence_digest_ref:
                raise ValueError("pinned source evidence digest drift")


def evaluation_lab_source_paths() -> tuple[str, ...]:
    paths = {
        "docs/evals/capability_evaluation_lab_v1.json",
        "scripts/run_capability_evaluation_lab.py",
        "src/ultimate_ai_agent/core/evals/capability_lab.py",
        "src/ultimate_ai_agent/core/evals/capability_metrics.py",
        "tests/test_agent_capability_evaluation.py",
        "tests/test_capability_evaluation_lab.py",
    }
    for scenario in SCENARIOS:
        if scenario.pinned_evidence_path is not None:
            paths.add(scenario.pinned_evidence_path)
        for part in scenario.command:
            if part.startswith(("scripts/", "tests/")):
                paths.add(part.split("::", 1)[0])
    return tuple(sorted(paths))


def evaluation_lab_source_digest() -> str:
    digest = hashlib.sha256()
    for relative in evaluation_lab_source_paths():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("capability lab source is missing or unsafe")
        digest.update(b"\n--UAA-CAPABILITY-LAB-SOURCE--\n")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def evaluation_lab_source_digest_at_commit(commit: str) -> str:
    if len(commit) != 40 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ValueError("exact evaluator source commit is required")
    executable = bounded_runner._trusted_executable("git")
    digest = hashlib.sha256()
    for relative in evaluation_lab_source_paths():
        result = subprocess.run(
            (executable, "cat-file", "blob", f"{commit}:{relative}"),
            cwd=ROOT,
            env={
                "PATH": "/usr/bin:/bin",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
            },
            capture_output=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            raise ValueError(
                "capability lab evaluator source is unavailable at exact revision"
            )
        digest.update(b"\n--UAA-CAPABILITY-LAB-SOURCE--\n")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\n")
        digest.update(result.stdout)
    return f"sha256:{digest.hexdigest()}"


def repository_inputs_match_exact_revision() -> bool:
    executable = bounded_runner._trusted_executable("git")
    result = subprocess.run(
        (
            executable,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        cwd=ROOT,
        env={
            "PATH": "/usr/bin:/bin",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
        capture_output=True,
        check=False,
        timeout=10,
    )
    if result.returncode != 0 or len(result.stdout) > 1_000_000:
        raise ValueError("capability lab repository revision is uninspectable")
    return not result.stdout


def _python_only_child_environment(temp_root: Path) -> dict[str, str]:
    python_dir = str(Path(bounded_runner._trusted_executable("{python}")).parent)
    home = temp_root / "home"
    home.mkdir(parents=True, exist_ok=True)
    site_packages = tuple(
        path
        for path in sys.path
        if path
        and Path(path).is_dir()
        and Path(path).name in {"site-packages", "dist-packages"}
    )
    return {
        "PATH": os.pathsep.join((python_dir, "/usr/bin", "/bin")),
        "HOME": str(home),
        "TMPDIR": str(temp_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CI": "true",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": os.pathsep.join(("src", *site_packages)),
        "VIRTUAL_ENV": sys.prefix,
        "UAA_AGENT_EVAL_OFFLINE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "",
    }


def _run_python_scenario(
    command: tuple[str, ...],
    *,
    basetemp: Path,
) -> bounded_runner.ScenarioCommandResult:
    if command[0] != "{python}":
        raise ValueError("capability lab supports exact Python verifiers only")
    try:
        executable = bounded_runner._trusted_executable(command[0])
        resolved = [
            executable,
            *(part.format(python=sys.executable) for part in command[1:]),
        ]
        if "pytest" in resolved:
            resolved.extend(("--basetemp", str(basetemp)))
        process = subprocess.Popen(
            (*bounded_runner._sandbox_prefix(), *resolved),
            cwd=ROOT,
            env=_python_only_child_environment(basetemp.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return bounded_runner.ScenarioCommandResult(127, 0, "spawn_failed")
    started = time.monotonic()
    try:
        return_code = process.wait(timeout=180)
        failure_code = "none" if return_code == 0 else "assertion_failed"
    except subprocess.TimeoutExpired:
        bounded_runner._terminate(process)
        return_code = 124
        failure_code = "timeout"
    duration_ms = max(1, round((time.monotonic() - started) * 1000))
    return bounded_runner.ScenarioCommandResult(
        return_code,
        duration_ms,
        failure_code,
    )


def _failure_posture(
    failure_code: str,
) -> tuple[CapabilityLabObservedStatus, CapabilityLabFailureAttribution, str]:
    if failure_code == "none":
        return (
            CapabilityLabObservedStatus.passed,
            CapabilityLabFailureAttribution.none,
            "reason-ref:capability-lab:verified",
        )
    if failure_code == "timeout":
        return (
            CapabilityLabObservedStatus.unknown,
            CapabilityLabFailureAttribution.timeout,
            "reason-ref:capability-lab:verifier-timeout",
        )
    if failure_code in {"spawn_failed", "output_limit_exceeded"}:
        return (
            CapabilityLabObservedStatus.unknown,
            CapabilityLabFailureAttribution.evaluator_environment,
            "reason-ref:capability-lab:evaluator-environment",
        )
    return (
        CapabilityLabObservedStatus.unknown,
        CapabilityLabFailureAttribution.unknown,
        "reason-ref:capability-lab:nonzero-unattributed",
    )


def _case_result(
    *,
    case: CapabilityEvaluationLabCase,
    evaluator_revision_ref: str,
    evaluator_source_digest_ref: str,
    failure_code: str,
) -> CapabilityEvaluationCaseResult:
    observed, attribution, reason_ref = _failure_posture(failure_code)
    source_revision_ref = (
        evaluator_revision_ref
        if case.source_revision_binding == "evaluator_revision"
        else case.source_revision_ref
    )
    source_evidence_digest_ref = (
        evaluator_source_digest_ref
        if case.source_revision_binding == "evaluator_revision"
        else case.source_evidence_digest_ref
    )
    if source_revision_ref is None or source_evidence_digest_ref is None:
        raise ValueError("capability lab source revision could not be resolved")
    evidence_digest_ref = capability_evaluation_case_evidence_digest(
        case=case,
        evaluator_revision_ref=evaluator_revision_ref,
        evaluator_source_digest_ref=evaluator_source_digest_ref,
        source_revision_ref=source_revision_ref,
        source_evidence_digest_ref=source_evidence_digest_ref,
        observed_status=observed,
        failure_attribution=attribution,
        reason_ref=reason_ref,
    )
    return CapabilityEvaluationCaseResult(
        case_ref=case.case_ref,
        subject_ref=case.subject_ref,
        claim_ref=case.claim_ref,
        source_revision_ref=source_revision_ref,
        source_evidence_digest_ref=source_evidence_digest_ref,
        observed_status=observed,
        failure_attribution=attribution,
        reason_ref=reason_ref,
        evidence_digest_ref=evidence_digest_ref,
    )


def run_capability_evaluation_lab(
    manifest: CapabilityEvaluationLabManifest | None = None,
) -> CapabilityEvaluationRunReceipt:
    active_manifest = manifest or load_manifest()
    _validate_registry(active_manifest)
    if not repository_inputs_match_exact_revision():
        raise ValueError(
            "capability lab verifier inputs do not match the exact repository revision"
        )
    evaluator_commit = bounded_runner.repository_commit()
    evaluator_revision_ref = f"git-sha:{evaluator_commit}"
    evaluator_source_digest_ref = evaluation_lab_source_digest()
    if (
        evaluation_lab_source_digest_at_commit(evaluator_commit)
        != evaluator_source_digest_ref
    ):
        raise ValueError(
            "capability lab evaluator source is not committed at the exact revision"
        )
    case_by_ref = {case.case_ref: case for case in active_manifest.cases}
    results: list[CapabilityEvaluationCaseResult] = []
    with tempfile.TemporaryDirectory(prefix="uaa-capability-lab-") as temp:
        temp_root = Path(temp)
        for index, scenario in enumerate(SCENARIOS, start=1):
            command_result = _run_python_scenario(
                scenario.command,
                basetemp=temp_root / f"case-{index:02d}",
            )
            results.append(
                _case_result(
                    case=case_by_ref[scenario.case_ref],
                    evaluator_revision_ref=evaluator_revision_ref,
                    evaluator_source_digest_ref=evaluator_source_digest_ref,
                    failure_code=command_result.failure_code,
                )
            )
    return build_capability_evaluation_run_receipt(
        manifest=active_manifest,
        evaluator_revision_ref=evaluator_revision_ref,
        evaluator_source_digest_ref=evaluator_source_digest_ref,
        results=tuple(results),
    )


def _human_receipt(receipt: CapabilityEvaluationRunReceipt) -> str:
    lines = [
        "UAA Capability Evaluation Lab V1",
        f"  Status: {receipt.status.value}",
        f"  Cases accounted for: {receipt.case_count}",
        f"  Evaluator revision: {receipt.evaluator_revision_ref}",
        f"  Manifest digest: {receipt.manifest_digest_ref}",
    ]
    for gate in receipt.claim_gates:
        lines.append(f"  {gate.subject_ref}: {gate.status.value}")
    lines.extend(
        (
            "  Live provider benchmark: no",
            "  Score authority: no",
            "  Product authority granted: no",
        )
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the versioned registry without executing its local verifiers.",
    )
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        if args.validate_only:
            payload = {
                "schema_version": manifest.schema_version,
                "manifest_ref": manifest.manifest_ref,
                "manifest_digest_ref": capability_evaluation_manifest_digest(manifest),
                "case_count": len(manifest.case_refs),
                "subject_refs": list(
                    dict.fromkeys(case.subject_ref for case in manifest.cases)
                ),
                "validated_only": True,
                "live_provider_benchmark_performed": False,
                "score_authority_granted": False,
                "authority_granted": False,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        receipt = run_capability_evaluation_lab(manifest)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        print(
            "capability evaluation lab failed closed: "
            "CAPABILITY_EVALUATION_LAB_VALIDATION_FAILED",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(_human_receipt(receipt))
    return 0 if receipt.status == CapabilityLabGateStatus.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
