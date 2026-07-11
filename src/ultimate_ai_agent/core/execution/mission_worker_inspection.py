from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import MissionStepStore
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    MissionWorkerReadModel,
    MissionWorkerStore,
    build_mission_worker_read_model,
    local_mission_worker_configuration_from_environment,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import AuthorityMissionRunner


MISSION_WORKER_INSPECTION_API_REF = "GET /api/runtime/authority-missions/worker-state"
MISSION_WORKER_INSPECTION_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-mission-worker"
)


def build_local_mission_worker_inspection(
    *,
    state_dir: Path | None = None,
) -> MissionWorkerReadModel:
    owned_state_dir = state_dir or authority_state_dir()
    dispatcher = AuthorityDispatcher(owned_state_dir, adapters=[])
    step_store = MissionStepStore(owned_state_dir)
    orchestrator = SynchronousAuthorityMissionOrchestrator(
        runner=AuthorityMissionRunner(
            dispatcher=dispatcher,
            step_store=step_store,
        ),
        plan_store=DurableMissionPlanStore(owned_state_dir),
    )
    return build_mission_worker_read_model(
        store=MissionWorkerStore(owned_state_dir),
        orchestrator=orchestrator,
        configuration=local_mission_worker_configuration_from_environment(),
    )
