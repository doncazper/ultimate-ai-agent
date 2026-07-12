from __future__ import annotations

import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationDecision
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
    authority_lease_kill_switch_engaged,
    authority_state_dir,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.plugin_install_review import (
    PluginInstallReviewApprovalBinding,
    PluginInstallReviewDecision,
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
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager


SAFE_REF_PATTERN = r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_.:-]*$"
SHA256_PATTERN = r"^sha256:[a-f0-9]{64}$"
EXTENSION_INSTALL_DISABLED_ACTION_REF = (
    "authority-action-ref:extension-install-disabled:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_REQUEST_REF = (
    "approval-request-ref:extension-install-disabled:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_RUN_REF = (
    "run-ref:extension-install-disabled:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_ACTOR_REF = "actor:extension-install-reviewer"
EXTENSION_INSTALL_DISABLED_RECORD_REF = (
    "extension-install-disabled-record:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_REF = (
    "idempotency-ref:extension-install-disabled:uaa-plugin-skill-boundary:v1"
)
EXTENSION_INSTALL_DISABLED_RECEIPT_REF = (
    "receipt-ref:extension-install-disabled:uaa-plugin-skill-boundary:v1"
)
EXTENSION_INSTALL_DISABLED_STORAGE_EFFECT_REF = (
    "side-effect:extension-install-disabled:local-record-write"
)
EXTENSION_INSTALL_DISABLED_DELETE_ACTION_REF = (
    "authority-action-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_DELETE_REQUEST_REF = (
    "approval-request-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_DELETE_RUN_REF = (
    "run-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary"
)
EXTENSION_INSTALL_DISABLED_DELETE_IDEMPOTENCY_REF = (
    "idempotency-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary:v1"
)
EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_REF = (
    "receipt-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary:v1"
)
EXTENSION_INSTALL_DISABLED_DELETE_EFFECT_REF = (
    "side-effect:extension-install-disabled:local-record-delete"
)
EXTENSION_INSTALL_DISABLED_DELETE_NOOP_EFFECT_REF = (
    "side-effect:extension-install-disabled:local-record-already-absent"
)
EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_EFFECT_REF = (
    "side-effect:extension-install-disabled:local-delete-receipt-write"
)
EXTENSION_INSTALL_DISABLED_MAX_RECORD_BYTES = 262_144
_EXPECTED_INSTALL_DISABLED_FILE_SHA256 = {
    "docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md": "ee4fa6782f7a3d95b8bc75322b723f4eb6227999f69f9de4cb7d5eb9cf4a8736",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md": "9f0191157a6680060cfc075efcdd1b72a48bb4f6516622bb44c7f148f60611c5",
    "docs/schemas/plugin_skill_trust_manifest.schema.json": "9c1d0fdfe45577f4510e6c1a90517f9789f58e523f90c006a2141d43db07bc46",
}
_HOSTNAME_RE = re.compile(
    r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|io|dev|app|local|internal)\b"
)


def _validate_durable_ref_value(value: str, *, field_name: str) -> None:
    if (
        re.fullmatch(SAFE_REF_PATTERN, value) is None
        or "/" in value
        or "\\" in value
        or "@" in value
        or "://" in value
        or _HOSTNAME_RE.search(value)
    ):
        raise ValueError("EXTENSION_INSTALL_DISABLED_UNSAFE_DURABLE_REF")
    forbidden_namespace = value.split(":", 1)[0]
    if forbidden_namespace in {
        "api-key",
        "credential",
        "key",
        "password",
        "secret",
        "token",
    }:
        raise ValueError("EXTENSION_INSTALL_DISABLED_SECRET_NAMESPACE_DENIED")
    required_prefixes = {
        "approval_ref": "approval-ref:",
        "approval_request_ref": "approval-request-ref:",
        "idempotency_key_ref": "idempotency-ref:",
    }
    required_prefix = required_prefixes.get(field_name)
    if required_prefix is not None and not value.startswith(required_prefix):
        raise ValueError("EXTENSION_INSTALL_DISABLED_REF_NAMESPACE_INVALID")


def _validate_durable_refs(payload: object, *, field_name: str = "") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _validate_durable_refs(value, field_name=str(key))
        return
    if isinstance(payload, list):
        for value in payload:
            _validate_durable_refs(value, field_name=field_name)
        return
    if isinstance(payload, str) and (
        field_name.endswith("_ref") or field_name.endswith("_refs")
    ):
        _validate_durable_ref_value(payload, field_name=field_name)


class _ExtensionInstallDisabledModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        protected_namespaces=(),
    )

    @model_validator(mode="after")
    def validate_durable_safe_refs(self) -> "_ExtensionInstallDisabledModel":
        payload = self.model_dump(mode="python")
        _validate_durable_refs(payload)
        if contains_secret_like(payload) or contains_obvious_secret(payload):
            raise ValueError("EXTENSION_INSTALL_DISABLED_SECRET_LIKE_PAYLOAD_DENIED")
        return self


class ExtensionInstallDisabledFileHash(_ExtensionInstallDisabledModel):
    file_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    hash_algorithm: Literal["sha256"] = "sha256"
    hash_value: str | None = Field(default=None, pattern=SHA256_PATTERN)
    hash_status: Literal["reviewed", "missing", "mismatch"] = "reviewed"


class ExtensionInstallDisabledCandidateRecord(_ExtensionInstallDisabledModel):
    schema_version: Literal["uaa_extension_install_disabled_candidate.v1"] = (
        "uaa_extension_install_disabled_candidate.v1"
    )
    candidate_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    catalog_entry_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    source_package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    provenance_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    static_review_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    sandbox_test_plan_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    tool_broker_mapping_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    event_ledger_plan_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_pin_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    revocation_plan_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    safe_disable_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    rollback_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_lane_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_decision_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_lease_ref: str | None = Field(default=None, pattern=SAFE_REF_PATTERN)
    authority_decision_outcome: AuthorityDecisionOutcome
    authority_decision_reason_refs: list[str] = Field(default_factory=list)
    required_mode: TrustMode = TrustMode.approved_safe_local_work_session
    required_domain: AuthorityDomain = AuthorityDomain.workspace
    required_capability: AuthorityCapability = AuthorityCapability.write
    manifest_security_decision_ref: str = Field(
        ..., min_length=1, pattern=SAFE_REF_PATTERN
    )
    install_review_decision_ref: str = Field(
        ..., min_length=1, pattern=SAFE_REF_PATTERN
    )
    receipt_plan_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    audit_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    file_hashes: list[ExtensionInstallDisabledFileHash] = Field(default_factory=list)
    blocked_capability_refs: list[str] = Field(default_factory=list)
    approval_request_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    approval_ref: str | None = Field(default=None, pattern=SAFE_REF_PATTERN)
    exact_approval_required: Literal[True] = True
    local_approval_validated: bool = False
    approval_validation_status: str = Field(..., min_length=1, max_length=80)
    approval_ref_authority: Literal[False] = False
    disabled_install_record_ready: bool = False
    disabled_install_record_persisted: Literal[False] = False
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    remote_execution_enabled: Literal[False] = False
    raw_manifest_content_stored: Literal[False] = False
    raw_package_content_stored: Literal[False] = False
    production_authority_granted: Literal[False] = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_candidate(self) -> "ExtensionInstallDisabledCandidateRecord":
        _validate_safe_ref_list(
            [
                *self.authority_decision_reason_refs,
                *self.audit_refs,
                *self.receipt_refs,
                *self.blocked_capability_refs,
            ],
            "extension_install_disabled_ref",
        )
        if self.local_approval_validated and not self.approval_ref:
            raise ValueError("EXTENSION_INSTALL_DISABLED_APPROVAL_REF_REQUIRED")
        if self.disabled_install_record_ready and (
            not self.local_approval_validated
            or self.authority_decision_outcome != AuthorityDecisionOutcome.allow.value
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_READY_REQUIRES_AUTHORITY")
        file_refs = [item.file_ref for item in self.file_hashes]
        if len(file_refs) != len(set(file_refs)):
            raise ValueError("EXTENSION_INSTALL_DISABLED_DUPLICATE_FILE_REF")
        if any(
            item.hash_status == "reviewed" and item.hash_value is None
            for item in self.file_hashes
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_REVIEWED_HASH_REQUIRED")
        if self.disabled_install_record_ready and any(
            item.hash_status != "reviewed" for item in self.file_hashes
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_PINNED_HASHES_REQUIRED")
        _deny_runtime_flags(self)
        return self


class ExtensionInstallDisabledPostureReadModel(_ExtensionInstallDisabledModel):
    schema_version: Literal["uaa_extension_install_disabled_posture.v1"] = (
        "uaa_extension_install_disabled_posture.v1"
    )
    posture_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: Literal[
        "blocked_pending_authority_and_approval",
        "review_ready_disabled_not_persisted",
    ]
    candidate_count: int = Field(..., ge=0)
    candidates: list[ExtensionInstallDisabledCandidateRecord] = Field(
        default_factory=list
    )
    required_authority_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    required_approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    verifier_refs: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_refs_only: Literal[True] = True
    read_only: Literal[True] = True
    install_disabled_posture_enabled: Literal[True] = True
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    remote_execution_enabled: Literal[False] = False
    raw_manifest_content_stored: Literal[False] = False
    raw_package_content_stored: Literal[False] = False
    production_authority_granted: Literal[False] = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=640)

    @model_validator(mode="after")
    def validate_posture(self) -> "ExtensionInstallDisabledPostureReadModel":
        if self.candidate_count != len(self.candidates):
            raise ValueError("EXTENSION_INSTALL_DISABLED_CANDIDATE_COUNT_DRIFT")
        _validate_safe_ref_list(
            [
                *self.verifier_refs,
                *self.docs_refs,
                *self.next_safe_action_refs,
                *self.blocked_authority_refs,
            ],
            "extension_install_disabled_posture_ref",
        )
        _deny_runtime_flags(self)
        return self


class ExtensionInstallDisabledRecordReceipt(_ExtensionInstallDisabledModel):
    schema_version: Literal["uaa_extension_install_disabled_record_receipt.v1"] = (
        "uaa_extension_install_disabled_record_receipt.v1"
    )
    receipt_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    record_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    idempotency_key_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    candidate_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    catalog_entry_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    source_package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    provenance_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: Literal["disabled_install_record_receipt_recorded"] = (
        "disabled_install_record_receipt_recorded"
    )
    record_storage_mode: Literal[
        "receipt_only",
        "local_disabled_record_store",
    ] = "receipt_only"
    durable_store_persistence: bool = False
    record_path_ref: str | None = Field(default=None, pattern=SAFE_REF_PATTERN)
    authority_lane_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_decision_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_lease_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_decision_outcome: AuthorityDecisionOutcome
    approval_request_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    exact_approval_required: Literal[True] = True
    local_approval_validated: Literal[True] = True
    approval_validation_status: Literal["approved"] = "approved"
    approval_ref_authority: Literal[False] = False
    receipt_plan_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    audit_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    file_hashes: list[ExtensionInstallDisabledFileHash] = Field(default_factory=list)
    safe_disable_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    rollback_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    kill_switch_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "raw_manifest_content_omitted",
            "raw_package_content_omitted",
            "local_paths_omitted",
        ]
    )
    disabled_install_record_receipt_recorded: Literal[True] = True
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    remote_execution_enabled: Literal[False] = False
    raw_manifest_content_stored: Literal[False] = False
    raw_package_content_stored: Literal[False] = False
    production_authority_granted: Literal[False] = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_record_receipt(self) -> "ExtensionInstallDisabledRecordReceipt":
        _validate_safe_ref_list(
            [
                *self.audit_refs,
                *self.evidence_refs,
                *self.side_effects_performed,
            ],
            "extension_install_disabled_record_receipt_ref",
        )
        if self.authority_decision_outcome != AuthorityDecisionOutcome.allow.value:
            raise ValueError("EXTENSION_INSTALL_DISABLED_RECORD_REQUIRES_ALLOW")
        if self.durable_store_persistence:
            if self.record_storage_mode != "local_disabled_record_store":
                raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_MODE_REQUIRED")
            if self.record_path_ref is None:
                raise ValueError("EXTENSION_INSTALL_DISABLED_RECORD_PATH_REF_REQUIRED")
            if self.side_effects_performed != [
                EXTENSION_INSTALL_DISABLED_STORAGE_EFFECT_REF
            ]:
                raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_EFFECT_REQUIRED")
        elif self.side_effects_performed:
            raise ValueError("EXTENSION_INSTALL_DISABLED_SIDE_EFFECTS_DENIED")
        _deny_runtime_authority_flags(self)
        return self


class ExtensionInstallDisabledRecordIssueRequest(_ExtensionInstallDisabledModel):
    schema_version: Literal[
        "uaa_extension_install_disabled_record_issue_request.v1"
    ] = "uaa_extension_install_disabled_record_issue_request.v1"
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    persist_to_local_disabled_record_store: Literal[True] = True
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    production_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_issue_request(self) -> "ExtensionInstallDisabledRecordIssueRequest":
        _deny_runtime_authority_flags(self)
        return self


class ExtensionInstallDisabledRecordDeleteReceipt(_ExtensionInstallDisabledModel):
    schema_version: Literal[
        "uaa_extension_install_disabled_record_delete_receipt.v1"
    ] = "uaa_extension_install_disabled_record_delete_receipt.v1"
    receipt_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    record_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    idempotency_key_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    candidate_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    catalog_entry_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: Literal["disabled_install_record_delete_receipt_recorded"] = (
        "disabled_install_record_delete_receipt_recorded"
    )
    deletion_status: Literal["record_deleted", "record_already_absent"]
    record_storage_mode: Literal["local_disabled_record_store"] = (
        "local_disabled_record_store"
    )
    durable_delete_receipt_persistence: Literal[True] = True
    record_path_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    delete_receipt_path_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_lane_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_decision_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_lease_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    authority_decision_outcome: AuthorityDecisionOutcome
    approval_request_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    exact_approval_required: Literal[True] = True
    local_approval_validated: Literal[True] = True
    approval_validation_status: Literal["approved"] = "approved"
    approval_ref_authority: Literal[False] = False
    audit_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_disable_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    rollback_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    kill_switch_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "raw_manifest_content_omitted",
            "raw_package_content_omitted",
            "local_paths_omitted",
        ]
    )
    disabled_install_record_deleted: bool
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    remote_execution_enabled: Literal[False] = False
    raw_manifest_content_stored: Literal[False] = False
    raw_package_content_stored: Literal[False] = False
    production_authority_granted: Literal[False] = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_delete_receipt(self) -> "ExtensionInstallDisabledRecordDeleteReceipt":
        _validate_safe_ref_list(
            [
                *self.audit_refs,
                *self.evidence_refs,
                *self.side_effects_performed,
            ],
            "extension_install_disabled_record_delete_receipt_ref",
        )
        if self.authority_decision_outcome != AuthorityDecisionOutcome.allow.value:
            raise ValueError("EXTENSION_INSTALL_DISABLED_DELETE_REQUIRES_ALLOW")
        expected_effect = (
            EXTENSION_INSTALL_DISABLED_DELETE_EFFECT_REF
            if self.deletion_status == "record_deleted"
            else EXTENSION_INSTALL_DISABLED_DELETE_NOOP_EFFECT_REF
        )
        if self.side_effects_performed != [
            expected_effect,
            EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_EFFECT_REF,
        ]:
            raise ValueError("EXTENSION_INSTALL_DISABLED_DELETE_EFFECT_REQUIRED")
        if self.disabled_install_record_deleted != (
            self.deletion_status == "record_deleted"
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_DELETE_STATUS_DRIFT")
        _deny_runtime_authority_flags(self)
        return self


class ExtensionInstallDisabledRecordDeleteRequest(_ExtensionInstallDisabledModel):
    schema_version: Literal[
        "uaa_extension_install_disabled_record_delete_request.v1"
    ] = "uaa_extension_install_disabled_record_delete_request.v1"
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    delete_from_local_disabled_record_store: Literal[True] = True
    plugin_install_enabled: Literal[False] = False
    plugin_enablement_enabled: Literal[False] = False
    plugin_execution_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    production_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_delete_request(self) -> "ExtensionInstallDisabledRecordDeleteRequest":
        _deny_runtime_authority_flags(self)
        return self


class ExtensionInstallDisabledAuthorityState:
    """Core-owned atomic lease and safe-disable state for the metadata lane."""

    def __init__(
        self,
        *,
        leases: list[AuthorityLease] | None = None,
        safe_disable_active: bool = True,
    ) -> None:
        self._lock = RLock()
        self._leases = [
            AuthorityLease.model_validate(lease.model_dump(mode="python"))
            for lease in leases or []
        ]
        self._safe_disable_active = safe_disable_active

    @contextmanager
    def hold_start_lock(self) -> Iterator[None]:
        with self._lock:
            yield

    def active_leases_locked(self) -> list[AuthorityLease]:
        with self._lock:
            return [
                lease.model_copy(deep=True)
                for lease in self._leases
                if lease.is_active()
            ]

    def safe_disable_active_locked(self) -> bool:
        return self._safe_disable_active

    def replace_leases(self, leases: list[AuthorityLease]) -> None:
        with self._lock:
            self._leases = [
                AuthorityLease.model_validate(lease.model_dump(mode="python"))
                for lease in leases
            ]

    def engage_safe_disable(self) -> None:
        with self._lock:
            self._safe_disable_active = True


class ExtensionInstallDisabledRecordStore:
    """Tiny exact-scoped local store for disabled install record receipts."""

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = Path(storage_root)
        self.records_dir = self.storage_root / "extension_install_disabled_records"
        self._lock_manager = FileSingleWriterLockManager(
            self.storage_root / "extension_install_disabled_locks"
        )

    def record_receipt(
        self,
        receipt: ExtensionInstallDisabledRecordReceipt,
        *,
        authority_state: ExtensionInstallDisabledAuthorityState | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> ExtensionInstallDisabledRecordReceipt:
        if authority_state is None or approval_authority is None:
            raise ValueError("EXTENSION_INSTALL_DISABLED_ATOMIC_AUTHORITY_STATE_REQUIRED")
        persisted = validate_extension_install_disabled_record_receipt(
            receipt.model_dump(mode="json")
            | {
                "record_storage_mode": "local_disabled_record_store",
                "durable_store_persistence": True,
                "record_path_ref": (
                    "storage-ref:extension-install-disabled-record:"
                    "uaa-plugin-skill-boundary"
                ),
                "side_effects_performed": [
                    EXTENSION_INSTALL_DISABLED_STORAGE_EFFECT_REF
                ],
            }
        )
        _ensure_real_directory(self.storage_root)
        _ensure_real_directory(self.records_dir)
        path = self.records_dir / "uaa-plugin-skill-boundary.disabled-install.json"
        with (
            approval_authority.hold_validation_lock(),
            authority_state.hold_start_lock(),
            self._lock_manager.acquire("extension-install-disabled-record"),
        ):
            if authority_lease_kill_switch_engaged():
                raise ValueError("EXTENSION_INSTALL_DISABLED_KILL_SWITCH_ENGAGED")
            if authority_state.safe_disable_active_locked():
                raise ValueError("EXTENSION_INSTALL_DISABLED_SAFE_DISABLE_ACTIVE")
            live_receipt = build_extension_install_disabled_record_receipt(
                leases=authority_state.active_leases_locked(),
                approval_authority=approval_authority,
                approval_ref=receipt.approval_ref,
                idempotency_key_ref=receipt.idempotency_key_ref,
            )
            _require_live_receipt_binding(receipt, live_receipt)
            existing_payload = _read_bounded_regular_file(path)
            if existing_payload is not None:
                existing = ExtensionInstallDisabledRecordReceipt.model_validate_json(
                    existing_payload
                )
                if existing.idempotency_key_ref != persisted.idempotency_key_ref:
                    raise ValueError("EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_MISMATCH")
                if existing.model_dump(mode="json") != persisted.model_dump(
                    mode="json"
                ):
                    raise ValueError(
                        "EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_PAYLOAD_MISMATCH"
                    )
                return existing
            _write_atomic_bounded_json(path, persisted.model_dump(mode="json"))
            return persisted

    def delete_record(
        self,
        receipt: ExtensionInstallDisabledRecordDeleteReceipt,
        *,
        authority_state: ExtensionInstallDisabledAuthorityState | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> ExtensionInstallDisabledRecordDeleteReceipt:
        if authority_state is None or approval_authority is None:
            raise ValueError(
                "EXTENSION_INSTALL_DISABLED_DELETE_ATOMIC_AUTHORITY_STATE_REQUIRED"
            )
        _ensure_real_directory(self.storage_root)
        _ensure_real_directory(self.records_dir)
        delete_receipts_dir = self.storage_root / "extension_install_disabled_deletions"
        _ensure_real_directory(delete_receipts_dir)
        delete_receipt_path = (
            delete_receipts_dir
            / f"{sha256(receipt.idempotency_key_ref.encode('utf-8')).hexdigest()}.json"
        )
        record_path = (
            self.records_dir / "uaa-plugin-skill-boundary.disabled-install.json"
        )
        with (
            approval_authority.hold_validation_lock(),
            authority_state.hold_start_lock(),
            self._lock_manager.acquire("extension-install-disabled-record"),
        ):
            if authority_lease_kill_switch_engaged():
                raise ValueError("EXTENSION_INSTALL_DISABLED_KILL_SWITCH_ENGAGED")
            if authority_state.safe_disable_active_locked():
                raise ValueError("EXTENSION_INSTALL_DISABLED_SAFE_DISABLE_ACTIVE")
            live_receipt = build_extension_install_disabled_record_delete_receipt(
                leases=authority_state.active_leases_locked(),
                approval_authority=approval_authority,
                approval_ref=receipt.approval_ref,
                idempotency_key_ref=receipt.idempotency_key_ref,
            )
            _require_live_delete_receipt_binding(receipt, live_receipt)
            existing_payload = _read_bounded_regular_file(delete_receipt_path)
            if existing_payload is not None:
                existing = (
                    ExtensionInstallDisabledRecordDeleteReceipt.model_validate_json(
                        existing_payload
                    )
                )
                if existing.idempotency_key_ref != receipt.idempotency_key_ref:
                    raise ValueError(
                        "EXTENSION_INSTALL_DISABLED_DELETE_IDEMPOTENCY_MISMATCH"
                    )
                if _delete_receipt_replay_identity(
                    existing
                ) != _delete_receipt_replay_identity(receipt):
                    raise ValueError(
                        "EXTENSION_INSTALL_DISABLED_DELETE_IDEMPOTENCY_PAYLOAD_MISMATCH"
                    )
                if (
                    existing.deletion_status == "record_deleted"
                    and _read_bounded_regular_file(record_path) is not None
                ):
                    record_path.unlink()
                    _fsync_directory(record_path.parent)
                return existing

            record_existed = _read_bounded_regular_file(record_path) is not None
            delete_effect = (
                EXTENSION_INSTALL_DISABLED_DELETE_EFFECT_REF
                if record_existed
                else EXTENSION_INSTALL_DISABLED_DELETE_NOOP_EFFECT_REF
            )
            persisted = validate_extension_install_disabled_record_delete_receipt(
                receipt.model_dump(mode="json")
                | {
                    "deletion_status": (
                        "record_deleted" if record_existed else "record_already_absent"
                    ),
                    "disabled_install_record_deleted": record_existed,
                    "side_effects_performed": [
                        delete_effect,
                        EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_EFFECT_REF,
                    ],
                }
            )
            # Persist the exact deletion decision first. Replay completes an
            # interrupted unlink without authorizing or repeating other work.
            _write_atomic_bounded_json(
                delete_receipt_path,
                persisted.model_dump(mode="json"),
            )
            if record_existed:
                record_path.unlink()
                _fsync_directory(record_path.parent)
            return persisted


def build_extension_install_disabled_approval_request() -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=EXTENSION_INSTALL_DISABLED_REQUEST_REF,
        run_id=EXTENSION_INSTALL_DISABLED_RUN_REF,
        subject_type=ApprovalSubjectType.external_action,
        subject_id="extension-install-disabled:uaa-plugin-skill-boundary",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            actor_display_name="Extension Install Reviewer",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action="record_disabled_extension_install_ref",
        purpose=(
            "Approve recording a disabled-by-default extension install reference "
            "without importing, enabling, or executing plugin code."
        ),
        risk_level=ApprovalRiskLevel.medium,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="extension_install_disabled_posture",
            reason="Repo-owned extension metadata review.",
            requires_redaction=True,
        ),
        resource_refs=[
            "extension-package:uaa-plugin-skill-boundary",
            "plugin-skill-manifest:uaa-plugin-skill-boundary",
            "version:uaa-p1-024",
            "plugin-provenance:uaa-plugin-skill-boundary",
            "storage-ref:extension-install-disabled-record:uaa-plugin-skill-boundary",
        ],
        event_ref="event-ref:extension-install-disabled:approval-request",
        trace_id="trace-ref:extension-install-disabled:uaa-plugin-skill-boundary",
        expires_at=utc_now() + timedelta(hours=1),
    )


def build_extension_install_disabled_delete_approval_request() -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=EXTENSION_INSTALL_DISABLED_DELETE_REQUEST_REF,
        run_id=EXTENSION_INSTALL_DISABLED_DELETE_RUN_REF,
        subject_type=ApprovalSubjectType.external_action,
        subject_id="extension-install-disabled-delete:uaa-plugin-skill-boundary",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            actor_display_name="Extension Install Reviewer",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action="delete_disabled_extension_install_ref",
        purpose=(
            "Approve rollback/delete of the local disabled extension install "
            "metadata record without importing, enabling, or executing plugin code."
        ),
        risk_level=ApprovalRiskLevel.medium,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="extension_install_disabled_record_rollback",
            reason="Repo-owned extension disabled-record rollback metadata.",
            requires_redaction=True,
        ),
        resource_refs=[
            "extension-package:uaa-plugin-skill-boundary",
            "plugin-skill-manifest:uaa-plugin-skill-boundary",
            "version:uaa-p1-024",
            "plugin-provenance:uaa-plugin-skill-boundary",
            "storage-ref:extension-install-disabled-record:uaa-plugin-skill-boundary",
        ],
        event_ref="event-ref:extension-install-disabled-delete:approval-request",
        trace_id="trace-ref:extension-install-disabled-delete:uaa-plugin-skill-boundary",
        expires_at=utc_now() + timedelta(hours=1),
    )


def build_default_extension_install_disabled_posture(
    *,
    leases: list[AuthorityLease] | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    approval_ref: str | None = None,
) -> ExtensionInstallDisabledPostureReadModel:
    install_decision = _build_repo_owned_plugin_install_review_decision()
    authority_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=EXTENSION_INSTALL_DISABLED_ACTION_REF,
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.write,
            safe_summary=(
                "Record a disabled extension install reference for a reviewed "
                "repo-owned package without importing or executing it."
            ),
            capability_ref="authority-capability-ref:extension-install-disabled",
            lane_ref="authority-lane-ref:extension-install-disabled",
            requested_mode=TrustMode.approved_safe_local_work_session,
            resource_refs=[
                "extension-package:uaa-plugin-skill-boundary",
                "plugin-skill-manifest:uaa-plugin-skill-boundary",
                "version:uaa-p1-024",
                "plugin-provenance:uaa-plugin-skill-boundary",
                "storage-ref:extension-install-disabled-record:uaa-plugin-skill-boundary",
            ],
            rollback_ref="rollback-ref:extension-install-disabled:delete-record",
            safe_disable_ref="safe-disable-ref:extension-install-disabled",
        ),
        leases or [],
    )
    approval_decision = _validate_local_approval(
        approval_authority=approval_authority,
        approval_ref=approval_ref,
    )
    local_approval_validated = bool(approval_decision and approval_decision.allowed)
    ready = (
        local_approval_validated
        and authority_decision.outcome == AuthorityDecisionOutcome.allow.value
    )
    candidate = ExtensionInstallDisabledCandidateRecord(
        candidate_ref="extension-install-disabled-candidate:uaa-plugin-skill-boundary",
        catalog_entry_ref="inspectable-catalog-entry:uaa-plugin-skill-boundary",
        package_ref="extension-package:uaa-plugin-skill-boundary",
        manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
        version_ref="version:uaa-p1-024",
        source_package_ref="plugin-package:uaa-plugin-skill-boundary-reviewed",
        provenance_ref="plugin-provenance:uaa-plugin-skill-boundary",
        static_review_ref="plugin-static-review:uaa-plugin-skill-boundary",
        sandbox_test_plan_ref="plugin-sandbox-test-plan:disabled-install-review",
        tool_broker_mapping_ref="tool-broker-map:disabled-install-none",
        event_ledger_plan_ref="event-ledger-plan:extension-install-disabled",
        version_pin_ref="plugin-version-pin:uaa-plugin-skill-boundary",
        revocation_plan_ref="plugin-revocation-plan:extension-install-disabled",
        safe_disable_ref="safe-disable-ref:extension-install-disabled",
        rollback_ref="rollback-ref:extension-install-disabled:delete-record",
        authority_lane_ref="authority-lane-ref:extension-install-disabled",
        authority_decision_ref=authority_decision.decision_ref,
        authority_decision_outcome=authority_decision.outcome,
        authority_decision_reason_refs=list(authority_decision.reason_refs),
        manifest_security_decision_ref=install_decision.manifest_security_decision_ref,
        install_review_decision_ref=install_decision.decision_ref,
        receipt_plan_ref=install_decision.receipt_plan.receipt_plan_ref,
        authority_lease_ref=authority_decision.lease_ref,
        audit_refs=[
            authority_decision.audit_record_ref,
            "audit:extension-install-disabled:m79-review",
        ],
        receipt_refs=[install_decision.receipt_plan.receipt_plan_ref],
        file_hashes=[
            _safe_file_hash(
                "file-ref:plugin-install-review-policy-doc",
                "docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md",
            ),
            _safe_file_hash(
                "file-ref:plugin-install-review-receipt-plan-doc",
                "docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md",
            ),
            _safe_file_hash(
                "file-ref:plugin-skill-trust-manifest-schema",
                "docs/schemas/plugin_skill_trust_manifest.schema.json",
            ),
        ],
        blocked_capability_refs=[
            "blocked-authority:extension-install-disabled:no-runtime-import",
            "blocked-authority:extension-install-disabled:no-plugin-execution",
            "blocked-authority:extension-install-disabled:no-marketplace-fetch",
            "blocked-authority:extension-install-disabled:no-connector-write",
            "blocked-authority:extension-install-disabled:no-shell-execution",
            "blocked-authority:extension-install-disabled:no-provider-model-call",
            "blocked-authority:extension-install-disabled:no-browser-automation",
            "blocked-authority:extension-install-disabled:no-production-authority",
        ],
        approval_request_ref=EXTENSION_INSTALL_DISABLED_REQUEST_REF,
        approval_ref=approval_ref if local_approval_validated else None,
        local_approval_validated=local_approval_validated,
        approval_validation_status=(
            str(approval_decision.status) if approval_decision else "approval_missing"
        ),
        disabled_install_record_ready=ready,
        safe_summary=(
            "Reviewed extension install-disabled candidate. It can only become "
            "record-ready after active workspace/write AuthorityLease scope and "
            "exact LocalApprovalAuthority validation; install, import, enablement, "
            "and execution remain disabled."
        ),
    )
    status = (
        "review_ready_disabled_not_persisted"
        if ready
        else "blocked_pending_authority_and_approval"
    )
    return validate_extension_install_disabled_posture(
        ExtensionInstallDisabledPostureReadModel(
            posture_ref="extension-install-disabled-posture:uaa:v1",
            status=status,
            candidate_count=1,
            candidates=[candidate],
            required_authority_ref="authority-capability-ref:extension-install-disabled",
            required_approval_ref=EXTENSION_INSTALL_DISABLED_REQUEST_REF,
            verifier_refs=[
                "verifier:extension-install-disabled-posture",
                "verifier:runtime-extensibility-final",
            ],
            docs_refs=[
                "doc:runtime-extensibility-final",
                "doc:plugin-install-review",
                "doc:authority-graduation-board",
            ],
            next_safe_action_refs=[
                "next-safe-action:issue-workspace-write-authority-lease",
                "next-safe-action:validate-exact-local-approval",
                "next-safe-action:keep-callable-extension-activation-blocked",
            ],
            blocked_authority_refs=list(candidate.blocked_capability_refs),
            safe_summary=(
                "Extension install-disabled posture is inspectable and safe-ref-only. "
                "It proves reviewed metadata, hashes, approval requirement, "
                "AuthorityLease decision refs, receipts, revocation, rollback, and "
                "blocked runtime authority without installing or executing code."
            ),
        )
    )


def build_extension_install_disabled_record_receipt(
    *,
    leases: list[AuthorityLease] | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    approval_ref: str | None = None,
    idempotency_key_ref: str = EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_REF,
) -> ExtensionInstallDisabledRecordReceipt:
    posture = build_default_extension_install_disabled_posture(
        leases=leases,
        approval_authority=approval_authority,
        approval_ref=approval_ref,
    )
    candidate = posture.candidates[0]
    if (
        not candidate.disabled_install_record_ready
        or candidate.authority_decision_outcome != AuthorityDecisionOutcome.allow.value
        or candidate.authority_lease_ref is None
        or candidate.approval_ref is None
    ):
        raise ValueError("EXTENSION_INSTALL_DISABLED_RECORD_AUTHORITY_REQUIRED")
    return validate_extension_install_disabled_record_receipt(
        ExtensionInstallDisabledRecordReceipt(
            receipt_ref=EXTENSION_INSTALL_DISABLED_RECEIPT_REF,
            record_ref=EXTENSION_INSTALL_DISABLED_RECORD_REF,
            idempotency_key_ref=idempotency_key_ref,
            candidate_ref=candidate.candidate_ref,
            catalog_entry_ref=candidate.catalog_entry_ref,
            package_ref=candidate.package_ref,
            manifest_ref=candidate.manifest_ref,
            version_ref=candidate.version_ref,
            source_package_ref=candidate.source_package_ref,
            provenance_ref=candidate.provenance_ref,
            authority_lane_ref=candidate.authority_lane_ref,
            authority_decision_ref=candidate.authority_decision_ref,
            authority_lease_ref=candidate.authority_lease_ref,
            authority_decision_outcome=candidate.authority_decision_outcome,
            approval_request_ref=candidate.approval_request_ref,
            approval_ref=candidate.approval_ref,
            receipt_plan_ref=candidate.receipt_plan_ref,
            audit_refs=[
                *candidate.audit_refs,
                "audit:extension-install-disabled:record-receipt",
            ],
            evidence_refs=[
                candidate.static_review_ref,
                candidate.install_review_decision_ref,
                candidate.manifest_security_decision_ref,
                candidate.authority_decision_ref,
            ],
            file_hashes=list(candidate.file_hashes),
            safe_disable_ref=candidate.safe_disable_ref,
            rollback_ref=candidate.rollback_ref,
            kill_switch_ref="kill-switch-ref:authority-lease-local",
            safe_summary=(
                "Disabled extension install record receipt issued after active "
                "workspace/write AuthorityLease scope and exact local approval; "
                "plugin install, import, activation, and execution remain disabled."
            ),
        )
    )


def issue_extension_install_disabled_record(
    request: ExtensionInstallDisabledRecordIssueRequest,
    *,
    leases: list[AuthorityLease] | None = None,
    authority_state: ExtensionInstallDisabledAuthorityState | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    idempotency_key_ref: str = EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_REF,
    storage_root: Path | None = None,
) -> ExtensionInstallDisabledRecordReceipt:
    if authority_state is None:
        raise ValueError("EXTENSION_INSTALL_DISABLED_ATOMIC_AUTHORITY_STATE_REQUIRED")
    receipt = build_extension_install_disabled_record_receipt(
        leases=authority_state.active_leases_locked(),
        approval_authority=approval_authority,
        approval_ref=request.approval_ref,
        idempotency_key_ref=idempotency_key_ref,
    )
    return ExtensionInstallDisabledRecordStore(
        storage_root or authority_state_dir()
    ).record_receipt(
        receipt,
        authority_state=authority_state,
        approval_authority=approval_authority,
    )


def build_extension_install_disabled_record_delete_receipt(
    *,
    leases: list[AuthorityLease] | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    approval_ref: str | None = None,
    idempotency_key_ref: str = EXTENSION_INSTALL_DISABLED_DELETE_IDEMPOTENCY_REF,
) -> ExtensionInstallDisabledRecordDeleteReceipt:
    authority_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=EXTENSION_INSTALL_DISABLED_DELETE_ACTION_REF,
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.write,
            safe_summary=(
                "Rollback/delete a local disabled extension install metadata record "
                "without importing, enabling, or executing plugin code."
            ),
            capability_ref="authority-capability-ref:extension-install-disabled-delete",
            lane_ref="authority-lane-ref:extension-install-disabled",
            requested_mode=TrustMode.approved_safe_local_work_session,
            resource_refs=[
                "extension-package:uaa-plugin-skill-boundary",
                "plugin-skill-manifest:uaa-plugin-skill-boundary",
                "version:uaa-p1-024",
                "plugin-provenance:uaa-plugin-skill-boundary",
                "storage-ref:extension-install-disabled-record:uaa-plugin-skill-boundary",
            ],
            rollback_ref="rollback-ref:extension-install-disabled:delete-record",
            safe_disable_ref="safe-disable-ref:extension-install-disabled",
        ),
        leases or [],
    )
    approval_decision = _validate_local_approval(
        approval_authority=approval_authority,
        approval_ref=approval_ref,
        approval_request_builder=build_extension_install_disabled_delete_approval_request,
    )
    if (
        authority_decision.outcome != AuthorityDecisionOutcome.allow.value
        or authority_decision.lease_ref is None
        or approval_decision is None
        or not approval_decision.allowed
        or approval_ref is None
    ):
        raise ValueError("EXTENSION_INSTALL_DISABLED_DELETE_AUTHORITY_REQUIRED")
    return validate_extension_install_disabled_record_delete_receipt(
        ExtensionInstallDisabledRecordDeleteReceipt(
            receipt_ref=EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_REF,
            record_ref=EXTENSION_INSTALL_DISABLED_RECORD_REF,
            idempotency_key_ref=idempotency_key_ref,
            candidate_ref="extension-install-disabled-candidate:uaa-plugin-skill-boundary",
            catalog_entry_ref="inspectable-catalog-entry:uaa-plugin-skill-boundary",
            package_ref="extension-package:uaa-plugin-skill-boundary",
            manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
            version_ref="version:uaa-p1-024",
            deletion_status="record_already_absent",
            record_path_ref=(
                "storage-ref:extension-install-disabled-record:"
                "uaa-plugin-skill-boundary"
            ),
            delete_receipt_path_ref=(
                "storage-ref:extension-install-disabled-delete-receipt:"
                "uaa-plugin-skill-boundary"
            ),
            authority_lane_ref="authority-lane-ref:extension-install-disabled",
            authority_decision_ref=authority_decision.decision_ref,
            authority_lease_ref=authority_decision.lease_ref,
            authority_decision_outcome=authority_decision.outcome,
            approval_request_ref=EXTENSION_INSTALL_DISABLED_DELETE_REQUEST_REF,
            approval_ref=approval_ref,
            audit_refs=[
                authority_decision.audit_record_ref,
                "audit:extension-install-disabled:delete-receipt",
            ],
            evidence_refs=[
                "rollback-ref:extension-install-disabled:delete-record",
                authority_decision.decision_ref,
            ],
            safe_disable_ref="safe-disable-ref:extension-install-disabled",
            rollback_ref="rollback-ref:extension-install-disabled:delete-record",
            kill_switch_ref="kill-switch-ref:authority-lease-local",
            disabled_install_record_deleted=False,
            side_effects_performed=[
                EXTENSION_INSTALL_DISABLED_DELETE_NOOP_EFFECT_REF,
                EXTENSION_INSTALL_DISABLED_DELETE_RECEIPT_EFFECT_REF,
            ],
            safe_summary=(
                "Disabled extension install record rollback/delete receipt issued "
                "after active workspace/write AuthorityLease scope and exact local "
                "approval; plugin install, import, activation, and execution remain "
                "disabled."
            ),
        )
    )


def delete_extension_install_disabled_record(
    request: ExtensionInstallDisabledRecordDeleteRequest,
    *,
    leases: list[AuthorityLease] | None = None,
    authority_state: ExtensionInstallDisabledAuthorityState | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    idempotency_key_ref: str = EXTENSION_INSTALL_DISABLED_DELETE_IDEMPOTENCY_REF,
    storage_root: Path | None = None,
) -> ExtensionInstallDisabledRecordDeleteReceipt:
    if authority_state is None:
        raise ValueError(
            "EXTENSION_INSTALL_DISABLED_DELETE_ATOMIC_AUTHORITY_STATE_REQUIRED"
        )
    receipt = build_extension_install_disabled_record_delete_receipt(
        leases=authority_state.active_leases_locked(),
        approval_authority=approval_authority,
        approval_ref=request.approval_ref,
        idempotency_key_ref=idempotency_key_ref,
    )
    return ExtensionInstallDisabledRecordStore(
        storage_root or authority_state_dir()
    ).delete_record(
        receipt,
        authority_state=authority_state,
        approval_authority=approval_authority,
    )


def validate_extension_install_disabled_record_receipt(
    receipt: ExtensionInstallDisabledRecordReceipt | dict[str, object],
) -> ExtensionInstallDisabledRecordReceipt:
    if isinstance(receipt, ExtensionInstallDisabledRecordReceipt):
        return receipt
    return ExtensionInstallDisabledRecordReceipt.model_validate(receipt)


def validate_extension_install_disabled_record_delete_receipt(
    receipt: ExtensionInstallDisabledRecordDeleteReceipt | dict[str, object],
) -> ExtensionInstallDisabledRecordDeleteReceipt:
    if isinstance(receipt, ExtensionInstallDisabledRecordDeleteReceipt):
        return receipt
    return ExtensionInstallDisabledRecordDeleteReceipt.model_validate(receipt)


def validate_extension_install_disabled_posture(
    posture: ExtensionInstallDisabledPostureReadModel,
) -> ExtensionInstallDisabledPostureReadModel:
    return posture


def _validate_local_approval(
    *,
    approval_authority: LocalApprovalAuthority | None,
    approval_ref: str | None,
    approval_request_builder=build_extension_install_disabled_approval_request,
) -> ApprovalValidationDecision | None:
    if approval_authority is None or approval_ref is None:
        return None
    request = approval_request_builder()
    return approval_authority.validate_for_request(request, approval_ref)


def _delete_receipt_replay_identity(
    receipt: ExtensionInstallDisabledRecordDeleteReceipt,
) -> dict[str, object]:
    payload = receipt.model_dump(mode="json")
    return {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "deletion_status",
            "disabled_install_record_deleted",
            "side_effects_performed",
        }
    }


def _require_live_receipt_binding(
    supplied: ExtensionInstallDisabledRecordReceipt,
    live: ExtensionInstallDisabledRecordReceipt,
) -> None:
    for field_name in (
        "record_ref",
        "idempotency_key_ref",
        "candidate_ref",
        "package_ref",
        "manifest_ref",
        "version_ref",
        "authority_lane_ref",
        "authority_lease_ref",
        "approval_request_ref",
        "approval_ref",
        "safe_disable_ref",
        "rollback_ref",
    ):
        if getattr(supplied, field_name) != getattr(live, field_name):
            raise ValueError("EXTENSION_INSTALL_DISABLED_LIVE_AUTHORITY_BINDING_MISMATCH")


def _require_live_delete_receipt_binding(
    supplied: ExtensionInstallDisabledRecordDeleteReceipt,
    live: ExtensionInstallDisabledRecordDeleteReceipt,
) -> None:
    for field_name in (
        "record_ref",
        "idempotency_key_ref",
        "candidate_ref",
        "package_ref",
        "manifest_ref",
        "version_ref",
        "authority_lane_ref",
        "authority_lease_ref",
        "approval_request_ref",
        "approval_ref",
        "safe_disable_ref",
        "rollback_ref",
    ):
        if getattr(supplied, field_name) != getattr(live, field_name):
            raise ValueError(
                "EXTENSION_INSTALL_DISABLED_DELETE_LIVE_AUTHORITY_BINDING_MISMATCH"
            )


def _build_repo_owned_plugin_install_review_decision() -> PluginInstallReviewDecision:
    manifest_decision = build_plugin_manifest_security_decision(
        PluginManifestSecurityReviewRequest(
            review_request_ref="plugin-manifest-review-request:extension-install-disabled",
            manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
            plugin_ref="extension-package:uaa-plugin-skill-boundary",
            plugin_name="UAA Plugin Skill Boundary",
            plugin_version="uaa-p1-024",
            actor_ref=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            source_ref="plugin-source:uaa-repo-owned-boundary",
            provenance_ref="plugin-provenance:uaa-plugin-skill-boundary",
            declared_permissions=[
                PluginManifestDeclaredPermission(
                    permission_ref="plugin-permission:metadata-only-review",
                    kind=PluginManifestPermissionKind.read_only_local_docs,
                    risk_level=PluginManifestRiskLevel.low,
                    safe_purpose="Review repo-owned extension metadata only.",
                    tool_broker_capability_ref="tool-broker-capability:none-disabled",
                )
            ],
            static_review_ref="plugin-static-review:uaa-plugin-skill-boundary",
            sandbox_test_plan_ref="plugin-sandbox-test-plan:disabled-install-review",
            tool_broker_mapping_ref="tool-broker-map:disabled-install-none",
            event_ledger_plan_ref="event-ledger-plan:extension-install-disabled",
            version_pin_ref="plugin-version-pin:uaa-plugin-skill-boundary",
            revocation_plan_ref="plugin-revocation-plan:extension-install-disabled",
            human_approval=PluginManifestApprovalBinding(
                approval_ref="approval:extension-install-disabled-manifest-review",
                approved_manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
                approved_plugin_ref="extension-package:uaa-plugin-skill-boundary",
                approved_version="uaa-p1-024",
                approved_actor_ref=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            ),
            safe_manifest_summary=(
                "Reviewed repo-owned extension metadata for disabled-install "
                "posture; no runtime import or execution requested."
            ),
        )
    )
    return build_plugin_install_review_decision(
        PluginInstallReviewRequest(
            install_review_request_ref=(
                "plugin-install-review-request:extension-install-disabled"
            ),
            manifest_security_decision=manifest_decision,
            manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
            plugin_ref="extension-package:uaa-plugin-skill-boundary",
            plugin_version="uaa-p1-024",
            actor_ref=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            source_package_ref="plugin-package:uaa-plugin-skill-boundary-reviewed",
            provenance_ref="plugin-provenance:uaa-plugin-skill-boundary",
            static_review_ref="plugin-static-review:uaa-plugin-skill-boundary",
            sandbox_test_plan_ref="plugin-sandbox-test-plan:disabled-install-review",
            tool_broker_mapping_ref="tool-broker-map:disabled-install-none",
            event_ledger_plan_ref="event-ledger-plan:extension-install-disabled",
            version_pin_ref="plugin-version-pin:uaa-plugin-skill-boundary",
            revocation_plan_ref="plugin-revocation-plan:extension-install-disabled",
            approval=PluginInstallReviewApprovalBinding(
                approval_ref="approval:extension-install-disabled-install-review",
                approved_install_review_request_ref=(
                    "plugin-install-review-request:extension-install-disabled"
                ),
                approved_manifest_security_decision_ref=manifest_decision.decision_ref,
                approved_manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
                approved_plugin_ref="extension-package:uaa-plugin-skill-boundary",
                approved_version="uaa-p1-024",
                approved_actor_ref=EXTENSION_INSTALL_DISABLED_ACTOR_REF,
            ),
            safe_install_review_summary=(
                "Review disabled extension install refs while keeping install, "
                "enablement, runtime import, and execution disabled."
            ),
        )
    )


def _safe_file_hash(file_ref: str, rel_path: str) -> ExtensionInstallDisabledFileHash:
    path = Path(__file__).resolve().parents[4] / rel_path
    payload = _read_bounded_regular_file(path)
    if payload is None:
        return ExtensionInstallDisabledFileHash(
            file_ref=file_ref,
            hash_status="missing",
        )
    digest = sha256(payload).hexdigest()
    if digest != _EXPECTED_INSTALL_DISABLED_FILE_SHA256.get(rel_path):
        return ExtensionInstallDisabledFileHash(
            file_ref=file_ref,
            hash_value=f"sha256:{digest}",
            hash_status="mismatch",
        )
    return ExtensionInstallDisabledFileHash(
        file_ref=file_ref,
        hash_value=f"sha256:{digest}",
        hash_status="reviewed",
    )


def _ensure_real_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_DIRECTORY_INVALID")


def _read_bounded_regular_file(path: Path) -> bytes | None:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID") from exc
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.lstat(path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
            or metadata.st_size > EXTENSION_INSTALL_DISABLED_MAX_RECORD_BYTES
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID")
        chunks: list[bytes] = []
        remaining = metadata.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65_536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) != metadata.st_size:
            raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID")
        if len(payload) > EXTENSION_INSTALL_DISABLED_MAX_RECORD_BYTES:
            raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID")
        return payload
    finally:
        os.close(descriptor)


def _write_atomic_bounded_json(path: Path, payload: dict[str, object]) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > EXTENSION_INSTALL_DISABLED_MAX_RECORD_BYTES:
        raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_SIZE_INVALID")
    _ensure_real_directory(path.parent)
    _recover_stale_pending_files(path)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.pending")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(temp_path, flags, 0o600)
    except OSError as exc:
        raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_WRITE_FAILED") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID")
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("extension disabled record write failed")
            view = view[written:]
        os.fsync(descriptor)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise
    finally:
        os.close(descriptor)
    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    if existing is not None and (
        not stat.S_ISREG(existing.st_mode) or stat.S_ISLNK(existing.st_mode)
    ):
        temp_path.unlink(missing_ok=True)
        raise ValueError("EXTENSION_INSTALL_DISABLED_STORAGE_FILE_INVALID")
    os.replace(temp_path, path)
    _fsync_directory(path.parent)


def _recover_stale_pending_files(path: Path) -> None:
    pending_paths = list(path.parent.glob(f".{path.name}.*.pending"))
    if len(pending_paths) > 16:
        raise ValueError("EXTENSION_INSTALL_DISABLED_PENDING_FILE_LIMIT_EXCEEDED")
    removed = False
    for pending_path in pending_paths:
        metadata = pending_path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > EXTENSION_INSTALL_DISABLED_MAX_RECORD_BYTES
        ):
            raise ValueError("EXTENSION_INSTALL_DISABLED_PENDING_FILE_INVALID")
        pending_path.unlink()
        removed = True
    if removed:
        _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _deny_runtime_flags(
    model: ExtensionInstallDisabledCandidateRecord
    | ExtensionInstallDisabledPostureReadModel,
) -> None:
    _deny_runtime_authority_flags(model)
    if model.side_effects_performed:
        raise ValueError("EXTENSION_INSTALL_DISABLED_SIDE_EFFECTS_DENIED")


def _deny_runtime_authority_flags(
    model: (
        ExtensionInstallDisabledCandidateRecord
        | ExtensionInstallDisabledPostureReadModel
        | ExtensionInstallDisabledRecordReceipt
        | ExtensionInstallDisabledRecordIssueRequest
        | ExtensionInstallDisabledRecordDeleteReceipt
        | ExtensionInstallDisabledRecordDeleteRequest
    ),
) -> None:
    for field_name in (
        "plugin_install_enabled",
        "plugin_enablement_enabled",
        "plugin_execution_enabled",
        "runtime_import_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "provider_model_call_enabled",
        "remote_execution_enabled",
        "raw_manifest_content_stored",
        "raw_package_content_stored",
        "production_authority_granted",
    ):
        if getattr(model, field_name, False):
            raise ValueError(f"EXTENSION_INSTALL_DISABLED_{field_name.upper()}_DENIED")


def _validate_safe_ref_list(refs: list[str], field_name: str) -> None:
    import re

    pattern = re.compile(SAFE_REF_PATTERN)
    for ref in refs:
        if not pattern.match(ref):
            raise ValueError(f"{field_name.upper()}_INVALID")
