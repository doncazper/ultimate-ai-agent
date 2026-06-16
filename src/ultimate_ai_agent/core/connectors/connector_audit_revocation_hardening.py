from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.connector_write_execution_low_risk import (
    ConnectorWriteExecutionDecision,
    ConnectorWriteExecutionLowRiskStatus,
    ConnectorWriteExecutionResult,
    validate_connector_write_execution_decision,
    validate_connector_write_execution_result,
)


CONNECTOR_AUDIT_REVOCATION_HARDENING_DOCS = [
    "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING.md",
    "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_AUDIT_REVOCATION_HARDENING_NON_GOALS.md",
    "docs/connectors/M129_TO_M130_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorAuditRevocationHardeningStatus(str, Enum):
    hardened_for_governed_review = "hardened_for_governed_review"
    rejected = "rejected"


class _ConnectorAuditRevocationHardening(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorAuditRevocationHardeningPolicy(_ConnectorAuditRevocationHardening):
    policy_ref: str = "connector-audit-revocation-hardening-policy:m129"
    enabled_for_review: bool = True
    exact_m128_execution_binding_required: bool = True
    safe_audit_entry_required: bool = True
    safe_revocation_record_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    revocation_readiness_required: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    audit_export_enabled: bool = False
    revocation_execution_enabled: bool = False
    kill_switch_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_safe_payload(self.metadata)
        return self


class ConnectorAuditRevocationHardeningRequest(_ConnectorAuditRevocationHardening):
    hardening_request_ref: str
    hardening_ref: str
    connector_write_execution_decision_ref: str
    connector_write_execution_result_ref: str
    execution_ref: str
    connector_write_dry_run_plan_ref: str
    connector_write_approval_ref: str
    safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    audit_ledger_entry_ref: str
    revocation_record_ref: str
    retention_policy_ref: str
    redaction_ref: str
    prior_milestone_refs: list[str]
    m128_decision: ConnectorWriteExecutionDecision
    m128_result: ConnectorWriteExecutionResult
    safe_audit_summary: str
    safe_revocation_summary: str
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    local_only: bool = True
    safe_refs_only: bool = True
    review_only: bool = True
    hardening_only: bool = True
    live_connector_runtime_requested: bool = False
    account_auth_requested: bool = False
    network_access_requested: bool = False
    credential_handling_requested: bool = False
    raw_connector_content_requested: bool = False
    full_content_read_requested: bool = False
    connector_write_requested: bool = False
    connector_send_requested: bool = False
    connector_delete_requested: bool = False
    connector_export_requested: bool = False
    connector_bulk_export_requested: bool = False
    attachment_download_requested: bool = False
    audit_export_requested: bool = False
    revocation_execution_requested: bool = False
    kill_switch_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        for refs, field_name in _request_ref_list_pairs(self):
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        _validate_safe_payload({"safe_audit_summary": self.safe_audit_summary})
        _validate_safe_payload({"safe_revocation_summary": self.safe_revocation_summary})
        _validate_safe_payload(self.metadata)
        return self


class ConnectorAuditLedgerEntry(_ConnectorAuditRevocationHardening):
    audit_ledger_entry_ref: str
    hardening_ref: str
    connector_write_execution_result_ref: str
    execution_ref: str
    connector_write_approval_ref: str
    safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    audit_ref: str
    replay_ref: str
    store_safe_refs_only: bool = True
    store_safe_summary_only: bool = True
    immutable: bool = True
    replay_safe: bool = True
    raw_connector_content_stored: bool = False
    full_connector_content_stored: bool = False
    credential_material_stored: bool = False
    raw_audit_payload_stored: bool = False
    audit_exported: bool = False
    network_access_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    production_authority_granted: bool = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _ledger_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        if not self.store_safe_refs_only or not self.store_safe_summary_only:
            raise ValueError("M129_SAFE_AUDIT_STORAGE_REQUIRED")
        if not self.immutable or not self.replay_safe:
            raise ValueError("M129_AUDIT_REPLAY_IMMUTABILITY_REQUIRED")
        for field_name, reason in _STORAGE_OR_ACTION_DENIAL_FIELDS.items():
            if getattr(self, field_name, False):
                raise ValueError(reason)
        _validate_safe_payload({"safe_summary": self.safe_summary})
        return self


class ConnectorRevocationHardeningRecord(_ConnectorAuditRevocationHardening):
    revocation_record_ref: str
    hardening_ref: str
    connector_write_execution_result_ref: str
    connector_write_approval_ref: str
    revocation_ref: str
    kill_switch_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    revocation_ready: bool = True
    revocation_review_only: bool = True
    revocation_executed: bool = False
    kill_switch_executed: bool = False
    connector_approval_revoked: bool = False
    connector_session_stopped: bool = False
    live_connector_runtime_touched: bool = False
    account_auth_touched: bool = False
    network_access_performed: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_stored: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _revocation_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        if not self.revocation_ready or not self.revocation_review_only:
            raise ValueError("M129_REVOCATION_READINESS_REQUIRED")
        for field_name, reason in _STORAGE_OR_ACTION_DENIAL_FIELDS.items():
            if getattr(self, field_name, False):
                raise ValueError(reason)
        _validate_safe_payload({"safe_summary": self.safe_summary})
        return self


class ConnectorAuditRevocationHardeningReport(_ConnectorAuditRevocationHardening):
    report_ref: str
    status: ConnectorAuditRevocationHardeningStatus
    hardening_ref: str
    connector_write_execution_decision_ref: str
    connector_write_execution_result_ref: str
    execution_ref: str
    connector_write_approval_ref: str
    safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    exact_m128_execution_bound: bool = True
    audit_hardened: bool = True
    revocation_hardened: bool = True
    audit_bound: bool = True
    replay_bound: bool = True
    revocation_ready: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    review_only: bool = True
    audit_ledger_entry: ConnectorAuditLedgerEntry
    revocation_record: ConnectorRevocationHardeningRecord
    reason_codes: list[str]
    safe_message: str
    live_connector_runtime_performed: bool = False
    account_auth_performed: bool = False
    network_access_performed: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_returned: bool = False
    full_connector_content_returned: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    connector_delete_performed: bool = False
    connector_export_performed: bool = False
    connector_bulk_export_performed: bool = False
    attachment_download_performed: bool = False
    audit_export_performed: bool = False
    revocation_executed: bool = False
    kill_switch_executed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in _report_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload({"safe_message": self.safe_message})
        return self


def build_connector_audit_revocation_hardening_report(
    request: ConnectorAuditRevocationHardeningRequest,
    *,
    policy: ConnectorAuditRevocationHardeningPolicy | None = None,
) -> ConnectorAuditRevocationHardeningReport:
    active_policy = validate_connector_audit_revocation_hardening_policy(
        policy or ConnectorAuditRevocationHardeningPolicy()
    )
    validated_request = validate_connector_audit_revocation_hardening_request(request)
    ledger_entry = ConnectorAuditLedgerEntry(
        audit_ledger_entry_ref=validated_request.audit_ledger_entry_ref,
        hardening_ref=validated_request.hardening_ref,
        connector_write_execution_result_ref=(
            validated_request.connector_write_execution_result_ref
        ),
        execution_ref=validated_request.execution_ref,
        connector_write_approval_ref=validated_request.connector_write_approval_ref,
        safe_result_ref=validated_request.safe_result_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        safe_summary=validated_request.safe_audit_summary,
    )
    revocation_record = ConnectorRevocationHardeningRecord(
        revocation_record_ref=validated_request.revocation_record_ref,
        hardening_ref=validated_request.hardening_ref,
        connector_write_execution_result_ref=(
            validated_request.connector_write_execution_result_ref
        ),
        connector_write_approval_ref=validated_request.connector_write_approval_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        safe_summary=validated_request.safe_revocation_summary,
    )
    report = ConnectorAuditRevocationHardeningReport(
        report_ref=f"connector-audit-revocation-hardening-report:{_suffix(validated_request.hardening_ref)}",
        status=ConnectorAuditRevocationHardeningStatus.hardened_for_governed_review,
        hardening_ref=validated_request.hardening_ref,
        connector_write_execution_decision_ref=(
            validated_request.connector_write_execution_decision_ref
        ),
        connector_write_execution_result_ref=(
            validated_request.connector_write_execution_result_ref
        ),
        execution_ref=validated_request.execution_ref,
        connector_write_approval_ref=validated_request.connector_write_approval_ref,
        safe_result_ref=validated_request.safe_result_ref,
        actor_ref=validated_request.actor_ref,
        user_ref=validated_request.user_ref,
        workspace_ref=validated_request.workspace_ref,
        exact_m128_execution_bound=(
            active_policy.exact_m128_execution_binding_required
        ),
        audit_hardened=active_policy.safe_audit_entry_required,
        revocation_hardened=active_policy.safe_revocation_record_required,
        audit_bound=active_policy.audit_required,
        replay_bound=active_policy.replay_required,
        revocation_ready=active_policy.revocation_readiness_required,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        audit_ledger_entry=ledger_entry,
        revocation_record=revocation_record,
        reason_codes=[
            "M129_CONNECTOR_AUDIT_REVOCATION_HARDENED",
            "M129_EXACT_M128_EXECUTION_REQUIRED",
            "M129_SAFE_AUDIT_ENTRY_REQUIRED",
            "M129_REVOCATION_READY_NO_EXECUTION",
            "M130_REMAINS_FUTURE",
        ],
        safe_message=(
            "M129 hardens connector audit and revocation records for governed "
            "review without executing revocation or connector runtime actions."
        ),
    )
    return validate_connector_audit_revocation_hardening_report(report)


def validate_connector_audit_revocation_hardening_policy(
    policy: ConnectorAuditRevocationHardeningPolicy,
) -> ConnectorAuditRevocationHardeningPolicy:
    payload = _model_payload(policy)
    validated = ConnectorAuditRevocationHardeningPolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _ENABLEMENT_DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ConnectorAuditRevocationHardeningPolicy):
        raise ValueError("M129_SECRET_LIKE_CONNECTOR_AUDIT_CONTENT_DENIED")
    return validated


def validate_connector_audit_revocation_hardening_request(
    request: ConnectorAuditRevocationHardeningRequest,
) -> ConnectorAuditRevocationHardeningRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, ConnectorAuditRevocationHardeningRequest):
        raise ValueError("M129_SECRET_LIKE_CONNECTOR_AUDIT_CONTENT_DENIED")
    validated = ConnectorAuditRevocationHardeningRequest.model_validate(payload)
    for field_name, reason in _REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _REQUEST_DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_m129_ref(validated.audit_ledger_entry_ref, "audit_ledger_entry_ref")
    _validate_m129_ref(validated.revocation_record_ref, "revocation_record_ref")
    _validate_m129_ref(validated.revocation_ref, "revocation_ref")
    _validate_m129_ref(validated.kill_switch_ref, "kill_switch_ref")
    _validate_m128_binding(validated)
    return validated


def validate_connector_audit_ledger_entry(
    entry: ConnectorAuditLedgerEntry,
) -> ConnectorAuditLedgerEntry:
    payload = _model_payload(entry)
    if _has_secret_like_extra(payload, ConnectorAuditLedgerEntry):
        raise ValueError("M129_SECRET_LIKE_CONNECTOR_AUDIT_CONTENT_DENIED")
    validated = ConnectorAuditLedgerEntry.model_validate(payload)
    if not validated.store_safe_refs_only or not validated.store_safe_summary_only:
        raise ValueError("M129_SAFE_AUDIT_STORAGE_REQUIRED")
    for field_name, reason in _STORAGE_OR_ACTION_DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    return validated


def validate_connector_revocation_hardening_record(
    record: ConnectorRevocationHardeningRecord,
) -> ConnectorRevocationHardeningRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ConnectorRevocationHardeningRecord):
        raise ValueError("M129_SECRET_LIKE_CONNECTOR_AUDIT_CONTENT_DENIED")
    validated = ConnectorRevocationHardeningRecord.model_validate(payload)
    if not validated.revocation_ready or not validated.revocation_review_only:
        raise ValueError("M129_REVOCATION_READINESS_REQUIRED")
    for field_name, reason in _STORAGE_OR_ACTION_DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    return validated


def validate_connector_audit_revocation_hardening_report(
    report: ConnectorAuditRevocationHardeningReport,
) -> ConnectorAuditRevocationHardeningReport:
    payload = _model_payload(report)
    if _has_secret_like_extra(payload, ConnectorAuditRevocationHardeningReport):
        raise ValueError("M129_SECRET_LIKE_CONNECTOR_AUDIT_CONTENT_DENIED")
    validated = ConnectorAuditRevocationHardeningReport.model_validate(payload)
    if (
        validated.status
        != ConnectorAuditRevocationHardeningStatus.hardened_for_governed_review
    ):
        raise ValueError("M129_HARDENED_STATUS_REQUIRED")
    for field_name, reason in _REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _STORAGE_OR_ACTION_DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M129_SIDE_EFFECTS_DENIED")
    if "M129_CONNECTOR_AUDIT_REVOCATION_HARDENED" not in validated.reason_codes:
        raise ValueError("M129_REASON_CODE_REQUIRED")
    validate_connector_audit_ledger_entry(validated.audit_ledger_entry)
    validate_connector_revocation_hardening_record(validated.revocation_record)
    return validated


def _validate_m128_binding(request: ConnectorAuditRevocationHardeningRequest) -> None:
    decision = validate_connector_write_execution_decision(request.m128_decision)
    result = validate_connector_write_execution_result(request.m128_result)
    if decision.status != (
        ConnectorWriteExecutionLowRiskStatus.write_allowed_for_low_risk_transport
    ):
        raise ValueError("M129_M128_DECISION_STATUS_MISMATCH")
    if result.status != ConnectorWriteExecutionLowRiskStatus.write_completed:
        raise ValueError("M129_M128_RESULT_STATUS_MISMATCH")
    comparisons = [
        (
            request.connector_write_execution_decision_ref,
            decision.decision_ref,
            "M129_M128_DECISION_REF_MISMATCH",
        ),
        (
            request.connector_write_execution_result_ref,
            result.result_ref,
            "M129_M128_RESULT_REF_MISMATCH",
        ),
        (request.execution_ref, decision.execution_ref, "M129_EXECUTION_REF_MISMATCH"),
        (request.execution_ref, result.execution_ref, "M129_RESULT_EXECUTION_REF_MISMATCH"),
        (
            request.connector_write_dry_run_plan_ref,
            decision.connector_write_dry_run_plan_ref,
            "M129_DRY_RUN_PLAN_REF_MISMATCH",
        ),
        (
            request.connector_write_dry_run_plan_ref,
            result.connector_write_dry_run_plan_ref,
            "M129_RESULT_DRY_RUN_PLAN_REF_MISMATCH",
        ),
        (
            request.connector_write_approval_ref,
            decision.connector_write_approval_ref,
            "M129_APPROVAL_REF_MISMATCH",
        ),
        (
            request.connector_write_approval_ref,
            result.connector_write_approval_ref,
            "M129_RESULT_APPROVAL_REF_MISMATCH",
        ),
        (request.safe_result_ref, decision.safe_result_ref, "M129_SAFE_RESULT_REF_MISMATCH"),
        (
            request.safe_result_ref,
            result.safe_result_ref,
            "M129_RESULT_SAFE_RESULT_REF_MISMATCH",
        ),
        (request.actor_ref, decision.actor_ref, "M129_ACTOR_BINDING_MISMATCH"),
        (request.user_ref, decision.user_ref, "M129_USER_BINDING_MISMATCH"),
        (request.workspace_ref, decision.workspace_ref, "M129_WORKSPACE_BINDING_MISMATCH"),
    ]
    for actual, expected, reason in comparisons:
        if actual != expected:
            raise ValueError(reason)


def _validate_m129_ref(ref: str, field_name: str) -> None:
    if "m129" not in ref.lower():
        raise ValueError("M129_EXACT_AUDIT_REVOCATION_REF_REQUIRED")
    _validate_m61_ref(ref, field_name)


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M129_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(set(refs)) != len(refs):
        raise ValueError("M129_PRIOR_MILESTONE_REF_DUPLICATE")
    missing = [ref for ref in _REQUIRED_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M129_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in _REQUIRED_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M129_PRIOR_MILESTONE_REF_UNEXPECTED")


def _request_ref_pairs(request: ConnectorAuditRevocationHardeningRequest):
    return [
        (request.hardening_request_ref, "hardening_request_ref"),
        (request.hardening_ref, "hardening_ref"),
        (
            request.connector_write_execution_decision_ref,
            "connector_write_execution_decision_ref",
        ),
        (
            request.connector_write_execution_result_ref,
            "connector_write_execution_result_ref",
        ),
        (request.execution_ref, "execution_ref"),
        (request.connector_write_dry_run_plan_ref, "connector_write_dry_run_plan_ref"),
        (request.connector_write_approval_ref, "connector_write_approval_ref"),
        (request.safe_result_ref, "safe_result_ref"),
        (request.actor_ref, "actor_ref"),
        (request.user_ref, "user_ref"),
        (request.workspace_ref, "workspace_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.audit_ledger_entry_ref, "audit_ledger_entry_ref"),
        (request.revocation_record_ref, "revocation_record_ref"),
        (request.retention_policy_ref, "retention_policy_ref"),
        (request.redaction_ref, "redaction_ref"),
    ]


def _request_ref_list_pairs(request: ConnectorAuditRevocationHardeningRequest):
    return [
        (request.prior_milestone_refs, "prior_milestone_ref"),
        (request.metadata_refs, "metadata_ref"),
    ]


def _ledger_ref_pairs(entry: ConnectorAuditLedgerEntry):
    return [
        (entry.audit_ledger_entry_ref, "audit_ledger_entry_ref"),
        (entry.hardening_ref, "hardening_ref"),
        (
            entry.connector_write_execution_result_ref,
            "connector_write_execution_result_ref",
        ),
        (entry.execution_ref, "execution_ref"),
        (entry.connector_write_approval_ref, "connector_write_approval_ref"),
        (entry.safe_result_ref, "safe_result_ref"),
        (entry.actor_ref, "actor_ref"),
        (entry.user_ref, "user_ref"),
        (entry.workspace_ref, "workspace_ref"),
        (entry.audit_ref, "audit_ref"),
        (entry.replay_ref, "replay_ref"),
    ]


def _revocation_ref_pairs(record: ConnectorRevocationHardeningRecord):
    return [
        (record.revocation_record_ref, "revocation_record_ref"),
        (record.hardening_ref, "hardening_ref"),
        (
            record.connector_write_execution_result_ref,
            "connector_write_execution_result_ref",
        ),
        (record.connector_write_approval_ref, "connector_write_approval_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.actor_ref, "actor_ref"),
        (record.user_ref, "user_ref"),
        (record.workspace_ref, "workspace_ref"),
    ]


def _report_ref_pairs(report: ConnectorAuditRevocationHardeningReport):
    return [
        (report.report_ref, "report_ref"),
        (report.hardening_ref, "hardening_ref"),
        (
            report.connector_write_execution_decision_ref,
            "connector_write_execution_decision_ref",
        ),
        (
            report.connector_write_execution_result_ref,
            "connector_write_execution_result_ref",
        ),
        (report.execution_ref, "execution_ref"),
        (report.connector_write_approval_ref, "connector_write_approval_ref"),
        (report.safe_result_ref, "safe_result_ref"),
        (report.actor_ref, "actor_ref"),
        (report.user_ref, "user_ref"),
        (report.workspace_ref, "workspace_ref"),
    ]


def _suffix(ref: str) -> str:
    return ref.replace(":", "-").replace("/", "-")


_REQUIRED_PRIOR_MILESTONE_REFS = [
    "milestone:M125",
    "milestone:M126",
    "milestone:M127",
    "milestone:M128",
]

_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "M129_REVIEW_ENABLED_REQUIRED"),
    ("exact_m128_execution_binding_required", "M129_EXACT_M128_EXECUTION_REQUIRED"),
    ("safe_audit_entry_required", "M129_SAFE_AUDIT_ENTRY_REQUIRED"),
    ("safe_revocation_record_required", "M129_SAFE_REVOCATION_RECORD_REQUIRED"),
    ("audit_required", "M129_AUDIT_REQUIRED"),
    ("replay_required", "M129_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M129_REVOCATION_READINESS_REQUIRED"),
    ("local_only", "M129_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M129_SAFE_REFS_ONLY_REQUIRED"),
]

_REQUEST_REQUIRED_TRUE = [
    ("local_only", "M129_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M129_SAFE_REFS_ONLY_REQUIRED"),
    ("review_only", "M129_REVIEW_ONLY_REQUIRED"),
    ("hardening_only", "M129_HARDENING_ONLY_REQUIRED"),
]

_REPORT_REQUIRED_TRUE = [
    ("exact_m128_execution_bound", "M129_EXACT_M128_EXECUTION_REQUIRED"),
    ("audit_hardened", "M129_SAFE_AUDIT_ENTRY_REQUIRED"),
    ("revocation_hardened", "M129_SAFE_REVOCATION_RECORD_REQUIRED"),
    ("audit_bound", "M129_AUDIT_REQUIRED"),
    ("replay_bound", "M129_REPLAY_REQUIRED"),
    ("revocation_ready", "M129_REVOCATION_READINESS_REQUIRED"),
    ("local_only", "M129_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M129_SAFE_REFS_ONLY_REQUIRED"),
    ("review_only", "M129_REVIEW_ONLY_REQUIRED"),
]

_ENABLEMENT_DENIAL_FIELDS = {
    "live_connector_runtime_enabled": "M129_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M129_ACCOUNT_AUTH_DENIED",
    "network_access_enabled": "M129_NETWORK_ACCESS_DENIED",
    "credential_handling_enabled": "M129_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_enabled": "M129_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_enabled": "M129_FULL_CONTENT_READ_DENIED",
    "connector_write_enabled": "M129_CONNECTOR_WRITE_DENIED",
    "connector_send_enabled": "M129_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M129_CONNECTOR_DELETE_DENIED",
    "connector_export_enabled": "M129_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_enabled": "M129_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_enabled": "M129_ATTACHMENT_DOWNLOAD_DENIED",
    "audit_export_enabled": "M129_AUDIT_EXPORT_DENIED",
    "revocation_execution_enabled": "M129_REVOCATION_EXECUTION_DENIED",
    "kill_switch_execution_enabled": "M129_KILL_SWITCH_EXECUTION_DENIED",
    "model_call_enabled": "M129_MODEL_CALL_DENIED",
    "memory_write_enabled": "M129_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M129_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M129_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M129_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M129_DEPENDENCY_DENIED",
    "production_authority_granted": "M129_PRODUCTION_AUTHORITY_DENIED",
}

_REQUEST_DENIAL_FIELDS = {
    "live_connector_runtime_requested": "M129_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_requested": "M129_ACCOUNT_AUTH_DENIED",
    "network_access_requested": "M129_NETWORK_ACCESS_DENIED",
    "credential_handling_requested": "M129_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_requested": "M129_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_requested": "M129_FULL_CONTENT_READ_DENIED",
    "connector_write_requested": "M129_CONNECTOR_WRITE_DENIED",
    "connector_send_requested": "M129_CONNECTOR_SEND_DENIED",
    "connector_delete_requested": "M129_CONNECTOR_DELETE_DENIED",
    "connector_export_requested": "M129_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_requested": "M129_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_requested": "M129_ATTACHMENT_DOWNLOAD_DENIED",
    "audit_export_requested": "M129_AUDIT_EXPORT_DENIED",
    "revocation_execution_requested": "M129_REVOCATION_EXECUTION_DENIED",
    "kill_switch_execution_requested": "M129_KILL_SWITCH_EXECUTION_DENIED",
    "model_call_requested": "M129_MODEL_CALL_DENIED",
    "memory_write_requested": "M129_MEMORY_WRITE_DENIED",
    "context_injection_requested": "M129_CONTEXT_INJECTION_DENIED",
    "backend_route_requested": "M129_BACKEND_ROUTE_DENIED",
    "control_center_control_requested": "M129_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_requested": "M129_DEPENDENCY_DENIED",
    "production_authority_requested": "M129_PRODUCTION_AUTHORITY_DENIED",
}

_STORAGE_OR_ACTION_DENIAL_FIELDS = {
    "raw_connector_content_stored": "M129_RAW_CONNECTOR_CONTENT_DENIED",
    "full_connector_content_stored": "M129_FULL_CONTENT_READ_DENIED",
    "credential_material_stored": "M129_CREDENTIAL_HANDLING_DENIED",
    "raw_audit_payload_stored": "M129_RAW_AUDIT_PAYLOAD_DENIED",
    "audit_exported": "M129_AUDIT_EXPORT_DENIED",
    "audit_export_performed": "M129_AUDIT_EXPORT_DENIED",
    "live_connector_runtime_touched": "M129_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_touched": "M129_ACCOUNT_AUTH_DENIED",
    "network_access_performed": "M129_NETWORK_ACCESS_DENIED",
    "credential_handling_performed": "M129_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_returned": "M129_RAW_CONNECTOR_CONTENT_DENIED",
    "full_connector_content_returned": "M129_FULL_CONTENT_READ_DENIED",
    "connector_write_performed": "M129_CONNECTOR_WRITE_DENIED",
    "connector_send_performed": "M129_CONNECTOR_SEND_DENIED",
    "connector_delete_performed": "M129_CONNECTOR_DELETE_DENIED",
    "connector_export_performed": "M129_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_performed": "M129_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_performed": "M129_ATTACHMENT_DOWNLOAD_DENIED",
    "revocation_executed": "M129_REVOCATION_EXECUTION_DENIED",
    "kill_switch_executed": "M129_KILL_SWITCH_EXECUTION_DENIED",
    "connector_approval_revoked": "M129_APPROVAL_REVOCATION_EXECUTION_DENIED",
    "connector_session_stopped": "M129_CONNECTOR_SESSION_STOP_DENIED",
    "model_call_performed": "M129_MODEL_CALL_DENIED",
    "memory_write_performed": "M129_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M129_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M129_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M129_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M129_DEPENDENCY_DENIED",
    "production_authority_granted": "M129_PRODUCTION_AUTHORITY_DENIED",
}
