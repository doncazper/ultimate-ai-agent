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

from scripts.verification import pytest_shard_processes as shard_processes
from scripts.verification import run_pytest_shards as runner


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
POSIX_CANCELLATION_SIGNALS = tuple(
    candidate
    for candidate in (signal.SIGINT, signal.SIGTERM, getattr(signal, "SIGHUP", None))
    if candidate is not None
)


@pytest.mark.skipif(os.name != "posix", reason="signal mask proof is POSIX-only")
def test_signal_handler_install_and_restore_transitions_are_atomic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    managed = (signal.SIGUSR1, signal.SIGUSR2)
    real_signal = signal.signal
    original_handlers = {
        candidate: signal.getsignal(candidate) for candidate in managed
    }
    observations: list[str] = []
    install_injected = False
    restore_injected = False

    def previous_handler(_signum: int, _frame: Any) -> None:
        assert all(
            signal.getsignal(candidate) is previous_handler for candidate in managed
        )
        observations.append("previous-handlers-complete")

    def installed_handler(_signum: int, _frame: Any) -> None:
        assert all(
            signal.getsignal(candidate) is installed_handler for candidate in managed
        )
        observations.append("installed-handlers-complete")

    for candidate in managed:
        real_signal(candidate, previous_handler)

    def instrumented_signal(candidate: signal.Signals, handler: Any) -> Any:
        nonlocal install_injected, restore_injected
        result = real_signal(candidate, handler)
        if (
            candidate == managed[0]
            and handler is installed_handler
            and not install_injected
        ):
            install_injected = True
            os.kill(os.getpid(), candidate)
        elif (
            candidate == managed[0]
            and handler is previous_handler
            and install_injected
            and not restore_injected
        ):
            restore_injected = True
            os.kill(os.getpid(), candidate)
        return result

    monkeypatch.setattr(shard_processes.signal, "signal", instrumented_signal)
    try:
        with shard_processes.installed_signal_handlers(
            managed,
            installed_handler,
        ):
            assert observations == ["installed-handlers-complete"]
        assert observations == [
            "installed-handlers-complete",
            "previous-handlers-complete",
        ]
    finally:
        for candidate, original_handler in original_handlers.items():
            real_signal(candidate, original_handler)


@pytest.mark.skipif(os.name != "posix", reason="signal mask proof is POSIX-only")
def test_signal_handler_partial_install_failure_restores_installed_subset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    managed = (signal.SIGUSR1, signal.SIGUSR2)
    previous_handlers = {
        managed[0]: object(),
        managed[1]: object(),
    }
    installed_handler = object()
    current_handlers = dict(previous_handlers)
    installed_count = 0
    mask_calls: list[tuple[int, tuple[signal.Signals, ...]]] = []

    def fake_getsignal(candidate: signal.Signals) -> object:
        return current_handlers[candidate]

    def fake_signal(candidate: signal.Signals, handler: object) -> object:
        nonlocal installed_count
        if handler is installed_handler:
            installed_count += 1
            if installed_count == 2:
                raise RuntimeError("injected partial signal installation failure")
        previous = current_handlers[candidate]
        current_handlers[candidate] = handler
        return previous

    def fake_pthread_sigmask(
        how: int,
        candidates: tuple[signal.Signals, ...] | set[signal.Signals],
    ) -> set[signal.Signals]:
        mask_calls.append((how, tuple(candidates)))
        return set()

    monkeypatch.setattr(shard_processes.signal, "getsignal", fake_getsignal)
    monkeypatch.setattr(shard_processes.signal, "signal", fake_signal)
    monkeypatch.setattr(
        shard_processes.signal,
        "pthread_sigmask",
        fake_pthread_sigmask,
    )

    with pytest.raises(
        RuntimeError,
        match="injected partial signal installation failure",
    ):
        with shard_processes.installed_signal_handlers(
            managed,
            installed_handler,  # type: ignore[arg-type]
        ):
            pytest.fail("partial installation must fail before yielding")

    assert current_handlers == previous_handlers
    assert mask_calls[0] == (signal.SIG_BLOCK, managed)
    assert mask_calls[-1] == (signal.SIG_SETMASK, ())


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_permission_denied_group_signal_kills_only_proven_same_owner_members(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_group = 31337
    signals: list[tuple[int, signal.Signals]] = []

    def deny_group_signal(_process_group: int, _sig: signal.Signals) -> None:
        raise PermissionError

    monkeypatch.setattr(shard_processes.os, "killpg", deny_group_signal)
    monkeypatch.setattr(
        shard_processes,
        "_owned_live_process_group_members",
        lambda _process_group: (31338, 31339),
    )
    monkeypatch.setattr(
        shard_processes.os,
        "getpgid",
        lambda _pid: process_group,
    )
    monkeypatch.setattr(
        shard_processes.os,
        "kill",
        lambda pid, sig: signals.append((pid, sig)),
    )

    shard_processes._signal_process_group(process_group, signal.SIGKILL)

    assert signals == [
        (31338, signal.SIGKILL),
        (31339, signal.SIGKILL),
    ]


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_process_group_inspection_rejects_unowned_live_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_group = 31337
    raw = f"31338 {process_group} {os.getuid() + 1} S\n".encode()
    monkeypatch.setattr(
        shard_processes.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=("/bin/ps",),
            returncode=0,
            stdout=raw,
        ),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="ownership could not be proven",
    ) as exc_info:
        shard_processes._owned_live_process_group_members(process_group)

    assert str(process_group) not in str(exc_info.value)
    assert "31338" not in str(exc_info.value)


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_stop_processes_fails_closed_when_group_remains_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnsettledProcess:
        pid = 31337

        def poll(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            pytest.fail("an unsettled process group must fail before leader wait")

    observed_signals: list[signal.Signals] = []
    process = UnsettledProcess()
    proof = shard_processes.OwnedProcessGroup(
        leader_pid=process.pid,
        process_group=process.pid,
        owner_uid=os.getuid(),
    )
    monkeypatch.setattr(shard_processes, "MIN_PROCESS_SETTLEMENT_SECONDS", 0.0)
    monkeypatch.setattr(
        shard_processes,
        "_registered_process_group",
        lambda _process: proof,
    )
    monkeypatch.setattr(
        shard_processes,
        "_require_reserved_process_group",
        lambda _process, _proof: None,
    )
    monkeypatch.setattr(
        shard_processes,
        "_owned_live_process_group_members",
        lambda _process_group: (31338,),
    )
    monkeypatch.setattr(
        shard_processes,
        "_signal_process_group",
        lambda _process_group, sig: observed_signals.append(sig),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="could not be proven",
    ):
        shard_processes.stop_processes((process,), 0.0)  # type: ignore[arg-type]

    assert observed_signals == [signal.SIGTERM, signal.SIGKILL]


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_stop_processes_continues_after_invalid_first_group_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        def __init__(self, pid: int) -> None:
            self.pid = pid
            self.returncode: int | None = None
            self.terminated = False
            self.waited = False

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = -signal.SIGTERM

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            self.waited = True
            if self.returncode is None:
                self.returncode = -signal.SIGTERM
            return self.returncode

    invalid = FakeProcess(31337)
    valid = FakeProcess(31338)
    setattr(invalid, shard_processes._OWNED_PROCESS_GROUP_ATTRIBUTE, "invalid")
    setattr(
        valid,
        shard_processes._OWNED_PROCESS_GROUP_ATTRIBUTE,
        shard_processes.OwnedProcessGroup(
            leader_pid=valid.pid,
            process_group=valid.pid,
            owner_uid=os.getuid(),
        ),
    )
    group_signals: list[tuple[int, signal.Signals]] = []
    monkeypatch.setattr(
        shard_processes,
        "_require_reserved_process_group",
        lambda _process, _proof: None,
    )
    monkeypatch.setattr(
        shard_processes,
        "_signal_process_group",
        lambda process_group, sig: group_signals.append((process_group, sig)),
    )
    monkeypatch.setattr(
        shard_processes,
        "_owned_live_process_group_members",
        lambda _process_group: (),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="one or more child process cleanups",
    ):
        shard_processes.stop_processes(  # type: ignore[arg-type]
            (invalid, valid),
            0.0,
        )

    assert invalid.terminated is True
    assert invalid.waited is True
    assert valid.waited is True
    assert (valid.pid, signal.SIGTERM) in group_signals


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_stop_processes_continues_after_first_group_signal_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        def __init__(self, pid: int) -> None:
            self.pid = pid
            self.returncode: int | None = None
            self.killed = False
            self.waited = False
            setattr(
                self,
                shard_processes._OWNED_PROCESS_GROUP_ATTRIBUTE,
                shard_processes.OwnedProcessGroup(
                    leader_pid=pid,
                    process_group=pid,
                    owner_uid=os.getuid(),
                ),
            )

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.returncode = -signal.SIGTERM

        def kill(self) -> None:
            self.killed = True
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            self.waited = True
            if self.returncode is None:
                self.returncode = -signal.SIGTERM
            return self.returncode

    first = FakeProcess(31337)
    second = FakeProcess(31338)
    group_signals: list[tuple[int, signal.Signals]] = []
    monkeypatch.setattr(
        shard_processes,
        "_require_reserved_process_group",
        lambda _process, _proof: None,
    )

    def signal_group(process_group: int, sig: signal.Signals) -> None:
        if process_group == first.pid:
            raise shard_processes.ProcessCleanupError(
                "child process-group signaling failed"
            )
        group_signals.append((process_group, sig))

    monkeypatch.setattr(shard_processes, "_signal_process_group", signal_group)
    monkeypatch.setattr(
        shard_processes,
        "_owned_live_process_group_members",
        lambda _process_group: (),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="one or more child process cleanups",
    ):
        shard_processes.stop_processes(  # type: ignore[arg-type]
            (first, second),
            0.0,
        )

    assert first.killed is False
    assert first.waited is True
    assert second.waited is True
    assert (second.pid, signal.SIGTERM) in group_signals


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_reaped_leader_cannot_signal_reused_same_owner_process_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReapedProcess:
        pid = 31337
        returncode = 0

        def poll(self) -> int:
            return self.returncode

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return self.returncode

    process = ReapedProcess()
    proof = shard_processes.OwnedProcessGroup(
        leader_pid=process.pid,
        process_group=process.pid,
        owner_uid=os.getuid(),
    )
    setattr(process, shard_processes._OWNED_PROCESS_GROUP_ATTRIBUTE, proof)
    group_signals: list[tuple[int, signal.Signals]] = []
    monkeypatch.setattr(
        shard_processes.os,
        "killpg",
        lambda process_group, sig: group_signals.append((process_group, sig)),
    )
    monkeypatch.setattr(
        shard_processes,
        "_owned_live_process_group_members",
        lambda _process_group: (31338,),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="could not be proven",
    ):
        shard_processes.stop_processes((process,), 0.0)  # type: ignore[arg-type]

    assert group_signals == []


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_capture_accepts_unreaped_zombie_leader_without_releasing_pgid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnreapedProcess:
        pid = 31337
        returncode = None

    process = UnreapedProcess()
    monkeypatch.setattr(
        shard_processes.os,
        "getpgid",
        lambda _pid: (_ for _ in ()).throw(ProcessLookupError()),
    )
    monkeypatch.setattr(
        shard_processes,
        "_process_group_members",
        lambda _process_group: ((31337, os.getuid(), "Z"),),
    )

    proof = shard_processes.capture_owned_process_group(process)  # type: ignore[arg-type]

    assert proof == shard_processes.OwnedProcessGroup(
        leader_pid=31337,
        process_group=31337,
        owner_uid=os.getuid(),
    )
    assert shard_processes._registered_process_group(process) == proof  # type: ignore[arg-type]


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
            self.returncode: int | None = None

        def poll(self) -> int:
            nonlocal active
            if not self._settled:
                active -= 1
                self._settled = True
                self.returncode = 0
            return 0

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            assert self.returncode is not None
            return self.returncode

    monkeypatch.setattr(runner.subprocess, "Popen", ImmediateProcess)
    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda argv, **kwargs: runner.subprocess.Popen(argv, **kwargs),
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "process_group_leader_is_terminal_without_reaping",
        lambda process: process.poll() is not None,
    )
    plans = [
        runner.ShardPlan(index, (f"tests/test_{index}.py",), 1.0) for index in range(5)
    ]

    results = runner.run_shards(
        plans,
        root=tmp_path,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
        write_timings=False,
        quiet=True,
        max_workers=2,
    )

    assert max_active == 2
    assert [result.index for result in results] == list(range(5))
    assert runner.overall_return_code(results) == 0


def test_run_shards_isolates_home_and_temp_per_shard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environments: list[dict[str, str]] = []

    class ImmediateProcess:
        def __init__(self, *_args: Any, **kwargs: Any) -> None:
            environments.append(kwargs["env"])
            self.returncode: int | None = None

        def poll(self) -> int:
            self.returncode = 0
            return 0

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            assert self.returncode is not None
            return self.returncode

    monkeypatch.setattr(runner.subprocess, "Popen", ImmediateProcess)
    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda argv, **kwargs: runner.subprocess.Popen(argv, **kwargs),
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "process_group_leader_is_terminal_without_reaping",
        lambda process: process.poll() is not None,
    )

    results = runner.run_shards(
        [
            runner.ShardPlan(0, ("tests/test_first.py",), 1.0),
            runner.ShardPlan(1, ("tests/test_second.py",), 1.0),
        ],
        root=tmp_path,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
        write_timings=False,
        quiet=True,
        max_workers=2,
    )

    assert runner.overall_return_code(results) == 0
    assert len(environments) == 2
    for index, environment in enumerate(environments):
        runtime_root = tmp_path / "shards"
        home = Path(environment["HOME"])
        temp = Path(environment["TMPDIR"])
        assert home.is_relative_to(runtime_root)
        assert temp.is_relative_to(runtime_root)
        assert home.name == "home"
        assert temp.name == "tmp"
        assert f"runtime-{index}" in home.parts
        assert environment["TEMP"] == str(temp)
        assert environment["TMP"] == str(temp)
        assert home.is_dir()
        assert temp.is_dir()
    assert environments[0]["HOME"] != environments[1]["HOME"]
    assert environments[0]["TMPDIR"] != environments[1]["TMPDIR"]


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
    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda argv, **kwargs: runner.subprocess.Popen(argv, **kwargs),
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "process_group_leader_is_terminal_without_reaping",
        lambda process: process.poll() is not None,
    )

    results = runner.run_shards(
        [runner.ShardPlan(0, ("tests/test_hangs.py",), 1.0)],
        root=tmp_path,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
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
    shard_processes.capture_owned_process_group(process)
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
        if process.stdout is not None:
            process.stdout.close()
        if not log_handle.closed:
            log_handle.close()


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_successful_shard_reaps_residual_descendant_before_return(
    tmp_path: Path,
) -> None:
    child_pid_path = tmp_path / "successful-shard-child.pid"
    test_path = tmp_path / "test_spawns_residual_child.py"
    test_path.write_text(
        "\n".join(
            (
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "def test_spawn_residual_child():",
                "    child = subprocess.Popen(",
                "        [sys.executable, '-c', 'import time;time.sleep(60)'],",
                "        stdin=subprocess.DEVNULL,",
                "        stdout=subprocess.DEVNULL,",
                "        stderr=subprocess.DEVNULL,",
                "    )",
                f"    Path({str(child_pid_path)!r}).write_text(",
                "        str(child.pid), encoding='ascii'",
                "    )",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    results = runner.run_shards(
        [runner.ShardPlan(0, (str(test_path),), 1.0)],
        root=ROOT,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
        write_timings=False,
        quiet=True,
        termination_grace_seconds=0.2,
    )

    assert [result.returncode for result in results] == [0]
    child_pid = int(child_pid_path.read_text(encoding="ascii"))
    deadline = time.monotonic() + 3
    try:
        while True:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                pytest.fail("successful shard residual descendant survived")
            time.sleep(0.02)
    finally:
        try:
            os.kill(child_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


@pytest.mark.skipif(os.name != "posix", reason="signal cleanup proof is POSIX-only")
@pytest.mark.parametrize(
    "termination_signal",
    POSIX_CANCELLATION_SIGNALS,
)
def test_external_signal_reaps_active_shard_process_group(
    tmp_path: Path,
    termination_signal: signal.Signals,
) -> None:
    pid_path = tmp_path / "active-shard.pid"
    test_path = tmp_path / "test_waits_for_cancellation.py"
    test_path.write_text(
        "\n".join(
            (
                "import os",
                "import signal",
                "import time",
                "from pathlib import Path",
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
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
            "    failure_ref_dir=None,",
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
                pytest.fail(
                    "shard runner exited before the cancellation fixture started"
                )
            time.sleep(0.02)
        assert child_pid is not None

        process.send_signal(termination_signal)
        time.sleep(0.05)
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
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
        if process.stdout is not None:
            process.stdout.close()
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.skipif(os.name != "posix", reason="signal launch guard is POSIX-only")
def test_signal_during_spawn_registration_reaps_the_new_shard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched: list[Any] = []

    class SignalledProcess:
        pid = None

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self.returncode: int | None = None
            self.terminated = False
            launched.append(self)
            os.kill(os.getpid(), signal.SIGTERM)

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = -signal.SIGTERM

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            assert self.returncode is not None
            return self.returncode

    monkeypatch.setattr(runner.subprocess, "Popen", SignalledProcess)
    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda argv, **kwargs: runner.subprocess.Popen(argv, **kwargs),
    )

    with pytest.raises(runner.ShardRunInterrupted):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_launch_guard.py",), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            termination_grace_seconds=0.0,
        )

    assert len(launched) == 1
    assert launched[0].terminated is True


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-only")
def test_shard_launch_preserves_spawn_cleanup_failure_over_pending_signal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_spawn(*_args: object, **_kwargs: object) -> None:
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)
        raise shard_processes.ProcessCleanupError("cleanup-unproven")

    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        fail_spawn,
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="cleanup-unproven",
    ):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_launch_cleanup_priority.py",), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            termination_grace_seconds=0.0,
        )


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-only")
def test_signal_during_normal_shard_settlement_is_deferred_until_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = tmp_path / "test_finishes.py"
    test_path.write_text("def test_finishes():\n    assert True\n", encoding="utf-8")
    launched: list[subprocess.Popen[Any]] = []
    real_spawn = runner.shard_processes.spawn_owned_process_group
    real_stop = runner.shard_processes.stop_processes
    signal_injected = False

    def record_spawn(*args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        process = real_spawn(*args, **kwargs)
        launched.append(process)
        return process

    def signal_then_stop(processes: object, grace_seconds: float) -> None:
        nonlocal signal_injected
        active = tuple(processes)  # type: ignore[arg-type]
        if not signal_injected:
            signal_injected = True
            os.kill(os.getpid(), signal.SIGTERM)
        real_stop(active, grace_seconds)

    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        record_spawn,
    )
    monkeypatch.setattr(runner.shard_processes, "stop_processes", signal_then_stop)

    with pytest.raises(runner.ShardRunInterrupted):
        runner.run_shards(
            [runner.ShardPlan(0, (str(test_path),), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            termination_grace_seconds=0.1,
        )

    assert signal_injected is True
    assert len(launched) == 1
    assert isinstance(launched[0].returncode, int)


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-only")
def test_signal_during_hard_timeout_settlement_is_deferred_until_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = tmp_path / "test_hangs.py"
    test_path.write_text(
        "import time\ndef test_hangs():\n    time.sleep(60)\n",
        encoding="utf-8",
    )
    launched: list[subprocess.Popen[Any]] = []
    real_spawn = runner.shard_processes.spawn_owned_process_group
    real_stop = runner.shard_processes.stop_processes
    signal_injected = False

    def record_spawn(*args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        process = real_spawn(*args, **kwargs)
        launched.append(process)
        return process

    def signal_then_stop(processes: object, grace_seconds: float) -> None:
        nonlocal signal_injected
        active = tuple(processes)  # type: ignore[arg-type]
        if not signal_injected:
            signal_injected = True
            os.kill(os.getpid(), signal.SIGTERM)
        real_stop(active, grace_seconds)

    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        record_spawn,
    )
    monkeypatch.setattr(runner.shard_processes, "stop_processes", signal_then_stop)

    with pytest.raises(runner.ShardRunInterrupted):
        runner.run_shards(
            [runner.ShardPlan(0, (str(test_path),), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            stretch_goal_seconds=0.05,
            target_seconds=0.1,
            hard_timeout_seconds=0.2,
            termination_grace_seconds=0.1,
        )

    assert signal_injected is True
    assert len(launched) == 1
    assert isinstance(launched[0].returncode, int)


def test_normal_cleanup_failure_retains_active_process_for_outer_settlement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[Any] = []
    cleanup_calls: list[tuple[Any, ...]] = []

    class TerminalProcess:
        pid = None

        def __init__(self) -> None:
            self.returncode = 0
            launched.append(self)

    monkeypatch.setattr(
        runner.shard_processes,
        "spawn_owned_process_group",
        lambda *_args, **_kwargs: TerminalProcess(),
    )
    monkeypatch.setattr(
        runner.shard_processes,
        "process_group_leader_is_terminal_without_reaping",
        lambda _process: True,
    )

    def fail_cleanup(processes: object, _grace_seconds: float) -> None:
        active = tuple(processes)  # type: ignore[arg-type]
        cleanup_calls.append(active)
        raise shard_processes.ProcessCleanupError("cleanup-unproven")

    monkeypatch.setattr(runner.shard_processes, "stop_processes", fail_cleanup)

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="cleanup-unproven",
    ):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_terminal.py",), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
        )

    assert len(launched) == 1
    assert cleanup_calls == [(launched[0],), (launched[0],)]


def test_capture_failure_settles_spawned_process_and_closes_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[Any] = []

    class UnregisteredProcess:
        pid = None

        def __init__(self, *_args: Any, **kwargs: Any) -> None:
            self.returncode: int | None = None
            self.terminated = False
            self.waited = False
            self.log_handle = kwargs["stdout"]
            launched.append(self)

        def poll(self) -> int | None:
            return self.returncode

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = -signal.SIGTERM

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            self.waited = True
            assert self.returncode is not None
            return self.returncode

    monkeypatch.setattr(runner.subprocess, "Popen", UnregisteredProcess)
    monkeypatch.setattr(
        shard_processes,
        "capture_owned_process_group",
        lambda _process: (_ for _ in ()).throw(
            shard_processes.ProcessCleanupError(
                "child process-group reservation could not be proven"
            )
        ),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="reservation could not be proven",
    ):
        runner.run_shards(
            [runner.ShardPlan(0, ("tests/test_capture_failure.py",), 1.0)],
            root=tmp_path,
            basetemp=tmp_path / "shards",
            failure_ref_dir=None,
            write_timings=False,
            quiet=True,
            termination_grace_seconds=0.0,
        )

    assert len(launched) == 1
    assert launched[0].terminated is True
    assert launched[0].waited is True
    assert launched[0].log_handle.closed is True


@pytest.mark.skipif(os.name != "posix", reason="spawn gate proof is POSIX-only")
def test_spawn_gate_capture_failure_never_executes_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / "target-executed"
    launched: list[subprocess.Popen[Any]] = []
    real_popen = shard_processes.subprocess.Popen

    def record_popen(*args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        process = real_popen(*args, **kwargs)
        argv = tuple(args[0])
        if len(argv) > 2 and argv[2] == shard_processes._SPAWN_GATE_SCRIPT:
            launched.append(process)
        return process

    monkeypatch.setattr(shard_processes.subprocess, "Popen", record_popen)
    monkeypatch.setattr(
        shard_processes,
        "capture_owned_process_group",
        lambda _process: (_ for _ in ()).throw(
            shard_processes.ProcessCleanupError(
                "child process-group reservation could not be proven"
            )
        ),
    )

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="reservation could not be proven",
    ):
        shard_processes.spawn_owned_process_group(
            (
                sys.executable,
                "-c",
                (
                    "import pathlib,sys;"
                    "pathlib.Path(sys.argv[1]).write_text('executed',encoding='ascii')"
                ),
                str(marker),
            ),
            cwd=tmp_path,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    assert len(launched) == 1
    assert launched[0].poll() is not None
    assert marker.exists() is False


@pytest.mark.skipif(os.name != "posix", reason="signal mask proof is POSIX-only")
def test_shard_process_does_not_inherit_blocked_cancellation_signals(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "test_signal_mask.py"
    test_path.write_text(
        "\n".join(
            (
                "import signal",
                "def test_cancellation_signals_unblocked():",
                "    blocked = signal.pthread_sigmask(signal.SIG_BLOCK, [])",
                "    cancellation = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}",
                "    assert blocked.isdisjoint(cancellation)",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    results = runner.run_shards(
        [runner.ShardPlan(0, (str(test_path),), 1.0)],
        root=tmp_path,
        basetemp=tmp_path / "shards",
        failure_ref_dir=None,
        write_timings=False,
        quiet=True,
    )

    assert [result.returncode for result in results] == [0]


def test_overall_return_code_fails_if_any_shard_failed(tmp_path: Path) -> None:
    passed = runner.ShardResult(0, 1, 0, 1.0, tmp_path / "a.log")
    failed = runner.ShardResult(1, 1, 2, 1.0, tmp_path / "b.log")

    assert runner.overall_return_code([passed]) == 0
    assert runner.overall_return_code([passed, failed]) == 1


def test_zero_duration_files_share_only_unattributed_shard_residual(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "shard.log"
    log_path.write_text(
        "2.00s call tests/test_a.py::test_a\n"
        "0.00s call tests/test_b.py::test_b\n"
        "0.00s call tests/test_c.py::test_c\n",
        encoding="utf-8",
    )
    plan = runner.ShardPlan(
        0,
        ("tests/test_a.py", "tests/test_b.py", "tests/test_c.py"),
        4.0,
    )
    result = runner.ShardResult(0, 3, 0, 4.0, log_path)

    entries = runner.collect_file_timings(
        [plan],
        [result],
        set(plan.files),
    )

    by_path = {entry["path"]: entry for entry in entries}
    assert by_path["tests/test_a.py"]["seconds"] == 2.0
    assert by_path["tests/test_b.py"]["seconds"] == 1.0
    assert by_path["tests/test_c.py"]["seconds"] == 1.0
    assert by_path["tests/test_b.py"]["source"] == "shard-elapsed-fallback"


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
