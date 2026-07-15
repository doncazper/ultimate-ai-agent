from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLeaseScope,
    AuthorityLeaseConflictError,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import AuthorityDispatchStatus
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.communications.matrix_harness import (
    MATRIX_HARNESS_LANES,
    MatrixHarnessAuthorityDispatchAdapter,
    MatrixHarnessBackendResult,
    MatrixHarnessCommand,
    MatrixHarnessOperation,
    MatrixHarnessOperationOutcome,
    MatrixHarnessRuntimeStatus,
    attach_exact_matrix_harness_approval,
    build_exact_matrix_harness_lease,
    build_matrix_harness_approval_request,
    build_matrix_harness_dispatch_request,
    capture_exact_matrix_harness_approval,
    execute_matrix_harness_command,
    issue_exact_matrix_harness_lease,
    matrix_harness_exact_resource_refs,
    matrix_harness_request_fingerprint_ref,
    stable_matrix_harness_ref,
)
from ultimate_ai_agent.core.time import utc_now


class _FakeHandle:
    def __init__(self, operation: MatrixHarnessOperation, execution_ref: str) -> None:
        self.operation = operation
        self.execution_ref = execution_ref
        self.commit_validated_at = utc_now()

    def collect(self) -> MatrixHarnessBackendResult:
        return MatrixHarnessBackendResult(
            execution_ref=self.execution_ref,
            operation=self.operation,
            outcome=MatrixHarnessOperationOutcome.succeeded,
            runtime_status=MatrixHarnessRuntimeStatus.healthy,
            evidence_refs=[
                f"evidence-ref:matrix-harness:test:{self.operation.value}"
            ],
            fixture_account_count=(
                2 if self.operation == MatrixHarnessOperation.fixture_seed else 0
            ),
            fixture_room_count=(
                3 if self.operation == MatrixHarnessOperation.fixture_seed else 0
            ),
            fixture_event_count=(
                5 if self.operation == MatrixHarnessOperation.fixture_seed else 0
            ),
            safe_summary="Synthetic Matrix harness test backend completed safely.",
        )


class _FakeBackend:
    binding_ref = "backend-binding-ref:matrix-harness:test"

    def __init__(self, *, readiness: list[str] | None = None) -> None:
        self.readiness = readiness or []
        self.starts: list[MatrixHarnessOperation] = []
        self.claimed: set[str] = set()

    def readiness_reason_refs(self, operation: MatrixHarnessOperation) -> list[str]:
        return list(self.readiness)

    def claim_request_state(self, dispatch_ref: str) -> None:
        if dispatch_ref in self.claimed:
            raise RuntimeError("duplicate claim")
        self.claimed.add(dispatch_ref)

    def release_request_state(self, dispatch_ref: str) -> None:
        self.claimed.discard(dispatch_ref)

    def request_state_active(self, dispatch_ref: str) -> bool:
        return dispatch_ref in self.claimed

    def start_operation(
        self,
        *,
        operation: MatrixHarnessOperation,
        execution_ref: str,
        lifecycle_generation_ref: str,
        expected_state_ref: str,
        validate_commit_fence: Any,
    ) -> _FakeHandle:
        assert lifecycle_generation_ref
        assert expected_state_ref
        reasons, validated_at = validate_commit_fence()
        assert reasons == []
        self.starts.append(operation)
        handle = _FakeHandle(operation, execution_ref)
        handle.commit_validated_at = validated_at
        return handle


def _command(
    operation: MatrixHarnessOperation,
    *,
    suffix: str = "test",
    start_delta: timedelta = timedelta(minutes=5),
    lease_ref: str | None = None,
) -> MatrixHarnessCommand:
    deadline = utc_now() + start_delta
    values = {
        "operation": operation,
        "request_ref": f"request-ref:matrix-harness:{suffix}",
        "task_ref": f"task-ref:matrix-harness:{suffix}",
        "mission_ref": f"mission-ref:matrix-harness:{suffix}",
        "run_ref": f"run-ref:matrix-harness:{suffix}",
        "dispatch_ref": f"dispatch-ref:matrix-harness:{suffix}",
        "idempotency_ref": f"idempotency-ref:matrix-harness:{suffix}",
        "lease_ref": lease_ref or f"authority-lease-ref:matrix-harness:{suffix}",
        "lifecycle_generation_ref": f"generation-ref:matrix-harness:{suffix}",
        "expected_state_ref": f"state-ref:matrix-harness:{suffix}",
        "start_deadline": deadline,
    }
    values["request_fingerprint_ref"] = matrix_harness_request_fingerprint_ref(
        **values
    )
    return MatrixHarnessCommand(**values)


def _store_with_lease(
    tmp_path: Path,
    command: MatrixHarnessCommand,
    *,
    lease_update: dict[str, Any] | None = None,
) -> AuthorityLeaseStore:
    store = AuthorityLeaseStore(tmp_path / "authority")
    lease = build_exact_matrix_harness_lease(
        command,
        issued_at=utc_now() - timedelta(minutes=1),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    if lease_update:
        lease = lease.model_copy(update=lease_update)
    store._write_leases([lease])
    return store


@pytest.mark.parametrize("operation", list(MatrixHarnessOperation))
def test_six_exact_lanes_have_closed_dispatcher_bindings(
    tmp_path: Path,
    operation: MatrixHarnessOperation,
) -> None:
    command = _command(operation, suffix=operation.value)
    store = _store_with_lease(tmp_path / operation.value, command)
    backend = _FakeBackend()
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=operation,
        backend=backend,  # type: ignore[arg-type]
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )

    dispatcher = AuthorityDispatcher(
        store.state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=LocalApprovalAuthority(),
    )

    assert dispatcher.adapters[adapter.descriptor.adapter_ref] is adapter
    assert adapter.descriptor.tool_ref == MATRIX_HARNESS_LANES[operation].tool_ref
    assert adapter.descriptor.domain == AuthorityDomain.messages.value
    assert adapter.descriptor.capability == MATRIX_HARNESS_LANES[
        operation
    ].authority_capability.value


@pytest.mark.parametrize("operation", list(MatrixHarnessOperation))
def test_exact_authority_executes_each_harness_lane_once(
    tmp_path: Path,
    operation: MatrixHarnessOperation,
) -> None:
    command = _command(operation, suffix=f"execute-{operation.value}")
    store = _store_with_lease(tmp_path / operation.value, command)
    backend = _FakeBackend()
    approvals = LocalApprovalAuthority()
    approval_ref = None
    if MATRIX_HARNESS_LANES[operation].approval_required:
        approval_adapter = MatrixHarnessAuthorityDispatchAdapter(
            operation=operation,
            backend=backend,  # type: ignore[arg-type]
            authority_leases_provider=lambda: store.list_leases(active_only=False),
        )
        approval_request = build_matrix_harness_dispatch_request(
            command,
            adapter=approval_adapter,
        )
        approval_ref = capture_exact_matrix_harness_approval(
            approval_request,
            approval_authority=approvals,
            confirmed=True,
        )

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
        approval_authority=approvals,
    )

    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert backend.starts == [operation]
    assert result.adapter_result is not None
    assert result.adapter_result.safe_output["operation"] == operation.value
    assert result.adapter_result.safe_output["raw_paths_persisted"] is False


def test_supported_exact_lease_issue_then_dispatch_uses_no_private_store_write(
    tmp_path: Path,
) -> None:
    command = _command(MatrixHarnessOperation.start, suffix="supported-issue")
    store = AuthorityLeaseStore(tmp_path / "authority")
    lease, receipt = issue_exact_matrix_harness_lease(
        command,
        store=store,
        confirmed=True,
    )
    backend = _FakeBackend()
    approvals = LocalApprovalAuthority()
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=command.operation,
        backend=backend,  # type: ignore[arg-type]
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )
    approval_ref = capture_exact_matrix_harness_approval(
        build_matrix_harness_dispatch_request(command, adapter=adapter),
        approval_authority=approvals,
        confirmed=True,
    )

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
        approval_authority=approvals,
    )

    assert receipt.status == "issued"
    assert lease.lease_ref == command.lease_ref
    assert result.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert backend.starts == [MatrixHarnessOperation.start]


def test_exact_lease_issue_rejects_existing_ref_without_replacing_original(
    tmp_path: Path,
) -> None:
    store = AuthorityLeaseStore(tmp_path / "authority")
    original = _command(MatrixHarnessOperation.inspect, suffix="lease-owner")
    replacement = _command(
        MatrixHarnessOperation.smoke,
        suffix="lease-collision",
        lease_ref=original.lease_ref,
    )
    issued, _receipt = issue_exact_matrix_harness_lease(
        original,
        store=store,
        confirmed=False,
    )

    with pytest.raises(
        AuthorityLeaseConflictError,
        match="AUTHORITY_LEASE_REF_CONFLICT",
    ):
        issue_exact_matrix_harness_lease(
            replacement,
            store=store,
            confirmed=False,
        )

    persisted = store.get_lease(original.lease_ref)
    assert persisted is not None
    assert persisted.constraints == issued.constraints


def test_requested_lease_ref_is_rejected_outside_exact_messages_contract() -> None:
    with pytest.raises(
        ValueError,
        match="AUTHORITY_LEASE_REQUESTED_REF_EXACT_BINDING_REQUIRED",
    ):
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            requested_lease_ref="authority-lease-ref:caller-selected",
            requested_domains={
                AuthorityDomain.files: [AuthorityCapability.read],
            },
            decision_reason_ref="decision-reason-ref:caller-selected",
            safe_summary="Reject a caller-selected lease ref outside an exact lane.",
        )


def test_coarse_messages_lease_cannot_authorize_harness_or_other_message_action(
    tmp_path: Path,
) -> None:
    command = _command(MatrixHarnessOperation.inspect, suffix="coarse-denied")
    store = _store_with_lease(tmp_path, command)
    coarse = store.list_leases()[0].model_copy(update={"constraints": {}})
    store._write_leases([coarse])
    backend = _FakeBackend()

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_exact_messages_binding_rejects_wrong_authority_capability(
    tmp_path: Path,
) -> None:
    command = _command(MatrixHarnessOperation.inspect, suffix="wrong-capability")
    store = _store_with_lease(tmp_path, command)
    lease = store.list_leases()[0].model_copy(
        update={
            "domains": {
                AuthorityDomain.messages: [AuthorityCapability.execute],
            }
        }
    )
    store._write_leases([lease])
    backend = _FakeBackend()

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_generic_messages_lease_issue_without_exact_lane_binding_is_denied(
    tmp_path: Path,
) -> None:
    store = AuthorityLeaseStore(tmp_path / "authority")
    lease, receipt = store.issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            scope=AuthorityLeaseScope.mission,
            mission_ref="mission-ref:matrix-harness:coarse-issue",
            requested_domains={
                AuthorityDomain.messages: [AuthorityCapability.read],
            },
            decision_reason_ref="decision-reason-ref:matrix-harness:coarse-issue",
            safe_summary="Attempt a coarse messages lease without an exact lane binding.",
        ),
        idempotency_ref="idempotency-ref:matrix-harness:coarse-issue",
    )

    assert lease is None
    assert receipt.status == "denied"
    assert receipt.granted_domains == {}


def test_mutation_approval_identifier_alone_cannot_start(tmp_path: Path) -> None:
    command = _command(MatrixHarnessOperation.start, suffix="approval-missing")
    store = _store_with_lease(tmp_path, command)
    backend = _FakeBackend()

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        approval_ref="approval-ref:matrix-harness:identifier-only",
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []
    assert "reason-ref:authority-budget:approval-not-valid" in result.receipt.reason_refs


def test_approval_for_request_a_cannot_authorize_request_b(tmp_path: Path) -> None:
    command_a = _command(MatrixHarnessOperation.start, suffix="approval-a")
    command_b = _command(MatrixHarnessOperation.start, suffix="approval-b")
    store = _store_with_lease(tmp_path, command_b)
    backend = _FakeBackend()
    approvals = LocalApprovalAuthority()
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=command_a.operation,
        backend=backend,  # type: ignore[arg-type]
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )
    approval_ref = capture_exact_matrix_harness_approval(
        build_matrix_harness_dispatch_request(command_a, adapter=adapter),
        approval_authority=approvals,
        confirmed=True,
    )

    result = execute_matrix_harness_command(
        command_b,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
        approval_authority=approvals,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


@pytest.mark.parametrize("posture", ["revoked", "expired"])
def test_revoked_or_expired_approval_denies_at_start(
    tmp_path: Path,
    posture: str,
) -> None:
    command = _command(MatrixHarnessOperation.start, suffix=posture)
    store = _store_with_lease(tmp_path, command)
    backend = _FakeBackend()
    approvals = LocalApprovalAuthority()
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=command.operation,
        backend=backend,  # type: ignore[arg-type]
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )
    request = build_matrix_harness_dispatch_request(command, adapter=adapter)
    if posture == "revoked":
        approval_ref = capture_exact_matrix_harness_approval(
            request,
            approval_authority=approvals,
            confirmed=True,
        )
        approvals.revoke(approval_ref, "operator revoked exact test grant")
    else:
        approval_request = approvals.create_request(
            build_matrix_harness_approval_request(request)
        )
        approval_ref = approvals.grant(
            approval_request.approval_request_id,
            approved_by_actor_id="operator-ref:local-user",
            expires_at=utc_now() - timedelta(seconds=1),
            approval_ref="approval-ref:matrix-harness:expired",
        ).approval_ref

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
        approval_authority=approvals,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_resource_substitution_denies_before_backend_start(tmp_path: Path) -> None:
    command = _command(MatrixHarnessOperation.start, suffix="resource-substitution")
    store = _store_with_lease(tmp_path, command)
    backend = _FakeBackend()
    approvals = LocalApprovalAuthority()
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=command.operation,
        backend=backend,  # type: ignore[arg-type]
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )
    request = build_matrix_harness_dispatch_request(command, adapter=adapter)
    approval_ref = capture_exact_matrix_harness_approval(
        request,
        approval_authority=approvals,
        confirmed=True,
    )
    action = request.action_request.model_copy(
        update={
            "resource_refs": [
                *request.action_request.resource_refs,
                "target-ref:matrix-harness:substituted",
            ]
        }
    )
    request = request.model_copy(update={"action_request": action})
    request = attach_exact_matrix_harness_approval(
        request,
        approval_authority=approvals,
        approval_ref=approval_ref,
    )

    result = AuthorityDispatcher(
        store.state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approvals,
    ).dispatch(request)

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert "reason-ref:matrix-harness:resource-binding-mismatch" in result.receipt.reason_refs
    assert backend.starts == []


@pytest.mark.parametrize(
    "lease_update",
    [
        {"mission_ref": "mission-ref:matrix-harness:other"},
        {"scope": AuthorityLeaseScope.session},
        {"expires_at": utc_now() - timedelta(seconds=1)},
    ],
)
def test_wrong_mission_session_or_stale_lease_denies(
    tmp_path: Path,
    lease_update: dict[str, Any],
) -> None:
    command = _command(MatrixHarnessOperation.inspect, suffix="bad-lease")
    store = _store_with_lease(tmp_path, command, lease_update=lease_update)
    backend = _FakeBackend()

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_safe_disable_blocks_final_start(tmp_path: Path) -> None:
    command = _command(MatrixHarnessOperation.inspect, suffix="safe-disable")
    store = _store_with_lease(tmp_path, command)
    backend = _FakeBackend(
        readiness=["reason-ref:matrix-harness:safe-disable-engaged"]
    )

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert (
        result.receipt.status
        == AuthorityDispatchStatus.cancelled_before_start.value
    )
    assert backend.starts == []


def test_global_kill_switch_blocks_containment_dispatch_too(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixHarnessOperation.inspect, suffix="global-kill")
    store = _store_with_lease(tmp_path, command)
    backend = _FakeBackend()
    monkeypatch.setenv("UAA_AUTHORITY_LEASE_KILL_SWITCH", "1")

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_reset_mutate_lease_does_not_grant_message_send(tmp_path: Path) -> None:
    command = _command(MatrixHarnessOperation.reset, suffix="no-send")
    store = _store_with_lease(tmp_path, command)
    lease = store.list_leases()[0]

    assert lease.grants(AuthorityDomain.messages, AuthorityCapability.mutate)
    assert not lease.grants(AuthorityDomain.messages, AuthorityCapability.send)
    resources = set(matrix_harness_exact_resource_refs(command))
    constraint = next(
        item
        for item in lease.authority_constraints
        if item.kind == AuthorityConstraintKind.resource_refs.value
    )
    assert set(constraint.allowed_refs) == resources


def test_changed_exact_resource_constraint_denies(tmp_path: Path) -> None:
    command = _command(MatrixHarnessOperation.smoke, suffix="changed-constraint")
    store = _store_with_lease(tmp_path, command)
    lease = store.list_leases()[0]
    constraints = [
        item
        if item.kind != AuthorityConstraintKind.resource_refs.value
        else AuthorityConstraint(
            constraint_ref=item.constraint_ref,
            kind=AuthorityConstraintKind.resource_refs,
            allowed_refs=[
                *item.allowed_refs,
                "target-ref:matrix-harness:unexpected",
            ],
            safe_summary=item.safe_summary,
        )
        for item in lease.authority_constraints
    ]
    store._write_leases(
        [lease.model_copy(update={"authority_constraints": constraints})]
    )
    backend = _FakeBackend()

    result = execute_matrix_harness_command(
        command,
        repo_root=tmp_path,
        authority_state_dir=store.state_dir,
        backend=backend,  # type: ignore[arg-type]
        lease_store=store,
    )

    assert result.receipt.status == AuthorityDispatchStatus.denied.value
    assert backend.starts == []


def test_backend_result_contains_only_bounded_counts_and_refs() -> None:
    result = _FakeHandle(
        MatrixHarnessOperation.fixture_seed,
        "execution-ref:matrix-harness:content-free",
    ).collect()
    payload = result.model_dump_json()

    assert result.fixture_account_count == 2
    assert result.fixture_room_count == 3
    assert result.fixture_event_count == 5
    assert "password" not in payload.lower()
    assert "access_token" not in payload.lower()
    assert "message body" not in payload.lower()
    assert stable_matrix_harness_ref(
        "fixture-ref:matrix-harness", {"count": 5}
    ).startswith("fixture-ref:matrix-harness:sha256:")
