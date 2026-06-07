import pytest

from ultimate_ai_agent.core.plugin_execution_sandbox import (
    BuiltInPluginExecutionSandboxPolicy,
    BuiltInPluginExecutionSandboxRequest,
    BuiltInPluginExecutionSandboxStatus,
    build_builtin_plugin_execution_sandbox_decision,
    validate_builtin_plugin_execution_sandbox_decision,
    validate_builtin_plugin_execution_sandbox_policy,
    validate_builtin_plugin_execution_sandbox_request,
)
from ultimate_ai_agent.core.plugin_install_review import (
    PluginInstallReviewApprovalBinding,
    PluginInstallReviewRequest,
    build_plugin_install_review_decision,
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
            review_request_ref="plugin-manifest-review-request:m96-built-in",
            manifest_ref="plugin-manifest:m96-built-in",
            plugin_ref="plugin:m96-built-in-test-noop",
            plugin_name="m96-built-in-test-noop",
            plugin_version="1.0.0",
            actor_ref="actor:m96-reviewer",
            source_ref="plugin-source:m96-built-in",
            provenance_ref="plugin-provenance:m96-built-in",
            declared_permissions=[
                PluginManifestDeclaredPermission(
                    permission_ref="plugin-permission:m96-built-in-test-noop",
                    kind=PluginManifestPermissionKind.read_only_local_docs,
                    risk_level=PluginManifestRiskLevel.low,
                    safe_purpose="Allow only the built-in deterministic no-op test plugin.",
                    tool_broker_capability_ref="tool-broker-capability:m96-built-in-test-noop",
                )
            ],
            static_review_ref="plugin-static-review:m96-built-in",
            sandbox_test_plan_ref="plugin-sandbox-test-plan:m96-built-in",
            tool_broker_mapping_ref="plugin-tool-broker-map:m96-built-in",
            event_ledger_plan_ref="event-ledger-plan:m96-built-in",
            version_pin_ref="plugin-version-pin:m96-built-in-1.0.0",
            revocation_plan_ref="plugin-revocation-plan:m96-built-in",
            human_approval=PluginManifestApprovalBinding(
                approval_ref="approval:m96-plugin-manifest-review",
                approved_manifest_ref="plugin-manifest:m96-built-in",
                approved_plugin_ref="plugin:m96-built-in-test-noop",
                approved_version="1.0.0",
                approved_actor_ref="actor:m96-reviewer",
            ),
            safe_manifest_summary="Reviewed built-in deterministic no-op test plugin metadata.",
        )
    )


def _install_review_decision():
    manifest_decision = _manifest_security_decision()
    return build_plugin_install_review_decision(
        PluginInstallReviewRequest(
            install_review_request_ref="plugin-install-review-request:m96-built-in",
            manifest_security_decision=manifest_decision,
            manifest_ref="plugin-manifest:m96-built-in",
            plugin_ref="plugin:m96-built-in-test-noop",
            plugin_version="1.0.0",
            actor_ref="actor:m96-reviewer",
            source_package_ref="plugin-package:m96-built-in",
            provenance_ref="plugin-provenance:m96-built-in",
            static_review_ref="plugin-static-review:m96-built-in",
            sandbox_test_plan_ref="plugin-sandbox-test-plan:m96-built-in",
            tool_broker_mapping_ref="plugin-tool-broker-map:m96-built-in",
            event_ledger_plan_ref="event-ledger-plan:m96-built-in",
            version_pin_ref="plugin-version-pin:m96-built-in-1.0.0",
            revocation_plan_ref="plugin-revocation-plan:m96-built-in",
            approval=PluginInstallReviewApprovalBinding(
                approval_ref="approval:m96-install-review",
                approved_install_review_request_ref="plugin-install-review-request:m96-built-in",
                approved_manifest_security_decision_ref=manifest_decision.decision_ref,
                approved_manifest_ref="plugin-manifest:m96-built-in",
                approved_plugin_ref="plugin:m96-built-in-test-noop",
                approved_version="1.0.0",
                approved_actor_ref="actor:m96-reviewer",
            ),
            safe_install_review_summary="Review built-in test plugin package metadata while install stays disabled.",
        )
    )


def _request(**overrides):
    install_decision = overrides.pop("install_review_decision", _install_review_decision())
    data = {
        "request_ref": "plugin-execution-sandbox-request:m96-safe",
        "plugin_ref": install_decision.plugin_ref,
        "action_ref": "plugin-action:m96-noop",
        "permission_ref": "plugin-permission:m96-built-in-test-noop",
        "actor_ref": install_decision.actor_ref,
        "scope_ref": "scope:m96-built-in-test-only",
        "sandbox_ref": "plugin-sandbox:m96-built-in-test-only",
        "audit_ref": "audit:m96-built-in-test-only",
        "revocation_ref": "revocation:m96-built-in-test-only",
        "install_review_decision_ref": install_decision.decision_ref,
        "manifest_security_decision_ref": install_decision.manifest_security_decision_ref,
        "manifest_ref": install_decision.manifest_ref,
        "plugin_version": install_decision.plugin_version,
        "safe_input_summary": "Invoke only the built-in deterministic no-op test plugin.",
        "install_review_decision": install_decision,
    }
    data.update(overrides)
    return BuiltInPluginExecutionSandboxRequest(**data)


def test_builtin_plugin_execution_sandbox_allows_only_builtin_test_plugin() -> None:
    decision = build_builtin_plugin_execution_sandbox_decision(_request())

    assert decision.status == BuiltInPluginExecutionSandboxStatus.builtin_test_plugin_allowed
    assert decision.capability_exists is True
    assert decision.disabled_by_default is True
    assert decision.builtin_test_plugin_only is True
    assert decision.sandbox_enforced is True
    assert decision.manifest_permissions_enforced is True
    assert decision.audit_receipt_created is True
    assert decision.revocation_bound is True
    assert decision.deterministic_result is True
    assert decision.safe_refs_only is True
    assert decision.built_in_test_plugin_invoked is True
    assert decision.external_plugin_loading_allowed is False
    assert decision.marketplace_plugin_allowed is False
    assert decision.arbitrary_plugin_code_allowed is False
    assert decision.runtime_import_allowed is False
    assert decision.networked_plugin_fetch_allowed is False
    assert decision.plugin_secret_access_allowed is False
    assert decision.raw_plugin_payload_allowed is False
    assert decision.shell_execution_allowed is False
    assert decision.network_access_allowed is False
    assert decision.browser_automation_allowed is False
    assert decision.filesystem_mutation_allowed is False
    assert decision.model_provider_call_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.context_injection_allowed is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.safe_output_ref == "plugin-output:m96-built-in-test-noop-ok"
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_raw_plugin_payload is False
    assert decision.reason_codes == [
        "M96_BUILTIN_TEST_PLUGIN_SANDBOX_ALLOWED",
        "BUILTIN_TEST_PLUGIN_ONLY",
        "PLUGIN_MANIFEST_PERMISSIONS_ENFORCED",
        "NO_EXTERNAL_PLUGIN_LOADING",
        "NO_ARBITRARY_PLUGIN_CODE",
        "NO_NETWORKED_PLUGIN_FETCH",
        "M97_REMAINS_FUTURE",
    ]


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"plugin_ref": "plugin:external"}, "PLUGIN_REF_BINDING_MISMATCH"),
        ({"action_ref": "plugin-action:external"}, "PLUGIN_ACTION_NOT_ALLOWLISTED"),
        ({"permission_ref": "plugin-permission:external"}, "PLUGIN_MANIFEST_PERMISSION_DENIED"),
        ({"external_plugin_requested": True}, "EXTERNAL_PLUGIN_LOADING_DENIED"),
        ({"marketplace_plugin_requested": True}, "MARKETPLACE_PLUGIN_DENIED"),
        ({"arbitrary_plugin_code_requested": True}, "ARBITRARY_PLUGIN_CODE_DENIED"),
        ({"runtime_import_requested": True}, "PLUGIN_RUNTIME_IMPORT_DENIED"),
        ({"networked_plugin_fetch_requested": True}, "NETWORKED_PLUGIN_FETCH_DENIED"),
        ({"plugin_secret_access_requested": True}, "PLUGIN_SECRET_ACCESS_DENIED"),
        ({"raw_plugin_payload_requested": True}, "RAW_PLUGIN_PAYLOAD_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
        ({"model_provider_call_requested": True}, "PROVIDER_MODEL_CALL_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_requested": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_builtin_plugin_execution_sandbox_denies_unsafe_request_shapes(
    override: dict[str, object], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_builtin_plugin_execution_sandbox_decision(_request(**override))


def test_builtin_plugin_execution_sandbox_requires_exact_review_binding() -> None:
    for update, reason in [
        ({"install_review_decision_ref": "plugin-install-review-decision:other"}, "PLUGIN_INSTALL_REVIEW_BINDING_MISMATCH"),
        ({"manifest_security_decision_ref": "plugin-manifest-security-decision:other"}, "PLUGIN_MANIFEST_SECURITY_BINDING_MISMATCH"),
        ({"manifest_ref": "plugin-manifest:other"}, "PLUGIN_MANIFEST_BINDING_MISMATCH"),
        ({"plugin_version": "2.0.0"}, "PLUGIN_VERSION_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "PLUGIN_ACTOR_BINDING_MISMATCH"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_builtin_plugin_execution_sandbox_decision(_request(**update))


def test_builtin_plugin_execution_sandbox_approval_refs_are_not_authority() -> None:
    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_PLUGIN_EXECUTION_AUTHORITY"):
        build_builtin_plugin_execution_sandbox_decision(_request(approval_ref="approval:m96-extra"))

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        BuiltInPluginExecutionSandboxRequest(
            **{
                **_request().model_dump(),
                "approval_test_ref": "approval_test_m96",
            }
        )

    with pytest.raises(ValueError, match="AUTHORITY_REF_NOT_PLUGIN_EXECUTION_AUTHORITY"):
        build_builtin_plugin_execution_sandbox_decision(
            _request(authority_refs=["context-pack:m96"]),
        )


def test_builtin_plugin_execution_sandbox_revalidates_model_copy_mutated_inputs() -> None:
    install_decision = _install_review_decision().model_copy(
        update={"plugin_execution_enabled": True}
    )

    with pytest.raises(ValueError, match="PLUGIN_EXECUTION_DENIED"):
        build_builtin_plugin_execution_sandbox_decision(
            _request(install_review_decision=install_decision)
        )


def test_builtin_plugin_execution_sandbox_revalidates_decision_and_receipt_flags() -> None:
    decision = build_builtin_plugin_execution_sandbox_decision(_request())
    for update, reason in [
        ({"external_plugin_loading_allowed": True}, "EXTERNAL_PLUGIN_LOADING_DENIED"),
        ({"arbitrary_plugin_code_allowed": True}, "ARBITRARY_PLUGIN_CODE_DENIED"),
        ({"networked_plugin_fetch_allowed": True}, "NETWORKED_PLUGIN_FETCH_DENIED"),
        ({"shell_execution_allowed": True}, "SHELL_EXECUTION_DENIED"),
        ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_builtin_plugin_execution_sandbox_decision(decision.model_copy(update=update))

    with pytest.raises(ValueError, match="RAW_PLUGIN_PAYLOAD_DENIED"):
        validate_builtin_plugin_execution_sandbox_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_plugin_payload": True}
                    )
                }
            )
        )


def test_builtin_plugin_execution_sandbox_policy_enforces_allowlists_and_sandbox() -> None:
    policy = validate_builtin_plugin_execution_sandbox_policy()
    assert policy.builtin_test_plugin_only is True
    assert policy.allowed_plugin_refs == ("plugin:m96-built-in-test-noop",)

    with pytest.raises(ValueError, match="EXTERNAL_PLUGIN_LOADING_DENIED"):
        validate_builtin_plugin_execution_sandbox_policy(
            BuiltInPluginExecutionSandboxPolicy(external_plugin_loading_allowed=True)
        )

    with pytest.raises(ValueError, match="BUILTIN_PLUGIN_ALLOWLIST_REQUIRED"):
        validate_builtin_plugin_execution_sandbox_policy(
            BuiltInPluginExecutionSandboxPolicy(allowed_plugin_refs=())
        )


def test_builtin_plugin_execution_sandbox_secret_like_metadata_denied() -> None:
    with pytest.raises(ValueError):
        validate_builtin_plugin_execution_sandbox_request(
            _request(metadata={"api_key": "not-allowed"})
        )
