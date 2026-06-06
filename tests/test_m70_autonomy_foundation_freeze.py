import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyFoundationFreezePolicy,
    AutonomyFoundationFreezeRequest,
    AutonomyFoundationFreezeStatus,
    build_autonomy_foundation_freeze_report,
    validate_autonomy_foundation_freeze_policy,
    validate_autonomy_foundation_freeze_request,
)


def _request(**overrides):
    data = {
        "request_ref": "autonomy-foundation-freeze-request:m70",
        "freeze_ref": "autonomy-foundation-freeze:m70",
        "baseline_ref": "baseline:v0.73.0",
        "actor_ref": "actor:local-reviewer",
        "accepted_milestone_refs": [
            "milestone:M61",
            "milestone:M62",
            "milestone:M63",
            "milestone:M64",
            "milestone:M65",
            "milestone:M66",
            "milestone:M67",
            "milestone:M68",
            "milestone:M69",
        ],
        "checklist_refs": [
            "autonomy-freeze:m61-m69-reviewed",
            "autonomy-freeze:route-stable",
            "autonomy-freeze:dependency-stable",
            "autonomy-freeze:authority-frozen",
            "autonomy-freeze:docs-current",
            "autonomy-freeze:gate-green",
        ],
        "safe_summary": "Freeze the M61-M69 autonomy foundation without adding authority.",
    }
    data.update(overrides)
    return AutonomyFoundationFreezeRequest(**data)


def test_autonomy_foundation_freeze_report_is_review_only_and_no_authority() -> None:
    report = build_autonomy_foundation_freeze_report(_request())

    assert report.status == AutonomyFoundationFreezeStatus.frozen
    assert report.freeze_only is True
    assert report.review_only is True
    assert report.autonomy_foundation_only is True
    assert report.policy_activation_performed is False
    assert report.session_start_performed is False
    assert report.execution_performed is False
    assert report.background_worker_started is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M70_AUTONOMY_FOUNDATION_FREEZE_REVIEW_ONLY",
        "M70_NO_NEW_AUTONOMY_AUTHORITY",
    ]
    assert "private key" not in str(report.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("low_risk_dry_run_execution_requested", "LOW_RISK_DRY_RUN_EXECUTION_DENIED"),
        ("autonomous_actions_requested", "AUTONOMOUS_ACTIONS_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("network_tool_requested", "NETWORK_TOOL_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_requested", "MODEL_PROVIDER_CALL_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_autonomy_foundation_freeze_denies_authority_request_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomy_foundation_freeze_request(_request(**{field: True}))


def test_autonomy_foundation_freeze_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "execution_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="EXECUTION_DENIED"):
        build_autonomy_foundation_freeze_report(request)


def test_autonomy_foundation_freeze_requires_m61_through_m69_refs_and_unique_checklist() -> None:
    with pytest.raises(ValueError, match="AUTONOMY_FOUNDATION_ACCEPTED_MILESTONES_REQUIRED"):
        validate_autonomy_foundation_freeze_request(_request(accepted_milestone_refs=[]))

    with pytest.raises(ValueError, match="AUTONOMY_FOUNDATION_MILESTONE_REF_REQUIRED"):
        validate_autonomy_foundation_freeze_request(
            _request(accepted_milestone_refs=["milestone:M61"])
        )

    with pytest.raises(ValueError, match="AUTONOMY_FOUNDATION_CHECKLIST_REF_DUPLICATE"):
        validate_autonomy_foundation_freeze_request(
            _request(
                checklist_refs=[
                    "autonomy-freeze:docs-current",
                    "autonomy-freeze:docs-current",
                ]
            )
        )


def test_autonomy_foundation_freeze_denies_secret_like_metadata() -> None:
    request = _request(metadata={"token": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_FOUNDATION_FREEZE_CONTENT_DENIED"):
        build_autonomy_foundation_freeze_report(request)


def test_autonomy_foundation_freeze_policy_denies_enablement() -> None:
    policy = AutonomyFoundationFreezePolicy(
        policy_activation_enabled=True,
        session_start_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="AUTONOMY_POLICY_ACTIVATION_DENIED"):
        validate_autonomy_foundation_freeze_policy(policy)
