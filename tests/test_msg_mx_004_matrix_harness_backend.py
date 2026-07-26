from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

import pytest

import ultimate_ai_agent.core.communications.matrix_harness.backend as matrix_backend
from ultimate_ai_agent.core.communications.matrix_harness.backend import (
    DockerMatrixHarnessBackend,
    MatrixHarnessBackendConfig,
    MatrixHarnessBackendError,
    MatrixHarnessExecutionHandle,
    MatrixHarnessSignalInterrupted,
    _MatrixHarnessCleanupError,
    _safe_counts,
)
from ultimate_ai_agent.core.communications.matrix_harness.constants import (
    MATRIX_HARNESS_IMAGE_REF,
    MatrixHarnessOperation,
)
from ultimate_ai_agent.core.communications.matrix_harness.contracts import (
    MatrixHarnessOperationOutcome,
    MatrixHarnessRuntimeStatus,
    matrix_harness_generation_ref,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
    _AtomicStartTerminationGuard,
)


@pytest.fixture
def harness_backend(tmp_path: Path) -> DockerMatrixHarnessBackend:
    repo = tmp_path / "repo"
    package = repo / "packaging" / "messenger-matrix-harness"
    package.mkdir(parents=True)
    source_package = Path("packaging/messenger-matrix-harness")
    for name in (
        "compose.yaml",
        "provider_lock.json",
        "homeserver.yaml.template",
        "seed_runtime_fixtures.py",
    ):
        shutil.copyfile(source_package / name, package / name)
    docker = repo / "docker"
    docker.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    docker.chmod(0o700)
    return DockerMatrixHarnessBackend(
        MatrixHarnessBackendConfig(
            repo_root=repo.resolve(),
            docker_binary=docker.resolve(),
            state_dir=repo.resolve() / ".uaa" / "messenger-matrix-harness",
        ),
        kill_switch_engaged=lambda: False,
        readiness_provider=lambda _operation: [],
    )


def test_config_rejects_state_escape_and_symlinked_state_parent(
    harness_backend: DockerMatrixHarnessBackend,
    tmp_path: Path,
) -> None:
    config = harness_backend.config
    with pytest.raises(ValueError, match="STATE_DIR_OUT_OF_SCOPE"):
        MatrixHarnessBackendConfig(
            repo_root=config.repo_root,
            docker_binary=config.docker_binary,
            state_dir=tmp_path / "outside",
        )

    outside = tmp_path / "outside-state"
    outside.mkdir()
    config.state_dir.parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="STATE_PARENT_UNSAFE"):
        MatrixHarnessBackendConfig(
            repo_root=config.repo_root,
            docker_binary=config.docker_binary,
            state_dir=config.state_dir,
        )


def test_config_rejects_symlinked_packaging_ancestor(
    harness_backend: DockerMatrixHarnessBackend,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "symlinked-package-repo"
    repo.mkdir()
    external = tmp_path / "external-packaging"
    package = external / "messenger-matrix-harness"
    package.mkdir(parents=True)
    for name in (
        "compose.yaml",
        "provider_lock.json",
        "homeserver.yaml.template",
    ):
        (package / name).write_text("safe", encoding="utf-8")
    (repo / "packaging").symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="PACKAGE_PARENT_UNSAFE"):
        MatrixHarnessBackendConfig(
            repo_root=repo.resolve(),
            docker_binary=harness_backend.config.docker_binary,
            state_dir=repo.resolve() / ".uaa" / "messenger-matrix-harness",
        )


def test_compose_uses_non_root_identity_no_raw_logs_and_inspect_includes_stopped(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    compose = harness_backend.config.compose_path.read_text(encoding="utf-8")
    assert "UAA_MATRIX_HARNESS_UID" in compose
    assert "UAA_MATRIX_HARNESS_GID" in compose
    assert "driver: none" in compose
    assert "json-file" not in compose
    assert 'com.docker.network.bridge.enable_ip_masquerade: "false"' in compose
    assert "com.docker.network.bridge.host_binding_ipv4: 127.0.0.1" in compose
    assert harness_backend._argv(MatrixHarnessOperation.inspect)[-4:] == [
        "ps",
        "--all",
        "--format",
        "json",
    ]
    environment = harness_backend._subprocess_env()
    assert environment["UAA_MATRIX_HARNESS_UID"] == str(os.getuid())
    assert environment["UAA_MATRIX_HARNESS_GID"] == str(os.getgid())


def test_read_only_inspect_lock_does_not_create_state_parent(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    assert not harness_backend.config.state_dir.parent.exists()
    assert harness_backend._acquire_lifecycle_lock(create=False) is None
    assert not harness_backend.config.state_dir.parent.exists()


def test_fixture_seed_marker_blocks_second_seed(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = harness_backend.config.state_dir
    state.mkdir(parents=True)
    (state / "fixture-seed-v1.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        harness_backend,
        "_resource_posture",
        lambda: type(
            "Posture",
            (),
            {
                "ownership_valid": True,
                "container_count": 1,
                "running_container_count": 1,
                "network_count": 1,
                "volume_count": 0,
            },
        )(),
    )
    with pytest.raises(MatrixHarnessBackendError, match="ALREADY_SEEDED"):
        harness_backend._validate_resource_preconditions(
            MatrixHarnessOperation.fixture_seed
        )


def test_state_deletion_preflights_every_entry_before_mutation(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    state = harness_backend.config.state_dir
    state.mkdir(parents=True)
    safe = state / "safe.txt"
    safe.write_text("safe", encoding="utf-8")
    unsafe = state / "unsafe.fifo"
    os.mkfifo(unsafe)

    with pytest.raises(MatrixHarnessBackendError, match="STATE_ENTRY_UNSAFE"):
        harness_backend._delete_state()

    assert safe.read_text(encoding="utf-8") == "safe"
    assert unsafe.exists()


def test_state_deletion_rejects_dangling_state_directory_symlink(
    harness_backend: DockerMatrixHarnessBackend,
    tmp_path: Path,
) -> None:
    state = harness_backend.config.state_dir
    state.parent.mkdir(parents=True)
    state.symlink_to(tmp_path / "missing-state-target", target_is_directory=True)

    with pytest.raises(MatrixHarnessBackendError, match="STATE_DIR_UNSAFE"):
        harness_backend._delete_state()

    assert state.is_symlink()


@pytest.mark.parametrize("entry_kind", ["symlink", "fifo"])
def test_lifecycle_and_lock_entries_fail_closed(
    harness_backend: DockerMatrixHarnessBackend,
    tmp_path: Path,
    entry_kind: str,
) -> None:
    parent = harness_backend.config.state_dir.parent
    parent.mkdir()
    lifecycle = harness_backend.config.lifecycle_path
    lock = parent / "messenger-matrix-harness.lock"
    outside = tmp_path / "outside"
    outside.write_text("outside", encoding="utf-8")
    if entry_kind == "symlink":
        lifecycle.symlink_to(outside)
    else:
        os.mkfifo(lifecycle)
    with pytest.raises((MatrixHarnessBackendError, ValueError)):
        harness_backend.lifecycle_record()
    lifecycle.unlink()
    if entry_kind == "symlink":
        lock.symlink_to(outside)
    else:
        os.mkfifo(lock)
    with pytest.raises(MatrixHarnessBackendError):
        harness_backend._acquire_lifecycle_lock()
    assert outside.read_text(encoding="utf-8") == "outside"


def test_lifecycle_ledger_rejects_stale_backend_ownership(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    harness_backend.config.state_dir.parent.mkdir()
    record = harness_backend._lifecycle_record(
        generation=2,
        state=MatrixHarnessRuntimeStatus.stopped,
        operation_ref=None,
    )
    harness_backend._write_lifecycle_record(
        record.model_copy(
            update={"ownership_ref": "ownership-ref:matrix-harness:stale"}
        )
    )

    with pytest.raises(MatrixHarnessBackendError, match="LIFECYCLE_LEDGER_INVALID"):
        harness_backend.lifecycle_record()


def test_physical_lifecycle_lock_serializes_and_recovers(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    first = harness_backend._acquire_lifecycle_lock()
    with pytest.raises(MatrixHarnessBackendError, match="LIFECYCLE_BUSY"):
        harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(first)
    second = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(second)


def test_stale_generation_denies_before_process_start(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harness_backend,
        "_spawn",
        lambda _argv: pytest.fail("process must not start"),
    )
    current = harness_backend.lifecycle_record()
    with pytest.raises(MatrixHarnessBackendError, match="GENERATION_MISMATCH"):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.start,
            execution_ref="execution-ref:matrix-harness:stale-generation",
            lifecycle_generation_ref=matrix_harness_generation_ref(99),
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )


def test_backend_binding_change_denies_before_process_start(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_lock = harness_backend.config.package_dir / "provider_lock.json"
    provider_lock.write_text('{"changed":true}', encoding="utf-8")
    monkeypatch.setattr(
        harness_backend,
        "_spawn",
        lambda _argv: pytest.fail("process must not start"),
    )
    current = harness_backend.lifecycle_record()
    with pytest.raises(MatrixHarnessBackendError, match="BINDING_CHANGED"):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.start,
            execution_ref="execution-ref:matrix-harness:changed-binding",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )


def test_failed_prestart_cleanup_persists_recovery_required(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_write = harness_backend._write_lifecycle_record
    writes = 0

    def fail_first_write(record: object) -> None:
        nonlocal writes
        writes += 1
        if writes == 1:
            os.mkfifo(harness_backend.config.state_dir / "unsafe.fifo")
            raise OSError("injected durable transition failure")
        original_write(record)  # type: ignore[arg-type]

    monkeypatch.setattr(harness_backend, "_write_lifecycle_record", fail_first_write)
    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    monkeypatch.setattr(
        harness_backend,
        "_spawn",
        lambda _argv: pytest.fail("process must not start"),
    )
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="PRESTART_CLEANUP_UNKNOWN",
    ):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.start,
            execution_ref="execution-ref:matrix-harness:prestart-recovery",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert harness_backend.lifecycle_record().state == (
        MatrixHarnessRuntimeStatus.recovery_required
    )
    assert (harness_backend.config.state_dir / "unsafe.fifo").exists()


def test_contained_spawn_failure_after_durable_transition_surfaces_recovery(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    monkeypatch.setattr(
        harness_backend,
        "_spawn",
        lambda _argv: (_ for _ in ()).throw(
            matrix_backend._MatrixHarnessCleanupError(
                "MATRIX_HARNESS_INJECTED_CONTAINED_SPAWN_FAILURE"
            )
        ),
    )
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="START_RECOVERY_REQUIRED",
    ):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.reset,
            execution_ref="execution-ref:matrix-harness:contained-spawn-failure",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )


def test_settled_start_recovery_is_not_settled_twice(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = object()
    settlement_attempts = 0

    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    monkeypatch.setattr(harness_backend, "_spawn", lambda _argv: process)
    monkeypatch.setattr(
        matrix_backend,
        "MatrixHarnessExecutionHandle",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("injected handle construction failure")
        ),
    )

    def settle_once(
        operation: MatrixHarnessOperation,
        execution_ref: str,
        _process: object,
    ) -> bool:
        nonlocal settlement_attempts
        settlement_attempts += 1
        harness_backend._mark_recovery_required(operation, execution_ref)
        raise matrix_backend._MatrixHarnessSettledRecoveryRequired(
            "MATRIX_HARNESS_INJECTED_SETTLED_RECOVERY"
        )

    monkeypatch.setattr(harness_backend, "_terminate_and_settle", settle_once)
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        matrix_backend._MatrixHarnessSettledRecoveryRequired,
        match="INJECTED_SETTLED_RECOVERY",
    ):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.reset,
            execution_ref="execution-ref:matrix-harness:settle-once",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert settlement_attempts == 1
    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )


def test_kill_switch_and_safe_disable_preserve_containment_operations(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness_backend._kill_switch_engaged = lambda: True
    monkeypatch.setenv("UAA_MATRIX_HARNESS_SAFE_DISABLE", "1")
    for operation in (
        MatrixHarnessOperation.start,
        MatrixHarnessOperation.smoke,
        MatrixHarnessOperation.fixture_seed,
    ):
        reasons = harness_backend.readiness_reason_refs(operation)
        assert "reason-ref:matrix-harness:kill-switch-engaged" in reasons
        assert "reason-ref:matrix-harness:safe-disable-engaged" in reasons
    for operation in (
        MatrixHarnessOperation.inspect,
        MatrixHarnessOperation.stop,
        MatrixHarnessOperation.reset,
    ):
        assert harness_backend.readiness_reason_refs(operation) == []


def test_resource_posture_rejects_foreign_container_owner(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        harness_backend,
        "_project_resource_ids",
        lambda kind: ["container-id"] if kind == "container" else [],
    )
    monkeypatch.setattr(
        harness_backend,
        "_run_probe",
        lambda _argv, timeout: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(f"foreign|{MATRIX_HARNESS_IMAGE_REF}|synapse|true\n").encode(),
            stderr=b"",
        ),
    )

    assert harness_backend._resource_posture().ownership_valid is False


def test_failed_start_with_unconfirmed_cleanup_requires_recovery(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = harness_backend._spawn(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(0.05); raise SystemExit(1)",
        ]
    )
    monkeypatch.setattr(harness_backend, "_cleanup_failed_start", lambda: False)
    monkeypatch.setattr(harness_backend, "_mark_recovery_required", lambda *_args: None)
    result = harness_backend._collect(
        operation=MatrixHarnessOperation.start,
        execution_ref="execution-ref:matrix-harness:failed-start",
        process=process,
    )

    assert result.outcome == MatrixHarnessOperationOutcome.recovery_required
    assert result.reason_codes == ["MATRIX_HARNESS_START_CLEANUP_UNCONFIRMED"]


def test_combined_output_limit_terminates_without_returning_raw_output(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    process = harness_backend._spawn(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 70000)"]
    )
    with pytest.raises(MatrixHarnessBackendError, match="OUTPUT_LIMIT_EXCEEDED"):
        harness_backend._communicate_bounded(process, timeout=5)
    assert process.stdout is not None and process.stdout.closed
    assert process.stderr is not None and process.stderr.closed
    harness_backend._terminate_process_group(process)
    assert process.poll() is not None


def test_bounded_communication_closes_output_descriptors_after_success(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    process = harness_backend._spawn(
        [sys.executable, "-c", "import os; os.write(1, b'safe-output')"]
    )

    stdout, stderr = harness_backend._communicate_bounded(process, timeout=5)

    assert stdout == b"safe-output"
    assert stderr == b""
    assert process.stdout is not None and process.stdout.closed
    assert process.stderr is not None and process.stderr.closed
    harness_backend._terminate_process_group(process)


def test_spawn_captures_owned_process_group_before_return(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    process = harness_backend._spawn(
        [sys.executable, "-c", "import time; time.sleep(30)"]
    )
    assert harness_backend._owned_process_groups[process] == process.pid
    harness_backend._terminate_process_group(process)


def test_parent_liveness_pipe_kills_detached_process_group(
    harness_backend: DockerMatrixHarnessBackend,
) -> None:
    process = harness_backend._spawn(
        [sys.executable, "-c", "import time; time.sleep(30)"]
    )
    process_group_id = harness_backend._owned_process_groups[process]

    harness_backend._close_process_liveness_pipe(process)
    # Preserve exact absence proof while allowing one production kill grace
    # plus bounded scheduler delay on a loaded self-hosted runner.
    deadline = (
        time.monotonic()
        + matrix_backend.MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
        + 5
    )
    unconfirmed_inventory_count = 0
    while time.monotonic() < deadline:
        try:
            inventory = harness_backend._process_group_inventory(
                process,
                process_group_id,
            )
        except _MatrixHarnessCleanupError as exc:
            assert str(exc) == "MATRIX_HARNESS_PROCESS_GROUP_INVENTORY_UNCONFIRMED"
            unconfirmed_inventory_count += 1
            time.sleep(0.01)
            continue
        if inventory.leader_terminal and inventory.live_member_count == 0:
            break
        time.sleep(0.01)
    else:
        pytest.fail(
            "parent-liveness watchdog did not reach an exactly confirmed "
            f"terminal group after {unconfirmed_inventory_count} transient probes"
        )

    process.wait(timeout=5)
    assert process.returncode is not None
    harness_backend._mark_process_group_settled(process)


def test_capture_quick_terminal_child_never_defers_reusable_pgid(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class QuickTerminalProcess:
        pid = 12345

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.poll_calls = 0

        def poll(self) -> int:
            self.poll_calls += 1
            self.returncode = 0
            return self.returncode

        def terminate(self) -> None:
            pytest.fail("confirmed terminal child must not be terminated again")

        def kill(self) -> None:
            pytest.fail("confirmed terminal child must not be killed again")

        def wait(self, *, timeout: float) -> int:
            assert timeout >= 0
            assert self.returncode is not None
            return self.returncode

    process = QuickTerminalProcess()
    signals: list[tuple[int, signal.Signals]] = []

    def missing_leader(_pid: int) -> int:
        raise ProcessLookupError

    monkeypatch.setattr(os, "getpgid", missing_leader)

    def absent_expected_group(pid: int, signum: signal.Signals) -> None:
        signals.append((pid, signum))
        raise ProcessLookupError

    monkeypatch.setattr(os, "killpg", absent_expected_group)

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_GROUP_ISOLATION_UNCONFIRMED",
    ):
        harness_backend._capture_process_group(process)  # type: ignore[arg-type]

    assert process not in harness_backend._owned_process_groups
    assert process in harness_backend._settled_process_groups
    assert process.poll_calls == 1
    assert signals == [(process.pid, 0)]


def test_spawn_cleans_exact_child_when_group_capture_raises(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_marker = harness_backend.config.repo_root / "target-executed"
    cleaned_returncodes: list[int | None] = []
    closed_output_pipes: list[bool] = []
    exact_cleanup = harness_backend._terminate_exact_child

    def fail_capture(_process: object) -> int:
        raise MatrixHarnessBackendError("injected capture failure")

    def record_cleanup(process: subprocess.Popen[bytes]) -> None:
        exact_cleanup(process)
        cleaned_returncodes.append(process.returncode)
        closed_output_pipes.append(
            process.stdout is not None
            and process.stdout.closed
            and process.stderr is not None
            and process.stderr.closed
        )

    monkeypatch.setattr(harness_backend, "_capture_process_group", fail_capture)
    monkeypatch.setattr(harness_backend, "_terminate_exact_child", record_cleanup)

    with pytest.raises(MatrixHarnessBackendError, match="capture failure"):
        harness_backend._spawn(
            [
                sys.executable,
                "-c",
                (
                    "import os,sys;"
                    "from pathlib import Path;"
                    "child=os.fork();"
                    "Path(sys.argv[1]).touch() if child == 0 else os._exit(0)"
                ),
                str(target_marker),
            ]
        )

    assert len(cleaned_returncodes) == 1
    assert cleaned_returncodes[0] is not None
    assert closed_output_pipes == [True]
    assert not target_marker.exists()


def test_post_gate_interrupt_settles_forked_group_and_mutating_lifecycle(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_spawn = harness_backend._spawn
    original_capture = harness_backend._capture_process_group
    original_write = os.write
    marker = harness_backend.config.repo_root / "forked-target-started"
    spawned: list[subprocess.Popen[bytes]] = []
    injected = False

    def capture(process: subprocess.Popen[bytes]) -> int:
        spawned.append(process)
        return original_capture(process)

    def release_then_interrupt(descriptor: int, payload: bytes) -> int:
        nonlocal injected
        written = original_write(descriptor, payload)
        if not injected:
            injected = True
            deadline = time.monotonic() + 2
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            raise KeyboardInterrupt("injected after spawn gate release")
        return written

    def spawn_with_interrupted_release(argv: list[str]) -> subprocess.Popen[bytes]:
        monkeypatch.setattr(os, "write", release_then_interrupt)
        try:
            return original_spawn(argv)
        finally:
            monkeypatch.setattr(os, "write", original_write)

    monkeypatch.setattr(harness_backend, "_capture_process_group", capture)
    monkeypatch.setattr(harness_backend, "_spawn", spawn_with_interrupted_release)
    monkeypatch.setattr(
        harness_backend,
        "_argv",
        lambda _operation: [
            sys.executable,
            "-c",
            (
                "import os,signal,sys,time;"
                "from pathlib import Path;"
                "child=os.fork();"
                "(Path(sys.argv[1]).write_text(str(os.getpid())),"
                "signal.signal(signal.SIGTERM,signal.SIG_IGN),time.sleep(30)) "
                "if child == 0 else time.sleep(30)"
            ),
            str(marker),
        ],
    )
    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="START_RECOVERY_REQUIRED",
    ) as recovery:
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.reset,
            execution_ref="execution-ref:matrix-harness:post-gate-interrupt",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert isinstance(recovery.value.__cause__, KeyboardInterrupt)
    assert marker.exists()
    assert len(spawned) == 1
    assert spawned[0].returncode is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(spawned[0].pid, 0)
    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )
    recovered = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(recovered)


def test_process_group_permission_race_requires_group_absence_after_reaping(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExitedDuringSignal:
        pid = 12345

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.exited = False
            self.wait_calls: list[float] = []

        def terminate(self) -> None:
            pytest.fail("owned process group must be signalled")

        def kill(self) -> None:
            pytest.fail("terminal permission race must not require exact kill")

        def wait(self, *, timeout: float) -> int:
            self.wait_calls.append(timeout)
            if not self.exited:
                raise subprocess.TimeoutExpired("semantic-process", timeout)
            self.returncode = 0
            return self.returncode

    process = ExitedDuringSignal()
    signals: list[tuple[int, signal.Signals]] = []

    group_signalable = True

    def permission_race(pid: int, signum: signal.Signals) -> None:
        nonlocal group_signalable
        signals.append((pid, signum))
        if signum == 0 and group_signalable:
            return
        if signum == signal.SIGTERM:
            process.exited = True
            group_signalable = False
            return
        if process.returncode is not None:
            raise ProcessLookupError
        raise PermissionError

    monkeypatch.setattr(os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(os, "killpg", permission_race)
    monkeypatch.setattr(
        harness_backend,
        "_process_group_inventory",
        lambda _process, _group_id: matrix_backend._MatrixHarnessProcessGroupInventory(
            leader_terminal=False,
            live_member_count=0,
            member_count=1,
        ),
    )
    harness_backend._terminate_process_group(process)  # type: ignore[arg-type]

    assert signals == [
        (12345, 0),
        (12345, signal.SIGTERM),
        (12345, 0),
        (12345, 0),
    ]
    assert process.returncode == 0
    assert len(process.wait_calls) == 1
    assert process.wait_calls[0] > 0


def test_process_group_permission_denial_fails_closed_while_child_is_live(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StillLive:
        pid = 12345
        returncode: int | None = None

        def terminate(self) -> None:
            pytest.fail("isolated group must not fall back to exact terminate")

        def kill(self) -> None:
            pytest.fail("isolated group must not fall back to exact kill")

        @staticmethod
        def wait(*, timeout: float) -> int:
            raise subprocess.TimeoutExpired("semantic-process", timeout)

    monkeypatch.setattr(matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0)
    monkeypatch.setattr(
        matrix_backend, "MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS", 0.01
    )

    def deny_group_signal(_pid: int, _signum: signal.Signals) -> None:
        raise PermissionError

    monkeypatch.setattr(os, "killpg", deny_group_signal)
    monkeypatch.setattr(os, "getpgid", lambda pid: pid)

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_TERMINATION_UNCONFIRMED",
    ):
        harness_backend._terminate_process_group(StillLive())  # type: ignore[arg-type]


def test_process_group_capture_deadline_confirms_exact_child_terminal(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnisolatedProcess:
        pid = 12345

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.terminate_calls = 0
            self.kill_calls = 0
            self.wait_calls: list[float] = []

        def terminate(self) -> None:
            self.terminate_calls += 1

        def poll(self) -> None:
            return None

        def kill(self) -> None:
            self.kill_calls += 1

        def wait(self, *, timeout: float) -> int:
            self.wait_calls.append(timeout)
            self.returncode = -signal.SIGTERM
            return self.returncode

    process = UnisolatedProcess()
    monkeypatch.setattr(matrix_backend, "MATRIX_HARNESS_PROCESS_GROUP_READY_SECONDS", 0)
    monkeypatch.setattr(os, "getpgid", lambda _pid: 9000)

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_GROUP_ISOLATION_UNCONFIRMED",
    ):
        harness_backend._capture_process_group(process)  # type: ignore[arg-type]

    assert process.returncode == -signal.SIGTERM
    assert process.terminate_calls == 1
    assert process.kill_calls == 0
    assert process.wait_calls == [
        matrix_backend.MATRIX_HARNESS_PROCESS_KILL_GRACE_SECONDS
    ]


def test_process_group_escalates_term_to_kill_and_proves_absence(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TermResistantProcess:
        pid = 12345

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.wait_calls: list[float] = []

        def terminate(self) -> None:
            pytest.fail("isolated group must not use exact terminate")

        def kill(self) -> None:
            pytest.fail("isolated group must not use exact kill")

        def wait(self, *, timeout: float) -> int:
            self.wait_calls.append(timeout)
            self.returncode = -signal.SIGKILL
            return self.returncode

    process = TermResistantProcess()
    group_absent = False
    signals: list[signal.Signals] = []

    def group_signal(_pid: int, signum: signal.Signals) -> None:
        nonlocal group_absent
        if signum == 0:
            if group_absent:
                raise ProcessLookupError
            return
        signals.append(signum)
        if signum == signal.SIGKILL:
            group_absent = True

    monkeypatch.setattr(matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0)
    monkeypatch.setattr(os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(os, "killpg", group_signal)
    monkeypatch.setattr(
        harness_backend,
        "_process_group_inventory",
        lambda _process, _group_id: matrix_backend._MatrixHarnessProcessGroupInventory(
            leader_terminal=False,
            live_member_count=0,
            member_count=1,
        ),
    )

    harness_backend._terminate_process_group(process)  # type: ignore[arg-type]

    assert signals == [signal.SIGTERM, signal.SIGKILL]
    assert process.returncode == -signal.SIGKILL
    assert len(process.wait_calls) == 1


def test_reaped_leader_never_signals_potentially_reused_process_group(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReapedLeader:
        pid = 12345
        returncode: int | None = 0

        @staticmethod
        def wait(*, timeout: float) -> int:
            assert timeout > 0
            return 0

    signals: list[signal.Signals] = []

    def group_signal(_pid: int, signum: signal.Signals) -> None:
        signals.append(signum)

    process = ReapedLeader()
    monkeypatch.setattr(matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0)
    monkeypatch.setattr(os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(os, "killpg", group_signal)

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_TERMINATION_UNCONFIRMED",
    ):
        harness_backend._terminate_process_group(process)  # type: ignore[arg-type]

    assert signals == [0]


def test_terminal_leader_without_live_descendants_skips_term_grace(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    group_absent = False

    class TerminalLeader:
        pid = 12345

        def __init__(self) -> None:
            self.returncode: int | None = None

        def wait(self, *, timeout: float) -> int:
            nonlocal group_absent
            assert timeout > 0
            self.returncode = 0
            group_absent = True
            return self.returncode

    process = TerminalLeader()
    signals: list[signal.Signals] = []

    def group_signal(_pid: int, signum: signal.Signals) -> None:
        nonlocal group_absent
        signals.append(signum)
        if signum == 0 and group_absent:
            raise ProcessLookupError

    monkeypatch.setattr(
        matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 10.0
    )
    monkeypatch.setattr(os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(os, "killpg", group_signal)
    monkeypatch.setattr(
        harness_backend,
        "_process_group_inventory",
        lambda _process, _group_id: matrix_backend._MatrixHarnessProcessGroupInventory(
            leader_terminal=True,
            live_member_count=0,
            member_count=1,
        ),
    )

    started_at = time.monotonic()
    harness_backend._terminate_process_group(process)  # type: ignore[arg-type]
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.1
    assert process.returncode == 0
    assert signals == [0, 0]


def test_process_group_never_swallows_final_wait_uncertainty(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnsettledExactChild:
        pid = 12345
        returncode: int | None = None

        def terminate(self) -> None:
            pytest.fail("isolated group must not use exact terminate")

        def kill(self) -> None:
            pytest.fail("isolated group must not use exact kill")

        @staticmethod
        def wait(*, timeout: float) -> int:
            raise subprocess.TimeoutExpired("semantic-process", timeout)

    group_absent = False
    signals: list[signal.Signals] = []

    def group_signal(_pid: int, signum: signal.Signals) -> None:
        nonlocal group_absent
        if signum == 0:
            if group_absent:
                raise ProcessLookupError
            return
        signals.append(signum)
        if signum == signal.SIGKILL:
            group_absent = True

    monkeypatch.setattr(matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0)
    monkeypatch.setattr(os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(os, "killpg", group_signal)
    monkeypatch.setattr(
        harness_backend,
        "_process_group_inventory",
        lambda _process, _group_id: matrix_backend._MatrixHarnessProcessGroupInventory(
            leader_terminal=False,
            live_member_count=0,
            member_count=1,
        ),
    )

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_TERMINATION_UNCONFIRMED",
    ):
        harness_backend._terminate_process_group(  # type: ignore[arg-type]
            UnsettledExactChild()
        )

    assert signals == [signal.SIGTERM, signal.SIGKILL]


def test_process_group_cleanup_kills_surviving_descendant(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0.05
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import os,signal,time;"
                "child=os.fork();"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN) "
                "if child == 0 else None;"
                "os.write(1, b'R') if child == 0 else None;"
                "time.sleep(30) if child == 0 else os._exit(0)"
            ),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    process_group_id = harness_backend._capture_process_group(process)
    assert process.stdout is not None
    assert process.stdout.read(1) == b"R"

    harness_backend._terminate_process_group(process)

    assert process.returncode is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(process_group_id, 0)


def test_collect_settles_descendant_after_successful_leader_closes_pipes(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0.05
    )
    monkeypatch.setattr(
        harness_backend,
        "_resource_posture",
        lambda: type(
            "Posture",
            (),
            {
                "ownership_valid": True,
                "container_count": 0,
                "running_container_count": 0,
                "network_count": 0,
                "volume_count": 0,
            },
        )(),
    )
    process = harness_backend._spawn(
        [
            sys.executable,
            "-c",
            (
                "import os,signal,time;"
                "child=os.fork();"
                "(os.close(1),os.close(2),"
                "signal.signal(signal.SIGTERM,signal.SIG_IGN),time.sleep(30)) "
                "if child == 0 else (os.write(1,b'[]'),os._exit(0))"
            ),
        ]
    )
    process_group_id = harness_backend._owned_process_groups[process]

    result = harness_backend._collect(
        operation=MatrixHarnessOperation.inspect,
        execution_ref="execution-ref:matrix-harness:successful-descendant",
        process=process,
    )

    assert result.outcome == MatrixHarnessOperationOutcome.succeeded
    assert process.returncode == 0
    with pytest.raises(ProcessLookupError):
        os.killpg(process_group_id, 0)


def test_run_probe_settles_descendant_after_successful_leader_closes_pipes(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        matrix_backend, "MATRIX_HARNESS_PROCESS_TERM_GRACE_SECONDS", 0.05
    )
    spawned: list[subprocess.Popen[bytes]] = []
    original_spawn = harness_backend._spawn

    def record_spawn(argv: list[str]) -> subprocess.Popen[bytes]:
        process = original_spawn(argv)
        spawned.append(process)
        return process

    monkeypatch.setattr(harness_backend, "_spawn", record_spawn)
    result = harness_backend._run_probe(
        [
            sys.executable,
            "-c",
            (
                "import os,signal,time;"
                "child=os.fork();"
                "(os.close(1),os.close(2),"
                "signal.signal(signal.SIGTERM,signal.SIG_IGN),time.sleep(30)) "
                "if child == 0 else (os.write(1,b'probe-safe'),os._exit(0))"
            ),
        ],
        timeout=5,
    )

    assert result is not None
    assert result.returncode == 0
    assert result.stdout == b"probe-safe"
    assert len(spawned) == 1
    with pytest.raises(ProcessLookupError):
        os.killpg(spawned[0].pid, 0)


def test_run_probe_fails_closed_after_one_completion_cleanup_attempt(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = object()
    cleanup_attempts = 0

    def fail_cleanup(_process: object) -> None:
        nonlocal cleanup_attempts
        cleanup_attempts += 1
        raise MatrixHarnessBackendError(
            "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
        )

    monkeypatch.setattr(harness_backend, "_spawn", lambda _argv: process)
    monkeypatch.setattr(
        harness_backend,
        "_communicate_bounded",
        lambda _process, timeout: (b"safe", b""),
    )
    monkeypatch.setattr(harness_backend, "_terminate_process_group", fail_cleanup)

    with pytest.raises(
        MatrixHarnessBackendError,
        match="PROCESS_TERMINATION_UNCONFIRMED",
    ):
        harness_backend._run_probe(["safe-probe"], timeout=5)
    assert cleanup_attempts == 1


def test_run_probe_setup_failure_closes_pipes_and_settles_group(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spawned: list[subprocess.Popen[bytes]] = []
    original_spawn = harness_backend._spawn

    def record_spawn(argv: list[str]) -> subprocess.Popen[bytes]:
        process = original_spawn(argv)
        spawned.append(process)
        return process

    monkeypatch.setattr(harness_backend, "_spawn", record_spawn)
    monkeypatch.setattr(
        os,
        "set_blocking",
        lambda _descriptor, _blocking: (_ for _ in ()).throw(
            ValueError("injected selector setup failure")
        ),
    )

    with pytest.raises(ValueError, match="selector setup failure"):
        harness_backend._run_probe(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout=5,
        )

    assert len(spawned) == 1
    process = spawned[0]
    assert process.returncode is not None
    assert process.stdout is not None and process.stdout.closed
    assert process.stderr is not None and process.stderr.closed
    with pytest.raises(ProcessLookupError):
        os.killpg(process.pid, 0)


def test_cleanup_failure_persists_recovery_before_releasing_lifecycle_lock(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = harness_backend._acquire_lifecycle_lock()
    harness_backend._write_lifecycle_record(
        harness_backend._lifecycle_record(
            generation=1,
            state=MatrixHarnessRuntimeStatus.starting,
            operation_ref=None,
        )
    )
    termination_attempts = 0

    def fail_termination(_process: object) -> None:
        nonlocal termination_attempts
        termination_attempts += 1
        raise MatrixHarnessBackendError(
            "MATRIX_HARNESS_PROCESS_TERMINATION_UNCONFIRMED"
        )

    monkeypatch.setattr(
        harness_backend,
        "_communicate_bounded",
        lambda _process, timeout: (b"", b""),
    )
    monkeypatch.setattr(harness_backend, "_terminate_process_group", fail_termination)
    handle = MatrixHarnessExecutionHandle(
        backend=harness_backend,
        operation=MatrixHarnessOperation.stop,
        execution_ref="execution-ref:matrix-harness:cleanup-recovery",
        process=object(),  # type: ignore[arg-type]
        commit_validated_at=harness_backend.lifecycle_record().updated_at,
        lifecycle_lock_fd=descriptor,
    )

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="COMPLETION_TERMINATION_UNKNOWN",
    ):
        handle.collect()

    assert termination_attempts == 1
    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )
    recovered = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(recovered)


def test_signal_guard_atomically_defers_repeated_signal_before_first_raise() -> None:
    guard = matrix_backend._MatrixHarnessSignalGuard()

    with pytest.raises(MatrixHarnessSignalInterrupted, match="SIGTERM"):
        guard.handle(signal.SIGTERM, None)

    assert guard.deferred is True
    assert guard.pending_signal == signal.SIGTERM
    guard.handle(signal.SIGHUP, None)
    assert guard.pending_signal == signal.SIGTERM


def test_signal_handler_install_and_restore_windows_are_masked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior_signals: list[int] = []

    def prior_handler(received: int, _frame: object) -> None:
        prior_signals.append(received)

    previous = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, prior_handler)
    original_signal = signal.signal
    install_injected = False
    restore_injected = False

    def inject_during_transition(
        watched_signal: signal.Signals,
        handler: object,
    ) -> object:
        nonlocal install_injected, restore_injected
        result = original_signal(watched_signal, handler)  # type: ignore[arg-type]
        if watched_signal == signal.SIGTERM:
            if not install_injected and handler != prior_handler:
                install_injected = True
                os.kill(os.getpid(), signal.SIGTERM)
            elif install_injected and not restore_injected and handler == prior_handler:
                restore_injected = True
                os.kill(os.getpid(), signal.SIGTERM)
        return result

    monkeypatch.setattr(signal, "signal", inject_during_transition)
    try:
        with matrix_backend._forward_termination_signals(deferred=True) as signal_guard:
            assert install_injected is True
            assert signal_guard.pending_signal == signal.SIGTERM
            signal_guard.pending_signal = None
        assert restore_injected is True
        assert prior_signals == [signal.SIGTERM]
    finally:
        monkeypatch.setattr(signal, "signal", original_signal)
        original_signal(signal.SIGTERM, previous)


def test_dispatcher_signal_owner_is_not_shadowed_by_nested_harness_guard() -> None:
    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="AUTHORITY_DISPATCH_ATOMIC_SIGNAL_INTERRUPTED_SIGTERM",
    ):
        with _AtomicStartTerminationGuard():
            with matrix_backend._forward_termination_signals() as nested:
                assert nested.active is False
                os.kill(os.getpid(), signal.SIGTERM)


def test_signal_interrupt_terminates_child_releases_lock_and_recovers(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = harness_backend._acquire_lifecycle_lock()
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    handle = MatrixHarnessExecutionHandle(
        backend=harness_backend,
        operation=MatrixHarnessOperation.inspect,
        execution_ref="execution-ref:matrix-harness:signal-test",
        process=process,
        commit_validated_at=harness_backend.lifecycle_record().updated_at,
        lifecycle_lock_fd=descriptor,
    )
    original_terminate_and_settle = harness_backend._terminate_and_settle
    repeated_signal_observed = False

    def terminate_after_repeated_signal(
        operation: MatrixHarnessOperation,
        execution_ref: str,
        active_process: subprocess.Popen[bytes],
    ) -> bool:
        nonlocal repeated_signal_observed
        os.kill(os.getpid(), signal.SIGHUP)
        repeated_signal_observed = True
        return original_terminate_and_settle(
            operation,
            execution_ref,
            active_process,
        )

    monkeypatch.setattr(
        harness_backend,
        "_terminate_and_settle",
        terminate_after_repeated_signal,
    )

    def interrupt() -> None:
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGTERM)

    sender = threading.Thread(target=interrupt)
    sender.start()
    with pytest.raises(MatrixHarnessSignalInterrupted, match="SIGTERM"):
        handle.collect()
    sender.join(timeout=2)
    assert repeated_signal_observed is True
    assert process.poll() is not None
    assert process.stdout is not None and process.stdout.closed
    assert process.stderr is not None and process.stderr.closed
    recovered = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(recovered)


def test_start_operation_defers_signal_until_spawned_child_is_owned_and_settled(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_spawn = harness_backend._spawn
    spawned: list[subprocess.Popen[bytes]] = []

    def spawn_then_interrupt(_argv: list[str]) -> subprocess.Popen[bytes]:
        process = original_spawn([sys.executable, "-c", "import time; time.sleep(30)"])
        spawned.append(process)
        os.kill(os.getpid(), signal.SIGTERM)
        return process

    monkeypatch.setattr(harness_backend, "_spawn", spawn_then_interrupt)
    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    monkeypatch.setattr(
        harness_backend,
        "_validate_lifecycle_request",
        lambda **_kwargs: None,
    )
    original_terminate_and_settle = harness_backend._terminate_and_settle
    repeated_signal_observed = False

    def terminate_after_repeated_signal(
        operation: MatrixHarnessOperation,
        execution_ref: str,
        active_process: subprocess.Popen[bytes],
    ) -> bool:
        nonlocal repeated_signal_observed
        os.kill(os.getpid(), signal.SIGHUP)
        repeated_signal_observed = True
        return original_terminate_and_settle(
            operation,
            execution_ref,
            active_process,
        )

    monkeypatch.setattr(
        harness_backend,
        "_terminate_and_settle",
        terminate_after_repeated_signal,
    )
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="START_RECOVERY_REQUIRED",
    ) as recovery:
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.stop,
            execution_ref="execution-ref:matrix-harness:launch-signal",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert isinstance(recovery.value.__cause__, MatrixHarnessSignalInterrupted)
    assert len(spawned) == 1
    assert repeated_signal_observed is True
    assert spawned[0].poll() is not None
    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )
    recovered = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(recovered)


def test_start_handoff_cannot_lose_signal_after_final_pending_check(
    harness_backend: DockerMatrixHarnessBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_spawn = harness_backend._spawn
    spawned: list[subprocess.Popen[bytes]] = []

    def spawn_long_running(_argv: list[str]) -> subprocess.Popen[bytes]:
        process = original_spawn([sys.executable, "-c", "import time; time.sleep(30)"])
        spawned.append(process)
        return process

    monkeypatch.setattr(harness_backend, "_spawn", spawn_long_running)
    monkeypatch.setattr(
        harness_backend,
        "_validate_resource_preconditions",
        lambda _operation: None,
    )
    monkeypatch.setattr(
        harness_backend,
        "_validate_lifecycle_request",
        lambda **_kwargs: None,
    )
    original_raise_if_pending = (
        matrix_backend._MatrixHarnessSignalGuard.raise_if_pending
    )
    pending_checks = 0

    def interrupt_after_final_check(
        guard: matrix_backend._MatrixHarnessSignalGuard,
    ) -> None:
        nonlocal pending_checks
        pending_checks += 1
        original_raise_if_pending(guard)
        if pending_checks == 5:
            os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(
        matrix_backend._MatrixHarnessSignalGuard,
        "raise_if_pending",
        interrupt_after_final_check,
    )
    current = harness_backend.lifecycle_record()

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="MATRIX_HARNESS_START_RECOVERY_REQUIRED",
    ):
        harness_backend.start_operation(
            operation=MatrixHarnessOperation.stop,
            execution_ref="execution-ref:matrix-harness:handoff-signal",
            lifecycle_generation_ref=current.generation_ref,
            expected_state_ref=current.state_ref,
            validate_commit_fence=lambda: ([], current.updated_at),
        )

    assert pending_checks == 6
    assert len(spawned) == 1
    assert spawned[0].poll() is not None
    assert spawned[0].stdout is not None and spawned[0].stdout.closed
    assert spawned[0].stderr is not None and spawned[0].stderr.closed
    assert (
        harness_backend.lifecycle_record().state
        == MatrixHarnessRuntimeStatus.recovery_required
    )
    recovered = harness_backend._acquire_lifecycle_lock()
    harness_backend._release_lifecycle_lock(recovered)


def test_inspect_and_fixture_output_schemas_fail_closed() -> None:
    with pytest.raises(MatrixHarnessBackendError, match="ENTRY_LIMIT_EXCEEDED"):
        _safe_counts(
            MatrixHarnessOperation.inspect,
            json.dumps([{} for _ in range(5)]).encode(),
        )
    with pytest.raises(MatrixHarnessBackendError, match="COUNTS_MISMATCH"):
        _safe_counts(
            MatrixHarnessOperation.fixture_seed,
            b'{"account_count":2,"room_count":3,"event_count":4}',
        )
