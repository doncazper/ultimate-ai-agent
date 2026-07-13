from __future__ import annotations

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
    _mapping,
)


def build_memory_lane_authority_mappings():
    return [
        _mapping(
            "lane-ref:memory-review-accept-correct",
            "Reviewed memory write",
            AuthorityDomain.memory,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_ask_required",
            [
                "POST /control-center/memory/review/{candidate_ref}/accept",
                "POST /control-center/memory/review/{candidate_ref}/correct",
            ],
            ["repo-local-command:inspect-memory-review"],
            (
                "Requires Memory domain write authority; Ask before changes "
                "returns ask until an operator confirms."
            ),
        ),
        _mapping(
            "lane-ref:memory-review-lifecycle-suppression",
            "Reviewed memory lifecycle suppression",
            AuthorityDomain.memory,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required_when_recall_state_changes",
            [
                "POST /control-center/memory/review/{candidate_ref}/reject",
                "POST /control-center/memory/review/{candidate_ref}/merge",
                "POST /control-center/memory/review/{candidate_ref}/supersede",
                "POST /control-center/memory/review/{candidate_ref}/expire",
                "POST /control-center/memory/review/{candidate_ref}/forget-request",
            ],
            ["scripts/dev/uaa_founder_loop.py record-memory-decision"],
            (
                "Requires exact Memory write approval and AuthorityLease scope "
                "when a lifecycle receipt suppresses existing recall records; "
                "receipt-only decisions without recall state changes mint no authority."
            ),
        ),
        _mapping(
            "lane-ref:memory-feedback-metadata-update",
            "Reviewed recall feedback metadata update",
            AuthorityDomain.memory,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required",
            ["POST /control-center/memory/feedback"],
            ["scripts/dev/uaa_founder_loop.py record-memory-feedback"],
            (
                "Requires exact Memory write approval and AuthorityLease scope; "
                "feedback may update only reviewed recall trust, stale, and conflict "
                "metadata through an append-first operation."
            ),
        ),
    ]


__all__ = ["build_memory_lane_authority_mappings"]
