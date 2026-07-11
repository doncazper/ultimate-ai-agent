from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_authority_dispatcher import _descriptor, _lease, _request
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseRevokeRequest,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepDefinition,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


def _runner_request(tmp_path: Path, suffix: str = "success"):
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text(
        "raw mission body must not persist",
        encoding="utf-8",
    )
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref="safe-root:test-authority",
                root_path=root,
                safe_label="Mission runner safe root",
            )
        ],
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    base = _request(lease.lease_ref, suffix=suffix, filesystem=True)
    step_ref = f"mission-step-ref:test:{suffix}"
    dispatch_ref = mission_step_dispatch_ref(step_ref)
    idempotency_ref = mission_step_idempotency_ref(step_ref)
    action = base.action_request.model_copy(
        update={"action_ref": mission_step_action_ref(step_ref)}
    )
    tool = {
        **base.tool_invocation_request,
        "invocation_id": dispatch_ref,
        "replay_key": idempotency_ref,
    }
    request = base.model_copy(
        update={
            "dispatch_ref": dispatch_ref,
            "idempotency_ref": idempotency_ref,
            "action_request": action,
            "tool_invocation_request": tool,
        }
    )
    definition = MissionStepDefinition(
        mission_ref=f"mission-ref:test:{suffix}",
        run_ref=request.run_ref,
        step_ref=step_ref,
        capability_ref=request.action_request.capability_ref or "",
        adapter_ref=request.adapter_ref,
        lease_ref=request.lease_ref,
        deadline=utc_now().replace(year=utc_now().year + 1),
        safe_summary="Run one exact filesystem metadata mission step.",
    )
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(tmp_path / "mission-steps"),
    )
    return runner, dispatcher, lease_store, lease, definition, request, root


def test_exact_filesystem_metadata_mission_succeeds_and_replays(tmp_path: Path) -> None:
    runner, dispatcher, _, _, definition, request, root = _runner_request(tmp_path)

    first = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:first",
    )
    second = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:second",
    )

    assert first.step.status == MissionStepStatus.succeeded.value
    assert first.dispatch_result is not None
    assert first.dispatch_result.receipt.adapter_invocation_performed is True
    assert first.execution_authority_minted_by_runner is False
    assert second.replayed_terminal_step is True
    assert second.dispatch_result is None
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )
    ledger = runner.step_store.receipts_path.read_text(encoding="utf-8")
    assert str(root) not in ledger
    assert "notes/report.md" not in ledger
    assert "raw mission body" not in ledger


def test_revoked_lease_fails_before_adapter_invocation(tmp_path: Path) -> None:
    runner, dispatcher, lease_store, lease, definition, request, _ = _runner_request(
        tmp_path,
        "revoked",
    )
    lease_store.revoke_lease(
        AuthorityLeaseRevokeRequest(
            lease_ref=lease.lease_ref,
            decision_reason_ref="reason-ref:test:mission-lease-revoked",
            safe_summary="Revoke mission runner test lease.",
        ),
        idempotency_ref="idempotency-ref:test:mission-lease-revoked",
    )

    result = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:revoked",
    )

    assert result.step.status == MissionStepStatus.failed.value
    assert result.dispatch_result is not None
    assert result.dispatch_result.receipt.adapter_invocation_performed is False
    assert all(item.status != "started" for item in dispatcher.list_receipts())


def test_deadline_expiry_after_prepare_cancels_before_adapter_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, dispatcher, _, _, definition, request, _ = _runner_request(
        tmp_path,
        "deadline-after-prepare",
    )
    current = [utc_now()]
    definition = definition.model_copy(
        update={"deadline": current[0] + timedelta(seconds=10)}
    )
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            tmp_path / "deadline-mission-steps",
            clock=lambda: current[0],
        ),
    )
    original_prepare = dispatcher.prepare

    def prepare_then_expire(request_value):
        prepared = original_prepare(request_value)
        current[0] = definition.deadline + timedelta(seconds=1)
        return prepared

    monkeypatch.setattr(dispatcher, "prepare", prepare_then_expire)
    result = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:deadline",
    )

    assert result.step.status == MissionStepStatus.failed.value
    assert result.dispatch_result is not None
    assert result.dispatch_result.receipt.status == "cancelled_before_start"
    assert all(item.status != "started" for item in dispatcher.list_receipts())
    assert any(
        receipt.status == "released"
        for receipt in dispatcher.budget_store.list_receipts()
    )


def test_deadline_cancellation_race_preserves_concurrent_success_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, dispatcher, _, _, definition, request, _ = _runner_request(
        tmp_path,
        "deadline-success-race",
    )
    current = [utc_now()]
    definition = definition.model_copy(
        update={"deadline": current[0] + timedelta(seconds=10)}
    )
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            tmp_path / "deadline-success-race-steps",
            clock=lambda: current[0],
        ),
    )
    original_prepare = dispatcher.prepare
    original_cancel = dispatcher.cancel

    def prepare_then_expire(request_value):
        prepared = original_prepare(request_value)
        current[0] = definition.deadline + timedelta(seconds=1)
        return prepared

    def execute_elsewhere_then_cancel(cancel_request):
        dispatcher.execute(request)
        return original_cancel(cancel_request)

    monkeypatch.setattr(dispatcher, "prepare", prepare_then_expire)
    monkeypatch.setattr(dispatcher, "cancel", execute_elsewhere_then_cancel)
    result = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:deadline-success-race",
    )

    assert result.step.status == MissionStepStatus.succeeded.value
    assert result.dispatch_result is not None
    assert result.dispatch_result.receipt.status == "succeeded"
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


def test_restart_replays_terminal_dispatch_without_second_adapter_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, dispatcher, lease_store, _, definition, request, _ = _runner_request(
        tmp_path,
        "restart-replay",
    )
    current = [utc_now()]
    definition = definition.model_copy(
        update={"deadline": current[0] + timedelta(seconds=1)}
    )
    mission_state_dir = tmp_path / "restart-mission-steps"
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )

    def crash_before_step_terminal(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated crash before mission step terminal receipt")

    monkeypatch.setattr(runner.step_store, "complete", crash_before_step_terminal)
    with pytest.raises(RuntimeError, match="simulated crash"):
        runner.run_once(
            definition,
            request,
            owner_ref="mission-owner-ref:test:crashed",
            claim_ttl_seconds=1,
        )

    current[0] += timedelta(seconds=2)
    restarted_dispatcher = AuthorityDispatcher(
        dispatcher.state_dir,
        adapters=list(dispatcher.adapters.values()),
        lease_store=lease_store,
    )
    restarted_runner = AuthorityMissionRunner(
        dispatcher=restarted_dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )
    recovered = restarted_runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:recovery",
        claim_ttl_seconds=30,
    )

    assert recovered.step.status == MissionStepStatus.succeeded.value
    assert recovered.replayed_terminal_step is True
    assert recovered.dispatch_result is not None
    assert recovered.dispatch_result.replayed is True
    assert (
        len(
            [
                item
                for item in restarted_dispatcher.list_receipts()
                if item.status == "started"
            ]
        )
        == 1
    )


def test_restart_after_prepared_deadline_cancels_and_releases_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, dispatcher, lease_store, _, definition, request, _ = _runner_request(
        tmp_path,
        "prepared-deadline-restart",
    )
    current = [utc_now()]
    definition = definition.model_copy(
        update={"deadline": current[0] + timedelta(seconds=1)}
    )
    mission_state_dir = tmp_path / "prepared-deadline-mission-steps"
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )
    original_prepare = dispatcher.prepare

    def prepare_then_crash(request_value):
        original_prepare(request_value)
        raise RuntimeError("simulated crash after durable prepare")

    monkeypatch.setattr(dispatcher, "prepare", prepare_then_crash)
    with pytest.raises(RuntimeError, match="simulated crash"):
        runner.run_once(
            definition,
            request,
            owner_ref="mission-owner-ref:test:prepared-crash",
            claim_ttl_seconds=1,
        )

    current[0] += timedelta(seconds=2)
    restarted_dispatcher = AuthorityDispatcher(
        dispatcher.state_dir,
        adapters=list(dispatcher.adapters.values()),
        lease_store=lease_store,
    )
    restarted_runner = AuthorityMissionRunner(
        dispatcher=restarted_dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )
    recovered = restarted_runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:prepared-deadline-recovery",
    )

    assert recovered.step.status == MissionStepStatus.failed.value
    assert recovered.dispatch_result is not None
    assert recovered.dispatch_result.receipt.status == "cancelled_before_start"
    assert all(
        item.status != "started" for item in restarted_dispatcher.list_receipts()
    )
    assert any(
        receipt.status == "released"
        for receipt in restarted_dispatcher.budget_store.list_receipts()
    )
    assert restarted_runner.step_store.read(definition.step_ref).status == "failed"


def test_reclaimer_cannot_change_request_after_durable_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, dispatcher, _, _, definition, request, _ = _runner_request(
        tmp_path,
        "intent-fingerprint",
    )
    current = [utc_now()]
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            tmp_path / "intent-mission-steps",
            clock=lambda: current[0],
        ),
    )
    original_prepare = dispatcher.prepare

    def crash_before_dispatch_prepare(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated crash before dispatcher prepare")

    monkeypatch.setattr(dispatcher, "prepare", crash_before_dispatch_prepare)
    with pytest.raises(RuntimeError, match="simulated crash"):
        runner.run_once(
            definition,
            request,
            owner_ref="mission-owner-ref:test:intent-first",
            claim_ttl_seconds=1,
        )

    monkeypatch.setattr(dispatcher, "prepare", original_prepare)
    current[0] += timedelta(seconds=2)
    drifted = request.model_copy(
        update={"safe_summary": "Change the exact request after durable intent."}
    )
    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT",
    ):
        runner.run_once(
            definition,
            drifted,
            owner_ref="mission-owner-ref:test:intent-reclaimer",
        )
    recovered = runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:intent-valid-recovery",
    )
    assert recovered.step.status == MissionStepStatus.succeeded.value
    assert recovered.step.generation == 2
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


def test_restart_after_durable_start_requires_recovery_without_reinvoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, dispatcher, lease_store, _, definition, request, _ = _runner_request(
        tmp_path,
        "started-crash",
    )
    current = [utc_now()]
    mission_state_dir = tmp_path / "started-crash-mission-steps"
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )
    original_append = dispatcher._append  # noqa: SLF001

    def append_started_then_crash(receipt) -> None:
        original_append(receipt)
        if receipt.status == "started":
            raise RuntimeError("simulated crash after durable adapter start")

    monkeypatch.setattr(dispatcher, "_append", append_started_then_crash)
    with pytest.raises(RuntimeError, match="simulated crash"):
        runner.run_once(
            definition,
            request,
            owner_ref="mission-owner-ref:test:started-crash",
            claim_ttl_seconds=1,
        )

    current[0] += timedelta(seconds=2)
    restarted_dispatcher = AuthorityDispatcher(
        dispatcher.state_dir,
        adapters=list(dispatcher.adapters.values()),
        lease_store=lease_store,
    )
    restarted_runner = AuthorityMissionRunner(
        dispatcher=restarted_dispatcher,
        step_store=MissionStepStore(
            mission_state_dir,
            clock=lambda: current[0],
        ),
    )
    recovered = restarted_runner.run_once(
        definition,
        request,
        owner_ref="mission-owner-ref:test:started-recovery",
    )

    assert recovered.step.status == MissionStepStatus.recovery_required.value
    assert recovered.dispatch_result is not None
    assert recovered.dispatch_result.recovery_required is True
    receipts = restarted_dispatcher.list_receipts()
    assert len([item for item in receipts if item.status == "started"]) == 1
    assert all(item.status not in {"succeeded", "failed"} for item in receipts)


def test_runner_rejects_non_filesystem_and_binding_drift_before_claim(
    tmp_path: Path,
) -> None:
    runner, _, _, _, definition, request, _ = _runner_request(tmp_path, "drift")
    drifted = request.model_copy(
        update={"dispatch_ref": "authority-dispatch-ref:test:caller-selected"}
    )

    with pytest.raises(ValueError, match="MISSION_RUNNER_DISPATCH_BINDING_INVALID"):
        runner.run_once(
            definition,
            drifted,
            owner_ref="mission-owner-ref:test:drift",
        )
    assert not runner.step_store.receipts_path.exists()


def test_runner_rejects_governed_noop_adapter(tmp_path: Path) -> None:
    state_dir = tmp_path / "authority"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    base = _request(lease.lease_ref, suffix="noop", filesystem=False)
    step_ref = "mission-step-ref:test:noop"
    dispatch_ref = mission_step_dispatch_ref(step_ref)
    idempotency_ref = mission_step_idempotency_ref(step_ref)
    request = base.model_copy(
        update={
            "dispatch_ref": dispatch_ref,
            "idempotency_ref": idempotency_ref,
            "action_request": base.action_request.model_copy(
                update={"action_ref": mission_step_action_ref(step_ref)}
            ),
            "tool_invocation_request": {
                **base.tool_invocation_request,
                "invocation_id": dispatch_ref,
                "replay_key": idempotency_ref,
            },
        }
    )
    definition = MissionStepDefinition(
        mission_ref="mission-ref:test:noop",
        run_ref=request.run_ref,
        step_ref=step_ref,
        capability_ref=request.action_request.capability_ref or "",
        adapter_ref=request.adapter_ref,
        lease_ref=request.lease_ref,
        deadline=utc_now().replace(year=utc_now().year + 1),
        safe_summary="Reject a non-filesystem mission runner adapter.",
    )
    runner = AuthorityMissionRunner(
        dispatcher=dispatcher,
        step_store=MissionStepStore(tmp_path / "mission-steps"),
    )

    with pytest.raises(
        ValueError, match="MISSION_RUNNER_EXACT_FILESYSTEM_LANE_REQUIRED"
    ):
        runner.run_once(
            definition,
            request,
            owner_ref="mission-owner-ref:test:noop",
        )


def test_runner_source_has_no_registry_or_direct_adapter_invocation() -> None:
    source = Path("src/ultimate_ai_agent/core/execution/mission_runner.py").read_text(
        encoding="utf-8"
    )

    assert "CapabilityRegistry" not in source
    assert "registry.invoke" not in source
    assert "adapter.invoke" not in source
    assert "evaluate_tool_invocation" not in source
