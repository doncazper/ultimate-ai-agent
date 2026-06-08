import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileNotificationChannel,
    MobileNotificationPlanningPolicy,
    MobileNotificationPlanningStatus,
    build_mobile_notification_planning_report,
    validate_mobile_notification_plan,
    validate_mobile_notification_planning_policy,
    validate_mobile_notification_planning_report,
)


def test_m104_notification_planning_is_contract_only_and_no_push() -> None:
    report = build_mobile_notification_planning_report()

    assert report.status == MobileNotificationPlanningStatus.contract_only
    assert report.contract_only is True
    assert report.planning_only is True
    assert report.no_push_execution is True
    assert report.notification_permission_prompt_enabled is False
    assert report.push_delivery_enabled is False
    assert report.notification_scheduling_enabled is False
    assert report.background_task_execution_enabled is False
    assert report.device_token_handling_enabled is False
    assert report.external_push_provider_enabled is False
    assert report.raw_notification_body_enabled is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M104_NOTIFICATION_PLANNING_NO_PUSH",
        "M104_SAFE_REFS_ONLY",
        "M104_NO_PERMISSION_PROMPT",
        "M104_NO_PUSH_DELIVERY",
        "M104_NO_BACKGROUND_TASK_EXECUTION",
        "M105_REMAINS_FUTURE",
    ]


def test_m104_notification_plans_are_safe_refs_only() -> None:
    report = build_mobile_notification_planning_report()

    assert {plan.channel for plan in report.notification_plans} == {
        MobileNotificationChannel.local_review_placeholder,
        MobileNotificationChannel.push_candidate_placeholder,
    }
    for plan in report.notification_plans:
        assert plan.notification_plan_ref.startswith("notification-plan:m104:")
        assert plan.safe_message_summary_ref.startswith("safe-notification-summary:")
        assert plan.safe_device_ref.startswith("safe-device-ref:")
        assert plan.safe_purpose_ref.startswith("safe-purpose-ref:")
        assert plan.consent_ref.startswith("consent-ref:")
        assert plan.revocation_ref.startswith("revocation-ref:")
        assert plan.audit_ref.startswith("audit-ref:")
        assert plan.planning_only is True
        assert plan.no_push_execution is True
        assert plan.push_delivery_enabled is False
        assert plan.raw_notification_body_enabled is False
        assert plan.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("push_delivery_enabled", "PUSH_DELIVERY_DENIED"),
        ("notification_permission_prompt_enabled", "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
        ("notification_scheduling_enabled", "NOTIFICATION_SCHEDULING_DENIED"),
        ("background_task_execution_enabled", "BACKGROUND_TASK_EXECUTION_DENIED"),
        ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
        ("external_push_provider_enabled", "EXTERNAL_PUSH_PROVIDER_DENIED"),
        ("raw_notification_body_enabled", "RAW_NOTIFICATION_BODY_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m104_policy_denies_notification_runtime_authority(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_notification_planning_policy(
            MobileNotificationPlanningPolicy(**{field: True})
        )


def test_m104_notification_plan_denies_raw_body_tokens_and_execution() -> None:
    report = build_mobile_notification_planning_report()
    plan = report.notification_plans[0]

    for update, reason in [
        ({"planning_only": False}, "M104_PLANNING_ONLY_REQUIRED"),
        ({"no_push_execution": False}, "M104_NO_PUSH_EXECUTION_REQUIRED"),
        ({"push_delivery_enabled": True}, "PUSH_DELIVERY_DENIED"),
        ({"notification_permission_prompt_enabled": True}, "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
        ({"device_token_handling_enabled": True}, "DEVICE_TOKEN_HANDLING_DENIED"),
        ({"raw_notification_body_enabled": True}, "RAW_NOTIFICATION_BODY_DENIED"),
        ({"side_effects_performed": ["sent push"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_notification_plan(plan.model_copy(update=update))


def test_m104_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_mobile_notification_planning_report()

    for update, reason in [
        ({"notification_permission_prompt_enabled": True}, "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
        ({"push_delivery_enabled": True}, "PUSH_DELIVERY_DENIED"),
        ({"notification_scheduling_enabled": True}, "NOTIFICATION_SCHEDULING_DENIED"),
        ({"background_task_execution_enabled": True}, "BACKGROUND_TASK_EXECUTION_DENIED"),
        ({"device_token_handling_enabled": True}, "DEVICE_TOKEN_HANDLING_DENIED"),
        ({"external_push_provider_enabled": True}, "EXTERNAL_PUSH_PROVIDER_DENIED"),
        ({"raw_notification_body_enabled": True}, "RAW_NOTIFICATION_BODY_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["delivered notification"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_notification_planning_report(report.model_copy(update=update))


def test_m104_rejects_duplicate_refs_and_secret_metadata() -> None:
    report = build_mobile_notification_planning_report()
    duplicate = report.model_copy(
        update={"notification_plans": [report.notification_plans[0], report.notification_plans[0]]}
    )

    with pytest.raises(ValueError, match="M104_NOTIFICATION_PLAN_REF_DUPLICATE"):
        validate_mobile_notification_planning_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M104_NOTIFICATION_CONTENT_DENIED"):
        validate_mobile_notification_planning_report(
            report.model_copy(update={"metadata": {"device_token": "abc123supersecret"}})
        )
