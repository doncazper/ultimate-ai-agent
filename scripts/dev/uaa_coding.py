#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.code import (  # noqa: E402
    build_coding_pair_agent_relay_read_model,
    build_coding_cockpit_session_seed,
    build_coding_git_review,
    build_coding_live_preview,
    build_coding_multi_agent_review,
    build_coding_patch_apply_readiness,
    build_coding_patch_proposal_preview,
    build_coding_project_model_read_model,
    build_coding_test_command_readiness,
    build_coding_workspace_context_preview,
    verify_coding_patch_proposal_signed_evidence,
)


def _dump_payload(args: argparse.Namespace, payload: object) -> None:
    print(
        json.dumps(
            payload,
            indent=2 if getattr(args, "pretty", False) else None,
            sort_keys=True,
        )
    )


def inspect_session(args: argparse.Namespace) -> int:
    session = build_coding_cockpit_session_seed()
    payload = session.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_context(args: argparse.Namespace) -> int:
    context = build_coding_workspace_context_preview()
    payload = context.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_project_model(args: argparse.Namespace) -> int:
    project_model = build_coding_project_model_read_model()
    payload = project_model.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_patch_proposal(args: argparse.Namespace) -> int:
    proposal = build_coding_patch_proposal_preview()
    payload = proposal.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def verify_patch_proposal_evidence(args: argparse.Namespace) -> int:
    proposal = build_coding_patch_proposal_preview()
    verification = verify_coding_patch_proposal_signed_evidence(
        proposal.signed_evidence
    )
    payload = {
        "command_ref": "repo-local-command:coding-patch-proposal-evidence-verify",
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "patch_apply_performed": False,
        "signed_evidence_ref": proposal.signed_evidence.signed_envelope_ref,
        "verification": verification.model_dump(mode="json"),
    }
    _dump_payload(args, payload)
    return 0


def inspect_patch_apply_readiness(args: argparse.Namespace) -> int:
    readiness = build_coding_patch_apply_readiness()
    payload = readiness.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_test_command_readiness(args: argparse.Namespace) -> int:
    readiness = build_coding_test_command_readiness()
    payload = readiness.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_git_review(args: argparse.Namespace) -> int:
    review = build_coding_git_review()
    payload = review.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_live_preview(args: argparse.Namespace) -> int:
    preview = build_coding_live_preview()
    payload = preview.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_multi_agent_review(args: argparse.Namespace) -> int:
    review = build_coding_multi_agent_review()
    payload = review.model_dump(mode="json")
    _dump_payload(args, payload)
    return 0


def inspect_pair_agent_relay(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    _dump_payload(args, relay.model_dump(mode="json"))
    return 0


def preview_pair_run(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    payload = {
        "preview_created": True,
        "execution_performed": False,
        "safe_refs_only": True,
        "pair_run": relay.run_contract.model_dump(mode="json"),
        "blocked_authority_refs": relay.blocked_authority_refs,
        "next_safe_action": relay.next_safe_action,
    }
    _dump_payload(args, payload)
    return 0


def inspect_pair_run(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    _dump_payload(args, relay.run_contract.model_dump(mode="json"))
    return 0


def inspect_pair_artifacts(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    payload = {
        "safe_refs_only": True,
        "raw_transcript_durable": False,
        "artifacts": [artifact.model_dump(mode="json") for artifact in relay.artifacts],
    }
    _dump_payload(args, payload)
    return 0


def inspect_pair_receipts(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    payload = {
        "safe_refs_only": True,
        "execution_performed": False,
        "receipts": [receipt.model_dump(mode="json") for receipt in relay.receipts],
    }
    _dump_payload(args, payload)
    return 0


def start_pair_run_readiness(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    payload = {
        "start_allowed": False,
        "execution_performed": False,
        "reason_ref": "blocked-state:coding-pair-no-foreground-adapter-execution",
        "lane_ref": relay.lane_ref,
        "blocked_authority_refs": relay.blocked_authority_refs,
        "unblock_prompt_refs": relay.unblock_prompt_refs,
    }
    _dump_payload(args, payload)
    return 0


def stop_pair_run_readiness(args: argparse.Namespace) -> int:
    relay = build_coding_pair_agent_relay_read_model()
    payload = {
        "stop_control_available": False,
        "execution_performed": False,
        "reason_ref": "blocked-state:coding-pair-no-active-foreground-run",
        "lane_ref": relay.lane_ref,
        "blocked_authority_refs": relay.blocked_authority_refs,
    }
    _dump_payload(args, payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect UAA Coding Cockpit read-only session state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser(
        "inspect-session",
        help="Print the backend-owned read-only Coding Cockpit session seed.",
    )
    inspect.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    inspect.set_defaults(func=inspect_session)
    context = subparsers.add_parser(
        "inspect-context",
        help="Print the backend-owned read-only Coding Cockpit context preview.",
    )
    context.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    context.set_defaults(func=inspect_context)
    project_model = subparsers.add_parser(
        "inspect-project-model",
        help="Print the backend-owned read-only Coding Cockpit project posture.",
    )
    project_model.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    project_model.set_defaults(func=inspect_project_model)
    patch_proposal = subparsers.add_parser(
        "inspect-patch-proposal",
        help="Print the backend-owned proposal-only Coding Cockpit patch preview.",
    )
    patch_proposal.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    patch_proposal.set_defaults(func=inspect_patch_proposal)
    patch_proposal_evidence = subparsers.add_parser(
        "verify-patch-proposal-evidence",
        help="Verify the deterministic signed evidence for the patch proposal preview.",
    )
    patch_proposal_evidence.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON verification result.",
    )
    patch_proposal_evidence.set_defaults(func=verify_patch_proposal_evidence)
    patch_apply = subparsers.add_parser(
        "inspect-patch-apply-readiness",
        help="Print the blocked Coding Cockpit patch apply readiness model.",
    )
    patch_apply.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    patch_apply.set_defaults(func=inspect_patch_apply_readiness)
    test_command = subparsers.add_parser(
        "inspect-test-command-readiness",
        help="Print the blocked Coding Cockpit allowlisted test command readiness model.",
    )
    test_command.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    test_command.set_defaults(func=inspect_test_command_readiness)
    git_review = subparsers.add_parser(
        "inspect-git-review",
        help="Print the blocked Coding Cockpit Git review read model.",
    )
    git_review.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    git_review.set_defaults(func=inspect_git_review)
    live_preview = subparsers.add_parser(
        "inspect-live-preview",
        help="Print the blocked Coding Cockpit live preview read model.",
    )
    live_preview.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    live_preview.set_defaults(func=inspect_live_preview)
    multi_agent_review = subparsers.add_parser(
        "inspect-multi-agent-review",
        help="Print the blocked Coding Cockpit multi-agent review read model.",
    )
    multi_agent_review.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    multi_agent_review.set_defaults(func=inspect_multi_agent_review)
    pair_agent_relay = subparsers.add_parser(
        "inspect-pair-agent-relay",
        help="Print the Coding Pair Agent Relay Runner readiness model.",
    )
    pair_agent_relay.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    pair_agent_relay.set_defaults(func=inspect_pair_agent_relay)
    pair_run_preview = subparsers.add_parser(
        "preview-pair-run",
        help="Create a no-effect preview pair-run envelope.",
    )
    pair_run_preview.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON preview.",
    )
    pair_run_preview.set_defaults(func=preview_pair_run)
    pair_run = subparsers.add_parser(
        "inspect-pair-run",
        help="Inspect the deterministic preview pair-run contract.",
    )
    pair_run.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    pair_run.set_defaults(func=inspect_pair_run)
    pair_artifacts = subparsers.add_parser(
        "inspect-pair-artifacts",
        help="Inspect pair-run artifact refs without raw transcript bodies.",
    )
    pair_artifacts.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    pair_artifacts.set_defaults(func=inspect_pair_artifacts)
    pair_receipts = subparsers.add_parser(
        "inspect-pair-receipts",
        help="Inspect pair-run receipt refs without execution.",
    )
    pair_receipts.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    pair_receipts.set_defaults(func=inspect_pair_receipts)
    start_pair = subparsers.add_parser(
        "start-pair-run-readiness",
        help="Inspect why foreground pair-run start remains blocked.",
    )
    start_pair.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    start_pair.set_defaults(func=start_pair_run_readiness)
    stop_pair = subparsers.add_parser(
        "stop-pair-run-readiness",
        help="Inspect why pair-run stop control has no active foreground run.",
    )
    stop_pair.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    stop_pair.set_defaults(func=stop_pair_run_readiness)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
