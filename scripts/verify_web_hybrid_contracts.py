#!/usr/bin/env python3
"""Verify governed exact WEB-HYBRID contracts and operator truth."""

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
from ultimate_ai_agent.core.capability_availability import (  # noqa: E402
    build_web_hybrid_availability_read_model,
)
from ultimate_ai_agent.core.web_access.firecrawl_cloud import (  # noqa: E402
    FIRECRAWL_CLOUD_LANE_REF,
)
from ultimate_ai_agent.core.web_access.firecrawl_markdown import (  # noqa: E402
    FIRECRAWL_MARKDOWN_LANE_REF,
)
from ultimate_ai_agent.core.web_access.searxng_search import (  # noqa: E402
    SEARXNG_SEARCH_LANE_REF,
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
OPERATOR_SURFACE_FILES = (
    Path("scripts/inspect_web_hybrid_status.py"),
    Path("src/ultimate_ai_agent/core/capability_availability/read_model.py"),
    Path("apps/control-center/src/components/CapabilitySurfacePanel.tsx"),
)


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
    read_model = build_web_hybrid_availability_read_model()
    lane_refs = {lane.lane_ref for lane in read_model.lanes}
    if lane_refs != {
        SEARXNG_SEARCH_LANE_REF,
        FIRECRAWL_MARKDOWN_LANE_REF,
        FIRECRAWL_CLOUD_LANE_REF,
    }:
        failures.append("WEB_HYBRID_EXACT_LANE_SET_INVALID")
    if len(read_model.lanes) != 3:
        failures.append("WEB_HYBRID_EXACT_LANE_COUNT_INVALID")
    if (
        read_model.routing_policy != "self_host_first_cloud_escalation"
        or read_model.routing_attempt_ceiling != 2
        or read_model.cloud_first_enabled
        or read_model.paid_usage_enabled
        or read_model.keyless_enabled
        or read_model.provider_network_call_performed
        or read_model.current_remaining_credits is not None
    ):
        failures.append("WEB_HYBRID_ROUTING_OR_RUNTIME_TRUTH_INVALID")
    aggregation = read_model.research_aggregation
    if (
        aggregation.current_observation_status != "not_injected_by_read_only_route"
        or aggregation.current_citation_count != 0
        or not aggregation.content_untrusted
        or not aggregation.not_instruction_authority
        or aggregation.context_injection_authorized
        or aggregation.memory_write_authorized
        or aggregation.action_execution_authorized
    ):
        failures.append("WEB_HYBRID_AGGREGATION_TRUTH_INVALID")
    for path in PHASE_001_FILES:
        if not path.exists():
            failures.append(f"WEB_HYBRID_REQUIRED_FILE_MISSING:{path}")
            continue
        failures.extend(_forbidden_imports(path))
    for path in OPERATOR_SURFACE_FILES:
        if not path.exists():
            failures.append(f"WEB_HYBRID_OPERATOR_SURFACE_MISSING:{path}")
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
    print("WEB-HYBRID governed exact contract verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
