from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MISSION_CONTROL_LEDGER_FILE,
    MissionControlConflictError,
    MissionControlCorruptionError,
    MissionControlEvent,
    MissionControlRequest,
    MissionControlStore,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerConflictError,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerStore,
)


def _request(
    *,
    suffix: str = "cancel",
    event: MissionControlEvent = MissionControlEvent.cancellation_requested,
) -> MissionControlRequest:
    updates = {}
    if event == MissionControlEvent.dead_letter_recovery_requested:
        updates = {
            "dead_letter_step_ref": f"mission-step-ref:{suffix}",
            "dead_letter_receipt_ref": f"mission-step-receipt-ref:{suffix}",
            "dead_letter_entry_hash_ref": f"mission-step-entry-hash-ref:{suffix}",
        }
    return MissionControlRequest(
        control_ref=f"mission-control-ref:test:{suffix}",
        event=event,
        plan_ref=f"mission-plan-ref:test:{suffix}",
        plan_fingerprint_ref=f"mission-plan-fingerprint-ref:test:{suffix}",
        mission_ref=f"mission-ref:test:{suffix}",
        run_ref=f"run-ref:test:{suffix}",
        lease_ref=f"authority-lease-ref:test:{suffix}",
        idempotency_ref=f"idempotency-ref:mission-control:test:{suffix}",
        reason_ref=f"reason-ref:mission-control:test:{suffix}",
        safe_summary="Request one exact mission control posture.",
        **updates,
    )


def _worker_config() -> LocalMissionWorkerConfiguration:
    with patch("platform.system", return_value="Darwin"):
        return LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
        )


def _cancellation_for_orchestration(request) -> MissionControlRequest:
    plan = request.build_durable_plan()
    return MissionControlRequest(
        control_ref=f"mission-control-ref:{plan.plan_ref}",
        event=MissionControlEvent.cancellation_requested,
        plan_ref=plan.plan_ref,
        plan_fingerprint_ref=plan.fingerprint_ref,
        mission_ref=plan.mission_ref,
        run_ref=plan.run_ref,
        lease_ref=request.steps[0].request.lease_ref,
        idempotency_ref=f"idempotency-ref:mission-cancel:{plan.plan_ref}",
        reason_ref="reason-ref:mission-control:test-operator-cancel",
        safe_summary="Cancel one exact immutable mission plan.",
    )


def test_cancellation_fence_is_append_first_idempotent_and_exact(
    tmp_path: Path,
) -> None:
    store = MissionControlStore(tmp_path)
    request = _request()

    first = store.append(request)
    replay = store.append(request)
    cancellation = store.cancellation_for(
        plan_ref=request.plan_ref,
        plan_fingerprint_ref=request.plan_fingerprint_ref,
        mission_ref=request.mission_ref,
        run_ref=request.run_ref,
    )

    assert replay == first
    assert cancellation == first
    assert len(store.receipts()) == 1
    assert first.request_fingerprint_ref == request.fingerprint_ref
    assert first.request.raw_request_persisted is False
    assert first.request.credentials_persisted is False


def test_changed_or_cross_mission_idempotency_scope_is_rejected(
    tmp_path: Path,
) -> None:
    store = MissionControlStore(tmp_path)
    request = _request()
    store.append(request)

    with pytest.raises(
        MissionControlConflictError,
        match="IDEMPOTENCY_OR_SCOPE_CONFLICT",
    ):
        store.append(
            request.model_copy(
                update={"reason_ref": "reason-ref:mission-control:test:changed"}
            )
        )
    with pytest.raises(
        MissionControlConflictError,
        match="IDEMPOTENCY_OR_SCOPE_CONFLICT",
    ):
        store.append(
            _request(suffix="other").model_copy(
                update={"idempotency_ref": request.idempotency_ref}
            )
        )


def test_dead_letter_recovery_intent_never_reopens_original_truth(
    tmp_path: Path,
) -> None:
    store = MissionControlStore(tmp_path)
    request = _request(
        suffix="dead-letter",
        event=MissionControlEvent.dead_letter_recovery_requested,
    )

    receipt = store.append(request)

    assert receipt.request.event == "dead_letter_recovery_requested"
    assert store.cancellation_for(
        plan_ref=request.plan_ref,
        plan_fingerprint_ref=request.plan_fingerprint_ref,
        mission_ref=request.mission_ref,
        run_ref=request.run_ref,
    ) is None


@pytest.mark.parametrize(
    "payload_update",
    [
        {"raw_request_persisted": True},
        {"raw_output_persisted": True},
        {"credentials_persisted": True},
        {"raw_prompt": "unsafe"},
    ],
)
def test_unsafe_mission_control_payload_fields_are_rejected(
    payload_update: dict[str, object],
) -> None:
    payload = _request().model_dump(mode="python")
    payload.update(payload_update)

    with pytest.raises(ValidationError):
        MissionControlRequest.model_validate(payload)


def test_cancellation_for_requires_exact_plan_binding(tmp_path: Path) -> None:
    store = MissionControlStore(tmp_path)
    request = _request()
    store.append(request)

    assert store.cancellation_for(
        plan_ref=request.plan_ref,
        plan_fingerprint_ref="mission-plan-fingerprint-ref:test:other",
        mission_ref=request.mission_ref,
        run_ref=request.run_ref,
    ) is None


def test_hash_chain_tampering_fails_closed(tmp_path: Path) -> None:
    store = MissionControlStore(tmp_path)
    store.append(_request())
    path = tmp_path / MISSION_CONTROL_LEDGER_FILE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["request"]["reason_ref"] = "reason-ref:mission-control:test:tampered"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(MissionControlCorruptionError, match="LEDGER_INVALID"):
        store.receipts()


@pytest.mark.parametrize("replacement", ["symlink", "fifo", "hardlink"])
def test_ledger_substitution_fails_closed(
    tmp_path: Path,
    replacement: str,
) -> None:
    path = tmp_path / MISSION_CONTROL_LEDGER_FILE
    tmp_path.mkdir(exist_ok=True)
    target = tmp_path / "target"
    target.write_text("not a ledger\n", encoding="utf-8")
    if replacement == "symlink":
        path.symlink_to(target)
    elif replacement == "fifo":
        os.mkfifo(path)
    else:
        os.link(target, path)

    with pytest.raises(MissionControlCorruptionError):
        MissionControlStore(tmp_path).append(_request())


def test_truncated_or_oversized_ledger_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / MISSION_CONTROL_LEDGER_FILE
    tmp_path.mkdir(exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(MissionControlCorruptionError, match="TRUNCATED"):
        MissionControlStore(tmp_path).receipts()

    path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(MissionControlCorruptionError, match="SIZE_OR_TYPE_INVALID"):
        MissionControlStore(tmp_path).receipts()


def test_cancellation_before_worker_claim_prevents_every_adapter_start(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-before-claim",
        shared_state=True,
    )
    control_store = MissionControlStore(orchestrator.step_store.state_dir)
    worker_store = MissionWorkerStore(orchestrator.step_store.state_dir)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=worker_store,
        control_store=control_store,
        configuration=_worker_config(),
    )
    worker.enqueue(request)
    control_store.append(_cancellation_for_orchestration(request))

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:cancel-before-claim",
    )

    assert result is None
    assert worker_store.latest()[0].status == MissionWorkerJobStatus.cancelled.value
    assert dispatcher.list_receipts() == []


def test_cancellation_requires_the_exact_active_mission_lease(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-wrong-lease",
        shared_state=True,
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_worker_config(),
    )
    worker.enqueue(request)
    cancellation = _cancellation_for_orchestration(request).model_copy(
        update={"lease_ref": "authority-lease-ref:test:unrelated"}
    )

    with pytest.raises(
        (ValueError, MissionWorkerConflictError),
        match="EXACT_PLAN_LEASE_REQUIRED",
    ):
        worker.control_store.append(cancellation)

    assert worker.control_store.receipts() == []
    assert dispatcher.list_receipts() == []


def test_synchronous_orchestrator_honors_durable_cancellation_fence(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-synchronous",
        dependency_graph=[[]],
        shared_state=True,
    )
    orchestrator.materialize(request)
    cancellation = orchestrator.control_store.append(
        _cancellation_for_orchestration(request)
    )

    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:cancel-synchronous",
    )

    assert result.status == "failed"
    assert cancellation.receipt_ref in result.evidence_refs
    assert not any(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    )


def test_cancellation_after_claim_wins_inside_locked_prestart_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-before-start",
        shared_state=True,
    )
    control_store = MissionControlStore(orchestrator.step_store.state_dir)
    worker_store = MissionWorkerStore(orchestrator.step_store.state_dir)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=worker_store,
        control_store=control_store,
        configuration=_worker_config(),
    )
    original_run = orchestrator.run
    appended = False

    def cancel_then_run(*args, **kwargs):
        nonlocal appended
        if not appended:
            control_store.append(_cancellation_for_orchestration(request))
            appended = True
        return original_run(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "run", cancel_then_run)

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:cancel-before-start",
    )

    assert result is not None and result.status == "failed"
    assert worker_store.latest()[0].status == MissionWorkerJobStatus.cancelled.value
    assert not any(item.execution_started for item in dispatcher.list_receipts())
    assert not any(
        item.adapter_invocation_performed for item in dispatcher.list_receipts()
    )


def test_durable_start_wins_race_and_cancellation_becomes_recovery_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-after-start",
        shared_state=True,
    )
    control_store = MissionControlStore(orchestrator.step_store.state_dir)
    worker_store = MissionWorkerStore(orchestrator.step_store.state_dir)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=worker_store,
        control_store=control_store,
        configuration=_worker_config(),
    )
    adapter = next(iter(dispatcher.adapters.values()))
    original_invoke = adapter.invoke
    appended = False

    def cancel_after_start(dispatch_request):
        nonlocal appended
        if not appended:
            control_store.append(_cancellation_for_orchestration(request))
            appended = True
        return original_invoke(dispatch_request)

    monkeypatch.setattr(adapter, "invoke", cancel_after_start)

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:cancel-after-start",
    )

    assert result is not None and result.status == "recovery_required"
    assert (
        worker_store.latest()[0].status
        == MissionWorkerJobStatus.recovery_required.value
    )
    assert sum(item.adapter_invocation_performed for item in dispatcher.list_receipts()) == 1
    assert not any(
        item.status == "started" and item.dispatch_ref == request.steps[1].request.dispatch_ref
        for item in dispatcher.list_receipts()
    )


def test_late_cancellation_cannot_rewrite_a_terminal_worker_result(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="cancel-after-terminal",
        dependency_graph=[[]],
        shared_state=True,
    )
    control_store = MissionControlStore(orchestrator.step_store.state_dir)
    worker_store = MissionWorkerStore(orchestrator.step_store.state_dir)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=worker_store,
        control_store=control_store,
        configuration=_worker_config(),
    )

    succeeded = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:cancel-after-terminal:first",
    )
    with pytest.raises(
        (ValueError, MissionWorkerConflictError),
        match="MISSION_CONTROL_MISSION_ALREADY_TERMINAL",
    ):
        control_store.append(_cancellation_for_orchestration(request))
    replay = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:cancel-after-terminal:replay",
    )

    assert succeeded is not None and succeeded.status == "succeeded"
    assert replay is None
    assert worker_store.latest()[0].status == MissionWorkerJobStatus.succeeded.value
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 1
