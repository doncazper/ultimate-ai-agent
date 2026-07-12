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
    covered = {
        ref
        for value in first["verifiers"]
        for ref in value["coverage_refs"]
    }
    assert covered == audit.required_coverage_refs()


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
