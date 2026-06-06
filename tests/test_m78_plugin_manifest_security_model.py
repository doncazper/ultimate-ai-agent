import pytest

from ultimate_ai_agent.core.plugin_manifest import (
    PluginManifestApprovalBinding,
    PluginManifestDeclaredPermission,
    PluginManifestPermissionKind,
    PluginManifestRiskLevel,
    PluginManifestSecurityDecisionStatus,
    PluginManifestSecurityReviewRequest,
    build_plugin_manifest_security_decision,
    validate_plugin_manifest_security_policy,
)


def _permission(
    kind: PluginManifestPermissionKind = PluginManifestPermissionKind.read_only_local_docs,
    risk: PluginManifestRiskLevel = PluginManifestRiskLevel.low,
) -> PluginManifestDeclaredPermission:
    return PluginManifestDeclaredPermission(
        permission_ref=f"plugin-permission:{kind.value}",
        kind=kind,
        risk_level=risk,
        safe_purpose="Review declared plugin capability metadata only.",
        tool_broker_capability_ref=f"tool-broker-capability:{kind.value}",
    )


def _approval_binding() -> PluginManifestApprovalBinding:
    return PluginManifestApprovalBinding(
        approval_ref="approval:m78-plugin-manifest-review",
        approved_manifest_ref="plugin-manifest:m78-safe",
        approved_plugin_ref="plugin:m78-safe",
        approved_version="1.2.3",
        approved_actor_ref="actor:m78-reviewer",
    )


def _request(**overrides) -> PluginManifestSecurityReviewRequest:
    data = {
        "review_request_ref": "plugin-manifest-review-request:m78-safe",
        "manifest_ref": "plugin-manifest:m78-safe",
        "plugin_ref": "plugin:m78-safe",
        "plugin_name": "safe-docs-review-helper",
        "plugin_version": "1.2.3",
        "actor_ref": "actor:m78-reviewer",
        "source_ref": "plugin-source:reviewed-local-fixture",
        "provenance_ref": "plugin-provenance:reviewed-local-fixture",
        "declared_permissions": [_permission()],
        "static_review_ref": "plugin-static-review:m78-safe",
        "sandbox_test_plan_ref": "plugin-sandbox-test-plan:m78-safe",
        "tool_broker_mapping_ref": "plugin-tool-broker-map:m78-safe",
        "event_ledger_plan_ref": "event-ledger-plan:m78-plugin-review",
        "version_pin_ref": "plugin-version-pin:m78-safe-1.2.3",
        "revocation_plan_ref": "plugin-revocation-plan:m78-safe",
        "human_approval": _approval_binding(),
        "safe_manifest_summary": "Reviewed plugin manifest metadata with disabled runtime capability.",
    }
    data.update(overrides)
    return PluginManifestSecurityReviewRequest(**data)


def test_plugin_manifest_security_model_accepts_reviewed_disabled_manifest() -> None:
    decision = build_plugin_manifest_security_decision(_request())

    assert decision.status == PluginManifestSecurityDecisionStatus.review_ready_disabled
    assert decision.manifest_reviewed is True
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
    assert decision.raw_prompt_exposure_enabled is False
    assert decision.raw_provider_payload_exposure_enabled is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.plugin_execution_performed is False
    assert decision.receipt_plan.raw_manifest_content_stored is False
    assert decision.receipt_plan.revocation_supported is True
    assert decision.reason_codes == [
        "M78_PLUGIN_MANIFEST_SECURITY_MODEL",
        "PLUGIN_REVIEW_READY_DISABLED",
        "M79_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_ref", None, "PLUGIN_SOURCE_REF_REQUIRED"),
        ("provenance_ref", None, "PLUGIN_PROVENANCE_REF_REQUIRED"),
        ("static_review_ref", None, "PLUGIN_STATIC_REVIEW_REQUIRED"),
        ("sandbox_test_plan_ref", None, "PLUGIN_SANDBOX_TEST_PLAN_REQUIRED"),
        ("tool_broker_mapping_ref", None, "TOOL_BROKER_MAPPING_REQUIRED"),
        ("event_ledger_plan_ref", None, "EVENT_LEDGER_PLAN_REQUIRED"),
        ("version_pin_ref", None, "PLUGIN_VERSION_PIN_REQUIRED"),
        ("revocation_plan_ref", None, "PLUGIN_REVOCATION_PLAN_REQUIRED"),
        ("declared_permissions", [], "DECLARED_PERMISSIONS_REQUIRED"),
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
        ("raw_prompt_exposure_requested", True, "RAW_PROMPT_EXPOSURE_DENIED"),
        ("raw_provider_payload_exposure_requested", True, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
        ("production_authority_requested", True, "PRODUCTION_AUTHORITY_DENIED"),
        ("approval_ref", "approval_test_m78", "APPROVAL_TEST_REF_DENIED"),
        ("model_output_authority_claimed", True, "MODEL_OUTPUT_AUTHORITY_DENIED"),
        ("openwebui_output_authority_claimed", True, "OPENWEBUI_OUTPUT_AUTHORITY_DENIED"),
    ],
)
def test_plugin_manifest_security_model_denies_missing_reviews_and_runtime_authority(
    field: str, value: object, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_plugin_manifest_security_decision(_request(**{field: value}))


def test_plugin_manifest_security_model_requires_exact_high_risk_approval_binding() -> None:
    high_risk_request = _request(
        declared_permissions=[
            _permission(PluginManifestPermissionKind.external_code_review, PluginManifestRiskLevel.high)
        ]
    )

    decision = build_plugin_manifest_security_decision(high_risk_request)
    assert decision.status == PluginManifestSecurityDecisionStatus.review_ready_disabled

    for update, reason in [
        ({"human_approval": None}, "HIGH_RISK_PLUGIN_APPROVAL_REQUIRED"),
        (
            {"human_approval": _approval_binding().model_copy(update={"approved_manifest_ref": "plugin-manifest:other"})},
            "APPROVAL_BINDING_MISMATCH",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approved_plugin_ref": "plugin:other"})},
            "APPROVAL_BINDING_MISMATCH",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approved_version": "9.9.9"})},
            "APPROVAL_BINDING_MISMATCH",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approved_actor_ref": "actor:other"})},
            "APPROVAL_BINDING_MISMATCH",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approval_expired": True})},
            "APPROVAL_EXPIRED_DENIED",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approval_revoked": True})},
            "APPROVAL_REVOKED_DENIED",
        ),
        (
            {"human_approval": _approval_binding().model_copy(update={"approval_replayed": True})},
            "APPROVAL_REPLAY_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_plugin_manifest_security_decision(high_risk_request.model_copy(update=update))


def test_plugin_manifest_security_model_revalidates_model_copy_mutated_fields() -> None:
    request = _request().model_copy(
        update={
            "plugin_execution_requested": True,
            "runtime_import_requested": True,
            "raw_provider_payload_exposure_requested": True,
        }
    )

    with pytest.raises(ValueError, match="PLUGIN_EXECUTION_DENIED"):
        build_plugin_manifest_security_decision(request)


def test_plugin_manifest_security_policy_blocks_enablement_and_execution() -> None:
    policy = validate_plugin_manifest_security_policy()
    assert policy.plugin_manifest_security_model_enabled is True
    assert policy.plugin_install_enabled is False
    assert policy.plugin_enablement_enabled is False
    assert policy.plugin_execution_enabled is False

    with pytest.raises(ValueError, match="PLUGIN_EXECUTION_DENIED"):
        validate_plugin_manifest_security_policy(
            policy.model_copy(update={"plugin_execution_enabled": True})
        )

    with pytest.raises(ValueError, match="PLUGIN_INSTALL_DENIED"):
        validate_plugin_manifest_security_policy(
            policy.model_copy(update={"plugin_install_enabled": True})
        )
