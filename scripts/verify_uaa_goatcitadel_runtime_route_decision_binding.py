#!/usr/bin/env python3
"""Verify the UAA GoatCitadel runtime route-decision binding slice."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "runtime" / "UAA_GOATCITADEL_RUNTIME_ROUTE_DECISION_BINDING.md"
CORE_PATH = ROOT / "src" / "ultimate_ai_agent" / "core" / "decision_router" / "route_binding.py"
CLI_PATH = ROOT / "scripts" / "dev" / "uaa_turn_router.py"
TEST_PATH = ROOT / "tests" / "test_route_decision_binding.py"

REQUIRED_DOC_STRINGS = (
    "# UAA GoatCitadel Runtime Route Decision Binding",
    "does not copy GoatCitadel code",
    "does not add runtime authority",
    "Route-decision binding is not approval",
    "Control Center still cannot mint authority",
    "runtime model calls",
    "provider SDK calls",
    "browser automation",
    "connector writes",
    "unrestricted shell/subprocess execution",
    "production authority",
    "broad autonomy",
)

REQUIRED_CORE_STRINGS = (
    "class RouteDecisionBinding",
    "class RouteDecisionMutationContext",
    "class RouteDecisionValidationResult",
    "class RouteDecisionValidationStatus",
    "expired",
    "scope_changed",
    "policy_changed",
    "replay_conflict",
    "authority_blocked",
    "unsafe_payload",
    "route_decision_is_approval",
    "validate_route_decision_binding",
)

REQUIRED_TEST_STRINGS = (
    "test_route_decision_binding_validates_current_scope_without_authority",
    "test_route_decision_binding_rejects_expired_decision",
    "test_route_decision_binding_rejects_actor_turn_or_session_mismatch",
    "test_route_decision_binding_rejects_side_effect_class_mismatch",
    "test_route_decision_binding_rejects_policy_version_drift",
    "test_route_decision_binding_rejects_approval_scope_mismatch",
    "test_route_decision_binding_rejects_provider_model_mismatch",
    "test_route_decision_binding_rejects_idempotency_replay_conflict",
    "test_route_decision_binding_rejects_safe_disable_activation",
    "test_route_decision_binding_rejects_unsafe_payload_flags",
    "test_turn_router_cli_route_binding_outputs_safe_json",
)

FORBIDDEN_STRINGS = (
    "runtime model calls are enabled",
    "provider SDK calls are enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "unrestricted shell/subprocess execution is enabled",
    "production authority is enabled",
    "broad autonomy is enabled",
)

ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s`)]+"),
    re.compile(r"/home/[^\s`)]+"),
    re.compile(r"/var/[^\s`)]+"),
    re.compile(r"/etc/[^\s`)]+"),
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _missing(text: str, required: tuple[str, ...], label: str) -> list[str]:
    return [f"missing {label}: {item}" for item in required if item not in text]


def verify() -> list[str]:
    failures: list[str] = []
    doc_text = _read(DOC_PATH)
    core_text = _read(CORE_PATH)
    cli_text = _read(CLI_PATH)
    test_text = _read(TEST_PATH)
    combined = "\n".join((doc_text, core_text, cli_text, test_text))
    lowered = combined.lower()

    failures.extend(_missing(doc_text, REQUIRED_DOC_STRINGS, "doc string"))
    failures.extend(_missing(core_text, REQUIRED_CORE_STRINGS, "core string"))
    failures.extend(_missing(test_text, REQUIRED_TEST_STRINGS, "test coverage"))
    if "route-binding" not in cli_text:
        failures.append("CLI route-binding inspection command is missing")

    for forbidden in FORBIDDEN_STRINGS:
        if forbidden.lower() in lowered:
            failures.append(f"forbidden overclaim present: {forbidden}")
    for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS:
        if pattern.search(combined):
            failures.append("route-decision binding artifacts contain an absolute local path")
            break
    return failures


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    failures = verify()
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("UAA GoatCitadel runtime route-decision binding verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
