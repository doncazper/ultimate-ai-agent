#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
    action_id_to_item_ref,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.memory import (  # noqa: E402
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS,
    ManualMemoryCandidateRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


def _repository(args: argparse.Namespace) -> FounderLoopRepository:
    if args.state_dir is None:
        return FounderLoopRepository.from_env()
    return FounderLoopRepository(Path(args.state_dir))


def _safe_action_projection(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_ref": action.get("item_ref"),
        "title": action.get("title"),
        "surface": action.get("surface"),
        "status": action.get("status"),
        "priority": action.get("priority"),
        "risk_class": action.get("risk_class"),
        "side_effect_class": action.get("side_effect_class"),
        "action_envelope_ref": action.get("action_envelope_ref"),
        "approval_envelope_ref": action.get("approval_envelope_ref"),
        "approval_envelope_status": action.get("approval_envelope_status"),
        "state_change_contract_ref": action.get("state_change_contract_ref"),
        "state_change_readiness": action.get("state_change_readiness"),
        "action_kind": action.get("action_kind"),
        "local_task_ref": action.get("local_task_ref"),
        "local_task_commit_approval_ref": action.get(
            "local_task_commit_approval_ref"
        ),
        "local_task_commit_eligible": action.get("local_task_commit_eligible"),
        "local_task_commit_approval_status": action.get(
            "local_task_commit_approval_status"
        ),
        "local_task_commit_contract_ref": action.get("local_task_commit_contract_ref"),
        "local_task_commit_route_ref": action.get("local_task_commit_route_ref"),
        "local_task_commit_receipt_ref": action.get("local_task_commit_receipt_ref"),
        "local_task_commit_next_safe_action": action.get(
            "local_task_commit_next_safe_action"
        ),
        "local_task_commit_blocked_reasons": list(
            action.get("local_task_commit_blocked_reasons") or []
        ),
        "local_task_commit_external_authority_blocked_refs": list(
            action.get("local_task_commit_external_authority_blocked_refs") or []
        ),
        "local_task_safe_disable_posture": action.get(
            "local_task_safe_disable_posture"
        ),
        "local_task_safe_disable_active": action.get("local_task_safe_disable_active"),
        "local_task_safe_disable_posture_ref": action.get(
            "local_task_safe_disable_posture_ref"
        ),
        "local_task_safe_disable_ref": action.get("local_task_safe_disable_ref"),
        "local_task_rollback_ref": action.get("local_task_rollback_ref"),
        "local_task_rollback_execution_enabled": action.get(
            "local_task_rollback_execution_enabled"
        ),
        "local_task_rollback_blocker_refs": list(
            action.get("local_task_rollback_blocker_refs") or []
        ),
        "receipt_refs": list(action.get("receipt_refs") or []),
        "audit_refs": list(action.get("audit_refs") or []),
        "evidence_refs": list(action.get("evidence_refs") or []),
        "rollback_ref": action.get("rollback_ref"),
        "safe_disable_ref": action.get("safe_disable_ref"),
        "next_safe_action": action.get("next_safe_action"),
    }


def _safe_evidence_projection(item: dict[str, Any]) -> dict[str, Any]:
    answers = item.get("history_answers") or {}
    return {
        "timeline_item_ref": item.get("timeline_item_ref"),
        "item_kind": item.get("item_kind"),
        "title": item.get("title"),
        "status_refs": {
            key: value.get("refs", [])
            for key, value in answers.items()
            if isinstance(value, dict)
        },
        "blocked_state_refs": list(item.get("blocked_state_refs") or []),
        "evidence_refs": list(item.get("evidence_refs") or []),
    }


def _inspect_state(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today = repo.today_summary(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect",
        "storage_status": repo.storage_status(),
        "today_status": today.get("status"),
        "plan_action_state": today.get("plan_action_state"),
        "actions": [
            _safe_action_projection(action)
            for action in repo.list_action_inbox(limit=args.limit)
        ],
        "evidence_timeline": [
            _safe_evidence_projection(item)
            for item in today.get("evidence_timeline", [])[: args.limit]
            if isinstance(item, dict)
        ],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _promote_action_envelope(args: argparse.Namespace) -> int:
    repo = _repository(args)
    request = FounderLoopActionEnvelopePromotionRequest(
        today_item_ref=args.today_item_ref,
        decision_reason_ref=args.decision_reason_ref,
        risk_class=args.risk_class,
        priority=args.priority,
        metadata_refs=args.metadata_ref,
    )
    receipt = repo.promote_today_item_to_action_envelope(
        request=request,
        idempotency_key_ref=args.idempotency_ref,
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-promote-action-envelope",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_action_decision(args: argparse.Namespace) -> int:
    repo = _repository(args)
    request = FounderLoopActionDecisionRequest(
        approval_ref=args.approval_ref,
        decision_reason_ref=args.decision_reason_ref,
        edited_envelope_ref=args.edited_envelope_ref,
        defer_until_ref=args.defer_until_ref,
        metadata_refs=args.metadata_ref,
    )
    try:
        receipt = repo.record_action_decision(
            action_id=args.action_id,
            decision=args.decision,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (
        FounderLoopStorageDuplicateError,
        FounderLoopStorageError,
        ValidationError,
        ValueError,
    ) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-record-action-decision",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_ACTION_DECISION_BLOCKED",
                "action_ref": args.action_id,
                "decision": args.decision,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-record-action-decision",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _commit_local_task(args: argparse.Namespace) -> int:
    repo = _repository(args)
    item_ref = action_id_to_item_ref(args.action_id)
    action = next(
        (
            candidate
            for candidate in repo.list_action_inbox(limit=200)
            if candidate.get("item_ref") == item_ref
        ),
        None,
    )
    if action is None:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-commit-local-task",
                "status": "blocked",
                "safe_message": "No safe Action Inbox item exists for this action ref.",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    request = FounderLoopLocalTaskCommitRequest(
        approval_ref=args.approval_ref,
        decision_reason_ref=args.decision_reason_ref,
        metadata_refs=args.metadata_ref,
    )
    try:
        receipt = repo.commit_local_task(
            action_id=args.action_id,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (
        FounderLoopStorageDuplicateError,
        FounderLoopStorageError,
        ValidationError,
        ValueError,
    ) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-commit-local-task",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_LOCAL_TASK_COMMIT_BLOCKED",
                "action_ref": args.action_id,
                "approval_ref": args.approval_ref,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-commit-local-task",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_workbench(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        workbench = repo.memory_workbench(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-workbench",
                error_ref="FOUNDER_LOOP_MEMORY_WORKBENCH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-workbench",
        "workbench": workbench,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _search_memory(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        search = repo.memory_search(
            query_ref=args.query_ref,
            kind=args.kind,
            source_ref=args.source_ref,
            project_ref=args.project_ref,
            person_ref=args.person_ref,
            org_ref=args.org_ref,
            deal_ref=args.deal_ref,
            review_state=args.review_state,
            quality_state=args.quality_state,
            stale_state=args.stale_state,
            conflict_state=args.conflict_state,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-search",
                error_ref="FOUNDER_LOOP_MEMORY_SEARCH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-search",
        "search": search,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_receipts(args: argparse.Namespace) -> int:
    repo = _repository(args)
    review = repo.memory_review(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-receipts",
        "route_ref": review.get("route_ref"),
        "decision_route_refs": review.get("decision_route_refs"),
        "decision_receipts": list(review.get("decision_receipts") or []),
        "decision_receipt_refs": list(review.get("decision_receipt_refs") or []),
        "workbench_health": review.get("workbench_health"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_memory_decision(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = MemoryReviewDecisionRequest(
            reviewer_ref=args.reviewer_ref,
            corrected_summary_ref=args.corrected_summary_ref,
            corrected_safe_summary=args.corrected_safe_summary,
            source_refs=args.source_ref,
            evidence_refs=args.evidence_ref,
            metadata_refs=args.metadata_ref,
            merge_refs=args.merge_ref,
            supersedes_refs=args.supersedes_ref,
            forget_request_ref=args.forget_request_ref,
            blocked_state_refs=(
                args.blocked_state_ref
                or list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS)
            ),
        )
        receipt = repo.record_memory_review_decision(
            candidate_ref=args.candidate_ref,
            decision=args.decision,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-decision",
                error_ref="FOUNDER_LOOP_MEMORY_DECISION_REF_DENIED",
                candidate_ref=args.candidate_ref,
                decision=args.decision,
                idempotency_ref=args.idempotency_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-memory-decision",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_MEMORY_DECISION_BLOCKED",
                "candidate_ref": args.candidate_ref,
                "decision": args.decision,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-decision",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_manual_memory_candidate(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = ManualMemoryCandidateRequest(
            candidate_kind=args.candidate_kind,
            title=args.title,
            safe_summary=args.safe_summary,
            priority=args.priority,
            reviewer_ref=args.reviewer_ref,
            source_refs=args.source_ref,
            provenance_refs=args.provenance_ref,
            evidence_refs=args.evidence_ref,
            missing_evidence_refs=args.missing_evidence_ref,
            related_entity_refs=args.related_entity_ref,
            tag_refs=args.tag_ref,
            metadata_refs=args.metadata_ref,
            blocked_state_refs=(
                args.blocked_state_ref
                or list(MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS)
            ),
        )
        receipt = repo.record_manual_memory_candidate(
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-manual-candidate",
                error_ref="FOUNDER_LOOP_MANUAL_MEMORY_CANDIDATE_REF_DENIED",
                candidate_kind=args.candidate_kind,
                idempotency_ref=args.idempotency_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-memory-manual-candidate",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_MANUAL_MEMORY_CANDIDATE_BLOCKED",
                "candidate_kind": args.candidate_kind,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-manual-candidate",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _blocked_cli_payload(
    *,
    command_ref: str,
    error_ref: str,
    **extra: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": command_ref,
        "status": "blocked",
        "error_ref": error_ref,
        **{key: value for key, value in extra.items() if value is not None},
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uaa_founder_loop",
        description="Inspect local Founder Loop state and create review-only Action envelopes.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local state directory; the value is not echoed in output.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Print safe refs for Today, Actions, receipts, and Evidence Timeline state.",
    )
    inspect_parser.add_argument("--limit", type=int, default=12)
    inspect_parser.set_defaults(func=_inspect_state)

    promote_parser = subparsers.add_parser(
        "promote-action-envelope",
        help="Create a review-only Action envelope receipt from a Today item ref.",
    )
    promote_parser.add_argument("--today-item-ref", required=True)
    promote_parser.add_argument("--idempotency-ref", required=True)
    promote_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-today-action-envelope",
    )
    promote_parser.add_argument(
        "--risk-class",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    )
    promote_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    promote_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    promote_parser.set_defaults(func=_promote_action_envelope)

    decision_parser = subparsers.add_parser(
        "record-action-decision",
        help="Record a backend-owned Action Inbox decision receipt without executing the action.",
    )
    decision_parser.add_argument("--action-id", required=True)
    decision_parser.add_argument(
        "--decision",
        choices=["approve", "edit", "reject", "defer"],
        required=True,
    )
    decision_parser.add_argument("--idempotency-ref", required=True)
    decision_parser.add_argument(
        "--approval-ref",
        default=None,
        help=(
            "Optional safe approval ref. If omitted for approve, Python Core "
            "records a backend-owned exact local approval ref."
        ),
    )
    decision_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-action-decision",
    )
    decision_parser.add_argument("--edited-envelope-ref", default=None)
    decision_parser.add_argument("--defer-until-ref", default=None)
    decision_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    decision_parser.set_defaults(func=_record_action_decision)

    commit_parser = subparsers.add_parser(
        "commit-local-task",
        help="Commit an approved local_task_create Action Inbox item to local task state.",
    )
    commit_parser.add_argument("--action-id", required=True)
    commit_parser.add_argument("--idempotency-ref", required=True)
    commit_parser.add_argument("--approval-ref", required=True)
    commit_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-local-task-commit",
    )
    commit_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    commit_parser.set_defaults(func=_commit_local_task)

    memory_workbench_parser = subparsers.add_parser(
        "memory-workbench",
        help="Inspect the backend-owned Memory Workbench read model.",
    )
    memory_workbench_parser.add_argument("--query-ref", default=None)
    memory_workbench_parser.add_argument("--limit", type=int, default=20)
    memory_workbench_parser.set_defaults(func=_inspect_memory_workbench)

    memory_search_parser = subparsers.add_parser(
        "memory-search",
        help="Search reviewed safe memory summaries and refs without semantic search.",
    )
    memory_search_parser.add_argument("--query-ref", default=None)
    memory_search_parser.add_argument("--kind", default=None)
    memory_search_parser.add_argument("--source-ref", default=None)
    memory_search_parser.add_argument("--project-ref", default=None)
    memory_search_parser.add_argument("--person-ref", default=None)
    memory_search_parser.add_argument("--org-ref", default=None)
    memory_search_parser.add_argument("--deal-ref", default=None)
    memory_search_parser.add_argument("--review-state", default=None)
    memory_search_parser.add_argument("--quality-state", default=None)
    memory_search_parser.add_argument("--stale-state", default=None)
    memory_search_parser.add_argument("--conflict-state", default=None)
    memory_search_parser.add_argument("--limit", type=int, default=20)
    memory_search_parser.set_defaults(func=_search_memory)

    memory_receipts_parser = subparsers.add_parser(
        "memory-receipts",
        help="Inspect memory review lifecycle receipt refs and workbench health.",
    )
    memory_receipts_parser.add_argument("--limit", type=int, default=20)
    memory_receipts_parser.set_defaults(func=_inspect_memory_receipts)

    memory_decision_parser = subparsers.add_parser(
        "record-memory-decision",
        help="Record a Memory Review lifecycle receipt without executing memory delete/export/context authority.",
    )
    memory_decision_parser.add_argument("--candidate-ref", required=True)
    memory_decision_parser.add_argument(
        "--decision",
        choices=[
            "accept",
            "correct",
            "reject",
            "defer",
            "merge",
            "supersede",
            "forget_request",
        ],
        required=True,
    )
    memory_decision_parser.add_argument("--idempotency-ref", required=True)
    memory_decision_parser.add_argument(
        "--reviewer-ref",
        default="actor-ref:founder-loop-cli-memory-review",
    )
    memory_decision_parser.add_argument("--corrected-summary-ref", default=None)
    memory_decision_parser.add_argument("--corrected-safe-summary", default=None)
    memory_decision_parser.add_argument("--forget-request-ref", default=None)
    memory_decision_parser.add_argument("--source-ref", action="append", default=[])
    memory_decision_parser.add_argument("--evidence-ref", action="append", default=[])
    memory_decision_parser.add_argument("--metadata-ref", action="append", default=[])
    memory_decision_parser.add_argument("--merge-ref", action="append", default=[])
    memory_decision_parser.add_argument("--supersedes-ref", action="append", default=[])
    memory_decision_parser.add_argument(
        "--blocked-state-ref",
        action="append",
        default=[],
    )
    memory_decision_parser.set_defaults(func=_record_memory_decision)

    manual_memory_parser = subparsers.add_parser(
        "memory-manual-candidate",
        help="Create a manual safe-summary Memory Review candidate; no recall record is created.",
    )
    manual_memory_parser.add_argument("--candidate-kind", required=True)
    manual_memory_parser.add_argument("--title", required=True)
    manual_memory_parser.add_argument("--safe-summary", required=True)
    manual_memory_parser.add_argument("--idempotency-ref", required=True)
    manual_memory_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    manual_memory_parser.add_argument(
        "--reviewer-ref",
        default="actor-ref:founder-loop-cli-memory-intake",
    )
    manual_memory_parser.add_argument("--source-ref", action="append", default=[])
    manual_memory_parser.add_argument("--provenance-ref", action="append", default=[])
    manual_memory_parser.add_argument("--evidence-ref", action="append", default=[])
    manual_memory_parser.add_argument(
        "--missing-evidence-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.add_argument(
        "--related-entity-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.add_argument("--tag-ref", action="append", default=[])
    manual_memory_parser.add_argument("--metadata-ref", action="append", default=[])
    manual_memory_parser.add_argument(
        "--blocked-state-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.set_defaults(func=_record_manual_memory_candidate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
