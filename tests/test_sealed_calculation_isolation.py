from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.sandbox_calculation import backend as backend_module
from ultimate_ai_agent.core.sandbox_calculation.backend import (
    DockerSealedCalculationBackend,
    SealedCalculationBackendConfig,
    SealedCalculationBackendError,
    SealedCalculationCleanupUnconfirmedError,
    SealedCalculationExecutionHandle,
    SealedCalculationExecutionTruthUnknownError,
    discover_local_docker_backend,
)
from ultimate_ai_agent.core.sandbox_calculation.contracts import (
    SealedCalculationRequest,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
SECCOMP_PROFILE = ROOT / "packaging" / "sealed-calculation" / "seccomp.json"


class _InputPipe:
    def __init__(
        self,
        *,
        write_result: int | None = None,
        fail_flush: bool = False,
        fail_close: bool = False,
    ):
        self.write_result = write_result
        self.fail_flush = fail_flush
        self.fail_close = fail_close
        self.closed = False

    def write(self, payload: bytes) -> int:
        return len(payload) if self.write_result is None else self.write_result

    def flush(self) -> None:
        if self.fail_flush:
            raise OSError("injected flush failure")

    def close(self) -> None:
        self.closed = True
        if self.fail_close:
            raise OSError("injected close failure")


class _InputProcess:
    def __init__(self, stdin: _InputPipe | None):
        self.stdin = stdin


def test_abort_closes_process_streams_when_termination_proof_fails() -> None:
    class FailingBackend:
        def _terminate(self, *_args: object) -> None:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_TEST_TERMINATION_UNCONFIRMED"
            )

    class Process:
        def __init__(self) -> None:
            self.stdin = _InputPipe(fail_close=True)
            self.stdout = _InputPipe()
            self.stderr = _InputPipe()

    process = Process()
    request = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:abort-streams",
        input_ref="input-ref:sealed-calculation:abort-streams",
        expression="1 + 1",
        expression_sha256=hash_text("1 + 1"),
    )
    handle = SealedCalculationExecutionHandle(
        backend=FailingBackend(),  # type: ignore[arg-type]
        process=process,  # type: ignore[arg-type]
        container_name="uaa-sealed-calculation-abort-streams",
        execution_ref="execution-ref:sealed-calculation:abort-streams",
        request=request,
        commit_validated_at=utc_now(),
    )

    with pytest.raises(
        SealedCalculationCleanupUnconfirmedError,
        match="TEST_TERMINATION_UNCONFIRMED",
    ):
        handle.abort()

    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_start_handshake_failure_closes_unclaimed_process_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_processes: list[object] = []

    class FakePopen(subprocess.Popen[bytes]):
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.stdin = _InputPipe()
            self.stdout = _InputPipe()
            self.stderr = _InputPipe()
            self.pid = 424242
            self.returncode = 1
            self.args = ["docker", "start"]
            created_processes.append(self)

        def poll(self) -> int:
            return self.returncode

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return self.returncode

    backend = object.__new__(DockerSealedCalculationBackend)
    backend.config = SimpleNamespace(
        docker_binary=Path("/usr/bin/docker"),
        docker_host="unix:///private/docker.sock",
        seccomp_profile=Path("/private/seccomp.json"),
        image_id="sha256:" + ("a" * 64),
    )
    backend._docker_env = {}
    backend.readiness_reason_codes = lambda: []  # type: ignore[method-assign]
    backend._container_name = lambda _execution_ref: "uaa-sealed-calculation-test"  # type: ignore[method-assign]
    backend._docker = lambda *_args, **_kwargs: (_ for _ in ()).throw(  # type: ignore[method-assign]
        SealedCalculationBackendError("SEALED_CALCULATION_NOT_FOUND")
    )
    backend._validate_seccomp_current = lambda: None  # type: ignore[method-assign]
    backend._validate_container_config = lambda *_args: None  # type: ignore[method-assign]
    backend.kill_switch_engaged = lambda: False  # type: ignore[method-assign]
    backend.safe_disabled = lambda: False  # type: ignore[method-assign]
    backend._read_json_frame = lambda *_args: {"frame": "invalid"}  # type: ignore[method-assign]
    backend._remove_owned_container = lambda *_args: None  # type: ignore[method-assign]
    monkeypatch.setattr(
        backend_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="container-id",
            stderr="",
        ),
    )
    monkeypatch.setattr(backend_module.subprocess, "Popen", FakePopen)
    request = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:start-streams",
        input_ref="input-ref:sealed-calculation:start-streams",
        expression="2 + 2",
        expression_sha256=hash_text("2 + 2"),
    )

    with pytest.raises(
        SealedCalculationBackendError,
        match="SEALED_CALCULATION_START_HANDSHAKE_INVALID",
    ):
        backend.start(
            execution_ref="execution-ref:sealed-calculation:start-streams",
            request=request,
            validate_commit_fence=lambda: ([], utc_now()),
        )

    assert len(created_processes) == 1
    process = created_processes[0]
    assert process.stdin.closed is True  # type: ignore[attr-defined]
    assert process.stdout.closed is True  # type: ignore[attr-defined]
    assert process.stderr.closed is True  # type: ignore[attr-defined]


def test_missing_stdin_fails_before_input_commit_truth_becomes_unknown() -> None:
    process = _InputProcess(None)

    with pytest.raises(
        SealedCalculationBackendError,
        match="SEALED_CALCULATION_STDIN_PIPE_REQUIRED",
    ) as exc_info:
        DockerSealedCalculationBackend._commit_input(process, b"{}\n")  # type: ignore[arg-type]  # noqa: SLF001

    assert not isinstance(exc_info.value, SealedCalculationExecutionTruthUnknownError)


@pytest.mark.parametrize(
    "pipe",
    [
        _InputPipe(write_result=1),
        _InputPipe(fail_flush=True),
    ],
)
def test_partial_input_delivery_reports_unknown_execution_truth(
    pipe: _InputPipe,
) -> None:
    process = _InputProcess(pipe)

    with pytest.raises(
        SealedCalculationExecutionTruthUnknownError,
        match="SEALED_CALCULATION_EXECUTION_TRUTH_UNKNOWN",
    ):
        DockerSealedCalculationBackend._commit_input(process, b"{}\n")  # type: ignore[arg-type]  # noqa: SLF001


def test_complete_input_delivery_closes_and_clears_stdin() -> None:
    pipe = _InputPipe()
    process = _InputProcess(pipe)

    DockerSealedCalculationBackend._commit_input(process, b"{}\n")  # type: ignore[arg-type]  # noqa: SLF001

    assert pipe.closed is True
    assert process.stdin is None


def _backend_or_skip():
    try:
        return discover_local_docker_backend(seccomp_profile=SECCOMP_PROFILE)
    except SealedCalculationBackendError as exc:
        if os.environ.get("UAA_REQUIRE_SEALED_BACKEND") == "1":
            pytest.fail(f"required sealed calculation backend unavailable: {exc}")
        pytest.skip(f"sealed calculation image is not configured: {exc}")


def _probe(probe: str) -> dict[str, str]:
    backend = _backend_or_skip()
    limits = backend.config.limits
    command = [
        str(backend.config.docker_binary),
        "--host",
        backend.config.docker_host,
        "run",
        "--rm",
        "--pull",
        "never",
        "--log-driver",
        "none",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,nodev,size={limits.tmpfs_bytes},mode=0700,uid=65532,gid=65532",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--security-opt",
        f"seccomp={backend.config.seccomp_profile}",
        "--pids-limit",
        str(limits.pids_limit),
        "--memory",
        str(limits.memory_bytes),
        "--memory-swap",
        str(limits.memory_bytes),
        "--cpus",
        str(limits.cpu_quota),
        "--ulimit",
        "nofile=32:32",
        "--ulimit",
        "fsize=1048576:1048576",
        "--user",
        "65532:65532",
        "--workdir",
        "/tmp",
        "--entrypoint",
        "/usr/local/bin/python3.13",
        backend.config.image_id,
        "-I",
        "-S",
        "/opt/uaa-sealed-calculation/isolation_probe.py",
        probe,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
        timeout=10,
    )
    assert len(completed.stdout) <= 256
    assert len(completed.stderr) <= 1024
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


@pytest.mark.parametrize(
    "probe",
    [
        "network_ipv4",
        "network_ipv6",
        "network_unix",
        "host_home",
        "host_private",
        "root_write",
        "subprocess",
        "environment",
        "shell_binary",
        "package_manager",
        "launcher_inventory",
        "credential_paths",
    ],
)
def test_exact_container_profile_denies_escape_surfaces(probe: str) -> None:
    assert _probe(probe) == {"probe": probe, "status": "denied"}


def test_exact_container_profile_allows_only_bounded_ephemeral_tmp_write() -> None:
    assert _probe("tmp_write") == {"probe": "tmp_write", "status": "allowed"}


def test_container_validation_accepts_only_the_exact_tmpfs_mount_shape() -> None:
    exact_tmpfs = {
        "Type": "tmpfs",
        "Source": "",
        "Destination": "/tmp",
        "Mode": "",
        "RW": True,
        "Propagation": "",
    }

    assert DockerSealedCalculationBackend._is_exact_tmpfs_mount(exact_tmpfs) is True
    assert (
        DockerSealedCalculationBackend._is_exact_tmpfs_mount(
            {**exact_tmpfs, "Type": "bind", "Source": "safe-location-marker"}
        )
        is False
    )
    assert (
        DockerSealedCalculationBackend._is_exact_tmpfs_mount(
            {**exact_tmpfs, "Destination": "/workspace"}
        )
        is False
    )


def test_transient_payload_validation_finishes_before_commit_attempt() -> None:
    expression = "\\" * 512
    request = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:payload-limit",
        input_ref="input-ref:sealed-calculation:payload-limit",
        expression=expression,
        expression_sha256=hash_text(expression),
    )

    with pytest.raises(
        SealedCalculationBackendError,
        match="SEALED_CALCULATION_TRANSIENT_INPUT_SIZE_EXCEEDED",
    ):
        DockerSealedCalculationBackend._validated_input_payload(request)


def test_backend_discovery_normalizes_missing_docker_binary(monkeypatch) -> None:
    original_resolve = Path.resolve

    def missing_docker(path: Path, *, strict: bool = False) -> Path:
        if path == Path("/usr/local/bin/docker"):
            raise FileNotFoundError("docker unavailable")
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(backend_module.Path, "resolve", missing_docker)

    with pytest.raises(
        SealedCalculationBackendError,
        match="SEALED_CALCULATION_LOCAL_BACKEND_NOT_CONFIGURED",
    ):
        discover_local_docker_backend(seccomp_profile=SECCOMP_PROFILE)


def test_backend_attestation_binds_image_runner_profile_and_limits() -> None:
    backend = _backend_or_skip()

    assert backend.readiness_reason_codes() == []
    assert backend.attestation.image_id_ref.endswith(
        backend.config.image_id.removeprefix("sha256:")
    )
    assert backend.attestation.runner_source_ref.startswith("runner-source-ref:sha256:")
    assert backend.attestation.seccomp_profile_ref.startswith(
        "seccomp-profile-ref:sha256:"
    )
    assert backend.attestation.no_host_mounts is True
    assert backend.attestation.network_disabled is True
    assert backend.attestation.read_only_root is True
    assert backend.attestation.one_process_limit is True


def test_runner_source_drift_blocks_current_image(tmp_path: Path) -> None:
    backend = _backend_or_skip()
    changed_runner = tmp_path / "runner.py"
    changed_runner.write_bytes(
        backend.config.runner_source.read_bytes() + b"\n# reviewed drift probe\n"
    )
    drifted = DockerSealedCalculationBackend(
        SealedCalculationBackendConfig(
            docker_binary=backend.config.docker_binary,
            docker_host=backend.config.docker_host,
            image_id=backend.config.image_id,
            seccomp_profile=backend.config.seccomp_profile,
            runner_source=changed_runner,
            isolation_probe_source=backend.config.isolation_probe_source,
        )
    )

    assert "SEALED_CALCULATION_IMAGE_SOURCE_BINDING_DRIFT" in (
        drifted.readiness_reason_codes()
    )


def test_symlinked_seccomp_profile_is_rejected(tmp_path: Path) -> None:
    backend = _backend_or_skip()
    linked_profile = tmp_path / "seccomp.json"
    linked_profile.symlink_to(backend.config.seccomp_profile)

    with pytest.raises(ValueError, match="SECCOMP_PROFILE_UNAVAILABLE"):
        DockerSealedCalculationBackend(
            SealedCalculationBackendConfig(
                docker_binary=backend.config.docker_binary,
                docker_host=backend.config.docker_host,
                image_id=backend.config.image_id,
                seccomp_profile=linked_profile,
                runner_source=backend.config.runner_source,
                isolation_probe_source=backend.config.isolation_probe_source,
            )
        )


def test_seccomp_profile_drift_blocks_container_create(tmp_path: Path) -> None:
    backend = _backend_or_skip()
    copied_profile = tmp_path / "seccomp.json"
    copied_profile.write_bytes(backend.config.seccomp_profile.read_bytes())
    drifted = DockerSealedCalculationBackend(
        SealedCalculationBackendConfig(
            docker_binary=backend.config.docker_binary,
            docker_host=backend.config.docker_host,
            image_id=backend.config.image_id,
            seccomp_profile=copied_profile,
            runner_source=backend.config.runner_source,
            isolation_probe_source=backend.config.isolation_probe_source,
        )
    )
    copied_profile.write_bytes(copied_profile.read_bytes() + b"\n")
    expression = "1 + 1"

    with pytest.raises(SealedCalculationBackendError, match="SECCOMP_PROFILE_DRIFT"):
        drifted.start(
            execution_ref="execution-ref:sealed-calculation:seccomp-drift",
            request=SealedCalculationRequest(
                request_ref="request-ref:sealed-calculation:seccomp-drift",
                input_ref="input-ref:sealed-calculation:seccomp-drift",
                expression=expression,
                expression_sha256=hash_text(expression),
            ),
            validate_commit_fence=lambda: ([], utc_now()),
        )

    assert drifted.list_orphan_refs() == []


@pytest.mark.parametrize(
    "response",
    [
        {
            "schema_version": "uaa-sealed-calculation-runner.v1",
            "status": "succeeded",
            "expression_sha256": hash_text("1 + 1"),
            "output_sha256": hash_text("2"),
            "result": "2",
            "safe_summary": "Safe bounded result.",
            "extra": "smuggled",
        },
        {
            "schema_version": "uaa-sealed-calculation-runner.v1",
            "status": "succeeded",
            "expression_sha256": hash_text("1 + 1"),
            "output_sha256": hash_text("/private/unsafe"),
            "result": "/private/unsafe",
            "safe_summary": "Safe bounded result.",
        },
    ],
)
def test_backend_rejects_extra_fields_and_non_numeric_result_smuggling(
    monkeypatch,
    response: dict[str, str],
) -> None:
    backend = _backend_or_skip()
    request = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:result-contract",
        input_ref="input-ref:sealed-calculation:result-contract",
        expression="1 + 1",
        expression_sha256=hash_text("1 + 1"),
    )

    class CompletedProcess:
        returncode = 0
        stdin = None
        stdout = None
        stderr = None

    monkeypatch.setattr(
        backend,
        "_bounded_collect",
        lambda *_args, **_kwargs: (json.dumps(response).encode("ascii"), b""),
    )
    monkeypatch.setattr(backend, "_remove_owned_container", lambda *_args: None)
    handle = SealedCalculationExecutionHandle(
        backend=backend,
        process=CompletedProcess(),  # type: ignore[arg-type]
        container_name="uaa-sealed-calculation-contract-test",
        execution_ref="execution-ref:sealed-calculation:result-contract",
        request=request,
        commit_validated_at=utc_now(),
    )

    result = handle.collect()

    assert result.status.value == "failed"
    assert result.reason_codes == ["SEALED_CALCULATION_RESULT_BINDING_INVALID"]


def test_orphan_inspection_failure_is_never_reported_as_clean(monkeypatch) -> None:
    backend = _backend_or_skip()

    def unavailable(*_args, **_kwargs):
        raise SealedCalculationBackendError("SEALED_CALCULATION_DOCKER_UNAVAILABLE")

    monkeypatch.setattr(backend, "_docker", unavailable)

    with pytest.raises(
        SealedCalculationCleanupUnconfirmedError,
        match="ORPHAN_INSPECTION_UNCONFIRMED",
    ):
        backend.list_orphan_refs()


def test_ambiguous_create_timeout_requires_exact_container_inspection(
    monkeypatch,
) -> None:
    backend = _backend_or_skip()
    inspected_names: list[str] = []
    monkeypatch.setattr(backend, "readiness_reason_codes", lambda: [])

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("docker-create", 1.0)

    def inspect_absence(container_name: str):
        inspected_names.append(container_name)
        return None

    monkeypatch.setattr(subprocess, "run", timeout)
    monkeypatch.setattr(backend, "_inspect_container_or_none", inspect_absence)
    expression = "4 + 4"

    with pytest.raises(subprocess.TimeoutExpired):
        backend.start(
            execution_ref="execution-ref:sealed-calculation:create-timeout",
            request=SealedCalculationRequest(
                request_ref="request-ref:sealed-calculation:create-timeout",
                input_ref="input-ref:sealed-calculation:create-timeout",
                expression=expression,
                expression_sha256=hash_text(expression),
            ),
            validate_commit_fence=lambda: ([], utc_now()),
        )

    assert inspected_names == [
        backend._container_name(  # noqa: SLF001
            "execution-ref:sealed-calculation:create-timeout"
        )
    ]
