from pathlib import Path

from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    command_registry,
    lane_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def _extract_job_block(workflow: str, job_name: str) -> str:
    lines = workflow.splitlines()
    start = next(index for index, line in enumerate(lines) if line == f"  {job_name}:")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = index
            break
    return "\n".join(lines[start:end])


def test_workflow_job_graph_and_lane_refs_match_canonical_manifest() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for job in CI_JOB_GRAPH:
        section = _extract_job_block(workflow, job.job_ref)
        for dependency in job.needs:
            assert f"- {dependency}" in section
        if job.lane_ref is not None:
            assert "scripts/verification/run_ci_lane.py" in section
            assert f"--lane {job.lane_ref}" in section
            assert '--sha "$UAA_CI_EXACT_SHA"' in section
            assert '--temp-root "$RUNNER_TEMP"' in section
            assert '--summary-file "$GITHUB_STEP_SUMMARY"' in section
        assert f"timeout-minutes: {job.timeout_minutes}" in section


def test_pr_and_push_jobs_checkout_the_same_explicit_sha_they_attest() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert (
        "UAA_CI_EXACT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}"
        in workflow
    )
    checkout_count = workflow.count("uses: actions/checkout@v4")
    assert checkout_count > 0
    assert workflow.count("ref: ${{ env.UAA_CI_EXACT_SHA }}") == checkout_count
    assert "$GITHUB_SHA" not in workflow
    attestation = _extract_job_block(workflow, "manifest-attestation")
    assert "--lane ci-manifest-attestation" in attestation
    assert "Run canonical manifest attestation" in attestation


def test_foundation_gate_ci_report_depends_on_required_verification_jobs() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "foundation-gate-report")
    graph_job = next(job for job in CI_JOB_GRAPH if job.job_ref == "foundation-gate-report")
    for dependency in graph_job.needs:
        assert f"- {dependency}" in section
    assert "--lane ci-foundation-report" in section
    assert "$GITHUB_STEP_SUMMARY" in section


def test_pytest_ci_uses_one_installed_job_with_bounded_workers_and_stable_aggregate() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    shards = _extract_job_block(workflow, "pytest-shards")
    aggregate = _extract_job_block(workflow, "pytest")
    argv = command_registry()["command:pytest.sharded-suite"].argv

    assert "matrix:" not in shards
    assert "- lint" in shards
    assert "- affected-preflight" in shards
    assert argv[argv.index("--shards") + 1] == "8"
    assert argv[argv.index("--max-workers") + 1] == "4"
    assert "--safe-summary" in argv
    assert "--write-timings-json" not in argv
    assert "/usr/sbin/taskpolicy -c utility" in shards
    assert "trap terminate_shard_runner EXIT INT TERM HUP" in shards
    assert 'kill -TERM "$shard_runner_pid"' in shards
    assert "for _ in {1..100}" in shards
    assert 'kill -KILL "$shard_runner_pid"' in shards
    assert "name: pytest" in aggregate
    assert "- pytest-shards" in aggregate
    assert "if: always()" in aggregate
    assert "needs.pytest-shards.result" in aggregate
    assert '!= "success"' in aggregate


def test_fast_affected_preflight_runs_parallel_with_lint_before_full_pytest() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    preflight = _extract_job_block(workflow, "affected-preflight")
    lint = _extract_job_block(workflow, "lint")

    assert "- manifest-attestation" in preflight
    assert "- manifest-attestation" in lint
    assert "--lane ci-affected-preflight" in preflight
    assert "fetch-depth: 0" in preflight
    assert "refs/uaa-ci/base-main" in preflight


def test_release_lanes_are_visible_jobs_using_shared_command_definitions() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    lanes = lane_registry()
    assert "actions/upload-artifact" not in workflow
    for job in CI_JOB_GRAPH:
        if not job.job_ref.startswith("release-lane-"):
            continue
        section = _extract_job_block(workflow, job.job_ref)
        assert f"name: {job.display_name}" in section
        assert f"--lane {job.lane_ref}" in section
        assert job.lane_ref in lanes
        assert "actions/upload-artifact" not in section


def test_openapi_and_frontend_commands_exist_only_in_canonical_registry() -> None:
    commands = command_registry()
    lanes = lane_registry()
    assert "command:route-module.ownership" in lanes["openapi"].command_refs
    assert commands["command:route-module.ownership"].env == (("PYTHONPATH", "src"),)
    assert lanes["frontend"].satisfied_command_refs == ("command:frontend.check",)
    assert command_registry()["command:frontend.check"].argv == ("make", "frontend-check")
