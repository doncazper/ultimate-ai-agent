from __future__ import annotations

import fcntl
import http.client
import json
import os
import re
import secrets
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import weakref
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol, TypeVar

from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
    atomic_start_signal_guard_active,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.time import utc_now
from .constants import (
    MATRIX_HARNESS_FIXTURE_PLAN_REF,
    MATRIX_HARNESS_IMAGE_REF,
    MATRIX_HARNESS_PROJECT_REF,
    MatrixHarnessOperation,
)
from .contracts import (
    MatrixHarnessBackendResult,
    MatrixHarnessLifecycleRecord,
    MatrixHarnessOperationOutcome,
    MatrixHarnessRuntimeStatus,
    matrix_harness_generation_ref,
    matrix_harness_state_ref,
    stable_matrix_harness_ref,
)


MATRIX_HARNESS_PROCESS_TIMEOUT_SECONDS = 120
MATRIX_HARNESS_OUTPUT_LIMIT_BYTES = 64 * 1024
MATRIX_HARNESS_SAFE_DISABLE_ENV = "UAA_MATRIX_HARNESS_SAFE_DISABLE"
MATRIX_HARNESS_PROCESS_GROUP_READY_SECONDS = 1.0
MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS = 1.0
MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS = 5.0
MATRIX_HARNESS_PROCESS_POLL_SECONDS = 0.01
MATRIX_HARNESS_PROCESS_INVENTORY_TIMEOUT_SECONDS = 1.0
MATRIX_HARNESS_PROCESS_INVENTORY_LIMIT_BYTES = 16 * 1024
MATRIX_HARNESS_PROCESS_GROUP_MEMBER_LIMIT = 64
_MATRIX_HARNESS_SPAWN_GATE = """
import os
import signal
import sys
import time

gate_fd = int(sys.argv[1])
liveness_fd = int(sys.argv[2])
token = os.read(gate_fd, 1)
os.close(gate_fd)
if token != b"1":
    os._exit(126)

try:
    watchdog_pid = os.fork()
except OSError:
    os._exit(125)

if watchdog_pid == 0:
    for watched in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(watched, signal.SIG_IGN)
    devnull = os.open(os.devnull, os.O_RDWR)
    for descriptor in (0, 1, 2):
        os.dup2(devnull, descriptor)
    if devnull > 2:
        os.close(devnull)
    while True:
        try:
            if not os.read(liveness_fd, 1):
                break
        except InterruptedError:
            continue
    os.killpg(os.getpgrp(), signal.SIGTERM)
    time.sleep(0.25)
    os.killpg(os.getpgrp(), signal.SIGKILL)
    os._exit(125)

os.close(liveness_fd)
os.execve(sys.argv[3], sys.argv[3:], os.environ)
"""


class MatrixHarnessBackendError(RuntimeError):
    pass


class MatrixHarnessSignalInterrupted(MatrixHarnessBackendError):
    pass


class _MatrixHarnessCleanupError(MatrixHarnessBackendError):
    """A cleanup failure that must not be masked by a second cleanup attempt."""


class _MatrixHarnessSettledRecoveryRequired(
    AuthorityDispatchAtomicStartRecoveryRequired
):
    """Recovery result whose process cleanup and lifecycle settlement ran once."""


class MatrixHarnessReadiness(Protocol):
    def __call__(self, operation: MatrixHarnessOperation) -> list[str]: ...


_ClaimedHandleT = TypeVar("_ClaimedHandleT")


@dataclass(frozen=True)
class _MatrixHarnessResourcePosture:
    container_count: int
    running_container_count: int
    network_count: int
    volume_count: int
    ownership_valid: bool

    @property
    def total_count(self) -> int:
        return self.container_count + self.network_count + self.volume_count


@dataclass(frozen=True)
class _MatrixHarnessProcessGroupInventory:
    leader_terminal: bool
    live_member_count: int
    member_count: int


@dataclass
class _MatrixHarnessSignalGuard:
    deferred: bool = False
    pending_signal: int | None = None
    watched_signals: tuple[signal.Signals, ...] = ()
    previous_handlers: dict[signal.Signals, object] = field(default_factory=dict)
    active: bool = False
    detached: bool = False

    def handle(self, received: int, _frame: object) -> None:
        if self.deferred:
            if self.pending_signal is None:
                self.pending_signal = received
            return
        # Defer every subsequent signal before raising the first interruption.
        # Without this atomic posture change, a second TERM/HUP can arrive while
        # Python is dispatching the first exception and bypass the cleanup path.
        self.deferred = True
        if self.pending_signal is None:
            self.pending_signal = received
        raise MatrixHarnessSignalInterrupted(
            f"MATRIX_HARNESS_SIGNAL_INTERRUPTED_{signal.Signals(received).name}"
        )

    def raise_if_pending(self) -> None:
        if self.pending_signal is None:
            return
        received = self.pending_signal
        self.pending_signal = None
        raise MatrixHarnessSignalInterrupted(
            f"MATRIX_HARNESS_SIGNAL_INTERRUPTED_{signal.Signals(received).name}"
        )

    def activate(
        self,
        watched_signals: tuple[signal.Signals, ...],
        previous_handlers: dict[signal.Signals, object],
    ) -> None:
        self.watched_signals = watched_signals
        self.previous_handlers = previous_handlers
        self.active = True

    def restore(self) -> None:
        if not self.active:
            return
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, self.watched_signals)
        self.deferred = True
        try:
            for watched_signal, handler in self.previous_handlers.items():
                signal.signal(watched_signal, handler)  # type: ignore[arg-type]
            self.active = False
        finally:
            # Never expose a partially restored handler set to a pending
            # process signal.
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

    def detach(self) -> None:
        if not self.active:
            return
        self.detached = True


@dataclass(frozen=True)
class MatrixHarnessBackendConfig:
    repo_root: Path
    docker_binary: Path
    state_dir: Path

    def __post_init__(self) -> None:
        if not self.repo_root.is_absolute() or not self.state_dir.is_absolute():
            raise ValueError("MATRIX_HARNESS_ABSOLUTE_PATHS_REQUIRED")
        if not self.docker_binary.is_absolute():
            raise ValueError("MATRIX_HARNESS_DOCKER_BINARY_ABSOLUTE_REQUIRED")
        if self.repo_root != self.repo_root.resolve():
            raise ValueError("MATRIX_HARNESS_REPO_ROOT_SYMLINKED")
        _require_safe_directory(self.repo_root, "MATRIX_HARNESS_REPO_ROOT_UNSAFE")
        expected_state_dir = self.repo_root / ".uaa" / "messenger-matrix-harness"
        if self.state_dir != expected_state_dir:
            raise ValueError("MATRIX_HARNESS_STATE_DIR_OUT_OF_SCOPE")
        packaging = self.repo_root / "packaging"
        _require_safe_directory(packaging, "MATRIX_HARNESS_PACKAGE_PARENT_UNSAFE")
        if packaging.resolve() != packaging:
            raise ValueError("MATRIX_HARNESS_PACKAGE_PARENT_SYMLINKED")
        package = packaging / "messenger-matrix-harness"
        _require_safe_directory(package, "MATRIX_HARNESS_PACKAGE_UNSAFE")
        if package.resolve() != package:
            raise ValueError("MATRIX_HARNESS_PACKAGE_SYMLINKED")
        for name in ("compose.yaml", "provider_lock.json", "homeserver.yaml.template"):
            _require_safe_regular_file(
                package / name,
                "MATRIX_HARNESS_PACKAGE_FILE_UNSAFE",
            )
        try:
            mode = os.lstat(self.docker_binary).st_mode
        except OSError as exc:
            raise ValueError("MATRIX_HARNESS_DOCKER_BINARY_UNAVAILABLE") from exc
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            raise ValueError("MATRIX_HARNESS_DOCKER_BINARY_UNSAFE")
        state_parent = self.state_dir.parent
        if state_parent.exists():
            _require_safe_directory(
                state_parent,
                "MATRIX_HARNESS_STATE_PARENT_UNSAFE",
            )

    @property
    def package_dir(self) -> Path:
        return self.repo_root / "packaging" / "messenger-matrix-harness"

    @property
    def compose_path(self) -> Path:
        return self.package_dir / "compose.yaml"

    @property
    def lifecycle_path(self) -> Path:
        return self.state_dir.parent / "messenger-matrix-harness-state.json"


class MatrixHarnessExecutionHandle:
    def __init__(
        self,
        *,
        backend: "DockerMatrixHarnessBackend",
        operation: MatrixHarnessOperation,
        execution_ref: str,
        process: subprocess.Popen[bytes],
        commit_validated_at: datetime,
        lifecycle_lock_fd: int | None,
        signal_guard: _MatrixHarnessSignalGuard | None = None,
    ) -> None:
        self._backend = backend
        self._operation = operation
        self._execution_ref = execution_ref
        self._process = process
        self._lifecycle_lock_fd = lifecycle_lock_fd
        self._signal_guard = signal_guard
        self.commit_validated_at = commit_validated_at
        self._collected = False
        self._runtime_settled = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    def _release_owned_resources(self) -> None:
        try:
            self._backend._release_lifecycle_lock(self._lifecycle_lock_fd)
            self._lifecycle_lock_fd = None
        finally:
            if self._signal_guard is not None:
                self._signal_guard.restore()
                self._signal_guard = None

    def _collect_with_signal_guard(
        self,
        signal_guard: _MatrixHarnessSignalGuard,
    ) -> MatrixHarnessBackendResult:
        signal_guard.deferred = False
        try:
            signal_guard.raise_if_pending()
            return self._backend._collect(
                operation=self._operation,
                execution_ref=self._execution_ref,
                process=self._process,
            )
        except (
            _MatrixHarnessSettledRecoveryRequired,
            _MatrixHarnessCleanupError,
        ):
            raise
        except BaseException as original:
            signal_guard.deferred = True
            try:
                self._backend._terminate_and_settle(
                    self._operation,
                    self._execution_ref,
                    self._process,
                )
            except BaseException as cleanup_error:
                raise cleanup_error from original
            raise

    def collect(self) -> MatrixHarnessBackendResult:
        if self._collected:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_HANDLE_ALREADY_COLLECTED")
        self._collected = True
        try:
            if self._signal_guard is not None:
                result = self._collect_with_signal_guard(self._signal_guard)
            else:
                with _forward_termination_signals() as signal_guard:
                    result = self._collect_with_signal_guard(signal_guard)
            self._runtime_settled = True
            self._release_owned_resources()
            return result
        except _MatrixHarnessSettledRecoveryRequired:
            # The backend already persisted the recovery posture and performed
            # its one bounded settlement attempt. Do not retain the lifecycle
            # lock or let dispatcher cleanup invoke the uncertain operation a
            # second time.
            self._runtime_settled = True
            self._settled = True
            self._release_owned_resources()
            raise
        except BaseException:
            try:
                process_terminal = self._process.poll() is not None
            except (AttributeError, OSError):
                process_terminal = False
            if process_terminal:
                self._runtime_settled = True
                self._settled = True
                try:
                    self._release_owned_resources()
                except BaseException as release_error:
                    raise AuthorityDispatchAtomicStartRecoveryRequired(
                        "MATRIX_HARNESS_COLLECT_RESOURCE_RELEASE_UNCERTAIN"
                    ) from release_error
            raise

    def finalize(self) -> None:
        if (
            self._settled
            or self._finalized
            or not self._runtime_settled
            or not self._collected
        ):
            raise MatrixHarnessBackendError("MATRIX_HARNESS_FINALIZATION_INVALID")
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_SETTLEMENT_INVALID")
        self._settled = True

    def abort(self) -> None:
        if self._settled:
            return
        self._collected = True
        if self._signal_guard is not None:
            self._signal_guard.deferred = True
        if self._runtime_settled:
            try:
                self._backend._mark_recovery_required(
                    self._operation,
                    self._execution_ref,
                )
                self._release_owned_resources()
            except BaseException as exc:
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "MATRIX_HARNESS_TERMINAL_RECEIPT_RECOVERY_UNCERTAIN"
                ) from exc
            self._settled = True
            return
        try:
            recovery_required = self._backend._terminate_and_settle(
                self._operation,
                self._execution_ref,
                self._process,
            )
            del recovery_required
        except AuthorityDispatchAtomicStartRecoveryRequired:
            raise
        except BaseException as exc:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_HARNESS_CONFIRMATION_ABORT_RECOVERY_REQUIRED"
            ) from exc
        finally:
            try:
                self._release_owned_resources()
            except BaseException as exc:
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "MATRIX_HARNESS_CONFIRMATION_ABORT_RESOURCE_RELEASE_UNCERTAIN"
                ) from exc
            else:
                self._runtime_settled = True
                self._settled = True


class DockerMatrixHarnessBackend:
    """Fixed-argv local Synapse lifecycle backend; it never pulls images."""

    def __init__(
        self,
        config: MatrixHarnessBackendConfig,
        *,
        kill_switch_engaged: Callable[[], bool],
        readiness_provider: MatrixHarnessReadiness | None = None,
    ) -> None:
        self.config = config
        self._kill_switch_engaged = kill_switch_engaged
        self._readiness_provider = readiness_provider
        self._request_states: set[str] = set()
        self._state_lock = threading.RLock()
        self._process_group_lock = threading.RLock()
        self._owned_process_groups: weakref.WeakKeyDictionary[
            subprocess.Popen[bytes], int
        ] = weakref.WeakKeyDictionary()
        self._process_liveness_write_fds: weakref.WeakKeyDictionary[
            subprocess.Popen[bytes], int
        ] = weakref.WeakKeyDictionary()
        self._settled_process_groups: weakref.WeakSet[subprocess.Popen[bytes]] = (
            weakref.WeakSet()
        )
        self._bound_ref = self._build_binding_ref()

    @property
    def binding_ref(self) -> str:
        return self._bound_ref

    def _build_binding_ref(self) -> str:
        self._validate_package_paths()
        execution_identity_ref = stable_matrix_harness_ref(
            "execution-identity-ref:matrix-harness",
            {"uid": os.getuid(), "gid": os.getgid()},
        )
        return stable_matrix_harness_ref(
            "backend-binding-ref:matrix-harness",
            {
                "image_ref": MATRIX_HARNESS_IMAGE_REF,
                "project_ref": MATRIX_HARNESS_PROJECT_REF,
                "compose_sha256": _file_sha256(self.config.compose_path),
                "template_sha256": _file_sha256(
                    self.config.package_dir / "homeserver.yaml.template"
                ),
                "provider_lock_sha256": _file_sha256(
                    self.config.package_dir / "provider_lock.json"
                ),
                "fixture_helper_sha256": _file_sha256(
                    self.config.package_dir / "seed_runtime_fixtures.py"
                ),
                "docker_binary_sha256": _file_sha256(self.config.docker_binary),
                "execution_identity_ref": execution_identity_ref,
            },
        )

    def _validate_package_paths(self) -> None:
        packaging = self.config.repo_root / "packaging"
        package = self.config.package_dir
        _require_safe_directory(packaging, "MATRIX_HARNESS_PACKAGE_PARENT_UNSAFE")
        _require_safe_directory(package, "MATRIX_HARNESS_PACKAGE_UNSAFE")
        if packaging.resolve() != packaging or package.resolve() != package:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_PACKAGE_PATH_CHANGED")
        for name in (
            "compose.yaml",
            "provider_lock.json",
            "homeserver.yaml.template",
            "seed_runtime_fixtures.py",
        ):
            _require_safe_regular_file(
                package / name,
                "MATRIX_HARNESS_PACKAGE_FILE_UNSAFE",
            )

    def _ownership_ref(self) -> str:
        return stable_matrix_harness_ref(
            "ownership-ref:matrix-harness",
            {
                "backend_binding_ref": self._bound_ref,
                "project_ref": MATRIX_HARNESS_PROJECT_REF,
            },
        )

    def claim_request_state(self, dispatch_ref: str) -> None:
        validate_execution_ref(dispatch_ref, "matrix_harness_dispatch_ref")
        with self._state_lock:
            if dispatch_ref in self._request_states:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_REQUEST_ALREADY_CLAIMED"
                )
            self._request_states.add(dispatch_ref)

    def release_request_state(self, dispatch_ref: str) -> None:
        with self._state_lock:
            self._request_states.discard(dispatch_ref)

    def request_state_active(self, dispatch_ref: str) -> bool:
        with self._state_lock:
            return dispatch_ref in self._request_states

    def safe_disable_engaged(self) -> bool:
        return os.environ.get(MATRIX_HARNESS_SAFE_DISABLE_ENV, "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
            "enabled",
            "engaged",
        }

    def lifecycle_record(self) -> MatrixHarnessLifecycleRecord:
        path = self.config.lifecycle_path
        if path.exists():
            _require_safe_regular_file(
                path,
                "MATRIX_HARNESS_LIFECYCLE_LEDGER_UNSAFE",
            )
            try:
                if path.stat().st_size > 16 * 1024:
                    raise ValueError("MATRIX_HARNESS_LIFECYCLE_LEDGER_OVERSIZED")
                record = MatrixHarnessLifecycleRecord.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
                if record.ownership_ref != self._ownership_ref():
                    raise ValueError("MATRIX_HARNESS_LIFECYCLE_OWNERSHIP_MISMATCH")
                return record
            except (OSError, ValueError) as exc:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_LIFECYCLE_LEDGER_INVALID"
                ) from exc
        state = self.config.state_dir
        if _path_entry_exists(state):
            try:
                _require_safe_directory(state, "MATRIX_HARNESS_STATE_DIR_UNSAFE")
            except ValueError as exc:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_STATE_DIR_UNSAFE"
                ) from exc
            status = MatrixHarnessRuntimeStatus.recovery_required
        else:
            status = MatrixHarnessRuntimeStatus.stopped
        return self._lifecycle_record(
            generation=0,
            state=status,
            operation_ref=None,
        )

    def readiness_reason_refs(self, operation: MatrixHarnessOperation) -> list[str]:
        reasons: list[str] = []
        containment_operation = operation in {
            MatrixHarnessOperation.inspect,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        }
        if self.safe_disable_engaged() and not containment_operation:
            reasons.append("reason-ref:matrix-harness:safe-disable-engaged")
        if self._kill_switch_engaged() and not containment_operation:
            reasons.append("reason-ref:matrix-harness:kill-switch-engaged")
        if self._readiness_provider is not None:
            return list(dict.fromkeys([*reasons, *self._readiness_provider(operation)]))
        if os.getuid() <= 0 or os.getgid() < 0:
            reasons.append("reason-ref:matrix-harness:non-root-identity-required")
        if operation in {
            MatrixHarnessOperation.inspect,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        }:
            return reasons
        result = self._run_probe(
            [
                str(self.config.docker_binary),
                "image",
                "inspect",
                "--format",
                "{{.Id}}",
                MATRIX_HARNESS_IMAGE_REF,
            ],
            timeout=15,
        )
        if result is None or result.returncode != 0:
            reasons.append("reason-ref:matrix-harness:image-not-preprovisioned")
        return list(dict.fromkeys(reasons))

    def start_operation(
        self,
        *,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        lifecycle_generation_ref: str,
        expected_state_ref: str,
        validate_commit_fence: Callable[[], tuple[list[str], datetime]],
        claim_handle: Callable[[MatrixHarnessExecutionHandle], _ClaimedHandleT]
        | None = None,
    ) -> MatrixHarnessExecutionHandle | _ClaimedHandleT:
        validate_execution_ref(execution_ref, "matrix_harness_execution_ref")
        lifecycle_lock_fd = self._acquire_lifecycle_lock(
            create=operation != MatrixHarnessOperation.inspect
        )
        prior_record: MatrixHarnessLifecycleRecord | None = None
        transition_started = False
        process: subprocess.Popen[bytes] | None = None
        with _forward_termination_signals(deferred=True) as signal_guard:
            try:
                fence_reasons, commit_validated_at = validate_commit_fence()
                signal_guard.raise_if_pending()
                runtime_reasons = self.readiness_reason_refs(operation)
                signal_guard.raise_if_pending()
                reasons = list(dict.fromkeys([*fence_reasons, *runtime_reasons]))
                if reasons:
                    raise MatrixHarnessBackendError("MATRIX_HARNESS_FINAL_START_DENIED")
                if self._build_binding_ref() != self._bound_ref:
                    raise MatrixHarnessBackendError(
                        "MATRIX_HARNESS_BACKEND_BINDING_CHANGED"
                    )
                prior_record = self.lifecycle_record()
                self._validate_lifecycle_request(
                    operation=operation,
                    expected_generation_ref=lifecycle_generation_ref,
                    expected_state_ref=expected_state_ref,
                    current=prior_record,
                )
                self._validate_resource_preconditions(operation)
                signal_guard.raise_if_pending()
                if operation == MatrixHarnessOperation.start:
                    self._prepare_ephemeral_state()
                if operation in {
                    MatrixHarnessOperation.start,
                    MatrixHarnessOperation.fixture_seed,
                    MatrixHarnessOperation.stop,
                    MatrixHarnessOperation.reset,
                }:
                    self._write_lifecycle_record(
                        self._lifecycle_record(
                            generation=prior_record.generation + 1,
                            state=MatrixHarnessRuntimeStatus.starting,
                            operation_ref=stable_matrix_harness_ref(
                                "operation-ref:matrix-harness",
                                {
                                    "execution_ref": execution_ref,
                                    "operation": operation.value,
                                },
                            ),
                        )
                    )
                    transition_started = True
                argv = self._argv(operation)
                if self._build_binding_ref() != self._bound_ref:
                    raise MatrixHarnessBackendError(
                        "MATRIX_HARNESS_BACKEND_BINDING_CHANGED"
                    )
                process = self._spawn(argv)
                signal_guard.raise_if_pending()
                handle = MatrixHarnessExecutionHandle(
                    backend=self,
                    operation=operation,
                    execution_ref=execution_ref,
                    process=process,
                    commit_validated_at=commit_validated_at,
                    lifecycle_lock_fd=lifecycle_lock_fd,
                    signal_guard=signal_guard,
                )
                signal_guard.raise_if_pending()
                claimed_handle = (
                    claim_handle(handle) if claim_handle is not None else handle
                )
                signal_guard.raise_if_pending()
                signal_guard.detach()
            except BaseException as exc:
                # Keep this exact guard active and deferred across cleanup. A
                # second signal must not escape between the failed start and
                # process/lifecycle settlement.
                signal_guard.deferred = True
                cleanup_failed = False
                settled_recovery: _MatrixHarnessSettledRecoveryRequired | None = None
                try:
                    if process is not None:
                        self._terminate_and_settle(
                            operation,
                            execution_ref,
                            process,
                        )
                    elif transition_started:
                        # A spawn failure after the durable `starting` record
                        # cannot leave that ambiguous posture behind, even when
                        # the spawn boundary proved process containment itself.
                        self._mark_recovery_required(operation, execution_ref)
                    if (
                        operation == MatrixHarnessOperation.start
                        and not transition_started
                    ):
                        self._delete_state()
                        if _path_entry_exists(self.config.state_dir):
                            raise MatrixHarnessBackendError(
                                "MATRIX_HARNESS_PRESTART_CLEANUP_UNCONFIRMED"
                            )
                    if prior_record is not None and not transition_started:
                        self._write_lifecycle_record(prior_record)
                except _MatrixHarnessSettledRecoveryRequired as settled:
                    settled_recovery = settled
                except BaseException:
                    cleanup_failed = True
                    if prior_record is not None:
                        try:
                            if transition_started:
                                self._mark_recovery_required(
                                    operation,
                                    execution_ref,
                                )
                            else:
                                self._write_lifecycle_record(
                                    self._lifecycle_record(
                                        generation=prior_record.generation + 1,
                                        state=(
                                            MatrixHarnessRuntimeStatus.recovery_required
                                        ),
                                        operation_ref=stable_matrix_harness_ref(
                                            "operation-ref:matrix-harness:prestart-recovery",
                                            {"execution_ref": execution_ref},
                                        ),
                                    )
                                )
                        except Exception:
                            pass
                finally:
                    self._release_lifecycle_lock(lifecycle_lock_fd)
                if settled_recovery is not None:
                    raise settled_recovery from exc
                if cleanup_failed:
                    raise AuthorityDispatchAtomicStartRecoveryRequired(
                        "MATRIX_HARNESS_PRESTART_CLEANUP_UNKNOWN"
                    ) from exc
                if transition_started:
                    try:
                        recovery_truth = (
                            self.lifecycle_record().state
                            == MatrixHarnessRuntimeStatus.recovery_required
                        )
                    except MatrixHarnessBackendError:
                        recovery_truth = True
                    if recovery_truth:
                        raise AuthorityDispatchAtomicStartRecoveryRequired(
                            "MATRIX_HARNESS_START_RECOVERY_REQUIRED"
                        ) from exc
                if isinstance(exc, MatrixHarnessBackendError):
                    raise
                if not isinstance(exc, Exception):
                    raise
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "MATRIX_HARNESS_START_TRUTH_UNKNOWN"
                ) from exc
        return claimed_handle

    def _argv(self, operation: MatrixHarnessOperation) -> list[str]:
        prefix = [
            str(self.config.docker_binary),
            "compose",
            "--project-name",
            "uaa-matrix-harness",
            "-f",
            str(self.config.compose_path),
        ]
        commands = {
            MatrixHarnessOperation.inspect: ["ps", "--all", "--format", "json"],
            MatrixHarnessOperation.smoke: [
                "exec",
                "-T",
                "synapse",
                "curl",
                "-fsS",
                "--max-time",
                "10",
                "http://127.0.0.1:8008/_matrix/client/versions",
            ],
            MatrixHarnessOperation.start: [
                "up",
                "-d",
                "--wait",
                "--wait-timeout",
                "90",
                "--pull",
                "never",
                "--no-build",
            ],
            MatrixHarnessOperation.fixture_seed: [
                "exec",
                "-T",
                "synapse",
                "python",
                "/data/seed_runtime_fixtures.py",
            ],
            MatrixHarnessOperation.stop: ["stop", "--timeout", "10"],
            MatrixHarnessOperation.reset: [
                "down",
                "--volumes",
                "--remove-orphans",
                "--timeout",
                "10",
            ],
        }
        return [*prefix, *commands[operation]]

    def _subprocess_env(self) -> dict[str, str]:
        # Only the exact package variables are inherited by Compose. No host
        # environment dump is exposed to the container or receipts.
        return {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin",
            "UAA_MATRIX_HARNESS_STATE_DIR": str(self.config.state_dir),
            "UAA_MATRIX_HARNESS_IMAGE": MATRIX_HARNESS_IMAGE_REF,
            "UAA_MATRIX_HARNESS_UID": str(os.getuid()),
            "UAA_MATRIX_HARNESS_GID": str(os.getgid()),
        }

    def _prepare_ephemeral_state(self) -> None:
        state = self.config.state_dir
        if _path_entry_exists(state):
            _require_safe_directory(state, "MATRIX_HARNESS_STATE_DIR_UNSAFE")
            entries = list(state.iterdir())
            if entries:
                raise MatrixHarnessBackendError("MATRIX_HARNESS_RETAINED_STATE_BLOCKED")
        else:
            state.mkdir(mode=0o700, parents=True)
        os.chmod(state, 0o700)
        template = (self.config.package_dir / "homeserver.yaml.template").read_text(
            encoding="utf-8"
        )
        secret = secrets.token_hex(32)
        rendered = template.replace("__UAA_MATRIX_REGISTRATION_SECRET__", secret)
        if rendered == template or "__UAA_MATRIX_REGISTRATION_SECRET__" in rendered:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_TEMPLATE_INVALID")
        _write_exclusive(state / "homeserver.yaml", rendered)
        seed_source = self.config.package_dir / "seed_runtime_fixtures.py"
        _require_safe_regular_file(
            seed_source,
            "MATRIX_HARNESS_FIXTURE_HELPER_UNSAFE",
        )
        _write_exclusive(
            state / "seed_runtime_fixtures.py",
            seed_source.read_text(encoding="utf-8"),
        )

    def _collect(
        self,
        *,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        process: subprocess.Popen[bytes],
    ) -> MatrixHarnessBackendResult:
        try:
            stdout, stderr = self._communicate_bounded(
                process,
                timeout=MATRIX_HARNESS_PROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            recovery_required = self._terminate_and_settle(
                operation,
                execution_ref,
                process,
            )
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_OPERATION_TIMEOUT",
                recovery_required=recovery_required,
            )
        except MatrixHarnessSignalInterrupted:
            raise
        except MatrixHarnessBackendError:
            recovery_required = self._terminate_and_settle(
                operation,
                execution_ref,
                process,
            )
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_OUTPUT_LIMIT_EXCEEDED",
                recovery_required=recovery_required,
            )
        self._settle_completed_process_group(
            operation,
            execution_ref,
            process,
        )
        if process.returncode != 0:
            if operation == MatrixHarnessOperation.start:
                cleanup_confirmed = self._cleanup_failed_start()
                if not cleanup_confirmed:
                    self._mark_recovery_required(operation, execution_ref)
                    return self._failure(
                        operation,
                        execution_ref,
                        "MATRIX_HARNESS_START_CLEANUP_UNCONFIRMED",
                        recovery_required=True,
                    )
                self._write_terminal_lifecycle(
                    MatrixHarnessRuntimeStatus.stopped,
                    operation,
                    execution_ref,
                )
            elif operation in {
                MatrixHarnessOperation.fixture_seed,
                MatrixHarnessOperation.stop,
                MatrixHarnessOperation.reset,
            }:
                self._mark_recovery_required(operation, execution_ref)
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_COMMAND_FAILED",
                recovery_required=operation
                in {
                    MatrixHarnessOperation.fixture_seed,
                    MatrixHarnessOperation.stop,
                    MatrixHarnessOperation.reset,
                },
            )
        if (
            operation == MatrixHarnessOperation.smoke
            and not self._host_loopback_healthy()
        ):
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_HOST_LOOPBACK_UNAVAILABLE",
                recovery_required=False,
            )
        resource_posture = self._resource_posture()
        if not self._resource_postcondition_valid(operation, resource_posture):
            if operation in {
                MatrixHarnessOperation.start,
                MatrixHarnessOperation.fixture_seed,
                MatrixHarnessOperation.stop,
                MatrixHarnessOperation.reset,
            }:
                self._mark_recovery_required(operation, execution_ref)
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_RESOURCE_POSTCONDITION_FAILED",
                recovery_required=operation
                in {
                    MatrixHarnessOperation.start,
                    MatrixHarnessOperation.fixture_seed,
                    MatrixHarnessOperation.stop,
                    MatrixHarnessOperation.reset,
                },
            )
        if operation == MatrixHarnessOperation.reset:
            try:
                self._delete_state()
            except MatrixHarnessBackendError:
                self._mark_recovery_required(operation, execution_ref)
                return self._failure(
                    operation,
                    execution_ref,
                    "MATRIX_HARNESS_CLEANUP_UNCONFIRMED",
                    recovery_required=True,
                )
        try:
            counts = _safe_counts(operation, stdout)
        except MatrixHarnessBackendError:
            if operation == MatrixHarnessOperation.fixture_seed:
                self._mark_recovery_required(operation, execution_ref)
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_OUTPUT_SCHEMA_INVALID",
                recovery_required=(operation == MatrixHarnessOperation.fixture_seed),
            )
        if operation == MatrixHarnessOperation.fixture_seed:
            try:
                self._write_fixture_seed_marker(counts)
            except (OSError, MatrixHarnessBackendError, ValueError):
                self._mark_recovery_required(operation, execution_ref)
                return self._failure(
                    operation,
                    execution_ref,
                    "MATRIX_HARNESS_FIXTURE_MARKER_FAILED",
                    recovery_required=True,
                )
        if (
            operation == MatrixHarnessOperation.inspect
            and counts["container_count"] != resource_posture.container_count
        ):
            return self._failure(
                operation,
                execution_ref,
                "MATRIX_HARNESS_INSPECT_OWNERSHIP_COUNT_MISMATCH",
                recovery_required=False,
            )
        counts.update(
            {
                "container_count": resource_posture.container_count,
                "network_count": resource_posture.network_count,
                "volume_count": resource_posture.volume_count,
                "residual_resource_count": 0,
            }
        )
        status = {
            MatrixHarnessOperation.inspect: MatrixHarnessRuntimeStatus.running
            if resource_posture.running_container_count
            else MatrixHarnessRuntimeStatus.stopped,
            MatrixHarnessOperation.smoke: MatrixHarnessRuntimeStatus.healthy,
            MatrixHarnessOperation.start: MatrixHarnessRuntimeStatus.running,
            MatrixHarnessOperation.fixture_seed: MatrixHarnessRuntimeStatus.healthy,
            MatrixHarnessOperation.stop: MatrixHarnessRuntimeStatus.stopped,
            MatrixHarnessOperation.reset: MatrixHarnessRuntimeStatus.stopped,
        }[operation]
        if operation == MatrixHarnessOperation.reset:
            counts.update(
                {
                    "container_count": 0,
                    "network_count": 0,
                    "volume_count": 0,
                    "residual_resource_count": 0,
                }
            )
        terminal_state = {
            MatrixHarnessOperation.start: MatrixHarnessRuntimeStatus.running,
            MatrixHarnessOperation.fixture_seed: MatrixHarnessRuntimeStatus.running,
            MatrixHarnessOperation.stop: MatrixHarnessRuntimeStatus.stopped,
            MatrixHarnessOperation.reset: MatrixHarnessRuntimeStatus.stopped,
        }.get(operation)
        if terminal_state is not None:
            self._write_terminal_lifecycle(
                terminal_state,
                operation,
                execution_ref,
            )
        lifecycle = self.lifecycle_record()
        warning_reason_refs: list[str] = []
        if operation == MatrixHarnessOperation.inspect and (
            (lifecycle.state == MatrixHarnessRuntimeStatus.running)
            != bool(resource_posture.running_container_count)
        ):
            warning_reason_refs.append(
                "reason-ref:matrix-harness:ledger-observation-divergence-reset-required"
            )
        return MatrixHarnessBackendResult(
            execution_ref=execution_ref,
            operation=operation,
            outcome=MatrixHarnessOperationOutcome.succeeded,
            runtime_status=status,
            evidence_refs=[
                stable_matrix_harness_ref(
                    "evidence-ref:matrix-harness",
                    {"execution_ref": execution_ref, "operation": operation.value},
                )
            ],
            safe_summary=_success_summary(operation),
            warning_reason_refs=warning_reason_refs,
            lifecycle_generation_ref=lifecycle.generation_ref,
            lifecycle_state_ref=lifecycle.state_ref,
            **counts,
        )

    def _failure(
        self,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        reason: str,
        *,
        recovery_required: bool,
    ) -> MatrixHarnessBackendResult:
        return MatrixHarnessBackendResult(
            execution_ref=execution_ref,
            operation=operation,
            outcome=(
                MatrixHarnessOperationOutcome.recovery_required
                if recovery_required
                else MatrixHarnessOperationOutcome.failed
            ),
            runtime_status=(
                MatrixHarnessRuntimeStatus.recovery_required
                if recovery_required
                else MatrixHarnessRuntimeStatus.degraded
            ),
            reason_codes=[reason],
            evidence_refs=[
                stable_matrix_harness_ref(
                    "evidence-ref:matrix-harness:failure",
                    {"execution_ref": execution_ref, "reason": reason},
                )
            ],
            safe_summary="Matrix harness operation failed closed with content omitted.",
        )

    def _delete_state(self) -> None:
        state = self.config.state_dir
        if not _path_entry_exists(state):
            return
        try:
            _require_safe_directory(state, "MATRIX_HARNESS_STATE_DIR_UNSAFE")
        except ValueError as exc:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_STATE_DIR_UNSAFE") from exc
        files, directories = self._state_deletion_plan(state)
        for path in files:
            mode = os.lstat(path).st_mode
            if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                raise MatrixHarnessBackendError("MATRIX_HARNESS_STATE_ENTRY_CHANGED")
            path.unlink()
        for path in directories:
            mode = os.lstat(path).st_mode
            if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
                raise MatrixHarnessBackendError("MATRIX_HARNESS_STATE_ENTRY_CHANGED")
            path.rmdir()
        state.rmdir()

    @staticmethod
    def _state_deletion_plan(state: Path) -> tuple[list[Path], list[Path]]:
        files: list[Path] = []
        directories: list[Path] = []
        entry_count = 0

        def inspect(directory: Path) -> None:
            nonlocal entry_count
            try:
                entries = list(directory.iterdir())
            except OSError as exc:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_STATE_ENTRY_UNSAFE"
                ) from exc
            for path in entries:
                entry_count += 1
                if entry_count > 64:
                    raise MatrixHarnessBackendError(
                        "MATRIX_HARNESS_STATE_ENTRY_LIMIT_EXCEEDED"
                    )
                try:
                    mode = os.lstat(path).st_mode
                except OSError as exc:
                    raise MatrixHarnessBackendError(
                        "MATRIX_HARNESS_STATE_ENTRY_UNSAFE"
                    ) from exc
                if stat.S_ISREG(mode) and not stat.S_ISLNK(mode):
                    files.append(path)
                    continue
                if stat.S_ISDIR(mode) and not stat.S_ISLNK(mode):
                    inspect(path)
                    directories.append(path)
                    continue
                raise MatrixHarnessBackendError("MATRIX_HARNESS_STATE_ENTRY_UNSAFE")

        inspect(state)
        return files, directories

    def _cleanup_failed_start(self) -> bool:
        cleanup = self._run_probe(
            self._argv(MatrixHarnessOperation.reset),
            timeout=30,
        )
        if cleanup is None or cleanup.returncode != 0:
            return False
        posture = self._resource_posture()
        if not posture.ownership_valid or posture.total_count != 0:
            return False
        try:
            self._delete_state()
        except MatrixHarnessBackendError:
            return False
        return True

    def _validate_resource_preconditions(
        self,
        operation: MatrixHarnessOperation,
    ) -> None:
        posture = self._resource_posture()
        if not posture.ownership_valid:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_FOREIGN_RESOURCE_COLLISION")
        if operation == MatrixHarnessOperation.start:
            if posture.total_count != 0:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_RETAINED_RESOURCES_BLOCK_START"
                )
            return
        if operation in {
            MatrixHarnessOperation.smoke,
            MatrixHarnessOperation.fixture_seed,
            MatrixHarnessOperation.stop,
        } and (
            posture.container_count != 1
            or posture.running_container_count != 1
            or posture.network_count != 1
            or posture.volume_count != 0
        ):
            raise MatrixHarnessBackendError("MATRIX_HARNESS_OWNED_RUNTIME_REQUIRED")
        if operation == MatrixHarnessOperation.fixture_seed:
            marker = self.config.state_dir / "fixture-seed-v1.json"
            if marker.exists():
                _require_safe_regular_file(
                    marker,
                    "MATRIX_HARNESS_FIXTURE_MARKER_UNSAFE",
                )
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_FIXTURES_ALREADY_SEEDED"
                )

    def _write_fixture_seed_marker(self, counts: dict[str, int]) -> None:
        marker = self.config.state_dir / "fixture-seed-v1.json"
        _write_exclusive(
            marker,
            json.dumps(
                {
                    "fixture_plan_ref": MATRIX_HARNESS_FIXTURE_PLAN_REF,
                    "account_count": counts["fixture_account_count"],
                    "room_count": counts["fixture_room_count"],
                    "event_count": counts["fixture_event_count"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    @staticmethod
    def _host_loopback_healthy() -> bool:
        connection = http.client.HTTPConnection("127.0.0.1", 18008, timeout=10)
        try:
            connection.request("GET", "/_matrix/client/versions")
            response = connection.getresponse()
            body = response.read(65537)
            if response.status != 200 or len(body) > 65536:
                return False
            decoded = json.loads(body.decode("utf-8"))
            return isinstance(decoded, dict) and isinstance(
                decoded.get("versions"), list
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        finally:
            connection.close()

    def _resource_postcondition_valid(
        self,
        operation: MatrixHarnessOperation,
        posture: _MatrixHarnessResourcePosture,
    ) -> bool:
        if not posture.ownership_valid:
            return False
        if operation == MatrixHarnessOperation.start:
            return (
                posture.container_count == 1
                and posture.running_container_count == 1
                and posture.network_count == 1
                and posture.volume_count == 0
            )
        if operation in {
            MatrixHarnessOperation.smoke,
            MatrixHarnessOperation.fixture_seed,
        }:
            return (
                posture.container_count == 1
                and posture.running_container_count == 1
                and posture.network_count == 1
                and posture.volume_count == 0
            )
        if operation == MatrixHarnessOperation.stop:
            return (
                posture.container_count == 1
                and posture.running_container_count == 0
                and posture.network_count == 1
                and posture.volume_count == 0
            )
        if operation == MatrixHarnessOperation.reset:
            return posture.total_count == 0
        return True

    def _resource_posture(self) -> _MatrixHarnessResourcePosture:
        container_ids = self._project_resource_ids("container")
        network_ids = self._project_resource_ids("network")
        volume_ids = self._project_resource_ids("volume")
        ownership_valid = len(volume_ids) == 0
        running_count = 0
        for resource_id in container_ids:
            result = self._run_probe(
                [
                    str(self.config.docker_binary),
                    "container",
                    "inspect",
                    "--format",
                    (
                        '{{index .Config.Labels "com.ultimate-ai-agent.owner"}}|'
                        "{{.Config.Image}}|"
                        '{{index .Config.Labels "com.docker.compose.service"}}|'
                        "{{.State.Running}}"
                    ),
                    resource_id,
                ],
                timeout=10,
            )
            if result is None or result.returncode != 0:
                ownership_valid = False
                continue
            try:
                owner, image, service, running = (
                    result.stdout.decode("utf-8").strip().split("|", 3)
                )
            except (UnicodeDecodeError, ValueError):
                ownership_valid = False
                continue
            if (
                owner != "matrix-harness-v1"
                or image != MATRIX_HARNESS_IMAGE_REF
                or service != "synapse"
                or running not in {"true", "false"}
            ):
                ownership_valid = False
            if running == "true":
                running_count += 1
        for resource_id in network_ids:
            result = self._run_probe(
                [
                    str(self.config.docker_binary),
                    "network",
                    "inspect",
                    "--format",
                    (
                        '{{index .Labels "com.ultimate-ai-agent.owner"}}|'
                        "{{.Internal}}|"
                        '{{index .Options "com.docker.network.bridge.enable_ip_masquerade"}}|'
                        '{{index .Options "com.docker.network.bridge.host_binding_ipv4"}}'
                    ),
                    resource_id,
                ],
                timeout=10,
            )
            if (
                result is None
                or result.returncode != 0
                or result.stdout.decode("utf-8", errors="ignore").strip()
                != "matrix-harness-v1|false|false|127.0.0.1"
            ):
                ownership_valid = False
        return _MatrixHarnessResourcePosture(
            container_count=len(container_ids),
            running_container_count=running_count,
            network_count=len(network_ids),
            volume_count=len(volume_ids),
            ownership_valid=ownership_valid,
        )

    def _project_resource_ids(self, kind: str) -> list[str]:
        noun = {"container": "container", "network": "network", "volume": "volume"}[
            kind
        ]
        result = self._run_probe(
            [
                str(self.config.docker_binary),
                noun,
                "ls",
                "-aq" if noun == "container" else "-q",
                "--filter",
                "label=com.docker.compose.project=uaa-matrix-harness",
            ],
            timeout=10,
        )
        if result is None or result.returncode != 0:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_RESOURCE_INSPECTION_FAILED")
        try:
            refs = [
                line.strip()
                for line in result.stdout.decode("ascii").splitlines()
                if line.strip()
            ]
        except UnicodeDecodeError as exc:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_RESOURCE_INSPECTION_FAILED"
            ) from exc
        if len(refs) > 4 or any(
            not re.fullmatch(r"[0-9a-f]{8,128}", ref) for ref in refs
        ):
            raise MatrixHarnessBackendError("MATRIX_HARNESS_RESOURCE_INSPECTION_FAILED")
        return refs

    def _settle_interrupted_operation(
        self,
        operation: MatrixHarnessOperation,
        execution_ref: str,
    ) -> bool:
        if operation == MatrixHarnessOperation.start:
            if self._cleanup_failed_start():
                self._write_terminal_lifecycle(
                    MatrixHarnessRuntimeStatus.stopped,
                    operation,
                    execution_ref,
                )
                return False
            self._mark_recovery_required(operation, execution_ref)
            return True
        if operation in {
            MatrixHarnessOperation.fixture_seed,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        }:
            self._mark_recovery_required(operation, execution_ref)
            return True
        return False

    def _terminate_and_settle(
        self,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        process: subprocess.Popen[bytes],
    ) -> bool:
        mutating = operation in {
            MatrixHarnessOperation.start,
            MatrixHarnessOperation.fixture_seed,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        }
        try:
            self._terminate_process_group(process)
        except BaseException as termination_error:
            if not mutating:
                raise
            try:
                self._mark_recovery_required(operation, execution_ref)
            except BaseException as settlement_error:
                raise _MatrixHarnessSettledRecoveryRequired(
                    "MATRIX_HARNESS_TERMINATION_SETTLEMENT_UNKNOWN"
                ) from settlement_error
            raise _MatrixHarnessSettledRecoveryRequired(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNKNOWN"
            ) from termination_error
        try:
            return self._settle_interrupted_operation(operation, execution_ref)
        except BaseException as interrupted_settlement_error:
            if not mutating:
                raise
            try:
                self._mark_recovery_required(operation, execution_ref)
            except BaseException as recovery_settlement_error:
                raise _MatrixHarnessSettledRecoveryRequired(
                    "MATRIX_HARNESS_INTERRUPTED_SETTLEMENT_UNKNOWN"
                ) from recovery_settlement_error
            raise _MatrixHarnessSettledRecoveryRequired(
                "MATRIX_HARNESS_INTERRUPTED_OPERATION_RECOVERY_REQUIRED"
            ) from interrupted_settlement_error

    def _settle_completed_process_group(
        self,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        process: subprocess.Popen[bytes],
    ) -> None:
        mutating = operation in {
            MatrixHarnessOperation.start,
            MatrixHarnessOperation.fixture_seed,
            MatrixHarnessOperation.stop,
            MatrixHarnessOperation.reset,
        }
        try:
            self._terminate_process_group(process)
        except BaseException as termination_error:
            if not mutating:
                raise
            try:
                self._mark_recovery_required(operation, execution_ref)
            except BaseException as settlement_error:
                raise _MatrixHarnessSettledRecoveryRequired(
                    "MATRIX_HARNESS_COMPLETION_SETTLEMENT_UNKNOWN"
                ) from settlement_error
            raise _MatrixHarnessSettledRecoveryRequired(
                "MATRIX_HARNESS_COMPLETION_TERMINATION_UNKNOWN"
            ) from termination_error

    def _validate_lifecycle_request(
        self,
        *,
        operation: MatrixHarnessOperation,
        expected_generation_ref: str,
        expected_state_ref: str,
        current: MatrixHarnessLifecycleRecord,
    ) -> None:
        if current.generation_ref != expected_generation_ref:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_LIFECYCLE_GENERATION_MISMATCH"
            )
        if current.state_ref != expected_state_ref:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_EXPECTED_STATE_MISMATCH")
        allowed_states = {
            MatrixHarnessOperation.inspect: set(MatrixHarnessRuntimeStatus),
            MatrixHarnessOperation.smoke: {MatrixHarnessRuntimeStatus.running},
            MatrixHarnessOperation.start: {MatrixHarnessRuntimeStatus.stopped},
            MatrixHarnessOperation.fixture_seed: {MatrixHarnessRuntimeStatus.running},
            MatrixHarnessOperation.stop: {MatrixHarnessRuntimeStatus.running},
            MatrixHarnessOperation.reset: {
                MatrixHarnessRuntimeStatus.running,
                MatrixHarnessRuntimeStatus.stopped,
                MatrixHarnessRuntimeStatus.starting,
                MatrixHarnessRuntimeStatus.recovery_required,
                MatrixHarnessRuntimeStatus.cleanup_required,
                MatrixHarnessRuntimeStatus.unknown,
            },
        }
        if current.state not in allowed_states[operation]:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_LIFECYCLE_TRANSITION_DENIED"
            )

    def _lifecycle_record(
        self,
        *,
        generation: int,
        state: MatrixHarnessRuntimeStatus,
        operation_ref: str | None,
    ) -> MatrixHarnessLifecycleRecord:
        return MatrixHarnessLifecycleRecord(
            generation=generation,
            generation_ref=matrix_harness_generation_ref(generation),
            state=state,
            state_ref=matrix_harness_state_ref(state, generation),
            ownership_ref=self._ownership_ref(),
            operation_ref=operation_ref,
            updated_at=utc_now(),
        )

    def _write_lifecycle_record(
        self,
        record: MatrixHarnessLifecycleRecord,
    ) -> None:
        parent = self.config.lifecycle_path.parent
        _require_safe_directory(parent, "MATRIX_HARNESS_STATE_PARENT_UNSAFE")
        target = self.config.lifecycle_path
        if target.exists():
            _require_safe_regular_file(
                target,
                "MATRIX_HARNESS_LIFECYCLE_LEDGER_UNSAFE",
            )
        temporary = parent / (
            f".messenger-matrix-harness-state.{secrets.token_hex(8)}.tmp"
        )
        _write_exclusive(temporary, record.model_dump_json())
        try:
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _write_terminal_lifecycle(
        self,
        state: MatrixHarnessRuntimeStatus,
        operation: MatrixHarnessOperation,
        execution_ref: str,
    ) -> None:
        current = self.lifecycle_record()
        self._write_lifecycle_record(
            self._lifecycle_record(
                generation=current.generation,
                state=state,
                operation_ref=stable_matrix_harness_ref(
                    "operation-ref:matrix-harness",
                    {
                        "execution_ref": execution_ref,
                        "operation": operation.value,
                    },
                ),
            )
        )

    def _mark_recovery_required(
        self,
        operation: MatrixHarnessOperation,
        execution_ref: str,
    ) -> None:
        self._write_terminal_lifecycle(
            MatrixHarnessRuntimeStatus.recovery_required,
            operation,
            execution_ref,
        )

    def _acquire_lifecycle_lock(self, *, create: bool = True) -> int | None:
        parent = self.config.state_dir.parent
        if not parent.exists():
            if not create:
                return None
            try:
                parent.mkdir(mode=0o700, parents=False)
            except OSError as exc:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_STATE_PARENT_UNAVAILABLE"
                ) from exc
        _require_safe_directory(parent, "MATRIX_HARNESS_STATE_PARENT_UNSAFE")
        lock_path = parent / "messenger-matrix-harness.lock"
        if not create and not lock_path.exists():
            return None
        flags = (os.O_RDWR | os.O_CREAT) if create else os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_LIFECYCLE_LOCK_UNSAFE"
            ) from exc
        try:
            mode = os.fstat(descriptor).st_mode
            if not stat.S_ISREG(mode):
                raise MatrixHarnessBackendError("MATRIX_HARNESS_LIFECYCLE_LOCK_UNSAFE")
            fcntl.flock(
                descriptor,
                (fcntl.LOCK_EX if create else fcntl.LOCK_SH) | fcntl.LOCK_NB,
            )
        except (OSError, MatrixHarnessBackendError) as exc:
            os.close(descriptor)
            raise MatrixHarnessBackendError("MATRIX_HARNESS_LIFECYCLE_BUSY") from exc
        return descriptor

    @staticmethod
    def _release_lifecycle_lock(descriptor: int | None) -> None:
        if descriptor is None:
            return
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _capture_process_group(self, process: subprocess.Popen[bytes]) -> int:
        with self._process_group_lock:
            registered = self._owned_process_groups.get(process)
            if registered is not None:
                return registered
            if process in self._settled_process_groups:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_ALREADY_SETTLED"
                )
        deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_GROUP_READY_SECONDS
        while True:
            try:
                process_group_id = os.getpgid(process.pid)
            except (ProcessLookupError, PermissionError):
                process_group_id = None
            if process_group_id == process.pid:
                with self._process_group_lock:
                    self._owned_process_groups[process] = process_group_id
                return process_group_id
            try:
                terminal_returncode = process.poll()
            except OSError as exc:
                self._terminate_exact_child(process)
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_ISOLATION_UNCONFIRMED"
                ) from exc
            if terminal_returncode is not None and process_group_id is None:
                expected_group_posture = self._process_group_posture(process.pid)
                if expected_group_posture == "absent":
                    with self._process_group_lock:
                        self._settled_process_groups.add(process)
                # Once poll() reaps the child, a bare PID/PGID can be reused.
                # Never defer or signal that number without captured ownership.
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_ISOLATION_UNCONFIRMED"
                )
            if time.monotonic() >= deadline:
                self._terminate_exact_child(process)
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_ISOLATION_UNCONFIRMED"
                )
            time.sleep(MATRIX_HARNESS_PROCESS_POLL_SECONDS)

    @staticmethod
    def _close_process_output_pipes(process: object) -> None:
        """Close captured output on every success, error, and cleanup path."""

        for name in ("stdout", "stderr"):
            stream = getattr(process, name, None)
            if stream is None or getattr(stream, "closed", False):
                continue
            try:
                stream.close()
            except (OSError, ValueError):
                # Process containment remains the stronger cleanup obligation;
                # continue closing the sibling stream and terminating the group.
                continue

    @staticmethod
    def _terminate_exact_child(process: subprocess.Popen[bytes]) -> None:
        DockerMatrixHarnessBackend._close_process_output_pipes(process)
        if process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            except OSError as exc:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
                ) from exc
        try:
            process.wait(timeout=MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            except OSError as exc:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
                ) from exc
            try:
                process.wait(timeout=MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
                ) from exc
        except OSError as exc:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            ) from exc
        if process.returncode is None:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            )

    @staticmethod
    def _process_group_posture(process_group_id: int) -> str:
        try:
            os.killpg(process_group_id, 0)
        except ProcessLookupError:
            return "absent"
        except PermissionError:
            return "permission_denied"
        except OSError as exc:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_GROUP_PROBE_UNCONFIRMED"
            ) from exc
        return "present"

    @staticmethod
    def _process_group_inventory(
        process: subprocess.Popen[bytes],
        process_group_id: int,
    ) -> _MatrixHarnessProcessGroupInventory:
        try:
            result = subprocess.run(
                [
                    "/bin/ps",
                    "-o",
                    "pid=,pgid=,uid=,stat=",
                    "-g",
                    str(process_group_id),
                ],
                cwd="/",
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=MATRIX_HARNESS_PROCESS_INVENTORY_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
            ) from exc
        if (
            result.returncode != 0
            or len(result.stdout) > MATRIX_HARNESS_PROCESS_INVENTORY_LIMIT_BYTES
        ):
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
            )
        rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
        if not rows or len(rows) > MATRIX_HARNESS_PROCESS_GROUP_MEMBER_LIMIT:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
            )
        leader_terminal: bool | None = None
        live_member_count = 0
        for row in rows:
            if len(row) != 4:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
                )
            try:
                pid = int(row[0])
                observed_group_id = int(row[1])
                uid = int(row[2])
                process_state = row[3].decode("ascii", errors="strict")
            except (UnicodeDecodeError, ValueError) as exc:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
                ) from exc
            if (
                pid <= 0
                or observed_group_id != process_group_id
                or uid != os.getuid()
                or not process_state
                or not process_state[0].isalpha()
            ):
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
                )
            terminal = process_state[0] in {"X", "Z"}
            if pid == process.pid:
                leader_terminal = terminal
            elif not terminal:
                live_member_count += 1
        if leader_terminal is None:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
            )
        return _MatrixHarnessProcessGroupInventory(
            leader_terminal=leader_terminal,
            live_member_count=live_member_count,
            member_count=len(rows),
        )

    @staticmethod
    def _signal_process_group(process_group_id: int, signum: signal.Signals) -> None:
        try:
            os.killpg(process_group_id, signum)
        except (ProcessLookupError, PermissionError):
            # The independent group-presence proof below distinguishes a
            # completed exit from a permission or zombie race.
            return
        except OSError as exc:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            ) from exc

    @classmethod
    def _wait_for_process_group_absence(
        cls,
        process_group_id: int,
        *,
        deadline: float,
    ) -> bool:
        while True:
            posture = cls._process_group_posture(process_group_id)
            if posture == "absent":
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(MATRIX_HARNESS_PROCESS_POLL_SECONDS)

    @staticmethod
    def _wait_for_exact_child(
        process: subprocess.Popen[bytes],
        *,
        deadline: float,
    ) -> None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            )
        try:
            process.wait(timeout=remaining)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            ) from exc
        if process.returncode is None:
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            )

    def _mark_process_group_settled(
        self,
        process: subprocess.Popen[bytes],
    ) -> None:
        self._close_process_output_pipes(process)
        self._close_process_liveness_pipe(process)
        with self._process_group_lock:
            self._owned_process_groups.pop(process, None)
            self._settled_process_groups.add(process)

    def _close_process_liveness_pipe(
        self,
        process: subprocess.Popen[bytes],
    ) -> None:
        with self._process_group_lock:
            descriptor = self._process_liveness_write_fds.pop(process, None)
        if descriptor is None:
            return
        try:
            os.close(descriptor)
        except OSError:
            pass

    def _reap_and_prove_process_group_absent(
        self,
        process: subprocess.Popen[bytes],
        process_group_id: int,
        *,
        deadline: float,
    ) -> None:
        self._wait_for_exact_child(process, deadline=deadline)
        if not self._wait_for_process_group_absence(
            process_group_id,
            deadline=deadline,
        ):
            # The leader has been reaped, so the numeric PGID may now be
            # reusable. Never signal it again; report stronger uncertainty.
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            )
        self._mark_process_group_settled(process)

    def _terminate_process_group(self, process: subprocess.Popen[bytes]) -> None:
        self._close_process_output_pipes(process)
        self._close_process_liveness_pipe(process)
        with self._process_group_lock:
            if process in self._settled_process_groups:
                return
            process_group_id = self._owned_process_groups.get(process)
        if process_group_id is None:
            process_group_id = self._capture_process_group(process)

        if process.returncode is not None:
            terminal_group_posture = self._process_group_posture(process_group_id)
            if terminal_group_posture == "absent":
                self._mark_process_group_settled(process)
                return
            # A reaped leader releases its numeric PID/PGID for reuse. Even a
            # signalable group cannot be proven to be the original group.
            raise _MatrixHarnessCleanupError(
                "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
            )

        initial_posture = self._process_group_posture(process_group_id)
        if initial_posture == "absent":
            deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
            self._reap_and_prove_process_group_absent(
                process,
                process_group_id,
                deadline=deadline,
            )
            return
        if initial_posture == "permission_denied":
            deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
            self._reap_and_prove_process_group_absent(
                process,
                process_group_id,
                deadline=deadline,
            )
            return
        inventory = self._process_group_inventory(process, process_group_id)
        if inventory.leader_terminal and inventory.live_member_count == 0:
            deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
            self._reap_and_prove_process_group_absent(
                process,
                process_group_id,
                deadline=deadline,
            )
            return
        self._signal_process_group(process_group_id, signal.SIGTERM)
        term_deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS
        while time.monotonic() < term_deadline:
            term_posture = self._process_group_posture(process_group_id)
            if term_posture in {"absent", "permission_denied"}:
                final_wait_deadline = (
                    time.monotonic() + MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
                )
                self._reap_and_prove_process_group_absent(
                    process,
                    process_group_id,
                    deadline=final_wait_deadline,
                )
                return
            time.sleep(MATRIX_HARNESS_PROCESS_POLL_SECONDS)

        self._signal_process_group(process_group_id, signal.SIGKILL)
        kill_deadline = time.monotonic() + MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
        self._reap_and_prove_process_group_absent(
            process,
            process_group_id,
            deadline=kill_deadline,
        )

    @staticmethod
    def _communicate_bounded(
        process: subprocess.Popen[bytes],
        *,
        timeout: int,
    ) -> tuple[bytes, bytes]:
        if process.stdout is None or process.stderr is None:
            raise MatrixHarnessBackendError("MATRIX_HARNESS_OUTPUT_PIPE_REQUIRED")
        selector = selectors.DefaultSelector()
        streams = {process.stdout: bytearray(), process.stderr: bytearray()}
        deadline = time.monotonic() + timeout
        total_bytes = 0
        try:
            for stream in streams:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(process.args, timeout)
                for key, _mask in selector.select(min(remaining, 0.1)):
                    stream = key.fileobj
                    try:
                        chunk = os.read(stream.fileno(), 4096)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(stream)
                        continue
                    total_bytes += len(chunk)
                    if total_bytes > MATRIX_HARNESS_OUTPUT_LIMIT_BYTES:
                        raise MatrixHarnessBackendError(
                            "MATRIX_HARNESS_OUTPUT_LIMIT_EXCEEDED"
                        )
                    streams[stream].extend(chunk)
        finally:
            selector.close()
            DockerMatrixHarnessBackend._close_process_output_pipes(process)
        return bytes(streams[process.stdout]), bytes(streams[process.stderr])

    def _run_probe(
        self,
        argv: list[str],
        *,
        timeout: int,
    ) -> subprocess.CompletedProcess[bytes] | None:
        process: subprocess.Popen[bytes] | None = None
        try:
            process = self._spawn(argv)
            stdout, stderr = self._communicate_bounded(process, timeout=timeout)
        except _MatrixHarnessCleanupError:
            raise
        except BaseException as probe_error:
            if process is not None:
                try:
                    self._terminate_process_group(process)
                except BaseException as cleanup_error:
                    raise cleanup_error from probe_error
            if isinstance(
                probe_error,
                (OSError, subprocess.TimeoutExpired, MatrixHarnessBackendError),
            ):
                return None
            raise
        self._terminate_process_group(process)
        return subprocess.CompletedProcess(
            args=argv,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr,
        )

    def _spawn(self, argv: list[str]) -> subprocess.Popen[bytes]:
        gate_read_fd, gate_write_fd = os.pipe()
        liveness_read_fd, liveness_write_fd = os.pipe()
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    _MATRIX_HARNESS_SPAWN_GATE,
                    str(gate_read_fd),
                    str(liveness_read_fd),
                    *argv,
                ],
                cwd=self.config.repo_root,
                env=self._subprocess_env(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                pass_fds=(gate_read_fd, liveness_read_fd),
                start_new_session=True,
                shell=False,
            )
            os.close(gate_read_fd)
            gate_read_fd = -1
            os.close(liveness_read_fd)
            liveness_read_fd = -1
            self._capture_process_group(process)
            with self._process_group_lock:
                self._process_liveness_write_fds[process] = liveness_write_fd
            liveness_write_fd = -1
            if os.write(gate_write_fd, b"1") != 1:
                raise _MatrixHarnessCleanupError(
                    "MATRIX_HARNESS_SPAWN_GATE_RELEASE_UNCONFIRMED"
                )
            os.close(gate_write_fd)
            gate_write_fd = -1
            return process
        except BaseException as spawn_error:
            if process is not None:
                try:
                    with self._process_group_lock:
                        group_owned = process in self._owned_process_groups
                    if group_owned:
                        self._terminate_process_group(process)
                    else:
                        # The target remains behind the inherited pipe gate
                        # unless owned group capture succeeded. Exact-child
                        # termination is therefore sufficient only here.
                        self._terminate_exact_child(process)
                        expected_group_posture = self._process_group_posture(
                            process.pid
                        )
                        if expected_group_posture != "absent":
                            raise _MatrixHarnessCleanupError(
                                "MATRIX_HARNESS_SPAWN_CONTAINMENT_UNCONFIRMED"
                            )
                except BaseException as cleanup_error:
                    raise cleanup_error from spawn_error
            raise
        finally:
            for descriptor in (
                gate_read_fd,
                gate_write_fd,
                liveness_read_fd,
                liveness_write_fd,
            ):
                if descriptor >= 0:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass


def _safe_counts(
    operation: MatrixHarnessOperation,
    stdout: bytes,
) -> dict[str, int]:
    counts = {
        "container_count": 0,
        "network_count": 0,
        "volume_count": 0,
        "fixture_account_count": 0,
        "fixture_room_count": 0,
        "fixture_event_count": 0,
        "residual_resource_count": 0,
    }
    if operation == MatrixHarnessOperation.inspect:
        try:
            raw = stdout.decode("utf-8").strip()
            rows = (
                json.loads(raw)
                if raw.startswith("[")
                else [json.loads(line) for line in raw.splitlines() if line]
            )
            if not isinstance(rows, list) or any(
                not isinstance(row, dict) for row in rows
            ):
                raise MatrixHarnessBackendError("MATRIX_HARNESS_INSPECT_SCHEMA_INVALID")
            if len(rows) > 4:
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_INSPECT_ENTRY_LIMIT_EXCEEDED"
                )
            counts["container_count"] = len(rows)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_INSPECT_SCHEMA_INVALID"
            ) from exc
    elif operation == MatrixHarnessOperation.fixture_seed:
        # The seed helper emits counts only, never accounts, credentials, room
        # names, event bodies, tokens, or provider payloads.
        try:
            payload = json.loads(stdout.decode("ascii"))
            counts["fixture_account_count"] = int(payload["account_count"])
            counts["fixture_room_count"] = int(payload["room_count"])
            counts["fixture_event_count"] = int(payload["event_count"])
            if (
                set(payload) != {"account_count", "room_count", "event_count"}
                or counts["fixture_account_count"] != 2
                or counts["fixture_room_count"] != 3
                or counts["fixture_event_count"] != 5
            ):
                raise MatrixHarnessBackendError(
                    "MATRIX_HARNESS_FIXTURE_COUNTS_MISMATCH"
                )
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise MatrixHarnessBackendError(
                "MATRIX_HARNESS_FIXTURE_SCHEMA_INVALID"
            ) from exc
    return counts


def _success_summary(operation: MatrixHarnessOperation) -> str:
    return {
        MatrixHarnessOperation.inspect: "Matrix harness ownership posture inspected with raw Compose output omitted.",
        MatrixHarnessOperation.smoke: "Matrix harness bounded loopback liveness check passed.",
        MatrixHarnessOperation.start: "Disposable loopback Matrix harness started from the pre-provisioned pinned image.",
        MatrixHarnessOperation.fixture_seed: "Synthetic runtime Matrix fixtures were seeded with content and credentials omitted.",
        MatrixHarnessOperation.stop: "Matrix harness process was stopped; disposable state remains until exact reset.",
        MatrixHarnessOperation.reset: "Matrix harness resources and disposable state were removed.",
    }[operation]


def _file_sha256(path: Path) -> str:
    import hashlib

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise ValueError("MATRIX_HARNESS_HASH_SOURCE_UNSAFE")
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _require_safe_regular_file(path: Path, code: str) -> None:
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        raise ValueError(code) from exc
    if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
        raise ValueError(code)


def _path_entry_exists(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise MatrixHarnessBackendError(
            "MATRIX_HARNESS_PATH_INSPECTION_FAILED"
        ) from exc
    return True


def _require_safe_directory(path: Path, code: str) -> None:
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        raise ValueError(code) from exc
    if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        raise ValueError(code)


def _write_exclusive(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def default_matrix_harness_backend_config(
    repo_root: Path,
) -> MatrixHarnessBackendConfig:
    docker = shutil.which("docker")
    if docker is None:
        raise ValueError("MATRIX_HARNESS_DOCKER_BINARY_UNAVAILABLE")
    return MatrixHarnessBackendConfig(
        repo_root=repo_root.resolve(),
        docker_binary=Path(docker).resolve(),
        state_dir=repo_root.resolve() / ".uaa" / "messenger-matrix-harness",
    )


@contextmanager
def _forward_termination_signals(
    *,
    deferred: bool = False,
) -> Iterator[_MatrixHarnessSignalGuard]:
    guard = _MatrixHarnessSignalGuard(deferred=deferred)
    if atomic_start_signal_guard_active():
        # AuthorityDispatcher owns the process-signal boundary for canonical
        # execution. Installing a nested backend handler would consume the
        # dispatcher interruption and could convert cancellation into a clean
        # return after local recovery.
        yield guard
        return
    if threading.current_thread() is not threading.main_thread():
        yield guard
        return
    watched = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, watched)
    previous: dict[signal.Signals, object] = {}
    installed: list[signal.Signals] = []
    try:
        for watched_signal in watched:
            previous[watched_signal] = signal.getsignal(watched_signal)
            signal.signal(watched_signal, guard.handle)
            installed.append(watched_signal)
        guard.activate(watched, previous)
    except BaseException:
        for watched_signal in reversed(installed):
            signal.signal(watched_signal, previous[watched_signal])  # type: ignore[arg-type]
        raise
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

    try:
        yield guard
    finally:
        if not guard.detached:
            guard.restore()
