from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from scripts.verification import run_frontend_check
from scripts.verification import verifier_value_measurement as measurement


def _bindings() -> measurement.MeasurementBindings:
    return measurement.MeasurementBindings(
        repository_sha="a" * 40,
        dependency_state_fingerprint="1" * 64,
        platform_fingerprint="2" * 64,
        command_manifest_fingerprint="3" * 64,
        verifier_definition_fingerprint="4" * 64,
        test_collection_fingerprint="5" * 64,
    )


def test_fixed_measurements_kill_every_synthetic_mutation() -> None:
    original_application = run_frontend_check.APP

    result = measurement.run_measurements(_bindings())

    measurement.validate_measurement_run(result)
    assert result["status"] == "passed"
    assert result["probe_count"] == len(measurement.PROBES) == 4
    assert result["killed_count"] == 4
    assert result["blocked_count"] == 0
    assert result["survived_count"] == 0
    assert {
        record["verifier_ref"] for record in result["value_records"]
    } == {
        "verifier:product-truth",
        "verifier:security-redaction",
        "verifier:api-contract",
        "verifier:control-center-frontend",
    }
    assert all(
        record["outcome"] == "killed" for record in result["value_records"]
    )
    assert run_frontend_check.APP == original_application


def test_measurement_results_are_content_bound_and_content_free() -> None:
    result = measurement.run_measurements(_bindings())
    rendered = json.dumps(result, sort_keys=True)

    assert result["measurement_run_ref"].endswith(result["fingerprint"])
    assert measurement.REDACTION_STATUS in rendered
    assert "synthetic-declaration-drift" not in rendered
    assert "value-probe.md" not in rendered
    assert "value-probe.txt" not in rendered
    assert "api_key" not in rendered
    assert "blocked capability is complete" not in rendered
    for record in result["value_records"]:
        assert record["value_ref"].removeprefix(
            "value:verification:"
        ) == record["receipt_ref"].removeprefix(
            "receipt:verification-value:"
        )
        assert record["repository_sha"] == "a" * 40


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("status", "passed-after-tamper"),
        ("killed_count", 0),
        ("redaction_status", "raw"),
    ],
)
def test_measurement_run_rejects_tampering(
    field: str,
    replacement: object,
) -> None:
    result = measurement.run_measurements(_bindings())
    result[field] = replacement

    with pytest.raises(
        measurement.VerifierValueMeasurementError,
        match="fingerprint",
    ):
        measurement.validate_measurement_run(result)


def test_measurement_record_rejects_content_binding_tamper() -> None:
    result = measurement.run_measurements(_bindings())
    records = list(result["value_records"])
    records[0] = {**records[0], "outcome": "survived"}
    unsigned = {
        **{
            key: value
            for key, value in result.items()
            if key not in {"measurement_run_ref", "fingerprint"}
        },
        "value_records": records,
        "killed_count": 3,
        "survived_count": 1,
        "status": "failed",
    }
    fingerprint = measurement._digest(unsigned)
    tampered = {
        **unsigned,
        "measurement_run_ref": (
            f"measurement-run:verification-value:sha256:{fingerprint}"
        ),
        "fingerprint": fingerprint,
    }

    with pytest.raises(
        measurement.VerifierValueMeasurementError,
        match="record binding",
    ):
        measurement.validate_measurement_run(tampered)


def test_owner_only_temporary_boundary_is_private_and_ephemeral() -> None:
    with measurement._owner_only_temporary_directory() as directory:
        metadata = directory.lstat()
        assert stat.S_ISDIR(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o700
        target = directory / "measurement.json"
        measurement._write_private_json(target, {"safe_ref": "ref:value"})
        assert stat.S_IMODE(target.lstat().st_mode) == 0o600
    assert not directory.exists()


def test_owner_only_boundary_rejects_symlink(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(private, target_is_directory=True)

    with pytest.raises(
        measurement.VerifierValueMeasurementError,
        match="owner-only",
    ):
        measurement._validate_owner_only_directory(linked)


def test_unexpected_probe_failure_is_blocked_without_error_content() -> None:
    def unsafe_probe() -> bool:
        raise OSError("sensitive-value-that-must-not-escape")

    probe = measurement.SyntheticProbe(
        probe_ref="probe:verifier-value:test",
        verifier_ref="verifier:test",
        synthetic_mutation_ref="mutation:test",
        defect_ref="defect:test",
        overlap_ref="overlap:none",
        disposition="retain",
        execute=unsafe_probe,
    )

    result = measurement._run_probe(probe, _bindings())

    assert result.outcome == "blocked"
    assert "sensitive-value" not in json.dumps(
        result.__dict__,
        sort_keys=True,
    )
