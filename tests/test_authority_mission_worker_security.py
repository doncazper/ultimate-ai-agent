from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from unittest.mock import patch

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.contracts import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchExecutionFence,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
    _entry_hash as dispatch_entry_hash,
    authority_dispatch_request_fingerprint,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    MISSION_WORKER_LOCK_KEY,
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerConflictError,
    MissionWorkerCorruptionError,
    MissionWorkerEvent,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerStore,
    mission_worker_identity_ref,
    mission_worker_job_binding,
)
from ultimate_ai_agent.core.time import utc_now


def _config() -> LocalMissionWorkerConfiguration:
    with patch("platform.system", return_value="Darwin"):
        return LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
        )


def _claimed_worker(tmp_path, suffix: str):
    current = [utc_now()]
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix=suffix,
        dependency_graph=[[]],
        shared_state=True,
    )
    orchestrator.step_store._clock = lambda: current[0]  # noqa: SLF001
    store = MissionWorkerStore(
        orchestrator.step_store.state_dir,
        clock=lambda: current[0],
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    )
    worker.enqueue(request)
    binding = mission_worker_job_binding(request)
    owner_ref = mission_worker_identity_ref(f"mission-worker-ref:test:{suffix}")
    job_claim = store.claim(binding.job_ref, worker_ref=owner_ref, ttl_seconds=5)
    step = request.steps[0]
    definition = request.bound_definition(step)
    context = orchestrator.plan_store.resolve_definition_binding(definition)
    assert context is not None
    step_claim = orchestrator.step_store.claim(
        definition.step_ref,
        owner_ref=owner_ref,
        ttl_seconds=5,
        dispatch_ref=step.request.dispatch_ref,
        dispatch_request_fingerprint_ref=authority_dispatch_request_fingerprint(
            step.request
        ),
        orchestration_context=context,
    )
    fence = AuthorityDispatchExecutionFence(
        job_ref=binding.job_ref,
        worker_ref=owner_ref,
        job_claim_ref=job_claim.claim_ref or "",
        job_generation=job_claim.generation,
        step_ref=definition.step_ref,
        step_claim_ref=step_claim.claim_ref or "",
        step_generation=step_claim.generation,
    )
    return current, orchestrator, dispatcher, store, request, binding, job_claim, fence


def test_correctly_rehashed_early_worker_claim_takeover_fails_closed(tmp_path) -> None:
    current, _, _, store, request, binding, prior, _ = _claimed_worker(
        tmp_path, "early-takeover"
    )
    receipts = store.receipts()
    takeover_at = current[0] + timedelta(seconds=1)
    successor = store._build_from(  # noqa: SLF001
        receipts,
        prior,
        event=MissionWorkerEvent.claimed,
        status=MissionWorkerJobStatus.claimed,
        generation=prior.generation + 1,
        worker_ref=mission_worker_identity_ref(
            "mission-worker-ref:test:early-takeover-successor"
        ),
        claim_ref="mission-worker-claim-ref:test:early-takeover-successor",
        claim_expires_at=takeover_at + timedelta(seconds=5),
        checked_at=takeover_at,
        safe_summary="A forged early takeover with a valid entry hash.",
    )
    store.receipts_path.write_text(
        "".join(item.model_dump_json() + "\n" for item in [*receipts, successor]),
        encoding="utf-8",
    )

    with pytest.raises(
        MissionWorkerCorruptionError,
        match="MISSION_WORKER_LEDGER_TRANSITION_INVALID",
    ):
        store.receipts()
    assert mission_worker_job_binding(request) == binding


def test_worker_completion_uses_time_captured_inside_atomic_lock(tmp_path) -> None:
    current, _, _, store, _, binding, claim, _ = _claimed_worker(
        tmp_path, "atomic-complete-time"
    )
    attempted = Event()

    def complete():
        attempted.set()
        return store.complete(
            binding.job_ref,
            worker_ref=claim.worker_ref or "",
            claim_ref=claim.claim_ref or "",
            generation=claim.generation,
            status=MissionWorkerJobStatus.failed,
            reason_refs=["reason-ref:mission-worker:atomic-time-test"],
            evidence_refs=[],
        )

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        with store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            future = pool.submit(complete)
            assert attempted.wait(timeout=2)
            current[0] += timedelta(seconds=6)
            # Thread remains blocked until the authority lock exits.
        with pytest.raises(MissionWorkerConflictError, match="CLAIM_EXPIRED"):
            future.result(timeout=2)
    finally:
        pool.shutdown(wait=True)


def test_dispatch_prestart_clock_is_captured_after_worker_lock(
    tmp_path, monkeypatch
) -> None:
    current, _, dispatcher, store, request, _, _, fence = _claimed_worker(
        tmp_path, "atomic-prestart-time"
    )
    dispatcher.prepare(request.steps[0].request)
    monkeypatch.setattr(
        "ultimate_ai_agent.core.authority.dispatcher.utc_now",
        lambda: current[0],
    )
    attempted = Event()

    def execute():
        attempted.set()
        return dispatcher.execute(request.steps[0].request, execution_fence=fence)

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        with store.lock_manager.acquire(MISSION_WORKER_LOCK_KEY):
            future = pool.submit(execute)
            assert attempted.wait(timeout=2)
            current[0] += timedelta(seconds=6)
            # Dispatcher remains blocked until the worker lock exits.
        result = future.result(timeout=2)
    finally:
        pool.shutdown(wait=True)

    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.adapter_invocation_performed is False
    assert "reason-ref:authority-dispatch:worker-fence-inactive" in (
        result.receipt.reason_refs
    )


def test_supplied_worker_fence_requires_a_bound_validator(tmp_path) -> None:
    _, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="missing-fence-validator",
        dependency_graph=[[]],
        shared_state=True,
    )
    step = request.steps[0]
    dispatcher.prepare(step.request)
    fence = AuthorityDispatchExecutionFence(
        job_ref="mission-worker-job-ref:test:unbound",
        worker_ref=mission_worker_identity_ref(
            "mission-worker-ref:test:missing-validator"
        ),
        job_claim_ref="mission-worker-claim-ref:test:unbound",
        job_generation=1,
        step_ref=step.definition.step_ref,
        step_claim_ref="mission-step-claim-ref:test:unbound",
        step_generation=1,
    )

    result = dispatcher.execute(step.request, execution_fence=fence)

    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.adapter_invocation_performed is False
    assert result.receipt.reason_refs == [
        "reason-ref:authority-dispatch:worker-fence-validator-unavailable"
    ]


def test_supplied_worker_fence_requires_an_exact_queued_binding(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="unmatched-fence-binding",
        dependency_graph=[[]],
        shared_state=True,
    )
    LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_config(),
    )
    step = request.steps[0]
    dispatcher.prepare(step.request)
    fence = AuthorityDispatchExecutionFence(
        job_ref="mission-worker-job-ref:test:unmatched",
        worker_ref=mission_worker_identity_ref(
            "mission-worker-ref:test:unmatched-binding"
        ),
        job_claim_ref="mission-worker-claim-ref:test:unmatched",
        job_generation=1,
        step_ref=step.definition.step_ref,
        step_claim_ref="mission-step-claim-ref:test:unmatched",
        step_generation=1,
    )

    result = dispatcher.execute(step.request, execution_fence=fence)

    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.adapter_invocation_performed is False
    assert result.receipt.reason_refs == [
        "reason-ref:authority-dispatch:worker-fence-unbound"
    ]


def test_kill_switch_is_rechecked_after_worker_and_step_claims(
    tmp_path, monkeypatch
) -> None:
    _, _, dispatcher, _, request, _, _, fence = _claimed_worker(
        tmp_path, "kill-switch-prestart"
    )
    step = request.steps[0]
    dispatcher.prepare(step.request)
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "engaged")

    result = dispatcher.execute(step.request, execution_fence=fence)

    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.adapter_invocation_performed is False
    assert result.receipt.reason_refs == [
        "reason-ref:authority-dispatch:prestart-authority-invalid"
    ]


def test_stale_unprepared_claim_resumes_with_a_successor_fence(tmp_path) -> None:
    current = [utc_now()]
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="stale-unprepared-resume",
        dependency_graph=[[]],
        shared_state=True,
    )
    orchestrator.step_store._clock = lambda: current[0]  # noqa: SLF001
    store = MissionWorkerStore(
        orchestrator.step_store.state_dir,
        clock=lambda: current[0],
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    )
    worker.enqueue(request)
    binding = mission_worker_job_binding(request)
    store.claim(
        binding.job_ref,
        worker_ref=mission_worker_identity_ref(
            "mission-worker-ref:test:stale-unprepared-old"
        ),
        ttl_seconds=5,
    )
    current[0] += timedelta(seconds=5)

    class Resolver:
        def resolve(self, binding):
            return request

    result = worker.resume_next(
        Resolver(),
        worker_ref="mission-worker-ref:test:stale-unprepared-new",
    )

    assert result is not None and result.status == "succeeded"
    assert (
        sum(item.adapter_invocation_performed for item in dispatcher.list_receipts())
        == 1
    )


def test_truncated_worker_ledger_fails_closed(tmp_path) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="truncated-worker-ledger",
        dependency_graph=[[]],
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    store.enqueue(mission_worker_job_binding(request), queue_capacity=1)
    payload = store.receipts_path.read_bytes()
    store.receipts_path.write_bytes(payload.rstrip(b"\n"))

    with pytest.raises(MissionWorkerCorruptionError, match="LEDGER_TRUNCATED"):
        store.receipts()


def test_correctly_rehashed_terminal_fence_removal_fails_closed(tmp_path) -> None:
    _, orchestrator, dispatcher, store, request, _, _, _ = _claimed_worker(
        tmp_path, "terminal-fence-drift"
    )
    current = store.current_time()
    # Let the existing claim expire so the normal worker can fence a successor.
    store._clock = lambda: current + timedelta(seconds=5)  # noqa: SLF001
    orchestrator.step_store._clock = store._clock  # noqa: SLF001
    result = LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    ).run_once(request, worker_ref="mission-worker-ref:test:terminal-fence-drift-new")
    assert result is not None and result.status == "succeeded"
    payloads = [
        json.loads(line)
        for line in dispatcher.receipts_path.read_text(encoding="utf-8").splitlines()
    ]
    terminal = dispatcher.list_receipts()[-1].model_copy(
        update={"execution_fence_ref": None}
    )
    terminal = terminal.model_copy(
        update={"entry_hash_ref": dispatch_entry_hash(terminal)}
    )
    payloads[-1] = terminal.model_dump(mode="json")
    dispatcher.receipts_path.write_text(
        "".join(json.dumps(payload, sort_keys=True) + "\n" for payload in payloads),
        encoding="utf-8",
    )

    with pytest.raises(
        AuthorityDispatchCorruptionError,
        match="AUTHORITY_DISPATCH_EXECUTION_BINDING_MISMATCH",
    ):
        dispatcher.list_receipts()
