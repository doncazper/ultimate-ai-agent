#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ultimate_ai_agent/core/capabilities/mcp_gateway.py"
REGISTRY = ROOT / "src/ultimate_ai_agent/core/capabilities/registry.py"
DOC = ROOT / "docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md"
LADDER = ROOT / "docs/tooling/CAPABILITY_PROMOTION_LADDER.md"
PRODUCT_LANGUAGE = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
DOCS_README = ROOT / "docs/README.md"
WATCHLIST = ROOT / "docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md"
TESTS = ROOT / "tests/test_mcp_gateway_foundation.py"

SOURCE_REQUIRED = [
    "McpDiscoveryToolMetadata",
    "mcp_tool_metadata_to_capability_candidate",
    "build_mcp_preview_contract",
    "McpExactApprovalBinding",
    "evaluate_mcp_exact_approval_binding",
    "build_mcp_blocked_receipt",
    "build_mcp_replay_audit_record",
    "MCP_REVIEW_AUTH_SCOPE",
    "mcp_tools_call_allowed",
    "network_transport_allowed",
]

DOC_REQUIRED = [
    "Unknown MCP tool does not mean",
    "read-only",
    "blocked / review required",
    "MCP runtime invocation",
    "generic `tools/call`",
    "server subprocess start",
    "network transport",
    "OAuth flow execution",
    "connector writes",
    "Capability Promotion Ladder",
]

LADDER_REQUIRED = [
    "Declared",
    "Discovered",
    "Imported as UAA Capability Candidate",
    "Classified",
    "Preview/Dry-run",
    "Policy checked",
    "Exact approval bound",
    "Broker-invoked",
    "Receipted",
    "Replayable",
    "Revocable",
    "Unknown does not mean read-only",
]

PRODUCT_LANGUAGE_REQUIRED = [
    "No MCP gateway authority drift",
    "Unknown MCP tools must be described as blocked/review-required, not read-only.",
    "generic `tools/call`",
]

FORBIDDEN_SOURCE_FRAGMENTS = [
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "tools/call",
    "playwright",
    "selenium",
]


def _read(path: Path) -> str:
    if not path.exists():
        _fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _require(path: Path, fragments: list[str]) -> None:
    text = _read(path)
    for fragment in fragments:
        if fragment not in text:
            _fail(f"{path.relative_to(ROOT)} missing fragment: {fragment}")


def _fail(message: str) -> None:
    raise SystemExit(f"MCP gateway foundation verification failed: {message}")


def main() -> None:
    _require(SOURCE, SOURCE_REQUIRED)
    _require(DOC, DOC_REQUIRED)
    _require(LADDER, LADDER_REQUIRED)
    _require(PRODUCT_LANGUAGE, PRODUCT_LANGUAGE_REQUIRED)
    _require(
        DOCS_README,
        [
            "MCP gateway foundation and capability promotion ladder",
            "scripts/verify_mcp_gateway_foundation.py",
        ],
    )
    _require(WATCHLIST, ["UAA_MCP_GATEWAY_FOUNDATION.md", "unknown MCP tools as blocked"])
    _require(
        TESTS,
        [
            "test_unknown_mcp_tool_import_defaults_to_blocked_review_required_not_read_only",
            "test_mcp_metadata_is_not_callable_by_manifest_presence_alone",
            "test_mcp_exact_approval_binding_blocks_mismatched_refs",
            "test_mcp_blocked_receipt_and_replay_audit_are_replayable_without_reexecution",
        ],
    )

    source_text = _read(SOURCE).lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in source_text:
            _fail(f"forbidden runtime fragment in MCP source: {fragment}")

    registry_text = _read(REGISTRY)
    if "manifest_from_mcp_tool_spec" not in registry_text or "unknown_blocked" not in registry_text:
        _fail("CapabilityRegistry MCP import must fail closed through unknown_blocked posture")

    print("MCP gateway foundation verification passed")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
