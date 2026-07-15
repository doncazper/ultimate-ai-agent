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

from ultimate_ai_agent.core.communications.matrix_harness.backend import (
    DockerMatrixHarnessBackend,
    MatrixHarnessBackendConfig,
    MatrixHarnessBackendError,
    MatrixHarnessExecutionHandle,
    MatrixHarnessSignalInterrupted,
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
        record.model_copy(update={"ownership_ref": "ownership-ref:matrix-harness:stale"})
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
    process = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(1)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
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
    process = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 70000)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    with pytest.raises(MatrixHarnessBackendError, match="OUTPUT_LIMIT_EXCEEDED"):
        harness_backend._communicate_bounded(process, timeout=5)
    harness_backend._terminate_process_group(process)
    assert process.poll() is not None


def test_signal_interrupt_terminates_child_releases_lock_and_recovers(
    harness_backend: DockerMatrixHarnessBackend,
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

    def interrupt() -> None:
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGTERM)

    sender = threading.Thread(target=interrupt)
    sender.start()
    with pytest.raises(MatrixHarnessSignalInterrupted, match="SIGTERM"):
        handle.collect()
    sender.join(timeout=2)
    assert process.poll() is not None
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
