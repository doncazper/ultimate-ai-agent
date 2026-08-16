from __future__ import annotations

from contextlib import nullcontext
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
    assert published == [((failed_ref,), 1)]


def test_playwright_runner_emits_one_safe_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir(mode=0o700)
    target = evidence_directory / "aggregate.json"
    command: list[tuple[str, ...]] = []
    published: list[tuple[Path, tuple[dict[str, object], ...]]] = []
    monkeypatch.setenv(frontend_playwright.EVIDENCE_ENV, str(target))
    monkeypatch.setattr(
        frontend_playwright,
        "resolve_installed_frontend_tool",
        lambda _app, _tool: Path("/safe-installed/playwright"),
    )

    def fake_run(
        argv: tuple[str, ...],
        **kwargs: object,
    ) -> int:
        assert kwargs["timeout_seconds"] == frontend_playwright.TIMEOUT_SECONDS
        command.append(argv)
        return 0

    monkeypatch.setattr(frontend_playwright, "run_frontend_command", fake_run)
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
        lambda path, observations: published.append((path, observations)),
    )

    assert frontend_playwright.run("visual") == 0
    assert len(command) == 1
    assert "--config=playwright.visual.config.ts" in command[0]
    assert "--project=desktop" in command[0]
    assert "--reporter=json" in command[0]
    assert any(argument.startswith("--output=") for argument in command[0])
    assert command[0][0] == "/safe-installed/playwright"
    assert published == [
        (target, (_observation("runner-ref:frontend:playwright"),))
    ]


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
    monkeypatch.setattr(
        frontend_playwright,
        "run_frontend_command",
        lambda argv, **_kwargs: commands.append(argv) or 0,
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
