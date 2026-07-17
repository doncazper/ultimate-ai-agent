#!/usr/bin/env python3
"""Verify MSG-MX-010 governed Matrix intelligence and proposal truth."""

from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_INTELLIGENCE_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.communications.matrix_intelligence import (
    MATRIX_INTELLIGENCE_LANES,
    MatrixIntelligenceFamily,
    MatrixIntelligenceOperation,
    build_default_matrix_intelligence_posture,
)


ROOT = Path(__file__).resolve().parents[1]
OPERATION_PREFIX = "/control-center/communications/matrix-intelligence/"
POSTURE_ROUTE = OPERATION_PREFIX + "posture"
PROPOSAL_ROUTE = OPERATION_PREFIX + "proposal"


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-010 verifier supports the current repository root only"]
    failures: list[str] = []

    if set(MATRIX_INTELLIGENCE_LANES) != set(MatrixIntelligenceOperation):
        failures.append("Matrix intelligence operation-to-lane set is not closed")
    if len(MATRIX_INTELLIGENCE_LANES) != 6:
        failures.append("six exact Matrix intelligence lanes are required")
    expected_bindings = {
        (
            lane.authority_domain.value,
            lane.authority_capability.value,
            "session",
            lane.required_mode.value,
            lane.lane_ref,
            lane.capability_ref,
            lane.adapter_ref,
            lane.tool_ref,
        )
        for lane in MATRIX_INTELLIGENCE_LANES.values()
    }
    if set(MATRIX_INTELLIGENCE_EXACT_AUTHORITY_BINDINGS) != expected_bindings:
        failures.append("generic AuthorityLease intelligence allowlist drifted")
    for blocked in (
        "provider_invoke",
        "attachment_materialize",
        "attachment_scan",
        "attachment_analyze",
        "attachment_cleanup",
    ):
        if blocked in {item.value for item in MatrixIntelligenceOperation}:
            failures.append(f"blocked family unexpectedly gained runtime: {blocked}")

    posture = build_default_matrix_intelligence_posture()
    family_postures = {item.family: item for item in posture.family_postures}
    accepted = {
        MatrixIntelligenceFamily.context_materialization,
        MatrixIntelligenceFamily.proposal_persistence,
    }
    if (
        posture.runtime_status != "partial_exact_local_lanes"
        or {
            family
            for family, item in family_postures.items()
            if item.status == "accepted_request_scoped"
        }
        != accepted
        or posture.provider_invocation_enabled
        or posture.attachment_analysis_enabled
        or posture.autonomous_send_enabled
        or posture.automatic_memory_write_enabled
        or posture.context_injection_enabled
        or posture.raw_content_persisted
        or not posture.request_scoped_evaluation_required
    ):
        failures.append("default Matrix intelligence posture no longer fails closed")

    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if route.path.startswith(OPERATION_PREFIX)
    }
    if len(routes) != 8:
        failures.append("eight Matrix intelligence API routes are required")
    posture_route = routes.get(POSTURE_ROUTE)
    proposal_route = routes.get(PROPOSAL_ROUTE)
    if posture_route is None or (
        posture_route.side_effect_class != "none"
        or posture_route.route_classification != "local_sensitive"
        or not posture_route.protected_route
    ):
        failures.append("Matrix intelligence posture route contract drifted")
    if proposal_route is None or (
        proposal_route.side_effect_class != "validation_only"
        or proposal_route.route_classification != "local_sensitive"
        or not proposal_route.protected_route
    ):
        failures.append("Matrix intelligence proposal route contract drifted")
    for operation, lane in MATRIX_INTELLIGENCE_LANES.items():
        path = OPERATION_PREFIX + operation.value.replace("_", "-")
        route = routes.get(path)
        if route is None or (
            route.side_effect_class != lane.side_effect_class
            or route.route_classification != "mutating_requires_authority"
            or not route.idempotency_required
            or not route.protected_route
            or route.rate_limit_group != "communications_matrix_intelligence"
        ):
            failures.append(f"exact Matrix intelligence route drifted: {path}")
    if any("provider" in path or "attachment" in path for path in routes):
        failures.append("blocked intelligence family gained an API runtime route")

    doc = ROOT / "docs/connectors/MESSENGER_MATRIX_INTELLIGENCE_PROPOSALS.md"
    try:
        doc_text = doc.read_text(encoding="utf-8")
    except OSError:
        failures.append("MSG-MX-010 canonical documentation is unavailable")
        doc_text = ""
    for marker in (
        "Six separately evaluated operations",
        "Provider invocation remains blocked",
        "attachment analysis remains blocked",
        "All message content is untrusted data",
        "proposal_only",
        "content-unit estimate",
    ):
        if marker not in doc_text:
            failures.append(f"MSG-MX-010 documentation marker missing: {marker}")
    for relative in (
        "src/ultimate_ai_agent/core/communications/matrix_intelligence/contracts.py",
        "src/ultimate_ai_agent/core/communications/matrix_intelligence/store.py",
        "src/ultimate_ai_agent/core/communications/matrix_intelligence/service.py",
        "tests/test_msg_mx_010_intelligence_contracts.py",
        "tests/test_msg_mx_010_intelligence_api_cli.py",
    ):
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-010 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-010 intelligence/proposals verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-010 intelligence/proposals verification PASSED")
    print(
        json.dumps(
            {
                "accepted_exact_authority_lanes": 6,
                "accepted_stage_b_families": 2,
                "blocked_stage_b_families": 2,
                "provider_invocation": False,
                "attachment_analysis": False,
                "autonomous_send": False,
                "automatic_memory_write": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
