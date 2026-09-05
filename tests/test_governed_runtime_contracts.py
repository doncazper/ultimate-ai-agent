import argparse
import errno
import hashlib
import json
import multiprocessing
import os
import stat
import threading
import subprocess
import sys
import time
import weakref
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.dev import uaa_runtime
import ultimate_ai_agent.core.runtime_gateway.command as runtime_command
import ultimate_ai_agent.core.runtime_gateway.storage as runtime_storage
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    HermesChatRequest,
    HermesCliAdapter,
    HermesProcessResult,
    LocalModelRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandGatewayResult,
    RuntimeCommandRunResult,
    RuntimeCriterionVerificationBinding,
    RuntimeGateway,
    RuntimeInvocationConflictError,
    RuntimeInvocationRecord,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeInvocationStore,
    RuntimeLocalModelCallRequest,
    RuntimeLocalModelMessage,
    build_default_runtime_capabilities,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.runtime_gateway.interface_mode import (
    HERMES_CHAT_AUTHORITY_CAPABILITY_REF,
    HERMES_CHAT_AUTHORITY_DOMAIN_REF,
    HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF,
    HERMES_CLI_ENV,
    HERMES_INTERFACE_MODE_ENABLED_ENV,
)
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    GoalRuntimeCorruptionError,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeApprovalBindingRequest,
    RuntimeExecuteRequest,
    RuntimeLocalModelReceiptMetadata,
    RuntimeSafeDisableRequest,
    build_local_model_receipt,
    build_policy_decision,
    runtime_invocation_ref,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStorageError
from ultimate_ai_agent.core.runtime_gateway.storage import (
    RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON,
)
from ultimate_ai_agent.core.local_model_management import FakeM164GatewayTransport
from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.time import utc_now
from tests.authority_helpers import (
    issue_workspace_execute_authority_lease,
    provider_model_execute_authority_lease,
    workspace_execute_authority_lease,
    workspace_execute_mission_authority_lease,
)


ROOT = Path(__file__).resolve().parents[1]
REDACTED_TEST_PROMPT = "[redacted-test-input]"


def _hold_runtime_gateway_store_lock(
    state_dir: Path,
    started_path: Path,
    release_path: Path,
) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        state_dir / runtime_storage.RUNTIME_GATEWAY_LOCK,
        os.O_RDWR | os.O_CREAT,
        0o600,
    )
    try:
        runtime_storage.fcntl.flock(
            descriptor,
            runtime_storage.fcntl.LOCK_EX,
        )
        started_path.write_text("started", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not release_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        runtime_storage.fcntl.flock(
            descriptor,
            runtime_storage.fcntl.LOCK_UN,
        )
        os.close(descriptor)


def _run_cross_process_command_owner(
    state_dir: Path,
    started_path: Path,
    release_path: Path,
) -> None:
    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        started_path.write_text("started", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not release_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not release_path.exists():
            raise RuntimeError("cross-process runtime command release timed out")
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    result = RuntimeGateway(
        store=RuntimeInvocationStore(state_dir),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    ).invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect current repo status with redacted output.",
            timeout_seconds=0.05,
        ),
        idempotency_ref="idempotency-ref:runtime-command-cross-process",
    )
    if result.record.receipt is None:
        raise RuntimeError("cross-process runtime command receipt missing")


def _hold_cross_process_command_lease_before_reservation(
    state_dir: Path,
    started_path: Path,
    release_path: Path,
) -> None:
    store = RuntimeInvocationStore(state_dir)
    claim_ref = runtime_command._command_execution_claim_ref(
        store,
        "idempotency-ref:runtime-command-pre-reservation",
    )
    lease = runtime_command._acquire_command_execution_lease(
        store=store,
        claim_ref=claim_ref,
        timeout_seconds=1.0,
    )
    if lease is None:
        raise RuntimeError("cross-process pre-reservation lease missing")
    try:
        started_path.write_text("started", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not release_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not release_path.exists():
            raise RuntimeError("cross-process pre-reservation release timed out")
    finally:
        lease.release()


def _probe_command_execution_byte_range(
    lock_path: Path,
    offset: int,
    result_path: Path,
) -> None:
    descriptor = os.open(lock_path, os.O_RDWR)
    try:
        try:
            runtime_command.fcntl.lockf(
                descriptor,
                runtime_command.fcntl.LOCK_EX | runtime_command.fcntl.LOCK_NB,
                1,
                offset,
                os.SEEK_SET,
            )
        except BlockingIOError:
            result_path.write_text("blocked", encoding="utf-8")
        else:
            result_path.write_text("acquired", encoding="utf-8")
            runtime_command.fcntl.lockf(
                descriptor,
                runtime_command.fcntl.LOCK_UN,
                1,
                offset,
                os.SEEK_SET,
            )
    finally:
        os.close(descriptor)


class _BlockingFakeM164GatewayTransport(FakeM164GatewayTransport):
    def __init__(
        self,
        content: str,
        *,
        transport_started: threading.Event,
        release_transport: threading.Event,
    ) -> None:
        super().__init__(content)
        self._transport_started = transport_started
        self._release_transport = release_transport

    def chat_completions(
        self,
        gateway_model: Any,
        chat_request: Any,
        *,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        self._transport_started.set()
        assert self._release_transport.wait(timeout=5)
        return super().chat_completions(
            gateway_model,
            chat_request,
            api_key=api_key,
        )


def _runtime_store_with_workspace_execute(tmp_path: Path) -> RuntimeInvocationStore:
    return RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[workspace_execute_authority_lease()],
    )


def _runtime_store_with_provider_model_execute(
    tmp_path: Path,
) -> RuntimeInvocationStore:
    return RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[provider_model_execute_authority_lease()],
    )


def test_hermes_cli_chat_requires_workspace_execute_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    called = False

    def runner(**_kwargs) -> HermesProcessResult:
        nonlocal called
        called = True
        return HermesProcessResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"should not run",
        )

    receipt = HermesCliAdapter(runner=runner, cwd=tmp_path).chat(
        HermesChatRequest(
            mode="shell_guarded",
            query="summarize current safe runtime posture",
        ),
        idempotency_ref="idempotency-ref:hermes-chat-no-authority",
        active_authority_leases=[],
    )

    assert receipt.status == "blocked"
    assert receipt.execution_performed is False
    assert called is False
    assert receipt.authority_decision_outcome == "deny"
    assert receipt.authority_lease_ref is None
    assert receipt.authority_domain_ref == HERMES_CHAT_AUTHORITY_DOMAIN_REF
    assert receipt.authority_capability_ref == HERMES_CHAT_AUTHORITY_CAPABILITY_REF
    assert HERMES_CHAT_AUTHORITY_REQUIRED_BLOCKED_REF in receipt.blocked_reason_refs


def test_hermes_cli_chat_records_authority_refs_when_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hermes_bin = tmp_path / "hermes"
    hermes_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hermes_bin.chmod(0o755)
    monkeypatch.setenv(HERMES_INTERFACE_MODE_ENABLED_ENV, "1")
    monkeypatch.setenv(HERMES_CLI_ENV, str(hermes_bin))
    observed_argv: tuple[str, ...] | None = None

    def runner(**kwargs) -> HermesProcessResult:
        nonlocal observed_argv
        observed_argv = kwargs["argv"]
        return HermesProcessResult(
            exit_code=0,
            timed_out=False,
            duration_ms=2,
            output_bytes=b"safe redacted answer",
        )

    receipt = HermesCliAdapter(runner=runner, cwd=tmp_path).chat(
        HermesChatRequest(
            mode="shell_guarded",
            query="summarize current safe runtime posture",
        ),
        idempotency_ref="idempotency-ref:hermes-chat-allowed",
        active_authority_leases=[workspace_execute_authority_lease()],
    )

    assert observed_argv is not None
    assert observed_argv[:2] == (str(hermes_bin), "chat")
    assert "--query" in observed_argv
    assert receipt.status == "receipt_recorded"
    assert receipt.execution_performed is True
    assert receipt.authority_decision_outcome == "allow"
    assert receipt.authority_lease_ref == "authority-lease-ref:test-workspace-execute"
    assert receipt.authority_domain_ref == HERMES_CHAT_AUTHORITY_DOMAIN_REF
    assert receipt.authority_capability_ref == HERMES_CHAT_AUTHORITY_CAPABILITY_REF
    assert receipt.authority_audit_ref
    assert receipt.authority_policy_receipt_ref


def _runtime_request(
    summary: str = "safe governed runtime summary",
) -> RuntimeInvocationRequest:
    return RuntimeInvocationRequest(
        requested_authority="local_model",
        requested_profile="sealed",
        input_ref="runtime-input-ref:test",
        safe_summary=summary,
        metadata_refs=["metadata-ref:governed-runtime-test"],
    )


def test_runtime_profiles_default_to_sealed_and_do_not_execute() -> None:
    capabilities = build_default_runtime_capabilities()
    payload = capabilities.model_dump(mode="json")

    assert payload["default_profile"] == "sealed"
    assert payload["adapter_execution_enabled"] is False
    assert payload["model_call_enabled"] is False
    assert payload["command_execution_enabled"] is False
    assert payload["approval_required_for_execution"] is True
    assert (
        "authority-ref:runtime-local-model-loopback-phase-03"
        in payload["implemented_authority_refs"]
    )
    assert (
        "authority-ref:runtime-allowlisted-readonly-command-phase-04"
        in payload["implemented_authority_refs"]
    )
    assert (
        "blocked-authority:runtime-unrestricted-command-execution"
        in payload["blocked_authority_refs"]
    )
    assert (
        "blocked-authority:runtime-command-execution-without-gateway-allowlist"
        in (payload["blocked_authority_refs"])
    )


def test_generic_runtime_policy_does_not_enable_local_model_without_gateway_validation() -> (
    None
):
    request = RuntimeInvocationRequest(
        requested_authority="local_model",
        requested_profile="local-runtime",
        input_ref="runtime-input-ref:test",
        safe_summary="safe governed runtime summary",
    )
    payload_ref = runtime_payload_fingerprint_ref(request)
    invocation_ref = runtime_invocation_ref(
        "idempotency-ref:runtime-generic-local-model",
        payload_ref,
    )

    decision = build_policy_decision(request, invocation_ref=invocation_ref)
    allowed = build_policy_decision(
        request,
        invocation_ref=invocation_ref,
        local_model_gateway_validated=True,
    )

    assert decision.allowed_to_execute is False
    assert decision.adapter_execution_enabled is False
    assert decision.model_call_enabled is False
    assert "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_GATEWAY_VALIDATION_REQUIRED" in (
        decision.reason_codes
    )
    assert allowed.allowed_to_execute is True


def test_generic_runtime_policy_does_not_enable_command_without_gateway_validation() -> (
    None
):
    request = RuntimeInvocationRequest(
        requested_authority="allowlisted_command",
        requested_profile="local-runtime",
        input_ref="runtime-command-input-ref:test",
        safe_summary="safe governed runtime command summary",
    )
    payload_ref = runtime_payload_fingerprint_ref(request)
    invocation_ref = runtime_invocation_ref(
        "idempotency-ref:runtime-generic-command",
        payload_ref,
    )

    decision = build_policy_decision(request, invocation_ref=invocation_ref)
    allowed = build_policy_decision(
        request,
        invocation_ref=invocation_ref,
        command_gateway_validated=True,
    )

    assert decision.allowed_to_execute is False
    assert decision.adapter_execution_enabled is False
    assert decision.command_execution_enabled is False
    assert "GOVERNED_RUNTIME_PHASE_04_COMMAND_GATEWAY_VALIDATION_REQUIRED" in (
        decision.reason_codes
    )
    assert allowed.allowed_to_execute is True
    assert allowed.command_execution_enabled is True


def test_runtime_contracts_reject_unsafe_persistence_and_extra_router_fields() -> None:
    with pytest.raises(ValidationError):
        RuntimeInvocationRequest(
            requested_authority="local_model",
            input_ref="runtime-input-ref:test",
            safe_summary="safe governed runtime summary",
            response_content_persisted=True,
        )

    with pytest.raises(ValidationError):
        RuntimeInvocationRequest(
            requested_authority="local_model",
            input_ref="runtime-input-ref:test",
            safe_summary="safe governed runtime summary",
            base_model="model-router-language-is-not-runtime-gateway",
        )

    with pytest.raises(ValidationError):
        _runtime_request("unsafe /Users/example/path must not persist")

    with pytest.raises(ValidationError):
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="safe governed runtime command summary",
            command_string_provided=True,
        )

    with pytest.raises(ValidationError):
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="safe governed runtime command summary",
            network_access_requested=True,
        )


def test_runtime_receipts_cannot_claim_execution() -> None:
    request = _runtime_request()
    payload_ref = runtime_payload_fingerprint_ref(request)
    invocation_ref = runtime_invocation_ref(
        "idempotency-ref:runtime-contract", payload_ref
    )
    decision = build_policy_decision(request, invocation_ref=invocation_ref)

    with pytest.raises(ValidationError):
        RuntimeInvocationReceipt(
            receipt_ref="runtime-receipt-ref:test",
            invocation_ref=invocation_ref,
            policy_decision_ref=decision.policy_decision_ref,
            invocation_status=RuntimeInvocationStatus.execution_blocked,
            execution_performed=True,
        )


def test_runtime_criterion_verifier_provenance_requires_exact_terminal_goal() -> None:
    binding = RuntimeCriterionVerificationBinding(
        goal_ref="goal-ref:criterion-provenance",
        goal_version=2,
        criterion_ref="criterion-ref:criterion-provenance:one",
        proof_ref="proof-ref:criterion-provenance:one",
        verifier_ref="verifier-ref:criterion-provenance",
        evaluator_receipt_ref="receipt-ref:evaluator:criterion-provenance:one",
    )
    request = _runtime_request()
    payload_ref = runtime_payload_fingerprint_ref(request)
    invocation_ref = runtime_invocation_ref(
        "idempotency-ref:criterion-provenance",
        payload_ref,
    )
    decision = build_policy_decision(request, invocation_ref=invocation_ref)
    with pytest.raises(
        ValidationError,
        match="RUNTIME_CRITERION_VERIFICATION_TERMINAL_RECEIPT_REQUIRED",
    ):
        RuntimeInvocationReceipt(
            receipt_ref="runtime-receipt-ref:criterion-provenance",
            invocation_ref=invocation_ref,
            policy_decision_ref=decision.policy_decision_ref,
            invocation_status=RuntimeInvocationStatus.execution_blocked,
            criterion_verification_bindings=[binding],
        )

    receipt = RuntimeInvocationReceipt(
        receipt_ref="runtime-receipt-ref:criterion-provenance",
        invocation_ref=invocation_ref,
        policy_decision_ref=decision.policy_decision_ref,
        invocation_status=RuntimeInvocationStatus.receipt_recorded,
        criterion_verification_bindings=[binding],
    )
    with pytest.raises(
        ValidationError,
        match="RUNTIME_CRITERION_VERIFICATION_GOAL_BINDING_MISMATCH",
    ):
        RuntimeInvocationRecord.model_validate(
            {
                "invocation_ref": invocation_ref,
                "request": request.model_dump(mode="json"),
                "policy_decision": decision.model_dump(mode="json"),
                "approval_requirement": (
                    decision.approval_requirement.model_dump(mode="json")
                ),
                "receipt": receipt.model_dump(mode="json"),
                "payload_fingerprint_ref": payload_ref,
                "idempotency_ref": "idempotency-ref:criterion-provenance",
                "status": RuntimeInvocationStatus.receipt_recorded,
            }
        )


def test_runtime_store_persists_safe_refs_only_and_replays_idempotency(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    request = _runtime_request("operator provided summary should not persist")

    created = store.create_invocation(
        request,
        idempotency_ref="idempotency-ref:runtime-store",
    )
    replayed = store.create_invocation(
        request,
        idempotency_ref="idempotency-ref:runtime-store",
    )

    assert created.replayed is False
    assert replayed.replayed is True
    assert replayed.record.invocation_ref == created.record.invocation_ref

    changed = _runtime_request("safe governed runtime summary changed")
    with pytest.raises(RuntimeInvocationConflictError):
        store.create_invocation(
            changed, idempotency_ref="idempotency-ref:runtime-store"
        )

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "operator provided summary should not persist" not in persisted
    for forbidden in [
        "raw prompt",
        "raw response",
        "stdout",
        "stderr",
        "/Users/",
        "api_key=",
        "authorization:",
    ]:
        assert forbidden not in persisted


def test_runtime_store_records_blocked_execute_and_detects_tampering(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    created = store.create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:runtime-tamper",
    )
    updated = store.record_blocked_execute(
        created.record.invocation_ref,
        safe_summary="operator execute summary should not persist",
        idempotency_ref="idempotency-ref:runtime-execute",
    )

    assert updated.receipt is not None
    assert updated.receipt.execution_performed is False
    assert updated.status == "execution_blocked"

    path = tmp_path / "runtime_gateway_invocations.jsonl"
    text = path.read_text(encoding="utf-8")
    assert "operator execute summary should not persist" not in text
    path.write_text(
        text.replace("execution_blocked", "receipt_recorded", 1), encoding="utf-8"
    )

    with pytest.raises(RuntimeInvocationStorageError):
        RuntimeInvocationStore(tmp_path).list_invocations()


def test_runtime_store_replays_mutating_operation_idempotency(tmp_path: Path) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    created = store.create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:runtime-mutation-create",
    )
    invocation_ref = created.record.invocation_ref

    approval = RuntimeApprovalBindingRequest(
        approval_ref="approval-ref:runtime-mutation"
    )
    first_approval = store.bind_approval(
        invocation_ref,
        approval,
        idempotency_ref="idempotency-ref:runtime-mutation-approval",
    )
    second_approval = store.bind_approval(
        invocation_ref,
        approval,
        idempotency_ref="idempotency-ref:runtime-mutation-approval",
    )

    assert first_approval.status == "pending_approval"
    assert second_approval.invocation_ref == first_approval.invocation_ref

    first_execute = store.record_blocked_execute(
        invocation_ref,
        safe_summary="operator execute replay summary should not persist",
        idempotency_ref="idempotency-ref:runtime-mutation-execute",
    )
    second_execute = store.record_blocked_execute(
        invocation_ref,
        safe_summary="operator execute replay summary should not persist",
        idempotency_ref="idempotency-ref:runtime-mutation-execute",
    )

    assert first_execute.receipt is not None
    assert second_execute.receipt is not None

    first_disable = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-mutation-disable"),
        idempotency_ref="idempotency-ref:runtime-mutation-disable",
    )
    second_disable = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-mutation-disable"),
        idempotency_ref="idempotency-ref:runtime-mutation-disable",
    )

    assert first_disable.safe_disable_ref == second_disable.safe_disable_ref
    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert len(persisted.splitlines()) == 4
    assert "operator execute replay summary should not persist" not in persisted


def test_runtime_store_safe_disable_sidecar_requires_durable_ledger(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    state = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-safe-disable-sidecar"),
        idempotency_ref="idempotency-ref:runtime-safe-disable-sidecar",
    )
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    assert state.active is True
    assert state_path.exists()
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved["active"] is True
    assert saved["reason_ref"] == "reason-ref:runtime-safe-disable-sidecar"

    (tmp_path / "runtime_gateway_invocations.jsonl").unlink()
    reloaded = RuntimeInvocationStore(tmp_path)
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
    ):
        reloaded.operator_safe_disable_active()


def test_runtime_store_safe_disable_replay_returns_original_without_rollback(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    first = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:safe-disable-first"),
        idempotency_ref="idempotency-ref:safe-disable-first",
    )
    second = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:safe-disable-second"),
        idempotency_ref="idempotency-ref:safe-disable-second",
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    before_replay = ledger_path.read_bytes()

    replayed_first = store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:safe-disable-first"),
        idempotency_ref="idempotency-ref:safe-disable-first",
    )

    assert replayed_first == first
    assert replayed_first != second
    assert ledger_path.read_bytes() == before_replay
    assert store.operator_safe_disable_state() == second
    assert RuntimeInvocationStore(tmp_path).operator_safe_disable_state() == second
    sidecar = json.loads(
        (tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).read_text(encoding="utf-8")
    )
    assert sidecar["reason_ref"] == "reason-ref:safe-disable-second"


def test_runtime_store_safe_disable_sidecar_rejects_deactivation_tamper(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-sidecar-active"),
        idempotency_ref="idempotency-ref:runtime-sidecar-active",
    )
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["active"] = False
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    reloaded = RuntimeInvocationStore(tmp_path)
    for _attempt in range(2):
        with pytest.raises(
            RuntimeInvocationStorageError,
            match="RUNTIME_SAFE_DISABLE_STATE_INVALID",
        ):
            reloaded.operator_safe_disable_active()


@pytest.mark.parametrize(
    "encoded",
    [
        b"[]",
        b'{"active":',
        b"x" * 16_385,
    ],
)
def test_runtime_store_safe_disable_sidecar_rejects_malformed_or_oversized_state(
    tmp_path: Path,
    encoded: bytes,
) -> None:
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    tmp_path.mkdir(parents=True, exist_ok=True)
    state_path.write_bytes(encoded)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_active()


def test_runtime_store_safe_disable_sidecar_rejects_symlink_substitution(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-sidecar-symlink"),
        idempotency_ref="idempotency-ref:runtime-sidecar-symlink",
    )
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    external = tmp_path / "external-safe-disable-state.json"
    external.write_bytes(state_path.read_bytes())
    state_path.unlink()
    state_path.symlink_to(external)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_active()


def test_runtime_store_safe_disable_sidecar_must_match_durable_ledger(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-sidecar-ledger"),
        idempotency_ref="idempotency-ref:runtime-sidecar-ledger",
    )
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["reason_ref"] = "reason-ref:runtime-sidecar-substitution"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_active()


def test_runtime_store_rejects_sidecar_without_matching_ledger_state(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source = RuntimeInvocationStore(source_dir)
    source.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:sidecar-without-ledger"),
        idempotency_ref="idempotency-ref:sidecar-without-ledger",
    )

    target_dir = tmp_path / "target"
    target = RuntimeInvocationStore(target_dir)
    target.create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:target-ledger-without-safe-disable",
    )
    (target_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).write_bytes(
        (source_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).read_bytes()
    )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
    ):
        RuntimeInvocationStore(target_dir).operator_safe_disable_active()


@pytest.mark.parametrize("ledger_payload", [b"", b"\n\n"])
def test_runtime_store_rejects_sidecar_with_empty_present_ledger(
    tmp_path: Path,
    ledger_payload: bytes,
) -> None:
    source_dir = tmp_path / "source"
    source = RuntimeInvocationStore(source_dir)
    source.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:sidecar-empty-ledger"),
        idempotency_ref="idempotency-ref:sidecar-empty-ledger",
    )

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "runtime_gateway_invocations.jsonl").write_bytes(ledger_payload)
    (target_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).write_bytes(
        (source_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).read_bytes()
    )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
    ):
        RuntimeInvocationStore(target_dir).operator_safe_disable_active()


@pytest.mark.parametrize("dangling", [False, True])
def test_runtime_store_rejects_sidecar_with_symlinked_present_ledger(
    tmp_path: Path,
    dangling: bool,
) -> None:
    source_dir = tmp_path / "source"
    source = RuntimeInvocationStore(source_dir)
    source.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:sidecar-symlink-ledger"),
        idempotency_ref="idempotency-ref:sidecar-symlink-ledger",
    )

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    symlink_target = target_dir / "substituted-ledger.jsonl"
    if not dangling:
        symlink_target.write_text("", encoding="utf-8")
    (target_dir / "runtime_gateway_invocations.jsonl").symlink_to(symlink_target)
    (target_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).write_bytes(
        (source_dir / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).read_bytes()
    )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(target_dir).operator_safe_disable_active()


def test_runtime_store_mutation_lock_rejects_symlinked_state_root_ancestor(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    state_dir = linked_parent / "runtime"

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(state_dir).list_invocations_locked()

    assert not (real_parent / "runtime" / "runtime_gateway_invocations.lock").exists()


def test_runtime_store_lock_contention_fails_closed_within_bounded_wait(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "runtime"
    started_path = tmp_path / "lock-started"
    release_path = tmp_path / "lock-release"
    process = multiprocessing.Process(
        target=_hold_runtime_gateway_store_lock,
        args=(state_dir, started_path, release_path),
    )
    process.start()
    deadline = time.monotonic() + 5
    while not started_path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert started_path.exists()
    monkeypatch.setattr(
        runtime_storage,
        "RUNTIME_GATEWAY_LOCK_TIMEOUT_SECONDS",
        0.05,
    )
    monkeypatch.setattr(
        runtime_storage,
        "RUNTIME_GATEWAY_LOCK_POLL_SECONDS",
        0.001,
    )

    started = time.monotonic()
    try:
        with pytest.raises(
            RuntimeInvocationStorageError,
            match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
        ):
            RuntimeInvocationStore(state_dir).list_invocations_locked()
        assert time.monotonic() - started < 1
    finally:
        release_path.write_text("release", encoding="utf-8")
        process.join(timeout=5)
        if process.is_alive():  # pragma: no cover - cleanup on failure
            process.terminate()
            process.join(timeout=1)
    assert process.exitcode == 0


def test_runtime_store_pins_validated_state_root_descriptor_through_lock_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "runtime"
    preserved_dir = tmp_path / "runtime-preserved"
    store = RuntimeInvocationStore(state_dir)
    real_open = os.open
    exchanged = False

    def exchanging_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal exchanged
        if (
            not exchanged
            and path == runtime_storage.RUNTIME_GATEWAY_LOCK
            and dir_fd is not None
        ):
            exchanged = True
            state_dir.rename(preserved_dir)
            state_dir.mkdir(mode=0o700)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", exchanging_open)
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        store.list_invocations_locked()

    assert exchanged is True
    assert (preserved_dir / runtime_storage.RUNTIME_GATEWAY_LOCK).is_file()
    assert not (state_dir / runtime_storage.RUNTIME_GATEWAY_LOCK).exists()


def test_runtime_store_uses_pinned_state_root_descriptor_for_first_ledger_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "runtime"
    preserved_dir = tmp_path / "runtime-preserved"
    substituted_dir = tmp_path / "runtime-substituted"
    store = RuntimeInvocationStore(state_dir)
    original_append = store._append_ledger_line  # noqa: SLF001
    exchanged = False

    def exchange_then_append(encoded_line: bytes) -> None:
        nonlocal exchanged
        if not exchanged:
            exchanged = True
            state_dir.rename(preserved_dir)
            state_dir.mkdir(mode=0o700)
        original_append(encoded_line)

    monkeypatch.setattr(store, "_append_ledger_line", exchange_then_append)
    try:
        result = store.safe_disable(
            RuntimeSafeDisableRequest(
                reason_ref="reason-ref:pinned-state-root-first-write"
            ),
            idempotency_ref="idempotency-ref:pinned-state-root-first-write",
        )

        assert exchanged is True
        assert result.active is True
        assert (preserved_dir / runtime_storage.RUNTIME_GATEWAY_JSONL).is_file()
        assert (
            preserved_dir / runtime_storage.RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
        ).is_file()
        assert not (state_dir / runtime_storage.RUNTIME_GATEWAY_JSONL).exists()
        assert not (
            state_dir / runtime_storage.RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
        ).exists()
    finally:
        if state_dir.exists():
            state_dir.rename(substituted_dir)
        if preserved_dir.exists():
            preserved_dir.rename(state_dir)


def test_runtime_store_ledger_read_rejects_inode_substitution_between_stat_and_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:ledger-inode-race"),
        idempotency_ref="idempotency-ref:ledger-inode-race",
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    replacement_path = tmp_path / "replacement-ledger.jsonl"
    replacement_path.write_bytes(ledger_path.read_bytes())
    real_open = os.open
    substituted = False

    def substituting_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal substituted
        if (
            not substituted
            and path == "runtime_gateway_invocations.jsonl"
            and dir_fd is not None
            and not flags & (os.O_WRONLY | os.O_RDWR)
        ):
            substituted = True
            ledger_path.unlink()
            ledger_path.symlink_to(replacement_path)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", substituting_open)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_active()
    assert substituted is True


def test_runtime_store_ledger_append_rejects_inode_substitution_after_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RuntimeInvocationStore(tmp_path).create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:ledger-append-inode-race",
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    replacement_path = tmp_path / "replacement-append-ledger.jsonl"
    replacement_path.write_bytes(ledger_path.read_bytes())
    replacement_bytes = replacement_path.read_bytes()
    real_open = os.open
    substituted = False

    def substituting_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal substituted
        if (
            not substituted
            and path == "runtime_gateway_invocations.jsonl"
            and dir_fd is not None
            and flags & os.O_WRONLY
        ):
            substituted = True
            os.replace(replacement_path, ledger_path)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", substituting_open)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).safe_disable(
            RuntimeSafeDisableRequest(reason_ref="reason-ref:ledger-append-race"),
            idempotency_ref="idempotency-ref:ledger-append-race",
        )
    assert substituted is True
    assert ledger_path.read_bytes() == replacement_bytes
    assert not (tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).exists()


def test_runtime_store_fsyncs_ledger_before_publishing_safe_disable_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    ordering: list[str] = []
    real_fsync = os.fsync
    real_replace = os.replace

    def recording_fsync(fd: int) -> None:
        if ledger_path.exists() and os.path.samestat(
            os.fstat(fd),
            os.stat(ledger_path, follow_symlinks=False),
        ):
            ordering.append("ledger_fsync")
        real_fsync(fd)

    def recording_replace(*args: object, **kwargs: object) -> None:
        ordering.append("sidecar_replace")
        real_replace(*args, **kwargs)

    monkeypatch.setattr(os, "fsync", recording_fsync)
    monkeypatch.setattr(os, "replace", recording_replace)

    RuntimeInvocationStore(tmp_path).safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:ledger-fsync-order"),
        idempotency_ref="idempotency-ref:ledger-fsync-order",
    )

    assert ordering.count("ledger_fsync") >= 1
    assert max(
        index for index, event in enumerate(ordering) if event == "ledger_fsync"
    ) < ordering.index("sidecar_replace")


def test_runtime_store_ledger_append_rejects_inode_substitution_after_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RuntimeInvocationStore(tmp_path).create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:ledger-post-append-race-setup",
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    replacement_path = tmp_path / "replacement-post-append-ledger.jsonl"
    replacement_path.write_bytes(ledger_path.read_bytes())
    replacement_bytes = replacement_path.read_bytes()
    real_fsync = os.fsync
    substituted = False

    def substituting_fsync(fd: int) -> None:
        nonlocal substituted
        real_fsync(fd)
        if (
            not substituted
            and ledger_path.exists()
            and os.path.samestat(
                os.fstat(fd),
                os.stat(ledger_path, follow_symlinks=False),
            )
        ):
            substituted = True
            os.replace(replacement_path, ledger_path)

    monkeypatch.setattr(os, "fsync", substituting_fsync)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).safe_disable(
            RuntimeSafeDisableRequest(reason_ref="reason-ref:ledger-post-append-race"),
            idempotency_ref="idempotency-ref:ledger-post-append-race",
        )
    assert substituted is True
    assert ledger_path.read_bytes() == replacement_bytes
    assert not (tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).exists()


def test_runtime_store_ledger_append_rechecks_inode_after_directory_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RuntimeInvocationStore(tmp_path).create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:ledger-directory-fsync-race-setup",
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    replacement_path = tmp_path / "replacement-directory-fsync-ledger.jsonl"
    replacement_path.write_bytes(ledger_path.read_bytes())
    replacement_bytes = replacement_path.read_bytes()
    real_fsync = os.fsync
    substituted = False

    def substituting_directory_fsync(fd: int) -> None:
        nonlocal substituted
        real_fsync(fd)
        if not substituted and stat.S_ISDIR(os.fstat(fd).st_mode):
            substituted = True
            os.replace(replacement_path, ledger_path)

    monkeypatch.setattr(os, "fsync", substituting_directory_fsync)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_STORAGE_LEDGER_PATH_INVALID",
    ):
        RuntimeInvocationStore(tmp_path).safe_disable(
            RuntimeSafeDisableRequest(
                reason_ref="reason-ref:ledger-directory-fsync-race"
            ),
            idempotency_ref="idempotency-ref:ledger-directory-fsync-race",
        )
    assert substituted is True
    assert ledger_path.read_bytes() == replacement_bytes
    assert not (tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).exists()


def test_runtime_store_safe_disable_sidecar_atomic_failure_fails_closed_after_ledger_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-sidecar-first"),
        idempotency_ref="idempotency-ref:runtime-sidecar-first",
    )
    state_path = tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON
    before = state_path.read_bytes()

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise PermissionError

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_WRITE_FAILED",
    ):
        store.safe_disable(
            RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-sidecar-second"),
            idempotency_ref="idempotency-ref:runtime-sidecar-second",
        )

    assert state_path.read_bytes() == before
    assert not list(tmp_path.glob(".runtime_gateway_safe_disable_state.json.*.tmp"))
    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "reason-ref:runtime-sidecar-second" in persisted
    for _attempt in range(2):
        with pytest.raises(
            RuntimeInvocationStorageError,
            match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
        ):
            store.operator_safe_disable_state()
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_STATE_MISMATCH",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_state()


def test_runtime_store_partial_safe_disable_ledger_commit_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    for index in range(2):
        store.create_invocation(
            RuntimeInvocationRequest(
                requested_authority="local_model",
                requested_profile="sealed",
                input_ref=f"runtime-input-ref:partial-safe-disable-{index}",
                safe_summary="Record an isolated governed runtime request.",
            ),
            idempotency_ref=f"idempotency-ref:partial-safe-disable-{index}",
        )

    original_append = store._append
    safe_disable_appends = 0

    def fail_second_safe_disable_append(*args: object, **kwargs: object) -> None:
        nonlocal safe_disable_appends
        if args[0] == "safe_disable_recorded":
            safe_disable_appends += 1
            if safe_disable_appends == 2:
                raise RuntimeInvocationStorageError(
                    "INJECTED_SAFE_DISABLE_APPEND_FAILURE"
                )
        original_append(*args, **kwargs)

    monkeypatch.setattr(store, "_append", fail_second_safe_disable_append)
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="INJECTED_SAFE_DISABLE_APPEND_FAILURE",
    ):
        store.safe_disable(
            RuntimeSafeDisableRequest(
                reason_ref="reason-ref:runtime-partial-safe-disable"
            ),
            idempotency_ref="idempotency-ref:runtime-partial-safe-disable",
        )

    assert not (tmp_path / RUNTIME_GATEWAY_SAFE_DISABLE_STATE_JSON).exists()
    for _attempt in range(2):
        with pytest.raises(
            RuntimeInvocationStorageError,
            match="RUNTIME_SAFE_DISABLE_LEDGER_MISMATCH",
        ):
            store.operator_safe_disable_state()
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_SAFE_DISABLE_LEDGER_MISMATCH",
    ):
        RuntimeInvocationStore(tmp_path).operator_safe_disable_state()


def test_runtime_gateway_local_model_call_blocks_without_provider_execute_authority(
    tmp_path: Path,
) -> None:
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda request: FakeM164GatewayTransport(
                "UAA_LOCAL_RUNTIME_OK"
            )
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
        allow_bounded_preview=True,
        max_preview_chars=40,
    )

    result = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-success",
    )
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-success",
    )

    assert result.record.status == "execution_blocked"
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is False
    assert result.record.receipt.model_output_non_authoritative is True
    assert result.response_preview is None
    assert result.error_category == "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
    assert result.record.policy_decision.authority_decision_outcome == (
        "degrade_to_draft"
    )
    assert result.record.policy_decision.authority_domain == "provider_model_calls"
    assert result.record.policy_decision.authority_capability == "execute"
    assert (
        result.record.policy_decision.authority_required_mode
        == "full_machine_access_session"
    )
    assert result.record.policy_decision.authority_lease_ref is None
    assert replay.replayed is True

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert REDACTED_TEST_PROMPT not in persisted
    assert "UAA_LOCAL_RUNTIME_OK" not in persisted
    assert "raw_prompt" not in persisted
    assert "provider_payload" not in persisted


def test_runtime_local_model_separates_raw_envelope_and_content_byte_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ultimate_ai_agent.core.local_model_management.gateway as local_model_gateway
    import ultimate_ai_agent.core.runtime_gateway.local_model as runtime_local_model

    content = "R" * 1_500
    body = json.dumps(
        local_model_gateway._openai_chat_response(
            "uaa-local-runtime",
            content,
            1,
        )
    ).encode("utf-8")
    assert len(body) > 1_024

    class MemoryResponse:
        def __init__(self) -> None:
            self.read_limit: int | None = None

        def __enter__(self) -> "MemoryResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            self.read_limit = limit
            return body[:limit]

    response = MemoryResponse()

    class MemoryOpener:
        def open(self, *_args: object, **_kwargs: object) -> MemoryResponse:
            return response

    monkeypatch.setattr(
        local_model_gateway.request,
        "build_opener",
        lambda *_args: MemoryOpener(),
    )
    attempt = runtime_local_model.LocalModelRuntimeAdapter().invoke(
        RuntimeLocalModelCallRequest(
            base_url="http://127.0.0.1:8080",
            model_ref="uaa-local-runtime",
            messages=[
                RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)
            ],
            safe_summary="Run a bounded local model response envelope regression.",
            allow_bounded_preview=True,
            max_preview_chars=16,
            max_response_bytes=1_024,
        )
    )

    assert response.read_limit == local_model_gateway.M164_MAX_RESPONSE_BYTES + 1
    assert attempt.error_category is None
    assert attempt.response_received is True
    assert attempt.response_truncated is True
    assert attempt.response_byte_count == 1_024
    assert attempt.response_preview == content[:16]


def test_runtime_gateway_local_model_call_requires_full_machine_provider_lease(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("UAA_LOCAL_RUNTIME_OK")

    gateway = RuntimeGateway(
        store=_runtime_store_with_provider_model_execute(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
        allow_bounded_preview=True,
        max_preview_chars=40,
    )

    result = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-authority-success",
    )

    assert calls == 1
    assert result.record.status == "receipt_recorded"
    assert result.error_category is None
    assert result.record.policy_decision.allowed_to_execute is True
    assert result.record.policy_decision.authority_decision_outcome == "allow"
    assert (
        result.record.policy_decision.authority_lease_ref
        == "authority-lease-ref:test-provider-model-execute"
    )
    assert result.record.policy_decision.authority_domain == "provider_model_calls"
    assert result.record.policy_decision.authority_capability == "execute"
    assert (
        result.record.policy_decision.authority_required_mode
        == "full_machine_access_session"
    )
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is True
    assert result.record.receipt.model_output_non_authoritative is True
    assert result.response_preview == "UAA_LOCAL_RUNTIME_OK"
    attempt_markers = [
        entry.record.receipt
        for entry in gateway.store.list_entries()
        if entry.record.receipt is not None
        and entry.record.receipt.model_receipt_metadata is not None
        and entry.record.receipt.model_receipt_metadata.attempt_outcome_unknown
    ]
    assert len(attempt_markers) == 1
    assert attempt_markers[0].receipt_ref != result.record.receipt.receipt_ref
    assert attempt_markers[0].artifact_refs[0].artifact_kind == (
        "local_model_runtime_attempt_marker"
    )

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert REDACTED_TEST_PROMPT not in persisted
    assert "UAA_LOCAL_RUNTIME_OK" not in persisted
    assert "provider_payload" not in persisted


def test_runtime_gateway_blocked_receipt_stays_non_executable_after_authority_grant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("MUST_NOT_RUN_ON_BLOCKED_REPLAY")

    store = RuntimeInvocationStore(tmp_path, active_authority_leases=[])
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Keep a previously blocked model call non-executable.",
    )
    idempotency_ref = "idempotency-ref:blocked-receipt-later-authority"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    monkeypatch.setattr(
        store,
        "current_authority_leases",
        lambda: [provider_model_execute_authority_lease()],
    )
    replay = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 0
    assert first.record.receipt is not None
    assert first.record.receipt.model_call_performed is False
    assert replay.replayed is True
    assert replay.record.status == "execution_blocked"
    assert replay.record.policy_decision.allowed_to_execute is False
    assert replay.record.policy_decision.adapter_execution_enabled is False
    assert replay.record.policy_decision.model_call_enabled is False
    assert replay.record.receipt == first.record.receipt


def test_runtime_gateway_local_model_replay_after_safe_disable_re_evaluates_policy(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_REPLAY_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
        allow_bounded_preview=True,
        max_preview_chars=40,
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replay-policy",
    )
    store.safe_disable(
        RuntimeSafeDisableRequest(
            reason_ref="reason-ref:runtime-local-model-replay-safe-disable"
        ),
        idempotency_ref="idempotency-ref:runtime-local-model-replay-safe-disable",
    )
    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_CHANGED_DURING_REVALIDATION",
    ):
        store.record_replay_posture(
            first.record.invocation_ref,
            first.record.policy_decision.model_copy(
                update={
                    "invocation_status": RuntimeInvocationStatus.receipt_recorded,
                }
            ),
            RuntimeInvocationStatus.receipt_recorded,
            local_model_gateway_validated=True,
            gateway_error_category=None,
            gateway_error_recheck=lambda: None,
            expected_receipt=first.record.receipt,
            idempotency_ref="idempotency-ref:stale-replay-posture",
            payload_fingerprint_ref="runtime-operation-fingerprint-ref:stale-posture",
        )
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replay-policy",
    )

    assert calls == 1
    assert first.record.receipt is not None
    assert first.record.status == "receipt_recorded"
    assert first.record.receipt.model_call_performed is True
    assert replay.replayed is True
    assert replay.record.status == "safe_disabled"
    assert replay.error_category is None
    assert replay.record.receipt is not None
    assert replay.record.receipt.execution_performed is True
    assert replay.record.receipt.model_call_performed is True
    assert replay.record.receipt.safe_disable.active is True
    assert replay.request_byte_count == first.request_byte_count
    assert replay.response_byte_count == first.response_byte_count
    assert (
        replay.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-local-model-replay-safe-disable"
    )
    persisted_record = store.get_invocation(replay.record.invocation_ref)
    assert persisted_record.receipt is not None
    assert persisted_record.receipt.model_call_performed is True


def test_runtime_gateway_local_model_replay_after_authority_revocation_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_AUTHORITY_REPLAY_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
        allow_bounded_preview=True,
        max_preview_chars=40,
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-revoked-replay",
    )
    monkeypatch.setattr(store, "current_authority_leases", lambda: [])
    first_replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-revoked-replay",
    )
    second_replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-revoked-replay",
    )

    assert calls == 1
    assert first.record.status == "receipt_recorded"
    assert first.record.receipt is not None
    assert first.record.receipt.model_call_performed is True
    for replay in (first_replay, second_replay):
        assert replay.replayed is True
        assert replay.error_category == "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
        assert replay.record.status == "execution_blocked"
        assert replay.record.policy_decision.allowed_to_execute is False
        assert (
            replay.record.policy_decision.authority_decision_outcome
            == "degrade_to_draft"
        )
        assert replay.record.receipt is not None
        assert replay.record.receipt.execution_performed is True
        assert replay.record.receipt.model_call_performed is True
        assert replay.request_byte_count == first.request_byte_count
        assert replay.response_byte_count == first.response_byte_count

    persisted_record = store.get_invocation(first.record.invocation_ref)
    assert persisted_record.status == "execution_blocked"
    assert persisted_record.policy_decision.allowed_to_execute is False
    assert persisted_record.receipt is not None
    assert persisted_record.receipt.execution_performed is True
    assert persisted_record.receipt.model_call_performed is True

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert REDACTED_TEST_PROMPT not in persisted
    assert "LOCAL_MODEL_AUTHORITY_REPLAY_OK" not in persisted


def test_runtime_gateway_local_model_replay_returns_revalidated_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda request: FakeM164GatewayTransport(
                "LOCAL_MODEL_REVALIDATED_AUTHORITY_OK"
            )
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )
    replacement = provider_model_execute_authority_lease().model_copy(
        update={"lease_ref": "authority-lease-ref:test-provider-model-replacement"}
    )
    monkeypatch.setattr(
        store,
        "current_authority_leases",
        lambda: [replacement],
    )

    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )

    assert first.record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-execute"
    )
    assert replay.replayed is True
    assert replay.error_category is None
    assert replay.record.policy_decision.allowed_to_execute is True
    assert replay.record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-replacement"
    )
    assert replay.record.receipt is not None
    assert replay.record.receipt.model_call_performed is True
    persisted_record = store.get_invocation(first.record.invocation_ref)
    assert persisted_record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-replacement"
    )
    assert persisted_record.receipt is not None
    assert persisted_record.receipt.model_call_performed is True

    original = provider_model_execute_authority_lease()
    monkeypatch.setattr(store, "current_authority_leases", lambda: [original])
    restored = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )
    monkeypatch.setattr(store, "current_authority_leases", lambda: [replacement])
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    before_replacement_again = ledger_path.read_bytes()
    replacement_again = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )
    before_revalidated_replay = ledger_path.read_bytes()
    revalidated_again = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )

    assert restored.record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-execute"
    )
    assert replacement_again.record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-replacement"
    )
    assert revalidated_again.record.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-replacement"
    )
    assert revalidated_again.record.receipt == replacement_again.record.receipt
    assert (
        revalidated_again.record.replay_count
        == replacement_again.record.replay_count + 1
    )
    assert before_revalidated_replay != before_replacement_again
    assert ledger_path.read_bytes() == before_revalidated_replay
    assert store.get_invocation(first.record.invocation_ref) == revalidated_again.record
    before_stable_replay = ledger_path.read_bytes()
    stable_replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replacement-authority",
    )
    assert stable_replay.record.updated_at == revalidated_again.record.updated_at
    assert (
        stable_replay.record.policy_decision == revalidated_again.record.policy_decision
    )
    assert stable_replay.record.receipt == revalidated_again.record.receipt
    assert stable_replay.record.replay_count == revalidated_again.record.replay_count
    assert ledger_path.read_bytes() == before_stable_replay


@pytest.mark.parametrize("posture_change", ["lease_revoked", "kill_switch"])
def test_runtime_gateway_local_model_replay_rejects_posture_change_in_store_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture_change: str,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_AUTHORITY_RACE_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-authority-race"
    first = gateway.invoke_local_model(
        request,
        idempotency_ref=idempotency_ref,
    )
    if posture_change == "lease_revoked":
        replacement = provider_model_execute_authority_lease().model_copy(
            update={
                "lease_ref": "authority-lease-ref:test-provider-model-race",
            }
        )
        authority_snapshots = iter(([replacement], []))
        monkeypatch.setattr(
            store,
            "current_authority_leases",
            lambda: next(authority_snapshots),
        )
    else:
        kill_switch_snapshots = iter((False, True))
        monkeypatch.setattr(
            store,
            "authority_lease_kill_switch_engaged",
            lambda: next(kill_switch_snapshots),
        )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    before_replay = ledger_path.read_bytes()

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_AUTHORITY_CHANGED_DURING_REVALIDATION",
    ):
        gateway.invoke_local_model(
            request,
            idempotency_ref=idempotency_ref,
        )

    assert calls == 1
    assert ledger_path.read_bytes() == before_replay
    persisted = RuntimeInvocationStore(tmp_path).get_invocation(
        first.record.invocation_ref
    )
    assert persisted.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-execute"
    )
    assert persisted.receipt == first.record.receipt


def test_runtime_gateway_local_model_replay_rejects_gateway_change_in_store_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_GATEWAY_RACE_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-gateway-race"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    gateway_snapshots = iter((True, True, False))
    monkeypatch.setattr(
        gateway,
        "_runtime_local_model_enabled",
        lambda: next(gateway_snapshots),
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    before_replay = ledger_path.read_bytes()

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_GATEWAY_CHANGED_DURING_REVALIDATION",
    ):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    assert ledger_path.read_bytes() == before_replay
    persisted = RuntimeInvocationStore(tmp_path).get_invocation(
        first.record.invocation_ref
    )
    assert persisted.policy_decision == first.record.policy_decision
    assert persisted.receipt == first.record.receipt


def test_runtime_gateway_local_model_replay_binds_exact_gateway_error_category(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_GATEWAY_CAUSE_RACE_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-gateway-cause-race"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    runtime_snapshots = iter((False, False, True))
    endpoint_snapshots = iter(
        (None, None, "RUNTIME_LOCAL_MODEL_ENDPOINT_NOT_CONFIGURED")
    )
    monkeypatch.setattr(
        gateway,
        "_runtime_local_model_enabled",
        lambda: next(runtime_snapshots),
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.core.runtime_gateway.local_model._validate_loopback_endpoint",
        lambda _request: next(endpoint_snapshots),
    )
    ledger_path = tmp_path / "runtime_gateway_invocations.jsonl"
    before_replay = ledger_path.read_bytes()

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_GATEWAY_CHANGED_DURING_REVALIDATION",
    ):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    assert ledger_path.read_bytes() == before_replay
    persisted = RuntimeInvocationStore(tmp_path).get_invocation(
        first.record.invocation_ref
    )
    assert persisted.policy_decision == first.record.policy_decision
    assert persisted.receipt == first.record.receipt


def test_runtime_gateway_local_model_replay_binds_exact_receipt_inside_store_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_RECEIPT_RACE_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Bind replay to the exact durable receipt.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-receipt-race"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    original_record_replay_posture = store.record_replay_posture
    changed = False

    def racing_record_replay_posture(*args: object, **kwargs: object) -> object:
        nonlocal changed
        if not changed:
            changed = True
            current = store.get_invocation(first.record.invocation_ref)
            assert current.receipt is not None
            replacement = current.receipt.model_copy(
                update={"created_at": current.receipt.created_at + timedelta(seconds=1)}
            )
            store.record_receipt(
                current.invocation_ref,
                replacement,
                idempotency_ref="idempotency-ref:runtime-local-model-receipt-race-write",
                payload_fingerprint_ref=(
                    "runtime-operation-fingerprint-ref:receipt-race-write"
                ),
            )
        return original_record_replay_posture(*args, **kwargs)

    monkeypatch.setattr(
        store,
        "record_replay_posture",
        racing_record_replay_posture,
    )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_RECEIPT_CHANGED_DURING_REVALIDATION",
    ):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    assert changed is True


def test_runtime_gateway_local_model_replay_key_binds_exact_durable_receipt(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("LOCAL_MODEL_RECEIPT_KEY_OK")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Bind replay idempotency to the exact durable receipt.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-receipt-key"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    replay = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    assert replay.record.receipt == first.record.receipt
    assert first.record.receipt is not None

    replacement = first.record.receipt.model_copy(
        update={"created_at": first.record.receipt.created_at + timedelta(seconds=1)}
    )
    store.record_receipt(
        first.record.invocation_ref,
        replacement,
        idempotency_ref="idempotency-ref:runtime-local-model-receipt-key-write",
        payload_fingerprint_ref=("runtime-operation-fingerprint-ref:receipt-key-write"),
    )
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH",
    ):
        gateway.invoke_local_model(
            request,
            idempotency_ref=idempotency_ref,
        )

    assert calls == 1


def test_runtime_gateway_blocked_replay_revalidates_before_equal_posture_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("MUST_NOT_RUN")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=False,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Keep disabled local model runtime blocked.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-blocked-race"
    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    original_record_replay_posture = store.record_replay_posture
    safe_disabled = False

    def racing_record_replay_posture(*args: object, **kwargs: object) -> object:
        nonlocal safe_disabled
        if not safe_disabled:
            safe_disabled = True
            store.safe_disable(
                RuntimeSafeDisableRequest(reason_ref="reason-ref:blocked-replay-race"),
                idempotency_ref="idempotency-ref:blocked-replay-race",
            )
        return original_record_replay_posture(*args, **kwargs)

    monkeypatch.setattr(
        store,
        "record_replay_posture",
        racing_record_replay_posture,
    )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_REPLAY_POSTURE_CHANGED_DURING_REVALIDATION",
    ):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 0
    assert first.record.receipt is not None
    assert safe_disabled is True


def test_runtime_gateway_local_model_replay_uses_original_posture_fingerprint(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SHOULD_NOT_RUN_ON_BLOCKED_REPLAY")

    gateway = RuntimeGateway(
        store=_runtime_store_with_provider_model_execute(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=False,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-posture-fingerprint",
    )
    gateway._local_model_runtime_enabled = True
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-posture-fingerprint",
    )

    assert calls == 0
    assert first.error_category == "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
    assert replay.replayed is True
    assert replay.error_category == "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
    assert replay.record.status == "execution_blocked"
    assert replay.record.receipt is not None
    assert replay.record.receipt.model_call_performed is False


def test_runtime_gateway_local_model_call_is_disabled_by_default(
    tmp_path: Path,
) -> None:
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda request: FakeM164GatewayTransport("SHOULD_NOT_RUN")
        ),
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )

    result = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-disabled",
    )

    assert result.record.status == "execution_blocked"
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is False
    assert result.error_category == "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
    assert result.local_model_runtime_enabled is False

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert REDACTED_TEST_PROMPT not in persisted
    assert "SHOULD_NOT_RUN" not in persisted


def test_runtime_gateway_blocks_non_loopback_model_url_without_persisting_url(
    tmp_path: Path,
) -> None:
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://example.com:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Attempt local model runtime with endpoint validation.",
    )

    result = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-remote-denied",
    )

    assert result.error_category == "M164_LOOPBACK_ONLY_REQUIRED"
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is False
    assert result.record.receipt.execution_performed is False

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "example.com" not in persisted
    assert REDACTED_TEST_PROMPT not in persisted


@pytest.mark.parametrize(
    ("base_url", "error_category"),
    [
        ("http://user:pass@127.0.0.1:8080", "M164_BASE_URL_SCOPE_DENIED"),
        ("http://127.0.0.1:8080/prefix", "M164_BASE_URL_SCOPE_DENIED"),
        ("http://127.0.0.1:8081", "RUNTIME_LOCAL_MODEL_ENDPOINT_NOT_CONFIGURED"),
    ],
)
def test_runtime_gateway_blocks_unconfigured_or_scoped_model_urls_without_transport(
    tmp_path: Path,
    base_url: str,
    error_category: str,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SHOULD_NOT_RUN")

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url=base_url,
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Attempt local model runtime with endpoint validation.",
    )

    result = gateway.invoke_local_model(
        request,
        idempotency_ref=f"idempotency-ref:runtime-local-model-url-{error_category.lower()}",
    )

    assert calls == 0
    assert result.error_category == error_category
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is False
    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "SHOULD_NOT_RUN" not in persisted
    assert "user:pass" not in persisted
    assert "/prefix" not in persisted


def test_runtime_gateway_allowlisted_command_records_redacted_receipt(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=7,
            output_bytes=b"unsafe /Users/example/path\napi_key=secret\n",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )

    result = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-success",
    )
    replay = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-success",
    )

    assert result.record.status == "receipt_recorded"
    assert result.record.policy_decision.command_execution_enabled is True
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert result.record.receipt.command_receipt_metadata is not None
    assert (
        result.record.receipt.command_receipt_metadata.command_output_persisted is False
    )
    assert result.output_summary is not None
    assert "2 bounded lines" in result.output_summary
    assert replay.replayed is True
    assert len(calls) == 1
    git_argv = calls[0]["argv"]
    assert isinstance(git_argv, tuple)
    assert Path(git_argv[0]).is_absolute()
    assert Path(git_argv[0]).name == "git"
    assert git_argv[1:] == (
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
    assert calls[0]["cwd"] == ROOT
    assert calls[0]["env"] == {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "/Users/example/path" not in persisted
    assert "api_key=secret" not in persisted
    assert "git status --short" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_governed_command_runtime_rejects_unapproved_workspace_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match="RUNTIME_COMMAND_WORKSPACE_ROOT_NOT_ALLOWLISTED"
    ):
        GovernedCommandRuntimeAdapter(workspace_root=tmp_path)


def test_runtime_launcher_command_run_cli_records_receipts_and_mission_scope(
    tmp_path: Path,
) -> None:
    mission_ref = "mission-ref:test-runtime-cli-command"
    env = os.environ.copy()
    env["UAA_AUTHORITY_STATE_DIR"] = str(tmp_path / "authority")
    runtime_state_dir = tmp_path / "runtime"

    issue = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "select-authority-mode",
            "--mode",
            "approved_safe_local_work_session",
            "--scope",
            "mission",
            "--mission-ref",
            mission_ref,
            "--domain",
            "workspace:read,execute",
            "--reason-ref",
            "reason-ref:runtime-cli-command-mission",
            "--idempotency-ref",
            "idempotency-ref:runtime-cli-command-mission",
            "--summary",
            "Authorize mission-bound runtime command inspection.",
            "--approve",
            "--approved-by-actor-ref",
            "operator-ref:test-runtime-authority",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    issue_body = json.loads(issue.stdout)
    assert issue_body["receipt"]["status"] == "issued"
    assert issue_body["lease"]["scope"] == "mission"
    assert issue_body["lease"]["mission_ref"] == mission_ref

    matching = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "--state-dir",
            str(runtime_state_dir),
            "command",
            "run",
            "git_status",
            "--mission-ref",
            mission_ref,
            "--idempotency-ref",
            "idempotency-ref:runtime-cli-command-matching",
            "--summary",
            "Inspect repo status under the matching mission lease.",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    matching_body = json.loads(matching.stdout)
    assert matching_body["success"] is True
    assert matching_body["execution_performed"] is True
    assert matching_body["command_execution_performed"] is True
    assert matching_body["mission_ref"] == mission_ref
    assert matching_body["record"]["request"]["mission_ref"] == mission_ref
    assert (
        matching_body["record"]["policy_decision"]["authority_decision_outcome"]
        == "allow"
    )
    assert str(tmp_path) not in matching.stdout
    assert "stdout" not in matching.stdout
    assert "stderr" not in matching.stdout

    missing = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "--state-dir",
            str(runtime_state_dir),
            "command",
            "run",
            "git_status",
            "--idempotency-ref",
            "idempotency-ref:runtime-cli-command-missing-mission",
            "--summary",
            "Inspect repo status without the active mission ref.",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert missing.returncode == 1
    missing_body = json.loads(missing.stdout)
    assert missing_body["success"] is False
    assert missing_body["execution_performed"] is False
    assert missing_body["command_execution_performed"] is False
    missing_policy = missing_body["record"]["policy_decision"]
    assert missing_policy["authority_decision_outcome"] == "degrade_to_draft"
    assert (
        "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION"
        in (missing_policy["reason_codes"])
    )
    assert str(tmp_path) not in missing.stdout
    assert "stdout" not in missing.stdout
    assert "stderr" not in missing.stdout


def test_runtime_gateway_command_replay_after_safe_disable_keeps_idempotency_shape(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )
    first = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-safe-disable-replay",
    )
    store.safe_disable(
        RuntimeSafeDisableRequest(
            reason_ref="reason-ref:runtime-command-replay-disable"
        ),
        idempotency_ref="idempotency-ref:runtime-command-replay-disable",
    )
    replay = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-safe-disable-replay",
    )

    assert first.record.receipt is not None
    assert len(calls) == 1
    assert replay.replayed is True
    assert replay.record.status == "safe_disabled"
    assert replay.record.policy_decision.allowed_to_execute is False
    assert replay.record.policy_decision.adapter_execution_enabled is False
    assert replay.record.policy_decision.command_execution_enabled is False
    assert replay.command_execution_enabled is False
    assert replay.record.receipt is not None
    assert replay.record.receipt.safe_disable.active is True
    assert (
        replay.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-command-replay-disable"
    )


def test_runtime_gateway_command_disabled_intent_records_blocked_receipt(
    tmp_path: Path,
) -> None:
    gateway = RuntimeGateway(store=RuntimeInvocationStore(tmp_path))
    request = RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        target_refs=["test-ref:focused-runtime"],
        approval_ref="approval-ref:identifier-only",
        safe_summary="Attempt focused pytest command with approval identifier only.",
    )

    result = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-approval-required",
    )

    assert result.record.status == "execution_blocked"
    assert result.command_execution_enabled is False
    assert result.error_category == "RUNTIME_COMMAND_APPROVAL_BRIDGE_REQUIRED"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.record.receipt.command_receipt_metadata is not None
    assert (
        result.record.receipt.command_receipt_metadata.command_execution_attempted
        is False
    )
    read_model = build_runtime_action_inbox_bridge_read_model([result.record])
    assert read_model["control_center_exact_runtime_mutations_enabled"] is True
    assert read_model["local_model_call_control_enabled"] is True
    assert read_model["command_request_control_enabled"] is True
    assert read_model["approval_decision_control_enabled"] is True
    assert read_model["exact_envelope_execution_control_enabled"] is True
    assert read_model["safe_disable_control_enabled"] is True
    assert read_model["control_center_mints_authority"] is False
    assert read_model["action_execution_enabled"] is False
    event_kinds = {event["event_kind"] for event in read_model["evidence_timeline"]}
    assert "receipt_recorded" in event_kinds
    assert "execution_started" not in event_kinds
    assert "execution_completed" not in event_kinds
    assert "execution_failed" not in event_kinds
    assert "execution_timed_out" not in event_kinds


def _approved_runtime_command_request(
    intent: str = "focused_pytest",
    mission_ref: str | None = None,
) -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent=intent,
        requested_profile="operator-approved",
        mission_ref=mission_ref,
        target_refs=[f"test-ref:governed-runtime-{intent.replace('_', '-')}"],
        approval_ref=None,
        safe_summary="Run one exact approved governed runtime command lane.",
    )


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (
        f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"
    )


def _runtime_action_inbox_refs(
    record,
    *,
    decision: str = "approve",
    command_intent: str = "focused_pytest",
) -> dict[str, str]:
    exact_scope_ref = _test_hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
            "requested_authority": record.request.requested_authority,
        },
    )
    approval_ref = _test_hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": record.invocation_ref,
            "requested_authority": record.request.requested_authority,
            "requested_profile": record.request.requested_profile,
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": command_intent,
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
    )
    action_envelope_ref = _test_hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return {
        "approval_ref": approval_ref,
        "action_envelope_ref": action_envelope_ref,
        "exact_scope_ref": exact_scope_ref,
    }


def _runtime_execute_request(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    envelope = record.action_inbox_envelope
    return RuntimeExecuteRequest(
        approval_ref=envelope.approval_ref,
        action_envelope_ref=envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
    )


def _command_request_for_approved_record(
    command_request: RuntimeCommandExecutionRequest,
    record,
) -> RuntimeCommandExecutionRequest:
    assert record.action_inbox_envelope is not None
    return command_request.model_copy(
        update={"approval_ref": record.action_inbox_envelope.approval_ref}
    )


def _bind_runtime_action_inbox_approval(
    store: RuntimeInvocationStore,
    *,
    command_request: RuntimeCommandExecutionRequest | None = None,
    expected_payload_fingerprint_ref: str | None = None,
    expected_policy_decision_ref: str | None = None,
    decision: str = "approve",
    expires_delta: timedelta = timedelta(minutes=30),
):
    command_request = command_request or _approved_runtime_command_request()
    command_intent = str(
        getattr(command_request.intent, "value", command_request.intent)
    )
    created = store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-action-inbox-create",
    )
    refs = _runtime_action_inbox_refs(
        created.record,
        decision=decision,
        command_intent=command_intent,
    )
    return store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision=decision,
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=(
                expected_payload_fingerprint_ref
                or created.record.payload_fingerprint_ref
            ),
            expected_policy_decision_ref=(
                expected_policy_decision_ref
                or created.record.policy_decision.policy_decision_ref
            ),
            adapter_id="governed-command-runtime-adapter",
            command_intent=command_intent,
            risk_class="medium",
            expires_at=utc_now() + expires_delta,
            safe_summary="Action Inbox approved one exact governed runtime command lane.",
        ),
        idempotency_ref=f"idempotency-ref:runtime-action-inbox-{decision}",
    )


def test_runtime_gateway_action_inbox_approval_executes_exact_command_once(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from scripts.dev import uaa_launcher, uaa_runtime

    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=3,
            output_bytes=b"safe pytest output",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    assert approved.action_inbox_envelope is not None
    approved_read_model = build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    assert (
        approved.action_inbox_envelope.approval_ref
        in (approved_read_model["pending_runtime_approval_refs"])
    )
    assert (
        approved.action_inbox_envelope.action_envelope_ref
        not in (approved_read_model["pending_runtime_approval_refs"])
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    execute_command_request = _command_request_for_approved_record(
        command_request,
        approved,
    )
    execute_request = _runtime_execute_request(approved)

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        execute_command_request,
        execute_request,
        idempotency_ref="idempotency-ref:runtime-action-inbox-execute",
    )
    replay = gateway.execute_approved_command(
        approved.invocation_ref,
        execute_command_request,
        execute_request,
        idempotency_ref="idempotency-ref:runtime-action-inbox-execute",
    )

    assert approved.status == "approved_pending_execution"
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.approval_validated is True
    assert approved.action_inbox_envelope.authority_scope_allowed is True
    assert approved.action_inbox_envelope.authority_decision_outcome == "allow"
    assert approved.action_inbox_envelope.authority_lease_ref
    assert approved.policy_decision.command_execution_enabled is True
    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert result.record.action_inbox_envelope is not None
    assert result.record.action_inbox_envelope.receipt_refs == [
        result.record.receipt.receipt_ref
    ]
    assert replay.replayed is True
    assert len(calls) == 1
    pytest_argv = calls[0]["argv"]
    assert isinstance(pytest_argv, tuple)
    assert pytest_argv == (
        str(ROOT / ".venv/bin/python"),
        "-m",
        "pytest",
        "tests/test_governed_runtime_contracts.py",
        "-q",
    )
    assert calls[0]["cwd"] == ROOT
    read_model = build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    assert read_model["item_count"] == 1
    assert read_model["receipt_refs"] == [result.record.receipt.receipt_ref]
    assert result.record.receipt.evidence_refs[0] in read_model["evidence_refs"]
    assert read_model["items"][0]["action_envelope_ref"] == (
        approved.action_inbox_envelope.action_envelope_ref
    )
    assert read_model["items"][0]["authority_scope_allowed"] is True
    assert read_model["items"][0]["authority_decision_outcome"] == "allow"
    assert read_model["items"][0]["authority_lease_ref"]

    cli = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "--state-dir",
            str(tmp_path),
            "inspect-action-inbox-bridge",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.record.receipt.receipt_ref in cli.stdout
    assert "safe pytest output" not in cli.stdout
    assert str(tmp_path) not in cli.stdout

    for command, expected_strings in [
        (
            ["status"],
            ["Governed runtime status", "utility_command_receipt_recorded"],
        ),
        (
            ["capabilities"],
            ["Governed runtime capabilities", "authority-ref:runtime-allowlisted"],
        ),
        (
            ["invocations", "list"],
            ["Governed runtime invocations", result.record.invocation_ref],
        ),
        (
            ["invocations", "show", result.record.invocation_ref],
            [
                "Governed runtime invocation",
                result.record.policy_decision.policy_decision_ref,
            ],
        ),
        (
            ["receipts", "show", result.record.receipt.receipt_ref],
            ["Governed runtime receipt", "Output summary: Command output redacted"],
        ),
    ]:
        assert uaa_runtime.main(["--state-dir", str(tmp_path), *command]) == 0
        cli_output = capsys.readouterr().out
        for expected in expected_strings:
            assert expected in cli_output
        assert "safe pytest output" not in cli_output
        assert str(tmp_path) not in cli_output

    assert (
        uaa_launcher.main(
            [
                "runtime",
                "--state-dir",
                str(tmp_path),
                "status",
            ]
        )
        == 0
    )
    launcher_output = capsys.readouterr().out
    assert "Governed runtime status" in launcher_output
    assert "utility_command_receipt_recorded" in launcher_output
    assert "safe pytest output" not in launcher_output
    assert str(tmp_path) not in launcher_output

    event_kinds = {event["event_kind"] for event in read_model["evidence_timeline"]}
    stable_event_refs = {
        event["event_kind"]: event["event_ref"]
        for event in read_model["evidence_timeline"]
    }
    assert {
        "invocation_requested",
        "policy_decision",
        "approval_requested",
        "approval_accepted",
        "execution_started",
        "execution_completed",
        "receipt_recorded",
    }.issubset(event_kinds)

    assert (
        uaa_runtime.main(
            [
                "--state-dir",
                str(tmp_path),
                "safe-disable",
                "--idempotency-ref",
                "idempotency-ref:runtime-cli-safe-disable-test",
            ]
        )
        == 0
    )
    safe_disable_output = capsys.readouterr().out
    assert "Governed runtime safe-disable" in safe_disable_output
    assert "Safe-disable ref:" in safe_disable_output
    assert "safe pytest output" not in safe_disable_output
    assert str(tmp_path) not in safe_disable_output
    disabled_read_model = build_runtime_action_inbox_bridge_read_model(
        RuntimeInvocationStore(tmp_path).list_invocations(),
        entries=RuntimeInvocationStore(tmp_path).list_entries(),
    )
    disabled_event_kinds = {
        event["event_kind"] for event in disabled_read_model["evidence_timeline"]
    }
    assert "safe_disable_invoked" in disabled_event_kinds
    disabled_event_refs = {
        event["event_kind"]: event["event_ref"]
        for event in disabled_read_model["evidence_timeline"]
    }
    assert (
        disabled_event_refs["invocation_requested"]
        == stable_event_refs["invocation_requested"]
    )
    assert (
        disabled_event_refs["approval_accepted"]
        == stable_event_refs["approval_accepted"]
    )

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "safe pytest output" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_runtime_gateway_action_inbox_approval_uses_current_authority_lease(
    tmp_path: Path,
) -> None:
    command_request = _approved_runtime_command_request()
    proposal_store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[],
    )
    created = proposal_store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-action-inbox-create-before-lease",
    )
    assert created.record.policy_decision.authority_decision_outcome == (
        "degrade_to_draft"
    )
    assert created.record.policy_decision.allowed_to_execute is False

    approval_store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    command_intent = str(
        getattr(command_request.intent, "value", command_request.intent)
    )
    refs = _runtime_action_inbox_refs(
        created.record,
        command_intent=command_intent,
    )

    approved = approval_store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision="approve",
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=(
                created.record.policy_decision.policy_decision_ref
            ),
            adapter_id="governed-command-runtime-adapter",
            command_intent=command_intent,
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary=(
                "Action Inbox approved one exact governed runtime command lane."
            ),
        ),
        idempotency_ref="idempotency-ref:runtime-action-inbox-approve-after-lease",
    )

    assert approved.status == "approved_pending_execution"
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.approval_validated is True
    assert approved.action_inbox_envelope.authority_scope_allowed is True
    assert approved.action_inbox_envelope.authority_decision_outcome == "allow"
    assert approved.action_inbox_envelope.authority_lease_ref == (
        "authority-lease-ref:test-workspace-execute"
    )
    assert approved.policy_decision.allowed_to_execute is True
    assert approved.policy_decision.authority_decision_outcome == "allow"
    assert approved.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-workspace-execute"
    )


def test_runtime_gateway_action_inbox_execute_requires_workspace_execute_lease(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=3,
            output_bytes=b"should not execute",
        )

    store = RuntimeInvocationStore(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-no-lease-execute",
    )

    assert calls == []
    assert approved.status == "execution_blocked"
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.approval_validated is True
    assert approved.action_inbox_envelope.authority_scope_allowed is False
    assert approved.action_inbox_envelope.authority_decision_outcome == (
        "degrade_to_draft"
    )
    assert "blocked-state:runtime-authority-lease-required" in (
        approved.action_inbox_envelope.blocked_reason_refs
    )
    assert approved.policy_decision.allowed_to_execute is False
    assert approved.policy_decision.authority_decision_outcome == "degrade_to_draft"
    assert result.record.status == "execution_blocked"
    assert result.error_category == "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False


def test_runtime_gateway_action_inbox_execute_rechecks_active_authority_lease(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=5,
            output_bytes=b"should not execute after lease removal",
        )

    approval_store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        approval_store,
        command_request=command_request,
    )
    assert approved.policy_decision.allowed_to_execute is True
    assert approved.policy_decision.authority_decision_outcome == "allow"

    execution_store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[],
    )
    gateway = RuntimeGateway(
        store=execution_store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-execute-stale-lease",
    )

    assert calls == []
    assert result.record.status == "execution_blocked"
    assert result.error_category == "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.policy_decision.authority_decision_outcome == (
        "degrade_to_draft"
    )
    assert result.record.policy_decision.authority_lease_ref is None
    assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in (
        result.record.policy_decision.reason_codes
    )
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert any(
        entry.entry_kind == "authority_policy_refreshed_for_execution"
        for entry in execution_store.list_entries()
    )


def test_runtime_gateway_action_inbox_execute_allows_matching_mission_lease(
    tmp_path: Path,
) -> None:
    mission_ref = "mission-ref:test-runtime-workspace-maintenance"
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=4,
            output_bytes=b"raw mission output should be redacted",
        )

    store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[
            workspace_execute_mission_authority_lease(mission_ref),
        ],
    )
    command_request = _approved_runtime_command_request(mission_ref=mission_ref)
    invocation_request = runtime_command_invocation_request(command_request)
    assert invocation_request.mission_ref == mission_ref
    assert mission_ref in invocation_request.metadata_refs
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-mission-lease-execute",
    )

    assert approved.policy_decision.allowed_to_execute is True
    assert approved.policy_decision.authority_decision_outcome == "allow"
    assert approved.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-workspace-execute-mission"
    )
    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert len(calls) == 1


def test_runtime_gateway_action_inbox_execute_blocks_mission_lease_without_mission_ref(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=4,
            output_bytes=b"should not execute",
        )

    store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[
            workspace_execute_mission_authority_lease(
                "mission-ref:test-runtime-workspace-maintenance"
            ),
        ],
    )
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-mission-lease-missing-ref",
    )

    assert calls == []
    assert approved.status == "execution_blocked"
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.approval_validated is True
    assert approved.action_inbox_envelope.authority_scope_allowed is False
    assert "reason-ref:authority:mission-scope-mismatch" in (
        approved.action_inbox_envelope.authority_reason_refs
    )
    assert approved.policy_decision.allowed_to_execute is False
    assert approved.policy_decision.authority_decision_outcome == "degrade_to_draft"
    assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in (
        approved.policy_decision.reason_codes
    )
    assert result.record.status == "execution_blocked"
    assert result.error_category == "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False


def test_runtime_gateway_action_inbox_approval_executes_exact_repo_verifier_command(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=4,
            output_bytes=b"raw repo verifier output should be redacted",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request(intent="repo_verifier")
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-repo-verifier-execute",
    )

    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert result.record.receipt.command_receipt_metadata is not None
    assert result.record.receipt.command_receipt_metadata.intent == "repo_verifier"
    assert result.output_persisted is False
    assert len(calls) == 1
    argv = calls[0]["argv"]
    assert isinstance(argv, tuple)
    assert argv == (
        str(ROOT / ".venv/bin/python"),
        "scripts/verify_documentation_integrity.py",
    )

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "raw repo verifier output" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_runtime_gateway_action_inbox_approval_executes_exact_frontend_check_command(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"raw frontend check output should be redacted",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request(intent="frontend_check")
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-frontend-check-execute",
    )

    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert result.record.receipt.command_receipt_metadata is not None
    assert result.record.receipt.command_receipt_metadata.intent == "frontend_check"
    assert result.output_persisted is False
    assert len(calls) == 1
    argv = calls[0]["argv"]
    assert isinstance(argv, tuple)
    assert argv in {
        ("/usr/bin/make", "frontend-check"),
        ("/bin/make", "frontend-check"),
    }

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "raw frontend check output" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_runtime_gateway_action_inbox_approval_executes_exact_repo_doctor_command(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=2,
            output_bytes=b"raw doctor output should be redacted",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request(intent="repo_doctor")
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-repo-doctor-execute",
    )

    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is True
    assert result.record.receipt.command_receipt_metadata is not None
    assert result.record.receipt.command_receipt_metadata.intent == "repo_doctor"
    assert result.output_persisted is False
    assert len(calls) == 1
    argv = calls[0]["argv"]
    assert isinstance(argv, tuple)
    assert argv in {
        ("/usr/bin/make", "doctor"),
        ("/bin/make", "doctor"),
    }

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "raw doctor output" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_runtime_launcher_actions_approve_and_deny_by_safe_selector_ref(
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["UAA_AUTHORITY_STATE_DIR"] = str(tmp_path / "authority")
    issue_workspace_execute_authority_lease(Path(env["UAA_AUTHORITY_STATE_DIR"]))
    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    created = store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-cli-selector-create",
    )
    refs = _runtime_action_inbox_refs(created.record)
    blocked = store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            approval_ref=refs["approval_ref"],
            decision="approve",
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Caller supplied approval refs remain identifiers.",
        ),
        idempotency_ref="idempotency-ref:runtime-cli-selector-blocked",
    )
    assert blocked.status == "execution_blocked"

    preflight = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_launcher.py"),
            "actions",
            "--state-dir",
            str(tmp_path),
            "approve",
            refs["approval_ref"],
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert preflight.returncode == 2
    assert "Governed runtime Action Inbox decision preflight" in preflight.stdout
    assert "Re-run with --confirm-exact-runtime-action" in preflight.stdout
    assert str(tmp_path) not in preflight.stdout
    preflight_record = RuntimeInvocationStore(tmp_path).get_invocation(
        created.record.invocation_ref
    )
    assert preflight_record.status == "execution_blocked"

    approved = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_launcher.py"),
            "actions",
            "--state-dir",
            str(tmp_path),
            "approve",
            refs["approval_ref"],
            "--confirm-exact-runtime-action",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "Governed runtime Action Inbox decision preflight" in approved.stdout
    assert "Governed runtime invocation" in approved.stdout
    assert str(tmp_path) not in approved.stdout
    reloaded = RuntimeInvocationStore(tmp_path).get_invocation(
        created.record.invocation_ref
    )
    assert reloaded.status == "approved_pending_execution"
    assert reloaded.action_inbox_envelope is not None
    assert reloaded.action_inbox_envelope.approval_validated is True
    assert "blocked-state:runtime-approval-ref-identifier-only" not in (
        reloaded.action_inbox_envelope.blocked_reason_refs
    )

    deny_store = RuntimeInvocationStore(tmp_path / "deny")
    deny_created = deny_store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-cli-deny-selector-create",
    )
    deny_refs = _runtime_action_inbox_refs(deny_created.record, decision="deny")
    deny_store.bind_approval(
        deny_created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            approval_ref=deny_refs["approval_ref"],
            decision="deny",
            action_envelope_ref=deny_refs["action_envelope_ref"],
            exact_scope_ref=deny_refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=deny_created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=deny_created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Caller supplied deny refs remain identifiers.",
        ),
        idempotency_ref="idempotency-ref:runtime-cli-deny-selector-envelope",
    )

    denied = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_launcher.py"),
            "actions",
            "--state-dir",
            str(tmp_path / "deny"),
            "deny",
            deny_refs["approval_ref"],
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert "Governed runtime invocation" in denied.stdout
    assert str(tmp_path / "deny") not in denied.stdout
    denied_record = RuntimeInvocationStore(tmp_path / "deny").get_invocation(
        deny_created.record.invocation_ref
    )
    assert denied_record.status == "approval_denied"
    assert denied_record.action_inbox_envelope is not None
    assert "blocked-state:runtime-approval-denied" in (
        denied_record.action_inbox_envelope.blocked_reason_refs
    )


def test_runtime_gateway_action_inbox_denied_expired_or_changed_scope_blocks(
    tmp_path: Path,
) -> None:
    denied = _bind_runtime_action_inbox_approval(
        RuntimeInvocationStore(tmp_path / "denied"),
        decision="deny",
    )
    expired = _bind_runtime_action_inbox_approval(
        RuntimeInvocationStore(tmp_path / "expired"),
        decision="approve",
        expires_delta=timedelta(minutes=-1),
    )
    changed = _bind_runtime_action_inbox_approval(
        RuntimeInvocationStore(tmp_path / "changed"),
        expected_payload_fingerprint_ref="runtime-payload-fingerprint-ref:changed",
    )

    assert denied.status == "approval_denied"
    assert denied.action_inbox_envelope is not None
    assert denied.action_inbox_envelope.approval_validated is False
    assert "blocked-state:runtime-approval-denied" in (
        denied.action_inbox_envelope.blocked_reason_refs
    )
    assert expired.status == "approval_expired"
    assert expired.action_inbox_envelope is not None
    assert "blocked-state:runtime-approval-expired" in (
        expired.action_inbox_envelope.blocked_reason_refs
    )
    assert changed.status == "execution_blocked"
    assert changed.action_inbox_envelope is not None
    assert "blocked-state:runtime-approval-scope-changed" in (
        changed.action_inbox_envelope.blocked_reason_refs
    )


def test_runtime_gateway_expired_approval_execution_fails_closed_with_receipt(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SHOULD_NOT_RUN",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    expired = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
        expires_delta=timedelta(minutes=-1),
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        expired.invocation_ref,
        _command_request_for_approved_record(command_request, expired),
        _runtime_execute_request(expired),
        idempotency_ref="idempotency-ref:runtime-action-inbox-expired-execute",
    )

    assert calls == []
    assert result.error_category == "RUNTIME_COMMAND_ACTION_INBOX_APPROVAL_EXPIRED"
    assert result.record.status == "execution_blocked"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.record.receipt.command_receipt_metadata is not None
    assert (
        result.record.receipt.command_receipt_metadata.command_execution_attempted
        is False
    )


def test_runtime_gateway_action_inbox_arbitrary_approval_ref_does_not_authorize(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    command_request = _approved_runtime_command_request()
    created = store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-action-inbox-arbitrary-create",
    )
    refs = _runtime_action_inbox_refs(created.record)

    blocked = store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            approval_ref=refs["approval_ref"],
            decision="approve",
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Caller supplied approval refs are not authority.",
        ),
        idempotency_ref="idempotency-ref:runtime-action-inbox-arbitrary-approval",
    )

    assert blocked.status == "execution_blocked"
    assert blocked.action_inbox_envelope is not None
    assert blocked.action_inbox_envelope.approval_validated is False
    assert blocked.policy_decision.command_execution_enabled is False
    assert "blocked-state:runtime-approval-ref-identifier-only" in (
        blocked.action_inbox_envelope.blocked_reason_refs
    )
    assert "blocked-state:runtime-backend-approval-missing" in (
        blocked.action_inbox_envelope.blocked_reason_refs
    )


def test_runtime_gateway_action_inbox_execute_requires_top_level_refs(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SHOULD_NOT_RUN",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        RuntimeExecuteRequest(),
        idempotency_ref="idempotency-ref:runtime-action-inbox-missing-execute-refs",
    )
    replay = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        RuntimeExecuteRequest(),
        idempotency_ref="idempotency-ref:runtime-action-inbox-missing-execute-refs",
    )

    assert calls == []
    assert result.record.status == "execution_blocked"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.error_category == (
        "RUNTIME_COMMAND_EXECUTE_APPROVAL_REF_MISSING_OR_CHANGED"
    )
    assert replay.replayed is True
    assert replay.record.receipt is not None
    assert replay.record.receipt.receipt_ref == result.record.receipt.receipt_ref
    assert replay.error_category == (
        "RUNTIME_COMMAND_EXECUTE_APPROVAL_REF_MISSING_OR_CHANGED"
    )
    read_model = build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    event_kinds = {event["event_kind"] for event in read_model["evidence_timeline"]}
    assert "execution_started" not in event_kinds
    assert "receipt_recorded" in event_kinds


def test_runtime_gateway_action_inbox_safe_disable_after_approval_blocks_runner(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SHOULD_NOT_RUN",
        )

    store = RuntimeInvocationStore(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-action-inbox-disable"),
        idempotency_ref="idempotency-ref:runtime-action-inbox-disable",
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        _command_request_for_approved_record(command_request, approved),
        _runtime_execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-inbox-safe-disabled",
    )

    assert calls == []
    assert result.record.status == "safe_disabled"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.error_category in {
        "RUNTIME_COMMAND_ACTION_INBOX_ENVELOPE_NOT_APPROVED",
        "RUNTIME_COMMAND_SAFE_DISABLED",
    }


def test_runtime_gateway_command_replay_without_receipt_does_not_spawn_again(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"FIRST_ATTEMPT",
        )

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    original_record_receipt = store.record_receipt

    def fail_after_create(*args: object, **kwargs: object) -> object:
        raise RuntimeError("simulated receipt write failure")

    store.record_receipt = fail_after_create  # type: ignore[method-assign]
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )
    with pytest.raises(RuntimeError):
        gateway.invoke_command(
            request,
            idempotency_ref="idempotency-ref:runtime-command-replay-no-receipt",
        )
    assert len(calls) == 1

    store.record_receipt = original_record_receipt  # type: ignore[method-assign]
    replay = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-replay-no-receipt",
    )

    assert len(calls) == 1
    assert replay.replayed is True
    assert replay.record.status == "pending_approval"
    assert replay.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
    assert replay.record.receipt is None
    assert replay.record.adapter_dispatch_started is True


def test_runtime_gateway_safe_disable_blocks_command_before_runner(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SHOULD_NOT_RUN",
        )

    store = RuntimeInvocationStore(tmp_path)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-command-disable"),
        idempotency_ref="idempotency-ref:runtime-command-disable",
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    result = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect current repo status after safe-disable.",
        ),
        idempotency_ref="idempotency-ref:runtime-command-safe-disabled",
    )

    assert result.record.status == "safe_disabled"
    assert result.error_category == "RUNTIME_COMMAND_SAFE_DISABLED"
    assert calls == []


def test_runtime_gateway_late_safe_disable_remains_active_after_receipt(
    tmp_path: Path,
) -> None:
    runner_started = threading.Event()
    release_runner = threading.Event()
    results: list[object] = []
    errors: list[BaseException] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        runner_started.set()
        release_runner.wait(timeout=15)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    def invoke_command() -> None:
        try:
            results.append(
                gateway.invoke_command(
                    RuntimeCommandExecutionRequest(
                        intent="git_status",
                        safe_summary="Inspect current repo status with redacted output.",
                    ),
                    idempotency_ref="idempotency-ref:runtime-command-late-disable",
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    worker = threading.Thread(target=invoke_command)
    worker.start()
    assert runner_started.wait(timeout=15)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-command-late-disable"),
        idempotency_ref="idempotency-ref:runtime-command-late-disable-safe-disable",
    )
    release_runner.set()
    worker.join(timeout=5)

    assert errors == []
    assert len(results) == 1
    result = results[0]
    assert result.record.status == "safe_disabled"
    assert result.record.receipt is not None
    assert result.record.receipt.safe_disable.active is True
    assert (
        result.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-command-late-disable"
    )
    assert result.record.receipt.command_execution_performed is True
    assert store.operator_safe_disable_active() is True


def test_runtime_gateway_command_safe_disable_between_precheck_and_create_blocks_runner(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SHOULD_NOT_RUN",
        )

    store = RuntimeInvocationStore(tmp_path)
    original_safe_disable_active = store.operator_safe_disable_active
    safe_disable_recorded = False

    def racing_safe_disable_check() -> bool:
        nonlocal safe_disable_recorded
        if not safe_disable_recorded:
            safe_disable_recorded = True
            store.safe_disable(
                RuntimeSafeDisableRequest(
                    reason_ref="reason-ref:runtime-command-race-disable"
                ),
                idempotency_ref="idempotency-ref:runtime-command-race-disable",
            )
            return False
        return original_safe_disable_active()

    store.operator_safe_disable_active = racing_safe_disable_check  # type: ignore[method-assign]
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect current repo status with redacted output.",
        ),
        idempotency_ref="idempotency-ref:runtime-command-race",
    )

    assert calls == []
    assert result.record.status == "safe_disabled"
    assert result.error_category == "RUNTIME_COMMAND_SAFE_DISABLED"
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert (
        result.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-command-race-disable"
    )


def test_runtime_gateway_command_duplicate_requests_reserve_idempotency_before_runner(
    tmp_path: Path,
) -> None:
    runner_started = threading.Event()
    release_runner = threading.Event()
    duplicate_receipt_attempted = threading.Event()
    calls = 0
    calls_lock = threading.Lock()
    results: list[object] = []
    errors: list[BaseException] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        with calls_lock:
            calls += 1
        runner_started.set()
        release_runner.wait(timeout=5)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )
    first_store = RuntimeInvocationStore(tmp_path)
    duplicate_store = RuntimeInvocationStore(tmp_path)
    original_record_receipt = duplicate_store.record_receipt

    def observe_duplicate_receipt(*args: Any, **kwargs: Any) -> Any:
        duplicate_receipt_attempted.set()
        return original_record_receipt(*args, **kwargs)

    duplicate_store.record_receipt = observe_duplicate_receipt  # type: ignore[method-assign]
    gateways = [
        RuntimeGateway(
            store=first_store,
            command_adapter=GovernedCommandRuntimeAdapter(
                workspace_root=ROOT,
                runner=runner,
            ),
        ),
        RuntimeGateway(
            store=duplicate_store,
            command_adapter=GovernedCommandRuntimeAdapter(
                workspace_root=ROOT,
                runner=runner,
            ),
        ),
    ]

    def invoke_command(gateway: RuntimeGateway) -> None:
        try:
            results.append(
                gateway.invoke_command(
                    request,
                    idempotency_ref="idempotency-ref:runtime-command-concurrent",
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    first = threading.Thread(target=invoke_command, args=(gateways[0],))
    first.start()
    assert runner_started.wait(timeout=5)
    second = threading.Thread(target=invoke_command, args=(gateways[1],))
    second.start()
    assert not duplicate_receipt_attempted.wait(timeout=0.2)
    assert second.is_alive() is True
    release_runner.set()
    first.join(timeout=15)
    second.join(timeout=15)

    assert first.is_alive() is False
    assert second.is_alive() is False
    assert errors == []
    assert len(results) == 2
    assert calls == 1
    assert duplicate_receipt_attempted.is_set() is False
    assert sum(1 for result in results if result.replayed) == 1
    assert any(
        result.record.receipt is not None
        and result.record.receipt.command_execution_performed
        for result in results
    )


def test_runtime_gateway_command_duplicate_timeout_does_not_compete_for_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_started = threading.Event()
    release_runner = threading.Event()
    duplicate_receipt_attempted = threading.Event()
    calls = 0
    calls_lock = threading.Lock()
    first_results: list[Any] = []
    errors: list[BaseException] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        with calls_lock:
            calls += 1
        runner_started.set()
        assert release_runner.wait(timeout=5)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
        timeout_seconds=0.01,
    )
    first_store = RuntimeInvocationStore(tmp_path)
    duplicate_store = RuntimeInvocationStore(tmp_path)
    original_record_receipt = duplicate_store.record_receipt

    def observe_duplicate_receipt(*args: Any, **kwargs: Any) -> Any:
        duplicate_receipt_attempted.set()
        return original_record_receipt(*args, **kwargs)

    duplicate_store.record_receipt = observe_duplicate_receipt  # type: ignore[method-assign]
    monkeypatch.setattr(
        "ultimate_ai_agent.core.runtime_gateway.command."
        "COMMAND_RUNTIME_RECEIPT_GRACE_SECONDS",
        0.0,
    )
    first_gateway = RuntimeGateway(
        store=first_store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    duplicate_gateway = RuntimeGateway(
        store=duplicate_store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    def invoke_first() -> None:
        try:
            first_results.append(
                first_gateway.invoke_command(
                    request,
                    idempotency_ref="idempotency-ref:runtime-command-timeout-race",
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    first = threading.Thread(target=invoke_first)
    first.start()
    assert runner_started.wait(timeout=5)
    try:
        duplicate = duplicate_gateway.invoke_command(
            request,
            idempotency_ref="idempotency-ref:runtime-command-timeout-race",
        )
        assert duplicate.replayed is True
        assert duplicate.record.receipt is None
        assert (
            duplicate.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
        )
        assert duplicate_receipt_attempted.is_set() is False
        assert calls == 1
    finally:
        release_runner.set()
        first.join(timeout=15)
        assert first.is_alive() is False

    assert errors == []
    assert len(first_results) == 1
    assert first_results[0].record.receipt is not None
    assert first_results[0].record.receipt.command_execution_performed is True
    completed_replay = duplicate_gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-timeout-race",
    )
    assert completed_replay.replayed is True
    assert completed_replay.record.receipt is not None
    assert completed_replay.record.receipt.command_execution_performed is True
    assert duplicate_receipt_attempted.is_set() is False
    assert calls == 1


def test_runtime_gateway_command_coordinates_ownership_across_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "runtime-state"
    started_path = tmp_path / "owner-started"
    release_path = tmp_path / "owner-release"
    context = multiprocessing.get_context("spawn")
    owner = context.Process(
        target=_run_cross_process_command_owner,
        args=(state_dir, started_path, release_path),
    )
    owner.start()
    try:
        deadline = time.monotonic() + 10
        while not started_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert started_path.exists()
    except BaseException:
        release_path.write_text("release", encoding="utf-8")
        owner.join(timeout=15)
        raise
    monkeypatch.setattr(
        "ultimate_ai_agent.core.runtime_gateway.command."
        "COMMAND_RUNTIME_RECEIPT_GRACE_SECONDS",
        0.0,
    )
    duplicate_calls: list[object] = []

    def duplicate_runner(**kwargs: object) -> RuntimeCommandRunResult:
        duplicate_calls.append(kwargs)
        raise AssertionError("duplicate command runner must not execute")

    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
        timeout_seconds=0.05,
    )
    duplicate_gateway = RuntimeGateway(
        store=RuntimeInvocationStore(state_dir),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=duplicate_runner,
        ),
    )
    try:
        unrelated_calls: list[object] = []

        def unrelated_runner(**kwargs: object) -> RuntimeCommandRunResult:
            unrelated_calls.append(kwargs)
            return RuntimeCommandRunResult(
                exit_code=0,
                timed_out=False,
                duration_ms=1,
                output_bytes=b"SAFE_STATUS",
            )

        unrelated_started = time.monotonic()
        unrelated = RuntimeGateway(
            store=RuntimeInvocationStore(state_dir),
            command_adapter=GovernedCommandRuntimeAdapter(
                workspace_root=ROOT,
                runner=unrelated_runner,
            ),
        ).invoke_command(
            request,
            idempotency_ref="idempotency-ref:runtime-command-unrelated",
        )
        assert time.monotonic() - unrelated_started < 5
        assert unrelated.record.receipt is not None
        assert unrelated.record.receipt.command_execution_performed is True
        assert len(unrelated_calls) == 1

        conflicting_request = request.model_copy(
            update={
                "safe_summary": (
                    "Inspect a different governed status payload with redacted output."
                )
            }
        )
        conflict_started = time.monotonic()
        with pytest.raises(RuntimeInvocationConflictError):
            duplicate_gateway.invoke_command(
                conflicting_request,
                idempotency_ref="idempotency-ref:runtime-command-cross-process",
            )
        assert time.monotonic() - conflict_started < 5

        duplicate = duplicate_gateway.invoke_command(
            request,
            idempotency_ref="idempotency-ref:runtime-command-cross-process",
        )
        assert duplicate.replayed is True
        assert duplicate.record.receipt is None
        assert duplicate.record.replay_count == 1
        assert (
            duplicate.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
        )
        assert duplicate_calls == []
    finally:
        release_path.write_text("release", encoding="utf-8")
        owner.join(timeout=15)

    assert owner.is_alive() is False
    assert owner.exitcode == 0
    completed_store = RuntimeInvocationStore(state_dir)
    completed = RuntimeGateway(
        store=completed_store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=duplicate_runner,
        ),
    ).invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-cross-process",
    )
    assert completed.replayed is True
    assert completed.record.receipt is not None
    assert completed.record.replay_count == 1
    assert completed.record.receipt.command_execution_performed is True
    assert duplicate_calls == []
    timeout_race = runtime_command._in_progress_command_replay_result(
        store=RuntimeInvocationStore(state_dir),
        invocation_request=runtime_command_invocation_request(request),
        idempotency_ref="idempotency-ref:runtime-command-cross-process",
    )
    assert timeout_race.record.receipt is not None
    assert timeout_race.error_category is None
    assert timeout_race.exit_code == 0
    assert timeout_race.replayed is True


def test_runtime_gateway_command_retries_pre_reservation_lease_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "runtime-state"
    started_path = tmp_path / "lease-started"
    release_path = tmp_path / "lease-release"
    context = multiprocessing.get_context("spawn")
    owner = context.Process(
        target=_hold_cross_process_command_lease_before_reservation,
        args=(state_dir, started_path, release_path),
    )
    owner.start()
    try:
        deadline = time.monotonic() + 10
        while not started_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert started_path.exists()
    except BaseException:
        release_path.write_text("release", encoding="utf-8")
        owner.join(timeout=15)
        raise
    monkeypatch.setattr(
        runtime_command,
        "COMMAND_RUNTIME_RECEIPT_GRACE_SECONDS",
        0.0,
    )
    results: list[RuntimeCommandGatewayResult] = []
    errors: list[BaseException] = []

    def invoke_after_owner() -> None:
        try:
            results.append(
                RuntimeGateway(
                    store=RuntimeInvocationStore(state_dir),
                    command_adapter=GovernedCommandRuntimeAdapter(
                        workspace_root=ROOT,
                        runner=lambda **kwargs: RuntimeCommandRunResult(
                            exit_code=0,
                            timed_out=False,
                            duration_ms=1,
                            output_bytes=b"SAFE_STATUS",
                        ),
                    ),
                ).invoke_command(
                    RuntimeCommandExecutionRequest(
                        intent="git_status",
                        safe_summary=(
                            "Inspect current repo status with redacted output."
                        ),
                        timeout_seconds=0.01,
                    ),
                    idempotency_ref=("idempotency-ref:runtime-command-pre-reservation"),
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    duplicate = threading.Thread(target=invoke_after_owner)
    try:
        duplicate.start()
        time.sleep(0.1)
        assert duplicate.is_alive() is True
    finally:
        release_path.write_text("release", encoding="utf-8")
        owner.join(timeout=15)
        duplicate.join(timeout=15)

    assert owner.is_alive() is False
    assert owner.exitcode == 0
    assert duplicate.is_alive() is False
    assert errors == []
    assert len(results) == 1
    assert results[0].record.receipt is not None
    assert results[0].record.receipt.command_execution_performed is True


def test_runtime_gateway_command_execution_lock_uses_exact_byte_ranges(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    paths = {
        runtime_command._command_execution_lock_path(store) for _index in range(1024)
    }
    offsets = {
        runtime_command._command_execution_lock_offset(
            runtime_command._command_execution_claim_ref(
                store,
                f"idempotency-ref:runtime-command-range-{index}",
            )
        )
        for index in range(1024)
    }

    assert paths == {tmp_path / ".runtime-command-execution.lock"}
    assert len(offsets) == 1024
    assert all(0 <= offset < (1 << 63) for offset in offsets)


def test_runtime_gateway_command_process_lock_is_python_310_weakref_compatible() -> (
    None
):
    process_lock = runtime_command._CommandExecutionProcessLock()

    assert "__slots__" not in type(process_lock).__dict__
    assert weakref.ref(process_lock)() is process_lock


def test_runtime_gateway_releasing_one_range_preserves_other_process_lock(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    first_claim = runtime_command._command_execution_claim_ref(
        store,
        "idempotency-ref:runtime-command-shared-file-first",
    )
    second_claim = runtime_command._command_execution_claim_ref(
        store,
        "idempotency-ref:runtime-command-shared-file-second",
    )
    second_offset = runtime_command._command_execution_lock_offset(second_claim)
    assert runtime_command._command_execution_lock_offset(first_claim) != second_offset

    first_lease = runtime_command._acquire_command_execution_lease(
        store=store,
        claim_ref=first_claim,
        timeout_seconds=0.1,
    )
    second_lease = runtime_command._acquire_command_execution_lease(
        store=store,
        claim_ref=second_claim,
        timeout_seconds=0.1,
    )
    assert first_lease is not None
    assert second_lease is not None
    assert first_lease.lock_file is second_lease.lock_file

    first_lease.release()
    blocked_result_path = tmp_path / "second-range-blocked"
    context = multiprocessing.get_context("spawn")
    blocked_probe = context.Process(
        target=_probe_command_execution_byte_range,
        args=(
            runtime_command._command_execution_lock_path(store),
            second_offset,
            blocked_result_path,
        ),
    )
    blocked_probe.start()
    blocked_probe.join(timeout=10)
    try:
        assert blocked_probe.is_alive() is False
        assert blocked_probe.exitcode == 0
        assert blocked_result_path.read_text(encoding="utf-8") == "blocked"
    finally:
        second_lease.release()

    acquired_result_path = tmp_path / "second-range-acquired"
    acquired_probe = context.Process(
        target=_probe_command_execution_byte_range,
        args=(
            runtime_command._command_execution_lock_path(store),
            second_offset,
            acquired_result_path,
        ),
    )
    acquired_probe.start()
    acquired_probe.join(timeout=10)
    assert acquired_probe.is_alive() is False
    assert acquired_probe.exitcode == 0
    assert acquired_result_path.read_text(encoding="utf-8") == "acquired"


def test_runtime_gateway_locked_reservation_refreshes_callers_store(
    tmp_path: Path,
) -> None:
    caller_store = RuntimeInvocationStore(tmp_path)
    assert caller_store.list_invocations() == []
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )
    owner_result = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=lambda **kwargs: RuntimeCommandRunResult(
                exit_code=0,
                timed_out=False,
                duration_ms=1,
                output_bytes=b"SAFE_STATUS",
            ),
        ),
    ).invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-store-refresh",
    )
    assert owner_result.record.receipt is not None

    refreshed = runtime_command._locked_command_reservation(
        store=caller_store,
        idempotency_ref="idempotency-ref:runtime-command-store-refresh",
    )

    assert refreshed is not None
    assert refreshed.receipt is not None
    assert (
        caller_store.get_invocation_for_idempotency(
            "idempotency-ref:runtime-command-store-refresh"
        )
        == refreshed
    )


def test_runtime_gateway_command_execution_lock_closes_on_lockf_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    claim_ref = runtime_command._command_execution_claim_ref(
        store,
        "idempotency-ref:runtime-command-flock-error",
    )
    closed_descriptors: list[int] = []
    original_close = os.close

    def fail_lockf(
        descriptor: int,
        operation: int,
        length: int,
        offset: int,
        whence: int,
    ) -> None:
        raise OSError(95, "operation not supported")

    def observe_close(descriptor: int) -> None:
        closed_descriptors.append(descriptor)
        original_close(descriptor)

    monkeypatch.setattr(runtime_command.fcntl, "lockf", fail_lockf)
    monkeypatch.setattr(runtime_command.os, "close", observe_close)

    with pytest.raises(OSError, match="operation not supported"):
        runtime_command._acquire_command_execution_lease(
            store=store,
            claim_ref=claim_ref,
            timeout_seconds=0.01,
        )

    assert len(closed_descriptors) == 1


def test_runtime_gateway_command_execution_lock_retries_eacces_contention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
    claim_ref = runtime_command._command_execution_claim_ref(
        store,
        "idempotency-ref:runtime-command-eacces-contention",
    )
    original_lockf = runtime_command.fcntl.lockf
    acquisition_attempts = 0

    def contend_once(
        descriptor: int,
        operation: int,
        length: int,
        offset: int,
        whence: int,
    ) -> object:
        nonlocal acquisition_attempts
        if operation & runtime_command.fcntl.LOCK_UN:
            return original_lockf(descriptor, operation, length, offset, whence)
        acquisition_attempts += 1
        if acquisition_attempts == 1:
            raise PermissionError(errno.EACCES, "range lock contention")
        return original_lockf(descriptor, operation, length, offset, whence)

    monkeypatch.setattr(runtime_command.fcntl, "lockf", contend_once)

    lease = runtime_command._acquire_command_execution_lease(
        store=store,
        claim_ref=claim_ref,
        timeout_seconds=0.1,
    )
    assert lease is not None
    try:
        assert acquisition_attempts == 2
    finally:
        lease.release()


def test_runtime_launcher_command_run_cli_reports_in_progress_replay_without_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect current repo status with redacted output.",
    )
    record = (
        RuntimeInvocationStore(tmp_path)
        .create_invocation(
            runtime_command_invocation_request(request),
            idempotency_ref="idempotency-ref:runtime-command-cli-in-progress",
            command_gateway_validated=True,
        )
        .record
    )
    result = RuntimeCommandGatewayResult(
        record=record,
        error_category="RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS",
        replayed=True,
        command_execution_enabled=True,
    )

    class _InProgressGateway:
        def __init__(self, **kwargs: object) -> None:
            pass

        def invoke_command(
            self,
            request: RuntimeCommandExecutionRequest,
            *,
            idempotency_ref: str,
        ) -> RuntimeCommandGatewayResult:
            return result

    monkeypatch.setattr(uaa_runtime, "RuntimeGateway", _InProgressGateway)
    args = argparse.Namespace(
        intent="git_status",
        profile="local-runtime",
        mission_ref=None,
        target_ref=[],
        summary="Inspect current repo status with redacted output.",
        timeout_seconds=5.0,
        output_byte_limit=4096,
        metadata_ref=[],
        idempotency_ref="idempotency-ref:runtime-command-cli-in-progress",
        state_dir=str(tmp_path / "cli-state"),
        json=True,
    )

    assert uaa_runtime._command_run(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False
    assert payload["replayed"] is True
    assert payload["error_category"] == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
    assert payload["receipt_ref"] is None
    assert payload["execution_performed"] is False
    assert payload["command_execution_performed"] is False
    assert payload["record"]["receipt"] is None


def test_runtime_launcher_command_run_cli_redacts_storage_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _UnavailableGoalRuntime:
        @staticmethod
        def sync_runtime_invocations(
            _records: object,
            *,
            invocation_store: object,
        ) -> None:
            del invocation_store
            raise OSError("raw storage failure must stay redacted")

    monkeypatch.setattr(
        uaa_runtime,
        "_goal_runtime_service",
        lambda _args: _UnavailableGoalRuntime(),
    )
    args = argparse.Namespace(
        intent="git_status",
        profile="local-runtime",
        mission_ref=None,
        target_ref=[],
        summary="Inspect current repo status with redacted output.",
        timeout_seconds=5.0,
        output_byte_limit=4096,
        metadata_ref=[],
        idempotency_ref="idempotency-ref:runtime-command-cli-storage-failure",
        state_dir=str(tmp_path / "cli-state"),
        json=True,
    )

    assert uaa_runtime._command_run(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False
    assert payload["error_category"] == "GOAL_RUNTIME_STORAGE_UNAVAILABLE"
    assert payload["safe_refs_only"] is True
    assert payload["raw_paths_omitted"] is True
    assert "raw storage failure" not in json.dumps(payload)


def test_runtime_gateway_command_nonzero_and_timeout_receipts(
    tmp_path: Path,
) -> None:
    def nonzero_runner(**kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=128,
            timed_out=False,
            duration_ms=2,
            output_bytes=b"fatal: output redacted",
            error_category="RUNTIME_COMMAND_NONZERO_EXIT",
        )

    nonzero_gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path / "nonzero"),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=nonzero_runner,
        ),
    )
    nonzero = nonzero_gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect repo status with nonzero receipt.",
        ),
        idempotency_ref="idempotency-ref:runtime-command-nonzero",
    )

    assert nonzero.record.status == "receipt_recorded"
    assert nonzero.exit_code == 128
    assert nonzero.error_category == "RUNTIME_COMMAND_NONZERO_EXIT"
    assert (
        nonzero.record.receipt.command_receipt_metadata.status_category
        == "nonzero_exit"
    )

    def timeout_runner(**kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=None,
            timed_out=True,
            duration_ms=30_000,
            output_bytes=b"",
            error_category="RUNTIME_COMMAND_TIMEOUT",
        )

    timeout_gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path / "timeout"),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=timeout_runner,
        ),
    )
    timeout = timeout_gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect repo status with timeout receipt.",
        ),
        idempotency_ref="idempotency-ref:runtime-command-timeout",
    )

    assert timeout.record.status == "receipt_recorded"
    assert timeout.timed_out is True
    assert timeout.error_category == "RUNTIME_COMMAND_TIMEOUT"
    assert timeout.record.receipt.command_receipt_metadata.status_category == "timeout"


@pytest.mark.parametrize("posture_change", ["lease_revoked", "safe_disable"])
def test_runtime_gateway_local_model_replay_without_receipt_is_atomic_and_no_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture_change: str,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("FIRST_MODEL_ATTEMPT")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory
        ),
        local_model_runtime_enabled=True,
    )
    original_record_receipt = store.record_receipt

    def fail_after_create(*args: object, **kwargs: object) -> object:
        raise RuntimeError("simulated local model receipt write failure")

    store.record_receipt = fail_after_create  # type: ignore[method-assign]
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    with pytest.raises(RuntimeError):
        gateway.invoke_local_model(
            request,
            idempotency_ref="idempotency-ref:runtime-local-model-replay-no-receipt",
        )
    assert calls == 0

    store.record_receipt = original_record_receipt  # type: ignore[method-assign]
    if posture_change == "lease_revoked":
        authority_snapshots = iter(([provider_model_execute_authority_lease()], []))
        monkeypatch.setattr(
            store,
            "current_authority_leases",
            lambda: next(authority_snapshots),
        )
    else:
        original_replay_recovery = store.record_local_model_replay_without_receipt
        safe_disable_recorded = False

        def racing_replay_recovery(*args: object, **kwargs: object) -> object:
            nonlocal safe_disable_recorded
            if not safe_disable_recorded:
                safe_disable_recorded = True
                store.safe_disable(
                    RuntimeSafeDisableRequest(
                        reason_ref="reason-ref:no-receipt-replay-race"
                    ),
                    idempotency_ref="idempotency-ref:no-receipt-replay-race",
                )
            return original_replay_recovery(*args, **kwargs)

        monkeypatch.setattr(
            store,
            "record_local_model_replay_without_receipt",
            racing_replay_recovery,
        )
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replay-no-receipt",
    )

    assert calls == 0
    assert replay.replayed is True
    expected_status = (
        "execution_blocked" if posture_change == "lease_revoked" else "safe_disabled"
    )
    assert replay.record.status == expected_status
    assert (
        replay.error_category == "RUNTIME_LOCAL_MODEL_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT"
    )
    assert replay.record.receipt is not None
    assert replay.record.receipt.model_call_performed is False
    assert replay.record.receipt.invocation_status == "execution_blocked"
    assert "blocked before transport" in replay.record.receipt.safe_summary.lower()
    assert replay.record.policy_decision.allowed_to_execute is False
    assert replay.record.policy_decision.adapter_execution_enabled is False
    assert replay.record.policy_decision.model_call_enabled is False
    assert replay.record.policy_decision.invocation_status == expected_status
    if posture_change == "lease_revoked":
        assert replay.record.policy_decision.authority_decision_outcome == (
            "degrade_to_draft"
        )
        monkeypatch.setattr(store, "current_authority_leases", lambda: [])
    else:
        assert replay.record.safe_disable.active is True
        assert replay.record.receipt.safe_disable.active is True

    second_replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replay-no-receipt",
    )
    assert calls == 0
    assert second_replay.replayed is True
    assert second_replay.record.status == expected_status
    assert second_replay.error_category == (
        "RUNTIME_LOCAL_MODEL_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT"
        if posture_change == "lease_revoked"
        else "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
    )
    assert second_replay.record.receipt is not None
    assert second_replay.record.receipt.model_call_performed is False
    assert second_replay.record.policy_decision.allowed_to_execute is False
    assert second_replay.record.policy_decision.adapter_execution_enabled is False
    assert second_replay.record.policy_decision.model_call_enabled is False


def test_runtime_gateway_persists_unknown_attempt_marker_before_transport(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("ATTEMPT_WITH_RECEIPT_WRITE_FAILURE")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    original_record_receipt = store.record_receipt
    receipt_writes = 0

    def fail_final_receipt(*args: object, **kwargs: object) -> object:
        nonlocal receipt_writes
        receipt_writes += 1
        if receipt_writes == 1:
            return original_record_receipt(*args, **kwargs)
        raise RuntimeError("simulated final receipt write failure")

    store.record_receipt = fail_final_receipt  # type: ignore[method-assign]
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Persist an outcome-unknown marker before transport.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-unknown-attempt"

    with pytest.raises(RuntimeError, match="final receipt write failure"):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    marker = store.get_invocation_for_idempotency(idempotency_ref)
    assert marker is not None
    assert marker.receipt is not None
    assert marker.receipt.model_receipt_metadata is not None
    assert marker.receipt.model_receipt_metadata.attempt_outcome_unknown is True
    assert marker.receipt.model_receipt_metadata.error_category == (
        "RUNTIME_LOCAL_MODEL_ATTEMPT_OUTCOME_UNKNOWN"
    )
    assert marker.receipt.model_call_performed is False

    store.record_receipt = original_record_receipt  # type: ignore[method-assign]
    replay = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    assert replay.replayed is True
    assert replay.error_category == "RUNTIME_LOCAL_MODEL_ATTEMPT_IN_PROGRESS"
    assert replay.record.status == marker.status
    assert replay.record.policy_decision == marker.policy_decision
    assert replay.record.receipt == marker.receipt


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status_code", 200),
        ("response_received", True),
        ("response_byte_count", 1),
        ("response_truncated", True),
        ("bounded_preview_returned", True),
    ],
)
def test_runtime_unknown_attempt_marker_rejects_response_evidence(
    field: str,
    value: object,
) -> None:
    payload: dict[str, object] = {
        "model_ref": "uaa-local-runtime",
        "endpoint_ref": "runtime-endpoint-ref:unknown-attempt-validation",
        "error_category": "RUNTIME_LOCAL_MODEL_ATTEMPT_OUTCOME_UNKNOWN",
        "attempt_outcome_unknown": True,
    }
    payload[field] = value

    with pytest.raises(
        ValueError,
        match="RUNTIME_MODEL_ATTEMPT_OUTCOME_UNKNOWN_INVALID",
    ):
        RuntimeLocalModelReceiptMetadata(**payload)


def test_runtime_unknown_attempt_marker_builder_defaults_execution_flags_off(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_provider_model_execute(tmp_path)
    created = store.create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:unknown-marker-builder",
    )
    metadata = RuntimeLocalModelReceiptMetadata(
        model_ref="uaa-local-runtime",
        endpoint_ref="runtime-endpoint-ref:unknown-marker-builder",
        error_category="RUNTIME_LOCAL_MODEL_ATTEMPT_OUTCOME_UNKNOWN",
        attempt_outcome_unknown=True,
    )

    receipt = build_local_model_receipt(created.record, metadata=metadata)

    assert receipt.execution_performed is False
    assert receipt.adapter_execution_performed is False
    assert receipt.model_call_performed is False
    with pytest.raises(
        ValueError,
        match="RUNTIME_MODEL_ATTEMPT_OUTCOME_UNKNOWN_EXECUTION_INVALID",
    ):
        RuntimeInvocationReceipt.model_validate(
            {
                **receipt.model_dump(mode="json"),
                "execution_performed": True,
                "adapter_execution_performed": True,
                "model_call_performed": True,
            }
        )


def test_runtime_gateway_replays_complete_failed_local_model_receipt_exactly(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        raise ValueError("M164_MODEL_ID_UNSAFE")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Replay one complete failed receipt exactly.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-complete-error"

    first = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)
    replay = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 1
    assert first.error_category == "M164_MODEL_ID_UNSAFE"
    assert first.record.status == "receipt_recorded"
    assert first.record.receipt is not None
    assert first.record.receipt.model_receipt_metadata is not None
    assert first.record.receipt.model_receipt_metadata.attempt_outcome_unknown is False
    assert replay.replayed is True
    assert replay.error_category == first.error_category
    assert replay.record.status == "receipt_recorded"
    assert replay.record.receipt == first.record.receipt


def test_runtime_gateway_inflight_marker_preserves_execution_policy_provenance(
    tmp_path: Path,
) -> None:
    transport_started = threading.Event()
    release_transport = threading.Event()
    calls = 0
    results: list[object] = []
    errors: list[BaseException] = []
    transport = _BlockingFakeM164GatewayTransport(
        "INFLIGHT_POLICY_PROVENANCE_OK",
        transport_started=transport_started,
        release_transport=release_transport,
    )

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return transport

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Preserve exact policy provenance for an in-flight call.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-inflight-policy"

    def invoke_first() -> None:
        try:
            results.append(
                gateway.invoke_local_model(
                    request,
                    idempotency_ref=idempotency_ref,
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    first = threading.Thread(target=invoke_first)
    first.start()
    assert transport_started.wait(timeout=5)
    marker = store.get_invocation_for_idempotency(idempotency_ref)
    assert marker is not None
    assert marker.receipt is not None
    assert marker.receipt.model_receipt_metadata is not None
    assert marker.receipt.model_receipt_metadata.attempt_outcome_unknown is True
    duplicate = gateway.invoke_local_model(
        request,
        idempotency_ref=idempotency_ref,
    )
    assert duplicate.replayed is True
    assert duplicate.error_category == "RUNTIME_LOCAL_MODEL_ATTEMPT_IN_PROGRESS"
    assert duplicate.record.status == marker.status
    assert duplicate.record.policy_decision == marker.policy_decision
    assert duplicate.record.receipt == marker.receipt
    persisted_during_attempt = store.get_invocation(duplicate.record.invocation_ref)
    assert persisted_during_attempt.status == marker.status
    assert persisted_during_attempt.policy_decision == marker.policy_decision
    assert persisted_during_attempt.receipt == marker.receipt
    assert (
        gateway.goal_runtime_service.sync_runtime_invocations(
            store.list_invocations(),
            invocation_store=store,
        )
        == []
    )
    assert (
        gateway.goal_runtime_service.events.replay(marker.invocation_ref).events == []
    )

    release_transport.set()
    first.join(timeout=5)

    assert errors == []
    assert len(results) == 1
    assert calls == 1
    durable = store.get_invocation(duplicate.record.invocation_ref)
    assert durable.receipt is not None
    assert durable.receipt.model_call_performed is True
    assert durable.policy_decision.allowed_to_execute is True
    assert durable.policy_decision.authority_lease_ref == (
        "authority-lease-ref:test-provider-model-execute"
    )
    assert [
        event.event_kind
        for event in gateway.goal_runtime_service.events.replay(
            durable.invocation_ref
        ).events
    ] == ["run_started", "receipt_recorded"]


@pytest.mark.parametrize("posture_change", ["safe_disabled", "lease_revoked"])
def test_runtime_gateway_inflight_final_receipt_preserves_current_denial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture_change: str,
) -> None:
    transport_started = threading.Event()
    release_transport = threading.Event()
    calls = 0
    invocation_refs: list[str] = []
    errors: list[BaseException] = []
    transport = _BlockingFakeM164GatewayTransport(
        "INFLIGHT_DENIAL_PROVENANCE_OK",
        transport_started=transport_started,
        release_transport=release_transport,
    )

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return transport

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Preserve current denial after an in-flight attempt.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-inflight-denial"

    def invoke_first() -> None:
        try:
            result = gateway.invoke_local_model(
                request,
                idempotency_ref=idempotency_ref,
            )
            invocation_refs.append(result.record.invocation_ref)
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    first = threading.Thread(target=invoke_first)
    first.start()
    assert transport_started.wait(timeout=5)
    if posture_change == "safe_disabled":
        store.safe_disable(
            RuntimeSafeDisableRequest(
                reason_ref="reason-ref:inflight-finalization-denial"
            ),
            idempotency_ref="idempotency-ref:inflight-finalization-denial",
        )
    else:
        monkeypatch.setattr(store, "current_authority_leases", lambda: [])
    release_transport.set()
    first.join(timeout=5)

    assert errors == []
    assert len(invocation_refs) == 1
    assert calls == 1
    durable = store.get_invocation(invocation_refs[0])
    assert durable.status == (
        "safe_disabled" if posture_change == "safe_disabled" else "execution_blocked"
    )
    assert durable.policy_decision.allowed_to_execute is False
    assert durable.policy_decision.adapter_execution_enabled is False
    assert durable.policy_decision.model_call_enabled is False
    assert durable.receipt is not None
    assert durable.receipt.execution_performed is True
    assert durable.receipt.adapter_execution_performed is True
    assert durable.receipt.model_call_performed is True
    assert durable.receipt.model_receipt_metadata is not None
    assert durable.receipt.model_receipt_metadata.error_category is None
    assert durable.receipt.safe_disable.active is (posture_change == "safe_disabled")


def test_runtime_gateway_no_receipt_recovery_preserves_concurrently_arrived_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("CONCURRENT_RECEIPT_MODEL_RESPONSE")

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    original_record_receipt = store.record_receipt

    def fail_receipt_write(*args: object, **kwargs: object) -> object:
        raise RuntimeError("simulated receipt coordination gap")

    store.record_receipt = fail_receipt_write  # type: ignore[method-assign]
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    idempotency_ref = "idempotency-ref:runtime-local-model-concurrent-receipt"
    with pytest.raises(RuntimeError, match="receipt coordination gap"):
        gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    store.record_receipt = original_record_receipt  # type: ignore[method-assign]
    original_recovery = store.record_local_model_replay_without_receipt
    durable_receipt = None

    def recording_concurrent_receipt(*args: object, **kwargs: object) -> object:
        nonlocal durable_receipt
        invocation_ref = str(args[0])
        current = store.get_invocation(invocation_ref)
        metadata = RuntimeLocalModelReceiptMetadata(
            model_ref=request.model_ref,
            endpoint_ref="runtime-endpoint-ref:concurrent-receipt",
            request_byte_count=37,
            response_byte_count=41,
            status_code=200,
            response_received=True,
        )
        durable_receipt = build_local_model_receipt(
            current,
            metadata=metadata,
            execution_performed=True,
            model_call_performed=True,
        )
        original_record_receipt(
            invocation_ref,
            durable_receipt,
            idempotency_ref="idempotency-ref:concurrent-real-receipt",
            payload_fingerprint_ref=(
                "runtime-operation-fingerprint-ref:concurrent-real-receipt"
            ),
        )
        return original_recovery(*args, **kwargs)

    monkeypatch.setattr(
        store,
        "record_local_model_replay_without_receipt",
        recording_concurrent_receipt,
    )
    replay = gateway.invoke_local_model(request, idempotency_ref=idempotency_ref)

    assert calls == 0
    assert durable_receipt is not None
    assert replay.replayed is True
    assert replay.error_category is None
    assert replay.record.receipt == durable_receipt
    assert replay.record.receipt.model_call_performed is True
    assert replay.request_byte_count == 37
    assert replay.response_byte_count == 41


def test_runtime_gateway_local_model_replay_after_safe_disable_keeps_idempotency_shape(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SAFE_MODEL_RESPONSE")

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-safe-disable-replay",
    )
    store.safe_disable(
        RuntimeSafeDisableRequest(
            reason_ref="reason-ref:runtime-local-model-replay-disable"
        ),
        idempotency_ref="idempotency-ref:runtime-local-model-replay-disable",
    )
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-safe-disable-replay",
    )

    assert first.record.receipt is not None
    assert first.record.status == "execution_blocked"
    assert calls == 0
    assert replay.replayed is True
    assert replay.record.status == "safe_disabled"
    assert replay.record.policy_decision.allowed_to_execute is False
    assert replay.record.policy_decision.adapter_execution_enabled is False
    assert replay.record.policy_decision.model_call_enabled is False
    assert replay.record.receipt is not None
    assert replay.record.receipt.safe_disable.active is True
    assert (
        replay.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-local-model-replay-disable"
    )


def test_runtime_gateway_local_model_safe_disable_between_precheck_and_create_blocks_transport(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SHOULD_NOT_RUN")

    store = RuntimeInvocationStore(tmp_path)
    original_safe_disable_active = store.operator_safe_disable_active
    safe_disable_recorded = False

    def racing_safe_disable_check() -> bool:
        nonlocal safe_disable_recorded
        if not safe_disable_recorded:
            safe_disable_recorded = True
            store.safe_disable(
                RuntimeSafeDisableRequest(
                    reason_ref="reason-ref:runtime-local-model-race-disable"
                ),
                idempotency_ref="idempotency-ref:runtime-local-model-race-disable",
            )
            return False
        return original_safe_disable_active()

    store.operator_safe_disable_active = racing_safe_disable_check  # type: ignore[method-assign]
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory
        ),
        local_model_runtime_enabled=True,
    )

    result = gateway.invoke_local_model(
        RuntimeLocalModelCallRequest(
            base_url="http://127.0.0.1:8080",
            model_ref="uaa-local-runtime",
            messages=[
                RuntimeLocalModelMessage(role="user", content=REDACTED_TEST_PROMPT)
            ],
            safe_summary="Run local model runtime as an untrusted proposal.",
        ),
        idempotency_ref="idempotency-ref:runtime-local-model-race",
    )

    assert calls == 0
    assert result.record.status == "safe_disabled"
    assert result.error_category == "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is False
    assert (
        result.record.receipt.safe_disable.reason_ref
        == "reason-ref:runtime-local-model-race-disable"
    )


@pytest.mark.parametrize(
    "posture_change",
    ["safe_disabled", "runtime_disabled", "lease_revoked", "kill_switch"],
)
def test_runtime_gateway_local_model_posture_change_at_transport_boundary_blocks_send(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture_change: str,
) -> None:
    calls = 0
    transport = FakeM164GatewayTransport("SHOULD_NOT_RUN")
    posture_changed = False

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        nonlocal calls, posture_changed
        calls += 1
        if not posture_changed:
            posture_changed = True
            if posture_change == "safe_disabled":
                store.safe_disable(
                    RuntimeSafeDisableRequest(
                        reason_ref="reason-ref:runtime-local-model-marker-disable"
                    ),
                    idempotency_ref=(
                        "idempotency-ref:runtime-local-model-marker-disable"
                    ),
                )
            elif posture_change == "lease_revoked":
                monkeypatch.setattr(store, "current_authority_leases", lambda: [])
            elif posture_change == "runtime_disabled":
                monkeypatch.setattr(
                    gateway,
                    "_local_model_runtime_enabled",
                    False,
                )
            else:
                monkeypatch.setattr(
                    store,
                    "authority_lease_kill_switch_engaged",
                    lambda: True,
                )
        return transport

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    result = gateway.invoke_local_model(
        RuntimeLocalModelCallRequest(
            base_url="http://127.0.0.1:8080",
            model_ref="uaa-local-runtime",
            messages=[
                RuntimeLocalModelMessage(
                    role="user",
                    content=REDACTED_TEST_PROMPT,
                )
            ],
            safe_summary="Block changed runtime posture before transport.",
        ),
        idempotency_ref="idempotency-ref:runtime-local-model-marker-race",
    )

    assert posture_changed is True
    assert calls == 1
    assert transport.calls == []
    expected_error = (
        "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
        if posture_change == "safe_disabled"
        else (
            "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
            if posture_change == "runtime_disabled"
            else "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
        )
    )
    expected_status = (
        "safe_disabled" if posture_change == "safe_disabled" else "execution_blocked"
    )
    assert result.error_category == expected_error
    assert result.record.status == expected_status
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.policy_decision.adapter_execution_enabled is False
    assert result.record.policy_decision.model_call_enabled is False
    assert result.local_model_runtime_enabled is (posture_change != "runtime_disabled")
    assert result.record.receipt is not None
    assert result.record.receipt.execution_performed is False
    assert result.record.receipt.adapter_execution_performed is False
    assert result.record.receipt.model_call_performed is False
    assert result.record.receipt.model_receipt_metadata is not None
    assert result.record.receipt.model_receipt_metadata.attempt_outcome_unknown is False
    assert result.record.receipt.model_receipt_metadata.error_category == expected_error
    if posture_change == "safe_disabled":
        assert result.record.receipt.safe_disable.reason_ref == (
            "reason-ref:runtime-local-model-marker-disable"
        )
    if posture_change in {"lease_revoked", "kill_switch"}:
        assert (
            "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_GATEWAY_VALIDATION_REQUIRED"
            not in result.record.policy_decision.reason_codes
        )
    if posture_change == "lease_revoked":
        assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in (
            result.record.policy_decision.reason_codes
        )


@pytest.mark.parametrize(
    "posture_change",
    ["runtime_disabled", "lease_revoked", "kill_switch"],
)
def test_runtime_gateway_local_model_boundary_denial_survives_restored_posture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture_change: str,
) -> None:
    transport = FakeM164GatewayTransport("SHOULD_NOT_RUN")

    def transport_factory(
        request: RuntimeLocalModelCallRequest,
    ) -> FakeM164GatewayTransport:
        if posture_change == "runtime_disabled":
            monkeypatch.setattr(gateway, "_local_model_runtime_enabled", False)
        elif posture_change == "lease_revoked":
            monkeypatch.setattr(store, "current_authority_leases", lambda: [])
        else:
            monkeypatch.setattr(
                store,
                "authority_lease_kill_switch_engaged",
                lambda: True,
            )
        return transport

    store = _runtime_store_with_provider_model_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=transport_factory,
        ),
        local_model_runtime_enabled=True,
    )
    original_record_receipt = store.record_receipt
    receipt_writes = 0

    def restore_posture_before_final_receipt(
        *args: object,
        **kwargs: object,
    ) -> object:
        nonlocal receipt_writes
        receipt_writes += 1
        if receipt_writes == 2:
            if posture_change == "runtime_disabled":
                monkeypatch.setattr(gateway, "_local_model_runtime_enabled", True)
            elif posture_change == "lease_revoked":
                monkeypatch.setattr(
                    store,
                    "current_authority_leases",
                    lambda: [provider_model_execute_authority_lease()],
                )
            else:
                monkeypatch.setattr(
                    store,
                    "authority_lease_kill_switch_engaged",
                    lambda: False,
                )
        return original_record_receipt(*args, **kwargs)

    monkeypatch.setattr(
        store,
        "record_receipt",
        restore_posture_before_final_receipt,
    )
    result = gateway.invoke_local_model(
        RuntimeLocalModelCallRequest(
            base_url="http://127.0.0.1:8080",
            model_ref="uaa-local-runtime",
            messages=[
                RuntimeLocalModelMessage(
                    role="user",
                    content=REDACTED_TEST_PROMPT,
                )
            ],
            safe_summary="Preserve exact transport-boundary denial evidence.",
        ),
        idempotency_ref="idempotency-ref:runtime-boundary-denial-restored",
    )

    assert receipt_writes == 2
    assert transport.calls == []
    assert result.record.status == "execution_blocked"
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.policy_decision.adapter_execution_enabled is False
    assert result.record.policy_decision.model_call_enabled is False
    assert result.record.receipt is not None
    assert result.record.receipt.execution_performed is False
    assert result.record.receipt.model_call_performed is False
    assert result.record.receipt.model_receipt_metadata is not None
    assert result.record.receipt.model_receipt_metadata.error_category == (
        "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
        if posture_change == "runtime_disabled"
        else "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
    )
    if posture_change in {"lease_revoked", "kill_switch"}:
        assert (
            "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_GATEWAY_VALIDATION_REQUIRED"
            not in result.record.policy_decision.reason_codes
        )
    if posture_change == "lease_revoked":
        assert "AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION" in (
            result.record.policy_decision.reason_codes
        )


def test_approved_command_boundary_rejection_retries_exact_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = _runtime_store_with_workspace_execute(tmp_path / "runtime")
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    original_refresh = (
        gateway.goal_runtime_service.refresh_runtime_projection_reservation
    )

    def reject_refresh(*_args: object, **_kwargs: object) -> None:
        raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_REFRESH_REJECTED")

    monkeypatch.setattr(
        gateway.goal_runtime_service,
        "refresh_runtime_projection_reservation",
        reject_refresh,
    )
    execute_request = _runtime_execute_request(approved)
    exact_command = _command_request_for_approved_record(
        command_request,
        approved,
    )
    idempotency_ref = "idempotency-ref:approved-command-boundary-retry"
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_PROJECTION_REFRESH_REJECTED",
    ):
        gateway.execute_approved_command(
            approved.invocation_ref,
            exact_command,
            execute_request,
            idempotency_ref=idempotency_ref,
        )
    assert calls == 0
    pending = store.get_invocation(approved.invocation_ref)
    assert pending.receipt is None
    assert pending.adapter_dispatch_protocol_ref is not None
    assert pending.adapter_dispatch_started is False

    monkeypatch.setattr(
        gateway.goal_runtime_service,
        "refresh_runtime_projection_reservation",
        original_refresh,
    )
    retried = gateway.execute_approved_command(
        approved.invocation_ref,
        exact_command,
        execute_request,
        idempotency_ref=idempotency_ref,
    )
    assert calls == 1
    assert retried.record.receipt is not None
    assert retried.record.adapter_dispatch_started is True


def test_local_model_boundary_rejection_retries_before_attempt_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeM164GatewayTransport("BOUNDARY_RETRY_OK")
    gateway = RuntimeGateway(
        store=_runtime_store_with_provider_model_execute(tmp_path / "runtime"),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda _request: transport,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Retry only the exact pre-dispatch local request.",
    )
    original_refresh = (
        gateway.goal_runtime_service.refresh_runtime_projection_reservation
    )

    def reject_refresh(*_args: object, **_kwargs: object) -> None:
        raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_REFRESH_REJECTED")

    monkeypatch.setattr(
        gateway.goal_runtime_service,
        "refresh_runtime_projection_reservation",
        reject_refresh,
    )
    idempotency_ref = "idempotency-ref:local-model-boundary-retry"
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_PROJECTION_REFRESH_REJECTED",
    ):
        gateway.invoke_local_model(
            request,
            idempotency_ref=idempotency_ref,
        )
    [pending] = gateway.store.list_invocations()
    assert pending.receipt is None
    assert pending.adapter_dispatch_protocol_ref is not None
    assert pending.adapter_dispatch_started is False
    assert transport.calls == []

    monkeypatch.setattr(
        gateway.goal_runtime_service,
        "refresh_runtime_projection_reservation",
        original_refresh,
    )
    retried = gateway.invoke_local_model(
        request,
        idempotency_ref=idempotency_ref,
    )
    assert retried.record.receipt is not None
    assert retried.record.adapter_dispatch_started is True
    assert len(transport.calls) == 1


def test_local_model_terminal_projection_refresh_failure_preserves_unknown_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeM164GatewayTransport("TERMINAL_REFRESH_REJECTED")
    gateway = RuntimeGateway(
        store=_runtime_store_with_provider_model_execute(tmp_path / "runtime"),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda _request: transport,
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(
                role="user",
                content=REDACTED_TEST_PROMPT,
            )
        ],
        safe_summary="Preserve unknown truth after terminal refresh rejection.",
    )
    original_refresh = (
        gateway.goal_runtime_service.refresh_runtime_projection_reservation
    )
    refresh_count = 0

    def reject_terminal_refresh(*args: object, **kwargs: object) -> None:
        nonlocal refresh_count
        refresh_count += 1
        if refresh_count == 2:
            raise GoalRuntimeCorruptionError("RUN_EVENT_PROJECTION_REFRESH_REJECTED")
        original_refresh(*args, **kwargs)

    monkeypatch.setattr(
        gateway.goal_runtime_service,
        "refresh_runtime_projection_reservation",
        reject_terminal_refresh,
    )
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_PROJECTION_REFRESH_REJECTED",
    ):
        gateway.invoke_local_model(
            request,
            idempotency_ref=("idempotency-ref:local-model-terminal-refresh-rejected"),
        )

    assert refresh_count == 2
    assert len(transport.calls) == 1
    [marker] = gateway.store.list_invocations()
    assert marker.receipt is not None
    assert marker.receipt.model_receipt_metadata is not None
    assert marker.receipt.model_receipt_metadata.attempt_outcome_unknown is True
    assert marker.receipt.execution_performed is False
    assert marker.receipt.model_call_performed is False


def test_adapter_dispatch_marker_grants_exactly_one_owner(tmp_path: Path) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect the bounded repository status.",
    )
    idempotency_ref = "idempotency-ref:adapter-dispatch-owner"
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref=idempotency_ref,
        command_gateway_validated=True,
        adapter_dispatch_protocol_ref=(runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF),
    )
    marker_idempotency_ref = "idempotency-ref:adapter-dispatch-owner:marker"
    barrier = threading.Barrier(2)
    claims: list[runtime_storage.RuntimeAdapterDispatchClaim] = []
    adapter_calls: list[str] = []

    def compete_for_dispatch() -> None:
        barrier.wait(timeout=5)
        claim = store.mark_adapter_dispatch_started(
            created.record.invocation_ref,
            protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
            idempotency_ref=marker_idempotency_ref,
        )
        claims.append(claim)
        if claim.acquired:
            adapter_calls.append(claim.record.invocation_ref)

    threads = [threading.Thread(target=compete_for_dispatch) for _index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert all(not thread.is_alive() for thread in threads)
    assert sorted(claim.acquired for claim in claims) == [False, True]
    assert adapter_calls == [created.record.invocation_ref]
    assert all(claim.record.adapter_dispatch_started is True for claim in claims)


def test_started_readonly_command_retry_preserves_unknown_attempt_without_receipt(
    tmp_path: Path,
) -> None:
    calls = 0

    def fail_after_start(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        raise RuntimeError("bounded runner failed after process start")

    store = _runtime_store_with_workspace_execute(tmp_path)
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Preserve unknown truth after a started read-only command.",
    )
    adapter = GovernedCommandRuntimeAdapter(
        workspace_root=ROOT,
        runner=fail_after_start,
    )
    idempotency_ref = "idempotency-ref:started-readonly-command-retry"
    with pytest.raises(
        RuntimeError,
        match="bounded runner failed after process start",
    ):
        runtime_command.invoke_governed_command(
            store=store,
            adapter=adapter,
            request=request,
            idempotency_ref=idempotency_ref,
        )

    retried = runtime_command.invoke_governed_command(
        store=store,
        adapter=adapter,
        request=request,
        idempotency_ref=idempotency_ref,
    )

    assert calls == 1
    assert retried.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
    assert retried.replayed is True
    assert retried.record.adapter_dispatch_started is True
    assert retried.record.receipt is None


def test_command_dispatch_derives_and_revalidates_durable_approval_envelope(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    prepared = store.prepare_adapter_dispatch_protocol(
        approved.invocation_ref,
        protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
        idempotency_ref="idempotency-ref:dispatch-envelope-derived:prepare",
    )

    claim = store.mark_adapter_dispatch_started(
        prepared.invocation_ref,
        protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
        idempotency_ref="idempotency-ref:dispatch-envelope-derived",
        command_gateway_validated=True,
    )

    assert claim.acquired is True
    assert claim.record.adapter_dispatch_started is True


def test_command_dispatch_rejects_missing_required_durable_approval_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=_approved_runtime_command_request(),
    )
    prepared = store.prepare_adapter_dispatch_protocol(
        approved.invocation_ref,
        protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
        idempotency_ref="idempotency-ref:dispatch-envelope-missing:prepare",
    )
    original_get_invocation = store.get_invocation

    def without_envelope(invocation_ref: str) -> RuntimeInvocationRecord:
        record = original_get_invocation(invocation_ref)
        return record.model_copy(update={"action_inbox_envelope": None})

    monkeypatch.setattr(store, "get_invocation", without_envelope)

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_COMMAND_DISPATCH_APPROVAL_REVOKED",
    ):
        store.mark_adapter_dispatch_started(
            prepared.invocation_ref,
            protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
            idempotency_ref="idempotency-ref:dispatch-envelope-missing:marker",
            command_gateway_validated=True,
        )
    monkeypatch.setattr(store, "get_invocation", original_get_invocation)
    assert (
        store.get_invocation(prepared.invocation_ref).adapter_dispatch_started is False
    )


@pytest.mark.parametrize("posture", ["safe-disable", "lease-revoked"])
def test_command_dispatch_revalidates_current_authority_under_store_lock(
    tmp_path: Path,
    posture: str,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect status only while current authority remains active.",
    )
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref="idempotency-ref:dispatch-current-authority",
        command_gateway_validated=True,
        adapter_dispatch_protocol_ref=(runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF),
    )
    if posture == "safe-disable":
        store.safe_disable(
            RuntimeSafeDisableRequest(
                reason_ref="reason-ref:dispatch-current-authority-revoked"
            ),
            idempotency_ref="idempotency-ref:dispatch-current-authority:disable",
        )
    else:
        store._explicit_active_authority_leases = []  # noqa: SLF001

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_COMMAND_DISPATCH_AUTHORITY_REVOKED",
    ):
        store.mark_adapter_dispatch_started(
            created.record.invocation_ref,
            protocol_ref=runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF,
            idempotency_ref=("idempotency-ref:dispatch-current-authority:marker"),
            command_gateway_validated=True,
        )
    assert (
        store.get_invocation(created.record.invocation_ref).adapter_dispatch_started
        is False
    )


def test_approved_command_dispatch_revalidates_current_action_inbox_envelope(
    tmp_path: Path,
) -> None:
    calls: list[object] = []
    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    exact_request = _command_request_for_approved_record(
        command_request,
        approved,
    )
    execute_request = _runtime_execute_request(approved)

    def deny_at_dispatch(current: RuntimeInvocationRecord) -> None:
        refs = _runtime_action_inbox_refs(current, decision="deny")
        store.bind_approval(
            current.invocation_ref,
            RuntimeApprovalBindingRequest(
                decision="deny",
                action_envelope_ref=refs["action_envelope_ref"],
                exact_scope_ref=refs["exact_scope_ref"],
                expected_payload_fingerprint_ref=current.payload_fingerprint_ref,
                expected_policy_decision_ref=(
                    current.policy_decision.policy_decision_ref
                ),
                adapter_id="governed-command-runtime-adapter",
                command_intent="focused_pytest",
                risk_class="medium",
                safe_summary="Deny the exact command before adapter dispatch.",
            ),
            idempotency_ref="idempotency-ref:dispatch-envelope-denied",
        )

    with pytest.raises(
        RuntimeInvocationStorageError,
        match="RUNTIME_COMMAND_DISPATCH_APPROVAL_REVOKED",
    ):
        runtime_command.invoke_approved_governed_command(
            store=store,
            adapter=GovernedCommandRuntimeAdapter(
                workspace_root=ROOT,
                runner=lambda **kwargs: calls.append(kwargs),
            ),
            record=approved,
            request=exact_request,
            execute_request=execute_request,
            idempotency_ref="idempotency-ref:dispatch-envelope-execute",
            pre_adapter_dispatch=deny_at_dispatch,
        )

    durable = store.get_invocation(approved.invocation_ref)
    assert durable.status == RuntimeInvocationStatus.approval_denied.value
    assert durable.adapter_dispatch_started is False
    assert durable.receipt is None
    assert calls == []


def test_overlapping_approved_command_retry_reports_in_progress_without_receipt(
    tmp_path: Path,
) -> None:
    runner_started = threading.Event()
    release_runner = threading.Event()
    calls = 0
    owner_results: list[RuntimeCommandGatewayResult] = []
    owner_errors: list[BaseException] = []

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        runner_started.set()
        assert release_runner.wait(timeout=5)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_APPROVED_OUTPUT",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    exact_request = _command_request_for_approved_record(
        command_request,
        approved,
    )
    execute_request = _runtime_execute_request(approved)
    adapter = GovernedCommandRuntimeAdapter(workspace_root=ROOT, runner=runner)
    execution_idempotency_ref = "idempotency-ref:approved-command-overlap"

    def run_owner() -> None:
        try:
            owner_results.append(
                runtime_command.invoke_approved_governed_command(
                    store=store,
                    adapter=adapter,
                    record=approved,
                    request=exact_request,
                    execute_request=execute_request,
                    idempotency_ref=execution_idempotency_ref,
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            owner_errors.append(exc)

    owner = threading.Thread(target=run_owner)
    owner.start()
    assert runner_started.wait(timeout=5)
    duplicate = runtime_command.invoke_approved_governed_command(
        store=store,
        adapter=adapter,
        record=approved,
        request=exact_request,
        execute_request=execute_request,
        idempotency_ref=execution_idempotency_ref,
    )
    try:
        assert duplicate.replayed is True
        assert duplicate.record.receipt is None
        assert (
            duplicate.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_IN_PROGRESS"
        )
        assert store.get_invocation(approved.invocation_ref).receipt is None
        assert calls == 1
    finally:
        release_runner.set()
        owner.join(timeout=10)

    assert owner.is_alive() is False
    assert owner_errors == []
    assert len(owner_results) == 1
    assert owner_results[0].record.receipt is not None
    assert owner_results[0].record.receipt.command_execution_performed is True
    assert calls == 1


def test_overlapping_action_inbox_retry_links_only_the_terminal_receipt(
    tmp_path: Path,
) -> None:
    runner_started = threading.Event()
    release_runner = threading.Event()
    calls = 0
    owner_results: list[RuntimeCommandGatewayResult] = []
    owner_errors: list[BaseException] = []

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        runner_started.set()
        assert release_runner.wait(timeout=5)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_APPROVED_OUTPUT",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    exact_request = _command_request_for_approved_record(
        command_request,
        approved,
    )
    execute_request = _runtime_execute_request(approved)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    execution_idempotency_ref = "idempotency-ref:action-inbox-command-overlap"

    def run_owner() -> None:
        try:
            owner_results.append(
                gateway.execute_approved_command(
                    approved.invocation_ref,
                    exact_request,
                    execute_request,
                    idempotency_ref=execution_idempotency_ref,
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            owner_errors.append(exc)

    owner = threading.Thread(target=run_owner)
    owner.start()
    assert runner_started.wait(timeout=5)
    duplicate = gateway.execute_approved_command(
        approved.invocation_ref,
        exact_request,
        execute_request,
        idempotency_ref=execution_idempotency_ref,
    )
    try:
        assert duplicate.replayed is True
        assert duplicate.record.receipt is None
        assert duplicate.record.action_inbox_envelope is not None
        assert duplicate.record.action_inbox_envelope.receipt_refs == []
        assert calls == 1
    finally:
        release_runner.set()
        owner.join(timeout=10)

    assert owner.is_alive() is False
    assert owner_errors == []
    assert len(owner_results) == 1
    terminal = owner_results[0].record
    assert terminal.receipt is not None
    assert terminal.action_inbox_envelope is not None
    assert terminal.action_inbox_envelope.receipt_refs == [terminal.receipt.receipt_ref]
    assert calls == 1


def test_legacy_protocol_accepts_only_immutable_receipt_replay(
    tmp_path: Path,
) -> None:
    calls = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = _runtime_store_with_workspace_execute(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    command_request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect one legacy committed runtime receipt.",
    )
    idempotency_ref = "idempotency-ref:legacy-committed-protocol"
    completed = gateway.invoke_command(
        command_request,
        idempotency_ref=idempotency_ref,
    ).record
    assert completed.receipt is not None
    invocation_request = runtime_command_invocation_request(command_request)

    with store._exclusive_mutation():  # noqa: SLF001
        store._records[completed.invocation_ref] = completed.model_copy(  # noqa: SLF001
            update={"adapter_dispatch_protocol_ref": None}
        )
        replay = store._create_invocation_loaded(  # noqa: SLF001
            invocation_request,
            idempotency_ref=idempotency_ref,
            command_gateway_validated=True,
            action_inbox_envelope_required=False,
            adapter_dispatch_protocol_ref=(
                runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF
            ),
        )
    assert replay.replayed is True
    assert replay.record.receipt == completed.receipt
    assert calls == 1

    receiptless_store = _runtime_store_with_workspace_execute(tmp_path / "receiptless")
    pending = receiptless_store.create_invocation(
        invocation_request,
        idempotency_ref="idempotency-ref:legacy-receiptless-protocol",
        command_gateway_validated=True,
        adapter_dispatch_protocol_ref=(runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF),
    ).record
    with receiptless_store._exclusive_mutation():  # noqa: SLF001
        receiptless_store._records[pending.invocation_ref] = (  # noqa: SLF001
            pending.model_copy(update={"adapter_dispatch_protocol_ref": None})
        )
        with pytest.raises(
            RuntimeInvocationStorageError,
            match="RUNTIME_ADAPTER_DISPATCH_PROTOCOL_MISMATCH",
        ):
            receiptless_store._create_invocation_loaded(  # noqa: SLF001
                invocation_request,
                idempotency_ref=("idempotency-ref:legacy-receiptless-protocol"),
                command_gateway_validated=True,
                adapter_dispatch_protocol_ref=(
                    runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF
                ),
            )


def test_legacy_readonly_pre_dispatch_retry_migrates_requirement_and_executes_once(
    tmp_path: Path,
) -> None:
    calls = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    command_request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Resume one exact legacy read-only command.",
    )
    invocation_request = runtime_command_invocation_request(command_request)
    idempotency_ref = "idempotency-ref:legacy-readonly-pre-dispatch"
    legacy_store = _runtime_store_with_workspace_execute(tmp_path)
    legacy = legacy_store.create_invocation(
        invocation_request,
        idempotency_ref=idempotency_ref,
        command_gateway_validated=True,
        adapter_dispatch_protocol_ref=(runtime_command.ADAPTER_DISPATCH_PROTOCOL_REF),
    ).record
    assert legacy.approval_requirement.action_inbox_envelope_required is True
    assert legacy.adapter_dispatch_started is False
    assert legacy.receipt is None

    restarted_store = _runtime_store_with_workspace_execute(tmp_path)
    gateway = RuntimeGateway(
        store=restarted_store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    completed = gateway.invoke_command(
        command_request,
        idempotency_ref=idempotency_ref,
    ).record

    assert calls == 1
    assert completed.receipt is not None
    assert completed.approval_requirement.action_inbox_envelope_required is False
    durable = _runtime_store_with_workspace_execute(tmp_path).get_invocation(
        legacy.invocation_ref
    )
    assert durable.receipt == completed.receipt
    assert durable.approval_requirement.action_inbox_envelope_required is False

    replayed = gateway.invoke_command(
        command_request,
        idempotency_ref=idempotency_ref,
    )
    assert replayed.replayed is True
    assert replayed.record.receipt == completed.receipt
    assert calls == 1
