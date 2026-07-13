from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
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
    assert pytest_job.needs == ("lint", "affected-preflight")


def test_canonical_ci_commands_are_fixed_argv_and_safe_environment() -> None:
    commands = manifest.command_registry()
    assert len(commands) == len(set(commands))
    assert commands["command:pytest.sharded-suite"].argv[2:6] == (
        "--shards",
        "8",
        "--max-workers",
        "4",
    )
    assert "--hard-timeout-seconds" in commands["command:pytest.sharded-suite"].argv
    assert commands["command:affected.preflight"].argv[-2:] == ("--tier", "fast")
    assert dict(commands["command:performance.latency-gate"].env) == {
        "FOUNDATION_GATE_MAX_BEST_MS": "45000",
        "FOUNDATION_GATE_MAX_MEAN_MS": "45000",
    }
    for shard_index in range(8):
        lane_ref = f"ci-pytest-shard-{shard_index}-reproduce"
        command_ref = f"command:pytest.shard-{shard_index}-reproduce"
        assert manifest.lane_registry()[lane_ref].command_refs == (command_ref,)
        assert "--shard-index" in commands[command_ref].argv
    for command in commands.values():
        assert command.argv
        assert command.argv[0] in {".venv/bin/python", "make"}
        assert all(";" not in token and "$(`" not in token for token in command.argv)


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


def test_plan_binds_sha_locks_commands_shards_and_visual_scope() -> None:
    plan = manifest.build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards", "docs"),
        affected_paths=("apps/control-center/src/App.tsx",),
        verify_repository_state=False,
    )
    assert plan.schema_version == manifest.SCHEMA_VERSION
    assert plan.repository_sha == SHA
    assert len(plan.dependency_lock_fingerprints) == len(manifest.LOCKFILE_REFS)
    assert plan.selected_command_refs == (
        "command:pytest.sharded-suite",
        "command:docs.integrity",
    )
    assert plan.frontend_visual_scope == "affected"
    assert len(plan.pytest_shard_plan_fingerprint) == 64
    assert len(plan.plan_fingerprint) == 64
    plan_payload = asdict(plan)
    plan_payload.pop("plan_fingerprint")
    assert manifest.verification_plan_fingerprint(plan_payload) == plan.plan_fingerprint


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
    (tmp_path / manifest.LOCKFILE_REFS[0]).symlink_to(tmp_path / manifest.LOCKFILE_REFS[1])
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
    assert asdict(manifest.CI_JOB_GRAPH[-1])["job_ref"] == "foundation-gate-report"


def test_visual_scope_is_fail_closed_and_path_bound() -> None:
    assert manifest.visual_scope_for_paths(None) == "unknown_fail_closed"
    assert manifest.visual_scope_for_paths(("src/ultimate_ai_agent/api/app.py",)) == "not_affected"
    assert manifest.visual_scope_for_paths(("apps/control-center/src/App.tsx",)) == "affected"
