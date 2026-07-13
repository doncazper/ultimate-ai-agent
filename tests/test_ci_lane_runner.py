from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.verification import run_ci_lane as runner
from scripts.verification.ci_command_manifest import CommandSpec, LaneSpec, build_plan


ROOT = Path(__file__).resolve().parents[1]
SHA = subprocess.run(
    ("git", "rev-parse", "HEAD"),
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


def _patch_lane(
    monkeypatch: pytest.MonkeyPatch,
    commands: tuple[CommandSpec, ...],
    *,
    optional: tuple[str, ...] = (),
    lane_ref: str = "test-lane",
) -> None:
    registry = {command.command_ref: command for command in commands}
    lane = LaneSpec(
        lane_ref,
        "Test Lane",
        tuple(registry),
        optional_command_refs=optional,
    )
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("docs",),
        verify_repository_state=False,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner, "command_registry", lambda: registry)
    monkeypatch.setattr(runner, "lane_registry", lambda: {lane_ref: lane})
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)


def test_lane_runner_emits_content_free_hash_bound_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "print('private-output-that-must-not-persist')"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))

    receipt_file = tmp_path / "temp" / "receipts" / "lane.json"
    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        receipt_file=receipt_file,
    )

    assert receipt["status"] == "pass"
    assert receipt["github_gate_satisfied"] is False
    assert receipt["merge_gate_satisfied"] is False
    serialized = json.dumps(receipt, sort_keys=True)
    assert "private-output-that-must-not-persist" not in serialized
    assert str(tmp_path) not in serialized
    assert receipt["command_results"][0]["output_byte_count"] > 0
    assert len(receipt["command_results"][0]["output_digest"]) == 64
    assert json.loads(receipt_file.read_text(encoding="utf-8"))["receipt_ref"] == (
        receipt["receipt_ref"]
    )


def test_lane_runner_stops_after_deterministic_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = (
        CommandSpec(
            "command:test.fail",
            (sys.executable, "-c", "raise SystemExit(3)"),
            (),
            "test",
            10,
        ),
        CommandSpec(
            "command:test.must-not-start",
            (sys.executable, "-c", "raise SystemExit(0)"),
            (),
            "test",
            10,
        ),
    )
    _patch_lane(monkeypatch, commands)

    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
    )

    assert receipt["status"] == "fail"
    assert [item["command_ref"] for item in receipt["command_results"]] == [
        "command:test.fail"
    ]


def test_full_suite_attempt_is_not_consumed_when_process_spawn_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.spawn-failure",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    starts: list[bool] = []
    validations: list[bool] = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("spawn failed")),
    )

    with pytest.raises(OSError, match="spawn failed"):
        runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
            validate_start=lambda: validations.append(True),
            before_start=lambda: starts.append(True),
        )

    assert validations == [True]
    assert starts == []


def test_visual_optional_command_is_skipped_only_for_exact_not_affected_posture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = (
        CommandSpec(
            "command:frontend.visual-regression",
            (sys.executable, "-c", "raise SystemExit(9)"),
            (),
            "frontend",
            10,
        ),
        CommandSpec(
            "command:test.contract",
            (sys.executable, "-c", "raise SystemExit(0)"),
            (),
            "test",
            10,
        ),
    )
    _patch_lane(
        monkeypatch,
        commands,
        optional=("command:frontend.visual-regression",),
    )

    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        visual_scope="not_affected",
    )

    assert receipt["status"] == "pass"
    assert receipt["command_results"][0]["status"] == "not_applicable"
    assert receipt["command_results"][1]["status"] == "pass"


def test_summary_rejects_symlink_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    target = tmp_path / "target"
    target.write_text("safe", encoding="utf-8")
    summary = tmp_path / "summary"
    summary.symlink_to(target)

    with pytest.raises(ValueError, match="regular non-symlink"):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            summary_file=summary,
        )


def test_summary_rejects_hardlink_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    target = tmp_path / "target"
    target.write_text("safe", encoding="utf-8")
    summary = tmp_path / "summary"
    summary.hardlink_to(target)
    with pytest.raises(ValueError, match="remain regular"):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            summary_file=summary,
        )


def test_pytest_lane_uses_host_lock_with_exact_sha_and_execution_plane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    captured: list[dict[str, object]] = []

    class FakeLock:
        def __init__(self, **kwargs: object) -> None:
            captured.append(kwargs)

        def __enter__(self) -> None:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def record_start(self) -> None:
            captured[-1]["started"] = True

        def ensure_start_available(self) -> None:
            captured[-1]["start_available"] = True

    monkeypatch.setattr(runner, "FullSuiteLock", FakeLock)
    receipt = runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        full_suite_lock_mode="private",
    )
    assert receipt["status"] == "pass"
    assert captured == [
        {
            "wait_seconds": 0,
            "repository_sha": SHA,
            "attempt_scope": "private",
            "start_available": True,
            "started": True,
        }
    ]
