from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.runtime_gateway import (
    build_runtime_streaming_progress_read_model_from_authority_catalog,
    iter_runtime_streaming_progress_sse_lines,
)


def _print_read_model(read_model: dict[str, Any]) -> None:
    print("Runtime streaming progress")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Stream state: {read_model['stream_state']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(f"Events: {read_model['event_count']}")
    print(f"Preview replay: {read_model['readonly_sse_replay_enabled']}")
    print(f"Live subscription: {read_model['live_subscription_enabled']}")
    print(f"Live SSE transport: {read_model['sse_transport_enabled']}")
    print(f"Live WebSocket transport: {read_model['websocket_transport_enabled']}")
    print(f"Stale stream: {read_model['stale_stream']}")
    print("Event previews:")
    for event in read_model["event_previews"]:
        print(f"- #{event['sequence']} {event['event_kind']} {event['event_ref']}")
        print(f"  proof={event['proof_ref']}")
        print(f"  hash={event['event_hash_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-streaming-progress",
        "runtime_streaming_progress": read_model,
        "authority_state": {
            "route_ref": read_model["authority_state_route_ref"],
            "cli_ref": read_model["authority_state_cli_ref"],
            "mapping_ref": read_model["authority_state_mapping_ref"],
            "catalog_ref": read_model["authority_state_catalog_ref"],
            "decision_ref": read_model["authority_state_decision_ref"],
            "decision_outcome": read_model["authority_state_decision_outcome"],
        },
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_tool_payload_omitted": True,
        "raw_logs_omitted": True,
        "raw_runtime_payload_persisted": False,
        "raw_tool_payload_persisted": False,
        "raw_generated_content_persisted": False,
        "raw_log_persisted": False,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "execution_performed": False,
        "live_subscription_performed": False,
        "readonly_sse_replay_available": read_model["readonly_sse_replay_enabled"],
        "readonly_sse_replay_source_posture": read_model[
            "readonly_sse_replay_source_posture"
        ],
        "sse_subscription_performed": False,
        "websocket_subscription_performed": False,
    }


def inspect(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model_obj = build_runtime_streaming_progress_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    read_model = read_model_obj.model_dump(mode="json")
    if args.replay_sse:
        if not args.run_ref:
            print("ERROR: --run-ref is required with --replay-sse", file=sys.stderr)
            return 2
        try:
            for line in iter_runtime_streaming_progress_sse_lines(
                read_model_obj,
                run_ref=args.run_ref,
                after_sequence=args.after_sequence,
            ):
                print(line, end="")
        except ValueError:
            print(
                "ERROR: read-only SSE replay is limited to deterministic redacted preview refs",
                file=sys.stderr,
            )
            return 2
        return 0
    if args.json:
        print(json.dumps(_payload(read_model), indent=2, sort_keys=True))
    else:
        _print_read_model(read_model)
    return 0


def register_parser(subparsers: object) -> None:
    parser = subparsers.add_parser(
        "inspect-streaming-progress",
        help=(
            "Inspect redacted runtime streaming progress previews without live "
            "transport."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime streaming progress read model as JSON.",
    )
    parser.add_argument(
        "--replay-sse",
        action="store_true",
        help="Replay deterministic redacted progress previews as read-only SSE lines.",
    )
    parser.add_argument(
        "--run-ref",
        help="Existing runtime or UAA durable run ref required for --replay-sse.",
    )
    parser.add_argument(
        "--after-sequence",
        type=int,
        default=-1,
        help="Resume read-only preview replay after this event sequence.",
    )
    parser.set_defaults(func=inspect)
