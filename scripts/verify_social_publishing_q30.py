#!/usr/bin/env python3
"""Verify the bounded Q30 proposal, dry-run, API/UI, and acceptance freeze."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ultimate_ai_agent.core.social_publishing.contracts import (
    ApprovalDecision,
    CompatibilitySeverity,
    ReconciliationObservation,
    SocialPublishingDryRunKernel,
    build_retry_plan,
    build_q30_fixture,
    build_q30_proposal_read_model,
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

    proposal = build_q30_proposal_read_model()
    if not (
        proposal.backend_owned
        and proposal.read_only
        and proposal.dry_run_only
        and not proposal.raw_content_included
        and not proposal.account_access_enabled
        and not proposal.credential_access_enabled
        and not proposal.network_access_enabled
        and not proposal.provider_sdk_enabled
        and not proposal.scheduler_enabled
        and not proposal.publishing_enabled
        and not proposal.external_write_enabled
        and not proposal.external_side_effect_performed
    ):
        failures.append("Q30 proposal read model authority posture drifted")

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

    concurrent_kernel = SocialPublishingDryRunKernel()
    success_scenario = build_scenario(fixture.plan, "success")
    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent_results = list(
            pool.map(
                lambda _: concurrent_kernel.execute(
                    plan=fixture.plan,
                    envelope=envelope,
                    scenario=success_scenario,
                ),
                range(8),
            )
        )
    if (
        len({item.result_ref for item in concurrent_results}) != 1
        or sum(item.replayed for item in concurrent_results) != 7
    ):
        failures.append("Q30 concurrent exact replay ownership drifted")

    from ultimate_ai_agent.api.app import app
    from ultimate_ai_agent.api.manifest import build_api_manifest

    route_path = "/control-center/social-publishing/proposal"
    openapi_path = app.openapi().get("paths", {}).get(route_path, {})
    if set(openapi_path) != {"get"}:
        failures.append("Q30 API route is missing or exposes a mutation method")
    manifest_routes = {
        (item.method, item.path): item for item in build_api_manifest(app).routes
    }
    route = manifest_routes.get(("GET", route_path))
    if route is None or (
        route.route_classification != "local_readonly"
        or route.side_effect_class != "validation_only"
    ):
        failures.append("Q30 API route classification drifted")

    repository_root = Path(__file__).resolve().parents[1]
    studio_source = (
        repository_root / "apps/control-center/src/northstar/StudioSurface.tsx"
    ).read_text(encoding="utf-8")
    for marker in (
        "Social publishing review",
        "No publish action",
        "Account not connected",
        "Dry-run review is CLI-gated",
    ):
        if marker not in studio_source:
            failures.append(f"Q30 readable Studio marker missing: {marker}")
    if "name: /^Publish$/" not in (
        repository_root
        / "apps/control-center/src/northstar/NorthStarControlCenter.test.tsx"
    ).read_text(encoding="utf-8"):
        failures.append("Q30 Studio no-Publish-control assertion is missing")

    acceptance_matrix = (
        repository_root / "docs/product/UAA_SOCIAL_PUBLISHING_Q30_ACCEPTANCE_MATRIX.md"
    )
    if not acceptance_matrix.is_file():
        failures.append("Q30 acceptance matrix is missing")
    else:
        matrix_text = acceptance_matrix.read_text(encoding="utf-8")
        for marker in (
            "Concurrent exact replay",
            "Unknown settlement",
            "GET-only API",
            "No live publishing authority",
        ):
            if marker not in matrix_text:
                failures.append(f"Q30 acceptance matrix marker missing: {marker}")
    return failures


def main() -> int:
    failures = verify()
    print(
        json.dumps(
            {
                "schema_version": "uaa-social-publishing-q30-verification.v1",
                "status": (
                    "Q30_VERIFIED_PROPOSAL_DRY_RUN_COMPLETE"
                    if not failures
                    else "Q30_VERIFICATION_FAILED"
                ),
                "failures": failures,
                "api_control_center_parity_complete": not failures,
                "acceptance_freeze_complete": not failures,
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
