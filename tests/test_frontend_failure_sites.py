from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verification import frontend_failure_diagnostics as diagnostics


def _report(tmp_path: Path, *, line: object = 141, outside: bool = False) -> tuple[Path, Path]:
    repository = tmp_path / "repo"
    root = repository / "apps/control-center/tests/visual"
    root.mkdir(parents=True)
    test_file = root / "foundation-surfaces.real.spec.ts"
    test_file.touch()
    result = tmp_path / "report.json"
    result.write_text(json.dumps({
        "config": {"rootDir": str(root)},
        "suites": [{"specs": [{
            "file": test_file.name,
            "id": "private-spec-identity",
            "title": "private test content",
            "tests": [{
                "projectId": "desktop",
                "status": "unexpected",
                "results": [{
                    "status": "failed",
                    "errors": [{
                        "message": "private assertion content must not escape",
                        "stack": "private stack and local path must not escape",
                        "location": {
                            "file": str(tmp_path / "outside.ts") if outside else str(test_file),
                            "line": line,
                            "column": 25,
                        },
                    }],
                }, {"status": "timedOut", "errors": []}],
            }],
        }]}],
    }), encoding="utf-8")
    return repository, result


def test_playwright_attempt_sites_preserve_identity_status_and_line_only(tmp_path: Path) -> None:
    repository, result = _report(tmp_path)
    sites: set[str] = set()
    refs = diagnostics.playwright_failed_test_refs(
        result, repository_root=repository, attempt_refs=sites,
    )
    identity = refs[0].rsplit(":", 1)[1]
    assert sites == {
        f"frontend-attempt-ref:playwright:{identity}:0:failed:141",
        f"frontend-attempt-ref:playwright:{identity}:1:timed-out:0",
    }
    rendered = json.dumps([refs, sorted(sites)])
    assert "private" not in rendered
    assert str(tmp_path) not in rendered


@pytest.mark.parametrize("line", [True, False, -1, 0, 1_000_000, "141", None])
def test_invalid_failure_line_is_unknown_not_reflected(tmp_path: Path, line: object) -> None:
    repository, result = _report(tmp_path, line=line)
    sites: set[str] = set()
    diagnostics.playwright_failed_test_refs(result, repository_root=repository, attempt_refs=sites)
    assert all(ref.endswith(":0") for ref in sites)


def test_outside_failure_location_is_unknown_not_reflected(tmp_path: Path) -> None:
    repository, result = _report(tmp_path, outside=True)
    sites: set[str] = set()
    diagnostics.playwright_failed_test_refs(result, repository_root=repository, attempt_refs=sites)
    assert all(ref.endswith(":0") for ref in sites)
    assert "outside" not in json.dumps(sorted(sites))


def test_attempt_sites_survive_retention_and_summary_without_raw_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    repository, result = _report(tmp_path)
    sites: set[str] = set()
    refs = diagnostics.playwright_failed_test_refs(result, repository_root=repository, attempt_refs=sites)
    selected = diagnostics.select_failed_attempt_refs(sites, refs)
    diagnostic = tmp_path / diagnostics.DIAGNOSTIC_NAME
    summary = tmp_path / "summary.md"
    diagnostics.retain_failed_test_refs(diagnostic, refs, failed_test_count=1, attempt_refs=selected)
    payload = json.loads(diagnostic.read_text(encoding="ascii"))
    assert payload["schema_version"] == "uaa.frontend_failure_diagnostics.v2"
    assert payload["failed_attempt_refs"] == list(selected)
    assert diagnostics.publish_retained_failed_test_refs(diagnostic, summary_path=summary)
    output = summary.read_text(encoding="ascii") + capsys.readouterr().out
    assert all(ref in output for ref in selected)
    assert "private" not in output
    assert str(tmp_path) not in output
    assert not diagnostic.exists()


@pytest.mark.parametrize("suffix", ["0:failed:1", "0:failed:True", "8:failed:1", "0:private-status:1", "0:failed:1000000"])
def test_unbound_or_invalid_attempt_site_cannot_be_published(tmp_path: Path, suffix: str) -> None:
    ref = "frontend-test-ref:playwright:visual.spec.ts:0123456789ab"
    site = f"frontend-attempt-ref:playwright:fedcba987654:{suffix}"
    summary = tmp_path / "summary.md"
    with pytest.raises(diagnostics.FrontendFailureDiagnosticsError):
        diagnostics.publish_failed_test_refs((ref,), failed_test_count=1, attempt_refs=(site,), summary_path=summary)
    assert not summary.exists()


def test_attempt_selection_is_bounded_and_omits_unselected_tests() -> None:
    refs = tuple(f"frontend-test-ref:playwright:visual.spec.ts:{index:012x}" for index in range(8))
    sites = {
        f"frontend-attempt-ref:playwright:{index:012x}:0:failed:{line}"
        for index in range(9) for line in range(1, 20)
    }
    selected = diagnostics.select_failed_attempt_refs(sites, refs)
    assert len(selected) == diagnostics.MAX_FAILED_ATTEMPT_REFS
    assert selected == tuple(sorted(set(selected)))
    assert all(site.split(":")[2] != f"{8:012x}" for site in selected)


@pytest.mark.parametrize("value", [None, 7, {}, [], ["private content"], ["frontend-attempt-ref:playwright:0123456789ab:0:failed:1"]])
def test_invalid_retained_attempts_are_not_published_or_consumed(tmp_path: Path, value: object) -> None:
    diagnostic = tmp_path / diagnostics.DIAGNOSTIC_NAME
    diagnostic.write_text(json.dumps({
        "schema_version": "uaa.frontend_failure_diagnostics.v2",
        "failed_test_count": 1,
        "failed_test_refs": ["frontend-test-ref:playwright:visual.spec.ts:fedcba987654"],
        "failed_attempt_refs": value,
        "redaction_status": "content_free",
    }), encoding="ascii")
    summary = tmp_path / "summary.md"
    with pytest.raises(diagnostics.FrontendFailureDiagnosticsError):
        diagnostics.publish_retained_failed_test_refs(diagnostic, summary_path=summary)
    assert diagnostic.exists()
    assert not summary.exists()


def test_visual_runner_retains_attempt_location_before_later_phase_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.verification import frontend_command_process
    from scripts.verification import run_frontend_playwright as runner

    repository, result = _report(tmp_path)
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    monkeypatch.setattr(runner, "ROOT", repository)
    monkeypatch.setenv(runner.EVIDENCE_ENV, str(evidence / "aggregate.json"))
    monkeypatch.setattr(runner, "resolve_installed_frontend_tool", lambda *_args: Path("/installed/playwright"))
    calls = 0

    def fake_run(_argv: tuple[str, ...], **kwargs: object) -> int:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise frontend_command_process.FrontendCommandProcessError("bounded phase block")
        env = kwargs["env"]
        assert isinstance(env, dict)
        Path(env["PLAYWRIGHT_JSON_OUTPUT_FILE"]).write_bytes(result.read_bytes())
        return 1

    monkeypatch.setattr(runner, "run_frontend_command", fake_run)
    monkeypatch.setattr(runner, "consume_playwright_json_result", lambda *_args, **_kwargs: {
        "result_status": "failed", "failed_test_count": 1,
    })
    with pytest.raises(runner.FrontendPlaywrightError, match="did not settle safely"):
        runner.run("visual")
    retained = json.loads((evidence / diagnostics.DIAGNOSTIC_NAME).read_text(encoding="ascii"))
    assert retained["schema_version"] == "uaa.frontend_failure_diagnostics.v2"
    assert len(retained["failed_attempt_refs"]) == 2
    assert any(ref.endswith(":failed:141") for ref in retained["failed_attempt_refs"])
    assert calls == 2
