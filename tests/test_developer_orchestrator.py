from __future__ import annotations

import json
import subprocess as _subprocess
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "dev"))

import uaa_developer_orchestrator.coordinator as coordinator_module  # noqa: E402
from uaa_developer_orchestrator.coordinator import (  # noqa: E402
    DeveloperScopeDisposition,
    DeveloperWorkCoordinator,
    DeveloperWorkQueueClaimError,
    DeveloperWorkQueueConflictError,
    DeveloperWorkNode,
    DeveloperWorkTask,
    DeveloperWorkTaskDraft,
)
from uaa_developer_orchestrator.planning import (  # noqa: E402
    build_developer_planning_catalog,
)
from uaa_developer_orchestrator.queue_record import (  # noqa: E402
    assess_developer_queue_record_health,
    build_developer_queue_record_drafts,
    load_developer_queue_record_manifest,
    queue_record_canonical_item_contract_ref,
    queue_record_task_contract_ref,
)
from uaa_developer_orchestrator.recovery import (  # noqa: E402
    assess_developer_queue_recovery_health,
    build_developer_queue_recovery_drafts,
    load_developer_queue_recovery_manifest,
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
    wip_lane: str = "shared_core",
    queue_order: int = 100000,
    depends_on_task_refs: list[str] | None = None,
) -> DeveloperWorkTaskDraft:
    suffix = task_ref.removeprefix("dev-task:")
    return DeveloperWorkTaskDraft(
        task_ref=task_ref,
        queue_order=queue_order,
        title=f"Developer task {suffix}",
        safe_summary="A bounded developer task with no implied execution authority.",
        priority=priority,
        concurrency=concurrency,
        wip_lane=wip_lane,
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


class _HistoricalMergeSubprocess:
    """Keep merge-gate fixtures bound to the immutable PR #425 revision."""

    @staticmethod
    def run(args: list[str], **kwargs: object) -> _subprocess.CompletedProcess[str]:
        if args == ["git", "rev-parse", "refs/remotes/origin/main"]:
            args = [
                "git",
                "log",
                "--format=%H",
                "--fixed-strings",
                "--grep=(#425)",
                "-1",
                "refs/remotes/origin/main",
            ]
        return _subprocess.run(args, **kwargs)  # type: ignore[call-overload]


def _inject_legacy_queue_task(
    coordinator: DeveloperWorkCoordinator,
    draft: DeveloperWorkTaskDraft,
    *,
    state: str = "queued",
) -> None:
    """Model a pre-hardening durable record without reopening legacy admission."""

    snapshot = json.loads(coordinator.state_path.read_text(encoding="utf-8"))
    task = DeveloperWorkTask(
        **draft.model_dump(mode="json"),
        state=state,
        completion_evidence_refs=(
            ["evidence-ref:legacy-completion"] if state == "completed" else []
        ),
    )
    snapshot["tasks"].append(task.model_dump(mode="json"))
    coordinator.state_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


subprocess = _HistoricalMergeSubprocess()


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
        _draft(
            "dev-task:authority-one",
            concurrency="exclusive",
            wip_lane="shared_core",
        ),
        idempotency_ref="idempotency-ref:add-authority-one",
    )
    coordinator.add_task(
        _draft(
            "dev-task:authority-two",
            concurrency="exclusive",
            wip_lane="product_surface",
        ),
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


def test_queue_enforces_three_claim_global_wip_limit(tmp_path: Path) -> None:
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
    lanes = [
        "shared_core",
        "product_surface",
        "verification_read_only",
        "shared_core",
    ]
    for index in range(4):
        coordinator.add_task(
            _draft(f"dev-task:global-wip-{index}", wip_lane=lanes[index]),
            idempotency_ref=f"idempotency-ref:add-global-wip-{index}",
        )
    for index, node_ref in enumerate(
        ["node-ref:mac", "node-ref:mac", "node-ref:beast"]
    ):
        coordinator.claim_task(
            task_ref=f"dev-task:global-wip-{index}",
            node_ref=node_ref,
            idempotency_ref=f"idempotency-ref:claim-global-wip-{index}",
        )

    with pytest.raises(DeveloperWorkQueueClaimError, match="GLOBAL_WIP_LIMIT"):
        coordinator.claim_task(
            task_ref="dev-task:global-wip-3",
            node_ref="node-ref:beast",
            idempotency_ref="idempotency-ref:claim-global-wip-3",
        )
    view = coordinator.inspect(node_refs=["node-ref:mac", "node-ref:beast"])
    assert view.global_wip_limit == 3
    assert view.wip_lane_limit == 1
    assert view.active_task_by_wip_lane == {
        "shared_core": "dev-task:global-wip-0",
        "product_surface": "dev-task:global-wip-1",
        "verification_read_only": "dev-task:global-wip-2",
    }
    assert view.next_task_by_node_ref == {
        "node-ref:mac": None,
        "node-ref:beast": None,
    }


def test_queue_allows_only_one_claim_per_wip_lane(tmp_path: Path) -> None:
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
    for suffix in ["one", "two"]:
        coordinator.add_task(
            _draft(
                f"dev-task:lane-{suffix}",
                wip_lane="verification_read_only",
            ),
            idempotency_ref=f"idempotency-ref:add-lane-{suffix}",
        )
    coordinator.claim_task(
        task_ref="dev-task:lane-one",
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-lane-one",
    )
    with pytest.raises(DeveloperWorkQueueClaimError, match="WIP_LANE_LIMIT"):
        coordinator.claim_task(
            task_ref="dev-task:lane-two",
            node_ref="node-ref:beast",
            idempotency_ref="idempotency-ref:claim-lane-two",
        )


def test_recovery_manifest_materializes_the_stranded_program() -> None:
    manifest = load_developer_queue_recovery_manifest(ROOT)
    drafts = build_developer_queue_recovery_drafts(ROOT)

    assert len(manifest.items) == 11
    assert len(drafts) == 11
    assert manifest.recovery_policy.max_parallel_claims == 3
    assert manifest.recovery_policy.queue_starvation_is_failure is True
    assert {item.item_id for item in manifest.items} >= {
        "queue-03-hermes-openclaw-parity",
        "calendar-read-only-product-lane",
        "first-class-crm",
        "queue-07-news-signals",
        "queue-09-final-goat-comparison",
    }
    assert all(draft.acceptance_refs for draft in drafts)
    assert all(draft.verifier_refs for draft in drafts)
    assert drafts[-1].concurrency == "exclusive"
    assert len(drafts[-1].depends_on_task_refs) == 10


def test_recovery_manifest_fails_closed_on_prompt_drift(tmp_path: Path) -> None:
    recovery_root = tmp_path / "repository"
    (recovery_root / "docs" / "roadmap").mkdir(parents=True)
    shutil.copy2(
        ROOT / "docs" / "roadmap" / "UAA_REMAINING_QUEUE_MANIFEST.json",
        recovery_root / "docs" / "roadmap" / "UAA_REMAINING_QUEUE_MANIFEST.json",
    )
    shutil.copy2(
        ROOT / "docs" / "roadmap" / "UAA_DEVELOPER_QUEUE_RECOVERY_MANIFEST.json",
        recovery_root
        / "docs"
        / "roadmap"
        / "UAA_DEVELOPER_QUEUE_RECOVERY_MANIFEST.json",
    )
    shutil.copytree(
        ROOT / "docs" / "prompts" / "remaining_queue_recovery",
        recovery_root / "docs" / "prompts" / "remaining_queue_recovery",
    )
    prompt = (
        recovery_root
        / "docs"
        / "prompts"
        / "remaining_queue_recovery"
        / "01_hermes_openclaw_parity.md"
    )
    prompt.write_text(
        prompt.read_text(encoding="utf-8") + "\ndrift\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="SOURCE_DIGEST_MISMATCH"):
        load_developer_queue_recovery_manifest(recovery_root)


def test_recovery_health_escalates_zero_admission_as_starvation(
    tmp_path: Path,
) -> None:
    manifest = load_developer_queue_recovery_manifest(ROOT)
    health = assess_developer_queue_recovery_health(manifest=manifest, task_states={})
    assert health.admission_gap_detected is True
    assert health.queue_starvation_detected is True
    assert health.risk_ref == "developer-risk-ref:recovery-queue-starvation"

    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    for index, draft in enumerate(build_developer_queue_recovery_drafts(ROOT)):
        coordinator.add_task(
            draft,
            idempotency_ref=f"idempotency-ref:recovery-admission-{index}",
        )
    view = coordinator.inspect()
    admitted_health = assess_developer_queue_recovery_health(
        manifest=manifest,
        task_states={task.task_ref: task.state for task in view.tasks},
    )
    assert admitted_health.admission_gap_detected is False
    assert admitted_health.queue_starvation_detected is False
    assert admitted_health.admitted_recovery_item_count == 11
    assert admitted_health.nonterminal_recovery_item_count == 11


def test_queue_v2_manifest_materializes_authoritative_order() -> None:
    manifest = load_developer_queue_record_manifest(ROOT)
    drafts = build_developer_queue_record_drafts(ROOT)

    assert len(manifest.items) == 37
    assert len(manifest.gated_items) == 11
    assert len(drafts) == 37
    assert [item.item_id for item in manifest.items] == [
        f"Q{index:02d}" for index in range(37)
    ]
    assert [draft.queue_order for draft in drafts] == list(range(37))
    assert [draft.wip_lane for draft in drafts[:3]] == [
        "product_surface",
        "shared_core",
        "verification_read_only",
    ]
    assert manifest.items[0].existing_owner_ref is not None
    assert manifest.items[1].existing_owner_ref is not None
    assert "Q22" in manifest.items[31].depends_on_item_ids
    assert "Q26" not in manifest.items[31].depends_on_item_ids
    assert "scope-ref:queue-v2/Q31/chat-surface-direct-observation" in (
        manifest.items[31].scope_refs
    )
    assert manifest.items[32].depends_on_item_ids == ["Q15", "Q31"]
    assert "scope-ref:queue-v2/Q33/chat-usability-parity" in (
        manifest.items[33].scope_refs
    )
    assert manifest.items[-1].depends_on_item_ids == ["Q32", "Q33", "Q34", "Q35"]
    assert manifest.policy.legacy_recovery_admission_enabled is False


def test_queue_v2_cli_supersedes_recovery_and_is_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "state"
    parser = build_parser()
    inspection = parser.parse_args(["--state-dir", str(state_dir), "inspect"])
    assert inspection.func(inspection) == 0
    empty_payload = json.loads(capsys.readouterr().out)
    assert empty_payload["queue_of_record_health"]["queue_starvation_detected"] is True
    assert empty_payload["legacy_recovery_status"]["admission_enabled"] is False

    missing_confirmation = parser.parse_args(
        [
            "--state-dir",
            str(state_dir),
            "recover-remaining-queue",
            "--idempotency-prefix",
            "idempotency-ref:remaining-queue-recovery-v1",
            "--confirm-recovery",
            "wrong",
        ]
    )
    with pytest.raises(ValueError, match="RECOVERY_SUPERSEDED_BY_V2"):
        missing_confirmation.func(missing_confirmation)

    admitted = parser.parse_args(
        [
            "--state-dir",
            str(state_dir),
            "admit-queue-v2",
            "--idempotency-prefix",
            "idempotency-ref:queue-v2-admission",
            "--confirm-admission",
            "admit-queue-v2",
        ]
    )
    assert admitted.func(admitted) == 0
    first_payload = json.loads(capsys.readouterr().out)
    assert first_payload["replayed_receipt_count"] == 0
    assert first_payload["queue_of_record_health"]["admission_gap_detected"] is False

    assert admitted.func(admitted) == 0
    replay_payload = json.loads(capsys.readouterr().out)
    assert replay_payload["replayed_receipt_count"] == 37
    view = DeveloperWorkCoordinator(state_dir=state_dir).inspect()
    assert len(view.tasks) == 37
    assert [task.queue_order for task in view.tasks] == list(range(37))

    health = assess_developer_queue_record_health(
        manifest=load_developer_queue_record_manifest(ROOT),
        task_states={task.task_ref: task.state for task in view.tasks},
        task_contract_refs={
            task.task_ref: queue_record_task_contract_ref(task)
            for task in view.tasks
        },
    )
    assert health.queue_starvation_detected is False
    assert health.admitted_item_count == 37


def test_queue_v2_cli_selectively_admits_a_manifest_extension(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "state"
    coordinator = DeveloperWorkCoordinator(state_dir=state_dir)
    drafts = build_developer_queue_record_drafts(ROOT)
    for draft in drafts[:31]:
        coordinator.add_task(
            draft,
            idempotency_ref=(
                "idempotency-ref:queue-v2-existing:"
                f"{draft.task_ref.removeprefix('dev-task:')}"
            ),
        )
    legacy_q31 = DeveloperWorkTaskDraft.model_validate_json(
        (ROOT / "tests/fixtures/developer_queue_v2_q31_pre_chat_observation.json")
        .read_text(encoding="utf-8")
    )
    _inject_legacy_queue_task(coordinator, legacy_q31)

    pre_amendment_view = coordinator.inspect()
    pre_amendment_health = assess_developer_queue_record_health(
        manifest=load_developer_queue_record_manifest(ROOT),
        task_states={task.task_ref: task.state for task in pre_amendment_view.tasks},
        task_contract_refs={
            task.task_ref: queue_record_task_contract_ref(task)
            for task in pre_amendment_view.tasks
        },
    )
    assert pre_amendment_health.record_drift_detected is True
    assert pre_amendment_health.stale_contract_task_refs == [legacy_q31.task_ref]

    parser = build_parser()
    q31_replacement = build_developer_queue_record_drafts(ROOT)[31]
    amendment_idempotency_ref = (
        "idempotency-ref:queue-v2-q31-chat-observation-amendment"
    )
    amendment_actor = coordinator_module.ActorContext(
        actor_type="human_user",
        actor_id="local_test_operator",
        authority_source="explicit_user_request",
    )
    amendment_scope_ref = (
        coordinator_module.build_developer_work_task_amendment_approval_request(
            q31_replacement,
            expected_current_fingerprint_ref=(
                legacy_q31.canonical_source_fingerprint_ref
            ),
            idempotency_ref=amendment_idempotency_ref,
            actor_context=amendment_actor,
        ).resource_refs[0]
    )
    revision_before_preview = coordinator.inspect().revision
    preview = parser.parse_args(
        [
            "--state-dir",
            str(state_dir),
            "preview-queue-v2-amendment",
            "--item-id",
            "Q31",
            "--expected-current-fingerprint-ref",
            legacy_q31.canonical_source_fingerprint_ref,
            "--idempotency-ref",
            amendment_idempotency_ref,
        ]
    )
    assert preview.func(preview) == 0
    preview_payload = json.loads(capsys.readouterr().out)
    assert preview_payload["approval_scope_ref"] == amendment_scope_ref
    assert preview_payload["queue_mutation_performed"] is False
    assert coordinator.inspect().revision == revision_before_preview
    amendment = parser.parse_args(
        [
            "--state-dir",
            str(state_dir),
            "amend-queue-v2-item",
            "--item-id",
            "Q31",
            "--expected-current-fingerprint-ref",
            legacy_q31.canonical_source_fingerprint_ref,
            "--idempotency-ref",
            amendment_idempotency_ref,
            "--confirm-amendment",
            "amend-queue-v2-item",
            "--approve-exact-scope",
            amendment_scope_ref,
        ]
    )
    assert amendment.func(amendment) == 0
    amendment_payload = json.loads(capsys.readouterr().out)
    assert amendment_payload["item_id"] == "Q31"
    assert amendment_payload["replayed"] is False
    assert amendment_payload["queue_of_record_health"]["record_drift_detected"] is False
    amended_q31 = next(
        task for task in coordinator.inspect().tasks if task.task_ref == legacy_q31.task_ref
    )
    assert "scope-ref:queue-v2/Q31/chat-surface-direct-observation" in (
        amended_q31.in_scope_refs
    )
    amendment_receipt = json.loads(
        coordinator.receipts_path.read_text(encoding="utf-8").splitlines()[-1]
    )
    assert amendment_receipt["approval_scope_ref"] == amendment_scope_ref
    assert amendment_receipt["approval_ref"].startswith(
        "approval-ref:developer-queue-amendment-"
    )
    assert amendment_receipt["approving_actor_ref"].startswith("actor-ref:sha256:")
    assert amendment_receipt["prior_fingerprint_ref"] == (
        legacy_q31.canonical_source_fingerprint_ref
    )
    assert amendment_receipt["approval_proof_ref"].startswith(
        "developer-work-approval-proof-ref:sha256:"
    )
    with pytest.raises(ValueError, match="approval proof is not bound"):
        coordinator_module.DeveloperWorkQueueReceipt.model_validate(
            {
                **amendment_receipt,
                "approval_scope_ref": "developer-work-amendment-scope-ref:sha256:tampered",
            }
        )

    assert amendment.func(amendment) == 0
    replayed_amendment = json.loads(capsys.readouterr().out)
    assert replayed_amendment["replayed"] is True

    selected_args = [
        "--state-dir",
        str(state_dir),
        "admit-queue-v2",
        "--idempotency-prefix",
        "idempotency-ref:queue-v2-functional-adoption",
        "--confirm-admission",
        "admit-queue-v2",
    ]
    for index in reversed(range(32, 37)):
        selected_args.extend(["--item-id", f"Q{index:02d}"])
    selected = parser.parse_args(selected_args)

    assert selected.func(selected) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected_item_ids"] == ["Q32", "Q33", "Q34", "Q35", "Q36"]
    assert payload["replayed_receipt_count"] == 0
    assert payload["queue_of_record_health"]["admission_gap_detected"] is False
    view = coordinator.inspect()
    assert len(view.tasks) == 37
    assert [task.queue_order for task in view.tasks] == list(range(37))

    assert selected.func(selected) == 0
    replay_payload = json.loads(capsys.readouterr().out)
    assert replay_payload["replayed_receipt_count"] == 5

    snapshot = json.loads(coordinator.state_path.read_text(encoding="utf-8"))
    for task in snapshot["tasks"]:
        if task["task_ref"] in {
            drafts[15].task_ref,
            q31_replacement.task_ref,
        }:
            task["state"] = "completed"
            task["completion_evidence_refs"] = [
                "evidence-ref:dependency-completed"
            ]
    coordinator.state_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        coordinator_module,
        "REPO_ROOT",
        tmp_path / "unrelated-worktree-without-manifest",
    )
    q32_view = next(
        task for task in coordinator.inspect().tasks if task.task_ref == drafts[32].task_ref
    )
    assert q32_view.dependency_ready is True
    assert set(q32_view.dependency_contract_refs) == set(q32_view.depends_on_task_refs)


def test_queue_v2_cli_rejects_duplicate_selective_admission(
    tmp_path: Path,
) -> None:
    parser = build_parser()
    selected = parser.parse_args(
        [
            "--state-dir",
            str(tmp_path / "state"),
            "admit-queue-v2",
            "--idempotency-prefix",
            "idempotency-ref:queue-v2-functional-adoption",
            "--confirm-admission",
            "admit-queue-v2",
            "--item-id",
            "Q32",
            "--item-id",
            "Q32",
        ]
    )

    with pytest.raises(ValueError, match="DUPLICATE_ITEM_SELECTION"):
        selected.func(selected)


def test_queue_v2_namespace_rejects_counterfeit_contract(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    counterfeit = build_developer_queue_record_drafts(ROOT)[32].model_copy(
        update={"depends_on_task_refs": []}
    )

    with pytest.raises(
        DeveloperWorkQueueConflictError,
        match="CANONICAL_TASK_CONTRACT_INVALID",
    ):
        coordinator.add_task(
            counterfeit,
            idempotency_ref="idempotency-ref:add-counterfeit-q32",
        )


def test_queue_v2_item_contract_binds_source_refs_without_global_drift() -> None:
    drafts = build_developer_queue_record_drafts(ROOT)
    q31 = drafts[31]
    changed_q31 = q31.model_copy(
        update={
            "canonical_source_refs": [
                *q31.canonical_source_refs,
                "repo-ref:queue-v2/source-only-change",
            ],
            "canonical_item_contract_ref": None,
        }
    )

    assert queue_record_canonical_item_contract_ref(changed_q31) != (
        q31.canonical_item_contract_ref
    )
    assert queue_record_canonical_item_contract_ref(drafts[30]) == (
        drafts[30].canonical_item_contract_ref
    )


def test_queue_v2_legacy_source_acceptance_fails_after_source_drift(
    tmp_path: Path,
) -> None:
    target = tmp_path / "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json"
    target.parent.mkdir(parents=True)
    payload = json.loads(
        (ROOT / "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    q15 = next(item for item in payload["items"] if item["item_id"] == "Q15")
    q15["source_refs"].append("canonical-task-ref:CRM-FC-SOURCE-DRIFT")
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="MANIFEST_INVALID"):
        load_developer_queue_record_manifest(tmp_path)


def test_task_amendment_requires_exact_fingerprint_and_pristine_queue(
    tmp_path: Path,
) -> None:
    def amendment_approval(
        draft: DeveloperWorkTaskDraft,
        *,
        expected_current_fingerprint_ref: str,
        idempotency_ref: str,
    ) -> tuple[object, str, object]:
        actor_context = coordinator_module.ActorContext(
            actor_type="human_user",
            actor_id="local_test_operator",
            authority_source="explicit_user_request",
        )
        request = (
            coordinator_module.build_developer_work_task_amendment_approval_request(
                draft,
                expected_current_fingerprint_ref=expected_current_fingerprint_ref,
                idempotency_ref=idempotency_ref,
                actor_context=actor_context,
            )
        )
        authority = coordinator_module.LocalApprovalAuthority()
        authority.create_request(request)
        approval_ref = (
            "approval-ref:test-developer-queue-amendment-"
            f"{request.resource_refs[0].rsplit(':', maxsplit=1)[-1]}"
        )
        authority.grant(
            request.approval_request_id,
            approved_by_actor_id=actor_context.actor_id,
            approval_ref=approval_ref,
        )
        return authority, approval_ref, actor_context

    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    original = _draft("dev-task:amend")
    replacement = original.model_copy(
        update={
            "canonical_source_fingerprint_ref": (
                "planning-fingerprint-ref:sha256:replacement"
            ),
            "in_scope_refs": ["scope-ref:amend/owned", "scope-ref:amend/expanded"],
        }
    )
    coordinator.add_task(original, idempotency_ref="idempotency-ref:add-amend")

    missing_approval_actor = coordinator_module.ActorContext(
        actor_type="human_user",
        actor_id="local_test_operator",
        authority_source="explicit_user_request",
    )
    with pytest.raises(
        DeveloperWorkQueueConflictError,
        match="AMENDMENT_APPROVAL_INVALID",
    ):
        coordinator.amend_queued_task(
            replacement,
            expected_current_fingerprint_ref=(
                original.canonical_source_fingerprint_ref
            ),
            idempotency_ref="idempotency-ref:amend-without-approval",
            approval_authority=coordinator_module.LocalApprovalAuthority(),
            approval_ref="approval-ref:unknown-amendment",
            actor_context=missing_approval_actor,
        )

    wrong_fingerprint_ref = "planning-fingerprint-ref:sha256:wrong"
    wrong_idempotency_ref = "idempotency-ref:amend-wrong-fingerprint"
    wrong_authority, wrong_approval_ref, wrong_actor = amendment_approval(
        replacement,
        expected_current_fingerprint_ref=wrong_fingerprint_ref,
        idempotency_ref=wrong_idempotency_ref,
    )
    with pytest.raises(
        DeveloperWorkQueueConflictError,
        match="AMENDMENT_FINGERPRINT_CONFLICT",
    ):
        coordinator.amend_queued_task(
            replacement,
            expected_current_fingerprint_ref=wrong_fingerprint_ref,
            idempotency_ref=wrong_idempotency_ref,
            approval_authority=wrong_authority,
            approval_ref=wrong_approval_ref,
            actor_context=wrong_actor,
        )

    _register_node(
        coordinator,
        "node-ref:mac",
        idempotency_ref="idempotency-ref:register-amend-node",
    )
    coordinator.claim_task(
        task_ref=original.task_ref,
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-amend",
    )
    with pytest.raises(
        DeveloperWorkQueueConflictError,
        match="AMENDMENT_STATE_INVALID",
    ):
        claimed_idempotency_ref = "idempotency-ref:amend-claimed"
        claimed_authority, claimed_approval_ref, claimed_actor = amendment_approval(
            replacement,
            expected_current_fingerprint_ref=(
                original.canonical_source_fingerprint_ref
            ),
            idempotency_ref=claimed_idempotency_ref,
        )
        coordinator.amend_queued_task(
            replacement,
            expected_current_fingerprint_ref=(
                original.canonical_source_fingerprint_ref
            ),
            idempotency_ref=claimed_idempotency_ref,
            approval_authority=claimed_authority,
            approval_ref=claimed_approval_ref,
            actor_context=claimed_actor,
        )


def test_stale_completed_q31_does_not_unlock_q32(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    drafts = build_developer_queue_record_drafts(ROOT)
    for draft in drafts[:31]:
        coordinator.add_task(
            draft,
            idempotency_ref=(
                "idempotency-ref:add-current-prerequisite:"
                f"{draft.task_ref.removeprefix('dev-task:')}"
            ),
        )
    legacy_q31 = drafts[31].model_copy(
        update={
            "canonical_source_fingerprint_ref": (
                "planning-fingerprint-ref:sha256:172be181716f7b8863a28b37"
            ),
            "canonical_source_refs": [],
            "canonical_item_contract_ref": None,
        }
    )
    _inject_legacy_queue_task(coordinator, legacy_q31, state="completed")
    q32 = drafts[32]
    with pytest.raises(
        DeveloperWorkQueueConflictError,
        match="CANONICAL_DEPENDENCY_CONTRACT_INVALID",
    ):
        coordinator.add_task(
            q32,
            idempotency_ref="idempotency-ref:add-q32-after-stale-q31",
        )
    assert q32.task_ref not in {task.task_ref for task in coordinator.inspect().tasks}


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
        task_ref="dev-task:blocked",
        expected_blocker_ref="blocker-ref:verification-failure",
        evidence_ref="evidence-ref:verification-reviewed",
        idempotency_ref="idempotency-ref:unblock",
    )
    coordinator.claim_task(
        task_ref="dev-task:blocked",
        node_ref="node-ref:mac",
        idempotency_ref="idempotency-ref:claim-unblocked",
    )


def test_unblock_rejects_blocker_set_drift(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:blocked-drift"),
        idempotency_ref="idempotency-ref:add-blocked-drift",
    )
    coordinator.block(
        task_ref="dev-task:blocked-drift",
        blocker_refs=[
            "blocker-ref:pr425-activation-merge-pending",
            "blocker-ref:independent-review-pending",
        ],
        idempotency_ref="idempotency-ref:block-drift",
    )

    current_revision = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    with pytest.raises(
        DeveloperWorkQueueClaimError, match="UNBLOCK_BLOCKER_SET_DRIFTED"
    ):
        coordinator.unblock(
            task_ref="dev-task:blocked-drift",
            expected_blocker_ref="blocker-ref:pr425-activation-merge-pending",
            evidence_ref=f"merge-commit-ref:{current_revision}",
            idempotency_ref="idempotency-ref:unblock-drift",
        )

    task = next(
        task
        for task in coordinator.inspect().tasks
        if task.task_ref == "dev-task:blocked-drift"
    )
    assert task.state == "blocked"
    assert task.blocker_refs == [
        "blocker-ref:pr425-activation-merge-pending",
        "blocker-ref:independent-review-pending",
    ]


def test_merge_gated_unblock_requires_current_history_commit(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:merge-gated"),
        idempotency_ref="idempotency-ref:add-merge-gated",
    )
    coordinator.block(
        task_ref="dev-task:merge-gated",
        blocker_refs=["blocker-ref:pr426-activation-merge-pending"],
        idempotency_ref="idempotency-ref:block-merge-gated",
    )

    current_main = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    for evidence_ref in (
        "evidence-ref:anything",
        "merge-commit-ref:activation-record",
        f"merge-commit-ref:{'f' * 40}",
        f"merge-commit-ref:{current_main}",
    ):
        with pytest.raises(DeveloperWorkQueueClaimError, match="MERGE_COMMIT"):
            coordinator.unblock(
                task_ref="dev-task:merge-gated",
                expected_blocker_ref="blocker-ref:pr426-activation-merge-pending",
                evidence_ref=evidence_ref,
                idempotency_ref=f"idempotency-ref:unblock-{evidence_ref.split(':')[-1]}",
            )

    task = next(
        item
        for item in coordinator.inspect().tasks
        if item.task_ref == "dev-task:merge-gated"
    )
    assert task.state == "blocked"


def test_merge_gated_unblock_accepts_current_history_commit(tmp_path: Path) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:merge-gated-valid"),
        idempotency_ref="idempotency-ref:add-merge-gated-valid",
    )
    coordinator.block(
        task_ref="dev-task:merge-gated-valid",
        blocker_refs=["blocker-ref:pr425-activation-merge-pending"],
        idempotency_ref="idempotency-ref:block-merge-gated-valid",
    )
    current_revision = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    coordinator.unblock(
        task_ref="dev-task:merge-gated-valid",
        expected_blocker_ref="blocker-ref:pr425-activation-merge-pending",
        evidence_ref=f"merge-commit-ref:{current_revision}",
        idempotency_ref="idempotency-ref:unblock-merge-gated-valid",
    )

    task = next(
        item
        for item in coordinator.inspect().tasks
        if item.task_ref == "dev-task:merge-gated-valid"
    )
    assert task.state == "queued"


def test_successful_unblock_replays_before_git_revalidation(
    tmp_path: Path, monkeypatch
) -> None:
    coordinator = DeveloperWorkCoordinator(state_dir=tmp_path / "state")
    coordinator.add_task(
        _draft("dev-task:merge-gated-replay"),
        idempotency_ref="idempotency-ref:add-merge-gated-replay",
    )
    coordinator.block(
        task_ref="dev-task:merge-gated-replay",
        blocker_refs=["blocker-ref:pr425-activation-merge-pending"],
        idempotency_ref="idempotency-ref:block-merge-gated-replay",
    )
    merged_revision = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    kwargs = {
        "task_ref": "dev-task:merge-gated-replay",
        "expected_blocker_ref": "blocker-ref:pr425-activation-merge-pending",
        "evidence_ref": f"merge-commit-ref:{merged_revision}",
        "idempotency_ref": "idempotency-ref:unblock-merge-gated-replay",
    }
    first = coordinator.unblock(**kwargs)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Git evidence must not be revalidated during replay")

    monkeypatch.setattr(coordinator_module.subprocess, "run", fail_if_called)

    replay = coordinator.unblock(**kwargs)

    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref


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


def test_catalog_does_not_emit_completed_authority_conveyor_as_active(
    tmp_path: Path,
) -> None:
    board = tmp_path / "docs" / "kanban" / "current_board.md"
    board.parent.mkdir(parents=True)
    board.write_text(
        "## Runtime lane\n\n"
        "UAA-P1-091 Governed Runtime Pilot is a completed scoped internal lane.\n",
        encoding="utf-8",
    )

    catalog = build_developer_planning_catalog(tmp_path)

    assert all(
        candidate.canonical_task_ref != "canonical-task-ref:uaa-p1-091"
        for candidate in catalog.candidates
    )


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
