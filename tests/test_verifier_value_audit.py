from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verification import verifier_value_audit as audit


def test_verifier_value_audit_is_registry_bound_and_non_authoritative() -> None:
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


def test_verifier_value_audit_rejects_duplicate_defect_claims() -> None:
    duplicate = audit.VerifierValue(
        "verifier-ref:duplicate",
        ("selector:command-ref:duplicate",),
        audit.VALUES[0].unique_defect_ref,
        "overlap-ref:none",
        "retain",
    )

    with pytest.raises(ValueError, match="VERIFIER_VALUE_DUPLICATE_DEFECT"):
        audit.validate((*audit.VALUES, duplicate))


def test_verifier_value_audit_rejects_registry_coverage_drift() -> None:
    with pytest.raises(ValueError, match="VERIFIER_VALUE_COVERAGE_DRIFT"):
        audit.validate(audit.VALUES[:-1])


def test_verifier_value_audit_rejects_tampered_measurement_artifact(
    tmp_path: Path,
) -> None:
    payload = audit.load_measurements().copy()
    payload["measurements"] = list(payload["measurements"])
    payload["measurements"][0] = dict(payload["measurements"][0])
    payload["measurements"][0]["seconds"] = 999.0
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="FINGERPRINT_INVALID"):
        audit.load_measurements(path)


def test_verifier_value_artifact_binds_exact_measurement_run_and_timings() -> None:
    result = audit.load_measurements()

    assert result["schema_version"] == "uaa-verifier-value-measurements.v2"
    assert result["measurement_run"]["status"] == "passed"
    assert result["measurement_run"]["bindings"]["repository_sha"] == result[
        "source_repository_sha"
    ]
    assert result["measurement_run"]["survived_count"] == 0
    assert result["measurement_run"]["blocked_count"] == 0
    assert all(
        comparison["regression_warning"] is False
        for comparison in result["timing_comparisons"]
    )


def test_verifier_value_audit_rejects_derived_timing_tamper(
    tmp_path: Path,
) -> None:
    payload = audit.load_measurements().copy()
    payload["timing_comparisons"] = [
        dict(row) for row in payload["timing_comparisons"]
    ]
    payload["timing_comparisons"][0]["delta_percent"] = 99.0
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="TIMING_DERIVATION_INVALID"):
        audit.load_measurements(path)


def test_verifier_value_audit_derives_regression_warning_above_fifteen_percent(
    tmp_path: Path,
) -> None:
    payload = audit.load_measurements().copy()
    payload["timing_comparisons"] = [
        dict(row) for row in payload["timing_comparisons"]
    ]
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
) -> None:
    payload = audit.load_measurements().copy()
    payload["source_repository_sha"] = "f" * 40
    payload["fingerprint"] = audit._measurement_fingerprint(payload)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="SOURCE_BINDING_INVALID"):
        audit.load_measurements(path)
