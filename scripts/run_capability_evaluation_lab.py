#!/usr/bin/env python3
"""Run the deterministic, revision-bound Capability Evaluation Lab V1."""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
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
ISOLATED_CONTROLLER_COMMIT_ENV = "UAA_CAPABILITY_LAB_CONTROLLER_COMMIT"
PYTHON_SITE_INITIALIZATION_FLAG = "-S"


class RedactedArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise ValueError("capability lab arguments are invalid")


@dataclass(frozen=True)
class CapabilityLabScenario:
    case_ref: str
    subject_ref: str
    claim_ref: str
    verifier_ref: str
    command: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    deterministic_seed_ref: str
    pinned_evidence_path: str | None
    pinned_source_revision_ref: str | None


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
        evidence_refs=(
            "repo-ref:tests/test_agent_capability_evaluation.py",
            "repo-ref:src/ultimate_ai_agent/core/evals/capability_metrics.py",
        ),
        deterministic_seed_ref="seed-ref:capability-lab:uaa-native:v1",
        pinned_evidence_path=None,
        pinned_source_revision_ref=None,
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:hermes-trajectory-contract:v1",
        subject_ref="subject-ref:hermes",
        claim_ref="claim-ref:hermes:trajectory-evidence-contract",
        verifier_ref="verifier-ref:capability-lab:hermes-trajectory-contract",
        command=("{python}", "scripts/verify_hermes_runtime_adoption_phase_40.py"),
        evidence_refs=(
            "repo-ref:docs/runtime/hermes_runtime_trajectory_eval_manifest.json",
            "repo-ref:scripts/verify_hermes_runtime_adoption_phase_40.py",
        ),
        deterministic_seed_ref="seed-ref:capability-lab:hermes:v1",
        pinned_evidence_path="docs/runtime/hermes_runtime_trajectory_eval_manifest.json",
        pinned_source_revision_ref="source-revision-ref:hermes-phase-40:sha256:ea7ac693587d1e84ed882fae3fdef39299ae03476ee84d2408f6e73b77f3827d",
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:openclaw-parity-pack:v1",
        subject_ref="subject-ref:openclaw",
        claim_ref="claim-ref:openclaw:parity-evidence-contract",
        verifier_ref="verifier-ref:capability-lab:openclaw-parity-pack",
        command=("{python}", "scripts/verify_uaa_parity_gap_closure_prompt_pack.py"),
        evidence_refs=(
            "repo-ref:docs/prompts/uaa_parity_gap_closure/prompt_bundle_manifest.json",
            "repo-ref:scripts/verify_uaa_parity_gap_closure_prompt_pack.py",
        ),
        deterministic_seed_ref="seed-ref:capability-lab:openclaw:v1",
        pinned_evidence_path="docs/prompts/uaa_parity_gap_closure/prompt_bundle_manifest.json",
        pinned_source_revision_ref="source-revision-ref:openclaw-parity-pack:sha256:89dfd29576c41411e44c393b71216026cc9ac89390ad896fcde24136dd729433",
    ),
    CapabilityLabScenario(
        case_ref="evaluation-case-ref:capability-lab:goat-comparison-contract:v1",
        subject_ref="subject-ref:goatcitadel",
        claim_ref="claim-ref:goatcitadel:bounded-comparison-evidence",
        verifier_ref="verifier-ref:capability-lab:goat-comparison-contract",
        command=("{python}", "scripts/verify_goat_comparison_findings.py"),
        evidence_refs=(
            "repo-ref:docs/benchmarks/runtime_capability_foundation/goat_comparison_20260712.json",
            "repo-ref:scripts/verify_goat_comparison_findings.py",
        ),
        deterministic_seed_ref="seed-ref:capability-lab:goatcitadel:v1",
        pinned_evidence_path="docs/benchmarks/runtime_capability_foundation/goat_comparison_20260712.json",
        pinned_source_revision_ref="git-sha:91775e6905c8ca6c5083444f64eb3457b2d0aaa0",
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
        if (
            case.evidence_refs != scenario.evidence_refs
            or case.deterministic_seed_ref != scenario.deterministic_seed_ref
        ):
            raise ValueError("capability lab evidence or seed binding drift")
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
            if scenario.pinned_source_revision_ref is not None:
                raise ValueError("evaluator-bound case cannot pin a source revision")
        else:
            if case.source_revision_binding != "pinned":
                raise ValueError("external comparison contract must remain pinned")
            if case.source_revision_ref != scenario.pinned_source_revision_ref:
                raise ValueError("pinned source revision drift")
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


def repository_inputs_match_exact_revision(root: Path = ROOT) -> bool:
    executable = bounded_runner._trusted_executable("git")
    result = subprocess.run(
        (
            executable,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        cwd=root,
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


def isolated_checkout_matches_exact_revision(root: Path, commit: str) -> bool:
    if not repository_inputs_match_exact_revision(root):
        return False
    executable = bounded_runner._trusted_executable("git")
    result = subprocess.run(
        (executable, "rev-parse", "HEAD"),
        cwd=root,
        env={
            "PATH": "/usr/bin:/bin",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
        capture_output=True,
        check=False,
        timeout=5,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == commit


def _prepare_isolated_checkout(commit: str, destination: Path) -> Path:
    executable = bounded_runner._trusted_executable("git")
    environment = {
        "PATH": "/usr/bin:/bin",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }
    clone = subprocess.run(
        (
            executable,
            "clone",
            "--no-hardlinks",
            "--no-checkout",
            "--quiet",
            "--config",
            "core.hooksPath=/dev/null",
            str(ROOT),
            str(destination),
        ),
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )
    if clone.returncode != 0:
        raise ValueError("capability lab isolated checkout could not be created")
    checkout = subprocess.run(
        (executable, "checkout", "--detach", "--quiet", commit),
        cwd=destination,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if checkout.returncode != 0 or not isolated_checkout_matches_exact_revision(
        destination, commit
    ):
        raise ValueError("capability lab isolated checkout revision drift")
    return destination


def _hash_file_into(digest: "hashlib._Hash", path: Path) -> str:
    file_digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            file_digest.update(chunk)
    return base64.urlsafe_b64encode(file_digest.digest()).rstrip(b"=").decode("ascii")


def _trusted_python_prefix() -> Path:
    prefix = Path(_trusted_python_launcher()).parent.parent.resolve(strict=True)
    if not (prefix / "pyvenv.cfg").is_file():
        raise ValueError("capability lab requires a verified virtual environment")
    return prefix


def _active_site_package_roots() -> tuple[Path, ...]:
    prefix = _trusted_python_prefix()
    variables = {"base": str(prefix), "platbase": str(prefix)}
    roots: list[Path] = []
    for name in ("purelib", "platlib"):
        root = Path(sysconfig.get_path(name, vars=variables)).resolve(strict=True)
        if not root.is_dir() or not root.is_relative_to(prefix):
            raise ValueError("capability lab site-packages root is unsafe")
        if root not in roots:
            roots.append(root)
    return tuple(roots)


def _installed_distribution_bindings() -> tuple[tuple[str, str, str], ...]:
    prefix = _trusted_python_prefix()
    bindings: list[tuple[str, str, str]] = []
    for distribution in importlib.metadata.distributions():
        name = (distribution.metadata.get("Name") or "").lower()
        if not name:
            raise ValueError("capability lab dependency name is unavailable")
        direct_url_text = distribution.read_text("direct_url.json") or ""
        if '"editable": true' in direct_url_text.lower():
            if name == "ultimate-ai-agent":
                continue
            raise ValueError("capability lab editable dependency is unsupported")
        files = distribution.files
        if files is None:
            raise ValueError("capability lab dependency file inventory is unavailable")
        digest = hashlib.sha256()
        for relative in sorted(files, key=str):
            recorded_hash = getattr(relative, "hash", None)
            relative_text = str(relative)
            digest.update(b"\n--UAA-CAPABILITY-LAB-DEPENDENCY-FILE--\n")
            digest.update(relative_text.encode("utf-8"))
            target = Path(distribution.locate_file(relative))
            if target.is_symlink():
                raise ValueError("capability lab dependency contains an unsafe symlink")
            try:
                resolved = target.resolve(strict=True)
            except OSError:
                if recorded_hash is not None:
                    raise ValueError(
                        "capability lab dependency file with a recorded hash is missing"
                    ) from None
                digest.update(b"\nmissing\n")
                continue
            if not resolved.is_relative_to(prefix):
                raise ValueError("capability lab dependency escapes the Python prefix")
            if resolved.is_file():
                digest.update(b"\nfile\n")
                observed_hash = _hash_file_into(digest, resolved)
                if recorded_hash is not None and (
                    recorded_hash.mode != "sha256"
                    or recorded_hash.value != observed_hash
                ):
                    raise ValueError(
                        "capability lab installed dependency integrity drift"
                    )
            else:
                digest.update(b"\nnon-file\n")
        bindings.append((name, distribution.version, digest.hexdigest()))
    return tuple(sorted(bindings))


def _standard_library_digest(root: Path | None = None) -> str:
    stdlib_root = (
        root
        if root is not None
        else Path(sysconfig.get_path("stdlib")).resolve(strict=True)
    )
    if not stdlib_root.is_dir() or stdlib_root.is_symlink():
        raise ValueError("capability lab standard library root is unsafe")
    allowed_target_root = (
        stdlib_root if root is not None else Path(sys.base_prefix).resolve(strict=True)
    )
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(stdlib_root.rglob("*")):
        relative = path.relative_to(stdlib_root)
        if any(part in {"site-packages", "dist-packages"} for part in relative.parts):
            continue
        if path.is_symlink():
            try:
                resolved = path.resolve(strict=True)
            except OSError:
                raise ValueError(
                    "capability lab standard library contains a broken symlink"
                ) from None
            if not resolved.is_file() or not resolved.is_relative_to(
                allowed_target_root
            ):
                raise ValueError(
                    "capability lab standard library symlink target is unsafe"
                )
            digest.update(b"\n--UAA-CAPABILITY-LAB-STDLIB-SYMLINK--\n")
            digest.update(str(relative).encode("utf-8"))
            digest.update(b"\n")
            digest.update(os.readlink(path).encode("utf-8"))
            digest.update(b"\n")
            _hash_file_into(digest, resolved)
            file_count += 1
            continue
        if not path.is_file():
            continue
        digest.update(b"\n--UAA-CAPABILITY-LAB-STDLIB-FILE--\n")
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\n")
        _hash_file_into(digest, path)
        file_count += 1
    if file_count == 0:
        raise ValueError("capability lab standard library inventory is empty")
    return f"sha256:{digest.hexdigest()}"


def evaluator_environment_digest() -> str:
    executable = Path(bounded_runner._trusted_executable("{python}"))
    if not executable.is_file() or executable.is_symlink():
        raise ValueError("capability lab Python executable is unsafe")
    payload = {
        "python_implementation": sys.implementation.name,
        "python_cache_tag": sys.implementation.cache_tag,
        "python_version": sys.version,
        "python_executable_digest": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "python_site_initialization_enabled": False,
        "standard_library_digest": _standard_library_digest(),
        "distributions": _installed_distribution_bindings(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _trusted_python_launcher() -> str:
    launcher = Path(sys.executable)
    resolved = launcher.resolve(strict=True)
    if not launcher.is_file() or not resolved.is_file() or resolved.is_symlink():
        raise OSError("trusted Python launcher is unavailable")
    return str(launcher)


def _python_only_child_environment(
    temp_root: Path,
    *,
    deterministic_seed_ref: str | None = None,
) -> dict[str, str]:
    python_dir = str(Path(_trusted_python_launcher()).parent)
    home = temp_root / "home"
    home.mkdir(parents=True, exist_ok=True)
    python_hash_seed = "0"
    if deterministic_seed_ref is not None:
        python_hash_seed = str(
            int(
                hashlib.sha256(deterministic_seed_ref.encode("utf-8")).hexdigest()[:8],
                16,
            )
        )
    site_packages = tuple(str(path) for path in _active_site_package_roots())
    environment = {
        "PATH": os.pathsep.join((python_dir, "/usr/bin", "/bin")),
        "HOME": str(home),
        "TMPDIR": str(temp_root),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CI": "true",
        "PYTHONHASHSEED": python_hash_seed,
        "PYTHONPATH": os.pathsep.join(("src", *site_packages)),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
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
    if deterministic_seed_ref is not None:
        environment["UAA_CAPABILITY_LAB_SEED_REF"] = deterministic_seed_ref
    return environment


def _run_python_scenario(
    command: tuple[str, ...],
    *,
    basetemp: Path,
    execution_root: Path = ROOT,
    deterministic_seed_ref: str | None = None,
) -> bounded_runner.ScenarioCommandResult:
    if command[0] != "{python}":
        raise ValueError("capability lab supports exact Python verifiers only")
    try:
        executable = _trusted_python_launcher()
        resolved = [
            executable,
            *(part.format(python=sys.executable) for part in command[1:]),
        ]
        if "pytest" in resolved:
            resolved.extend(("--basetemp", str(basetemp)))
        process = subprocess.Popen(
            (
                *bounded_runner._sandbox_prefix(),
                resolved[0],
                PYTHON_SITE_INITIALIZATION_FLAG,
                *resolved[1:],
            ),
            cwd=execution_root,
            env=_python_only_child_environment(
                basetemp.parent,
                deterministic_seed_ref=deterministic_seed_ref,
            ),
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
    evaluator_environment_digest_ref: str,
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
        evaluator_environment_digest_ref=evaluator_environment_digest_ref,
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
    if os.environ.get(ISOLATED_CONTROLLER_COMMIT_ENV) != evaluator_commit:
        raise ValueError(
            "capability lab controller is not bound to the evaluator revision"
        )
    evaluator_revision_ref = f"git-sha:{evaluator_commit}"
    evaluator_source_digest_ref = evaluation_lab_source_digest()
    evaluator_environment_digest_ref = evaluator_environment_digest()
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
        execution_root = _prepare_isolated_checkout(
            evaluator_commit, temp_root / "repository"
        )
        for index, scenario in enumerate(SCENARIOS, start=1):
            if not isolated_checkout_matches_exact_revision(
                execution_root, evaluator_commit
            ):
                raise ValueError("capability lab isolated verifier inputs drifted")
            if evaluator_environment_digest() != evaluator_environment_digest_ref:
                raise ValueError("capability lab dependency environment drifted")
            command_result = _run_python_scenario(
                scenario.command,
                basetemp=temp_root / f"case-{index:02d}",
                execution_root=execution_root,
                deterministic_seed_ref=scenario.deterministic_seed_ref,
            )
            if not isolated_checkout_matches_exact_revision(
                execution_root, evaluator_commit
            ):
                raise ValueError("capability lab isolated verifier inputs drifted")
            if evaluator_environment_digest() != evaluator_environment_digest_ref:
                raise ValueError("capability lab dependency environment drifted")
            results.append(
                _case_result(
                    case=case_by_ref[scenario.case_ref],
                    evaluator_revision_ref=evaluator_revision_ref,
                    evaluator_source_digest_ref=evaluator_source_digest_ref,
                    evaluator_environment_digest_ref=evaluator_environment_digest_ref,
                    failure_code=command_result.failure_code,
                )
            )
    return build_capability_evaluation_run_receipt(
        manifest=active_manifest,
        evaluator_revision_ref=evaluator_revision_ref,
        evaluator_source_digest_ref=evaluator_source_digest_ref,
        evaluator_environment_digest_ref=evaluator_environment_digest_ref,
        results=tuple(results),
    )


def _human_receipt(receipt: CapabilityEvaluationRunReceipt) -> str:
    lines = [
        "UAA Capability Evaluation Lab V1",
        f"  Status: {receipt.status.value}",
        f"  Cases accounted for: {receipt.case_count}",
        f"  Evaluator revision: {receipt.evaluator_revision_ref}",
        f"  Evaluator environment: {receipt.evaluator_environment_digest_ref}",
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


def _relaunch_from_isolated_controller(argv: list[str]) -> int:
    if not repository_inputs_match_exact_revision():
        raise ValueError(
            "capability lab verifier inputs do not match the exact repository revision"
        )
    before_commit = bounded_runner.repository_commit()
    if not repository_inputs_match_exact_revision():
        raise ValueError("capability lab controller revision changed during capture")
    after_commit = bounded_runner.repository_commit()
    if before_commit != after_commit:
        raise ValueError("capability lab controller revision changed during capture")
    with tempfile.TemporaryDirectory(prefix="uaa-capability-controller-") as temp:
        temp_root = Path(temp)
        isolated_root = _prepare_isolated_checkout(
            before_commit, temp_root / "repository"
        )
        environment = _python_only_child_environment(temp_root)
        environment[ISOLATED_CONTROLLER_COMMIT_ENV] = before_commit
        completed = subprocess.run(
            (
                _trusted_python_launcher(),
                PYTHON_SITE_INITIALIZATION_FLAG,
                str(isolated_root / "scripts/run_capability_evaluation_lab.py"),
                *argv,
            ),
            cwd=isolated_root,
            env=environment,
            check=False,
        )
        return completed.returncode


def main(argv: list[str] | None = None) -> int:
    active_argv = list(sys.argv[1:] if argv is None else argv)
    if (
        "--validate-only" not in active_argv
        and ISOLATED_CONTROLLER_COMMIT_ENV not in os.environ
    ):
        try:
            return _relaunch_from_isolated_controller(active_argv)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
            print(
                "capability evaluation lab failed closed: "
                "CAPABILITY_EVALUATION_LAB_VALIDATION_FAILED",
                file=sys.stderr,
            )
            return 1
    parser = RedactedArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the versioned registry without executing its local verifiers.",
    )
    try:
        args = parser.parse_args(active_argv)
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
