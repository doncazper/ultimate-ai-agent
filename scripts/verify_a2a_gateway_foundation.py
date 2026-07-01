#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ultimate_ai_agent/core/capabilities/a2a_gateway.py"
REGISTRY = ROOT / "src/ultimate_ai_agent/core/capabilities/registry.py"
DOC = ROOT / "docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md"
LADDER = ROOT / "docs/tooling/CAPABILITY_PROMOTION_LADDER.md"
PRODUCT_LANGUAGE = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
DOCS_README = ROOT / "docs/README.md"
WATCHLIST = ROOT / "docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md"
TESTS = ROOT / "tests/test_a2a_gateway_foundation.py"

SOURCE_REQUIRED = [
    "A2AAgentMetadata",
    "a2a_agent_card_to_metadata",
    "a2a_agent_metadata_to_capability_candidate",
    "build_a2a_handoff_proposal",
    "A2AExactDelegationApprovalBinding",
    "evaluate_a2a_exact_approval_binding",
    "build_a2a_blocked_receipt",
    "build_a2a_replay_audit_record",
    "A2A_REVIEW_AUTH_SCOPE",
    "remote_dispatch_allowed",
    "remote_self_approval_allowed",
]

DOC_REQUIRED = [
    "Unknown A2A agent-card metadata is blocked / review required",
    "Unknown does not mean read-only",
    "remote dispatch",
    "peer-auth runtime",
    "remote self-approval",
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
    "No A2A gateway authority drift",
    "Unknown A2A agents must be described as blocked/review-required",
    "remote self-approval",
]

FORBIDDEN_SOURCE_FRAGMENTS = [
    "requests",
    "httpx",
    "urllib",
    "socket",
    "grpc",
    "subprocess",
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
    raise SystemExit(f"A2A gateway foundation verification failed: {message}")


def main() -> None:
    _require(SOURCE, SOURCE_REQUIRED)
    _require(DOC, DOC_REQUIRED)
    _require(LADDER, LADDER_REQUIRED)
    _require(PRODUCT_LANGUAGE, PRODUCT_LANGUAGE_REQUIRED)
    _require(
        DOCS_README,
        [
            "A2A gateway foundation",
            "scripts/verify_a2a_gateway_foundation.py",
        ],
    )
    _require(
        WATCHLIST,
        [
            "UAA_A2A_GATEWAY_FOUNDATION.md",
            "unknown A2A agents are blocked",
        ],
    )
    _require(
        TESTS,
        [
            "test_a2a_card_import_defaults_to_blocked_review_required_not_delegation",
            "test_a2a_manifest_presence_is_not_callable_delegation_authority",
            "test_a2a_exact_approval_binding_blocks_mismatched_refs",
            "test_a2a_blocked_receipt_and_replay_audit_do_not_redelegate",
        ],
    )

    source_text = _read(SOURCE).lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in source_text:
            _fail(f"forbidden runtime fragment in A2A source: {fragment}")

    registry_text = _read(REGISTRY)
    if "manifest_from_a2a_agent_card" not in registry_text or "a2a_agent_card_to_metadata" not in registry_text:
        _fail("CapabilityRegistry A2A import must use the A2A gateway metadata posture")
    if "CoordinationMode.agent_as_tool" in registry_text.partition("manifest_from_a2a_agent_card")[2].split(
        "def manifest_from_mcp_tool_spec", 1
    )[0]:
        _fail("CapabilityRegistry A2A import must not grant agent_as_tool coordination")

    print("A2A gateway foundation verification passed")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
