from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, deque
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_BUDGET_RECEIPTS_FILE,
    AUTHORITY_STATE_LOCK_KEY,
    AUTHORITY_STATE_REDACTIONS,
    MATRIX_HARNESS_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.authority.budget_contracts import AuthorityBudgetReadModel
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


AUTHORITY_LEASE_SCHEMA_VERSION = "uaa-authority-lease.v1"
AUTHORITY_STATE_SCHEMA_VERSION = "uaa-authority-state.v1"
AUTHORITY_LANE_CATALOG_SCHEMA_VERSION = "uaa-authority-lane-catalog.v1"
AUTHORITY_DOMAIN_READINESS_SCHEMA_VERSION = "uaa-authority-domain-readiness-index.v1"
AUTHORITY_MISSION_PLAN_SCHEMA_VERSION = "uaa-authority-mission-plan.v1"
AUTHORITY_CONSTRAINT_SCHEMA_VERSION = "uaa-authority-constraint.v1"
AUTHORITY_STATE_CONTRACT_REF = "contract-ref:authority-modes-mission-leases:v1"
AUTHORITY_LANE_CATALOG_CONTRACT_REF = "contract-ref:authority-lane-catalog:v1"
AUTHORITY_DOMAIN_READINESS_CONTRACT_REF = (
    "contract-ref:authority-domain-readiness:v1"
)
AUTHORITY_STATE_API_REF = "GET /api/runtime/authority-state"
AUTHORITY_STATE_SETTINGS_ROUTE_REF = "GET /control-center/settings/status#authority_lease_state"
AUTHORITY_STATE_CLI_REF = "repo-local-command:uaa-runtime-inspect-authority-state"
AUTHORITY_LANE_CATALOG_API_REF = "GET /api/runtime/authority-state#authority_lane_catalog"
AUTHORITY_LANE_CATALOG_CLI_REF = "repo-local-command:uaa-runtime-inspect-authority-lane-catalog"
AUTHORITY_DOMAIN_READINESS_API_REF = "GET /api/runtime/authority-domain-readiness"
AUTHORITY_DOMAIN_READINESS_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-domain-readiness"
)
AUTHORITY_MISSION_PLAN_ROUTE_REF = "POST /api/runtime/authority-missions/plan"
AUTHORITY_MISSION_PLAN_CLI_REF = "repo-local-command:uaa-runtime-plan-authority-mission"
AUTHORITY_STATE_DIR_ENV = "UAA_AUTHORITY_STATE_DIR"
AUTHORITY_LEASE_KILL_SWITCH_ENV = "UAA_AUTHORITY_LEASE_KILL_SWITCH"
AUTHORITY_LEASES_FILE = "authority_leases.json"
AUTHORITY_LEASE_RECEIPTS_FILE = "authority_lease_receipts.jsonl"
AUTHORITY_LEASE_LOCAL_OPERATOR_REF = "operator-ref:local-user"


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
    evidence_signing = "evidence_signing"


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


class AuthorityConstraintKind(str, Enum):
    resource_refs = "resource_refs"
    path_refs = "path_refs"
    app_refs = "app_refs"
    host_refs = "host_refs"
    delegation_depth = "delegation_depth"
    operation_budget = "operation_budget"
    cost_budget_microusd = "cost_budget_microusd"
    retry_attempts = "retry_attempts"


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


_AUTHORITY_REF_CONSTRAINT_KINDS = {
    AuthorityConstraintKind.resource_refs,
    AuthorityConstraintKind.path_refs,
    AuthorityConstraintKind.app_refs,
    AuthorityConstraintKind.host_refs,
}
_AUTHORITY_NUMERIC_CONSTRAINT_KINDS = {
    AuthorityConstraintKind.delegation_depth,
    AuthorityConstraintKind.operation_budget,
    AuthorityConstraintKind.cost_budget_microusd,
    AuthorityConstraintKind.retry_attempts,
}


class AuthorityConstraint(_AuthorityModel):
    schema_version: Literal["uaa-authority-constraint.v1"] = (
        AUTHORITY_CONSTRAINT_SCHEMA_VERSION
    )
    constraint_ref: str = Field(..., min_length=1)
    kind: AuthorityConstraintKind
    allowed_refs: list[str] = Field(default_factory=list)
    maximum: StrictInt | None = Field(default=None, ge=0)
    safe_summary: str = Field(..., min_length=1, max_length=260)
    @model_validator(mode="after")
    def validate_constraint(self) -> "AuthorityConstraint":
        validate_task_ref(self.constraint_ref, "authority_constraint_ref")
        validate_safe_task_text(self.schema_version, "authority_constraint_schema")
        validate_safe_task_text(_enum_value(self.kind), "authority_constraint_kind")
        validate_safe_task_text(self.safe_summary, "authority_constraint_summary")
        _validate_ref_list(self.allowed_refs, "authority_constraint_allowed_ref")
        kind = AuthorityConstraintKind(self.kind)
        if kind in _AUTHORITY_REF_CONSTRAINT_KINDS:
            if not self.allowed_refs or self.maximum is not None:
                raise ValueError("AUTHORITY_CONSTRAINT_REF_ALLOWLIST_REQUIRED")
        elif kind in _AUTHORITY_NUMERIC_CONSTRAINT_KINDS:
            if self.maximum is None or self.allowed_refs:
                raise ValueError("AUTHORITY_CONSTRAINT_MAXIMUM_REQUIRED")
        return self


class AuthorityConstraintClaim(_AuthorityModel):
    kind: AuthorityConstraintKind
    refs: list[str] = Field(default_factory=list)
    value: StrictInt | None = Field(default=None, ge=0)
    @model_validator(mode="after")
    def validate_claim(self) -> "AuthorityConstraintClaim":
        validate_safe_task_text(_enum_value(self.kind), "authority_constraint_claim_kind")
        _validate_ref_list(self.refs, "authority_constraint_claim_ref")
        kind = AuthorityConstraintKind(self.kind)
        if kind in _AUTHORITY_REF_CONSTRAINT_KINDS:
            if kind == AuthorityConstraintKind.resource_refs:
                if self.refs or self.value is not None:
                    raise ValueError("AUTHORITY_RESOURCE_CONSTRAINT_USES_ACTION_REFS")
            elif not self.refs or self.value is not None:
                raise ValueError("AUTHORITY_CONSTRAINT_CLAIM_REFS_REQUIRED")
        elif kind in _AUTHORITY_NUMERIC_CONSTRAINT_KINDS:
            if self.value is None or self.refs:
                raise ValueError("AUTHORITY_CONSTRAINT_CLAIM_VALUE_REQUIRED")
        return self


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
    authority_constraints: list[AuthorityConstraint] = Field(default_factory=list)
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
        constraint_kinds = [constraint.kind for constraint in self.authority_constraints]
        if len(constraint_kinds) != len(set(constraint_kinds)):
            raise ValueError("AUTHORITY_LEASE_DUPLICATE_CONSTRAINT_KIND")
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
    AuthorityCapability.click: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.click,
    },
    AuthorityCapability.form_fill: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.draft,
        AuthorityCapability.prepare,
        AuthorityCapability.form_fill,
    },
    AuthorityCapability.upload: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.prepare,
        AuthorityCapability.upload,
    },
    AuthorityCapability.download: {
        AuthorityCapability.observe,
        AuthorityCapability.read,
        AuthorityCapability.prepare,
        AuthorityCapability.download,
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
    constraint_claims: list[AuthorityConstraintClaim] = Field(default_factory=list)
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
        claim_kinds = [claim.kind for claim in self.constraint_claims]
        if len(claim_kinds) != len(set(claim_kinds)):
            raise ValueError("AUTHORITY_ACTION_DUPLICATE_CONSTRAINT_CLAIM_KIND")
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
    applied_constraint_refs: list[str] = Field(default_factory=list)
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
            (self.applied_constraint_refs, "authority_applied_constraint_ref"),
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
        # Empty mission domain requests intentionally mean: preview this mode's
        # current implemented default mission scope. The planner still performs
        # no execution and unsupported explicit domains fail closed below.
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


AuthorityLaneStatus = Literal[
    "implemented",
    "partial",
    "proposal_only",
    "approval_required",
    "planned",
    "blocked",
]


class AuthorityLaneCatalogEntry(_AuthorityModel):
    lane_id: str = Field(..., min_length=1, max_length=120)
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=160)
    status: AuthorityLaneStatus
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    side_effect_class: str = Field(..., min_length=1, max_length=120)
    risk: Literal["low", "medium", "high", "blocked"]
    allowed_inputs_schema: dict[str, Any] = Field(default_factory=dict)
    denied_capabilities: list[str] = Field(default_factory=list)
    approval_scope: str = Field(..., min_length=1, max_length=180)
    idempotency_required: bool
    rollback_posture: str = Field(..., min_length=1, max_length=360)
    receipt_kind: str = Field(..., min_length=1, max_length=120)
    cli_inspection_ref: str = Field(..., min_length=1, max_length=180)
    api_operation_ref: str = Field(..., min_length=1, max_length=180)
    control_center_surface_ref: str = Field(..., min_length=1, max_length=180)
    source_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    active_decision_outcome: AuthorityDecisionOutcome
    active_decision_ref: str = Field(..., min_length=1)
    active_decision_reason_refs: list[str] = Field(default_factory=list)
    known_authority: bool = True
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False
    raw_content_included: bool = False

    @model_validator(mode="after")
    def validate_lane_catalog_entry(self) -> "AuthorityLaneCatalogEntry":
        for value, field_name in [
            (self.lane_ref, "authority_lane_catalog_ref"),
            (self.active_decision_ref, "authority_lane_catalog_decision_ref"),
        ]:
            validate_task_ref(value, field_name)
        for refs, field_name in [
            (self.source_refs, "authority_lane_catalog_source_ref"),
            (self.blocked_reason_refs, "authority_lane_catalog_blocked_ref"),
            (
                self.unsupported_adapter_refs,
                "authority_lane_catalog_unsupported_adapter_ref",
            ),
            (
                self.active_decision_reason_refs,
                "authority_lane_catalog_decision_reason_ref",
            ),
        ]:
            _validate_ref_list(refs, field_name)
        for value in [
            self.lane_id,
            self.label,
            self.status,
            self.authority_domain,
            self.authority_capability,
            self.required_mode,
            self.side_effect_class,
            self.risk,
            self.approval_scope,
            self.rollback_posture,
            self.receipt_kind,
            self.cli_inspection_ref,
            self.api_operation_ref,
            self.control_center_surface_ref,
            self.active_decision_outcome,
            *self.denied_capabilities,
        ]:
            validate_safe_task_text(_enum_value(value), "authority_lane_catalog_text")
        validate_safe_task_payload(
            self.allowed_inputs_schema,
            "authority_lane_catalog_allowed_inputs_schema",
        )
        if self.status in {"approval_required", "blocked"} and not self.idempotency_required:
            raise ValueError("AUTHORITY_LANE_IDEMPOTENCY_REQUIRED_FOR_GOVERNED_LANE")
        if self.status == "blocked" and not (
            self.blocked_reason_refs or self.unsupported_adapter_refs
        ):
            raise ValueError("AUTHORITY_LANE_BLOCKED_REASON_REQUIRED")
        if (
            not self.known_authority
            or not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
            or self.raw_content_included
        ):
            raise ValueError("AUTHORITY_LANE_CATALOG_MUST_NOT_EXECUTE_OR_MINT_AUTHORITY")
        return self


class AuthorityLaneCatalogReadModel(_AuthorityModel):
    schema_version: Literal["uaa-authority-lane-catalog.v1"] = (
        AUTHORITY_LANE_CATALOG_SCHEMA_VERSION
    )
    contract_ref: str = AUTHORITY_LANE_CATALOG_CONTRACT_REF
    catalog_ref: str = "authority-lane-catalog-ref:uaa:v1"
    status: Literal["implemented_read_only_authority_lane_catalog"] = (
        "implemented_read_only_authority_lane_catalog"
    )
    api_ref: str = AUTHORITY_LANE_CATALOG_API_REF
    cli_ref: str = AUTHORITY_LANE_CATALOG_CLI_REF
    operator_summary: str = Field(..., min_length=1, max_length=720)
    entry_count: int = Field(..., ge=0)
    status_counts: dict[str, int] = Field(default_factory=dict)
    required_lane_ids: list[str] = Field(default_factory=list)
    missing_required_lane_ids: list[str] = Field(default_factory=list)
    entries: list[AuthorityLaneCatalogEntry] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False
    unknown_authority_default: AuthorityDecisionOutcome = AuthorityDecisionOutcome.deny
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    rollback_or_safe_disable_required: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    @model_validator(mode="after")
    def validate_lane_catalog(self) -> "AuthorityLaneCatalogReadModel":
        validate_task_ref(self.contract_ref, "authority_lane_catalog_contract_ref")
        validate_task_ref(self.catalog_ref, "authority_lane_catalog_ref")
        for value in [self.status, self.api_ref, self.cli_ref, self.operator_summary]:
            validate_safe_task_text(str(value), "authority_lane_catalog_text")
        for counts_key, count in self.status_counts.items():
            validate_safe_task_text(counts_key, "authority_lane_catalog_status")
            if count < 0:
                raise ValueError("AUTHORITY_LANE_STATUS_COUNT_INVALID")
        for refs, field_name in [
            (self.blocked_reason_refs, "authority_lane_catalog_blocked_ref"),
            (
                self.unsupported_adapter_refs,
                "authority_lane_catalog_unsupported_adapter_ref",
            ),
        ]:
            _validate_ref_list(refs, field_name)
        for lane_id in [*self.required_lane_ids, *self.missing_required_lane_ids]:
            validate_safe_task_text(lane_id, "authority_lane_catalog_required_lane_id")
        if self.entry_count != len(self.entries):
            raise ValueError("AUTHORITY_LANE_ENTRY_COUNT_DRIFT")
        actual_counts = Counter(entry.status for entry in self.entries)
        if self.status_counts != dict(sorted(actual_counts.items())):
            raise ValueError("AUTHORITY_LANE_STATUS_COUNTS_DRIFT")
        if self.missing_required_lane_ids:
            raise ValueError("AUTHORITY_LANE_REQUIRED_IDS_MISSING")
        if (
            not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
            or self.unknown_authority_default != AuthorityDecisionOutcome.deny.value
            or not self.receipts_required
            or not self.audit_required
            or not self.redaction_required
            or not self.rollback_or_safe_disable_required
        ):
            raise ValueError("AUTHORITY_LANE_CATALOG_GOVERNANCE_REQUIRED")
        return self


class AuthorityLeaseIssueRequest(_AuthorityModel):
    mode: TrustMode
    scope: AuthorityLeaseScope = AuthorityLeaseScope.session
    mission_ref: str | None = None
    operator_ref: str = AUTHORITY_LEASE_LOCAL_OPERATOR_REF
    requested_lease_ref: str | None = None
    requested_domains: dict[AuthorityDomain, list[AuthorityCapability]] = Field(
        default_factory=dict
    )
    authority_constraints: list[AuthorityConstraint] = Field(default_factory=list)
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
            (self.requested_lease_ref, "authority_lease_requested_lease_ref"),
            (self.decision_reason_ref, "authority_lease_decision_reason_ref"),
            (self.approval_ref, "authority_lease_approval_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "authority_lease_issue_summary")
        if (
            self.requested_lease_ref is not None
            and _exact_messages_issue_capability(self) is None
        ):
            raise ValueError("AUTHORITY_LEASE_REQUESTED_REF_EXACT_BINDING_REQUIRED")
        validate_safe_task_payload(self.constraints, "authority_lease_issue_constraints")
        validate_safe_task_payload(self.approval_grants, "authority_lease_approval_grants")
        constraint_kinds = [constraint.kind for constraint in self.authority_constraints]
        if len(constraint_kinds) != len(set(constraint_kinds)):
            raise ValueError("AUTHORITY_LEASE_DUPLICATE_CONSTRAINT_KIND")
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


def _exact_messages_issue_capability(
    request: AuthorityLeaseIssueRequest,
) -> AuthorityCapability | None:
    exact_binding = (
        request.constraints.get("exact_lane_ref"),
        request.constraints.get("exact_capability_ref"),
        request.constraints.get("exact_adapter_ref"),
        request.constraints.get("exact_tool_ref"),
    )
    if not all(isinstance(value, str) for value in exact_binding):
        return None
    accepted = {
        (lane, capability, adapter, tool): AuthorityCapability(authority_capability)
        for authority_capability, lane, capability, adapter, tool in (
            MATRIX_HARNESS_EXACT_AUTHORITY_BINDINGS
        )
    }
    expected_capability = accepted.get(exact_binding)
    requested_messages = request.requested_domains.get(AuthorityDomain.messages, [])
    if not (
        request.scope == AuthorityLeaseScope.mission
        and request.mission_ref is not None
        and request.requested_lease_ref is not None
        and set(request.requested_domains) == {AuthorityDomain.messages}
        and expected_capability is not None
        and requested_messages == [expected_capability]
        and isinstance(
            request.constraints.get("exact_request_fingerprint_ref"), str
        )
        and len(request.authority_constraints) > 0
    ):
        return None
    return expected_capability


class AuthorityLeaseApproveAndIssueRequest(_AuthorityModel):
    lease_issue_request: AuthorityLeaseIssueRequest

    @model_validator(mode="after")
    def validate_approve_and_issue_request(
        self,
    ) -> "AuthorityLeaseApproveAndIssueRequest":
        if self.lease_issue_request.operator_ref != AUTHORITY_LEASE_LOCAL_OPERATOR_REF:
            raise ValueError("AUTHORITY_LEASE_LOCAL_OPERATOR_REF_REQUIRED")
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


AuthorityDomainReadinessStatus = Literal[
    "active_allow",
    "requires_confirmation",
    "draft_only",
    "known_denied",
    "blocked_unsupported",
    "unmapped_target_domain",
]


class AuthorityDomainReadinessEntry(_AuthorityModel):
    schema_version: Literal["uaa-authority-domain-readiness.v1"] = (
        "uaa-authority-domain-readiness.v1"
    )
    domain: AuthorityDomain
    status: AuthorityDomainReadinessStatus
    mapped_capability_count: int = Field(default=0, ge=0)
    mapped_capability_refs: list[str] = Field(default_factory=list)
    active_lease_refs: list[str] = Field(default_factory=list)
    default_requested_modes: list[TrustMode] = Field(default_factory=list)
    issue_ready_modes: list[TrustMode] = Field(default_factory=list)
    grantable_capabilities: list[AuthorityCapability] = Field(default_factory=list)
    decision_outcome_counts: dict[str, int] = Field(default_factory=dict)
    mapped_status_counts: dict[str, int] = Field(default_factory=dict)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    operator_summary: str = Field(..., min_length=1, max_length=520)
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False

    @model_validator(mode="after")
    def validate_domain_readiness(self) -> "AuthorityDomainReadinessEntry":
        validate_safe_task_text(_enum_value(self.domain), "authority_domain_readiness")
        validate_safe_task_text(self.status, "authority_domain_readiness_status")
        for counts, field_name in [
            (
                self.decision_outcome_counts,
                "authority_domain_readiness_outcome",
            ),
            (self.mapped_status_counts, "authority_domain_readiness_mapping_status"),
        ]:
            for key, value in counts.items():
                validate_safe_task_text(key, field_name)
                if value < 0:
                    raise ValueError("AUTHORITY_DOMAIN_READINESS_COUNT_INVALID")
        for refs, field_name in [
            (
                self.mapped_capability_refs,
                "authority_domain_readiness_capability_ref",
            ),
            (self.active_lease_refs, "authority_domain_readiness_lease_ref"),
            (
                self.unsupported_adapter_refs,
                "authority_domain_readiness_unsupported_ref",
            ),
            (self.blocked_reason_refs, "authority_domain_readiness_blocked_ref"),
        ]:
            _validate_ref_list(refs, field_name)
        for value in [
            *self.default_requested_modes,
            *self.issue_ready_modes,
            *self.grantable_capabilities,
        ]:
            validate_safe_task_text(
                _enum_value(value),
                "authority_domain_readiness_text",
            )
        validate_safe_task_text(
            self.operator_summary,
            "authority_domain_readiness_summary",
        )
        if self.mapped_capability_count != len(self.mapped_capability_refs):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_CAPABILITY_COUNT_DRIFT")
        if (
            self.status == "unmapped_target_domain"
            and self.mapped_capability_refs
        ):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_UNMAPPED_HAS_CAPABILITIES")
        if self.status != "unmapped_target_domain" and not self.mapped_capability_refs:
            raise ValueError("AUTHORITY_DOMAIN_READINESS_STATUS_WITHOUT_MAPPING")
        if (
            not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
        ):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MUST_NOT_EXECUTE")
        return self


class AuthorityDomainReadinessReadModel(_AuthorityModel):
    schema_version: Literal["uaa-authority-domain-readiness-index.v1"] = (
        AUTHORITY_DOMAIN_READINESS_SCHEMA_VERSION
    )
    contract_ref: str = AUTHORITY_DOMAIN_READINESS_CONTRACT_REF
    api_ref: str = AUTHORITY_DOMAIN_READINESS_API_REF
    source_authority_state_api_ref: str = AUTHORITY_STATE_API_REF
    settings_route_ref: str = AUTHORITY_STATE_SETTINGS_ROUTE_REF
    cli_ref: str = AUTHORITY_DOMAIN_READINESS_CLI_REF
    operator_summary: str = Field(..., min_length=1, max_length=720)
    target_domains: list[AuthorityDomain] = Field(default_factory=lambda: list(AuthorityDomain))
    policy_outcomes: list[AuthorityDecisionOutcome] = Field(
        default_factory=lambda: list(AuthorityDecisionOutcome)
    )
    domain_count: int = Field(..., ge=0)
    status_counts: dict[str, int] = Field(default_factory=dict)
    decision_outcome_counts: dict[str, int] = Field(default_factory=dict)
    entries: list[AuthorityDomainReadinessEntry] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    execution_performed: bool = False
    mutation_performed: bool = False
    control_center_grants_authority: bool = False
    unknown_authority_default: AuthorityDecisionOutcome = AuthorityDecisionOutcome.deny
    receipts_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    @model_validator(mode="after")
    def validate_domain_readiness_model(self) -> "AuthorityDomainReadinessReadModel":
        validate_task_ref(self.contract_ref, "authority_domain_readiness_contract_ref")
        for value in [
            self.api_ref,
            self.source_authority_state_api_ref,
            self.settings_route_ref,
            self.cli_ref,
            self.operator_summary,
        ]:
            validate_safe_task_text(value, "authority_domain_readiness_model_text")
        for counts, field_name in [
            (self.status_counts, "authority_domain_readiness_model_status"),
            (
                self.decision_outcome_counts,
                "authority_domain_readiness_model_outcome",
            ),
        ]:
            for key, count in counts.items():
                validate_safe_task_text(key, field_name)
                if count < 0:
                    raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_COUNT_INVALID")
        for refs, field_name in [
            (
                self.blocked_reason_refs,
                "authority_domain_readiness_model_blocked_ref",
            ),
            (
                self.unsupported_adapter_refs,
                "authority_domain_readiness_model_unsupported_ref",
            ),
        ]:
            _validate_ref_list(refs, field_name)
        for redaction in self.redactions_applied:
            validate_safe_task_text(
                redaction,
                "authority_domain_readiness_model_redaction",
            )
        if self.domain_count != len(self.entries):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_COUNT_DRIFT")
        entry_domains = [_enum_value(entry.domain) for entry in self.entries]
        if len(entry_domains) != len(set(entry_domains)):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_DUPLICATE_DOMAIN")
        if set(entry_domains) != {_enum_value(domain) for domain in self.target_domains}:
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_TARGET_DOMAIN_DRIFT")
        actual_status_counts = Counter(entry.status for entry in self.entries)
        if self.status_counts != dict(sorted(actual_status_counts.items())):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_STATUS_COUNT_DRIFT")
        if self.unknown_authority_default != AuthorityDecisionOutcome.deny.value:
            raise ValueError("AUTHORITY_DOMAIN_READINESS_UNKNOWN_MUST_DENY")
        if (
            not self.safe_refs_only
            or self.execution_performed
            or self.mutation_performed
            or self.control_center_grants_authority
            or not self.receipts_required
            or not self.audit_required
            or not self.redaction_required
        ):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_MODEL_MUST_NOT_EXECUTE")
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
    request_fingerprint_ref: str | None = None
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
            (
                self.request_fingerprint_ref,
                "authority_lease_receipt_request_fingerprint_ref",
            ),
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
    domain_readiness: list[AuthorityDomainReadinessEntry] = Field(default_factory=list)
    authority_lane_catalog: AuthorityLaneCatalogReadModel
    decision_catalog: list[AuthorityDecisionCatalogEntry] = Field(default_factory=list)
    recent_receipts: list[AuthorityLeaseReceipt] = Field(default_factory=list)
    authority_budget: AuthorityBudgetReadModel = Field(
        default_factory=AuthorityBudgetReadModel
    )
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
        readiness_domains = [_enum_value(entry.domain) for entry in self.domain_readiness]
        if len(readiness_domains) != len(set(readiness_domains)):
            raise ValueError("AUTHORITY_DOMAIN_READINESS_DUPLICATE_DOMAIN")
        if set(readiness_domains) != {
            _enum_value(domain) for domain in self.target_domains
        }:
            raise ValueError("AUTHORITY_DOMAIN_READINESS_TARGET_DOMAIN_DRIFT")
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


def _lease_constraint_match(
    lease: AuthorityLease,
    request: AuthorityActionRequest,
) -> tuple[list[str], list[str]]:
    claims = {
        AuthorityConstraintKind(claim.kind): claim for claim in request.constraint_claims
    }
    reason_refs: list[str] = []
    applied_refs: list[str] = []
    for constraint in lease.authority_constraints:
        kind = AuthorityConstraintKind(constraint.kind)
        if kind == AuthorityConstraintKind.resource_refs:
            actual_refs = request.resource_refs
        else:
            claim = claims.get(kind)
            if claim is None:
                reason_refs.append(
                    f"reason-ref:authority:constraint-claim-missing:{kind.value}"
                )
                continue
            actual_refs = claim.refs
        if kind in _AUTHORITY_REF_CONSTRAINT_KINDS:
            if not actual_refs:
                reason_refs.append(
                    f"reason-ref:authority:constraint-claim-missing:{kind.value}"
                )
                continue
            if not set(actual_refs).issubset(set(constraint.allowed_refs)):
                reason_refs.append(
                    f"reason-ref:authority:constraint-ref-outside-scope:{kind.value}"
                )
                continue
        elif kind in _AUTHORITY_NUMERIC_CONSTRAINT_KINDS:
            claim = claims.get(kind)
            if claim is None or claim.value is None:
                reason_refs.append(
                    f"reason-ref:authority:constraint-claim-missing:{kind.value}"
                )
                continue
            if constraint.maximum is None or claim.value > constraint.maximum:
                reason_refs.append(
                    f"reason-ref:authority:constraint-limit-exceeded:{kind.value}"
                )
                continue
        applied_refs.append(constraint.constraint_ref)
    return list(dict.fromkeys(reason_refs)), applied_refs


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


def _exact_messages_binding(lease: AuthorityLease) -> tuple[str, str, str, str] | None:
    values = tuple(
        lease.constraints.get(key)
        for key in (
            "exact_lane_ref",
            "exact_capability_ref",
            "exact_adapter_ref",
            "exact_tool_ref",
        )
    )
    if not all(isinstance(value, str) for value in values):
        return None
    return values  # type: ignore[return-value]


def _lease_exact_messages_binding_matches(
    lease: AuthorityLease,
    request: AuthorityActionRequest,
) -> bool:
    if request.domain != AuthorityDomain.messages:
        return True
    binding = _exact_messages_binding(lease)
    if binding is None:
        return False
    lane_ref, capability_ref, adapter_ref, tool_ref = binding
    allowed = {
        (lane, capability, adapter, tool): AuthorityCapability(authority_capability)
        for authority_capability, lane, capability, adapter, tool in (
            MATRIX_HARNESS_EXACT_AUTHORITY_BINDINGS
        )
    }
    expected_authority_capability = allowed.get(binding)
    granted_messages_capabilities = lease.domains.get(AuthorityDomain.messages, [])
    return (
        expected_authority_capability is not None
        and granted_messages_capabilities == [expected_authority_capability]
        and AuthorityCapability(request.capability) == expected_authority_capability
        and request.lane_ref == lane_ref
        and request.capability_ref == capability_ref
        and request.adapter_ref == adapter_ref
        and request.constraints.get("tool_ref") == tool_ref
        and request.constraints.get("request_fingerprint_ref")
        == lease.constraints.get("exact_request_fingerprint_ref")
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
    matching_scope = [
        lease
        for lease in matching_domain_capability
        if _lease_scope_matches_action(lease, request)
        and _lease_exact_messages_binding_matches(lease, request)
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
    if not matching_scope:
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
    constraint_results = [
        (lease, *_lease_constraint_match(lease, request)) for lease in matching_scope
    ]
    matching = [item for item in constraint_results if not item[1]]
    if not matching:
        constraint_reason_refs = list(
            dict.fromkeys(
                reason
                for _, mismatch_refs, _ in constraint_results
                for reason in mismatch_refs
            )
        )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            reason_refs=[
                "reason-ref:authority:lease-constraint-mismatch",
                *constraint_reason_refs,
            ],
            operator_message=(
                "Denied because the action does not satisfy the active lease constraints."
            ),
            known_authority=True,
        )
    lease, _, applied_constraint_refs = matching[0]
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
            applied_constraint_refs=applied_constraint_refs,
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
                applied_constraint_refs=applied_constraint_refs,
            )
        return _decision(
            request,
            AuthorityDecisionOutcome.deny,
            lease=lease,
            reason_refs=reason_refs,
            operator_message="Requires a stronger trust mode for this capability.",
            known_authority=True,
            applied_constraint_refs=applied_constraint_refs,
        )
    reason_refs.append("reason-ref:authority:active-lease-grants-domain-capability")
    return _decision(
        request,
        AuthorityDecisionOutcome.allow,
        lease=lease,
        reason_refs=reason_refs,
        operator_message="Allowed by active authority lease.",
        known_authority=True,
        applied_constraint_refs=applied_constraint_refs,
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
    applied_constraint_refs: list[str] | None = None,
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
        applied_constraint_refs=applied_constraint_refs or [],
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


def _authority_lease_operation_fingerprint_ref(
    operation: Literal["issue", "revoke"],
    request: AuthorityLeaseIssueRequest | AuthorityLeaseRevokeRequest,
) -> str:
    payload = request.model_dump(mode="json")
    if operation == "issue":
        payload.pop("approval_grants", None)
    return _stable_ref(
        "request-fingerprint-ref:authority-lease",
        {"operation": operation, "request": payload},
    )


def authority_state_dir() -> Path:
    value = os.environ.get(AUTHORITY_STATE_DIR_ENV, "").strip()
    if value:
        return Path(value).expanduser()
    return Path(".uaa") / "authority"


@lru_cache(maxsize=32)
def authority_state_lock_manager(state_dir_ref: str) -> FileSingleWriterLockManager:
    return FileSingleWriterLockManager(Path(state_dir_ref))


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
            AuthorityDomain.files: [
                AuthorityCapability.read,
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
            AuthorityDomain.browser: [
                AuthorityCapability.read,
            ],
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.observe,
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
            AuthorityDomain.contacts: [
                AuthorityCapability.read,
                AuthorityCapability.write,
            ],
            AuthorityDomain.email: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.calendar: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.browser: [
                AuthorityCapability.read,
            ],
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.observe,
                AuthorityCapability.read,
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
            AuthorityDomain.contacts: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.mutate,
            ],
            AuthorityDomain.email: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.calendar: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.browser: [
                AuthorityCapability.read,
            ],
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.observe,
                AuthorityCapability.read,
            ],
        }
    if mode == TrustMode.full_machine_access_session:
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
            AuthorityDomain.contacts: [
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.mutate,
            ],
            AuthorityDomain.email: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.calendar: [
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            ],
            AuthorityDomain.browser: [
                AuthorityCapability.read,
            ],
            AuthorityDomain.provider_model_calls: [
                AuthorityCapability.read,
                AuthorityCapability.execute,
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
        AuthorityDomain.contacts: [
            AuthorityCapability.read,
            AuthorityCapability.write,
            AuthorityCapability.mutate,
        ],
        AuthorityDomain.email: [
            AuthorityCapability.observe,
            AuthorityCapability.draft,
        ],
        AuthorityDomain.calendar: [
            AuthorityCapability.observe,
            AuthorityCapability.draft,
        ],
        AuthorityDomain.browser: [
            AuthorityCapability.read,
        ],
        AuthorityDomain.provider_model_calls: [
            AuthorityCapability.read,
            AuthorityCapability.execute,
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
        AuthorityDomain.evidence_signing: {
            AuthorityCapability.execute,
            AuthorityCapability.mutate,
        },
        # This admits only the coarse domain/capability projection needed by
        # the six exact disposable Matrix harness lanes. Their adapters still
        # require exact capability, lane, tool, mission, and resource-set
        # equality, so this cannot authorize message sync or send.
        AuthorityDomain.messages: {
            AuthorityCapability.read,
            AuthorityCapability.execute,
            AuthorityCapability.mutate,
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
            AuthorityDomain.messages: {
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
            AuthorityDomain.browser: {
                AuthorityCapability.read,
            },
            AuthorityDomain.provider_model_calls: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
            },
            AuthorityDomain.evidence_signing: {
                AuthorityCapability.execute,
                AuthorityCapability.mutate,
            },
            AuthorityDomain.messages: {
                AuthorityCapability.read,
                AuthorityCapability.execute,
                AuthorityCapability.mutate,
            },
        }
    if mode == TrustMode.approved_safe_local_work_session:
        return {
            AuthorityDomain.workspace: {
                AuthorityCapability.read,
                AuthorityCapability.write,
                AuthorityCapability.execute,
            },
            AuthorityDomain.messages: {
                AuthorityCapability.read,
                AuthorityCapability.execute,
                AuthorityCapability.mutate,
            },
        }
    if mode == TrustMode.full_local_workspace_session:
        return {
            **_local_implemented_authority_capabilities(),
            AuthorityDomain.email: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.calendar: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.provider_model_calls: {
                AuthorityCapability.observe,
                AuthorityCapability.read,
            },
        }
    if mode == TrustMode.full_machine_access_session:
        return {
            **_local_implemented_authority_capabilities(),
            AuthorityDomain.email: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.calendar: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
        }
    if mode == TrustMode.delegated_mission_autonomous_window:
        return {
            **_local_implemented_authority_capabilities(),
            AuthorityDomain.email: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
            AuthorityDomain.calendar: {
                AuthorityCapability.observe,
                AuthorityCapability.draft,
            },
        }
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
        if domain_value == AuthorityDomain.messages:
            expected_capability = _exact_messages_issue_capability(request)
            if expected_capability is None or granted_capabilities != [
                expected_capability
            ]:
                granted_capabilities = []
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
    for constraint in request.authority_constraints:
        resource_refs.extend(
            [
                constraint.constraint_ref,
                *constraint.allowed_refs,
                _stable_ref(
                    "authority-constraint-binding-ref",
                    constraint.model_dump(mode="json"),
                ),
            ]
        )
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
        "authority_constraints": [
            constraint.model_dump(mode="json")
            for constraint in request.authority_constraints
        ],
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
    if not domains:
        return _default_requested_domains(TrustMode(request.requested_mode))
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
        self.lock_manager = authority_state_lock_manager(
            str(self.state_dir.resolve())
        )

    def list_leases(self, *, active_only: bool = False) -> list[AuthorityLease]:
        if not self.leases_path.exists():
            return []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._list_leases(active_only=active_only)

    def _list_leases(self, *, active_only: bool = False) -> list[AuthorityLease]:
        leases = self._read_leases()
        if active_only:
            leases = [lease for lease in leases if lease.is_active()]
        return leases

    def list_receipts(self, *, limit: int = 20) -> list[AuthorityLeaseReceipt]:
        if limit <= 0 or not self.receipts_path.exists():
            return []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._list_receipts(limit=limit)

    def _list_receipts(self, *, limit: int = 20) -> list[AuthorityLeaseReceipt]:
        if not self.receipts_path.exists():
            return []
        if limit <= 0:
            return []
        recent_lines: deque[str] = deque(maxlen=limit)
        with self.receipts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    recent_lines.append(line)
        return [AuthorityLeaseReceipt(**json.loads(line)) for line in recent_lines]

    def build_state_read_model(self) -> AuthorityStateReadModel:
        budget_receipts_path = self.state_dir / AUTHORITY_BUDGET_RECEIPTS_FILE
        if not any(
            path.exists()
            for path in [self.leases_path, self.receipts_path, budget_receipts_path]
        ):
            return build_authority_state_read_model(
                kill_switch_engaged=authority_lease_kill_switch_engaged(),
            )
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            active = self._list_leases(active_only=True)
            from ultimate_ai_agent.core.authority.budgets import AuthorityBudgetStore

            budget_read_model = AuthorityBudgetStore(
                self.state_dir,
                lease_store=self,
            )._build_read_model(recent_limit=8)
            return build_authority_state_read_model(
                active_leases=active or build_default_authority_leases(),
                recent_receipts=self._list_receipts(limit=8),
                budget_read_model=budget_read_model,
                kill_switch_engaged=authority_lease_kill_switch_engaged(),
            )

    def build_domain_readiness_read_model(self) -> AuthorityDomainReadinessReadModel:
        active = self.list_leases(active_only=True) or build_default_authority_leases()
        kill_switch_engaged = authority_lease_kill_switch_engaged()
        capability_mappings = build_existing_lane_authority_mappings()
        decision_catalog = build_authority_decision_catalog(
            capability_mappings,
            active,
            kill_switch_engaged=kill_switch_engaged,
        )
        return build_authority_domain_readiness_read_model(
            decision_catalog,
            active_leases=active,
            mode_catalog=build_authority_mode_catalog(
                kill_switch_engaged=kill_switch_engaged,
            ),
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
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._issue_lease(
                request,
                idempotency_ref=idempotency_ref,
                approval_validator=approval_validator,
            )

    def _issue_lease(
        self,
        request: AuthorityLeaseIssueRequest,
        *,
        idempotency_ref: str,
        approval_validator: AuthorityLeaseApprovalValidator | None = None,
    ) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
        validate_task_ref(idempotency_ref, "authority_lease_idempotency_ref")
        request_fingerprint_ref = _authority_lease_operation_fingerprint_ref(
            "issue", request
        )
        existing = self._receipt_for_idempotency(idempotency_ref)
        if existing is not None:
            if (
                existing.operation != "issue"
                or existing.request_fingerprint_ref != request_fingerprint_ref
            ):
                raise AuthorityLeaseConflictError("AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT")
            lease = self._lease_by_ref(existing.lease_ref)
            return lease, existing.model_copy(update={"status": "replayed"})
        if (
            request.requested_lease_ref is not None
            and self._lease_by_ref(request.requested_lease_ref) is not None
        ):
            raise AuthorityLeaseConflictError("AUTHORITY_LEASE_REF_CONFLICT")
        granted, denied_refs, unsupported_refs = _filter_requested_domains(request)
        approval_requirement = build_authority_lease_approval_requirement(
            request,
            granted,
            idempotency_ref=idempotency_ref,
        )
        computed_lease_ref = _stable_ref(
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
                "authority_constraints": [
                    constraint.model_dump(mode="json")
                    for constraint in request.authority_constraints
                ],
            },
        )
        lease_ref = request.requested_lease_ref or computed_lease_ref
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
            authority_constraints=request.authority_constraints,
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
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._revoke_lease(
                request,
                idempotency_ref=idempotency_ref,
            )

    def _revoke_lease(
        self,
        request: AuthorityLeaseRevokeRequest,
        *,
        idempotency_ref: str,
    ) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
        validate_task_ref(idempotency_ref, "authority_lease_idempotency_ref")
        request_fingerprint_ref = _authority_lease_operation_fingerprint_ref(
            "revoke", request
        )
        existing = self._receipt_for_idempotency(idempotency_ref)
        if existing is not None:
            if (
                existing.operation != "revoke"
                or existing.request_fingerprint_ref != request_fingerprint_ref
            ):
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
                request_fingerprint_ref=request_fingerprint_ref,
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
            request_fingerprint_ref=request_fingerprint_ref,
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
            request_fingerprint_ref=_authority_lease_operation_fingerprint_ref(
                operation, request
            ),
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
        temp_path = self.leases_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, self.leases_path)
        directory_fd = os.open(self.state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def _append_receipt(self, receipt: AuthorityLeaseReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt.model_dump(mode="json"), sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _receipt_for_idempotency(
        self,
        idempotency_ref: str,
    ) -> AuthorityLeaseReceipt | None:
        if not self.receipts_path.exists():
            return None
        matched: AuthorityLeaseReceipt | None = None
        with self.receipts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                receipt = AuthorityLeaseReceipt(**json.loads(line))
                if receipt.idempotency_ref == idempotency_ref:
                    if matched is not None and (
                        receipt.operation != matched.operation
                        or receipt.lease_ref != matched.lease_ref
                        or receipt.request_fingerprint_ref
                        != matched.request_fingerprint_ref
                    ):
                        raise AuthorityLeaseConflictError(
                            "AUTHORITY_LEASE_IDEMPOTENCY_HISTORY_CONFLICT"
                        )
                    matched = receipt
        return matched

    def _lease_by_ref(self, lease_ref: str) -> AuthorityLease | None:
        return next((lease for lease in self._read_leases() if lease.lease_ref == lease_ref), None)

    def get_lease(self, lease_ref: str) -> AuthorityLease | None:
        validate_task_ref(lease_ref, "authority_lease_ref")
        if not self.leases_path.exists():
            return None
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            return self._lease_by_ref(lease_ref)


def build_existing_lane_authority_mappings() -> list[AuthorityCapabilityMapping]:
    return [
        mapping.model_copy(deep=True)
        for mapping in _cached_existing_lane_authority_mappings()
    ]


@lru_cache(maxsize=1)
def _cached_existing_lane_authority_mappings() -> tuple[AuthorityCapabilityMapping, ...]:
    return tuple(_build_existing_lane_authority_mappings_uncached())


def _build_existing_lane_authority_mappings_uncached() -> list[AuthorityCapabilityMapping]:
    from ultimate_ai_agent.core.authority.lane_registry import (
        build_existing_lane_authority_mappings as build_registry,
    )

    return build_registry()


def build_authority_state_read_model(
    *,
    active_leases: list[AuthorityLease] | None = None,
    recent_receipts: list[AuthorityLeaseReceipt] | None = None,
    budget_read_model: AuthorityBudgetReadModel | None = None,
    kill_switch_engaged: bool = False,
) -> AuthorityStateReadModel:
    leases = active_leases or build_default_authority_leases()
    capability_mappings = build_existing_lane_authority_mappings()
    decision_catalog = build_authority_decision_catalog(
        capability_mappings,
        leases,
        kill_switch_engaged=kill_switch_engaged,
    )
    mode_catalog = build_authority_mode_catalog(
        kill_switch_engaged=kill_switch_engaged,
    )
    domain_readiness_model = build_authority_domain_readiness_read_model(
        decision_catalog,
        active_leases=leases,
        mode_catalog=mode_catalog,
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
        mode_catalog=mode_catalog,
        active_leases=leases,
        capability_mappings=capability_mappings,
        decision_summary=build_authority_decision_summary(
            decision_catalog,
            active_lease_count=len(leases),
        ),
        domain_readiness=domain_readiness_model.entries,
        authority_lane_catalog=build_authority_lane_catalog_read_model(
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        decision_catalog=decision_catalog,
        recent_receipts=recent_receipts or [],
        authority_budget=budget_read_model
        or AuthorityBudgetReadModel(kill_switch_engaged=kill_switch_engaged),
        sample_decisions=samples,
        kill_switch_engaged=kill_switch_engaged,
    )


REQUIRED_AUTHORITY_LANE_IDS = (
    "local.verify.focused_pytest",
    "local.verify.repo_verifier",
    "local.verify.frontend_check",
    "code.patch_proposal",
    "calculation.sealed_arithmetic",
    "code.apply_exact_patch",
    "web.evidence.fetch_readonly",
    "memory.review.decision",
    "model.provider.readiness",
    "extension.catalog.review",
    "matrix.harness.inspect",
    "matrix.harness.smoke",
    "matrix.harness.start",
    "matrix.harness.fixture_seed",
    "matrix.harness.stop",
    "matrix.harness.reset",
)


def build_authority_lane_catalog_read_model(
    *,
    active_leases: list[AuthorityLease] | None = None,
    kill_switch_engaged: bool = False,
) -> AuthorityLaneCatalogReadModel:
    from ultimate_ai_agent.core.sandbox_calculation.authority_surfaces import build_sealed_arithmetic_lane_catalog_entry
    from ultimate_ai_agent.core.communications.matrix_harness.authority_surfaces import build_matrix_harness_lane_catalog_entries
    leases = active_leases or build_default_authority_leases()
    entries = [
        _authority_lane_entry(
            lane_id="local.verify.focused_pytest",
            label="Focused pytest verifier",
            status="approval_required",
            authority_domain=AuthorityDomain.shell,
            authority_capability=AuthorityCapability.execute,
            required_mode=TrustMode.approved_safe_local_work_session,
            side_effect_class="local_dev_workspace_only",
            risk="medium",
            allowed_inputs_schema={
                "argv": "fixed_pytest_wrapper",
                "selector_refs": "bounded_repo_local_test_selectors",
                "cwd": "repo_root_only",
                "shell_expansion": False,
            },
            denied_capabilities=[
                "arbitrary command strings",
                "shell expansion",
                "network commands",
                "background processes",
                "raw command output persistence",
            ],
            approval_scope="approval-scope:runtime-focused-pytest-exact",
            idempotency_required=True,
            rollback_posture="No mutation rollback; safe-disable cancels the RuntimeGateway lane and receipts keep redacted output refs only.",
            receipt_kind="runtime_command_receipt",
            cli_inspection_ref="scripts/dev/uaa_runtime.py inspect-action-inbox-bridge",
            api_operation_ref="POST /api/runtime/invocations/{id}/execute",
            control_center_surface_ref="control-center-surface:actions-inbox",
            source_refs=[
                "lane-ref:runtime-gateway:focused-pytest-action-inbox",
                "capability-ref:runtime-gateway:focused-pytest-action-inbox",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="local.verify.repo_verifier",
            label="Repo verifier command",
            status="approval_required",
            authority_domain=AuthorityDomain.shell,
            authority_capability=AuthorityCapability.execute,
            required_mode=TrustMode.approved_safe_local_work_session,
            side_effect_class="local_dev_workspace_only",
            risk="medium",
            allowed_inputs_schema={
                "argv": "fixed_verifier_script_id",
                "script_refs": "allowlisted_repo_verifier_refs",
                "cwd": "repo_root_only",
                "shell_expansion": False,
            },
            denied_capabilities=[
                "arbitrary verifier paths",
                "shell expansion",
                "network commands",
                "background processes",
                "raw command output persistence",
            ],
            approval_scope="approval-scope:runtime-repo-verifier-exact",
            idempotency_required=True,
            rollback_posture="No mutation rollback; safe-disable cancels the RuntimeGateway lane and receipts keep redacted verifier refs only.",
            receipt_kind="runtime_command_receipt",
            cli_inspection_ref="scripts/dev/uaa_runtime.py inspect-action-inbox-bridge",
            api_operation_ref="POST /api/runtime/invocations/{id}/execute",
            control_center_surface_ref="control-center-surface:actions-inbox",
            source_refs=[
                "lane-ref:runtime-gateway:repo-verifier-action-inbox",
                "capability-ref:runtime-gateway:repo-verifier-action-inbox",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="local.verify.frontend_check",
            label="Frontend check command",
            status="approval_required",
            authority_domain=AuthorityDomain.shell,
            authority_capability=AuthorityCapability.execute,
            required_mode=TrustMode.approved_safe_local_work_session,
            side_effect_class="local_dev_workspace_only",
            risk="medium",
            allowed_inputs_schema={
                "argv": "fixed_frontend_check_wrapper",
                "workspace": "control_center_app_only",
                "cwd": "repo_root_only",
                "shell_expansion": False,
            },
            denied_capabilities=[
                "arbitrary package scripts",
                "shell expansion",
                "network commands",
                "background processes",
                "raw command output persistence",
            ],
            approval_scope="approval-scope:runtime-frontend-check-exact",
            idempotency_required=True,
            rollback_posture="No mutation rollback; safe-disable cancels the RuntimeGateway lane and receipts keep redacted check refs only.",
            receipt_kind="runtime_command_receipt",
            cli_inspection_ref="scripts/dev/uaa_runtime.py inspect-action-inbox-bridge",
            api_operation_ref="POST /api/runtime/invocations/{id}/execute",
            control_center_surface_ref="control-center-surface:actions-inbox",
            source_refs=[
                "lane-ref:runtime-gateway:frontend-check-action-inbox",
                "capability-ref:runtime-gateway:frontend-check-action-inbox",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="code.patch_proposal",
            label="Code patch proposal artifact",
            status="proposal_only",
            authority_domain=AuthorityDomain.workspace,
            authority_capability=AuthorityCapability.draft,
            required_mode=TrustMode.read_only,
            side_effect_class="validation_only",
            risk="low",
            allowed_inputs_schema={
                "source_refs": "safe_file_and_context_refs_only",
                "artifact_refs": "diff_summary_and_hash_refs_only",
                "file_mutation": False,
            },
            denied_capabilities=[
                "file writes",
                "patch apply",
                "shell execution",
                "provider model calls",
                "hidden context injection",
            ],
            approval_scope="approval-scope:not-required-for-preview",
            idempotency_required=False,
            rollback_posture="No mutation is performed; rollback posture is planned before any apply lane can graduate.",
            receipt_kind="proposal_receipt_plan",
            cli_inspection_ref="scripts/dev/uaa_coding.py inspect-patch-proposal",
            api_operation_ref="GET /control-center/coding/patch-proposal",
            control_center_surface_ref="control-center-surface:code-workbench",
            source_refs=[
                "capability-ref:coding:patch-proposal-preview",
                "lane-ref:coding:patch-proposal-preview",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        build_sealed_arithmetic_lane_catalog_entry(active_leases=leases, kill_switch_engaged=kill_switch_engaged),
        _authority_lane_entry(
            lane_id="code.apply_exact_patch",
            label="Code exact patch apply",
            status="blocked",
            authority_domain=AuthorityDomain.files,
            authority_capability=AuthorityCapability.write,
            required_mode=TrustMode.full_local_workspace_session,
            side_effect_class="local_dev_workspace_only",
            risk="high",
            allowed_inputs_schema={
                "patch_ref": "precomputed_patch_hash_ref",
                "file_refs": "approved_repo_file_refs_only",
                "rollback_ref": "required_before_apply",
                "shell_execution": False,
            },
            denied_capabilities=[
                "unhashed patch payloads",
                "unapproved file targets",
                "shell execution",
                "git mutation",
                "provider model calls",
            ],
            approval_scope="approval-scope:coding-approved-patch-apply-exact",
            idempotency_required=True,
            rollback_posture="Blocked until checkpoint and rollback artifact refs are implemented and tested for exact patch apply.",
            receipt_kind="patch_apply_receipt_required",
            cli_inspection_ref="scripts/dev/uaa_coding.py inspect-patch-apply-readiness",
            api_operation_ref="GET /control-center/coding/patch-apply-readiness",
            control_center_surface_ref="control-center-surface:code-workbench",
            source_refs=[
                "capability-ref:coding:approved-patch-apply",
                "lane-ref:coding:approved-patch-apply",
            ],
            blocked_reason_refs=[
                "blocked-state:coding-no-file-write",
                "blocked-authority:action-tool-code:no-generic-tool-execution",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="web.evidence.fetch_readonly",
            label="Web evidence read-only preview",
            status="approval_required",
            authority_domain=AuthorityDomain.browser,
            authority_capability=AuthorityCapability.read,
            required_mode=TrustMode.ask_before_changes,
            side_effect_class="governed_network_read_only",
            risk="medium",
            allowed_inputs_schema={
                "url_ref": "allowlisted_https_get_ref",
                "request_ref": "idempotent_web_evidence_request_ref",
                "content": "untrusted_bounded_preview",
                "browser_action": False,
            },
            denied_capabilities=[
                "unrestricted browsing",
                "browser actions",
                "auth session state",
                "downloads or uploads",
                "POST PUT PATCH DELETE",
                "context injection",
                "memory writes",
            ],
            approval_scope="approval-scope:web-evidence-browser-read-exact",
            idempotency_required=True,
            rollback_posture="Safe-disable blocks the web evidence product slice; local attachment receipts can be suppressed without trusting fetched content.",
            receipt_kind="web_evidence_preview_receipt",
            cli_inspection_ref="scripts/dev/uaa_founder_loop.py inspect-web-evidence",
            api_operation_ref="POST /control-center/web-evidence/attach",
            control_center_surface_ref="control-center-surface:evidence",
            source_refs=[
                "lane-ref:web-evidence-product-slice",
                "contract-ref:web-evidence-product-slice:v1",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="memory.review.decision",
            label="Memory Review decision receipt",
            status="approval_required",
            authority_domain=AuthorityDomain.memory,
            authority_capability=AuthorityCapability.write,
            required_mode=TrustMode.approved_safe_local_work_session,
            side_effect_class="local_dev_workspace_only",
            risk="medium",
            allowed_inputs_schema={
                "decision": "accept_correct_reject_defer_merge_supersede_forget_request",
                "candidate_ref": "memory_review_candidate_ref",
                "corrected_summary_ref": "safe_ref_required_for_correct",
                "raw_memory_content": False,
            },
            denied_capabilities=[
                "memory as truth",
                "automatic memory write",
                "hidden context injection",
                "raw memory content persistence",
                "silent delete",
            ],
            approval_scope="approval-scope:memory-review-decision-exact",
            idempotency_required=True,
            rollback_posture="Decision receipts preserve review lifecycle refs; write/delete rollback stays blocked outside exact accept/correct reviewed recall scope.",
            receipt_kind="memory_review_decision_receipt",
            cli_inspection_ref="scripts/dev/uaa_founder_loop.py memory-review-decision",
            api_operation_ref="POST /control-center/memory/review/{candidate_ref}/{decision}",
            control_center_surface_ref="control-center-surface:memory-review",
            source_refs=[
                "contract-ref:memory-review-decision:v1",
                "safe-disable-posture-ref:memory-review:accept-correct-write-disabled",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="model.provider.readiness",
            label="Model provider readiness",
            status="implemented",
            authority_domain=AuthorityDomain.provider_model_calls,
            authority_capability=AuthorityCapability.read,
            required_mode=TrustMode.read_only,
            side_effect_class="validation_only",
            risk="low",
            allowed_inputs_schema={
                "provider_refs": "configured_provider_status_refs_only",
                "runtime_measurements": "stored_or_static_measurement_refs_only",
                "model_call": False,
            },
            denied_capabilities=[
                "provider SDK calls",
                "runtime model calls",
                "provider transport payload persistence",
                "model output as authority",
                "billing authority",
            ],
            approval_scope="approval-scope:not-required-for-readiness",
            idempotency_required=False,
            rollback_posture="Read-only status has no mutation rollback; provider execution remains separately gated.",
            receipt_kind="readiness_status_evidence_ref",
            cli_inspection_ref="scripts/inspect_model_provider_control_plane.py",
            api_operation_ref="GET /control-center/providers/runtime-control-plane",
            control_center_surface_ref="control-center-surface:models-runtime",
            source_refs=[
                "lane-ref:model-slot-posture",
                "contract-ref:model-provider-control-plane:v1",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="extension.catalog.review",
            label="Extension catalog review",
            status="implemented",
            authority_domain=AuthorityDomain.workspace,
            authority_capability=AuthorityCapability.read,
            required_mode=TrustMode.read_only,
            side_effect_class="validation_only",
            risk="low",
            allowed_inputs_schema={
                "package_refs": "inspectable_extension_metadata_refs_only",
                "hash_refs": "reviewed_or_missing_hash_refs",
                "callable_import": False,
            },
            denied_capabilities=[
                "runtime import",
                "plugin execution",
                "connector writes",
                "automatic skill enablement",
                "unrestricted network access",
            ],
            approval_scope="approval-scope:not-required-for-readonly-review",
            idempotency_required=False,
            rollback_posture="Review-only metadata performs no activation; revoked or disabled extension posture remains deny-by-default.",
            receipt_kind="extension_catalog_review_evidence_ref",
            cli_inspection_ref="scripts/dev/uaa_extensions.py inspect-catalog",
            api_operation_ref="GET /extensions/catalog",
            control_center_surface_ref="control-center-surface:extensions",
            source_refs=[
                "inspectable-catalog:uaa-extension-catalog-v1",
                "doc:inspectable-extension-catalog",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        _authority_lane_entry(
            lane_id="extension.install_disabled",
            label="Extension install-disabled record",
            status="approval_required",
            authority_domain=AuthorityDomain.workspace,
            authority_capability=AuthorityCapability.write,
            required_mode=TrustMode.approved_safe_local_work_session,
            side_effect_class="local_disabled_record_proposal",
            risk="medium",
            allowed_inputs_schema={
                "package_refs": "repo_owned_or_reviewed_extension_refs_only",
                "approval_ref": "exact_local_approval_required",
                "authority_lease": "workspace_write_required",
                "callable_import": False,
                "execution": False,
            },
            denied_capabilities=[
                "plugin package install",
                "plugin enablement",
                "runtime import",
                "plugin execution",
                "marketplace fetch",
                "connector writes",
                "shell execution",
                "provider model calls",
                "browser automation",
                "production authority",
            ],
            approval_scope="approval-scope:extension-install-disabled-exact-package-version",
            idempotency_required=True,
            rollback_posture=(
                "Only disabled install-record refs may be proposed; any future "
                "record must be removable by its rollback ref and safe-disable ref."
            ),
            receipt_kind="extension_install_disabled_receipt_plan_ref",
            cli_inspection_ref=(
                "scripts/dev/uaa_extensions.py inspect-install-disabled-posture"
            ),
            api_operation_ref="GET /extensions/catalog#install_disabled_posture",
            control_center_surface_ref="control-center-surface:extensions",
            source_refs=[
                "extension-install-disabled-posture:uaa:v1",
                "doc:plugin-install-review",
                "doc:authority-graduation-board",
            ],
            blocked_reason_refs=[
                "reason-ref:extension-install-disabled:local-approval-required",
                "reason-ref:extension-install-disabled:authority-lease-required",
            ],
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
        *build_matrix_harness_lane_catalog_entries(
            active_leases=leases,
            kill_switch_engaged=kill_switch_engaged,
        ),
    ]
    lane_ids = [entry.lane_id for entry in entries]
    missing = [lane_id for lane_id in REQUIRED_AUTHORITY_LANE_IDS if lane_id not in lane_ids]
    blocked_refs = sorted({ref for entry in entries for ref in entry.blocked_reason_refs})
    unsupported_refs = sorted(
        {ref for entry in entries for ref in entry.unsupported_adapter_refs}
    )
    status_counts = Counter(entry.status for entry in entries)
    return AuthorityLaneCatalogReadModel(
        operator_summary=(
            "Authority Lane Catalog V1 normalizes exact governed lanes for local "
            "verification, code proposals, web evidence, memory review, provider "
            "readiness, and extension review. Unknown authority still denies; "
            "blocked lanes are visible contracts, not executable authority."
        ),
        entry_count=len(entries),
        status_counts=dict(sorted(status_counts.items())),
        required_lane_ids=list(REQUIRED_AUTHORITY_LANE_IDS),
        missing_required_lane_ids=missing,
        entries=entries,
        blocked_reason_refs=blocked_refs,
        unsupported_adapter_refs=unsupported_refs,
    )


def _authority_lane_entry(
    *,
    lane_id: str,
    label: str,
    status: AuthorityLaneStatus,
    authority_domain: AuthorityDomain,
    authority_capability: AuthorityCapability,
    required_mode: TrustMode,
    side_effect_class: str,
    risk: Literal["low", "medium", "high", "blocked"],
    allowed_inputs_schema: dict[str, Any],
    denied_capabilities: list[str],
    approval_scope: str,
    idempotency_required: bool,
    rollback_posture: str,
    receipt_kind: str,
    cli_inspection_ref: str,
    api_operation_ref: str,
    control_center_surface_ref: str,
    source_refs: list[str],
    active_leases: list[AuthorityLease],
    kill_switch_engaged: bool,
    blocked_reason_refs: list[str] | None = None,
    unsupported_adapter_refs: list[str] | None = None,
) -> AuthorityLaneCatalogEntry:
    lane_ref = f"authority-lane-ref:{lane_id.replace('.', '-')}"
    source_blocked_refs = blocked_reason_refs or []
    source_unsupported_refs = unsupported_adapter_refs or []
    decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=f"authority-action-ref:lane-catalog:{lane_id.replace('.', '-')}",
            domain=authority_domain,
            capability=authority_capability,
            safe_summary=f"Evaluate Authority Lane Catalog posture for {label}.",
            route_ref=api_operation_ref,
            capability_ref=f"authority-capability-ref:{lane_id.replace('.', '-')}",
            lane_ref=lane_ref,
            requested_mode=required_mode,
            draft_fallback_available=status in {"implemented", "partial", "proposal_only"},
            unsupported_adapter=bool(source_unsupported_refs),
            kill_switch_engaged=kill_switch_engaged,
            rollback_ref=f"rollback-ref:authority-lane-catalog:{lane_id.replace('.', '-')}",
            safe_disable_ref=f"safe-disable-ref:authority-lane-catalog:{lane_id.replace('.', '-')}",
        ),
        active_leases,
    )
    return AuthorityLaneCatalogEntry(
        lane_id=lane_id,
        lane_ref=lane_ref,
        label=label,
        status=status,
        authority_domain=authority_domain,
        authority_capability=authority_capability,
        required_mode=required_mode,
        side_effect_class=side_effect_class,
        risk=risk,
        allowed_inputs_schema=allowed_inputs_schema,
        denied_capabilities=denied_capabilities,
        approval_scope=approval_scope,
        idempotency_required=idempotency_required,
        rollback_posture=rollback_posture,
        receipt_kind=receipt_kind,
        cli_inspection_ref=cli_inspection_ref,
        api_operation_ref=api_operation_ref,
        control_center_surface_ref=control_center_surface_ref,
        source_refs=source_refs,
        blocked_reason_refs=list(dict.fromkeys(source_blocked_refs)),
        unsupported_adapter_refs=list(dict.fromkeys(source_unsupported_refs)),
        active_decision_outcome=decision.outcome,
        active_decision_ref=decision.decision_ref,
        active_decision_reason_refs=list(decision.reason_refs),
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


def build_authority_domain_readiness(
    decision_catalog: list[AuthorityDecisionCatalogEntry],
    *,
    active_leases: list[AuthorityLease],
    mode_catalog: list[AuthorityModeCatalogEntry],
) -> list[AuthorityDomainReadinessEntry]:
    rows: list[AuthorityDomainReadinessEntry] = []
    active_lease_refs_by_domain: dict[str, list[str]] = {}
    for lease in active_leases:
        if not lease.is_active():
            continue
        for domain in lease.domains:
            active_lease_refs_by_domain.setdefault(_enum_value(domain), []).append(
                lease.lease_ref
            )

    for domain in AuthorityDomain:
        domain_value = domain.value
        domain_entries = [
            entry
            for entry in decision_catalog
            if _enum_value(entry.decision.domain) == domain_value
        ]
        outcome_counter = Counter(
            _enum_value(entry.decision.outcome) for entry in domain_entries
        )
        status_counter = Counter(entry.status for entry in domain_entries)
        mapped_refs = [entry.authority_capability_ref for entry in domain_entries]
        unsupported_refs = sorted(
            {
                ref
                for entry in domain_entries
                for ref in entry.unsupported_adapter_refs
            }
        )
        blocked_refs = sorted(
            {
                ref
                for entry in domain_entries
                if _enum_value(entry.decision.outcome)
                != AuthorityDecisionOutcome.allow.value
                for ref in entry.decision.reason_refs
            }
        )
        if not domain_entries:
            blocked_refs = ["reason-ref:authority:target-domain-unmapped"]

        default_requested_modes = [
            TrustMode(entry.mode)
            for entry in mode_catalog
            if _domain_in_capability_map(domain, entry.default_requested_domains)
        ]
        issue_ready_modes = [
            TrustMode(entry.mode)
            for entry in mode_catalog
            if entry.issue_ready
            and _domain_in_capability_map(domain, entry.grantable_domains)
        ]
        grantable_capability_values = {
            _enum_value(capability)
            for entry in mode_catalog
            for capability in _domain_capabilities(domain, entry.grantable_domains)
        }
        grantable_capabilities = [
            capability
            for capability in AuthorityCapability
            if capability.value in grantable_capability_values
        ]
        status = _authority_domain_readiness_status(
            domain_entries=domain_entries,
            outcome_counter=outcome_counter,
            unsupported_adapter_refs=unsupported_refs,
        )
        rows.append(
            AuthorityDomainReadinessEntry(
                domain=domain,
                status=status,
                mapped_capability_count=len(mapped_refs),
                mapped_capability_refs=mapped_refs,
                active_lease_refs=list(
                    dict.fromkeys(active_lease_refs_by_domain.get(domain_value, []))
                ),
                default_requested_modes=list(dict.fromkeys(default_requested_modes)),
                issue_ready_modes=list(dict.fromkeys(issue_ready_modes)),
                grantable_capabilities=grantable_capabilities,
                decision_outcome_counts={
                    outcome.value: outcome_counter.get(outcome.value, 0)
                    for outcome in AuthorityDecisionOutcome
                },
                mapped_status_counts=dict(sorted(status_counter.items())),
                unsupported_adapter_refs=unsupported_refs,
                blocked_reason_refs=blocked_refs,
                operator_summary=_authority_domain_readiness_summary(
                    domain=domain,
                    status=status,
                    mapped_count=len(mapped_refs),
                    active_lease_count=len(
                        active_lease_refs_by_domain.get(domain_value, [])
                    ),
                    unsupported_count=len(unsupported_refs),
                    issue_ready_mode_count=len(issue_ready_modes),
                ),
            )
        )
    return rows


def build_authority_domain_readiness_read_model(
    decision_catalog: list[AuthorityDecisionCatalogEntry],
    *,
    active_leases: list[AuthorityLease],
    mode_catalog: list[AuthorityModeCatalogEntry],
) -> AuthorityDomainReadinessReadModel:
    entries = build_authority_domain_readiness(
        decision_catalog,
        active_leases=active_leases,
        mode_catalog=mode_catalog,
    )
    status_counts = Counter(entry.status for entry in entries)
    outcome_counts: Counter[str] = Counter()
    blocked_reason_refs: list[str] = []
    unsupported_adapter_refs: list[str] = []
    for entry in entries:
        outcome_counts.update(entry.decision_outcome_counts)
        blocked_reason_refs.extend(entry.blocked_reason_refs)
        unsupported_adapter_refs.extend(entry.unsupported_adapter_refs)
    allowed = outcome_counts.get(AuthorityDecisionOutcome.allow.value, 0)
    asked = outcome_counts.get(AuthorityDecisionOutcome.ask.value, 0)
    degraded = outcome_counts.get(
        AuthorityDecisionOutcome.degrade_to_draft.value,
        0,
    )
    denied = outcome_counts.get(AuthorityDecisionOutcome.deny.value, 0)
    return AuthorityDomainReadinessReadModel(
        operator_summary=(
            f"Authority domain readiness covers {len(entries)} target domains "
            f"from active AuthorityLease state: {allowed} allowed capability "
            f"decision(s), {asked} ask decision(s), {degraded} draft-only "
            f"decision(s), and {denied} denied decision(s). Unsupported "
            "adapters remain visible and non-executable."
        ),
        domain_count=len(entries),
        status_counts=dict(sorted(status_counts.items())),
        decision_outcome_counts={
            outcome.value: outcome_counts.get(outcome.value, 0)
            for outcome in AuthorityDecisionOutcome
        },
        entries=entries,
        blocked_reason_refs=sorted(set(blocked_reason_refs)),
        unsupported_adapter_refs=sorted(set(unsupported_adapter_refs)),
    )


def _domain_in_capability_map(
    domain: AuthorityDomain,
    capability_map: dict[AuthorityDomain, list[AuthorityCapability]],
) -> bool:
    return domain.value in {_enum_value(key) for key in capability_map}


def _domain_capabilities(
    domain: AuthorityDomain,
    capability_map: dict[AuthorityDomain, list[AuthorityCapability]],
) -> list[AuthorityCapability]:
    for key, capabilities in capability_map.items():
        if _enum_value(key) == domain.value:
            return capabilities
    return []


def _authority_domain_readiness_status(
    *,
    domain_entries: list[AuthorityDecisionCatalogEntry],
    outcome_counter: Counter[str],
    unsupported_adapter_refs: list[str],
) -> AuthorityDomainReadinessStatus:
    if not domain_entries:
        return "unmapped_target_domain"
    if outcome_counter.get(AuthorityDecisionOutcome.allow.value, 0) > 0:
        return "active_allow"
    if outcome_counter.get(AuthorityDecisionOutcome.ask.value, 0) > 0:
        return "requires_confirmation"
    if outcome_counter.get(AuthorityDecisionOutcome.degrade_to_draft.value, 0) > 0:
        return "draft_only"
    if unsupported_adapter_refs:
        return "blocked_unsupported"
    return "known_denied"


def _authority_domain_readiness_summary(
    *,
    domain: AuthorityDomain,
    status: AuthorityDomainReadinessStatus,
    mapped_count: int,
    active_lease_count: int,
    unsupported_count: int,
    issue_ready_mode_count: int,
) -> str:
    return (
        f"{domain.value} authority is {status} with {mapped_count} mapped "
        f"capability ref(s), {active_lease_count} active lease ref(s), "
        f"{issue_ready_mode_count} issue-ready mode(s), and "
        f"{unsupported_count} unsupported adapter ref(s)."
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
