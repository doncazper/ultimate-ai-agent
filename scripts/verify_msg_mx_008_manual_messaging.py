#!/usr/bin/env python3
"""Verify MSG-MX-008 exact manual-messaging authority and runtime truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_MESSAGING_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.communications.matrix_messaging import (
    MATRIX_MESSAGING_LANES,
    MatrixMessagingOperation,
    build_default_matrix_messaging_posture,
)
from ultimate_ai_agent.core.communications.matrix_messaging.static_safety import (
    MATRIX_MESSAGING_BROKER_REL,
    MATRIX_MESSAGING_NOTIFIER_REL,
    is_exact_matrix_messaging_broker_subprocess_site,
    is_exact_matrix_messaging_notifier_subprocess_site,
)


ROOT = Path(__file__).resolve().parents[1]
POSTURE_ROUTE = "/control-center/communications/matrix-messaging/posture"
PROPOSAL_ROUTE = "/control-center/communications/matrix-messaging/proposal"
OPERATION_PREFIX = "/control-center/communications/matrix-messaging/"
BROKER_ROOT = ROOT / "integrations/matrix-rust-broker"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_integrity_manifest(failures: list[str]) -> None:
    path = BROKER_ROOT / "runtime-integrity.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        failures.append("Matrix Rust broker integrity metadata is unavailable")
        return
    if (
        manifest.get("schema_version")
        != "uaa-matrix-rust-broker-integrity.v1"
        or manifest.get("rust_toolchain") != "1.93.0"
        or manifest.get("remote_targets_enabled") is not False
        or manifest.get("loopback_only") is not True
    ):
        failures.append("Matrix Rust broker integrity posture drifted")
    sdk = manifest.get("matrix_sdk")
    if not isinstance(sdk, dict) or (
        sdk.get("version") != "0.18.0"
        or sdk.get("source_commit")
        != "1c44fb66214667c6d00acaf72ab592493653708b"
    ):
        failures.append("pinned Matrix Rust SDK source identity drifted")
    if manifest.get("cargo_lock_sha256") != _sha256(BROKER_ROOT / "Cargo.lock"):
        failures.append("Matrix Rust broker Cargo.lock digest drifted")
    if manifest.get("cargo_manifest_sha256") != _sha256(
        BROKER_ROOT / "Cargo.toml"
    ):
        failures.append("Matrix Rust broker Cargo.toml digest drifted")
    sources = manifest.get("source_sha256")
    expected_sources = {
        path.name: _sha256(path)
        for path in sorted((BROKER_ROOT / "src").glob("*.rs"))
    }
    if sources != expected_sources:
        failures.append("Matrix Rust broker reviewed source digests drifted")


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-008 verifier supports the current repository root only"]
    failures: list[str] = []
    if set(MATRIX_MESSAGING_LANES) != set(MatrixMessagingOperation):
        failures.append("Matrix messaging operation-to-lane set is not closed")
    if len(MATRIX_MESSAGING_LANES) != 15:
        failures.append("fifteen exact Matrix messaging lanes are required")
    expected_bindings = {
        (lane.lane_ref, lane.capability_ref, lane.adapter_ref, lane.tool_ref)
        for lane in MATRIX_MESSAGING_LANES.values()
    }
    actual_bindings = {
        (lane_ref, capability_ref, adapter_ref, tool_ref)
        for (
            _domain,
            _capability,
            _scope,
            _mode,
            lane_ref,
            capability_ref,
            adapter_ref,
            tool_ref,
        ) in MATRIX_MESSAGING_EXACT_AUTHORITY_BINDINGS
    }
    if actual_bindings != expected_bindings:
        failures.append("generic AuthorityLease messaging allowlist drifted")
    if not all(lane.approval_required for lane in MATRIX_MESSAGING_LANES.values()):
        failures.append("every messaging lane must require exact fresh approval")

    posture = build_default_matrix_messaging_posture()
    if (
        posture.runtime_status != "configuration_required"
        or len(posture.authority_lane_refs) != 15
        or len(posture.live_executor_operation_refs) != 15
        or len(posture.blocked_operation_refs) != 15
        or posture.autonomous_send_enabled
        or posture.remote_homeservers_enabled
        or posture.approval_ref_is_authority
        or posture.raw_content_included
        or posture.element_interoperability_status != "external_facility_required"
        or not posture.request_scoped_evaluation_required
        or not posture.desktop_only
    ):
        failures.append("default Matrix messaging posture no longer fails closed")

    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if route.path.startswith(OPERATION_PREFIX)
    }
    if len(routes) != 17:
        failures.append("seventeen Matrix messaging API routes are required")
    posture_route = routes.get(POSTURE_ROUTE)
    proposal_route = routes.get(PROPOSAL_ROUTE)
    if posture_route is None or (
        posture_route.side_effect_class != "none"
        or posture_route.route_classification != "local_sensitive"
        or not posture_route.protected_route
    ):
        failures.append("Matrix messaging posture route contract drifted")
    if proposal_route is None or (
        proposal_route.side_effect_class != "validation_only"
        or proposal_route.route_classification != "local_sensitive"
        or not proposal_route.protected_route
    ):
        failures.append("Matrix messaging proposal route contract drifted")
    operation_paths = {
        f"{OPERATION_PREFIX}{operation.value.replace('_', '-')}"
        for operation in MatrixMessagingOperation
    }
    for path in operation_paths:
        route = routes.get(path)
        if route is None or (
            route.route_classification != "mutating_requires_authority"
            or not route.idempotency_required
            or not route.protected_route
        ):
            failures.append(f"exact Matrix messaging operation route drifted: {path}")

    broker_source = (ROOT / MATRIX_MESSAGING_BROKER_REL).read_text()
    notifier_source = (ROOT / MATRIX_MESSAGING_NOTIFIER_REL).read_text()
    if not is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=MATRIX_MESSAGING_BROKER_REL,
        source=broker_source,
        fragment="subprocess.Popen(",
    ):
        failures.append("reviewed Matrix Rust broker process profile drifted")
    if not is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=MATRIX_MESSAGING_NOTIFIER_REL,
        source=notifier_source,
        fragment="subprocess.run(",
    ):
        failures.append("reviewed Matrix notification process profile drifted")
    _verify_integrity_manifest(failures)

    required = (
        "docs/connectors/MESSENGER_MATRIX_MANUAL_MESSAGING.md",
        "integrations/matrix-rust-broker/Cargo.lock",
        "integrations/matrix-rust-broker/runtime-integrity.json",
        "src/ultimate_ai_agent/core/communications/matrix_messaging/adapter.py",
        "src/ultimate_ai_agent/core/communications/matrix_messaging/broker.py",
        "src/ultimate_ai_agent/core/communications/matrix_messaging/outbox.py",
        "src/ultimate_ai_agent/core/communications/matrix_messaging/service.py",
        "tests/test_msg_mx_008_matrix_messaging_contracts.py",
        "tests/test_msg_mx_008_matrix_messaging_api_cli.py",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-008 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-008 manual messaging verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-008 manual messaging verification PASSED")
    print(
        json.dumps(
            {
                "accepted_exact_authority_lanes": 15,
                "implemented_executor_operations": 15,
                "default_blocked_operations": 15,
                "runtime": "configuration_required",
                "remote_homeservers": False,
                "autonomous_send": False,
                "element_interoperability": "external_facility_required",
                "desktop_only": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
