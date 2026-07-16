from __future__ import annotations

import copy
from pathlib import Path

import pytest

from scripts.verification.ci_command_manifest import CI_JOB_GRAPH, VERIFICATION_DAG
from scripts.verification.verification_shadow_comparison import (
    baseline_fingerprint,
    compare_shadow_baseline,
    load_baseline,
    validate_baseline,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/verification/selector_shadow_baseline.json"


def _baseline() -> dict[str, object]:
    return copy.deepcopy(load_baseline(BASELINE_PATH))


def _refingerprint(payload: dict[str, object]) -> dict[str, object]:
    payload["fingerprint"] = baseline_fingerprint(payload)
    return payload


def test_bounded_shadow_baseline_is_not_less_conservative() -> None:
    comparison = compare_shadow_baseline(
        verification_dag=VERIFICATION_DAG,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        repo=ROOT,
        baseline_path=BASELINE_PATH,
    )

    assert comparison.status == "passed"
    assert len(comparison.case_results) == 11
    assert all(result.status == "passed" for result in comparison.case_results)
    assert len(comparison.comparison_fingerprint) == 64


def test_baseline_cannot_supply_executable_commands() -> None:
    payload = _baseline()
    payload["commands"] = ["command:unsafe"]
    _refingerprint(payload)

    with pytest.raises(
        ValueError,
        match="SHADOW_BASELINE_ROOT_FIELDS_INVALID|EXECUTABLE_CONTENT_FORBIDDEN",
    ):
        validate_baseline(payload)


def test_baseline_rejects_nested_command_content_even_when_refingerprinted() -> None:
    payload = _baseline()
    case = payload["cases"][0]
    case["required_proof_refs"] = ["command:unsafe"]
    _refingerprint(payload)

    with pytest.raises(ValueError, match="EXECUTABLE_CONTENT_FORBIDDEN"):
        validate_baseline(payload)


def test_baseline_fingerprint_detects_tampering() -> None:
    payload = _baseline()
    payload["cases"][0]["minimum_tier"] = "tier_3"

    with pytest.raises(ValueError, match="SHADOW_BASELINE_FINGERPRINT_INVALID"):
        validate_baseline(payload)


def test_shadow_comparison_rejects_lost_proof_coverage() -> None:
    payload = _baseline()
    payload["cases"][0]["required_proof_refs"].append(
        "proof-obligation-ref:unimplemented-legacy-proof"
    )
    _refingerprint(payload)

    comparison = compare_shadow_baseline(
        verification_dag=VERIFICATION_DAG,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        repo=ROOT,
        baseline=payload,
    )

    assert comparison.status == "failed"
    result = comparison.case_results[0]
    assert result.status == "failed"
    assert result.failure_refs == ("shadow-failure-ref:proof-coverage-lost",)


def test_shadow_comparison_rejects_lost_test_ownership() -> None:
    payload = _baseline()
    payload["cases"][3]["required_test_refs"].append(
        "tests/test_capability_maturity_integrity.py"
    )
    _refingerprint(payload)

    comparison = compare_shadow_baseline(
        verification_dag=VERIFICATION_DAG,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        repo=ROOT,
        baseline=payload,
    )

    assert comparison.status == "failed"
    result = comparison.case_results[3]
    assert result.failure_refs == ("shadow-failure-ref:test-ownership-lost",)


def test_symlinked_baseline_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "baseline.json"
    target.write_text(BASELINE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    link = tmp_path / "linked.json"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="SHADOW_BASELINE_FILE_INVALID"):
        load_baseline(link)
