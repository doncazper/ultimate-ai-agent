import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileApprovalRenewalUxChannel,
    MobileApprovalRenewalUxPolicy,
    MobileApprovalRenewalUxStatus,
    build_mobile_approval_renewal_ux_report,
    validate_mobile_approval_renewal_prompt,
    validate_mobile_approval_renewal_ux_policy,
    validate_mobile_approval_renewal_ux_report,
)


def test_m107_approval_renewal_ux_is_contract_only_and_non_authoritative() -> None:
    report = build_mobile_approval_renewal_ux_report()

    assert report.status == MobileApprovalRenewalUxStatus.review_only_contract
    assert report.contract_only is True
    assert report.review_only is True
    assert report.safe_refs_required is True
    assert report.renewal_prompts
    assert report.approval_capture_enabled is False
    assert report.approval_persistence_enabled is False
    assert report.approval_renewal_execution_enabled is False
    assert report.approval_renewal_runtime_prompt_enabled is False
    assert report.native_mobile_ui_enabled is False
    assert report.control_center_control_added is False
    assert report.backend_route_added is False
    assert report.notification_delivery_enabled is False
    assert report.push_trigger_enabled is False
    assert report.background_worker_enabled is False
    assert report.scheduler_enabled is False
    assert report.daemon_enabled is False
    assert report.device_token_handling_enabled is False
    assert report.external_service_enabled is False
    assert report.network_sync_enabled is False
    assert report.raw_approval_payload_enabled is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.kill_switch_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M107_MOBILE_APPROVAL_RENEWAL_UX",
        "M107_SAFE_RENEWAL_REFS_ONLY",
        "M107_REVIEW_ONLY_UX_CONTRACT",
        "M107_NO_APPROVAL_CAPTURE",
        "M107_NO_APPROVAL_PERSISTENCE",
        "M108_REMAINS_FUTURE",
    ]


def test_m107_renewal_prompts_are_safe_refs_only() -> None:
    report = build_mobile_approval_renewal_ux_report()

    assert {prompt.channel for prompt in report.renewal_prompts} == {
        MobileApprovalRenewalUxChannel.renewal_banner_copy,
        MobileApprovalRenewalUxChannel.renewal_expiration_notice,
    }
    for prompt in report.renewal_prompts:
        assert prompt.prompt_ref.startswith("approval-renewal-prompt:m107:")
        assert prompt.approval_ref.startswith("approval-ref:m107:")
        assert prompt.actor_ref.startswith("actor:")
        assert prompt.safe_device_ref.startswith("safe-device-ref:")
        assert prompt.safe_renewal_copy_ref.startswith("safe-renewal-copy-ref:")
        assert prompt.safe_renewal_window_ref.startswith("safe-renewal-window-ref:")
        assert prompt.safe_expiration_ref.startswith("safe-expiration-ref:")
        assert prompt.consent_ref.startswith("consent-ref:")
        assert prompt.revocation_ref.startswith("revocation-ref:")
        assert prompt.audit_ref.startswith("audit-ref:")
        assert prompt.review_only is True
        assert prompt.safe_refs_only is True
        assert prompt.approval_capture_enabled is False
        assert prompt.approval_persistence_enabled is False
        assert prompt.raw_approval_payload_enabled is False
        assert prompt.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("approval_capture_enabled", "APPROVAL_CAPTURE_DENIED"),
        ("approval_persistence_enabled", "APPROVAL_PERSISTENCE_DENIED"),
        ("approval_renewal_execution_enabled", "APPROVAL_RENEWAL_EXECUTION_DENIED"),
        (
            "approval_renewal_runtime_prompt_enabled",
            "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED",
        ),
        ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
        ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("scheduler_enabled", "SCHEDULER_DENIED"),
        ("daemon_enabled", "DAEMON_DENIED"),
        ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
        ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
        ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
        ("raw_approval_payload_enabled", "RAW_APPROVAL_PAYLOAD_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("kill_switch_enabled", "KILL_SWITCH_DENIED"),
    ],
)
def test_m107_policy_denies_runtime_renewal_authority(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_approval_renewal_ux_policy(
            MobileApprovalRenewalUxPolicy(**{field: True})
        )


def test_m107_prompt_denies_model_copy_unsafe_flags() -> None:
    report = build_mobile_approval_renewal_ux_report()
    prompt = report.renewal_prompts[0]

    for update, reason in [
        ({"review_only": False}, "M107_REVIEW_ONLY_REQUIRED"),
        ({"safe_refs_only": False}, "M107_SAFE_REFS_REQUIRED"),
        ({"approval_capture_enabled": True}, "APPROVAL_CAPTURE_DENIED"),
        ({"approval_persistence_enabled": True}, "APPROVAL_PERSISTENCE_DENIED"),
        ({"approval_renewal_execution_enabled": True}, "APPROVAL_RENEWAL_EXECUTION_DENIED"),
        ({"raw_approval_payload_enabled": True}, "RAW_APPROVAL_PAYLOAD_DENIED"),
        ({"side_effects_performed": ["renewed approval"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_approval_renewal_prompt(prompt.model_copy(update=update))


def test_m107_report_revalidates_model_copy_runtime_flags() -> None:
    report = build_mobile_approval_renewal_ux_report()

    for update, reason in [
        ({"approval_capture_enabled": True}, "APPROVAL_CAPTURE_DENIED"),
        ({"approval_persistence_enabled": True}, "APPROVAL_PERSISTENCE_DENIED"),
        ({"approval_renewal_execution_enabled": True}, "APPROVAL_RENEWAL_EXECUTION_DENIED"),
        ({"approval_renewal_runtime_prompt_enabled": True}, "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED"),
        ({"native_mobile_ui_enabled": True}, "NATIVE_MOBILE_UI_DENIED"),
        ({"backend_route_added": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"notification_delivery_enabled": True}, "NOTIFICATION_DELIVERY_DENIED"),
        ({"push_trigger_enabled": True}, "PUSH_TRIGGER_DENIED"),
        ({"background_worker_enabled": True}, "BACKGROUND_WORKER_DENIED"),
        ({"scheduler_enabled": True}, "SCHEDULER_DENIED"),
        ({"daemon_enabled": True}, "DAEMON_DENIED"),
        ({"device_token_handling_enabled": True}, "DEVICE_TOKEN_HANDLING_DENIED"),
        ({"external_service_enabled": True}, "EXTERNAL_SERVICE_DENIED"),
        ({"network_sync_enabled": True}, "NETWORK_SYNC_DENIED"),
        ({"raw_approval_payload_enabled": True}, "RAW_APPROVAL_PAYLOAD_DENIED"),
        ({"memory_write_enabled": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_enabled": True}, "CONTEXT_INJECTION_DENIED"),
        ({"execution_enabled": True}, "EXECUTION_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"kill_switch_enabled": True}, "KILL_SWITCH_DENIED"),
        ({"side_effects_performed": ["prompted mobile runtime"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_approval_renewal_ux_report(report.model_copy(update=update))


def test_m107_rejects_duplicate_refs_and_secret_metadata() -> None:
    report = build_mobile_approval_renewal_ux_report()
    duplicate = report.model_copy(
        update={
            "renewal_prompts": [
                report.renewal_prompts[0],
                report.renewal_prompts[0],
            ]
        }
    )

    with pytest.raises(ValueError, match="M107_RENEWAL_PROMPT_REF_DUPLICATE"):
        validate_mobile_approval_renewal_ux_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M107_APPROVAL_RENEWAL_CONTENT_DENIED"):
        validate_mobile_approval_renewal_ux_report(
            report.model_copy(update={"metadata": {"approval_token": "abc123supersecret"}})
        )
