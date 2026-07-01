#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ultimate_ai_agent/core/web_access/browser_gateway_ladder.py"
DOC = ROOT / "docs/browser/UAA_BROWSER_GATEWAY_LADDER.md"
PRODUCT_LANGUAGE = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
TESTS = ROOT / "tests/test_browser_gateway_ladder.py"
STATIC_GUARDS = ROOT / "tests/test_web_access_static_guards.py"

STATES = [
    "declared",
    "discovered",
    "metadata_only",
    "observe_planned",
    "observe_blocked",
    "action_dry_run_planned",
    "action_dry_run_blocked",
    "exact_approved_low_risk_action_planned",
    "high_risk_action_blocked",
    "auth_cookie_download_upload_blocked",
    "mutation_blocked",
    "runtime_disabled",
]

SOURCE_REQUIRED = [
    "BrowserGatewayLadderState",
    "BrowserGatewayIntentMetadata",
    "BrowserGatewayExactApprovalBinding",
    "evaluate_browser_gateway_exact_approval_binding",
    "BrowserGatewayBlockedReceipt",
    "BrowserGatewayReplayAuditRecord",
    "build_browser_gateway_ladder_contract",
    "live_browser_execution_allowed",
    "raw_page_payload_persistence_allowed",
    "model_output_authority_allowed",
    "provider_output_authority_allowed",
    "control_center_state_authority_allowed",
]

DOC_REQUIRED = [
    "Unknown browser capability metadata is blocked and review-required",
    "Unknown does not mean read-only",
    "WebAccessGateway",
    "Approval Binding Is Not Execution",
    "live browser execution",
    "browser clicks",
    "form filling",
    "auth, cookies",
    "downloads and uploads",
    "non-GET public-web mutations",
    "raw page payloads",
    "Capability Promotion Ladder",
]

PRODUCT_LANGUAGE_REQUIRED = [
    "No browser gateway ladder authority drift",
    "Unknown browser capability metadata must be described as blocked/review-required",
    "observe planned/blocked",
    "action dry-run planned/blocked",
    "click/form/auth/cookies/download/upload/mutation",
]

TEST_REQUIRED = [
    "test_browser_gateway_ladder_states_are_ordered_and_non_executing",
    "test_browser_gateway_intent_metadata_uses_safe_refs_and_not_raw_page_payloads",
    "test_browser_gateway_exact_approval_binding_blocks_mismatched_refs",
    "test_browser_gateway_blocked_receipt_and_replay_are_safe_ref_only",
]

FORBIDDEN_SOURCE_FRAGMENTS = [
    "requests",
    "httpx",
    "urllib",
    "socket",
    "subprocess",
    "playwright",
    "selenium",
    "browserbase",
    "firecrawl",
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
    raise SystemExit(f"Browser Gateway Ladder verification failed: {message}")


def main() -> None:
    _require(SOURCE, SOURCE_REQUIRED + STATES)
    _require(DOC, DOC_REQUIRED + STATES)
    _require(PRODUCT_LANGUAGE, PRODUCT_LANGUAGE_REQUIRED)
    _require(
        DOCS_README,
        [
            "Browser Gateway Ladder",
            "docs/browser/UAA_BROWSER_GATEWAY_LADDER.md",
            "scripts/verify_browser_gateway_ladder.py",
        ],
    )
    _require(
        DOCS_INDEX,
        [
            "Browser Gateway Ladder",
            "docs/browser/UAA_BROWSER_GATEWAY_LADDER.md",
            "tests/test_browser_gateway_ladder.py",
        ],
    )
    _require(TESTS, TEST_REQUIRED)
    _require(
        STATIC_GUARDS,
        [
            "test_no_new_direct_public_web_or_browser_imports_outside_gateway",
            "playwright",
            "selenium",
            "browserbase",
        ],
    )

    source_text = _read(SOURCE).lower()
    for fragment in FORBIDDEN_SOURCE_FRAGMENTS:
        if fragment in source_text:
            _fail(f"forbidden runtime fragment in Browser Gateway source: {fragment}")

    print("Browser Gateway Ladder verification passed")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
