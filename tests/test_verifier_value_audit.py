from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.verification import verifier_value_audit as audit


def _artifact_payload() -> dict[str, object]:
    return json.loads(audit.MEASUREMENT_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def stable_measurement_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _artifact_payload()
    source_sha = artifact["source_repository_sha"]
    run_bindings = artifact["measurement_run"]["bindings"]
    monkeypatch.setattr(
        audit,
        "_repository_measurement_state",
        lambda _repo, _source_sha: audit.RepositoryMeasurementState(source_sha, ()),
    )
    monkeypatch.setattr(
        audit,
        "_current_measurement_bindings",
        lambda _repo: dict(run_bindings),
    )


def _write_measurement(tmp_path: Path, payload: dict[str, object]) -> Path:
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, filename: str) -> str:
    (repo / filename).write_text(filename, encoding="utf-8")
    _git(repo, "add", filename)
    _git(
        repo,
        "-c",
        "user.name=Verification Fixture",
        "-c",
        "user.email=verification@invalid.example",
        "commit",
        "-m",
        filename,
    )
    return _git(repo, "rev-parse", "HEAD")


def test_verifier_value_audit_is_registry_bound_and_non_authoritative(
    stable_measurement_repository: None,
) -> None:
    first = audit.payload()
    second = audit.payload()

    assert first == second
    assert first["status"] == "current"
    assert first["release_gate_replacement"] is False
    assert first["measurement_fingerprint"].startswith(
        "verifier-measurement-fingerprint:sha256:"
    )
    covered = {ref for value in first["verifiers"] for ref in value["coverage_refs"]}
    assert audit.required_coverage_refs().issubset(covered)
    assert "selector:command:ci.ruff" in covered
    assert "measurement-ref:synthetic-verifier-value" in covered


def test_action_inbox_revision_suite_has_advisory_timing_coverage() -> None:
    timing_seed = json.loads(
        (audit.ROOT / "scripts/verification/pytest_file_timing_seed.json").read_text(
            encoding="utf-8"
        )
    )

    assert any(
        row["path"] == "tests/test_action_inbox_revision_lifecycle.py"
        for row in timing_seed["timings"]
    )


def test_verifier_value_audit_rejects_duplicate_defect_claims(
    stable_measurement_repository: None,
) -> None:
    duplicate = audit.VerifierValue(
        "verifier-ref:duplicate",
        ("selector:command-ref:duplicate",),
        audit.VALUES[0].unique_defect_ref,
        "overlap-ref:none",
        "retain",
    )

    with pytest.raises(ValueError, match="VERIFIER_VALUE_DUPLICATE_DEFECT"):
        audit.validate((*audit.VALUES, duplicate))


def test_verifier_value_audit_rejects_registry_coverage_drift(
    stable_measurement_repository: None,
) -> None:
    with pytest.raises(ValueError, match="VERIFIER_VALUE_COVERAGE_DRIFT"):
        audit.validate(audit.VALUES[:-1])


def test_verifier_value_audit_rejects_tampered_measurement_artifact(
    tmp_path: Path,
    stable_measurement_repository: None,
) -> None:
    payload = audit.load_measurements().copy()
    payload["measurements"] = list(payload["measurements"])
    payload["measurements"][0] = dict(payload["measurements"][0])
    payload["measurements"][0]["seconds"] = 999.0
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="FINGERPRINT_INVALID"):
        audit.load_measurements(path)


def test_verifier_value_artifact_binds_exact_measurement_run_and_timings(
    stable_measurement_repository: None,
) -> None:
    result = audit.load_measurements()

    assert result["schema_version"] == "uaa-verifier-value-measurements.v2"
    assert result["measurement_run"]["status"] == "passed"
    assert (
        result["measurement_run"]["bindings"]["repository_sha"]
        == result["source_repository_sha"]
    )
    assert result["measurement_run"]["survived_count"] == 0
    assert result["measurement_run"]["blocked_count"] == 0
    assert all(
        comparison["regression_warning"] is False
        for comparison in result["timing_comparisons"]
    )


def test_verifier_value_audit_rejects_derived_timing_tamper(
    tmp_path: Path,
    stable_measurement_repository: None,
) -> None:
    payload = audit.load_measurements().copy()
    payload["timing_comparisons"] = [dict(row) for row in payload["timing_comparisons"]]
    payload["timing_comparisons"][0]["delta_percent"] = 99.0
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="TIMING_DERIVATION_INVALID"):
        audit.load_measurements(path)


def test_verifier_value_audit_derives_regression_warning_above_fifteen_percent(
    tmp_path: Path,
    stable_measurement_repository: None,
) -> None:
    payload = audit.load_measurements().copy()
    payload["timing_comparisons"] = [dict(row) for row in payload["timing_comparisons"]]
    row = payload["timing_comparisons"][0]
    row.update(
        {
            "before_samples_ms": [100],
            "after_samples_ms": [120],
            "before_median_ms": 100,
            "after_median_ms": 120,
            "delta_percent": 20.0,
            "comparable": True,
            "regression_warning": True,
        }
    )
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = audit.load_measurements(path)

    assert loaded["timing_comparisons"][0]["regression_warning"] is True


def test_verifier_value_audit_rejects_source_sha_substitution(
    tmp_path: Path,
    stable_measurement_repository: None,
) -> None:
    payload = audit.load_measurements().copy()
    payload["source_repository_sha"] = "f" * 40
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="SOURCE_BINDING_INVALID"):
        audit.load_measurements(path)


@pytest.mark.parametrize("binding_field", audit.MEASUREMENT_BINDING_FIELDS)
def test_verifier_value_audit_rejects_stale_measured_input_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    binding_field: str,
) -> None:
    payload = _artifact_payload()
    source_sha = payload["source_repository_sha"]
    current_bindings = dict(payload["measurement_run"]["bindings"])
    current_bindings[binding_field] = "a" * 64
    monkeypatch.setattr(
        audit,
        "_repository_measurement_state",
        lambda _repo, _source_sha: audit.RepositoryMeasurementState(
            source_sha,
            (),
        ),
    )
    monkeypatch.setattr(
        audit,
        "_current_measurement_bindings",
        lambda _repo: current_bindings,
    )

    path = _write_measurement(tmp_path, payload)

    with pytest.raises(ValueError, match="INPUT_BINDING_DRIFT"):
        audit.load_measurements(path)


def test_verifier_value_audit_allows_documentation_only_descendant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _artifact_payload()
    run_bindings = dict(payload["measurement_run"]["bindings"])
    monkeypatch.setattr(
        audit,
        "_repository_measurement_state",
        lambda _repo, _source_sha: audit.RepositoryMeasurementState(
            "b" * 40,
            ("docs/verification/verifier_value_measurements.json",),
        ),
    )
    monkeypatch.setattr(
        audit,
        "_current_measurement_bindings",
        lambda _repo: run_bindings,
    )

    path = _write_measurement(tmp_path, payload)

    assert (
        audit.load_measurements(path)["source_repository_sha"]
        == payload["source_repository_sha"]
    )


def test_verifier_value_audit_rejects_missing_source_commit(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(repo, "current.txt")

    with pytest.raises(ValueError, match="SOURCE_COMMIT_MISSING"):
        audit._repository_measurement_state(repo, "f" * 40)


def test_verifier_value_audit_rejects_nonancestor_source_commit(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    base_sha = _commit(repo, "base.txt")
    source_sha = _commit(repo, "source.txt")
    _git(repo, "switch", "--detach", "-q", base_sha)
    _commit(repo, "current.txt")

    with pytest.raises(ValueError, match="SOURCE_NOT_ANCESTOR"):
        audit._repository_measurement_state(repo, source_sha)


def test_verifier_value_audit_rejects_non_documentation_commit_after_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _artifact_payload()
    run_bindings = dict(payload["measurement_run"]["bindings"])
    monkeypatch.setattr(
        audit,
        "_repository_measurement_state",
        lambda _repo, _source_sha: audit.RepositoryMeasurementState(
            "b" * 40,
            ("src/ultimate_ai_agent/core/example.py",),
        ),
    )
    monkeypatch.setattr(
        audit,
        "_current_measurement_bindings",
        lambda _repo: run_bindings,
    )

    path = _write_measurement(tmp_path, payload)

    with pytest.raises(ValueError, match="SOURCE_SCOPE_INVALID"):
        audit.load_measurements(path)


def test_verifier_value_audit_rejects_zero_timing_sample(
    tmp_path: Path,
    stable_measurement_repository: None,
) -> None:
    payload = audit.load_measurements().copy()
    payload["timing_comparisons"] = [dict(row) for row in payload["timing_comparisons"]]
    row = payload["timing_comparisons"][0]
    row.update(
        {
            "before_samples_ms": [0],
            "before_median_ms": 0,
            "delta_percent": 0,
        }
    )
    path = _write_measurement(tmp_path, payload)

    with pytest.raises(ValueError, match="TIMING_SAMPLES_INVALID"):
        audit.load_measurements(path)
