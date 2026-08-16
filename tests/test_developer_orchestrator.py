from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "dev"))

from uaa_developer_orchestrator.coordinator import (  # noqa: E402
    DeveloperScopeDisposition,
    DeveloperWorkCoordinator,
    DeveloperWorkQueueClaimError,
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
) -> None:
    coordinator.register_node(
        DeveloperWorkNode(
            node_ref=node_ref,
            transport_ref="developer-transport-ref:test-shared-ledger",
            capabilities=["queue_claim", "local_worktree", "local_verification"],
        ),
        idempotency_ref=idempotency_ref,
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
    assert view.revision == 7
    assert view.next_task_by_node_ref["node-ref:beast"] is None
    follow_up = next(task for task in view.tasks if task.task_ref == "dev-task:follow-up")
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


def test_blocked_task_requires_an_explicit_unblock_before_reclaim(tmp_path: Path) -> None:
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
    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-mac",
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


def test_ledger_snapshot_and_receipts_are_atomic_and_safe_ref_only(tmp_path: Path) -> None:
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
    assert not (state_dir / ".developer_work_queue.json.tmp").exists()


def test_scope_disposition_requires_evidence_or_a_durable_deferral(tmp_path: Path) -> None:
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
                " M src/example.py\n?? /Users/example/private.txt\n",
                0,
            ),
            ("git", "worktree", "list", "--porcelain"): (
                "worktree /Users/example/repo\nHEAD abc\n\n"
                "worktree /private/tmp/old\nHEAD def\nprunable missing\n",
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


def test_workspace_scout_redacts_metadata_and_emits_review_gates(tmp_path: Path) -> None:
    runner = _FixedRunner()
    report = DeveloperWorkspaceScout(runner=runner).inspect(repository_root=tmp_path)
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


class _PullRequestRunner:
    def run(self, args: tuple[str, ...], *, cwd: Path) -> GitMetadataCommandResult:
        assert args[:3] == ("gh", "pr", "list")
        return GitMetadataCommandResult(
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


def test_pull_request_scout_is_read_only_and_redacts_unsafe_metadata(
    tmp_path: Path,
) -> None:
    report = DeveloperPullRequestScout(runner=_PullRequestRunner()).inspect(
        repository_root=tmp_path
    )
    assert report.available is True
    assert report.open_pull_request_count == 2
    assert report.pull_requests[0].title == "Action Inbox correction"
    assert report.pull_requests[1].title == "Pull request 365 title redacted"
    assert report.pull_requests[1].head_branch_display_name is None
    assert {risk.severity for risk in report.risks} == {"p0", "p1"}
    assert report.github_read_only_inspection_performed is True
    assert report.github_mutation_performed is False
