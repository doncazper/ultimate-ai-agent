from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    AutonomyV1SafetyFreezePolicy,
    AutonomyV1SafetyFreezeRequest,
    AutonomyV1SafetyFreezeStatus,
    build_autonomy_v1_safety_freeze_report,
    validate_autonomy_v1_safety_freeze_policy,
    validate_autonomy_v1_safety_freeze_report,
    validate_autonomy_v1_safety_freeze_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "autonomy-v1-safety-freeze-request:m99",
        "freeze_ref": "autonomy-v1-safety-freeze:m99",
        "baseline_ref": "baseline:v1.2.0",
        "actor_ref": "actor:local-reviewer",
        "accepted_milestone_refs": [f"milestone:M{index}" for index in range(61, 99)],
        "checklist_refs": [
            "m99-freeze:m61-m98-covered",
            "m99-freeze:browser-network-shell-reviewed",
            "m99-freeze:plugin-autonomy-reviewed",
            "m99-freeze:recurring-automation-reviewed",
            "m99-freeze:route-stable",
            "m99-freeze:dependency-stable",
            "m99-freeze:production-authority-blocked",
            "m99-freeze:m100-future",
        ],
        "safe_summary": "Freeze the accepted M61-M98 autonomy v1 surface without adding authority.",
    }
    data.update(overrides)
    return AutonomyV1SafetyFreezeRequest(**data)
