#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DOC_PATH = ROOT / "docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md"
PRODUCT_LANGUAGE_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
CURRENT_BOARD_PATH = ROOT / "docs/kanban/current_board.md"
DOC_INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
README_PATH = ROOT / "docs/README.md"
CANONICAL_MAP_PATH = ROOT / "docs/canonical/CANONICAL_DOC_MAP.md"
TRUTH_PACKET_PATH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
ROADMAP_PATH = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"

REQUIRED_DOC_FRAGMENTS = {
    "Status: planning-only provider billing authority boundary; provider billing",
    "authority remains blocked.",
    "prefers exact per-request and per-session max USD",
    "Python Agent Core remains the authority boundary.",
    "no_billing_authority",
    "per_request_max_usd",
    "per_session_max_usd",
    "spend_window_exhausted",
    "unknown_cost_blocked",
    "incomplete_cost_blocked",
    "billing_review_required",
    "No state may be implemented as a broad spend toggle.",
    "Exact approval",
    "CostGovernor hard limits",
    "Actual usage/cost receipts",
    "Incomplete-cost blocking",
    "Revocation",
    "UI/CLI inspection",
    "Audit/replay posture",
    "Safe-disable/rollback posture",
    "No hidden prompt injection",
    "No raw payload persistence",
    "Red-team checks",
    "CostGovernor must hard-block before provider use",
    "Unknown cost and incomplete cost are stop conditions, not warnings.",
    "No billing integration.",
    "No payment methods.",
    "No subscription management.",
    "No broad spend toggle.",
    "No production billing claims.",
    "No provider calls.",
    "No autonomous/background calls.",
    "No runtime activation.",
}

REQUIRED_SUPPORTING_FRAGMENTS = {
    PRODUCT_LANGUAGE_PATH: "No provider billing authority drift",
    CURRENT_BOARD_PATH: "Provider Billing Authority Boundary",
    DOC_INDEX_PATH: "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
    README_PATH: "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
    CANONICAL_MAP_PATH: "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
    TRUTH_PACKET_PATH: "Provider Billing Authority Boundary",
    ROADMAP_PATH: "Provider billing authority remains blocked.",
}

FORBIDDEN_DOC_FRAGMENTS = {
    "provider billing authority is implemented",
    "provider billing authority is enabled",
    "provider billing authority is available",
    "billing authority is granted",
    "billing authority is enabled",
    "broad spend toggle is enabled",
    "broad spend toggle is available",
    "payment methods are enabled",
    "subscription management is enabled",
    "autonomous provider billing is enabled",
    "background provider billing is enabled",
    "provider calls are enabled by billing posture",
    "production billing is available",
}

FORBIDDEN_DOC_PATTERNS = {
    "provider_billing_authority_enabled": re.compile(
        r"\bprovider billing authority\s+(?:is\s+)?"
        r"(?:implemented|enabled|available|live|callable|granted)\b"
    ),
    "billing_authority_granted": re.compile(
        r"\bbilling authority\s+(?:is\s+)?"
        r"(?:granted|enabled|available|live|callable)\b"
    ),
    "broad_spend_toggle_enabled": re.compile(
        r"\bbroad spend toggle\s+(?:is\s+)?"
        r"(?:implemented|enabled|available|live|callable)\b"
    ),
    "payment_methods_enabled": re.compile(
        r"\bpayment methods?\s+(?:is|are)\s+"
        r"(?:implemented|enabled|available|live|callable)\b"
    ),
    "subscription_management_enabled": re.compile(
        r"\bsubscription management\s+(?:is\s+)?"
        r"(?:implemented|enabled|available|live|callable)\b"
    ),
    "production_billing_available": re.compile(
        r"\bproduction billing\s+(?:is\s+)?"
        r"(?:implemented|enabled|available|live|callable)\b"
    ),
}

FORBIDDEN_API_ROUTE_FRAGMENTS = {
    "/providers/billing-authority",
    "/providers/billing",
    "/provider-billing-authority",
    "/billing-authority",
    "provider_billing_authority",
}


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing required file: {_display_path(path)}")
        return ""
    return path.read_text(encoding="utf-8")


def _append_authority_drift_failures(
    failures: list[str],
    *,
    label: str,
    text: str,
) -> None:
    lowered = text.lower()
    for fragment in FORBIDDEN_DOC_FRAGMENTS:
        if fragment in lowered:
            failures.append(f"{label} contains authority drift: {fragment}")
    for drift_label, pattern in FORBIDDEN_DOC_PATTERNS.items():
        if pattern.search(lowered):
            failures.append(f"{label} contains authority drift: {drift_label}")


def _append_api_route_failures(failures: list[str]) -> None:
    api_root = ROOT / "src/ultimate_ai_agent/api"
    for path in api_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for fragment in FORBIDDEN_API_ROUTE_FRAGMENTS:
            if fragment in lowered:
                failures.append(
                    f"{_display_path(path)} contains forbidden runtime route fragment: {fragment}"
                )


def validate_provider_billing_authority_boundary() -> list[str]:
    failures: list[str] = []
    doc_text = _read(DOC_PATH, failures)

    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in doc_text:
            failures.append(
                f"provider billing authority boundary missing fragment: {fragment}"
            )

    _append_authority_drift_failures(
        failures,
        label="provider billing authority boundary",
        text=doc_text,
    )

    for path, fragment in REQUIRED_SUPPORTING_FRAGMENTS.items():
        text = _read(path, failures)
        if fragment not in text:
            failures.append(
                f"{_display_path(path)} missing provider billing boundary fragment: {fragment}"
            )
        _append_authority_drift_failures(
            failures,
            label=_display_path(path),
            text=text,
        )

    _append_api_route_failures(failures)
    return failures


def main() -> int:
    failures = validate_provider_billing_authority_boundary()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("provider billing authority boundary verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
