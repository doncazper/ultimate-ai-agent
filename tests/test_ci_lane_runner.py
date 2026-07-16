from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.verification import run_ci_lane as runner
from scripts.verification.ci_command_manifest import CommandSpec, LaneSpec, build_plan
from scripts.verification.verification_contracts import VerificationTerminalStatus


ROOT = Path(__file__).resolve().parents[1]
SHA = subprocess.run(
    ("git", "rev-parse", "HEAD"),
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


class _FakeFullSuiteLock:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def __enter__(self) -> _FakeFullSuiteLock:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def ensure_start_available(self) -> None:
        pass

    def record_start(self) -> None:
        pass


def _write_pytest_performance_report(
    path: Path,
    *,
    failed_index: int | None = None,
    timed_out: bool = False,
    plan_ref: str = "pytest-shard-plan-ref:sha256:" + "a" * 64,
    run_status: str | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "uaa_pytest_performance_report.v1",
                "plan_fingerprint_ref": plan_ref,
                "run_status": run_status
                or (
                    "timeout"
                    if timed_out
                    else "failed"
                    if failed_index is not None
                    else "green"
                ),
                "shards": [
                    {
                        "shard_index": index,
                        "return_code": 1 if index == failed_index else 0,
                        "timed_out": timed_out and index == failed_index,
                    }
                    for index in range(8)
                ],
            }
        ),
        encoding="utf-8",
    )


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
    assert (
        json.loads(receipt_file.read_text(encoding="utf-8"))["receipt_ref"]
        == receipt["receipt_ref"]
    )


def test_typed_lane_evidence_is_content_bound_and_partial_run_is_blocked() -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    command_results = [
        {
            "command_ref": command_ref,
            "status": "pass",
            "duration_ms": 1,
            "output_byte_count": 0,
            "output_digest": "a" * 64,
            "result_ref": f"result-ref:ci:{index}",
        }
        for index, command_ref in enumerate(
            ("command:ci.ruff", "command:ci.self-hosted-contract"), start=1
        )
    ]
    legacy_receipt = {
        "receipt_ref": "receipt-ref:ci-lane:legacy",
        "status": "pass",
        "started_at": "2026-07-15T00:00:00Z",
        "completed_at": "2026-07-15T00:00:01Z",
        "duration_ms": 1_000,
    }

    receipt, run = runner._build_typed_lane_evidence(
        lane_ref="ci-lint",
        legacy_receipt=legacy_receipt,
        full_plan=plan,
        results=command_results,
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
    )

    assert receipt.status is VerificationTerminalStatus.PASSED
    assert receipt.receipt_ref.endswith(receipt.receipt_fingerprint or "missing")
    assert run.status is VerificationTerminalStatus.BLOCKED
    assert run.receipt_refs == (receipt.receipt_ref,)
    serialized = json.dumps(
        {"receipt": asdict(receipt), "run": asdict(run)}, sort_keys=True
    )
    assert "/Users/" not in serialized
    assert "raw_output" not in serialized


def test_receipt_writer_rejects_outside_parent_before_creating_it(
    tmp_path: Path,
) -> None:
    temp_root = runner._safe_temp_root(tmp_path / "temp")
    outside = tmp_path / "outside" / "receipt.json"

    with pytest.raises(ValueError, match="inside the temp root"):
        runner._write_receipt(outside, {"safe": True}, temp_root)

    assert not outside.parent.exists()


def test_receipt_writer_rejects_symlinked_parent(tmp_path: Path) -> None:
    temp_root = runner._safe_temp_root(tmp_path / "temp")
    outside = tmp_path / "outside"
    outside.mkdir()
    (temp_root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="inside the temp root"):
        runner._write_receipt(
            temp_root / "linked" / "receipt.json",
            {"safe": True},
            temp_root,
        )

    assert not (outside / "receipt.json").exists()


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


def test_pytest_shard_evidence_retains_only_reproducible_failed_refs(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(report, failed_index=3)

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence == {
        "pytest_shard_evidence_status": "available",
        "pytest_shard_plan_fingerprint_ref": (
            "pytest-shard-plan-ref:sha256:" + "a" * 64
        ),
        "pytest_shard_count": 8,
        "failed_shard_count": 1,
        "failed_shard_refs": ("pytest-shard-ref:3:failed",),
    }
    serialized = json.dumps(evidence, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "raw" not in serialized


def test_pytest_shard_evidence_marks_timeout_without_raw_output(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(report, failed_index=6, timed_out=True)

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence["failed_shard_refs"] == ("pytest-shard-ref:6:timed-out",)


def test_pytest_shard_evidence_rejects_symlink_and_malformed_report(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.json"
    _write_pytest_performance_report(outside, failed_index=1)
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    report.symlink_to(outside)

    symlink_evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )
    assert symlink_evidence["pytest_shard_evidence_status"] == "rejected"
    assert "unsafe" in symlink_evidence["pytest_shard_evidence_reason_ref"]

    report.unlink()
    report.write_text('{"schema_version":"wrong"}', encoding="utf-8")
    malformed_evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )
    assert malformed_evidence["pytest_shard_evidence_status"] == "rejected"
    assert "invalid" in malformed_evidence["pytest_shard_evidence_reason_ref"]


def test_pytest_lane_receipt_and_summary_retain_safe_failed_shard_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pytest-shards",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")

    def fake_run_command(
        _command: CommandSpec,
        *,
        temp_root: Path,
        **_kwargs: object,
    ) -> dict[str, object]:
        _write_pytest_performance_report(
            temp_root / runner.PYTEST_PERFORMANCE_REPORT_NAME,
            failed_index=2,
        )
        return {
            "command_ref": "command:test.pytest-shards",
            "category": "test",
            "status": "fail",
            "duration_ms": 1,
            "result_ref": "result-ref:ci:test",
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        runner,
        "expected_pytest_shard_plan_ref",
        lambda: "pytest-shard-plan-ref:sha256:" + "a" * 64,
    )
    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    summary_file = tmp_path / "summary.md"

    receipt = runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        summary_file=summary_file,
    )

    result = receipt["command_results"][0]
    assert result["failed_shard_refs"] == ("pytest-shard-ref:2:failed",)
    summary = summary_file.read_text(encoding="utf-8")
    assert "pytest-shard-ref:2:failed" in summary
    assert "make ci-reproduce-shard CI_SHARD_INDEX=2" in summary
    assert str(tmp_path) not in json.dumps(receipt, sort_keys=True)


def test_main_prints_safe_failed_shard_reproduction_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt = {
        "lane_ref": "ci-pytest-shards",
        "status": "fail",
        "repository_sha": SHA,
        "plan": {"definition_fingerprint": "manifest-ref:safe"},
        "command_results": [
            {
                "command_ref": "command:pytest.sharded-suite",
                "status": "fail",
                "pytest_shard_evidence_status": "available",
                "failed_shard_refs": ("pytest-shard-ref:4:failed",),
            }
        ],
    }
    monkeypatch.setattr(runner, "run_lane", lambda *_args, **_kwargs: receipt)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pytest-shard-ref:4:failed" in captured.out
    assert "make ci-reproduce-shard CI_SHARD_INDEX=4" in captured.out
    assert str(tmp_path) not in captured.out


def test_pytest_shard_evidence_rejects_stale_or_contradictory_report(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(
        report,
        plan_ref="pytest-shard-plan-ref:sha256:" + "b" * 64,
    )
    stale = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="pass",
    )
    assert stale["pytest_shard_evidence_status"] == "rejected"

    report.unlink()
    _write_pytest_performance_report(report, failed_index=2)
    contradictory = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="pass",
    )
    assert contradictory["pytest_shard_evidence_status"] == "rejected"
    assert "inconsistent" in contradictory["pytest_shard_evidence_reason_ref"]


def test_pytest_lane_rejects_preexisting_performance_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pytest-shards",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    _write_pytest_performance_report(temp_root / runner.PYTEST_PERFORMANCE_REPORT_NAME)
    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    started: list[bool] = []
    monkeypatch.setattr(
        runner,
        "_run_command",
        lambda *_args, **_kwargs: started.append(True),
    )

    with pytest.raises(ValueError, match="must not predate"):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=temp_root,
        )
    assert started == []


def test_full_suite_attempt_is_fenced_before_process_spawn(
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
    assert starts == [True]


def test_pytest_lane_rejects_missing_runtime_before_attempt_lock(
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
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: None)

    with pytest.raises(
        runner.PytestRuntimeUnavailableError,
        match="pytest runtime is unavailable",
    ):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            full_suite_lock_mode="private",
        )


def test_cli_redacts_missing_pytest_runtime_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"pytest missing from {tmp_path}"

    def _raise_unavailable(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.PytestRuntimeUnavailableError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_unavailable)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:pytest-runtime-unavailable"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_cli_redacts_full_suite_lock_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"lock unavailable at {tmp_path}"

    def _raise_unavailable(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.FullSuiteLockUnavailableError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_unavailable)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:full-suite-capacity-unavailable"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_cli_redacts_duplicate_full_suite_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"duplicate attempt recorded at {tmp_path}"

    def _raise_duplicate(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.FullSuiteAttemptAlreadyRecordedError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_duplicate)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:full-suite-attempt-recorded"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


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
