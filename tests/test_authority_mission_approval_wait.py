from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.test_authority_dispatcher import _approval, _descriptor
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
)
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepStatus,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerRequestResolver,
    MissionWorkerStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationStepInput,
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import AuthorityMissionRunner
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


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


def _approval_wait_fixture(tmp_path: Path, *, suffix: str):
    original, _, lease_store, _, request, root = _orchestration_fixture(
        tmp_path,
        suffix=suffix,
        dependency_graph=[[]],
        shared_state=True,
    )
    authority = LocalApprovalAuthority()
    step = request.steps[0]
    validation = _approval(authority, step.request)
    authority.remove_grant_for_rollback(validation.approval_ref)
    updated_step = AuthorityMissionOrchestrationStepInput(
        definition=step.definition,
        request=step.request.model_copy(
            update={"approval_validation_request": validation}
        ),
    )
    updated_request = request.model_copy(update={"steps": [updated_step]})
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True).model_copy(
            update={"approval_required": True}
        ),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref="safe-root:test-authority",
                root_path=root,
                safe_label="Mission approval wait safe root",
            )
        ],
    )
    dispatcher = AuthorityDispatcher(
        original.runner.dispatcher.state_dir,
        adapters=[adapter],
        lease_store=lease_store,
        approval_authority=authority,
    )
    step_store = MissionStepStore(original.step_store.state_dir)
    orchestrator = SynchronousAuthorityMissionOrchestrator(
        runner=AuthorityMissionRunner(
            dispatcher=dispatcher,
            step_store=step_store,
        ),
        plan_store=DurableMissionPlanStore(step_store.state_dir),
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(step_store.state_dir),
        configuration=_worker_config(),
    )
    return worker, orchestrator, dispatcher, authority, updated_request


def test_registered_exact_request_waits_without_claim_or_budget_then_resumes(
    tmp_path: Path,
) -> None:
    worker, orchestrator, dispatcher, authority, request = _approval_wait_fixture(
        tmp_path,
        suffix="approval-wait-resume",
    )

    waiting = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:approval-wait",
    )

    assert waiting is not None and waiting.status == "waiting_for_approval"
    assert waiting.approval_wait_step_count == 1
    step = orchestrator.step_store.read(request.steps[0].definition.step_ref)
    assert step.status == MissionStepStatus.approval_wait.value
    assert step.owner_ref is None and step.claim_ref is None
    assert worker.store.latest()[0].status == MissionWorkerJobStatus.approval_wait.value
    assert dispatcher.list_receipts() == []
    assert dispatcher.budget_store.list_receipts() == []
    receipt_count = len(worker.store._load())  # noqa: SLF001

    assert (
        worker.run_once(
            request,
            worker_ref="mission-worker-ref:test:approval-still-waiting",
        )
        is None
    )
    assert len(worker.store._load()) == receipt_count  # noqa: SLF001

    validation = request.steps[0].request.approval_validation_request
    assert validation is not None
    registered = authority.find_request_for_validation(validation)
    assert registered is not None
    authority.grant(
        registered.approval_request_id,
        approved_by_actor_id="operator-ref:test-approval-resume",
        approval_ref=validation.approval_ref,
    )

    resumed = worker.resume_next(
        _Resolver(request),
        worker_ref="mission-worker-ref:test:approval-resume",
    )

    assert resumed is not None and resumed.status == "succeeded"
    assert sum(
        receipt.adapter_invocation_performed
        for receipt in dispatcher.list_receipts()
    ) == 1


def test_approval_identifier_without_registered_exact_scope_fails_closed(
    tmp_path: Path,
) -> None:
    worker, orchestrator, dispatcher, _, request = _approval_wait_fixture(
        tmp_path,
        suffix="approval-unregistered",
    )
    step = request.steps[0]
    validation = step.request.approval_validation_request
    assert validation is not None
    unsafe_validation = validation.model_copy(
        update={"resource_refs": ["resource-ref:test:wrong-scope"]}
    )
    changed = request.model_copy(
        update={
            "steps": [
                step.model_copy(
                    update={
                        "request": step.request.model_copy(
                            update={
                                "approval_validation_request": unsafe_validation
                            }
                        )
                    }
                )
            ]
        }
    )

    result = worker.run_once(
        changed,
        worker_ref="mission-worker-ref:test:approval-unregistered",
    )

    assert result is not None and result.status == "failed"
    current = orchestrator.step_store.read(step.definition.step_ref)
    assert current.status == MissionStepStatus.failed.value
    assert "approval-request-not-registered" in current.reason_refs[0]
    assert dispatcher.list_receipts() == []


@pytest.mark.parametrize("invalid_posture", ["revoked", "expired"])
def test_revoked_or_expired_approval_never_starts(
    tmp_path: Path,
    invalid_posture: str,
) -> None:
    worker, orchestrator, dispatcher, authority, request = _approval_wait_fixture(
        tmp_path,
        suffix=f"approval-{invalid_posture}",
    )
    validation = request.steps[0].request.approval_validation_request
    assert validation is not None
    registered = authority.find_request_for_validation(validation)
    assert registered is not None
    grant = authority.grant(
        registered.approval_request_id,
        approved_by_actor_id="operator-ref:test-approval-invalid",
        approval_ref=validation.approval_ref,
    )
    if invalid_posture == "revoked":
        authority.revoke(
            grant.approval_ref,
            "Approval withdrawn before mission start.",
        )
    else:
        authority.load_grant_for_validation(
            grant.model_copy(update={"expires_at": grant.created_at})
        )

    result = worker.run_once(
        request,
        worker_ref=f"mission-worker-ref:test:approval-{invalid_posture}",
    )

    assert result is not None and result.status == "failed"
    current = orchestrator.step_store.read(request.steps[0].definition.step_ref)
    assert current.status == MissionStepStatus.failed.value
    assert dispatcher.list_receipts() == []


def test_approval_wait_expiry_fails_terminal_without_dispatch(
    tmp_path: Path,
) -> None:
    worker, orchestrator, dispatcher, _, request = _approval_wait_fixture(
        tmp_path,
        suffix="approval-wait-expiry",
    )
    waiting = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:approval-wait-expiry:first",
    )
    assert waiting is not None and waiting.status == "waiting_for_approval"
    deadline = request.steps[0].definition.deadline
    orchestrator.step_store._clock = lambda: deadline + timedelta(  # noqa: SLF001
        microseconds=1
    )

    expired = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:approval-wait-expiry:resume",
    )

    assert expired is not None and expired.status == "failed"
    assert (
        orchestrator.step_store.read(request.steps[0].definition.step_ref).status
        == MissionStepStatus.failed.value
    )
    assert dispatcher.list_receipts() == []
