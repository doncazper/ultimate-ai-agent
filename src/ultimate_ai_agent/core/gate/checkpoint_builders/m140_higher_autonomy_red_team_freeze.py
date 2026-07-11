from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS,
    HigherAutonomyRedTeamFreezeRequest,
)


def _request(**overrides: Any) -> HigherAutonomyRedTeamFreezeRequest:
    data = {
        "request_ref": "higher-autonomy-red-team-freeze-request:m140",
        "freeze_ref": "higher-autonomy-red-team-freeze:m140",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS),
        "red_team_checklist_refs": [
            "m140-freeze:m131-m139-covered",
            "m140-freeze:higher-autonomy-boundary-reviewed",
            "m140-freeze:red-team-runtime-absent",
            "m140-freeze:route-stable",
            "m140-freeze:dependency-stable",
            "m140-freeze:production-authority-blocked",
            "m140-freeze:m141-future",
        ],
        "audit_ref": "audit:m140:higher-autonomy-red-team-freeze",
        "replay_ref": "replay:m140:higher-autonomy-red-team-freeze",
        "revocation_ref": "revocation:m140:higher-autonomy-red-team-freeze",
        "kill_switch_ref": "kill-switch:m140:higher-autonomy-red-team-freeze",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m140:higher-autonomy-red-team-freeze:no-effect"
        ),
        "safe_summary": (
            "Freeze accepted M131-M139 higher-autonomy refs without adding runtime."
        ),
    }
    data.update(overrides)
    return HigherAutonomyRedTeamFreezeRequest(**data)
