import re
from collections.abc import Mapping
from typing import Any

from ultimate_ai_agent.core.plugin_install_review.contracts import (
    PluginInstallReviewApprovalBinding,
    PluginInstallReviewDecision,
    PluginInstallReviewPolicy,
    PluginInstallReviewReceiptPlan,
    PluginInstallReviewRequest,
)
from ultimate_ai_agent.core.plugin_manifest.enums import PluginManifestSecurityDecisionStatus
from ultimate_ai_agent.core.plugin_manifest.validation import (
    validate_plugin_manifest_security_decision,
)


SECRET_FRAGMENT = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|cookie|credential|oauth|password|private[_-]?key|secret|session|token)"
)
SAFE_REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:/-]*$")


def validate_plugin_install_review_policy(
    policy: PluginInstallReviewPolicy | None = None,
) -> PluginInstallReviewPolicy:
    active = policy or PluginInstallReviewPolicy()
    _assert_safe_ref(active.policy_ref)
    _assert_safe_collection(active.docs_refs)
    _assert_safe_collection(active.metadata_refs)
    _assert_safe_metadata(active.metadata)
    if not active.plugin_install_review_enabled:
        raise ValueError("PLUGIN_INSTALL_REVIEW_REQUIRED")
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
    _deny(active.raw_manifest_content_enabled, "RAW_MANIFEST_CONTENT_DENIED")
    _deny(active.raw_package_content_enabled, "RAW_PACKAGE_CONTENT_DENIED")
    _deny(active.raw_prompt_exposure_enabled, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(active.raw_provider_payload_exposure_enabled, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(active.production_authority_enabled, "PRODUCTION_AUTHORITY_DENIED")
    for field_name in (
        "manifest_security_decision_required",
        "source_package_ref_required",
        "provenance_ref_required",
        "static_review_required",
        "sandbox_test_plan_required",
        "tool_broker_mapping_required",
        "event_ledger_plan_required",
        "version_pin_required",
        "revocation_plan_required",
        "exact_approval_required",
    ):
        if not getattr(active, field_name):
            raise ValueError(f"{field_name.upper()}_REQUIRED")
    return active


def validate_plugin_install_review_request(
    request: PluginInstallReviewRequest,
    policy: PluginInstallReviewPolicy | None = None,
) -> PluginInstallReviewRequest:
    active_policy = validate_plugin_install_review_policy(policy)
    validate_plugin_manifest_security_decision(request.manifest_security_decision)
    if (
        request.manifest_security_decision.status
        != PluginManifestSecurityDecisionStatus.review_ready_disabled
    ):
        raise ValueError("PLUGIN_MANIFEST_SECURITY_DECISION_REQUIRED")
    _assert_safe_ref(request.install_review_request_ref)
    _assert_safe_ref(request.manifest_ref)
    _assert_safe_ref(request.plugin_ref)
    _assert_safe_ref(request.plugin_version)
    _assert_safe_ref(request.actor_ref)
    _assert_safe_text(request.safe_install_review_summary)
    _assert_safe_collection(request.metadata_refs)
    _assert_safe_metadata(request.metadata)

    if request.approval_ref and request.approval_ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if active_policy.source_package_ref_required and not request.source_package_ref:
        raise ValueError("PLUGIN_SOURCE_PACKAGE_REF_REQUIRED")
    if active_policy.provenance_ref_required and not request.provenance_ref:
        raise ValueError("PLUGIN_PROVENANCE_REF_REQUIRED")
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
    if active_policy.exact_approval_required and request.approval is None:
        raise ValueError("PLUGIN_INSTALL_REVIEW_APPROVAL_REQUIRED")

    _assert_manifest_decision_binding(request)
    for ref in (
        request.source_package_ref,
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
    _deny(request.raw_manifest_content_requested, "RAW_MANIFEST_CONTENT_DENIED")
    _deny(request.raw_package_content_requested, "RAW_PACKAGE_CONTENT_DENIED")
    _deny(request.raw_prompt_exposure_requested, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(request.raw_provider_payload_exposure_requested, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(request.production_authority_requested, "PRODUCTION_AUTHORITY_DENIED")
    _deny(request.model_output_authority_claimed, "MODEL_OUTPUT_AUTHORITY_DENIED")
    _deny(request.openwebui_output_authority_claimed, "OPENWEBUI_OUTPUT_AUTHORITY_DENIED")

    if request.approval is not None:
        validate_plugin_install_review_approval_binding(request.approval, request)
    return request


def validate_plugin_install_review_approval_binding(
    approval: PluginInstallReviewApprovalBinding,
    request: PluginInstallReviewRequest,
) -> PluginInstallReviewApprovalBinding:
    for ref in (
        approval.approval_ref,
        approval.approved_install_review_request_ref,
        approval.approved_manifest_security_decision_ref,
        approval.approved_manifest_ref,
        approval.approved_plugin_ref,
        approval.approved_version,
        approval.approved_actor_ref,
    ):
        _assert_safe_ref(ref)
    _assert_safe_collection(approval.metadata_refs)
    if approval.approval_ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if (
        approval.approved_install_review_request_ref != request.install_review_request_ref
        or approval.approved_manifest_security_decision_ref
        != request.manifest_security_decision.decision_ref
        or approval.approved_manifest_ref != request.manifest_ref
        or approval.approved_plugin_ref != request.plugin_ref
        or approval.approved_version != request.plugin_version
        or approval.approved_actor_ref != request.actor_ref
    ):
        raise ValueError("APPROVAL_BINDING_MISMATCH")
    _deny(approval.approval_expired, "APPROVAL_EXPIRED_DENIED")
    _deny(approval.approval_revoked, "APPROVAL_REVOKED_DENIED")
    _deny(approval.approval_replayed, "APPROVAL_REPLAY_DENIED")
    return approval


def validate_plugin_install_review_receipt_plan(
    receipt: PluginInstallReviewReceiptPlan,
) -> PluginInstallReviewReceiptPlan:
    for ref in (
        receipt.receipt_plan_ref,
        receipt.install_review_request_ref,
        receipt.manifest_security_decision_ref,
        receipt.manifest_ref,
        receipt.plugin_ref,
        receipt.plugin_version,
        receipt.source_package_ref,
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
    _deny(receipt.plugin_install_performed, "PLUGIN_INSTALL_DENIED")
    _deny(receipt.plugin_enablement_performed, "PLUGIN_ENABLEMENT_DENIED")
    _deny(receipt.plugin_execution_performed, "PLUGIN_EXECUTION_DENIED")
    _deny(receipt.runtime_import_performed, "PLUGIN_RUNTIME_IMPORT_DENIED")
    _deny(receipt.raw_manifest_content_stored, "RAW_MANIFEST_CONTENT_DENIED")
    _deny(receipt.raw_package_content_stored, "RAW_PACKAGE_CONTENT_DENIED")
    if receipt.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    return receipt


def validate_plugin_install_review_decision(
    decision: PluginInstallReviewDecision,
) -> PluginInstallReviewDecision:
    for ref in (
        decision.decision_ref,
        decision.install_review_request_ref,
        decision.manifest_security_decision_ref,
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
    validate_plugin_install_review_receipt_plan(decision.receipt_plan)
    if not decision.install_reviewed:
        raise ValueError("PLUGIN_INSTALL_REVIEW_REQUIRED")
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
    _deny(decision.raw_manifest_content_returned, "RAW_MANIFEST_CONTENT_DENIED")
    _deny(decision.raw_package_content_returned, "RAW_PACKAGE_CONTENT_DENIED")
    _deny(decision.raw_prompt_exposure_enabled, "RAW_PROMPT_EXPOSURE_DENIED")
    _deny(decision.raw_provider_payload_exposure_enabled, "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED")
    _deny(decision.production_authority_granted, "PRODUCTION_AUTHORITY_DENIED")
    if decision.side_effects_performed:
        raise ValueError("PLUGIN_SIDE_EFFECTS_DENIED")
    return decision


def _assert_manifest_decision_binding(request: PluginInstallReviewRequest) -> None:
    decision = request.manifest_security_decision
    if (
        decision.manifest_ref != request.manifest_ref
        or decision.plugin_ref != request.plugin_ref
        or decision.plugin_version != request.plugin_version
        or decision.actor_ref != request.actor_ref
    ):
        raise ValueError("PLUGIN_MANIFEST_SECURITY_DECISION_BINDING_MISMATCH")


def _deny(value: bool, reason: str) -> None:
    if value:
        raise ValueError(reason)


def _assert_safe_ref(value: str) -> None:
    if SECRET_FRAGMENT.search(value) or not SAFE_REF.match(value):
        raise ValueError("UNSAFE_PLUGIN_INSTALL_REF_DENIED")


def _assert_safe_text(value: str) -> None:
    if SECRET_FRAGMENT.search(value):
        raise ValueError("SECRET_LIKE_PLUGIN_INSTALL_TEXT_DENIED")


def _assert_safe_collection(values: list[str]) -> None:
    for value in values:
        _assert_safe_ref(value)


def _assert_safe_metadata(metadata: Mapping[str, Any]) -> None:
    for key, value in metadata.items():
        if SECRET_FRAGMENT.search(str(key)) or SECRET_FRAGMENT.search(str(value)):
            raise ValueError("SECRET_LIKE_PLUGIN_INSTALL_METADATA_DENIED")
