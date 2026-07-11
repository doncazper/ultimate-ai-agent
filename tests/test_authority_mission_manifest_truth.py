from __future__ import annotations

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest


def test_authority_mission_failure_management_capability_truth() -> None:
    manifest = build_api_manifest(app).model_dump(mode="json")
    for capability in [
        "authority_mission_approval_wait_durable_state",
        "authority_mission_retry_policy_exact_idempotent",
        "authority_mission_dead_letter_terminal_state",
        "authority_mission_cancellation_fence",
        "authority_mission_failure_management_operator_intent_api",
        "authority_mission_failure_management_cli",
        "control_center_authority_mission_read_only_inspection",
    ]:
        assert capability in manifest["capabilities_declared"]
    for capability in [
        "authority_mission_approval_decision_as_execution_authority",
        "authority_mission_approval_grant_durable_rehydration",
        "authority_mission_retry_unknown_execution_truth",
        "authority_mission_dead_letter_automatic_replay",
        "authority_mission_after_start_cancellation",
        "authority_mission_control_center_mutation",
    ]:
        assert capability in manifest["capabilities_blocked"]
    assert (
        "authority_mission_orchestration_automatic_retry_or_approval_wait"
        not in manifest["capabilities_blocked"]
    )
    assert (
        "authority_mission_orchestration_mission_level_cancellation"
        not in manifest["capabilities_blocked"]
    )


def test_authority_mission_failure_management_route_truth() -> None:
    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if route.method == "POST"
    }
    reasons = {
        path: routes[path].classification_reason
        for path in (
            "/api/runtime/authority-missions/approval-decisions",
            "/api/runtime/authority-missions/cancel",
            "/api/runtime/authority-missions/dead-letter-recovery",
        )
    }
    assert "grants no execution authority" in reasons[
        "/api/runtime/authority-missions/approval-decisions"
    ]
    assert "fresh LocalApprovalAuthority and dispatcher request-scoped validation" in reasons[
        "/api/runtime/authority-missions/approval-decisions"
    ]
    assert "can only reduce authority" in reasons[
        "/api/runtime/authority-missions/cancel"
    ]
    assert "does not reopen, replay, or execute" in reasons[
        "/api/runtime/authority-missions/dead-letter-recovery"
    ]
