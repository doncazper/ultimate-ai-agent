from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.verification import run_pytest_shards as runner


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"


def test_run_shards_respects_explicit_worker_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = 0
    max_active = 0

    class ImmediateProcess:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            self._settled = False

        def poll(self) -> int:
            nonlocal active
            if not self._settled:
                active -= 1
                self._settled = True
            return 0

    monkeypatch.setattr(runner.subprocess, "Popen", ImmediateProcess)
    plans = [
        runner.ShardPlan(index, (f"tests/test_{index}.py",), 1.0) for index in range(5)
    ]

    results = runner.run_shards(
        plans,
        root=tmp_path,
        basetemp=tmp_path / "shards",
        junit_dir=None,
        write_timings=False,
        quiet=True,
        max_workers=2,
    )

    assert max_active == 2
    assert [result.index for result in results] == list(range(5))
    assert runner.overall_return_code(results) == 0


def test_run_shards_terminates_all_work_at_hard_runtime_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Clock:
        def __init__(self) -> None:
            self.values = iter((0.0, 0.0, 61.0, 121.0, 121.0, 121.0))
            self.last = 121.0

        def __call__(self) -> float:
            self.last = next(self.values, self.last)
            return self.last

    class HangingProcess:
        pid = None

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.returncode: int | None = None
            self.terminated = False

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = -15

        def kill(self) -> None:
            self.returncode = -9

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            assert self.returncode is not None
            return self.returncode

    monkeypatch.setattr(runner.time, "perf_counter", Clock())
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(runner.subprocess, "Popen", HangingProcess)

    results = runner.run_shards(
        [runner.ShardPlan(0, ("tests/test_hangs.py",), 1.0)],
        root=tmp_path,
        basetemp=tmp_path / "shards",
        junit_dir=None,
        write_timings=False,
        quiet=False,
        stretch_goal_seconds=30.0,
        target_seconds=60.0,
        hard_timeout_seconds=120.0,
        termination_grace_seconds=0.0,
        overall_started=0.0,
    )

    assert runner.overall_return_code(results) == runner.TIMEOUT_RETURN_CODE
    assert results[0].timed_out is True
    assert results[0].returncode == runner.TIMEOUT_RETURN_CODE
    output = capsys.readouterr().out
    assert "target exceeded" in output
    assert "hard timeout exceeded" in output
    assert "runtime budget expired" in results[0].log_path.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_terminate_active_shards_kills_real_process_group(tmp_path: Path) -> None:
    log_path = tmp_path / "real-process-group.log"
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import subprocess, sys, time; "
                "child = subprocess.Popen([sys.executable, '-c', "
                "'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                'print("ready", flush=True); time.sleep(60)\'], '
                "stdout=subprocess.PIPE, text=True); "
                "assert child.stdout is not None; "
                "assert child.stdout.readline().strip() == 'ready'; "
                "print(child.pid, flush=True); time.sleep(60)"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    assert process.stdout is not None
    child_pid = int(process.stdout.readline().strip())
    active = {
        0: (
            process,
            log_handle,
            time.perf_counter(),
            log_path,
            runner.ShardPlan(0, ("tests/test_real_process_group.py",), 1.0),
        )
    }
    results: dict[int, Any] = {}

    try:
        runner._terminate_active_shards(
            active,
            results,
            hard_timeout_seconds=1.0,
            termination_grace_seconds=0.2,
        )
        assert process.poll() is not None
        for _ in range(50):
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            pytest.fail("child process survived process-group termination")
        assert results[0].timed_out is True
    finally:
        try:
            os.killpg(process.pid, 9)
        except ProcessLookupError:
            pass
        process.wait(timeout=2)
        if not log_handle.closed:
            log_handle.close()


@pytest.mark.skipif(os.name != "posix", reason="signal cleanup proof is POSIX-only")
def test_external_sigterm_reaps_active_shard_process_group(tmp_path: Path) -> None:
    pid_path = tmp_path / "active-shard.pid"
    test_path = tmp_path / "test_waits_for_cancellation.py"
    test_path.write_text(
        "\n".join(
            (
                "import os",
                "import time",
                "from pathlib import Path",
                f"Path({str(pid_path)!r}).write_text(str(os.getpid()), encoding='utf-8')",
                "time.sleep(60)",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    script = "\n".join(
        (
            "from pathlib import Path",
            "from scripts.verification import run_pytest_shards as runner",
            "runner.run_shards(",
            f"    [runner.ShardPlan(0, ({str(test_path)!r},), 1.0)],",
            f"    root=Path({str(tmp_path)!r}),",
            f"    basetemp=Path({str(tmp_path / 'shards')!r}),",
            "    junit_dir=None,",
            "    write_timings=False,",
            "    quiet=True,",
            "    termination_grace_seconds=0.2,",
            ")",
        )
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    child_pid: int | None = None

    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if pid_path.exists():
                child_pid = int(pid_path.read_text(encoding="utf-8"))
                break
            if process.poll() is not None:
                pytest.fail("shard runner exited before the cancellation fixture started")
            time.sleep(0.02)
        assert child_pid is not None

        process.terminate()
        assert process.wait(timeout=5) != 0
        for _ in range(50):
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            pytest.fail("active shard survived external runner cancellation")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_overall_return_code_fails_if_any_shard_failed(tmp_path: Path) -> None:
    passed = runner.ShardResult(0, 1, 0, 1.0, tmp_path / "a.log")
    failed = runner.ShardResult(1, 1, 2, 1.0, tmp_path / "b.log")

    assert runner.overall_return_code([passed]) == 0
    assert runner.overall_return_code([passed, failed]) == 1


def test_performance_report_requires_refactor_after_target(tmp_path: Path) -> None:
    output = tmp_path / "performance.json"
    plan = runner.ShardPlan(0, ("tests/test_slow.py",), 75.0)
    result = runner.ShardResult(0, 1, 0, 75.0, tmp_path / "shard.log")

    runner.write_performance_report(
        output,
        plans=[plan],
        results=[result],
        stretch_goal_seconds=90.0,
        target_seconds=100.0,
        hard_timeout_seconds=120.0,
        total_elapsed_seconds=105.0,
        estimated_timings={"tests/test_slow.py": 74.5},
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "target_exceeded"
    assert payload["refactor_required"] is True
    assert payload["refactor_candidates"] == [
        {
            "estimated_seconds": 74.5,
            "shard_index": 0,
            "test_ref": "tests/test_slow.py",
        }
    ]
    assert str(tmp_path) not in json.dumps(payload)


def test_performance_report_never_labels_failed_tests_healthy(tmp_path: Path) -> None:
    output = tmp_path / "performance.json"
    plan = runner.ShardPlan(0, ("tests/test_failed.py",), 1.0)
    result = runner.ShardResult(0, 1, 1, 1.0, tmp_path / "shard.log")

    runner.write_performance_report(
        output,
        plans=[plan],
        results=[result],
        stretch_goal_seconds=100.0,
        target_seconds=115.0,
        hard_timeout_seconds=150.0,
        total_elapsed_seconds=1.0,
        estimated_timings={"tests/test_failed.py": 1.0},
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "test_failed"
    assert payload["run_status"] == "failed"
    assert payload["stretch_goal_met"] is False
    assert payload["advisory_only"] is True
    assert payload["verification_evidence"] is False


def test_timing_output_uses_atomic_process_scoped_temporary_file(
    tmp_path: Path,
) -> None:
    output = tmp_path / "timings.json"

    runner.write_timings_json(
        output,
        [
            {
                "path": "tests/test_a.py",
                "seconds": 1.25,
                "source": "pytest-duration-summary",
            }
        ],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == runner.TIMING_SCHEMA_VERSION
    assert payload["advisory_only"] is True
    assert payload["verification_evidence"] is False
    assert payload["timed_file_count"] == 1
    assert payload["timings"][0]["path"] == "tests/test_a.py"
    assert list(tmp_path.glob("timings.json.*.tmp")) == []


def test_single_shard_rejects_partial_timing_output(capsys) -> None:
    assert (
        runner.main(
            [
                "--shards",
                "8",
                "--shard-index",
                "2",
                "--write-timings-json",
                "timings.json",
            ]
        )
        == 2
    )
    assert "complete shard set" in capsys.readouterr().err


def test_runtime_budget_arguments_fail_closed(capsys) -> None:
    assert runner.main(["--target-seconds", "0"]) == 2
    assert "target-seconds" in capsys.readouterr().err
    assert (
        runner.main(
            [
                "--stretch-goal-seconds",
                "30",
                "--target-seconds",
                "60",
                "--hard-timeout-seconds",
                "60",
            ]
        )
        == 2
    )
    assert "exceed" in capsys.readouterr().err
    assert runner.main(["--stretch-goal-seconds", "nan"]) == 2
    assert "finite" in capsys.readouterr().err
    assert runner.main(["--hard-timeout-seconds", "inf"]) == 2
    assert "finite" in capsys.readouterr().err


def test_safe_summary_omits_local_log_paths(tmp_path: Path, capsys) -> None:
    result = runner.ShardResult(
        index=2,
        file_count=101,
        returncode=0,
        elapsed_seconds=12.5,
        log_path=tmp_path / "private" / "pytest.log",
    )

    runner.print_summary(
        [result],
        assignment_method="deterministic-file-count",
        timing_source="not-requested",
        timing_output=None,
        performance_output=tmp_path / "performance.json",
        stretch_goal_seconds=90.0,
        target_seconds=100.0,
        hard_timeout_seconds=120.0,
        total_elapsed_seconds=12.5,
        safe_summary=True,
    )

    output = capsys.readouterr().out
    assert "pytest-shard-log:2" in output
    assert "pytest-performance-report:local" in output
    assert str(tmp_path) not in output


def test_makefile_makes_sharded_pytest_canonical_and_preserves_serial_diagnostics() -> (
    None
):
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert "\ntest-sharded:\n" in makefile
    assert "\ntest-sharded-profile:\n" in makefile
    assert "\ntest-serial:\n" in makefile
    assert "\nverify-dev-sharded:\n" in makefile
    assert "scripts/verification/run_pytest_shards.py" in makefile
    assert "PYTEST_STRETCH_GOAL_SECONDS ?= 110" in makefile
    assert "PYTEST_TARGET_SECONDS ?= 125" in makefile
    assert "PYTEST_HARD_TIMEOUT_SECONDS ?= 180" in makefile
    assert "PYTEST_PERFORMANCE_REPORT ?=" in makefile
    assert "PYTEST_SHARDS ?= 8" in makefile
    assert "PYTEST_SHARD_WORKERS ?= 8" in makefile
    test_block = makefile.split("\ntest:\n", 1)[1].split("\ntest-serial:", 1)[0]
    assert "test-sharded" in test_block
    verify_block = makefile.split("\nverify:\n", 1)[1].split("\nverify-static:", 1)[0]
    assert "test-sharded" in verify_block
    assert "verify-static" in verify_block
