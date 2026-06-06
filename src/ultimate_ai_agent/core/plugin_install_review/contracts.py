from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.plugin_install_review.enums import (
    PluginInstallReviewDecisionStatus,
)
from ultimate_ai_agent.core.plugin_manifest.contracts import PluginManifestSecurityDecision


class _PluginInstallReviewModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class PluginInstallReviewApprovalBinding(_PluginInstallReviewModel):
    approval_ref: str = Field(..., min_length=1)
    approved_install_review_request_ref: str = Field(..., min_length=1)
    approved_manifest_security_decision_ref: str = Field(..., min_length=1)
    approved_manifest_ref: str = Field(..., min_length=1)
    approved_plugin_ref: str = Field(..., min_length=1)
    approved_version: str = Field(..., min_length=1)
    approved_actor_ref: str = Field(..., min_length=1)
    approval_expired: bool = False
    approval_revoked: bool = False
    approval_replayed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)

    @field_validator("metadata_refs")
    @classmethod
    def _copy_refs(cls, value: list[str]) -> list[str]:
        return list(value)


class PluginInstallReviewPolicy(_PluginInstallReviewModel):
    policy_ref: str = "plugin-install-review-policy:m79"
    baseline_version: str = "0.83.0"
    plugin_install_review_enabled: bool = True
    plugin_install_enabled: bool = False
    plugin_enablement_enabled: bool = False
    plugin_execution_enabled: bool = False
    runtime_import_enabled: bool = False
    network_access_enabled: bool = False
    model_provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    shell_execution_enabled: bool = False
    mobile_device_access_enabled: bool = False
    remote_execution_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    raw_manifest_content_enabled: bool = False
    raw_package_content_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    production_authority_enabled: bool = False
    manifest_security_decision_required: bool = True
    source_package_ref_required: bool = True
    provenance_ref_required: bool = True
    static_review_required: bool = True
    sandbox_test_plan_required: bool = True
    tool_broker_mapping_required: bool = True
    event_ledger_plan_required: bool = True
    version_pin_required: bool = True
    revocation_plan_required: bool = True
    exact_approval_required: bool = True
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginInstallReviewRequest(_PluginInstallReviewModel):
    install_review_request_ref: str = Field(..., min_length=1)
    manifest_security_decision: PluginManifestSecurityDecision
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    source_package_ref: str | None = Field(default=None)
    provenance_ref: str | None = Field(default=None)
    static_review_ref: str | None = Field(default=None)
    sandbox_test_plan_ref: str | None = Field(default=None)
    tool_broker_mapping_ref: str | None = Field(default=None)
    event_ledger_plan_ref: str | None = Field(default=None)
    version_pin_ref: str | None = Field(default=None)
    revocation_plan_ref: str | None = Field(default=None)
    approval: PluginInstallReviewApprovalBinding | None = None
    approval_ref: str | None = None
    safe_install_review_summary: str = Field(..., min_length=1)
    plugin_install_requested: bool = False
    plugin_enablement_requested: bool = False
    plugin_execution_requested: bool = False
    runtime_import_requested: bool = False
    network_access_requested: bool = False
    model_provider_call_requested: bool = False
    browser_automation_requested: bool = False
    shell_execution_requested: bool = False
    mobile_device_access_requested: bool = False
    remote_execution_requested: bool = False
    credential_cookie_access_requested: bool = False
    raw_manifest_content_requested: bool = False
    raw_package_content_requested: bool = False
    raw_prompt_exposure_requested: bool = False
    raw_provider_payload_exposure_requested: bool = False
    production_authority_requested: bool = False
    model_output_authority_claimed: bool = False
    openwebui_output_authority_claimed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginInstallReviewReceiptPlan(_PluginInstallReviewModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    install_review_request_ref: str = Field(..., min_length=1)
    manifest_security_decision_ref: str = Field(..., min_length=1)
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    source_package_ref: str = Field(..., min_length=1)
    static_review_ref: str = Field(..., min_length=1)
    sandbox_test_plan_ref: str = Field(..., min_length=1)
    tool_broker_mapping_ref: str = Field(..., min_length=1)
    event_ledger_plan_ref: str = Field(..., min_length=1)
    version_pin_ref: str = Field(..., min_length=1)
    revocation_plan_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    plugin_install_performed: bool = False
    plugin_enablement_performed: bool = False
    plugin_execution_performed: bool = False
    runtime_import_performed: bool = False
    raw_manifest_content_stored: bool = False
    raw_package_content_stored: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)


class PluginInstallReviewDecision(_PluginInstallReviewModel):
    decision_ref: str = Field(..., min_length=1)
    install_review_request_ref: str = Field(..., min_length=1)
    manifest_security_decision_ref: str = Field(..., min_length=1)
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    status: PluginInstallReviewDecisionStatus = (
        PluginInstallReviewDecisionStatus.install_review_ready_disabled
    )
    install_reviewed: bool = True
    safe_message: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    receipt_plan: PluginInstallReviewReceiptPlan
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plugin_install_enabled: bool = False
    plugin_enablement_enabled: bool = False
    plugin_execution_enabled: bool = False
    runtime_import_enabled: bool = False
    network_access_enabled: bool = False
    model_provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    shell_execution_enabled: bool = False
    mobile_device_access_enabled: bool = False
    remote_execution_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    raw_manifest_content_returned: bool = False
    raw_package_content_returned: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
