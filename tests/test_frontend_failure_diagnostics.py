from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.verification import frontend_failure_diagnostics as diagnostics


SAFE_REF = re.compile(
    r"^frontend-test-ref:(?:vitest|playwright):"
    r"[A-Za-z0-9_.-]{1,72}:[a-f0-9]{12}$"
)


def _write_result(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_vitest_failure_refs_are_bounded_and_content_free(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    test_file = repository / "apps/control-center/src/ActionInbox.test.tsx"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("", encoding="utf-8")
    raw_title = "operator prompt and local-user-content"
    assertions = [
        {
            "fullName": f"{raw_title}-{index}",
            "status": "failed",
        }
        for index in range(12)
    ]
    result = _write_result(
        tmp_path / "vitest.json",
        {
            "testResults": [
                {
                    "name": str(test_file),
                    "assertionResults": assertions,
                }
            ]
        },
    )

    refs = diagnostics.vitest_failed_test_refs(
        result,
        repository_root=repository,
    )

    assert len(refs) == diagnostics.MAX_FAILED_TEST_REFS
    assert refs == tuple(sorted(refs))
    assert all(SAFE_REF.fullmatch(ref) for ref in refs)
    rendered = json.dumps(refs)
    assert "ActionInbox.test.tsx" in rendered
    assert raw_title not in rendered
    assert str(tmp_path) not in rendered


def test_playwright_failure_ref_identifies_only_repo_test_file(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    playwright_root = repository / "apps/control-center"
    test_file = playwright_root / "e2e/control-center.visual.spec.ts"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("", encoding="utf-8")
    result = _write_result(
        tmp_path / "playwright.json",
        {
            "config": {"rootDir": str(playwright_root)},
            "suites": [
                {
                    "specs": [
                        {
                            "file": "e2e/control-center.visual.spec.ts",
                            "id": "raw-spec-identity",
                            "tests": [
                                {
                                    "projectId": "desktop",
                                    "status": "unexpected",
                                }
                            ],
                        }
                    ]
                }
            ],
        },
    )

    refs = diagnostics.playwright_failed_test_refs(
        result,
        repository_root=repository,
    )

    assert len(refs) == 1
    assert SAFE_REF.fullmatch(refs[0])
    assert "control-center.visual.spec.ts" in refs[0]
    assert "raw-spec-identity" not in refs[0]
    assert str(tmp_path) not in refs[0]


def test_failed_refs_append_only_safe_summary_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv(diagnostics.SUMMARY_ENV, str(summary))
    ref = "frontend-test-ref:playwright:visual.spec.ts:0123456789ab"

    diagnostics.publish_failed_test_refs((ref,), failed_test_count=1)

    expected = (
        "Frontend diagnostic refs: 1 of 1 failed tests\n"
        f"Diagnostic frontend test ref: {ref}\n"
    )
    assert summary.read_text(encoding="ascii") == expected
    assert capsys.readouterr().out == expected


def test_failed_refs_reject_symlink_summary_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_summary = tmp_path / "real.md"
    real_summary.write_text("unchanged\n", encoding="ascii")
    linked_summary = tmp_path / "linked.md"
    linked_summary.symlink_to(real_summary)
    monkeypatch.setenv(diagnostics.SUMMARY_ENV, str(linked_summary))

    with pytest.raises(
        diagnostics.FrontendFailureDiagnosticsError,
        match="unavailable",
    ):
        diagnostics.publish_failed_test_refs(
            ("frontend-test-ref:vitest:unit.test.ts:0123456789ab",),
            failed_test_count=1,
        )

    assert real_summary.read_text(encoding="ascii") == "unchanged\n"
