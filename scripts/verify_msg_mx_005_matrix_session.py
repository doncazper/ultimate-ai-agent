#!/usr/bin/env python3
"""Verify the exact partial MSG-MX-005 discovery/session boundary."""

from __future__ import annotations

import importlib.util
import json
import re
import stat
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_session import (
    MATRIX_SESSION_LANES,
    MatrixSessionOperation,
    build_matrix_session_lane_catalog_entries,
)

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_ROOT = ROOT / "integrations/matrix-client-adapter"
PACKAGE_PATH = ADAPTER_ROOT / "package.json"
LOCK_PATH = ADAPTER_ROOT / "package-lock.json"
NOTICE_PATH = ADAPTER_ROOT / "THIRD_PARTY_NOTICES.md"
INTEGRITY_PATH = ADAPTER_ROOT / "runtime-integrity.json"
NODE_RUNTIME_TRUST_PATH = ADAPTER_ROOT / "runtime-trust" / "node-runtime.json"
HELPER_SOURCE_PATH = (
    ROOT
    / "tools/macos/matrix-session-keychain-helper/Sources/UAAMatrixSessionKeychainHelper/main.swift"
)
SESSION_DOC_PATH = ROOT / "docs/connectors/MESSENGER_MATRIX_SESSION.md"
APPROVED_LICENSES = {"Apache-2.0", "MIT"}
BLOCKED_OPERATIONS = {
    MatrixSessionOperation.credential_auth_create,
    MatrixSessionOperation.sso_launch,
    MatrixSessionOperation.sso_callback_consume,
    MatrixSessionOperation.refresh,
    MatrixSessionOperation.logout,
    MatrixSessionOperation.revoke_all,
    MatrixSessionOperation.credential_store_rotate,
    MatrixSessionOperation.credential_delete,
}


def _build_integrity_manifest() -> dict[str, object]:
    path = ROOT / "scripts/dev/generate_matrix_adapter_integrity.py"
    spec = importlib.util.spec_from_file_location(
        "generate_matrix_adapter_integrity", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("MATRIX_ADAPTER_INTEGRITY_GENERATOR_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_manifest()


def _read_regular(path: Path, failures: list[str]) -> str:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise OSError("unsafe file")
        return path.read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing or unsafe MSG-MX-005 artifact: {path.name}")
        return ""


def _lock_inventory(lock: dict[str, object]) -> set[tuple[str, str, str]]:
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        return set()
    inventory: set[tuple[str, str, str]] = set()
    for path, value in packages.items():
        if not isinstance(path, str) or not path.startswith("node_modules/"):
            continue
        if not isinstance(value, dict):
            return set()
        version = value.get("version")
        license_ref = value.get("license")
        integrity = value.get("integrity")
        if (
            not isinstance(version, str)
            or not isinstance(license_ref, str)
            or license_ref not in APPROVED_LICENSES
            or not isinstance(integrity, str)
            or not integrity.startswith("sha512-")
        ):
            return set()
        inventory.add((path.removeprefix("node_modules/"), version, license_ref))
    return inventory


def _helper_failures(source: str) -> list[str]:
    failures: list[str] = []
    for required in (
        'operation == "version"',
        "MATRIX_KEYCHAIN_CALLER_AUTH_REQUIRED",
        "credentialMaterialIncluded = false",
        "executionAuthorityGranted = false",
    ):
        if required not in source:
            failures.append(f"native helper missing fail-closed marker: {required}")
    for forbidden in (
        "import Security",
        "SecItem",
        "readItem(",
        "storeItem(",
        'adapter_with_credential"',
        'interactive_auth"',
        'store_rotate"',
    ):
        if forbidden in source:
            failures.append(
                f"native helper exposes blocked credential behavior: {forbidden}"
            )
    return failures


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    if root != ROOT:
        failures.append("MSG-MX-005 verifier supports the current repository root only")
        return failures

    if set(MATRIX_SESSION_LANES) != set(MatrixSessionOperation):
        failures.append("ten exact Matrix session authority lanes are not closed")
    entries = {
        item.lane_id: item
        for item in build_matrix_session_lane_catalog_entries(
            active_leases=[], kill_switch_engaged=False
        )
    }
    for operation, lane in MATRIX_SESSION_LANES.items():
        entry = entries.get(f"matrix.session.{operation.value}")
        if entry is None:
            failures.append(f"missing authority catalog entry: {operation.value}")
            continue
        expected = "blocked" if operation in BLOCKED_OPERATIONS else "implemented"
        if entry.status != expected:
            failures.append(f"runtime truth drifted for {operation.value}")
        if entry.side_effect_class != lane.side_effect_class:
            failures.append(f"side-effect truth drifted for {operation.value}")

    package_text = _read_regular(PACKAGE_PATH, failures)
    lock_text = _read_regular(LOCK_PATH, failures)
    notice = _read_regular(NOTICE_PATH, failures)
    integrity_text = _read_regular(INTEGRITY_PATH, failures)
    node_runtime_trust_text = _read_regular(
        NODE_RUNTIME_TRUST_PATH,
        failures,
    )
    helper_source = _read_regular(HELPER_SOURCE_PATH, failures)
    session_doc = _read_regular(SESSION_DOC_PATH, failures)
    if failures:
        return failures
    try:
        package = json.loads(package_text)
        lock = json.loads(lock_text)
        integrity = json.loads(integrity_text)
        node_runtime_trust = json.loads(node_runtime_trust_text)
    except json.JSONDecodeError:
        return ["MSG-MX-005 dependency metadata is invalid JSON"]
    if package.get("dependencies") != {"matrix-js-sdk": "41.9.0"}:
        failures.append("matrix-js-sdk is not the one exact stable 41.9.0 pin")
    if package.get("engines") != {"node": ">=22 <23"}:
        failures.append("Matrix adapter does not require the supported Node 22 major")
    packages = lock.get("packages", {})
    lock_root = packages.get("", {}) if isinstance(packages, dict) else {}
    if not isinstance(lock_root, dict) or lock_root.get("engines") != {
        "node": ">=22 <23"
    }:
        failures.append("Matrix adapter lock does not preserve the Node 22 policy")
    sdk = packages.get("node_modules/matrix-js-sdk", {})
    wasm = packages.get("node_modules/@matrix-org/matrix-sdk-crypto-wasm", {})
    if sdk.get("version") != "41.9.0" or wasm.get("version") != "18.3.1":
        failures.append("Matrix SDK or Rust/WASM dependency pin drifted")
    inventory = _lock_inventory(lock)
    if len(inventory) != 18:
        failures.append("Matrix adapter lock inventory is incomplete or unreviewed")
    for name, version, license_ref in inventory:
        row = f"| `{name}` | `{version}` | `{license_ref}` |"
        if row not in notice:
            failures.append(f"third-party notice missing locked dependency: {name}")
    try:
        expected_integrity = _build_integrity_manifest()
    except (OSError, RuntimeError, ValueError):
        failures.append("installed Matrix adapter runtime assets are missing or unsafe")
    else:
        if integrity != expected_integrity:
            failures.append("Matrix adapter runtime integrity manifest drifted")
    approved_runtime_bindings = node_runtime_trust.get("approved_runtime_bindings")
    if (
        node_runtime_trust.get("schema_version") != "uaa-matrix-node-runtime-trust.v1"
        or node_runtime_trust.get("raw_paths_included") is not False
        or node_runtime_trust.get("credential_material_included") is not False
        or not isinstance(approved_runtime_bindings, list)
        or len(approved_runtime_bindings) != 2
    ):
        failures.append("Matrix Node runtime trust anchor is incomplete")

    failures.extend(_helper_failures(helper_source))
    if "tools/macos/matrix-session-keychain-helper/.build/" not in (
        root / ".gitignore"
    ).read_text(encoding="utf-8"):
        failures.append("Swift helper build cache is not ignored")

    sdk_import = re.compile(r"(?:from|import)\s*[({]*\s*[\"']matrix-js-sdk")
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in {".js", ".mjs", ".ts", ".tsx"}
            or "node_modules" in path.parts
            or ".git" in path.parts
        ):
            continue
        source = path.read_text(encoding="utf-8")
        if sdk_import.search(source) and not path.is_relative_to(ADAPTER_ROOT / "src"):
            failures.append(f"Matrix SDK import escaped approved adapter: {path.name}")

    manifest = build_api_manifest(app)
    routes = {
        route.path: route
        for route in manifest.routes
        if route.path.startswith("/control-center/communications/matrix/")
    }
    if len(routes) != len(MatrixSessionOperation):
        failures.append(
            "API manifest does not expose exactly ten Matrix session routes"
        )
    schema = app.openapi()
    for operation, lane in MATRIX_SESSION_LANES.items():
        path = (
            f"/control-center/communications/matrix/{operation.value.replace('_', '-')}"
        )
        route = routes.get(path)
        if route is None:
            failures.append(f"missing Matrix session route: {path}")
            continue
        if (
            route.operation_id
            != f"post_control_center_communications_matrix_{operation.value}"
        ):
            failures.append(f"Matrix session operation ID drifted: {path}")
        if route.side_effect_class != lane.side_effect_class:
            failures.append(f"Matrix session side-effect class drifted: {path}")
        if route.idempotency_required is not lane.approval_required:
            failures.append(f"Matrix session idempotency posture drifted: {path}")
        if (
            not route.protected_route
            or route.rate_limit_group != "communications_matrix_session"
        ):
            failures.append(f"Matrix session route protection drifted: {path}")
        if schema["paths"][path]["post"]["operationId"] != route.operation_id:
            failures.append(f"Matrix session OpenAPI drifted: {path}")

    required_doc_markers = (
        "MSG-MX-005",
        "matrix-js-sdk` `41.9.0",
        "implemented: discovery",
        "implemented: authentication-method",
        "authenticated one-use handoff",
        "repository-reviewed node 22 runtime profile",
        "socket-owning SSO broker",
        "no sync, room read, message send, crypto, or media runtime",
    )
    lowered_doc = session_doc.lower()
    for marker in required_doc_markers:
        if marker.lower() not in lowered_doc:
            failures.append(
                f"Matrix session documentation missing truth marker: {marker}"
            )
    for relative in (
        "tests/test_msg_mx_005_matrix_session_authority.py",
        "tests/test_msg_mx_005_matrix_session_dispatch.py",
        "tests/test_msg_mx_005_matrix_discovery_observations.py",
        "tests/test_msg_mx_005_matrix_session_api_cli.py",
        "tests/test_msg_mx_005_matrix_session_helper.py",
        "tests/test_msg_mx_005_matrix_session_node_integration.py",
        "tests/test_matrix_node_runtime.py",
        "tests/test_msg_mx_005_adapter_runtime.py",
    ):
        if not (root / relative).is_file():
            failures.append(f"missing focused Matrix session proof: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-005 Matrix session verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-005 Matrix session verification PASSED")
    print(
        json.dumps(
            {
                "exact_lanes": 10,
                "implemented_read_lanes": 2,
                "blocked_mutation_lanes": 8,
                "desktop_only": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
