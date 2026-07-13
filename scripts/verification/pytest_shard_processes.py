from __future__ import annotations

import math
import os
import signal
import subprocess
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType


SignalHandler = Callable[[int, FrameType | None], None]

LIVE_MODEL_ENV_DENYLIST_PREFIXES = (
    "UAA_M160_LIVE_HF_",
    "UAA_M162_LIVE_HF_",
    "UAA_M164_LLAMA_CPP_",
    "UAA_LLAMA_CPP_",
    "UAA_MODEL_ROUTER_SWEEP",
    "UAA_OPENWEBUI_TEST_",
    "UAA_TINY_LIVE_PROVIDER_",
    "UAA_WEB_HYBRID_LIVE_",
)
LIVE_MODEL_ENV_DENYLIST_EXACT = frozenset(
    {
        "UAA_FIRECRAWL_CLOUD_SECRET_FILE",
        "UAA_LOCAL_MODEL_REF",
        "UAA_LOCAL_MODEL_ROOTS",
    }
)
SHARD_ENV_ALLOWLIST_EXACT = frozenset(
    {
        "HOME",
        "LANG",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "SHELL",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "TZ",
        "VIRTUAL_ENV",
    }
)
SHARD_ENV_ALLOWLIST_PREFIXES = ("LC_",)


def validate_runtime_budget(
    *,
    stretch_goal_seconds: float,
    target_seconds: float,
    hard_timeout_seconds: float,
    termination_grace_seconds: float,
) -> None:
    if not math.isfinite(stretch_goal_seconds) or stretch_goal_seconds <= 0:
        raise ValueError("--stretch-goal-seconds must be finite and greater than zero")
    if not math.isfinite(target_seconds) or target_seconds <= stretch_goal_seconds:
        raise ValueError(
            "--target-seconds must be finite and exceed --stretch-goal-seconds"
        )
    if (
        not math.isfinite(hard_timeout_seconds)
        or hard_timeout_seconds <= target_seconds
    ):
        raise ValueError(
            "--hard-timeout-seconds must be finite and exceed --target-seconds"
        )
    if not math.isfinite(termination_grace_seconds) or termination_grace_seconds < 0:
        raise ValueError("--termination-grace-seconds must be finite and non-negative")


def is_live_model_opt_in_env_var(name: str) -> bool:
    if name in LIVE_MODEL_ENV_DENYLIST_EXACT:
        return True
    return any(name.startswith(prefix) for prefix in LIVE_MODEL_ENV_DENYLIST_PREFIXES)


def build_shard_env(
    root: Path, inherited: dict[str, str] | None = None
) -> dict[str, str]:
    base_env = dict(os.environ if inherited is None else inherited)
    env = {
        name: value
        for name, value in base_env.items()
        if not is_live_model_opt_in_env_var(name)
        and (
            name in SHARD_ENV_ALLOWLIST_EXACT
            or any(name.startswith(prefix) for prefix in SHARD_ENV_ALLOWLIST_PREFIXES)
        )
    }
    src_path = str(root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path
        if not existing_pythonpath
        else f"{src_path}{os.pathsep}{existing_pythonpath}"
    )
    return env


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
