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

from ultimate_ai_agent.core.crm import (  # noqa: E402
    CrmLocalMutationRequest,
    CrmLocalStore,
    expected_crm_local_mutation_approval_ref,
)


def _store(args: argparse.Namespace) -> CrmLocalStore:
    if args.state_dir is None:
        return CrmLocalStore.from_env()
    return CrmLocalStore(Path(args.state_dir))


def _print(payload: Any, *, pretty: bool) -> None:
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))


def inspect_summary(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(crm.model_dump(mode="json"), pretty=args.pretty)
    return 0


def inspect_relationships(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(
        {
            "contract_ref": crm.contract_ref,
            "people": [item.model_dump(mode="json") for item in crm.people],
            "organizations": [
                item.model_dump(mode="json") for item in crm.organizations
            ],
            "relationships": [
                item.model_dump(mode="json") for item in crm.relationships
            ],
            "communication_drafts": [
                item.model_dump(mode="json") for item in crm.communication_drafts
            ],
            "ai_proposals": [
                item.model_dump(mode="json") for item in crm.ai_proposals
            ],
        },
        pretty=args.pretty,
    )
    return 0


def inspect_timeline(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(
        {
            "contract_ref": crm.contract_ref,
            "timeline_events": [
                item.model_dump(mode="json") for item in crm.timeline_events
            ],
            "reports": [item.model_dump(mode="json") for item in crm.reports],
        },
        pretty=args.pretty,
    )
    return 0


def inspect_follow_ups(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(
        {
            "contract_ref": crm.contract_ref,
            "follow_ups": [item.model_dump(mode="json") for item in crm.follow_ups],
        },
        pretty=args.pretty,
    )
    return 0


def inspect_pipelines(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(
        {
            "contract_ref": crm.contract_ref,
            "pipelines": [item.model_dump(mode="json") for item in crm.pipelines],
            "opportunities": [
                item.model_dump(mode="json") for item in crm.opportunities
            ],
        },
        pretty=args.pretty,
    )
    return 0


def inspect_smart_lists(args: argparse.Namespace) -> int:
    crm = _store(args).read_model()
    _print(
        {
            "contract_ref": crm.contract_ref,
            "smart_lists": [
                item.model_dump(mode="json") for item in crm.smart_lists
            ],
            "connector_read_lanes": crm.connector_read_lanes.model_dump(mode="json"),
            "sends_writes_authority_plan": (
                crm.sends_writes_authority_plan.model_dump(mode="json")
            ),
        },
        pretty=args.pretty,
    )
    return 0


def inspect_storage(args: argparse.Namespace) -> int:
    _print(_store(args).storage_status().model_dump(mode="json"), pretty=args.pretty)
    return 0


def seed_demo(args: argparse.Namespace) -> int:
    _print(_store(args).seed_demo().model_dump(mode="json"), pretty=args.pretty)
    return 0


def clear_demo(args: argparse.Namespace) -> int:
    status = _store(args).clear_demo(confirm_local_only=args.confirm_local_only)
    _print(status.model_dump(mode="json"), pretty=args.pretty)
    return 0


def export_redacted(args: argparse.Namespace) -> int:
    _print(_store(args).export_redacted_snapshot(), pretty=args.pretty)
    return 0


def import_preview(args: argparse.Namespace) -> int:
    _print(
        _store(args).import_preview_from_csv(Path(args.csv), limit=args.limit),
        pretty=args.pretty,
    )
    return 0


def expected_approval(args: argparse.Namespace) -> int:
    _print(
        {
            "approval_ref": expected_crm_local_mutation_approval_ref(
                target_ref=args.target_ref,
                idempotency_ref=args.idempotency_ref,
            )
        },
        pretty=args.pretty,
    )
    return 0


def mutate_local(args: argparse.Namespace) -> int:
    request = CrmLocalMutationRequest(
        mutation_kind=args.kind,
        target_ref=args.target_ref,
        approval_ref=args.approval_ref,
        safe_summary=args.safe_summary,
        relationship_ref=args.relationship_ref,
        follow_up_status=args.follow_up_status,
        stage_ref=args.stage_ref,
        metadata_refs=args.metadata_ref,
    )
    receipt = _store(args).record_local_mutation(
        request=request,
        idempotency_ref=args.idempotency_ref,
    )
    _print(receipt.model_dump(mode="json"), pretty=args.pretty)
    return 0


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-dir",
        help="Optional local CRM state directory. Output never includes this path.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print safe JSON output.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect and manage the local-only UAA CRM command center."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = [
        ("inspect-summary", inspect_summary, "Print the complete CRM read model."),
        (
            "inspect-relationships",
            inspect_relationships,
            "Print relationship, people, organization, draft, and proposal refs.",
        ),
        ("inspect-timeline", inspect_timeline, "Print timeline and report refs."),
        ("inspect-follow-ups", inspect_follow_ups, "Print follow-up queue refs."),
        ("inspect-pipelines", inspect_pipelines, "Print pipeline and opportunity refs."),
        ("inspect-smart-lists", inspect_smart_lists, "Print smart list refs."),
        ("inspect-storage", inspect_storage, "Print local storage status refs."),
        ("seed-demo", seed_demo, "Seed safe local demo CRM state."),
        ("export-redacted", export_redacted, "Print a redacted safe-ref snapshot."),
    ]
    for name, handler, help_text in commands:
        command = subparsers.add_parser(name, help=help_text)
        _add_common(command)
        command.set_defaults(func=handler)

    clear = subparsers.add_parser("clear-demo", help="Clear local demo CRM state.")
    _add_common(clear)
    clear.add_argument(
        "--confirm-local-only",
        action="store_true",
        help="Required guard confirming only local demo CRM state is cleared.",
    )
    clear.set_defaults(func=clear_demo)

    preview = subparsers.add_parser(
        "import-preview",
        help="Preview local CSV import candidates without committing them.",
    )
    _add_common(preview)
    preview.add_argument("--csv", required=True, help="Local CSV to preview.")
    preview.add_argument("--limit", type=int, default=20, help="Preview row limit.")
    preview.set_defaults(func=import_preview)

    approval = subparsers.add_parser(
        "expected-approval",
        help="Print the exact approval ref required for a local CRM mutation.",
    )
    _add_common(approval)
    approval.add_argument("--target-ref", required=True)
    approval.add_argument("--idempotency-ref", required=True)
    approval.set_defaults(func=expected_approval)

    mutation = subparsers.add_parser(
        "mutate-local",
        help="Record an exact-scoped local-only CRM mutation receipt.",
    )
    _add_common(mutation)
    mutation.add_argument("--kind", required=True)
    mutation.add_argument("--target-ref", required=True)
    mutation.add_argument("--approval-ref", required=True)
    mutation.add_argument("--idempotency-ref", required=True)
    mutation.add_argument(
        "--safe-summary",
        default="Local CRM mutation requested with safe summary only.",
    )
    mutation.add_argument("--relationship-ref")
    mutation.add_argument("--follow-up-status")
    mutation.add_argument("--stage-ref")
    mutation.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Optional safe metadata/evidence ref. Repeatable.",
    )
    mutation.set_defaults(func=mutate_local)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
