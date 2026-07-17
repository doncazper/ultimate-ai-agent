#!/usr/bin/env python3
"""Verify the fixture-only MSG-MX-002 desktop shell contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACE_IDS = (
    "founder",
    "personal",
    "dm",
    "group",
    "threads",
    "search",
    "room-info",
    "invite",
    "room-settings",
    "sessions",
    "intelligence",
    "recovery",
    "dark",
    "calling",
    "setup",
)
VARIANT_IDS = (
    "loading",
    "initial-sync",
    "empty-room",
    "no-search-results",
    "invite-pending",
    "join-failed",
    "local-echo",
    "queued-send",
    "failed-send",
    "retry",
    "edited",
    "redacted",
    "undecryptable",
    "verification-requested",
    "verification-failed",
    "backup-unavailable",
    "offline",
    "reconnecting",
    "rate-limited",
    "permission-denied",
    "room-archived-left",
    "inspector-collapsed",
)
FORBIDDEN_DEPENDENCIES = (
    "matrix-js-sdk",
    "matrix-react-sdk",
    "element-web",
    "@matrix-org/",
)
FORBIDDEN_RUNTIME_TOKENS = (
    "useControlCenterData",
    "fetch(",
    "WebSocket(",
    "EventSource(",
    "XMLHttpRequest(",
    "navigator" + ".mediaDevices",
    "getUser" + "Media(",
    "localStorage",
    "sessionStorage",
)


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _string_array(text: str, constant: str) -> tuple[str, ...]:
    match = re.search(
        rf"export const {constant} = \[(.*?)\] as const;",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        return ()
    return tuple(re.findall(r'"([a-z0-9-]+)"', match.group(1)))


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    required = (
        "apps/control-center/src/components/messenger/MessengerShell.tsx",
        "apps/control-center/src/components/messenger/messengerShell.css",
        "apps/control-center/src/messenger/contracts.ts",
        "apps/control-center/src/messenger/fixtures.ts",
        "apps/control-center/src/components/messenger/MessengerShell.test.tsx",
    )
    for relative in required:
        if not (root / relative).is_file():
            failures.append(f"missing required MSG-MX-002 file: {relative}")
    if failures:
        return failures

    contracts = _read(root, "apps/control-center/src/messenger/contracts.ts")
    shell = _read(
        root,
        "apps/control-center/src/components/messenger/MessengerShell.tsx",
    )
    fixtures = _read(root, "apps/control-center/src/messenger/fixtures.ts")
    app = _read(root, "apps/control-center/src/App.tsx")
    package = json.loads(_read(root, "apps/control-center/package.json"))
    lockfile = _read(root, "apps/control-center/package-lock.json").lower()

    if _string_array(contracts, "MESSENGER_SURFACE_IDS") != SURFACE_IDS:
        failures.append("Messenger surface inventory must contain the exact 15 accepted IDs")
    if _string_array(contracts, "MESSENGER_VARIANT_IDS") != VARIANT_IDS:
        failures.append("Messenger state inventory must contain the exact 22 accepted IDs")

    dependencies = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    for dependency in FORBIDDEN_DEPENDENCIES:
        if any(dependency in name.lower() for name in dependencies):
            failures.append(f"forbidden Matrix/Element dependency present: {dependency}")
        if f'node_modules/{dependency}' in lockfile:
            failures.append(f"forbidden Matrix/Element lock entry present: {dependency}")

    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token in shell or token in fixtures:
            failures.append(f"forbidden Messenger runtime token present: {token}")

    messenger_branch = app.find('activePath === "/messenger"')
    data_route = app.find("return <ControlCenterRoute")
    if messenger_branch < 0 or data_route < 0 or messenger_branch > data_route:
        failures.append("Messenger must bypass ControlCenterRoute and backend data hooks")

    for required_text in (
        "data-messenger-runtime={",
        "Read-only sync ·",
        "External actions blocked",
        "Human message composer",
        "UAA proposal composer",
        "untrusted data, never instruction authority",
    ):
        if required_text not in shell:
            failures.append(f"missing Messenger fail-closed UI truth: {required_text}")

    if re.search(r"\b(?:authorized|callable)\s*:", contracts + fixtures):
        failures.append("Messenger fixture contract must not contain authorized/callable booleans")

    routes = _read(root, "apps/control-center/src/routes.tsx")
    if (
        'path: "/messenger"' not in routes
        or 'status: "fixture-only desktop content with backend-owned sync, crypto, and exact manual-messaging posture; synthetic composer remains disabled"'
        not in routes
    ):
        failures.append(
            "Messenger route must remain an explicit fixture-only content surface with backend-owned sync, crypto, and exact manual-messaging posture"
        )

    release = json.loads(_read(root, "docs/control_center/release_surface_manifest.json"))
    route = next((row for row in release["routes"] if row["path"] == "/messenger"), None)
    if route is None:
        failures.append("release surface manifest is missing /messenger")
    elif route["status"] != "experimental":
        failures.append("/messenger release truth must remain experimental")
    elif route["backend_routes"] != [
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-sync/posture",
            "operation_id": "get_control_center_communications_matrix_sync_posture",
            "side_effect_class": "none",
            "route_classification": "local_sensitive",
        },
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-crypto/posture",
            "operation_id": "get_control_center_communications_matrix_crypto_posture",
            "side_effect_class": "none",
            "route_classification": "local_sensitive",
        },
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-messaging/posture",
            "operation_id": "get_control_center_communications_matrix_messaging_posture",
            "side_effect_class": "none",
            "route_classification": "local_sensitive",
        },
    ]:
        failures.append(
            "/messenger may expose only the exact content-free Matrix sync, crypto, and manual-messaging posture routes"
        )

    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-002 static shell verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-002 static shell verification PASSED")
    print("surfaces=15 variants=22 runtime_authority_added=false desktop_only=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
