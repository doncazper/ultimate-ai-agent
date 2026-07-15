from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
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
from scripts.verification.verification_contracts import (  # noqa: E402
    VerificationPlan,
    VerificationRiskTier,
    VerificationUnit,
    VerificationUnitKind,
    dependency_closed_unit_refs,
    validate_verification_dag,
)
from scripts.verification.verification_risk import (  # noqa: E402
    ChangeKind,
    ChangeRecord,
    RISK_MANIFEST_VERSION,
    audit_posture_for_tier,
    change_fingerprint,
    classify_changes,
    risk_definition_payload,
    risk_manifest_fingerprint,
    unit_refs_for_selection,
)


SCHEMA_VERSION = "uaa_ci_command_manifest.v2"
PROFILE_REF = "ci-profile:merge-macos-v1"
MACHINE_PROFILE_REF = "machine-profile:macos-arm64-private"
PRIVATE_BASE_REF = "refs/uaa-ci/base-main"
PLAYWRIGHT_BROWSER_DIRNAME = "playwright-browsers"
GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS = 600
PYTEST_JOB_SETUP_BUDGET_SECONDS = 900
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
LOCKFILE_REFS = (
    "pyproject.toml",
    "uv.lock",
    "apps/control-center/package.json",
    "apps/control-center/package-lock.json",
    "integrations/matrix-client-adapter/package.json",
    "integrations/matrix-client-adapter/package-lock.json",
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


JobSpec = VerificationUnit


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
            "command:git.diff-check": CommandSpec(
                "command:git.diff-check",
                ("git", "diff", "--check", "{base_sha}", "{repository_sha}"),
                (),
                "diff_integrity",
                60,
            ),
            "command:pytest.focused": CommandSpec(
                "command:pytest.focused",
                (
                    ".venv/bin/python",
                    "-m",
                    "pytest",
                    "-q",
                    "{selected_test_refs}",
                ),
                (("PYTHONPATH", "src"),),
                "test_focused",
                900,
            ),
            "command:frontend.typecheck": CommandSpec(
                "command:frontend.typecheck",
                (
                    "npm",
                    "--prefix",
                    "apps/control-center",
                    "run",
                    "typecheck",
                    "--if-present",
                ),
                (),
                "frontend_typecheck",
                300,
            ),
            "command:frontend.unit-tests": CommandSpec(
                "command:frontend.unit-tests",
                (
                    "npm",
                    "--prefix",
                    "apps/control-center",
                    "run",
                    "test",
                    "--if-present",
                    "--",
                    "--run",
                ),
                (),
                "frontend_test",
                600,
            ),
            "command:frontend.vite-build": CommandSpec(
                "command:frontend.vite-build",
                (
                    "npm",
                    "--prefix",
                    "apps/control-center",
                    "exec",
                    "--",
                    "vite",
                    "build",
                ),
                (),
                "frontend_build",
                300,
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
                    "--tier",
                    "fast",
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
                    "--failure-ref-dir",
                    "{temp_root}/uaa_pytest_failure_refs",
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
                "--failure-ref-dir",
                f"{{temp_root}}/uaa_pytest_shard_{shard_index}_failure_refs",
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


FOCUSED_VERIFICATION_UNITS = (
    VerificationUnit(
        "risk-diff-check",
        "Changed Diff Integrity",
        None,
        (),
        command_refs=("command:git.diff-check",),
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:diff-integrity",
    ),
    VerificationUnit(
        "risk-documentation",
        "Documentation Integrity",
        None,
        ("risk-diff-check",),
        command_refs=("command:docs.integrity",),
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:documentation",
    ),
    VerificationUnit(
        "risk-product-truth",
        "Product Truth",
        None,
        ("risk-diff-check",),
        command_refs=("command:product-truth.regression-verifier",),
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:product-truth",
    ),
    VerificationUnit(
        "risk-redaction",
        "Security Artifact Redaction",
        None,
        ("risk-diff-check",),
        command_refs=("command:security.artifact-redaction",),
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:redaction",
    ),
    VerificationUnit(
        "risk-ruff",
        "Python Lint",
        None,
        ("risk-diff-check",),
        command_refs=("command:ci.ruff",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:python-lint",
    ),
    VerificationUnit(
        "risk-focused-pytest",
        "Affected Pytest",
        None,
        ("risk-diff-check",),
        command_refs=("command:pytest.focused",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        exclusive_resource_refs=("resource-ref:pytest-process-tree",),
        proof_equivalence_ref="proof-equivalence-ref:focused-pytest",
    ),
    VerificationUnit(
        "risk-frontend-typecheck",
        "Control Center Typecheck",
        None,
        ("risk-diff-check",),
        command_refs=("command:frontend.typecheck",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        exclusive_resource_refs=("resource-ref:typescript-typecheck",),
        proof_equivalence_ref="proof-equivalence-ref:typescript-typecheck",
    ),
    VerificationUnit(
        "risk-frontend-tests",
        "Control Center Unit Tests",
        None,
        ("risk-diff-check",),
        command_refs=("command:frontend.unit-tests",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:frontend-unit-tests",
    ),
    VerificationUnit(
        "risk-frontend-build",
        "Control Center Vite Build",
        None,
        ("risk-frontend-typecheck",),
        command_refs=("command:frontend.vite-build",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:frontend-build",
    ),
    VerificationUnit(
        "risk-frontend-safety",
        "Control Center Frontend Safety",
        None,
        ("risk-diff-check",),
        command_refs=("command:frontend.safety",),
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:frontend-safety",
    ),
    VerificationUnit(
        "risk-openapi",
        "OpenAPI Contract",
        None,
        ("risk-diff-check",),
        command_refs=("command:openapi.contract",),
        minimum_risk_tier=VerificationRiskTier.TIER_2,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:openapi",
    ),
    VerificationUnit(
        "risk-api-safety",
        "API Safety",
        None,
        ("risk-openapi",),
        command_refs=("command:api.safe-errors", "command:control-center.api-routes"),
        minimum_risk_tier=VerificationRiskTier.TIER_2,
        execution_surfaces=("github", "local", "private", "shadow"),
        proof_equivalence_ref="proof-equivalence-ref:api-safety",
    ),
    VerificationUnit(
        "risk-final-diff-audit",
        "Final Scoped Diff Audit",
        None,
        ("risk-diff-check",),
        unit_kind=VerificationUnitKind.AUDIT,
        minimum_risk_tier=VerificationRiskTier.TIER_1,
        execution_surfaces=("audit", "shadow"),
        parallel_safe=False,
        proof_equivalence_ref="proof-equivalence-ref:human-final-diff-audit",
    ),
    VerificationUnit(
        "risk-security-audit",
        "Security Or Authority Audit",
        None,
        ("risk-diff-check",),
        unit_kind=VerificationUnitKind.AUDIT,
        minimum_risk_tier=VerificationRiskTier.TIER_3,
        execution_surfaces=("audit", "shadow"),
        parallel_safe=False,
        proof_equivalence_ref="proof-equivalence-ref:human-security-audit",
    ),
)


CI_JOB_GRAPH = (
    JobSpec(
        "manifest-attestation",
        "manifest-attestation",
        "ci-manifest-attestation",
        (),
    ),
    JobSpec("lint", "lint", "ci-lint", ("manifest-attestation",)),
    JobSpec(
        "affected-preflight",
        "affected-preflight",
        "ci-affected-preflight",
        ("manifest-attestation",),
    ),
    JobSpec(
        "pytest-shards",
        "pytest / sharded suite",
        "ci-pytest-shards",
        ("lint", "affected-preflight"),
        timeout_minutes=60,
        minimum_risk_tier=VerificationRiskTier.TIER_3,
        exclusive_resource_refs=("resource-ref:complete-pytest",),
        proof_equivalence_ref="proof-equivalence-ref:complete-pytest",
    ),
    JobSpec(
        "pytest",
        "pytest",
        None,
        ("pytest-shards",),
        unit_kind=VerificationUnitKind.AGGREGATE,
        minimum_risk_tier=VerificationRiskTier.TIER_3,
        proof_equivalence_ref="proof-equivalence-ref:complete-pytest-aggregate",
    ),
    JobSpec("static-verification", "static-verification", "ci-static", ("pytest",)),
    JobSpec(
        "release-lane-docs",
        "Release Lane / Documentation Integrity",
        "docs",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-openapi",
        "Release Lane / OpenAPI Contract",
        "openapi",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-api-safety",
        "Release Lane / API Safety",
        "api-safety",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-security-redaction",
        "Release Lane / Security and Redaction",
        "security-redaction",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-product-truth",
        "Release Lane / Product Truth Regression",
        "product-truth-regression",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-local-model-e2e",
        "Release Lane / Local Model E2E",
        "local-model-e2e",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-durability",
        "Release Lane / Durability",
        "durability",
        ("pytest",),
    ),
    JobSpec(
        "release-lane-desktop-packaging",
        "Release Lane / Desktop and Local Packaging Proof",
        "desktop-packaging",
        ("pytest",),
    ),
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
        minimum_risk_tier=VerificationRiskTier.TIER_3,
        exclusive_resource_refs=("resource-ref:typescript-typecheck",),
        proof_equivalence_ref="proof-equivalence-ref:frontend-complete",
    ),
    JobSpec(
        "release-lane-frontend",
        "Release Lane / Control Center Frontend",
        "frontend",
        ("control-center-frontend",),
    ),
    JobSpec(
        "release-lane-visual-regression",
        "Release Lane / Control Center Visual Regression",
        "visual-regression",
        ("control-center-frontend",),
    ),
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


VERIFICATION_DAG = FOCUSED_VERIFICATION_UNITS + CI_JOB_GRAPH

VERIFIER_DEFINITION_REFS = (
    ".github/workflows/ci.yml",
    "Makefile",
    "apps/control-center/package.json",
    "pyproject.toml",
    "scripts/run_foundation_gate.py",
    "scripts/verify_release_lanes.py",
    "scripts/verification/changed_path_selector.py",
    "scripts/verification/ci_command_manifest.py",
    "scripts/verification/plan_affected_verification.py",
    "scripts/verification/run_ci_lane.py",
    "scripts/verification/run_pytest_shards.py",
    "scripts/verification/verification_contracts.py",
    "scripts/verification/verification_risk.py",
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
        "playwright_browser_directory_name": PLAYWRIGHT_BROWSER_DIRNAME,
        "commands": [asdict(commands[key]) for key in sorted(commands)],
        "lanes": [asdict(lanes[key]) for key in sorted(lanes)],
        "risk_manifest": risk_definition_payload(),
        "verification_dag": [asdict(unit) for unit in VERIFICATION_DAG],
        "job_graph": [
            {
                "job_ref": job.job_ref,
                "display_name": job.display_name,
                "lane_ref": job.lane_ref,
                "needs": list(job.needs),
                "timeout_minutes": job.timeout_minutes,
            }
            for job in CI_JOB_GRAPH
        ],
        "redaction_status": "content_free_refs_and_hashes_only",
    }


def definition_fingerprint() -> str:
    return _canonical_digest(definition_payload())


def command_manifest_fingerprint() -> str:
    commands = command_registry()
    return _canonical_digest(
        [asdict(commands[command_ref]) for command_ref in sorted(commands)]
    )


def platform_fingerprint() -> str:
    """Bind plans without persisting hostnames, usernames, paths, or environment."""

    return _canonical_digest(
        {
            "system": platform.system().lower(),
            "machine": platform.machine().lower(),
            "os_release": platform.mac_ver()[0]
            if platform.system() == "Darwin"
            else platform.release(),
            "python_implementation": platform.python_implementation().lower(),
            "python_version": platform.python_version(),
        }
    )


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
        if any(
            token.startswith("/") or ".." in Path(token).parts for token in command.argv
        ):
            failures.append(f"unsafe command argv: {command_ref}")
        if any(
            key
            not in {
                "PYTHONPATH",
                "FOUNDATION_GATE_MAX_BEST_MS",
                "FOUNDATION_GATE_MAX_MEAN_MS",
            }
            for key, _ in command.env
        ):
            failures.append(f"unsafe command environment: {command_ref}")
    for lane_ref, lane in lanes.items():
        if lane_ref != lane.lane_ref:
            failures.append(f"lane ref mismatch: {lane_ref}")
        for command_ref in (
            *lane.command_refs,
            *lane.optional_command_refs,
            *lane.satisfied_command_refs,
        ):
            if command_ref not in commands:
                failures.append(f"unknown command ref in {lane_ref}: {command_ref}")
    try:
        validate_verification_dag(VERIFICATION_DAG)
    except ValueError as exc:
        failures.append(f"invalid verification DAG: {exc}")
    job_refs = {job.job_ref for job in CI_JOB_GRAPH}
    for job in CI_JOB_GRAPH:
        if job.timeout_minutes <= 0 or job.timeout_minutes > 60:
            failures.append(f"invalid job timeout: {job.job_ref}")
        if job.lane_ref is not None and job.lane_ref not in lanes:
            failures.append(f"unknown job lane: {job.job_ref}")
        for dependency in job.needs:
            if dependency not in job_refs:
                failures.append(f"unknown job dependency: {job.job_ref}:{dependency}")
    unit_refs = {unit.unit_ref for unit in VERIFICATION_DAG}
    for tier_refs in risk_definition_payload()["tier_base_unit_refs"].values():
        for unit_ref in tier_refs:
            if unit_ref not in unit_refs:
                failures.append(f"unknown risk-tier verification unit: {unit_ref}")
    for unit in VERIFICATION_DAG:
        if unit.lane_ref is not None and unit.lane_ref not in lanes:
            failures.append(f"unknown verification unit lane: {unit.unit_ref}")
        for command_ref in unit.command_refs:
            if command_ref not in commands:
                failures.append(
                    f"unknown verification unit command: {unit.unit_ref}:{command_ref}"
                )
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


def _fingerprint_repository_files(
    repo: Path, refs: Iterable[str]
) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for ref in sorted(set(refs)):
        path = repo / ref
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise ValueError(
                f"missing or unsafe verifier definition ref: {ref}"
            ) from exc
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError(f"missing or unsafe verifier definition ref: {ref}")
            digest = hashlib.sha256()
            while chunk := os.read(descriptor, 1024 * 1024):
                digest.update(chunk)
            values.append((ref, digest.hexdigest()))
        finally:
            os.close(descriptor)
    return tuple(values)


def verifier_definition_fingerprint(repo: Path) -> str:
    refs = set(VERIFIER_DEFINITION_REFS)
    for pattern in (
        ".github/workflows/*.yml",
        "scripts/verify_*.py",
        "scripts/verification/*.py",
    ):
        refs.update(
            path.relative_to(repo).as_posix()
            for path in repo.glob(pattern)
            if path.is_file()
        )
    return _canonical_digest(_fingerprint_repository_files(repo, refs))


def test_inventory_fingerprint(repo: Path) -> str:
    refs = tuple(
        sorted(
            {
                path.relative_to(repo).as_posix()
                for pattern in (
                    "tests/**/test_*.py",
                    "apps/control-center/src/**/*.test.ts",
                    "apps/control-center/src/**/*.test.tsx",
                    "apps/control-center/tests/**/*.ts",
                )
                for path in repo.glob(pattern)
                if path.is_file()
            }
        )
    )
    refs = tuple(sorted({*refs, "pyproject.toml", "tests/conftest.py"}))
    if not refs:
        raise ValueError("verification test inventory is empty")
    return _canonical_digest(_fingerprint_repository_files(repo, refs))


def pytest_shard_plan_fingerprint(repo: Path) -> str:
    from scripts.verification.run_pytest_shards import current_shard_plan_fingerprint

    plan_ref = current_shard_plan_fingerprint(
        repo,
        8,
        repo / "scripts/verification/pytest_file_timing_seed.json",
    )
    digest = plan_ref.rsplit(":", maxsplit=1)[-1]
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("pytest shard plan fingerprint is invalid")
    return digest


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
    change_records: Iterable[ChangeRecord] | None = None,
    selected_unit_refs: Iterable[str] | None = None,
    base_sha: str | None = None,
    force_full: bool = False,
    shadow_mode: bool = False,
    unsafe_path_refs: Iterable[str] = (),
    frontend_visual_scope: str | None = None,
    verify_repository_state: bool = True,
) -> VerificationPlan:
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("repository SHA must be an exact lowercase 40-character ref")
    resolved_base_sha = sha if base_sha is None else base_sha
    if not SHA_PATTERN.fullmatch(resolved_base_sha):
        raise ValueError("base SHA must be an exact lowercase 40-character ref")
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
    records = (
        tuple(change_records)
        if change_records is not None
        else tuple(
            ChangeRecord(ChangeKind.MODIFIED, (path,))
            for path in sorted(set(affected_paths or ()))
        )
    )
    implicit_full = change_records is None and affected_paths is None
    risk_selection = classify_changes(
        records,
        force_full=force_full or implicit_full,
        unsafe_path_refs=tuple(unsafe_path_refs),
    )
    units_by_ref = {unit.unit_ref: unit for unit in VERIFICATION_DAG}
    if selected_unit_refs is not None:
        selected_units = tuple(selected_unit_refs)
    elif lane_refs is not None and not shadow_mode:
        requested_lanes = tuple(lane_refs)
        selected_units = tuple(
            unit.unit_ref for unit in CI_JOB_GRAPH if unit.lane_ref in requested_lanes
        )
    elif change_records is not None or affected_paths is not None or shadow_mode:
        selected_units = unit_refs_for_selection(
            risk_selection,
            full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        )
    else:
        selected_units = tuple(unit.unit_ref for unit in CI_JOB_GRAPH)
    if len(selected_units) != len(set(selected_units)) or any(
        unit_ref not in units_by_ref for unit_ref in selected_units
    ):
        raise ValueError("selected verification units must be unique canonical refs")
    selected_units = dependency_closed_unit_refs(VERIFICATION_DAG, selected_units)
    if shadow_mode and any(
        units_by_ref[unit_ref].minimum_risk_tier.rank > risk_selection.tier.rank
        for unit_ref in selected_units
    ):
        raise ValueError("selected verification unit exceeds the plan risk tier")

    if lane_refs is None:
        selected = tuple(
            dict.fromkeys(
                units_by_ref[unit_ref].lane_ref
                for unit_ref in selected_units
                if units_by_ref[unit_ref].lane_ref is not None
            )
        )
    else:
        selected = tuple(lane_refs)
    if len(selected) != len(set(selected)) or any(
        lane not in lanes for lane in selected
    ):
        raise ValueError("selected CI lanes must be unique canonical refs")
    command_refs = tuple(
        dict.fromkeys(
            (
                command_ref
                for unit_ref in selected_units
                for command_ref in units_by_ref[unit_ref].command_refs
            )
        )
    )
    command_refs = tuple(
        dict.fromkeys(
            (
                *command_refs,
                *(
                    command_ref
                    for lane_ref in selected
                    for command_ref in lanes[lane_ref].command_refs
                    if command_ref not in lanes[lane_ref].satisfied_command_refs
                ),
            )
        )
    )
    locks = _fingerprint_lockfiles(repo)
    shard_fingerprint = pytest_shard_plan_fingerprint(repo)
    visual_scope = (
        frontend_visual_scope
        if frontend_visual_scope is not None
        else visual_scope_for_paths(affected_paths)
    )
    if visual_scope not in {"affected", "not_affected", "unknown_fail_closed"}:
        raise ValueError("invalid frontend visual scope")
    definition_ref = definition_fingerprint()
    changed_tests = tuple(
        path
        for path in risk_selection.changed_path_refs
        if path.startswith("tests/test_") and path.endswith(".py")
    )
    platform_ref = platform_fingerprint()
    command_ref = command_manifest_fingerprint()
    verifier_ref = verifier_definition_fingerprint(repo)
    collection_ref = test_inventory_fingerprint(repo)
    selected_resources = {
        resource_ref
        for unit_ref in selected_units
        for resource_ref in units_by_ref[unit_ref].exclusive_resource_refs
    }
    base = {
        "schema_version": SCHEMA_VERSION,
        "profile_ref": PROFILE_REF,
        "repository_sha": sha,
        "definition_fingerprint": definition_ref,
        "dependency_lock_fingerprints": locks,
        "affected_path_classification": f"risk:{risk_selection.tier.value}",
        "selected_lane_refs": selected,
        "selected_command_refs": command_refs,
        "pytest_shard_plan_fingerprint": shard_fingerprint,
        "frontend_visual_scope": visual_scope,
        "redaction_status": "content_free_refs_hashes_and_repo_paths_only",
        "base_sha": resolved_base_sha,
        "risk_manifest_version": RISK_MANIFEST_VERSION,
        "risk_manifest_fingerprint": risk_manifest_fingerprint(),
        "risk_tier": risk_selection.tier,
        "changed_path_refs": risk_selection.changed_path_refs,
        "change_fingerprint": change_fingerprint(records),
        "escalation_reason_refs": risk_selection.reason_refs,
        "selected_unit_refs": selected_units,
        "selected_test_refs": changed_tests,
        "audit_posture": audit_posture_for_tier(risk_selection.tier),
        "full_pytest_required": (
            risk_selection.tier is VerificationRiskTier.TIER_3
            or "resource-ref:complete-pytest" in selected_resources
        ),
        "typescript_typecheck_required": (
            "resource-ref:typescript-typecheck" in selected_resources
        ),
        "release_gate_required": risk_selection.tier is VerificationRiskTier.TIER_3,
        "platform_fingerprint": platform_ref,
        "command_manifest_fingerprint": command_ref,
        "verifier_definition_fingerprint": verifier_ref,
        "test_collection_fingerprint": collection_ref,
        "test_collection_posture": "inventory_bound",
        "force_full": force_full or implicit_full,
        "shadow_mode": shadow_mode,
    }
    plan = VerificationPlan(
        **base,
        plan_fingerprint=verification_plan_fingerprint(base),
    )
    plan.validate()
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the canonical UAA CI command manifest."
    )
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
