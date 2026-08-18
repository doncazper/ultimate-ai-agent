#!/usr/bin/env python3
"""Fail closed when canonical UAA capability or feature map inputs drift."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.authority import (  # noqa: E402
    build_existing_lane_authority_mappings,
)
from ultimate_ai_agent.core.ecosystem import (  # noqa: E402
    AppId,
    CANONICAL_OWNERSHIP_REGISTRY,
    CanonicalOwnerId,
)
from ultimate_ai_agent.core.system_map import (  # noqa: E402
    SYSTEM_MAP_CAPABILITY_SOURCE_MODULES,
    SYSTEM_MAP_FEATURE_CATALOG,
    SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES,
    build_default_system_map_snapshot,
)


QUEUE_ITEM_ID = "UAA-P1-092"
FIXED_TIME = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def discover_manifest_constructor_modules(root: Path = ROOT) -> tuple[str, ...]:
    """Return first-party modules that construct supported manifest records."""

    source_root = root / "src"
    package_root = source_root / "ultimate_ai_agent"
    discovered: set[str] = set()
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        constructor_names = set(SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            for imported in node.names:
                if imported.name in SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES:
                    constructor_names.add(imported.asname or imported.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            constructor = _call_name(node.func)
            if constructor not in constructor_names:
                continue
            relative = path.relative_to(source_root).with_suffix("")
            discovered.add(".".join(relative.parts))
            break
    return tuple(sorted(discovered))


def verify_repository(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    discovered = set(discover_manifest_constructor_modules(root))
    registered = set(SYSTEM_MAP_CAPABILITY_SOURCE_MODULES)
    for module in sorted(discovered - registered):
        failures.append(f"SYSTEM_MAP_CAPABILITY_SOURCE_UNREGISTERED:{module}")
    for module in sorted(registered - discovered):
        failures.append(f"SYSTEM_MAP_CAPABILITY_SOURCE_STALE:{module}")

    first = build_default_system_map_snapshot(
        created_at=FIXED_TIME,
        max_opportunities=30,
    )
    second = build_default_system_map_snapshot(
        created_at=FIXED_TIME,
        max_opportunities=30,
    )
    if first != second:
        failures.append("SYSTEM_MAP_DEFAULT_BUILD_NONDETERMINISTIC")

    node_ids = {node.node_id for node in first.graph.nodes}
    expected_nodes = {
        *(f"domain:{owner.value}" for owner in CanonicalOwnerId),
        *(f"surface:{app.value}" for app in AppId),
        *(
            f"entity:{assignment.entity_kind.value}"
            for assignment in CANONICAL_OWNERSHIP_REGISTRY.assignments
        ),
        *(mapping.lane_ref for mapping in build_existing_lane_authority_mappings()),
        *(feature.feature_ref for feature in SYSTEM_MAP_FEATURE_CATALOG),
        *(
            f"capability-source:{module}"
            for module in SYSTEM_MAP_CAPABILITY_SOURCE_MODULES
        ),
    }
    for node_id in sorted(expected_nodes - node_ids):
        failures.append(f"SYSTEM_MAP_CANONICAL_NODE_MISSING:{node_id}")

    board = root / "docs/kanban/current_board.md"
    board_text = board.read_text(encoding="utf-8") if board.exists() else ""
    if f"### {QUEUE_ITEM_ID} " not in board_text:
        failures.append("SYSTEM_MAP_MERGE_QUEUE_ITEM_MISSING")
    if (
        "System map registration: required for every future capability or feature"
        not in board_text
    ):
        failures.append("SYSTEM_MAP_FUTURE_REGISTRATION_POLICY_MISSING")

    contract = root / "docs/architecture/SYSTEM_CAPABILITY_MAP.md"
    contract_text = contract.read_text(encoding="utf-8") if contract.exists() else ""
    required_contract_terms = (
        "## Currentness and merge contract",
        "scripts/verify_system_map_currentness.py",
        "SYSTEM_MAP_FEATURE_CATALOG",
        "SYSTEM_MAP_CAPABILITY_SOURCE_MODULES",
    )
    for term in required_contract_terms:
        if term not in contract_text:
            failures.append("SYSTEM_MAP_CURRENTNESS_CONTRACT_INCOMPLETE")
            break

    pull_request_template = root / ".github/PULL_REQUEST_TEMPLATE.md"
    template_text = (
        pull_request_template.read_text(encoding="utf-8")
        if pull_request_template.exists()
        else ""
    )
    if (
        "typed system-map sources" not in template_text
        or "make verify-system-map" not in template_text
    ):
        failures.append("SYSTEM_MAP_PULL_REQUEST_CHECKLIST_MISSING")

    return failures


def _call_name(function: ast.expr) -> str | None:
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    failures = verify_repository(ROOT)
    payload = {
        "schema_version": "uaa-system-map-currentness-verification.v1",
        "status": "failed" if failures else "verified",
        "failure_refs": failures,
        "capability_source_count": len(SYSTEM_MAP_CAPABILITY_SOURCE_MODULES),
        "feature_count": len(SYSTEM_MAP_FEATURE_CATALOG),
        "grants_authority": False,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif failures:
        print("FAIL: UAA system map currentness gate")
        for failure in failures:
            print(f"- {failure}")
    else:
        print(
            "OK: UAA system map currentness gate "
            f"({payload['capability_source_count']} capability sources, "
            f"{payload['feature_count']} catalogued features)"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
