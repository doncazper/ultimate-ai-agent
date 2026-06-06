import pytest

from ultimate_ai_agent.core.plugin_install_review import (
    PluginInstallReviewApprovalBinding,
    PluginInstallReviewDecisionStatus,
    PluginInstallReviewRequest,
    build_plugin_install_review_decision,
    validate_plugin_install_review_policy,
)
from ultimate_ai_agent.core.plugin_manifest import (
    PluginManifestApprovalBinding,
    PluginManifestDeclaredPermission,
    PluginManifestPermissionKind,
    PluginManifestRiskLevel,
    PluginManifestSecurityReviewRequest,
    build_plugin_manifest_security_decision,
)


def _manifest_security_decision():
    return build_plugin_manifest_security_decision(
        PluginManifestSecurityReviewRequest(
            review_request_ref="plugin-manifest-review-request:m79-safe",
            manifest_ref="plugin-manifest:m79-safe",
            plugin_ref="plugin:m79-safe",
            plugin_name="safe-install-review-helper",
            plugin_version="2.0.0",
            actor_ref="actor:m79-reviewer",
            source_ref="plugin-source:m79-safe",
            provenance_ref="plugin-provenance:m79-safe",
            declared_permissions=[
                PluginManifestDeclaredPermission(
                    permission_ref="plugin-permission:read-only-docs",
                    kind=PluginManifestPermissionKind.read_only_local_docs,
                    risk_level=PluginManifestRiskLevel.low,
                    safe_purpose="Review declared metadata only.",
                    tool_broker_capability_ref="tool-broker-capability:read-only-docs",
                )
            ],
            static_review_ref="plugin-static-review:m79-safe",
            sandbox_test_plan_ref="plugin-sandbox-test-plan:m79-safe",
            tool_broker_mapping_ref="plugin-tool-broker-map:m79-safe",
            event_ledger_plan_ref="event-ledger-plan:m79-plugin-review",
            version_pin_ref="plugin-version-pin:m79-safe-2.0.0",
            revocation_plan_ref="plugin-revocation-plan:m79-safe",
            human_approval=PluginManifestApprovalBinding(
                approval_ref="approval:m79-manifest-review",
                approved_manifest_ref="plugin-manifest:m79-safe",
                approved_plugin_ref="plugin:m79-safe",
                approved_version="2.0.0",
                approved_actor_ref="actor:m79-reviewer",
            ),
            safe_manifest_summary="Reviewed plugin manifest metadata with disabled runtime capability.",
        )
    )


def _approval_binding() -> PluginInstallReviewApprovalBinding:
    return PluginInstallReviewApprovalBinding(
        approval_ref="approval:m79-install-review",
        approved_install_review_request_ref="plugin-install-review-request:m79-safe",
        approved_manifest_security_decision_ref="plugin-manifest-security-decision:m79-safe",
        approved_manifest_ref="plugin-manifest:m79-safe",
        approved_plugin_ref="plugin:m79-safe",
        approved_version="2.0.0",
        approved_actor_ref="actor:m79-reviewer",
    )


def _request(**overrides) -> PluginInstallReviewRequest:
    data = {
        "install_review_request_ref": "plugin-install-review-request:m79-safe",
        "manifest_security_decision": _manifest_security_decision(),
        "manifest_ref": "plugin-manifest:m79-safe",
        "plugin_ref": "plugin:m79-safe",
        "plugin_version": "2.0.0",
        "actor_ref": "actor:m79-reviewer",
        "source_package_ref": "plugin-package:m79-safe-reviewed",
        "provenance_ref": "plugin-provenance:m79-safe",
        "static_review_ref": "plugin-static-review:m79-safe",
        "sandbox_test_plan_ref": "plugin-sandbox-test-plan:m79-safe",
        "tool_broker_mapping_ref": "plugin-tool-broker-map:m79-safe",
        "event_ledger_plan_ref": "event-ledger-plan:m79-plugin-install-review",
        "version_pin_ref": "plugin-version-pin:m79-safe-2.0.0",
        "revocation_plan_ref": "plugin-revocation-plan:m79-safe",
        "approval": _approval_binding(),
        "safe_install_review_summary": "Review plugin install candidate metadata while keeping install disabled.",
    }
    data.update(overrides)
    return PluginInstallReviewRequest(**data)


def test_plugin_install_review_accepts_exact_bound_review_but_keeps_plugin_disabled() -> None:
    decision = build_plugin_install_review_decision(_request())

    assert decision.status == PluginInstallReviewDecisionStatus.install_review_ready_disabled
    assert decision.install_reviewed is True
    assert decision.plugin_install_enabled is False
    assert decision.plugin_enablement_enabled is False
    assert decision.plugin_execution_enabled is False
    assert decision.runtime_import_enabled is False
    assert decision.network_access_enabled is False
    assert decision.model_provider_call_enabled is False
    assert decision.browser_automation_enabled is False
    assert decision.shell_execution_enabled is False
    assert decision.mobile_device_access_enabled is False
    assert decision.remote_execution_enabled is False
    assert decision.credential_cookie_access_enabled is False
    assert decision.raw_manifest_content_returned is False
    assert decision.raw_package_content_returned is False
    assert decision.raw_prompt_exposure_enabled is False
    assert decision.raw_provider_payload_exposure_enabled is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.plugin_install_performed is False
    assert decision.receipt_plan.plugin_enablement_performed is False
    assert decision.receipt_plan.plugin_execution_performed is False
    assert decision.receipt_plan.raw_package_content_stored is False
    assert decision.reason_codes == [
        "M79_PLUGIN_INSTALL_REVIEW_DISABLED_BY_DEFAULT",
        "PLUGIN_INSTALL_REVIEW_READY_DISABLED",
        "M80_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_package_ref", None, "PLUGIN_SOURCE_PACKAGE_REF_REQUIRED"),
        ("static_review_ref", None, "PLUGIN_STATIC_REVIEW_REQUIRED"),
        ("sandbox_test_plan_ref", None, "PLUGIN_SANDBOX_TEST_PLAN_REQUIRED"),
        ("tool_broker_mapping_ref", None, "TOOL_BROKER_MAPPING_REQUIRED"),
        ("event_ledger_plan_ref", None, "EVENT_LEDGER_PLAN_REQUIRED"),
        ("version_pin_ref", None, "PLUGIN_VERSION_PIN_REQUIRED"),
        ("revocation_plan_ref", None, "PLUGIN_REVOCATION_PLAN_REQUIRED"),
        ("approval", None, "PLUGIN_INSTALL_REVIEW_APPROVAL_REQUIRED"),
        ("approval_ref", "approval_test_m79", "APPROVAL_TEST_REF_DENIED"),
        ("plugin_install_requested", True, "PLUGIN_INSTALL_DENIED"),
        ("plugin_enablement_requested", True, "PLUGIN_ENABLEMENT_DENIED"),
        ("plugin_execution_requested", True, "PLUGIN_EXECUTION_DENIED"),
        ("runtime_import_requested", True, "PLUGIN_RUNTIME_IMPORT_DENIED"),
        ("network_access_requested", True, "PLUGIN_NETWORK_ACCESS_DENIED"),
        ("model_provider_call_requested", True, "PLUGIN_MODEL_PROVIDER_CALL_DENIED"),
        ("browser_automation_requested", True, "PLUGIN_BROWSER_AUTOMATION_DENIED"),
        ("shell_execution_requested", True, "PLUGIN_SHELL_EXECUTION_DENIED"),
        ("mobile_device_access_requested", True, "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED"),
        ("remote_execution_requested", True, "PLUGIN_REMOTE_EXECUTION_DENIED"),
        ("credential_cookie_access_requested", True, "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("raw_manifest_content_requested", True, "RAW_MANIFEST_CONTENT_DENIED"),
        ("raw_package_content_requested", True, "RAW_PACKAGE_CONTENT_DENIED"),
        ("raw_prompt_exposure_requested", True, "RAW_PROMPT_EXPOSURE_DENIED"),
        ("raw_provider_payload_exposure_requested", True, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
        ("production_authority_requested", True, "PRODUCTION_AUTHORITY_DENIED"),
        ("model_output_authority_claimed", True, "MODEL_OUTPUT_AUTHORITY_DENIED"),
        ("openwebui_output_authority_claimed", True, "OPENWEBUI_OUTPUT_AUTHORITY_DENIED"),
    ],
)
def test_plugin_install_review_denies_missing_refs_and_runtime_authority(
    field: str, value: object, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_plugin_install_review_decision(_request(**{field: value}))


def test_plugin_install_review_requires_exact_approval_binding() -> None:
    base = _request()

    for update, reason in [
        ({"approved_install_review_request_ref": "plugin-install-review-request:other"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approved_manifest_security_decision_ref": "plugin-manifest-security-decision:other"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approved_manifest_ref": "plugin-manifest:other"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approved_plugin_ref": "plugin:other"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approved_version": "9.9.9"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approved_actor_ref": "actor:other"}, "APPROVAL_BINDING_MISMATCH"),
        ({"approval_expired": True}, "APPROVAL_EXPIRED_DENIED"),
        ({"approval_revoked": True}, "APPROVAL_REVOKED_DENIED"),
        ({"approval_replayed": True}, "APPROVAL_REPLAY_DENIED"),
        ({"approval_ref": "approval_test_m79"}, "APPROVAL_TEST_REF_DENIED"),
    ]:
        approval = _approval_binding().model_copy(update=update)
        with pytest.raises(ValueError, match=reason):
            build_plugin_install_review_decision(base.model_copy(update={"approval": approval}))


def test_plugin_install_review_revalidates_model_copy_mutated_request_and_manifest_decision() -> None:
    manifest_decision = _manifest_security_decision().model_copy(
        update={"plugin_install_enabled": True}
    )
    request = _request().model_copy(
        update={
            "manifest_security_decision": manifest_decision,
            "raw_package_content_requested": True,
            "runtime_import_requested": True,
        }
    )

    with pytest.raises(ValueError, match="PLUGIN_INSTALL_DENIED"):
        build_plugin_install_review_decision(request)


def test_plugin_install_review_policy_blocks_install_enablement_execution() -> None:
    policy = validate_plugin_install_review_policy()
    assert policy.plugin_install_review_enabled is True
    assert policy.plugin_install_enabled is False
    assert policy.plugin_enablement_enabled is False
    assert policy.plugin_execution_enabled is False

    with pytest.raises(ValueError, match="PLUGIN_INSTALL_DENIED"):
        validate_plugin_install_review_policy(
            policy.model_copy(update={"plugin_install_enabled": True})
        )

    with pytest.raises(ValueError, match="PLUGIN_RUNTIME_IMPORT_DENIED"):
        validate_plugin_install_review_policy(
            policy.model_copy(update={"runtime_import_enabled": True})
        )
