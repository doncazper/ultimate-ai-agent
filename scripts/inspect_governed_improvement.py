#!/usr/bin/env python3
"""Inspect Q29 governed-improvement contracts using synthetic safe refs."""

from __future__ import annotations

import argparse
import json

from ultimate_ai_agent.core.ecosystem.improvements import (
    ImprovementDecision,
    ImprovementEvidenceKind,
    ImprovementEvidenceSource,
    ImprovementProposalRequest,
    ImprovementReviewRequest,
    ImprovementRightsPosture,
    ImprovementSession,
    ImprovementTargetKind,
    build_improvement_proposal,
    build_improvement_status,
)


def _request(*, rights_ready: bool, safe_disabled: bool) -> ImprovementProposalRequest:
    rights = (
        ImprovementRightsPosture.permitted
        if rights_ready
        else ImprovementRightsPosture.unknown
    )
    return ImprovementProposalRequest(
        workspace_ref="workspace-ref:q29:synthetic",
        target_kind=ImprovementTargetKind.evaluation_case,
        target_ref="evaluation-case-ref:q29:synthetic",
        target_revision_ref="revision-ref:q29:target:1",
        source_evidence=(
            ImprovementEvidenceSource(
                source_kind=ImprovementEvidenceKind.evaluation_gap,
                source_receipt_ref="evaluation-receipt-ref:q29:synthetic",
                source_revision_ref="revision-ref:q29:source:1",
                provenance_ref="provenance-ref:q29:synthetic",
                rights_posture=rights,
                rights_evidence_ref=(
                    "rights-evidence-ref:q29:synthetic" if rights_ready else None
                ),
                evidence_refs=("evidence-ref:q29:synthetic-gap",),
            ),
        ),
        intended_delta_refs=("delta-ref:q29:synthetic",),
        expected_regression_refs=("regression-ref:q29:synthetic",),
        rollback_plan_ref="rollback-plan-ref:q29:synthetic",
        safe_disabled=safe_disabled,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect proposal-only Q29 governed improvement truth."
    )
    parser.add_argument(
        "mode", choices=("status", "proposal", "review"), nargs="?", default="status"
    )
    parser.add_argument("--rights-unresolved", action="store_true")
    parser.add_argument("--safe-disabled", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    request = _request(
        rights_ready=not args.rights_unresolved,
        safe_disabled=args.safe_disabled,
    )
    if args.mode == "status":
        payload = build_improvement_status()
    elif args.mode == "proposal":
        payload = build_improvement_proposal(request).model_dump(mode="json")
    else:
        proposal = build_improvement_proposal(request)
        receipt = ImprovementSession().review(
            ImprovementReviewRequest(
                proposal=request,
                proposal_ref=proposal.proposal_ref,
                proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
                decision=ImprovementDecision.accept,
                reviewer_ref="reviewer-ref:q29:synthetic",
                independent_review_ref="review-evidence-ref:q29:synthetic",
                idempotency_ref="idempotency-ref:q29:synthetic",
            )
        )
        payload = receipt.model_dump(mode="json")

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"Governed improvement: {payload.get('status', payload.get('state', payload.get('outcome')))}"
        )
        print(f"Target mutated: {payload.get('target_mutated', False)}")
        print(f"Automatic training: {payload.get('automatic_training_enabled', False)}")
        print(f"Automatic merge: {payload.get('automatic_merge_enabled', False)}")
        if "next_safe_action" in payload:
            print(f"Next: {payload['next_safe_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
