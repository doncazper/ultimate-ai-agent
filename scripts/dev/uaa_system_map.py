#!/usr/bin/env python3
"""Build and inspect UAA's durable, proposal-only system capability map."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.capabilities.models import CapabilityManifest
from ultimate_ai_agent.core.system_map import (
    SystemMapSnapshot,
    SystemMapSnapshotStore,
    build_default_system_map_snapshot,
)


DEFAULT_STORE = Path(".uaa/system_map")


def load_manifest_files(paths: list[Path]) -> list[CapabilityManifest]:
    manifests: list[CapabilityManifest] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records: Any = (
            payload.get("manifests")
            if isinstance(payload, dict) and "manifests" in payload
            else payload
        )
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            raise ValueError("SYSTEM_MAP_MANIFEST_FILE_SHAPE_INVALID")
        manifests.extend(
            CapabilityManifest.model_validate(record) for record in records
        )
    manifest_ids = [manifest.id for manifest in manifests]
    if len(manifest_ids) != len(set(manifest_ids)):
        raise ValueError("SYSTEM_MAP_DUPLICATE_MANIFEST_ID")
    return manifests


def render_snapshot_summary(snapshot: SystemMapSnapshot) -> str:
    node_counts = Counter(node.kind.value for node in snapshot.graph.nodes)
    status_counts = Counter(node.truth_status.value for node in snapshot.graph.nodes)
    edge_counts = Counter(edge.kind.value for edge in snapshot.graph.edges)
    lines = [
        "UAA durable system capability map",
        "Read-only structure and proposal-only opportunity discovery; no authority is granted.",
        f"Graph: {snapshot.graph.graph_ref}",
        f"Snapshot: {snapshot.snapshot_ref}",
        (
            f"Nodes: {len(snapshot.graph.nodes)} | edges: {len(snapshot.graph.edges)} | "
            f"opportunities: {len(snapshot.opportunities)}"
        ),
        "Node kinds: " + _render_counts(node_counts),
        "Truth states: " + _render_counts(status_counts),
        "Edge kinds: " + _render_counts(edge_counts),
    ]
    return "\n".join(lines)


def render_opportunities(snapshot: SystemMapSnapshot) -> str:
    lines = [
        "UAA system map opportunity proposals",
        "Every item requires operator review and grants no authority.",
    ]
    if not snapshot.opportunities:
        lines.append(
            "No bounded composition opportunities were detected in this snapshot."
        )
        return "\n".join(lines)
    for opportunity in snapshot.opportunities:
        gaps = ", ".join(opportunity.gap_refs) or "none"
        lines.extend(
            [
                f"- {opportunity.title}",
                (
                    f"  status={opportunity.truth_status} confidence={opportunity.confidence:.2f} "
                    f"capabilities={len(opportunity.capability_node_ids)}"
                ),
                f"  proposal={opportunity.opportunity_ref}",
                f"  gaps={gaps}",
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser(
        "build", help="Build and durably save a canonical snapshot."
    )
    build.add_argument("--manifest-file", type=Path, action="append", default=[])
    build.add_argument("--max-opportunities", type=int, default=30)
    build.add_argument("--json", action="store_true")

    inspect = subparsers.add_parser(
        "inspect", help="Load and summarize the current snapshot."
    )
    inspect.add_argument("--json", action="store_true")

    opportunities = subparsers.add_parser(
        "opportunities",
        help="Inspect proposal-only compositions bound to the current graph.",
    )
    opportunities.add_argument("--json", action="store_true")

    verify = subparsers.add_parser(
        "verify", help="Verify current/history integrity and schema binding."
    )
    verify.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = SystemMapSnapshotStore(args.store)
    if args.command == "build":
        manifests = load_manifest_files(args.manifest_file)
        snapshot = build_default_system_map_snapshot(
            manifests=manifests,
            max_opportunities=args.max_opportunities,
        )
        store.save(snapshot)
        _print(
            snapshot.model_dump(mode="json")
            if args.json
            else render_snapshot_summary(snapshot)
        )
        return 0

    snapshot = store.load_current()
    if args.command == "inspect":
        _print(
            snapshot.model_dump(mode="json")
            if args.json
            else render_snapshot_summary(snapshot)
        )
        return 0
    if args.command == "opportunities":
        payload = [item.model_dump(mode="json") for item in snapshot.opportunities]
        _print(payload if args.json else render_opportunities(snapshot))
        return 0
    if args.command == "verify":
        payload = {
            "status": "verified",
            "snapshot_ref": snapshot.snapshot_ref,
            "graph_ref": snapshot.graph.graph_ref,
            "history_count": len(store.list_snapshot_refs()),
            "read_only": snapshot.read_only,
            "grants_authority": snapshot.grants_authority,
        }
        _print(
            payload
            if args.json
            else "\n".join(f"{key}: {value}" for key, value in payload.items())
        )
        return 0
    raise ValueError("SYSTEM_MAP_COMMAND_UNSUPPORTED")


def _render_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _print(payload: object) -> None:
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
