#!/usr/bin/env python3
"""Inspect and exercise the fixture-only Q30 social publishing dry-run."""

from __future__ import annotations

import argparse
import json

from ultimate_ai_agent.core.social_publishing.contracts import (
    ApprovalDecision,
    ReconciliationObservation,
    SocialPublishingDryRunKernel,
    build_q30_fixture,
    build_review_envelope,
    build_scenario,
    reconcile_unknown_settlement,
)


def _dump(value: object) -> None:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Q30 fixture-only social publishing proposal and dry-run CLI."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="Inspect the content-free fixture bundle.")
    subparsers.add_parser("validate", help="Validate the exact fixture contracts.")
    dry_run = subparsers.add_parser("dry-run", help="Simulate target settlements.")
    dry_run.add_argument(
        "--scenario", choices=("success", "mixed", "unknown"), default="mixed"
    )
    dry_run.add_argument("--decision", choices=("approve", "reject"), default="approve")
    reconcile = subparsers.add_parser(
        "reconcile", help="Simulate reconciliation for an unknown outcome."
    )
    reconcile.add_argument(
        "--observation",
        choices=("matched", "unmatched", "still-unknown"),
        default="still-unknown",
    )
    args = parser.parse_args()

    fixture = build_q30_fixture()
    if args.command == "inspect":
        _dump(fixture)
        return 0
    if args.command == "validate":
        _dump(
            {
                "schema_version": "uaa-social-publishing-q30-verification.v1",
                "status": "FIXTURE_DRY_RUN_CONTRACT_VALID",
                "fixture_ref": fixture.fixture_ref,
                "platform_count": len(fixture.capabilities),
                "publishing_enabled": False,
                "external_side_effect_performed": False,
            }
        )
        return 0

    decision = (
        ApprovalDecision.approved_for_dry_run
        if getattr(args, "decision", "approve") == "approve"
        else ApprovalDecision.rejected
    )
    envelope = build_review_envelope(fixture.plan, decision)
    if decision is ApprovalDecision.rejected:
        _dump(
            {
                "status": "DRY_RUN_REJECTED_BY_OPERATOR",
                "envelope_ref": envelope.envelope_ref,
                "publishing_enabled": False,
                "external_side_effect_performed": False,
            }
        )
        return 0
    kernel = SocialPublishingDryRunKernel()
    scenario_name = getattr(args, "scenario", "unknown")
    result = kernel.execute(
        plan=fixture.plan,
        envelope=envelope,
        scenario=build_scenario(fixture.plan, scenario_name),
    )
    if args.command == "dry-run":
        _dump(result)
        return 0
    target_ref = result.reconciliation_required_target_refs[0]
    observation = ReconciliationObservation(args.observation.replace("-", "_"))
    _dump(
        reconcile_unknown_settlement(
            result, target_ref=target_ref, observation=observation
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
