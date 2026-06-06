import re
from collections.abc import Mapping
from typing import Any

from ultimate_ai_agent.core.plugin_manifest.contracts import (
    PluginManifestApprovalBinding,
    PluginManifestDeclaredPermission,
    PluginManifestReceiptPlan,
    PluginManifestSecurityDecision,
    PluginManifestSecurityPolicy,
    PluginManifestSecurityReviewRequest,
)
from ultimate_ai_agent.core.plugin_manifest.enums import PluginManifestRiskLevel


SECRET_FRAGMENT = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|cookie|credential|oauth|password|private[_-]?key|secret|session|token)"
)
SAFE_REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:/-]*$")


def validate_plugin_manifest_security_policy(
    policy: PluginManifestSecurityPolicy | None = None,
) -> PluginManifestSecurityPolicy:
    active = policy or PluginManifestSecurityPolicy()
    _assert_safe_ref(active.policy_ref)
    _assert_safe_collection(active.docs_refs)
    _assert_safe_collection(active.metadata_refs)
    _assert_safe_metadata(active.metadata)
    if not active.plugin_manifest_security_model_enabled:
        raise ValueError("PLUGIN_MANIFEST_SECURITY_MODEL_REQUIRED")
    _deny(active.plugin_install_enabled, "PLUGIN_INSTALL_DENIED")
    _deny(active.plugin_enablement_enabled, "PLUGIN_ENABLEMENT_DENIED")
    _deny(active.plugin_execution_enabled, "PLUGIN_EXECUTION_DENIED")
    _deny(active.runtime_import_enabled, "PLUGIN_RUNTIME_IMPORT_DENIED")
    _deny(active.network_access_enabled, "PLUGIN_NETWORK_ACCESS_DENIED")
    _deny(active.model_provider_call_enabled, "PLUGIN_MODEL_PROVIDER_CALL_DENIED")
    _deny(active.browser_automation_enabled, "PLUGIN_BROWSER_AUTOMATION_DENIED")
    _deny(active.shell_execution_enabled, "PLUGIN_SHELL_EXECUTION_DENIED")
    _deny(active.mobile_device_access_enabled, "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED")
    _deny(active.remote_execution_enabled, "PLUGIN_REMOTE_EXECUTION_DENIED")
    _deny(active.credential_cookie_access_enabled, "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED")
    _deny(active.raw_prompt_exposure_enabled, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(active.raw_provider_payload_exposure_enabled, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(active.production_authority_enabled, "PRODUCTION_AUTHORITY_DENIED")
    for field_name in (
        "source_provenance_required",
        "declared_permissions_required",
        "static_review_required",
        "sandbox_test_plan_required",
        "tool_broker_mapping_required",
        "event_ledger_plan_required",
        "version_pin_required",
        "revocation_plan_required",
        "high_risk_human_approval_required",
    ):
        if not getattr(active, field_name):
            raise ValueError(f"{field_name.upper()}_REQUIRED")
    return active


def validate_plugin_manifest_permission(
    permission: PluginManifestDeclaredPermission,
) -> PluginManifestDeclaredPermission:
    _assert_safe_ref(permission.permission_ref)
    _assert_safe_ref(permission.tool_broker_capability_ref)
    _assert_safe_text(permission.safe_purpose)
    _assert_safe_collection(permission.scope_refs)
    _assert_safe_collection(permission.metadata_refs)
    if permission.risk_level == PluginManifestRiskLevel.forbidden:
        raise ValueError("FORBIDDEN_PLUGIN_PERMISSION_DENIED")
    return permission


def validate_plugin_manifest_security_request(
    request: PluginManifestSecurityReviewRequest,
    policy: PluginManifestSecurityPolicy | None = None,
) -> PluginManifestSecurityReviewRequest:
    active_policy = validate_plugin_manifest_security_policy(policy)
    _assert_safe_ref(request.review_request_ref)
    _assert_safe_ref(request.manifest_ref)
    _assert_safe_ref(request.plugin_ref)
    _assert_safe_ref(request.plugin_version)
    _assert_safe_ref(request.actor_ref)
    _assert_safe_text(request.plugin_name)
    _assert_safe_text(request.safe_manifest_summary)
    _assert_safe_collection(request.metadata_refs)
    _assert_safe_metadata(request.metadata)

    if request.approval_ref and request.approval_ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if active_policy.source_provenance_required and not request.source_ref:
        raise ValueError("PLUGIN_SOURCE_REF_REQUIRED")
    if active_policy.source_provenance_required and not request.provenance_ref:
        raise ValueError("PLUGIN_PROVENANCE_REF_REQUIRED")
    if active_policy.declared_permissions_required and not request.declared_permissions:
        raise ValueError("DECLARED_PERMISSIONS_REQUIRED")
    if active_policy.static_review_required and not request.static_review_ref:
        raise ValueError("PLUGIN_STATIC_REVIEW_REQUIRED")
    if active_policy.sandbox_test_plan_required and not request.sandbox_test_plan_ref:
        raise ValueError("PLUGIN_SANDBOX_TEST_PLAN_REQUIRED")
    if active_policy.tool_broker_mapping_required and not request.tool_broker_mapping_ref:
        raise ValueError("TOOL_BROKER_MAPPING_REQUIRED")
    if active_policy.event_ledger_plan_required and not request.event_ledger_plan_ref:
        raise ValueError("EVENT_LEDGER_PLAN_REQUIRED")
    if active_policy.version_pin_required and not request.version_pin_ref:
        raise ValueError("PLUGIN_VERSION_PIN_REQUIRED")
    if active_policy.revocation_plan_required and not request.revocation_plan_ref:
        raise ValueError("PLUGIN_REVOCATION_PLAN_REQUIRED")

    for ref in (
        request.source_ref,
        request.provenance_ref,
        request.static_review_ref,
        request.sandbox_test_plan_ref,
        request.tool_broker_mapping_ref,
        request.event_ledger_plan_ref,
        request.version_pin_ref,
        request.revocation_plan_ref,
    ):
        if ref:
            _assert_safe_ref(ref)
    for permission in request.declared_permissions:
        validate_plugin_manifest_permission(permission)

    _deny(request.plugin_install_requested, "PLUGIN_INSTALL_DENIED")
    _deny(request.plugin_enablement_requested, "PLUGIN_ENABLEMENT_DENIED")
    _deny(request.plugin_execution_requested, "PLUGIN_EXECUTION_DENIED")
    _deny(request.runtime_import_requested, "PLUGIN_RUNTIME_IMPORT_DENIED")
    _deny(request.network_access_requested, "PLUGIN_NETWORK_ACCESS_DENIED")
    _deny(request.model_provider_call_requested, "PLUGIN_MODEL_PROVIDER_CALL_DENIED")
    _deny(request.browser_automation_requested, "PLUGIN_BROWSER_AUTOMATION_DENIED")
    _deny(request.shell_execution_requested, "PLUGIN_SHELL_EXECUTION_DENIED")
    _deny(request.mobile_device_access_requested, "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED")
    _deny(request.remote_execution_requested, "PLUGIN_REMOTE_EXECUTION_DENIED")
    _deny(request.credential_cookie_access_requested, "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED")
    _deny(request.raw_prompt_exposure_requested, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(request.raw_provider_payload_exposure_requested, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(request.production_authority_requested, "PRODUCTION_AUTHORITY_DENIED")
    _deny(request.model_output_authority_claimed, "MODEL_OUTPUT_AUTHORITY_DENIED")
    _deny(request.openwebui_output_authority_claimed, "OPENWEBUI_OUTPUT_AUTHORITY_DENIED")

    if _requires_human_approval(request):
        if request.human_approval is None:
            raise ValueError("HIGH_RISK_PLUGIN_APPROVAL_REQUIRED")
        validate_plugin_manifest_approval_binding(request.human_approval, request)
    elif request.human_approval is not None:
        validate_plugin_manifest_approval_binding(request.human_approval, request)
    return request


def validate_plugin_manifest_approval_binding(
    approval: PluginManifestApprovalBinding,
    request: PluginManifestSecurityReviewRequest,
) -> PluginManifestApprovalBinding:
    _assert_safe_ref(approval.approval_ref)
    _assert_safe_ref(approval.approved_manifest_ref)
    _assert_safe_ref(approval.approved_plugin_ref)
    _assert_safe_ref(approval.approved_version)
    _assert_safe_ref(approval.approved_actor_ref)
    _assert_safe_collection(approval.metadata_refs)
    if approval.approval_ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if (
        approval.approved_manifest_ref != request.manifest_ref
        or approval.approved_plugin_ref != request.plugin_ref
        or approval.approved_version != request.plugin_version
        or approval.approved_actor_ref != request.actor_ref
    ):
        raise ValueError("APPROVAL_BINDING_MISMATCH")
    _deny(approval.approval_expired, "APPROVAL_EXPIRED_DENIED")
    _deny(approval.approval_revoked, "APPROVAL_REVOKED_DENIED")
    _deny(approval.approval_replayed, "APPROVAL_REPLAY_DENIED")
    return approval


def validate_plugin_manifest_receipt_plan(
    receipt: PluginManifestReceiptPlan,
) -> PluginManifestReceiptPlan:
    for ref in (
        receipt.receipt_plan_ref,
        receipt.review_request_ref,
        receipt.manifest_ref,
        receipt.plugin_ref,
        receipt.plugin_version,
        receipt.static_review_ref,
        receipt.sandbox_test_plan_ref,
        receipt.tool_broker_mapping_ref,
        receipt.event_ledger_plan_ref,
        receipt.version_pin_ref,
        receipt.revocation_plan_ref,
    ):
        _assert_safe_ref(ref)
    _assert_safe_text(receipt.safe_summary)
    _assert_safe_collection(receipt.metadata_refs)
    if not receipt.revocation_supported:
        raise ValueError("PLUGIN_REVOCATION_PLAN_REQUIRED")
    _deny(receipt.plugin_install_performed, "PLUGIN_INSTALL_DENIED")
    _deny(receipt.plugin_enablement_performed, "PLUGIN_ENABLEMENT_DENIED")
    _deny(receipt.plugin_execution_performed, "PLUGIN_EXECUTION_DENIED")
    _deny(receipt.raw_manifest_content_stored, "RAW_MANIFEST_CONTENT_DENIED")
    if receipt.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    return receipt


def validate_plugin_manifest_security_decision(
    decision: PluginManifestSecurityDecision,
) -> PluginManifestSecurityDecision:
    for ref in (
        decision.decision_ref,
        decision.review_request_ref,
        decision.manifest_ref,
        decision.plugin_ref,
        decision.plugin_version,
        decision.actor_ref,
    ):
        _assert_safe_ref(ref)
    _assert_safe_text(decision.safe_message)
    _assert_safe_collection(decision.reason_codes)
    _assert_safe_collection(decision.docs_refs)
    _assert_safe_collection(decision.metadata_refs)
    validate_plugin_manifest_receipt_plan(decision.receipt_plan)
    if not decision.manifest_reviewed:
        raise ValueError("PLUGIN_STATIC_REVIEW_REQUIRED")
    _deny(decision.plugin_install_enabled, "PLUGIN_INSTALL_DENIED")
    _deny(decision.plugin_enablement_enabled, "PLUGIN_ENABLEMENT_DENIED")
    _deny(decision.plugin_execution_enabled, "PLUGIN_EXECUTION_DENIED")
    _deny(decision.runtime_import_enabled, "PLUGIN_RUNTIME_IMPORT_DENIED")
    _deny(decision.network_access_enabled, "PLUGIN_NETWORK_ACCESS_DENIED")
    _deny(decision.model_provider_call_enabled, "PLUGIN_MODEL_PROVIDER_CALL_DENIED")
    _deny(decision.browser_automation_enabled, "PLUGIN_BROWSER_AUTOMATION_DENIED")
    _deny(decision.shell_execution_enabled, "PLUGIN_SHELL_EXECUTION_DENIED")
    _deny(decision.mobile_device_access_enabled, "PLUGIN_MOBILE_DEVICE_ACCESS_DENIED")
    _deny(decision.remote_execution_enabled, "PLUGIN_REMOTE_EXECUTION_DENIED")
    _deny(decision.credential_cookie_access_enabled, "PLUGIN_CREDENTIAL_COOKIE_ACCESS_DENIED")
    _deny(decision.raw_prompt_exposure_enabled, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(decision.raw_provider_payload_exposure_enabled, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(decision.production_authority_granted, "PRODUCTION_AUTHORITY_DENIED")
    if decision.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    return decision


def _requires_human_approval(request: PluginManifestSecurityReviewRequest) -> bool:
    return any(
        permission.risk_level in {PluginManifestRiskLevel.high, PluginManifestRiskLevel.critical}
        for permission in request.declared_permissions
    )


def _deny(value: bool, reason: str) -> None:
    if value:
        raise ValueError(reason)


def _assert_safe_ref(value: str) -> None:
    if SECRET_FRAGMENT.search(value) or not SAFE_REF.match(value):
        raise ValueError("UNSAFE_PLUGIN_REF_DENIED")


def _assert_safe_text(value: str) -> None:
    if SECRET_FRAGMENT.search(value):
        raise ValueError("SECRET_LIKE_PLUGIN_TEXT_DENIED")


def _assert_safe_collection(values: list[str]) -> None:
    for value in values:
        _assert_safe_ref(value)


def _assert_safe_metadata(metadata: Mapping[str, Any]) -> None:
    for key, value in metadata.items():
        if SECRET_FRAGMENT.search(str(key)) or SECRET_FRAGMENT.search(str(value)):
            raise ValueError("SECRET_LIKE_PLUGIN_METADATA_DENIED")
