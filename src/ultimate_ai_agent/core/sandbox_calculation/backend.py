from __future__ import annotations

import json
import hashlib
import os
import platform
import pwd
import re
import selectors
import signal
import stat
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar

from ultimate_ai_agent.core.safe_refs import hash_bytes, hash_text

from .contracts import (
    SEALED_CALCULATION_RECEIPT_CONTRACT_REF,
    SealedCalculationBackendAttestation,
    SealedCalculationLimits,
    SealedCalculationRequest,
    SealedCalculationResult,
    SealedCalculationStatus,
)


RUNNER_CONTRACT_REF = "runner-contract-ref:sealed-calculation-ast-v1"
GRAMMAR_POLICY_REF = "grammar-policy-ref:sealed-arithmetic-v1"
BACKEND_REF = "backend-ref:docker-desktop-sealed-calculation-v1"
PLATFORM_REF = "platform-ref:macos-docker-desktop-linux-vm"
CONTAINER_LABEL = "com.ultimate-ai-agent.sealed-calculation=v1"
CONTAINER_NAME_PREFIX = "uaa-sealed-calculation-"
BASE_IMAGE_REF = (
    "python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
)
SAFE_NUMERIC_RESULT_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?\Z")
SAFE_REASON_CODE_RE = re.compile(r"[A-Z][A-Z0-9_]{1,95}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class SealedCalculationBackendError(RuntimeError):
    pass


class SealedCalculationOutputLimitError(SealedCalculationBackendError):
    pass


class SealedCalculationKillSwitchError(SealedCalculationBackendError):
    pass


class SealedCalculationCleanupUnconfirmedError(SealedCalculationBackendError):
    pass


class SealedCalculationExecutionTruthUnknownError(SealedCalculationBackendError):
    pass


CommitFenceValidator = Callable[[], tuple[list[str], datetime]]
_ClaimedHandleT = TypeVar("_ClaimedHandleT")


@dataclass(frozen=True)
class SealedCalculationBackendConfig:
    docker_binary: Path
    docker_host: str
    image_id: str
    seccomp_profile: Path
    runner_source: Path
    isolation_probe_source: Path
    limits: SealedCalculationLimits = field(default_factory=SealedCalculationLimits)

    def __post_init__(self) -> None:
        if not self.docker_binary.is_absolute():
            raise ValueError("SEALED_CALCULATION_DOCKER_BINARY_ABSOLUTE_REQUIRED")
        if not self.docker_host.startswith("unix://"):
            raise ValueError("SEALED_CALCULATION_LOCAL_DOCKER_HOST_REQUIRED")
        socket_path = Path(self.docker_host.removeprefix("unix://"))
        local_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        expected_socket = local_home / ".docker" / "run" / "docker.sock"
        try:
            socket_stat = os.lstat(socket_path)
        except OSError as exc:
            raise ValueError("SEALED_CALCULATION_DOCKER_SOCKET_UNAVAILABLE") from exc
        if (
            socket_path != expected_socket
            or not socket_path.is_absolute()
            or not stat.S_ISSOCK(socket_stat.st_mode)
            or stat.S_ISLNK(socket_stat.st_mode)
            or socket_stat.st_uid != os.getuid()
            or socket_stat.st_mode & 0o022
        ):
            raise ValueError("SEALED_CALCULATION_DOCKER_SOCKET_UNTRUSTED")
        if not self.image_id.startswith("sha256:") or len(self.image_id) != 71:
            raise ValueError("SEALED_CALCULATION_EXACT_IMAGE_ID_REQUIRED")
        if not self.seccomp_profile.is_absolute():
            raise ValueError("SEALED_CALCULATION_SECCOMP_PATH_ABSOLUTE_REQUIRED")
        if not self.runner_source.is_absolute():
            raise ValueError("SEALED_CALCULATION_RUNNER_PATH_ABSOLUTE_REQUIRED")
        if not self.isolation_probe_source.is_absolute():
            raise ValueError("SEALED_CALCULATION_PROBE_PATH_ABSOLUTE_REQUIRED")


@dataclass(frozen=True)
class _CommittedCalculationRequest:
    """Content-free request metadata retained after stdin commitment."""

    request_ref: str
    input_ref: str
    expression_sha256: str
    limits: SealedCalculationLimits

    @classmethod
    def from_request(
        cls,
        request: SealedCalculationRequest,
    ) -> "_CommittedCalculationRequest":
        return cls(
            request_ref=request.request_ref,
            input_ref=request.input_ref,
            expression_sha256=request.expression_sha256,
            limits=request.limits.model_copy(deep=True),
        )


class TransientCalculationInputStore:
    def __init__(self) -> None:
        self._inputs: dict[str, SealedCalculationRequest] = {}
        self._lock = threading.RLock()

    def put(self, request: SealedCalculationRequest) -> None:
        validated = request.model_copy(deep=True)
        with self._lock:
            existing = self._inputs.get(validated.input_ref)
            if existing is not None and existing != validated:
                raise ValueError("SEALED_CALCULATION_TRANSIENT_INPUT_CONFLICT")
            self._inputs[validated.input_ref] = validated

    def get(self, input_ref: str) -> SealedCalculationRequest | None:
        with self._lock:
            item = self._inputs.get(input_ref)
            return item.model_copy(deep=True) if item is not None else None

    def discard(self, input_ref: str) -> None:
        with self._lock:
            self._inputs.pop(input_ref, None)


class SealedCalculationExecutionHandle:
    def __init__(
        self,
        *,
        backend: "DockerSealedCalculationBackend",
        process: subprocess.Popen[bytes],
        container_name: str,
        execution_ref: str,
        request: SealedCalculationRequest,
        commit_validated_at: datetime,
    ) -> None:
        self._backend = backend
        self._process = process
        self._container_name = container_name
        self._execution_ref = execution_ref
        self._request = _CommittedCalculationRequest.from_request(request)
        self.commit_validated_at = commit_validated_at
        self._collected = False
        self._runtime_settled = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    @property
    def execution_ref(self) -> str:
        return self._execution_ref

    def _close_process_streams(self) -> None:
        first_error: BaseException | None = None
        for stream in (
            self._process.stdin,
            self._process.stdout,
            self._process.stderr,
        ):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except BaseException as exc:
                    first_error = first_error or exc
        if first_error is not None:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_PROCESS_STREAM_CLEANUP_UNCONFIRMED"
            ) from first_error

    def abort(self) -> None:
        if self._settled:
            return
        self._collected = True
        if self._runtime_settled:
            self._settled = True
            return
        cleanup_error: BaseException | None = None
        try:
            self._backend._terminate(
                self._process,
                self._container_name,
                self._execution_ref,
            )
            if self._process.poll() is None:
                raise SealedCalculationCleanupUnconfirmedError(
                    "SEALED_CALCULATION_PROCESS_REAP_UNCONFIRMED"
                )
        except BaseException as exc:
            cleanup_error = exc
        try:
            self._close_process_streams()
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise cleanup_error
        self._runtime_settled = True
        self._settled = True

    def collect(self) -> SealedCalculationResult:
        if self._collected:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_HANDLE_ALREADY_COLLECTED"
            )
        self._collected = True
        try:
            result = self._collect_result()
        except BaseException as original:
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except BaseException as cleanup_error:
                raise cleanup_error from original
            raise
        self._close_process_streams()
        self._runtime_settled = True
        return result

    def finalize(self) -> None:
        if (
            self._settled
            or self._finalized
            or not self._runtime_settled
            or not self._collected
        ):
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_FINALIZATION_INVALID"
            )
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise SealedCalculationBackendError("SEALED_CALCULATION_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise SealedCalculationBackendError("SEALED_CALCULATION_SETTLEMENT_INVALID")
        self._settled = True

    def _collect_result(self) -> SealedCalculationResult:
        if self._backend.kill_switch_engaged():
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except SealedCalculationCleanupUnconfirmedError:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.recovery_required,
                    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
                )
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.killed,
                "SEALED_CALCULATION_KILL_SWITCH_ENGAGED",
            )
        try:
            stdout, stderr = self._backend._bounded_collect(
                self._process,
                stdout_limit=self._request.limits.stdout_limit_bytes,
                stderr_limit=self._request.limits.stderr_limit_bytes,
                timeout=self._request.limits.wall_time_seconds,
            )
        except subprocess.TimeoutExpired:
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except SealedCalculationCleanupUnconfirmedError:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.recovery_required,
                    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
                )
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.timed_out,
                "SEALED_CALCULATION_WALL_TIME_EXCEEDED",
            )
        except SealedCalculationOutputLimitError:
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except SealedCalculationCleanupUnconfirmedError:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.recovery_required,
                    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
                )
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.output_limit_exceeded,
                "SEALED_CALCULATION_OUTPUT_LIMIT_EXCEEDED",
            )
        except SealedCalculationKillSwitchError:
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except SealedCalculationCleanupUnconfirmedError:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.recovery_required,
                    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
                )
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.killed,
                "SEALED_CALCULATION_RUNTIME_FENCE_ENGAGED",
            )
        except Exception:
            try:
                self._backend._terminate(
                    self._process,
                    self._container_name,
                    self._execution_ref,
                )
            except SealedCalculationCleanupUnconfirmedError:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.recovery_required,
                    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
                )
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.recovery_required,
                "SEALED_CALCULATION_COLLECTION_TRUTH_UNKNOWN",
            )
        try:
            self._backend._remove_owned_container(
                self._container_name,
                self._execution_ref,
            )
        except SealedCalculationCleanupUnconfirmedError:
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.recovery_required,
                "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
            )
        try:
            response = json.loads(stdout.decode("ascii"))
        except (UnicodeError, json.JSONDecodeError):
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.failed,
                "SEALED_CALCULATION_RESULT_INVALID",
            )
        if (
            not isinstance(response, dict)
            or response.get("schema_version") != "uaa-sealed-calculation-runner.v1"
            or stderr != b""
        ):
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.failed,
                "SEALED_CALCULATION_RESULT_CONTRACT_INVALID",
            )
        if response.get("status") != "succeeded" or self._process.returncode != 0:
            if set(response) != {
                "schema_version",
                "status",
                "reason_code",
                "safe_summary",
            }:
                return self._backend._failure_result(
                    self._execution_ref,
                    self._request,
                    SealedCalculationStatus.failed,
                    "SEALED_CALCULATION_RESULT_CONTRACT_INVALID",
                )
            reason = response.get("reason_code")
            if (
                not isinstance(reason, str)
                or SAFE_REASON_CODE_RE.fullmatch(reason) is None
            ):
                reason = "SEALED_CALCULATION_INPUT_DENIED"
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.denied,
                reason,
            )
        result_preview = response.get("result")
        output_sha256 = response.get("output_sha256")
        expression_sha256 = response.get("expression_sha256")
        if (
            set(response)
            != {
                "schema_version",
                "status",
                "expression_sha256",
                "output_sha256",
                "result",
                "safe_summary",
            }
            or not isinstance(result_preview, str)
            or len(result_preview) > 128
            or SAFE_NUMERIC_RESULT_RE.fullmatch(result_preview) is None
            or not isinstance(output_sha256, str)
            or SHA256_RE.fullmatch(output_sha256) is None
            or output_sha256 != hash_text(result_preview)
            or not isinstance(expression_sha256, str)
            or SHA256_RE.fullmatch(expression_sha256) is None
            or expression_sha256 != self._request.expression_sha256
        ):
            return self._backend._failure_result(
                self._execution_ref,
                self._request,
                SealedCalculationStatus.failed,
                "SEALED_CALCULATION_RESULT_BINDING_INVALID",
            )
        return SealedCalculationResult(
            execution_ref=self._execution_ref,
            request_ref=self._request.request_ref,
            input_ref=self._request.input_ref,
            status=SealedCalculationStatus.succeeded,
            expression_sha256=self._request.expression_sha256,
            output_sha256=output_sha256,
            result_preview=result_preview,
            evidence_refs=self._backend._evidence_refs(
                self._execution_ref, output_sha256
            ),
            receipt_ref=self._backend._receipt_ref(self._execution_ref),
            attestation_ref=self._backend.attestation.attestation_ref,
            safe_summary="Sealed deterministic calculation completed with bounded numeric evidence.",
        )


class DockerSealedCalculationBackend:
    def __init__(
        self,
        config: SealedCalculationBackendConfig,
        *,
        kill_switch: Callable[[], bool] = lambda: False,
        safe_disabled: Callable[[], bool] = lambda: False,
    ) -> None:
        self.config = config
        self._kill_switch = kill_switch
        self._safe_disabled = safe_disabled
        self._docker_env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
        self._validate_local_files()
        profile_bytes, profile_identity = self._read_validated_seccomp_profile()
        self._seccomp_hash = hash_bytes(profile_bytes)
        self._seccomp_identity = profile_identity
        self.attestation = self._build_attestation()

    def kill_switch_engaged(self) -> bool:
        try:
            return bool(self._kill_switch())
        except Exception:
            return True

    def safe_disabled(self) -> bool:
        try:
            return bool(self._safe_disabled())
        except Exception:
            return True

    def readiness_reason_codes(self) -> list[str]:
        reasons: list[str] = []
        if platform.system() != "Darwin":
            reasons.append("SEALED_CALCULATION_MACOS_REQUIRED")
        if self.kill_switch_engaged():
            reasons.append("SEALED_CALCULATION_KILL_SWITCH_ENGAGED")
        if self.safe_disabled():
            reasons.append("SEALED_CALCULATION_SAFE_DISABLED")
        try:
            self._validate_seccomp_current()
        except SealedCalculationBackendError:
            reasons.append("SEALED_CALCULATION_SECCOMP_PROFILE_DRIFT")
        try:
            current_docker_cli_ref = (
                f"docker-cli-ref:sha256:{_hash_file(self.config.docker_binary)}"
            )
        except OSError:
            current_docker_cli_ref = "docker-cli-ref:unavailable"
        if current_docker_cli_ref != self.attestation.docker_cli_ref:
            reasons.append("SEALED_CALCULATION_DOCKER_CLI_DRIFT")
        try:
            daemon_payload = self._inspect_daemon_payload()
        except SealedCalculationBackendError:
            reasons.append("SEALED_CALCULATION_DOCKER_DAEMON_UNAVAILABLE")
        else:
            security_options = daemon_payload.get("SecurityOptions") or []
            if (
                daemon_payload.get("OSType") != "linux"
                or daemon_payload.get("CgroupVersion") != "2"
                or not any("seccomp" in str(value) for value in security_options)
            ):
                reasons.append("SEALED_CALCULATION_DAEMON_ISOLATION_UNSUPPORTED")
            if self._daemon_ref(daemon_payload) != self.attestation.docker_daemon_ref:
                reasons.append("SEALED_CALCULATION_DOCKER_DAEMON_DRIFT")
        try:
            inspection = self._docker(
                ["image", "inspect", self.config.image_id, "--format", "{{json .}}"],
                timeout=5.0,
            )
        except SealedCalculationBackendError:
            reasons.append("SEALED_CALCULATION_IMAGE_UNAVAILABLE")
        else:
            try:
                payload = json.loads(inspection.stdout)
            except json.JSONDecodeError:
                reasons.append("SEALED_CALCULATION_IMAGE_INSPECTION_INVALID")
                payload = {}
            if payload.get("Id") != self.config.image_id:
                reasons.append("SEALED_CALCULATION_IMAGE_ID_DRIFT")
            labels = (payload.get("Config") or {}).get("Labels") or {}
            expected_labels = self._expected_image_labels()
            if any(labels.get(key) != value for key, value in expected_labels.items()):
                reasons.append("SEALED_CALCULATION_IMAGE_SOURCE_BINDING_DRIFT")
        return list(dict.fromkeys(reasons))

    def start(
        self,
        *,
        execution_ref: str,
        request: SealedCalculationRequest,
        validate_commit_fence: CommitFenceValidator,
        claim_handle: Callable[[SealedCalculationExecutionHandle], _ClaimedHandleT]
        | None = None,
    ) -> SealedCalculationExecutionHandle | _ClaimedHandleT:
        reasons = self.readiness_reason_codes()
        if reasons:
            raise SealedCalculationBackendError(reasons[0])
        container_name = self._container_name(execution_ref)
        try:
            self._docker(
                ["container", "inspect", container_name, "--format", "{{.Id}}"],
                timeout=3.0,
            )
        except SealedCalculationBackendError:
            pass
        else:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_CONTAINER_NAME_CONFLICT"
            )
        self._validate_seccomp_current()
        create_command = [
            str(self.config.docker_binary),
            "--host",
            self.config.docker_host,
            "create",
            "--interactive",
            "--rm",
            "--pull",
            "never",
            "--name",
            container_name,
            "--label",
            CONTAINER_LABEL,
            "--label",
            f"com.ultimate-ai-agent.execution={hash_text(execution_ref)[:24]}",
            "--log-driver",
            "none",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,nodev,size={request.limits.tmpfs_bytes},mode=0700,uid=65532,gid=65532",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--security-opt",
            f"seccomp={self.config.seccomp_profile}",
            "--pids-limit",
            str(request.limits.pids_limit),
            "--memory",
            str(request.limits.memory_bytes),
            "--memory-swap",
            str(request.limits.memory_bytes),
            "--cpus",
            str(request.limits.cpu_quota),
            "--ulimit",
            "nofile=32:32",
            "--ulimit",
            "fsize=1048576:1048576",
            "--user",
            "65532:65532",
            "--workdir",
            "/tmp",
            self.config.image_id,
        ]
        container_created = False
        input_committed = False
        try:
            created = subprocess.run(
                create_command,
                check=False,
                text=True,
                capture_output=True,
                env=self._docker_env,
                timeout=request.limits.startup_time_seconds,
            )
            container_created = created.returncode == 0
            if (
                created.returncode != 0
                or len(created.stdout) > 256
                or len(created.stderr) > 1024
            ):
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_CONTAINER_CREATE_FAILED"
                )
            self._validate_container_config(container_name, request.limits)
            if self.kill_switch_engaged() or self.safe_disabled():
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_START_FENCE_DENIED"
                )
            process = subprocess.Popen(
                [
                    str(self.config.docker_binary),
                    "--host",
                    self.config.docker_host,
                    "start",
                    "--attach",
                    "--interactive",
                    container_name,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self._docker_env,
                start_new_session=True,
            )
            ready = self._read_json_frame(
                process,
                request.limits.startup_time_seconds,
            )
            if ready != {
                "frame": "ready",
                "grammar_policy_ref": GRAMMAR_POLICY_REF,
                "protocol": "uaa-sealed-calculation-runner.v1",
                "runner_contract_ref": RUNNER_CONTRACT_REF,
            }:
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_START_HANDSHAKE_INVALID"
                )
            if self.kill_switch_engaged() or self.safe_disabled():
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_START_FENCE_DENIED"
                )
            self._validate_seccomp_current()
            commit_reasons, commit_validated_at = validate_commit_fence()
            if commit_reasons:
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_COMMIT_AUTHORITY_FENCE_DENIED"
                )
            if self.kill_switch_engaged() or self.safe_disabled():
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_START_FENCE_DENIED"
                )
            input_payload = self._validated_input_payload(request)
            self._commit_input(process, input_payload)
            input_committed = True
            accepted = self._read_json_frame(
                process,
                request.limits.startup_time_seconds,
            )
            if accepted != {
                "expression_sha256": request.expression_sha256,
                "frame": "input_accepted",
                "protocol": "uaa-sealed-calculation-runner.v1",
            }:
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_INPUT_ACCEPTANCE_INVALID"
                )
            handle = SealedCalculationExecutionHandle(
                backend=self,
                process=process,
                container_name=container_name,
                execution_ref=execution_ref,
                request=request,
                commit_validated_at=commit_validated_at,
            )
            return claim_handle(handle) if claim_handle is not None else handle
        except BaseException as original_error:
            active_process = locals().get("process")
            if isinstance(active_process, subprocess.Popen):
                self._terminate(active_process, container_name, execution_ref)
            elif container_created:
                self._remove_owned_container(container_name, execution_ref)
            else:
                ambiguous_container = self._inspect_container_or_none(container_name)
                if ambiguous_container is not None:
                    self._remove_owned_container(container_name, execution_ref)
            if isinstance(original_error, SealedCalculationExecutionTruthUnknownError):
                raise
            if input_committed:
                raise SealedCalculationExecutionTruthUnknownError(
                    "SEALED_CALCULATION_EXECUTION_TRUTH_UNKNOWN"
                ) from original_error
            raise

    def list_orphan_refs(self) -> list[str]:
        try:
            result = self._docker(
                [
                    "ps",
                    "--all",
                    "--filter",
                    f"label={CONTAINER_LABEL}",
                    "--format",
                    "{{.Names}}",
                ],
                timeout=5.0,
            )
        except SealedCalculationBackendError as exc:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_ORPHAN_INSPECTION_UNCONFIRMED"
            ) from exc
        orphan_refs: list[str] = []
        for name in result.stdout.splitlines():
            if name.startswith(CONTAINER_NAME_PREFIX):
                orphan_refs.append(f"container-ref:sha256:{hash_text(name)}")
        return orphan_refs

    def _validate_local_files(self) -> None:
        if (
            not self.config.docker_binary.is_file()
            or self.config.docker_binary.is_symlink()
            or not os.access(self.config.docker_binary, os.X_OK)
        ):
            raise ValueError("SEALED_CALCULATION_DOCKER_BINARY_UNAVAILABLE")
        if (
            not self.config.seccomp_profile.is_file()
            or self.config.seccomp_profile.is_symlink()
        ):
            raise ValueError("SEALED_CALCULATION_SECCOMP_PROFILE_UNAVAILABLE")
        if (
            not self.config.runner_source.is_file()
            or self.config.runner_source.is_symlink()
        ):
            raise ValueError("SEALED_CALCULATION_RUNNER_SOURCE_UNAVAILABLE")
        if (
            not self.config.isolation_probe_source.is_file()
            or self.config.isolation_probe_source.is_symlink()
        ):
            raise ValueError("SEALED_CALCULATION_PROBE_SOURCE_UNAVAILABLE")
        try:
            self._read_validated_seccomp_profile()
        except SealedCalculationBackendError as exc:
            raise ValueError("SEALED_CALCULATION_SECCOMP_PROFILE_INVALID") from exc

    def _read_validated_seccomp_profile(
        self,
    ) -> tuple[bytes, tuple[int, int, int, int]]:
        try:
            profile_bytes, identity = _read_regular_file_no_follow(
                self.config.seccomp_profile,
                max_bytes=64 * 1024,
            )
            payload = json.loads(profile_bytes.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_SECCOMP_PROFILE_INVALID"
            ) from exc
        if payload.get("defaultAction") != "SCMP_ACT_ERRNO":
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_SECCOMP_PROFILE_UNEXPECTED"
            )
        allowed = {
            name
            for group in payload.get("syscalls", [])
            if isinstance(group, dict) and group.get("action") == "SCMP_ACT_ALLOW"
            for name in group.get("names", [])
            if isinstance(name, str)
        }
        if not {"read", "write", "exit", "exit_group"}.issubset(allowed) or {
            "socket",
            "connect",
            "mount",
            "ptrace",
            "bpf",
            "clone",
            "clone3",
            "fork",
            "vfork",
        }.intersection(allowed):
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_SECCOMP_DENIALS_INCOMPLETE"
            )
        return profile_bytes, identity

    def _validate_seccomp_current(self) -> None:
        profile_bytes, identity = self._read_validated_seccomp_profile()
        if (
            hash_bytes(profile_bytes) != self._seccomp_hash
            or identity != self._seccomp_identity
        ):
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_SECCOMP_PROFILE_DRIFT"
            )

    def _build_attestation(self) -> SealedCalculationBackendAttestation:
        profile_hash = self._seccomp_hash
        runner_hash = hash_bytes(self.config.runner_source.read_bytes())
        docker_cli_hash = _hash_file(self.config.docker_binary)
        daemon_ref = self._daemon_ref(self._inspect_daemon_payload())
        limits_payload = self.config.limits.model_dump(mode="json")
        limits_ref = f"limits-ref:sealed-calculation:sha256:{hash_text(json.dumps(limits_payload, sort_keys=True, separators=(',', ':')))}"
        image_digest = self.config.image_id.removeprefix("sha256:")
        payload = {
            "image_id": self.config.image_id,
            "profile_hash": profile_hash,
            "runner_hash": runner_hash,
            "docker_cli_hash": docker_cli_hash,
            "docker_daemon_ref": daemon_ref,
            "limits": limits_payload,
            "backend_ref": BACKEND_REF,
        }
        return SealedCalculationBackendAttestation(
            attestation_ref=f"attestation-ref:sealed-calculation:sha256:{hash_text(json.dumps(payload, sort_keys=True, separators=(',', ':')))}",
            image_ref=f"image-ref:sealed-calculation:sha256:{image_digest}",
            image_id_ref=f"image-id-ref:sha256:{image_digest}",
            seccomp_profile_ref=f"seccomp-profile-ref:sha256:{profile_hash}",
            runner_contract_ref=RUNNER_CONTRACT_REF,
            runner_source_ref=f"runner-source-ref:sha256:{runner_hash}",
            backend_ref=BACKEND_REF,
            platform_ref=PLATFORM_REF,
            docker_cli_ref=(f"docker-cli-ref:sha256:{docker_cli_hash}"),
            docker_daemon_ref=daemon_ref,
            container_config_ref=self._container_config_ref(),
            limits_ref=limits_ref,
        )

    def _inspect_daemon_payload(self) -> dict[str, object]:
        daemon = self._docker(["info", "--format", "{{json .}}"], timeout=5.0)
        if len(daemon.stdout) > 64 * 1024:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DAEMON_INSPECTION_OVERSIZED"
            )
        try:
            payload = json.loads(daemon.stdout)
        except json.JSONDecodeError as exc:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DAEMON_INSPECTION_INVALID"
            ) from exc
        if not isinstance(payload, dict):
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DAEMON_INSPECTION_INVALID"
            )
        return payload

    @staticmethod
    def _daemon_ref(payload: dict[str, object]) -> str:
        identity = {
            "id": payload.get("ID"),
            "server_version": payload.get("ServerVersion"),
            "os_type": payload.get("OSType"),
            "architecture": payload.get("Architecture"),
            "cgroup_version": payload.get("CgroupVersion"),
            "security_options": sorted(
                str(item) for item in payload.get("SecurityOptions") or []
            ),
        }
        if not all(
            identity[key]
            for key in (
                "id",
                "server_version",
                "os_type",
                "architecture",
                "cgroup_version",
            )
        ):
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DAEMON_IDENTITY_INCOMPLETE"
            )
        return f"docker-daemon-ref:sha256:{hash_text(json.dumps(identity, sort_keys=True, separators=(',', ':')))}"

    def _container_config_ref(self) -> str:
        payload = {
            "image_id": self.config.image_id,
            "seccomp_profile_sha256": self._seccomp_hash,
            "limits": self.config.limits.model_dump(mode="json"),
            "network": "none",
            "rootfs": "read_only",
            "user": "65532:65532",
            "cap_drop": ["ALL"],
            "no_new_privileges": True,
        }
        return f"container-config-ref:sha256:{hash_text(json.dumps(payload, sort_keys=True, separators=(',', ':')))}"

    def _expected_image_labels(self) -> dict[str, str]:
        return {
            "com.ultimate-ai-agent.sealed-calculation": "v1",
            "com.ultimate-ai-agent.sealed-calculation.base-image": BASE_IMAGE_REF,
            "com.ultimate-ai-agent.sealed-calculation.runner-sha256": hash_bytes(
                self.config.runner_source.read_bytes()
            ),
            "com.ultimate-ai-agent.sealed-calculation.probe-sha256": hash_bytes(
                self.config.isolation_probe_source.read_bytes()
            ),
        }

    def _read_json_frame(
        self,
        process: subprocess.Popen[bytes],
        timeout: float,
    ) -> dict[str, object]:
        if process.stderr is None:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_STDERR_PIPE_REQUIRED"
            )
        selector = selectors.DefaultSelector()
        buffer = bytearray()
        deadline = time.monotonic() + timeout
        try:
            os.set_blocking(process.stderr.fileno(), False)
            selector.register(process.stderr, selectors.EVENT_READ)
            while True:
                if self.kill_switch_engaged() or self.safe_disabled():
                    raise SealedCalculationBackendError(
                        "SEALED_CALCULATION_START_FENCE_DENIED"
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise SealedCalculationBackendError(
                        "SEALED_CALCULATION_START_TIMEOUT"
                    )
                events = selector.select(min(remaining, 0.05))
                if not events:
                    continue
                value = os.read(process.stderr.fileno(), 1)
                if not value:
                    raise SealedCalculationBackendError(
                        "SEALED_CALCULATION_PROTOCOL_FRAME_INVALID"
                    )
                buffer.extend(value)
                if len(buffer) > 512:
                    raise SealedCalculationBackendError(
                        "SEALED_CALCULATION_PROTOCOL_FRAME_INVALID"
                    )
                if value == b"\n":
                    break
            payload = json.loads(bytes(buffer[:-1]).decode("ascii"))
            if not isinstance(payload, dict):
                raise SealedCalculationBackendError(
                    "SEALED_CALCULATION_PROTOCOL_FRAME_INVALID"
                )
            return payload
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_PROTOCOL_FRAME_INVALID"
            ) from exc
        finally:
            selector.close()

    @staticmethod
    def _validated_input_payload(
        request: SealedCalculationRequest,
    ) -> bytes:
        if hash_text(request.expression) != request.expression_sha256:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_TRANSIENT_INPUT_HASH_MISMATCH"
            )
        payload = (
            json.dumps(
                {"expression": request.expression},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        if len(payload) > 1024:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_TRANSIENT_INPUT_SIZE_EXCEEDED"
            )
        return payload

    @staticmethod
    def _commit_input(
        process: subprocess.Popen[bytes],
        payload: bytes,
    ) -> None:
        if process.stdin is None:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_STDIN_PIPE_REQUIRED"
            )
        try:
            written = process.stdin.write(payload)
            if written != len(payload):
                raise OSError("SEALED_CALCULATION_STDIN_SHORT_WRITE")
            process.stdin.flush()
            process.stdin.close()
        except Exception as exc:
            raise SealedCalculationExecutionTruthUnknownError(
                "SEALED_CALCULATION_EXECUTION_TRUTH_UNKNOWN"
            ) from exc
        process.stdin = None

    def _validate_container_config(
        self,
        container_name: str,
        limits: SealedCalculationLimits,
    ) -> None:
        inspection = self._docker(
            ["inspect", container_name, "--format", "{{json .}}"],
            timeout=3.0,
        )
        if len(inspection.stdout) > 64 * 1024:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_OVERSIZED"
            )
        try:
            payload = json.loads(inspection.stdout)
        except json.JSONDecodeError as exc:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_INVALID"
            ) from exc
        config = payload.get("Config", {})
        host = payload.get("HostConfig", {})
        expected_entrypoint = [
            "/usr/local/bin/python3.13",
            "-I",
            "-S",
            "/opt/uaa-sealed-calculation/runner.py",
        ]
        expected_env = {
            "LANG=C.UTF-8",
            "PATH=/usr/local/bin",
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONHASHSEED=0",
            "PYTHONNOUSERSITE=1",
        }
        security_options = set(host.get("SecurityOpt") or [])
        tmpfs = host.get("Tmpfs") or {}
        reasons = []
        if payload.get("Image") != self.config.image_id:
            reasons.append("IMAGE_ID_DRIFT")
        if config.get("Entrypoint") != expected_entrypoint or config.get("Cmd") not in (
            None,
            [],
        ):
            reasons.append("ENTRYPOINT_DRIFT")
        if config.get("User") != "65532:65532" or config.get("WorkingDir") != "/tmp":
            reasons.append("IDENTITY_OR_WORKDIR_DRIFT")
        if set(config.get("Env") or []) != expected_env:
            reasons.append("ENVIRONMENT_DRIFT")
        if config.get("Volumes") not in (None, {}):
            reasons.append("IMAGE_VOLUME_DENIED")
        mounts = payload.get("Mounts")
        if mounts not in (None, []) and not (
            isinstance(mounts, list)
            and len(mounts) == 1
            and self._is_exact_tmpfs_mount(mounts[0])
        ):
            reasons.append("HOST_MOUNT_DENIED")
        if host.get("Binds") not in (None, []):
            reasons.append("HOST_BIND_DENIED")
        if host.get("NetworkMode") != "none" or host.get("PortBindings") not in (
            None,
            {},
        ):
            reasons.append("NETWORK_CONFIGURATION_DENIED")
        if (
            host.get("ReadonlyRootfs") is not True
            or host.get("Privileged") is not False
        ):
            reasons.append("ROOTFS_OR_PRIVILEGE_DRIFT")
        if set(host.get("CapDrop") or []) != {"ALL"}:
            reasons.append("CAPABILITY_DROP_DRIFT")
        seccomp_options = [
            option for option in security_options if option.startswith("seccomp=")
        ]
        try:
            actual_seccomp = (
                json.loads(seccomp_options[0].removeprefix("seccomp="))
                if len(seccomp_options) == 1
                else None
            )
            expected_seccomp = json.loads(
                self._read_validated_seccomp_profile()[0].decode("utf-8")
            )
        except (UnicodeError, json.JSONDecodeError, SealedCalculationBackendError):
            actual_seccomp = None
            expected_seccomp = object()
        if (
            security_options - set(seccomp_options) != {"no-new-privileges:true"}
            or actual_seccomp != expected_seccomp
        ):
            reasons.append("SECURITY_OPTION_DRIFT")
        if host.get("PidsLimit") != 1:
            reasons.append("PIDS_LIMIT_DRIFT")
        if (
            host.get("Memory") != limits.memory_bytes
            or host.get("MemorySwap") != limits.memory_bytes
        ):
            reasons.append("MEMORY_LIMIT_DRIFT")
        if host.get("NanoCpus") != int(limits.cpu_quota * 1_000_000_000):
            reasons.append("CPU_LIMIT_DRIFT")
        ulimits = {
            (item.get("Name"), item.get("Soft"), item.get("Hard"))
            for item in host.get("Ulimits") or []
            if isinstance(item, dict)
        }
        if ulimits != {("nofile", 32, 32), ("fsize", 1048576, 1048576)}:
            reasons.append("ULIMIT_DRIFT")
        if (host.get("LogConfig") or {}).get("Type") != "none":
            reasons.append("LOG_DRIVER_DRIFT")
        if (host.get("RestartPolicy") or {}).get("Name") not in ("", "no"):
            reasons.append("RESTART_POLICY_DRIFT")
        tmpfs_options = {
            item.strip()
            for item in str(tmpfs.get("/tmp", "")).split(",")
            if item.strip()
        }
        expected_tmpfs_options = {
            "rw",
            "noexec",
            "nosuid",
            "nodev",
            f"size={limits.tmpfs_bytes}",
            "mode=0700",
            "uid=65532",
            "gid=65532",
        }
        if tmpfs_options != expected_tmpfs_options:
            reasons.append("TMPFS_LIMIT_DRIFT")
        if host.get("Devices") not in (None, []) or host.get("DeviceRequests") not in (
            None,
            [],
        ):
            reasons.append("DEVICE_ACCESS_DENIED")
        denied_empty_fields = {
            "Binds": (None, []),
            "Links": (None, []),
            "Dns": (None, []),
            "DnsOptions": (None, []),
            "DnsSearch": (None, []),
            "ExtraHosts": (None, []),
            "GroupAdd": (None, []),
            "DeviceCgroupRules": (None, []),
        }
        if any(
            host.get(field) not in allowed
            for field, allowed in denied_empty_fields.items()
        ):
            reasons.append("HOST_INTEGRATION_DENIED")
        if any(
            host.get(field) not in (None, "", "private")
            for field in ("PidMode", "IpcMode", "UTSMode", "UsernsMode", "CgroupnsMode")
        ):
            reasons.append("HOST_NAMESPACE_DENIED")
        if host.get("PublishAllPorts") not in (None, False):
            reasons.append("PUBLISHED_PORTS_DENIED")
        if config.get("ExposedPorts") not in (None, {}) or config.get(
            "Healthcheck"
        ) not in (None, {}):
            reasons.append("IMAGE_NETWORK_OR_HEALTHCHECK_DENIED")
        if reasons:
            raise SealedCalculationBackendError(
                f"SEALED_CALCULATION_CONTAINER_CONFIG_INVALID:{reasons[0]}"
            )

    @staticmethod
    def _is_exact_tmpfs_mount(mount: object) -> bool:
        if not isinstance(mount, dict):
            return False
        allowed_fields = {
            "Type",
            "Source",
            "Destination",
            "Mode",
            "RW",
            "Propagation",
            "Name",
            "Driver",
        }
        return (
            set(mount) <= allowed_fields
            and mount.get("Type") == "tmpfs"
            and mount.get("Destination") == "/tmp"
            and mount.get("Source") in (None, "")
            and mount.get("Mode") in (None, "")
            and mount.get("RW") is True
            and mount.get("Propagation") in (None, "")
            and mount.get("Name") in (None, "")
            and mount.get("Driver") in (None, "")
        )

    def _bounded_collect(
        self,
        process: subprocess.Popen[bytes],
        *,
        stdout_limit: int,
        stderr_limit: int,
        timeout: float,
    ) -> tuple[bytes, bytes]:
        if process.stdout is None or process.stderr is None:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_OUTPUT_PIPES_REQUIRED"
            )
        streams = {
            process.stdout.fileno(): (process.stdout, bytearray(), stdout_limit),
            process.stderr.fileno(): (process.stderr, bytearray(), stderr_limit),
        }
        selector = selectors.DefaultSelector()
        deadline = time.monotonic() + timeout
        try:
            for stream, _buffer, _limit in streams.values():
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            while selector.get_map():
                if self.kill_switch_engaged() or self.safe_disabled():
                    raise SealedCalculationKillSwitchError(
                        "SEALED_CALCULATION_RUNTIME_FENCE_ENGAGED"
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired("sealed-calculation", timeout)
                events = selector.select(min(remaining, 0.05))
                if not events:
                    continue
                for key, _mask in events:
                    stream, buffer, limit = streams[key.fd]
                    chunk = os.read(key.fd, min(512, limit + 1 - len(buffer)))
                    if not chunk:
                        selector.unregister(stream)
                        continue
                    buffer.extend(chunk)
                    if len(buffer) > limit:
                        raise SealedCalculationOutputLimitError(
                            "SEALED_CALCULATION_OUTPUT_LIMIT_EXCEEDED"
                        )
            process.wait(timeout=max(0.01, deadline - time.monotonic()))
        finally:
            selector.close()
        return bytes(streams[process.stdout.fileno()][1]), bytes(
            streams[process.stderr.fileno()][1]
        )

    def _docker(
        self, args: list[str], *, timeout: float
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [
                    str(self.config.docker_binary),
                    "--host",
                    self.config.docker_host,
                    *args,
                ],
                check=False,
                text=True,
                capture_output=True,
                env=self._docker_env,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DOCKER_UNAVAILABLE"
            ) from exc
        if result.returncode != 0:
            raise SealedCalculationBackendError(
                "SEALED_CALCULATION_DOCKER_COMMAND_FAILED"
            )
        return result

    def _terminate(
        self,
        process: subprocess.Popen[bytes],
        container_name: str,
        execution_ref: str,
    ) -> None:
        cleanup_error: BaseException | None = None
        cleanup_cause: BaseException | None = None
        try:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            try:
                self._remove_owned_container(container_name, execution_ref)
            except SealedCalculationCleanupUnconfirmedError as exc:
                cleanup_error = exc
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired as exc:
                if cleanup_error is None:
                    cleanup_error = SealedCalculationCleanupUnconfirmedError(
                        "SEALED_CALCULATION_PROCESS_REAP_UNCONFIRMED"
                    )
                    cleanup_cause = exc
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        stream_error: BaseException | None = None
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except BaseException as exc:
                    stream_error = stream_error or exc
        if stream_error is not None:
            if cleanup_error is None:
                cleanup_error = SealedCalculationCleanupUnconfirmedError(
                    "SEALED_CALCULATION_PROCESS_STREAM_CLEANUP_UNCONFIRMED"
                )
                cleanup_cause = stream_error
        if cleanup_error is not None:
            if cleanup_cause is not None:
                raise cleanup_error from cleanup_cause
            raise cleanup_error

    def _remove_owned_container(
        self,
        container_name: str,
        execution_ref: str,
    ) -> None:
        payload = self._inspect_container_or_none(container_name)
        if payload is None:
            return
        labels = (payload.get("Config") or {}).get("Labels") or {}
        if (
            payload.get("Image") != self.config.image_id
            or labels.get("com.ultimate-ai-agent.sealed-calculation") != "v1"
            or labels.get("com.ultimate-ai-agent.execution")
            != hash_text(execution_ref)[:24]
        ):
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CONTAINER_OWNERSHIP_UNCONFIRMED"
            )
        try:
            self._docker(["rm", "--force", container_name], timeout=3.0)
        except SealedCalculationBackendError as exc:
            if self._inspect_container_or_none(container_name) is None:
                return
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CLEANUP_UNCONFIRMED"
            ) from exc
        if self._inspect_container_or_none(container_name) is not None:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CLEANUP_UNCONFIRMED"
            )

    def _inspect_container_or_none(
        self, container_name: str
    ) -> dict[str, object] | None:
        command = [
            str(self.config.docker_binary),
            "--host",
            self.config.docker_host,
            "container",
            "inspect",
            container_name,
            "--format",
            "{{json .}}",
        ]
        try:
            result = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                env=self._docker_env,
                timeout=3.0,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_UNAVAILABLE"
            ) from exc
        if len(result.stdout) > 64 * 1024 or len(result.stderr) > 4096:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_OVERSIZED"
            )
        if result.returncode != 0:
            try:
                self._inspect_daemon_payload()
            except SealedCalculationBackendError as exc:
                raise SealedCalculationCleanupUnconfirmedError(
                    "SEALED_CALCULATION_CONTAINER_ABSENCE_UNCONFIRMED"
                ) from exc
            return None
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_INVALID"
            ) from exc
        if not isinstance(payload, dict):
            raise SealedCalculationCleanupUnconfirmedError(
                "SEALED_CALCULATION_CONTAINER_INSPECTION_INVALID"
            )
        return payload

    @staticmethod
    def _container_name(execution_ref: str) -> str:
        return f"{CONTAINER_NAME_PREFIX}{hash_text(execution_ref)[:20]}"

    def _receipt_ref(self, execution_ref: str) -> str:
        return f"receipt-ref:sealed-calculation:sha256:{hash_text(execution_ref)}"

    def _evidence_refs(self, execution_ref: str, output_sha256: str) -> list[str]:
        return [
            SEALED_CALCULATION_RECEIPT_CONTRACT_REF,
            self.attestation.attestation_ref,
            self.attestation.runner_source_ref,
            f"output-hash-ref:sha256:{output_sha256}",
            f"execution-evidence-ref:sha256:{hash_text(execution_ref)}",
        ]

    def _failure_result(
        self,
        execution_ref: str,
        request: _CommittedCalculationRequest,
        status: SealedCalculationStatus,
        reason_code: str,
    ) -> SealedCalculationResult:
        return SealedCalculationResult(
            execution_ref=execution_ref,
            request_ref=request.request_ref,
            input_ref=request.input_ref,
            status=status,
            expression_sha256=request.expression_sha256,
            reason_codes=[reason_code],
            evidence_refs=[
                SEALED_CALCULATION_RECEIPT_CONTRACT_REF,
                self.attestation.attestation_ref,
                f"execution-evidence-ref:sha256:{hash_text(execution_ref)}",
            ],
            receipt_ref=self._receipt_ref(execution_ref),
            attestation_ref=self.attestation.attestation_ref,
            safe_summary="Sealed calculation failed closed without durable raw content.",
        )


def discover_local_docker_backend(
    *,
    image_ref: str = "uaa-sealed-calculation:local",
    seccomp_profile: Path,
    kill_switch: Callable[[], bool] = lambda: False,
    safe_disabled: Callable[[], bool] = lambda: False,
) -> DockerSealedCalculationBackend:
    try:
        docker_binary = Path("/usr/local/bin/docker").resolve(strict=True)
    except OSError as exc:
        raise SealedCalculationBackendError(
            "SEALED_CALCULATION_LOCAL_BACKEND_NOT_CONFIGURED"
        ) from exc
    local_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    endpoint = f"unix://{local_home / '.docker' / 'run' / 'docker.sock'}"
    try:
        image_id = subprocess.run(
            [
                str(docker_binary),
                "--host",
                endpoint,
                "image",
                "inspect",
                image_ref,
                "--format",
                "{{.Id}}",
            ],
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            timeout=5.0,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise SealedCalculationBackendError(
            "SEALED_CALCULATION_LOCAL_BACKEND_NOT_CONFIGURED"
        ) from exc
    try:
        return DockerSealedCalculationBackend(
            SealedCalculationBackendConfig(
                docker_binary=docker_binary,
                docker_host=endpoint,
                image_id=image_id,
                seccomp_profile=seccomp_profile.resolve(strict=True),
                runner_source=(seccomp_profile.parent / "runner.py").resolve(
                    strict=True
                ),
                isolation_probe_source=(
                    seccomp_profile.parent / "isolation_probe.py"
                ).resolve(strict=True),
            ),
            kill_switch=kill_switch,
            safe_disabled=safe_disabled,
        )
    except (OSError, ValueError) as exc:
        raise SealedCalculationBackendError(
            "SEALED_CALCULATION_LOCAL_BACKEND_NOT_CONFIGURED"
        ) from exc


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_regular_file_no_follow(
    path: Path,
    *,
    max_bytes: int,
) -> tuple[bytes, tuple[int, int, int, int]]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            raise ValueError("SEALED_CALCULATION_FILE_POSTURE_INVALID")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            raise ValueError("SEALED_CALCULATION_FILE_OVERSIZED")
        return payload, (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        )
    finally:
        os.close(descriptor)
