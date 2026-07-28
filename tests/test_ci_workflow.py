from pathlib import Path

from scripts.verify_github_hosted_ci import job_dependencies
from scripts.verification.ci_command_manifest import (
    CANONICAL_PYTEST_SHARD_COUNT,
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
        assert job_dependencies(workflow, job.job_ref) == job.needs
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
    assert "UAA_CI_COMPARISON_BASE_SHA:" in workflow
    assert "github.event.pull_request.base.sha" in workflow
    assert "github.event.before" in workflow
    checkout_count = workflow.count(
        "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    )
    assert checkout_count > 0
    assert workflow.count("ref: ${{ env.UAA_CI_EXACT_SHA }}") == checkout_count
    assert "$GITHUB_SHA" not in workflow
    attestation = _extract_job_block(workflow, "manifest-attestation")
    assert "--lane ci-manifest-attestation" in attestation
    assert "Run canonical manifest attestation" in attestation


def test_ci_bootstrap_environment_cannot_dirty_exact_plan_attestation() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".ci-bootstrap/" in gitignore


def test_foundation_gate_ci_report_depends_on_required_verification_jobs() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "foundation-gate-report")
    graph_job = next(job for job in CI_JOB_GRAPH if job.job_ref == "foundation-gate-report")
    for dependency in graph_job.needs:
        assert f"- {dependency}" in section
    assert "--lane ci-foundation-report" in section
    assert "$GITHUB_STEP_SUMMARY" in section
    for dependency in (
        "manifest-attestation",
        "lint",
        "affected-preflight",
        "pytest-shards",
        "static-verification",
    ):
        assert f"- {dependency}" in section
        assert f"needs.{dependency}.outputs.verification-envelope" in section
    assert "verification_github_prerequisites.py" in section
    assert "foundation-manifest" in section
    assert section.count('--envelope "$') == 12
    assert "verify_ci_evidence_dag.py" in section
    assert "Install canonical frontend runtime" in section
    assert "working-directory: apps/control-center" in section
    assert "run: npm ci" in section
    assert "if: always()" in section
    assert "uaa_foundation_prerequisite_manifest.json" in section
    assert '--github-output-file "$GITHUB_OUTPUT"' in section
    dependency_envelopes = tuple(
        line.strip().removeprefix('--dependency-envelope "$').removesuffix('" \\')
        for line in section.splitlines()
        if line.strip().startswith('--dependency-envelope "$')
    )
    assert dependency_envelopes == (
        "MANIFEST_ENVELOPE",
        "LINT_ENVELOPE",
        "AFFECTED_ENVELOPE",
        "DOCS_ENVELOPE",
        "OPENAPI_ENVELOPE",
        "API_SAFETY_ENVELOPE",
        "SECURITY_REDACTION_ENVELOPE",
        "PRODUCT_TRUTH_ENVELOPE",
        "LOCAL_MODEL_ENVELOPE",
        "DURABILITY_ENVELOPE",
        "PYTEST_SHARDS_ENVELOPE",
        "PYTEST_ENVELOPE",
        "STATIC_ENVELOPE",
        "CONTROL_CENTER_ENVELOPE",
        "DESKTOP_ENVELOPE",
        "FRONTEND_ENVELOPE",
        "VISUAL_ENVELOPE",
        "PERFORMANCE_ENVELOPE",
    )


def test_pytest_ci_uses_one_installed_job_with_bounded_workers_and_stable_aggregate() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    shards = _extract_job_block(workflow, "pytest-shards")
    aggregate = _extract_job_block(workflow, "pytest")
    argv = command_registry()["command:pytest.sharded-suite"].argv

    assert "matrix:" not in shards
    assert "- manifest-attestation" in shards
    assert "- lint" not in shards
    assert "- affected-preflight" not in shards
    assert argv[argv.index("--shards") + 1] == str(
        CANONICAL_PYTEST_SHARD_COUNT
    )
    assert argv[argv.index("--max-workers") + 1] == "4"
    assert "--safe-summary" in argv
    assert "--write-timings-json" in argv
    assert (
        argv[argv.index("--write-timings-json") + 1]
        == "{temp_root}/uaa_pytest_file_timings.json"
    )
    assert "runs-on: macos-15" in shards
    assert (
        '--verification-execution-fence-root "$RUNNER_TEMP/'
        'uaa-verification-execution-fence-v2"'
        in shards
    )
    assert "/usr/sbin/taskpolicy" not in shards
    assert "trap terminate_shard_runner EXIT INT TERM HUP" in shards
    assert 'kill -TERM "$shard_runner_pid"' in shards
    assert "for _ in {1..100}" in shards
    assert 'kill -KILL "$shard_runner_pid"' in shards
    assert "name: pytest" in aggregate
    assert "- pytest-shards" in aggregate
    assert "if: always()" in aggregate
    assert "needs.pytest-shards.result" in aggregate
    assert '!= "success"' in aggregate
    assert "verification_github_prerequisites.py" in aggregate
    assert "aggregate" in aggregate
    assert aggregate.count('--envelope "$') == 11
    assert "STATIC_ENVELOPE" not in aggregate
    assert '--github-output-file "$GITHUB_OUTPUT"' in aggregate


def test_exact_github_receipt_outputs_are_non_artifact_job_dependencies() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for job_ref in (
        "manifest-attestation",
        "lint",
        "affected-preflight",
        "pytest-shards",
        "static-verification",
    ):
        section = _extract_job_block(workflow, job_ref)
        assert "verification-envelope:" in section
        assert "steps.canonical.outputs.verification_envelope" in section
        assert 'id: canonical' in section
        assert '--github-output-file "$GITHUB_OUTPUT"' in section
        assert '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"' in section
    pytest_section = _extract_job_block(workflow, "pytest")
    for job_ref in (
        "manifest-attestation",
        "lint",
        "affected-preflight",
        "pytest-shards",
    ):
        assert f"- {job_ref}" in pytest_section
        assert f"needs.{job_ref}.outputs.verification-envelope" in pytest_section
    assert "actions/upload-artifact" not in workflow
    assert "actions/download-artifact" not in workflow

    aggregate = _extract_job_block(workflow, "pytest")
    foundation = _extract_job_block(workflow, "foundation-gate-report")
    assert '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"' in aggregate
    assert foundation.count('--base-sha "$UAA_CI_COMPARISON_BASE_SHA"') == 3


def test_frontend_exact_receipt_is_fenced_and_reused_by_release_lane() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    control = _extract_job_block(workflow, "control-center-frontend")
    release = _extract_job_block(workflow, "release-lane-frontend")
    visual = _extract_job_block(workflow, "release-lane-visual-regression")

    assert "verification-envelope:" in control
    assert "steps.canonical.outputs.verification_envelope" in control
    assert 'id: canonical' in control
    assert "--verification-execution-fence-root" in control
    assert '--github-output-file "$GITHUB_OUTPUT"' in control
    assert '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"' in control

    assert "verification-envelope:" in release
    assert "needs.control-center-frontend.outputs.verification-envelope" in release
    assert '--dependency-envelope "$CONTROL_CENTER_FRONTEND_ENVELOPE"' in release
    assert '--github-output-file "$GITHUB_OUTPUT"' in release
    assert '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"' in release

    assert "verification-envelope:" in visual
    assert visual.count('--github-output-file "$GITHUB_OUTPUT"') == 1
    assert '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"' in visual


def test_independent_preflights_and_full_pytest_start_after_manifest() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    preflight = _extract_job_block(workflow, "affected-preflight")
    lint = _extract_job_block(workflow, "lint")
    pytest_shards = _extract_job_block(workflow, "pytest-shards")

    assert "- manifest-attestation" in preflight
    assert "- manifest-attestation" in lint
    assert "- manifest-attestation" in pytest_shards
    assert "- lint" not in pytest_shards
    assert "- affected-preflight" not in pytest_shards
    assert "--lane ci-affected-preflight" in preflight
    assert "fetch-depth: 0" in preflight
    assert "refs/uaa-ci/base-main" in preflight
    assert 'git cat-file -e "${UAA_CI_COMPARISON_BASE_SHA}^{commit}"' in preflight


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
    assert command_registry()["command:frontend.check"].argv == (
        ".venv/bin/python",
        "scripts/verification/run_frontend_check.py",
    )
