#!/usr/bin/env python3
"""Inspect Q28 autocorrect controls with bounded synthetic safe refs only."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ultimate_ai_agent.core.ecosystem.changesets import FieldChangeKind, FieldDiff
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId, EntityKind
from ultimate_ai_agent.core.ecosystem.corrections import (
    CorrectionDecision,
    CorrectionProposalRequest,
    CorrectionReviewRequest,
    CorrectionReviewSession,
    build_autocorrect_control_status,
    build_correction_proposal,
)


def _synthetic_request(
    *, stale: bool, low_confidence: bool, safe_disabled: bool
) -> CorrectionProposalRequest:
    return CorrectionProposalRequest(
        workspace_ref="workspace-ref:q28:synthetic",
        source_proposal_ref="proposal-ref:q27:synthetic-task",
        target_kind=EntityKind.task,
        target_owner=CanonicalOwnerId.tasks,
        target_ref="task-ref:q28:synthetic",
        expected_revision_ref="revision-ref:q28:task:7",
        current_revision_ref=(
            "revision-ref:q28:task:8" if stale else "revision-ref:q28:task:7"
        ),
        confidence_percent=45 if low_confidence else 88,
        field_diffs=(
            FieldDiff(
                operation_ref="operation-ref:q28:correct-title",
                target_ref="task-ref:q28:synthetic",
                field_ref="field-ref:title",
                change_kind=FieldChangeKind.updated,
                before_fingerprint_ref="fingerprint-ref:q28:title:before",
                after_fingerprint_ref="fingerprint-ref:q28:title:after",
            ),
        ),
        evidence_refs=("evidence-ref:q28:synthetic-source",),
        reason_refs=("reason-ref:q28:operator-correction",),
        rejection_history_refs=("learning-ref:q28:prior-rejection",),
        safe_disabled=safe_disabled,
    )


def _review(
    request: CorrectionProposalRequest,
    *,
    decision: CorrectionDecision,
) -> dict[str, Any]:
    proposal = build_correction_proposal(request)
    session = CorrectionReviewSession()
    review_request = CorrectionReviewRequest(
        proposal=request,
        proposal_ref=proposal.proposal_ref,
        proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
        decision=decision,
        reviewer_ref="reviewer-ref:q28:local-operator",
        idempotency_ref="idempotency-ref:q28:synthetic-review",
        superseding_proposal_ref=(
            "correction-proposal-ref:q28:replacement"
            if decision == CorrectionDecision.supersede
            else None
        ),
    )
    first = session.review(review_request)
    replay = session.review(review_request)
    return {
        "review": first.model_dump(mode="json"),
        "idempotent_replay": replay.model_dump(mode="json"),
    }


def _render_text(mode: str, payload: dict[str, Any]) -> str:
    if mode == "status":
        return "\n".join(
            (
                "Autocorrect controls: proposal-only",
                f"Supported targets: {', '.join(payload['supported_target_kinds'])}",
                f"Minimum confidence: {payload['minimum_review_confidence']}%",
                f"Canonical mutation enabled: {payload['canonical_mutation_enabled']}",
                f"ChangeSet creation enabled: {payload['changeset_creation_enabled']}",
                f"Rollback execution enabled: {payload['rollback_execution_enabled']}",
                f"Next: {payload['next_safe_action']}",
            )
        )
    if mode == "proposal":
        comparison = payload["comparison"]
        return "\n".join(
            (
                "Autocorrect proposal preview",
                f"State: {payload['state']}",
                f"Confidence: {payload['confidence']} ({payload['confidence_percent']}%)",
                f"Target: {payload['target_ref']}",
                f"Exact revision match: {comparison['exact_revision_match']}",
                f"Changed fields: {comparison['changed_field_count']}",
                f"Raw values included: {comparison['raw_values_included']}",
                f"Rollback ready: {payload['rollback']['rollback_ready']}",
                f"Canonical state mutated: {payload['canonical_state_mutated']}",
                f"Next: {payload['next_safe_action']}",
            )
        )
    review = payload["review"]
    replay = payload["idempotent_replay"]
    return "\n".join(
        (
            "Autocorrect review preview",
            f"Decision: {review['decision']}",
            f"Outcome: {review['outcome']}",
            f"Receipt: {review['receipt_ref']}",
            f"Replay stable: {replay['receipt_ref'] == review['receipt_ref']}",
            f"Replay marked: {replay['replayed']}",
            f"Canonical state mutated: {review['canonical_state_mutated']}",
            f"ChangeSet created: {review['changeset_created']}",
            f"Next: {review['next_safe_action']}",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect proposal-only Q28 autocorrect controls."
    )
    parser.add_argument(
        "mode", choices=("status", "proposal", "review"), nargs="?", default="status"
    )
    parser.add_argument(
        "--decision",
        choices=tuple(item.value for item in CorrectionDecision),
        default=CorrectionDecision.accept.value,
    )
    parser.add_argument("--stale", action="store_true")
    parser.add_argument("--low-confidence", action="store_true")
    parser.add_argument("--safe-disabled", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    request = _synthetic_request(
        stale=args.stale,
        low_confidence=args.low_confidence,
        safe_disabled=args.safe_disabled,
    )
    if args.mode == "status":
        payload = build_autocorrect_control_status().model_dump(mode="json")
    elif args.mode == "proposal":
        payload = build_correction_proposal(request).model_dump(mode="json")
    else:
        payload = _review(request, decision=CorrectionDecision(args.decision))

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(args.mode, payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
