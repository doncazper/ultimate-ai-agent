#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DOC_PATH = ROOT / "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md"
PRODUCT_LANGUAGE_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
CURRENT_BOARD_PATH = ROOT / "docs/kanban/current_board.md"
DOC_INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
README_PATH = ROOT / "docs/README.md"
CANONICAL_MAP_PATH = ROOT / "docs/canonical/CANONICAL_DOC_MAP.md"
TRUTH_PACKET_PATH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"

REQUIRED_DOC_FRAGMENTS = {
    "Status: disabled-default live adapter lane implemented; broad callable provider runtime remains future gated.",
    "credential_ref",
    "provider_ref",
    "model_ref",
    "`PolicyEngine` policy validation",
    "exact approval scope validated by `LocalApprovalAuthority`",
    "`CostGovernor` decision",
    "unknown paid cost blocked by default",
    "max approved USD",
    "idempotency ref",
    "redacted request receipt ref",
    "redacted response receipt ref",
    "`PolicyEngine` policy decision ref",
    "no raw prompt, response, or provider payload persistence",
    "rollback or safe-disable posture",
    "durable receipt replay guard before any scoped network call",
    "provider-network-attempt failures both remain",
    "receipt-backed",
    "blocked_missing_policy_validation",
    "live_adapter_blocked",
    "CLI inspection parity",
    "UI blocked, approved, and cost-blocked states",
    "No provider SDK calls.",
    "No enabled runtime invocation by default.",
    "No credential validation authority through this invocation lane.",
    "No network calls by default.",
    "No network calls outside `OpenAICompatibleTinyLiveProviderAdapter`.",
    "No model output authority.",
}
REQUIRED_SUPPORTING_FRAGMENTS = {
    PRODUCT_LANGUAGE_PATH: "No provider invocation promotion authority drift",
    CURRENT_BOARD_PATH: "Tiny Exact-Approved Provider Invocation Lane",
    DOC_INDEX_PATH: "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
    README_PATH: "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
    CANONICAL_MAP_PATH: "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
    TRUTH_PACKET_PATH: "Tiny Exact-Approved Provider Invocation Lane",
}
REQUIRED_SUPPORTING_POLICY_FRAGMENTS = {
    PRODUCT_LANGUAGE_PATH: "exact approval",
    CURRENT_BOARD_PATH: "exact approval",
    TRUTH_PACKET_PATH: "exact-approval-bound",
}
FORBIDDEN_DOC_FRAGMENTS = {
    "provider invocation is implemented",
    "provider invocation is enabled",
    "runtime invocation is available",
    "provider sdk call is available",
    "credential validation is available",
    "network call is available",
    "model output is authority",
    "provider output is authority",
    "broad provider enabled toggle is available",
}
FORBIDDEN_DOC_PATTERNS = {
    "provider_invocation_available": re.compile(
        r"\bprovider invocation\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "provider_sdk_calls_available": re.compile(
        r"\bprovider sdk calls?\s+(?:is|are)\s+"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "runtime_invocation_available": re.compile(
        r"\bruntime invocation\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "providers_callable": re.compile(r"\bproviders?\s+(?:is|are)\s+callable\b"),
    "credential_validation_available": re.compile(
        r"\bcredential validation\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "network_calls_available": re.compile(
        r"\bnetwork calls?\s+(?:is|are)\s+"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "model_output_authority": re.compile(
        r"\bmodel output\s+(?:has authority|is authority|is authoritative)\b"
    ),
    "provider_output_authority": re.compile(
        r"\bprovider output\s+(?:has authority|is authority|is authoritative)\b"
    ),
    "broad_provider_toggle_available": re.compile(
        r"\bbroad provider enabled toggle\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live)\b"
    ),
}


def _read(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing required file: {_display_path(path)}")
        return ""
    return path.read_text(encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def validate_provider_invocation_promotion_plan() -> list[str]:
    failures: list[str] = []
    doc_text = _read(DOC_PATH, failures)

    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in doc_text:
            failures.append(f"provider invocation plan missing fragment: {fragment}")

    _append_authority_drift_failures(
        failures,
        label="provider invocation plan",
        text=doc_text,
    )

    for path, fragment in REQUIRED_SUPPORTING_FRAGMENTS.items():
        text = _read(path, failures)
        if fragment not in text:
            failures.append(
                f"{_display_path(path)} missing provider invocation plan fragment: {fragment}"
            )
        policy_fragment = REQUIRED_SUPPORTING_POLICY_FRAGMENTS.get(path)
        if policy_fragment is not None and policy_fragment not in text:
            failures.append(
                f"{_display_path(path)} missing provider policy gate fragment: {policy_fragment}"
            )
        _append_authority_drift_failures(
            failures,
            label=_display_path(path),
            text=text,
        )

    return failures


def main() -> int:
    failures = validate_provider_invocation_promotion_plan()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("provider invocation promotion plan verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
