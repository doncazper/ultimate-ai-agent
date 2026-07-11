from __future__ import annotations

import argparse
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from scripts.dev.uaa_runtime_mission_failure_management import (
    cancel as cli_cancel,
    record_approval_decision as cli_record_approval_decision,
    request_dead_letter_recovery as cli_request_dead_letter_recovery,
)
from tests.test_authority_mission_controls import _cancellation_for_orchestration
from tests.test_authority_mission_approval_wait import (
    _Resolver,
    _approval_wait_fixture,
)
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from tests.test_authority_mission_retries import (
    _retry_fixture,
    _transient_failure,
)
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import (
    ApiRouteClassification,
    build_api_manifest,
)
from ultimate_ai_agent.api.rate_limits import route_rate_limit_group
from ultimate_ai_agent.api.routes import runtime_pilot_service
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MissionControlConflictError,
    MissionControlEvent,
    MissionControlRequest,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepStatus,
)
from ultimate_ai_agent.core.execution import durable_mission_worker as worker_module
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    MissionWorkerConflictError,
)
from ultimate_ai_agent.core.execution.mission_failure_management import (
    AuthorityMissionFailureManagementService,
    MissionApprovalDecision,
    MissionApprovalDecisionRequest,
)


def _cli_args(request: MissionControlRequest, state_dir: Path) -> argparse.Namespace:
    return argparse.Namespace(
        state_dir=str(state_dir),
        control_ref=request.control_ref,
        plan_ref=request.plan_ref,
        plan_fingerprint_ref=request.plan_fingerprint_ref,
        mission_ref=request.mission_ref,
        run_ref=request.run_ref,
        lease_ref=request.lease_ref,
        idempotency_ref=request.idempotency_ref,
        reason_ref=request.reason_ref,
        summary=request.safe_summary,
        json=False,
    )


def test_api_cli_and_service_share_one_idempotent_cancellation_truth(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    orchestrator, dispatcher, _, _, mission, _ = _orchestration_fixture(
        tmp_path,
        suffix="failure-management-parity",
        dependency_graph=[[]],
        shared_state=True,
    )
    orchestrator.materialize(mission)
    request = _cancellation_for_orchestration(mission)
    service = AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    )
    core = service.cancel(request)
    monkeypatch.setattr(
        runtime_pilot_service,
        "_mission_failure_service_getter",
        lambda: service,
    )

    response = TestClient(app).post(
        "/api/runtime/authority-missions/cancel",
        json=request.model_dump(mode="json"),
        headers={"x-uaa-idempotency-key": request.idempotency_ref},
    )
    cli_status = cli_cancel(_cli_args(request, orchestrator.step_store.state_dir))

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["control_receipt_ref"] == core.control_receipt_ref
    assert cli_status == 0
    assert core.control_receipt_ref in capsys.readouterr().out
    assert len(service.control_store.receipts()) == 1
    assert dispatcher.list_receipts() == []


def test_dead_letter_recovery_records_intent_without_replay(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    orchestrator, dispatcher, adapter, mission = _retry_fixture(
        tmp_path,
        suffix="failure-management-dead-letter",
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
        mission,
        owner_ref="mission-owner-ref:test:dead-letter:first",
    )
    terminal = orchestrator.run(
        mission,
        owner_ref="mission-owner-ref:test:dead-letter:second",
    )
    step_receipt = orchestrator.step_store.receipts()[-1]
    plan = mission.build_durable_plan()
    request = MissionControlRequest(
        control_ref="mission-control-ref:test:dead-letter-recovery",
        event=MissionControlEvent.dead_letter_recovery_requested,
        plan_ref=plan.plan_ref,
        plan_fingerprint_ref=plan.fingerprint_ref,
        mission_ref=plan.mission_ref,
        run_ref=plan.run_ref,
        lease_ref=mission.steps[0].request.lease_ref,
        idempotency_ref="idempotency-ref:test:dead-letter-recovery",
        reason_ref="reason-ref:test:dead-letter-recovery",
        dead_letter_step_ref=step_receipt.definition.step_ref,
        dead_letter_receipt_ref=step_receipt.receipt_ref,
        dead_letter_entry_hash_ref=step_receipt.entry_hash_ref,
        safe_summary="Request a new authorized plan without replaying old work.",
    )

    result = AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    ).request_dead_letter_recovery(request)
    cli_args = _cli_args(request, orchestrator.step_store.state_dir)
    cli_args.dead_letter_step_ref = request.dead_letter_step_ref
    cli_args.dead_letter_receipt_ref = request.dead_letter_receipt_ref
    cli_args.dead_letter_entry_hash_ref = request.dead_letter_entry_hash_ref
    cli_status = cli_request_dead_letter_recovery(cli_args)

    assert terminal.steps[0].status == MissionStepStatus.dead_lettered.value
    assert result.original_dead_letter_reopened is False
    assert orchestrator.step_store.read(
        step_receipt.definition.step_ref
    ).status == MissionStepStatus.dead_lettered.value
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 2
    assert cli_status == 0
    assert result.control_receipt_ref in capsys.readouterr().out


def test_failure_management_routes_are_exact_mutations_with_rate_limits() -> None:
    routes = {
        (route.method, route.path): route for route in build_api_manifest(app).routes
    }
    for path in (
        "/api/runtime/authority-missions/cancel",
        "/api/runtime/authority-missions/approval-decisions",
        "/api/runtime/authority-missions/dead-letter-recovery",
    ):
        route = routes[("POST", path)]
        assert (
            route.route_classification
            == ApiRouteClassification.mutating_requires_authority.value
        )
        assert route.idempotency_required is True
        assert route_rate_limit_group("POST", path) == "governed_runtime_pilot"


def test_exact_api_approval_records_evidence_then_worker_freshly_validates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval",
    )
    waiting = worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval:wait",
    )
    assert waiting is not None and waiting.status == "waiting_for_approval"
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    waiting_step = orchestrator.step_store.read(step.definition.step_ref)
    decision_request = MissionApprovalDecisionRequest(
        step_ref=step.definition.step_ref,
        approval_request_ref=waiting_step.approval_request_ref or "",
        approval_ref=waiting_step.approval_ref or "",
        approval_scope_fingerprint_ref=(
            waiting_step.approval_scope_fingerprint_ref or ""
        ),
        approval_validation_request=validation,
        decision=MissionApprovalDecision.approve,
        operator_ref="operator-ref:test:mission-approval",
        idempotency_ref="idempotency-ref:test:mission-approval",
        reason_ref="reason-ref:test:mission-approval",
        safe_summary="Approve one exact registered mission request.",
    )
    monkeypatch.setenv(
        "UAA_AUTHORITY_STATE_DIR",
        str(orchestrator.step_store.state_dir),
    )
    response = TestClient(app).post(
        "/api/runtime/authority-missions/approval-decisions",
        json=decision_request.model_dump(mode="json"),
        headers={
            "x-uaa-idempotency-key": decision_request.idempotency_ref,
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "recorded"
    assert dispatcher.list_receipts() == []
    assert authority.get_grant(decision_request.approval_ref) is None
    resumed = worker.resume_next(
        _Resolver(mission),
        worker_ref="mission-worker-ref:test:failure-management-approval:resume",
    )
    assert resumed is not None and resumed.status == "succeeded"


def test_approval_cli_records_same_evidence_without_minting_authority(
    tmp_path: Path,
    capsys,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-cli",
    )
    waiting = worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval-cli:wait",
    )
    assert waiting is not None and waiting.status == "waiting_for_approval"
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    validation_file = tmp_path / "approval-validation.json"
    validation_file.write_text(validation.model_dump_json(), encoding="utf-8")
    args = argparse.Namespace(
        state_dir=str(orchestrator.step_store.state_dir),
        step_ref=step.definition.step_ref,
        approval_request_ref=current.approval_request_ref,
        approval_ref=current.approval_ref,
        approval_scope_fingerprint_ref=current.approval_scope_fingerprint_ref,
        decision="approve",
        operator_ref="operator-ref:test:mission-approval-cli",
        validation_request_file=str(validation_file),
        idempotency_ref="idempotency-ref:test:mission-approval-cli",
        reason_ref="reason-ref:test:mission-approval-cli",
        summary="Approve one exact registered mission request through the CLI.",
        json=False,
    )

    status = cli_record_approval_decision(args)

    assert status == 0
    assert "Execution authority granted: false" in capsys.readouterr().out
    assert authority.get_grant(current.approval_ref or "") is None
    assert dispatcher.list_receipts() == []
    resumed = worker.resume_next(
        _Resolver(mission),
        worker_ref="mission-worker-ref:test:failure-management-approval-cli:resume",
    )
    assert resumed is not None and resumed.status == "succeeded"


def test_denied_wait_cannot_later_mint_or_resume_authority(tmp_path: Path) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-deny",
    )
    worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval-deny:wait",
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    base = dict(
        step_ref=step.definition.step_ref,
        approval_request_ref=current.approval_request_ref or "",
        approval_ref=current.approval_ref or "",
        approval_scope_fingerprint_ref=(
            current.approval_scope_fingerprint_ref or ""
        ),
        approval_validation_request=validation,
        operator_ref="operator-ref:test:mission-approval-deny",
        reason_ref="reason-ref:test:mission-approval-deny",
        safe_summary="Deny one exact registered mission request.",
    )
    service = AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    )
    service.resolve_approval(
        MissionApprovalDecisionRequest(
            **base,
            decision=MissionApprovalDecision.deny,
            idempotency_ref="idempotency-ref:test:mission-approval-deny",
        )
    )
    with pytest.raises(MissionControlConflictError):
        service.resolve_approval(
            MissionApprovalDecisionRequest(
                **base,
                decision=MissionApprovalDecision.approve,
                idempotency_ref="idempotency-ref:test:mission-approval-after-deny",
            )
        )
    assert authority.get_grant(validation.approval_ref) is None
    terminal = worker.resume_next(
        _Resolver(mission),
        worker_ref="mission-worker-ref:test:failure-management-approval-deny:resume",
    )
    assert terminal is not None and terminal.status == "failed"
    assert authority.get_grant(validation.approval_ref) is None
    assert dispatcher.list_receipts() == []


def test_worker_rolls_back_new_grant_when_durable_resume_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-rollback",
    )
    worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval-rollback:wait",
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    ).resolve_approval(
        MissionApprovalDecisionRequest(
            step_ref=step.definition.step_ref,
            approval_request_ref=current.approval_request_ref or "",
            approval_ref=current.approval_ref or "",
            approval_scope_fingerprint_ref=(
                current.approval_scope_fingerprint_ref or ""
            ),
            approval_validation_request=validation,
            decision=MissionApprovalDecision.approve,
            operator_ref="operator-ref:test:mission-approval-rollback",
            idempotency_ref="idempotency-ref:test:mission-approval-rollback",
            reason_ref="reason-ref:test:mission-approval-rollback",
            safe_summary="Approve one exact request before a durable write fault.",
        )
    )
    monkeypatch.setattr(
        orchestrator.step_store,
        "resume_approval_wait",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            MissionStepConflictError("synthetic durable resume failure")
        ),
    )

    with pytest.raises(MissionStepConflictError):
        worker.resume_next(
            _Resolver(mission),
            worker_ref=(
                "mission-worker-ref:test:failure-management-approval-rollback:resume"
            ),
        )

    assert authority.get_grant(validation.approval_ref) is None
    assert dispatcher.list_receipts() == []


def test_forged_approval_control_fingerprint_cannot_mint_authority(
    tmp_path: Path,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-forged",
    )
    worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval-forged:wait",
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    plan = mission.build_durable_plan()
    worker.control_store.append(
        MissionControlRequest(
            control_ref="mission-control-ref:test:approval-forged",
            event=MissionControlEvent.approval_decision_recorded,
            plan_ref=plan.plan_ref,
            plan_fingerprint_ref=plan.fingerprint_ref,
            mission_ref=plan.mission_ref,
            run_ref=plan.run_ref,
            lease_ref=step.request.lease_ref,
            idempotency_ref="idempotency-ref:test:approval-forged",
            reason_ref="reason-ref:test:approval-forged",
            approval_step_ref=step.definition.step_ref,
            approval_request_ref=current.approval_request_ref,
            approval_ref=current.approval_ref,
            approval_scope_fingerprint_ref=(
                current.approval_scope_fingerprint_ref
            ),
            approval_decision="approve",
            approval_decision_fingerprint_ref=(
                "approval-validation-ref:mission-decision:sha256:forged000000000000000000"
            ),
            operator_ref="operator-ref:test:approval-forged",
            safe_summary="Forged approval evidence must fail closed.",
        )
    )

    terminal = worker.resume_next(
        _Resolver(mission),
        worker_ref="mission-worker-ref:test:failure-management-approval-forged:resume",
    )

    assert terminal is not None and terminal.status == "failed"
    assert authority.get_grant(validation.approval_ref) is None
    assert dispatcher.list_receipts() == []


def test_cancellation_wins_before_recorded_approval_is_applied(
    tmp_path: Path,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-cancel",
    )
    worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:failure-management-approval-cancel:wait",
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    service = AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    )
    service.resolve_approval(
        MissionApprovalDecisionRequest(
            step_ref=step.definition.step_ref,
            approval_request_ref=current.approval_request_ref or "",
            approval_ref=current.approval_ref or "",
            approval_scope_fingerprint_ref=(
                current.approval_scope_fingerprint_ref or ""
            ),
            approval_validation_request=validation,
            decision=MissionApprovalDecision.approve,
            operator_ref="operator-ref:test:mission-approval-cancel",
            idempotency_ref="idempotency-ref:test:mission-approval-cancel",
            reason_ref="reason-ref:test:mission-approval-cancel",
            safe_summary="Record approval before cancellation wins.",
        )
    )
    service.cancel(_cancellation_for_orchestration(mission))

    result = worker.resume_next(
        _Resolver(mission),
        worker_ref="mission-worker-ref:test:failure-management-approval-cancel:resume",
    )

    assert result is None
    assert worker.store.latest()[0].status == "cancelled"
    assert authority.get_grant(validation.approval_ref) is None
    assert dispatcher.list_receipts() == []


def test_prestart_cancellation_removes_worker_created_approval_grant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-prestart-cancel",
    )
    worker.run_once(
        mission,
        worker_ref=(
            "mission-worker-ref:test:failure-management-approval-prestart-cancel:wait"
        ),
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    service = AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    )
    service.resolve_approval(
        MissionApprovalDecisionRequest(
            step_ref=step.definition.step_ref,
            approval_request_ref=current.approval_request_ref or "",
            approval_ref=current.approval_ref or "",
            approval_scope_fingerprint_ref=(
                current.approval_scope_fingerprint_ref or ""
            ),
            approval_validation_request=validation,
            decision=MissionApprovalDecision.approve,
            operator_ref="operator-ref:test:mission-approval-prestart-cancel",
            idempotency_ref=(
                "idempotency-ref:test:mission-approval-prestart-cancel"
            ),
            reason_ref="reason-ref:test:mission-approval-prestart-cancel",
            safe_summary="Record approval before prestart cancellation wins.",
        )
    )
    original_run = orchestrator.run
    cancellation = _cancellation_for_orchestration(mission)
    cancellation_recorded = False

    def cancel_before_dispatch(*args, **kwargs):
        nonlocal cancellation_recorded
        if not cancellation_recorded:
            service.cancel(cancellation)
            cancellation_recorded = True
        return original_run(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "run", cancel_before_dispatch)

    result = worker.resume_next(
        _Resolver(mission),
        worker_ref=(
            "mission-worker-ref:test:failure-management-approval-prestart-cancel:resume"
        ),
    )

    assert result is not None and result.status == "failed"
    assert worker.store.latest()[0].status == "cancelled"
    assert authority.get_grant(validation.approval_ref) is None
    assert not any(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    )


def test_claim_time_kill_switch_removes_worker_created_approval_grant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker, orchestrator, dispatcher, authority, mission = _approval_wait_fixture(
        tmp_path,
        suffix="failure-management-approval-claim-kill",
    )
    worker.run_once(
        mission,
        worker_ref="mission-worker-ref:test:approval-claim-kill:wait",
    )
    step = mission.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    current = orchestrator.step_store.read(step.definition.step_ref)
    AuthorityMissionFailureManagementService(
        orchestrator.step_store.state_dir
    ).resolve_approval(
        MissionApprovalDecisionRequest(
            step_ref=step.definition.step_ref,
            approval_request_ref=current.approval_request_ref or "",
            approval_ref=current.approval_ref or "",
            approval_scope_fingerprint_ref=(
                current.approval_scope_fingerprint_ref or ""
            ),
            approval_validation_request=validation,
            decision=MissionApprovalDecision.approve,
            operator_ref="operator-ref:test:mission-approval-claim-kill",
            idempotency_ref="idempotency-ref:test:mission-approval-claim-kill",
            reason_ref="reason-ref:test:mission-approval-claim-kill",
            safe_summary="Record approval before a claim-time kill switch.",
        )
    )
    kill_switch_checks = iter([False, True])
    monkeypatch.setattr(
        worker_module,
        "authority_lease_kill_switch_engaged",
        lambda: next(kill_switch_checks),
    )

    with pytest.raises(
        MissionWorkerConflictError,
        match="MISSION_WORKER_KILL_SWITCH_ENGAGED",
    ):
        worker.resume_next(
            _Resolver(mission),
            worker_ref="mission-worker-ref:test:approval-claim-kill:resume",
        )

    assert authority.get_grant(validation.approval_ref) is None
    assert dispatcher.list_receipts() == []
