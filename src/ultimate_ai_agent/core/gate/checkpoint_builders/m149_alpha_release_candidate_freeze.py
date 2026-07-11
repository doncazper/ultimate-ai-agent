from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS,
    AlphaReleaseCandidateFreezeRequest,
)


def _request(**overrides: Any) -> AlphaReleaseCandidateFreezeRequest:
    data = {
        "request_ref": "alpha-release-candidate-freeze-request:m149",
        "release_candidate_ref": "alpha-release-candidate-freeze:m149",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M149_ACCEPTED_CHECKPOINT_REFS),
        "release_candidate_refs": [
            "release-candidate:m149:freeze",
            "release-candidate:m149:no-tag",
        ],
        "freeze_checklist_refs": [
            "freeze-checklist:m149:contracts",
            "freeze-checklist:m149:foundation-gate",
        ],
        "alpha_readiness_refs": [
            "alpha-readiness:m149:readiness-summary",
            "alpha-readiness:m149:no-public-release",
        ],
        "evidence_index_refs": [
            "evidence-index:m149:gate-results",
            "evidence-index:m149:docs-currentness",
        ],
        "blocker_summary_refs": [
            "blocker-summary:m149:none-recorded",
            "blocker-summary:m149:m150-future",
        ],
        "signoff_review_refs": [
            "signoff-review:m149:local-review",
            "signoff-review:m149:no-distribution",
        ],
        "m150_promotion_gate_refs": [
            "m150-promotion-gate:m149:future-only",
            "m150-promotion-gate:m149:no-alpha-publish",
        ],
        "audit_ref": "audit:m149:alpha-release-candidate-freeze",
        "replay_ref": "replay:m149:alpha-release-candidate-freeze",
        "revocation_ref": "revocation:m149:alpha-release-candidate-freeze",
        "kill_switch_ref": "kill-switch:m149:alpha-release-candidate-freeze",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m149:alpha-release-candidate-freeze:no-effect"
        ),
        "safe_summary": "Record alpha release candidate freeze refs without release authority.",
    }
    data.update(overrides)
    return AlphaReleaseCandidateFreezeRequest(**data)
