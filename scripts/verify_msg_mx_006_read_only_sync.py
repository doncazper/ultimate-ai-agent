#!/usr/bin/env python3
"""Verify the exact MSG-MX-006 read-only sync and protected-cache boundary."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_sync import (
    MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
    MATRIX_SYNC_LANES,
    MatrixSyncOperation,
    build_default_matrix_sync_posture,
)


ROOT = Path(__file__).resolve().parents[1]
SYNC_ROUTE = "/control-center/communications/matrix-sync/posture"


def _integrity_manifest() -> dict[str, object]:
    path = ROOT / "scripts/dev/generate_matrix_adapter_integrity.py"
    spec = importlib.util.spec_from_file_location("matrix_integrity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("MSG_MX_006_INTEGRITY_GENERATOR_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_manifest()


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-006 verifier supports the current repository root only"]
    failures: list[str] = []
    if set(MATRIX_SYNC_LANES) != set(MatrixSyncOperation) or len(MATRIX_SYNC_LANES) != 12:
        failures.append("twelve exact Matrix sync/cache/key lanes are not closed")
    if MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS != {
        MatrixSyncOperation.sync_read,
        MatrixSyncOperation.timeline_paginate_read,
    }:
        failures.append("concrete Matrix GET transport operation set drifted")
    for lane in MATRIX_SYNC_LANES.values():
        if lane.authority_capability.value in {"execute", "commit"}:
            failures.append(f"connector-write-like authority escaped: {lane.operation.value}")
        if lane.network_read and lane.operation not in {
            MatrixSyncOperation.sync_read,
            MatrixSyncOperation.timeline_paginate_read,
            MatrixSyncOperation.room_state_read,
        }:
            failures.append(f"unexpected network lane: {lane.operation.value}")

    posture = build_default_matrix_sync_posture()
    if (
        posture.runtime_status.value != "configuration_required"
        or posture.sync_enabled
        or posture.connector_writes_enabled
        or posture.message_sends_enabled
        or posture.browser_automation_enabled
        or posture.raw_content_included
        or not posture.content_untrusted
        or not posture.not_instruction_authority
        or len(posture.concrete_transport_operation_refs) != 2
        or len(posture.uncomposed_executor_operation_refs) != 10
        or "blocker-ref:matrix-sync:canonical-operation-executors-required"
        not in posture.blocker_refs
    ):
        failures.append("default Matrix sync posture no longer fails closed")

    routes = {route.path: route for route in build_api_manifest(app).routes}
    route = routes.get(SYNC_ROUTE)
    if route is None:
        failures.append("Matrix sync posture route is missing")
    elif (
        route.operation_id != "get_control_center_communications_matrix_sync_posture"
        or route.side_effect_class != "none"
        or route.route_classification != "local_sensitive"
        or not route.protected_route
    ):
        failures.append("Matrix sync posture route contract drifted")

    integrity_path = ROOT / "integrations/matrix-client-adapter/runtime-integrity.json"
    try:
        installed = json.loads(integrity_path.read_text(encoding="utf-8"))
        expected = _integrity_manifest()
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError):
        failures.append("Matrix adapter integrity metadata is unavailable")
    else:
        if installed != expected:
            failures.append("Matrix adapter integrity metadata drifted")

    required = (
        "docs/connectors/MESSENGER_MATRIX_READ_ONLY_SYNC.md",
        "tests/test_msg_mx_006_matrix_sync_authority.py",
        "tests/test_msg_mx_006_matrix_sync_cache.py",
        "tests/test_msg_mx_006_matrix_sync_dispatch.py",
        "tests/test_msg_mx_006_matrix_sync_transport.py",
        "tests/test_msg_mx_006_matrix_sync_api_cli.py",
        "tools/macos/matrix-protected-cache-helper/Package.swift",
        "tools/macos/matrix-protected-cache-helper/Sources/UAAMatrixProtectedCacheHelper/main.swift",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-006 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-006 read-only sync verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-006 read-only sync verification PASSED")
    print(
        json.dumps(
            {
                "declared_authority_lanes": 12,
                "concrete_get_transports": 2,
                "uncomposed_executors": 10,
                "live_runtime": "configuration_required",
                "connector_writes": False,
                "encrypted_content_materialization": False,
                "desktop_only": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
