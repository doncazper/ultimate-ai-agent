from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from ultimate_ai_agent.core.sandbox_calculation.backend import (
    DockerSealedCalculationBackend,
    SealedCalculationBackendConfig,
    SealedCalculationBackendError,
    SealedCalculationCleanupUnconfirmedError,
    SealedCalculationExecutionHandle,
    discover_local_docker_backend,
)
from ultimate_ai_agent.core.sandbox_calculation.contracts import (
    SealedCalculationRequest,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
SECCOMP_PROFILE = ROOT / "packaging" / "sealed-calculation" / "seccomp.json"


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
