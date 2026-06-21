from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.connector_audit_revocation_hardening import (
    ConnectorAuditRevocationHardeningReport,
    validate_connector_audit_revocation_hardening_report,
)


CONNECTOR_SAFETY_FREEZE_DOCS = [
    "docs/connectors/CONNECTOR_SAFETY_FREEZE.md",
    "docs/connectors/CONNECTOR_SAFETY_FREEZE_POLICY.md",
    "docs/connectors/CONNECTOR_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_SAFETY_FREEZE_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_SAFETY_FREEZE_NON_GOALS.md",
    "docs/connectors/M130_TO_M131_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorSafetyFreezeStatus(str, Enum):
    frozen_for_review = "frozen_for_review"


class _ConnectorSafetyFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorSafetyFreezePolicy(_ConnectorSafetyFreezeModel):
    policy_ref: str = "connector-safety-freeze-policy:m130"
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m129_hardening_binding_required: bool = True
    accepted_checkpoint_refs_required: bool = True
    no_effect_receipt_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    revocation_readiness_required: bool = True
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
    connector_approval_revocation_enabled: bool = False
    connector_session_stop_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    external_service_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M130_SECRET_LIKE_CONNECTOR_FREEZE_CONTENT_DENIED") from exc
        return self


class ConnectorSafetyFreezeRecord(_ConnectorSafetyFreezeModel):
    freeze_ref: str
    source_report: ConnectorAuditRevocationHardeningReport
    source_hardening_ref: str
    source_report_ref: str
    source_audit_ledger_entry_ref: str
    source_revocation_record_ref: str
    source_connector_write_execution_result_ref: str
    source_connector_write_approval_ref: str
    source_safe_result_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    safety_checklist_ref: str
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ConnectorSafetyFreezeStatus = ConnectorSafetyFreezeStatus.frozen_for_review
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m129_hardening_bound: bool = True
    connector_surface_frozen: bool = True
    audit_replay_bound: bool = True
    revocation_readiness_bound: bool = True
    no_effect_receipt_required: bool = True
    live_connector_runtime_enabled: bool = False
    live_connector_runtime_performed: bool = False
    account_auth_enabled: bool = False
    account_auth_performed: bool = False
    network_access_enabled: bool = False
    network_access_performed: bool = False
    credential_handling_enabled: bool = False
    credential_handling_performed: bool = False
    raw_connector_content_enabled: bool = False
    raw_connector_content_returned: bool = False
    full_content_read_enabled: bool = False
    full_connector_content_returned: bool = False
    connector_write_enabled: bool = False
    connector_write_performed: bool = False
    connector_send_enabled: bool = False
    connector_send_performed: bool = False
    connector_delete_enabled: bool = False
    connector_delete_performed: bool = False
    connector_export_enabled: bool = False
    connector_export_performed: bool = False
    connector_bulk_export_enabled: bool = False
    connector_bulk_export_performed: bool = False
    attachment_download_enabled: bool = False
    attachment_download_performed: bool = False
    audit_export_enabled: bool = False
    audit_export_performed: bool = False
    revocation_execution_enabled: bool = False
    revocation_executed: bool = False
    kill_switch_execution_enabled: bool = False
    kill_switch_executed: bool = False
    connector_approval_revoked: bool = False
    connector_session_stopped: bool = False
    background_worker_started: bool = False
    scheduler_started: bool = False
    external_service_called: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _record_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        for checkpoint_ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(checkpoint_ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("M130_REASON_CODE_REQUIRED")
        try:
            _validate_safe_payload({"safe_summary": self.safe_summary})
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M130_SECRET_LIKE_CONNECTOR_FREEZE_CONTENT_DENIED") from exc
        return self


def build_connector_safety_freeze_record(
    *,
    source_report: ConnectorAuditRevocationHardeningReport,
    policy: ConnectorSafetyFreezePolicy | None = None,
) -> ConnectorSafetyFreezeRecord:
    active_policy = validate_connector_safety_freeze_policy(
        policy or ConnectorSafetyFreezePolicy()
    )
    validated_source = validate_connector_audit_revocation_hardening_report(
        source_report
    )
    record = ConnectorSafetyFreezeRecord(
        freeze_ref="connector-safety-freeze:m130",
        source_report=validated_source,
        source_hardening_ref=validated_source.hardening_ref,
        source_report_ref=validated_source.report_ref,
        source_audit_ledger_entry_ref=(
            validated_source.audit_ledger_entry.audit_ledger_entry_ref
        ),
        source_revocation_record_ref=(
            validated_source.revocation_record.revocation_record_ref
        ),
        source_connector_write_execution_result_ref=(
            validated_source.connector_write_execution_result_ref
        ),
        source_connector_write_approval_ref=(
            validated_source.connector_write_approval_ref
        ),
        source_safe_result_ref=validated_source.safe_result_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        safety_checklist_ref="connector-safety-freeze-checklist-ref:m130",
        audit_ref="audit-ref:m130:connector-safety-freeze",
        replay_ref="replay-ref:m130:connector-safety-freeze",
        revocation_ref="revocation-ref:m130:connector-safety-freeze",
        kill_switch_ref="kill-switch-ref:m130:connector-safety-freeze",
        accepted_checkpoint_refs=list(_REQUIRED_ACCEPTED_CHECKPOINT_REFS),
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m130:connector-safety-freeze:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        freeze_only=active_policy.freeze_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        exact_m129_hardening_bound=(
            active_policy.exact_m129_hardening_binding_required
        ),
        connector_surface_frozen=active_policy.accepted_checkpoint_refs_required,
        audit_replay_bound=active_policy.audit_required and active_policy.replay_required,
        revocation_readiness_bound=active_policy.revocation_readiness_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        reason_codes=[
            "M130_CONNECTOR_SAFETY_FREEZE",
            "M130_FREEZE_ONLY_CONNECTOR_BOUNDARY",
            "M130_EXACT_M129_HARDENING_REQUIRED",
            "M130_NO_CONNECTOR_RUNTIME_AUTHORITY",
            "M131_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M130 freezes the accepted M121-M129 connector safety surface for "
            "governed review using safe refs, an exact M129 hardening report, "
            "audit refs, replay refs, revocation refs, kill-switch refs, and a "
            "no-effect receipt plan. It grants no live connector runtime, account "
            "auth, network access, credential handling, raw connector content, "
            "full content read, connector write/send/delete/export, attachment "
            "download, audit export, revocation execution, kill-switch execution, "
            "backend route, Control Center control, dependency, beta release, or "
            "production authority."
        ),
    )
    return validate_connector_safety_freeze_record(record)


def validate_connector_safety_freeze_policy(
    policy: ConnectorSafetyFreezePolicy,
) -> ConnectorSafetyFreezePolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, ConnectorSafetyFreezePolicy):
        raise ValueError("M130_SECRET_LIKE_CONNECTOR_FREEZE_CONTENT_DENIED")
    validated = ConnectorSafetyFreezePolicy.model_validate(payload)
    for field_name, reason in _POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    return validated


def validate_connector_safety_freeze_record(
    record: ConnectorSafetyFreezeRecord,
) -> ConnectorSafetyFreezeRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ConnectorSafetyFreezeRecord):
        raise ValueError("M130_SECRET_LIKE_CONNECTOR_FREEZE_CONTENT_DENIED")
    for field_name, reason in _DENIAL_FIELDS.items():
        if payload.get(field_name):
            raise ValueError(reason)
    validated = ConnectorSafetyFreezeRecord.model_validate(payload)
    for field_name, reason in _RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DENIAL_FIELDS.items():
        if getattr(validated, field_name, False):
            raise ValueError(reason)
    if validated.status != ConnectorSafetyFreezeStatus.frozen_for_review:
        raise ValueError("M130_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M130_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoint_refs(validated.accepted_checkpoint_refs)
    source_report = _coerce_source_report(payload.get("source_report"))
    _validate_source_binding(validated, source_report)
    return validated


def _coerce_source_report(value: Any) -> ConnectorAuditRevocationHardeningReport:
    if isinstance(value, ConnectorAuditRevocationHardeningReport):
        return value
    if isinstance(value, dict):
        return ConnectorAuditRevocationHardeningReport.model_validate(value)
    raise ValueError("M130_SOURCE_M129_HARDENING_REQUIRED")


def _validate_source_binding(
    record: ConnectorSafetyFreezeRecord,
    source_report: ConnectorAuditRevocationHardeningReport,
) -> None:
    validated_source = validate_connector_audit_revocation_hardening_report(
        source_report
    )
    comparisons = [
        (
            record.source_hardening_ref,
            validated_source.hardening_ref,
            "M130_SOURCE_HARDENING_BINDING_MISMATCH",
        ),
        (
            record.source_report_ref,
            validated_source.report_ref,
            "M130_SOURCE_REPORT_BINDING_MISMATCH",
        ),
        (
            record.source_audit_ledger_entry_ref,
            validated_source.audit_ledger_entry.audit_ledger_entry_ref,
            "M130_AUDIT_LEDGER_BINDING_MISMATCH",
        ),
        (
            record.source_revocation_record_ref,
            validated_source.revocation_record.revocation_record_ref,
            "M130_REVOCATION_RECORD_BINDING_MISMATCH",
        ),
        (
            record.source_connector_write_execution_result_ref,
            validated_source.connector_write_execution_result_ref,
            "M130_CONNECTOR_RESULT_BINDING_MISMATCH",
        ),
        (
            record.source_connector_write_approval_ref,
            validated_source.connector_write_approval_ref,
            "M130_CONNECTOR_APPROVAL_BINDING_MISMATCH",
        ),
        (
            record.source_safe_result_ref,
            validated_source.safe_result_ref,
            "M130_SAFE_RESULT_BINDING_MISMATCH",
        ),
        (record.actor_ref, validated_source.actor_ref, "M130_ACTOR_BINDING_MISMATCH"),
        (record.user_ref, validated_source.user_ref, "M130_USER_BINDING_MISMATCH"),
        (
            record.workspace_ref,
            validated_source.workspace_ref,
            "M130_WORKSPACE_BINDING_MISMATCH",
        ),
    ]
    for actual, expected, reason in comparisons:
        if actual != expected:
            raise ValueError(reason)
    if not record.safety_checklist_ref.startswith(
        "connector-safety-freeze-checklist-ref:"
    ):
        raise ValueError("M130_SAFETY_CHECKLIST_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M130_NO_EFFECT_RECEIPT_PLAN_REQUIRED")
    for ref, reason in [
        (record.freeze_ref, "M130_FREEZE_REF_REQUIRED"),
        (record.audit_ref, "M130_AUDIT_REF_REQUIRED"),
        (record.replay_ref, "M130_REPLAY_REF_REQUIRED"),
        (record.revocation_ref, "M130_REVOCATION_REF_REQUIRED"),
        (record.kill_switch_ref, "M130_KILL_SWITCH_REF_REQUIRED"),
    ]:
        if "m130" not in ref.lower():
            raise ValueError(reason)


def _validate_accepted_checkpoint_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M130_ACCEPTED_CHECKPOINT_REFS_REQUIRED")
    if len(set(refs)) != len(refs):
        raise ValueError("M130_ACCEPTED_CHECKPOINT_REF_DUPLICATE")
    if list(refs) != list(_REQUIRED_ACCEPTED_CHECKPOINT_REFS):
        raise ValueError("M130_ACCEPTED_CHECKPOINT_REFS_REQUIRED")


def _record_ref_pairs(record: ConnectorSafetyFreezeRecord) -> list[Any]:
    return [
        (record.freeze_ref, "freeze_ref"),
        (record.source_hardening_ref, "source_hardening_ref"),
        (record.source_report_ref, "source_report_ref"),
        (record.source_audit_ledger_entry_ref, "source_audit_ledger_entry_ref"),
        (record.source_revocation_record_ref, "source_revocation_record_ref"),
        (
            record.source_connector_write_execution_result_ref,
            "source_connector_write_execution_result_ref",
        ),
        (
            record.source_connector_write_approval_ref,
            "source_connector_write_approval_ref",
        ),
        (record.source_safe_result_ref, "source_safe_result_ref"),
        (record.actor_ref, "actor_ref"),
        (record.user_ref, "user_ref"),
        (record.workspace_ref, "workspace_ref"),
        (record.safety_checklist_ref, "safety_checklist_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


_REQUIRED_ACCEPTED_CHECKPOINT_REFS = (
    "checkpoint:m121",
    "checkpoint:m122",
    "checkpoint:m123",
    "checkpoint:m124",
    "checkpoint:m125",
    "checkpoint:m126",
    "checkpoint:m127",
    "checkpoint:m128",
    "checkpoint:m129",
)

_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M130_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M130_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M130_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M130_DETERMINISTIC_REQUIRED"),
    ("local_only", "M130_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M130_SAFE_REFS_ONLY_REQUIRED"),
    (
        "exact_m129_hardening_binding_required",
        "M130_EXACT_M129_HARDENING_REQUIRED",
    ),
    ("accepted_checkpoint_refs_required", "M130_ACCEPTED_CHECKPOINT_REFS_REQUIRED"),
    ("no_effect_receipt_required", "M130_NO_EFFECT_RECEIPT_PLAN_REQUIRED"),
    ("audit_required", "M130_AUDIT_REQUIRED"),
    ("replay_required", "M130_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M130_REVOCATION_READINESS_REQUIRED"),
]

_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M130_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M130_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M130_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M130_DETERMINISTIC_REQUIRED"),
    ("local_only", "M130_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M130_SAFE_REFS_ONLY_REQUIRED"),
    ("exact_m129_hardening_bound", "M130_EXACT_M129_HARDENING_REQUIRED"),
    ("connector_surface_frozen", "M130_CONNECTOR_SURFACE_FREEZE_REQUIRED"),
    ("audit_replay_bound", "M130_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_bound", "M130_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M130_NO_EFFECT_RECEIPT_PLAN_REQUIRED"),
]

_DENIAL_FIELDS = {
    "live_connector_runtime_enabled": "M130_LIVE_CONNECTOR_RUNTIME_DENIED",
    "live_connector_runtime_performed": "M130_LIVE_CONNECTOR_RUNTIME_DENIED",
    "account_auth_enabled": "M130_ACCOUNT_AUTH_DENIED",
    "account_auth_performed": "M130_ACCOUNT_AUTH_DENIED",
    "network_access_enabled": "M130_NETWORK_ACCESS_DENIED",
    "network_access_performed": "M130_NETWORK_ACCESS_DENIED",
    "credential_handling_enabled": "M130_CREDENTIAL_HANDLING_DENIED",
    "credential_handling_performed": "M130_CREDENTIAL_HANDLING_DENIED",
    "raw_connector_content_enabled": "M130_RAW_CONNECTOR_CONTENT_DENIED",
    "raw_connector_content_returned": "M130_RAW_CONNECTOR_CONTENT_DENIED",
    "full_content_read_enabled": "M130_FULL_CONTENT_READ_DENIED",
    "full_connector_content_returned": "M130_FULL_CONTENT_READ_DENIED",
    "connector_write_enabled": "M130_CONNECTOR_WRITE_DENIED",
    "connector_write_performed": "M130_CONNECTOR_WRITE_DENIED",
    "connector_send_enabled": "M130_CONNECTOR_SEND_DENIED",
    "connector_send_performed": "M130_CONNECTOR_SEND_DENIED",
    "connector_delete_enabled": "M130_CONNECTOR_DELETE_DENIED",
    "connector_delete_performed": "M130_CONNECTOR_DELETE_DENIED",
    "connector_export_enabled": "M130_CONNECTOR_EXPORT_DENIED",
    "connector_export_performed": "M130_CONNECTOR_EXPORT_DENIED",
    "connector_bulk_export_enabled": "M130_CONNECTOR_BULK_EXPORT_DENIED",
    "connector_bulk_export_performed": "M130_CONNECTOR_BULK_EXPORT_DENIED",
    "attachment_download_enabled": "M130_ATTACHMENT_DOWNLOAD_DENIED",
    "attachment_download_performed": "M130_ATTACHMENT_DOWNLOAD_DENIED",
    "audit_export_enabled": "M130_AUDIT_EXPORT_DENIED",
    "audit_export_performed": "M130_AUDIT_EXPORT_DENIED",
    "revocation_execution_enabled": "M130_REVOCATION_EXECUTION_DENIED",
    "revocation_executed": "M130_REVOCATION_EXECUTION_DENIED",
    "kill_switch_execution_enabled": "M130_KILL_SWITCH_EXECUTION_DENIED",
    "kill_switch_executed": "M130_KILL_SWITCH_EXECUTION_DENIED",
    "connector_approval_revocation_enabled": "M130_APPROVAL_REVOCATION_DENIED",
    "connector_approval_revoked": "M130_APPROVAL_REVOCATION_DENIED",
    "connector_session_stop_enabled": "M130_CONNECTOR_SESSION_STOP_DENIED",
    "connector_session_stopped": "M130_CONNECTOR_SESSION_STOP_DENIED",
    "background_worker_enabled": "M130_BACKGROUND_WORKER_DENIED",
    "background_worker_started": "M130_BACKGROUND_WORKER_DENIED",
    "scheduler_enabled": "M130_SCHEDULER_DENIED",
    "scheduler_started": "M130_SCHEDULER_DENIED",
    "external_service_enabled": "M130_EXTERNAL_SERVICE_DENIED",
    "external_service_called": "M130_EXTERNAL_SERVICE_DENIED",
    "model_call_enabled": "M130_MODEL_CALL_DENIED",
    "model_call_performed": "M130_MODEL_CALL_DENIED",
    "memory_write_enabled": "M130_MEMORY_WRITE_DENIED",
    "memory_write_performed": "M130_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M130_CONTEXT_INJECTION_DENIED",
    "context_injection_performed": "M130_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M130_BACKEND_ROUTE_DENIED",
    "backend_route_added": "M130_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M130_CONTROL_CENTER_CONTROL_DENIED",
    "control_center_control_added": "M130_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M130_DEPENDENCY_DENIED",
    "beta_release_enabled": "M130_BETA_RELEASE_DENIED",
    "production_authority_granted": "M130_PRODUCTION_AUTHORITY_DENIED",
}
