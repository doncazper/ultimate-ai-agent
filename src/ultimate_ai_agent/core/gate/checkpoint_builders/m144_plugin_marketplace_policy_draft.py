from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS,
    PluginMarketplacePolicyDraftRequest,
)


def _request(**overrides: Any) -> PluginMarketplacePolicyDraftRequest:
    data = {
        "request_ref": "plugin-marketplace-policy-draft-request:m144",
        "policy_draft_ref": "plugin-marketplace-policy-draft:m144",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS),
        "marketplace_policy_refs": [
            "marketplace-policy:m144:disabled-by-default",
            "marketplace-policy:m144:no-runtime",
        ],
        "publisher_policy_refs": [
            "publisher-policy:m144:identity-review-only",
            "publisher-policy:m144:no-publish-authority",
        ],
        "listing_review_refs": [
            "listing-review:m144:safe-summary-only",
            "listing-review:m144:no-listing-mutation",
        ],
        "provenance_review_refs": [
            "provenance-review:m144:source-ref-only",
            "provenance-review:m144:no-package-import",
        ],
        "signature_review_refs": [
            "signature-review:m144:policy-only",
            "signature-review:m144:no-runtime-verification",
        ],
        "sandbox_review_refs": [
            "sandbox-review:m144:future-test-plan",
            "sandbox-review:m144:no-plugin-execution",
        ],
        "permission_mapping_refs": [
            "permission-mapping:m144:tool-broker-plan",
            "permission-mapping:m144:no-permission-grant",
        ],
        "approval_policy_refs": [
            "approval-policy:m144:high-risk-human-review",
            "approval-policy:m144:no-approval-capture",
        ],
        "audit_ref": "audit:m144:plugin-marketplace-policy-draft",
        "replay_ref": "replay:m144:plugin-marketplace-policy-draft",
        "revocation_ref": "revocation:m144:plugin-marketplace-policy-draft",
        "kill_switch_ref": "kill-switch:m144:plugin-marketplace-policy-draft",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m144:plugin-marketplace-policy-draft:no-effect"
        ),
        "safe_summary": "Record plugin marketplace policy refs without runtime authority.",
    }
    data.update(overrides)
    return PluginMarketplacePolicyDraftRequest(**data)
