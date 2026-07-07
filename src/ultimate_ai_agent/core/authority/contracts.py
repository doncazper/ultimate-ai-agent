from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections.abc import Callable
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
AUTHORITY_MISSION_PLAN_SCHEMA_VERSION = "uaa-authority-mission-plan.v1"
AUTHORITY_STATE_CONTRACT_REF = "contract-ref:authority-modes-mission-leases:v1"
AUTHORITY_STATE_API_REF = "GET /api/runtime/authority-state"
AUTHORITY_STATE_SETTINGS_ROUTE_REF = "GET /control-center/settings/status#authority_lease_state"
AUTHORITY_STATE_CLI_REF = "repo-local-command:uaa-runtime-inspect-authority-state"
AUTHORITY_MISSION_PLAN_ROUTE_REF = "POST /api/runtime/authority-missions/plan"
AUTHORITY_MISSION_PLAN_CLI_REF = "repo-local-command:uaa-runtime-plan-authority-mission"
AUTHORITY_STATE_DIR_ENV = "UAA_AUTHORITY_STATE_DIR"
AUTHORITY_LEASE_KILL_SWITCH_ENV = "UAA_AUTHORITY_LEASE_KILL_SWITCH"
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
        if (
            self.mode == TrustMode.delegated_mission_autonomous_window.value
            and self.scope != AuthorityLeaseScope.mission.value
        ):
            raise ValueError("AUTHORITY_DELEGATED_MISSION_REQUIRES_MISSION_SCOPE")
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
        granted = {AuthorityCapability(item) for item in values}
        requested = AuthorityCapability(capability)
        return any(_capability_grants(item, requested) for item in granted)


_CAPABILITY_IMPLICATIONS: dict[AuthorityCapability, set[AuthorityCapability]] = {
    AuthorityCapability.observe: {AuthorityCapability.observe},
    AuthorityCapability.read: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
    },
    AuthorityCapability.draft: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
    },
    AuthorityCapability.prepare: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
    },
    AuthorityCapability.write: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.write,
    },
    AuthorityCapability.mutate: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.write,
        AuthorityCapability.mutate,
    },
    AuthorityCapability.execute: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.execute,
    },
    AuthorityCapability.commit: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.write,
        AuthorityCapability.commit,
    },
    AuthorityCapability.send: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.send,
    },
    AuthorityCapability.purchase: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.purchase,
    },
    AuthorityCapability.purchase_under_budget: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.purchase_under_budget,
    },
    AuthorityCapability.admin: set(AuthorityCapability),
    AuthorityCapability.destructive: set(AuthorityCapability),
}


def _capability_grants(
    granted: AuthorityCapability,
    requested: AuthorityCapability,
) -> bool:
    return requested in _CAPABILITY_IMPLICATIONS.get(granted, {granted})


class AuthorityActionRequest(_AuthorityModel):
    action_ref: str = Field(..., min_length=1)
    domain: AuthorityDomain
    capability: AuthorityCapability
    safe_summary: str = Field(..., min_length=1, max_length=520)
    resource_refs: list[str] = Field(default_factory=list)
    route_ref: str | None = None
    capability_ref: str | None = None
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
            (self.capability_ref, "authority_capability_ref"),
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
    capability_ref: str | None = None
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
            (self.capability_ref, "authority_capability_ref"),
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


class AuthorityDecisionPreview(_AuthorityModel):
    schema_version: Literal["uaa-authority-decision-preview.v1"] = (
        "uaa-authority-decision-preview.v1"
    )
    preview_ref: str = Field(..., min_length=1)
    decision: AuthorityPolicyDecision
    active_lease_refs: list[str] = Field(default_factory=list)
    preview_receipt_ref: str = Field(..., min_length=1)
    audit_record_ref: str = Field(..., min_length=1)
    operator_summary: str = Field(..., min_length=1, max_length=640)
    execution_performed: bool = False
    mutation_performed: bool = False
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    unknown_authority_default: AuthorityDecisionOutcome = AuthorityDecisionOutcome.deny
    unsupported_adapters_claimed_execution: bool = False
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    @model_validator(mode="after")
    def validate_preview(self) -> "AuthorityDecisionPreview":
        for value, field_name in [
            (self.preview_ref, "authority_decision_preview_ref"),
            (self.preview_receipt_ref, "authority_decision_preview_receipt_ref"),
            (self.audit_record_ref, "authority_decision_preview_audit_ref"),
        ]:
            validate_task_ref(value, field_name)
        _validate_ref_list(self.active_lease_refs, "authority_decision_preview_lease_ref")
        validate_safe_task_text(self.operator_summary, "authority_decision_preview_summary")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_decision_preview_redaction")
        if (
            self.execution_performed
            or self.mutation_performed
            or not self.safe_refs_only
            or self.raw_paths_included
            or self.raw_prompt_included
            or self.raw_response_included
            or self.raw_provider_payload_included
            or self.unsupported_adapters_claimed_execution
        ):
            raise ValueError("AUTHORITY_DECISION_PREVIEW_MUST_NOT_EXECUTE")
        if (
            not self.receipts_required
            or not self.audit_required
            or not self.redaction_required
            or self.unknown_authority_default != AuthorityDecisionOutcome.deny.value
        ):
            raise ValueError("AUTHORITY_DECISION_PREVIEW_GOVERNANCE_REQUIRED")
        return self


class AuthorityDecisionCatalogEntry(_AuthorityModel):
    catalog_ref: str = Field(..., min_length=1)
    authority_capability_ref: str = Field(..., min_length=1)
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=80)
    route_refs: list[str] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    decision: AuthorityPolicyDecision
    operator_summary: str = Field(..., min_length=1, max_length=520)
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False

    @model_validator(mode="after")
    def validate_catalog_entry(self) -> "AuthorityDecisionCatalogEntry":
        _validate_ref_list(
            [
                self.catalog_ref,
                self.authority_capability_ref,
                self.lane_ref,
                *self.evidence_refs,
                *self.unsupported_adapter_refs,
            ],
            "authority_decision_catalog_ref",
        )
        for text in [
            self.label,
            self.status,
            self.operator_summary,
            *self.route_refs,
            *self.cli_refs,
        ]:
            validate_safe_task_text(text, "authority_decision_catalog_text")
        if (
            not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
        ):
            raise ValueError("AUTHORITY_DECISION_CATALOG_MUST_NOT_EXECUTE")
        return self


class AuthorityMissionPlanRequest(_AuthorityModel):
    schema_version: Literal["uaa-authority-mission-plan-request.v1"] = (
        "uaa-authority-mission-plan-request.v1"
    )
    mission_ref: str = Field(..., min_length=1)
    safe_goal_summary: str = Field(..., min_length=1, max_length=640)
    requested_mode: TrustMode = TrustMode.delegated_mission_autonomous_window
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    action_requests: list[AuthorityActionRequest] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    decision_reason_ref: str = "reason-ref:authority-mission-plan"
    operator_ref: str = "operator-ref:local-user"
    duration_minutes: int = Field(default=120, ge=5, le=480)
    draft_fallback_available: bool = True

    @model_validator(mode="after")
    def validate_mission_plan_request(self) -> "AuthorityMissionPlanRequest":
        for value, field_name in [
            (self.mission_ref, "authority_mission_ref"),
            (self.decision_reason_ref, "authority_mission_decision_reason_ref"),
            (self.operator_ref, "authority_mission_operator_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_goal_summary, "authority_mission_goal_summary")
        validate_safe_task_text(_enum_value(self.requested_mode), "authority_mission_mode")
        validate_safe_task_payload(self.constraints, "authority_mission_constraints")
        if not self.requested_domains and not self.action_requests:
            raise ValueError("AUTHORITY_MISSION_PLAN_REQUIRES_DOMAIN_OR_ACTION")
        for domain, capabilities in self.requested_domains.items():
            validate_safe_task_text(_enum_value(domain), "authority_mission_domain")
            if not capabilities:
                raise ValueError("AUTHORITY_MISSION_DOMAIN_CAPABILITIES_REQUIRED")
            for capability in capabilities:
                validate_safe_task_text(
                    _enum_value(capability),
                    "authority_mission_capability",
                )
        return self


class AuthorityMissionPlan(_AuthorityModel):
    schema_version: Literal["uaa-authority-mission-plan.v1"] = (
        "uaa-authority-mission-plan.v1"
    )
    plan_ref: str = Field(..., min_length=1)
    mission_ref: str = Field(..., min_length=1)
    requested_mode: TrustMode
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    denied_domain_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    action_previews: list[AuthorityDecisionPreview] = Field(default_factory=list)
    active_lease_refs: list[str] = Field(default_factory=list)
    lease_issue_request_ref: str = Field(..., min_length=1)
    lease_issue_request: AuthorityLeaseIssueRequest
    lease_issue_ready: bool = False
    required_domain_refs: list[str] = Field(default_factory=list)
    required_capability_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    route_ref: str = AUTHORITY_MISSION_PLAN_ROUTE_REF
    cli_ref: str = AUTHORITY_MISSION_PLAN_CLI_REF
    operator_summary: str = Field(..., min_length=1, max_length=720)
    next_safe_action: str = Field(..., min_length=1, max_length=520)
    execution_performed: bool = False
    mutation_performed: bool = False
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    unknown_authority_default: AuthorityDecisionOutcome = AuthorityDecisionOutcome.deny
    unsupported_adapters_claimed_execution: bool = False
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    kill_switch_visible: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    @model_validator(mode="after")
    def validate_mission_plan(self) -> "AuthorityMissionPlan":
        for value, field_name in [
            (self.plan_ref, "authority_mission_plan_ref"),
            (self.mission_ref, "authority_mission_ref"),
            (self.lease_issue_request_ref, "authority_mission_lease_request_ref"),
        ]:
            validate_task_ref(value, field_name)
        for refs, field_name in [
            (self.denied_domain_refs, "authority_mission_denied_domain_ref"),
            (self.unsupported_adapter_refs, "authority_mission_unsupported_ref"),
            (self.active_lease_refs, "authority_mission_active_lease_ref"),
            (self.required_domain_refs, "authority_mission_required_domain_ref"),
            (self.required_capability_refs, "authority_mission_required_capability_ref"),
            (self.blocked_reason_refs, "authority_mission_blocked_reason_ref"),
        ]:
            _validate_ref_list(refs, field_name)
        for text in [self.route_ref, self.cli_ref]:
            validate_safe_task_text(text, "authority_mission_route_or_cli")
        validate_safe_task_text(self.operator_summary, "authority_mission_summary")
        validate_safe_task_text(self.next_safe_action, "authority_mission_next_action")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_mission_redaction")
        if (
            self.execution_performed
            or self.mutation_performed
            or not self.safe_refs_only
            or self.raw_paths_included
            or self.raw_prompt_included
            or self.raw_response_included
            or self.raw_provider_payload_included
            or self.unsupported_adapters_claimed_execution
        ):
            raise ValueError("AUTHORITY_MISSION_PLAN_MUST_NOT_EXECUTE")
        if (
            not self.receipts_required
            or not self.audit_required
            or not self.redaction_required
            or not self.kill_switch_visible
            or self.unknown_authority_default != AuthorityDecisionOutcome.deny.value
        ):
            raise ValueError("AUTHORITY_MISSION_PLAN_GOVERNANCE_REQUIRED")
        if self.lease_issue_ready and (
            self.denied_domain_refs or self.unsupported_adapter_refs
        ):
            raise ValueError("AUTHORITY_MISSION_PLAN_UNSUPPORTED_NOT_ISSUE_READY")
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
    unsupported_adapter_blocks_capability: bool = False
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
        if (
            self.unsupported_adapter_blocks_capability
            and not self.unsupported_adapter_refs
        ):
            raise ValueError("AUTHORITY_MAPPING_BLOCKING_UNSUPPORTED_REFS_REQUIRED")
        if (
            self.status.startswith("planned_unsupported")
            and not self.unsupported_adapter_refs
        ):
            raise ValueError("AUTHORITY_MAPPING_PLANNED_UNSUPPORTED_REFS_REQUIRED")
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
    approval_ref: str | None = None
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_issue_request(self) -> "AuthorityLeaseIssueRequest":
        for value, field_name in [
            (self.mission_ref, "authority_lease_mission_ref"),
            (self.operator_ref, "authority_lease_operator_ref"),
            (self.decision_reason_ref, "authority_lease_decision_reason_ref"),
            (self.approval_ref, "authority_lease_approval_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "authority_lease_issue_summary")
        validate_safe_task_payload(self.constraints, "authority_lease_issue_constraints")
        validate_safe_task_payload(self.approval_grants, "authority_lease_approval_grants")
        if self.scope == AuthorityLeaseScope.mission.value and not self.mission_ref:
            raise ValueError("AUTHORITY_LEASE_MISSION_REF_REQUIRED")
        if (
            self.mode == TrustMode.delegated_mission_autonomous_window.value
            and self.scope != AuthorityLeaseScope.mission.value
        ):
            raise ValueError("AUTHORITY_DELEGATED_MISSION_REQUIRES_MISSION_SCOPE")
        for domain, capabilities in self.requested_domains.items():
            validate_safe_task_text(_enum_value(domain), "authority_issue_domain")
            for capability in capabilities:
                validate_safe_task_text(
                    _enum_value(capability),
                    "authority_issue_capability",
                )
        return self


class AuthorityLeaseApproveAndIssueRequest(_AuthorityModel):
    lease_issue_request: AuthorityLeaseIssueRequest
    approved_by_actor_ref: str = "operator-ref:local-user"
    approval_safe_summary: str = Field(
        default=(
            "Operator approved this exact AuthorityLease mode, domain, "
            "capability, scope, and duration."
        ),
        min_length=1,
        max_length=520,
    )

    @model_validator(mode="after")
    def validate_approve_and_issue_request(
        self,
    ) -> "AuthorityLeaseApproveAndIssueRequest":
        validate_task_ref(
            self.approved_by_actor_ref,
            "authority_lease_approved_by_actor_ref",
        )
        validate_safe_task_text(
            self.approval_safe_summary,
            "authority_lease_approval_safe_summary",
        )
        if (
            self.lease_issue_request.approval_ref is not None
            or self.lease_issue_request.approval_grants
        ):
            raise ValueError("AUTHORITY_LEASE_INLINE_APPROVAL_GRANTS_DENIED")
        return self


class AuthorityDecisionSummary(_AuthorityModel):
    schema_version: Literal["uaa-authority-decision-summary.v1"] = (
        "uaa-authority-decision-summary.v1"
    )
    total_capabilities: int = Field(default=0, ge=0)
    active_lease_count: int = Field(default=0, ge=0)
    outcome_counts: dict[str, int] = Field(default_factory=dict)
    domain_counts: dict[str, int] = Field(default_factory=dict)
    status_counts: dict[str, int] = Field(default_factory=dict)
    allowed_capability_refs: list[str] = Field(default_factory=list)
    ask_capability_refs: list[str] = Field(default_factory=list)
    degraded_capability_refs: list[str] = Field(default_factory=list)
    denied_capability_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    operator_summary: str = Field(..., min_length=1, max_length=520)
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False

    @model_validator(mode="after")
    def validate_summary(self) -> "AuthorityDecisionSummary":
        for counts, field_name in [
            (self.outcome_counts, "authority_decision_summary_outcome"),
            (self.domain_counts, "authority_decision_summary_domain"),
            (self.status_counts, "authority_decision_summary_status"),
        ]:
            for key, value in counts.items():
                validate_safe_task_text(key, field_name)
                if value < 0:
                    raise ValueError("AUTHORITY_DECISION_SUMMARY_COUNT_INVALID")
        for refs, field_name in [
            (self.allowed_capability_refs, "authority_decision_summary_allowed_ref"),
            (self.ask_capability_refs, "authority_decision_summary_ask_ref"),
            (self.degraded_capability_refs, "authority_decision_summary_degraded_ref"),
            (self.denied_capability_refs, "authority_decision_summary_denied_ref"),
            (self.blocked_reason_refs, "authority_decision_summary_reason_ref"),
            (
                self.unsupported_adapter_refs,
                "authority_decision_summary_unsupported_ref",
            ),
        ]:
            _validate_ref_list(refs, field_name)
        validate_safe_task_text(self.operator_summary, "authority_decision_summary")
        if (
            not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
        ):
            raise ValueError("AUTHORITY_DECISION_SUMMARY_MUST_NOT_EXECUTE")
        return self


class AuthorityModeCatalogEntry(_AuthorityModel):
    schema_version: Literal["uaa-authority-mode-catalog-entry.v1"] = (
        "uaa-authority-mode-catalog-entry.v1"
    )
    mode: TrustMode
    scope: AuthorityLeaseScope
    status: str = Field(..., min_length=1, max_length=80)
    default_requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    grantable_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    granted_default_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    denied_default_domain_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    approval_required: bool = False
    issue_ready: bool = False
    requires_mission_ref: bool = False
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    operator_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_mode_catalog_entry(self) -> "AuthorityModeCatalogEntry":
        for value in [self.mode, self.scope, self.status]:
            validate_safe_task_text(_enum_value(value), "authority_mode_catalog_text")
        for domains, field_name in [
            (self.default_requested_domains, "authority_mode_default_domain"),
            (self.grantable_domains, "authority_mode_grantable_domain"),
        ]:
            if not domains:
                raise ValueError("AUTHORITY_MODE_CATALOG_DOMAINS_REQUIRED")
            for domain, capabilities in domains.items():
                validate_safe_task_text(_enum_value(domain), field_name)
                if not capabilities:
                    raise ValueError("AUTHORITY_MODE_CATALOG_CAPABILITIES_REQUIRED")
                for capability in capabilities:
                    validate_safe_task_text(
                        _enum_value(capability),
                        "authority_mode_catalog_capability",
                    )
        for domain, capabilities in self.granted_default_domains.items():
            validate_safe_task_text(_enum_value(domain), "authority_mode_granted_domain")
            if not capabilities:
                raise ValueError("AUTHORITY_MODE_CATALOG_CAPABILITIES_REQUIRED")
            for capability in capabilities:
                validate_safe_task_text(
                    _enum_value(capability),
                    "authority_mode_catalog_capability",
                )
        for refs, field_name in [
            (self.denied_default_domain_refs, "authority_mode_denied_ref"),
            (self.unsupported_adapter_refs, "authority_mode_unsupported_ref"),
            (self.blocked_reason_refs, "authority_mode_blocked_reason_ref"),
        ]:
            _validate_ref_list(refs, field_name)
        validate_safe_task_text(self.operator_summary, "authority_mode_catalog_summary")
        if not self.safe_refs_only or self.execution_performed or self.mutation_performed:
            raise ValueError("AUTHORITY_MODE_CATALOG_MUST_NOT_EXECUTE")
        return self


class AuthorityLeaseApprovalRequirement(_AuthorityModel):
    schema_version: Literal["uaa-authority-lease-approval-requirement.v1"] = (
        "uaa-authority-lease-approval-requirement.v1"
    )
    approval_required: bool
    approval_scope_ref: str = Field(..., min_length=1)
    approval_request_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    subject_ref: str = Field(..., min_length=1)
    requested_action: Literal["issue_authority_lease"] = "issue_authority_lease"
    resource_refs: list[str] = Field(default_factory=list)
    operator_ref: str = Field(..., min_length=1)
    risk_level: Literal["safe", "high"] = "high"
    data_classification: Literal["system_internal"] = "system_internal"
    purpose: str = Field(..., min_length=1, max_length=260)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    @model_validator(mode="after")
    def validate_requirement(self) -> "AuthorityLeaseApprovalRequirement":
        for value, field_name in [
            (self.approval_scope_ref, "authority_lease_approval_scope_ref"),
            (self.approval_request_ref, "authority_lease_approval_request_ref"),
            (self.run_ref, "authority_lease_approval_run_ref"),
            (self.subject_ref, "authority_lease_approval_subject_ref"),
            (self.operator_ref, "authority_lease_approval_operator_ref"),
        ]:
            validate_task_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "authority_lease_approval_resource_ref")
        validate_safe_task_text(self.purpose, "authority_lease_approval_purpose")
        validate_safe_task_text(self.safe_summary, "authority_lease_approval_summary")
        return self


AuthorityLeaseApprovalValidator = Callable[
    [AuthorityLeaseIssueRequest, AuthorityLeaseApprovalRequirement],
    Any,
]


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
    lease_issued_at: datetime | None = None
    lease_expires_at: datetime | None = None
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    denied_domain_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    audit_ref: str
    rollback_ref: str
    safe_disable_ref: str
    kill_switch_ref: str
    receipt_sink_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=520)
    approval_required: bool = False
    approval_validated: bool = False
    approval_ref: str | None = None
    approval_scope_ref: str | None = None
    approval_request_ref: str | None = None
    approval_status: str = "not_required"
    approval_reason_codes: list[str] = Field(default_factory=list)
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
            (self.approval_ref, "authority_lease_receipt_approval_ref"),
            (self.approval_scope_ref, "authority_lease_receipt_approval_scope_ref"),
            (self.approval_request_ref, "authority_lease_receipt_approval_request_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for refs, field_name in [
            (self.denied_domain_refs, "authority_lease_denied_domain_ref"),
            (self.unsupported_adapter_refs, "authority_lease_unsupported_adapter_ref"),
            (self.blocked_reason_refs, "authority_lease_blocked_reason_ref"),
        ]:
            _validate_ref_list(refs, field_name)
        validate_safe_task_text(self.safe_summary, "authority_lease_receipt_summary")
        validate_safe_task_text(self.approval_status, "authority_lease_approval_status")
        for reason_code in self.approval_reason_codes:
            validate_safe_task_text(reason_code, "authority_lease_approval_reason_code")
        for redaction in self.redactions_applied:
            validate_safe_task_text(redaction, "authority_lease_receipt_redaction")
        if (self.lease_issued_at is None) != (self.lease_expires_at is None):
            raise ValueError("AUTHORITY_LEASE_RECEIPT_WINDOW_INCOMPLETE")
        if (
            self.lease_issued_at is not None
            and self.lease_expires_at is not None
            and self.lease_expires_at <= self.lease_issued_at
        ):
            raise ValueError("AUTHORITY_LEASE_RECEIPT_WINDOW_INVALID")
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
    mode_catalog: list[AuthorityModeCatalogEntry] = Field(default_factory=list)
    active_leases: list[AuthorityLease] = Field(default_factory=list)
    capability_mappings: list[AuthorityCapabilityMapping] = Field(default_factory=list)
    decision_summary: AuthorityDecisionSummary
    decision_catalog: list[AuthorityDecisionCatalogEntry] = Field(default_factory=list)
    recent_receipts: list[AuthorityLeaseReceipt] = Field(default_factory=list)
    sample_decisions: list[AuthorityPolicyDecision] = Field(default_factory=list)
    kill_switch_visible: bool = True
    kill_switch_engaged: bool = False
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


def _lease_scope_matches_action(
    lease: AuthorityLease,
    request: AuthorityActionRequest,
) -> bool:
    if lease.scope == AuthorityLeaseScope.session.value:
        return True
    if lease.scope != AuthorityLeaseScope.mission.value:
        return False
    if not lease.mission_ref:
        return False
    constraint_mission_ref = request.constraints.get(
        "mission_ref"
    ) or request.constraints.get(
        "authority_mission_ref"
    )
    return lease.mission_ref in set(request.resource_refs) or (
        isinstance(constraint_mission_ref, str)
        and constraint_mission_ref == lease.mission_ref
    )


def evaluate_authority_request(
    request: AuthorityActionRequest,
    leases: list[AuthorityLease],
    *,
    now: datetime | None = None,
) -> AuthorityPolicyDecision:
    active_leases = [lease for lease in leases if lease.is_active(now=now)]
    matching_domain_capability = [
        lease
        for lease in active_leases
        if lease.grants(AuthorityDomain(request.domain), AuthorityCapability(request.capability))
    ]
    matching = [
        lease
        for lease in matching_domain_capability
        if _lease_scope_matches_action(lease, request)
    ]
    reason_refs: list[str] = []
    if request.kill_switch_engaged or authority_lease_kill_switch_engaged():
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
        reason_ref = (
            "reason-ref:authority:mission-scope-mismatch"
            if matching_domain_capability
            else "reason-ref:authority:no-active-lease-for-domain-capability"
        )
        reason_refs.append(reason_ref)
        operator_message = (
            "Requires a mission-scoped authority lease that matches the action mission ref."
            if reason_ref == "reason-ref:authority:mission-scope-mismatch"
            else "Requires an active authority lease; degraded to a draft proposal."
        )
        if request.draft_fallback_available:
            return _decision(
                request,
                AuthorityDecisionOutcome.degrade_to_draft,
                reason_refs=reason_refs,
                operator_message=operator_message,
            )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            reason_refs=reason_refs,
            operator_message=(
                "Denied because no active lease grants this action mission scope."
                if reason_ref == "reason-ref:authority:mission-scope-mismatch"
                else "Denied because no active lease grants this domain and capability."
            ),
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
        capability_ref=request.capability_ref,
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


def build_authority_decision_preview(
    request: AuthorityActionRequest,
    leases: list[AuthorityLease],
    *,
    now: datetime | None = None,
    kill_switch_engaged: bool = False,
) -> AuthorityDecisionPreview:
    effective_leases = leases or build_default_authority_leases()
    active_leases = [lease for lease in effective_leases if lease.is_active(now=now)]
    if kill_switch_engaged and not request.kill_switch_engaged:
        request = request.model_copy(update={"kill_switch_engaged": True})
    decision = evaluate_authority_request(request, effective_leases, now=now)
    preview_ref = _stable_ref(
        "authority-decision-preview-ref",
        {
            "action_ref": request.action_ref,
            "domain": request.domain,
            "capability": request.capability,
            "decision_ref": decision.decision_ref,
        },
    )
    return AuthorityDecisionPreview(
        preview_ref=preview_ref,
        decision=decision,
        active_lease_refs=[lease.lease_ref for lease in active_leases],
        preview_receipt_ref=_stable_ref(
            "receipt-ref:authority-decision-preview",
            {
                "preview_ref": preview_ref,
                "decision_ref": decision.decision_ref,
                "outcome": decision.outcome,
            },
        ),
        audit_record_ref=_stable_ref(
            "audit-ref:authority-decision-preview",
            {
                "preview_ref": preview_ref,
                "decision_ref": decision.decision_ref,
                "outcome": decision.outcome,
            },
        ),
        operator_summary=(
            "Authority decision preview evaluated active lease scope without "
            "executing or mutating anything."
        ),
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


def authority_lease_kill_switch_engaged() -> bool:
    value = os.environ.get(AUTHORITY_LEASE_KILL_SWITCH_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on", "enabled", "engaged"}


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
            AuthorityDomain.browser: [
                AuthorityCapability.read,
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
    if mode == TrustMode.approved_safe_local_work_session:
        return {
            AuthorityDomain.workspace: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            ],
        }
    if mode == TrustMode.full_local_workspace_session:
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
    if mode == TrustMode.full_machine_access_session:
        return {
            AuthorityDomain.shell: [AuthorityCapability.execute],
            AuthorityDomain.apps: [
                AuthorityCapability.observe,
                AuthorityCapability.click,
            ],
            AuthorityDomain.browser: [
                AuthorityCapability.observe,
                AuthorityCapability.click,
                AuthorityCapability.form_fill,
                AuthorityCapability.upload,
                AuthorityCapability.download,
            ],
            AuthorityDomain.system_settings: [
                AuthorityCapability.read,
                AuthorityCapability.mutate,
            ],
        }
    return {
        AuthorityDomain.browser: [
            AuthorityCapability.observe,
            AuthorityCapability.click,
            AuthorityCapability.form_fill,
        ],
        AuthorityDomain.shopping_payments: [
            AuthorityCapability.purchase_under_budget,
        ],
    }


def _local_implemented_authority_capabilities() -> dict[
    AuthorityDomain,
    set[AuthorityCapability],
]:
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
    return {
        AuthorityDomain.workspace: local_execute,
        AuthorityDomain.files: local_change,
        AuthorityDomain.memory: local_change,
        AuthorityDomain.contacts: local_change,
        AuthorityDomain.provider_model_calls: {
            AuthorityCapability.observe,
            AuthorityCapability.read,
            AuthorityCapability.execute,
        },
        AuthorityDomain.browser: {
            AuthorityCapability.read,
        },
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
            AuthorityDomain.browser: {
                AuthorityCapability.read,
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
    if mode == TrustMode.approved_safe_local_work_session:
        return {
            AuthorityDomain.workspace: {
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            },
        }
    if mode == TrustMode.full_local_workspace_session:
        return {
            **_local_implemented_authority_capabilities(),
            AuthorityDomain.provider_model_calls: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
            },
        }
    if mode in {
        TrustMode.full_machine_access_session,
        TrustMode.delegated_mission_autonomous_window,
    }:
        return _local_implemented_authority_capabilities()
    return _local_implemented_authority_capabilities()


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
    known_local = _local_implemented_authority_capabilities()
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
            suffix = (
                "not-available-for-authority-mode-v1"
                if capability in known_local.get(domain_value, set())
                else "not-implemented-for-authority-lease-v1"
            )
            unsupported_refs.append(
                "adapter-ref:"
                f"{domain_value.value}:{capability.value}"
                f"-{suffix}"
            )
        if domain_value not in allowed and domain_value not in known_local:
            unsupported_refs.append(
                f"adapter-ref:{domain_value.value}:not-implemented-for-authority-lease-v1"
            )
    return granted, list(dict.fromkeys(denied_refs)), list(dict.fromkeys(unsupported_refs))


def _sorted_domain_capabilities(
    domains: dict[AuthorityDomain, list[AuthorityCapability] | set[AuthorityCapability]],
) -> dict[AuthorityDomain, list[AuthorityCapability]]:
    sorted_domains: dict[AuthorityDomain, list[AuthorityCapability]] = {}
    for domain, capabilities in sorted(domains.items(), key=lambda item: _enum_value(item[0])):
        sorted_domains[AuthorityDomain(domain)] = sorted(
            [AuthorityCapability(capability) for capability in capabilities],
            key=_enum_value,
        )
    return sorted_domains


def _authority_mode_catalog_status(
    *,
    issue_ready: bool,
    approval_required: bool,
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
    denied_refs: list[str],
    unsupported_refs: list[str],
    kill_switch_engaged: bool,
) -> str:
    if kill_switch_engaged:
        return "blocked_kill_switch_engaged"
    if issue_ready and approval_required:
        return "issue_ready_approval_required"
    if issue_ready:
        return "issue_ready_no_approval_required"
    if granted_domains and (denied_refs or unsupported_refs):
        return "partial_explicit_scope_required"
    return "blocked_default_scope_unsupported"


def _authority_mode_catalog_summary(
    mode: TrustMode,
    *,
    status: str,
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
    unsupported_refs: list[str],
) -> str:
    mode_label = mode.value.replace("_", " ")
    granted_count = sum(len(capabilities) for capabilities in granted_domains.values())
    if status == "blocked_kill_switch_engaged":
        return (
            f"{mode_label} cannot issue while the AuthorityLease kill switch is engaged."
        )
    if status.startswith("issue_ready"):
        return (
            f"{mode_label} default scope is issue-ready for {granted_count} "
            "governed domain capabilities; unsupported adapters are not granted."
        )
    if status == "partial_explicit_scope_required":
        return (
            f"{mode_label} has implemented local sub-scope available, but the "
            "default request includes unsupported adapters; request an exact "
            "implemented domain/capability subset."
        )
    return (
        f"{mode_label} default scope is blocked because {len(unsupported_refs)} "
        "unsupported adapter ref(s) remain planned unsupported or denied."
    )


def build_authority_mode_catalog(
    *,
    kill_switch_engaged: bool = False,
) -> list[AuthorityModeCatalogEntry]:
    entries: list[AuthorityModeCatalogEntry] = []
    for mode in TrustMode:
        scope = (
            AuthorityLeaseScope.mission
            if mode == TrustMode.delegated_mission_autonomous_window
            else AuthorityLeaseScope.session
        )
        requested = _default_requested_domains(mode)
        request = AuthorityLeaseIssueRequest(
            mode=mode,
            scope=scope,
            mission_ref=(
                "mission-ref:authority-mode-catalog:delegated"
                if scope == AuthorityLeaseScope.mission
                else None
            ),
            requested_domains=requested,
            decision_reason_ref=f"reason-ref:authority-mode-catalog:{mode.value}",
            safe_summary=(
                f"Evaluate default AuthorityLease readiness for {mode.value} mode."
            ),
        )
        granted, denied_refs, unsupported_refs = _filter_requested_domains(request)
        approval_required = _authority_lease_requires_approval(request, granted)
        issue_ready = bool(granted) and not denied_refs and not unsupported_refs and not kill_switch_engaged
        blocked_reason_refs: list[str] = []
        if kill_switch_engaged:
            blocked_reason_refs.append("reason-ref:authority:kill-switch-engaged")
        if denied_refs:
            blocked_reason_refs.append("reason-ref:authority:mode-default-scope-denied")
        if unsupported_refs:
            blocked_reason_refs.append("reason-ref:authority:adapter-unsupported")
        if scope == AuthorityLeaseScope.mission:
            blocked_reason_refs.append("reason-ref:authority:mission-scope-required")
        status = _authority_mode_catalog_status(
            issue_ready=issue_ready,
            approval_required=approval_required,
            granted_domains=granted,
            denied_refs=denied_refs,
            unsupported_refs=unsupported_refs,
            kill_switch_engaged=kill_switch_engaged,
        )
        entries.append(
            AuthorityModeCatalogEntry(
                mode=mode,
                scope=scope,
                status=status,
                default_requested_domains=_sorted_domain_capabilities(requested),
                grantable_domains=_sorted_domain_capabilities(
                    {
                        domain: capabilities
                        for domain, capabilities in _allowed_domain_capabilities(mode).items()
                    }
                ),
                granted_default_domains=_sorted_domain_capabilities(granted),
                denied_default_domain_refs=denied_refs,
                unsupported_adapter_refs=unsupported_refs,
                blocked_reason_refs=list(dict.fromkeys(blocked_reason_refs)),
                approval_required=approval_required,
                issue_ready=issue_ready,
                requires_mission_ref=scope == AuthorityLeaseScope.mission,
                operator_summary=_authority_mode_catalog_summary(
                    mode,
                    status=status,
                    granted_domains=granted,
                    unsupported_refs=unsupported_refs,
                ),
            )
        )
    return entries


def _authority_lease_requires_approval(
    request: AuthorityLeaseIssueRequest,
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
) -> bool:
    mode = TrustMode(request.mode)
    if mode != TrustMode.read_only:
        return True
    for capabilities in granted_domains.values():
        if any(
            AuthorityCapability(capability) not in READ_PREPARE_CAPABILITIES
            for capability in capabilities
        ):
            return True
    return False


def _authority_lease_approval_resource_refs(
    request: AuthorityLeaseIssueRequest,
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
    *,
    idempotency_ref: str,
) -> list[str]:
    resource_refs = [
        idempotency_ref,
        request.decision_reason_ref,
        f"authority-mode-ref:{_enum_value(request.mode)}",
        f"authority-scope-ref:{_enum_value(request.scope)}",
    ]
    if request.mission_ref:
        resource_refs.append(request.mission_ref)
    for domain, capabilities in sorted(
        granted_domains.items(),
        key=lambda item: _enum_value(item[0]),
    ):
        domain_value = _enum_value(domain)
        resource_refs.append(f"authority-domain-ref:{domain_value}")
        for capability in sorted(capabilities, key=_enum_value):
            resource_refs.append(
                f"authority-capability-ref:{domain_value}:{_enum_value(capability)}"
            )
    return list(dict.fromkeys(resource_refs))


def build_authority_lease_approval_requirement(
    request: AuthorityLeaseIssueRequest,
    granted_domains: dict[AuthorityDomain, list[AuthorityCapability]],
    *,
    idempotency_ref: str,
) -> AuthorityLeaseApprovalRequirement:
    validate_task_ref(idempotency_ref, "authority_lease_approval_idempotency_ref")
    resource_refs = _authority_lease_approval_resource_refs(
        request,
        granted_domains,
        idempotency_ref=idempotency_ref,
    )
    approval_required = _authority_lease_requires_approval(request, granted_domains)
    scope_payload = {
        "idempotency_ref": idempotency_ref,
        "mode": request.mode,
        "scope": request.scope,
        "mission_ref": request.mission_ref,
        "operator_ref": request.operator_ref,
        "resources": resource_refs,
    }
    approval_scope_ref = _stable_ref("approval-scope-ref:authority-lease", scope_payload)
    approval_request_ref = _stable_ref(
        "approval-request-ref:authority-lease",
        {"approval_scope_ref": approval_scope_ref, "operation": "issue"},
    )
    subject_ref = _stable_ref(
        "authority-lease-issue-ref",
        {"approval_scope_ref": approval_scope_ref},
    )
    return AuthorityLeaseApprovalRequirement(
        approval_required=approval_required,
        approval_scope_ref=approval_scope_ref,
        approval_request_ref=approval_request_ref,
        run_ref=_stable_ref(
            "run-ref:authority-lease",
            {"approval_scope_ref": approval_scope_ref},
        ),
        subject_ref=subject_ref,
        resource_refs=resource_refs,
        operator_ref=request.operator_ref,
        risk_level="high" if approval_required else "safe",
        purpose=(
            "Validate exact operator approval before issuing an AuthorityLease "
            "for the filtered mode, domain, and capability scope."
        ),
        safe_summary=(
            "AuthorityLease approval requirement for the filtered granted "
            "mode/domain/capability scope."
        ),
    )


def build_authority_lease_approval_requirement_for_request(
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
) -> AuthorityLeaseApprovalRequirement:
    granted, _, _ = _filter_requested_domains(request)
    return build_authority_lease_approval_requirement(
        request,
        granted,
        idempotency_ref=idempotency_ref,
    )


def _approval_decision_status(decision: Any | None) -> str:
    status = getattr(decision, "status", None)
    return str(getattr(status, "value", status or "missing"))


def _approval_decision_reason_codes(decision: Any | None) -> list[str]:
    reason_codes = getattr(decision, "reason_codes", None)
    if not reason_codes:
        return []
    return [str(code) for code in reason_codes]


def _approval_decision_ref(
    decision: Any | None,
    request: AuthorityLeaseIssueRequest,
) -> str | None:
    ref = getattr(decision, "approval_ref", None) or request.approval_ref
    return str(ref) if ref else None


def _approval_decision_validated(
    decision: Any | None,
    requirement: AuthorityLeaseApprovalRequirement,
) -> bool:
    if not requirement.approval_required:
        return True
    return (
        bool(getattr(decision, "allowed", False))
        and _approval_decision_status(decision) == "approved"
        and bool(getattr(decision, "matched_grant_ref", None))
    )


def _mission_requested_domains(
    request: AuthorityMissionPlanRequest,
) -> dict[AuthorityDomain, list[AuthorityCapability]]:
    domains: dict[AuthorityDomain, list[AuthorityCapability]] = {
        AuthorityDomain(domain): [
            AuthorityCapability(capability) for capability in capabilities
        ]
        for domain, capabilities in request.requested_domains.items()
    }
    for action in request.action_requests:
        domain = AuthorityDomain(action.domain)
        capability = AuthorityCapability(action.capability)
        current = domains.setdefault(domain, [])
        if capability not in current:
            current.append(capability)
    return domains


def _mission_action_requests(
    request: AuthorityMissionPlanRequest,
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]],
    *,
    kill_switch_engaged: bool = False,
) -> list[AuthorityActionRequest]:
    if request.action_requests:
        if not kill_switch_engaged:
            return request.action_requests
        return [
            action.model_copy(update={"kill_switch_engaged": True})
            for action in request.action_requests
        ]
    allowed = _allowed_domain_capabilities(TrustMode(request.requested_mode))
    actions: list[AuthorityActionRequest] = []
    for domain, capabilities in requested_domains.items():
        for capability in capabilities:
            unsupported = capability not in allowed.get(domain, set())
            actions.append(
                AuthorityActionRequest(
                    action_ref=_stable_ref(
                        "authority-action-ref",
                        {
                            "mission_ref": request.mission_ref,
                            "domain": domain,
                            "capability": capability,
                        },
                    ),
                    domain=domain,
                    capability=capability,
                    safe_summary=(
                        f"Preview mission authority for {domain.value} "
                        f"{capability.value}."
                    ),
                    resource_refs=[request.mission_ref],
                    route_ref=f"mission-action-ref:{domain.value}:{capability.value}",
                    requested_mode=TrustMode(request.requested_mode),
                    draft_fallback_available=request.draft_fallback_available,
                    unsupported_adapter=unsupported,
                    kill_switch_engaged=kill_switch_engaged,
                )
            )
    return actions


def build_authority_mission_plan(
    request: AuthorityMissionPlanRequest,
    leases: list[AuthorityLease],
    *,
    now: datetime | None = None,
    kill_switch_engaged: bool = False,
) -> AuthorityMissionPlan:
    requested_domains = _mission_requested_domains(request)
    issue_request = AuthorityLeaseIssueRequest(
        mode=TrustMode(request.requested_mode),
        scope=AuthorityLeaseScope.mission,
        mission_ref=request.mission_ref,
        operator_ref=request.operator_ref,
        requested_domains=requested_domains,
        constraints={
            **request.constraints,
            "authority_mission_plan_preview": True,
            "execution_performed": False,
        },
        decision_reason_ref=request.decision_reason_ref,
        duration_minutes=request.duration_minutes,
        safe_summary=(
            "Mission-scoped AuthorityLease issue draft for implemented "
            "domain capabilities only."
        ),
    )
    granted, denied_refs, unsupported_refs = _filter_requested_domains(issue_request)
    active_leases = [lease for lease in leases if lease.is_active(now=now)]
    action_previews = [
        build_authority_decision_preview(
            action,
            active_leases or build_default_authority_leases(),
            now=now,
            kill_switch_engaged=kill_switch_engaged,
        )
        for action in _mission_action_requests(
            request,
            requested_domains,
            kill_switch_engaged=kill_switch_engaged,
        )
    ]
    required_domain_refs = sorted(
        {
            ref
            for preview in action_previews
            for ref in preview.decision.required_domain_refs
        }
    )
    required_capability_refs = sorted(
        {
            ref
            for preview in action_previews
            for ref in preview.decision.required_capability_refs
        }
    )
    blocked_reason_refs = sorted(
        {
            ref
            for preview in action_previews
            for ref in preview.decision.reason_refs
            if preview.decision.outcome
            in {
                AuthorityDecisionOutcome.deny.value,
                AuthorityDecisionOutcome.degrade_to_draft.value,
            }
        }
    )
    issue_ready = (
        bool(granted)
        and not denied_refs
        and not unsupported_refs
        and not kill_switch_engaged
    )
    plan_ref = _stable_ref(
        "authority-mission-plan-ref",
        {
            "mission_ref": request.mission_ref,
            "requested_mode": request.requested_mode,
            "requested_domains": {
                domain.value: [capability.value for capability in capabilities]
                for domain, capabilities in requested_domains.items()
            },
        },
    )
    if kill_switch_engaged:
        operator_summary = (
            "Mission lease plan is draft-only because the authority lease kill "
            "switch is engaged."
        )
        next_safe_action = (
            "Keep the mission as a draft until the operator disables the "
            "authority lease kill switch through the configured local control."
        )
    elif issue_ready:
        operator_summary = (
            "Mission lease plan is issue-ready for currently implemented "
            "domain capabilities; action previews still require the lease to be issued."
        )
        next_safe_action = (
            "Issue the mission-scoped AuthorityLease with the displayed domain "
            "scope, then re-preview or execute only implemented lanes."
        )
    else:
        operator_summary = (
            "Mission lease plan is draft-only because at least one requested "
            "domain capability is unsupported or denied by current authority policy."
        )
        next_safe_action = (
            "Keep the mission as a draft, remove unsupported domains, or implement "
            "the named adapters with tests before issuing authority."
        )
    return AuthorityMissionPlan(
        plan_ref=plan_ref,
        mission_ref=request.mission_ref,
        requested_mode=TrustMode(request.requested_mode),
        requested_domains=requested_domains,
        granted_domains=granted,
        denied_domain_refs=denied_refs,
        unsupported_adapter_refs=unsupported_refs,
        action_previews=action_previews,
        active_lease_refs=[lease.lease_ref for lease in active_leases],
        lease_issue_request_ref=_stable_ref(
            "authority-lease-issue-request-ref",
            {
                "mission_ref": request.mission_ref,
                "plan_ref": plan_ref,
                "requested_mode": request.requested_mode,
            },
        ),
        lease_issue_request=issue_request,
        lease_issue_ready=issue_ready,
        required_domain_refs=required_domain_refs,
        required_capability_refs=required_capability_refs,
        blocked_reason_refs=(
            list(
                dict.fromkeys(
                    [
                        *blocked_reason_refs,
                        "reason-ref:authority:lease-kill-switch-engaged",
                    ]
                )
            )
            if kill_switch_engaged
            else blocked_reason_refs
        ),
        operator_summary=operator_summary,
        next_safe_action=next_safe_action,
    )


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
            kill_switch_engaged=authority_lease_kill_switch_engaged(),
        )

    def preview_decision(
        self,
        request: AuthorityActionRequest,
    ) -> AuthorityDecisionPreview:
        active = self.list_leases(active_only=True)
        return build_authority_decision_preview(
            request,
            active or build_default_authority_leases(),
            kill_switch_engaged=authority_lease_kill_switch_engaged(),
        )

    def plan_mission(
        self,
        request: AuthorityMissionPlanRequest,
    ) -> AuthorityMissionPlan:
        active = self.list_leases(active_only=True)
        return build_authority_mission_plan(
            request,
            active or build_default_authority_leases(),
            kill_switch_engaged=authority_lease_kill_switch_engaged(),
        )

    def issue_lease(
        self,
        request: AuthorityLeaseIssueRequest,
        *,
        idempotency_ref: str,
        approval_validator: AuthorityLeaseApprovalValidator | None = None,
    ) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
        validate_task_ref(idempotency_ref, "authority_lease_idempotency_ref")
        existing = self._receipt_for_idempotency(idempotency_ref)
        if existing is not None:
            if existing.operation != "issue":
                raise AuthorityLeaseConflictError("AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT")
            lease = self._lease_by_ref(existing.lease_ref)
            return lease, existing.model_copy(update={"status": "replayed"})
        granted, denied_refs, unsupported_refs = _filter_requested_domains(request)
        approval_requirement = build_authority_lease_approval_requirement(
            request,
            granted,
            idempotency_ref=idempotency_ref,
        )
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
        approval_decision = (
            approval_validator(request, approval_requirement)
            if approval_requirement.approval_required and approval_validator is not None
            else None
        )
        if authority_lease_kill_switch_engaged():
            receipt = self._receipt(
                operation="issue",
                status="denied",
                lease_ref=lease_ref,
                idempotency_ref=idempotency_ref,
                request=request,
                granted_domains={},
                denied_domain_refs=denied_refs,
                unsupported_adapter_refs=unsupported_refs,
                approval_requirement=approval_requirement,
                approval_decision=approval_decision,
                approval_reason_codes=["AUTHORITY_LEASE_KILL_SWITCH_ENGAGED"],
                blocked_reason_refs=[
                    "reason-ref:authority:lease-kill-switch-engaged",
                ],
                safe_summary=(
                    "Authority lease request denied because the authority "
                    "lease kill switch is engaged."
                ),
            )
            self._append_receipt(receipt)
            return None, receipt
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
                approval_requirement=approval_requirement,
                approval_decision=None,
                safe_summary=(
                    "Authority lease request denied because no requested domain "
                    "capability is implemented for this trust mode."
                ),
            )
            self._append_receipt(receipt)
            return None, receipt
        if not _approval_decision_validated(approval_decision, approval_requirement):
            reason_codes = _approval_decision_reason_codes(approval_decision)
            if not reason_codes:
                reason_codes = (
                    ["APPROVAL_REF_MISSING"]
                    if request.approval_ref is None
                    else ["APPROVAL_VALIDATION_REQUIRED"]
                )
            receipt = self._receipt(
                operation="issue",
                status="denied",
                lease_ref=lease_ref,
                idempotency_ref=idempotency_ref,
                request=request,
                granted_domains={},
                denied_domain_refs=denied_refs,
                unsupported_adapter_refs=unsupported_refs,
                approval_requirement=approval_requirement,
                approval_decision=approval_decision,
                approval_reason_codes=reason_codes,
                safe_summary=(
                    "Authority lease request denied because exact "
                    "LocalApprovalAuthority validation is missing or invalid."
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
                "approval_required": approval_requirement.approval_required,
                "approval_validated": True,
                "approval_ref": _approval_decision_ref(approval_decision, request),
                "approval_scope_ref": approval_requirement.approval_scope_ref,
                "approval_request_ref": approval_requirement.approval_request_ref,
                "approval_status": _approval_decision_status(approval_decision),
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
            approval_requirement=approval_requirement,
            approval_decision=approval_decision,
            lease_issued_at=lease.issued_at,
            lease_expires_at=lease.expires_at,
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
            lease_issued_at=lease.issued_at,
            lease_expires_at=lease.expires_at,
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
        approval_requirement: AuthorityLeaseApprovalRequirement | None = None,
        approval_decision: Any | None = None,
        approval_reason_codes: list[str] | None = None,
        blocked_reason_refs: list[str] | None = None,
        lease_issued_at: datetime | None = None,
        lease_expires_at: datetime | None = None,
    ) -> AuthorityLeaseReceipt:
        approval_required = bool(
            approval_requirement and approval_requirement.approval_required
        )
        approval_validated = False
        if approval_required and approval_requirement is not None:
            approval_validated = _approval_decision_validated(
                approval_decision,
                approval_requirement,
            )
        reason_codes = (
            approval_reason_codes
            if approval_reason_codes is not None
            else _approval_decision_reason_codes(approval_decision)
        )
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
            lease_issued_at=lease_issued_at,
            lease_expires_at=lease_expires_at,
            requested_domains=request.requested_domains
            or _default_requested_domains(TrustMode(request.mode)),
            granted_domains=granted_domains,
            denied_domain_refs=denied_domain_refs,
            unsupported_adapter_refs=unsupported_adapter_refs,
            blocked_reason_refs=blocked_reason_refs or [],
            approval_required=approval_required,
            approval_validated=approval_validated,
            approval_ref=_approval_decision_ref(approval_decision, request),
            approval_scope_ref=(
                approval_requirement.approval_scope_ref
                if approval_requirement is not None
                else None
            ),
            approval_request_ref=(
                approval_requirement.approval_request_ref
                if approval_requirement is not None
                else None
            ),
            approval_status=(
                _approval_decision_status(approval_decision)
                if approval_requirement and approval_requirement.approval_required
                else "not_required"
            ),
            approval_reason_codes=reason_codes,
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
            "lane-ref:authority-lease-control-plane",
            "AuthorityLease issue and revoke",
            AuthorityDomain.system_settings,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_operator_selected_root_control_receipt_required",
            [
                "POST /api/runtime/authority-leases",
                "POST /api/runtime/authority-leases/approve-and-issue",
                "POST /api/runtime/authority-leases/revoke",
            ],
            [
                "scripts/dev/uaa_runtime.py select-authority-mode --approve",
                "scripts/dev/uaa_runtime.py revoke-authority-lease",
            ],
            (
                "Operator-selected trust-mode control plane for issuing or "
                "revoking session/mission AuthorityLease objects. It records "
                "idempotent receipts, audit refs, redaction posture, rollback/"
                "safe-disable refs, and kill-switch visibility; it does not "
                "execute adapters, mint model/provider authority, bypass "
                "unknown-authority denial, or grant unsupported domains."
            ),
        ),
        _mapping(
            "lane-ref:start-here-read",
            "Start Here local loop summary",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/start-here/summary"],
            ["python scripts/dev/uaa_founder_loop.py inspect-start-here"],
            (
                "Backend-owned Start Here inspection reads safe refs, readiness, "
                "next safe action, and proof refs only; it does not execute work."
            ),
        ),
        _mapping(
            "lane-ref:today-loop-read",
            "Today daily loop",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/today/summary"],
            ["python scripts/dev/uaa_founder_loop.py inspect"],
            (
                "Backend-owned Today inspection reads local action, memory, "
                "evidence, proof, and run refs only; mutations need separate gates."
            ),
        ),
        _mapping(
            "lane-ref:proof-detail-read",
            "Universal Proof Detail",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            [
                "GET /control-center/proof/index",
                "GET /control-center/proof/{proof_ref}",
            ],
            ["python scripts/dev/uaa_founder_loop.py inspect-proof"],
            (
                "Proof inspection reads safe proof, receipt, evidence, and "
                "redaction refs only; proof surfaces do not grant action authority."
            ),
        ),
        _mapping(
            "lane-ref:operator-workspace-spine",
            "Operator Workspace Spine",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/today/summary#operator_workspace_spine"],
            ["python scripts/inspect_operator_workspace_spine.py"],
            (
                "Workspace spine inspection reads safe workspace, Git, preview, "
                "run-log, and handoff posture refs without starting or editing."
            ),
        ),
        _mapping(
            "lane-ref:action-inbox-work-queue",
            "Action Inbox work queue",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/actions/inbox"],
            ["python scripts/dev/uaa_founder_loop.py inspect-action-work-queue"],
            (
                "Action Inbox queue inspection reads requested, blocked, and "
                "receipt-recorded item refs only; execution requires exact lanes."
            ),
        ),
        _mapping(
            "lane-ref:memory-review-read",
            "Memory Review and loop binding",
            AuthorityDomain.memory,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/memory/review"],
            [
                "python scripts/dev/uaa_founder_loop.py "
                "inspect-evidence-memory-binding"
            ],
            (
                "Memory Review inspection reads recall candidates and why-shown "
                "safe refs only; memory remains recall, not truth or authority."
            ),
        ),
        _mapping(
            "lane-ref:evidence-timeline-read",
            "Evidence Timeline",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/evidence/timeline"],
            ["python scripts/dev/uaa_founder_loop.py inspect"],
            (
                "Evidence Timeline inspection reads local safe-ref history linked "
                "to actions, memory, runs, receipts, and proof; it cannot execute."
            ),
        ),
        _mapping(
            "lane-ref:local-draft-proposal",
            "Local drafts and proposals",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_control_center_draft_proposal",
            [
                "GET /control-center/memory/context-packs",
                "GET /control-center/memory/context-packs/{context_pack_ref}/preview",
            ],
            ["python scripts/dev/uaa_founder_loop.py memory-context-manifest"],
            (
                "Local draft/proposal inspection may prepare review artifacts "
                "inside read-only workspace draft scope; applying or sending is separate."
            ),
        ),
        _mapping(
            "lane-ref:model-slot-posture",
            "Main and auxiliary model slot posture",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_model_slot_read_model",
            ["GET /control-center/providers/runtime-control-plane"],
            ["python scripts/inspect_model_provider_control_plane.py"],
            (
                "Model slot posture is read-only routing intent inspection; it "
                "does not call models, switch providers, or trust model output."
            ),
        ),
        _mapping(
            "lane-ref:connector-draft-only",
            "Connector draft-only proposals",
            AuthorityDomain.email,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_control_center_connector_draft_only",
            ["GET /control-center/sources/readiness#connector_draft_proposals"],
            ["python scripts/inspect_connector_draft_proposals.py"],
            (
                "Connector draft-only proposals are local safe-ref review "
                "artifacts; live account sync, sends, and writes remain separate."
            ),
        ),
        _mapping(
            "lane-ref:shell-arbitrary-command-adapter",
            "Arbitrary shell command adapter",
            AuthorityDomain.shell,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Shell execute is a known authority domain, but arbitrary shell "
                "strings are not implemented; only separately mapped RuntimeGateway "
                "workspace commands may execute under their exact lease gates."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:shell-arbitrary-command:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:apps-local-automation-adapter",
            "Local app automation adapter",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Local app control is modeled as an authority domain, but app "
                "automation adapters are not implemented or callable from leases."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:apps-local-automation:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:issue-tracker-sync",
            "Issue tracker exact sync adapter",
            AuthorityDomain.apps,
            AuthorityCapability.write,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["external-lane-ref:issue-tracker-sync-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Issue tracker sync is a known Apps/write authority capability, "
                "but no project binding, item write adapter, receipt replay, or "
                "compensating update adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:issue-tracker-sync:not-implemented",
                "adapter-ref:issue-tracker-compensating-update:not-implemented",
            ],
        ),
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
            "lane-ref:runtime-invocation-record",
            "Runtime invocation record",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_no_execution_record_only",
            ["POST /api/runtime/invocations"],
            ["repo-local-command:governed-runtime-invocations-list"],
            (
                "Records a redacted RuntimeGateway invocation proposal only; "
                "adapter execution, approval, command execution, model calls, "
                "browser automation, connector writes, and production authority "
                "remain denied unless an AuthorityLease-gated capability is "
                "implemented, approved, and active."
            ),
        ),
        _mapping(
            "lane-ref:runtime-action-inbox-approval-binding",
            "Runtime approval binding",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_approval_binding_lease_evaluated",
            ["POST /api/runtime/invocations/{id}/approve"],
            ["repo-local-command:governed-runtime-action-approve-preflight"],
            (
                "Binds exact Action Inbox approval refs to one RuntimeGateway "
                "command envelope and evaluates workspace/execute lease scope; "
                "approval refs are identifiers only and do not execute work."
            ),
        ),
        _mapping(
            "lane-ref:runtime-action-inbox-approved-execute",
            "Runtime approved execution",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_rechecked_execution",
            ["POST /api/runtime/invocations/{id}/execute"],
            [],
            (
                "Executes only exact approved RuntimeGateway command envelopes "
                "after idempotency, approval refs, active workspace/execute "
                "AuthorityLease recheck, safe-disable, redacted receipts, and "
                "allowlist gates pass."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-implementer-proposal",
            "Runtime worktree implementer proposal",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Implementer worktree lane is a read-only Workspace draft "
                "proposal for branch/worktree shape. It does not create "
                "worktrees, mutate branches, write files, commit, push, run "
                "shell commands, call providers, or persist path values."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-reviewer-compare",
            "Runtime worktree reviewer compare",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Reviewer worktree lane reads safe comparison refs only under "
                "Workspace read authority. Git worktree create/delete, file "
                "mutation, commit, push, shell execution, and path-value "
                "persistence remain blocked."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-verifier-proof",
            "Runtime worktree verifier proof",
            AuthorityDomain.workspace,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Verifier worktree lane prepares checkpoint, Git receipt, and "
                "rollback plan refs under Workspace prepare authority. It does "
                "not run Git, shell commands, provider calls, file writes, "
                "commits, pushes, or rollback execution."
            ),
        ),
        _mapping(
            "lane-ref:staged-orchestration-read-model",
            "Staged orchestration read model",
            AuthorityDomain.workspace,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/staged-orchestration"],
            ["repo-local-command:uaa-runtime-inspect-staged-orchestration"],
            (
                "Staged orchestration inspection prepares safe plan, dependency, "
                "checkpoint, receipt-plan, and degraded-handoff refs under "
                "Workspace prepare authority. The read model cannot execute, "
                "mint approvals, call models, run shell commands, automate "
                "browsers, write connectors, or grant production authority."
            ),
        ),
        _mapping(
            "lane-ref:runtime-preview-rail-safe-ref-read-model",
            "Runtime preview rail safe-ref read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/preview-rail"],
            ["repo-local-command:uaa-runtime-inspect-preview-rail"],
            (
                "Preview rail inspection reads safe refs, source "
                "classifications, bounded preview plans, receipt-plan refs, "
                "and proof refs under Workspace read authority. It does not "
                "read raw files, render raw runtime payloads, capture "
                "screenshots, automate browsers, run shell commands, call "
                "providers, or persist raw paths/content."
            ),
        ),
        _mapping(
            "lane-ref:runtime-slash-command-registry-metadata",
            "Runtime slash command registry metadata",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/slash-command-registry"],
            ["repo-local-command:uaa-runtime-inspect-slash-command-registry"],
            (
                "Slash command registry inspection reads command metadata, "
                "side-effect classes, approval/idempotency policies, receipt "
                "plans, and proof refs under Workspace read authority. It does "
                "not enable chat triggers, runtime invocations, state mutation, "
                "shell execution, provider calls, browser automation, connector "
                "writes, or prompt/response material persistence."
            ),
        ),
        _mapping(
            "lane-ref:runtime-result-classification-taxonomy",
            "Runtime result classification taxonomy",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/result-classification"],
            ["repo-local-command:uaa-runtime-inspect-result-classification"],
            (
                "Result classification inspection reads taxonomy labels, "
                "verification statuses, provenance/redaction policies, receipt "
                "requirements, proof bindings, and blocked refs under "
                "Workspace read authority. It does not make tool output truth, "
                "grant action authority, mutate without receipts, persist "
                "output/provider material, or mint Control Center authority."
            ),
        ),
        _mapping(
            "lane-ref:runtime-logging-profile-posture",
            "Runtime logging profile posture",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/logging-profile"],
            ["repo-local-command:uaa-runtime-inspect-logging-profile"],
            (
                "Logging profile inspection reads active profile, retention, "
                "TTL, redaction verifier, proof, safe-disable, and blocked refs "
                "under Workspace read authority. It does not enable verbose "
                "logging, prompt/response/log/provider/path material persistence, "
                "remote telemetry export, background log streams, or Control "
                "Center authority minting."
            ),
        ),
        _mapping(
            "lane-ref:runtime-interrupt-redirect-proposals",
            "Runtime interrupt redirect proposals",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/interrupt-redirect"],
            ["repo-local-command:uaa-runtime-inspect-interrupt-redirect"],
            (
                "Interrupt redirect inspection reads run-control proposal "
                "metadata, approval scopes, idempotency refs, receipt plans, "
                "recovery/proof refs, and blocked refs under Workspace read "
                "authority. It does not post live stops, kill processes, mutate "
                "runtime state, run shell/provider/browser work, write "
                "connectors, or persist runtime/log material."
            ),
        ),
        _mapping(
            "lane-ref:runtime-voice-media-posture-read-model",
            "Runtime voice and media posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/voice-media-posture"],
            ["repo-local-command:uaa-runtime-inspect-voice-media-posture"],
            (
                "Voice and media posture inspection reads lane labels, consent, "
                "device-permission, redaction, receipt, proof, safe-disable, "
                "and blocked refs under Workspace read authority. It does not "
                "use microphones, cameras, uploads, transcription, generation, "
                "provider calls, external delivery, media material persistence, "
                "or Control Center authority minting."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:voice-media-microphone:not-implemented",
                "adapter-ref:voice-media-camera:not-implemented",
                "adapter-ref:voice-media-upload:not-implemented",
                "adapter-ref:voice-media-transcription:not-implemented",
                "adapter-ref:voice-media-generation:not-implemented",
                "adapter-ref:voice-media-provider-call:not-implemented",
                "adapter-ref:voice-media-external-delivery:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:staged-orchestration-approved-runtime-command",
            "Staged orchestration approved runtime command step",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_runtime_command_step",
            [
                "GET /api/runtime/staged-orchestration#approved-runtime-command-step",
                "POST /api/runtime/invocations/{id}/execute",
            ],
            ["repo-local-command:uaa-runtime-inspect-staged-orchestration"],
            (
                "A staged approved-runtime-command step requires active "
                "Workspace execute AuthorityLease scope plus exact RuntimeGateway "
                "invocation, Action Inbox approval, idempotency, allowlist, "
                "safe-disable, rollback, redaction, and receipt refs before one "
                "supported utility command may run."
            ),
        ),
        _mapping(
            "lane-ref:runtime-safe-disable",
            "Runtime safe-disable",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.read_only,
            "implemented_safety_control_no_execution",
            ["POST /api/runtime/safe-disable"],
            ["repo-local-command:governed-runtime-safe-disable"],
            (
                "Records local safe-disable posture as a safety control that can "
                "only reduce runtime authority; it cannot enable execution, mint "
                "approval, call models, run commands, or grant production authority."
            ),
        ),
        _mapping(
            "lane-ref:hermes-interface-chat-exact-cli",
            "Hermes exact CLI chat",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_external_runtime",
            ["POST /api/runtime/hermes/chat"],
            ["scripts/dev/uaa_runtime.py hermes-chat"],
            (
                "Requires Approved safe local work with workspace/execute "
                "AuthorityLease scope before UAA discovers or executes the exact "
                "guarded Hermes CLI chat argv; arbitrary args, yolo/oneshot, "
                "tool passthrough, raw persistence, direct memory writes, browser "
                "automation, connector writes, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:task-decomposition-plan-execute",
            "Task decomposition local plan execution",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_local_orchestration",
            ["POST /task-decomposition/plans/execute", "POST /task-decomposition/run"],
            ["repo-local-command:task-decomposition:inspect-run"],
            (
                "Requires Approved safe local work with workspace/execute "
                "AuthorityLease scope before local registered handlers run; "
                "high-risk nodes still require exact LocalApprovalAuthority grants."
            ),
        ),
        _mapping(
            "lane-ref:today-action-envelope-promotion",
            "Today-to-Action envelope promotion",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            ["POST /control-center/today/action-envelope"],
            ["scripts/dev/uaa_founder_loop.py promote-action-envelope"],
            (
                "Requires Workspace draft AuthorityLease scope before a Today "
                "item can be promoted into a reviewable Action envelope; action "
                "execution, connector writes, memory writes, shell/browser work, "
                "provider/model calls, and production authority remain denied."
            ),
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
            "lane-ref:action-inbox-decision-receipts",
            "Action Inbox decision receipts",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required_receipt_only",
            [
                "POST /control-center/actions/{action_id}/approve",
                "POST /control-center/actions/{action_id}/edit",
                "POST /control-center/actions/{action_id}/reject",
                "POST /control-center/actions/{action_id}/defer",
            ],
            ["repo-local-command:inspect-action-inbox-decision-lanes"],
            (
                "Requires Workspace write AuthorityLease scope before "
                "approve/edit/reject/defer decision receipt state is recorded; "
                "decision receipts do not execute actions, connector writes, "
                "shell/browser work, memory writes, provider/model calls, or "
                "production authority."
            ),
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
            [
                "POST /control-center/memory/review/{candidate_ref}/accept",
                "POST /control-center/memory/review/{candidate_ref}/correct",
            ],
            ["repo-local-command:inspect-memory-review"],
            "Requires Memory domain write authority; Ask before changes returns ask until an operator confirms.",
        ),
        _mapping(
            "lane-ref:memory-context-pack-action-proposal",
            "Memory context-pack internal Action proposal",
            AuthorityDomain.memory,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            [
                "POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal"
            ],
            ["scripts/dev/uaa_founder_loop.py memory-context-pack-action-proposal"],
            (
                "Requires Memory draft AuthorityLease scope before reviewed "
                "context-pack refs can create an internal Action proposal receipt; "
                "action execution, runtime context injection, memory write, "
                "connector writes, browser automation, provider/model calls, "
                "and production authority remain denied."
            ),
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
            "lane-ref:file-review-approval-capture",
            "File Review approval capture",
            AuthorityDomain.files,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required_review_only",
            ["POST /files/review/approvals/capture"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files write authority to persist review-only safe refs; "
                "raw file access, context injection, memory writes, export, "
                "execution, patch apply, and rollback execution remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-raw-content:not-implemented",
                "adapter-ref:file-patch-apply:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:file-safe-preview",
            "Safe file preview",
            AuthorityDomain.files,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_exact_lease_required_metadata_only",
            ["POST /files/read/preview", "POST /files/tree/preview"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files read authority before safe-root file metadata or "
                "tree previews; raw content and raw paths remain omitted."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-raw-content:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:file-write-proposal-diff-preview",
            "File write proposal and diff preview",
            AuthorityDomain.files,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            ["POST /files/write/propose", "POST /files/diff/preview"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files prepare authority before write proposal or "
                "redacted diff preview; patch apply and rollback execution remain "
                "unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-patch-apply:not-implemented",
            ],
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
            "lane-ref:source-readiness-calendar-metadata",
            "Calendar metadata readiness",
            AuthorityDomain.calendar,
            AuthorityCapability.observe,
            TrustMode.read_only,
            "partial_metadata_contract_only",
            ["GET /control-center/sources/readiness"],
            ["repo-local-command:inspect-source-readiness-metadata-contracts"],
            (
                "Calendar authority is limited to safe readiness contract refs; "
                "live calendar fetch, event creation, updates, deletion, and "
                "invites remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:calendar-live-fetch:not-implemented",
                "adapter-ref:calendar-live-write:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:connector-write-low-risk",
            "Connector low-risk send/write adapter",
            AuthorityDomain.email,
            AuthorityCapability.send,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["connector-lane-ref:low-risk-send-write-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Connector send/write is a known Email/send authority capability, "
                "but live account binding, outbound send, retry, replay, and "
                "compensating-action adapters are not implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:email-live-send:not-implemented",
                "adapter-ref:connector-write-replay:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:messages-live-send-adapter",
            "Messages send adapter",
            AuthorityDomain.messages,
            AuthorityCapability.send,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Messages send authority is modeled for future missions, but no "
                "iMessage/SMS adapter, account binding, send, archive, or delete "
                "execution is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:messages-live-send:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:web-evidence-product-slice",
            "Web evidence product slice",
            AuthorityDomain.browser,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_lease_required_gateway_https_get",
            ["POST /control-center/web-evidence/attach"],
            ["scripts/dev/uaa_founder_loop.py attach-web-evidence"],
            (
                "Requires Read-only mode with Browser read AuthorityLease scope, "
                "configured host allowlist, WebAccessGateway HTTPS GET only, bounded "
                "redacted preview, safe refs, and audit/receipt refs; browser actions, "
                "auth/session state, downloads/uploads, mutation methods, provider/model "
                "calls, memory writes, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:browser-action-adapter",
            "Browser action adapter",
            AuthorityDomain.browser,
            AuthorityCapability.click,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Browser click and form authority is modeled for delegated missions, "
                "but browser sessions, auth state, clicks, forms, uploads, "
                "downloads, and mutations remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:browser-execution:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:browser-low-risk-action",
            "Browser low-risk action adapter",
            AuthorityDomain.browser,
            AuthorityCapability.click,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["browser-lane-ref:low-risk-click-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Low-risk browser click authority is a known Browser/click "
                "capability, but browser sessions, page binding, dry-run replay, "
                "clicks, forms, downloads, uploads, and auth state are unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:browser-low-risk-click:not-implemented",
                "adapter-ref:browser-session-binding:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:provider-credential-validation",
            "Provider credential validation",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_non_invoking_validation",
            ["POST /control-center/providers/credentials/validate"],
            ["scripts/inspect_provider_credential_validation_lane.py"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope plus exact approval, transient credential "
                "handling, idempotency, redacted receipts, and safe-disable refs; "
                "no model invocation, provider SDK authority, billing authority, "
                "or payload persistence is granted."
            ),
        ),
        _mapping(
            "lane-ref:runtime-local-model-loopback-call",
            "Local loopback model call",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_local_loopback",
            ["POST /api/runtime/local-model/call"],
            ["repo-local-command:uaa-runtime-local-model-call"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope before local loopback model runtime can run; "
                "model output remains an untrusted proposal, and remote provider "
                "SDK calls, tools/functions, streaming, memory/file writes, connector "
                "writes, browser automation, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:provider-tiny-exact-approved-invocation",
            "Tiny exact-approved provider invocation",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_provider_cost_governed",
            ["POST /control-center/providers/exact-approved-lanes/tiny"],
            ["scripts/inspect_tiny_provider_invocation_lane.py"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope plus exact provider/model/policy/cost approval, "
                "idempotency, redacted receipts, and safe-disable refs; no broad "
                "provider router, autonomous calls, billing authority, or payload "
                "persistence is granted."
            ),
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
        _mapping(
            "lane-ref:home-assistant-control-adapter",
            "Home Assistant control adapter",
            AuthorityDomain.home_assistant,
            AuthorityCapability.write,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Home Assistant control is modeled as a governed domain, but no "
                "device/entity read or write adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:home-assistant-control:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:background-autonomy-scoped",
            "Scoped background work session",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["autonomy-lane-ref:scoped-background-work-session"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Scoped background autonomy is a known delegated Apps/execute "
                "capability, but worker runtime, queue supervisor, checkpoints, "
                "heartbeats, cancellation, replay, and budget enforcement adapters "
                "are not implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:background-worker-runtime:not-implemented",
                "adapter-ref:background-supervisor:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-subagent-isolation-live-dispatch",
            "Runtime subagent live dispatch",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/subagent-isolation"],
            ["repo-local-command:uaa-runtime-inspect-subagent-isolation"],
            (
                "Subagent live dispatch is modeled as delegated Apps/execute "
                "authority, but no live subagent dispatch, tool-sharing, "
                "cross-agent memory transfer, budgeted fanout, checkpoint, "
                "cancellation, or receipted worker adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:subagent-live-dispatch:not-implemented",
                "adapter-ref:subagent-tool-sharing:not-implemented",
                "adapter-ref:subagent-memory-transfer:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-lsp-diagnostics-evidence",
            "Runtime LSP diagnostics evidence",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.full_local_workspace_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/lsp-diagnostics"],
            ["repo-local-command:uaa-runtime-inspect-lsp-diagnostics"],
            (
                "Semantic diagnostics are modeled as Full local workspace "
                "read authority, but no allowlisted language-server launch, "
                "cwd jail, file-read adapter, dependency install guard, "
                "timeout, redacted diagnostic extraction, or diagnostic "
                "receipt adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:lsp-server-launch:not-implemented",
                "adapter-ref:lsp-file-read:not-implemented",
                "adapter-ref:lsp-diagnostic-extraction:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:cloud-production-deploy-adapter",
            "Cloud production deploy adapter",
            AuthorityDomain.cloud_production,
            AuthorityCapability.deploy,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Cloud production deploy authority is a known domain, but deploy, "
                "configuration mutation, remote execution, and rollback execution "
                "adapters remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:cloud-production-deploy:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:production-authority-gate",
            "Production authority gate",
            AuthorityDomain.cloud_production,
            AuthorityCapability.deploy,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["production-lane-ref:authority-readiness-review"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Production deployment is a known Cloud production/deploy "
                "authority capability, but go-live, release, remote execution, "
                "environment mutation, and rollback execution adapters remain "
                "unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:production-go-live:not-implemented",
                "adapter-ref:production-rollback-execution:not-implemented",
            ],
        ),
    ]


def build_authority_state_read_model(
    *,
    active_leases: list[AuthorityLease] | None = None,
    recent_receipts: list[AuthorityLeaseReceipt] | None = None,
    kill_switch_engaged: bool = False,
) -> AuthorityStateReadModel:
    leases = active_leases or build_default_authority_leases()
    capability_mappings = build_existing_lane_authority_mappings()
    decision_catalog = build_authority_decision_catalog(
        capability_mappings,
        leases,
        kill_switch_engaged=kill_switch_engaged,
    )
    samples = [
        evaluate_authority_request(
            AuthorityActionRequest(
                action_ref="authority-action-ref:sample-workspace-read",
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.read,
                safe_summary="Inspect workspace state under the default read-only lease.",
                route_ref="GET /api/runtime/authority-state",
                kill_switch_engaged=kill_switch_engaged,
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
                kill_switch_engaged=kill_switch_engaged,
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
                kill_switch_engaged=kill_switch_engaged,
            ),
            leases,
        ),
    ]
    operator_summary = (
        "Authority lease kill switch is engaged; new lease issue attempts and "
        "authority decisions deny until the local operator clears it."
        if kill_switch_engaged
        else (
            "Authority is now modeled as trust modes, explicit domains, and "
            "session or mission leases. Unknown authority denies by default; "
            "unsupported adapters are shown as planned unsupported or denied "
            "instead of pretending execution exists."
        )
    )
    return AuthorityStateReadModel(
        active_mode=TrustMode(leases[-1].mode) if leases else TrustMode.read_only,
        operator_summary=operator_summary,
        mode_catalog=build_authority_mode_catalog(
            kill_switch_engaged=kill_switch_engaged,
        ),
        active_leases=leases,
        capability_mappings=capability_mappings,
        decision_summary=build_authority_decision_summary(
            decision_catalog,
            active_lease_count=len(leases),
        ),
        decision_catalog=decision_catalog,
        recent_receipts=recent_receipts or [],
        sample_decisions=samples,
        kill_switch_engaged=kill_switch_engaged,
    )


def build_authority_decision_catalog(
    capability_mappings: list[AuthorityCapabilityMapping] | None = None,
    leases: list[AuthorityLease] | None = None,
    kill_switch_engaged: bool = False,
) -> list[AuthorityDecisionCatalogEntry]:
    mappings = capability_mappings or build_existing_lane_authority_mappings()
    effective_leases = leases or build_default_authority_leases()
    return [
        _authority_decision_catalog_entry(
            mapping,
            effective_leases,
            kill_switch_engaged=kill_switch_engaged,
        )
        for mapping in mappings
    ]


def build_authority_decision_summary(
    decision_catalog: list[AuthorityDecisionCatalogEntry],
    *,
    active_lease_count: int,
) -> AuthorityDecisionSummary:
    outcome_counts = Counter(
        _enum_value(entry.decision.outcome) for entry in decision_catalog
    )
    domain_counts = Counter(_enum_value(entry.decision.domain) for entry in decision_catalog)
    status_counts = Counter(entry.status for entry in decision_catalog)
    capability_refs_by_outcome: dict[str, list[str]] = {
        outcome.value: [] for outcome in AuthorityDecisionOutcome
    }
    blocked_reason_refs: list[str] = []
    unsupported_adapter_refs: list[str] = []
    for entry in decision_catalog:
        outcome = _enum_value(entry.decision.outcome)
        capability_refs_by_outcome.setdefault(outcome, []).append(
            entry.authority_capability_ref
        )
        if outcome != AuthorityDecisionOutcome.allow.value:
            blocked_reason_refs.extend(entry.decision.reason_refs)
        unsupported_adapter_refs.extend(entry.unsupported_adapter_refs)
    allowed = outcome_counts.get(AuthorityDecisionOutcome.allow.value, 0)
    asked = outcome_counts.get(AuthorityDecisionOutcome.ask.value, 0)
    degraded = outcome_counts.get(AuthorityDecisionOutcome.degrade_to_draft.value, 0)
    denied = outcome_counts.get(AuthorityDecisionOutcome.deny.value, 0)
    return AuthorityDecisionSummary(
        total_capabilities=len(decision_catalog),
        active_lease_count=active_lease_count,
        outcome_counts={
            outcome.value: outcome_counts.get(outcome.value, 0)
            for outcome in AuthorityDecisionOutcome
        },
        domain_counts=dict(sorted(domain_counts.items())),
        status_counts=dict(sorted(status_counts.items())),
        allowed_capability_refs=capability_refs_by_outcome[
            AuthorityDecisionOutcome.allow.value
        ],
        ask_capability_refs=capability_refs_by_outcome[
            AuthorityDecisionOutcome.ask.value
        ],
        degraded_capability_refs=capability_refs_by_outcome[
            AuthorityDecisionOutcome.degrade_to_draft.value
        ],
        denied_capability_refs=capability_refs_by_outcome[
            AuthorityDecisionOutcome.deny.value
        ],
        blocked_reason_refs=sorted(set(blocked_reason_refs)),
        unsupported_adapter_refs=sorted(set(unsupported_adapter_refs)),
        operator_summary=(
            f"Authority catalog covers {len(decision_catalog)} capabilities under "
            f"{active_lease_count} active lease(s): {allowed} allowed, {asked} ask, "
            f"{degraded} degrade to draft, {denied} denied. Unsupported adapters "
            "remain denied until implemented and tested."
        ),
    )


def _authority_decision_catalog_entry(
    mapping: AuthorityCapabilityMapping,
    leases: list[AuthorityLease],
    *,
    kill_switch_engaged: bool = False,
) -> AuthorityDecisionCatalogEntry:
    unsupported_adapter = (
        mapping.unsupported_adapter_blocks_capability
        or mapping.status.startswith("planned_unsupported")
    )
    decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=_authority_catalog_action_ref(mapping.lane_ref),
            domain=AuthorityDomain(mapping.domain),
            capability=AuthorityCapability(mapping.capability),
            safe_summary=f"Evaluate AuthorityLease decision posture for {mapping.label}.",
            route_ref=mapping.route_refs[0] if mapping.route_refs else None,
            capability_ref=(
                f"authority-capability-ref:{_safe_mapping_suffix(mapping.lane_ref)}"
            ),
            lane_ref=mapping.lane_ref,
            requested_mode=TrustMode(mapping.required_mode),
            draft_fallback_available=_mapping_supports_draft_fallback(mapping),
            unsupported_adapter=unsupported_adapter,
            kill_switch_engaged=kill_switch_engaged,
            rollback_ref=f"rollback-ref:authority-decision-catalog:{_safe_mapping_suffix(mapping.lane_ref)}",
            safe_disable_ref=f"safe-disable-ref:authority-decision-catalog:{_safe_mapping_suffix(mapping.lane_ref)}",
        ),
        leases,
    )
    return AuthorityDecisionCatalogEntry(
        catalog_ref=f"authority-decision-catalog-ref:{_safe_mapping_suffix(mapping.lane_ref)}",
        authority_capability_ref=(
            f"authority-capability-ref:{_safe_mapping_suffix(mapping.lane_ref)}"
        ),
        lane_ref=mapping.lane_ref,
        label=mapping.label,
        status=mapping.status,
        route_refs=mapping.route_refs,
        cli_refs=mapping.cli_refs,
        evidence_refs=mapping.evidence_refs,
        unsupported_adapter_refs=mapping.unsupported_adapter_refs,
        decision=decision,
        operator_summary=(
            f"{mapping.label} currently evaluates to "
            f"{_enum_value(decision.outcome)} under active AuthorityLease scope."
        ),
    )


def _authority_catalog_action_ref(lane_ref: str) -> str:
    return f"authority-action-ref:catalog:{_safe_mapping_suffix(lane_ref)}"


def _safe_mapping_suffix(lane_ref: str) -> str:
    return lane_ref.split(":", 1)[-1].replace("_", "-")


def _mapping_supports_draft_fallback(mapping: AuthorityCapabilityMapping) -> bool:
    if mapping.unsupported_adapter_blocks_capability:
        return False
    capability = AuthorityCapability(mapping.capability)
    if capability in READ_PREPARE_CAPABILITIES:
        return True
    return mapping.status.startswith("implemented")


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
    unsupported_adapter_blocks_capability: bool = False,
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
        unsupported_adapter_blocks_capability=(
            unsupported_adapter_blocks_capability
            or status.startswith("planned_unsupported")
        ),
        operator_copy=operator_copy,
    )
