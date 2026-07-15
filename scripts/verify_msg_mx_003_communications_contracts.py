#!/usr/bin/env python3
"""Verify MSG-MX-003 backend-owned contracts and disabled Matrix posture."""

from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "src/ultimate_ai_agent/core/communications/contracts.py",
    "src/ultimate_ai_agent/core/communications/registry.py",
    "src/ultimate_ai_agent/core/communications/service.py",
    "src/ultimate_ai_agent/core/communications/matrix_disabled.py",
    "src/ultimate_ai_agent/api/communications.py",
    "scripts/dev/uaa_communications.py",
    "apps/control-center/src/api/client.communications.test.ts",
)
ROUTE_OPERATION_IDS = {
    "/control-center/communications/providers": "get_control_center_communications_providers",
    "/control-center/communications/session-posture": "get_control_center_communications_session_posture",
    "/control-center/communications/rooms": "get_control_center_communications_rooms",
    "/control-center/communications/failed-sends": "get_control_center_communications_failed_sends",
    "/control-center/communications/security-posture": "get_control_center_communications_security_posture",
    "/control-center/communications/receipts/{receipt_ref}": "get_control_center_communications_receipt",
}
DENIED_IMPORT_ROOTS = {
    "aiohttp",
    "httpx",
    "matrix_client",
    "nio",
    "requests",
    "urllib3",
}
DENIED_DEPENDENCIES = (
    "matrix-js-sdk",
    "matrix-react-sdk",
    "matrix-nio",
)


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            failures.append(f"missing MSG-MX-003 artifact: {relative}")
    if failures:
        return failures

    sys.path.insert(0, str(root / "src"))
    try:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import build_api_manifest
        from ultimate_ai_agent.core.communications import (
            CommunicationsAdapterDisabled,
            DisabledMatrixAdapter,
        )
    finally:
        if sys.path[0] == str(root / "src"):
            sys.path.pop(0)

    descriptor = DisabledMatrixAdapter().inspect_descriptor(
        checked_at=datetime(2026, 7, 14, tzinfo=timezone.utc)
    )
    snapshot = descriptor.availability
    exact_tuple = (
        snapshot.catalog_status.value,
        snapshot.compatibility_status.value,
        snapshot.configuration_status.value,
        snapshot.health_status.value,
        snapshot.authority_posture.value,
        snapshot.resource_status.value,
        snapshot.cost_posture.value,
        snapshot.safe_disable_status.value,
        snapshot.freshness_status.value,
        snapshot.runtime_readiness_status.value,
    )
    if exact_tuple != (
        "unsupported",
        "unknown",
        "not_configured",
        "unknown",
        "blocked",
        "unknown",
        "unknown",
        "unknown",
        "unknown",
        "unknown",
    ):
        failures.append("disabled Matrix availability tuple drifted")

    for method in (
        "authenticate",
        "synchronize",
        "read_messages",
        "send_message",
        "initialize_crypto",
        "transfer_media",
    ):
        try:
            getattr(DisabledMatrixAdapter(), method)()
        except CommunicationsAdapterDisabled:
            pass
        else:
            failures.append(f"disabled Matrix runtime method became callable: {method}")

    manifest = build_api_manifest(app)
    manifest_routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/")
    }
    if not set(ROUTE_OPERATION_IDS).issubset(manifest_routes):
        failures.append("communications route inventory drifted")
    for path, expected_operation_id in ROUTE_OPERATION_IDS.items():
        route = manifest_routes.get(path)
        if route is None:
            continue
        if route.method != "GET":
            failures.append(f"communications route is not read-only GET: {path}")
        if route.operation_id != expected_operation_id:
            failures.append(f"communications operation ID drifted: {path}")
        if route.side_effect_class != "none":
            failures.append(f"communications route has side effects: {path}")
        if route.route_classification != "local_sensitive":
            failures.append(
                f"communications route lost protected classification: {path}"
            )

    schema = app.openapi()
    for path, expected_operation_id in ROUTE_OPERATION_IDS.items():
        if (
            schema.get("paths", {}).get(path, {}).get("get", {}).get("operationId")
            != expected_operation_id
        ):
            failures.append(f"communications OpenAPI operation ID drifted: {path}")

    declared = set(manifest.capabilities_declared)
    blocked = set(manifest.capabilities_blocked)
    if "communications_backend_owned_normalized_contracts" not in declared:
        failures.append("communications declaration missing from API manifest")
    if "communications_matrix_message_send_or_mutation" not in blocked:
        failures.append("communications write denial missing from API manifest")

    imported: set[str] = set()
    for path in (root / "src/ultimate_ai_agent/core/communications").glob("*.py"):
        imported.update(_imports(path))
    if imported.intersection(DENIED_IMPORT_ROOTS):
        failures.append(
            "communications core imports a denied network or Matrix runtime"
        )

    package_text = (
        (root / "apps/control-center/package.json").read_text(encoding="utf-8").lower()
    )
    lock_text = (
        (root / "apps/control-center/package-lock.json")
        .read_text(encoding="utf-8")
        .lower()
    )
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8").lower()
    for dependency in DENIED_DEPENDENCIES:
        if (
            dependency in package_text
            or dependency in lock_text
            or dependency in pyproject
        ):
            failures.append(f"forbidden Matrix dependency added: {dependency}")

    endpoints = (root / "apps/control-center/src/api/endpoints.ts").read_text(
        encoding="utf-8"
    )
    client = (root / "apps/control-center/src/api/client.ts").read_text(
        encoding="utf-8"
    )
    for fragment in (
        "communicationsProviders",
        "communicationsSessionPosture",
        "communicationsRooms",
        "communicationsFailedSends",
        "communicationsSecurityPosture",
    ):
        if fragment not in endpoints:
            failures.append(f"TypeScript endpoint binding missing: {fragment}")
    for fragment in (
        "loadCommunicationsProviders",
        "loadCommunicationsSessionPosture",
        "loadCommunicationsRooms",
        "loadCommunicationsFailedSends",
        "loadCommunicationsSecurityPosture",
        "loadCommunicationsReceipt",
    ):
        if fragment not in client:
            failures.append(f"TypeScript client binding missing: {fragment}")

    board = (root / "docs/kanban/current_board.md").read_text(encoding="utf-8")
    truth = (root / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md").read_text(
        encoding="utf-8"
    )
    if "MSG-MX-003" not in board:
        failures.append("current board does not preserve MSG-MX-003 history")
    if (
        "MSG-MX-003 implements backend-owned normalized communications contracts"
        not in truth
    ):
        failures.append("MSG-MX-003 product truth is missing")

    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-003 communications contract verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-003 communications contract verification PASSED")
    print(
        json.dumps(
            {"routes": 6, "runtime_authority_added": False, "desktop_only": True}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
