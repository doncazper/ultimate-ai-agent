from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


AUTHORITY_LEASE_SCHEMA_VERSION = "uaa-authority-lease.v1"
AUTHORITY_STATE_SCHEMA_VERSION = "uaa-authority-state.v1"
AUTHORITY_STATE_CONTRACT_REF = "contract-ref:authority-modes-mission-leases:v1"
AUTHORITY_STATE_API_REF = "GET /api/runtime/authority-state"
AUTHORITY_STATE_SETTINGS_ROUTE_REF = "GET /control-center/settings/status#authority_lease_state"
AUTHORITY_STATE_CLI_REF = "repo-local-command:uaa-runtime-inspect-authority-state"
AUTHORITY_STATE_DIR_ENV = "UAA_AUTHORITY_STATE_DIR"
AUTHORITY_LEASES_FILE = "authority_leases.json"
AUTHORITY_LEASE_RECEIPTS_FILE = "authority_lease_receipts.jsonl"
AUTHORITY_STATE_REDACTIONS = (
    "safe_refs_only",
    "bounded_summaries_only",
    "raw_prompt_omitted",
    "raw_response_omitted",
    "raw_log_omitted",
    "local_paths_omitted",
    "provider_payload_omitted",
    "credentials_omitted",
)


class TrustMode(str, Enum):
    read_only = "read_only"
    ask_before_changes = "ask_before_changes"
    approved_safe_local_work_session = "approved_safe_local_work_session"
    full_local_workspace_session = "full_local_workspace_session"
    full_machine_access_session = "full_machine_access_session"
    delegated_mission_autonomous_window = "delegated_mission_autonomous_window"


class AuthorityDomain(str, Enum):
    workspace = "workspace"
    files = "files"
    shell = "shell"
    apps = "apps"
    browser = "browser"
    system_settings = "system_settings"
    calendar = "calendar"
    messages = "messages"
    email = "email"
    contacts = "contacts"
    home_assistant = "home_assistant"
    shopping_payments = "shopping_payments"
    provider_model_calls = "provider_model_calls"
    memory = "memory"
    cloud_production = "cloud_production"


class AuthorityCapability(str, Enum):
    observe = "observe"
    read = "read"
    draft = "draft"
    prepare = "prepare"
    mutate = "mutate"
    write = "write"
    execute = "execute"
    click = "click"
    form_fill = "form_fill"
    upload = "upload"
    download = "download"
    send = "send"
    purchase = "purchase"
    purchase_under_budget = "purchase_under_budget"
    commit = "commit"
    deploy = "deploy"
    admin = "admin"
    destructive = "destructive"


class AuthorityLeaseScope(str, Enum):
    session = "session"
    mission = "mission"


class AuthorityLeaseStatus(str, Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"
    planned = "planned"


class AuthorityDecisionOutcome(str, Enum):
    allow = "allow"
    ask = "ask"
    deny = "deny"
    degrade_to_draft = "degrade_to_draft"


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_task_ref(ref, field_name)


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


class _AuthorityModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class AuthorityLease(_AuthorityModel):
    schema_version: str = AUTHORITY_LEASE_SCHEMA_VERSION
    lease_ref: str = Field(..., min_length=1)
    mode: TrustMode
    scope: AuthorityLeaseScope = AuthorityLeaseScope.session
    status: AuthorityLeaseStatus = AuthorityLeaseStatus.active
    mission_ref: str | None = None
    operator_ref: str = "operator-ref:local-user"
    domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    constraints: dict[str, Any] = Field(default_factory=dict)
    ask_if: list[str] = Field(default_factory=list)
    hard_deny: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    rollback_required: bool = True
    safe_disable_required: bool = True
    kill_switch_required: bool = True
    safe_disable_ref: str = "safe-disable-ref:authority-lease-session"
    rollback_ref: str = "rollback-ref:authority-lease-revoke"
    kill_switch_ref: str = "kill-switch-ref:authority-lease-local"
    audit_ref: str = "audit-ref:authority-lease-decision-log"
    receipt_sink_ref: str = "receipt-sink-ref:authority-lease-action-receipts"
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(default_factory=lambda: utc_now() + timedelta(hours=1))
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_lease(self) -> "AuthorityLease":
        for value, field_name in [
            (self.lease_ref, "lease_ref"),
            (self.operator_ref, "operator_ref"),
            (self.mission_ref, "mission_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
            (self.audit_ref, "audit_ref"),
            (self.receipt_sink_ref, "receipt_sink_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "lease_safe_summary")
        for text in [self.mode, self.scope, self.status, *self.ask_if, *self.hard_deny]:
            validate_safe_task_text(_enum_value(text), "authority_lease_text")
        _validate_ref_list(self.unsupported_adapter_refs, "unsupported_adapter_ref")
        validate_safe_task_payload(self.constraints, "authority_lease_constraints")
        if not self.domains:
            raise ValueError("AUTHORITY_LEASE_DOMAINS_REQUIRED")
        for domain, capabilities in self.domains.items():
            validate_safe_task_text(_enum_value(domain), "authority_domain")
            if not capabilities:
                raise ValueError("AUTHORITY_LEASE_DOMAIN_CAPABILITIES_REQUIRED")
            for capability in capabilities:
                validate_safe_task_text(
                    _enum_value(capability),
                    "authority_capability",
                )
        if self.scope == AuthorityLeaseScope.mission.value and not self.mission_ref:
            raise ValueError("AUTHORITY_LEASE_MISSION_REF_REQUIRED")
        required = {
            "receipts_required": self.receipts_required,
            "audit_required": self.audit_required,
            "redaction_required": self.redaction_required,
            "rollback_required": self.rollback_required,
            "safe_disable_required": self.safe_disable_required,
            "kill_switch_required": self.kill_switch_required,
        }
        disabled = [name for name, enabled in required.items() if not enabled]
        if disabled:
            raise ValueError(f"AUTHORITY_LEASE_REQUIRED_GOVERNANCE_DISABLED:{disabled[0]}")
        return self

    def is_active(self, *, now: datetime | None = None) -> bool:
        current = now or utc_now()
        return self.status == AuthorityLeaseStatus.active.value and self.expires_at > current

    def grants(self, domain: AuthorityDomain, capability: AuthorityCapability) -> bool:
        values = self.domains.get(domain, [])
        return capability in values or _enum_value(capability) in {
            _enum_value(item) for item in values
        }


class AuthorityActionRequest(_AuthorityModel):
    action_ref: str = Field(..., min_length=1)
    domain: AuthorityDomain
    capability: AuthorityCapability
    safe_summary: str = Field(..., min_length=1, max_length=520)
    resource_refs: list[str] = Field(default_factory=list)
    route_ref: str | None = None
    lane_ref: str | None = None
    adapter_ref: str | None = None
    requested_mode: TrustMode | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    draft_fallback_available: bool = False
    unsupported_adapter: bool = False
    kill_switch_engaged: bool = False
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    rollback_ref: str = "rollback-ref:authority-action-required"
    safe_disable_ref: str = "safe-disable-ref:authority-action-required"

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityActionRequest":
        for value, field_name in [
            (self.action_ref, "authority_action_ref"),
            (self.lane_ref, "authority_lane_ref"),
            (self.adapter_ref, "authority_adapter_ref"),
            (self.rollback_ref, "authority_rollback_ref"),
            (self.safe_disable_ref, "authority_safe_disable_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "authority_resource_ref")
        validate_safe_task_text(self.safe_summary, "authority_action_summary")
        if self.route_ref is not None:
            validate_safe_task_text(self.route_ref, "authority_route_ref")
        validate_safe_task_text(_enum_value(self.domain), "authority_domain")
        validate_safe_task_text(_enum_value(self.capability), "authority_capability")
        if self.requested_mode:
            validate_safe_task_text(_enum_value(self.requested_mode), "trust_mode")
        validate_safe_task_payload(self.constraints, "authority_action_constraints")
        if not self.receipts_required or not self.audit_required or not self.redaction_required:
            raise ValueError("AUTHORITY_ACTION_GOVERNANCE_REQUIRED")
        return self


class AuthorityPolicyDecision(_AuthorityModel):
    schema_version: str = AUTHORITY_STATE_SCHEMA_VERSION
    decision_ref: str = Field(..., min_length=1)
    action_ref: str = Field(..., min_length=1)
    outcome: AuthorityDecisionOutcome
    domain: AuthorityDomain
    capability: AuthorityCapability
    lease_ref: str | None = None
    matched_mode: TrustMode | None = None
    required_mode: TrustMode | None = None
    required_domain_refs: list[str] = Field(default_factory=list)
    required_capability_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    operator_message: str = Field(..., min_length=1, max_length=520)
    known_authority: bool = False
    unsupported_adapter: bool = False
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    rollback_ref: str
    safe_disable_ref: str
    kill_switch_ref: str = "kill-switch-ref:authority-lease-local"
    audit_record_ref: str
    receipt_ref: str | None = None
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )
    decided_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_decision(self) -> "AuthorityPolicyDecision":
        for value, field_name in [
            (self.decision_ref, "authority_decision_ref"),
            (self.action_ref, "authority_action_ref"),
            (self.lease_ref, "authority_lease_ref"),
            (self.rollback_ref, "authority_rollback_ref"),
            (self.safe_disable_ref, "authority_safe_disable_ref"),
            (self.kill_switch_ref, "authority_kill_switch_ref"),
            (self.audit_record_ref, "authority_audit_record_ref"),
            (self.receipt_ref, "authority_receipt_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for ref_list, field_name in [
            (self.required_domain_refs, "required_domain_ref"),
            (self.required_capability_refs, "required_capability_ref"),
            (self.reason_refs, "authority_reason_ref"),
        ]:
            _validate_ref_list(ref_list, field_name)
        validate_safe_task_text(self.operator_message, "authority_operator_message")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_redaction")
        if self.outcome == AuthorityDecisionOutcome.allow.value and not (
            self.known_authority and self.lease_ref
        ):
            raise ValueError("AUTHORITY_ALLOW_REQUIRES_ACTIVE_LEASE")
        if self.outcome == AuthorityDecisionOutcome.allow.value and self.unsupported_adapter:
            raise ValueError("AUTHORITY_UNSUPPORTED_ADAPTER_CANNOT_ALLOW")
        if not self.receipts_required or not self.audit_required or not self.redaction_required:
            raise ValueError("AUTHORITY_DECISION_GOVERNANCE_REQUIRED")
        return self


class AuthorityCapabilityMapping(_AuthorityModel):
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    domain: AuthorityDomain
    capability: AuthorityCapability
    required_mode: TrustMode
    status: str = Field(..., min_length=1, max_length=80)
    route_refs: list[str] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    operator_copy: str = Field(..., min_length=1, max_length=360)

    @model_validator(mode="after")
    def validate_mapping(self) -> "AuthorityCapabilityMapping":
        for ref in [self.lane_ref, *self.evidence_refs, *self.unsupported_adapter_refs]:
            validate_task_ref(ref, "authority_mapping_ref")
        for text in [*self.route_refs, *self.cli_refs]:
            validate_safe_task_text(text, "authority_mapping_route_or_cli")
        for value in [
            self.label,
            self.status,
            self.operator_copy,
            self.domain,
            self.capability,
            self.required_mode,
        ]:
            validate_safe_task_text(_enum_value(value), "authority_mapping_text")
        return self


class AuthorityLeaseIssueRequest(_AuthorityModel):
    mode: TrustMode
    scope: AuthorityLeaseScope = AuthorityLeaseScope.session
    mission_ref: str | None = None
    operator_ref: str = "operator-ref:local-user"
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    constraints: dict[str, Any] = Field(default_factory=dict)
    decision_reason_ref: str = Field(..., min_length=1)
    duration_minutes: int = Field(default=60, ge=5, le=480)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_issue_request(self) -> "AuthorityLeaseIssueRequest":
        for value, field_name in [
            (self.mission_ref, "authority_lease_mission_ref"),
            (self.operator_ref, "authority_lease_operator_ref"),
            (self.decision_reason_ref, "authority_lease_decision_reason_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "authority_lease_issue_summary")
        validate_safe_task_payload(self.constraints, "authority_lease_issue_constraints")
        if self.scope == AuthorityLeaseScope.mission.value and not self.mission_ref:
            raise ValueError("AUTHORITY_LEASE_MISSION_REF_REQUIRED")
        for domain, capabilities in self.requested_domains.items():
            validate_safe_task_text(_enum_value(domain), "authority_issue_domain")
            for capability in capabilities:
                validate_safe_task_text(
                    _enum_value(capability),
                    "authority_issue_capability",
                )
        return self


class AuthorityLeaseRevokeRequest(_AuthorityModel):
    lease_ref: str = Field(..., min_length=1)
    decision_reason_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_revoke_request(self) -> "AuthorityLeaseRevokeRequest":
        validate_task_ref(self.lease_ref, "authority_lease_revoke_lease_ref")
        validate_task_ref(
            self.decision_reason_ref,
            "authority_lease_revoke_decision_reason_ref",
        )
        validate_safe_task_text(self.safe_summary, "authority_lease_revoke_summary")
        return self


class AuthorityLeaseReceipt(_AuthorityModel):
    schema_version: Literal["uaa-authority-lease-receipt.v1"] = (
        "uaa-authority-lease-receipt.v1"
    )
    operation: Literal["issue", "revoke"]
    status: Literal["issued", "revoked", "replayed", "denied"]
    receipt_ref: str = Field(..., min_length=1)
    lease_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    decision_reason_ref: str = Field(..., min_length=1)
    mode: TrustMode
    scope: AuthorityLeaseScope
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    denied_domain_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    audit_ref: str
    rollback_ref: str
    safe_disable_ref: str
    kill_switch_ref: str
    receipt_sink_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=520)
    execution_performed: bool = False
    raw_paths_included: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> "AuthorityLeaseReceipt":
        for value, field_name in [
            (self.receipt_ref, "authority_lease_receipt_ref"),
            (self.lease_ref, "authority_lease_receipt_lease_ref"),
            (self.idempotency_ref, "authority_lease_receipt_idempotency_ref"),
            (self.decision_reason_ref, "authority_lease_receipt_reason_ref"),
            (self.audit_ref, "authority_lease_receipt_audit_ref"),
            (self.rollback_ref, "authority_lease_receipt_rollback_ref"),
            (self.safe_disable_ref, "authority_lease_receipt_safe_disable_ref"),
            (self.kill_switch_ref, "authority_lease_receipt_kill_switch_ref"),
            (self.receipt_sink_ref, "authority_lease_receipt_sink_ref"),
        ]:
            validate_task_ref(value, field_name)
        for refs, field_name in [
            (self.denied_domain_refs, "authority_lease_denied_domain_ref"),
            (self.unsupported_adapter_refs, "authority_lease_unsupported_adapter_ref"),
        ]:
            _validate_ref_list(refs, field_name)
        validate_safe_task_text(self.safe_summary, "authority_lease_receipt_summary")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_lease_receipt_redaction")
        if (
            self.execution_performed
            or self.raw_paths_included
            or self.raw_prompt_included
            or self.raw_response_included
            or self.raw_provider_payload_included
        ):
            raise ValueError("AUTHORITY_LEASE_RECEIPT_MUST_BE_REDACTED")
        return self


class AuthorityStateReadModel(_AuthorityModel):
    schema_version: str = AUTHORITY_STATE_SCHEMA_VERSION
    contract_ref: str = AUTHORITY_STATE_CONTRACT_REF
    backend_owned: bool = True
    active_mode: TrustMode = TrustMode.read_only
    operator_summary: str = Field(..., min_length=1, max_length=640)
    api_ref: str = AUTHORITY_STATE_API_REF
    settings_route_ref: str = AUTHORITY_STATE_SETTINGS_ROUTE_REF
    cli_ref: str = AUTHORITY_STATE_CLI_REF
    target_modes: list[TrustMode] = Field(default_factory=lambda: list(TrustMode))
    target_domains: list[AuthorityDomain] = Field(default_factory=lambda: list(AuthorityDomain))
    policy_outcomes: list[AuthorityDecisionOutcome] = Field(
        default_factory=lambda: list(AuthorityDecisionOutcome)
    )
    active_leases: list[AuthorityLease] = Field(default_factory=list)
    capability_mappings: list[AuthorityCapabilityMapping] = Field(default_factory=list)
    recent_receipts: list[AuthorityLeaseReceipt] = Field(default_factory=list)
    sample_decisions: list[AuthorityPolicyDecision] = Field(default_factory=list)
    kill_switch_visible: bool = True
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    unknown_authority_default: AuthorityDecisionOutcome = AuthorityDecisionOutcome.deny
    unsupported_adapters_claimed_execution: bool = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    @model_validator(mode="after")
    def validate_state(self) -> "AuthorityStateReadModel":
        validate_task_ref(self.contract_ref, "authority_state_ref")
        for text in [self.api_ref, self.settings_route_ref, self.cli_ref]:
            validate_safe_task_text(text, "authority_state_route_or_cli")
        validate_safe_task_text(self.operator_summary, "authority_operator_summary")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_redaction")
        if (
            not self.backend_owned
            or not self.kill_switch_visible
            or not self.receipts_required
            or not self.audit_required
            or not self.redaction_required
            or self.unsupported_adapters_claimed_execution
        ):
            raise ValueError("AUTHORITY_STATE_GOVERNANCE_REQUIRED")
        if self.unknown_authority_default != AuthorityDecisionOutcome.deny.value:
            raise ValueError("AUTHORITY_UNKNOWN_MUST_DENY")
        return self


READ_PREPARE_CAPABILITIES = {
    AuthorityCapability.observe,
    AuthorityCapability.read,
    AuthorityCapability.draft,
    AuthorityCapability.prepare,
    AuthorityCapability.observe.value,
    AuthorityCapability.read.value,
    AuthorityCapability.draft.value,
    AuthorityCapability.prepare.value,
}


def evaluate_authority_request(
    request: AuthorityActionRequest,
    leases: list[AuthorityLease],
    *,
    now: datetime | None = None,
) -> AuthorityPolicyDecision:
    active_leases = [lease for lease in leases if lease.is_active(now=now)]
    matching = [
        lease
        for lease in active_leases
        if lease.grants(AuthorityDomain(request.domain), AuthorityCapability(request.capability))
    ]
    reason_refs: list[str] = []
    if request.kill_switch_engaged:
        reason_refs.append("reason-ref:authority:kill-switch-engaged")
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            reason_refs=reason_refs,
            operator_message="Denied because the authority kill switch is engaged.",
        )
    if request.unsupported_adapter:
        reason_refs.append("reason-ref:authority:adapter-unsupported")
        if request.draft_fallback_available:
            return _decision(
                request,
                AuthorityDecisionOutcome.degrade_to_draft,
                reason_refs=reason_refs,
                operator_message=(
                    "Degraded to draft because the requested adapter is not implemented."
                ),
                unsupported_adapter=True,
            )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            reason_refs=reason_refs,
            operator_message="Denied because the requested adapter is not implemented.",
            unsupported_adapter=True,
        )
    if not matching:
        reason_refs.append("reason-ref:authority:no-active-lease-for-domain-capability")
        if request.draft_fallback_available:
            return _decision(
                request,
                AuthorityDecisionOutcome.degrade_to_draft,
                reason_refs=reason_refs,
                operator_message=(
                    "Requires an active authority lease; degraded to a draft proposal."
                ),
            )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            reason_refs=reason_refs,
            operator_message="Denied because no active lease grants this domain and capability.",
        )
    lease = matching[0]
    mode = TrustMode(lease.mode)
    capability = AuthorityCapability(request.capability)
    if mode == TrustMode.ask_before_changes and capability not in READ_PREPARE_CAPABILITIES:
        reason_refs.append("reason-ref:authority:ask-before-changes-mode")
        return _decision(
            request,
            AuthorityDecisionOutcome.ask,
            lease=lease,
            reason_refs=reason_refs,
            operator_message="Ask before changes mode requires operator confirmation.",
            known_authority=True,
        )
    if mode == TrustMode.read_only and capability not in READ_PREPARE_CAPABILITIES:
        reason_refs.append("reason-ref:authority:read-only-mode")
        if request.draft_fallback_available:
            return _decision(
                request,
                AuthorityDecisionOutcome.degrade_to_draft,
                lease=lease,
                reason_refs=reason_refs,
                operator_message="Read-only mode degraded the action to a draft proposal.",
                known_authority=True,
            )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            lease=lease,
            reason_refs=reason_refs,
            operator_message="Requires a stronger trust mode for this capability.",
            known_authority=True,
        )
    reason_refs.append("reason-ref:authority:active-lease-grants-domain-capability")
    return _decision(
        request,
        AuthorityDecisionOutcome.allow,
        lease=lease,
        reason_refs=reason_refs,
        operator_message="Allowed by active authority lease.",
        known_authority=True,
    )


def _decision(
    request: AuthorityActionRequest,
    outcome: AuthorityDecisionOutcome,
    *,
    reason_refs: list[str],
    operator_message: str,
    lease: AuthorityLease | None = None,
    known_authority: bool = False,
    unsupported_adapter: bool = False,
) -> AuthorityPolicyDecision:
    lease_ref = lease.lease_ref if lease else None
    matched_mode = TrustMode(lease.mode) if lease else None
    receipt_ref = (
        _stable_ref(
            "receipt-ref:authority-policy",
            {"action_ref": request.action_ref, "lease_ref": lease_ref, "outcome": outcome},
        )
        if outcome in {AuthorityDecisionOutcome.allow, AuthorityDecisionOutcome.ask}
        else None
    )
    return AuthorityPolicyDecision(
        decision_ref=_stable_ref(
            "authority-policy-decision-ref",
            {
                "action_ref": request.action_ref,
                "domain": request.domain,
                "capability": request.capability,
                "lease_ref": lease_ref,
                "outcome": outcome,
            },
        ),
        action_ref=request.action_ref,
        outcome=outcome,
        domain=request.domain,
        capability=request.capability,
        lease_ref=lease_ref,
        matched_mode=matched_mode,
        required_mode=request.requested_mode,
        required_domain_refs=[f"authority-domain-ref:{_enum_value(request.domain)}"],
        required_capability_refs=[
            f"authority-capability-ref:{_enum_value(request.capability)}"
        ],
        reason_refs=list(dict.fromkeys(reason_refs)),
        operator_message=operator_message,
        known_authority=known_authority,
        unsupported_adapter=unsupported_adapter,
        rollback_ref=request.rollback_ref if lease is None else lease.rollback_ref,
        safe_disable_ref=(
            request.safe_disable_ref if lease is None else lease.safe_disable_ref
        ),
        kill_switch_ref=(
            "kill-switch-ref:authority-lease-local"
            if lease is None
            else lease.kill_switch_ref
        ),
        audit_record_ref=_stable_ref(
            "audit-ref:authority-policy",
            {
                "action_ref": request.action_ref,
                "domain": request.domain,
                "capability": request.capability,
                "lease_ref": lease_ref,
                "outcome": outcome,
            },
        ),
        receipt_ref=receipt_ref,
    )


def build_default_authority_leases() -> list[AuthorityLease]:
    return [
        AuthorityLease(
            lease_ref="authority-lease-ref:default-read-only-session",
            mode=TrustMode.read_only,
            scope=AuthorityLeaseScope.session,
            domains={
                AuthorityDomain.workspace: [
                    AuthorityCapability.observe,
                    AuthorityCapability.read,
                    AuthorityCapability.draft,
                    AuthorityCapability.prepare,
                ],
                AuthorityDomain.memory: [
                    AuthorityCapability.observe,
                    AuthorityCapability.read,
                    AuthorityCapability.draft,
                ],
                AuthorityDomain.email: [
                    AuthorityCapability.observe,
                    AuthorityCapability.draft,
                ],
                AuthorityDomain.calendar: [
                    AuthorityCapability.observe,
                    AuthorityCapability.draft,
                ],
                AuthorityDomain.provider_model_calls: [
                    AuthorityCapability.observe,
                    AuthorityCapability.read,
                ],
            },
            constraints={
                "session_scope_ref": "session-scope-ref:default-read-only",
                "mutation_allowed": False,
                "unsupported_adapters_execute": False,
            },
            ask_if=["reason-ref:authority:mode-escalation-requested"],
            hard_deny=[
                "reason-ref:authority:unknown-domain",
                "reason-ref:authority:unsupported-adapter-execution",
                "reason-ref:authority:cloud-production-without-mission-lease",
            ],
            unsupported_adapter_refs=[
                "adapter-ref:browser-execution:not-implemented",
                "adapter-ref:shopping-payment:not-implemented",
                "adapter-ref:home-assistant-write:not-implemented",
            ],
            safe_summary=(
                "Default read-only session lease allows inspection, planning, and "
                "draft proposals only; mutations require an explicit stronger lease."
            ),
        )
    ]


class AuthorityLeaseConflictError(RuntimeError):
    """Raised when an idempotency ref is reused for a different lease operation."""


def authority_state_dir() -> Path:
    value = os.environ.get(AUTHORITY_STATE_DIR_ENV, "").strip()
    if value:
        return Path(value).expanduser()
    return Path(".uaa") / "authority"


def _default_requested_domains(
    mode: TrustMode,
) -> dict[AuthorityDomain, list[AuthorityCapability]]:
    if mode == TrustMode.read_only:
        return {
            AuthorityDomain.workspace: [
                AuthorityCapability.observe,
                AuthorityCapability.read,
                AuthorityCapability.draft,
                AuthorityCapability.prepare,
            ],
            AuthorityDomain.memory: [
                AuthorityCapability.observe,
                AuthorityCapability.read,
                AuthorityCapability.draft,
            ],
        }
    if mode == TrustMode.ask_before_changes:
        return {
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ],
            AuthorityDomain.files: [
                AuthorityCapability.read,
                AuthorityCapability.write,
            ],
            AuthorityDomain.memory: [
                AuthorityCapability.read,
                AuthorityCapability.write,
            ],
        }
    return {
        AuthorityDomain.workspace: [
            AuthorityCapability.read,
            AuthorityCapability.write,
            AuthorityCapability.execute,
            AuthorityCapability.commit,
        ],
        AuthorityDomain.files: [
            AuthorityCapability.read,
            AuthorityCapability.write,
            AuthorityCapability.mutate,
        ],
        AuthorityDomain.memory: [
            AuthorityCapability.read,
            AuthorityCapability.write,
            AuthorityCapability.mutate,
        ],
    }


def _allowed_domain_capabilities(
    mode: TrustMode,
) -> dict[AuthorityDomain, set[AuthorityCapability]]:
    read_prepare = {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
    }
    local_change = read_prepare | {
        AuthorityCapability.write,
        AuthorityCapability.mutate,
        AuthorityCapability.commit,
    }
    local_execute = local_change | {AuthorityCapability.execute}
    if mode == TrustMode.read_only:
        return {
            AuthorityDomain.workspace: read_prepare,
            AuthorityDomain.files: read_prepare,
            AuthorityDomain.memory: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
                AuthorityCapability.draft,
            },
            AuthorityDomain.email: {AuthorityCapability.observe, AuthorityCapability.draft},
            AuthorityDomain.calendar: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.provider_model_calls: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
            },
        }
    if mode == TrustMode.ask_before_changes:
        return {
            AuthorityDomain.workspace: local_execute,
            AuthorityDomain.files: local_change,
            AuthorityDomain.memory: local_change,
            AuthorityDomain.contacts: local_change,
            AuthorityDomain.email: {AuthorityCapability.observe, AuthorityCapability.draft},
            AuthorityDomain.calendar: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.provider_model_calls: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
            },
        }
    return {
        AuthorityDomain.workspace: local_execute,
        AuthorityDomain.files: local_change,
        AuthorityDomain.memory: local_change,
        AuthorityDomain.contacts: local_change,
        AuthorityDomain.provider_model_calls: {
            AuthorityCapability.observe,
            AuthorityCapability.read,
        },
    }


def _filter_requested_domains(
    request: AuthorityLeaseIssueRequest,
) -> tuple[
    dict[AuthorityDomain, list[AuthorityCapability]],
    list[str],
    list[str],
]:
    mode = TrustMode(request.mode)
    requested = request.requested_domains or _default_requested_domains(mode)
    allowed = _allowed_domain_capabilities(mode)
    granted: dict[AuthorityDomain, list[AuthorityCapability]] = {}
    denied_refs: list[str] = []
    unsupported_refs: list[str] = []
    for domain, capabilities in requested.items():
        domain_value = AuthorityDomain(domain)
        allowed_capabilities = allowed.get(domain_value, set())
        granted_capabilities = [
            AuthorityCapability(capability)
            for capability in capabilities
            if AuthorityCapability(capability) in allowed_capabilities
        ]
        if granted_capabilities:
            granted[domain_value] = granted_capabilities
        denied = [
            AuthorityCapability(capability)
            for capability in capabilities
            if AuthorityCapability(capability) not in allowed_capabilities
        ]
        if denied or domain_value not in allowed:
            denied_refs.append(f"authority-domain-ref:{domain_value.value}")
        for capability in denied:
            unsupported_refs.append(
                "adapter-ref:"
                f"{domain_value.value}:{capability.value}"
                "-not-implemented-for-authority-lease-v1"
            )
        if domain_value not in allowed:
            unsupported_refs.append(
                f"adapter-ref:{domain_value.value}:not-implemented-for-authority-lease-v1"
            )
    return granted, list(dict.fromkeys(denied_refs)), list(dict.fromkeys(unsupported_refs))


class AuthorityLeaseStore:
    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or authority_state_dir()
        self.leases_path = self.state_dir / AUTHORITY_LEASES_FILE
        self.receipts_path = self.state_dir / AUTHORITY_LEASE_RECEIPTS_FILE

    def list_leases(self, *, active_only: bool = False) -> list[AuthorityLease]:
        leases = self._read_leases()
        if active_only:
            leases = [lease for lease in leases if lease.is_active()]
        return leases

    def list_receipts(self, *, limit: int = 20) -> list[AuthorityLeaseReceipt]:
        if not self.receipts_path.exists():
            return []
        receipts: list[AuthorityLeaseReceipt] = []
        for line in self.receipts_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            receipts.append(AuthorityLeaseReceipt(**json.loads(line)))
        return receipts[-limit:]

    def build_state_read_model(self) -> AuthorityStateReadModel:
        active = self.list_leases(active_only=True)
        return build_authority_state_read_model(
            active_leases=active or build_default_authority_leases(),
            recent_receipts=self.list_receipts(limit=8),
        )

    def issue_lease(
        self,
        request: AuthorityLeaseIssueRequest,
        *,
        idempotency_ref: str,
    ) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
        validate_task_ref(idempotency_ref, "authority_lease_idempotency_ref")
        existing = self._receipt_for_idempotency(idempotency_ref)
        if existing is not None:
            if existing.operation != "issue":
                raise AuthorityLeaseConflictError("AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT")
            lease = self._lease_by_ref(existing.lease_ref)
            return lease, existing.model_copy(update={"status": "replayed"})
        granted, denied_refs, unsupported_refs = _filter_requested_domains(request)
        lease_ref = _stable_ref(
            "authority-lease-ref",
            {
                "idempotency_ref": idempotency_ref,
                "mode": request.mode,
                "scope": request.scope,
                "mission_ref": request.mission_ref,
                "granted": {
                    _enum_value(domain): [_enum_value(capability) for capability in caps]
                    for domain, caps in granted.items()
                },
            },
        )
        if not granted:
            receipt = self._receipt(
                operation="issue",
                status="denied",
                lease_ref=lease_ref,
                idempotency_ref=idempotency_ref,
                request=request,
                granted_domains={},
                denied_domain_refs=denied_refs or ["authority-domain-ref:none-granted"],
                unsupported_adapter_refs=unsupported_refs,
                safe_summary=(
                    "Authority lease request denied because no requested domain "
                    "capability is implemented for this trust mode."
                ),
            )
            self._append_receipt(receipt)
            return None, receipt
        now = utc_now()
        lease = AuthorityLease(
            lease_ref=lease_ref,
            mode=request.mode,
            scope=request.scope,
            mission_ref=request.mission_ref,
            operator_ref=request.operator_ref,
            domains=granted,
            constraints={
                **request.constraints,
                "decision_reason_ref": request.decision_reason_ref,
                "idempotency_ref": idempotency_ref,
                "unsupported_adapters_execute": False,
            },
            unsupported_adapter_refs=unsupported_refs,
            safe_disable_ref=f"safe-disable-ref:{lease_ref.split(':')[-1]}",
            rollback_ref=f"rollback-ref:{lease_ref.split(':')[-1]}",
            kill_switch_ref="kill-switch-ref:authority-lease-local",
            audit_ref=f"audit-ref:{lease_ref.split(':')[-1]}",
            receipt_sink_ref="receipt-sink-ref:authority-lease-action-receipts",
            issued_at=now,
            expires_at=now + timedelta(minutes=request.duration_minutes),
            safe_summary=request.safe_summary,
        )
        leases = [item for item in self._read_leases() if item.lease_ref != lease.lease_ref]
        leases.append(lease)
        self._write_leases(leases)
        receipt = self._receipt(
            operation="issue",
            status="issued",
            lease_ref=lease.lease_ref,
            idempotency_ref=idempotency_ref,
            request=request,
            granted_domains=granted,
            denied_domain_refs=denied_refs,
            unsupported_adapter_refs=unsupported_refs,
            safe_summary="Authority lease issued with safe refs, receipts, and kill-switch posture.",
        )
        self._append_receipt(receipt)
        return lease, receipt

    def revoke_lease(
        self,
        request: AuthorityLeaseRevokeRequest,
        *,
        idempotency_ref: str,
    ) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
        validate_task_ref(idempotency_ref, "authority_lease_idempotency_ref")
        existing = self._receipt_for_idempotency(idempotency_ref)
        if existing is not None:
            if existing.operation != "revoke":
                raise AuthorityLeaseConflictError("AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT")
            return self._lease_by_ref(existing.lease_ref), existing.model_copy(
                update={"status": "replayed"}
            )
        leases = self._read_leases()
        lease = next((item for item in leases if item.lease_ref == request.lease_ref), None)
        if lease is None:
            receipt = AuthorityLeaseReceipt(
                operation="revoke",
                status="denied",
                receipt_ref=_stable_ref(
                    "receipt-ref:authority-lease",
                    {"operation": "revoke", "idempotency_ref": idempotency_ref},
                ),
                lease_ref=request.lease_ref,
                idempotency_ref=idempotency_ref,
                decision_reason_ref=request.decision_reason_ref,
                mode=TrustMode.read_only,
                scope=AuthorityLeaseScope.session,
                requested_domains={},
                granted_domains={},
                denied_domain_refs=["authority-lease-ref:not-found"],
                unsupported_adapter_refs=[],
                audit_ref=_stable_ref(
                    "audit-ref:authority-lease",
                    {"operation": "revoke-denied", "idempotency_ref": idempotency_ref},
                ),
                rollback_ref="rollback-ref:authority-lease-noop",
                safe_disable_ref="safe-disable-ref:authority-lease-noop",
                kill_switch_ref="kill-switch-ref:authority-lease-local",
                receipt_sink_ref="receipt-sink-ref:authority-lease-action-receipts",
                safe_summary="Authority lease revoke denied because the lease ref was not found.",
            )
            self._append_receipt(receipt)
            return None, receipt
        revoked = lease.model_copy(
            update={
                "status": AuthorityLeaseStatus.revoked,
                "constraints": {
                    **lease.constraints,
                    "revocation_reason_ref": request.decision_reason_ref,
                    "revocation_idempotency_ref": idempotency_ref,
                },
            }
        )
        self._write_leases(
            [revoked if item.lease_ref == lease.lease_ref else item for item in leases]
        )
        receipt = AuthorityLeaseReceipt(
            operation="revoke",
            status="revoked",
            receipt_ref=_stable_ref(
                "receipt-ref:authority-lease",
                {"operation": "revoke", "lease_ref": lease.lease_ref},
            ),
            lease_ref=lease.lease_ref,
            idempotency_ref=idempotency_ref,
            decision_reason_ref=request.decision_reason_ref,
            mode=TrustMode(lease.mode),
            scope=AuthorityLeaseScope(lease.scope),
            requested_domains=lease.domains,
            granted_domains={},
            denied_domain_refs=[],
            unsupported_adapter_refs=lease.unsupported_adapter_refs,
            audit_ref=_stable_ref(
                "audit-ref:authority-lease",
                {"operation": "revoke", "lease_ref": lease.lease_ref},
            ),
            rollback_ref=lease.rollback_ref,
            safe_disable_ref=lease.safe_disable_ref,
            kill_switch_ref=lease.kill_switch_ref,
            receipt_sink_ref=lease.receipt_sink_ref,
            safe_summary=request.safe_summary,
        )
        self._append_receipt(receipt)
        return revoked, receipt

    def _receipt(
        self,
        *,
        operation: Literal["issue", "revoke"],
        status: Literal["issued", "revoked", "replayed", "denied"],
        lease_ref: str,
        idempotency_ref: str,
        request: AuthorityLeaseIssueRequest,
        granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
        denied_domain_refs: list[str],
        unsupported_adapter_refs: list[str],
        safe_summary: str,
    ) -> AuthorityLeaseReceipt:
        return AuthorityLeaseReceipt(
            operation=operation,
            status=status,
            receipt_ref=_stable_ref(
                "receipt-ref:authority-lease",
                {"operation": operation, "idempotency_ref": idempotency_ref},
            ),
            lease_ref=lease_ref,
            idempotency_ref=idempotency_ref,
            decision_reason_ref=request.decision_reason_ref,
            mode=request.mode,
            scope=request.scope,
            requested_domains=request.requested_domains
            or _default_requested_domains(TrustMode(request.mode)),
            granted_domains=granted_domains,
            denied_domain_refs=denied_domain_refs,
            unsupported_adapter_refs=unsupported_adapter_refs,
            audit_ref=_stable_ref(
                "audit-ref:authority-lease",
                {"operation": operation, "idempotency_ref": idempotency_ref},
            ),
            rollback_ref=f"rollback-ref:{lease_ref.split(':')[-1]}",
            safe_disable_ref=f"safe-disable-ref:{lease_ref.split(':')[-1]}",
            kill_switch_ref="kill-switch-ref:authority-lease-local",
            receipt_sink_ref="receipt-sink-ref:authority-lease-action-receipts",
            safe_summary=safe_summary,
        )

    def _read_leases(self) -> list[AuthorityLease]:
        if not self.leases_path.exists():
            return []
        payload = json.loads(self.leases_path.read_text(encoding="utf-8"))
        return [AuthorityLease(**item) for item in payload.get("leases", [])]

    def _write_leases(self, leases: list[AuthorityLease]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "uaa-authority-lease-store.v1",
            "leases": [lease.model_dump(mode="json") for lease in leases],
        }
        self.leases_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _append_receipt(self, receipt: AuthorityLeaseReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt.model_dump(mode="json"), sort_keys=True) + "\n")

    def _receipt_for_idempotency(
        self,
        idempotency_ref: str,
    ) -> AuthorityLeaseReceipt | None:
        for receipt in reversed(self.list_receipts(limit=200)):
            if receipt.idempotency_ref == idempotency_ref:
                return receipt
        return None

    def _lease_by_ref(self, lease_ref: str) -> AuthorityLease | None:
        return next((lease for lease in self._read_leases() if lease.lease_ref == lease_ref), None)


def build_existing_lane_authority_mappings() -> list[AuthorityCapabilityMapping]:
    return [
        _mapping(
            "lane-ref:runtime-command-git-status",
            "Git status",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented",
            ["GET /api/runtime/capabilities"],
            ["repo-local-command:uaa-runtime-command-git-status"],
            "Allowed by Read-only with workspace/read when the exact gateway command shape matches.",
        ),
        _mapping(
            "lane-ref:runtime-command-focused-pytest",
            "Focused pytest",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required",
            ["POST /api/runtime/command/run"],
            ["repo-local-command:uaa-runtime-command-run"],
            "Requires Approved safe local work with workspace/execute plus RuntimeGateway allowlist and receipts.",
        ),
        _mapping(
            "lane-ref:runtime-command-repo-doctor",
            "Repo doctor",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required",
            ["POST /api/runtime/command/run"],
            ["repo-local-command:uaa-runtime-command-run"],
            "Requires Approved safe local work with workspace/execute plus RuntimeGateway allowlist and receipts.",
        ),
        _mapping(
            "lane-ref:work-board-reorder",
            "Work Board reorder",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/work-board/reorder"],
            ["scripts/dev/uaa_work_board.py inspect-reorder-receipt"],
            "Requires Workspace write authority plus exact approval, idempotency, receipts, and rollback refs.",
        ),
        _mapping(
            "lane-ref:work-board-card-create",
            "Work Board card create",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/work-board/cards"],
            ["scripts/dev/uaa_work_board.py inspect-card-create-receipt"],
            "Requires Workspace write authority plus exact approval, idempotency, receipts, and rollback refs.",
        ),
        _mapping(
            "lane-ref:action-inbox-local-task-commit",
            "Action Inbox local task commit",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/actions/{action_id}/local-task/commit"],
            ["repo-local-command:inspect-action-inbox-local-task-commit"],
            "Requires Workspace write authority plus exact Action Inbox approval, idempotency, receipts, and safe-disable refs.",
        ),
        _mapping(
            "lane-ref:memory-review-accept-correct",
            "Reviewed memory write",
            AuthorityDomain.memory,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_ask_required",
            ["POST /control-center/memory/review/{candidate_ref}/accept"],
            ["repo-local-command:inspect-memory-review"],
            "Requires Memory domain write authority; Ask before changes returns ask until an operator confirms.",
        ),
        _mapping(
            "lane-ref:crm-local-mutation",
            "CRM local mutation",
            AuthorityDomain.contacts,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/crm/local-mutations"],
            ["repo-local-command:uaa-crm:mutate-local"],
            "Requires Contacts write authority plus exact approval, idempotency, receipts, and rollback refs for local CRM state only.",
        ),
        _mapping(
            "lane-ref:source-readiness-email-calendar",
            "Email and calendar metadata readiness",
            AuthorityDomain.email,
            AuthorityCapability.observe,
            TrustMode.read_only,
            "partial_metadata_contract_only",
            ["GET /control-center/sources/readiness"],
            ["repo-local-command:inspect-source-readiness-metadata-contracts"],
            "Read-only mode may show safe metadata contract refs; live account adapters remain unsupported.",
            unsupported_adapter_refs=[
                "adapter-ref:email-live-fetch:not-implemented",
                "adapter-ref:calendar-live-fetch:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:browser-shopping-mission",
            "Browser ticket purchase mission",
            AuthorityDomain.shopping_payments,
            AuthorityCapability.purchase_under_budget,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            "Requires Delegated mission with Browser and Shopping domains, budget constraints, receipts, and implemented adapters.",
            unsupported_adapter_refs=[
                "adapter-ref:browser-execution:not-implemented",
                "adapter-ref:shopping-payment:not-implemented",
            ],
        ),
    ]


def build_authority_state_read_model(
    *,
    active_leases: list[AuthorityLease] | None = None,
    recent_receipts: list[AuthorityLeaseReceipt] | None = None,
) -> AuthorityStateReadModel:
    leases = active_leases or build_default_authority_leases()
    samples = [
        evaluate_authority_request(
            AuthorityActionRequest(
                action_ref="authority-action-ref:sample-workspace-read",
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.read,
                safe_summary="Inspect workspace state under the default read-only lease.",
                route_ref="GET /api/runtime/authority-state",
            ),
            leases,
        ),
        evaluate_authority_request(
            AuthorityActionRequest(
                action_ref="authority-action-ref:sample-workspace-execute",
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.execute,
                safe_summary="Run a workspace command that requires a stronger lease.",
                route_ref="POST /api/runtime/command/run",
                draft_fallback_available=True,
                requested_mode=TrustMode.approved_safe_local_work_session,
            ),
            leases,
        ),
        evaluate_authority_request(
            AuthorityActionRequest(
                action_ref="authority-action-ref:sample-ticket-purchase",
                domain=AuthorityDomain.shopping_payments,
                capability=AuthorityCapability.purchase_under_budget,
                safe_summary="Ticket purchase mission remains unsupported without browser and payment adapters.",
                route_ref="GET /api/runtime/authority-state",
                draft_fallback_available=False,
                unsupported_adapter=True,
                requested_mode=TrustMode.delegated_mission_autonomous_window,
            ),
            leases,
        ),
    ]
    return AuthorityStateReadModel(
        active_mode=TrustMode(leases[-1].mode) if leases else TrustMode.read_only,
        operator_summary=(
            "Authority is now modeled as trust modes, explicit domains, and "
            "session or mission leases. Unknown authority denies by default; "
            "unsupported adapters are shown as planned or blocked instead of "
            "pretending execution exists."
        ),
        active_leases=leases,
        capability_mappings=build_existing_lane_authority_mappings(),
        recent_receipts=recent_receipts or [],
        sample_decisions=samples,
    )


def _mapping(
    lane_ref: str,
    label: str,
    domain: AuthorityDomain,
    capability: AuthorityCapability,
    required_mode: TrustMode,
    status: str,
    route_refs: list[str],
    cli_refs: list[str],
    operator_copy: str,
    *,
    unsupported_adapter_refs: list[str] | None = None,
) -> AuthorityCapabilityMapping:
    return AuthorityCapabilityMapping(
        lane_ref=lane_ref,
        label=label,
        domain=domain,
        capability=capability,
        required_mode=required_mode,
        status=status,
        route_refs=route_refs,
        cli_refs=cli_refs,
        evidence_refs=[f"evidence-ref:authority-mapping:{lane_ref.split(':')[-1]}"],
        unsupported_adapter_refs=unsupported_adapter_refs or [],
        operator_copy=operator_copy,
    )
