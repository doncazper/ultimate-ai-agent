#!/usr/bin/env python3
"""Verify the exact MSG-MX-004 disposable local Synapse harness boundary."""

from __future__ import annotations

import json
from pathlib import Path
import stat

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_harness import (
    MATRIX_HARNESS_IMAGE_REF,
    MATRIX_HARNESS_LANES,
    MatrixHarnessOperation,
)


ROOT = Path(__file__).resolve().parents[1]
HARNESS_DOC = ROOT / "docs/connectors/MESSENGER_MATRIX_LOCAL_HARNESS.md"
BACKEND_PATH = (
    ROOT
    / "src/ultimate_ai_agent/core/communications/matrix_harness/backend.py"
)
COMPOSE_PATH = ROOT / "packaging/messenger-matrix-harness/compose.yaml"
PROVIDER_LOCK_PATH = (
    ROOT / "packaging/messenger-matrix-harness/provider_lock.json"
)
CLI_PATH = ROOT / "scripts/dev/uaa_communications.py"
BOARD_PATH = ROOT / "docs/kanban/current_board.md"
TRUTH_PATH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
ROUTE_STATUS_PATH = ROOT / "docs/control_center/route_status_manifest.json"


def _read(path: Path, failures: list[str]) -> str:
    try:
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode) or path.is_symlink():
            raise OSError("unsafe file")
        return path.read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing or unsafe MSG-MX-004 artifact: {path.name}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    operations = tuple(MatrixHarnessOperation)
    if len(operations) != 6 or set(MATRIX_HARNESS_LANES) != set(operations):
        failures.append("six exact Matrix harness lanes are not closed")
    for operation, lane in MATRIX_HARNESS_LANES.items():
        if operation in {
            MatrixHarnessOperation.inspect,
            MatrixHarnessOperation.smoke,
        } and lane.approval_required:
            failures.append(f"read lane unexpectedly requires approval: {operation.value}")
        if operation not in {
            MatrixHarnessOperation.inspect,
            MatrixHarnessOperation.smoke,
        } and not lane.approval_required:
            failures.append(f"mutation lane lacks exact approval: {operation.value}")

    backend = _read(BACKEND_PATH, failures)
    compose = _read(COMPOSE_PATH, failures)
    provider_lock_text = _read(PROVIDER_LOCK_PATH, failures)
    cli = _read(CLI_PATH, failures)
    harness_doc = _read(HARNESS_DOC, failures)
    board = _read(BOARD_PATH, failures)
    truth = _read(TRUTH_PATH, failures)
    index = _read(INDEX_PATH, failures)
    route_status_text = _read(ROUTE_STATUS_PATH, failures)

    for marker in (
        "start_new_session=True",
        "shell=False",
        "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES = 64 * 1024",
        "MATRIX_HARNESS_BACKEND_BINDING_CHANGED",
        "MATRIX_HARNESS_FOREIGN_RESOURCE_COLLISION",
        "MATRIX_HARNESS_LIFECYCLE_BUSY",
        "MATRIX_HARNESS_START_CLEANUP_UNCONFIRMED",
        "MATRIX_HARNESS_HOST_LOOPBACK_UNAVAILABLE",
        "MATRIX_HARNESS_FIXTURES_ALREADY_SEEDED",
        '"--pull",\n                "never"',
        '"--all", "--format", "json"',
    ):
        if marker not in backend:
            failures.append(f"backend missing exact safety marker: {marker}")
    for forbidden in ("shell" + "=True", "docker pull", "--pull=always"):
        if forbidden in backend:
            failures.append(f"backend contains forbidden behavior: {forbidden}")
    for marker in (
        "pull_policy: never",
        '127.0.0.1:18008:8008',
        "com.docker.network.bridge.gateway_mode_ipv4: nat",
        'com.docker.network.bridge.enable_ip_masquerade: "false"',
        "com.docker.network.bridge.host_binding_ipv4: 127.0.0.1",
        "read_only: true",
        "cap_drop:",
        "no-new-privileges:true",
        "pids_limit: 128",
        "mem_limit: 1g",
        "cpus: 1.0",
        "UAA_MATRIX_HARNESS_UID",
        "UAA_MATRIX_HARNESS_GID",
        "driver: none",
    ):
        if marker not in compose:
            failures.append(f"Compose missing containment marker: {marker}")

    try:
        provider_lock = json.loads(provider_lock_text)
    except json.JSONDecodeError:
        failures.append("provider lock is invalid JSON")
        provider_lock = {}
    if provider_lock.get("image") != MATRIX_HARNESS_IMAGE_REF:
        failures.append("provider lock does not pin the canonical Synapse digest")

    for marker in (
        "for operation in MatrixHarnessOperation",
        'dest="harness_operation"',
        "_matrix_harness_command",
        "execute_matrix_harness_command",
        "issue_exact_matrix_harness_lease",
    ):
        if marker not in cli:
            failures.append(f"CLI missing shared harness contract: {marker}")

    manifest = build_api_manifest(app)
    routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/harness/")
    }
    if len(routes) != 6:
        failures.append("API manifest does not expose exactly six harness routes")
    schema = app.openapi()
    for operation in operations:
        path = (
            "/control-center/communications/harness/"
            + operation.value.replace("_", "-")
        )
        route = routes.get(path)
        expected_id = f"post_control_center_communications_harness_{operation.value}"
        if route is None:
            failures.append(f"missing harness route: {path}")
            continue
        if schema["paths"][path]["post"]["operationId"] != expected_id:
            failures.append(f"operation ID drifted: {path}")
        is_mutation = operation not in {
            MatrixHarnessOperation.inspect,
            MatrixHarnessOperation.smoke,
        }
        if route.idempotency_required is not is_mutation:
            failures.append(f"idempotency posture drifted: {path}")
        if not route.protected_route or route.rate_limit_group != "communications_matrix_harness":
            failures.append(f"protection or rate-limit posture drifted: {path}")

    required_doc_markers = (
        "MSG-MX-004",
        "approval ref identifies a record only",
        "pull_policy: never",
        "recovery_required",
        "Checklist status: `not_run`",
        "standing harness authority",
        "no Matrix SDK",
        "no connector/session/message/crypto/UI/public/production authority",
    )
    combined_docs = "\n".join((harness_doc, board, truth, index)).lower()
    for marker in required_doc_markers:
        if marker.lower() not in combined_docs:
            failures.append(f"current documentation missing truth marker: {marker}")
    if "Current phase: `MSG-MX-004`" not in board:
        failures.append("current board is not bound to MSG-MX-004")
    if "evidence-ref:msg-mx-004:local-synapse-harness" not in board:
        failures.append("current board lacks Phase004 evidence ref")

    try:
        route_status = json.loads(route_status_text)
    except json.JSONDecodeError:
        failures.append("route-status manifest is invalid JSON")
        route_status = {}
    status_paths = {
        route["path"]
        for surface in route_status.get("surfaces", [])
        for route in surface.get("current_backend_routes", [])
        if route.get("path", "").startswith(
            "/control-center/communications/harness/"
        )
    }
    if status_paths != set(routes):
        failures.append("route-status manifest does not match harness API truth")

    for relative in (
        "tests/test_msg_mx_004_matrix_harness_authority.py",
        "tests/test_msg_mx_004_matrix_harness_backend.py",
        "tests/test_msg_mx_004_matrix_harness_api_cli.py",
    ):
        if not (ROOT / relative).is_file():
            failures.append(f"missing focused harness proof: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("MSG-MX-004 local Synapse harness verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
