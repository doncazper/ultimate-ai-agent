#!/usr/bin/env python3
"""Local-only developer queue coordination for explicit Mac/Beast handoffs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from uaa_developer_orchestrator.coordinator import (  # noqa: E402
    DeveloperScopeDisposition,
    DeveloperWorkCoordinator,
    DeveloperWorkQueueError,
    DeveloperWorkNode,
    DeveloperWorkTaskDraft,
    build_developer_work_task_amendment_approval_request,
)
from uaa_developer_orchestrator.planning import (  # noqa: E402
    build_developer_planning_catalog,
    find_planning_candidate,
)
from uaa_developer_orchestrator.queue_record import (  # noqa: E402
    assess_developer_queue_record_health,
    build_developer_queue_record_drafts,
    load_developer_queue_record_manifest,
    queue_record_health_contract_refs,
)
from uaa_developer_orchestrator.scout import (  # noqa: E402
    DeveloperWorkspaceScout,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.hygiene.actor_context import (  # noqa: E402
    ActorContext,
    ActorType,
    AuthoritySource,
)


def _coordinator(args: argparse.Namespace) -> DeveloperWorkCoordinator:
    state_dir = Path(args.state_dir).expanduser() if args.state_dir else None
    return DeveloperWorkCoordinator(state_dir=state_dir)


def _print(payload: object, *, pretty: bool) -> int:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))
    return 0


def catalog(args: argparse.Namespace) -> int:
    return _print(build_developer_planning_catalog(ROOT), pretty=args.pretty)


def initialize(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).initialize(idempotency_ref=args.idempotency_ref),
        pretty=args.pretty,
    )


def register_node(args: argparse.Namespace) -> int:
    if args.confirm_register != "register-node":
        raise ValueError("DEVELOPER_QUEUE_NODE_REGISTRATION_CONFIRMATION_REQUIRED")
    return _print(
        _coordinator(args).register_node(
            DeveloperWorkNode(
                node_ref=args.node_ref,
                transport_ref=args.transport_ref,
                readiness=args.readiness,
                capabilities=args.capability,
            ),
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def node_heartbeat(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).node_heartbeat(
            node_ref=args.node_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def triage(args: argparse.Namespace) -> int:
    if args.confirm_triage != "triage":
        raise ValueError("DEVELOPER_QUEUE_TRIAGE_CONFIRMATION_REQUIRED")
    candidate = find_planning_candidate(
        build_developer_planning_catalog(ROOT), args.planning_item_ref
    )
    priority = args.priority or candidate.priority
    if priority is None:
        raise ValueError("DEVELOPER_QUEUE_PRIORITY_REQUIRED")
    draft = DeveloperWorkTaskDraft(
        task_ref=args.task_ref,
        queue_order=args.queue_order,
        title=candidate.title,
        safe_summary=candidate.safe_summary,
        priority=priority,
        concurrency=args.concurrency,
        wip_lane=args.wip_lane,
        canonical_task_ref=candidate.canonical_task_ref,
        canonical_source_ref=candidate.canonical_source_ref,
        canonical_source_fingerprint_ref=candidate.canonical_source_fingerprint_ref,
        scope_contract_ref=args.scope_contract_ref,
        in_scope_refs=args.in_scope_ref,
        out_of_scope_refs=args.out_of_scope_ref,
        sol_thinking_level=args.sol_thinking,
        branch_ref=args.branch_ref,
        worktree_ref=args.worktree_ref,
        workstream_ref=args.workstream_ref,
        acceptance_refs=args.acceptance_ref,
        verifier_refs=args.verifier_ref,
        merge_gate_refs=args.merge_gate_ref,
        depends_on_task_refs=args.depends_on_task_ref,
        next_safe_action=args.next_safe_action,
    )
    return _print(
        _coordinator(args).add_task(draft, idempotency_ref=args.idempotency_ref),
        pretty=args.pretty,
    )


def inspect(args: argparse.Namespace) -> int:
    coordinator = _coordinator(args)
    queue = coordinator.inspect(node_refs=args.node_ref)
    queue_manifest = load_developer_queue_record_manifest(ROOT)
    payload: dict[str, object] = {
        "queue": queue.model_dump(mode="json"),
        "queue_of_record_health": assess_developer_queue_record_health(
            manifest=queue_manifest,
            task_states={task.task_ref: task.state for task in queue.tasks},
            task_contract_refs=queue_record_health_contract_refs(
                queue_manifest, queue.tasks
            ),
        ).model_dump(mode="json"),
        "legacy_recovery_status": {
            "artifact_status": "superseded_historical_evidence",
            "admission_enabled": False,
            "superseded_by_ref": queue_manifest.queue_ref,
        },
    }
    if args.include_scout:
        payload["workspace_scout"] = (
            DeveloperWorkspaceScout()
            .inspect(repository_root=ROOT)
            .model_dump(mode="json")
        )
    return _print(payload, pretty=args.pretty)


def recover_remaining_queue(args: argparse.Namespace) -> int:
    load_developer_queue_record_manifest(ROOT)
    raise ValueError("DEVELOPER_QUEUE_RECOVERY_SUPERSEDED_BY_V2")


def admit_queue_v2(args: argparse.Namespace) -> int:
    if args.confirm_admission != "admit-queue-v2":
        raise ValueError("DEVELOPER_QUEUE_V2_ADMISSION_CONFIRMATION_REQUIRED")
    coordinator = _coordinator(args)
    manifest = load_developer_queue_record_manifest(ROOT)
    drafts = build_developer_queue_record_drafts(ROOT)
    requested_item_ids = list(args.item_id or [])
    if len(requested_item_ids) != len(set(requested_item_ids)):
        raise ValueError("DEVELOPER_QUEUE_V2_DUPLICATE_ITEM_SELECTION")
    known_item_ids = {item.item_id for item in manifest.items}
    if set(requested_item_ids) - known_item_ids:
        raise ValueError("DEVELOPER_QUEUE_V2_UNKNOWN_ITEM_SELECTION")
    requested_item_id_set = set(requested_item_ids)
    selected_item_ids = [
        item.item_id
        for item in manifest.items
        if not requested_item_ids or item.item_id in requested_item_id_set
    ]
    draft_by_item_id = {
        item.item_id: draft for item, draft in zip(manifest.items, drafts, strict=True)
    }
    receipts = []
    for item_id in selected_item_ids:
        draft = draft_by_item_id[item_id]
        receipts.append(
            coordinator.add_task(
                draft,
                idempotency_ref=(
                    f"{args.idempotency_prefix}:"
                    f"{draft.task_ref.removeprefix('dev-task:')}"
                ),
            )
        )
    queue = coordinator.inspect()
    health = assess_developer_queue_record_health(
        manifest=manifest,
        task_states={task.task_ref: task.state for task in queue.tasks},
        task_contract_refs=queue_record_health_contract_refs(manifest, queue.tasks),
    )
    return _print(
        {
            "schema_version": "uaa.developer_queue_admission_receipt.v2",
            "selected_item_ids": selected_item_ids,
            "receipt_refs": [receipt.receipt_ref for receipt in receipts],
            "replayed_receipt_count": sum(receipt.replayed for receipt in receipts),
            "queue_of_record_health": health.model_dump(mode="json"),
            "automatic_agent_dispatch_performed": False,
            "git_or_github_mutation_performed": False,
            "product_runtime_authority_granted": False,
            "raw_paths_included": False,
            "raw_content_included": False,
        },
        pretty=args.pretty,
    )


def _queue_v2_amendment_context(
    args: argparse.Namespace,
) -> tuple[object, DeveloperWorkTaskDraft, ActorContext, object, str, str]:
    manifest = load_developer_queue_record_manifest(ROOT)
    drafts = build_developer_queue_record_drafts(ROOT)
    draft_by_item_id = {
        item.item_id: draft for item, draft in zip(manifest.items, drafts, strict=True)
    }
    draft = draft_by_item_id[args.item_id]
    coordinator = _coordinator(args)
    current_task_revision_ref = getattr(
        args, "expected_current_task_revision_ref", None
    ) or coordinator.current_task_revision_ref(draft.task_ref)
    actor_context = ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_founder_operator",
        actor_display_name="Local founder operator",
        authority_source=AuthoritySource.explicit_user_request,
        execution_contract_id="developer_queue_v2_exact_amendment",
    )
    approval_request = build_developer_work_task_amendment_approval_request(
        draft,
        expected_current_fingerprint_ref=args.expected_current_fingerprint_ref,
        expected_current_task_revision_ref=current_task_revision_ref,
        idempotency_ref=args.idempotency_ref,
        actor_context=actor_context,
    )
    exact_scope_ref = approval_request.resource_refs[0]
    return (
        manifest,
        draft,
        actor_context,
        approval_request,
        exact_scope_ref,
        current_task_revision_ref,
    )


def preview_queue_v2_amendment(args: argparse.Namespace) -> int:
    _, draft, _, approval_request, exact_scope_ref, current_task_revision_ref = (
        _queue_v2_amendment_context(args)
    )
    return _print(
        {
            "schema_version": "uaa.developer_queue_amendment_preview.v1",
            "item_id": args.item_id,
            "task_ref": draft.task_ref,
            "expected_current_fingerprint_ref": (args.expected_current_fingerprint_ref),
            "current_task_revision_ref": current_task_revision_ref,
            "replacement_fingerprint_ref": draft.canonical_source_fingerprint_ref,
            "approval_request_ref": approval_request.approval_request_id,
            "approval_scope_ref": exact_scope_ref,
            "queue_mutation_performed": False,
            "automatic_agent_dispatch_performed": False,
            "git_or_github_mutation_performed": False,
            "product_runtime_authority_granted": False,
            "raw_paths_included": False,
            "raw_content_included": False,
        },
        pretty=args.pretty,
    )


def amend_queue_v2_item(args: argparse.Namespace) -> int:
    if args.confirm_amendment != "amend-queue-v2-item":
        raise ValueError("DEVELOPER_QUEUE_V2_AMENDMENT_CONFIRMATION_REQUIRED")
    (
        manifest,
        draft,
        actor_context,
        approval_request,
        exact_scope_ref,
        current_task_revision_ref,
    ) = _queue_v2_amendment_context(args)
    if args.approve_exact_scope != exact_scope_ref:
        raise ValueError(
            f"DEVELOPER_QUEUE_V2_AMENDMENT_EXACT_APPROVAL_REQUIRED:{exact_scope_ref}"
        )
    approval_authority = LocalApprovalAuthority()
    approval_authority.create_request(approval_request)
    approval_ref = (
        "approval-ref:developer-queue-amendment-"
        f"{exact_scope_ref.rsplit(':', maxsplit=1)[-1]}"
    )
    approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=actor_context.actor_id,
        approved_actions=[approval_request.requested_action],
        approved_resource_refs=approval_request.resource_refs,
        approval_ref=approval_ref,
    )
    coordinator = _coordinator(args)
    receipt = coordinator.amend_queued_task(
        draft,
        expected_current_fingerprint_ref=args.expected_current_fingerprint_ref,
        expected_current_task_revision_ref=current_task_revision_ref,
        idempotency_ref=args.idempotency_ref,
        approval_authority=approval_authority,
        approval_ref=approval_ref,
        actor_context=actor_context,
    )
    queue = coordinator.inspect()
    health = assess_developer_queue_record_health(
        manifest=manifest,
        task_states={task.task_ref: task.state for task in queue.tasks},
        task_contract_refs=queue_record_health_contract_refs(manifest, queue.tasks),
    )
    return _print(
        {
            "schema_version": "uaa.developer_queue_amendment_receipt.v1",
            "item_id": args.item_id,
            "receipt_ref": receipt.receipt_ref,
            "replayed": receipt.replayed,
            "approval_scope_ref": exact_scope_ref,
            "queue_of_record_health": health.model_dump(mode="json"),
            "automatic_agent_dispatch_performed": False,
            "git_or_github_mutation_performed": False,
            "product_runtime_authority_granted": False,
            "raw_paths_included": False,
            "raw_content_included": False,
        },
        pretty=args.pretty,
    )


def claim_next(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).claim_next(
            node_ref=args.node_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def claim_task(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).claim_task(
            task_ref=args.task_ref,
            node_ref=args.node_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def heartbeat(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).heartbeat(
            task_ref=args.task_ref,
            node_ref=args.node_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def release(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).release(
            task_ref=args.task_ref,
            node_ref=args.node_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def complete(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).complete(
            task_ref=args.task_ref,
            node_ref=args.node_ref,
            evidence_refs=args.evidence_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def cancel(args: argparse.Namespace) -> int:
    if args.confirm_cancel != "cancel-task":
        raise ValueError("DEVELOPER_QUEUE_CANCELLATION_CONFIRMATION_REQUIRED")
    return _print(
        _coordinator(args).cancel(
            task_ref=args.task_ref,
            cancellation_reason_ref=args.cancellation_reason_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def record_terminal_packet(args: argparse.Namespace) -> int:
    if args.confirm_archive_ready != "archive-ready":
        raise ValueError("DEVELOPER_QUEUE_ARCHIVE_READY_CONFIRMATION_REQUIRED")
    return _print(
        _coordinator(args).record_terminal_scope_packet(
            task_ref=args.task_ref,
            terminal_scope_packet_ref=args.terminal_scope_packet_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def block(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).block(
            task_ref=args.task_ref,
            blocker_refs=args.blocker_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def unblock(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).unblock(
            task_ref=args.task_ref,
            expected_blocker_ref=args.expected_blocker_ref,
            evidence_ref=args.evidence_ref,
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def record_scope_disposition(args: argparse.Namespace) -> int:
    return _print(
        _coordinator(args).record_scope_disposition(
            task_ref=args.task_ref,
            disposition=DeveloperScopeDisposition(
                finding_ref=args.finding_ref,
                classification=args.classification,
                safe_summary=args.safe_summary,
                evidence_refs=args.evidence_ref,
                deferred_follow_up_ref=args.deferred_follow_up_ref,
            ),
            idempotency_ref=args.idempotency_ref,
        ),
        pretty=args.pretty,
    )


def handoff(args: argparse.Namespace) -> int:
    view = _coordinator(args).inspect(node_refs=[args.node_ref])
    task = next((task for task in view.tasks if task.task_ref == args.task_ref), None)
    if task is None:
        raise ValueError("DEVELOPER_WORK_TASK_NOT_FOUND")
    return _print(
        {
            "schema_version": "uaa-developer-work-handoff.v1",
            "task": task.model_dump(mode="json"),
            "target_node_ref": args.node_ref,
            "safe_summary": (
                "A bounded developer handoff. The target node must explicitly claim "
                "the task before implementation and record verifier evidence before "
                "review; this command does not dispatch or execute an agent."
            ),
            "remote_dispatch_performed": False,
            "git_mutation_performed": False,
            "product_runtime_authority_granted": False,
            "raw_paths_included": False,
            "raw_content_included": False,
        },
        pretty=args.pretty,
    )


def scout(args: argparse.Namespace) -> int:
    payload = {
        "workspace_scout": DeveloperWorkspaceScout()
        .inspect(repository_root=ROOT)
        .model_dump(mode="json")
    }
    return _print(payload, pretty=args.pretty)


def _receipt_command(
    parser: argparse.ArgumentParser, *, name: str, func: object
) -> None:
    command = parser.add_parser(name)
    command.add_argument("--task-ref", required=True)
    command.add_argument("--node-ref", required=True)
    command.add_argument("--idempotency-ref", required=True)
    command.add_argument("--pretty", action="store_true")
    command.set_defaults(func=func)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local-only developer queue coordination. It never runs agents, merges, "
            "prunes worktrees, or grants UAA product-runtime authority."
        )
    )
    parser.add_argument(
        "--state-dir",
        help=(
            "Explicit shared local state directory for Mac/Beast coordination. "
            "Defaults to the host-level local developer coordinator state."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_command = subparsers.add_parser(
        "catalog", help="Index canonical planning sources without mutating the queue."
    )
    catalog_command.add_argument("--pretty", action="store_true")
    catalog_command.set_defaults(func=catalog)

    initialize_command = subparsers.add_parser(
        "initialize", help="Initialize the durable local queue."
    )
    initialize_command.add_argument("--idempotency-ref", required=True)
    initialize_command.add_argument("--pretty", action="store_true")
    initialize_command.set_defaults(func=initialize)

    recover_command = subparsers.add_parser(
        "recover-remaining-queue",
        help=("Fail closed because the legacy recovery manifest is superseded by V2."),
    )
    recover_command.add_argument("--idempotency-prefix", required=True)
    recover_command.add_argument("--confirm-recovery", required=True)
    recover_command.add_argument("--pretty", action="store_true")
    recover_command.set_defaults(func=recover_remaining_queue)

    queue_v2_command = subparsers.add_parser(
        "admit-queue-v2",
        help=(
            "Idempotently admit the authoritative Q00-Q36 records without claiming "
            "or dispatching work."
        ),
    )
    queue_v2_command.add_argument("--idempotency-prefix", required=True)
    queue_v2_command.add_argument("--confirm-admission", required=True)
    queue_v2_command.add_argument(
        "--item-id",
        action="append",
        choices=tuple(f"Q{index:02d}" for index in range(37)),
        help=(
            "Admit only this canonical item. Repeat for a bounded manifest extension; "
            "omit to admit the complete queue."
        ),
    )
    queue_v2_command.add_argument("--pretty", action="store_true")
    queue_v2_command.set_defaults(func=admit_queue_v2)

    amend_queue_v2_command = subparsers.add_parser(
        "amend-queue-v2-item",
        help=(
            "Idempotently replace one never-claimed queued Queue V2 contract under "
            "its exact prior source fingerprint."
        ),
    )
    amend_queue_v2_command.add_argument(
        "--item-id",
        required=True,
        choices=tuple(f"Q{index:02d}" for index in range(37)),
    )
    amend_queue_v2_command.add_argument(
        "--expected-current-fingerprint-ref", required=True
    )
    amend_queue_v2_command.add_argument(
        "--expected-current-task-revision-ref", required=True
    )
    amend_queue_v2_command.add_argument("--idempotency-ref", required=True)
    amend_queue_v2_command.add_argument("--confirm-amendment", required=True)
    amend_queue_v2_command.add_argument("--approve-exact-scope", required=True)
    amend_queue_v2_command.add_argument("--pretty", action="store_true")
    amend_queue_v2_command.set_defaults(func=amend_queue_v2_item)

    preview_amendment_command = subparsers.add_parser(
        "preview-queue-v2-amendment",
        help=(
            "Preview the exact non-mutating LocalApprovalAuthority scope for one "
            "Queue V2 amendment."
        ),
    )
    preview_amendment_command.add_argument(
        "--item-id",
        required=True,
        choices=tuple(f"Q{index:02d}" for index in range(37)),
    )
    preview_amendment_command.add_argument(
        "--expected-current-fingerprint-ref", required=True
    )
    preview_amendment_command.add_argument("--idempotency-ref", required=True)
    preview_amendment_command.add_argument("--pretty", action="store_true")
    preview_amendment_command.set_defaults(func=preview_queue_v2_amendment)

    register_node_command = subparsers.add_parser(
        "register-node",
        help="Register one reviewed developer node before it may claim work.",
    )
    register_node_command.add_argument("--node-ref", required=True)
    register_node_command.add_argument("--transport-ref", required=True)
    register_node_command.add_argument(
        "--readiness", choices=("ready", "degraded", "offline"), default="ready"
    )
    register_node_command.add_argument(
        "--capability",
        action="append",
        required=True,
        choices=("queue_claim", "local_worktree", "local_verification", "github_merge"),
    )
    register_node_command.add_argument("--idempotency-ref", required=True)
    register_node_command.add_argument("--confirm-register", required=True)
    register_node_command.add_argument("--pretty", action="store_true")
    register_node_command.set_defaults(func=register_node)

    node_heartbeat_command = subparsers.add_parser(
        "node-heartbeat", help="Record liveness for one ready developer node."
    )
    node_heartbeat_command.add_argument("--node-ref", required=True)
    node_heartbeat_command.add_argument("--idempotency-ref", required=True)
    node_heartbeat_command.add_argument("--pretty", action="store_true")
    node_heartbeat_command.set_defaults(func=node_heartbeat)

    triage_command = subparsers.add_parser(
        "triage",
        help="Turn one catalog candidate into a bounded, branch/worktree-gated task.",
    )
    triage_command.add_argument("--planning-item-ref", required=True)
    triage_command.add_argument("--task-ref", required=True)
    triage_command.add_argument("--queue-order", type=int, default=100000)
    triage_command.add_argument("--branch-ref", required=True)
    triage_command.add_argument("--worktree-ref", required=True)
    triage_command.add_argument("--workstream-ref", required=True)
    triage_command.add_argument("--scope-contract-ref", required=True)
    triage_command.add_argument("--in-scope-ref", action="append", required=True)
    triage_command.add_argument("--out-of-scope-ref", action="append", required=True)
    triage_command.add_argument(
        "--sol-thinking", choices=("medium", "high", "xhigh"), required=True
    )
    triage_command.add_argument("--priority", choices=("p0", "p1", "p2", "p3"))
    triage_command.add_argument(
        "--concurrency", choices=("parallel_safe", "exclusive"), default="parallel_safe"
    )
    triage_command.add_argument(
        "--wip-lane",
        choices=("shared_core", "product_surface", "verification_read_only"),
        required=True,
    )
    triage_command.add_argument("--acceptance-ref", action="append", required=True)
    triage_command.add_argument("--verifier-ref", action="append", required=True)
    triage_command.add_argument("--merge-gate-ref", action="append", required=True)
    triage_command.add_argument("--depends-on-task-ref", action="append", default=[])
    triage_command.add_argument("--next-safe-action", required=True)
    triage_command.add_argument("--idempotency-ref", required=True)
    triage_command.add_argument("--confirm-triage", required=True)
    triage_command.add_argument("--pretty", action="store_true")
    triage_command.set_defaults(func=triage)

    inspect_command = subparsers.add_parser(
        "inspect",
        help="Inspect durable queue state and optionally the local Git scout.",
    )
    inspect_command.add_argument("--node-ref", action="append", default=[])
    inspect_command.add_argument("--include-scout", action="store_true")
    inspect_command.add_argument("--pretty", action="store_true")
    inspect_command.set_defaults(func=inspect)

    claim_next_command = subparsers.add_parser(
        "claim-next",
        help="Explicitly claim the highest-priority dependency-ready task.",
    )
    claim_next_command.add_argument("--node-ref", required=True)
    claim_next_command.add_argument("--idempotency-ref", required=True)
    claim_next_command.add_argument("--pretty", action="store_true")
    claim_next_command.set_defaults(func=claim_next)
    _receipt_command(subparsers, name="claim", func=claim_task)
    _receipt_command(subparsers, name="heartbeat", func=heartbeat)
    _receipt_command(subparsers, name="release", func=release)

    complete_command = subparsers.add_parser(
        "complete", help="Record verifier evidence for an owned task."
    )
    complete_command.add_argument("--task-ref", required=True)
    complete_command.add_argument("--node-ref", required=True)
    complete_command.add_argument("--evidence-ref", action="append", required=True)
    complete_command.add_argument("--idempotency-ref", required=True)
    complete_command.add_argument("--pretty", action="store_true")
    complete_command.set_defaults(func=complete)

    cancel_command = subparsers.add_parser(
        "cancel",
        help="Cancel one unclaimed task with an exact durable reason ref.",
    )
    cancel_command.add_argument("--task-ref", required=True)
    cancel_command.add_argument("--cancellation-reason-ref", required=True)
    cancel_command.add_argument("--idempotency-ref", required=True)
    cancel_command.add_argument("--confirm-cancel", required=True)
    cancel_command.add_argument("--pretty", action="store_true")
    cancel_command.set_defaults(func=cancel)

    archive_ready_command = subparsers.add_parser(
        "record-terminal-packet",
        help="Record terminal scope evidence before a completed Codex task can be archived.",
    )
    archive_ready_command.add_argument("--task-ref", required=True)
    archive_ready_command.add_argument("--terminal-scope-packet-ref", required=True)
    archive_ready_command.add_argument("--idempotency-ref", required=True)
    archive_ready_command.add_argument("--confirm-archive-ready", required=True)
    archive_ready_command.add_argument("--pretty", action="store_true")
    archive_ready_command.set_defaults(func=record_terminal_packet)

    block_command = subparsers.add_parser(
        "block", help="Record a safe blocker ref for a task."
    )
    block_command.add_argument("--task-ref", required=True)
    block_command.add_argument("--blocker-ref", action="append", required=True)
    block_command.add_argument("--idempotency-ref", required=True)
    block_command.add_argument("--pretty", action="store_true")
    block_command.set_defaults(func=block)

    unblock_command = subparsers.add_parser(
        "unblock", help="Return a reviewed blocked task to the queue."
    )
    unblock_command.add_argument("--task-ref", required=True)
    unblock_command.add_argument("--expected-blocker-ref", required=True)
    unblock_command.add_argument("--evidence-ref", required=True)
    unblock_command.add_argument("--idempotency-ref", required=True)
    unblock_command.add_argument("--pretty", action="store_true")
    unblock_command.set_defaults(func=unblock)

    scope_command = subparsers.add_parser(
        "record-scope-disposition",
        help="Record an evidence-gated fix, safe deferral, or dismissal without expanding scope.",
    )
    scope_command.add_argument("--task-ref", required=True)
    scope_command.add_argument("--finding-ref", required=True)
    scope_command.add_argument(
        "--classification",
        required=True,
        choices=("must_fix_now", "defer_safely", "dismiss_with_evidence"),
    )
    scope_command.add_argument("--safe-summary", required=True)
    scope_command.add_argument("--evidence-ref", action="append", default=[])
    scope_command.add_argument("--deferred-follow-up-ref")
    scope_command.add_argument("--idempotency-ref", required=True)
    scope_command.add_argument("--pretty", action="store_true")
    scope_command.set_defaults(func=record_scope_disposition)

    handoff_command = subparsers.add_parser(
        "handoff", help="Print one safe task handoff for a Mac or Beast worker."
    )
    handoff_command.add_argument("--task-ref", required=True)
    handoff_command.add_argument("--node-ref", required=True)
    handoff_command.add_argument("--pretty", action="store_true")
    handoff_command.set_defaults(func=handoff)

    scout_command = subparsers.add_parser(
        "scout", help="Run fixed read-only local Git metadata checks."
    )
    scout_command.add_argument("--pretty", action="store_true")
    scout_command.set_defaults(func=scout)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (DeveloperWorkQueueError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason_ref": f"developer-queue-error-ref:{type(error).__name__}",
                    "safe_summary": str(error),
                    "raw_paths_included": False,
                    "raw_content_included": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
