#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned model/provider control-plane truth."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted backend-owned schema instead of the readable summary.",
    )
    return parser


def render_summary(payload: dict[str, object]) -> str:
    routing = payload["provider_routing_intelligence"]
    assert isinstance(routing, dict)
    candidates = routing.get("candidates", [])
    assert isinstance(candidates, list)
    lines = [
        "UAA model/provider control plane",
        f"Status: {payload['status']}",
        "Authority: exact request-scoped lanes only",
        f"Routing strategy: {routing['strategy']}",
        (
            "Routing candidates: "
            f"{routing['presented_candidate_count']} presented / "
            f"{routing['observed_candidate_count']} observed"
        ),
    ]
    if not candidates:
        lines.append("  No provider candidates are available.")
    for candidate in candidates:
        assert isinstance(candidate, dict)
        rank = candidate.get("rank")
        prefix = f"  {rank}." if rank is not None else "  -"
        lines.append(f"{prefix} {candidate['provider_label']} — {candidate['status']}")
        cost = candidate.get("estimated_cost_usd")
        latency = candidate.get("estimated_latency_ms")
        lines.append(
            "     cost="
            f"{'unknown' if cost is None else cost} "
            "latency_ms="
            f"{'unknown' if latency is None else latency}"
        )
        blockers = candidate.get("blocker_codes")
        if isinstance(blockers, list) and blockers:
            lines.append(f"     blockers={','.join(str(code) for code in blockers)}")
    lines.extend(
        [
            "Provider selection is a proposal, never invocation authority.",
            "Approval refs are identifiers only; exact LocalApprovalAuthority and "
            "AuthorityLease evaluation remain required immediately before execution.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    read_model = build_model_provider_control_plane_read_model()
    payload = read_model.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
