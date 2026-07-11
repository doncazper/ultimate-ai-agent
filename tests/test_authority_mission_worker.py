from __future__ import annotations

import os
import time
from datetime import timedelta
from unittest.mock import patch

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.contracts import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerConflictError,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerRequestResolver,
    MissionWorkerStore,
    build_mission_worker_read_model,
    mission_worker_job_binding,
    mission_worker_identity_ref,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import AuthorityDispatchStatus
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchExecutionFence,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_request_fingerprint,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager


def _config(**updates):
    with patch("platform.system", return_value="Darwin"):
        return LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
            **updates,
        )


class _Resolver(MissionWorkerRequestResolver):
    def __init__(self, request):
        self.request = request

    def resolve(self, binding):
        return self.request


def test_drifted_request_resolver_is_denied_before_claim(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-resolver-drift",
        shared_state=True,
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_config(),
    )
    worker.enqueue(request)
    changed = request.model_copy(
        update={"safe_summary": "A changed but still safe mission summary."}
    )

    with pytest.raises(
        MissionWorkerConflictError,
        match="REQUEST_RESOLVER_FINGERPRINT_MISMATCH",
    ):
        worker.resume_next(
            _Resolver(changed),
            worker_ref="mission-worker-ref:test:resolver-drift",
        )
    assert dispatcher.list_receipts() == []
    assert worker.store.latest()[0].status == MissionWorkerJobStatus.pending.value


def test_stale_worker_generation_is_fenced(tmp_path) -> None:
    current = [utc_now()]
    store = MissionWorkerStore(tmp_path, clock=lambda: current[0])
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-stale",
        shared_state=True,
    )
    binding = mission_worker_job_binding(request)
    store.enqueue(binding, queue_capacity=2)
    old = store.claim(
        binding.job_ref,
        worker_ref=mission_worker_identity_ref("mission-worker-ref:test:stale-old"),
        ttl_seconds=5,
    )
    current[0] += timedelta(seconds=5)
    new = store.claim(
        binding.job_ref,
        worker_ref=mission_worker_identity_ref("mission-worker-ref:test:stale-new"),
        ttl_seconds=5,
    )

    assert new.generation == old.generation + 1
    with pytest.raises(MissionWorkerConflictError, match="STALE_OWNER_FENCED"):
        store.heartbeat(
            binding.job_ref,
            worker_ref=old.worker_ref or "",
            claim_ref=old.claim_ref or "",
            generation=old.generation,
            ttl_seconds=5,
        )


def test_kill_switch_blocks_before_queue_claim(tmp_path, monkeypatch) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-kill-before-claim",
        shared_state=True,
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_config(),
    )
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "engaged")

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:kill-before-claim",
    )

    assert result is None
    assert worker.store.latest() == []
    assert dispatcher.list_receipts() == []


def test_kill_switch_engagement_inside_claim_boundary_records_no_claim(
    tmp_path, monkeypatch
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-kill-claim-boundary",
        dependency_graph=[[]],
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    binding = mission_worker_job_binding(request)
    store.enqueue(binding, queue_capacity=1)
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "engaged")

    with pytest.raises(MissionWorkerConflictError, match="KILL_SWITCH_ENGAGED"):
        store.claim(
            binding.job_ref,
            worker_ref=mission_worker_identity_ref("mission-worker-ref:test:kill-race"),
            ttl_seconds=5,
        )

    assert store.latest()[0].status == MissionWorkerJobStatus.pending.value


def test_periodic_worker_and_step_heartbeats_are_recorded(
    tmp_path, monkeypatch
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-heartbeat",
        dependency_graph=[[]],
        shared_state=True,
    )
    adapter = next(iter(dispatcher.adapters.values()))
    original = adapter.invoke

    def delayed(request):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            worker_heartbeat = any(
                item.event == "heartbeat" for item in worker.store.receipts()
            )
            step_heartbeat = (
                sum(
                    item.status == "claimed"
                    for item in orchestrator.step_store.receipts()
                )
                >= 3
            )
            if worker_heartbeat and step_heartbeat:
                break
            time.sleep(0.02)
        else:
            raise AssertionError("worker and step heartbeats were not observed")
        return original(request)

    monkeypatch.setattr(adapter, "invoke", delayed)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_config(),
    )

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:heartbeat",
    )

    assert result is not None and result.status == "succeeded"
    assert any(item.event == "heartbeat" for item in worker.store.receipts())
    inspected = build_mission_worker_read_model(
        store=worker.store,
        orchestrator=orchestrator,
        configuration=_config(),
    )
    assert inspected.jobs[0].last_heartbeat_at is not None
    assert inspected.jobs[0].latest_event == "completed"
    step_receipts = orchestrator.step_store.receipts()
    assert sum(item.status == "claimed" for item in step_receipts) >= 3
    assert os.environ.get(AUTHORITY_LEASE_KILL_SWITCH_ENV) is None


def test_graceful_shutdown_releases_claim_between_steps(tmp_path, monkeypatch) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-graceful-shutdown",
        dependency_graph=[[], [0]],
        shared_state=True,
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_config(),
    )
    original_run = orchestrator.run

    def stop_after_first(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if result.status == "in_progress":
            worker.request_shutdown()
        return result

    monkeypatch.setattr(orchestrator, "run", stop_after_first)

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:graceful-shutdown",
    )

    assert result is not None and result.status == "in_progress"
    assert worker.store.latest()[0].status == MissionWorkerJobStatus.pending.value
    assert (
        sum(
            item.status == "succeeded" and item.adapter_invocation_performed
            for item in dispatcher.list_receipts()
        )
        == 1
    )
    assert orchestrator.step_store.read(
        request.steps[1].definition.step_ref
    ).status == ("pending")


def test_job_claim_deadline_preserves_later_step_deadlines(tmp_path) -> None:
    _, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-mixed-deadlines",
        dependency_graph=[[], [0]],
        shared_state=True,
    )
    first_deadline = utc_now() + timedelta(minutes=5)
    second_deadline = utc_now() + timedelta(minutes=10)
    deadlines = [first_deadline, second_deadline]
    steps = [
        step.model_copy(
            update={
                "definition": step.definition.model_copy(
                    update={"deadline": deadlines[index]}
                ),
                "request": step.request.model_copy(
                    update={"start_deadline": deadlines[index]}
                ),
            }
        )
        for index, step in enumerate(request.steps)
    ]
    changed = request.model_copy(update={"steps": steps})

    assert mission_worker_job_binding(changed).deadline == second_deadline


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO is not supported")
def test_worker_ledger_and_lock_files_reject_symlink_and_fifo(tmp_path) -> None:
    _, _, _, _, request, _ = _orchestration_fixture(
        tmp_path / "fixture",
        suffix="worker-storage-hardening",
        dependency_graph=[[]],
        shared_state=True,
    )
    binding = mission_worker_job_binding(request)
    target = tmp_path / "target"
    target.write_text("do not follow", encoding="utf-8")

    symlink_state = tmp_path / "symlink-state"
    symlink_state.mkdir()
    (symlink_state / "local_mission_worker_receipts.jsonl").symlink_to(target)
    with pytest.raises(Exception, match="MISSION_WORKER_LEDGER_(READ|WRITE)_FAILED"):
        MissionWorkerStore(symlink_state).enqueue(binding, queue_capacity=1)
    assert target.read_text(encoding="utf-8") == "do not follow"

    fifo_state = tmp_path / "fifo-state"
    fifo_state.mkdir()
    os.mkfifo(fifo_state / "local_mission_worker_receipts.jsonl")
    with pytest.raises(
        Exception, match="MISSION_WORKER_LEDGER_(TYPE|SIZE_OR_TYPE)_INVALID"
    ):
        MissionWorkerStore(fifo_state).enqueue(binding, queue_capacity=1)

    lock_dir = tmp_path / "lock-state"
    lock_dir.mkdir()
    (lock_dir / "worker.lock").symlink_to(target)
    with pytest.raises(OSError):
        with FileSingleWriterLockManager(lock_dir).acquire("worker"):
            pass

    fifo_lock_dir = tmp_path / "fifo-lock-state"
    fifo_lock_dir.mkdir()
    os.mkfifo(fifo_lock_dir / "worker.lock")
    with pytest.raises(OSError):
        with FileSingleWriterLockManager(fifo_lock_dir).acquire("worker"):
            pass

    real_state = tmp_path / "real-state"
    real_state.mkdir()
    aliased_state = tmp_path / "aliased-state"
    aliased_state.symlink_to(real_state, target_is_directory=True)
    with pytest.raises(Exception, match="MISSION_WORKER_STATE_DIR_INVALID"):
        MissionWorkerStore(aliased_state).enqueue(binding, queue_capacity=1)


def test_deadline_expiry_and_terminal_job_recovery_fail_closed(tmp_path) -> None:
    current = [utc_now()]
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-deadline-expiry",
        dependency_graph=[[]],
        shared_state=True,
    )
    store = MissionWorkerStore(
        orchestrator.step_store.state_dir,
        clock=lambda: current[0],
    )
    binding = mission_worker_job_binding(request)
    store.enqueue(binding, queue_capacity=1)
    current[0] = binding.deadline

    expired = store.claim(
        binding.job_ref,
        worker_ref=mission_worker_identity_ref("mission-worker-ref:test:expired"),
        ttl_seconds=5,
    )
    read_model = build_mission_worker_read_model(
        store=store,
        orchestrator=orchestrator,
        configuration=_config(),
    )

    assert expired.status == MissionWorkerJobStatus.failed.value
    assert read_model.jobs[0].recovery_status == "failed"
    assert read_model.jobs[0].reason_refs == [
        "reason-ref:mission-worker:deadline-expired"
    ]


def test_platform_and_worker_identity_inputs_cannot_spoof_durable_truth(
    tmp_path,
) -> None:
    with patch("platform.system", return_value="Linux"):
        with pytest.raises(ValueError, match="OBSERVED_PLATFORM_MISMATCH"):
            LocalMissionWorkerConfiguration(
                enabled=True,
                observed_platform=MissionWorkerPlatform.macos,
            )

    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-identity-redaction",
        dependency_graph=[[]],
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    binding = mission_worker_job_binding(request)
    store.enqueue(binding, queue_capacity=1)
    with pytest.raises(ValueError, match="OPAQUE_IDENTITY_REQUIRED"):
        store.claim(
            binding.job_ref,
            worker_ref="mission-worker-ref:alice",
            ttl_seconds=5,
        )
    assert "alice" not in store.receipts_path.read_text(encoding="utf-8")


def test_boot_recovery_classifies_prepared_dispatch(tmp_path) -> None:
    current = [utc_now()]
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-prepared-recovery",
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
    owner_ref = mission_worker_identity_ref("mission-worker-ref:test:prepared-recovery")
    store.claim(binding.job_ref, worker_ref=owner_ref, ttl_seconds=5)
    step = request.steps[0]
    definition = request.bound_definition(step)
    context = orchestrator.plan_store.resolve_definition_binding(definition)
    assert context is not None
    orchestrator.step_store.claim(
        definition.step_ref,
        owner_ref=owner_ref,
        ttl_seconds=5,
        dispatch_ref=step.request.dispatch_ref,
        dispatch_request_fingerprint_ref=authority_dispatch_request_fingerprint(
            step.request
        ),
        orchestration_context=context,
    )
    dispatcher.prepare(step.request)

    read_model = build_mission_worker_read_model(
        store=store,
        orchestrator=orchestrator,
        configuration=_config(),
    )

    assert read_model.jobs[0].recovery_status == "prepared_dispatch"
    assert read_model.active_claim_count == 1
    assert read_model.jobs[0].steps[0].adapter_reinvocation_allowed is False
    assert all(
        item.adapter_invocation_performed is False
        for item in dispatcher.list_receipts()
    )

    current[0] += timedelta(seconds=5)
    resumed = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:prepared-recovery-new",
    )

    assert resumed is not None and resumed.status == "succeeded"
    assert (
        sum(
            item.status == "succeeded" and item.adapter_invocation_performed
            for item in dispatcher.list_receipts()
        )
        == 1
    )


def test_durable_start_crash_is_never_reinvoked_on_boot_recovery(
    tmp_path, monkeypatch
) -> None:
    current = [utc_now()]
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-started-recovery",
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
    owner_ref = mission_worker_identity_ref("mission-worker-ref:test:started-recovery")
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
    dispatcher.prepare(step.request)
    execution_fence = AuthorityDispatchExecutionFence(
        job_ref=binding.job_ref,
        worker_ref=owner_ref,
        job_claim_ref=job_claim.claim_ref or "",
        job_generation=job_claim.generation,
        step_ref=definition.step_ref,
        step_claim_ref=step_claim.claim_ref or "",
        step_generation=step_claim.generation,
    )
    original_append = dispatcher._append  # noqa: SLF001

    def crash_after_durable_start(receipt):
        original_append(receipt)
        if receipt.status == AuthorityDispatchStatus.started.value:
            raise RuntimeError("simulated crash after durable start")

    monkeypatch.setattr(dispatcher, "_append", crash_after_durable_start)
    with pytest.raises(RuntimeError, match="simulated crash"):
        dispatcher.execute(step.request, execution_fence=execution_fence)
    monkeypatch.setattr(dispatcher, "_append", original_append)
    store.complete(
        binding.job_ref,
        worker_ref=owner_ref,
        claim_ref=job_claim.claim_ref or "",
        generation=job_claim.generation,
        status=MissionWorkerJobStatus.failed,
        reason_refs=["reason-ref:mission-worker:simulated-worker-failure"],
        evidence_refs=[],
    )

    read_model = build_mission_worker_read_model(
        store=store,
        orchestrator=orchestrator,
        configuration=_config(),
    )
    assert read_model.jobs[0].recovery_status == "started_unknown_terminal"
    assert read_model.jobs[0].durable_status == "failed"
    assert read_model.active_claim_count == 0
    assert all(
        item.adapter_invocation_performed is False
        for item in dispatcher.list_receipts()
    )

    current[0] += timedelta(seconds=5)
    recovered = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:started-recovery-new",
    )
    assert recovered is None
    assert all(
        item.adapter_invocation_performed is False
        for item in dispatcher.list_receipts()
    )


def test_expired_caller_cannot_use_successor_claims_to_start(tmp_path) -> None:
    current = [utc_now()]
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-stale-caller-start",
        dependency_graph=[[]],
        shared_state=True,
    )
    orchestrator.step_store._clock = lambda: current[0]  # noqa: SLF001
    store = MissionWorkerStore(
        orchestrator.step_store.state_dir,
        clock=lambda: current[0],
    )
    LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    ).enqueue(request)
    binding = mission_worker_job_binding(request)
    step = request.steps[0]
    definition = request.bound_definition(step)
    context = orchestrator.plan_store.resolve_definition_binding(definition)
    assert context is not None
    old_owner = mission_worker_identity_ref("mission-worker-ref:test:stale-caller-old")
    old_job = store.claim(binding.job_ref, worker_ref=old_owner, ttl_seconds=5)
    old_step = orchestrator.step_store.claim(
        definition.step_ref,
        owner_ref=old_owner,
        ttl_seconds=5,
        dispatch_ref=step.request.dispatch_ref,
        dispatch_request_fingerprint_ref=authority_dispatch_request_fingerprint(
            step.request
        ),
        orchestration_context=context,
    )
    dispatcher.prepare(step.request)
    old_fence = AuthorityDispatchExecutionFence(
        job_ref=binding.job_ref,
        worker_ref=old_owner,
        job_claim_ref=old_job.claim_ref or "",
        job_generation=old_job.generation,
        step_ref=definition.step_ref,
        step_claim_ref=old_step.claim_ref or "",
        step_generation=old_step.generation,
    )

    current[0] += timedelta(seconds=5)
    new_owner = mission_worker_identity_ref("mission-worker-ref:test:stale-caller-new")
    store.claim(binding.job_ref, worker_ref=new_owner, ttl_seconds=5)
    orchestrator.step_store.claim(
        definition.step_ref,
        owner_ref=new_owner,
        ttl_seconds=5,
        dispatch_ref=step.request.dispatch_ref,
        dispatch_request_fingerprint_ref=authority_dispatch_request_fingerprint(
            step.request
        ),
        orchestration_context=context,
    )

    result = dispatcher.execute(step.request, execution_fence=old_fence)

    assert result.receipt.status == "cancelled_before_start"
    assert result.receipt.adapter_invocation_performed is False
    assert result.receipt.execution_started is False
    assert "reason-ref:authority-dispatch:worker-fence-inactive" in (
        result.receipt.reason_refs
    )


def test_inspection_bounds_terminal_history_without_hiding_active_jobs(
    tmp_path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-bounded-history",
        dependency_graph=[[]],
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    base = mission_worker_job_binding(request)
    worker_ref = mission_worker_identity_ref("mission-worker-ref:test:history")
    for index in range(33):
        binding = base.model_copy(
            update={
                "job_ref": f"mission-worker-job-ref:test:history:{index}",
                "plan_ref": f"mission-plan-ref:test:history:{index}",
            }
        )
        store.enqueue(binding, queue_capacity=1)
        claim = store.claim(binding.job_ref, worker_ref=worker_ref, ttl_seconds=5)
        store.complete(
            binding.job_ref,
            worker_ref=worker_ref,
            claim_ref=claim.claim_ref or "",
            generation=claim.generation,
            status=MissionWorkerJobStatus.failed,
            reason_refs=["reason-ref:mission-worker:test-terminal-history"],
            evidence_refs=[],
        )

    read_model = build_mission_worker_read_model(
        store=store,
        orchestrator=orchestrator,
        configuration=_config(),
    )

    assert read_model.total_job_count == 33
    assert read_model.omitted_terminal_job_count == 1
    assert len(read_model.jobs) == 32
