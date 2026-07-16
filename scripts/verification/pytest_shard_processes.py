from __future__ import annotations

import math
import os
import select
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import FrameType
from typing import Any


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
PROCESS_GROUP_INSPECTION_TIMEOUT_SECONDS = 2.0
MAX_PROCESS_GROUP_INSPECTION_BYTES = 1024 * 1024
MIN_PROCESS_SETTLEMENT_SECONDS = 1.0
PROCESS_SETTLEMENT_POLL_SECONDS = 0.05
_OWNED_PROCESS_GROUP_ATTRIBUTE = "_uaa_owned_process_group"
_SPAWN_GATE_SCRIPT = (
    "import os,sys;"
    "fd=int(sys.argv[1]);"
    "token=os.read(fd,1);"
    "os.close(fd);"
    "target=sys.argv[2:];"
    "raise_on_invalid=(token!=b'1' or not target);"
    "raise_on_invalid and sys.exit(126);"
    "os.execvp(target[0],target)"
)


class ProcessCleanupError(RuntimeError):
    """Raised when bounded child-process settlement cannot be proven."""


@dataclass(frozen=True)
class OwnedProcessGroup:
    """Spawn-time proof that an unreaped child reserved an isolated group."""

    leader_pid: int
    process_group: int
    owner_uid: int
    exit_monitor: _ProcessExitMonitor | None = field(
        default=None,
        compare=False,
        repr=False,
    )


class _ProcessExitMonitor:
    """Observe macOS process exit without reaping the owned leader."""

    def __init__(self, process_id: int) -> None:
        self._terminal = False
        self._queue: select.kqueue | None = None
        if not all(
            hasattr(select, name)
            for name in (
                "kqueue",
                "kevent",
                "KQ_FILTER_PROC",
                "KQ_NOTE_EXIT",
                "KQ_EV_ADD",
                "KQ_EV_ENABLE",
            )
        ):
            return
        try:
            queue = select.kqueue()
        except OSError:
            return
        try:
            queue.control(
                (
                    select.kevent(
                        process_id,
                        filter=select.KQ_FILTER_PROC,
                        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE,
                        fflags=select.KQ_NOTE_EXIT,
                    ),
                ),
                0,
                0,
            )
        except OSError:
            queue.close()
            return
        self._queue = queue

    def terminal(self) -> bool | None:
        if self._terminal:
            return True
        if self._queue is None:
            return None
        try:
            events = self._queue.control((), 1, 0)
        except OSError as exc:
            raise ProcessCleanupError("child process exit monitoring failed") from exc
        self._terminal = bool(events)
        return self._terminal

    def close(self) -> None:
        if self._queue is not None:
            self._queue.close()
            self._queue = None

    def __del__(self) -> None:
        try:
            self.close()
        except OSError:
            # Explicit settlement reports close failures. Destruction is only a
            # final best-effort guard and must not emit an unraisable warning.
            pass


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
    if os.name != "posix" or not signals or not hasattr(signal, "pthread_sigmask"):
        installed: list[signal.Signals] = []
        try:
            for candidate in signals:
                signal.signal(candidate, handler)
                installed.append(candidate)
            yield
        finally:
            first_error: BaseException | None = None
            for candidate in reversed(installed):
                try:
                    signal.signal(candidate, previous_handlers[candidate])
                except BaseException as exc:
                    first_error = first_error or exc
            if first_error is not None:
                raise first_error
        return

    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
    installed: list[signal.Signals] = []
    mask_restored = False
    try:
        for candidate in signals:
            signal.signal(candidate, handler)
            installed.append(candidate)
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        mask_restored = True
        try:
            yield
        finally:
            restore_mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
            first_error: BaseException | None = None
            try:
                for candidate in reversed(installed):
                    try:
                        signal.signal(candidate, previous_handlers[candidate])
                    except BaseException as exc:
                        first_error = first_error or exc
                installed.clear()
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, restore_mask)
            if first_error is not None:
                raise first_error
    except BaseException:
        if installed:
            transition_mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
            first_error: BaseException | None = None
            try:
                for candidate in reversed(installed):
                    try:
                        signal.signal(candidate, previous_handlers[candidate])
                    except BaseException as exc:
                        first_error = first_error or exc
                installed.clear()
            finally:
                signal.pthread_sigmask(
                    signal.SIG_SETMASK,
                    previous_mask if not mask_restored else transition_mask,
                )
            if first_error is not None:
                raise first_error
        elif not mask_restored:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        raise


def ignore_signals(signals: tuple[signal.Signals, ...]) -> None:
    for candidate in signals:
        signal.signal(candidate, signal.SIG_IGN)


def capture_owned_process_group(
    process: subprocess.Popen[str] | subprocess.Popen[bytes],
) -> OwnedProcessGroup | None:
    """Bind an isolated child group before any wait/poll can reap its leader."""

    if os.name != "posix":
        return None
    pid = getattr(process, "pid", None)
    if not isinstance(pid, int) or pid <= 0:
        return None
    if getattr(process, "returncode", None) is not None:
        raise ProcessCleanupError("child process-group reservation expired")
    try:
        process_group = os.getpgid(pid)
    except ProcessLookupError:
        members = _process_group_members(pid)
        if (pid, os.getuid()) not in {
            (member_pid, uid)
            for member_pid, uid, state in members
            if state.startswith("Z")
        }:
            raise ProcessCleanupError(
                "child process-group reservation could not be proven"
            )
        process_group = pid
    except (PermissionError, OSError) as exc:
        raise ProcessCleanupError(
            "child process-group reservation could not be proven"
        ) from exc
    if process_group != pid:
        raise ProcessCleanupError("child process-group isolation could not be proven")
    proof = OwnedProcessGroup(
        leader_pid=pid,
        process_group=process_group,
        owner_uid=os.getuid(),
        exit_monitor=_ProcessExitMonitor(pid),
    )
    setattr(process, _OWNED_PROCESS_GROUP_ATTRIBUTE, proof)
    return proof


def spawn_owned_process_group(
    argv: tuple[str, ...] | list[str],
    **popen_kwargs: Any,
) -> subprocess.Popen[Any]:
    """Spawn behind a pipe gate and release target exec only after PGID proof."""

    if os.name != "posix":
        return subprocess.Popen(argv, **popen_kwargs)
    if "pass_fds" in popen_kwargs:
        raise ValueError("owned process-group spawn does not accept pass_fds")
    read_fd, write_fd = os.pipe()
    process: subprocess.Popen[Any] | None = None
    write_open = True
    try:
        gate_argv = (
            sys.executable,
            "-c",
            _SPAWN_GATE_SCRIPT,
            str(read_fd),
            *argv,
        )
        popen_kwargs["start_new_session"] = True
        popen_kwargs["pass_fds"] = (read_fd,)
        process = subprocess.Popen(gate_argv, **popen_kwargs)
        os.close(read_fd)
        read_fd = -1
        capture_owned_process_group(process)
        os.write(write_fd, b"1")
        os.close(write_fd)
        write_open = False
        return process
    except BaseException:
        if write_open:
            os.close(write_fd)
            write_open = False
        if process is not None:
            try:
                stop_processes((process,), 0.25)
            except Exception as cleanup_exc:
                raise ProcessCleanupError(
                    "spawn-gate child cleanup could not be proven"
                ) from cleanup_exc
        raise
    finally:
        if read_fd >= 0:
            os.close(read_fd)
        if write_open:
            os.close(write_fd)


def stop_processes(
    processes: Iterable[subprocess.Popen[str]], termination_grace_seconds: float
) -> None:
    active = tuple(processes)
    if not active:
        return
    if not math.isfinite(termination_grace_seconds) or termination_grace_seconds < 0:
        raise ValueError("termination grace must be finite and non-negative")
    cleanup_errors: list[Exception] = []
    registered: list[tuple[subprocess.Popen[str], OwnedProcessGroup]] = []
    exact: list[subprocess.Popen[str]] = []
    for process in active:
        try:
            proof = _registered_process_group(process)
        except Exception as exc:
            cleanup_errors.append(exc)
            exact.append(process)
            continue
        if proof is None:
            exact.append(process)
        else:
            registered.append((process, proof))
    group_processes = list(registered)
    exact_processes = list(exact)

    def record_group_failure(
        _process: subprocess.Popen[str],
        exc: Exception,
    ) -> None:
        cleanup_errors.append(exc)

    try:
        eligible_groups: list[tuple[subprocess.Popen[str], OwnedProcessGroup]] = []
        if os.name == "posix":
            for process, proof in group_processes:
                try:
                    _require_reserved_process_group(process, proof)
                    _signal_process_group(proof.process_group, signal.SIGTERM)
                except Exception as exc:
                    record_group_failure(process, exc)
                else:
                    eligible_groups.append((process, proof))
        eligible_exact: list[subprocess.Popen[str]] = []
        for process in exact_processes:
            try:
                if process.poll() is None:
                    _signal_process(process, signal.SIGTERM)
            except Exception as exc:
                cleanup_errors.append(exc)
            else:
                eligible_exact.append(process)

        grace_deadline = time.monotonic() + termination_grace_seconds
        while time.monotonic() < grace_deadline:
            groups_pending = False
            still_eligible_groups: list[
                tuple[subprocess.Popen[str], OwnedProcessGroup]
            ] = []
            for process, proof in eligible_groups:
                try:
                    is_live = bool(
                        _owned_live_process_group_members(proof.process_group)
                    )
                except Exception as exc:
                    record_group_failure(process, exc)
                else:
                    groups_pending = groups_pending or is_live
                    still_eligible_groups.append((process, proof))
            eligible_groups = still_eligible_groups
            exact_pending = False
            still_eligible_exact: list[subprocess.Popen[str]] = []
            for process in eligible_exact:
                try:
                    is_live = process.poll() is None
                except Exception as exc:
                    cleanup_errors.append(exc)
                else:
                    exact_pending = exact_pending or is_live
                    still_eligible_exact.append(process)
            eligible_exact = still_eligible_exact
            if not groups_pending and not exact_pending:
                break
            time.sleep(PROCESS_SETTLEMENT_POLL_SECONDS)

        still_eligible_groups = []
        for process, proof in eligible_groups:
            try:
                if _owned_live_process_group_members(proof.process_group):
                    _require_reserved_process_group(process, proof)
                    _signal_process_group(proof.process_group, signal.SIGKILL)
            except Exception as exc:
                record_group_failure(process, exc)
            else:
                still_eligible_groups.append((process, proof))
        eligible_groups = still_eligible_groups
        for process in eligible_exact:
            try:
                if process.poll() is None:
                    _signal_process(process, signal.SIGKILL)
            except Exception as exc:
                cleanup_errors.append(exc)

        wait_deadline = time.monotonic() + max(
            termination_grace_seconds,
            MIN_PROCESS_SETTLEMENT_SECONDS,
        )
        settled_group_processes: set[int] = set()
        # Revisit every registered group, including one whose earlier TERM or
        # inspection attempt failed. A transient failure for one group must not
        # prevent a bounded KILL/settlement attempt for it or any sibling group.
        for process, proof in group_processes:
            while True:
                try:
                    live_members = _owned_live_process_group_members(
                        proof.process_group
                    )
                    if not live_members:
                        settled_group_processes.add(id(process))
                        break
                    if time.monotonic() >= wait_deadline:
                        raise ProcessCleanupError(
                            "child process-group cleanup could not be proven"
                        )
                    _require_reserved_process_group(process, proof)
                    _signal_process_group(proof.process_group, signal.SIGKILL)
                except Exception as exc:
                    record_group_failure(process, exc)
                    break
                time.sleep(PROCESS_SETTLEMENT_POLL_SECONDS)
        registered_by_process = {id(process) for process, _proof in group_processes}
        for process in active:
            if (
                id(process) in registered_by_process
                and id(process) not in settled_group_processes
            ):
                # Do not reap the leader while descendants remain live or their
                # posture is indeterminate: the unreaped leader is the
                # reservation preventing an unrelated process from reusing
                # this PGID.
                continue
            try:
                process.wait(timeout=max(wait_deadline - time.monotonic(), 0.01))
            except (subprocess.TimeoutExpired, OSError):
                cleanup_errors.append(
                    ProcessCleanupError("child process cleanup could not be proven")
                )
    finally:
        for _process, proof in group_processes:
            if proof.exit_monitor is not None:
                try:
                    proof.exit_monitor.close()
                except OSError:
                    cleanup_errors.append(
                        ProcessCleanupError("child process exit monitor cleanup failed")
                    )
    if cleanup_errors:
        raise ProcessCleanupError(
            "one or more child process cleanups could not be proven"
        ) from cleanup_errors[0]


def _registered_process_group(
    process: subprocess.Popen[str] | subprocess.Popen[bytes],
) -> OwnedProcessGroup | None:
    proof = getattr(process, _OWNED_PROCESS_GROUP_ATTRIBUTE, None)
    if proof is None:
        return None
    if not isinstance(proof, OwnedProcessGroup):
        raise ProcessCleanupError("child process-group proof is invalid")
    pid = getattr(process, "pid", None)
    if (
        proof.leader_pid != pid
        or proof.process_group != proof.leader_pid
        or proof.owner_uid != os.getuid()
    ):
        raise ProcessCleanupError("child process-group proof is invalid")
    return proof


def _require_reserved_process_group(
    process: subprocess.Popen[str],
    proof: OwnedProcessGroup,
) -> None:
    """Prove the original unreaped leader still prevents PGID reuse."""

    if getattr(process, "returncode", None) is not None:
        raise ProcessCleanupError("child process-group reservation expired")
    try:
        current_group = os.getpgid(proof.leader_pid)
    except ProcessLookupError:
        members = _process_group_members(proof.process_group)
        if (
            proof.leader_pid,
            proof.owner_uid,
        ) not in {(pid, uid) for pid, uid, state in members if state.startswith("Z")}:
            raise ProcessCleanupError("child process-group reservation expired")
        return
    except (PermissionError, OSError) as exc:
        raise ProcessCleanupError("child process-group reservation expired") from exc
    if current_group != proof.process_group:
        raise ProcessCleanupError("child process-group reservation expired")


def process_group_leader_is_terminal_without_reaping(
    process: subprocess.Popen[str] | subprocess.Popen[bytes],
) -> bool:
    """Observe an owned leader's zombie posture without releasing its PGID."""

    proof = _registered_process_group(process)
    if proof is None:
        raise ProcessCleanupError("child process-group proof is missing")
    if getattr(process, "returncode", None) is not None:
        raise ProcessCleanupError("child process-group reservation expired")
    if proof.exit_monitor is not None:
        terminal = proof.exit_monitor.terminal()
        if terminal is not None:
            return terminal
    members = _process_group_members(proof.process_group)
    leader_states = tuple(
        state
        for pid, uid, state in members
        if pid == proof.leader_pid and uid == proof.owner_uid
    )
    if len(leader_states) != 1:
        raise ProcessCleanupError(
            "child process-group leader posture could not be proven"
        )
    return leader_states[0].startswith("Z")


def _owned_live_process_group_members(process_group: int) -> tuple[int, ...]:
    """Return live same-owner group members without reading command content."""

    members = _process_group_members(process_group)
    live_members: list[int] = []
    for pid, uid, state in members:
        if state.startswith("Z"):
            continue
        if uid != os.getuid() or pid <= 0:
            raise ProcessCleanupError(
                "child process-group ownership could not be proven"
            )
        live_members.append(pid)
    return tuple(sorted(set(live_members)))


def _process_group_members(process_group: int) -> tuple[tuple[int, int, str], ...]:
    """Read only PID, PGID, UID, and state for one process group."""

    if os.name != "posix" or process_group <= 0:
        return ()
    try:
        completed = subprocess.run(
            ("/bin/ps", "-axo", "pid=,pgid=,uid=,state="),
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=PROCESS_GROUP_INSPECTION_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProcessCleanupError("child process-group inspection failed") from exc
    if (
        completed.returncode != 0
        or len(completed.stdout) > MAX_PROCESS_GROUP_INSPECTION_BYTES
    ):
        raise ProcessCleanupError("child process-group inspection failed")
    try:
        lines = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        raise ProcessCleanupError("child process-group inspection failed") from exc
    members: list[tuple[int, int, str]] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            raise ProcessCleanupError("child process-group inspection failed")
        try:
            pid, pgid, uid = (int(value) for value in parts[:3])
        except ValueError as exc:
            raise ProcessCleanupError("child process-group inspection failed") from exc
        if pgid != process_group:
            continue
        if pid <= 0:
            raise ProcessCleanupError("child process-group inspection failed")
        members.append((pid, uid, parts[3]))
    return tuple(sorted(set(members)))


def _signal_process_group(process_group: int, sig: signal.Signals) -> None:
    try:
        os.killpg(process_group, sig)
        return
    except ProcessLookupError:
        return
    except PermissionError:
        members = _owned_live_process_group_members(process_group)
    except OSError as exc:
        raise ProcessCleanupError("child process-group signaling failed") from exc
    for pid in members:
        try:
            if os.getpgid(pid) != process_group:
                continue
            os.kill(pid, sig)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            raise ProcessCleanupError(
                "child process-group ownership could not be proven"
            ) from exc
        except OSError as exc:
            raise ProcessCleanupError("child process-group signaling failed") from exc


def _signal_process(process: subprocess.Popen[str], sig: signal.Signals) -> None:
    action = process.terminate if sig == signal.SIGTERM else process.kill
    try:
        action()
    except ProcessLookupError:
        pass
    except OSError as exc:
        raise ProcessCleanupError("child process signaling failed") from exc
