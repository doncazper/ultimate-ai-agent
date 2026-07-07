from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS,
    ExternalSecurityReviewPolicy,
    ExternalSecurityReviewRequest,
    ExternalSecurityReviewStatus,
    build_external_security_review_record,
    validate_external_security_review_policy,
    validate_external_security_review_record,
    validate_external_security_review_request,
)


def _request(**overrides: Any) -> ExternalSecurityReviewRequest:
    data = {
        "request_ref": "external-security-review-request:m148",
        "security_review_ref": "external-security-review:m148",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS),
        "security_review_refs": [
            "security-review:m148:readme",
            "security-review:m148:safety-overview",
        ],
        "threat_model_refs": [
            "threat-model:m148:landing-index",
            "threat-model:m148:no-upload",
        ],
        "review_scope_refs": [
            "review-scope:m148:evidence-index-entry",
            "review-scope:m148:no-generated-site",
        ],
        "evidence_index_refs": [
            "evidence-index:m148:security-reviews",
            "evidence-index:m148:threat-model",
        ],
        "finding_summary_refs": [
            "finding-summary:m148:checkpoint",
            "finding-summary:m148:no-release-publish",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m148:authority-boundary",
            "disclosure-review:m148:no-sensitive-content",
        ],
        "remediation_plan_refs": [
            "remediation-plan:m148:manual-review",
            "remediation-plan:m148:no-automation",
        ],
        "audit_ref": "audit:m148:external-security-review",
        "replay_ref": "replay:m148:external-security-review",
        "revocation_ref": "revocation:m148:external-security-review",
        "kill_switch_ref": "kill-switch:m148:external-security-review",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m148:external-security-review:no-effect"
        ),
        "safe_summary": "Record security reviews and threat model refs without external security authority.",
    }
    data.update(overrides)
    return ExternalSecurityReviewRequest(**data)
