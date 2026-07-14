from __future__ import annotations

from pathlib import Path

import pytest

from scripts import verify_verifier_maintainability as verifier


def _oversized_module(tmp_path: Path) -> Path:
    path = tmp_path / "sample_verifier.py"
    path.write_text("pass\n" * 701, encoding="utf-8")
    return path


def _patch_single_policy_path(
    monkeypatch: pytest.MonkeyPatch, path: Path
) -> None:
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
            }
        },
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
        "verifier_modules has unsupported line budget enforcement "
        f"{enforcement!r}"
    ]
    assert warnings == []
