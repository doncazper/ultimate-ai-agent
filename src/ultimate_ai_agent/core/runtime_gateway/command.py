from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import threading
import time
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeCommandAllowlistEntry,
    RuntimeCommandIntent,
    RuntimeCommandReceiptMetadata,
    RuntimeExecuteRequest,
    RuntimeInvocationRecord,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeProfile,
    build_command_receipt,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.runtime_gateway.hardline_command_blocklist import (
    hardline_block_reason_for_argv,
)
from ultimate_ai_agent.core.runtime_gateway.storage import (
    RuntimeInvocationConflictError,
    RuntimeInvocationStorageError,
    RuntimeInvocationStore,
)
from ultimate_ai_agent.core.time import utc_now


COMMAND_RUNTIME_ADAPTER_ID = "governed-command-runtime-adapter"
COMMAND_RUNTIME_WORKSPACE_REF = "workspace-ref:current-repo"
COMMAND_RUNTIME_MAX_TARGET_REFS = 12
COMMAND_RUNTIME_MAX_METADATA_REFS = 12
COMMAND_RUNTIME_MAX_TIMEOUT_SECONDS = 30.0
COMMAND_RUNTIME_MAX_OUTPUT_BYTES = 16_000
COMMAND_RUNTIME_ENV_REF = "runtime-command-env-ref:minimal-git-no-optional-locks"
COMMAND_RUNTIME_EXECUTION_PERFORMED = bool(1)
COMMAND_RUNTIME_EXECUTION_ENABLED = bool(1)
COMMAND_RUNTIME_APPROVED_REPO_ROOT = Path(__file__).resolve().parents[4]
COMMAND_RUNTIME_REPO_MARKERS = ("AGENTS.md", "pyproject.toml")
COMMAND_RUNTIME_ALLOWED_SYSTEM_EXECUTABLES = {
    "git": (Path("/usr/bin/git"), Path("/bin/git")),
    "make": (Path("/usr/bin/make"), Path("/bin/make")),
}
DEFAULT_SAFE_DISABLE_REASON_REF = "reason-ref:governed-runtime-phase-02-disabled"
COMMAND_RUNTIME_RECEIPT_GRACE_SECONDS = 1.0
ADAPTER_DISPATCH_PROTOCOL_REF = (
    "adapter-dispatch-protocol-ref:exact-boundary-attempt-v1"
)

_COMMAND_EXECUTION_LOCK_GUARD = threading.Lock()
_COMMAND_EXECUTION_PROCESS_LOCKS: weakref.WeakValueDictionary[
    int, _CommandExecutionProcessLock
] = weakref.WeakValueDictionary()
_COMMAND_EXECUTION_LOCK_FILES: dict[str, _CommandExecutionLockFile] = {}

class RuntimeCommandExecutionRequest(BaseModel):
    intent: RuntimeCommandIntent
    requested_profile: RuntimeProfile = RuntimeProfile.local_runtime
    workspace_ref: str = COMMAND_RUNTIME_WORKSPACE_REF
    mission_ref: str | None = None
    target_refs: list[str] = Field(default_factory=list, max_length=COMMAND_RUNTIME_MAX_TARGET_REFS)
    approval_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=500)
    timeout_seconds: float = Field(default=5.0, gt=0, le=COMMAND_RUNTIME_MAX_TIMEOUT_SECONDS)
    output_byte_limit: int = Field(default=4_096, gt=0, le=COMMAND_RUNTIME_MAX_OUTPUT_BYTES)
    metadata_refs: list[str] = Field(default_factory=list, max_length=COMMAND_RUNTIME_MAX_METADATA_REFS)
    network_access_requested: bool = False
    command_string_provided: bool = False
    raw_output_persisted: bool = False
    local_path_persisted: bool = False
    environment_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "RuntimeCommandExecutionRequest":
        validate_execution_ref(self.workspace_ref, "workspace_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.requested_profile not in {
            RuntimeProfile.local_runtime.value,
            RuntimeProfile.operator_approved.value,
        }:
            raise ValueError("RUNTIME_COMMAND_PROFILE_REQUIRED")
        if self.mission_ref:
            validate_execution_ref(self.mission_ref, "mission_ref")
        if self.approval_ref:
            validate_execution_ref(self.approval_ref, "approval_ref")
        for ref in self.target_refs:
            validate_execution_ref(ref, "target_ref")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        if self.network_access_requested:
            raise ValueError("RUNTIME_COMMAND_NETWORK_ACCESS_DENIED")
        if self.command_string_provided:
            raise ValueError("RUNTIME_COMMAND_STRING_DENIED")
        if self.raw_output_persisted:
            raise ValueError("RUNTIME_COMMAND_RAW_OUTPUT_PERSISTENCE_DENIED")
        if self.local_path_persisted:
            raise ValueError("RUNTIME_COMMAND_LOCAL_PATH_PERSISTENCE_DENIED")
        if self.environment_persisted:
            raise ValueError("RUNTIME_COMMAND_ENV_PERSISTENCE_DENIED")
        return self


class RuntimeCommandGatewayResult(BaseModel):
    record: RuntimeInvocationRecord
    output_summary: str | None = None
    output_summary_returned: bool = False
    output_persisted: bool = False
    exit_code: int | None = None
    timed_out: bool = False
    error_category: str | None = None
    replayed: bool = False
    command_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RuntimeCommandGatewayResult":
        if self.output_persisted:
            raise ValueError("RUNTIME_COMMAND_OUTPUT_PERSISTENCE_DENIED")
        if self.output_summary:
            validate_safe_execution_text(self.output_summary, "output_summary")
        if self.error_category:
            validate_safe_execution_text(self.error_category, "error_category")
        return self


@dataclass(frozen=True)
class RuntimeCommandRunResult:
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    output_bytes: bytes
    error_category: str | None = None


@dataclass(frozen=True)
class _CommandAttempt:
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    output_byte_count: int
    output_truncated: bool
    output_summary: str
    redacted_output_ref: str
    error_category: str | None


@dataclass
class _CommandExecutionProcessLock:
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class _CommandExecutionLockFile:
    descriptor: int
    path: Path
    users: int = 1


@dataclass
class _CommandExecutionLease:
    lock_file: _CommandExecutionLockFile
    offset: int
    process_lock: _CommandExecutionProcessLock

    def release(self) -> None:
        try:
            with _COMMAND_EXECUTION_LOCK_GUARD:
                try:
                    fcntl.lockf(
                        self.lock_file.descriptor,
                        fcntl.LOCK_UN,
                        1,
                        self.offset,
                        os.SEEK_SET,
                    )
                finally:
                    _release_command_execution_lock_file_locked(self.lock_file)
        finally:
            self.process_lock.lock.release()


class RuntimeCommandRunner(Protocol):
    def __call__(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: float,
        output_byte_limit: int,
    ) -> RuntimeCommandRunResult:
        ...


class GovernedCommandRuntimeAdapter:
    def __init__(
        self,
        *,
        workspace_root: Path | None = None,
        runner: RuntimeCommandRunner | None = None,
    ) -> None:
        self._workspace_root = _validate_workspace_root(
            workspace_root or COMMAND_RUNTIME_APPROVED_REPO_ROOT
        )
        self._runner = runner or _run_subprocess

    def invoke(
        self,
        request: RuntimeCommandExecutionRequest,
        entry: RuntimeCommandAllowlistEntry,
        *,
        pre_dispatch_guard: Callable[[], None] | None = None,
    ) -> _CommandAttempt:
        argv = _argv_for_entry(entry, workspace_root=self._workspace_root)
        hardline_block_reason = hardline_block_reason_for_argv(argv)
        if hardline_block_reason is not None:
            raise ValueError(hardline_block_reason)
        _validate_exact_argv(argv, workspace_root=self._workspace_root)
        if pre_dispatch_guard is not None:
            pre_dispatch_guard()
        result = self._runner(
            argv=argv,
            cwd=self._workspace_root,
            env=_minimal_env(),
            timeout_seconds=min(request.timeout_seconds, COMMAND_RUNTIME_MAX_TIMEOUT_SECONDS),
            output_byte_limit=request.output_byte_limit,
        )
        output_byte_count = len(result.output_bytes)
        output_truncated = output_byte_count > request.output_byte_limit
        bounded_bytes = result.output_bytes[: request.output_byte_limit]
        line_count = len([line for line in bounded_bytes.splitlines() if line.strip()])
        status_category = _status_category(result)
        summary = (
            f"Command output redacted; {line_count} bounded lines and "
            f"{min(output_byte_count, request.output_byte_limit)} bytes observed."
        )
        validate_safe_execution_text(summary, "output_summary")
        return _CommandAttempt(
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            duration_ms=result.duration_ms,
            output_byte_count=min(output_byte_count, request.output_byte_limit),
            output_truncated=output_truncated,
            output_summary=summary,
            redacted_output_ref=_redacted_output_ref(
                intent=RuntimeCommandIntent(request.intent),
                status_category=status_category,
                exit_code=result.exit_code,
                timed_out=result.timed_out,
                output_byte_count=min(output_byte_count, request.output_byte_limit),
                line_count=line_count,
            ),
            error_category=result.error_category,
        )


def command_allowlist_catalog() -> list[RuntimeCommandAllowlistEntry]:
    return [
        RuntimeCommandAllowlistEntry(
            intent=RuntimeCommandIntent.git_status,
            command_shape_ref="runtime-command-shape-ref:git-status-no-optional-locks-short-branch",
            enabled_for_phase=True,
            no_op_readonly=True,
            approval_required=False,
            exact_action_inbox_approval_required=False,
            safe_summary="Exact read-only git status command with optional writes disabled is enabled for Phase 04.",
        ),
        RuntimeCommandAllowlistEntry(
            intent=RuntimeCommandIntent.focused_pytest,
            command_shape_ref="runtime-command-shape-ref:focused-pytest",
            safe_summary="Focused pytest commands require the later exact approval bridge.",
        ),
        RuntimeCommandAllowlistEntry(
            intent=RuntimeCommandIntent.repo_verifier,
            command_shape_ref="runtime-command-shape-ref:repo-verifier",
            safe_summary="Repo verifier commands require the later exact approval bridge.",
        ),
        RuntimeCommandAllowlistEntry(
            intent=RuntimeCommandIntent.frontend_check,
            command_shape_ref="runtime-command-shape-ref:frontend-check",
            safe_summary="Frontend check commands require the later exact approval bridge.",
        ),
        RuntimeCommandAllowlistEntry(
            intent=RuntimeCommandIntent.repo_doctor,
            command_shape_ref="runtime-command-shape-ref:repo-doctor",
            safe_summary="Repo doctor commands require the later exact approval bridge.",
        ),
    ]


def command_allowlist_entry(intent: RuntimeCommandIntent | str) -> RuntimeCommandAllowlistEntry:
    normalized = RuntimeCommandIntent(intent)
    for entry in command_allowlist_catalog():
        if entry.intent == normalized.value:
            return entry
    raise ValueError("RUNTIME_COMMAND_INTENT_NOT_ALLOWLISTED")


def runtime_command_invocation_request(
    request: RuntimeCommandExecutionRequest,
) -> RuntimeInvocationRequest:
    return _runtime_invocation_request(
        request,
        entry=command_allowlist_entry(request.intent),
    )


def promoted_approval_bridge_command_intents() -> set[RuntimeCommandIntent]:
    return {
        RuntimeCommandIntent.focused_pytest,
        RuntimeCommandIntent.repo_verifier,
        RuntimeCommandIntent.frontend_check,
        RuntimeCommandIntent.repo_doctor,
    }


def _retryable_pre_dispatch_record(record: RuntimeInvocationRecord) -> bool:
    return bool(
        record.adapter_dispatch_protocol_ref == ADAPTER_DISPATCH_PROTOCOL_REF
        and not record.adapter_dispatch_started
        and record.receipt is None
    )


def _prepare_adapter_dispatch(
    *,
    store: RuntimeInvocationStore,
    record: RuntimeInvocationRecord,
    idempotency_ref: str,
    pre_adapter_dispatch: Callable[[RuntimeInvocationRecord], None] | None,
    action_inbox_envelope_ref: str | None = None,
    action_inbox_approval_ref: str | None = None,
) -> None:
    if pre_adapter_dispatch is not None:
        pre_adapter_dispatch(record)
    claim = store.mark_adapter_dispatch_started(
        record.invocation_ref,
        protocol_ref=ADAPTER_DISPATCH_PROTOCOL_REF,
        idempotency_ref=_hash_ref(
            "idempotency-ref",
            {
                "base_idempotency_ref": idempotency_ref,
                "operation": "adapter-dispatch-started",
            },
        ),
        command_gateway_validated=True,
        action_inbox_envelope_ref=action_inbox_envelope_ref,
        action_inbox_approval_ref=action_inbox_approval_ref,
    )
    if not claim.acquired:
        raise RuntimeInvocationStorageError(
            "RUNTIME_ADAPTER_DISPATCH_ALREADY_CLAIMED"
        )


def invoke_governed_command(
    *,
    store: RuntimeInvocationStore,
    adapter: GovernedCommandRuntimeAdapter,
    request: RuntimeCommandExecutionRequest,
    idempotency_ref: str,
    pre_adapter_dispatch: Callable[[RuntimeInvocationRecord], None] | None = None,
    pre_terminal_receipt: Callable[[RuntimeInvocationRecord], None] | None = None,
) -> RuntimeCommandGatewayResult:
    validate_execution_ref(idempotency_ref, "idempotency_ref")
    runtime_disabled = store.operator_safe_disable_active()
    entry = command_allowlist_entry(request.intent)
    blocked_error = _command_block_reason(
        request,
        entry=entry,
        runtime_disabled=runtime_disabled,
    )
    invocation_request = _runtime_invocation_request(
        request,
        entry=entry,
        force_sealed=blocked_error not in {
            None,
            "RUNTIME_COMMAND_SAFE_DISABLED",
        },
    )
    claim_ref = _command_execution_claim_ref(store, idempotency_ref)
    preflight_replay = _preflight_command_reservation(
        store=store,
        invocation_request=invocation_request,
        idempotency_ref=idempotency_ref,
    )
    if preflight_replay is not None:
        return preflight_replay
    execution_lease = _acquire_command_execution_lease(
        store=store,
        claim_ref=claim_ref,
        timeout_seconds=(
            request.timeout_seconds + COMMAND_RUNTIME_RECEIPT_GRACE_SECONDS
        ),
    )
    if execution_lease is None:
        return _in_progress_command_replay_result(
            store=store,
            invocation_request=invocation_request,
            idempotency_ref=idempotency_ref,
        )
    try:
        # Hold the claim-specific inter-process lease from reservation through
        # terminal receipt so API and CLI callers cannot compete for ownership.
        created = store.create_invocation(
            invocation_request,
            idempotency_ref=idempotency_ref,
            command_gateway_validated=blocked_error is None,
            action_inbox_envelope_required=(
                entry.exact_action_inbox_approval_required
            ),
            adapter_dispatch_protocol_ref=ADAPTER_DISPATCH_PROTOCOL_REF,
        )
        record = created.record
        if blocked_error is None and _record_safe_disabled(record):
            blocked_error = "RUNTIME_COMMAND_SAFE_DISABLED"
        if created.replayed:
            if record.receipt is not None:
                return _completed_command_replay_result(record)
            if (
                record.adapter_dispatch_started
                and record.adapter_dispatch_protocol_ref
                == ADAPTER_DISPATCH_PROTOCOL_REF
            ):
                return _in_progress_command_replay_result(
                    store=store,
                    invocation_request=invocation_request,
                    idempotency_ref=idempotency_ref,
                )
            if not _retryable_pre_dispatch_record(record):
                return _record_blocked_command_result(
                    store=store,
                    request=request,
                    entry=entry,
                    record=record,
                    idempotency_ref=idempotency_ref,
                    operation="command-replay-without-receipt",
                    error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT",
                    replayed=True,
                    pre_terminal_receipt=pre_terminal_receipt,
                )

        if blocked_error is not None or not record.policy_decision.allowed_to_execute:
            return _record_blocked_command_result(
                store=store,
                request=request,
                entry=entry,
                record=record,
                idempotency_ref=idempotency_ref,
                operation="command-blocked",
                error_category=blocked_error
                or "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED",
                replayed=False,
                pre_terminal_receipt=pre_terminal_receipt,
            )

        attempt = adapter.invoke(
            request,
            entry,
            pre_dispatch_guard=(
                lambda: _prepare_adapter_dispatch(
                    store=store,
                    record=record,
                    idempotency_ref=idempotency_ref,
                    pre_adapter_dispatch=pre_adapter_dispatch,
                )
            ),
        )
        status_category = _status_category(
            RuntimeCommandRunResult(
                exit_code=attempt.exit_code,
                timed_out=attempt.timed_out,
                duration_ms=attempt.duration_ms,
                output_bytes=b"",
                error_category=attempt.error_category,
            )
        )
        metadata = _command_metadata(
            request,
            entry=entry,
            record=record,
            exit_code=attempt.exit_code,
            timed_out=attempt.timed_out,
            duration_ms=attempt.duration_ms,
            output_byte_count=attempt.output_byte_count,
            output_truncated=attempt.output_truncated,
            output_summary=attempt.output_summary,
            redacted_output_ref=attempt.redacted_output_ref,
            status_category=status_category,
            error_category=attempt.error_category,
            command_execution_attempted=True,
        )
        receipt = build_command_receipt(
            record,
            metadata=metadata,
            execution_performed=COMMAND_RUNTIME_EXECUTION_PERFORMED,
            command_execution_performed=COMMAND_RUNTIME_EXECUTION_PERFORMED,
            status=RuntimeInvocationStatus.receipt_recorded,
        )
        _refresh_before_terminal_receipt(pre_terminal_receipt, record)
        updated = store.record_receipt(
            record.invocation_ref,
            receipt,
            idempotency_ref=_operation_idempotency_ref(
                idempotency_ref,
                "command-receipt",
            ),
            payload_fingerprint_ref=_operation_fingerprint_ref(
                record.invocation_ref,
                {
                    "operation": "command_receipt",
                    "metadata": metadata.model_dump(mode="json"),
                },
            ),
        )
        return RuntimeCommandGatewayResult(
            record=updated,
            output_summary=metadata.output_summary,
            output_summary_returned=True,
            exit_code=attempt.exit_code,
            timed_out=attempt.timed_out,
            error_category=attempt.error_category,
            command_execution_enabled=COMMAND_RUNTIME_EXECUTION_ENABLED,
        )
    finally:
        execution_lease.release()


def _command_execution_claim_ref(
    store: RuntimeInvocationStore,
    idempotency_ref: str,
) -> tuple[str, str]:
    return (str(store.path.resolve(strict=False)), idempotency_ref)


def _command_execution_lock_path(
    store: RuntimeInvocationStore,
) -> Path:
    return store.state_dir / ".runtime-command-execution.lock"


def _command_execution_lock_offset(claim_ref: tuple[str, str]) -> int:
    digest = hashlib.sha256(
        json.dumps(claim_ref, separators=(",", ":")).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _command_execution_process_lock(
    offset: int,
) -> _CommandExecutionProcessLock:
    with _COMMAND_EXECUTION_LOCK_GUARD:
        process_lock = _COMMAND_EXECUTION_PROCESS_LOCKS.get(offset)
        if process_lock is None:
            process_lock = _CommandExecutionProcessLock()
            _COMMAND_EXECUTION_PROCESS_LOCKS[offset] = process_lock
        return process_lock


def _retain_command_execution_lock_file(
    store: RuntimeInvocationStore,
) -> _CommandExecutionLockFile:
    lock_path = _command_execution_lock_path(store)
    lock_key = str(lock_path.resolve(strict=False))
    with _COMMAND_EXECUTION_LOCK_GUARD:
        retained = _COMMAND_EXECUTION_LOCK_FILES.get(lock_key)
        if retained is not None:
            metadata = os.fstat(retained.descriptor)
            path_metadata = os.lstat(lock_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_COMMAND_EXECUTION_LOCK_INVALID"
                )
            retained.users += 1
            return retained

        store.state_dir.mkdir(parents=True, exist_ok=True)
        directory_metadata = os.lstat(store.state_dir)
        if not stat.S_ISDIR(directory_metadata.st_mode):
            raise RuntimeInvocationStorageError(
                "RUNTIME_COMMAND_EXECUTION_LOCK_DIRECTORY_INVALID"
            )
        flags = (
            os.O_RDWR
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(lock_path, flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(lock_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise RuntimeInvocationStorageError(
                    "RUNTIME_COMMAND_EXECUTION_LOCK_INVALID"
                )
            os.fchmod(descriptor, 0o600)
        except BaseException:
            os.close(descriptor)
            raise
        retained = _CommandExecutionLockFile(
            descriptor=descriptor,
            path=lock_path,
        )
        _COMMAND_EXECUTION_LOCK_FILES[lock_key] = retained
        return retained


def _release_command_execution_lock_file_locked(
    lock_file: _CommandExecutionLockFile,
) -> None:
    lock_file.users -= 1
    if lock_file.users > 0:
        return
    lock_key = str(lock_file.path.resolve(strict=False))
    if _COMMAND_EXECUTION_LOCK_FILES.get(lock_key) is lock_file:
        del _COMMAND_EXECUTION_LOCK_FILES[lock_key]
    os.close(lock_file.descriptor)


def _release_command_execution_lock_file(
    lock_file: _CommandExecutionLockFile,
) -> None:
    with _COMMAND_EXECUTION_LOCK_GUARD:
        _release_command_execution_lock_file_locked(lock_file)


def _locked_command_reservation(
    *,
    store: RuntimeInvocationStore,
    idempotency_ref: str,
) -> RuntimeInvocationRecord | None:
    return store.get_invocation_for_idempotency_locked(idempotency_ref)


def _acquire_command_execution_lease(
    *,
    store: RuntimeInvocationStore,
    claim_ref: tuple[str, str],
    timeout_seconds: float,
) -> _CommandExecutionLease | None:
    offset = _command_execution_lock_offset(claim_ref)
    process_lock = _command_execution_process_lock(offset)
    deadline = time.monotonic() + timeout_seconds
    while not process_lock.lock.acquire(blocking=False):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            if (
                _locked_command_reservation(
                    store=store,
                    idempotency_ref=claim_ref[1],
                )
                is not None
            ):
                return None
            deadline = time.monotonic() + 0.05
            remaining = 0.05
        time.sleep(min(0.01, remaining))

    try:
        lock_file = _retain_command_execution_lock_file(store)
    except BaseException:
        process_lock.lock.release()
        raise
    try:
        while True:
            try:
                fcntl.lockf(
                    lock_file.descriptor,
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                    1,
                    offset,
                    os.SEEK_SET,
                )
                return _CommandExecutionLease(
                    lock_file=lock_file,
                    offset=offset,
                    process_lock=process_lock,
                )
            except OSError as exc:
                if exc.errno not in {
                    errno.EACCES,
                    errno.EAGAIN,
                    errno.EWOULDBLOCK,
                }:
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    durable_record = _locked_command_reservation(
                        store=store,
                        idempotency_ref=claim_ref[1],
                    )
                    if durable_record is not None:
                        try:
                            _release_command_execution_lock_file(lock_file)
                        finally:
                            process_lock.lock.release()
                        return None
                    # The owner holds the lease but has not finished its
                    # reservation. Continue the safe ownership retry until the
                    # reservation becomes visible or the lease becomes free.
                    deadline = time.monotonic() + 0.05
                    remaining = 0.05
                time.sleep(min(0.01, remaining))
    except BaseException:
        try:
            _release_command_execution_lock_file(lock_file)
        finally:
            process_lock.lock.release()
        raise


def _preflight_command_reservation(
    *,
    store: RuntimeInvocationStore,
    invocation_request: RuntimeInvocationRequest,
    idempotency_ref: str,
) -> RuntimeCommandGatewayResult | None:
    durable_record = _locked_command_reservation(
        store=store,
        idempotency_ref=idempotency_ref,
    )
    if durable_record is None:
        return None
    if (
        durable_record.payload_fingerprint_ref
        != runtime_payload_fingerprint_ref(invocation_request)
    ):
        raise RuntimeInvocationConflictError(
            "RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT"
        )
    if durable_record.receipt is None:
        return None
    replayed_record = durable_record.model_copy(
        update={"replay_count": durable_record.replay_count + 1}
    )
    return _completed_command_replay_result(replayed_record)


def _completed_command_replay_result(
    record: RuntimeInvocationRecord,
) -> RuntimeCommandGatewayResult:
    receipt = record.receipt
    if receipt is None:
        raise RuntimeInvocationStorageError(
            "RUNTIME_COMMAND_COMPLETED_REPLAY_RECEIPT_MISSING"
        )
    metadata = receipt.command_receipt_metadata
    return RuntimeCommandGatewayResult(
        record=record,
        output_summary=metadata.output_summary if metadata else None,
        output_summary_returned=metadata is not None,
        exit_code=metadata.exit_code if metadata else None,
        timed_out=metadata.timed_out if metadata else False,
        error_category=metadata.error_category if metadata else None,
        replayed=True,
        command_execution_enabled=(
            record.policy_decision.command_execution_enabled
        ),
    )


def _in_progress_command_replay_result(
    *,
    store: RuntimeInvocationStore,
    invocation_request: RuntimeInvocationRequest,
    idempotency_ref: str,
) -> RuntimeCommandGatewayResult:
    durable_record = _locked_command_reservation(
        store=store,
        idempotency_ref=idempotency_ref,
    )
    if durable_record is None:
        raise RuntimeInvocationStorageError(
            "RUNTIME_COMMAND_ACTIVE_RESERVATION_MISSING"
        )
    if (
        durable_record.payload_fingerprint_ref
        != runtime_payload_fingerprint_ref(invocation_request)
    ):
        raise RuntimeInvocationConflictError(
            "RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT"
        )
    replayed_record = durable_record.model_copy(
        update={"replay_count": durable_record.replay_count + 1}
    )
    if replayed_record.receipt is not None:
        return _completed_command_replay_result(replayed_record)
    return RuntimeCommandGatewayResult(
        record=replayed_record,
        error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS",
        replayed=True,
        command_execution_enabled=(
            replayed_record.policy_decision.command_execution_enabled
        ),
    )


def _in_progress_approved_command_replay_result(
    record: RuntimeInvocationRecord,
) -> RuntimeCommandGatewayResult:
    """Report the exact owned attempt without installing competing evidence."""

    replayed_record = record.model_copy(
        update={"replay_count": record.replay_count + 1}
    )
    if replayed_record.receipt is not None:
        return _completed_command_replay_result(replayed_record)
    return RuntimeCommandGatewayResult(
        record=replayed_record,
        error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS",
        replayed=True,
        command_execution_enabled=(
            replayed_record.policy_decision.command_execution_enabled
        ),
    )


def _run_subprocess(
    *,
    argv: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    output_byte_limit: int,
) -> RuntimeCommandRunResult:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=env,
            shell=False,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        output = (completed.stdout or b"") + (completed.stderr or b"")
        return RuntimeCommandRunResult(
            exit_code=completed.returncode,
            timed_out=False,
            duration_ms=duration_ms,
            output_bytes=output[: max(output_byte_limit + 1, 1)],
            error_category=(
                None if completed.returncode == 0 else "RUNTIME_COMMAND_NONZERO_EXIT"
            ),
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
        stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
        return RuntimeCommandRunResult(
            exit_code=None,
            timed_out=True,
            duration_ms=duration_ms,
            output_bytes=(stdout + stderr)[: max(output_byte_limit + 1, 1)],
            error_category="RUNTIME_COMMAND_TIMEOUT",
        )
    except OSError:
        duration_ms = int((time.monotonic() - start) * 1000)
        return RuntimeCommandRunResult(
            exit_code=None,
            timed_out=False,
            duration_ms=duration_ms,
            output_bytes=b"",
            error_category="RUNTIME_COMMAND_RUNNER_UNAVAILABLE",
        )


def _command_block_reason(
    request: RuntimeCommandExecutionRequest,
    *,
    entry: RuntimeCommandAllowlistEntry,
    runtime_disabled: bool,
) -> str | None:
    if runtime_disabled:
        return "RUNTIME_COMMAND_SAFE_DISABLED"
    if request.workspace_ref != COMMAND_RUNTIME_WORKSPACE_REF:
        return "RUNTIME_COMMAND_WORKSPACE_REF_NOT_ALLOWLISTED"
    if request.target_refs and request.intent == RuntimeCommandIntent.git_status.value:
        return "RUNTIME_COMMAND_TARGET_REFS_NOT_ALLOWED_FOR_STATUS"
    hardline_block_reason = _hardline_block_reason(entry)
    if hardline_block_reason is not None:
        return hardline_block_reason
    if not entry.enabled_for_phase:
        return "RUNTIME_COMMAND_APPROVAL_BRIDGE_REQUIRED"
    if entry.approval_required:
        return "RUNTIME_COMMAND_EXACT_APPROVAL_REQUIRED"
    return None


def invoke_approved_governed_command(
    *,
    store: RuntimeInvocationStore,
    adapter: GovernedCommandRuntimeAdapter,
    record: RuntimeInvocationRecord,
    request: RuntimeCommandExecutionRequest,
    execute_request: RuntimeExecuteRequest,
    idempotency_ref: str,
    pre_adapter_dispatch: Callable[[RuntimeInvocationRecord], None] | None = None,
    pre_terminal_receipt: Callable[[RuntimeInvocationRecord], None] | None = None,
) -> RuntimeCommandGatewayResult:
    validate_execution_ref(idempotency_ref, "idempotency_ref")
    envelope = record.action_inbox_envelope
    entry = command_allowlist_entry(request.intent)
    execution_payload = {
        "operation": "approved_command_execute",
        "intent": request.intent,
        "workspace_ref": request.workspace_ref,
        "target_refs": request.target_refs,
        "approval_ref": request.approval_ref,
        "execute_approval_ref": execute_request.approval_ref,
        "execute_action_envelope_ref": execute_request.action_envelope_ref,
        "execute_expected_payload_fingerprint_ref": (
            execute_request.expected_payload_fingerprint_ref
        ),
        "execute_expected_policy_decision_ref": (
            execute_request.expected_policy_decision_ref
        ),
        "envelope_ref": (
            envelope.action_envelope_ref
            if envelope
            else "runtime-action-envelope-ref:missing"
        ),
    }
    if request.mission_ref:
        execution_payload["mission_ref"] = request.mission_ref
    execution_fingerprint_ref = _operation_fingerprint_ref(
        record.invocation_ref,
        execution_payload,
    )
    replayed = store.replay_idempotent_operation(
        idempotency_ref=idempotency_ref,
        payload_fingerprint_ref=execution_fingerprint_ref,
    )
    if replayed is not None:
        record = replayed.record
        if record.receipt is not None:
            metadata = record.receipt.command_receipt_metadata
            return RuntimeCommandGatewayResult(
                record=record,
                output_summary=metadata.output_summary if metadata else None,
                output_summary_returned=metadata is not None,
                exit_code=metadata.exit_code if metadata else None,
                timed_out=metadata.timed_out if metadata else False,
                error_category=metadata.error_category if metadata else None,
                replayed=True,
                command_execution_enabled=record.policy_decision.command_execution_enabled,
            )
        if not _retryable_pre_dispatch_record(record):
            if (
                record.adapter_dispatch_started
                and record.adapter_dispatch_protocol_ref
                == ADAPTER_DISPATCH_PROTOCOL_REF
            ):
                return _in_progress_approved_command_replay_result(record)
            return _record_blocked_command_result(
                store=store,
                request=request,
                entry=entry,
                record=record,
                idempotency_ref=idempotency_ref,
                operation="approved-command-replay-without-receipt",
                error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT",
                replayed=True,
                pre_terminal_receipt=pre_terminal_receipt,
            )
    if envelope is None:
        return _record_blocked_command_result(
            store=store,
            request=request,
            entry=entry,
            record=record,
            idempotency_ref=idempotency_ref,
            operation="approved-command-envelope-missing",
            error_category="RUNTIME_COMMAND_ACTION_INBOX_ENVELOPE_MISSING",
            replayed=False,
            direct_idempotency_ref=True,
            payload_fingerprint_ref=execution_fingerprint_ref,
            pre_terminal_receipt=pre_terminal_receipt,
        )
    record = store.refresh_policy_decision_for_execution(
        record.invocation_ref,
        idempotency_ref=_operation_idempotency_ref(
            idempotency_ref,
            "authority-policy-refresh",
        ),
    )
    blocked_error = _approved_command_block_reason(
        record=record,
        request=request,
        execute_request=execute_request,
        entry=entry,
    )
    if blocked_error is not None:
        return _record_blocked_command_result(
            store=store,
            request=request,
            entry=entry,
            record=record,
            idempotency_ref=idempotency_ref,
            operation="approved-command-blocked",
            error_category=blocked_error,
            replayed=False,
            direct_idempotency_ref=True,
            payload_fingerprint_ref=execution_fingerprint_ref,
            pre_terminal_receipt=pre_terminal_receipt,
        )
    record = store.prepare_adapter_dispatch_protocol(
        record.invocation_ref,
        protocol_ref=ADAPTER_DISPATCH_PROTOCOL_REF,
        idempotency_ref=_hash_ref(
            "idempotency-ref",
            {
                "base_idempotency_ref": idempotency_ref,
                "operation": "adapter-dispatch-protocol-prepared",
            },
        ),
    )
    reserved = store.begin_action_inbox_execution(
        record.invocation_ref,
        idempotency_ref=idempotency_ref,
        payload_fingerprint_ref=execution_fingerprint_ref,
    )
    record = reserved.record
    if reserved.replayed:
        if record.receipt is not None:
            metadata = record.receipt.command_receipt_metadata
            return RuntimeCommandGatewayResult(
                record=record,
                output_summary=metadata.output_summary if metadata else None,
                output_summary_returned=metadata is not None,
                exit_code=metadata.exit_code if metadata else None,
                timed_out=metadata.timed_out if metadata else False,
                error_category=metadata.error_category if metadata else None,
                replayed=True,
                command_execution_enabled=record.policy_decision.command_execution_enabled,
            )
        if not _retryable_pre_dispatch_record(record):
            if (
                record.adapter_dispatch_started
                and record.adapter_dispatch_protocol_ref
                == ADAPTER_DISPATCH_PROTOCOL_REF
            ):
                return _in_progress_approved_command_replay_result(record)
            return _record_blocked_command_result(
                store=store,
                request=request,
                entry=entry,
                record=record,
                idempotency_ref=idempotency_ref,
                operation="approved-command-replay-without-receipt",
                error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT",
                replayed=True,
                pre_terminal_receipt=pre_terminal_receipt,
            )
    attempt = adapter.invoke(
        request,
        entry,
        pre_dispatch_guard=(
            lambda: _prepare_adapter_dispatch(
                store=store,
                record=record,
                idempotency_ref=idempotency_ref,
                pre_adapter_dispatch=pre_adapter_dispatch,
                action_inbox_envelope_ref=(
                    execute_request.action_envelope_ref
                ),
                action_inbox_approval_ref=execute_request.approval_ref,
            )
        ),
    )
    status_category = _status_category(
        RuntimeCommandRunResult(
            exit_code=attempt.exit_code,
            timed_out=attempt.timed_out,
            duration_ms=attempt.duration_ms,
            output_bytes=b"",
            error_category=attempt.error_category,
        )
    )
    metadata = _command_metadata(
        request,
        entry=entry,
        record=record,
        exit_code=attempt.exit_code,
        timed_out=attempt.timed_out,
        duration_ms=attempt.duration_ms,
        output_byte_count=attempt.output_byte_count,
        output_truncated=attempt.output_truncated,
        output_summary=attempt.output_summary,
        redacted_output_ref=attempt.redacted_output_ref,
        status_category=status_category,
        error_category=attempt.error_category,
        command_execution_attempted=True,
    )
    receipt = build_command_receipt(
        record,
        metadata=metadata,
        execution_performed=COMMAND_RUNTIME_EXECUTION_PERFORMED,
        command_execution_performed=COMMAND_RUNTIME_EXECUTION_PERFORMED,
        status=RuntimeInvocationStatus.receipt_recorded,
    )
    _refresh_before_terminal_receipt(pre_terminal_receipt, record)
    updated = store.record_receipt(
        record.invocation_ref,
        receipt,
        idempotency_ref=_operation_idempotency_ref(idempotency_ref, "approved-command-receipt"),
        payload_fingerprint_ref=_operation_fingerprint_ref(
            record.invocation_ref,
            {
                "operation": "approved_command_receipt",
                "metadata": metadata.model_dump(mode="json"),
            },
        ),
    )
    return RuntimeCommandGatewayResult(
        record=updated,
        output_summary=metadata.output_summary,
        output_summary_returned=True,
        exit_code=attempt.exit_code,
        timed_out=attempt.timed_out,
        error_category=attempt.error_category,
        command_execution_enabled=COMMAND_RUNTIME_EXECUTION_ENABLED,
    )


def _approved_command_block_reason(
    *,
    record: RuntimeInvocationRecord,
    request: RuntimeCommandExecutionRequest,
    execute_request: RuntimeExecuteRequest,
    entry: RuntimeCommandAllowlistEntry,
) -> str | None:
    envelope = record.action_inbox_envelope
    if envelope is None:
        return "RUNTIME_COMMAND_ACTION_INBOX_ENVELOPE_MISSING"
    if (
        envelope.expires_at <= utc_now()
        or record.status == RuntimeInvocationStatus.approval_expired.value
    ):
        return "RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_EXPIRED"
    explicit_safe_disable_active = (
        (envelope.safe_disable_active or record.safe_disable.active)
        and record.safe_disable.reason_ref != DEFAULT_SAFE_DISABLE_REASON_REF
    )
    if explicit_safe_disable_active:
        return "RUNTIME_COMMAND_SAFE_DISABLED"
    if envelope.approval_validated and not envelope.authority_scope_allowed:
        return "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    if record.status != RuntimeInvocationStatus.approved_pending_execution.value:
        return "RUNTIME_COMMAND_ACTION_INBOX_ENVELOPE_NOT_APPROVED"
    if not envelope.approval_validated:
        return "RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_NOT_VALIDATED"
    if request.requested_profile != RuntimeProfile.operator_approved.value:
        return "RUNTIME_COMMAND_OPERATOR_APPROVED_PROFILE_REQUIRED"
    if record.request.requested_profile != RuntimeProfile.operator_approved.value:
        return "RUNTIME_COMMAND_INVOCATION_PROFILE_WEAKENED"
    if (
        not record.policy_decision.allowed_to_execute
        or not record.policy_decision.command_execution_enabled
    ):
        return "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    if request.approval_ref != envelope.approval_ref:
        return "RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_REF_CHANGED"
    if execute_request.approval_ref != envelope.approval_ref:
        return "RUNTIME_COMMAND_EXECUTE_APPROVAL_REF_MISSING_OR_CHANGED"
    if execute_request.action_envelope_ref != envelope.action_envelope_ref:
        return "RUNTIME_COMMAND_EXECUTE_ACTION_ENVELOPE_REF_MISSING_OR_CHANGED"
    if execute_request.expected_payload_fingerprint_ref != record.payload_fingerprint_ref:
        return "RUNTIME_COMMAND_EXECUTE_PAYLOAD_REF_MISSING_OR_CHANGED"
    if (
        execute_request.expected_policy_decision_ref
        != record.policy_decision.policy_decision_ref
    ):
        return "RUNTIME_COMMAND_EXECUTE_POLICY_REF_MISSING_OR_CHANGED"
    if envelope.adapter_id != COMMAND_RUNTIME_ADAPTER_ID:
        return "RUNTIME_COMMAND_ACTION_INBOX_ADAPTER_CHANGED"
    if request.workspace_ref != COMMAND_RUNTIME_WORKSPACE_REF:
        return "RUNTIME_COMMAND_WORKSPACE_REF_NOT_ALLOWLISTED"
    hardline_block_reason = _hardline_block_reason(entry)
    if hardline_block_reason is not None:
        return hardline_block_reason
    if entry.intent not in {intent.value for intent in promoted_approval_bridge_command_intents()}:
        return "RUNTIME_COMMAND_APPROVAL_BRIDGE_INTENT_NOT_PROMOTED"
    expected_request = _runtime_invocation_request(request, entry=entry)
    if runtime_payload_fingerprint_ref(expected_request) != record.payload_fingerprint_ref:
        return "RUNTIME_COMMAND_ACTION_INBOX_SCOPE_CHANGED"
    if envelope.command_intent != RuntimeCommandIntent(request.intent).value:
        return "RUNTIME_COMMAND_ACTION_INBOX_INTENT_CHANGED"
    if envelope.payload_fingerprint_ref != record.payload_fingerprint_ref:
        return "RUNTIME_COMMAND_ACTION_INBOX_PAYLOAD_CHANGED"
    if envelope.policy_decision_ref != record.policy_decision.policy_decision_ref:
        return "RUNTIME_COMMAND_ACTION_INBOX_POLICY_STALE"
    return None


def _record_safe_disabled(record: RuntimeInvocationRecord) -> bool:
    return record.status == RuntimeInvocationStatus.safe_disabled.value


def _hardline_block_reason(entry: RuntimeCommandAllowlistEntry) -> str | None:
    argv = _argv_for_entry(entry, workspace_root=COMMAND_RUNTIME_APPROVED_REPO_ROOT)
    return hardline_block_reason_for_argv(argv)


def _record_blocked_command_result(
    *,
    store: RuntimeInvocationStore,
    request: RuntimeCommandExecutionRequest,
    entry: RuntimeCommandAllowlistEntry,
    record: RuntimeInvocationRecord,
    idempotency_ref: str,
    operation: str,
    error_category: str,
    replayed: bool,
    direct_idempotency_ref: bool = False,
    payload_fingerprint_ref: str | None = None,
    pre_terminal_receipt: Callable[[RuntimeInvocationRecord], None] | None = None,
) -> RuntimeCommandGatewayResult:
    metadata = _command_metadata(
        request,
        entry=entry,
        record=record,
        exit_code=None,
        timed_out=False,
        duration_ms=0,
        output_byte_count=0,
        output_truncated=False,
        output_summary="Command output redacted; command was blocked before process start.",
        redacted_output_ref=_redacted_output_ref(
            intent=RuntimeCommandIntent(request.intent),
            status_category="blocked",
            exit_code=None,
            timed_out=False,
            output_byte_count=0,
            line_count=0,
        ),
        status_category="blocked",
        error_category=error_category,
        command_execution_attempted=False,
    )
    receipt = build_command_receipt(
        record,
        metadata=metadata,
        execution_performed=False,
        command_execution_performed=False,
        status=RuntimeInvocationStatus.execution_blocked,
    )
    receipt_idempotency_ref = (
        idempotency_ref
        if direct_idempotency_ref
        else _operation_idempotency_ref(idempotency_ref, operation)
    )
    receipt_payload_fingerprint_ref = payload_fingerprint_ref or _operation_fingerprint_ref(
        record.invocation_ref,
        {
            "operation": operation.replace("-", "_"),
            "metadata": metadata.model_dump(mode="json"),
        },
    )
    _refresh_before_terminal_receipt(pre_terminal_receipt, record)
    updated = store.record_receipt(
        record.invocation_ref,
        receipt,
        idempotency_ref=receipt_idempotency_ref,
        payload_fingerprint_ref=receipt_payload_fingerprint_ref,
    )
    return RuntimeCommandGatewayResult(
        record=updated,
        output_summary=metadata.output_summary,
        output_summary_returned=True,
        exit_code=None,
        timed_out=False,
        error_category=metadata.error_category,
        replayed=replayed,
        command_execution_enabled=False,
    )


def _refresh_before_terminal_receipt(
    callback: Callable[[RuntimeInvocationRecord], None] | None,
    record: RuntimeInvocationRecord,
) -> None:
    if callback is not None:
        callback(record)


def _runtime_invocation_request(
    request: RuntimeCommandExecutionRequest,
    *,
    entry: RuntimeCommandAllowlistEntry,
    force_sealed: bool = False,
) -> RuntimeInvocationRequest:
    input_ref = _command_input_ref(request, entry)
    return RuntimeInvocationRequest(
        requested_authority="allowlisted_command",
        requested_profile=RuntimeProfile.sealed if force_sealed else request.requested_profile,
        input_ref=input_ref,
        mission_ref=request.mission_ref,
        action_ref=f"action-ref:runtime-command-{request.intent}",
        approval_ref=None,
        safe_summary=request.safe_summary,
        metadata_refs=[
            request.workspace_ref,
            entry.command_shape_ref,
            input_ref,
            *([request.mission_ref] if request.mission_ref else []),
            *request.target_refs,
            *request.metadata_refs,
        ],
    )


def _command_metadata(
    request: RuntimeCommandExecutionRequest,
    *,
    entry: RuntimeCommandAllowlistEntry,
    record: RuntimeInvocationRecord,
    exit_code: int | None,
    timed_out: bool,
    duration_ms: int,
    output_byte_count: int,
    output_truncated: bool,
    output_summary: str,
    redacted_output_ref: str,
    status_category: str,
    error_category: str | None,
    command_execution_attempted: bool,
) -> RuntimeCommandReceiptMetadata:
    return RuntimeCommandReceiptMetadata(
        adapter_id=COMMAND_RUNTIME_ADAPTER_ID,
        intent=RuntimeCommandIntent(request.intent),
        command_shape_ref=entry.command_shape_ref,
        argv_ref=_argv_ref(entry),
        cwd_ref=_cwd_ref(request.workspace_ref),
        environment_ref=COMMAND_RUNTIME_ENV_REF,
        profile=record.policy_decision.profile
        if record.policy_decision.profile
        in {RuntimeProfile.local_runtime.value, RuntimeProfile.operator_approved.value}
        else RuntimeProfile(request.requested_profile),
        exit_code=exit_code,
        timed_out=timed_out,
        duration_ms=duration_ms,
        output_byte_count=output_byte_count,
        output_truncated=output_truncated,
        redacted_output_ref=redacted_output_ref,
        output_summary=output_summary,
        status_category=status_category,
        error_category=error_category,
        command_execution_attempted=command_execution_attempted,
        shell_used=False,
        command_string_accepted=False,
        network_access_allowed=False,
        command_output_persisted=False,
        cwd_persisted=False,
        environment_persisted=False,
    )


def _argv_for_entry(
    entry: RuntimeCommandAllowlistEntry,
    *,
    workspace_root: Path,
) -> tuple[str, ...]:
    if entry.intent == RuntimeCommandIntent.git_status.value:
        return (
            _system_executable("git"),
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "status",
            "--short",
            "--branch",
            "--no-renames",
            "--untracked-files=no",
        )
    if entry.intent == RuntimeCommandIntent.focused_pytest.value:
        return (
            str(workspace_root / ".venv/bin/python"),
            "-m",
            "pytest",
            "tests/test_governed_runtime_contracts.py",
            "-q",
        )
    if entry.intent == RuntimeCommandIntent.repo_verifier.value:
        return (
            str(workspace_root / ".venv/bin/python"),
            "scripts/verify_documentation_integrity.py",
        )
    if entry.intent == RuntimeCommandIntent.frontend_check.value:
        return (_system_executable("make"), "frontend-check")
    if entry.intent == RuntimeCommandIntent.repo_doctor.value:
        return (_system_executable("make"), "doctor")
    raise ValueError("RUNTIME_COMMAND_ARGV_NOT_PROMOTED")


def _validate_exact_argv(argv: tuple[str, ...], *, workspace_root: Path) -> None:
    if not argv:
        raise ValueError("RUNTIME_COMMAND_ARGV_REQUIRED")
    unsafe = {";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r"}
    allowed_system = {
        candidate.resolve()
        for candidates in COMMAND_RUNTIME_ALLOWED_SYSTEM_EXECUTABLES.values()
        for candidate in candidates
        if candidate.exists()
    }
    for part in argv:
        if any(marker in part for marker in unsafe):
            raise ValueError("RUNTIME_COMMAND_ARGV_METACHAR_DENIED")
        path = Path(part)
        if path.is_absolute():
            if _is_relative_to(path, workspace_root):
                continue
            resolved = path.resolve()
            if not (
                _is_relative_to(resolved, workspace_root) or resolved in allowed_system
            ):
                raise ValueError("RUNTIME_COMMAND_ARGV_ABSOLUTE_PATH_DENIED")
            continue
        if "/" in part:
            resolved = (workspace_root / part).resolve()
            if not _is_relative_to(resolved, workspace_root):
                raise ValueError("RUNTIME_COMMAND_ARGV_RELATIVE_PATH_DENIED")
        validate_safe_execution_text(part, "runtime_command_argv_part")


def _minimal_env() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }


def _status_category(result: RuntimeCommandRunResult) -> str:
    if result.timed_out:
        return "timeout"
    if result.error_category == "RUNTIME_COMMAND_RUNNER_UNAVAILABLE":
        return "runner_unavailable"
    if result.exit_code == 0:
        return "success"
    return "nonzero_exit"


def _redacted_output_ref(
    *,
    intent: RuntimeCommandIntent,
    status_category: str,
    exit_code: int | None,
    timed_out: bool,
    output_byte_count: int,
    line_count: int,
) -> str:
    return _hash_ref(
        "runtime-command-output-ref",
        {
            "intent": intent.value,
            "status_category": status_category,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "output_byte_count": output_byte_count,
            "line_count": line_count,
        },
    )


def _command_input_ref(
    request: RuntimeCommandExecutionRequest,
    entry: RuntimeCommandAllowlistEntry,
) -> str:
    payload = {
        "intent": request.intent,
        "workspace_ref": request.workspace_ref,
        "target_refs": request.target_refs,
        "command_shape_ref": entry.command_shape_ref,
    }
    if request.mission_ref:
        payload["mission_ref"] = request.mission_ref
    return _hash_ref("runtime-command-input-ref", payload)


def _argv_ref(entry: RuntimeCommandAllowlistEntry) -> str:
    return _hash_ref(
        "runtime-command-argv-ref",
        {"command_shape_ref": entry.command_shape_ref, "intent": entry.intent},
    )


def _cwd_ref(workspace_ref: str) -> str:
    return _hash_ref("runtime-command-cwd-ref", {"workspace_ref": workspace_ref})


def _validate_workspace_root(workspace_root: Path) -> Path:
    resolved = workspace_root.resolve()
    approved = COMMAND_RUNTIME_APPROVED_REPO_ROOT.resolve()
    if resolved != approved:
        raise ValueError("RUNTIME_COMMAND_WORKSPACE_ROOT_NOT_ALLOWLISTED")
    missing = [marker for marker in COMMAND_RUNTIME_REPO_MARKERS if not (resolved / marker).exists()]
    if missing:
        raise ValueError("RUNTIME_COMMAND_WORKSPACE_ROOT_MARKERS_MISSING")
    return resolved


def _system_executable(name: str) -> str:
    for candidate in COMMAND_RUNTIME_ALLOWED_SYSTEM_EXECUTABLES.get(name, ()):
        if candidate.exists():
            return str(candidate.resolve())
    raise ValueError("RUNTIME_COMMAND_SYSTEM_EXECUTABLE_UNAVAILABLE")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _operation_idempotency_ref(base_ref: str, operation: str) -> str:
    return _hash_ref(
        "idempotency-ref",
        {
            "base_idempotency_ref": base_ref,
            "operation": operation,
        },
    )


def _operation_fingerprint_ref(invocation_ref: str, payload: object) -> str:
    return _hash_ref(
        "runtime-operation-fingerprint-ref",
        {
            "invocation_ref": invocation_ref,
            "payload": payload,
        },
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_ref(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"
