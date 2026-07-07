from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS,
    AlphaUiAppReadinessPolicy,
    AlphaUiAppReadinessRequest,
    AlphaUiAppReadinessStatus,
    build_alpha_ui_app_readiness_record,
    validate_alpha_ui_app_readiness_policy,
    validate_alpha_ui_app_readiness_record,
    validate_alpha_ui_app_readiness_request,
)


def _request(**overrides: Any) -> AlphaUiAppReadinessRequest:
    data = {
        "request_ref": "alpha-ui-app-readiness-request:m143",
        "readiness_review_ref": "alpha-ui-app-readiness:m143",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS),
        "ui_readiness_refs": [
            "ui-readiness:m143:alpha-shell-safe",
            "ui-readiness:m143:no-runtime-start",
        ],
        "app_readiness_refs": [
            "app-readiness:m143:checklist-only",
            "app-readiness:m143:no-build",
        ],
        "privacy_review_refs": [
            "privacy-review:m142:safe-summary-only",
            "privacy-review:m143:no-raw-private-content",
        ],
        "accessibility_review_refs": [
            "accessibility-review:m143:keyboard-copy",
            "accessibility-review:m143:contrast-review",
        ],
        "release_blocker_refs": [
            "release-blocker:m143:no-alpha-release",
            "release-blocker:m143:no-beta-release",
        ],
        "audit_ref": "audit:m143:alpha-ui-app-readiness",
        "replay_ref": "replay:m143:alpha-ui-app-readiness",
        "revocation_ref": "revocation:m143:alpha-ui-app-readiness",
        "kill_switch_ref": "kill-switch:m143:alpha-ui-app-readiness",
        "no_effect_receipt_plan_ref": "receipt-plan:m143:alpha-ui-app-readiness:no-effect",
        "safe_summary": "Record alpha UI and app readiness refs without starting runtime.",
    }
    data.update(overrides)
    return AlphaUiAppReadinessRequest(**data)
