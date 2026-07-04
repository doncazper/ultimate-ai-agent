from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeCommandAllowlistEntry,
    RuntimeCommandIntent,
    RuntimeCommandReceiptMetadata,
    RuntimeInvocationRecord,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeProfile,
    build_command_receipt,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStore


COMMAND_RUNTIME_ADAPTER_ID = "governed-command-runtime-adapter"
COMMAND_RUNTIME_WORKSPACE_REF = "workspace-ref:current-repo"
COMMAND_RUNTIME_MAX_TARGET_REFS = 12
COMMAND_RUNTIME_MAX_METADATA_REFS = 12
COMMAND_RUNTIME_MAX_TIMEOUT_SECONDS = 30.0
COMMAND_RUNTIME_MAX_OUTPUT_BYTES = 16_000
COMMAND_RUNTIME_ENV_REF = "runtime-command-env-ref:minimal-git-no-optional-locks"
COMMAND_RUNTIME_EXECUTION_PERFORMED = bool(1)
COMMAND_RUNTIME_EXECUTION_ENABLED = bool(1)


class RuntimeCommandExecutionRequest(BaseModel):
    intent: RuntimeCommandIntent
    requested_profile: RuntimeProfile = RuntimeProfile.local_runtime
    workspace_ref: str = COMMAND_RUNTIME_WORKSPACE_REF
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
        self._workspace_root = (workspace_root or Path.cwd()).resolve()
        self._runner = runner or _run_subprocess

    def invoke(
        self,
        request: RuntimeCommandExecutionRequest,
        entry: RuntimeCommandAllowlistEntry,
    ) -> _CommandAttempt:
        argv = _argv_for_entry(entry)
        _validate_exact_argv(argv)
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
    ]


def command_allowlist_entry(intent: RuntimeCommandIntent | str) -> RuntimeCommandAllowlistEntry:
    normalized = RuntimeCommandIntent(intent)
    for entry in command_allowlist_catalog():
        if entry.intent == normalized.value:
            return entry
    raise ValueError("RUNTIME_COMMAND_INTENT_NOT_ALLOWLISTED")


def invoke_governed_command(
    *,
    store: RuntimeInvocationStore,
    adapter: GovernedCommandRuntimeAdapter,
    request: RuntimeCommandExecutionRequest,
    idempotency_ref: str,
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
        force_sealed=blocked_error is not None,
    )
    created = store.create_invocation(
        invocation_request,
        idempotency_ref=idempotency_ref,
        command_gateway_validated=blocked_error is None,
    )
    record = created.record
    if blocked_error is None and _record_safe_disabled(record):
        blocked_error = "RUNTIME_COMMAND_SAFE_DISABLED"
    if created.replayed:
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
        return _record_blocked_command_result(
            store=store,
            request=request,
            entry=entry,
            record=record,
            idempotency_ref=idempotency_ref,
            operation="command-replay-without-receipt",
            error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT",
            replayed=True,
        )

    if blocked_error is not None or not record.policy_decision.allowed_to_execute:
        return _record_blocked_command_result(
            store=store,
            request=request,
            entry=entry,
            record=record,
            idempotency_ref=idempotency_ref,
            operation="command-blocked",
            error_category=blocked_error or "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED",
            replayed=False,
        )

    attempt = adapter.invoke(request, entry)
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
    updated = store.record_receipt(
        record.invocation_ref,
        receipt,
        idempotency_ref=_operation_idempotency_ref(idempotency_ref, "command-receipt"),
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
    if not entry.enabled_for_phase:
        return "RUNTIME_COMMAND_APPROVAL_BRIDGE_REQUIRED"
    if entry.approval_required:
        return "RUNTIME_COMMAND_EXACT_APPROVAL_REQUIRED"
    return None


def _record_safe_disabled(record: RuntimeInvocationRecord) -> bool:
    return record.status == RuntimeInvocationStatus.safe_disabled.value


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
    updated = store.record_receipt(
        record.invocation_ref,
        receipt,
        idempotency_ref=_operation_idempotency_ref(idempotency_ref, operation),
        payload_fingerprint_ref=_operation_fingerprint_ref(
            record.invocation_ref,
            {
                "operation": operation.replace("-", "_"),
                "metadata": metadata.model_dump(mode="json"),
            },
        ),
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
        action_ref=f"action-ref:runtime-command-{request.intent}",
        approval_ref=request.approval_ref,
        safe_summary=request.safe_summary,
        metadata_refs=[
            request.workspace_ref,
            entry.command_shape_ref,
            input_ref,
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


def _argv_for_entry(entry: RuntimeCommandAllowlistEntry) -> tuple[str, ...]:
    if entry.intent == RuntimeCommandIntent.git_status.value:
        return (
            "git",
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
    raise ValueError("RUNTIME_COMMAND_ARGV_NOT_PROMOTED")


def _validate_exact_argv(argv: tuple[str, ...]) -> None:
    if not argv:
        raise ValueError("RUNTIME_COMMAND_ARGV_REQUIRED")
    unsafe = {";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r"}
    for part in argv:
        if any(marker in part for marker in unsafe):
            raise ValueError("RUNTIME_COMMAND_ARGV_METACHAR_DENIED")
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
    return _hash_ref(
        "runtime-command-input-ref",
        {
            "intent": request.intent,
            "workspace_ref": request.workspace_ref,
            "target_refs": request.target_refs,
            "command_shape_ref": entry.command_shape_ref,
        },
    )


def _argv_ref(entry: RuntimeCommandAllowlistEntry) -> str:
    return _hash_ref(
        "runtime-command-argv-ref",
        {"command_shape_ref": entry.command_shape_ref, "intent": entry.intent},
    )


def _cwd_ref(workspace_ref: str) -> str:
    return _hash_ref("runtime-command-cwd-ref", {"workspace_ref": workspace_ref})


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
