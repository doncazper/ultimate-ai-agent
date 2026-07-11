from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS,
    UltimateAiAgentAlphaRequest,
)


def _request(**overrides: Any) -> UltimateAiAgentAlphaRequest:
    data = {
        "request_ref": "ultimate-ai-agent-alpha-request:m150",
        "alpha_target_ref": "ultimate-ai-agent-alpha:m150",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS),
        "alpha_target_refs": [
            "alpha-target:m150:v1.2.0-alpha",
            "alpha-target:m150:no-public-release",
        ],
        "release_candidate_freeze_refs": [
            "release-candidate-freeze:m149:accepted",
            "release-candidate-freeze:m150:no-tag",
        ],
        "alpha_readiness_refs": [
            "alpha-readiness:m150:target-summary",
            "alpha-readiness:m150:local-only",
        ],
        "evidence_index_refs": [
            "evidence-index:m150:gate-results",
            "evidence-index:m150:docs-currentness",
        ],
        "blocker_summary_refs": [
            "blocker-summary:m150:none-recorded",
            "blocker-summary:m150:beta-future",
        ],
        "signoff_review_refs": [
            "signoff-review:m150:local-review",
            "signoff-review:m150:no-distribution",
        ],
        "beta_promotion_gate_refs": [
            "beta-promotion-gate:m150:future-only",
            "beta-promotion-gate:m150:no-beta-publish",
        ],
        "audit_ref": "audit:m150:ultimate-ai-agent-alpha",
        "replay_ref": "replay:m150:ultimate-ai-agent-alpha",
        "revocation_ref": "revocation:m150:ultimate-ai-agent-alpha",
        "kill_switch_ref": "kill-switch:m150:ultimate-ai-agent-alpha",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m150:ultimate-ai-agent-alpha:no-effect"
        ),
        "safe_summary": "Record v1.2.0-alpha target refs without release authority.",
    }
    data.update(overrides)
    return UltimateAiAgentAlphaRequest(**data)
