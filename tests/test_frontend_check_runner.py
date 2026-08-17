from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from pathlib import Path

import pytest

from scripts.verification import frontend_command_process
from scripts.verification import run_frontend_check as frontend_check
from scripts.verification import run_frontend_playwright as frontend_playwright


def _observation(runner_ref: str) -> dict[str, object]:
    return {
        "schema_version": "uaa_frontend_collection_evidence.v1",
        "runner_ref": runner_ref,
        "collected_test_count": 3,
        "collection_digest_ref": "sha256:" + "a" * 64,
        "collection_error_count": 0,
        "failed_test_count": 0,
        "flaky_test_count": 0,
        "passed_test_count": 3,
        "redaction_status": "content_free",
        "result_status": "passed",
        "retry_attempt_count": 0,
        "skipped_test_count": 0,
        "todo_test_count": 0,
    }


def test_frontend_script_declarations_fail_closed_on_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = tmp_path / "control-center"
    app.mkdir()
    package = app / "package.json"
    scripts = {
        "typecheck": "tsc -b --pretty false",
        "lint": "tsc -b --pretty false",
        "test": "vitest",
        "build": "tsc -b && vite build",
    }
    package.write_text(json.dumps({"scripts": scripts}), encoding="utf-8")
    monkeypatch.setattr(frontend_check, "APP", app)

    assert frontend_check._load_scripts() == scripts

    package.write_text(
        json.dumps({"scripts": {**scripts, "lint": "eslint ."}}),
        encoding="utf-8",
    )
    with pytest.raises(
        frontend_check.FrontendCheckError,
        match="duplicate-proof declaration changed",
    ):
        frontend_check._load_scripts()


def test_frontend_check_rejects_unsafe_evidence_parent_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir(mode=0o700)
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    monkeypatch.setenv(
        frontend_check.EVIDENCE_ENV,
        str(linked_parent / "aggregate.json"),
    )
    monkeypatch.setattr(
        frontend_check,
        "_run",
        lambda *_args, **_kwargs: pytest.fail(
            "unsafe evidence must block before command execution"
        ),
    )

    with pytest.raises(
        frontend_check.FrontendCollectionEvidenceError,
        match="unsafe",
    ):
        frontend_check.run()


def test_frontend_check_executes_one_typecheck_and_no_duplicate_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    target = evidence_directory / "aggregate.json"
    commands: list[tuple[tuple[str, ...], Path]] = []
    published: list[tuple[Path, tuple[dict[str, object], ...]]] = []
    monkeypatch.setenv(frontend_check.EVIDENCE_ENV, str(target))
    monkeypatch.setattr(frontend_check, "_load_scripts", lambda: {})
    monkeypatch.setattr(
        frontend_check,
        "resolve_installed_frontend_tool",
        lambda _app, _tool: Path("/safe-installed/vite"),
    )

    def fake_run(
        argv: tuple[str, ...],
        *,
        timeout: int,
        env: dict[str, str],
        cwd: Path = frontend_check.ROOT,
    ) -> int:
        assert timeout > 0
        assert env
        commands.append((argv, cwd))
        return 0

    monkeypatch.setattr(frontend_check, "_run", fake_run)
    monkeypatch.setattr(
        frontend_check,
        "consume_vitest_json_result",
        lambda *_args, **_kwargs: _observation("runner-ref:frontend:vitest"),
    )
    monkeypatch.setattr(
        frontend_check,
        "vitest_failed_test_refs",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        frontend_check,
        "publish_frontend_collection_evidence",
        lambda path, observations: published.append((path, observations)),
    )

    assert frontend_check.run() == 0
    assert sum("typecheck" in argv for argv, _cwd in commands) == 1
    assert all("lint" not in argv for argv, _cwd in commands)
    assert commands[-1][0][:2] == ("/safe-installed/vite", "build")
    assert commands[-1][1] == frontend_check.APP
    assert all("tsc" not in argv for argv, _cwd in commands[-1:])
    assert published == [
        (target, (_observation("runner-ref:frontend:vitest"),))
    ]


def test_frontend_check_fails_closed_on_result_status_disagreement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    monkeypatch.setenv(
        frontend_check.EVIDENCE_ENV,
        str(evidence_directory / "aggregate.json"),
    )
    monkeypatch.setattr(frontend_check, "_load_scripts", lambda: {})
    returncodes = iter((0, 1))
    monkeypatch.setattr(
        frontend_check,
        "_run",
        lambda *_args, **_kwargs: next(returncodes),
    )
    monkeypatch.setattr(
        frontend_check,
        "consume_vitest_json_result",
        lambda *_args, **_kwargs: _observation("runner-ref:frontend:vitest"),
    )
    monkeypatch.setattr(
        frontend_check,
        "vitest_failed_test_refs",
        lambda *_args, **_kwargs: (),
    )

    with pytest.raises(
        frontend_check.FrontendCheckError,
        match="status and evidence disagree",
    ):
        frontend_check.run()


def test_frontend_check_publishes_failed_test_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    monkeypatch.setenv(
        frontend_check.EVIDENCE_ENV,
        str(evidence_directory / "aggregate.json"),
    )
    monkeypatch.setattr(frontend_check, "_load_scripts", lambda: {})
    returncodes = iter((0, 1))
    monkeypatch.setattr(
        frontend_check,
        "_run",
        lambda *_args, **_kwargs: next(returncodes),
    )
    failed_observation = _observation("runner-ref:frontend:vitest")
    failed_observation.update(
        failed_test_count=1,
        passed_test_count=2,
        result_status="failed",
    )
    monkeypatch.setattr(
        frontend_check,
        "consume_vitest_json_result",
        lambda *_args, **_kwargs: failed_observation,
    )
    failed_ref = "frontend-test-ref:vitest:unit.test.ts:0123456789ab"
    monkeypatch.setattr(
        frontend_check,
        "vitest_failed_test_refs",
        lambda *_args, **_kwargs: (failed_ref,),
    )
    published: list[tuple[tuple[str, ...], int]] = []
    retained: list[tuple[Path, tuple[str, ...], int]] = []
    monkeypatch.setattr(
        frontend_check,
        "retain_failed_test_refs",
        lambda path, refs, *, failed_test_count: retained.append(
            (path, refs, failed_test_count)
        ),
    )
    monkeypatch.setattr(
        frontend_check,
        "publish_failed_test_refs",
        lambda refs, *, failed_test_count: published.append(
            (refs, failed_test_count)
        ),
    )
    monkeypatch.setattr(
        frontend_check,
        "publish_frontend_collection_evidence",
        lambda *_args, **_kwargs: {},
    )

    assert frontend_check.run() == 1
    assert retained == [
        (
            evidence_directory / frontend_check.DIAGNOSTIC_NAME,
            (failed_ref,),
            1,
        )
    ]
    assert published == [((failed_ref,), 1)]


def test_playwright_visual_runner_isolates_backend_truth_and_preserves_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    target = evidence_directory / "aggregate.json"
    command: list[tuple[str, ...]] = []
    phase_environments: list[dict[str, str]] = []
    invert_list_contents: list[str] = []
    timeouts: list[int] = []
    published: list[tuple[Path, tuple[dict[str, object], ...]]] = []
    monkeypatch.setenv(frontend_playwright.EVIDENCE_ENV, str(target))
    monkeypatch.setenv("CONTROL_CENTER_VISUAL_REUSE_EXISTING_SERVER", "1")
    monkeypatch.setattr(
        frontend_playwright,
        "resolve_installed_frontend_tool",
        lambda _app, _tool: Path("/safe-installed/playwright"),
    )

    def fake_run(
        argv: tuple[str, ...],
        **kwargs: object,
    ) -> int:
        timeouts.append(int(kwargs["timeout_seconds"]))
        phase_environments.append(dict(kwargs["env"]))
        for argument in argv:
            if argument.startswith("--test-list-invert="):
                invert_list_contents.append(
                    Path(argument.split("=", 1)[1]).read_text(encoding="ascii")
                )
        command.append(argv)
        return 0

    monkeypatch.setattr(frontend_playwright, "run_frontend_command", fake_run)
    monotonic = iter((0.0, 0.0, 100.0, 100.0, 100.0))
    monkeypatch.setattr(
        frontend_playwright.time,
        "monotonic",
        lambda: next(monotonic),
    )
    backend_observation = _observation("runner-ref:frontend:playwright")
    backend_observation.update(
        collected_test_count=2,
        collection_digest_ref="sha256:" + "b" * 64,
        passed_test_count=2,
    )
    fixture_observation = _observation("runner-ref:frontend:playwright")
    fixture_observation.update(
        collected_test_count=94,
        collection_digest_ref="sha256:" + "c" * 64,
        passed_test_count=94,
    )
    observations = iter((backend_observation, fixture_observation))
    monkeypatch.setattr(
        frontend_playwright,
        "consume_playwright_json_result",
        lambda *_args, **_kwargs: next(observations),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "playwright_failed_test_refs",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "publish_frontend_collection_evidence",
        lambda path, observations: published.append((path, observations)),
    )

    assert frontend_playwright.run("visual") == 0
    assert len(command) == 2
    assert timeouts == [frontend_playwright.TIMEOUT_SECONDS, 800]
    assert all(
        "CONTROL_CENTER_VISUAL_REUSE_EXISTING_SERVER" not in phase_environment
        for phase_environment in phase_environments
    )
    assert frontend_playwright.VISUAL_BACKEND_TRUTH_TEST in command[0]
    assert frontend_playwright.VISUAL_BACKEND_TRUTH_TEST not in command[1]
    assert invert_list_contents == [frontend_playwright.VISUAL_BACKEND_TRUTH_INVERT]
    for phase_command in command:
        assert "--config=playwright.visual.config.ts" in phase_command
        assert "--project=desktop" in phase_command
        assert "--workers=1" in phase_command
        assert "--reporter=json" in phase_command
        assert any(argument.startswith("--output=") for argument in phase_command)
        assert phase_command[0] == "/safe-installed/playwright"
    expected_digest = "sha256:" + hashlib.sha256(
        b"uaa-playwright-phase-aggregate-v1\0"
        + json.dumps(
            [
                backend_observation["collection_digest_ref"],
                fixture_observation["collection_digest_ref"],
            ],
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    assert len(published) == 1
    assert published[0][0] == target
    combined = published[0][1][0]
    assert combined["collected_test_count"] == 96
    assert combined["passed_test_count"] == 96
    assert combined["failed_test_count"] == 0
    assert combined["retry_attempt_count"] == 0
    assert combined["collection_digest_ref"] == expected_digest


def test_playwright_visual_runner_rejects_fractional_timeout_overrun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    monkeypatch.setenv(
        frontend_playwright.EVIDENCE_ENV,
        str(evidence_directory / "aggregate.json"),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "resolve_installed_frontend_tool",
        lambda _app, _tool: Path("/safe-installed/playwright"),
    )
    monotonic = iter((0.0, 899.2))
    monkeypatch.setattr(
        frontend_playwright.time,
        "monotonic",
        lambda: next(monotonic),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "run_frontend_command",
        lambda *_args, **_kwargs: pytest.fail(
            "fractional remaining time must not extend the shared deadline"
        ),
    )

    with pytest.raises(
        frontend_playwright.FrontendPlaywrightError,
        match="bounded timeout",
    ):
        frontend_playwright.run("visual")


def test_smoke_runner_preserves_all_configured_projects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    monkeypatch.setenv(
        frontend_playwright.EVIDENCE_ENV,
        str(evidence_directory / "aggregate.json"),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "resolve_installed_frontend_tool",
        lambda _app, _tool: Path("/safe-installed/playwright"),
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(argv: tuple[str, ...], **kwargs: object) -> int:
        assert kwargs["timeout_seconds"] == frontend_playwright.TIMEOUT_SECONDS
        commands.append(argv)
        return 0

    monkeypatch.setattr(
        frontend_playwright,
        "run_frontend_command",
        fake_run,
    )
    monkeypatch.setattr(
        frontend_playwright,
        "consume_playwright_json_result",
        lambda *_args, **_kwargs: _observation("runner-ref:frontend:playwright"),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "playwright_failed_test_refs",
        lambda *_args, **_kwargs: (),
    )
    monkeypatch.setattr(
        frontend_playwright,
        "publish_frontend_collection_evidence",
        lambda *_args, **_kwargs: {},
    )

    assert frontend_playwright.run("smoke") == 0
    assert "--config=playwright.smoke.config.ts" in commands[0]
    assert all(not argument.startswith("--project=") for argument in commands[0])
    assert all(not argument.startswith("--workers=") for argument in commands[0])


def test_playwright_runner_bounds_installed_tool_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    monkeypatch.setenv(
        frontend_playwright.EVIDENCE_ENV,
        str(evidence_directory / "aggregate.json"),
    )

    def fail_resolution(_app: Path, _tool: str) -> Path:
        raise frontend_command_process.FrontendCommandProcessError(
            "unsafe local tool detail"
        )

    monkeypatch.setattr(
        frontend_playwright,
        "resolve_installed_frontend_tool",
        fail_resolution,
    )

    assert frontend_playwright.main(["--suite", "smoke"]) == 1
    assert capsys.readouterr().out == (
        "Frontend Playwright: blocked "
        "(reason-ref:frontend-check:unsafe-evidence)\n"
    )


def test_installed_frontend_tool_must_resolve_inside_node_modules(
    tmp_path: Path,
) -> None:
    app = tmp_path / "app"
    executable = app / "node_modules" / "vite" / "bin" / "vite.js"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o700)
    bin_directory = app / "node_modules" / ".bin"
    bin_directory.mkdir()
    (bin_directory / "vite").symlink_to(executable)

    assert (
        frontend_command_process.resolve_installed_frontend_tool(app, "vite")
        == executable
    )

    outside = tmp_path / "outside"
    outside.write_text("#!/bin/sh\n", encoding="utf-8")
    outside.chmod(0o700)
    (bin_directory / "playwright").symlink_to(outside)
    with pytest.raises(
        frontend_command_process.FrontendCommandProcessError,
        match="unsafe",
    ):
        frontend_command_process.resolve_installed_frontend_tool(
            app,
            "playwright",
        )


def test_frontend_process_runner_settles_the_owned_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        returncode = 0

    process = Process()
    stopped: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        frontend_command_process,
        "installed_signal_handlers",
        lambda *_args, **_kwargs: nullcontext(),
    )
    monkeypatch.setattr(
        frontend_command_process,
        "spawn_owned_process_group",
        lambda *_args, **_kwargs: process,
    )
    monkeypatch.setattr(
        frontend_command_process,
        "process_group_leader_is_terminal_without_reaping",
        lambda _process: True,
    )
    monkeypatch.setattr(
        frontend_command_process,
        "stop_processes",
        lambda processes, _grace: stopped.append(tuple(processes)),
    )

    assert (
        frontend_command_process.run_frontend_command(
            ("frontend-tool",),
            cwd=tmp_path,
            env={},
            timeout_seconds=1,
        )
        == 0
    )
    assert stopped == [(process,)]


def test_vitest_failure_refs_are_bounded_and_content_free(tmp_path: Path) -> None:
    import re

    from scripts.verification import frontend_failure_diagnostics as diagnostics

    safe_ref = re.compile(
        r"^frontend-test-ref:(?:vitest|playwright):"
        r"[A-Za-z0-9_.-]{1,72}:[a-f0-9]{12}$"
    )
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
    result = tmp_path / "vitest.json"
    result.write_text(
        json.dumps({
            "testResults": [
                {
                    "name": str(test_file),
                    "assertionResults": assertions,
                }
            ]
        }),
        encoding="utf-8",
    )

    refs = diagnostics.vitest_failed_test_refs(
        result,
        repository_root=repository,
    )

    assert len(refs) == diagnostics.MAX_FAILED_TEST_REFS
    assert refs == tuple(sorted(refs))
    assert all(safe_ref.fullmatch(ref) for ref in refs)
    rendered = json.dumps(refs)
    assert "ActionInbox.test.tsx" in rendered
    assert raw_title not in rendered
    assert str(tmp_path) not in rendered


def test_playwright_failure_ref_identifies_only_repo_test_file(
    tmp_path: Path,
) -> None:
    import re

    from scripts.verification import frontend_failure_diagnostics as diagnostics

    safe_ref = re.compile(
        r"^frontend-test-ref:(?:vitest|playwright):"
        r"[A-Za-z0-9_.-]{1,72}:[a-f0-9]{12}$"
    )
    repository = tmp_path / "repo"
    playwright_root = repository / "apps/control-center"
    test_file = playwright_root / "e2e/control-center.visual.spec.ts"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("", encoding="utf-8")
    result = tmp_path / "playwright.json"
    result.write_text(
        json.dumps({
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
        }),
        encoding="utf-8",
    )

    refs = diagnostics.playwright_failed_test_refs(
        result,
        repository_root=repository,
    )

    assert len(refs) == 1
    assert safe_ref.fullmatch(refs[0])
    assert "control-center.visual.spec.ts" in refs[0]
    assert "raw-spec-identity" not in refs[0]
    assert str(tmp_path) not in refs[0]


def test_failed_refs_append_only_safe_summary_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.verification import frontend_failure_diagnostics as diagnostics

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
    from scripts.verification import frontend_failure_diagnostics as diagnostics

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


def test_retained_refs_are_validated_published_and_consumed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.verification import frontend_failure_diagnostics as diagnostics

    directory = tmp_path / "evidence"
    directory.mkdir()
    diagnostic = directory / diagnostics.DIAGNOSTIC_NAME
    summary = tmp_path / "summary.md"
    ref = "frontend-test-ref:vitest:ActionInbox.test.tsx:0123456789ab"

    diagnostics.retain_failed_test_refs(
        diagnostic,
        (ref,),
        failed_test_count=1,
    )
    assert diagnostics.publish_retained_failed_test_refs(
        diagnostic,
        summary_path=summary,
    )

    assert not diagnostic.exists()
    assert ref in summary.read_text(encoding="ascii")
    assert ref in capsys.readouterr().out


def test_invalid_utf8_result_becomes_bounded_diagnostics_error(
    tmp_path: Path,
) -> None:
    from scripts.verification import frontend_failure_diagnostics as diagnostics

    repository = tmp_path / "repo"
    repository.mkdir()
    result = tmp_path / "result.json"
    result.write_bytes(b'{"testResults": ["\xff"]}')

    with pytest.raises(
        diagnostics.FrontendFailureDiagnosticsError,
        match="unavailable",
    ):
        diagnostics.vitest_failed_test_refs(
            result,
            repository_root=repository,
        )


def test_frontend_process_timeout_still_cleans_the_owned_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        returncode = None

    process = Process()
    stopped: list[tuple[object, ...]] = []
    clock = iter((0.0, 1.0))
    monkeypatch.setattr(
        frontend_command_process,
        "installed_signal_handlers",
        lambda *_args, **_kwargs: nullcontext(),
    )
    monkeypatch.setattr(
        frontend_command_process,
        "spawn_owned_process_group",
        lambda *_args, **_kwargs: process,
    )
    monkeypatch.setattr(
        frontend_command_process,
        "process_group_leader_is_terminal_without_reaping",
        lambda _process: False,
    )
    monkeypatch.setattr(
        frontend_command_process.time,
        "monotonic",
        lambda: next(clock),
    )
    monkeypatch.setattr(
        frontend_command_process,
        "stop_processes",
        lambda processes, _grace: stopped.append(tuple(processes)),
    )

    with pytest.raises(
        frontend_command_process.FrontendCommandProcessError,
        match="bounded timeout",
    ):
        frontend_command_process.run_frontend_command(
            ("frontend-tool",),
            cwd=tmp_path,
            env={},
            timeout_seconds=1,
        )
    assert stopped == [(process,)]
