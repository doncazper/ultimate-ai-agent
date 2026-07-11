from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import MissionStepStore
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerDisabledError,
    MissionWorkerJobStatus,
    MissionWorkerPlatform,
    MissionWorkerRequestResolver,
    MissionWorkerStore,
    build_mission_worker_read_model,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import AuthorityMissionRunner


def _config() -> LocalMissionWorkerConfiguration:
    with patch("platform.system", return_value="Darwin"):
        return LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
        )


class _Resolver(MissionWorkerRequestResolver):
    def __init__(self, request):
        self.request = request

    def resolve(self, binding):
        return self.request


def test_worker_is_disabled_by_default_and_linux_windows_are_placeholders(
    tmp_path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-disabled",
        shared_state=True,
    )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
    )

    with pytest.raises(MissionWorkerDisabledError, match="DISABLED_BY_DEFAULT"):
        worker.run_once(request, worker_ref="mission-worker-ref:test:disabled")

    read_model = build_mission_worker_read_model(
        store=worker.store,
        orchestrator=orchestrator,
    )
    assert read_model.configuration_enabled is False
    assert read_model.linux_surface_posture == "render_placeholder"
    assert read_model.windows_surface_posture == "render_placeholder"
    assert read_model.execution_authority_granted is False


def test_local_worker_runs_sliced_mission_with_fenced_start_and_safe_ledger(
    tmp_path,
) -> None:
    orchestrator, dispatcher, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-success",
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    )

    result = worker.run_once(
        request,
        worker_ref="mission-worker-ref:test:worker-success",
    )

    assert result is not None
    assert result.status == "succeeded"
    latest = store.latest()[0]
    assert latest.status == MissionWorkerJobStatus.succeeded.value
    started = [item for item in dispatcher.list_receipts() if item.status == "started"]
    assert len(started) == 2
    assert all(item.execution_fence_ref for item in started)
    payload = store.receipts_path.read_text(encoding="utf-8")
    assert "relative_path" not in payload
    assert "notes/report" not in payload
    assert str(tmp_path) not in payload
    assert "sensitive body" not in payload
    assert "mission-worker-ref:test:worker-success" not in payload
    assert (
        json.loads(payload.splitlines()[0])["binding"]["plan_ref"] == request.plan_ref
    )


def test_restart_requires_exact_resolved_request_and_replays_without_duplicate_start(
    tmp_path,
) -> None:
    orchestrator, dispatcher, lease_store, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-restart",
        shared_state=True,
    )
    store = MissionWorkerStore(orchestrator.step_store.state_dir)
    first = LocalMissionWorker(
        orchestrator=orchestrator,
        store=store,
        configuration=_config(),
    )
    first.enqueue(request)
    first.request_shutdown()

    restarted_dispatcher = AuthorityDispatcher(
        dispatcher.state_dir,
        adapters=list(dispatcher.adapters.values()),
        lease_store=lease_store,
    )
    restarted_step_store = MissionStepStore(orchestrator.step_store.state_dir)
    restarted_orchestrator = SynchronousAuthorityMissionOrchestrator(
        runner=AuthorityMissionRunner(
            dispatcher=restarted_dispatcher,
            step_store=restarted_step_store,
        ),
        plan_store=DurableMissionPlanStore(orchestrator.step_store.state_dir),
    )
    restarted = LocalMissionWorker(
        orchestrator=restarted_orchestrator,
        store=MissionWorkerStore(restarted_step_store.state_dir),
        configuration=_config(),
    )
    assert (
        restarted.resume_next(
            _Resolver(None),
            worker_ref="mission-worker-ref:test:restart-missing",
        )
        is None
    )
    assert restarted_dispatcher.list_receipts() == []

    result = restarted.resume_next(
        _Resolver(request),
        worker_ref="mission-worker-ref:test:restart-resolved",
    )
    replay = restarted.run_once(
        request,
        worker_ref="mission-worker-ref:test:restart-replay",
    )

    assert result is not None and result.status == "succeeded"
    assert replay is None
    assert (
        sum(
            item.adapter_invocation_performed
            for item in restarted_dispatcher.list_receipts()
        )
        == 2
    )
