#!/usr/bin/env python3
"""Verify the finite MSG-MX-012 Messenger acceptance packet."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/connectors/MESSENGER_MATRIX_ACCEPTANCE_PACKET.md"

EXPECTED_MILESTONES = {f"MSG-MX-{index:03d}" for index in range(13)}
EXPECTED_SURFACES = {f"COMMS-MX-{index:02d}" for index in range(1, 16)}
EXPECTED_SCENARIOS = {
    "restart",
    "offline",
    "rate-limit",
    "revocation",
    "decryption",
    "backup",
    "retry",
    "duplicate",
    "malicious-event",
    "redaction",
    "rollback",
    "safe-disable",
    "Element interoperability",
}
REQUIRED_STATES = {
    "implemented",
    "partial",
    "blocked",
    "unsupported",
    "configuration_required",
    "external_facility_required",
}


def _table_ids(text: str, prefix: str) -> list[str]:
    return re.findall(rf"^\| `({re.escape(prefix)}[^`]+)` \|", text, re.MULTILINE)


def _scenario_ids(text: str) -> list[str]:
    section = text.partition("## Required Failure And Recovery Scenarios")[2]
    section = section.partition("## API, CLI, And macOS Desktop Parity")[0]
    return re.findall(
        r"^\| ([^|]+?) \| `(?:implemented|partial|blocked|unsupported|configuration_required|external_facility_required)` \|",
        section,
        re.MULTILINE,
    )


def verify_packet_text(text: str) -> list[str]:
    failures: list[str] = []
    milestones = _table_ids(text, "MSG-MX-")
    surfaces = _table_ids(text, "COMMS-MX-")
    scenarios = _scenario_ids(text)

    if set(milestones) != EXPECTED_MILESTONES or len(milestones) != 13:
        failures.append("MSG-MX-012 milestone matrix is incomplete or duplicated")
    if set(surfaces) != EXPECTED_SURFACES or len(surfaces) != 15:
        failures.append("MSG-MX-012 desktop surface matrix is incomplete or duplicated")
    if set(scenarios) != EXPECTED_SCENARIOS or len(scenarios) != 13:
        failures.append(
            "MSG-MX-012 failure/recovery scenario matrix is incomplete or duplicated"
        )
    for state in sorted(REQUIRED_STATES):
        if f"`{state}`" not in text:
            failures.append(f"MSG-MX-012 state vocabulary missing: {state}")

    for marker in (
        "grants no new runtime authority",
        "partial_acceptance_evidence",
        "desktop-only",
        "676 focused Python Messenger tests",
        "Element Desktop",
        "evidence was not simulated",
        "approval ref alone authorizes",
        "No safe in-scope runtime defect was found",
        "no persistent crypto adapter",
        "no provider/model invocation",
        "no enrolled remote account",
    ):
        if marker not in text:
            failures.append(f"MSG-MX-012 acceptance marker missing: {marker}")

    for forbidden in ("/Users/", "file://", "access_token", "Bearer ey"):
        if forbidden in text:
            failures.append(
                f"MSG-MX-012 packet contains forbidden durable data: {forbidden}"
            )
    return failures


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing or unreadable MSG-MX-012 artifact: {relative}")
        return ""


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-012 verifier supports the current repository root only"]
    failures: list[str] = []
    try:
        packet_text = PACKET.read_text(encoding="utf-8")
    except OSError:
        return ["missing or unreadable MSG-MX-012 acceptance packet"]
    failures.extend(verify_packet_text(packet_text))

    truth_text = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)
    board_text = _read("docs/kanban/current_board.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    docs_readme = _read("docs/README.md", failures)
    for marker, text, label in (
        ("MSG-MX-012 grants no new runtime lane", truth_text, "release truth"),
        ("Current phase: `MSG-MX-012`", board_text, "current board"),
        ("partial_acceptance_evidence", board_text, "current board status"),
        ("MESSENGER_MATRIX_ACCEPTANCE_PACKET.md", docs_index, "documentation index"),
        ("MSG-MX-012", docs_readme, "documentation entrypoint"),
    ):
        if marker not in text:
            failures.append(f"MSG-MX-012 {label} marker missing: {marker}")

    frontend = _read(
        "apps/control-center/src/components/messenger/MessengerShell.tsx", failures
    )
    cli = _read("scripts/dev/uaa_communications.py", failures)
    endpoints = _read("apps/control-center/src/api/endpoints.ts", failures)
    for marker, text, label in (
        ("loadMatrixSyncPosture", frontend, "desktop sync posture"),
        ("loadMatrixCryptoPosture", frontend, "desktop crypto posture"),
        ("loadMatrixMessagingPosture", frontend, "desktop messaging posture"),
        ("loadMatrixRoomsMediaPosture", frontend, "desktop rooms/media posture"),
        ("loadMatrixIntelligencePosture", frontend, "desktop intelligence posture"),
        ("loadMatrixHardeningPosture", frontend, "desktop hardening posture"),
        ("matrix-sync-status", cli, "CLI sync posture"),
        ("matrix-crypto-status", cli, "CLI crypto posture"),
        ("matrix-messaging-status", cli, "CLI messaging posture"),
        ("matrix-rooms-media-status", cli, "CLI rooms/media posture"),
        ("matrix-intelligence-status", cli, "CLI intelligence posture"),
        ("matrix-hardening-status", cli, "CLI hardening posture"),
        (
            "communicationsMatrixHardeningPosture",
            endpoints,
            "desktop/API endpoint parity",
        ),
    ):
        if marker not in text:
            failures.append(f"MSG-MX-012 {label} marker missing: {marker}")

    route_inventory = ROOT / "tests/fixtures/api_route_inventory_133.json"
    try:
        route_payload = json.loads(route_inventory.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        failures.append("MSG-MX-012 route inventory is missing or invalid")
    else:
        routes = route_payload.get("routes", route_payload)
        communications = [
            route
            for route in routes
            if isinstance(route, dict)
            and str(route.get("path", "")).startswith("/control-center/communications")
        ]
        if len(communications) != 75:
            failures.append("MSG-MX-012 accepted communications route count drifted")
        if any(
            route.get("route_classification")
            not in {"local_sensitive", "mutating_requires_authority"}
            or route.get("auth_posture") != "protected_local_bearer_required"
            for route in communications
        ):
            failures.append("MSG-MX-012 communications route protection drifted")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-012 Messenger acceptance verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-012 Messenger acceptance verification PASSED")
    print(
        json.dumps(
            {
                "milestones": 13,
                "desktop_surfaces": 15,
                "failure_recovery_scenarios": 13,
                "new_runtime_authority": False,
                "element_interoperability": "external_facility_required",
                "runtime": "partial_acceptance_evidence",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
