from __future__ import annotations

import json
from pathlib import Path

from scripts.verification.verify_codeql_sarif import high_severity_findings
from scripts.verification.verify_sbom_artifacts import _validate


ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PIN = "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5"
CODEQL_PIN = "github/codeql-action/init@02c5e83432fe5497fd85b873b6c9f16a8578e1d9"


def test_supply_chain_workflow_is_portable_locked_and_commit_pinned() -> None:
    workflow = (ROOT / ".github/workflows/supply-chain.yml").read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in workflow
    assert "uv sync --frozen --extra dev" in workflow
    assert "uv export --quiet --frozen --extra dev --no-emit-project" in workflow
    assert '.venv/bin/pip-audit --strict -r "$RUNNER_TEMP/locked-requirements.txt"' in workflow
    assert "npm audit --audit-level=high" in workflow
    assert "cyclonedx-py environment" in workflow
    assert CHECKOUT_PIN in workflow
    assert CODEQL_PIN in workflow
    assert "dependency-review:" in workflow
    assert "Reject known high-risk dependencies" in workflow
    assert "dependency-compatibility:" in workflow
    assert "resolution: [lowest-direct, highest]" in workflow
    assert 'uv venv ".venv-${{ matrix.resolution }}" --python 3.12' in workflow
    assert "@v" not in workflow
    assert "persist-credentials: false" in workflow
    assert "upload: never" in workflow
    assert ".venv/bin/mutmut run --max-children 4" in workflow
    assert "scripts/verification/verify_mutation_score.py" in workflow


def test_runtime_dependencies_have_upper_bounds() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for dependency in ("cryptography", "fastapi", "uvicorn", "pydantic", "starlette"):
        declaration = next(
            line
            for line in project.splitlines()
            if line.strip().startswith(f'"{dependency}')
        )
        assert "<" in declaration


def test_sbom_validator_requires_real_cyclonedx_components(tmp_path: Path) -> None:
    sbom = tmp_path / "sbom.json"
    sbom.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [{"type": "library", "name": "safe-sample"}],
            }
        ),
        encoding="utf-8",
    )

    assert _validate(sbom, "test").startswith("sha256:")


def test_codeql_sarif_gate_rejects_high_severity_findings(tmp_path: Path) -> None:
    sarif = tmp_path / "result.sarif"
    sarif.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "tool": {
                            "driver": {
                                "rules": [
                                    {
                                        "id": "py/example",
                                        "properties": {"security-severity": "9.1"},
                                    }
                                ]
                            }
                        },
                        "results": [{"ruleId": "py/example"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert high_severity_findings(tmp_path) == ["CODEQL_HIGH_SEVERITY:py/example:9.1"]


def test_codeql_sarif_gate_fails_closed_for_unscored_errors(tmp_path: Path) -> None:
    sarif = tmp_path / "unscored-error.sarif"
    sarif.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "tool": {"driver": {"rules": [{"id": "py/unscored"}]}},
                        "results": [{"ruleId": "py/unscored", "level": "error"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert high_severity_findings(tmp_path) == [
        "CODEQL_HIGH_SEVERITY:py/unscored:10"
    ]
