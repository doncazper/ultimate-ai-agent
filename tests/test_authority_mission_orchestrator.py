from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path

import pytest

from tests.test_authority_dispatcher import (
    _constraints,
    _descriptor,
    _lease,
    _request,
)
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs.budgets import BudgetScope, CostBudget
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanConflictError,
    DurableMissionPlanCorruptionError,
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepDefinition,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationStatus,
    AuthorityMissionOrchestrationStepInput,
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


def _issue_mission_lease(
    state_dir: Path,
    *,
    mission_ref: str,
    operation_limit: int = 8,
):
    from ultimate_ai_agent.core.authority import AuthorityLeaseStore

    store = AuthorityLeaseStore(state_dir)
    lease, receipt = issue_authority_lease_with_test_approval(
        store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=mission_ref,
            requested_domains={AuthorityDomain.files: [AuthorityCapability.read]},
            authority_constraints=_constraints(operation_limit=operation_limit),
            decision_reason_ref="reason-ref:test-mission-orchestration-lease",
            safe_summary="Issue one exact mission-scoped orchestration test lease.",
        ),
        idempotency_ref="idempotency-ref:test-mission-orchestration-lease",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return store, lease


def _orchestration_fixture(
    tmp_path: Path,
    *,
    suffix: str,
    dependency_graph: list[list[int]] | None = None,
    mission_lease: bool = True,
    operation_limit: int = 8,
    shared_state: bool = False,
):
    authority_state = tmp_path / "authority"
    mission_state = authority_state if shared_state else tmp_path / "mission-state"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text(
        "sensitive body must not persist",
        encoding="utf-8",
    )
    mission_ref = f"mission-ref:test-orchestration:{suffix}"
    run_ref = f"run-ref:test-orchestration:{suffix}"
    plan_ref = f"mission-plan-ref:test-orchestration:{suffix}"
    if mission_lease:
        lease_store, lease = _issue_mission_lease(
            authority_state,
            mission_ref=mission_ref,
            operation_limit=operation_limit,
        )
    else:
        lease_store, lease = _lease(
            authority_state,
            mode=TrustMode.full_local_workspace_session,
            domain=AuthorityDomain.files,
            capability=AuthorityCapability.read,
            authority_constraints=_constraints(operation_limit=operation_limit),
        )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref="safe-root:test-authority",
                root_path=root,
                safe_label="Mission orchestrator safe root",
            )
        ],
    )
    dispatcher = AuthorityDispatcher(
        authority_state,
        adapters=[adapter],
        lease_store=lease_store,
    )
    step_store = MissionStepStore(mission_state)
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=step_store,
    )
    orchestrator = SynchronousAuthorityMissionOrchestrator(
        runner=runner,
        plan_store=DurableMissionPlanStore(mission_state),
    )
    deadline = utc_now() + timedelta(hours=1)
    dependencies = dependency_graph or [[], [0]]
    step_refs = [
        f"mission-step-ref:test-orchestration:{suffix}:{index}"
        for index in range(len(dependencies))
    ]
    steps: list[AuthorityMissionOrchestrationStepInput] = []
    for index, dependency_indexes in enumerate(dependencies):
        base = _request(
            lease.lease_ref,
            suffix=f"{suffix}-{index}",
            filesystem=True,
        )
        step_ref = step_refs[index]
        dispatch_ref = mission_step_dispatch_ref(step_ref)
        idempotency_ref = mission_step_idempotency_ref(step_ref)
        action = base.action_request.model_copy(
            update={
                "action_ref": mission_step_action_ref(step_ref),
                "resource_refs": [
                    *base.action_request.resource_refs,
                    mission_ref,
                ],
                "constraints": {
                    **base.action_request.constraints,
                    "mission_ref": mission_ref,
                },
            }
        )
        tool_request = {
            **base.tool_invocation_request,
            "invocation_id": dispatch_ref,
            "replay_key": idempotency_ref,
        }
        cost_budgets = [
            CostBudget(
                budget_id=f"cost-budget:test-orchestration:{suffix}:{index}",
                scope=BudgetScope.run,
                scope_id=run_ref,
                max_cost_usd=1,
                max_total_tokens=8,
            )
        ]
        request = base.model_copy(
            update={
                "dispatch_ref": dispatch_ref,
                "run_ref": run_ref,
                "idempotency_ref": idempotency_ref,
                "action_request": action,
                "tool_invocation_request": tool_request,
                "cost_budgets": cost_budgets,
                "cost_governor_decision_ref": (
                    build_authority_dispatch_cost_governor_decision_ref(
                        base.cost_estimate,
                        cost_budgets,
                    )
                ),
                "start_deadline": deadline,
            }
        )
        definition = MissionStepDefinition(
            mission_ref=mission_ref,
            run_ref=run_ref,
            step_ref=step_ref,
            capability_ref=request.action_request.capability_ref or "",
            adapter_ref=request.adapter_ref,
            lease_ref=request.lease_ref,
            dependency_step_refs=[
                (
                    step_refs[dependency_index]
                    if 0 <= dependency_index < len(step_refs)
                    else f"mission-step-ref:test-orchestration:{suffix}:missing"
                )
                for dependency_index in dependency_indexes
            ],
            deadline=deadline,
            safe_summary="Run one exact mission-bound filesystem metadata step.",
        )
        steps.append(
            AuthorityMissionOrchestrationStepInput(
                definition=definition,
                request=request,
            )
        )
    request = AuthorityMissionOrchestrationRequest(
        plan_ref=plan_ref,
        mission_ref=mission_ref,
        run_ref=run_ref,
        steps=steps,
        safe_summary="Run a bounded synchronous dependency-aware mission.",
    )
    return orchestrator, dispatcher, lease_store, lease, request, root


def test_two_step_mission_executes_in_topological_order_and_replays(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, root = _orchestration_fixture(
        tmp_path,
        suffix="success",
    )

    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:first",
    )
    second = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:replay",
    )

    assert first.status == AuthorityMissionOrchestrationStatus.succeeded.value
    assert first.evaluated_step_count == 2
    assert first.started_step_count == 2
    assert first.invoked_step_count == 2
    assert first.replayed_step_count == 0
    assert second.status == AuthorityMissionOrchestrationStatus.succeeded.value
    assert second.evaluated_step_count == 0
    assert second.started_step_count == 2
    assert second.invoked_step_count == 2
    assert second.replayed_step_count == 2
    assert first.execution_authority_minted_by_orchestrator is False
    assert first.request_scoped_authority_evaluated_for_each_attempted_step is True
    started = [
        receipt for receipt in dispatcher.list_receipts() if receipt.status == "started"
    ]
    assert [receipt.dispatch_ref for receipt in started] == [
        step.request.dispatch_ref for step in request.steps
    ]
    assert len(orchestrator.plan_store.list_receipts()) == 1
    durable_text = "".join(
        path.read_text(encoding="utf-8")
        for path in [
            orchestrator.plan_store.receipts_path,
            orchestrator.step_store.receipts_path,
            dispatcher.receipts_path,
        ]
    )
    assert str(root) not in durable_text
    assert "notes/report.md" not in durable_text
    assert "sensitive body" not in durable_text


def test_plan_and_later_request_drift_conflict_before_new_execution(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="drift",
    )
    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:drift-first",
    )
    assert first.status == AuthorityMissionOrchestrationStatus.succeeded.value
    started_before = len(
        [item for item in dispatcher.list_receipts() if item.status == "started"]
    )
    changed_step = request.steps[1].model_copy(
        update={
            "request": request.steps[1].request.model_copy(
                update={"safe_summary": "Changed but still safe request summary."}
            )
        }
    )
    drifted_requests = [
        request.model_copy(update={"steps": [request.steps[0], changed_step]}),
        request.model_copy(update={"steps": list(reversed(request.steps))}),
        request.model_copy(update={"steps": [request.steps[0]]}),
    ]
    for index, changed in enumerate(drifted_requests):
        with pytest.raises(
            DurableMissionPlanConflictError,
            match="DURABLE_MISSION_PLAN_IMMUTABLE_CONFLICT",
        ):
            orchestrator.run(
                changed,
                owner_ref=(
                    f"mission-owner-ref:test-orchestration:drift-second-{index}"
                ),
            )
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == started_before
    )


def test_partial_execution_still_rejects_later_request_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="partial-drift",
    )
    original_run_once = orchestrator.runner._run_orchestrated_once  # noqa: SLF001
    calls = [0]

    def run_once_then_interrupt(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise RuntimeError("synthetic interruption")
        return original_run_once(*args, **kwargs)

    monkeypatch.setattr(
        orchestrator.runner,
        "_run_orchestrated_once",
        run_once_then_interrupt,
    )
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test-orchestration:partial-first",
        )
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )
    changed_step = request.steps[1].model_copy(
        update={
            "request": request.steps[1].request.model_copy(
                update={"safe_summary": "Changed later request summary."}
            )
        }
    )
    changed = request.model_copy(update={"steps": [request.steps[0], changed_step]})
    with pytest.raises(DurableMissionPlanConflictError):
        orchestrator.run(
            changed,
            owner_ref="mission-owner-ref:test-orchestration:partial-second",
        )
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


@pytest.mark.parametrize(
    "dependencies",
    [
        [[1], [0]],
        [[], [2]],
    ],
)
def test_invalid_graph_fails_before_durable_mutation(
    tmp_path: Path,
    dependencies: list[list[int]],
) -> None:
    with pytest.raises(ValueError):
        _orchestration_fixture(
            tmp_path,
            suffix="invalid-graph",
            dependency_graph=dependencies,
        )
    assert not list(tmp_path.rglob("*mission_plan_receipts.jsonl"))
    assert not list(tmp_path.rglob("mission_step_receipts.jsonl"))


def test_session_lease_fails_preflight_before_plan_or_step_persistence(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="session-lease",
        mission_lease=False,
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_MISSION_LEASE_REQUIRED",
    ):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test-orchestration:session",
        )
    assert not orchestrator.plan_store.receipts_path.exists()
    assert not orchestrator.step_store.receipts_path.exists()
    assert dispatcher.list_receipts() == []


def test_dependent_step_cannot_bypass_durable_plan_through_runner(
    tmp_path: Path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="runner-plan-bypass",
    )

    with pytest.raises(
        ValueError,
        match="MISSION_RUNNER_DURABLE_PLAN_BINDING_REQUIRED",
    ):
        orchestrator.runner.validate_step(
            request.steps[1].definition,
            request.steps[1].request,
        )


def test_invalid_later_target_fails_full_preflight_before_first_execution(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="later-target-preflight",
    )
    invalid_tool_request = {
        **request.steps[1].request.tool_invocation_request,
        "metadata": {
            **request.steps[1].request.tool_invocation_request["metadata"],
            "relative_path": "../escape",
        },
    }
    invalid_second = request.steps[1].model_copy(
        update={
            "request": request.steps[1].request.model_copy(
                update={"tool_invocation_request": invalid_tool_request}
            )
        }
    )
    invalid_request = request.model_copy(
        update={"steps": [request.steps[0], invalid_second]}
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_STRUCTURAL_PREFLIGHT_DENIED",
    ):
        orchestrator.run(
            invalid_request,
            owner_ref="mission-owner-ref:test-orchestration:invalid-target",
        )
    assert not orchestrator.plan_store.receipts_path.exists()
    assert not orchestrator.step_store.receipts_path.exists()
    assert dispatcher.list_receipts() == []


def test_known_failure_blocks_descendants_and_halts_independent_steps(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="fail-fast",
        dependency_graph=[[], [0], [1], []],
        operation_limit=1,
    )

    first = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:failed",
    )
    replay = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:failed-replay",
    )

    assert first.status == AuthorityMissionOrchestrationStatus.failed.value
    assert [step.status for step in first.steps] == [
        MissionStepStatus.succeeded.value,
        MissionStepStatus.failed.value,
        MissionStepStatus.dependency_blocked.value,
        MissionStepStatus.fail_fast_halted.value,
    ]
    assert first.dependency_blocked_step_count == 1
    assert replay.status == AuthorityMissionOrchestrationStatus.failed.value
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


def test_lease_revocation_between_steps_is_rechecked_before_second_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, lease_store, lease, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="between-step-revocation",
    )
    original_run_once = orchestrator.runner._run_orchestrated_once  # noqa: SLF001
    calls = [0]

    def run_once_then_revoke(*args, **kwargs):
        result = original_run_once(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 1:
            lease_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=lease.lease_ref,
                    decision_reason_ref=(
                        "reason-ref:test-orchestration-between-step-revocation"
                    ),
                    safe_summary="Revoke mission lease after the first step.",
                ),
                idempotency_ref=(
                    "idempotency-ref:test-orchestration-between-step-revocation"
                ),
            )
        return result

    monkeypatch.setattr(
        orchestrator.runner,
        "_run_orchestrated_once",
        run_once_then_revoke,
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:between-step",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.failed.value
    assert [step.status for step in result.steps] == [
        MissionStepStatus.succeeded.value,
        MissionStepStatus.failed.value,
    ]
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


def test_concurrent_identical_orchestrators_start_each_step_at_most_once(
    tmp_path: Path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="concurrent",
    )

    def execute(owner_suffix: str):
        return orchestrator.run(
            request,
            owner_ref=f"mission-owner-ref:test-orchestration:{owner_suffix}",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(execute, ["concurrent-a", "concurrent-b"]))

    assert AuthorityMissionOrchestrationStatus.succeeded.value in {
        result.status for result in results
    }
    started = [
        receipt for receipt in dispatcher.list_receipts() if receipt.status == "started"
    ]
    assert len(started) == 2
    assert len({receipt.dispatch_ref for receipt in started}) == 2


def test_atomic_start_deadline_blocks_adapter_after_runner_precheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="atomic-deadline",
    )
    expired_time = request.steps[0].definition.deadline + timedelta(seconds=1)
    monkeypatch.setattr(
        "ultimate_ai_agent.core.authority.dispatcher.utc_now",
        lambda: expired_time,
    )

    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:deadline",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.failed.value
    assert all(item.status != "started" for item in dispatcher.list_receipts())
    assert any(
        "start-deadline-expired" in reason
        for receipt in dispatcher.list_receipts()
        for reason in receipt.reason_refs
    )


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO is POSIX-only")
def test_plan_ledger_symlink_and_fifo_fail_closed(tmp_path: Path) -> None:
    symlink_state = tmp_path / "symlink-state"
    symlink_state.mkdir()
    symlink_store = DurableMissionPlanStore(symlink_state)
    symlink_store.receipts_path.symlink_to(tmp_path / "missing-plan-ledger")
    with pytest.raises(DurableMissionPlanCorruptionError):
        symlink_store.list_receipts()

    fifo_state = tmp_path / "fifo-state"
    fifo_state.mkdir()
    fifo_store = DurableMissionPlanStore(fifo_state)
    os.mkfifo(fifo_store.receipts_path)
    with pytest.raises(DurableMissionPlanCorruptionError):
        fifo_store.list_receipts()


def test_manifest_truth_declares_backend_and_blocks_external_execution() -> None:
    from ultimate_ai_agent.api.app import app
    from ultimate_ai_agent.api.manifest import build_api_manifest

    manifest = build_api_manifest(app).model_dump(mode="json")
    assert (
        "authority_mission_synchronous_dependency_orchestration_backend"
        in manifest["capabilities_declared"]
    )
    assert "authority_mission_local_worker_v1" in manifest["capabilities_declared"]
    for capability in [
        "authority_mission_orchestration_api_cli_ui_execution",
        "authority_mission_orchestration_parallel_worker",
        "authority_mission_worker_remote_queue_or_public_daemon",
        "authority_mission_orchestration_automatic_retry_or_approval_wait",
        "authority_mission_orchestration_mission_level_cancellation",
    ]:
        assert capability in manifest["capabilities_blocked"]
