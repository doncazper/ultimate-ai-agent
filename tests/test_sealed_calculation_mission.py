from __future__ import annotations

import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_execution_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.sandbox_calculation.backend import (
    SealedCalculationBackendError,
    SealedCalculationCleanupUnconfirmedError,
    discover_local_docker_backend,
)
from ultimate_ai_agent.core.sandbox_calculation.mission import (
    SealedCalculationMissionRequest,
    SealedCalculationMissionService,
)
from ultimate_ai_agent.core.sandbox_calculation.contracts import (
    SealedCalculationRequest,
    SealedCalculationStatus,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
SECCOMP_PROFILE = ROOT / "packaging" / "sealed-calculation" / "seccomp.json"
EXPRESSION = "31415926 * 27182818 + 7"


def _backend_or_skip(*, kill_switch=lambda: False, safe_disabled=lambda: False):
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI unavailable for the macOS sealed-backend proof")
    try:
        return discover_local_docker_backend(
            seccomp_profile=SECCOMP_PROFILE,
            kill_switch=kill_switch,
            safe_disabled=safe_disabled,
        )
    except SealedCalculationBackendError as exc:
        if os.environ.get("UAA_REQUIRE_SEALED_BACKEND") == "1":
            pytest.fail(f"required sealed calculation backend unavailable: {exc}")
        pytest.skip(f"sealed calculation image is not configured: {exc}")


def _request(*, lease_ref: str) -> SealedCalculationMissionRequest:
    created_at = utc_now()
    return SealedCalculationMissionRequest(
        request_ref="request-ref:sealed-calculation:test",
        input_ref="transient-input-ref:sealed-calculation:test",
        expression=EXPRESSION,
        expression_sha256=hash_text(EXPRESSION),
        plan_ref="mission-plan-ref:sealed-calculation:test",
        mission_ref="mission-ref:sealed-calculation:test",
        run_ref="run-ref:sealed-calculation:test",
        step_ref="mission-step-ref:sealed-calculation:test:1",
        lease_ref=lease_ref,
        request_created_at=created_at,
        start_deadline=created_at + timedelta(minutes=5),
    )


def _service_with_exact_lease(tmp_path: Path, *, backend=None):
    state_dir = tmp_path / "state"
    lease_store = AuthorityLeaseStore(state_dir)
    backend = backend or _backend_or_skip()
    service = SealedCalculationMissionService(
        state_dir=state_dir,
        backend=backend,
        lease_store=lease_store,
    )
    provisional = _request(lease_ref="authority-lease-ref:sealed-calculation:pending")
    resources = service._action_resource_refs(provisional)  # noqa: SLF001
    lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=provisional.mission_ref,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.execute]
            },
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref="constraint-ref:sealed-calculation:resources",
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resources,
                    safe_summary="Allow only the exact sealed calculation resources.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:sealed-calculation:operations",
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Allow one sealed calculation operation.",
                ),
                AuthorityConstraint(
                    constraint_ref="constraint-ref:sealed-calculation:cost",
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    maximum=1,
                    safe_summary="Bound the zero-cost calculation to one micro-unit ceiling.",
                ),
            ],
            decision_reason_ref="reason-ref:sealed-calculation:exact-mission-lease",
            safe_summary="Issue one exact sealed calculation mission lease.",
        ),
        idempotency_ref="idempotency-ref:sealed-calculation:lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return service, _request(lease_ref=lease.lease_ref), state_dir


def test_exact_mission_executes_once_and_replays_content_free(tmp_path: Path) -> None:
    service, request, state_dir = _service_with_exact_lease(tmp_path)
    assert "expression" not in request.model_dump(mode="json")
    assert EXPRESSION not in repr(request)
    starts = 0
    original_start = service.adapter._backend.start  # noqa: SLF001

    def counted_start(**kwargs):
        nonlocal starts
        starts += 1
        return original_start(**kwargs)

    service.adapter._backend.start = counted_start  # type: ignore[method-assign]  # noqa: SLF001
    first = service.run(request, owner_ref="worker-ref:sealed-calculation:test")
    replay = service.run(request, owner_ref="worker-ref:sealed-calculation:test")

    assert first.orchestration.status == "succeeded"
    assert first.transient_result is not None
    assert first.result_preview == "853973398759475"
    assert first.output_sha256 == hash_text(first.result_preview)
    assert replay.orchestration.status == "succeeded"
    assert replay.transient_result is None
    assert replay.result_preview is None
    assert starts == 1

    durable_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in state_dir.rglob("*.json*")
        if path.is_file()
    )
    assert EXPRESSION not in durable_text
    assert first.result_preview not in durable_text
    receipts = [
        json.loads(line)
        for path in state_dir.rglob("*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
        if '"dispatch_ref"' in line
    ]
    start_receipts = [item for item in receipts if item.get("status") == "started"]
    assert any(not item["runtime_start_confirmed"] for item in start_receipts)
    assert any(
        item["runtime_start_confirmed"] and item["input_committed"]
        for item in start_receipts
    )
    terminal = next(
        item
        for item in receipts
        if item.get("status") == "succeeded" and "atomic_start_required" in item
    )
    assert terminal["atomic_start_required"] is True
    assert terminal["runtime_start_confirmed"] is True
    assert terminal["input_committed"] is True
    assert terminal["approval_required"] is False
    assert terminal["approval_ref"] is None


def test_missing_exact_mission_lease_denies_before_backend_start(
    tmp_path: Path,
) -> None:
    backend = _backend_or_skip()
    service = SealedCalculationMissionService(
        state_dir=tmp_path / "state",
        backend=backend,
        lease_store=AuthorityLeaseStore(tmp_path / "state"),
    )

    with pytest.raises(ValueError, match="EXACT_MISSION_LEASE_REQUIRED"):
        service.run(
            _request(lease_ref="authority-lease-ref:sealed-calculation:missing"),
            owner_ref="worker-ref:sealed-calculation:test",
        )

    assert backend.list_orphan_refs() == []


def test_concurrent_identical_mission_starts_at_most_one_container(
    tmp_path: Path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    starts = 0
    original_start = service.adapter._backend.start  # noqa: SLF001

    def counted_start(**kwargs):
        nonlocal starts
        starts += 1
        return original_start(**kwargs)

    service.adapter._backend.start = counted_start  # type: ignore[method-assign]  # noqa: SLF001
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _index: service.run(
                    request,
                    owner_ref="worker-ref:sealed-calculation:concurrent",
                ),
                range(2),
            )
        )

    assert all(result.orchestration.status == "succeeded" for result in results)
    assert sum(result.transient_result is not None for result in results) == 1
    assert starts == 1
    assert service.adapter._backend.list_orphan_refs() == []  # noqa: SLF001


def test_concurrent_dispatch_calls_start_atomic_adapter_at_most_once(
    tmp_path: Path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    starts = 0
    original_start = service.adapter._backend.start  # noqa: SLF001

    def counted_start(**kwargs):
        nonlocal starts
        starts += 1
        return original_start(**kwargs)

    service.adapter._backend.start = counted_start  # type: ignore[method-assign]  # noqa: SLF001
    transient = SealedCalculationRequest(
        request_ref=request.request_ref,
        input_ref=request.input_ref,
        expression=request.expression,
        expression_sha256=request.expression_sha256,
    )
    resources = service._action_resource_refs(request)  # noqa: SLF001
    dispatch_request = (
        service._build_orchestration_request(  # noqa: SLF001
            request,
            transient,
            resources,
        )
        .steps[0]
        .request
    )
    service.input_store.put(transient)
    dispatcher = service.orchestrator.runner.dispatcher
    dispatcher.prepare(dispatch_request)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _index: dispatcher.execute(dispatch_request), range(2))
        )

    assert starts == 1
    assert sum(not result.replayed for result in results) == 1
    assert {result.receipt.status for result in results} == {"started", "succeeded"}
    assert sum(result.recovery_required for result in results) == 1
    terminal_replay = dispatcher.execute(dispatch_request)
    assert terminal_replay.replayed is True
    assert terminal_replay.receipt.status == "succeeded"
    assert service.adapter._backend.list_orphan_refs() == []  # noqa: SLF001


def test_kill_switch_and_safe_disable_fail_closed_before_start(tmp_path: Path) -> None:
    posture = {"kill": False, "disabled": False}
    backend = _backend_or_skip(
        kill_switch=lambda: posture["kill"],
        safe_disabled=lambda: posture["disabled"],
    )
    service, request, _state_dir = _service_with_exact_lease(
        tmp_path,
        backend=backend,
    )
    posture["kill"] = True

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_STRUCTURAL_PREFLIGHT_DENIED",
    ):
        service.run(request, owner_ref="worker-ref:sealed-calculation:test")

    assert backend.list_orphan_refs() == []


def test_revoked_lease_and_changed_input_cannot_start_backend(tmp_path: Path) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    starts = 0
    original_start = service.adapter._backend.start  # noqa: SLF001

    def counted_start(**kwargs):
        nonlocal starts
        starts += 1
        return original_start(**kwargs)

    service.adapter._backend.start = counted_start  # type: ignore[method-assign]  # noqa: SLF001
    changed_expression = "2 + 2"
    changed = request.model_copy(
        update={
            "expression": changed_expression,
            "expression_sha256": hash_text(changed_expression),
        }
    )
    with pytest.raises(ValueError, match="EXACT_MISSION_LEASE_REQUIRED"):
        service.run(
            changed,
            owner_ref="worker-ref:sealed-calculation:changed-input",
        )

    _lease, receipt = service.orchestrator.runner.dispatcher.lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=request.lease_ref,
            decision_reason_ref="reason-ref:sealed-calculation:test-revocation",
            safe_summary="Revoke the exact sealed calculation test lease.",
        ),
        idempotency_ref="idempotency-ref:sealed-calculation:test-revocation",
    )
    assert receipt.status == "revoked"
    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_POLICY_PREFLIGHT_DENIED",
    ):
        service.run(
            request,
            owner_ref="worker-ref:sealed-calculation:revoked",
        )

    assert starts == 0


def test_deadline_expiry_during_ready_handshake_prevents_input_commit(
    tmp_path: Path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    backend = service.adapter._backend  # noqa: SLF001
    deadline_request = request.model_copy(
        update={"start_deadline": utc_now() + timedelta(seconds=1.0)}
    )
    original_read_frame = backend._read_json_frame  # noqa: SLF001
    original_commit = backend._commit_input  # noqa: SLF001
    frame_reads = 0
    commits = 0

    def delayed_read_frame(process, timeout):
        nonlocal frame_reads
        frame_reads += 1
        if frame_reads == 1:
            time.sleep(1.1)
        return original_read_frame(process, timeout)

    def counted_commit(process, transient):
        nonlocal commits
        commits += 1
        return original_commit(process, transient)

    backend._read_json_frame = delayed_read_frame  # type: ignore[method-assign]  # noqa: SLF001
    backend._commit_input = counted_commit  # type: ignore[method-assign]  # noqa: SLF001

    transient = SealedCalculationRequest(
        request_ref=deadline_request.request_ref,
        input_ref=deadline_request.input_ref,
        expression=deadline_request.expression,
        expression_sha256=deadline_request.expression_sha256,
    )
    resources = service._action_resource_refs(deadline_request)  # noqa: SLF001
    dispatch_request = (
        service._build_orchestration_request(  # noqa: SLF001
            deadline_request,
            transient,
            resources,
        )
        .steps[0]
        .request
    )
    service.input_store.put(transient)
    dispatcher = service.orchestrator.runner.dispatcher
    dispatcher.prepare(dispatch_request)

    result = dispatcher.execute(dispatch_request)

    assert result.receipt.status == "failed"
    assert result.receipt.adapter_start_attempted is True
    assert result.receipt.adapter_invocation_performed is False
    assert frame_reads == 1
    assert commits == 0
    assert backend.list_orphan_refs() == []


def test_kill_switch_after_input_acceptance_removes_exact_container() -> None:
    posture = {"kill": False}
    backend = _backend_or_skip(kill_switch=lambda: posture["kill"])
    expression = "2 ** 64"
    transient = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:runtime-kill",
        input_ref="input-ref:sealed-calculation:runtime-kill",
        expression=expression,
        expression_sha256=hash_text(expression),
    )
    handle = backend.start(
        execution_ref="execution-ref:sealed-calculation:runtime-kill",
        request=transient,
        validate_commit_fence=lambda: ([], utc_now()),
    )
    posture["kill"] = True

    result = handle.collect()

    assert result.status == SealedCalculationStatus.killed
    assert backend.list_orphan_refs() == []


def test_unconfirmed_cleanup_never_reports_calculation_success() -> None:
    backend = _backend_or_skip()
    expression = "9 * 9"
    transient = SealedCalculationRequest(
        request_ref="request-ref:sealed-calculation:cleanup",
        input_ref="input-ref:sealed-calculation:cleanup",
        expression=expression,
        expression_sha256=hash_text(expression),
    )
    execution_ref = "execution-ref:sealed-calculation:cleanup"
    handle = backend.start(
        execution_ref=execution_ref,
        request=transient,
        validate_commit_fence=lambda: ([], utc_now()),
    )
    original_remove = backend._remove_owned_container  # noqa: SLF001

    def cleanup_unconfirmed(_container_name, _execution_ref):
        raise SealedCalculationCleanupUnconfirmedError(
            "SEALED_CALCULATION_CLEANUP_UNCONFIRMED"
        )

    backend._remove_owned_container = cleanup_unconfirmed  # type: ignore[method-assign]  # noqa: SLF001
    try:
        result = handle.collect()
    finally:
        backend._remove_owned_container = original_remove  # type: ignore[method-assign]  # noqa: SLF001
        original_remove(handle._container_name, execution_ref)  # noqa: SLF001

    assert result.status == SealedCalculationStatus.recovery_required
    assert result.reason_codes == ["SEALED_CALCULATION_CLEANUP_UNCONFIRMED"]
    assert backend.list_orphan_refs() == []


def test_unconfirmed_cleanup_remains_dispatch_recovery_required(
    tmp_path: Path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    transient = SealedCalculationRequest(
        request_ref=request.request_ref,
        input_ref=request.input_ref,
        expression=request.expression,
        expression_sha256=request.expression_sha256,
    )
    resources = service._action_resource_refs(request)  # noqa: SLF001
    dispatch_request = service._build_orchestration_request(  # noqa: SLF001
        request,
        transient,
        resources,
    ).steps[0].request
    service.input_store.put(transient)
    dispatcher = service.orchestrator.runner.dispatcher
    dispatcher.prepare(dispatch_request)
    backend = service.adapter._backend  # noqa: SLF001
    original_remove = backend._remove_owned_container  # noqa: SLF001

    def cleanup_unconfirmed(_container_name, _execution_ref):
        raise SealedCalculationCleanupUnconfirmedError(
            "SEALED_CALCULATION_CLEANUP_UNCONFIRMED"
        )

    backend._remove_owned_container = cleanup_unconfirmed  # type: ignore[method-assign]  # noqa: SLF001
    try:
        result = dispatcher.execute(dispatch_request)
    finally:
        backend._remove_owned_container = original_remove  # type: ignore[method-assign]  # noqa: SLF001
        execution_ref = authority_dispatch_execution_ref(dispatch_request)
        original_remove(backend._container_name(execution_ref), execution_ref)  # noqa: SLF001

    assert result.recovery_required is True
    assert result.receipt.status == "started"
    assert result.receipt.runtime_start_confirmed is True
    assert result.receipt.input_committed is True
    replay = dispatcher.execute(dispatch_request)
    assert replay.recovery_required is True
    assert replay.receipt.status == "started"


def test_unexpected_collection_failure_requires_recovery_without_second_start(
    tmp_path: Path,
) -> None:
    service, request, _state_dir = _service_with_exact_lease(tmp_path)
    transient = SealedCalculationRequest(
        request_ref=request.request_ref,
        input_ref=request.input_ref,
        expression=request.expression,
        expression_sha256=request.expression_sha256,
    )
    resources = service._action_resource_refs(request)  # noqa: SLF001
    dispatch_request = service._build_orchestration_request(  # noqa: SLF001
        request,
        transient,
        resources,
    ).steps[0].request
    service.input_store.put(transient)
    dispatcher = service.orchestrator.runner.dispatcher
    dispatcher.prepare(dispatch_request)
    backend = service.adapter._backend  # noqa: SLF001
    original_start = backend.start
    start_count = 0

    def counted_start(**kwargs):
        nonlocal start_count
        start_count += 1
        return original_start(**kwargs)

    def collection_failed(*_args, **_kwargs):
        raise OSError("injected collection failure")

    backend.start = counted_start  # type: ignore[method-assign]
    backend._bounded_collect = collection_failed  # type: ignore[method-assign]  # noqa: SLF001

    result = dispatcher.execute(dispatch_request)
    replay = dispatcher.execute(dispatch_request)

    assert result.recovery_required is True
    assert result.receipt.status == "started"
    assert result.receipt.runtime_start_confirmed is True
    assert result.receipt.input_committed is True
    assert replay.recovery_required is True
    assert replay.receipt.receipt_ref == result.receipt.receipt_ref
    assert start_count == 1
    assert backend.list_orphan_refs() == []
