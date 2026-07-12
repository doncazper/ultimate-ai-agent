from datetime import timedelta
import hashlib
import json

import pytest
from pydantic import ValidationError

from tests.test_authority_dispatcher import _constraints, _descriptor, _lease, _request
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.authority.contracts import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
)
from ultimate_ai_agent.core.execution import durable_mission_plans as plan_module
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlan,
    DurableMissionPlanCorruptionError,
    DurableMissionPlanStepBinding,
    DurableMissionPlanStore,
    _entry_hash as plan_entry_hash,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepCorruptionError,
    MissionStepDefinition,
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationStatus,
)
from ultimate_ai_agent.core.time import utc_now


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _short_ref(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical(value).encode()).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


def _full_ref(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical(value).encode()).hexdigest()
    return f"{prefix}:sha256:{digest}"


def test_plan_bound_direct_runner_requires_prior_accepted_membership(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="plan-first",
    )
    first = request.steps[0]
    bound = request.bound_definition(first)

    with pytest.raises(
        ValueError,
        match="MISSION_RUNNER_ORCHESTRATED_ENTRYPOINT_REQUIRED",
    ):
        orchestrator.runner.run_once(
            bound,
            first.request,
            owner_ref="mission-owner-ref:test-orchestration:plan-first-direct",
        )

    assert orchestrator.plan_store.list_receipts() == []
    assert orchestrator.step_store.receipts() == []
    assert dispatcher.list_receipts() == []
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:plan-first-accepted",
    )
    assert result.status == AuthorityMissionOrchestrationStatus.succeeded.value
    assert result.replayed_step_count == 0


def test_accepted_plan_reserves_step_refs_from_unbound_runner(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="accepted-plan-reservation",
    )
    orchestrator.plan_store.accept(request.build_durable_plan())
    first = request.steps[0]

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_REF_RESERVED_BY_ACCEPTED_PLAN",
    ):
        orchestrator.runner.run_once(
            first.definition,
            first.request,
            owner_ref="mission-owner-ref:test-orchestration:unbound-reserved-step",
        )

    assert orchestrator.step_store.receipts() == []
    assert dispatcher.list_receipts() == []


def test_atomic_plan_claim_rejects_direct_start_after_terminal_failure(
    tmp_path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="claim-fail-fast",
        dependency_graph=[[], []],
    )
    plan = request.build_durable_plan()
    definitions = [request.bound_definition(step) for step in request.steps]
    orchestrator.plan_store.accept(plan)
    orchestrator.step_store._materialize_definitions_under_orchestration_lock(  # noqa: SLF001
        definitions
    )
    context = orchestrator.plan_store.resolve_definition_binding(definitions[0])
    assert context is not None
    claim = orchestrator.step_store.claim(
        definitions[0].step_ref,
        owner_ref="mission-owner-ref:test-orchestration:claim-fail-fast-source",
        ttl_seconds=30,
        dispatch_ref=definitions[0].planned_dispatch_ref,
        dispatch_request_fingerprint_ref=(
            definitions[0].planned_dispatch_request_fingerprint_ref
        ),
        orchestration_context=context,
    )
    orchestrator.step_store.complete(
        definitions[0].step_ref,
        owner_ref=claim.owner_ref or "",
        claim_ref=claim.claim_ref or "",
        generation=claim.generation,
        status=MissionStepStatus.recovery_required,
        reason_refs=["reason-ref:mission-step:dispatch-reconciliation-failed"],
    )

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_FAIL_FAST_ACTIVE",
    ):
        orchestrator.runner._run_orchestrated_once(  # noqa: SLF001
            definitions[1],
            request.steps[1].request,
            owner_ref="mission-owner-ref:test-orchestration:claim-fail-fast-target",
            claim_ttl_seconds=30,
            orchestration_context=context,
        )
    assert dispatcher.list_receipts() == []


def test_conflicting_legacy_mission_scope_metadata_is_rejected(tmp_path) -> None:
    _, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="mission-scope-conflict",
    )
    first = request.steps[0]
    conflicting_action = first.request.action_request.model_copy(
        update={
            "constraints": {
                **first.request.action_request.constraints,
                "mission_ref": "mission-ref:test-orchestration:other",
            }
        }
    )
    conflicting_step = first.model_copy(
        update={
            "request": first.request.model_copy(
                update={"action_request": conflicting_action}
            )
        }
    )

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_ACTION_MISSION_SCOPE_CONFLICT",
    ):
        type(request).model_validate(
            request.model_copy(
                update={"steps": [conflicting_step, request.steps[1]]}
            ).model_dump(mode="python")
        )


def test_conflicting_existing_step_does_not_strand_new_plan(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="preflight-conflict",
    )
    conflicting = request.steps[1].definition.model_copy(
        update={"safe_summary": "Conflicting but safe standalone definition."}
    )
    orchestrator.step_store.create(conflicting)

    with pytest.raises(
        MissionStepConflictError,
        match="MISSION_STEP_DEFINITION_CONFLICT",
    ):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test-orchestration:preflight-conflict",
        )

    assert orchestrator.plan_store.list_receipts() == []
    assert dispatcher.list_receipts() == []


def test_later_policy_ineligible_lease_is_denied_before_any_start(tmp_path) -> None:
    orchestrator, dispatcher, lease_store, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="policy-preflight",
    )
    wrong_lease, receipt = issue_authority_lease_with_test_approval(
        lease_store,
        AuthorityLeaseIssueRequest(
            mode=TrustMode.delegated_mission_autonomous_window,
            scope=AuthorityLeaseScope.mission,
            mission_ref=request.mission_ref,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.execute]
            },
            authority_constraints=_constraints(operation_limit=8),
            decision_reason_ref="reason-ref:test-orchestration-policy-preflight",
            safe_summary="Issue an exact but policy-ineligible mission lease.",
        ),
        idempotency_ref="idempotency-ref:test-orchestration-policy-preflight",
    )
    assert wrong_lease is not None
    assert receipt.status == "issued"
    second = request.steps[1]
    changed_second = second.model_copy(
        update={
            "definition": second.definition.model_copy(
                update={"lease_ref": wrong_lease.lease_ref}
            ),
            "request": second.request.model_copy(
                update={"lease_ref": wrong_lease.lease_ref}
            ),
        }
    )
    changed = request.model_copy(update={"steps": [request.steps[0], changed_second]})

    with pytest.raises(
        ValueError,
        match="AUTHORITY_MISSION_ORCHESTRATION_POLICY_PREFLIGHT_DENIED",
    ):
        orchestrator.run(
            changed,
            owner_ref="mission-owner-ref:test-orchestration:policy-preflight",
        )
    assert dispatcher.list_receipts() == []


def test_deadline_is_rechecked_at_persisted_start_boundary(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="sequenced-deadline",
    )
    deadline = request.steps[0].definition.deadline
    current = [deadline - timedelta(microseconds=1)]
    monkeypatch.setattr(
        "ultimate_ai_agent.core.authority.dispatcher.utc_now",
        lambda: current[0],
    )
    original = dispatcher._prestart_reason_refs

    def pass_initial_boundary(*args, **kwargs):
        reasons = original(*args, **kwargs)
        current[0] = deadline + timedelta(microseconds=1)
        return reasons

    monkeypatch.setattr(dispatcher, "_prestart_reason_refs", pass_initial_boundary)
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:sequenced-deadline",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.failed.value
    assert result.started_step_count == 0
    assert result.invoked_step_count == 0
    assert all(not receipt.execution_started for receipt in dispatcher.list_receipts())


def test_supplied_child_first_still_executes_stable_topological_order(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="child-first",
    )
    reordered = request.model_copy(update={"steps": list(reversed(request.steps))})
    result = orchestrator.run(
        reordered,
        owner_ref="mission-owner-ref:test-orchestration:child-first",
    )

    started = [
        receipt.dispatch_ref
        for receipt in dispatcher.list_receipts()
        if receipt.status == "started"
    ]
    assert result.status == AuthorityMissionOrchestrationStatus.succeeded.value
    assert started == [
        request.steps[0].request.dispatch_ref,
        request.steps[1].request.dispatch_ref,
    ]


def test_multi_branch_success_and_partial_crash_resume(tmp_path, monkeypatch) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="multi-branch-resume",
        dependency_graph=[[], [0], [0], [1, 2]],
    )
    original = orchestrator.runner._run_orchestrated_once  # noqa: SLF001
    calls = [0]

    def interrupt_before_second(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise RuntimeError("synthetic crash before second step")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        orchestrator.runner,
        "_run_orchestrated_once",
        interrupt_before_second,
    )
    with pytest.raises(RuntimeError, match="synthetic crash"):
        orchestrator.run(
            request,
            owner_ref="mission-owner-ref:test-orchestration:multi-branch-crash",
        )
    monkeypatch.setattr(orchestrator.runner, "_run_orchestrated_once", original)
    resumed = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:multi-branch-resume",
    )

    assert resumed.status == AuthorityMissionOrchestrationStatus.succeeded.value
    assert resumed.replayed_step_count == 1
    started = [item for item in dispatcher.list_receipts() if item.status == "started"]
    assert len(started) == 4
    assert len({item.dispatch_ref for item in started}) == 4


def test_concurrent_terminal_failure_is_rescanned_before_next_step(
    tmp_path,
    monkeypatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="rescan-fail-fast",
        dependency_graph=[[], [], []],
    )
    original = orchestrator.runner._run_orchestrated_once  # noqa: SLF001
    calls = [0]

    def terminalize_later_step(*args, **kwargs):
        result = original(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 1:
            later = request.bound_definition(request.steps[2])
            context = orchestrator.plan_store.resolve_definition_binding(later)
            assert context is not None
            claim = orchestrator.step_store.claim(
                later.step_ref,
                owner_ref="mission-owner-ref:test-orchestration:rescan-later",
                ttl_seconds=30,
                dispatch_ref=later.planned_dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    later.planned_dispatch_request_fingerprint_ref
                ),
                orchestration_context=context,
            )
            orchestrator.step_store.complete(
                later.step_ref,
                owner_ref=claim.owner_ref or "",
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
                status=MissionStepStatus.recovery_required,
                reason_refs=["reason-ref:mission-step:dispatch-reconciliation-failed"],
            )
        return result

    monkeypatch.setattr(
        orchestrator.runner,
        "_run_orchestrated_once",
        terminalize_later_step,
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:rescan",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.recovery_required.value
    assert [step.status for step in result.steps] == [
        "succeeded",
        "fail_fast_halted",
        "recovery_required",
    ]
    assert result.started_step_count == 1
    assert (
        len([item for item in dispatcher.list_receipts() if item.status == "started"])
        == 1
    )


def test_cumulative_operation_budget_blocks_later_step(tmp_path) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="operation-budget",
        operation_limit=1,
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:operation-budget",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.failed.value
    assert [step.status for step in result.steps] == ["succeeded", "failed"]
    assert result.started_step_count == 1
    assert result.invoked_step_count == 1


def test_kill_switch_between_steps_blocks_next_start(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="between-step-kill-switch",
    )
    original = orchestrator.runner._run_orchestrated_once  # noqa: SLF001
    calls = [0]

    def run_once_then_engage(*args, **kwargs):
        result = original(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 1:
            monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "1")
        return result

    monkeypatch.setattr(
        orchestrator.runner,
        "_run_orchestrated_once",
        run_once_then_engage,
    )
    result = orchestrator.run(
        request,
        owner_ref="mission-owner-ref:test-orchestration:between-step-kill-switch",
    )

    assert result.status == AuthorityMissionOrchestrationStatus.failed.value
    assert result.started_step_count == 1
    assert result.invoked_step_count == 1


def test_legacy_mission_step_payload_remains_readable_and_replayable(tmp_path) -> None:
    store = MissionStepStore(tmp_path)
    definition = MissionStepDefinition(
        mission_ref="mission-ref:test:legacy-step",
        run_ref="run-ref:test:legacy-step",
        step_ref="mission-step-ref:test:legacy-step",
        capability_ref="authority-capability-ref:filesystem-metadata-v1",
        adapter_ref="authority-adapter-ref:filesystem-metadata-v1",
        lease_ref="authority-lease-ref:test:legacy-step",
        deadline=utc_now() + timedelta(minutes=5),
        safe_summary="Load one safe legacy mission step receipt.",
    )
    store.create(definition)
    payload = json.loads(store.receipts_path.read_text(encoding="utf-8"))
    legacy_definition = payload["definition"]
    for field_name in ("orchestration_plan_ref", "planned_dispatch_ref", "planned_dispatch_request_fingerprint_ref"):  # noqa: E501
        legacy_definition.pop(field_name)
    for field_name in ("retryable_failure_categories", "retry_backoff_seconds", "planned_retry_attempts"):  # noqa: E501
        legacy_definition.pop(field_name)
    for field_name in ("blocked_dependency_step_ref", "halted_by_step_ref", "retry_not_before", "failure_category"):  # noqa: E501
        payload.pop(field_name)
    payload["definition_fingerprint_ref"] = _short_ref(
        "mission-step-fingerprint-ref",
        legacy_definition,
    )
    entry_payload = {
        key: value for key, value in payload.items() if key != "entry_hash_ref"
    }
    payload["entry_hash_ref"] = _short_ref(
        "mission-step-entry-hash-ref",
        entry_payload,
    )
    store.receipts_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    reloaded = MissionStepStore(tmp_path)
    assert (
        reloaded.receipts()[0].definition_fingerprint_ref == definition.fingerprint_ref
    )
    assert reloaded.create(definition).sequence == 1


def test_legacy_dispatch_payload_remains_readable_and_replayable(tmp_path) -> None:
    state_dir = tmp_path / "legacy-dispatch"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
        authority_constraints=_constraints(operation_limit=2),
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[ToolRuntimeAuthorityDispatchAdapter(_descriptor(filesystem=False))],
        lease_store=lease_store,
    )
    request = _request(
        lease.lease_ref,
        suffix="legacy-dispatch",
        filesystem=False,
    )
    dispatcher.prepare(request)
    payload = json.loads(dispatcher.receipts_path.read_text(encoding="utf-8"))
    for field in ("start_deadline", "start_validated_at", "execution_fence_ref", "failure_category", "provider_ref", "target_binding_ref", "approval_scope_fingerprint_ref"):
        payload.pop(field)
    entry_payload = {
        key: value for key, value in payload.items() if key != "entry_hash_ref"
    }
    payload["entry_hash_ref"] = _full_ref(
        "entry-hash-ref:authority-dispatch",
        entry_payload,
    )
    dispatcher.receipts_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    assert dispatcher.list_receipts()[0].dispatch_ref == request.dispatch_ref
    assert dispatcher.prepare(request).replayed is True


def test_dispatch_and_step_append_reject_regular_file_replacement(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "dispatch-swap"
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.execute,
        authority_constraints=_constraints(operation_limit=2),
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=False).model_copy(update={"approval_required": False})
    )
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(lease.lease_ref, suffix="dispatch-swap", filesystem=False)
    dispatcher.prepare(request)
    adapter_calls = [0]
    original_invoke = adapter.invoke

    def counted_invoke(request_value):
        adapter_calls[0] += 1
        return original_invoke(request_value)

    monkeypatch.setattr(adapter, "invoke", counted_invoke)
    original_append = dispatcher._append

    def swap_before_started_append(receipt_value):
        if receipt_value.status == "started":
            dispatcher.receipts_path.unlink()
            dispatcher.receipts_path.write_text("", encoding="utf-8")
        return original_append(receipt_value)

    monkeypatch.setattr(dispatcher, "_append", swap_before_started_append)
    with pytest.raises(
        AuthorityDispatchCorruptionError,
        match="AUTHORITY_DISPATCH_APPEND_BINDING_INVALID",
    ):
        dispatcher.execute(request)
    assert adapter_calls == [0]

    step_store = MissionStepStore(tmp_path / "step-swap")
    definition = MissionStepDefinition(
        mission_ref="mission-ref:test:step-swap",
        run_ref="run-ref:test:step-swap",
        step_ref="mission-step-ref:test:step-swap",
        capability_ref="authority-capability-ref:filesystem-metadata-v1",
        adapter_ref="authority-adapter-ref:filesystem-metadata-v1",
        lease_ref="authority-lease-ref:test:step-swap",
        deadline=utc_now() + timedelta(minutes=5),
        safe_summary="Reject regular-file replacement before claim append.",
    )
    step_store.create(definition)
    original_step_append = step_store._append

    def swap_before_claim_append(receipt_value):
        if receipt_value.status == "claimed":
            step_store.receipts_path.unlink()
            step_store.receipts_path.write_text("", encoding="utf-8")
        return original_step_append(receipt_value)

    monkeypatch.setattr(step_store, "_append", swap_before_claim_append)
    with pytest.raises(
        MissionStepCorruptionError,
        match="MISSION_STEP_LEDGER_APPEND_BINDING_INVALID",
    ):
        step_store.claim(
            definition.step_ref,
            owner_ref="mission-owner-ref:test:step-swap",
            ttl_seconds=30,
        )


def test_plan_ledger_rejects_semantic_tamper_and_append_over_limit(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="plan-storage",
    )
    store = DurableMissionPlanStore(tmp_path / "plan-storage")
    plan = request.build_durable_plan()
    receipt = store.accept(plan)
    tampered = receipt.model_copy(
        update={
            "plan": plan.model_copy(update={"safe_summary": "Tampered safe summary."})
        }
    )
    tampered = tampered.model_copy(update={"entry_hash_ref": plan_entry_hash(tampered)})
    store.receipts_path.write_text(tampered.model_dump_json() + "\n", encoding="utf-8")
    with pytest.raises(DurableMissionPlanCorruptionError):
        store.list_receipts()

    capped = DurableMissionPlanStore(tmp_path / "plan-cap")
    monkeypatch.setattr(plan_module, "DURABLE_MISSION_PLAN_LEDGER_MAX_RECEIPTS", 1)
    capped.accept(plan)
    second = plan.model_copy(
        update={
            "plan_ref": "mission-plan-ref:test-orchestration:plan-storage-second",
            "mission_ref": "mission-ref:test-orchestration:plan-storage-second",
            "run_ref": "run-ref:test-orchestration:plan-storage-second",
        }
    )
    with pytest.raises(
        DurableMissionPlanCorruptionError,
        match="DURABLE_MISSION_PLAN_LEDGER_RECEIPT_LIMIT_EXCEEDED",
    ):
        capped.accept(second)


def test_plan_step_and_dependency_bounds_fail_closed() -> None:
    bindings = [
        DurableMissionPlanStepBinding(
            step_ref=f"mission-step-ref:test:bounds:{index}",
            definition_fingerprint_ref=f"mission-step-fingerprint-ref:test:bounds:{index}",
            dispatch_ref=f"authority-dispatch-ref:test:bounds:{index}",
            dispatch_request_fingerprint_ref=f"request-fingerprint-ref:test:bounds:{index}",
            dependency_step_refs=[],
        )
        for index in range(17)
    ]
    with pytest.raises(ValidationError):
        DurableMissionPlan(
            plan_ref="mission-plan-ref:test:bounds:steps",
            mission_ref="mission-ref:test:bounds:steps",
            run_ref="run-ref:test:bounds:steps",
            ordered_steps=bindings,
            safe_summary="Reject a mission plan beyond the bounded step limit.",
        )

    bounded = bindings[:16]
    remaining = 65
    for index, binding in enumerate(bounded):
        dependencies = [item.step_ref for item in bounded[:index]][:remaining]
        bounded[index] = binding.model_copy(
            update={"dependency_step_refs": dependencies}
        )
        remaining -= len(dependencies)
    assert remaining == 0
    with pytest.raises(
        ValueError, match="DURABLE_MISSION_PLAN_DEPENDENCY_LIMIT_EXCEEDED"
    ):
        DurableMissionPlan(
            plan_ref="mission-plan-ref:test:bounds:dependencies",
            mission_ref="mission-ref:test:bounds:dependencies",
            run_ref="run-ref:test:bounds:dependencies",
            ordered_steps=bounded,
            safe_summary="Reject a mission plan beyond the dependency limit.",
        )
