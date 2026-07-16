from __future__ import annotations

import ctypes
import fcntl
import hashlib
import json
import os
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
)
from .constants import MatrixSessionOperation
from .contracts import MatrixSessionCommand, stable_matrix_session_ref
from .node_runtime import (
    MATRIX_NODE_RUNTIME_PROBE_OUTPUT,
    MatrixNodeRuntimeBinding,
    copy_matrix_node_runtime_binding,
    matrix_node_runtime_environment,
    resolve_approved_matrix_node_runtime_binding,
    resolve_matrix_node_runtime_binding,
    validate_matrix_node_runtime_probe,
)
from .target_policy import validate_matrix_transient_target


MATRIX_SESSION_ADAPTER_RESPONSE_MAX_BYTES = 128 * 1024
MATRIX_SESSION_ADAPTER_INPUT_MAX_BYTES = 128 * 1024
MATRIX_SESSION_ADAPTER_TIMEOUT_SECONDS = 30
MATRIX_SESSION_NODE_RUNTIME_PROBE_TIMEOUT_SECONDS = 15
MATRIX_SESSION_NODE_RUNTIME_PROBE_NAME = "node-runtime-probe.mjs"
MATRIX_SESSION_NODE_RUNTIME_PROBE_SOURCE = b"""\
import { readFileSync } from "node:fs";
const outsidePath = process.argv[2];
const version = process.versions?.node ?? "";
if (process.release?.name !== "node" || !/^22\\.[0-9]+\\.[0-9]+$/.test(version)) {
  process.exit(64);
}
let denied = false;
try {
  readFileSync(outsidePath);
} catch (error) {
  denied = error?.code === "ERR_ACCESS_DENIED";
}
if (!denied) {
  process.exit(65);
}
process.stdout.write("node22-permission-enforced\\n");
"""
MATRIX_SESSION_SAFE_DISABLE_ENV = "UAA_MATRIX_SESSION_SAFE_DISABLE"
MATRIX_SESSION_HELPER_NAME = "uaa-matrix-session-keychain-helper"
MATRIX_SESSION_HELPER_METADATA_NAME = "matrix-session-keychain-helper.json"
MATRIX_SESSION_RUNTIME_FILE_MAX_BYTES = 256 * 1024 * 1024
MATRIX_SESSION_HELPER_METADATA_MAX_BYTES = 16 * 1024
_CLONEFILE = getattr(ctypes.CDLL(None, use_errno=True), "clonefile", None)
if _CLONEFILE is not None:
    _CLONEFILE.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    _CLONEFILE.restype = ctypes.c_int


class MatrixSessionBackendError(RuntimeError):
    pass


_ClaimedHandleT = TypeVar("_ClaimedHandleT")


@dataclass(frozen=True, repr=False)
class MatrixSessionTransientInput:
    endpoint_url: str | None = None
    discovery_origin: str | None = None
    callback_url: str | None = None

    def __repr__(self) -> str:
        return "MatrixSessionTransientInput(<redacted>)"


class _AdapterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: str
    ok: bool
    operation: str
    runtime_status: str
    result_ref: str
    redaction_status: str
    error_code: str | None = None
    homeserver_observation_ref: str | None = None
    discovery_freshness_ref: str | None = None
    versions_ref: str | None = None
    login_flows_ref: str | None = None
    auth_metadata_ref: str | None = None
    capabilities: dict[str, bool] | None = None
    sdk_version_ref: str | None = None
    account_ref: str | None = None
    device_ref: str | None = None
    session_ref: str | None = None
    session_generation_ref: str | None = None
    credential_receipt_ref: str | None = None
    callback_attempt_ref: str | None = None
    redirect_target_ref: str | None = None
    browser_launch_ref: str | None = None

    @model_validator(mode="after")
    def validate_response(self) -> "_AdapterResponse":
        if self.schema_version != "uaa-matrix-client-adapter-response.v1":
            raise ValueError("MATRIX_SESSION_ADAPTER_SCHEMA_MISMATCH")
        if self.redaction_status != "safe_refs_only":
            raise ValueError("MATRIX_SESSION_ADAPTER_REDACTION_REQUIRED")
        for name, value in self.model_dump(mode="python").items():
            if name.endswith("_ref") and value is not None:
                validate_execution_ref(str(value), f"matrix_session_adapter_{name}")
        validate_safe_execution_payload(
            self.model_dump(mode="json"), "matrix_session_adapter_response"
        )
        if self.ok and self.error_code is not None:
            raise ValueError("MATRIX_SESSION_ADAPTER_SUCCESS_ERROR_FORBIDDEN")
        if not self.ok and not self.error_code:
            raise ValueError("MATRIX_SESSION_ADAPTER_FAILURE_CODE_REQUIRED")
        return self

    def validate_for_operation(self, expected: MatrixSessionOperation) -> None:
        if self.operation != expected.value:
            raise ValueError("MATRIX_SESSION_ADAPTER_OPERATION_MISMATCH")
        if not self.ok:
            if self.runtime_status != "blocked":
                raise ValueError("MATRIX_SESSION_ADAPTER_FAILURE_STATUS_INVALID")
            return
        if expected not in {
            MatrixSessionOperation.discovery_read,
            MatrixSessionOperation.auth_methods_read,
        }:
            raise ValueError("MATRIX_SESSION_ADAPTER_BLOCKED_OPERATION_SUCCEEDED")
        required: dict[MatrixSessionOperation, tuple[str, set[str]]] = {
            MatrixSessionOperation.discovery_read: (
                "discovered",
                {
                    "homeserver_observation_ref",
                    "discovery_freshness_ref",
                    "sdk_version_ref",
                },
            ),
            MatrixSessionOperation.auth_methods_read: (
                "ready_for_authentication",
                {
                    "homeserver_observation_ref",
                    "versions_ref",
                    "login_flows_ref",
                    "capabilities",
                    "sdk_version_ref",
                },
            ),
        }
        status, names = required[expected]
        if self.runtime_status != status or any(
            getattr(self, name) is None for name in names
        ):
            raise ValueError("MATRIX_SESSION_ADAPTER_SUCCESS_CONTRACT_INVALID")
        optional_response_names = {
            "homeserver_observation_ref",
            "discovery_freshness_ref",
            "versions_ref",
            "login_flows_ref",
            "auth_metadata_ref",
            "capabilities",
            "sdk_version_ref",
            "account_ref",
            "device_ref",
            "session_ref",
            "session_generation_ref",
            "credential_receipt_ref",
            "callback_attempt_ref",
            "redirect_target_ref",
            "browser_launch_ref",
        }
        allowed = set(names)
        if expected == MatrixSessionOperation.auth_methods_read:
            allowed.add("auth_metadata_ref")
        if any(
            getattr(self, name) is not None
            for name in optional_response_names - allowed
        ):
            raise ValueError("MATRIX_SESSION_ADAPTER_RESPONSE_SCOPE_INVALID")


@dataclass(frozen=True)
class MatrixSessionBackendConfig:
    repo_root: Path
    adapter_root: Path
    node_binary: Path
    runner_path: Path
    helper_path: Path | None
    expected_node_sha256: str
    expected_runner_sha256: str
    expected_helper_sha256: str | None
    wasm_asset_path: Path
    package_lock_path: Path
    runtime_integrity_path: Path
    node_runtime_binding: MatrixNodeRuntimeBinding = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        for path in (
            self.repo_root,
            self.adapter_root,
            self.node_binary,
            self.runner_path,
            self.wasm_asset_path,
            self.package_lock_path,
            self.runtime_integrity_path,
        ):
            if not path.is_absolute():
                raise ValueError("MATRIX_SESSION_BACKEND_ABSOLUTE_PATHS_REQUIRED")
        if self.repo_root != self.repo_root.resolve():
            raise ValueError("MATRIX_SESSION_REPO_ROOT_SYMLINKED")
        if (self.helper_path is None) != (self.expected_helper_sha256 is None):
            raise ValueError("MATRIX_SESSION_HELPER_BINDING_INCOMPLETE")
        _validate_runtime_integrity(
            adapter_root=self.adapter_root,
            package_lock_path=self.package_lock_path,
            manifest_path=self.runtime_integrity_path,
        )
        for path, expected in (
            (self.node_binary, self.expected_node_sha256),
            (self.runner_path, self.expected_runner_sha256),
        ):
            _validate_hash_bound_file(path, expected)
        runtime_binding = resolve_approved_matrix_node_runtime_binding(
            self.node_binary,
            trust_manifest_path=(
                self.adapter_root / "runtime-trust" / "node-runtime.json"
            ),
        )
        if runtime_binding.executable.expected_sha256 != self.expected_node_sha256:
            raise ValueError("MATRIX_SESSION_RUNTIME_HASH_MISMATCH")
        object.__setattr__(self, "node_runtime_binding", runtime_binding)
        if self.helper_path is not None and self.expected_helper_sha256 is not None:
            _validate_hash_bound_file(self.helper_path, self.expected_helper_sha256)
        for path in (self.node_binary,):
            if not os.access(path, os.X_OK):
                raise ValueError("MATRIX_SESSION_RUNTIME_EXECUTABLE_REQUIRED")
        if self.helper_path is not None and not os.access(self.helper_path, os.X_OK):
            raise ValueError("MATRIX_SESSION_RUNTIME_EXECUTABLE_REQUIRED")
        _require_safe_regular_file(self.wasm_asset_path)


@dataclass(frozen=True)
class MatrixSessionBackendResult:
    execution_ref: str
    succeeded: bool
    runtime_status: str
    evidence_refs: tuple[str, ...]
    safe_output: dict[str, Any]
    safe_summary: str


@dataclass(frozen=True)
class MatrixRuntimeSnapshot:
    root: Path
    adapter_root: Path
    node_binary: Path
    runner_path: Path
    owner_lock_fd: int = field(repr=False, compare=False)


class MatrixSessionExecutionHandle:
    def __init__(
        self,
        *,
        backend: "MatrixSessionBackend",
        execution_ref: str,
        process: subprocess.Popen[bytes],
        commit_validated_at: datetime,
        expected_operation: MatrixSessionOperation,
        runtime_snapshot: MatrixRuntimeSnapshot,
    ) -> None:
        self._backend = backend
        self._execution_ref = execution_ref
        self._process = process
        self.commit_validated_at = commit_validated_at
        self._expected_operation = expected_operation
        self._runtime_snapshot: MatrixRuntimeSnapshot | None = runtime_snapshot
        self._collected = False
        self._runtime_settled = False
        self._finalized = False
        self._committed = False
        self._settled = False

    @property
    def settled(self) -> bool:
        return self._settled

    def collect(self) -> MatrixSessionBackendResult:
        if self._collected:
            raise MatrixSessionBackendError("MATRIX_SESSION_HANDLE_ALREADY_COLLECTED")
        self._collected = True
        collection_error: BaseException | None = None
        cleanup_error: BaseException | None = None
        stdout: bytes | None = None
        try:
            stdout = _communicate_bounded(
                self._process,
                timeout_seconds=MATRIX_SESSION_ADAPTER_TIMEOUT_SECONDS,
                maximum_output_bytes=MATRIX_SESSION_ADAPTER_RESPONSE_MAX_BYTES,
            )
        except BaseException as exc:
            collection_error = exc
        if collection_error is not None:
            try:
                self._backend._terminate_process_group(self._process)
            except BaseException as exc:
                cleanup_error = exc
        try:
            _close_process_streams(self._process)
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        try:
            self._backend._release_lifecycle()
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        try:
            self._release_runtime_snapshot()
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SESSION_COLLECTION_CLEANUP_UNCERTAIN"
            ) from cleanup_error
        self._runtime_settled = True
        if collection_error is not None:
            if self._expected_operation in {
                MatrixSessionOperation.discovery_read,
                MatrixSessionOperation.auth_methods_read,
            }:
                return self._safe_read_failure("collection-failed")
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SESSION_COLLECTION_RECOVERY_REQUIRED"
            ) from collection_error
        assert stdout is not None
        try:
            response = _AdapterResponse.model_validate_json(stdout)
            response.validate_for_operation(self._expected_operation)
            if response.ok != (self._process.returncode == 0):
                raise ValueError("MATRIX_SESSION_ADAPTER_EXIT_STATUS_MISMATCH")
        except ValueError as exc:
            if self._expected_operation in {
                MatrixSessionOperation.discovery_read,
                MatrixSessionOperation.auth_methods_read,
            }:
                return self._safe_read_failure("invalid-response")
            raise MatrixSessionBackendError(
                "MATRIX_SESSION_ADAPTER_RESPONSE_INVALID"
            ) from exc
        evidence_refs = tuple(
            ref
            for ref in (
                response.result_ref,
                response.homeserver_observation_ref,
                response.discovery_freshness_ref,
                response.versions_ref,
                response.login_flows_ref,
                response.auth_metadata_ref,
                response.credential_receipt_ref,
                response.browser_launch_ref,
            )
            if ref is not None
        )
        return MatrixSessionBackendResult(
            execution_ref=self._execution_ref,
            succeeded=response.ok,
            runtime_status=response.runtime_status,
            evidence_refs=evidence_refs or (response.result_ref,),
            safe_output=response.model_dump(mode="json", exclude_none=True),
            safe_summary=(
                "Matrix session operation completed with content-free evidence."
                if response.ok
                else "Matrix session operation failed closed with a safe error code."
            ),
        )

    def _safe_read_failure(self, reason: str) -> MatrixSessionBackendResult:
        evidence_ref = stable_matrix_session_ref(
            "evidence-ref:matrix-session:read-failure",
            {
                "execution_ref": self._execution_ref,
                "operation": self._expected_operation.value,
                "reason": reason,
            },
        )
        return MatrixSessionBackendResult(
            execution_ref=self._execution_ref,
            succeeded=False,
            runtime_status="blocked",
            evidence_refs=(evidence_ref,),
            safe_output={},
            safe_summary=(
                "Matrix read failed closed after bounded runtime settlement."
            ),
        )

    def _release_runtime_snapshot(self) -> None:
        if self._runtime_snapshot is not None:
            remove_matrix_runtime_snapshot(self._runtime_snapshot)
            self._runtime_snapshot = None

    def finalize(self) -> None:
        if (
            self._settled
            or self._finalized
            or not self._runtime_settled
            or not self._collected
        ):
            raise MatrixSessionBackendError("MATRIX_SESSION_FINALIZATION_INVALID")
        self._finalized = True

    def commit(self) -> None:
        if self._settled or self._committed or not self._finalized:
            raise MatrixSessionBackendError("MATRIX_SESSION_COMMIT_INVALID")
        self._committed = True

    def settle(self) -> None:
        if self._settled or not self._committed:
            raise MatrixSessionBackendError("MATRIX_SESSION_SETTLEMENT_INVALID")
        self._settled = True

    def abort(self) -> None:
        if self._settled:
            return
        self._collected = True
        if self._runtime_settled:
            self._settled = True
            return
        cleanup_error: BaseException | None = None
        try:
            self._backend._terminate_process_group(self._process)
        except BaseException as exc:
            cleanup_error = exc
        try:
            _close_process_streams(self._process)
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        try:
            self._backend._release_lifecycle()
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        try:
            self._release_runtime_snapshot()
        except BaseException as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise AuthorityDispatchAtomicStartRecoveryRequired(
                "MATRIX_SESSION_CONFIRMATION_ABORT_CLEANUP_UNCERTAIN"
            ) from cleanup_error
        self._runtime_settled = True
        self._settled = True


class MatrixSessionBackend:
    def __init__(
        self,
        config: MatrixSessionBackendConfig,
        *,
        kill_switch_engaged: Callable[[], bool],
        lifecycle_lock_dir: Path,
    ) -> None:
        self.config = config
        self._kill_switch_engaged = kill_switch_engaged
        self._transient: dict[str, MatrixSessionTransientInput] = {}
        self._request_states: set[str] = set()
        self._state_lock = threading.RLock()
        self._lifecycle_lock = threading.Lock()
        self._lifecycle_lock_dir = lifecycle_lock_dir
        self._lifecycle_descriptor: int | None = None
        assert config.node_runtime_binding is not None
        self.binding_ref = stable_matrix_session_ref(
            "backend-binding-ref:matrix-session",
            {
                "node_sha256": config.expected_node_sha256,
                "node_runtime_binding_ref": config.node_runtime_binding.binding_ref,
                "node_runtime_profile_ref": (
                    config.node_runtime_binding.trust_profile_ref
                ),
                "runner_sha256": config.expected_runner_sha256,
                "helper_sha256": config.expected_helper_sha256 or "not-installed",
                "wasm_sha256": _file_sha256(config.wasm_asset_path),
                "runtime_integrity_sha256": _file_sha256(config.runtime_integrity_path),
            },
        )

    def bind_transient(
        self, dispatch_ref: str, transient: MatrixSessionTransientInput
    ) -> None:
        validate_execution_ref(dispatch_ref, "matrix_session_dispatch_ref")
        with self._state_lock:
            if dispatch_ref in self._transient:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_TRANSIENT_ALREADY_BOUND"
                )
            self._transient[dispatch_ref] = transient

    def claim_request_state(self, dispatch_ref: str) -> None:
        with self._state_lock:
            if dispatch_ref in self._request_states:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_REQUEST_ALREADY_CLAIMED"
                )
            self._request_states.add(dispatch_ref)

    def release_request_state(self, dispatch_ref: str) -> None:
        with self._state_lock:
            self._request_states.discard(dispatch_ref)
            self._transient.pop(dispatch_ref, None)

    def request_state_active(self, dispatch_ref: str) -> bool:
        with self._state_lock:
            return dispatch_ref in self._request_states

    def readiness_reason_refs(self, operation: MatrixSessionOperation) -> list[str]:
        reasons: list[str] = []
        if sys.platform != "darwin":
            reasons.append("reason-ref:matrix-session:macos-required")
        if os.getenv(MATRIX_SESSION_SAFE_DISABLE_ENV, "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            reasons.append("reason-ref:matrix-session:safe-disabled")
        if self._kill_switch_engaged():
            reasons.append("reason-ref:matrix-session:kill-switch-engaged")
        try:
            self.config.__post_init__()
        except (OSError, ValueError):
            reasons.append("reason-ref:matrix-session:runtime-binding-unready")
        if operation in {
            MatrixSessionOperation.sso_launch,
            MatrixSessionOperation.sso_callback_consume,
        }:
            reasons.append("reason-ref:matrix-session:sso-broker-required")
        if operation in {
            MatrixSessionOperation.credential_auth_create,
            MatrixSessionOperation.refresh,
            MatrixSessionOperation.logout,
            MatrixSessionOperation.revoke_all,
            MatrixSessionOperation.credential_store_rotate,
            MatrixSessionOperation.credential_delete,
        }:
            reasons.append(
                "reason-ref:matrix-session:authenticated-one-use-handoff-required"
            )
        if (
            operation
            in {
                MatrixSessionOperation.credential_auth_create,
                MatrixSessionOperation.sso_callback_consume,
                MatrixSessionOperation.refresh,
                MatrixSessionOperation.logout,
                MatrixSessionOperation.revoke_all,
                MatrixSessionOperation.credential_store_rotate,
                MatrixSessionOperation.credential_delete,
            }
            and self.config.helper_path is None
        ):
            reasons.append("reason-ref:matrix-session:keychain-helper-not-installed")
        return list(dict.fromkeys(reasons))

    def validate_transient_target(self, command: MatrixSessionCommand) -> None:
        """Bind transient network material to the hash-bound command before start."""

        with self._state_lock:
            transient = self._transient.get(command.dispatch_ref)
        if transient is None:
            raise MatrixSessionBackendError("MATRIX_SESSION_TRANSIENT_TARGET_REQUIRED")
        sso_operations = {
            MatrixSessionOperation.sso_launch,
            MatrixSessionOperation.sso_callback_consume,
        }
        if command.operation == MatrixSessionOperation.discovery_read:
            if (
                transient.discovery_origin is None
                or transient.endpoint_url is not None
                or transient.callback_url is not None
            ):
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_DISCOVERY_TRANSIENT_SCOPE_INVALID"
                )
        else:
            if transient.endpoint_url is None or transient.discovery_origin is not None:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_ENDPOINT_TRANSIENT_SCOPE_INVALID"
                )
            if (command.operation in sso_operations) != (
                transient.callback_url is not None
            ):
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_CALLBACK_TRANSIENT_SCOPE_INVALID"
                )
        validate_matrix_transient_target(
            expected_homeserver_ref=command.homeserver_ref,
            endpoint_class_ref=command.endpoint_class_ref,
            endpoint_url=transient.endpoint_url,
            discovery_origin=transient.discovery_origin,
            expected_redirect_target_ref=command.redirect_target_ref,
            callback_url=transient.callback_url,
        )

    def start_operation(
        self,
        *,
        operation: MatrixSessionOperation,
        dispatch_ref: str,
        execution_ref: str,
        safe_request: dict[str, Any],
        validate_commit_fence: Callable[[], tuple[list[str], datetime]],
        claim_handle: Callable[[MatrixSessionExecutionHandle], _ClaimedHandleT]
        | None = None,
    ) -> MatrixSessionExecutionHandle | _ClaimedHandleT:
        if not self._lifecycle_lock.acquire(blocking=False):
            raise MatrixSessionBackendError("MATRIX_SESSION_DUPLICATE_LIFECYCLE_OWNER")
        process: subprocess.Popen[bytes] | None = None
        runtime_snapshot: MatrixRuntimeSnapshot | None = None
        input_committed = False
        try:
            reasons = self.readiness_reason_refs(operation)
            if reasons:
                raise MatrixSessionBackendError("MATRIX_SESSION_PRESTART_DENIED")
            with self._state_lock:
                transient = self._transient.get(dispatch_ref)
            if transient is None:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_TRANSIENT_TARGET_REQUIRED"
                )
            self._acquire_cross_process_lifecycle(safe_request)
            commit_reasons, commit_validated_at = validate_commit_fence()
            if commit_reasons:
                raise MatrixSessionBackendError("MATRIX_SESSION_COMMIT_FENCE_DENIED")
            runtime_snapshot = create_matrix_runtime_snapshot(
                adapter_root=self.config.adapter_root,
                node_binary=self.config.node_binary,
                runner_path=self.config.runner_path,
                expected_node_sha256=self.config.expected_node_sha256,
                expected_runner_sha256=self.config.expected_runner_sha256,
                snapshot_parent=self._lifecycle_lock_dir / "runtime-snapshots",
                node_runtime_binding=self.config.node_runtime_binding,
            )
            payload = self._build_adapter_payload(
                operation=operation,
                safe_request=safe_request,
                transient=transient,
            )
            process, input_payload = self._start_node_adapter(
                payload,
                runtime_snapshot=runtime_snapshot,
            )
            _commit_input_bounded(
                process,
                input_payload,
                timeout_seconds=MATRIX_SESSION_ADAPTER_TIMEOUT_SECONDS,
            )
            input_committed = True
            handle = MatrixSessionExecutionHandle(
                backend=self,
                execution_ref=execution_ref,
                process=process,
                commit_validated_at=commit_validated_at,
                expected_operation=operation,
                runtime_snapshot=runtime_snapshot,
            )
            return claim_handle(handle) if claim_handle is not None else handle
        except BaseException as original:
            cleanup_error: BaseException | None = None
            if process is not None:
                try:
                    self._terminate_process_group(process)
                except BaseException as exc:
                    cleanup_error = exc
                try:
                    _close_process_streams(process)
                except BaseException as exc:
                    cleanup_error = cleanup_error or exc
            if runtime_snapshot is not None:
                try:
                    remove_matrix_runtime_snapshot(runtime_snapshot)
                except BaseException as exc:
                    cleanup_error = cleanup_error or exc
            try:
                self._release_lifecycle()
            except BaseException as exc:
                cleanup_error = cleanup_error or exc
            if cleanup_error is not None:
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "MATRIX_SESSION_INPUT_COMMIT_CLEANUP_UNCERTAIN"
                ) from cleanup_error
            if input_committed and not isinstance(
                original,
                AuthorityDispatchAtomicStartRecoveryRequired,
            ):
                raise AuthorityDispatchAtomicStartRecoveryRequired(
                    "MATRIX_SESSION_INPUT_COMMIT_RECOVERY_REQUIRED"
                ) from original
            raise

    def _build_adapter_payload(
        self,
        *,
        operation: MatrixSessionOperation,
        safe_request: dict[str, Any],
        transient: MatrixSessionTransientInput,
    ) -> dict[str, Any]:
        validate_matrix_transient_target(
            expected_homeserver_ref=str(safe_request["homeserver_ref"]),
            endpoint_class_ref=str(safe_request["endpoint_class_ref"]),
            endpoint_url=transient.endpoint_url,
            discovery_origin=transient.discovery_origin,
            expected_redirect_target_ref=safe_request.get("redirect_target_ref"),
            callback_url=transient.callback_url,
        )
        payload = {**safe_request, "operation": operation.value}
        if transient.endpoint_url is not None:
            payload["base_url"] = transient.endpoint_url
        if transient.discovery_origin is not None:
            payload["discovery_origin"] = transient.discovery_origin
        if transient.callback_url is not None:
            payload["callback_url"] = transient.callback_url
        if any(key in payload for key in ("password", "access_token", "refresh_token")):
            raise MatrixSessionBackendError("MATRIX_SESSION_RAW_MATERIAL_INPUT_DENIED")
        return payload

    def _start_node_adapter(
        self,
        payload: dict[str, Any],
        *,
        runtime_snapshot: MatrixRuntimeSnapshot,
    ) -> tuple[subprocess.Popen[bytes], bytes]:
        return _spawn_bounded(
            [
                os.fspath(runtime_snapshot.node_binary),
                "--permission",
                f"--allow-fs-read={runtime_snapshot.adapter_root}",
                os.fspath(runtime_snapshot.runner_path),
            ],
            payload,
            runtime_root=runtime_snapshot.node_binary.parent.parent,
        )

    def _release_lifecycle(self) -> None:
        descriptor = self._lifecycle_descriptor
        self._lifecycle_descriptor = None
        if descriptor is not None:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        if self._lifecycle_lock.locked():
            self._lifecycle_lock.release()

    def _acquire_cross_process_lifecycle(self, safe_request: dict[str, Any]) -> None:
        directory = self._lifecycle_lock_dir
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory_metadata = os.lstat(directory)
        if (
            not stat.S_ISDIR(directory_metadata.st_mode)
            or directory_metadata.st_uid != os.getuid()
            or directory_metadata.st_mode & 0o077
        ):
            raise MatrixSessionBackendError("MATRIX_SESSION_LIFECYCLE_LOCK_DIR_UNSAFE")
        owner_ref = str(
            safe_request.get("session_ref") or safe_request.get("homeserver_ref") or ""
        )
        validate_execution_ref(owner_ref, "matrix_session_lifecycle_owner_ref")
        lock_path = directory / "matrix-session.lifecycle.lock"
        descriptor = os.open(
            lock_path,
            os.O_CREAT
            | os.O_RDWR
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(lock_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_uid != os.getuid()
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise MatrixSessionBackendError("MATRIX_SESSION_LIFECYCLE_LOCK_UNSAFE")
            os.fchmod(descriptor, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_DUPLICATE_LIFECYCLE_OWNER"
                ) from exc
        except BaseException:
            os.close(descriptor)
            raise
        self._lifecycle_descriptor = descriptor

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired as exc:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_PROCESS_REAP_FAILED"
                ) from exc


def default_matrix_session_backend_config(
    repo_root: Path,
) -> MatrixSessionBackendConfig:
    node = shutil.which("node")
    if not node:
        raise MatrixSessionBackendError("MATRIX_SESSION_NODE_REQUIRED")
    node_path = Path(node).resolve()
    runner = repo_root / "integrations" / "matrix-client-adapter" / "src" / "runner.mjs"
    adapter_root = runner.parent.parent
    runtime_integrity_path = adapter_root / "runtime-integrity.json"
    runtime_binding = resolve_approved_matrix_node_runtime_binding(
        node_path,
        trust_manifest_path=(adapter_root / "runtime-trust" / "node-runtime.json"),
    )
    wasm = (
        repo_root
        / "integrations"
        / "matrix-client-adapter"
        / "node_modules"
        / "@matrix-org"
        / "matrix-sdk-crypto-wasm"
        / "pkg"
        / "matrix_sdk_crypto_wasm_bg.wasm"
    )
    helper_root = Path.home() / ".local" / "share" / "uaa" / "helpers"
    helper = helper_root / MATRIX_SESSION_HELPER_NAME
    metadata_path = helper_root / MATRIX_SESSION_HELPER_METADATA_NAME
    expected_helper: str | None = None
    try:
        metadata = json.loads(_read_safe_private_metadata_file(metadata_path))
        if metadata.get("schema_version") != (
            "uaa-matrix-session-keychain-helper-install.v1"
        ):
            raise ValueError("MATRIX_SESSION_HELPER_METADATA_SCHEMA_INVALID")
        helper_ref = str(metadata["helper_fingerprint_ref"])
        expected_helper = helper_ref.removeprefix("helper-fingerprint-ref:sha256:")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        helper = None
        expected_helper = None
    return MatrixSessionBackendConfig(
        repo_root=repo_root,
        adapter_root=adapter_root,
        node_binary=node_path,
        runner_path=runner,
        helper_path=helper,
        expected_node_sha256=runtime_binding.executable.expected_sha256,
        expected_runner_sha256=_file_sha256(runner),
        expected_helper_sha256=expected_helper,
        wasm_asset_path=wasm,
        package_lock_path=adapter_root / "package-lock.json",
        runtime_integrity_path=runtime_integrity_path,
    )


def _copy_runtime_file(source: Path, target: Path) -> None:
    if _CLONEFILE is not None:
        if _CLONEFILE(os.fsencode(source), os.fsencode(target), 0) == 0:
            return
    shutil.copy2(source, target)


def _snapshot_tree_roots(manifest_path: Path) -> tuple[str, ...]:
    manifest = json.loads(
        _read_safe_regular_file(
            manifest_path,
            maximum=MATRIX_SESSION_HELPER_METADATA_MAX_BYTES,
        )
    )
    trees = manifest.get("trees") if isinstance(manifest, dict) else None
    if not isinstance(trees, list):
        raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
    roots: list[str] = []
    for item in trees:
        if not isinstance(item, dict) or not isinstance(item.get("root"), str):
            raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
        roots.append(item["root"])
    return tuple(roots)


def create_matrix_runtime_snapshot(
    *,
    adapter_root: Path,
    node_binary: Path,
    runner_path: Path,
    expected_node_sha256: str,
    expected_runner_sha256: str,
    snapshot_parent: Path | None = None,
    node_runtime_binding: MatrixNodeRuntimeBinding,
) -> MatrixRuntimeSnapshot:
    """Copy reviewed runtime bytes into one private, revalidated launch root."""

    _validate_hash_bound_file(node_binary, expected_node_sha256)
    _validate_hash_bound_file(runner_path, expected_runner_sha256)
    runtime_binding = resolve_matrix_node_runtime_binding(
        node_binary,
        expected_node_sha256=expected_node_sha256,
        expected=node_runtime_binding,
    )
    package_lock = adapter_root / "package-lock.json"
    manifest = adapter_root / "runtime-integrity.json"
    _validate_runtime_integrity(
        adapter_root=adapter_root,
        package_lock_path=package_lock,
        manifest_path=manifest,
    )
    requested_parent = snapshot_parent or (
        Path(tempfile.gettempdir()) / "uaa-matrix-runtime"
    )
    requested_parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = requested_parent.resolve()
    os.chmod(parent, 0o700)
    parent_info = os.lstat(parent)
    if (
        not stat.S_ISDIR(parent_info.st_mode)
        or stat.S_ISLNK(parent_info.st_mode)
        or parent_info.st_uid != os.getuid()
        or parent_info.st_mode & 0o077
    ):
        raise ValueError("MATRIX_SESSION_RUNTIME_SNAPSHOT_PARENT_UNSAFE")
    reconcile_lock_fd = _open_runtime_snapshot_lock(
        parent / ".reconcile.lock",
        create=True,
    )
    fcntl.flock(reconcile_lock_fd, fcntl.LOCK_EX)
    try:
        _reconcile_stale_runtime_snapshots(parent)
        root = Path(tempfile.mkdtemp(prefix="snapshot-", dir=parent)).resolve()
        owner_lock_fd: int | None = None
        try:
            owner_lock_fd = _open_runtime_snapshot_lock(
                root / ".owner.lock",
                create=True,
            )
            fcntl.flock(owner_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            if owner_lock_fd is not None:
                os.close(owner_lock_fd)
            _remove_runtime_snapshot_root(root)
            raise
        assert owner_lock_fd is not None
        snapshot = MatrixRuntimeSnapshot(
            root=root,
            adapter_root=root / "adapter",
            node_binary=root / "node-runtime" / "bin" / "node-runtime",
            runner_path=root / "adapter" / runner_path.relative_to(adapter_root),
            owner_lock_fd=owner_lock_fd,
        )
        try:
            snapshot.adapter_root.mkdir(mode=0o700)
            copied_node = copy_matrix_node_runtime_binding(
                runtime_binding,
                target_root=snapshot.node_binary.parent.parent,
            )
            if copied_node != snapshot.node_binary:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_LAYOUT_INVALID")
            _copy_runtime_file(
                package_lock,
                snapshot.adapter_root / "package-lock.json",
            )
            _copy_runtime_file(
                manifest,
                snapshot.adapter_root / "runtime-integrity.json",
            )
            for relative in _snapshot_tree_roots(manifest):
                source = adapter_root / relative
                target = snapshot.adapter_root / relative
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                shutil.copytree(source, target, copy_function=_copy_runtime_file)
            if not snapshot.runner_path.exists():
                snapshot.runner_path.parent.mkdir(
                    mode=0o700,
                    parents=True,
                    exist_ok=True,
                )
                _copy_runtime_file(runner_path, snapshot.runner_path)
            _write_snapshot_node_runtime_probe(snapshot)
            _validate_hash_bound_file(snapshot.node_binary, expected_node_sha256)
            _validate_hash_bound_file(snapshot.runner_path, expected_runner_sha256)
            _validate_runtime_integrity(
                adapter_root=snapshot.adapter_root,
                package_lock_path=snapshot.adapter_root / "package-lock.json",
                manifest_path=snapshot.adapter_root / "runtime-integrity.json",
            )
            for path in sorted(root.rglob("*"), reverse=True):
                os.chmod(path, 0o500 if path.is_dir() else 0o400)
            os.chmod(snapshot.node_binary, 0o500)
            _validate_snapshot_node_runtime(snapshot)
            os.chmod(root, 0o500)
            return snapshot
        except BaseException:
            remove_matrix_runtime_snapshot(snapshot)
            raise
    finally:
        try:
            fcntl.flock(reconcile_lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(reconcile_lock_fd)


def remove_matrix_runtime_snapshot(snapshot: MatrixRuntimeSnapshot) -> None:
    root = snapshot.root
    try:
        if root.exists():
            _remove_runtime_snapshot_root(root)
    finally:
        try:
            fcntl.flock(snapshot.owner_lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(snapshot.owner_lock_fd)
        except OSError:
            pass


def _validate_snapshot_node_runtime(snapshot: MatrixRuntimeSnapshot) -> None:
    probe_path = snapshot.root / MATRIX_SESSION_NODE_RUNTIME_PROBE_NAME
    outside_path = snapshot.adapter_root / "package-lock.json"
    process, _payload = _spawn_bounded(
        [
            os.fspath(snapshot.node_binary),
            "--permission",
            f"--allow-fs-read={probe_path}",
            os.fspath(probe_path),
            os.fspath(outside_path),
        ],
        None,
        runtime_root=snapshot.node_binary.parent.parent,
    )
    try:
        if process.stdin is None:
            raise MatrixSessionBackendError("MATRIX_SESSION_ADAPTER_PIPE_REQUIRED")
        process.stdin.close()
        output = _communicate_bounded(
            process,
            timeout_seconds=MATRIX_SESSION_NODE_RUNTIME_PROBE_TIMEOUT_SECONDS,
            maximum_output_bytes=len(MATRIX_NODE_RUNTIME_PROBE_OUTPUT),
        )
        if process.returncode != 0:
            raise ValueError("MATRIX_SESSION_NODE_RUNTIME_PERMISSION_PROBE_FAILED")
        validate_matrix_node_runtime_probe(output)
    except ValueError:
        if process.poll() is None:
            MatrixSessionBackend._terminate_process_group(process)
        raise
    except BaseException:
        if process.poll() is None:
            MatrixSessionBackend._terminate_process_group(process)
        raise ValueError("MATRIX_SESSION_NODE_RUNTIME_VERSION_PROBE_FAILED") from None
    finally:
        if process.poll() is None:
            MatrixSessionBackend._terminate_process_group(process)
        _close_process_streams(process)


def _write_snapshot_node_runtime_probe(snapshot: MatrixRuntimeSnapshot) -> None:
    target = snapshot.root / MATRIX_SESSION_NODE_RUNTIME_PROBE_NAME
    descriptor: int | None = None
    try:
        descriptor = os.open(
            target,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o400,
        )
        view = memoryview(MATRIX_SESSION_NODE_RUNTIME_PROBE_SOURCE)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ValueError("MATRIX_SESSION_NODE_RUNTIME_PROBE_WRITE_FAILED")
            view = view[written:]
        os.fsync(descriptor)
    except BaseException:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _open_runtime_snapshot_lock(path: Path, *, create: bool) -> int:
    flags = (os.O_RDWR if create else os.O_RDONLY) | getattr(os, "O_CLOEXEC", 0)
    if create:
        flags |= os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise MatrixSessionBackendError(
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_LOCK_UNSAFE"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise MatrixSessionBackendError(
                "MATRIX_SESSION_RUNTIME_SNAPSHOT_LOCK_UNSAFE"
            )
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _reconcile_stale_runtime_snapshots(parent: Path) -> None:
    entries = tuple(parent.iterdir())
    if len(entries) > 32:
        raise MatrixSessionBackendError(
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_ENTRY_LIMIT_EXCEEDED"
        )
    for root in entries:
        if root.name == ".reconcile.lock":
            continue
        metadata = os.lstat(root)
        if (
            not root.name.startswith("snapshot-")
            or not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
        ):
            raise MatrixSessionBackendError(
                "MATRIX_SESSION_RUNTIME_SNAPSHOT_ENTRY_UNSAFE"
            )
        lock_path = root / ".owner.lock"
        if not lock_path.exists():
            _remove_runtime_snapshot_root(root)
            continue
        descriptor = _open_runtime_snapshot_lock(lock_path, create=False)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            _remove_runtime_snapshot_root(root)
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(descriptor)


def _remove_runtime_snapshot_root(root: Path) -> None:
    entries = tuple(root.rglob("*"))
    if len(entries) > 100_000:
        raise MatrixSessionBackendError(
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_CLEANUP_LIMIT_EXCEEDED"
        )
    for path in entries:
        metadata = os.lstat(path)
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode))
            or metadata.st_uid != os.getuid()
        ):
            raise MatrixSessionBackendError(
                "MATRIX_SESSION_RUNTIME_SNAPSHOT_CLEANUP_UNSAFE"
            )
    for path in sorted(entries):
        os.chmod(path, 0o700 if path.is_dir() else 0o600)
    os.chmod(root, 0o700)
    shutil.rmtree(root)
    if root.exists():
        raise MatrixSessionBackendError(
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_CLEANUP_UNCONFIRMED"
        )


def _spawn_bounded(
    argv: list[str],
    payload: dict[str, Any] | None,
    *,
    runtime_root: Path,
) -> tuple[subprocess.Popen[bytes], bytes]:
    encoded = (
        b""
        if payload is None
        else json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )
    if len(encoded) > MATRIX_SESSION_ADAPTER_INPUT_MAX_BYTES:
        raise MatrixSessionBackendError("MATRIX_SESSION_ADAPTER_INPUT_TOO_LARGE")
    process = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=matrix_node_runtime_environment(runtime_root),
        start_new_session=True,
    )
    return process, encoded


def _commit_input_bounded(
    process: subprocess.Popen[bytes],
    input_payload: bytes,
    *,
    timeout_seconds: float,
) -> None:
    """Commit the complete bounded request before start confirmation."""

    if process.stdin is None:
        raise MatrixSessionBackendError("MATRIX_SESSION_ADAPTER_PIPE_REQUIRED")
    selector = selectors.DefaultSelector()
    stdin = process.stdin
    input_offset = 0
    deadline = time.monotonic() + timeout_seconds
    try:
        os.set_blocking(stdin.fileno(), False)
        selector.register(stdin, selectors.EVENT_WRITE)
        while input_offset < len(input_payload):
            if process.poll() is not None:
                raise MatrixSessionBackendError("MATRIX_SESSION_INPUT_COMMIT_REJECTED")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout_seconds)
            events = selector.select(min(remaining, 0.1))
            if not events:
                continue
            try:
                written = os.write(
                    stdin.fileno(),
                    input_payload[input_offset : input_offset + 65536],
                )
            except BlockingIOError:
                continue
            except BrokenPipeError as exc:
                raise MatrixSessionBackendError(
                    "MATRIX_SESSION_INPUT_COMMIT_REJECTED"
                ) from exc
            if written <= 0:
                raise MatrixSessionBackendError("MATRIX_SESSION_INPUT_COMMIT_REJECTED")
            input_offset += written
    finally:
        selector.close()
        stdin.close()


def _communicate_bounded(
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float,
    maximum_output_bytes: int,
) -> bytes:
    """Collect one bounded response after the request was committed."""

    if process.stdout is None:
        raise MatrixSessionBackendError("MATRIX_SESSION_ADAPTER_PIPE_REQUIRED")
    selector = selectors.DefaultSelector()
    stdout = process.stdout
    stdout_open = True
    output = bytearray()
    deadline = time.monotonic() + timeout_seconds
    try:
        os.set_blocking(stdout.fileno(), False)
        selector.register(stdout, selectors.EVENT_READ)
        while stdout_open or process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout_seconds)
            for _key, _event in selector.select(min(remaining, 0.1)):
                read_size = min(65536, maximum_output_bytes + 1 - len(output))
                try:
                    chunk = os.read(stdout.fileno(), max(1, read_size))
                except BlockingIOError:
                    continue
                if chunk:
                    output.extend(chunk)
                    if len(output) > maximum_output_bytes:
                        raise MatrixSessionBackendError(
                            "MATRIX_SESSION_ADAPTER_OUTPUT_TOO_LARGE"
                        )
                else:
                    selector.unregister(stdout)
                    stdout.close()
                    stdout_open = False
            if process.poll() is not None and not stdout_open:
                break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, timeout_seconds)
        process.wait(timeout=remaining)
        return bytes(output)
    finally:
        selector.close()
        if stdout_open:
            stdout.close()


def _close_process_streams(process: subprocess.Popen[bytes]) -> None:
    first_error: BaseException | None = None
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None and not stream.closed:
            try:
                stream.close()
            except BaseException as exc:
                first_error = first_error or exc
    if first_error is not None:
        raise MatrixSessionBackendError(
            "MATRIX_SESSION_PROCESS_STREAM_CLEANUP_UNCONFIRMED"
        ) from first_error


def _require_safe_regular_file(path: Path) -> None:
    descriptor = _open_safe_regular_file(path)
    os.close(descriptor)


def _read_safe_private_metadata_file(path: Path) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ValueError("MATRIX_SESSION_HELPER_METADATA_UNSAFE") from exc
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or metadata.st_size > MATRIX_SESSION_HELPER_METADATA_MAX_BYTES
            or metadata.st_mode & 0o077
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise ValueError("MATRIX_SESSION_HELPER_METADATA_UNSAFE")
        payload = os.read(descriptor, MATRIX_SESSION_HELPER_METADATA_MAX_BYTES + 1)
        if len(payload) > MATRIX_SESSION_HELPER_METADATA_MAX_BYTES:
            raise ValueError("MATRIX_SESSION_HELPER_METADATA_UNSAFE")
        return payload
    finally:
        os.close(descriptor)


def _file_sha256(path: Path) -> str:
    descriptor = _open_safe_regular_file(path)
    digest = hashlib.sha256()
    try:
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _read_safe_regular_file(path: Path, *, maximum: int) -> bytes:
    descriptor = _open_safe_regular_file(path, maximum=maximum)
    try:
        payload = bytearray()
        while len(payload) <= maximum:
            chunk = os.read(descriptor, min(64 * 1024, maximum + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) > maximum:
            raise ValueError("MATRIX_SESSION_RUNTIME_FILE_TOO_LARGE")
        return bytes(payload)
    finally:
        os.close(descriptor)


def _open_safe_regular_file(
    path: Path, *, maximum: int = MATRIX_SESSION_RUNTIME_FILE_MAX_BYTES
) -> int:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ValueError("MATRIX_SESSION_RUNTIME_FILE_UNSAFE") from exc
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > maximum
            or metadata.st_mode & 0o022
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise ValueError("MATRIX_SESSION_RUNTIME_FILE_UNSAFE")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _validate_hash_bound_file(path: Path, expected: str) -> None:
    if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise ValueError("MATRIX_SESSION_RUNTIME_HASH_INVALID")
    if _file_sha256(path) != expected:
        raise ValueError("MATRIX_SESSION_RUNTIME_HASH_MISMATCH")


def _tree_sha256(root: Path) -> str:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("MATRIX_SESSION_RUNTIME_TREE_UNSAFE")
    digest = hashlib.sha256()
    entries = sorted(root.rglob("*"))
    files: list[Path] = []
    for path in entries:
        metadata = os.lstat(path)
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode))
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o022
        ):
            raise ValueError("MATRIX_SESSION_RUNTIME_TREE_UNSAFE")
        if stat.S_ISREG(metadata.st_mode):
            files.append(path)
    if not files:
        raise ValueError("MATRIX_SESSION_RUNTIME_TREE_EMPTY")
    for path in files:
        _require_safe_regular_file(path)
        relative = path.relative_to(root).as_posix().encode()
        metadata = os.lstat(path)
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(metadata.st_size).encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(_file_sha256(path)))
    return digest.hexdigest()


def _validate_runtime_integrity(
    *, adapter_root: Path, package_lock_path: Path, manifest_path: Path
) -> None:
    if adapter_root != adapter_root.resolve() or not adapter_root.is_dir():
        raise ValueError("MATRIX_SESSION_ADAPTER_ROOT_UNSAFE")
    _require_safe_regular_file(package_lock_path)
    _require_safe_regular_file(manifest_path)
    try:
        manifest = json.loads(
            _read_safe_regular_file(
                manifest_path, maximum=MATRIX_SESSION_HELPER_METADATA_MAX_BYTES
            )
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != "uaa-matrix-client-adapter-integrity.v1"
        or manifest.get("package_lock_sha256") != _file_sha256(package_lock_path)
        or manifest.get("raw_paths_included") is not False
        or manifest.get("credential_material_included") is not False
        or manifest.get("execution_authority_granted") is not False
    ):
        raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
    trees = manifest.get("trees")
    if not isinstance(trees, list) or not trees or len(trees) > 64:
        raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
    seen: set[str] = set()
    for item in trees:
        if not isinstance(item, dict) or set(item) != {"root", "sha256"}:
            raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
        relative = item.get("root")
        expected = item.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or relative in seen
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not isinstance(expected, str)
        ):
            raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
        seen.add(relative)
        root = adapter_root / relative
        if root.resolve().is_relative_to(adapter_root) is False:
            raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_INVALID")
        if _tree_sha256(root) != expected:
            raise ValueError("MATRIX_SESSION_RUNTIME_INTEGRITY_MISMATCH")
