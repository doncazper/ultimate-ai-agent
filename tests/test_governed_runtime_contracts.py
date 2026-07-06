import hashlib
import json
import threading
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    LocalModelRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeGateway,
    RuntimeInvocationConflictError,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeInvocationStore,
    RuntimeLocalModelCallRequest,
    RuntimeLocalModelMessage,
    build_default_runtime_capabilities,
    promoted_approval_bridge_command_intents,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeApprovalBindingRequest,
    RuntimeExecuteRequest,
    RuntimeSafeDisableRequest,
    build_policy_decision,
    runtime_invocation_ref,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStorageError
from ultimate_ai_agent.core.local_model_management import FakeM164GatewayTransport
from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]


def _runtime_request(summary: str = "safe governed runtime summary") -> RuntimeInvocationRequest:
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
    assert "authority-ref:runtime-local-model-loopback-phase-03" in payload[
        "implemented_authority_refs"
    ]
    assert "authority-ref:runtime-allowlisted-readonly-command-phase-04" in payload[
        "implemented_authority_refs"
    ]
    assert "blocked-authority:runtime-unrestricted-command-execution" in payload[
        "blocked_authority_refs"
    ]
    assert "blocked-authority:runtime-command-execution-without-gateway-allowlist" in (
        payload["blocked_authority_refs"]
    )


def test_generic_runtime_policy_does_not_enable_local_model_without_gateway_validation() -> None:
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


def test_generic_runtime_policy_does_not_enable_command_without_gateway_validation() -> None:
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
    invocation_ref = runtime_invocation_ref("idempotency-ref:runtime-contract", payload_ref)
    decision = build_policy_decision(request, invocation_ref=invocation_ref)

    with pytest.raises(ValidationError):
        RuntimeInvocationReceipt(
            receipt_ref="runtime-receipt-ref:test",
            invocation_ref=invocation_ref,
            policy_decision_ref=decision.policy_decision_ref,
            invocation_status=RuntimeInvocationStatus.execution_blocked,
            execution_performed=True,
        )


def test_runtime_store_persists_safe_refs_only_and_replays_idempotency(tmp_path: Path) -> None:
    store = RuntimeInvocationStore(tmp_path)
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
        store.create_invocation(changed, idempotency_ref="idempotency-ref:runtime-store")

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(encoding="utf-8")
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


def test_runtime_store_records_blocked_execute_and_detects_tampering(tmp_path: Path) -> None:
    store = RuntimeInvocationStore(tmp_path)
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
    path.write_text(text.replace("execution_blocked", "receipt_recorded", 1), encoding="utf-8")

    with pytest.raises(RuntimeInvocationStorageError):
        RuntimeInvocationStore(tmp_path).list_invocations()


def test_runtime_store_replays_mutating_operation_idempotency(tmp_path: Path) -> None:
    store = RuntimeInvocationStore(tmp_path)
    created = store.create_invocation(
        _runtime_request(),
        idempotency_ref="idempotency-ref:runtime-mutation-create",
    )
    invocation_ref = created.record.invocation_ref

    approval = RuntimeApprovalBindingRequest(approval_ref="approval-ref:runtime-mutation")
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


def test_runtime_gateway_local_model_call_records_metadata_only_receipt(tmp_path: Path) -> None:
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda request: FakeM164GatewayTransport("UAA_LOCAL_RUNTIME_OK")
        ),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(role="user", content="local prompt should not persist")
        ],
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

    assert result.record.status == "receipt_recorded"
    assert result.record.receipt is not None
    assert result.record.receipt.model_call_performed is True
    assert result.record.receipt.model_output_non_authoritative is True
    assert result.response_preview == "UAA_LOCAL_RUNTIME_OK"
    assert replay.replayed is True

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "local prompt should not persist" not in persisted
    assert "UAA_LOCAL_RUNTIME_OK" not in persisted
    assert "raw_prompt" not in persisted
    assert "provider_payload" not in persisted


def test_runtime_gateway_local_model_call_is_disabled_by_default(tmp_path: Path) -> None:
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda request: FakeM164GatewayTransport("SHOULD_NOT_RUN")
        ),
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[
            RuntimeLocalModelMessage(role="user", content="disabled prompt should not persist")
        ],
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
    assert "disabled prompt should not persist" not in persisted
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
        messages=[RuntimeLocalModelMessage(role="user", content="safe transient prompt")],
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
    assert "safe transient prompt" not in persisted


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

    def transport_factory(request: RuntimeLocalModelCallRequest) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SHOULD_NOT_RUN")

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        local_model_adapter=LocalModelRuntimeAdapter(transport_factory=transport_factory),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url=base_url,
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content="safe transient prompt")],
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
        result.record.receipt.command_receipt_metadata.command_output_persisted
        is False
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


def test_governed_command_runtime_rejects_unapproved_workspace_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="RUNTIME_COMMAND_WORKSPACE_ROOT_NOT_ALLOWLISTED"):
        GovernedCommandRuntimeAdapter(workspace_root=tmp_path)


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

    store = RuntimeInvocationStore(tmp_path)
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
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-command-replay-disable"),
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
    event_kinds = {event["event_kind"] for event in read_model["evidence_timeline"]}
    assert "receipt_recorded" in event_kinds
    assert "execution_started" not in event_kinds
    assert "execution_completed" not in event_kinds
    assert "execution_failed" not in event_kinds
    assert "execution_timed_out" not in event_kinds


def _approved_runtime_command_request() -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:governed-runtime-contracts"],
        approval_ref=None,
        safe_summary="Run the exact focused governed runtime contract test lane.",
    )


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def _runtime_action_inbox_refs(
    record,
    *,
    decision: str = "approve",
) -> dict[str, str]:
    command_intent = record.request.action_ref.removeprefix(
        "action-ref:runtime-command-"
    )
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
        "command_intent": command_intent,
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
    created = store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref=(
            f"idempotency-ref:runtime-action-inbox-create-{command_request.intent}"
        ),
    )
    refs = _runtime_action_inbox_refs(created.record, decision=decision)
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
            command_intent=refs["command_intent"],
            risk_class="medium",
            expires_at=utc_now() + expires_delta,
            safe_summary=(
                f"Action Inbox approved exact {refs['command_intent']} runtime lane."
            ),
        ),
        idempotency_ref=(
            f"idempotency-ref:runtime-action-inbox-{refs['command_intent']}-{decision}"
        ),
    )


def test_runtime_gateway_action_inbox_approval_executes_exact_command_once(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=3,
            output_bytes=b"safe pytest output",
        )

    store = RuntimeInvocationStore(tmp_path)
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
    assert approved.action_inbox_envelope.approval_ref in (
        approved_read_model["pending_runtime_approval_refs"]
    )
    assert approved.action_inbox_envelope.action_envelope_ref not in (
        approved_read_model["pending_runtime_approval_refs"]
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
            ["Governed runtime status", "focused_pytest_receipt_recorded"],
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
            ["Governed runtime invocation", result.record.policy_decision.policy_decision_ref],
        ),
        (
            ["receipts", "show", result.record.receipt.receipt_ref],
            ["Governed runtime receipt", "Output summary: Command output redacted"],
        ),
    ]:
        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/dev/uaa_runtime.py"),
                "--state-dir",
                str(tmp_path),
                *command,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        for expected in expected_strings:
            assert expected in cli_result.stdout
        assert "safe pytest output" not in cli_result.stdout
        assert str(tmp_path) not in cli_result.stdout

    launcher_status = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_launcher.py"),
            "runtime",
            "--state-dir",
            str(tmp_path),
            "status",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Governed runtime status" in launcher_status.stdout
    assert "focused_pytest_receipt_recorded" in launcher_status.stdout
    assert "safe pytest output" not in launcher_status.stdout
    assert str(tmp_path) not in launcher_status.stdout

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

    safe_disable = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "--state-dir",
            str(tmp_path),
            "safe-disable",
            "--idempotency-ref",
            "idempotency-ref:runtime-cli-safe-disable-test",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Governed runtime safe-disable" in safe_disable.stdout
    assert "Safe-disable ref:" in safe_disable.stdout
    assert "safe pytest output" not in safe_disable.stdout
    assert str(tmp_path) not in safe_disable.stdout
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
    assert disabled_event_refs["invocation_requested"] == stable_event_refs[
        "invocation_requested"
    ]
    assert disabled_event_refs["approval_accepted"] == stable_event_refs[
        "approval_accepted"
    ]

    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert "safe pytest output" not in persisted
    assert "stdout" not in persisted
    assert "stderr" not in persisted


def test_runtime_gateway_promotes_repo_verifier_and_frontend_check_exact_lanes(
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=4,
            output_bytes=b"safe verifier output",
        )

    assert sorted(
        intent.value for intent in promoted_approval_bridge_command_intents()
    ) == ["focused_pytest", "frontend_check", "repo_verifier"]

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    receipt_refs: list[str] = []
    for intent in ["repo_verifier", "frontend_check"]:
        command_request = RuntimeCommandExecutionRequest(
            intent=intent,
            requested_profile="operator-approved",
            target_refs=[f"test-ref:governed-runtime-{intent.replace('_', '-')}"],
            approval_ref=None,
            safe_summary=f"Run the exact {intent} governed runtime command lane.",
        )
        approved = _bind_runtime_action_inbox_approval(
            store,
            command_request=command_request,
        )
        execute_command_request = _command_request_for_approved_record(
            command_request,
            approved,
        )
        result = gateway.execute_approved_command(
            approved.invocation_ref,
            execute_command_request,
            _runtime_execute_request(approved),
            idempotency_ref=f"idempotency-ref:runtime-action-inbox-execute-{intent}",
        )
        assert result.record.status == "receipt_recorded"
        assert result.record.receipt is not None
        receipt_refs.append(result.record.receipt.receipt_ref)

    assert len(calls) == 2
    assert calls[0]["argv"] == (
        str(ROOT / ".venv/bin/python"),
        "scripts/verify_documentation_integrity.py",
    )
    frontend_argv = calls[1]["argv"]
    assert isinstance(frontend_argv, tuple)
    assert Path(frontend_argv[0]).name == "make"
    assert frontend_argv[1:] == ("frontend-check",)

    read_model = build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    assert read_model["command_runtime_readiness"] == (
        "multiple_exact_runtime_commands_receipt_recorded"
    )
    assert set(receipt_refs).issubset(set(read_model["receipt_refs"]))
    assert {item["command_intent"] for item in read_model["items"]} == {
        "repo_verifier",
        "frontend_check",
    }
    assert "safe verifier output" not in json.dumps(read_model, sort_keys=True)


def test_runtime_launcher_actions_approve_and_deny_by_safe_selector_ref(
    tmp_path: Path,
) -> None:
    store = RuntimeInvocationStore(tmp_path)
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
    assert replay.record.status == "execution_blocked"
    assert replay.error_category == "RUNTIME_COMMAND_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT"
    assert replay.record.receipt is not None
    assert replay.record.receipt.command_execution_performed is False


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
        release_runner.wait(timeout=5)
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
    assert runner_started.wait(timeout=5)
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
                RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-command-race-disable"),
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
    gateways = [
        RuntimeGateway(
            store=RuntimeInvocationStore(tmp_path),
            command_adapter=GovernedCommandRuntimeAdapter(
                workspace_root=ROOT,
                runner=runner,
            ),
        ),
        RuntimeGateway(
            store=RuntimeInvocationStore(tmp_path),
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
    release_runner.set()
    first.join(timeout=5)
    second.join(timeout=5)

    assert errors == []
    assert len(results) == 2
    assert calls == 1
    assert sum(1 for result in results if result.replayed) == 1
    assert any(
        result.record.receipt is not None
        and result.record.receipt.command_execution_performed
        for result in results
    )


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


def test_runtime_gateway_local_model_replay_without_receipt_does_not_call_transport(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(request: RuntimeLocalModelCallRequest) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("FIRST_MODEL_ATTEMPT")

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(transport_factory=transport_factory),
        local_model_runtime_enabled=True,
    )
    original_record_receipt = store.record_receipt

    def fail_after_create(*args: object, **kwargs: object) -> object:
        raise RuntimeError("simulated local model receipt write failure")

    store.record_receipt = fail_after_create  # type: ignore[method-assign]
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content="safe transient prompt")],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    with pytest.raises(RuntimeError):
        gateway.invoke_local_model(
            request,
            idempotency_ref="idempotency-ref:runtime-local-model-replay-no-receipt",
        )
    assert calls == 1

    store.record_receipt = original_record_receipt  # type: ignore[method-assign]
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-replay-no-receipt",
    )

    assert calls == 1
    assert replay.replayed is True
    assert replay.record.status == "execution_blocked"
    assert replay.error_category == "RUNTIME_LOCAL_MODEL_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT"
    assert replay.record.receipt is not None
    assert replay.record.receipt.model_call_performed is False


def test_runtime_gateway_local_model_replay_after_safe_disable_keeps_idempotency_shape(
    tmp_path: Path,
) -> None:
    calls = 0

    def transport_factory(request: RuntimeLocalModelCallRequest) -> FakeM164GatewayTransport:
        nonlocal calls
        calls += 1
        return FakeM164GatewayTransport("SAFE_MODEL_RESPONSE")

    store = RuntimeInvocationStore(tmp_path)
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(transport_factory=transport_factory),
        local_model_runtime_enabled=True,
    )
    request = RuntimeLocalModelCallRequest(
        base_url="http://127.0.0.1:8080",
        model_ref="uaa-local-runtime",
        messages=[RuntimeLocalModelMessage(role="user", content="safe transient prompt")],
        safe_summary="Run local model runtime as an untrusted proposal.",
    )
    first = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-safe-disable-replay",
    )
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-local-model-replay-disable"),
        idempotency_ref="idempotency-ref:runtime-local-model-replay-disable",
    )
    replay = gateway.invoke_local_model(
        request,
        idempotency_ref="idempotency-ref:runtime-local-model-safe-disable-replay",
    )

    assert first.record.receipt is not None
    assert calls == 1
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

    def transport_factory(request: RuntimeLocalModelCallRequest) -> FakeM164GatewayTransport:
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
                RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-local-model-race-disable"),
                idempotency_ref="idempotency-ref:runtime-local-model-race-disable",
            )
            return False
        return original_safe_disable_active()

    store.operator_safe_disable_active = racing_safe_disable_check  # type: ignore[method-assign]
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(transport_factory=transport_factory),
        local_model_runtime_enabled=True,
    )

    result = gateway.invoke_local_model(
        RuntimeLocalModelCallRequest(
            base_url="http://127.0.0.1:8080",
            model_ref="uaa-local-runtime",
            messages=[RuntimeLocalModelMessage(role="user", content="safe transient prompt")],
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
