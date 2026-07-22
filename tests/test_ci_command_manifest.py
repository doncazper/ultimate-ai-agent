from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from scripts.verification import ci_command_manifest as manifest


ROOT = Path(__file__).resolve().parents[1]
SHA = subprocess.run(
    ("git", "rev-parse", "HEAD"),
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


def test_canonical_ci_definition_is_valid_deterministic_and_complete() -> None:
    assert manifest.validate_definition() == []
    assert manifest.definition_fingerprint() == manifest.definition_fingerprint()
    assert len(manifest.definition_fingerprint()) == 64
    assert "product-truth-regression" in manifest.lane_registry()
    assert {job.job_ref for job in manifest.CI_JOB_GRAPH} >= {
        "manifest-attestation",
        "lint",
        "affected-preflight",
        "pytest-shards",
        "pytest",
        "static-verification",
        "release-lane-product-truth",
        "control-center-frontend",
        "release-lane-performance",
        "foundation-gate-report",
    }
    assert manifest.CI_JOB_GRAPH[1].needs == ("manifest-attestation",)
    affected = next(
        job for job in manifest.CI_JOB_GRAPH if job.job_ref == "affected-preflight"
    )
    pytest_job = next(
        job for job in manifest.CI_JOB_GRAPH if job.job_ref == "pytest-shards"
    )
    assert affected.needs == ("manifest-attestation",)
    assert pytest_job.needs[:3] == (
        "manifest-attestation",
        "lint",
        "affected-preflight",
    )
    assert set(pytest_job.needs[3:]) == {
        "release-lane-docs",
        "release-lane-openapi",
        "release-lane-api-safety",
        "release-lane-security-redaction",
        "release-lane-product-truth",
        "release-lane-local-model-e2e",
        "release-lane-durability",
    }
    assert pytest_job.command_refs == ("command:pytest.sharded-suite",)
    assert all(
        job.command_refs == manifest.lane_registry()[job.lane_ref].command_refs
        for job in manifest.CI_JOB_GRAPH
        if job.lane_ref is not None
    )
    assert not [
        unit.unit_ref
        for unit in manifest.VERIFICATION_DAG
        if "private" in unit.execution_surfaces
        and (
            unit.unit_kind
            in {
                manifest.VerificationUnitKind.AGGREGATE,
                manifest.VerificationUnitKind.AUDIT,
            }
            or bool(
                set(unit.exclusive_resource_refs).intersection(
                    {
                        "resource-ref:complete-pytest",
                        "resource-ref:typescript-typecheck",
                    }
                )
            )
        )
    ]


def test_ci_architecture_inventory_binds_fixed_resource_and_evidence_budgets() -> None:
    inventory = manifest.ci_architecture_inventory()
    jobs = {job.job_ref: job for job in manifest.CI_JOB_GRAPH}

    assert inventory["current_profile_ref"] == (
        "ci-architecture:exact-head-evidence-dag-v1"
    )
    assert inventory["runner_service_count"] == 4
    assert inventory["pytest_shard_count"] == 8
    assert inventory["pytest_worker_count"] == 4
    assert inventory["required_check_contexts"] == tuple(
        job.display_name for job in manifest.CI_JOB_GRAPH
    )
    for concurrent_refs in manifest.CI_RESOURCE_CONCURRENCY_SETS:
        assert sum(jobs[ref].cpu_units for ref in concurrent_refs) <= 4
        assert sum(jobs[ref].memory_units for ref in concurrent_refs) <= 4
    for ref in ("pytest-shards", "release-lane-performance", "foundation-gate-report"):
        assert jobs[ref].cpu_units == jobs[ref].memory_units == 4


def test_definition_rejects_private_on_a_runtime_ineligible_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    typecheck = next(
        unit
        for unit in manifest.VERIFICATION_DAG
        if unit.unit_ref == "risk-frontend-typecheck"
    )
    forged = replace(
        typecheck,
        execution_surfaces=(*typecheck.execution_surfaces, "private"),
    )
    monkeypatch.setattr(
        manifest,
        "VERIFICATION_DAG",
        tuple(
            forged if unit.unit_ref == forged.unit_ref else unit
            for unit in manifest.VERIFICATION_DAG
        ),
    )

    assert (
        "private execution forbidden for canonical unit: risk-frontend-typecheck"
        in manifest.validate_definition()
    )


def test_canonical_ci_commands_are_fixed_argv_and_safe_environment() -> None:
    commands = manifest.command_registry()
    assert len(commands) == len(set(commands))
    assert commands["command:pytest.sharded-suite"].argv[2:6] == (
        "--shards",
        str(manifest.CANONICAL_PYTEST_SHARD_COUNT),
        "--max-workers",
        "4",
    )
    assert "--hard-timeout-seconds" in commands["command:pytest.sharded-suite"].argv
    assert (
        "{temp_root}/uaa_pytest_failure_refs"
        in commands["command:pytest.sharded-suite"].argv
    )
    assert (
        "{temp_root}/uaa_pytest_collection_evidence.json"
        in commands["command:pytest.sharded-suite"].argv
    )
    assert commands["command:frontend.unit-tests"].argv[-2:] == (
        "--run",
        "--no-cache",
    )
    assert commands["command:frontend.vite-build"].argv[-4:] == (
        "apps/control-center",
        "--outDir",
        "{temp_root}/uaa_control_center_vite_dist",
        "--emptyOutDir",
    )
    assert commands["command:affected.preflight"].argv[-2:] == ("--tier", "fast")
    assert dict(commands["command:performance.latency-gate"].env) == {
        "FOUNDATION_GATE_MAX_BEST_MS": "45000",
        "FOUNDATION_GATE_MAX_MEAN_MS": "45000",
    }
    for shard_index in range(manifest.CANONICAL_PYTEST_SHARD_COUNT):
        lane_ref = f"ci-pytest-shard-{shard_index}-reproduce"
        command_ref = f"command:pytest.shard-{shard_index}-reproduce"
        assert manifest.lane_registry()[lane_ref].command_refs == (command_ref,)
        diagnostic_unit = next(
            unit for unit in manifest.VERIFICATION_DAG if unit.lane_ref == lane_ref
        )
        assert diagnostic_unit not in manifest.CI_JOB_GRAPH
        assert diagnostic_unit.command_refs == (command_ref,)
        assert diagnostic_unit.execution_surfaces == ("local", "private")
        assert diagnostic_unit.parallel_safe is False
        assert diagnostic_unit.proof_equivalence_ref.endswith("-non-gating")
        assert "--shard-index" in commands[command_ref].argv
        assert (
            f"{{temp_root}}/uaa_pytest_shard_{shard_index}_failure_refs"
            in commands[command_ref].argv
        )
    for command in commands.values():
        assert command.argv
        assert command.argv[0] in {".venv/bin/python", "git", "make", "npm"}
        assert all(";" not in token and "$(`" not in token for token in command.argv)


def test_canonical_frontend_commands_keep_generated_state_outside_checkout(
    tmp_path: Path,
) -> None:
    commands = manifest.command_registry()
    vitest_argv = commands["command:frontend.unit-tests"].argv
    vite_argv = commands["command:frontend.vite-build"].argv
    resolved_vite_argv = tuple(
        token.replace("{temp_root}", str(tmp_path)) for token in vite_argv
    )
    output_path = Path(
        resolved_vite_argv[resolved_vite_argv.index("--outDir") + 1]
    )

    assert "--no-cache" in vitest_argv
    assert "apps/control-center" in vite_argv
    assert output_path.is_relative_to(tmp_path)
    assert not output_path.is_relative_to(ROOT)
    assert "apps/control-center/dist" not in resolved_vite_argv


def test_pytest_lock_setup_and_command_bounds_fit_the_job_timeout() -> None:
    job = next(job for job in manifest.CI_JOB_GRAPH if job.job_ref == "pytest-shards")
    command = manifest.command_registry()["command:pytest.sharded-suite"]
    bounded_total = (
        manifest.GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS
        + manifest.PYTEST_JOB_SETUP_BUDGET_SECONDS
        + command.timeout_seconds
    )

    assert bounded_total <= job.timeout_minutes * 60
    assert job.timeout_minutes == 60


def test_exact_shard_reproduction_plan_is_canonical_but_never_in_full_graph() -> None:
    lane_ref = "ci-pytest-shard-1-reproduce"
    command_ref = "command:pytest.shard-1-reproduce"

    plan = manifest.build_plan(
        ROOT,
        SHA,
        lane_refs=(lane_ref,),
        verify_repository_state=False,
    )
    full_plan = manifest.build_plan(ROOT, SHA, verify_repository_state=False)

    assert plan.selected_lane_refs == (lane_ref,)
    assert plan.selected_unit_refs == ("diagnostic-pytest-shard-1",)
    assert plan.selected_command_refs == (command_ref,)
    assert plan.risk_tier is manifest.VerificationRiskTier.TIER_3
    assert plan.full_pytest_required is True
    assert plan.release_gate_required is True
    assert "diagnostic-pytest-shard-1" not in full_plan.selected_unit_refs
    assert command_ref not in full_plan.selected_command_refs


def test_definition_rejects_a_lane_without_one_canonical_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lanes = manifest.lane_registry()
    lanes["ci-orphan-diagnostic"] = manifest.LaneSpec(
        "ci-orphan-diagnostic",
        "Orphan Diagnostic",
        ("command:git.diff-check",),
    )
    monkeypatch.setattr(manifest, "lane_registry", lambda: lanes)

    failures = manifest.validate_definition()

    assert (
        "CI lane must map to exactly one verification unit: "
        "ci-orphan-diagnostic:0"
    ) in failures


def test_plan_binds_sha_locks_commands_shards_and_visual_scope() -> None:
    plan = manifest.build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards", "docs"),
        affected_paths=("apps/control-center/src/App.tsx",),
        verify_repository_state=False,
    )
    assert plan.schema_version == manifest.SCHEMA_VERSION
    assert plan.schema_version == "uaa_ci_command_manifest.v3"
    assert plan.repository_sha == SHA
    assert len(plan.dependency_lock_fingerprints) == len(manifest.LOCKFILE_REFS)
    assert plan.selected_command_refs[0:4] == (
        "command:ci.manifest-attestation",
        "command:ci.ruff",
        "command:ci.self-hosted-contract",
        "command:affected.preflight",
    )
    assert "command:pytest.sharded-suite" in plan.selected_command_refs
    assert "command:docs.integrity" in plan.selected_command_refs
    assert plan.frontend_visual_scope == "affected"
    assert len(plan.pytest_shard_plan_fingerprint) == 64
    assert len(plan.platform_fingerprint) == 64
    assert len(plan.command_manifest_fingerprint) == 64
    assert len(plan.verifier_definition_fingerprint) == 64
    assert len(plan.test_collection_fingerprint) == 64
    assert plan.test_collection_posture == "inventory_bound"
    assert len(plan.typescript_project_fingerprint) == 64
    assert plan.typescript_project_posture == "project_bound"
    assert len(plan.plan_fingerprint) == 64
    assert plan.verification_dag_fingerprint == (
        manifest.verification_dag_definition_fingerprint(manifest.VERIFICATION_DAG)
    )
    assert tuple(
        unit_ref for unit_ref, _fingerprint in plan.selected_unit_definition_fingerprints
    ) == plan.selected_unit_refs
    plan_payload = asdict(plan)
    plan_payload.pop("plan_fingerprint")
    assert manifest.verification_plan_fingerprint(plan_payload) == plan.plan_fingerprint


def test_focused_python_plan_selects_an_exact_owned_test() -> None:
    source_ref = "src/ultimate_ai_agent/core/evals/capability_metrics.py"

    plan = manifest.build_plan(
        ROOT,
        SHA,
        change_records=(
            manifest.ChangeRecord(manifest.ChangeKind.MODIFIED, (source_ref,)),
        ),
        base_sha=SHA,
        shadow_mode=True,
        verify_repository_state=False,
    )

    assert "risk-focused-pytest" in plan.selected_unit_refs
    assert plan.selected_test_refs == (
        "tests/test_agent_capability_evaluation.py",
    )


def test_plan_rejects_forged_focused_test_ownership() -> None:
    source_ref = "src/ultimate_ai_agent/core/evals/capability_metrics.py"

    with pytest.raises(ValueError, match="exactly match canonical"):
        manifest.build_plan(
            ROOT,
            SHA,
            change_records=(
                manifest.ChangeRecord(manifest.ChangeKind.MODIFIED, (source_ref,)),
            ),
            selected_unit_refs=("risk-diff-check", "risk-focused-pytest"),
            selected_test_refs=("tests/test_capability_maturity_integrity.py",),
            base_sha=SHA,
            verify_repository_state=False,
        )


def test_plan_fails_closed_for_unknown_sha_lane_or_unsafe_lockfile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="exact lowercase"):
        manifest.build_plan(ROOT, "HEAD")
    with pytest.raises(ValueError, match="unique canonical"):
        manifest.build_plan(
            ROOT,
            SHA,
            lane_refs=("missing",),
            verify_repository_state=False,
        )

    for ref in manifest.LOCKFILE_REFS:
        target = tmp_path / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("safe", encoding="utf-8")
    (tmp_path / manifest.LOCKFILE_REFS[0]).unlink()
    (tmp_path / manifest.LOCKFILE_REFS[0]).symlink_to(
        tmp_path / manifest.LOCKFILE_REFS[1]
    )
    monkeypatch.setattr(
        manifest.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=("git",), returncode=0, stdout=SHA + "\n", stderr=""
        ),
    )
    with pytest.raises(ValueError, match="unsafe dependency lock"):
        manifest.build_plan(
            tmp_path,
            SHA,
            lane_refs=("docs",),
            verify_repository_state=False,
        )


def test_manifest_payload_is_content_free_and_redacted() -> None:
    payload = json.dumps(manifest.definition_payload(), sort_keys=True)
    for forbidden in (
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "credential_material",
        "/Users/",
        "C:\\Users\\",
    ):
        assert forbidden not in payload
    assert asdict(manifest.CI_JOB_GRAPH[-1])["unit_ref"] == "foundation-gate-report"
    assert manifest.definition_payload()["job_graph"][-1]["job_ref"] == (
        "foundation-gate-report"
    )


def test_visual_scope_is_fail_closed_and_path_bound() -> None:
    assert manifest.visual_scope_for_paths(None) == "unknown_fail_closed"
    assert (
        manifest.visual_scope_for_paths(("src/ultimate_ai_agent/api/app.py",))
        == "not_affected"
    )
    assert (
        manifest.visual_scope_for_paths(("apps/control-center/src/App.tsx",))
        == "affected"
    )
