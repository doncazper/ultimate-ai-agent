from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType


SignalHandler = Callable[[int, FrameType | None], None]


def cancellation_signals() -> tuple[signal.Signals, ...]:
    return tuple(
        candidate
        for candidate in (
            signal.SIGTERM,
            signal.SIGINT,
            getattr(signal, "SIGHUP", None),
        )
        if candidate is not None
    )


def isolated_shard_environment(
    base_env: dict[str, str], runtime_dir: Path
) -> dict[str, str]:
    home = runtime_dir / "home"
    temp = runtime_dir / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)
    env = dict(base_env)
    env.update(
        {"HOME": str(home), "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    )
    return env


@contextmanager
def installed_signal_handlers(
    signals: tuple[signal.Signals, ...], handler: SignalHandler
) -> Iterator[None]:
    previous_handlers = {
        candidate: signal.getsignal(candidate) for candidate in signals
    }
    for candidate in signals:
        signal.signal(candidate, handler)
    try:
        yield
    finally:
        for candidate, previous_handler in previous_handlers.items():
            signal.signal(candidate, previous_handler)


def ignore_signals(signals: tuple[signal.Signals, ...]) -> None:
    for candidate in signals:
        signal.signal(candidate, signal.SIG_IGN)


def stop_processes(
    processes: Iterable[subprocess.Popen[str]], termination_grace_seconds: float
) -> None:
    active = tuple(processes)
    process_groups = {
        process.pid
        for process in active
        if os.name == "posix" and isinstance(getattr(process, "pid", None), int)
    }
    for process in active:
        _signal_process(process, signal.SIGTERM)
    grace_deadline = time.perf_counter() + termination_grace_seconds
    while time.perf_counter() < grace_deadline:
        if all(process.poll() is not None for process in active):
            break
        time.sleep(0.05)
    if os.name == "posix":
        for process_group in process_groups:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
    else:
        for process in active:
            if process.poll() is None:
                _signal_process(process, signal.SIGKILL)
    wait_deadline = time.perf_counter() + max(termination_grace_seconds, 0.1)
    for process in active:
        try:
            process.wait(timeout=max(wait_deadline - time.perf_counter(), 0.01))
        except subprocess.TimeoutExpired:
            pass


def _signal_process(process: subprocess.Popen[str], sig: signal.Signals) -> None:
    if os.name == "posix" and isinstance(getattr(process, "pid", None), int):
        try:
            os.killpg(process.pid, sig)
            return
        except ProcessLookupError:
            return
    action = process.terminate if sig == signal.SIGTERM else process.kill
    try:
        action()
    except ProcessLookupError:
        pass
