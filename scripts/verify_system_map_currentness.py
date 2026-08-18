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
_APPROVED_MANIFEST_MODULES = frozenset(
    {
        "ultimate_ai_agent.core.capabilities",
        "ultimate_ai_agent.core.capabilities.models",
        "ultimate_ai_agent.core.device_capabilities",
        "ultimate_ai_agent.core.device_capabilities.contracts",
    }
)


def discover_manifest_constructor_modules(root: Path = ROOT) -> tuple[str, ...]:
    """Return first-party modules that construct supported manifest records."""

    source_root = root / "src"
    package_root = source_root / "ultimate_ai_agent"
    discovered: set[str] = set()
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        constructor_names, module_aliases = _resolve_manifest_imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_manifest_constructor_call(
                node.func,
                constructor_names=constructor_names,
                module_aliases=module_aliases,
            ):
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


def _resolve_manifest_imports(
    tree: ast.AST,
) -> tuple[set[str], dict[str, str]]:
    constructor_names: set[str] = set()
    module_aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for imported in node.names:
                if (
                    node.module in _APPROVED_MANIFEST_MODULES
                    and imported.name in SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES
                ):
                    constructor_names.add(imported.asname or imported.name)
                imported_module = f"{node.module}.{imported.name}"
                if imported_module in _APPROVED_MANIFEST_MODULES:
                    module_aliases[imported.asname or imported.name] = imported_module
        elif isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name not in _APPROVED_MANIFEST_MODULES:
                    continue
                alias = imported.asname or imported.name
                module_aliases[alias] = imported.name
    return constructor_names, module_aliases


def _is_manifest_constructor_call(
    function: ast.expr,
    *,
    constructor_names: set[str],
    module_aliases: dict[str, str],
) -> bool:
    if isinstance(function, ast.Name):
        return function.id in constructor_names
    if not isinstance(function, ast.Attribute):
        return False
    if function.attr not in SYSTEM_MAP_MANIFEST_CONSTRUCTOR_NAMES:
        return False
    receiver = _dotted_name(function.value)
    if receiver in module_aliases:
        receiver = module_aliases[receiver]
    return receiver in _APPROVED_MANIFEST_MODULES


def _dotted_name(value: ast.expr) -> str | None:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        parent = _dotted_name(value.value)
        return f"{parent}.{value.attr}" if parent else None
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
