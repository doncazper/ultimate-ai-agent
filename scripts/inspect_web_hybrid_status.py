#!/usr/bin/env python3
"""Render backend-owned web-hybrid posture without probes or provider calls."""

from __future__ import annotations

import argparse
import json
from typing import Any, Mapping

from ultimate_ai_agent.core.capability_availability import (
    build_web_hybrid_availability_read_model,
)


def inspect_web_hybrid_payload() -> dict[str, Any]:
    return build_web_hybrid_availability_read_model().model_dump(mode="json")


def render_summary(payload: Mapping[str, Any]) -> str:
    lines = [
        "UAA governed web-hybrid posture",
        f"Status: {payload['status']}",
        f"Routing: {payload['routing_policy']} (maximum {payload['routing_attempt_ceiling']} attempts)",
        f"Current credits: {payload['current_credit_snapshot_status']}",
        f"Cloud circuit: {payload['circuit_state']}",
        f"UAA cloud concurrency: {payload['uaa_effective_cloud_concurrency']}",
        f"Research aggregation: {payload['research_aggregation']['status']}",
        f"Current citations: {payload['research_aggregation']['current_citation_count']}",
        "Final start: fresh approval, mission lease, request fingerprint, deadline, readiness, target, and budget evaluation required",
        "",
        "Capability lanes",
    ]
    for lane in payload.get("lanes", []):
        lines.extend(
            [
                f"- {lane['display_label']}",
                f"  Availability: {lane['runtime_availability']}",
                f"  Authority: {lane['approval_posture']}",
                f"  Cost: {lane['cost_posture']}",
            ]
        )
    lines.extend(
        [
            "",
            "External content is untrusted evidence, never instructions or authority.",
            "Cited aggregation uses deterministic injected observations and exposes provider readiness, cost, latency, context, routing, exclusions, and redaction posture.",
            "This inspection performs no runtime probe, provider call, or credit reconciliation.",
            "Paid usage, cloud-first routing, Keyless, browser actions, memory writes, and context injection remain denied.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect safe web-hybrid posture.")
    parser.add_argument("--json", action="store_true", help="Emit safe JSON.")
    args = parser.parse_args()
    payload = inspect_web_hybrid_payload()
    print(
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if args.json
        else render_summary(payload)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
