from typing import Any
import pytest

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


def test_m99_autonomy_v1_safety_freeze_report_is_review_only() -> None:
    report = build_autonomy_v1_safety_freeze_report(_request())

    assert report.status == AutonomyV1SafetyFreezeStatus.frozen_for_review
    assert report.freeze_only is True
    assert report.review_only is True
    assert report.m61_m98_covered is True
    assert report.no_broad_unsandboxed_autonomy is True
    assert report.no_production_authority is True
    assert report.execution_performed is False
    assert report.shell_execution_performed is False
    assert report.browser_action_performed is False
    assert report.network_mutation_performed is False
    assert report.plugin_execution_performed is False
    assert report.background_worker_started is False
    assert report.scheduler_started is False
    assert report.mobile_sensor_performed is False
    assert report.memory_write_performed is False
    assert report.context_injection_performed is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M99_AUTONOMY_V1_SAFETY_FREEZE_REVIEW_ONLY",
        "M99_M61_M98_COVERED",
        "M99_NO_BROAD_UNSANDBOXED_AUTONOMY",
        "M99_NO_PRODUCTION_AUTHORITY",
        "M100_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("broad_autonomy_requested", "BROAD_AUTONOMY_DENIED"),
        ("global_autonomy_switch_requested", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("browser_action_requested", "BROWSER_ACTION_DENIED"),
        ("network_mutation_requested", "NETWORK_MUTATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("scheduler_requested", "SCHEDULER_DENIED"),
        ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("credential_cookie_access_requested", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("raw_prompt_payload_exposure_requested", "RAW_PROMPT_PAYLOAD_EXPOSURE_DENIED"),
        ("raw_file_export_requested", "RAW_FILE_EXPORT_DENIED"),
        ("full_file_read_requested", "FULL_FILE_READ_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m99_freeze_denies_authority_expansion_requests(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomy_v1_safety_freeze_request(_request(**{field: True}))


def test_m99_freeze_requires_m61_through_m98_refs_and_unique_checklist() -> None:
    with pytest.raises(ValueError, match="M99_ACCEPTED_MILESTONES_REQUIRED"):
        validate_autonomy_v1_safety_freeze_request(_request(accepted_milestone_refs=[]))

    with pytest.raises(ValueError, match="M99_MILESTONE_REF_REQUIRED"):
        validate_autonomy_v1_safety_freeze_request(
            _request(accepted_milestone_refs=["milestone:M61"])
        )

    with pytest.raises(ValueError, match="M99_MILESTONE_REF_UNEXPECTED"):
        validate_autonomy_v1_safety_freeze_request(
            _request(accepted_milestone_refs=[f"milestone:M{index}" for index in range(61, 100)])
        )

    with pytest.raises(ValueError, match="M99_CHECKLIST_REF_DUPLICATE"):
        validate_autonomy_v1_safety_freeze_request(
            _request(checklist_refs=["m99-freeze:route-stable", "m99-freeze:route-stable"])
        )


def test_m99_freeze_revalidates_model_copy_mutations() -> None:
    request = _request().model_copy(
        update={
            "production_authority_requested": True,
            "contains_secret": True,
        }
    )
    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        build_autonomy_v1_safety_freeze_report(request)

    report = build_autonomy_v1_safety_freeze_report(_request())
    with pytest.raises(ValueError, match="SHELL_EXECUTION_DENIED"):
        validate_autonomy_v1_safety_freeze_report(
            report.model_copy(update={"shell_execution_performed": True})
        )


def test_m99_freeze_denies_secret_like_metadata_and_policy_enablement() -> None:
    with pytest.raises(ValueError, match="SECRET_LIKE_M99_FREEZE_CONTENT_DENIED"):
        build_autonomy_v1_safety_freeze_report(_request(metadata={"token": "abcde12345678901234"}))

    with pytest.raises(ValueError, match="BROAD_AUTONOMY_DENIED"):
        validate_autonomy_v1_safety_freeze_policy(
            AutonomyV1SafetyFreezePolicy(broad_autonomy_enabled=True)
        )
