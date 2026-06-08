import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileBackgroundTaskChannel,
    MobileBackgroundTaskContractPolicy,
    MobileBackgroundTaskContractStatus,
    build_mobile_background_task_contract_report,
    validate_mobile_background_task_contract_policy,
    validate_mobile_background_task_contract_report,
    validate_mobile_background_task_plan,
)


def test_m105_background_task_contract_is_contract_only_and_no_execution() -> None:
    report = build_mobile_background_task_contract_report()

    assert report.status == MobileBackgroundTaskContractStatus.contract_only
    assert report.contract_only is True
    assert report.planning_only is True
    assert report.no_background_execution is True
    assert report.safe_refs_required is True
    assert report.background_worker_enabled is False
    assert report.scheduler_enabled is False
    assert report.daemon_enabled is False
    assert report.os_background_permission_prompt_enabled is False
    assert report.push_trigger_enabled is False
    assert report.device_token_handling_enabled is False
    assert report.external_service_enabled is False
    assert report.raw_task_payload_enabled is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M105_BACKGROUND_TASK_CONTRACT_NO_EXECUTION",
        "M105_SAFE_REFS_ONLY",
        "M105_NO_BACKGROUND_WORKER",
        "M105_NO_SCHEDULER",
        "M105_NO_DAEMON",
        "M106_REMAINS_FUTURE",
    ]


def test_m105_background_task_plans_are_safe_refs_only() -> None:
    report = build_mobile_background_task_contract_report()

    assert {plan.channel for plan in report.background_task_plans} == {
        MobileBackgroundTaskChannel.local_status_placeholder,
        MobileBackgroundTaskChannel.sync_candidate_placeholder,
    }
    for plan in report.background_task_plans:
        assert plan.background_task_plan_ref.startswith("background-task-plan:m105:")
        assert plan.safe_task_summary_ref.startswith("safe-background-task-summary:")
        assert plan.safe_device_ref.startswith("safe-device-ref:")
        assert plan.safe_cadence_ref.startswith("safe-cadence-ref:")
        assert plan.consent_ref.startswith("consent-ref:")
        assert plan.revocation_ref.startswith("revocation-ref:")
        assert plan.audit_ref.startswith("audit-ref:")
        assert plan.planning_only is True
        assert plan.no_background_execution is True
        assert plan.background_worker_enabled is False
        assert plan.scheduler_enabled is False
        assert plan.daemon_enabled is False
        assert plan.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "SCHEDULER_DENIED"),
        ("daemon_enabled", "DAEMON_DENIED"),
        ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
        ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
        ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
        ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
        ("raw_task_payload_enabled", "RAW_TASK_PAYLOAD_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m105_policy_denies_background_runtime_authority(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_background_task_contract_policy(
            MobileBackgroundTaskContractPolicy(**{field: True})
        )


def test_m105_background_task_plan_denies_execution_and_runtime_flags() -> None:
    report = build_mobile_background_task_contract_report()
    plan = report.background_task_plans[0]

    for update, reason in [
        ({"planning_only": False}, "M105_PLANNING_ONLY_REQUIRED"),
        ({"no_background_execution": False}, "M105_NO_BACKGROUND_EXECUTION_REQUIRED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"daemon_enabled": True}, "DAEMON_DENIED"),
        ({"raw_task_payload_enabled": True}, "RAW_TASK_PAYLOAD_DENIED"),
        ({"side_effects_performed": ["started background worker"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_background_task_plan(plan.model_copy(update=update))


def test_m105_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_mobile_background_task_contract_report()

    for update, reason in [
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"daemon_enabled": True}, "DAEMON_DENIED"),
        ({"os_background_permission_prompt_enabled": True}, "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
        ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
        ({"device_token_handling_enabled": True}, "DEVICE_TOKEN_HANDLING_DENIED"),
        ({"external_service_enabled": True}, "EXTERNAL_SERVICE_DENIED"),
        ({"raw_task_payload_enabled": True}, "RAW_TASK_PAYLOAD_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["scheduled task"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_background_task_contract_report(report.model_copy(update=update))


def test_m105_rejects_duplicate_refs_and_secret_metadata() -> None:
    report = build_mobile_background_task_contract_report()
    duplicate = report.model_copy(
        update={
            "background_task_plans": [
                report.background_task_plans[0],
                report.background_task_plans[0],
            ]
        }
    )

    with pytest.raises(ValueError, match="M105_BACKGROUND_TASK_PLAN_REF_DUPLICATE"):
        validate_mobile_background_task_contract_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M105_BACKGROUND_TASK_CONTENT_DENIED"):
        validate_mobile_background_task_contract_report(
            report.model_copy(update={"metadata": {"background_token": "abc123supersecret"}})
        )
