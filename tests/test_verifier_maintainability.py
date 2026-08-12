from __future__ import annotations

from pathlib import Path

import pytest

from scripts import verify_verifier_maintainability as verifier


def _test_corpus_policy() -> dict[str, object]:
    return {
        "schema_version": "uaa.test_corpus_retirements.v1",
        "retirement_ledger": "docs/verification/test_corpus_retirements.json",
        "comparison_base_env": "UAA_VERIFICATION_BASE_SHA",
        "enforcement": "fail_closed_when_exact_base_is_available",
        "required_evidence": [
            "replacement_refs",
            "assertion_equivalence_artifact",
            "assertion_equivalence_ref",
            "evidence_artifact",
            "evidence_ref",
            "reason",
        ],
    }


def _oversized_module(tmp_path: Path) -> Path:
    path = tmp_path / "sample_verifier.py"
    path.write_text("pass\n" * 701, encoding="utf-8")
    return path


def _patch_single_policy_path(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setattr(verifier, "_iter_policy_paths", lambda _globs: [path])
    monkeypatch.setattr(
        verifier,
        "_relative",
        lambda _path: "scripts/verification/sample_verifier.py",
    )


def test_advisory_line_threshold_warns_without_failing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _patch_single_policy_path(monkeypatch, _oversized_module(tmp_path))
    monkeypatch.setattr(
        verifier,
        "load_json",
        lambda _path: {
            "line_budgets": {
                "verifier_modules": {
                    "max_lines": 700,
                    "enforcement": "advisory",
                    "globs": ["scripts/verification/**/*.py"],
                }
            },
            "test_corpus_guard": {
                "schema_version": "uaa.test_corpus_retirements.v1",
                "retirement_ledger": "docs/verification/test_corpus_retirements.json",
                "comparison_base_env": "UAA_VERIFICATION_BASE_SHA",
                "enforcement": "fail_closed_when_exact_base_is_available",
                "required_evidence": [
                    "replacement_refs",
                    "assertion_equivalence_artifact",
                    "assertion_equivalence_ref",
                    "evidence_artifact",
                    "evidence_ref",
                    "reason",
                ],
            },
        },
    )
    monkeypatch.setattr(
        verifier,
        "verify_test_corpus_guard",
        lambda _root: {},
    )

    assert verifier.main() == 0
    output = capsys.readouterr().out
    assert (
        "WARNING: verifier_modules line review threshold exceeded for "
        "scripts/verification/sample_verifier.py: 701 > 700"
    ) in output
    assert "ERROR:" not in output
    assert "Verifier maintainability verification passed." in output


def test_hard_line_budget_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_single_policy_path(monkeypatch, _oversized_module(tmp_path))
    failures: list[str] = []
    warnings: list[str] = []

    verifier._append_line_budget_findings(
        failures,
        warnings,
        "compatibility_wrappers",
        {"max_lines": 700, "enforcement": "hard", "globs": ["ignored"]},
    )

    assert failures == [
        "compatibility_wrappers line budget exceeded for "
        "scripts/verification/sample_verifier.py: 701 > 700"
    ]
    assert warnings == []


def test_repository_line_budget_policy_is_advisory_only() -> None:
    policy = verifier.load_json(verifier.POLICY_PATH)

    assert {section["enforcement"] for section in policy["line_budgets"].values()} == {
        "advisory"
    }


@pytest.mark.parametrize("enforcement", ["ignored", ["advisory"]])
def test_unknown_line_budget_enforcement_fails_closed(enforcement: object) -> None:
    failures: list[str] = []
    warnings: list[str] = []

    verifier._append_line_budget_findings(
        failures,
        warnings,
        "verifier_modules",
        {"max_lines": 700, "enforcement": enforcement},
    )

    assert failures == [
        f"verifier_modules has unsupported line budget enforcement {enforcement!r}"
    ]
    assert warnings == []


def test_test_corpus_guard_failure_is_part_of_maintainability_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failures: list[str] = []
    monkeypatch.setattr(
        verifier,
        "verify_test_corpus_guard",
        lambda _root: (_ for _ in ()).throw(
            verifier.TestCorpusGuardError("removed test is unaccounted")
        ),
    )

    verifier._append_test_corpus_guard_failures(
        failures,
        {"test_corpus_guard": _test_corpus_policy()},
    )

    assert failures == ["test corpus guard failed: removed test is unaccounted"]


@pytest.mark.parametrize(
    "policy",
    (
        {},
        {"test_corpus_guard": {}},
        {
            "test_corpus_guard": {
                **_test_corpus_policy(),
                "enforcement": "optional",
            }
        },
    ),
)
def test_test_corpus_guard_policy_is_required_and_exact(
    policy: dict[str, object],
) -> None:
    failures: list[str] = []

    verifier._append_test_corpus_guard_failures(failures, policy)

    assert failures == ["test corpus guard policy section is missing or invalid"]
