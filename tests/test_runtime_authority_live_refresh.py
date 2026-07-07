from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_STATE_DIR_ENV,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    RuntimeApprovalBindingRequest,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeInvocationStore,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.time import utc_now
from tests.authority_helpers import issue_workspace_execute_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def _hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def _command_request() -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:runtime-authority-live-refresh"],
        safe_summary="Run the exact focused runtime authority refresh lane.",
    )


def _action_inbox_refs(record) -> dict[str, str]:
    command_intent = str(record.request.action_ref).removeprefix(
        "action-ref:runtime-command-"
    )
    exact_scope_ref = _hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
            "requested_authority": record.request.requested_authority,
        },
    )
    approval_ref = _hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": record.invocation_ref,
            "requested_authority": record.request.requested_authority,
            "requested_profile": record.request.requested_profile,
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": command_intent,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
    )
    action_envelope_ref = _hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return {
        "approval_ref": approval_ref,
        "action_envelope_ref": action_envelope_ref,
        "exact_scope_ref": exact_scope_ref,
    }


def _approve_command(
    store: RuntimeInvocationStore,
    request: RuntimeCommandExecutionRequest,
):
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref="idempotency-ref:runtime-authority-refresh-create",
    )
    refs = _action_inbox_refs(created.record)
    return store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision="approve",
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Action Inbox approved exact runtime authority refresh lane.",
        ),
        idempotency_ref="idempotency-ref:runtime-authority-refresh-approve",
    )


def _execute_request(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    return RuntimeExecuteRequest(
        approval_ref=record.action_inbox_envelope.approval_ref,
        action_envelope_ref=record.action_inbox_envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        safe_summary="Execute approved runtime command after live authority refresh.",
    )


def _gateway_that_must_not_execute(store: RuntimeInvocationStore) -> RuntimeGateway:
    def runner(**_: object) -> RuntimeCommandRunResult:
        raise AssertionError("runtime command runner must not execute")

    return RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(workspace_root=ROOT, runner=runner),
    )


def test_runtime_execution_rechecks_revoked_authority_lease_before_runner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    issue_workspace_execute_authority_lease(authority_dir)
    store = RuntimeInvocationStore(tmp_path / "runtime")
    request = _command_request()
    approved = _approve_command(store, request)
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.authority_scope_allowed is True

    active_lease = AuthorityLeaseStore(authority_dir).list_leases(active_only=True)[0]
    _lease, receipt = AuthorityLeaseStore(authority_dir).revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=active_lease.lease_ref,
            decision_reason_ref="reason-ref:runtime-authority-refresh-revoked",
            safe_summary="Revoke test workspace execute authority before execution.",
        ),
        idempotency_ref="idempotency-ref:runtime-authority-refresh-revoke",
    )
    assert receipt.status == "revoked"

    result = _gateway_that_must_not_execute(store).execute_approved_command(
        approved.invocation_ref,
        request.model_copy(
            update={"approval_ref": approved.action_inbox_envelope.approval_ref}
        ),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-authority-refresh-execute-revoked",
    )

    assert result.error_category == "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    assert result.record.receipt is not None
    assert result.record.receipt.execution_performed is False
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.policy_decision.command_execution_enabled is False
    assert result.record.policy_decision.authority_lease_ref is None
    assert result.record.policy_decision.authority_decision_outcome == "degrade_to_draft"
    assert "reason-ref:authority:no-active-lease-for-domain-capability" in (
        result.record.policy_decision.authority_reason_refs
    )


def test_runtime_execution_rechecks_authority_kill_switch_before_runner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    issue_workspace_execute_authority_lease(authority_dir)
    store = RuntimeInvocationStore(tmp_path / "runtime")
    request = _command_request()
    approved = _approve_command(store, request)
    assert approved.action_inbox_envelope is not None
    assert approved.action_inbox_envelope.authority_scope_allowed is True

    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "1")
    result = _gateway_that_must_not_execute(store).execute_approved_command(
        approved.invocation_ref,
        request.model_copy(
            update={"approval_ref": approved.action_inbox_envelope.approval_ref}
        ),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-authority-refresh-execute-kill-switch",
    )

    assert result.error_category == "RUNTIME_COMMAND_POLICY_EXECUTION_BLOCKED"
    assert result.record.receipt is not None
    assert result.record.receipt.execution_performed is False
    assert result.record.policy_decision.allowed_to_execute is False
    assert result.record.policy_decision.command_execution_enabled is False
    assert result.record.policy_decision.authority_lease_ref is None
    assert result.record.policy_decision.authority_decision_outcome == "deny"
    assert "reason-ref:authority:kill-switch-engaged" in (
        result.record.policy_decision.authority_reason_refs
    )
