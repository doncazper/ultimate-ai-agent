from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeInvocationConflictError,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeInvocationStore,
    build_default_runtime_capabilities,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeApprovalBindingRequest,
    RuntimeSafeDisableRequest,
    build_policy_decision,
    runtime_invocation_ref,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStorageError


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
    assert "blocked-authority:runtime-adapter-execution-phase-02" in payload[
        "blocked_authority_refs"
    ]


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
