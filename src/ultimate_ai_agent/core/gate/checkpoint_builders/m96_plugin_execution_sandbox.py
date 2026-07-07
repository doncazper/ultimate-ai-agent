from __future__ import annotations
from typing import Any
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


def _manifest_security_decision() -> Any:
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


def _install_review_decision() -> Any:
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


def _request(**overrides: Any) -> Any:
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
