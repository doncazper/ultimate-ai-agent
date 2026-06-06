from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.plugin_manifest.enums import (
    PluginManifestPermissionKind,
    PluginManifestReviewStage,
    PluginManifestRiskLevel,
    PluginManifestSecurityDecisionStatus,
)


class _PluginManifestModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class PluginManifestDeclaredPermission(_PluginManifestModel):
    permission_ref: str = Field(..., min_length=1)
    kind: PluginManifestPermissionKind
    risk_level: PluginManifestRiskLevel = PluginManifestRiskLevel.low
    safe_purpose: str = Field(..., min_length=1)
    tool_broker_capability_ref: str = Field(..., min_length=1)
    scope_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)

    @field_validator("scope_refs", "metadata_refs")
    @classmethod
    def _copy_refs(cls, value: list[str]) -> list[str]:
        return list(value)


class PluginManifestApprovalBinding(_PluginManifestModel):
    approval_ref: str = Field(..., min_length=1)
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


class PluginManifestSecurityPolicy(_PluginManifestModel):
    policy_ref: str = "plugin-manifest-security-policy:m78"
    baseline_version: str = "0.82.0"
    stage: PluginManifestReviewStage = PluginManifestReviewStage.security_model_only
    plugin_manifest_security_model_enabled: bool = True
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
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    production_authority_enabled: bool = False
    source_provenance_required: bool = True
    declared_permissions_required: bool = True
    static_review_required: bool = True
    sandbox_test_plan_required: bool = True
    tool_broker_mapping_required: bool = True
    event_ledger_plan_required: bool = True
    version_pin_required: bool = True
    revocation_plan_required: bool = True
    high_risk_human_approval_required: bool = True
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginManifestSecurityReviewRequest(_PluginManifestModel):
    review_request_ref: str = Field(..., min_length=1)
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_name: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    source_ref: str | None = Field(default=None)
    provenance_ref: str | None = Field(default=None)
    declared_permissions: list[PluginManifestDeclaredPermission] = Field(default_factory=list)
    static_review_ref: str | None = Field(default=None)
    sandbox_test_plan_ref: str | None = Field(default=None)
    tool_broker_mapping_ref: str | None = Field(default=None)
    event_ledger_plan_ref: str | None = Field(default=None)
    version_pin_ref: str | None = Field(default=None)
    revocation_plan_ref: str | None = Field(default=None)
    human_approval: PluginManifestApprovalBinding | None = None
    approval_ref: str | None = None
    safe_manifest_summary: str = Field(..., min_length=1)
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
    raw_prompt_exposure_requested: bool = False
    raw_provider_payload_exposure_requested: bool = False
    production_authority_requested: bool = False
    model_output_authority_claimed: bool = False
    openwebui_output_authority_claimed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PluginManifestReceiptPlan(_PluginManifestModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    review_request_ref: str = Field(..., min_length=1)
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    static_review_ref: str = Field(..., min_length=1)
    sandbox_test_plan_ref: str = Field(..., min_length=1)
    tool_broker_mapping_ref: str = Field(..., min_length=1)
    event_ledger_plan_ref: str = Field(..., min_length=1)
    version_pin_ref: str = Field(..., min_length=1)
    revocation_plan_ref: str = Field(..., min_length=1)
    revocation_supported: bool = True
    plugin_install_performed: bool = False
    plugin_enablement_performed: bool = False
    plugin_execution_performed: bool = False
    raw_manifest_content_stored: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)


class PluginManifestSecurityDecision(_PluginManifestModel):
    decision_ref: str = Field(..., min_length=1)
    review_request_ref: str = Field(..., min_length=1)
    manifest_ref: str = Field(..., min_length=1)
    plugin_ref: str = Field(..., min_length=1)
    plugin_version: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    status: PluginManifestSecurityDecisionStatus = (
        PluginManifestSecurityDecisionStatus.review_ready_disabled
    )
    manifest_reviewed: bool = True
    safe_message: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    receipt_plan: PluginManifestReceiptPlan
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
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
