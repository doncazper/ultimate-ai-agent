#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.runtime_action_bridge import (  # noqa: E402
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.runtime_gateway import RuntimeInvocationStore  # noqa: E402


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _bridge_payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-action-inbox-bridge",
        "runtime_action_inbox_bridge_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _print_bridge_summary(read_model: dict[str, Any]) -> None:
    print("Governed runtime Action Inbox bridge")
    print(f"Status: {read_model['status']}")
    print(f"Contract: {read_model['contract_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Summary: {read_model['operator_summary']}")
    print(
        "Counts: "
        f"items={read_model['item_count']} "
        f"pending={read_model['pending_approval_count']} "
        f"approved={read_model['approved_pending_execution_count']} "
        f"receipts={read_model['receipt_recorded_count']} "
        f"blocked={read_model['blocked_count']}"
    )
    print("Authority: exact focused pytest bridge only; broad runtime remains blocked")
    print(
        "Blocked: "
        + ", ".join(read_model["blocked_authority_refs"] or ["none"])
    )
    print("Items:")
    if not read_model["items"]:
        print("- none")
        return
    for item in read_model["items"]:
        approval = "validated" if item["approval_validated"] else "not_validated"
        execution = "performed" if item["execution_performed"] else "not_performed"
        print(
            f"- {item['invocation_ref']} "
            f"intent={item.get('command_intent') or 'not_applicable'} "
            f"status={item['status']} approval={approval} execution={execution}"
        )
        print(f"  envelope: {item['action_envelope_ref']}")
        print(f"  scope: {item['exact_scope_ref']}")
        print(f"  receipt refs: {', '.join(item['receipt_refs'] or ['none'])}")
        print(f"  evidence refs: {', '.join(item['evidence_refs'] or ['none'])}")
        print(
            "  blocked reason refs: "
            + ", ".join(item["blocked_reason_refs"] or ["none"])
        )


def _runtime_store(args: argparse.Namespace) -> RuntimeInvocationStore:
    if args.state_dir is None:
        return RuntimeInvocationStore()
    return RuntimeInvocationStore(Path(args.state_dir))


def _inspect_action_inbox_bridge(args: argparse.Namespace) -> int:
    store = _runtime_store(args)
    read_model = build_runtime_action_inbox_bridge_read_model(store.list_invocations())
    if args.json:
        _print_json(_bridge_payload(read_model))
    else:
        _print_bridge_summary(read_model)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uaa_runtime",
        description="Inspect governed runtime pilot state through safe refs.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local runtime state directory; the value is not echoed.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bridge = subparsers.add_parser(
        "inspect-action-inbox-bridge",
        help="Inspect the runtime Action Inbox execution bridge read model.",
    )
    bridge.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref read model as JSON for automation.",
    )
    bridge.set_defaults(func=_inspect_action_inbox_bridge)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
