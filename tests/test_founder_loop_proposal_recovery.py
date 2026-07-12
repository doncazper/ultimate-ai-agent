from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import ultimate_ai_agent.core.control_center.founder_loop_mission as founder_module
from tests.test_founder_loop_filesystem_mission import _service_fixture
from ultimate_ai_agent.core.control_center.founder_loop_mission import (
    FounderLoopFilesystemMissionService,
    FounderLoopPreparedProposalStore,
)
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


def test_prepared_proposal_recovers_after_service_restart_without_raw_path(
    tmp_path: Path,
) -> None:
    service, approval_authority, lease_store, _, request, readiness, root_path = (
        _service_fixture(tmp_path, suffix="proposal-restart")
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:proposal-restart",
    )
    state_dir = service.orchestrator.step_store.state_dir
    recovered = FounderLoopFilesystemMissionService(
        state_dir=state_dir,
        root=FilesystemSafeRoot(
            root_ref=next(iter(service.targets.values())).root_ref,
            root_path=root_path,
            safe_label="Founder Loop repository root",
        ),
        targets=tuple(service.targets.values()),
        lease_store=lease_store,
        approval_authority=approval_authority,
        readiness=lambda: readiness["status"],  # type: ignore[return-value]
    )

    result = recovered.execute(
        proposal_ref=prepared.proposal.proposal_ref,
        approval_ref=grant.approval_ref,
        owner_ref="mission-owner-ref:founder-loop:proposal-restart",
    )
    assert result.orchestration.status == "succeeded"
    persisted = (state_dir / "founder_loop_prepared_proposals.jsonl").read_text(
        encoding="utf-8"
    )
    assert "docs/README.md" not in persisted
    assert str(root_path) not in persisted


def test_prepared_proposal_rejects_root_replacement_after_restart(
    tmp_path: Path,
) -> None:
    service, approval_authority, lease_store, _, request, readiness, root_path = (
        _service_fixture(tmp_path, suffix="proposal-restart-root-drift")
    )
    prepared = service.prepare(request)
    grant = approval_authority.grant(
        prepared.proposal.approval_request_ref,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref="approval-ref:founder-loop:proposal-restart-root-drift",
    )
    moved = root_path.with_name("repository-root-original")
    root_path.rename(moved)
    (root_path / "docs").mkdir(parents=True)
    (root_path / "docs" / "README.md").write_text(
        "replacement content",
        encoding="utf-8",
    )
    recovered = FounderLoopFilesystemMissionService(
        state_dir=service.orchestrator.step_store.state_dir,
        root=FilesystemSafeRoot(
            root_ref=next(iter(service.targets.values())).root_ref,
            root_path=root_path,
            safe_label="Founder Loop repository root",
        ),
        targets=tuple(service.targets.values()),
        lease_store=lease_store,
        approval_authority=approval_authority,
        readiness=lambda: readiness["status"],  # type: ignore[return-value]
    )

    with pytest.raises(
        ValueError,
        match="FOUNDER_LOOP_FILESYSTEM_ROOT_IDENTITY_DRIFT",
    ):
        recovered.execute(
            proposal_ref=prepared.proposal.proposal_ref,
            approval_ref=grant.approval_ref,
            owner_ref="mission-owner-ref:founder-loop:proposal-restart-root-drift",
        )
    assert not recovered.orchestrator.runner.dispatcher.list_receipts()


def test_prepared_proposal_ledger_serializes_cross_instance_appends(
    tmp_path: Path,
) -> None:
    service, _, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix="proposal-concurrency",
    )
    state_dir = service.orchestrator.step_store.state_dir
    stores = (
        FounderLoopPreparedProposalStore(state_dir),
        FounderLoopPreparedProposalStore(state_dir),
    )
    identity_ref = service._lane_adapter.root_identity_ref  # noqa: SLF001
    with ThreadPoolExecutor(max_workers=2) as pool:
        same_records = list(
            pool.map(
                lambda store: store.record(
                    request,
                    root_identity_ref=identity_ref,
                ),
                stores,
            )
        )
    assert same_records[0] == same_records[1]
    assert len(stores[0]._load()) == 1  # noqa: SLF001

    second = request.model_copy(
        update={
            "proposal_ref": "action-proposal-ref:founder-loop:proposal-concurrency:2",
            "intent_ref": "intent-ref:founder-loop:proposal-concurrency:2",
        }
    )
    third = request.model_copy(
        update={
            "proposal_ref": "action-proposal-ref:founder-loop:proposal-concurrency:3",
            "intent_ref": "intent-ref:founder-loop:proposal-concurrency:3",
        }
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(
            pool.map(
                lambda item: item[0].record(
                    item[1],
                    root_identity_ref=identity_ref,
                ),
                zip(stores, (second, third)),
            )
        )
    records = stores[0]._load()  # noqa: SLF001
    assert [record.sequence for record in records] == [1, 2, 3]


@pytest.mark.parametrize("append", [False, True])
def test_prepared_proposal_ledger_rejects_state_directory_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    append: bool,
) -> None:
    service, _, _, _, request, _, _ = _service_fixture(
        tmp_path,
        suffix=f"proposal-state-swap-{append}",
    )
    state_dir = service.orchestrator.step_store.state_dir
    moved = tmp_path / f"proposal-state-swap-{append}-original"
    outside = tmp_path / f"proposal-state-swap-{append}-outside"
    outside.mkdir()
    original_open = founder_module.os.open
    swapped = False

    def swap_before_ledger_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and path == founder_module.FOUNDER_LOOP_PROPOSAL_LEDGER_FILE
            and dir_fd is not None
            and bool(flags & founder_module.os.O_CREAT) is append
        ):
            swapped = True
            state_dir.rename(moved)
            state_dir.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(founder_module.os, "open", swap_before_ledger_open)
    with pytest.raises(ValueError, match="FOUNDER_LOOP_PROPOSAL_STATE_DIR_INVALID"):
        if append:
            service.prepare(request)
        else:
            service._proposal_store.get(request.proposal_ref)  # noqa: SLF001
    assert not (outside / founder_module.FOUNDER_LOOP_PROPOSAL_LEDGER_FILE).exists()
