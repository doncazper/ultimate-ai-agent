import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepCorruptionError,
    MissionStepStore,
)


def test_plan_acceptance_and_unbound_step_creation_are_mutually_exclusive(
    tmp_path,
) -> None:
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="materialization-race",
    )
    conflicting = request.steps[0].definition.model_copy(
        update={"safe_summary": "Conflicting unbound definition for race proof."}
    )
    barrier = Barrier(2)

    def accept_plan() -> str:
        barrier.wait()
        try:
            orchestrator.run(
                request,
                owner_ref="mission-owner-ref:test-orchestration:materialization-race",
            )
            return "plan"
        except MissionStepConflictError:
            return "plan-blocked"

    def create_unbound() -> str:
        barrier.wait()
        try:
            orchestrator.step_store.create(conflicting)
            return "unbound"
        except MissionStepConflictError:
            return "unbound-blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(accept_plan), pool.submit(create_unbound)]
        results = {future.result() for future in futures}

    assert results in [
        {"plan", "unbound-blocked"},
        {"plan-blocked", "unbound"},
    ]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO is POSIX-only")
@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_dispatch_and_step_ledgers_reject_non_regular_paths(tmp_path, kind) -> None:
    dispatch_state = tmp_path / f"dispatch-{kind}"
    dispatch_state.mkdir()
    dispatcher = AuthorityDispatcher(dispatch_state, adapters=[])
    step_state = tmp_path / f"step-{kind}"
    step_state.mkdir()
    step_store = MissionStepStore(step_state)
    for path in [dispatcher.receipts_path, step_store.receipts_path]:
        if kind == "symlink":
            path.symlink_to(tmp_path / f"missing-{path.name}")
        else:
            os.mkfifo(path)

    with pytest.raises(AuthorityDispatchCorruptionError):
        dispatcher.list_receipts()
    with pytest.raises(MissionStepCorruptionError):
        step_store.receipts()
