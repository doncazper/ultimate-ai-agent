#!/usr/bin/env python3
"""Verify the bounded Q30 P0-P4 proposal and dry-run implementation."""

from __future__ import annotations

import json

from ultimate_ai_agent.core.social_publishing.contracts import (
    ApprovalDecision,
    CompatibilitySeverity,
    ReconciliationObservation,
    SocialPublishingDryRunKernel,
    build_retry_plan,
    build_q30_fixture,
    build_review_envelope,
    build_scenario,
    reconcile_unknown_settlement,
)


def verify() -> list[str]:
    failures: list[str] = []
    fixture = build_q30_fixture()
    if [item.platform.value for item in fixture.capabilities] != [
        "instagram",
        "x",
        "tiktok",
    ]:
        failures.append("Q30 platform fixture inventory drifted")
    if any(
        finding.severity
        in {CompatibilitySeverity.blocking, CompatibilitySeverity.unknown}
        for finding in fixture.findings
    ):
        failures.append("Q30 checked-in fixture contains an unresolved finding")
    if any(
        (
            capability.live_account_configured
            or capability.provider_sdk_enabled
            or capability.network_access_enabled
            or capability.publishing_enabled
        )
        for capability in fixture.capabilities
    ):
        failures.append("Q30 capability fixture grants live authority")
    if (
        fixture.live_account_access_enabled
        or fixture.network_access_enabled
        or fixture.background_scheduler_enabled
        or fixture.publishing_enabled
        or fixture.plan.publishing_enabled
        or fixture.plan.external_write_enabled
    ):
        failures.append("Q30 fixture grants prohibited authority")

    envelope = build_review_envelope(
        fixture.plan, ApprovalDecision.approved_for_dry_run
    )
    mixed = SocialPublishingDryRunKernel().execute(
        plan=fixture.plan,
        envelope=envelope,
        scenario=build_scenario(fixture.plan, "mixed"),
    )
    if set(mixed.succeeded_target_refs) & set(mixed.retry_eligible_target_refs):
        failures.append("Q30 successful target became retry eligible")
    if mixed.retry_eligible_target_refs:
        retry = build_retry_plan(
            mixed, target_refs=(mixed.retry_eligible_target_refs[0],)
        )
        if not retry.new_approval_required:
            failures.append("Q30 retry plan bypasses new exact review")

    unknown = SocialPublishingDryRunKernel().execute(
        plan=fixture.plan,
        envelope=envelope,
        scenario=build_scenario(fixture.plan, "unknown"),
    )
    if not unknown.reconciliation_required_target_refs:
        failures.append("Q30 unknown outcome does not require reconciliation")
    else:
        target_ref = unknown.reconciliation_required_target_refs[0]
        result = reconcile_unknown_settlement(
            unknown,
            target_ref=target_ref,
            observation=ReconciliationObservation.still_unknown,
        )
        if result.retry_eligible:
            failures.append("Q30 unresolved unknown outcome became retry eligible")
    if any(
        item.external_side_effect_performed
        for item in (*mixed.receipts, *unknown.receipts)
    ):
        failures.append("Q30 dry-run receipt claims an external side effect")
    return failures


def main() -> int:
    failures = verify()
    print(
        json.dumps(
            {
                "schema_version": "uaa-social-publishing-q30-verification.v1",
                "status": (
                    "Q30_P0_P4_VERIFIED_P5_P6_PENDING"
                    if not failures
                    else "Q30_P0_P4_VERIFICATION_FAILED"
                ),
                "failures": failures,
                "api_control_center_parity_complete": False,
                "acceptance_freeze_complete": False,
                "publishing_enabled": False,
                "external_side_effect_performed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
