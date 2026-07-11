#!/usr/bin/env python3
"""Verify inert WEB-HYBRID contracts, ledger, and router simulation."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.web_access import (  # noqa: E402
    WEB_HYBRID_SCHEMA_VERSION,
    WebAccessPolicy,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
    WebProviderRoutingPolicy,
)


PHASE_001_FILES = (
    Path("src/ultimate_ai_agent/core/web_access/hybrid_contracts.py"),
    Path("src/ultimate_ai_agent/core/web_access/hybrid_ledger.py"),
    Path("src/ultimate_ai_agent/core/web_access/hybrid_router.py"),
)
FORBIDDEN_IMPORT_ROOTS = {
    "firecrawl",
    "http.client",
    "httpx",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
}
PLAN_PATH = Path("docs/network/SEARXNG_FIRECRAWL_HYBRID_IMPLEMENTATION_PLAN.md")


def _import_root(name: str) -> str:
    return name.split(".", 1)[0]


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        for name in names:
            if (
                name in FORBIDDEN_IMPORT_ROOTS
                or _import_root(name) in FORBIDDEN_IMPORT_ROOTS
            ):
                failures.append(f"{path}:{node.lineno}:{name}")
    return failures


def main() -> int:
    failures: list[str] = []
    if WEB_HYBRID_SCHEMA_VERSION != "uaa-web-hybrid.v1":
        failures.append("WEB_HYBRID_SCHEMA_VERSION_MISMATCH")
    policies = {item.value for item in WebProviderRoutingPolicy}
    if policies != {
        "sealed",
        "self_host_only",
        "self_host_first_cloud_escalation",
    }:
        failures.append("WEB_HYBRID_ROUTING_POLICY_SET_INVALID")
    decision = WebAccessPolicy().evaluate(
        WebAccessRequest(
            kind=WebAccessRequestKind.EXTRACT_MARKDOWN,
            url="https://example.invalid/fixture",
        )
    )
    if decision.status != WebAccessPolicyStatus.DENIED:
        failures.append("WEB_HYBRID_EXTRACT_MARKDOWN_NOT_POLICY_DENIED")
    for path in PHASE_001_FILES:
        if not path.exists():
            failures.append(f"WEB_HYBRID_REQUIRED_FILE_MISSING:{path}")
            continue
        failures.extend(_forbidden_imports(path))
    plan = PLAN_PATH.read_text(encoding="utf-8")
    for fragment in (
        "WEB-HYBRID-001",
        "providers remain policy-denied",
        "`cloud_budget_first` absent because it was not separately accepted",
    ):
        if fragment not in plan:
            failures.append(f"WEB_HYBRID_PLAN_FRAGMENT_MISSING:{fragment}")
    if failures:
        print("WEB-HYBRID contract verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("WEB-HYBRID inert contract verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
