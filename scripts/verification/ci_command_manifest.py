from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_release_lanes import LaneCommand, release_lanes  # noqa: E402


SCHEMA_VERSION = "uaa_ci_command_manifest.v1"
PROFILE_REF = "ci-profile:merge-macos-v1"
MACHINE_PROFILE_REF = "machine-profile:macos-arm64-private"
PRIVATE_BASE_REF = "refs/uaa-ci/base-main"
GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS = 600
PYTEST_JOB_SETUP_BUDGET_SECONDS = 900
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
LOCKFILE_REFS = (
    "pyproject.toml",
    "uv.lock",
    "apps/control-center/package.json",
    "apps/control-center/package-lock.json",
)
VISUAL_SCOPE_PATHS = (
    "apps/control-center",
    "docs/control_center",
    "docs/design/control_center_north_star",
    "docs/schemas/control_center_release_surface.schema.json",
    "scripts/verify_beta_local.py",
    "scripts/verify_beta_13_frontend_loading_visual_proof.py",
    "scripts/verify_control_center_visual_regression.py",
    "scripts/verify_control_center_release_surface.py",
    "scripts/verify_fcc_polish_001_native_apple_grade_ux_layer.py",
    "tests/test_control_center_release_surface_manifest.py",
    "tests/test_control_center_visual_and_packaging_proofs.py",
    "tests/test_fcc_polish_001_native_apple_grade_ux_layer.py",
)


@dataclass(frozen=True)
class CommandSpec:
    command_ref: str
    argv: tuple[str, ...]
    env: tuple[tuple[str, str], ...]
    category: str
    timeout_seconds: int


@dataclass(frozen=True)
class LaneSpec:
    lane_ref: str
    name: str
    command_refs: tuple[str, ...]
    prerequisite_posture: str = "required"
    optional_command_refs: tuple[str, ...] = ()
    satisfied_command_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class JobSpec:
    job_ref: str
    display_name: str
    lane_ref: str | None
    needs: tuple[str, ...]
    timeout_minutes: int = 45


@dataclass(frozen=True)
class VerificationPlan:
    schema_version: str
    profile_ref: str
    repository_sha: str
    definition_fingerprint: str
    dependency_lock_fingerprints: tuple[tuple[str, str], ...]
    affected_path_classification: str
    selected_lane_refs: tuple[str, ...]
    selected_command_refs: tuple[str, ...]
    pytest_shard_plan_fingerprint: str
    frontend_visual_scope: str
    redaction_status: str
    plan_fingerprint: str


def _command_from_release(command: LaneCommand) -> CommandSpec:
    env = tuple(sorted(command.env.items()))
    if command.command_ref == "command:performance.latency-gate":
        env = (
            ("FOUNDATION_GATE_MAX_BEST_MS", "45000"),
            ("FOUNDATION_GATE_MAX_MEAN_MS", "45000"),
        )
    category = (
        "frontend"
        if command.command_ref.startswith("command:frontend.")
        else "release_lane"
    )
    timeout = 600 if category == "frontend" else 300
    if command.command_ref == "command:desktop-packaging.proof":
        timeout = 300
    return CommandSpec(
        command_ref=command.command_ref,
        argv=tuple(command.argv),
        env=env,
        category=category,
        timeout_seconds=timeout,
    )


def command_registry() -> dict[str, CommandSpec]:
    commands = {
        command.command_ref: _command_from_release(command)
        for lane in release_lanes()
        for command in lane.commands
    }
    commands.update(
        {
            "command:ci.ruff": CommandSpec(
                "command:ci.ruff",
                (".venv/bin/python", "-m", "ruff", "check", "."),
                (),
                "lint",
                300,
            ),
            "command:ci.self-hosted-contract": CommandSpec(
                "command:ci.self-hosted-contract",
                (".venv/bin/python", "scripts/verify_self_hosted_macos_ci.py"),
                (),
                "lint",
                120,
            ),
            "command:ci.manifest-attestation": CommandSpec(
                "command:ci.manifest-attestation",
                (
                    ".venv/bin/python",
                    "scripts/verification/ci_command_manifest.py",
                    "--verify-plan",
                    "--sha",
                    "{repository_sha}",
                ),
                (),
                "attestation",
                120,
            ),
            "command:affected.preflight": CommandSpec(
                "command:affected.preflight",
                (
                    ".venv/bin/python",
                    "scripts/verification/run_private_affected_preflight.py",
                    "--base-ref",
                    PRIVATE_BASE_REF,
                ),
                (),
                "preflight",
                900,
            ),
            "command:pytest.sharded-suite": CommandSpec(
                "command:pytest.sharded-suite",
                (
                    ".venv/bin/python",
                    "scripts/verification/run_pytest_shards.py",
                    "--shards",
                    "8",
                    "--max-workers",
                    "4",
                    "--timings-json",
                    "scripts/verification/pytest_file_timing_seed.json",
                    "--basetemp",
                    "{temp_root}/uaa_pytest_shards",
                    "--performance-report",
                    "{temp_root}/uaa_pytest_performance_report.json",
                    "--stretch-goal-seconds",
                    "900",
                    "--target-seconds",
                    "1200",
                    "--hard-timeout-seconds",
                    "1800",
                    "--quiet",
                    "--safe-summary",
                ),
                (),
                "test",
                1830,
            ),
            "command:static.verify-all": CommandSpec(
                "command:static.verify-all",
                (
                    ".venv/bin/python",
                    "scripts/verify_all.py",
                    "--skip-ruff",
                    "--skip-pytest",
                    "--timings-json",
                    "{temp_root}/uaa_static_verification_timings.json",
                ),
                (),
                "verification",
                900,
            ),
            "command:foundation-gate.ci-parallel": CommandSpec(
                "command:foundation-gate.ci-parallel",
                (
                    ".venv/bin/python",
                    "scripts/run_foundation_gate.py",
                    "--command-mode",
                    "ci-parallel",
                    "--no-write-latest",
                ),
                (),
                "gate",
                300,
            ),
        }
    )
    for shard_index in range(8):
        command_ref = f"command:pytest.shard-{shard_index}-reproduce"
        commands[command_ref] = CommandSpec(
            command_ref,
            (
                ".venv/bin/python",
                "scripts/verification/run_pytest_shards.py",
                "--shards",
                "8",
                "--shard-index",
                str(shard_index),
                "--max-workers",
                "1",
                "--timings-json",
                "scripts/verification/pytest_file_timing_seed.json",
                "--basetemp",
                f"{{temp_root}}/uaa_pytest_shard_{shard_index}",
                "--hard-timeout-seconds",
                "900",
                "--quiet",
                "--safe-summary",
            ),
            (),
            "test_reproduction",
            930,
        )
    return commands


def lane_registry() -> dict[str, LaneSpec]:
    lanes = {
        lane.lane_id: LaneSpec(
            lane_ref=lane.lane_id,
            name=lane.name,
            command_refs=tuple(command.command_ref for command in lane.commands),
            prerequisite_posture=(
                "typed_optional"
                if lane.lane_id in {"visual-regression", "desktop-packaging"}
                else "required"
            ),
            optional_command_refs=(
                ("command:frontend.visual-regression",)
                if lane.lane_id == "visual-regression"
                else (
                    ("command:desktop-packaging.proof",)
                    if lane.lane_id == "desktop-packaging"
                    else ()
                )
            ),
            satisfied_command_refs=(
                ("command:frontend.check",) if lane.lane_id == "frontend" else ()
            ),
        )
        for lane in release_lanes()
    }
    lanes.update(
        {
            "ci-lint": LaneSpec(
                "ci-lint",
                "Lint and CI Contract",
                ("command:ci.ruff", "command:ci.self-hosted-contract"),
            ),
            "ci-manifest-attestation": LaneSpec(
                "ci-manifest-attestation",
                "Canonical Manifest Attestation",
                ("command:ci.manifest-attestation",),
            ),
            "ci-pytest-shards": LaneSpec(
                "ci-pytest-shards",
                "Complete Pytest Sharded Suite",
                ("command:pytest.sharded-suite",),
            ),
            "ci-affected-preflight": LaneSpec(
                "ci-affected-preflight",
                "Affected Verification Preflight",
                ("command:affected.preflight",),
            ),
            "ci-static": LaneSpec(
                "ci-static",
                "Static Verification",
                ("command:static.verify-all",),
            ),
            "ci-control-center-frontend": LaneSpec(
                "ci-control-center-frontend",
                "Control Center Frontend Installed Suite",
                ("command:frontend.check",),
            ),
            "ci-foundation-report": LaneSpec(
                "ci-foundation-report",
                "Foundation Gate CI Parallel Report",
                ("command:foundation-gate.ci-parallel",),
            ),
        }
    )
    for shard_index in range(8):
        command_ref = f"command:pytest.shard-{shard_index}-reproduce"
        lane_ref = f"ci-pytest-shard-{shard_index}-reproduce"
        lanes[lane_ref] = LaneSpec(
            lane_ref,
            f"Exact Pytest Shard {shard_index} Reproduction",
            (command_ref,),
        )
    return lanes


CI_JOB_GRAPH = (
    JobSpec(
        "manifest-attestation",
        "manifest-attestation",
        "ci-manifest-attestation",
        (),
    ),
    JobSpec("lint", "lint", "ci-lint", ("manifest-attestation",)),
    JobSpec(
        "pytest-shards",
        "pytest / sharded suite",
        "ci-pytest-shards",
        ("lint",),
        timeout_minutes=60,
    ),
    JobSpec("pytest", "pytest", None, ("pytest-shards",)),
    JobSpec("static-verification", "static-verification", "ci-static", ("pytest",)),
    JobSpec("release-lane-docs", "Release Lane / Documentation Integrity", "docs", ("pytest",)),
    JobSpec("release-lane-openapi", "Release Lane / OpenAPI Contract", "openapi", ("pytest",)),
    JobSpec("release-lane-api-safety", "Release Lane / API Safety", "api-safety", ("pytest",)),
    JobSpec("release-lane-security-redaction", "Release Lane / Security and Redaction", "security-redaction", ("pytest",)),
    JobSpec("release-lane-product-truth", "Release Lane / Product Truth Regression", "product-truth-regression", ("pytest",)),
    JobSpec("release-lane-local-model-e2e", "Release Lane / Local Model E2E", "local-model-e2e", ("pytest",)),
    JobSpec("release-lane-durability", "Release Lane / Durability", "durability", ("pytest",)),
    JobSpec("release-lane-desktop-packaging", "Release Lane / Desktop and Local Packaging Proof", "desktop-packaging", ("pytest",)),
    JobSpec(
        "control-center-frontend",
        "control-center-frontend",
        "ci-control-center-frontend",
        (
            "static-verification",
            "release-lane-docs",
            "release-lane-openapi",
            "release-lane-api-safety",
            "release-lane-security-redaction",
            "release-lane-product-truth",
            "release-lane-local-model-e2e",
            "release-lane-durability",
            "release-lane-desktop-packaging",
        ),
    ),
    JobSpec("release-lane-frontend", "Release Lane / Control Center Frontend", "frontend", ("control-center-frontend",)),
    JobSpec("release-lane-visual-regression", "Release Lane / Control Center Visual Regression", "visual-regression", ("control-center-frontend",)),
    JobSpec(
        "release-lane-performance",
        "Release Lane / Performance",
        "performance",
        (
            "lint",
            "pytest",
            "static-verification",
            "release-lane-docs",
            "release-lane-openapi",
            "release-lane-api-safety",
            "release-lane-security-redaction",
            "release-lane-product-truth",
            "release-lane-local-model-e2e",
            "release-lane-durability",
            "release-lane-frontend",
            "release-lane-visual-regression",
            "release-lane-desktop-packaging",
            "control-center-frontend",
        ),
    ),
    JobSpec(
        "foundation-gate-report",
        "foundation-gate-report",
        "ci-foundation-report",
        (
            "lint",
            "pytest",
            "static-verification",
            "release-lane-docs",
            "release-lane-openapi",
            "release-lane-api-safety",
            "release-lane-security-redaction",
            "release-lane-product-truth",
            "release-lane-local-model-e2e",
            "release-lane-durability",
            "release-lane-frontend",
            "release-lane-visual-regression",
            "release-lane-desktop-packaging",
            "release-lane-performance",
        ),
    ),
)


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def definition_payload() -> dict[str, Any]:
    commands = command_registry()
    lanes = lane_registry()
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_ref": PROFILE_REF,
        "machine_profile_ref": MACHINE_PROFILE_REF,
        "lockfile_refs": list(LOCKFILE_REFS),
        "visual_scope_paths": list(VISUAL_SCOPE_PATHS),
        "commands": [asdict(commands[key]) for key in sorted(commands)],
        "lanes": [asdict(lanes[key]) for key in sorted(lanes)],
        "job_graph": [asdict(job) for job in CI_JOB_GRAPH],
        "redaction_status": "content_free_refs_and_hashes_only",
    }


def definition_fingerprint() -> str:
    return _canonical_digest(definition_payload())


def verification_plan_fingerprint(payload: dict[str, Any]) -> str:
    expected_fields = {
        field_name
        for field_name in VerificationPlan.__dataclass_fields__
        if field_name != "plan_fingerprint"
    }
    if set(payload) != expected_fields:
        raise ValueError("verification plan payload fields are invalid")
    return _canonical_digest(
        {field_name: payload[field_name] for field_name in sorted(expected_fields)}
    )


def validate_definition() -> list[str]:
    failures: list[str] = []
    commands = command_registry()
    lanes = lane_registry()
    if len(commands) != len(set(commands)):
        failures.append("command refs must be unique")
    for command_ref, command in commands.items():
        if command_ref != command.command_ref or not command_ref.startswith("command:"):
            failures.append(f"invalid command ref: {command_ref}")
        if not command.argv or command.timeout_seconds <= 0:
            failures.append(f"invalid command definition: {command_ref}")
        if any(token.startswith("/") or ".." in Path(token).parts for token in command.argv):
            failures.append(f"unsafe command argv: {command_ref}")
        if any(key not in {"PYTHONPATH", "FOUNDATION_GATE_MAX_BEST_MS", "FOUNDATION_GATE_MAX_MEAN_MS"} for key, _ in command.env):
            failures.append(f"unsafe command environment: {command_ref}")
    for lane_ref, lane in lanes.items():
        if lane_ref != lane.lane_ref:
            failures.append(f"lane ref mismatch: {lane_ref}")
        for command_ref in (*lane.command_refs, *lane.optional_command_refs, *lane.satisfied_command_refs):
            if command_ref not in commands:
                failures.append(f"unknown command ref in {lane_ref}: {command_ref}")
    job_refs = {job.job_ref for job in CI_JOB_GRAPH}
    if len(job_refs) != len(CI_JOB_GRAPH):
        failures.append("job refs must be unique")
    for job in CI_JOB_GRAPH:
        if job.timeout_minutes <= 0 or job.timeout_minutes > 60:
            failures.append(f"invalid job timeout: {job.job_ref}")
        if job.lane_ref is not None and job.lane_ref not in lanes:
            failures.append(f"unknown job lane: {job.job_ref}")
        for dependency in job.needs:
            if dependency not in job_refs:
                failures.append(f"unknown job dependency: {job.job_ref}:{dependency}")
    pytest_job = next(job for job in CI_JOB_GRAPH if job.job_ref == "pytest-shards")
    pytest_command = commands["command:pytest.sharded-suite"]
    if (
        GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS
        + PYTEST_JOB_SETUP_BUDGET_SECONDS
        + pytest_command.timeout_seconds
        > pytest_job.timeout_minutes * 60
    ):
        failures.append("pytest lock, setup, and command bounds exceed the job timeout")
    return failures


def _fingerprint_lockfiles(repo: Path) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for ref in LOCKFILE_REFS:
        path = repo / ref
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise ValueError(f"missing or unsafe dependency lock ref: {ref}") from exc
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError(f"missing or unsafe dependency lock ref: {ref}")
            digest = hashlib.sha256()
            while chunk := os.read(descriptor, 1024 * 1024):
                digest.update(chunk)
            values.append((ref, digest.hexdigest()))
        finally:
            os.close(descriptor)
    return tuple(values)


def visual_scope_for_paths(paths: Iterable[str] | None) -> str:
    if paths is None:
        return "unknown_fail_closed"
    normalized = tuple(path.strip("/") for path in paths)
    return (
        "affected"
        if any(
            path == prefix or path.startswith(f"{prefix}/")
            for path in normalized
            for prefix in VISUAL_SCOPE_PATHS
        )
        else "not_affected"
    )


def build_plan(
    repo: Path,
    sha: str,
    *,
    lane_refs: Iterable[str] | None = None,
    affected_paths: Iterable[str] | None = None,
    frontend_visual_scope: str | None = None,
    verify_repository_state: bool = True,
) -> VerificationPlan:
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("repository SHA must be an exact lowercase 40-character ref")
    if verify_repository_state:
        completed = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.stdout.strip() != sha:
            raise ValueError("repository worktree does not match the plan SHA")
        status = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=all"),
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if status.stdout:
            raise ValueError("repository worktree must be clean for an exact plan")
    failures = validate_definition()
    if failures:
        raise ValueError("invalid canonical CI definition")
    lanes = lane_registry()
    selected = tuple(lane_refs or tuple(job.lane_ref for job in CI_JOB_GRAPH if job.lane_ref))
    if len(selected) != len(set(selected)) or any(lane not in lanes for lane in selected):
        raise ValueError("selected CI lanes must be unique canonical refs")
    command_refs = tuple(
        command_ref
        for lane_ref in selected
        for command_ref in lanes[lane_ref].command_refs
        if command_ref not in lanes[lane_ref].satisfied_command_refs
    )
    locks = _fingerprint_lockfiles(repo)
    shard_command = command_registry()["command:pytest.sharded-suite"]
    shard_fingerprint = _canonical_digest(asdict(shard_command))
    visual_scope = (
        frontend_visual_scope
        if frontend_visual_scope is not None
        else visual_scope_for_paths(affected_paths)
    )
    if visual_scope not in {"affected", "not_affected", "unknown_fail_closed"}:
        raise ValueError("invalid frontend visual scope")
    definition_ref = definition_fingerprint()
    base = {
        "schema_version": SCHEMA_VERSION,
        "profile_ref": PROFILE_REF,
        "repository_sha": sha,
        "definition_fingerprint": definition_ref,
        "dependency_lock_fingerprints": locks,
        "affected_path_classification": (
            "full_merge_gate" if affected_paths is None else "affected_paths_supplied"
        ),
        "selected_lane_refs": selected,
        "selected_command_refs": command_refs,
        "pytest_shard_plan_fingerprint": shard_fingerprint,
        "frontend_visual_scope": visual_scope,
        "redaction_status": "content_free_refs_and_hashes_only",
    }
    return VerificationPlan(**base, plan_fingerprint=verification_plan_fingerprint(base))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the canonical UAA CI command manifest.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verify-plan", action="store_true")
    parser.add_argument("--sha")
    args = parser.parse_args(argv)
    failures = validate_definition()
    if args.verify_plan:
        if args.sha is None:
            parser.error("--verify-plan requires --sha")
        build_plan(ROOT, args.sha)
    payload = {
        **definition_payload(),
        "definition_fingerprint": definition_fingerprint(),
        "definition_status": "pass" if not failures else "fail",
        "validation_failures": failures,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("UAA canonical CI command manifest")
        print(f"Version: {SCHEMA_VERSION}")
        print(f"Profile: {PROFILE_REF}")
        print(f"Fingerprint: {payload['definition_fingerprint']}")
        print(f"Commands: {len(payload['commands'])}")
        print(f"Lanes: {len(payload['lanes'])}")
        print(f"Jobs: {len(payload['job_graph'])}")
        print(f"Status: {payload['definition_status']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
