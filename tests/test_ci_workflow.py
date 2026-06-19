from pathlib import Path


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


def test_foundation_gate_ci_report_depends_on_required_verification_jobs():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    section = _extract_job_block(workflow, "foundation-gate-report")

    assert "needs:" in section
    for job in ["lint", "pytest", "static-verification", "control-center-frontend"]:
        assert f"- {job}" in section
    assert "--command-mode ci-parallel" in section
