#!/usr/bin/env python3
"""Verify the MSG-MX-007 exact crypto authority and fail-closed runtime truth."""

from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_CRYPTO_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.communications import build_default_communications_service
from ultimate_ai_agent.core.communications.matrix_crypto import (
    MATRIX_CRYPTO_LANES,
    MatrixCryptoOperation,
    build_default_matrix_crypto_posture,
)


ROOT = Path(__file__).resolve().parents[1]
POSTURE_ROUTE = "/control-center/communications/matrix-crypto/posture"
PROPOSAL_ROUTE = "/control-center/communications/matrix-crypto/proposal"


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-007 verifier supports the current repository root only"]
    failures: list[str] = []
    if set(MATRIX_CRYPTO_LANES) != set(MatrixCryptoOperation):
        failures.append("Matrix crypto operation-to-lane set is not closed")
    if len(MATRIX_CRYPTO_LANES) != 17:
        failures.append("seventeen exact Matrix crypto lanes are required")
    expected_bindings = {
        (lane.lane_ref, lane.capability_ref, lane.adapter_ref, lane.tool_ref)
        for lane in MATRIX_CRYPTO_LANES.values()
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
        ) in MATRIX_CRYPTO_EXACT_AUTHORITY_BINDINGS
    }
    if actual_bindings != expected_bindings:
        failures.append("generic AuthorityLease crypto allowlist drifted")

    posture = build_default_matrix_crypto_posture()
    if (
        posture.runtime_status.value != "adapter_required"
        or posture.freshness.value != "unknown"
        or len(posture.authority_lane_refs) != 17
        or len(posture.accepted_authority_operation_refs) != 17
        or posture.live_executor_operation_refs
        or len(posture.blocked_operation_refs) != 17
        or posture.recovery_material_included
        or posture.raw_crypto_payload_included
        or posture.element_interoperability_status != "external_facility_required"
        or not posture.request_scoped_evaluation_required
        or not posture.single_owner_required
        or not posture.desktop_only
    ):
        failures.append("default Matrix crypto posture no longer fails closed")

    security = build_default_communications_service().inspect_security_posture()
    if (
        security.crypto_runtime_status.value != "adapter_required"
        or security.crypto_live_executor_refs
        or len(security.crypto_authority_lane_refs) != 17
        or len(security.crypto_blocked_operation_refs) != 17
        or security.recovery_material_included
        or security.raw_crypto_payload_included
        or not security.request_scoped_evaluation_required
    ):
        failures.append("communications security posture diverged from crypto truth")

    routes = {route.path: route for route in build_api_manifest(app).routes}
    posture_route = routes.get(POSTURE_ROUTE)
    proposal_route = routes.get(PROPOSAL_ROUTE)
    if posture_route is None or (
        posture_route.operation_id
        != "get_control_center_communications_matrix_crypto_posture"
        or posture_route.side_effect_class != "none"
        or posture_route.route_classification != "local_sensitive"
        or not posture_route.protected_route
    ):
        failures.append("Matrix crypto posture route contract drifted")
    if proposal_route is None or (
        proposal_route.operation_id
        != "post_control_center_communications_matrix_crypto_proposal"
        or proposal_route.side_effect_class != "validation_only"
        or proposal_route.route_classification != "local_sensitive"
        or not proposal_route.protected_route
        or not proposal_route.rate_limit_targeted
    ):
        failures.append("Matrix crypto proposal route contract drifted")

    required = (
        "docs/connectors/MESSENGER_MATRIX_CRYPTO_RECOVERY.md",
        "src/ultimate_ai_agent/core/communications/matrix_crypto/authority.py",
        "src/ultimate_ai_agent/core/communications/matrix_crypto/contracts.py",
        "src/ultimate_ai_agent/core/communications/matrix_crypto/availability.py",
        "tests/test_msg_mx_007_matrix_crypto_authority.py",
        "tests/test_msg_mx_007_matrix_crypto_api_cli.py",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-007 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-007 Matrix crypto verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-007 Matrix crypto verification PASSED")
    print(
        json.dumps(
            {
                "accepted_exact_authority_lanes": 17,
                "live_executors": 0,
                "blocked_operations": 17,
                "persistent_runtime": "adapter_required",
                "recovery_material_included": False,
                "element_interoperability": "external_facility_required",
                "desktop_only": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
