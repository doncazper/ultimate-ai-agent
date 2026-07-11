from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchAdapterResult,
    AuthorityDispatchFailureCategory,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepStatus,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationStepInput,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerRequestResolver,
    MissionWorkerStore,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)


def _retry_fixture(
    tmp_path: Path,
    *,
    suffix: str,
    backoff_seconds: int = 0,
    bind_retry_lease: bool = True,
):
    orchestrator, dispatcher, lease_store, lease, request, _ = (
        _orchestration_fixture(
            tmp_path,
            suffix=suffix,
            dependency_graph=[[]],
            shared_state=True,
        )
    )
    if bind_retry_lease:
        retry_constraint = AuthorityConstraint(
            constraint_ref=f"authority-constraint-ref:test-retry:{suffix}",
            kind=AuthorityConstraintKind.retry_attempts,
            maximum=2,
            safe_summary="Allow at most two prebound mission attempts.",
        )
        updated_lease = lease.model_copy(
            update={
                "authority_constraints": [
                    *lease.authority_constraints,
                    retry_constraint,
                ]
            }
        )
        with lease_store.lock_manager.acquire("authority-state"):
            lease_store._write_leases([updated_lease])  # noqa: SLF001
    adapter = next(iter(dispatcher.adapters.values()))
    adapter._descriptor = adapter.descriptor.model_copy(  # noqa: SLF001
        update={"idempotent_replay_supported": True}
    )
    step = request.steps[0]
    retry_claim = AuthorityConstraintClaim(
        kind=AuthorityConstraintKind.retry_attempts,
        value=2,
    )
    action = step.request.action_request.model_copy(
        update={
            "constraint_claims": [
                *step.request.action_request.constraint_claims,
                retry_claim,
            ]
        }
    )
    first_request = step.request.model_copy(update={"action_request": action})
    retry_dispatch_ref = mission_step_dispatch_ref(step.definition.step_ref, 2)
    retry_idempotency_ref = mission_step_idempotency_ref(
        step.definition.step_ref,
        2,
    )
    retry_request = first_request.model_copy(
        update={
            "dispatch_ref": retry_dispatch_ref,
            "idempotency_ref": retry_idempotency_ref,
            "action_request": action.model_copy(
                update={
                    "action_ref": mission_step_action_ref(
                        step.definition.step_ref,
                        2,
                    )
                }
            ),
            "tool_invocation_request": {
                **first_request.tool_invocation_request,
                "invocation_id": retry_dispatch_ref,
                "replay_key": retry_idempotency_ref,
            },
        }
    )
    definition = step.definition.model_copy(
        update={
            "max_attempts": 2,
            "retryable_failure_categories": [
                AuthorityDispatchFailureCategory.transient_adapter_error
            ],
            "retry_backoff_seconds": backoff_seconds,
        }
    )
    retry_step = AuthorityMissionOrchestrationStepInput(
        definition=definition,
        request=first_request,
        retry_requests=[retry_request],
    )
    retry_mission = AuthorityMissionOrchestrationRequest(
        plan_ref=request.plan_ref,
        mission_ref=request.mission_ref,
        run_ref=request.run_ref,
        steps=[retry_step],
        safe_summary=request.safe_summary,
        automatic_retry_requested=True,
    )
    return orchestrator, dispatcher, adapter, retry_mission


def _transient_failure(
    result: AuthorityDispatchAdapterResult,
) -> AuthorityDispatchAdapterResult:
    return result.model_copy(
        update={
            "succeeded": False,
            "failure_category": (
                AuthorityDispatchFailureCategory.transient_adapter_error
            ),
            "safe_summary": "Retryable adapter failure was classified safely.",
        }
    )


class _Resolver(MissionWorkerRequestResolver):
    def __init__(self, request: AuthorityMissionOrchestrationRequest) -> None:
        self.request = request

    def resolve(self, _binding):
        return self.request


def _worker_config() -> LocalMissionWorkerConfiguration:
    with patch("platform.system", return_value="Darwin"):
        return LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
        )


def test_typed_idempotent_failure_retries_once_then_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, adapter, request = _retry_fixture(
        tmp_path,
        suffix="retry-success",
    )
    original_invoke = adapter.invoke
    call_count = 0

    def fail_once(dispatch_request):
        nonlocal call_count
        call_count += 1
        result = original_invoke(dispatch_request)
        return _transient_failure(result) if call_count == 1 else result

    monkeypatch.setattr(adapter, "invoke", fail_once)

    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-success:first",
    )
    second = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-success:second",
    )

    assert first.status == "waiting_for_retry"
    assert first.retry_pending_step_count == 1
    assert second.status == "succeeded"
    assert second.steps[0].attempt_no == 2
    assert second.automatic_retry_performed is True
    assert call_count == 2
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 2


def test_retry_backoff_releases_claim_and_blocks_early_reentry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, adapter, request = _retry_fixture(
        tmp_path,
        suffix="retry-backoff",
        backoff_seconds=60,
    )
    original_invoke = adapter.invoke
    monkeypatch.setattr(
        adapter,
        "invoke",
        lambda dispatch_request: _transient_failure(
            original_invoke(dispatch_request)
        ),
    )

    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-backoff:first",
    )
    replay = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-backoff:early",
    )

    assert first.status == replay.status == "waiting_for_retry"
    assert first.steps[0].owner_ref is None
    assert first.steps[0].claim_ref is None
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 1


def test_exhausted_retry_is_dead_lettered_and_never_auto_replays(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, adapter, request = _retry_fixture(
        tmp_path,
        suffix="retry-dead-letter",
    )
    original_invoke = adapter.invoke
    monkeypatch.setattr(
        adapter,
        "invoke",
        lambda dispatch_request: _transient_failure(
            original_invoke(dispatch_request)
        ),
    )

    orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-dead-letter:first",
    )
    dead_lettered = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-dead-letter:second",
    )
    replay = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test:retry-dead-letter:replay",
    )

    assert dead_lettered.status == replay.status == "failed"
    assert dead_lettered.steps[0].status == MissionStepStatus.dead_lettered.value
    assert dead_lettered.dead_letter_step_count == 1
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 2


def test_retry_without_exact_lease_constraint_fails_before_mutation(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, request = _retry_fixture(
        tmp_path,
        suffix="retry-no-lease",
        bind_retry_lease=False,
    )

    with pytest.raises(
        ValueError,
        match="RETRY_LEASE_REQUIRED",
    ):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test:retry-no-lease",
        )

    assert orchestrator.plan_store.list_receipts() == []
    assert dispatcher.list_receipts() == []


def test_worker_retry_releases_claim_and_resumes_through_dispatcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, adapter, request = _retry_fixture(
        tmp_path,
        suffix="retry-worker",
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=_worker_config(),
    )
    original_invoke = adapter.invoke
    call_count = 0

    def fail_once(dispatch_request):
        nonlocal call_count
        call_count += 1
        result = original_invoke(dispatch_request)
        return _transient_failure(result) if call_count == 1 else result

    monkeypatch.setattr(adapter, "invoke", fail_once)

    waiting = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:retry-worker:first",
    )
    resumed = worker.resume_next(
        _Resolver(request),
        worker_ref="mission-worker-ref:test:retry-worker:second",
    )

    assert waiting is not None and waiting.status == "waiting_for_retry"
    assert resumed is not None and resumed.status == "succeeded"
    assert worker.store.latest()[0].status == MissionWorkerJobStatus.succeeded.value
    assert call_count == 2
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 2
