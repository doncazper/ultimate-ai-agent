from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS,
    AlphaPrivacyReviewPolicy,
    AlphaPrivacyReviewRequest,
    AlphaPrivacyReviewStatus,
    build_alpha_privacy_review_record,
    validate_alpha_privacy_review_policy,
    validate_alpha_privacy_review_record,
    validate_alpha_privacy_review_request,
)


def _request(**overrides: Any) -> AlphaPrivacyReviewRequest:
    data = {
        "request_ref": "alpha-privacy-review-request:m142",
        "privacy_review_ref": "alpha-privacy-review:m142",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS),
        "privacy_review_refs": [
            "privacy-review:m142:safe-summary-only",
            "privacy-review:m142:no-raw-private-content",
        ],
        "data_boundary_refs": [
            "data-boundary:m142:safe-refs-only",
            "data-boundary:m142:no-cross-workspace-raw-content",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m142:no-raw-prompt",
            "disclosure-review:m142:no-provider-payload",
        ],
        "consent_review_refs": [
            "consent-review:m142:consent-copy-review",
            "consent-review:m142:revocation-copy-review",
        ],
        "retention_review_refs": [
            "retention-review:m142:no-production-retention",
            "retention-review:m142:no-audit-export",
        ],
        "audit_ref": "audit:m142:alpha-privacy-review",
        "replay_ref": "replay:m142:alpha-privacy-review",
        "revocation_ref": "revocation:m142:alpha-privacy-review",
        "kill_switch_ref": "kill-switch:m142:alpha-privacy-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m142:alpha-privacy-review:no-effect",
        "safe_summary": "Record alpha privacy review refs without raw private content.",
    }
    data.update(overrides)
    return AlphaPrivacyReviewRequest(**data)
