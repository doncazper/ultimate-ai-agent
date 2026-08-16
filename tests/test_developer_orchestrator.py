from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "dev"))

from uaa_developer_orchestrator.coordinator import (  # noqa: E402
    DeveloperScopeDisposition,
    DeveloperWorkCoordinator,
    DeveloperWorkQueueClaimError,
    DeveloperWorkQueueConflictError,
    DeveloperWorkNode,
    DeveloperWorkTaskDraft,
)
from uaa_developer_orchestrator.planning import (  # noqa: E402
    build_developer_planning_catalog,
)
from uaa_developer_orchestrator.scout import (  # noqa: E402
    DeveloperPullRequestScout,
    DeveloperWorkspaceScout,
    GitMetadataCommandResult,
)
from uaa_developer_queue import build_parser  # noqa: E402


def _draft(
    task_ref: str,
    *,
    priority: str = "p0",
    concurrency: str = "parallel_safe",
    depends_on_task_refs: list[str] | None = None,
) -> DeveloperWorkTaskDraft:
    suffix = task_ref.removeprefix("dev-task:")
    return DeveloperWorkTaskDraft(
        task_ref=task_ref,
        title=f"Developer task {suffix}",
        safe_summary="A bounded developer task with no implied execution authority.",
        priority=priority,
        concurrency=concurrency,
        canonical_task_ref=f"canonical-task-ref:{suffix}",
        canonical_source_ref="canonical:developer-queue-test",
        canonical_source_fingerprint_ref="planning-fingerprint-ref:sha256:test",
        scope_contract_ref=f"scope-contract-ref:{suffix}",
        in_scope_refs=[f"scope-ref:{suffix}/owned"],
        out_of_scope_refs=[f"scope-ref:{suffix}/excluded"],
        sol_thinking_level="high",
        branch_ref=f"branch-ref:codex/{suffix}",
        worktree_ref=f"worktree-ref:test/{suffix}",
        workstream_ref="workstream-ref:test",
        acceptance_refs=[f"acceptance-ref:{suffix}"],
        verifier_refs=[f"verifier-ref:{suffix}"],
        merge_gate_refs=[f"merge-gate-ref:{suffix}"],
        depends_on_task_refs=depends_on_task_refs or [],
        next_safe_action="Implement only the scoped task and record focused verifier evidence.",
    )


def _register_node(
    coordinator: DeveloperWorkCoordinator,
    node_ref: str,
    *,
    idempotency_ref: str,
    heartbeat: bool = True,
) -> None:
    coordinator.register_node(
        DeveloperWorkNode(
            node_ref=node_ref,
            transport_ref="developer-transport-ref:test-shared-ledger",
            capabilities=["queue_claim", "local_worktree", "local_verification"],
        ),
        idempotency_ref=idempotency_ref,
    )
    if heartbeat:
        coordinator.node_heartbeat(
            node_ref=node_ref,
            idempotency_ref=f"{idempotency_ref}-heartbeat",
        )


def test_queue_claims_are_idempotent_and_dependency_bound(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.initialize(idempotency_ref="idempotency-ref:init")
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
    )
    _register_node(
        coordinator,
        "node-ref:beast",
        idempotency_ref="idempotency-ref:register-beast",
    )
    coordinator.add_task(
        _draft("dev-task:foundation"), idempotency_ref="idempotency-ref:add-foundation"
    )
    replay = coordinator.add_task(
        _draft("dev-task:foundation"), idempotency_ref="idempotency-ref:add-foundation"
    )
    assert replay.replayed is True
    coordinator.add_task(
        _draft(
            "dev-task:follow-up",
            depends_on_task_refs=["dev-task:foundation"],
        ),
        idempotency_ref="idempotency-ref:add-follow-up",
    )

    with pytest.raises(DeveloperWorkQueueClaimError, match="DEPENDENCIES_INCOMPLETE"):
        coordinator.claim_task(
            task_ref="dev-task:follow-up",
            node_ref="node-ref:beast",
            idempotency_ref="idempotency-ref:claim-follow-up-too-early",
        )

    initial_claim = coordinator.claim_next(
        node_ref="node-ref:mac", idempotency_ref="idempotency-ref:claim-foundation"
    )
    replayed_claim = coordinator.claim_next(
        node_ref="node-ref:mac", idempotency_ref="idempotency-ref:claim-foundation"
    )
    assert replayed_claim.replayed is True
    assert replayed_claim.receipt_ref == initial_claim.receipt_ref
    coordinator.complete(
        task_ref="dev-task:foundation",
        node_ref="node-ref:mac",
        evidence_refs=["evidence-ref:foundation-verifier"],
        idempotency_ref="idempotency-ref:complete-foundation",
    )
    coordinator.claim_next(
        node_ref="node-ref:beast",
        idempotency_ref="idempotency-ref:claim-follow-up",
    )
    view = coordinator.inspect(node_refs=["node-ref:mac", "node-ref:beast"])
    assert view.revision == 9
    assert view.next_task_by_node_ref["node-ref:beast"] is None
    follow_up = next(
        task for task in view.tasks if task.task_ref == "dev-task:follow-up"
    )
    assert follow_up.state == "claimed"
    assert follow_up.owner_node_ref == "node-ref:beast"
    assert follow_up.worktree_ref == "worktree-ref:test/follow-up"


def test_queue_allows_only_one_exclusive_developer_task(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
    )
    _register_node(
        coordinator,
        "node-ref:beast",
        idempotency_ref="idempotency-ref:register-beast",
    )
    coordinator.add_task(
        _draft("dev-task:authority-one", concurrency="exclusive"),
        idempotency_ref="idempotency-ref:add-authority-one",
    )
    coordinator.add_task(
        _draft("dev-task:authority-two", concurrency="exclusive"),
        idempotency_ref="idempotency-ref:add-authority-two",
    )
    coordinator.claim_next(
        node_ref="node-ref:mac", idempotency_ref="idempotency-ref:claim-authority-one"
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="EXCLUSIVE_WIP_LIMIT"):
        coordinator.claim_task(
            task_ref="dev-task:authority-two",
            node_ref="node-ref:beast",
            idempotency_ref="idempotency-ref:claim-authority-two",
        )


def test_blocked_task_requires_an_explicit_unblock_before_reclaim(
    tmp_path: Path,
) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
    )
    coordinator.add_task(
        _draft("dev-task:blocked"), idempotency_ref="idempotency-ref:add-blocked"
    )
    coordinator.block(
        task_ref="dev-task:blocked",
        blocker_refs=["blocker-ref:verification-failure"],
        idempotency_ref="idempotency-ref:block",
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="TASK_NOT_QUEUED"):
        coordinator.claim_task(
            task_ref="dev-task:blocked",
            node_ref="node-ref:mac",
            idempotency_ref="idempotency-ref:claim-blocked",
        )
    coordinator.unblock(
        task_ref="dev-task:blocked", idempotency_ref="idempotency-ref:unblock"
    )
    coordinator.claim_task(
        task_ref="dev-task:blocked",
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-unblocked",
    )


def test_node_registration_and_heartbeat_gate_claims(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:node-gated"),
        idempotency_ref="idempotency-ref:add-node-gated",
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="NODE_NOT_REGISTERED"):
        coordinator.claim_task(
            task_ref="dev-task:node-gated",
            node_ref="node-ref:mac",
            idempotency_ref="idempotency-ref:claim-unregistered",
        )
    with pytest.raises(ValueError, match="cannot preseed heartbeat"):
        coordinator.register_node(
            DeveloperWorkNode(
                node_ref="node-ref:mac",
                transport_ref="developer-transport-ref:test-shared-ledger",
                capabilities=[
                    "queue_claim",
                    "local_worktree",
                    "local_verification",
                ],
                heartbeat_generation=1,
                latest_heartbeat_ref="developer-node-heartbeat-ref:forged",
            ),
            idempotency_ref="idempotency-ref:register-preseeded-mac",
        )
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
        heartbeat=False,
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="NODE_NOT_READY"):
        coordinator.claim_task(
            task_ref="dev-task:node-gated",
            node_ref="node-ref:mac",
            idempotency_ref="idempotency-ref:claim-before-heartbeat",
        )
    receipt = coordinator.node_heartbeat(
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:heartbeat-mac",
    )
    assert receipt.event_kind == "node_heartbeat"
    assert coordinator.inspect().nodes[0].latest_heartbeat_ref is not None
    coordinator.claim_task(
        task_ref="dev-task:node-gated",
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-registered",
    )


def test_terminal_scope_packet_is_an_explicit_archive_gate(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
    )
    coordinator.add_task(
        _draft("dev-task:archive-gate"),
        idempotency_ref="idempotency-ref:add-archive-gate",
    )
    coordinator.claim_task(
        task_ref="dev-task:archive-gate",
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-archive-gate",
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="TASK_NOT_TERMINAL"):
        coordinator.record_terminal_scope_packet(
            task_ref="dev-task:archive-gate",
            terminal_scope_packet_ref="terminal-packet-ref:archive-gate",
            idempotency_ref="idempotency-ref:premature-archive-gate",
        )
    coordinator.complete(
        task_ref="dev-task:archive-gate",
        node_ref="node-ref:mac",
        evidence_refs=["evidence-ref:archive-gate-verifier"],
        idempotency_ref="idempotency-ref:complete-archive-gate",
    )
    receipt = coordinator.record_terminal_scope_packet(
        task_ref="dev-task:archive-gate",
        terminal_scope_packet_ref="terminal-packet-ref:archive-gate",
        idempotency_ref="idempotency-ref:archive-gate",
    )
    replay = coordinator.record_terminal_scope_packet(
        task_ref="dev-task:archive-gate",
        terminal_scope_packet_ref="terminal-packet-ref:archive-gate",
        idempotency_ref="idempotency-ref:archive-gate",
    )
    assert receipt.event_kind == "task_archive_ready"
    assert replay.replayed is True
    view = coordinator.inspect()
    assert view.archive_ready_task_refs == ["dev-task:archive-gate"]
    assert view.tasks[0].archive_ready is True


def test_ledger_snapshot_and_receipts_are_atomic_and_safe_ref_only(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "state"
    coordinator = DeveloperWorkCoordinator(state_dir=state_dir)
    coordinator.initialize(idempotency_ref="idempotency-ref:init")
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
    )
    snapshot = json.loads((state_dir / "developer_work_queue.json").read_text())
    receipts = [
        json.loads(line)
        for line in (state_dir / "developer_work_queue_receipts.jsonl")
        .read_text()
        .splitlines()
    ]
    assert snapshot["nodes"][0]["node_ref"] == "node-ref:mac"
    assert all(receipt["raw_paths_included"] is False for receipt in receipts)
    assert all(receipt["raw_content_included"] is False for receipt in receipts)
    view = coordinator.inspect()
    assert view.shell_execution_enabled is False
    assert view.git_execution_enabled is False
    assert view.remote_dispatch_enabled is False
    assert view.provider_execution_enabled is False
    assert view.product_runtime_authority_granted is False
    assert not (state_dir / ".developer_work_queue.json.tmp").exists()
    assert not (state_dir / "developer_work_queue_pending_transaction.json").exists()


@pytest.mark.parametrize("failure_target", ["snapshot", "receipt"])
def test_pending_transaction_recovers_crash_and_replays_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_target: str,
) -> None:
    state_dir = tmp_path / "state"
    coordinator = DeveloperWorkCoordinator(state_dir=state_dir)
    coordinator.initialize(idempotency_ref="idempotency-ref:init")
    method_name = (
        "_write_snapshot" if failure_target == "snapshot" else "_append_receipt"
    )
    original = getattr(coordinator, method_name)
    failed = False

    def fail_once(payload: object) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("synthetic transaction interruption")
        original(payload)

    monkeypatch.setattr(coordinator, method_name, fail_once)
    with pytest.raises(OSError, match="synthetic transaction interruption"):
        coordinator.add_task(
            _draft("dev-task:recovery"),
            idempotency_ref="idempotency-ref:add-recovery",
        )
    assert (state_dir / "developer_work_queue_pending_transaction.json").exists()

    recovered = DeveloperWorkCoordinator(state_dir=state_dir)
    replay = recovered.add_task(
        _draft("dev-task:recovery"),
        idempotency_ref="idempotency-ref:add-recovery",
    )
    assert replay.replayed is True
    view = recovered.inspect()
    assert [task.task_ref for task in view.tasks] == ["dev-task:recovery"]
    receipts = [
        json.loads(line)
        for line in (state_dir / "developer_work_queue_receipts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert (
        sum(
            receipt["idempotency_ref"] == "idempotency-ref:add-recovery"
            for receipt in receipts
        )
        == 1
    )
    assert not (state_dir / "developer_work_queue_pending_transaction.json").exists()


def test_task_admission_rejects_missing_dependencies_and_resource_collisions(
    tmp_path: Path,
) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    with pytest.raises(DeveloperWorkQueueConflictError, match="DEPENDENCY_MISSING"):
        coordinator.add_task(
            _draft(
                "dev-task:missing-dependency",
                depends_on_task_refs=["dev-task:not-recorded"],
            ),
            idempotency_ref="idempotency-ref:add-missing-dependency",
        )
    assert coordinator.inspect().tasks == []

    coordinator.add_task(
        _draft("dev-task:resource-owner"),
        idempotency_ref="idempotency-ref:add-resource-owner",
    )
    branch_collision = _draft("dev-task:branch-collision").model_copy(
        update={"branch_ref": "branch-ref:codex/resource-owner"}
    )
    with pytest.raises(DeveloperWorkQueueConflictError, match="BRANCH_REF_CONFLICT"):
        coordinator.add_task(
            branch_collision,
            idempotency_ref="idempotency-ref:add-branch-collision",
        )
    worktree_collision = _draft("dev-task:worktree-collision").model_copy(
        update={"worktree_ref": "worktree-ref:test/resource-owner"}
    )
    with pytest.raises(DeveloperWorkQueueConflictError, match="WORKTREE_REF_CONFLICT"):
        coordinator.add_task(
            worktree_collision,
            idempotency_ref="idempotency-ref:add-worktree-collision",
        )
    assert [task.task_ref for task in coordinator.inspect().tasks] == [
        "dev-task:resource-owner"
    ]


@pytest.mark.parametrize("collision_field", ["branch_ref", "worktree_ref"])
def test_concurrent_task_admission_allows_one_resource_owner(
    tmp_path: Path,
    collision_field: str,
) -> None:
    state_dir = tmp_path / "state"
    barrier = threading.Barrier(2)
    drafts = [_draft("dev-task:parallel-a"), _draft("dev-task:parallel-b")]
    if collision_field == "branch_ref":
        drafts = [
            draft.model_copy(update={"branch_ref": "branch-ref:codex/shared"})
            for draft in drafts
        ]
    else:
        drafts = [
            draft.model_copy(update={"worktree_ref": "worktree-ref:test/shared"})
            for draft in drafts
        ]

    def add(index: int) -> str:
        barrier.wait()
        try:
            DeveloperWorkCoordinator(state_dir=state_dir).add_task(
                drafts[index],
                idempotency_ref=f"idempotency-ref:add-parallel-{index}",
            )
        except DeveloperWorkQueueConflictError:
            return "conflict"
        return "added"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(add, range(2)))
    assert sorted(results) == ["added", "conflict"]
    assert len(DeveloperWorkCoordinator(state_dir=state_dir).inspect().tasks) == 1


def test_inspect_rejects_unsafe_or_duplicate_node_refs(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    with pytest.raises(ValueError):
        coordinator.inspect(node_refs=["unsafe raw node value"])
    with pytest.raises(ValueError, match="must be unique"):
        coordinator.inspect(node_refs=["node-ref:mac", "node-ref:mac"])


def test_cancel_is_explicit_idempotent_and_archive_bound(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:obsolete"),
        idempotency_ref="idempotency-ref:add-obsolete",
    )
    receipt = coordinator.cancel(
        task_ref="dev-task:obsolete",
        cancellation_reason_ref="cancellation-ref:superseded-by-accepted-scope",
        idempotency_ref="idempotency-ref:cancel-obsolete",
    )
    replay = coordinator.cancel(
        task_ref="dev-task:obsolete",
        cancellation_reason_ref="cancellation-ref:superseded-by-accepted-scope",
        idempotency_ref="idempotency-ref:cancel-obsolete",
    )
    assert receipt.event_kind == "task_canceled"
    assert replay.replayed is True
    task = coordinator.inspect().tasks[0]
    assert task.state == "canceled"
    assert task.cancellation_reason_ref == (
        "cancellation-ref:superseded-by-accepted-scope"
    )
    assert task.archive_ready is False
    coordinator.record_terminal_scope_packet(
        task_ref="dev-task:obsolete",
        terminal_scope_packet_ref="terminal-packet-ref:obsolete",
        idempotency_ref="idempotency-ref:archive-obsolete",
    )
    assert coordinator.inspect().tasks[0].archive_ready is True
    parsed = build_parser().parse_args(
        [
            "cancel",
            "--task-ref",
            "dev-task:obsolete",
            "--cancellation-reason-ref",
            "cancellation-ref:superseded-by-accepted-scope",
            "--idempotency-ref",
            "idempotency-ref:cancel-obsolete",
            "--confirm-cancel",
            "cancel-task",
        ]
    )
    assert parsed.command == "cancel"


def test_scope_disposition_requires_evidence_or_a_durable_deferral(
    tmp_path: Path,
) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:scope"), idempotency_ref="idempotency-ref:add-scope"
    )
    with pytest.raises(ValueError, match="durable follow-up"):
        DeveloperScopeDisposition(
            finding_ref="finding-ref:adjacent",
            classification="defer_safely",
            safe_summary="Adjacent hardening is deferred to preserve the bounded task.",
        )
    coordinator.record_scope_disposition(
        task_ref="dev-task:scope",
        disposition=DeveloperScopeDisposition(
            finding_ref="finding-ref:adjacent",
            classification="defer_safely",
            safe_summary="Adjacent hardening is deferred to preserve the bounded task.",
            deferred_follow_up_ref="follow-up-ref:adjacent-hardening",
        ),
        idempotency_ref="idempotency-ref:defer-adjacent",
    )
    task = coordinator.inspect().tasks[0]
    assert task.scope_dispositions[0].classification == "defer_safely"
    assert task.sol_thinking_level == "high"


def test_catalog_indexes_canonical_queue_without_dispatching(tmp_path: Path) -> None:
    board = tmp_path / "docs" / "kanban" / "current_board.md"
    board.parent.mkdir(parents=True)
    board.write_text(
        "## Backlog\n\n"
        "### FCC-P0-999 - P0 - Readable test queue entry\n\n"
        "Status: queued.\n",
        encoding="utf-8",
    )
    catalog = build_developer_planning_catalog(tmp_path)
    candidate = next(
        item
        for item in catalog.candidates
        if item.canonical_task_ref == "canonical-task-ref:fcc-p0-999"
    )
    assert candidate.priority == "p0"
    assert candidate.source_status == "queued"
    assert candidate.triage_required is True
    assert candidate.dispatch_eligible is False
    assert catalog.automatic_queue_mutation_performed is False
    assert catalog.automatic_agent_dispatch_performed is False


def test_catalog_status_is_section_bound_and_item_refs_are_stable(
    tmp_path: Path,
) -> None:
    board = tmp_path / "docs" / "kanban" / "current_board.md"
    board.parent.mkdir(parents=True)
    board.write_text(
        "## Planning\n\n"
        "### FCC-DOC-002 - Documentation follow-up\n\n"
        "No explicit status is recorded.\n\n"
        "### Unrelated notes\n\n"
        "Status: implemented.\n\n"
        "### FCC-P0-999 - P0 - Stable queue item\n\n"
        "Status: queued.\n",
        encoding="utf-8",
    )
    first = build_developer_planning_catalog(tmp_path)
    unclear = next(
        candidate
        for candidate in first.candidates
        if candidate.canonical_task_ref == "canonical-task-ref:fcc-doc-002"
    )
    stable = next(
        candidate
        for candidate in first.candidates
        if candidate.canonical_task_ref == "canonical-task-ref:fcc-p0-999"
    )
    assert unclear.source_status == "unclear"
    assert stable.planning_item_ref.endswith("/fcc-p0-999")

    board.write_text(
        "## Planning\n\n"
        "### FCC-P3-001 - P3 - Inserted earlier item\n\n"
        "Status: queued.\n\n"
        + board.read_text(encoding="utf-8").removeprefix("## Planning\n\n"),
        encoding="utf-8",
    )
    second = build_developer_planning_catalog(tmp_path)
    stable_after_insert = next(
        candidate
        for candidate in second.candidates
        if candidate.canonical_task_ref == "canonical-task-ref:fcc-p0-999"
    )
    assert stable_after_insert.planning_item_ref == stable.planning_item_ref
    assert stable_after_insert.source_anchor_ref == stable.source_anchor_ref


def test_catalog_keeps_queued_follow_up_queued_when_status_mentions_current() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    catalog = build_developer_planning_catalog(repository_root)
    candidate = next(
        item
        for item in catalog.candidates
        if item.canonical_task_ref == "canonical-task-ref:fcc-today-render-001"
    )
    assert candidate.source_status == "queued"


class _FixedRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult:
        self.commands.append(args)
        outputs = {
            ("git", "status", "--porcelain=v1", "--untracked-files=all"): (
                " M src/example.py\n?? unsafe-entry-redacted\n",
                0,
            ),
            ("git", "worktree", "list", "--porcelain"): (
                "worktree redacted-worktree-a\nHEAD abc\n\n"
                "worktree redacted-worktree-b\nHEAD def\nprunable missing\n",
                0,
            ),
            (
                "git",
                "branch",
                "--no-merged",
                "main",
                "--format=%(refname:short)|%(upstream:short)",
            ): ("codex/normal|origin/codex/normal\ncodex/token-review|\n", 0),
            ("git", "rev-list", "--left-right", "--count", "main...origin/main"): (
                "1\t3\n",
                0,
            ),
        }
        stdout, exit_code = outputs[args]
        return GitMetadataCommandResult(stdout=stdout, exit_code=exit_code)


def test_workspace_scout_redacts_metadata_and_emits_review_gates(
    tmp_path: Path,
) -> None:
    runner = _FixedRunner()
    report = DeveloperWorkspaceScout(runner=runner).inspect(repository_root=tmp_path)
    assert report.available is True
    assert report.dirty_entry_count == 2
    assert report.registered_worktree_count == 2
    assert report.prunable_worktree_count == 1
    assert report.local_main_ahead_count == 1
    assert report.local_main_behind_count == 3
    assert report.unmerged_branch_count == 2
    assert report.branch_without_upstream_count == 1
    assert report.unmerged_branches[0].display_name == "codex/normal"
    assert report.unmerged_branches[1].display_name is None
    assert {risk.severity for risk in report.risks} == {"p0", "p1"}
    assert report.git_metadata_inspection_performed is True
    assert report.git_mutation_performed is False
    assert report.merge_performed is False
    assert report.raw_paths_included is False
    assert len(runner.commands) == 4


class _FailingGitRunner(_FixedRunner):
    def __init__(self, failed_command: tuple[str, ...]) -> None:
        super().__init__()
        self.failed_command = failed_command

    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult:
        if args == self.failed_command:
            self.commands.append(args)
            return GitMetadataCommandResult(stdout="", exit_code=1)
        return super().run(args, cwd=cwd)


@pytest.mark.parametrize(
    ("failed_command", "expected_ref", "field_name"),
    [
        (
            ("git", "status", "--porcelain=v1", "--untracked-files=all"),
            "developer-git-check-ref:status",
            "dirty_entry_count",
        ),
        (
            ("git", "worktree", "list", "--porcelain"),
            "developer-git-check-ref:worktrees",
            "registered_worktree_count",
        ),
        (
            (
                "git",
                "branch",
                "--no-merged",
                "main",
                "--format=%(refname:short)|%(upstream:short)",
            ),
            "developer-git-check-ref:unmerged-branches",
            "unmerged_branch_count",
        ),
        (
            ("git", "rev-list", "--left-right", "--count", "main...origin/main"),
            "developer-git-check-ref:main-divergence",
            "local_main_ahead_count",
        ),
    ],
)
def test_workspace_scout_fails_closed_on_nonzero_git_metadata(
    tmp_path: Path,
    failed_command: tuple[str, ...],
    expected_ref: str,
    field_name: str,
) -> None:
    report = DeveloperWorkspaceScout(runner=_FailingGitRunner(failed_command)).inspect(
        repository_root=tmp_path
    )
    assert report.available is False
    assert report.git_metadata_inspection_performed is False
    assert report.unavailable_check_refs == [expected_ref]
    assert getattr(report, field_name) is None
    assert report.risks[0].risk_ref == "developer-risk-ref:git-metadata-unavailable"


def test_pull_request_scout_is_read_only_and_redacts_unsafe_metadata() -> None:
    report = DeveloperPullRequestScout().inspect_result(
        GitMetadataCommandResult(
            stdout=(
                "["
                '{"number":379,"title":"Action Inbox correction",'
                '"headRefName":"codex/action-inbox","baseRefName":"main",'
                '"isDraft":false,"mergeStateStatus":"UNSTABLE","reviewDecision":""},'
                '{"number":365,"title":"Bearer secret title",'
                '"headRefName":"codex/token-review","baseRefName":"main",'
                '"isDraft":true,"mergeStateStatus":"DIRTY","reviewDecision":""}'
                "]"
            )
        )
    )
    assert report.available is True
    assert report.open_pull_request_count == 2
    assert report.pull_requests[0].title == "Action Inbox correction"
    assert report.pull_requests[1].title == "Pull request 365 title redacted"
    assert report.pull_requests[1].head_branch_display_name is None
    assert {risk.severity for risk in report.risks} == {"p0", "p1"}
    assert report.github_read_only_inspection_performed is False
    assert report.github_mutation_performed is False


@pytest.mark.parametrize(
    "result",
    [
        GitMetadataCommandResult(stdout="[{", exit_code=0),
        GitMetadataCommandResult(stdout="{}", exit_code=0),
        GitMetadataCommandResult(stdout='[{"number":0}]', exit_code=0),
        GitMetadataCommandResult(stdout="", exit_code=1),
    ],
)
def test_pull_request_metadata_parser_fails_closed_on_unavailable_or_malformed_input(
    result: GitMetadataCommandResult,
) -> None:
    report = DeveloperPullRequestScout().inspect_result(result)
    assert report.available is False
    assert report.open_pull_request_count == 0
    assert report.github_read_only_inspection_performed is False
    assert report.risks[0].risk_ref == "developer-risk-ref:github-pr-state-unavailable"
