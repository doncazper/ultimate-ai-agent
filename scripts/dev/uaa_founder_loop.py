#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionEnvelopePromotionRequest,
    action_id_to_item_ref,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FounderLoopLocalTaskCommitRequest,
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
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
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


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
