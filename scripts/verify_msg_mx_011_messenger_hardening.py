#!/usr/bin/env python3
"""Verify MSG-MX-011 Messenger reliability and security hardening truth."""

from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_hardening import (
    MatrixHardeningCheckCategory,
    MatrixHardeningCheckStatus,
    build_default_matrix_hardening_posture,
)
from ultimate_ai_agent.core.communications.matrix_messaging.constants import (
    MATRIX_MESSAGING_MAX_OUTBOX_RECORDS,
)
from ultimate_ai_agent.core.communications.matrix_sync.constants import (
    MATRIX_SYNC_MAX_BYTES,
    MATRIX_SYNC_MAX_CACHE_BYTES,
    MATRIX_SYNC_MAX_CACHE_EVENTS,
    MATRIX_SYNC_MAX_EVENTS,
    MATRIX_SYNC_MAX_RELATION_DEPTH,
    MATRIX_SYNC_MAX_ROOM_EVENT_REFS,
    MATRIX_SYNC_MAX_ROOMS,
)


ROOT = Path(__file__).resolve().parents[1]
POSTURE_ROUTE = "/control-center/communications/matrix-hardening/posture"


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing or unreadable MSG-MX-011 artifact: {relative}")
        return ""


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-011 verifier supports the current repository root only"]
    failures: list[str] = []

    posture = build_default_matrix_hardening_posture()
    checks = {check.category: check for check in posture.checks}
    statuses = {category: check.status for category, check in checks.items()}
    expected_passed = {
        MatrixHardeningCheckCategory.large_room_backpressure,
        MatrixHardeningCheckCategory.cache_queue_bounds,
        MatrixHardeningCheckCategory.rate_limit_malicious_events,
        MatrixHardeningCheckCategory.retention_deletion_low_disk,
        MatrixHardeningCheckCategory.restart_offline_recovery,
        MatrixHardeningCheckCategory.accessibility_keyboard_focus,
        MatrixHardeningCheckCategory.telemetry_redaction,
        MatrixHardeningCheckCategory.dependency_sbom,
        MatrixHardeningCheckCategory.rollback_safe_disable,
    }
    if (
        posture.runtime_status != "partial_hardening_evidence"
        or set(checks) != set(MatrixHardeningCheckCategory)
        or {category for category, status in statuses.items() if status == "passed"}
        != expected_passed
        or statuses.get(MatrixHardeningCheckCategory.migration_multi_device)
        != MatrixHardeningCheckStatus.blocked
        or statuses.get(MatrixHardeningCheckCategory.localization_readiness)
        != MatrixHardeningCheckStatus.partial
        or statuses.get(MatrixHardeningCheckCategory.element_interoperability)
        != MatrixHardeningCheckStatus.external_facility_required
        or posture.new_runtime_authority_granted
        or posture.calls_enabled
        or posture.agent_participants_enabled
        or posture.hosted_infrastructure_enabled
        or posture.public_federation_enabled
        or posture.production_deployment_enabled
        or posture.raw_content_included
        or posture.local_paths_included
        or not posture.desktop_only
        or not posture.request_scoped_runtime_evaluation_required
    ):
        failures.append("default Matrix hardening posture no longer fails closed")

    expected_budgets = {
        "budget-ref:matrix-hardening:sync-response-bytes": MATRIX_SYNC_MAX_BYTES,
        "budget-ref:matrix-hardening:sync-batch-events": MATRIX_SYNC_MAX_EVENTS,
        "budget-ref:matrix-hardening:sync-rooms": MATRIX_SYNC_MAX_ROOMS,
        "budget-ref:matrix-hardening:cache-ciphertext-bytes": MATRIX_SYNC_MAX_CACHE_BYTES,
        "budget-ref:matrix-hardening:cache-retained-events": MATRIX_SYNC_MAX_CACHE_EVENTS,
        "budget-ref:matrix-hardening:room-event-refs": MATRIX_SYNC_MAX_ROOM_EVENT_REFS,
        "budget-ref:matrix-hardening:relation-depth": MATRIX_SYNC_MAX_RELATION_DEPTH,
        "budget-ref:matrix-hardening:outbox-records": MATRIX_MESSAGING_MAX_OUTBOX_RECORDS,
    }
    if {budget.budget_ref: budget.limit for budget in posture.budgets} != expected_budgets:
        failures.append("Matrix hardening resource budgets drifted")

    route = next(
        (
            item
            for item in build_api_manifest(app).routes
            if item.path == POSTURE_ROUTE and item.method == "GET"
        ),
        None,
    )
    if route is None or (
        route.side_effect_class != "none"
        or route.route_classification != "local_sensitive"
        or not route.protected_route
        or route.idempotency_required
    ):
        failures.append("Matrix hardening posture route contract drifted")

    doc_text = _read("docs/connectors/MESSENGER_MATRIX_HARDENING.md", failures)
    for marker in (
        "grants no new runtime authority",
        "5,000 events",
        "256 records",
        "external_facility_required",
        "Calls, agent room participants",
        POSTURE_ROUTE,
        "matrix-hardening-status",
    ):
        if marker not in doc_text:
            failures.append(f"MSG-MX-011 documentation marker missing: {marker}")

    cli_text = _read("scripts/dev/uaa_communications.py", failures)
    frontend_text = _read(
        "apps/control-center/src/components/messenger/MessengerShell.tsx", failures
    )
    endpoints_text = _read("apps/control-center/src/api/endpoints.ts", failures)
    for marker, text, label in (
        ("matrix-hardening-status", cli_text, "CLI"),
        ("build_default_matrix_hardening_posture", cli_text, "CLI parity"),
        ("communicationsMatrixHardeningPosture", endpoints_text, "frontend endpoint"),
        ("hardening-posture", frontend_text, "desktop hardening projection"),
        ("element_interoperability_status", frontend_text, "desktop external truth"),
    ):
        if marker not in text:
            failures.append(f"MSG-MX-011 {label} marker missing: {marker}")

    for relative in (
        "src/ultimate_ai_agent/core/communications/matrix_hardening/contracts.py",
        "src/ultimate_ai_agent/core/communications/matrix_hardening/posture.py",
        "tests/test_msg_mx_011_messenger_hardening.py",
    ):
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-011 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-011 Messenger hardening verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-011 Messenger hardening verification PASSED")
    print(
        json.dumps(
            {
                "hardening_categories": 12,
                "passed_categories": 9,
                "bounded_budgets": 8,
                "new_runtime_authority": False,
                "element_interoperability": "external_facility_required",
                "runtime": "partial_hardening_evidence",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
