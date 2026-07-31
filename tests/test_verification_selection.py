from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_agent_capability_evaluation import evaluation_source_paths
from scripts.verification.verification_contracts import VerificationRiskTier, VerificationUnit
from scripts.verification.verification_risk import ChangeKind, ChangeRecord
from scripts.verification.verification_selection import (
    EXACT_SOURCE_TEST_OWNERSHIP,
    GOAT_EVIDENCE_SOURCE_PATHS,
    select_owned_test_refs,
    select_verification,
)


ROOT = Path(__file__).resolve().parents[1]


def _unit(unit_ref: str, *, needs: tuple[str, ...] = ()) -> VerificationUnit:
    return VerificationUnit(
        unit_ref=unit_ref,
        display_name=unit_ref,
        lane_ref=f"lane:{unit_ref}",
        needs=needs,
        command_refs=(f"command:{unit_ref}",),
        proof_equivalence_ref=f"proof-equivalence-ref:{unit_ref}",
    )


def _dag() -> tuple[VerificationUnit, ...]:
    refs = (
        "risk-diff-check",
        "risk-documentation",
        "risk-product-truth",
        "risk-redaction",
        "risk-ruff",
        "risk-focused-pytest",
        "risk-frontend-typecheck",
        "risk-frontend-tests",
        "risk-frontend-build",
        "risk-frontend-safety",
        "risk-openapi",
        "risk-api-safety",
        "risk-final-diff-audit",
        "risk-security-audit",
    )
    units = tuple(_unit(ref) for ref in refs)
    return (
        *units,
        _unit("full-root"),
        _unit("full-child", needs=("full-root",)),
    )


FULL_REFS = ("full-child",)


def _change(path: str, kind: ChangeKind = ChangeKind.MODIFIED) -> ChangeRecord:
    return ChangeRecord(kind=kind, path_refs=(path,))


def test_canonical_selection_is_deterministic_and_dependency_closed() -> None:
    records = (
        _change("src/ultimate_ai_agent/core/evals/capability_metrics.py"),
    )

    first = select_verification(
        records,
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )
    second = select_verification(
        records,
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )

    assert first == second
    assert first.risk_tier is VerificationRiskTier.TIER_2
    assert "risk-focused-pytest" in first.selected_unit_refs
    assert first.selected_test_refs == (
        "tests/test_agent_capability_evaluation.py",
        "tests/test_goat_comparison_findings.py",
    )
    assert len(first.selection_fingerprint) == 64


def test_goat_evidence_sources_have_exact_affected_test_ownership() -> None:
    assert GOAT_EVIDENCE_SOURCE_PATHS == evaluation_source_paths()
    for source_path in GOAT_EVIDENCE_SOURCE_PATHS:
        assert "tests/test_goat_comparison_findings.py" in (
            EXACT_SOURCE_TEST_OWNERSHIP[source_path]
        )
    for registry_path in (
        "scripts/run_agent_capability_evaluation.py",
        "scripts/run_uaa_runtime_phase09_benchmark.py",
    ):
        assert "tests/test_verification_selection.py" in (
            EXACT_SOURCE_TEST_OWNERSHIP[registry_path]
        )


def test_cross_surface_ownership_schedules_affected_pytest() -> None:
    selection = select_verification(
        (_change("apps/control-center/src/App.test.tsx"),),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )

    assert selection.risk_tier is VerificationRiskTier.TIER_2
    assert "risk-focused-pytest" in selection.selected_unit_refs
    assert "risk-frontend-tests" in selection.selected_unit_refs
    assert selection.selected_test_refs == (
        "tests/test_goat_comparison_findings.py",
    )


def test_full_selection_closes_declared_dependencies() -> None:
    selection = select_verification(
        (_change("unclassified/runtime.surface"),),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )

    assert selection.risk_tier is VerificationRiskTier.TIER_3
    assert selection.fail_closed is True
    assert selection.selected_unit_refs.index("full-root") < selection.selected_unit_refs.index(
        "full-child"
    )


@pytest.mark.parametrize(
    ("record", "reason_ref"),
    [
        (
            ChangeRecord(ChangeKind.DELETED, ("docs/architecture/removed.md",)),
            "reason-ref:risk:deleted",
        ),
        (
            ChangeRecord(
                ChangeKind.RENAMED,
                ("docs/architecture/old.md", "docs/architecture/new.md"),
            ),
            "reason-ref:risk:renamed",
        ),
        (
            ChangeRecord(ChangeKind.UNKNOWN, ("docs/architecture/unknown.md",)),
            "reason-ref:risk:unknown",
        ),
    ],
)
def test_destructive_or_unknown_change_kinds_fail_closed(
    record: ChangeRecord,
    reason_ref: str,
) -> None:
    selection = select_verification(
        (record,),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )

    assert selection.risk_tier is VerificationRiskTier.TIER_3
    assert selection.full_gate_required is True
    assert reason_ref in selection.escalation_reason_refs


def test_overlapping_change_records_and_unsafe_file_type_fail_closed() -> None:
    overlap = select_verification(
        (
            _change("docs/architecture/verification_notes.md"),
            _change("docs/architecture/verification_notes.md"),
        ),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )
    unsafe = select_verification(
        (_change("docs/architecture/verification_notes.md"),),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
        unsafe_path_refs=("docs/architecture/verification_notes.md",),
    )

    assert "reason-ref:risk:overlapping-change-records" in overlap.escalation_reason_refs
    assert "reason-ref:risk:unsafe-file-type" in unsafe.escalation_reason_refs
    assert overlap.full_gate_required is True
    assert unsafe.full_gate_required is True


def test_api_selection_preserves_legacy_coverage_as_abstract_proof_obligations() -> None:
    selection = select_verification(
        (_change("src/ultimate_ai_agent/api/app.py"),),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=ROOT,
    )

    assert {
        "proof-obligation-ref:api-contract-snapshot",
        "proof-obligation-ref:api-verifier-lane",
        "proof-obligation-ref:openapi-contract",
        "proof-obligation-ref:api-safety",
    }.issubset(selection.coverage_proof_obligation_refs)
    assert not hasattr(selection, "selected_command_refs")
    assert selection.selected_test_refs == (
        "tests/test_api_manifest.py",
        "tests/test_api_route_inventory_fixture.py",
        "tests/test_openapi_contract.py",
    )


def test_missing_owned_test_escalates_to_full_and_drops_partial_test_selection(
    tmp_path: Path,
) -> None:
    source_ref = "src/ultimate_ai_agent/core/evals/capability_metrics.py"
    (tmp_path / source_ref).parent.mkdir(parents=True)
    (tmp_path / source_ref).write_text("VALUE = 1\n", encoding="utf-8")

    selection = select_verification(
        (_change(source_ref),),
        verification_dag=_dag(),
        full_unit_refs=FULL_REFS,
        repo=tmp_path,
    )

    assert selection.risk_tier is VerificationRiskTier.TIER_3
    assert selection.selected_test_refs == ()
    assert "reason-ref:risk:missing-test-ownership" in selection.escalation_reason_refs


def test_python_convention_rejects_symlinked_test_ownership(tmp_path: Path) -> None:
    source_ref = "src/ultimate_ai_agent/core/example.py"
    test_ref = "tests/test_example.py"
    (tmp_path / source_ref).parent.mkdir(parents=True)
    (tmp_path / source_ref).write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "outside.py").write_text("def test_value(): pass\n", encoding="utf-8")
    (tmp_path / test_ref).parent.mkdir(parents=True)
    (tmp_path / test_ref).symlink_to(tmp_path / "outside.py")

    ownership = select_owned_test_refs((source_ref,), repo=tmp_path)

    assert ownership.selected_test_refs == ()
    assert ownership.missing_test_refs == (test_ref,)


def test_unknown_full_unit_ref_is_rejected() -> None:
    with pytest.raises(ValueError, match="VERIFICATION_FULL_UNIT_REFS_UNKNOWN"):
        select_verification(
            (_change("README.md"),),
            verification_dag=_dag(),
            full_unit_refs=("missing-full-unit",),
            repo=ROOT,
        )
