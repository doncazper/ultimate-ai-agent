from pathlib import Path

import scripts.verify_release_lanes as release_lanes


ROOT = Path(__file__).resolve().parents[1]

RELEASE_LANE_JOBS = {
    f"release-lane-{lane.lane_id}": (
        lane.lane_id,
        lane.name,
        [command.command_ref for command in lane.commands],
    )
    for lane in release_lanes.release_lanes()
}


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


def test_foundation_gate_ci_report_depends_on_required_verification_jobs():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "foundation-gate-report")

    assert "needs:" in section
    for job in ["lint", "pytest", "static-verification", *RELEASE_LANE_JOBS]:
        assert f"- {job}" in section
    assert "--command-mode ci-parallel" in section
    assert "--no-write-latest" in section
    assert "safe-summary-only" in section
    assert "required CI job dependencies" in section
    assert "not collected or uploaded" in section
    assert "$GITHUB_STEP_SUMMARY" in section


def test_release_lanes_are_visible_ci_jobs_with_safe_summary_reports():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "actions/upload-artifact" not in workflow
    for job, (lane_id, lane_name, command_refs) in RELEASE_LANE_JOBS.items():
        section = _extract_job_block(workflow, job)

        assert f"name: Release Lane / {lane_name}" in section
        assert f"- Lane id: {lane_id}" in section
        assert "safe-summary-only" in section
        assert "not uploaded" in section
        assert "$GITHUB_STEP_SUMMARY" in section
        assert '> "$log_file" 2>&1' in section
        assert "actions/upload-artifact" not in section
        for command_ref in command_refs:
            assert command_ref in section


def test_openapi_release_lane_keeps_route_module_ownership_green():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "release-lane-openapi")

    assert "command:route-module.ownership" in section
    assert "tests/test_route_module_ownership.py" in section
    assert "PYTHONPATH=src" in section


def test_frontend_release_lane_uses_existing_frontend_job_as_required_equivalent():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "release-lane-frontend")

    assert "needs:" in section
    assert "- control-center-frontend" in section
    assert "satisfied by required control-center-frontend job" in section
