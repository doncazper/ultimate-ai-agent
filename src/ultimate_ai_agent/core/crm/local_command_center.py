from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.crm.contracts import (
    CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    CRM_COMMUNICATIONS_SPINE_CONTRACT_REF,
    CrmImplementationState,
    _deny_true_flags,
    _validate_no_private_or_secret_text,
    _validate_optional_ref_list,
    _validate_ref,
    _validate_ref_list,
    _validate_safe_text,
)
from ultimate_ai_agent.core.crm.social_projection import (
    CRM_SOCIAL_RELATIONSHIP_CLI_REF,
    CRM_SOCIAL_RELATIONSHIP_TAG,
    CrmSocialRelationshipProjection,
    build_crm_social_relationship_projection,
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
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager
from ultimate_ai_agent.core.time import utc_now


CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF = "contract-ref:crm-local-command-center:m2:v1"
CRM_LOCAL_COMMAND_CENTER_DOC_REF = "docs-ref:uaa-crm-local-command-center-plan"
CRM_LOCAL_COMMAND_CENTER_VERIFIER_REF = "script-ref:verify-crm-local-command-center"
CRM_LOCAL_COMMAND_CENTER_STORAGE_REF = (
    "storage-ref:crm-local-command-center:jsonl-local:v1"
)
CRM_LOCAL_COMMAND_CENTER_SOURCE = "python_core_crm_local_command_center_read_model"
CRM_LOCAL_COMMAND_CENTER_SCHEMA_VERSION = "crm-local-command-center.v1"

CRM_LOCAL_COMMAND_CENTER_ROUTE_REFS = [
    "GET /control-center/crm/summary",
    "GET /control-center/crm/relationships",
    "GET /control-center/crm/timeline",
    "GET /control-center/crm/follow-ups",
    "GET /control-center/crm/pipelines",
    "GET /control-center/crm/smart-lists",
    "POST /control-center/crm/local-mutations",
]
CRM_LOCAL_COMMAND_CENTER_READ_ROUTE_REFS = [
    ref for ref in CRM_LOCAL_COMMAND_CENTER_ROUTE_REFS if ref.startswith("GET ")
]
CRM_LOCAL_COMMAND_CENTER_CLI_REFS = [
    "repo-local-command:uaa-crm:inspect-summary",
    "repo-local-command:uaa-crm:inspect-relationships",
    "repo-local-command:uaa-crm:inspect-follow-ups",
    "repo-local-command:uaa-crm:inspect-pipelines",
    "repo-local-command:uaa-crm:inspect-connector-read-lanes",
    "repo-local-command:uaa-crm:inspect-storage",
    CRM_SOCIAL_RELATIONSHIP_CLI_REF,
    "repo-local-command:uaa-crm:mutate-local",
]

CRM_LOCAL_MUTATION_CONTRACT_REF = "contract-ref:crm-local-mutation-lane:v1"
CRM_LOCAL_MUTATION_ROUTE_REF = "POST /control-center/crm/local-mutations"
CRM_LOCAL_MUTATION_AUTHORITY_ACTION_REF = "authority-action-ref:crm-local-mutation"
CRM_LOCAL_MUTATION_AUTHORITY_LANE_REF = "lane-ref:crm-local-mutation"
CRM_LOCAL_MUTATION_AUTHORITY_DOMAIN_REF = "authority-domain-ref:contacts"
CRM_LOCAL_MUTATION_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
CRM_LOCAL_MUTATION_AUTHORITY_REQUIRED_MODE_REF = "authority-mode-ref:ask-before-changes"
CRM_LOCAL_MUTATION_AUTHORITY_REQUIRED_BLOCKED_REF = (
    "blocked-state:crm-local-mutation-authority-lease-required"
)
CRM_LOCAL_MUTATION_SAFE_DISABLE_REF = "safe-disable-ref:crm-local-mutation"
CRM_LOCAL_STATE_LOCK_KEY = "crm-local-command-center-state"
CRM_LOCAL_IMPORT_EXPORT_CONTRACT_REF = "contract-ref:crm-local-import-export:v1"
CRM_LOCAL_AI_PROPOSAL_CONTRACT_REF = "contract-ref:crm-ai-proposal-layer:v1"
CRM_LOCAL_CONNECTOR_READ_POSTURE_REF = "posture-ref:crm-connector-read-lanes:v1"
CRM_LOCAL_SENDS_WRITES_PLAN_REF = "plan-ref:crm-sends-writes-authority:v1"

CRM_LOCAL_BLOCKED_AUTHORITY_REFS = [
    *CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS,
    "blocked-state-ref:crm-local:no-connector-runtime",
    "blocked-state-ref:crm-local:no-connector-writes",
    "blocked-state-ref:crm-local:no-account-sync",
    "blocked-state-ref:crm-local:no-sends",
    "blocked-state-ref:crm-local:no-calendar-writes",
    "blocked-state-ref:crm-local:no-provider-model-calls",
    "blocked-state-ref:crm-local:no-live-web",
    "blocked-state-ref:crm-local:no-browser-automation",
    "blocked-state-ref:crm-local:no-background-autonomy",
    "blocked-state-ref:crm-local:no-external-crm-write",
    "blocked-state-ref:crm-local:no-production-authority",
]
CRM_LOCAL_REDACTIONS = [
    "safe_refs_only",
    "bounded_summaries_only",
    "raw_contact_details_omitted",
    "raw_message_bodies_omitted",
    "raw_paths_omitted",
    "provider_payloads_omitted",
]

FOLLOW_UP_STATUSES = (
    "due",
    "upcoming",
    "stale",
    "blocked",
    "proposed",
    "completed",
)
TIMELINE_EVENT_KINDS = (
    "note_ref",
    "follow_up_ref",
    "memory_ref",
    "evidence_ref",
    "opportunity_ref",
    "proposal_ref",
    "decision_ref",
)
OPPORTUNITY_KINDS = (
    "opportunity",
    "deal",
    "partnership",
    "investor",
    "customer",
    "candidate",
    "project",
    "renewal",
    "vendor",
)
MUTATION_KINDS = (
    "create_follow_up",
    "update_follow_up",
    "mark_follow_up_complete",
    "move_opportunity_stage",
    "add_note_summary_ref",
)

SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_.:-]+")


class CrmLocalCommandCenterError(RuntimeError):
    """Safe-ref-only CRM local command center error."""


class CrmLocalAuthorityError(CrmLocalCommandCenterError):
    """Raised when a CRM local mutation lacks active AuthorityLease scope."""

    def __init__(
        self,
        reason_refs: list[str],
        *,
        code: str = "CRM_LOCAL_MUTATION_AUTHORITY_DENIED",
        required_refs: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.reason_refs = reason_refs
        self.required_refs = required_refs or {}


class CrmLocalCommandCenterDuplicateError(CrmLocalCommandCenterError):
    """Raised when an idempotency key is replayed with a changed payload."""


class _CrmLocalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CrmAuthorityPostureReadModel(_CrmLocalModel):
    posture_ref: str = "posture-ref:crm-local-command-center:authority:v1"
    backend_owned: bool = True
    control_center_grants_authority: bool = False
    read_only_routes_enabled: bool = True
    exact_local_mutation_lane_enabled: bool = True
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    provider_model_call_enabled: bool = False
    live_web_enabled: bool = False
    browser_runtime_enabled: bool = False
    background_autonomy_enabled: bool = False
    external_crm_write_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_BLOCKED_AUTHORITY_REFS)
    )

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmAuthorityPostureReadModel":
        _validate_ref(self.posture_ref, "posture_ref")
        if not self.backend_owned:
            raise ValueError("CRM_LOCAL_BACKEND_OWNED_REQUIRED")
        if self.control_center_grants_authority:
            raise ValueError("CRM_LOCAL_CONTROL_CENTER_AUTHORITY_DENIED")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _deny_true_flags(
            self,
            [
                ("connector_runtime_enabled", "CRM_LOCAL_CONNECTOR_RUNTIME_DENIED"),
                ("connector_write_enabled", "CRM_LOCAL_CONNECTOR_WRITE_DENIED"),
                ("account_sync_enabled", "CRM_LOCAL_ACCOUNT_SYNC_DENIED"),
                ("send_enabled", "CRM_LOCAL_SEND_DENIED"),
                ("calendar_write_enabled", "CRM_LOCAL_CALENDAR_WRITE_DENIED"),
                ("provider_model_call_enabled", "CRM_LOCAL_PROVIDER_MODEL_DENIED"),
                ("live_web_enabled", "CRM_LOCAL_LIVE_WEB_DENIED"),
                ("browser_runtime_enabled", "CRM_LOCAL_BROWSER_DENIED"),
                ("background_autonomy_enabled", "CRM_LOCAL_BACKGROUND_DENIED"),
                ("external_crm_write_enabled", "CRM_LOCAL_EXTERNAL_WRITE_DENIED"),
                ("production_authority_enabled", "CRM_LOCAL_PRODUCTION_DENIED"),
            ],
        )
        return self


class CrmStorageStatusReadModel(_CrmLocalModel):
    storage_ref: str = CRM_LOCAL_COMMAND_CENTER_STORAGE_REF
    state: Literal["code_seed", "seeded_demo", "local_state", "cleared_demo"]
    initialized: bool
    seeded_demo: bool
    record_counts: dict[str, int]
    event_log_ref: str
    snapshot_ref: str
    raw_paths_omitted: bool = True
    raw_contact_details_omitted: bool = True
    connector_sync_enabled: bool = False
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmStorageStatusReadModel":
        for field_name in ["storage_ref", "event_log_ref", "snapshot_ref"]:
            _validate_ref(getattr(self, field_name), field_name)
        if not self.raw_paths_omitted or not self.raw_contact_details_omitted:
            raise ValueError("CRM_LOCAL_STORAGE_REDACTION_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("connector_sync_enabled", "CRM_LOCAL_STORAGE_CONNECTOR_SYNC_DENIED"),
                ("account_sync_enabled", "CRM_LOCAL_STORAGE_ACCOUNT_SYNC_DENIED"),
            ],
        )
        return self


class CrmPersonReadModel(_CrmLocalModel):
    person_ref: str
    safe_display_label: str
    relationship_refs: list[str]
    organization_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_provenance_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_contact_details_included: bool = False
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPersonReadModel":
        _validate_ref(self.person_ref, "person_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label")
        _validate_ref_list(self.relationship_refs, "relationship_refs")
        _validate_optional_ref_list(self.organization_refs, "organization_refs")
        _validate_optional_ref_list(self.evidence_refs, "evidence_refs")
        _validate_optional_ref_list(
            self.memory_provenance_refs,
            "memory_provenance_refs",
        )
        for tag in self.tags:
            _validate_safe_text(tag, "tags", max_chars=80)
        _deny_true_flags(
            self,
            [
                ("raw_contact_details_included", "CRM_PERSON_RAW_CONTACT_DENIED"),
                ("account_sync_enabled", "CRM_PERSON_ACCOUNT_SYNC_DENIED"),
            ],
        )
        return self


class CrmOrganizationReadModel(_CrmLocalModel):
    organization_ref: str
    safe_display_label: str
    relationship_refs: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    raw_contact_details_included: bool = False
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmOrganizationReadModel":
        _validate_ref(self.organization_ref, "organization_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label")
        _validate_ref_list(self.relationship_refs, "relationship_refs")
        _validate_optional_ref_list(self.evidence_refs, "evidence_refs")
        _deny_true_flags(
            self,
            [
                ("raw_contact_details_included", "CRM_ORG_RAW_CONTACT_DENIED"),
                ("account_sync_enabled", "CRM_ORG_ACCOUNT_SYNC_DENIED"),
            ],
        )
        return self


class CrmRelationshipReadModel(_CrmLocalModel):
    relationship_ref: str
    person_ref: str
    organization_ref: str | None = None
    safe_display_label: str
    relationship_kind_ref: str
    health_state: Literal["warm", "steady", "stale", "blocked", "needs_evidence"]
    safe_summary: str
    why_shown: str
    timeline_event_refs: list[str]
    follow_up_refs: list[str]
    opportunity_refs: list[str]
    evidence_refs: list[str]
    memory_provenance_refs: list[str]
    stale_state: Literal["fresh", "stale", "conflict", "missing_evidence"] = "fresh"
    raw_contact_details_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmRelationshipReadModel":
        for field_name in [
            "relationship_ref",
            "person_ref",
            "relationship_kind_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        if self.organization_ref is not None:
            _validate_ref(self.organization_ref, "organization_ref")
        for field_name in [
            "timeline_event_refs",
            "follow_up_refs",
            "opportunity_refs",
            "evidence_refs",
            "memory_provenance_refs",
        ]:
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_safe_text(self.safe_display_label, "safe_display_label")
        _validate_safe_text(self.safe_summary, "safe_summary")
        _validate_safe_text(self.why_shown, "why_shown")
        if self.raw_contact_details_included:
            raise ValueError("CRM_RELATIONSHIP_RAW_CONTACT_DENIED")
        return self


class CrmTimelineEventReadModel(_CrmLocalModel):
    event_ref: str
    relationship_ref: str
    event_kind: Literal[
        "note_ref",
        "follow_up_ref",
        "memory_ref",
        "evidence_ref",
        "opportunity_ref",
        "proposal_ref",
        "decision_ref",
    ]
    occurred_at_ref: str
    safe_summary: str
    why_shown: str
    source_refs: list[str]
    evidence_refs: list[str]
    memory_provenance_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    stale_conflict_posture: Literal["fresh", "stale", "conflict", "missing_evidence"]
    raw_content_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmTimelineEventReadModel":
        for field_name in ["event_ref", "relationship_ref", "occurred_at_ref"]:
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in [
            "source_refs",
            "evidence_refs",
            "memory_provenance_refs",
            "proof_refs",
        ]:
            _validate_optional_ref_list(getattr(self, field_name), field_name)
        _validate_safe_text(self.safe_summary, "safe_summary")
        _validate_safe_text(self.why_shown, "why_shown")
        if self.raw_content_included:
            raise ValueError("CRM_TIMELINE_RAW_CONTENT_DENIED")
        return self


class CrmFollowUpReadModel(_CrmLocalModel):
    follow_up_ref: str
    relationship_ref: str
    status: Literal["due", "upcoming", "stale", "blocked", "proposed", "completed"]
    priority: Literal["high", "medium", "low"]
    due_ref: str
    safe_summary: str
    reason_refs: list[str]
    evidence_refs: list[str]
    memory_provenance_refs: list[str]
    opportunity_refs: list[str] = Field(default_factory=list)
    action_inbox_handoff_proposal_ref: str
    action_inbox_handoff_proposal_only: bool = True
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    connector_write_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmFollowUpReadModel":
        for field_name in [
            "follow_up_ref",
            "relationship_ref",
            "due_ref",
            "action_inbox_handoff_proposal_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in [
            "reason_refs",
            "evidence_refs",
            "memory_provenance_refs",
            "opportunity_refs",
        ]:
            _validate_optional_ref_list(getattr(self, field_name), field_name)
        _validate_safe_text(self.safe_summary, "safe_summary")
        if not self.action_inbox_handoff_proposal_only:
            raise ValueError("CRM_FOLLOWUP_ACTION_INBOX_PROPOSAL_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("send_enabled", "CRM_FOLLOWUP_SEND_DENIED"),
                ("calendar_write_enabled", "CRM_FOLLOWUP_CALENDAR_WRITE_DENIED"),
                ("connector_write_enabled", "CRM_FOLLOWUP_CONNECTOR_WRITE_DENIED"),
            ],
        )
        return self


class CrmOpportunityReadModel(_CrmLocalModel):
    opportunity_ref: str
    relationship_ref: str
    pipeline_ref: str
    opportunity_kind: Literal[
        "opportunity",
        "deal",
        "partnership",
        "investor",
        "customer",
        "candidate",
        "project",
        "renewal",
        "vendor",
    ]
    stage_ref: str
    stage_label: str
    safe_summary: str
    evidence_refs: list[str]
    proof_refs: list[str]
    local_preview_drag_drop_enabled: bool = True
    persisted_stage_mutation_route_ref: str = CRM_LOCAL_MUTATION_ROUTE_REF
    external_crm_write_enabled: bool = False
    fake_revenue_claim_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmOpportunityReadModel":
        for field_name in [
            "opportunity_ref",
            "relationship_ref",
            "pipeline_ref",
            "stage_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_safe_text(self.stage_label, "stage_label")
        _validate_safe_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.proof_refs, "proof_refs")
        _deny_true_flags(
            self,
            [
                ("external_crm_write_enabled", "CRM_OPPORTUNITY_EXTERNAL_WRITE_DENIED"),
                ("fake_revenue_claim_enabled", "CRM_OPPORTUNITY_FAKE_REVENUE_DENIED"),
            ],
        )
        return self


class CrmPipelineStageReadModel(_CrmLocalModel):
    stage_ref: str
    safe_label: str
    opportunity_refs: list[str]

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPipelineStageReadModel":
        _validate_ref(self.stage_ref, "stage_ref")
        _validate_safe_text(self.safe_label, "safe_label")
        _validate_optional_ref_list(self.opportunity_refs, "opportunity_refs")
        return self


class CrmPipelineReadModel(_CrmLocalModel):
    pipeline_ref: str
    safe_label: str
    stages: list[CrmPipelineStageReadModel]
    opportunity_refs: list[str]
    evidence_refs: list[str]
    local_preview_drag_drop_enabled: bool = True
    persisted_reorder_requires_exact_mutation: bool = True
    external_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPipelineReadModel":
        _validate_ref(self.pipeline_ref, "pipeline_ref")
        _validate_safe_text(self.safe_label, "safe_label")
        _validate_ref_list(self.opportunity_refs, "opportunity_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if not self.persisted_reorder_requires_exact_mutation:
            raise ValueError("CRM_PIPELINE_EXACT_MUTATION_REQUIRED")
        if self.external_sync_enabled:
            raise ValueError("CRM_PIPELINE_EXTERNAL_SYNC_DENIED")
        return self


class CrmSmartListReadModel(_CrmLocalModel):
    smart_list_ref: str
    safe_label: str
    membership_rule_ref: str
    explanation: str
    relationship_refs: list[str]
    follow_up_refs: list[str] = Field(default_factory=list)
    opportunity_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str]
    hidden_context_injection_enabled: bool = False
    external_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmSmartListReadModel":
        for field_name in ["smart_list_ref", "membership_rule_ref"]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_safe_text(self.safe_label, "safe_label")
        _validate_safe_text(self.explanation, "explanation")
        for field_name in [
            "relationship_refs",
            "follow_up_refs",
            "opportunity_refs",
            "evidence_refs",
        ]:
            _validate_optional_ref_list(getattr(self, field_name), field_name)
        _deny_true_flags(
            self,
            [
                ("hidden_context_injection_enabled", "CRM_SMART_LIST_CONTEXT_DENIED"),
                ("external_sync_enabled", "CRM_SMART_LIST_EXTERNAL_SYNC_DENIED"),
            ],
        )
        return self


class CrmCommunicationDraftReadModel(_CrmLocalModel):
    draft_ref: str
    relationship_ref: str
    draft_kind: Literal[
        "email_draft",
        "text_draft",
        "call_script",
        "meeting_agenda",
        "follow_up_note",
        "calendar_invite_draft",
    ]
    bounded_redacted_summary: str
    proof_refs: list[str]
    local_review_artifact_only: bool = True
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    connector_write_enabled: bool = False
    raw_body_persisted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmCommunicationDraftReadModel":
        _validate_ref(self.draft_ref, "draft_ref")
        _validate_ref(self.relationship_ref, "relationship_ref")
        _validate_safe_text(
            self.bounded_redacted_summary,
            "bounded_redacted_summary",
        )
        _validate_ref_list(self.proof_refs, "proof_refs")
        if not self.local_review_artifact_only:
            raise ValueError("CRM_DRAFT_LOCAL_REVIEW_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("send_enabled", "CRM_DRAFT_SEND_DENIED"),
                ("calendar_write_enabled", "CRM_DRAFT_CALENDAR_WRITE_DENIED"),
                ("connector_write_enabled", "CRM_DRAFT_CONNECTOR_WRITE_DENIED"),
                ("raw_body_persisted", "CRM_DRAFT_RAW_BODY_DENIED"),
            ],
        )
        return self


class CrmAiProposalReadModel(_CrmLocalModel):
    proposal_ref: str
    proposal_type: Literal[
        "contact_summary",
        "next_best_follow_up",
        "relationship_risk",
        "stale_promise_explanation",
        "draft_message",
        "smart_list_reason",
        "opportunity_update_proposal",
    ]
    relationship_ref: str
    safe_summary: str
    proof_refs: list[str]
    deterministic_fixture: bool = True
    proposal_only: bool = True
    provider_model_call_enabled: bool = False
    model_output_authority_enabled: bool = False
    raw_prompt_or_response_persisted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmAiProposalReadModel":
        _validate_ref(self.proposal_ref, "proposal_ref")
        _validate_ref(self.relationship_ref, "relationship_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.proof_refs, "proof_refs")
        if not self.proposal_only:
            raise ValueError("CRM_AI_PROPOSAL_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("provider_model_call_enabled", "CRM_AI_PROVIDER_MODEL_DENIED"),
                ("model_output_authority_enabled", "CRM_AI_OUTPUT_AUTHORITY_DENIED"),
                ("raw_prompt_or_response_persisted", "CRM_AI_RAW_PAYLOAD_DENIED"),
            ],
        )
        return self


class CrmReportReadModel(_CrmLocalModel):
    report_ref: str
    safe_label: str
    value_label: str
    freshness_ref: str
    drilldown_refs: list[str]
    evidence_refs: list[str]
    fake_revenue_claim_enabled: bool = False
    external_sync_claim_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmReportReadModel":
        for field_name in ["report_ref", "freshness_ref"]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_safe_text(self.safe_label, "safe_label")
        _validate_safe_text(self.value_label, "value_label")
        _validate_ref_list(self.drilldown_refs, "drilldown_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _deny_true_flags(
            self,
            [
                ("fake_revenue_claim_enabled", "CRM_REPORT_FAKE_REVENUE_DENIED"),
                ("external_sync_claim_enabled", "CRM_REPORT_EXTERNAL_SYNC_DENIED"),
            ],
        )
        return self


class CrmConnectorReadLaneReadModel(_CrmLocalModel):
    posture_ref: str = CRM_LOCAL_CONNECTOR_READ_POSTURE_REF
    lanes: list[dict[str, str]]
    readiness_status: Literal["blocked_missing_exact_authority"] = (
        "blocked_missing_exact_authority"
    )
    source_scope_ref: str = (
        "scope-ref:crm-connector-read:single-source-metadata-only:v1"
    )
    test_account_scope_ref: str = (
        "scope-ref:crm-connector-read:named-test-account-required:v1"
    )
    gateway_boundary_ref: str = (
        "gateway-ref:crm-connector-read:approved-read-gateway-required:v1"
    )
    policy_decision_ref: str = "policy-ref:crm-connector-read:deny-until-exact-lane:v1"
    approval_scope_ref: str = (
        "approval-scope-ref:crm-connector-read:per-attempt-required:v1"
    )
    audit_schema_ref: str = "audit-schema-ref:crm-connector-read:v1"
    redaction_policy_ref: str = "redaction-ref:crm-connector-read:safe-refs-only:v1"
    safe_disable_ref: str = "safe-disable-ref:crm-connector-read:disable-lane:v1"
    rollback_readiness_ref: str = (
        "rollback-readiness-ref:crm-connector-read:no-external-mutation:v1"
    )
    proof_ref: str = "proof-ref:crm-connector-read-readiness:v1"
    evidence_ref: str = "evidence-ref:crm-connector-read-readiness:v1"
    cli_inspection_ref: str = "repo-local-command:uaa-crm:inspect-connector-read-lanes"
    api_surface_ref: str = "GET /control-center/crm/summary"
    control_center_surface_ref: str = (
        "route-ref:control-center:crm:connector-readiness-panel"
    )
    blocker_report_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:crm-blocker:connector-read-lanes",
        ]
    )
    missing_prerequisite_refs: list[str] = Field(
        default_factory=lambda: [
            "missing-ref:crm-connector-read:approved-gateway-adapter",
            "missing-ref:crm-connector-read:policy-source-decision",
            "missing-ref:crm-connector-read:local-approval-scope",
            "missing-ref:crm-connector-read:audit-receipt-schema",
            "missing-ref:crm-connector-read:openapi-route-classification",
        ]
    )
    promotion_path_refs: list[str] = Field(
        default_factory=lambda: [
            "promotion-ref:crm-connector-read:define-single-source-scope",
            "promotion-ref:crm-connector-read:bind-test-account-scope",
            "promotion-ref:crm-connector-read:add-policy-and-approval",
            "promotion-ref:crm-connector-read:add-read-only-adapter",
            "promotion-ref:crm-connector-read:add-cli-api-control-center-parity",
        ]
    )
    disabled_by_default: bool = True
    unblock_prompt_ref: str = "prompt-ref:crm:unblock-connector-read-lanes"
    connector_runtime_enabled: bool = False
    connector_writes_enabled: bool = False
    raw_body_ingestion_enabled: bool = False
    live_connector_read_performed: bool = False
    external_account_auth_enabled: bool = False
    background_polling_enabled: bool = False
    provider_model_call_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmConnectorReadLaneReadModel":
        for field_name in [
            "posture_ref",
            "source_scope_ref",
            "test_account_scope_ref",
            "gateway_boundary_ref",
            "policy_decision_ref",
            "approval_scope_ref",
            "audit_schema_ref",
            "redaction_policy_ref",
            "safe_disable_ref",
            "rollback_readiness_ref",
            "proof_ref",
            "evidence_ref",
            "cli_inspection_ref",
            "control_center_surface_ref",
            "unblock_prompt_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in [
            "blocker_report_refs",
            "missing_prerequisite_refs",
            "promotion_path_refs",
        ]:
            _validate_ref_list(getattr(self, field_name), field_name)
        if not self.disabled_by_default:
            raise ValueError("CRM_CONNECTOR_READ_DISABLED_DEFAULT_REQUIRED")
        if self.api_surface_ref not in CRM_LOCAL_COMMAND_CENTER_READ_ROUTE_REFS:
            raise ValueError("CRM_CONNECTOR_READ_API_SURFACE_UNSCOPED")
        _deny_true_flags(
            self,
            [
                ("connector_runtime_enabled", "CRM_CONNECTOR_RUNTIME_DENIED"),
                ("connector_writes_enabled", "CRM_CONNECTOR_WRITES_DENIED"),
                ("raw_body_ingestion_enabled", "CRM_CONNECTOR_RAW_BODY_DENIED"),
                (
                    "live_connector_read_performed",
                    "CRM_CONNECTOR_LIVE_READ_DENIED",
                ),
                (
                    "external_account_auth_enabled",
                    "CRM_CONNECTOR_ACCOUNT_AUTH_DENIED",
                ),
                ("background_polling_enabled", "CRM_CONNECTOR_POLLING_DENIED"),
                ("provider_model_call_enabled", "CRM_CONNECTOR_PROVIDER_DENIED"),
            ],
        )
        _validate_safe_payload(self.lanes, "crm_connector_read_lanes")
        return self


class CrmSendsWritesAuthorityPlanReadModel(_CrmLocalModel):
    plan_ref: str = CRM_LOCAL_SENDS_WRITES_PLAN_REF
    lane_refs: list[str]
    blocker_report_refs: list[str]
    unblock_prompt_refs: list[str]
    sends_enabled: bool = False
    connector_writes_enabled: bool = False
    calendar_writes_enabled: bool = False
    external_crm_writes_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmSendsWritesAuthorityPlanReadModel":
        _validate_ref(self.plan_ref, "plan_ref")
        for field_name in ["lane_refs", "blocker_report_refs", "unblock_prompt_refs"]:
            _validate_ref_list(getattr(self, field_name), field_name)
        _deny_true_flags(
            self,
            [
                ("sends_enabled", "CRM_SENDS_PLAN_SEND_DENIED"),
                ("connector_writes_enabled", "CRM_SENDS_PLAN_CONNECTOR_DENIED"),
                ("calendar_writes_enabled", "CRM_SENDS_PLAN_CALENDAR_DENIED"),
                ("external_crm_writes_enabled", "CRM_SENDS_PLAN_EXTERNAL_CRM_DENIED"),
            ],
        )
        return self


class CrmImportExportPostureReadModel(_CrmLocalModel):
    contract_ref: str = CRM_LOCAL_IMPORT_EXPORT_CONTRACT_REF
    import_preview_cli_ref: str = "repo-local-command:uaa-crm:import-preview"
    export_redacted_cli_ref: str = "repo-local-command:uaa-crm:export-redacted"
    exact_import_commit_enabled: bool = False
    export_redacted_snapshot_enabled: bool = True
    no_raw_path_persistence: bool = True
    identity_match_review_only: bool = True
    silent_merge_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmImportExportPostureReadModel":
        for field_name in [
            "contract_ref",
            "import_preview_cli_ref",
            "export_redacted_cli_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        if not self.no_raw_path_persistence or not self.identity_match_review_only:
            raise ValueError("CRM_IMPORT_EXPORT_SAFE_POSTURE_REQUIRED")
        if self.silent_merge_enabled:
            raise ValueError("CRM_IMPORT_EXPORT_SILENT_MERGE_DENIED")
        return self


class CrmLocalCommandCenterReadModel(_CrmLocalModel):
    schema_version: str = CRM_LOCAL_COMMAND_CENTER_SCHEMA_VERSION
    contract_ref: str = CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF
    source_m0_contract_ref: str = CRM_COMMUNICATIONS_SPINE_CONTRACT_REF
    source: str = CRM_LOCAL_COMMAND_CENTER_SOURCE
    state: CrmImplementationState = CrmImplementationState.read_only
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    route_refs: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_COMMAND_CENTER_ROUTE_REFS)
    )
    cli_refs: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_COMMAND_CENTER_CLI_REFS)
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_REDACTIONS)
    )
    authority_posture: CrmAuthorityPostureReadModel
    storage_status: CrmStorageStatusReadModel
    people: list[CrmPersonReadModel]
    organizations: list[CrmOrganizationReadModel]
    relationships: list[CrmRelationshipReadModel]
    social_relationship_projection: CrmSocialRelationshipProjection
    timeline_events: list[CrmTimelineEventReadModel]
    follow_ups: list[CrmFollowUpReadModel]
    opportunities: list[CrmOpportunityReadModel]
    pipelines: list[CrmPipelineReadModel]
    smart_lists: list[CrmSmartListReadModel]
    communication_drafts: list[CrmCommunicationDraftReadModel]
    ai_proposals: list[CrmAiProposalReadModel]
    reports: list[CrmReportReadModel]
    connector_read_lanes: CrmConnectorReadLaneReadModel
    sends_writes_authority_plan: CrmSendsWritesAuthorityPlanReadModel
    import_export_posture: CrmImportExportPostureReadModel
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_BLOCKED_AUTHORITY_REFS)
    )
    raw_contact_details_included: bool = False
    raw_message_bodies_included: bool = False
    raw_paths_included: bool = False
    provider_payloads_included: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmLocalCommandCenterReadModel":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref(self.source_m0_contract_ref, "source_m0_contract_ref")
        _validate_safe_text(self.source, "source")
        _validate_ref_list(self.cli_refs, "cli_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_safe_payload(self.model_dump(mode="json"), "crm_local_read_model")
        if not self.backend_owned or not self.read_only or not self.safe_refs_only:
            raise ValueError("CRM_LOCAL_READ_MODEL_SAFE_POSTURE_REQUIRED")
        self.social_relationship_projection.validate_owner_links(
            people=self.people,
            organizations=self.organizations,
            relationships=self.relationships,
        )
        _deny_true_flags(
            self,
            [
                ("raw_contact_details_included", "CRM_LOCAL_RAW_CONTACT_DENIED"),
                ("raw_message_bodies_included", "CRM_LOCAL_RAW_MESSAGE_DENIED"),
                ("raw_paths_included", "CRM_LOCAL_RAW_PATH_DENIED"),
                ("provider_payloads_included", "CRM_LOCAL_PROVIDER_PAYLOAD_DENIED"),
                ("production_authority_enabled", "CRM_LOCAL_PRODUCTION_DENIED"),
            ],
        )
        return self


class CrmLocalMutationRequest(_CrmLocalModel):
    actor_context: ActorContext = Field(
        default_factory=lambda: _default_actor_context()
    )
    mutation_kind: Literal[
        "create_follow_up",
        "update_follow_up",
        "mark_follow_up_complete",
        "move_opportunity_stage",
        "add_note_summary_ref",
        "select_social_context",
        "clear_social_context",
    ]
    target_ref: str
    approval_ref: str
    safe_summary: str = "Local CRM mutation requested with safe summary only."
    relationship_ref: str | None = None
    follow_up_status: (
        Literal[
            "due",
            "upcoming",
            "stale",
            "blocked",
            "proposed",
            "completed",
        ]
        | None
    ) = None
    stage_ref: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmLocalMutationRequest":
        _validate_ref(self.target_ref, "target_ref")
        _validate_ref(self.approval_ref, "approval_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if self.relationship_ref is not None:
            _validate_ref(self.relationship_ref, "relationship_ref")
        if self.stage_ref is not None:
            _validate_ref(self.stage_ref, "stage_ref")
        _validate_optional_ref_list(self.metadata_refs, "metadata_refs")
        _validate_safe_payload(
            self.model_dump(mode="json"), "crm_local_mutation_request"
        )
        return self


class CrmLocalMutationReceipt(_CrmLocalModel):
    contract_ref: str = CRM_LOCAL_MUTATION_CONTRACT_REF
    mutation_ref: str
    receipt_ref: str
    audit_ref: str
    mutation_kind: str
    target_ref: str
    approval_ref: str
    approval_status: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    authority_decision_ref: str
    authority_decision_outcome: str
    authority_lease_ref: str
    authority_domain_ref: str = CRM_LOCAL_MUTATION_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = CRM_LOCAL_MUTATION_AUTHORITY_CAPABILITY_REF
    before_ref: str
    after_ref: str
    rollback_ref: str
    proof_ref: str
    safe_summary: str
    evidence_refs: list[str]
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CRM_LOCAL_BLOCKED_AUTHORITY_REFS)
    )
    local_mutation_performed: bool = True
    replayed: bool = False
    connector_write_performed: bool = False
    send_performed: bool = False
    calendar_write_performed: bool = False
    account_sync_performed: bool = False
    provider_model_call_performed: bool = False
    browser_automation_performed: bool = False
    external_crm_write_performed: bool = False
    raw_content_stored: bool = False
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmLocalMutationReceipt":
        for field_name in [
            "contract_ref",
            "mutation_ref",
            "receipt_ref",
            "audit_ref",
            "target_ref",
            "approval_ref",
            "idempotency_ref",
            "payload_fingerprint_ref",
            "authority_decision_ref",
            "authority_lease_ref",
            "authority_domain_ref",
            "authority_capability_ref",
            "before_ref",
            "after_ref",
            "rollback_ref",
            "proof_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_safe_text(
            self.authority_decision_outcome, "authority_decision_outcome"
        )
        if self.authority_decision_outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise ValueError("CRM_LOCAL_MUTATION_AUTHORITY_DECISION_UNSUPPORTED")
        _validate_safe_text(self.safe_summary, "safe_summary")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _deny_true_flags(
            self,
            [
                ("connector_write_performed", "CRM_MUTATION_CONNECTOR_WRITE_DENIED"),
                ("send_performed", "CRM_MUTATION_SEND_DENIED"),
                ("calendar_write_performed", "CRM_MUTATION_CALENDAR_DENIED"),
                ("account_sync_performed", "CRM_MUTATION_ACCOUNT_SYNC_DENIED"),
                ("provider_model_call_performed", "CRM_MUTATION_PROVIDER_DENIED"),
                ("browser_automation_performed", "CRM_MUTATION_BROWSER_DENIED"),
                ("external_crm_write_performed", "CRM_MUTATION_EXTERNAL_WRITE_DENIED"),
                ("raw_content_stored", "CRM_MUTATION_RAW_CONTENT_DENIED"),
            ],
        )
        return self


def build_crm_local_command_center_read_model(
    store: "CrmLocalStore | None" = None,
) -> CrmLocalCommandCenterReadModel:
    return (store or CrmLocalStore.from_env()).read_model()


def validate_crm_local_command_center_read_model(
    payload: CrmLocalCommandCenterReadModel | dict[str, Any],
) -> CrmLocalCommandCenterReadModel:
    data = (
        payload.model_dump(mode="python")
        if isinstance(payload, BaseModel)
        else dict(payload)
    )
    _validate_safe_payload(data, "crm_local_command_center")
    return CrmLocalCommandCenterReadModel.model_validate(data)


def expected_crm_local_mutation_approval_ref(
    *,
    target_ref: str,
    idempotency_ref: str,
) -> str:
    _validate_ref(target_ref, "target_ref")
    _validate_ref(idempotency_ref, "idempotency_ref")
    return _crm_local_derived_ref(
        "approval-ref:crm-local",
        target_ref,
        idempotency_ref,
    )


def crm_local_mutation_approval_request(
    *,
    request: CrmLocalMutationRequest,
    idempotency_ref: str,
) -> ApprovalRequest:
    _validate_ref(idempotency_ref, "idempotency_ref")
    resources = [
        request.target_ref,
        f"mutation-kind-ref:crm-local:{request.mutation_kind}",
        CRM_LOCAL_MUTATION_CONTRACT_REF,
        idempotency_ref,
    ]
    if request.relationship_ref:
        resources.append(request.relationship_ref)
    if request.stage_ref:
        resources.append(request.stage_ref)
    return ApprovalRequest(
        approval_request_id=_crm_local_derived_ref(
            "approval-request:crm-local",
            request.target_ref,
            idempotency_ref,
        ),
        run_id=_crm_local_derived_ref(
            "run:crm-local",
            request.target_ref,
        ),
        subject_type=ApprovalSubjectType.external_action,
        subject_id=request.target_ref,
        actor_context=request.actor_context,
        requested_action=f"crm_local_mutation:{request.mutation_kind}",
        purpose="Approve an exact-scoped local-only CRM mutation with receipt refs.",
        risk_level=ApprovalRiskLevel.medium,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="crm_local_command_center",
            requires_redaction=True,
        ),
        resource_refs=resources,
        event_ref=_crm_local_derived_ref(
            "event-ref:crm-local-mutation",
            request.target_ref,
            idempotency_ref,
        ),
        trace_id=_crm_local_derived_ref(
            "trace-ref:crm-local-mutation",
            request.target_ref,
            idempotency_ref,
        ),
        expires_at=utc_now() + timedelta(hours=1),
    )


class CrmLocalStore:
    def __init__(
        self,
        state_dir: Path,
        *,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> None:
        self.state_dir = state_dir
        self.snapshot_file = state_dir / "crm_local_command_center_snapshot.json"
        self.events_file = state_dir / "crm_local_command_center_events.jsonl"
        self._active_authority_leases = active_authority_leases
        self._state_lock = FileSingleWriterLockManager(state_dir / ".locks")

    @classmethod
    def from_env(cls) -> "CrmLocalStore":
        configured = os.environ.get("UAA_CRM_STATE_DIR")
        if configured:
            return cls(Path(configured))
        return cls(Path.cwd() / ".uaa" / "crm")

    def read_model(self) -> CrmLocalCommandCenterReadModel:
        state = self._read_state()
        storage_status = self.storage_status(state)
        payload = _state_to_read_model_payload(state, storage_status)
        return validate_crm_local_command_center_read_model(payload)

    def storage_status(
        self,
        state: dict[str, Any] | None = None,
    ) -> CrmStorageStatusReadModel:
        data = state or self._read_state()
        counts = {
            key: len(data.get(key, []))
            for key in [
                "people",
                "organizations",
                "relationships",
                "timeline_events",
                "follow_ups",
                "opportunities",
                "pipelines",
                "smart_lists",
                "communication_drafts",
                "ai_proposals",
                "reports",
                "mutation_receipts",
            ]
        }
        return CrmStorageStatusReadModel(
            state=str(data.get("storage_state", "code_seed")),
            initialized=self.snapshot_file.exists(),
            seeded_demo=bool(data.get("seeded_demo", False)),
            record_counts=counts,
            event_log_ref="jsonl-ref:crm-local-command-center:events",
            snapshot_ref="snapshot-ref:crm-local-command-center:state",
        )

    def seed_demo(self) -> CrmStorageStatusReadModel:
        state = _default_state_payload(storage_state="seeded_demo", seeded_demo=True)
        self._write_state(state, "event-ref:crm-local:seed-demo")
        return self.storage_status(state)

    def clear_demo(self, *, confirm_local_only: bool) -> CrmStorageStatusReadModel:
        if not confirm_local_only:
            raise CrmLocalCommandCenterError(
                "CRM_CLEAR_DEMO_LOCAL_ONLY_CONFIRM_REQUIRED"
            )
        state = _empty_state_payload()
        self._write_state(state, "event-ref:crm-local:clear-demo")
        return self.storage_status(state)

    def record_local_mutation(
        self,
        *,
        request: CrmLocalMutationRequest,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> CrmLocalMutationReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        with self._state_lock.acquire(CRM_LOCAL_STATE_LOCK_KEY):
            return self._record_local_mutation_locked(
                request=request,
                idempotency_ref=idempotency_ref,
                approval_authority=approval_authority,
            )

    def _record_local_mutation_locked(
        self,
        *,
        request: CrmLocalMutationRequest,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority | None,
    ) -> CrmLocalMutationReceipt:
        state = self._read_state()
        payload_fingerprint_ref = _local_mutation_payload_fingerprint_ref(request)
        replay = _find_replay(state, idempotency_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise CrmLocalCommandCenterDuplicateError(
                    "CRM_LOCAL_MUTATION_IDEMPOTENCY_CONFLICT"
                )
            receipt = _find_receipt(state, str(replay["receipt_ref"]))
            return CrmLocalMutationReceipt.model_validate({**receipt, "replayed": True})

        approval_status, approval_reason_refs = _validate_local_mutation_approval(
            request=request,
            idempotency_ref=idempotency_ref,
            approval_authority=approval_authority,
        )
        if approval_status != "approved":
            raise CrmLocalCommandCenterError("CRM_LOCAL_MUTATION_APPROVAL_DENIED")
        authority_decision = self._local_mutation_authority_decision(
            request=request,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )

        before_ref = _crm_local_derived_ref(
            "before-ref:crm-local",
            request.target_ref,
        )
        after_ref = _crm_local_derived_ref(
            "after-ref:crm-local",
            request.target_ref,
            idempotency_ref,
        )
        receipt_ref = _crm_local_derived_ref(
            "receipt-ref:crm-local-mutation",
            request.target_ref,
            idempotency_ref,
        )
        receipt = CrmLocalMutationReceipt(
            mutation_ref=_crm_local_derived_ref(
                "mutation-ref:crm-local",
                request.target_ref,
                idempotency_ref,
            ),
            receipt_ref=receipt_ref,
            audit_ref=_crm_local_derived_ref(
                "audit-ref:crm-local-mutation",
                request.target_ref,
                idempotency_ref,
            ),
            mutation_kind=request.mutation_kind,
            target_ref=request.target_ref,
            approval_ref=request.approval_ref,
            approval_status=approval_status,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=str(authority_decision.lease_ref),
            before_ref=before_ref,
            after_ref=after_ref,
            rollback_ref=_crm_local_derived_ref(
                "rollback-ref:crm-local:manual-reverse-ready",
                request.target_ref,
            ),
            proof_ref=_crm_local_derived_ref(
                "proof-ref:crm-local-mutation",
                request.target_ref,
                idempotency_ref,
            ),
            safe_summary="Exact local CRM mutation receipt recorded.",
            evidence_refs=[
                "evidence-ref:crm-local:mutation-lane",
                authority_decision.decision_ref,
                str(authority_decision.lease_ref),
                *request.metadata_refs,
                *approval_reason_refs,
            ],
        )
        _apply_mutation(state, request, receipt)
        try:
            validate_crm_local_command_center_read_model(
                _state_to_read_model_payload(state, self.storage_status(state))
            )
        except (CrmLocalCommandCenterError, ValueError) as exc:
            raise CrmLocalCommandCenterError(
                "CRM_LOCAL_MUTATION_PROSPECTIVE_STATE_INVALID"
            ) from exc
        state.setdefault("mutation_receipts", []).append(
            receipt.model_dump(mode="json")
        )
        state.setdefault("mutation_replays", []).append(
            {
                "idempotency_ref": idempotency_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "receipt_ref": receipt.receipt_ref,
            }
        )
        state["storage_state"] = "local_state"
        self._write_state(state, receipt.audit_ref)
        return receipt

    def record_confirmed_local_mutation(
        self,
        *,
        request: CrmLocalMutationRequest,
        idempotency_ref: str,
        confirmed: bool,
    ) -> CrmLocalMutationReceipt:
        """Capture one exact operator approval and lease, then mutate locally."""
        if not confirmed:
            raise CrmLocalCommandCenterError(
                "CRM_LOCAL_MUTATION_OPERATOR_CONFIRMATION_REQUIRED"
            )
        _require_local_human_operator(request.actor_context)
        _validate_ref(idempotency_ref, "idempotency_ref")
        with self._state_lock.acquire(CRM_LOCAL_STATE_LOCK_KEY):
            return self._record_confirmed_local_mutation_locked(
                request=request,
                idempotency_ref=idempotency_ref,
            )

    def _record_confirmed_local_mutation_locked(
        self,
        *,
        request: CrmLocalMutationRequest,
        idempotency_ref: str,
    ) -> CrmLocalMutationReceipt:
        expected_ref = expected_crm_local_mutation_approval_ref(
            target_ref=request.target_ref,
            idempotency_ref=idempotency_ref,
        )
        if request.approval_ref != expected_ref:
            raise CrmLocalCommandCenterError("CRM_LOCAL_MUTATION_APPROVAL_DENIED")

        payload_fingerprint_ref = _local_mutation_payload_fingerprint_ref(request)
        state = self._read_state()
        replay = _find_replay(state, idempotency_ref)
        if replay is not None:
            if replay["payload_fingerprint_ref"] != payload_fingerprint_ref:
                raise CrmLocalCommandCenterDuplicateError(
                    "CRM_LOCAL_MUTATION_IDEMPOTENCY_CONFLICT"
                )
            receipt = _find_receipt(state, str(replay["receipt_ref"]))
            return CrmLocalMutationReceipt.model_validate({**receipt, "replayed": True})

        approvals = LocalApprovalAuthority()
        approval_request = approvals.create_request(
            crm_local_mutation_approval_request(
                request=request,
                idempotency_ref=idempotency_ref,
            )
        )
        approvals.grant(
            approval_request.approval_request_id,
            approved_by_actor_id="local_operator",
            approval_ref=expected_ref,
            expires_at=approval_request.expires_at,
        )

        lease_store = AuthorityLeaseStore(self.state_dir / "authority")
        lease_request = _crm_local_mutation_lease_issue_request(
            request=request,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        lease_idempotency_ref = _hashed_ref(
            "idempotency-ref:crm-local-mutation-lease",
            payload_fingerprint_ref,
        )
        _requirement, _grant, lease, lease_receipt = (
            issue_authority_lease_with_backend_approval(
                lease_store,
                lease_request,
                idempotency_ref=lease_idempotency_ref,
                approved_by_actor_id="operator-ref:local-user",
            )
        )
        if lease is None or lease_receipt.status not in {"issued", "replayed"}:
            raise CrmLocalCommandCenterError(
                "CRM_LOCAL_MUTATION_EXACT_LEASE_ISSUANCE_DENIED"
            )
        confirmed_store = CrmLocalStore(
            self.state_dir,
            active_authority_leases=[lease],
        )
        try:
            return confirmed_store._record_local_mutation_locked(
                request=request,
                idempotency_ref=idempotency_ref,
                approval_authority=approvals,
            )
        except Exception:
            _revoked_lease, revoke_receipt = lease_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=lease.lease_ref,
                    decision_reason_ref=(
                        "decision-reason-ref:crm-local-mutation:post-issue-failure"
                    ),
                    safe_summary=(
                        "Revoke the exact CRM mutation lease after the local "
                        "mutation failed before commit."
                    ),
                ),
                idempotency_ref=_hashed_ref(
                    "idempotency-ref:crm-local-mutation-lease-revoke",
                    lease.lease_ref,
                ),
            )
            if revoke_receipt.status not in {"revoked", "replayed"}:
                raise CrmLocalCommandCenterError(
                    "CRM_LOCAL_MUTATION_LEASE_REVOCATION_FAILED"
                )
            raise

    def _local_mutation_authority_decision(
        self,
        *,
        request: CrmLocalMutationRequest,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ):
        leases = (
            self._active_authority_leases
            if self._active_authority_leases is not None
            else (
                AuthorityLeaseStore().list_leases(active_only=True)
                or build_default_authority_leases()
            )
        )
        resource_refs = _crm_local_mutation_resource_refs(
            request=request,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
        )
        authority_decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=CRM_LOCAL_MUTATION_AUTHORITY_ACTION_REF,
                domain=AuthorityDomain.contacts,
                capability=AuthorityCapability.write,
                safe_summary=(
                    "Evaluate Contacts write authority for exact local CRM "
                    "mutation receipt."
                ),
                resource_refs=resource_refs,
                route_ref=CRM_LOCAL_MUTATION_ROUTE_REF,
                lane_ref=CRM_LOCAL_MUTATION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget,
                        value=1,
                    )
                ],
                rollback_ref=_crm_local_derived_ref(
                    "rollback-ref:crm-local:manual-reverse-ready",
                    request.target_ref,
                ),
                safe_disable_ref=CRM_LOCAL_MUTATION_SAFE_DISABLE_REF,
            ),
            leases,
        )
        if authority_decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            raise CrmLocalAuthorityError(
                [
                    *authority_decision.reason_refs,
                    CRM_LOCAL_MUTATION_AUTHORITY_REQUIRED_BLOCKED_REF,
                ],
                required_refs={
                    "authority_decision_ref": authority_decision.decision_ref,
                    "required_mode_ref": CRM_LOCAL_MUTATION_AUTHORITY_REQUIRED_MODE_REF,
                    "required_domain_ref": CRM_LOCAL_MUTATION_AUTHORITY_DOMAIN_REF,
                    "required_capability_ref": (
                        CRM_LOCAL_MUTATION_AUTHORITY_CAPABILITY_REF
                    ),
                    "safe_disable_ref": authority_decision.safe_disable_ref,
                    "rollback_ref": authority_decision.rollback_ref,
                },
            )
        return authority_decision

    def export_redacted_snapshot(self) -> dict[str, Any]:
        model = self.read_model()
        return {
            "schema_version": "crm-local-command-center.redacted-export.v1",
            "contract_ref": CRM_LOCAL_IMPORT_EXPORT_CONTRACT_REF,
            "snapshot_ref": "export-ref:crm-local:redacted-snapshot",
            "crm": model.model_dump(mode="json"),
            "safe_refs_only": True,
            "raw_paths_omitted": True,
            "raw_contact_details_omitted": True,
        }

    def import_preview_from_csv(
        self, csv_path: Path, *, limit: int = 20
    ) -> dict[str, Any]:
        rows: list[dict[str, str]] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                if index >= limit:
                    break
                rows.append(
                    {
                        "candidate_ref": f"identity-match-candidate-ref:crm-local:csv:{index + 1}",
                        "safe_label_ref": _hashed_ref(
                            "safe-label-ref:crm-local:csv",
                            json.dumps(row, sort_keys=True),
                        ),
                        "review_only": "true",
                    }
                )
        return {
            "schema_version": "crm-local-command-center.import-preview.v1",
            "contract_ref": CRM_LOCAL_IMPORT_EXPORT_CONTRACT_REF,
            "source_ref": _hashed_ref("source-ref:crm-local:csv-import", str(csv_path)),
            "candidate_count": len(rows),
            "identity_match_candidates": rows,
            "commit_enabled": False,
            "exact_approval_required_before_commit": True,
            "raw_path_persisted": False,
            "raw_contact_details_persisted": False,
            "silent_merge_enabled": False,
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.snapshot_file.exists():
            return _default_state_payload()
        try:
            state = json.loads(self.snapshot_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CrmLocalCommandCenterError("CRM_LOCAL_STATE_UNREADABLE") from exc
        _validate_safe_payload(state, "crm_local_state")
        return dict(state)

    def _write_state(self, state: dict[str, Any], event_ref: str) -> None:
        with self._state_lock.acquire(CRM_LOCAL_STATE_LOCK_KEY):
            self._write_state_locked(state, event_ref)

    def _write_state_locked(self, state: dict[str, Any], event_ref: str) -> None:
        _validate_safe_payload(state, "crm_local_state")
        _validate_ref(event_ref, "event_ref")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.state_dir,
                prefix=".crm-local-snapshot-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(json.dumps(state, indent=2, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                tmp_path = Path(handle.name)
            tmp_path.replace(self.snapshot_file)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        event = {
            "event_ref": event_ref,
            "safe_summary": "CRM local command center state event recorded.",
            "storage_ref": CRM_LOCAL_COMMAND_CENTER_STORAGE_REF,
            "created_at": utc_now().isoformat(),
            "raw_paths_omitted": True,
        }
        with self.events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def _default_actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_operator",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _require_local_human_operator(actor_context: ActorContext) -> None:
    if (
        actor_context.actor_type != ActorType.human_user.value
        or actor_context.actor_id != "local_operator"
        or actor_context.authority_source
        not in {
            AuthoritySource.explicit_user_request.value,
            AuthoritySource.manual_operator_action.value,
        }
    ):
        raise CrmLocalCommandCenterError("CRM_LOCAL_MUTATION_HUMAN_OPERATOR_REQUIRED")


def _default_state_payload(
    *,
    storage_state: str = "code_seed",
    seeded_demo: bool = False,
) -> dict[str, Any]:
    people = [
        {
            "person_ref": "person-ref:crm-local:relationship-alpha",
            "safe_display_label": "Relationship Alpha",
            "relationship_refs": ["relationship-ref:crm-local:alpha"],
            "organization_refs": ["organization-ref:crm-local:alpha"],
            "evidence_refs": ["evidence-ref:crm-local:alpha"],
            "memory_provenance_refs": ["memory-ref:crm-local:alpha"],
            "tags": ["warm", "high context", "social-context"],
        },
        {
            "person_ref": "person-ref:crm-local:relationship-beta",
            "safe_display_label": "Relationship Beta",
            "relationship_refs": ["relationship-ref:crm-local:beta"],
            "organization_refs": ["organization-ref:crm-local:beta"],
            "evidence_refs": ["evidence-ref:crm-local:beta"],
            "memory_provenance_refs": ["memory-ref:crm-local:beta"],
            "tags": ["needs follow up"],
        },
    ]
    organizations = [
        {
            "organization_ref": "organization-ref:crm-local:alpha",
            "safe_display_label": "Organization Alpha",
            "relationship_refs": ["relationship-ref:crm-local:alpha"],
            "evidence_refs": ["evidence-ref:crm-local:alpha"],
        },
        {
            "organization_ref": "organization-ref:crm-local:beta",
            "safe_display_label": "Organization Beta",
            "relationship_refs": ["relationship-ref:crm-local:beta"],
            "evidence_refs": ["evidence-ref:crm-local:beta"],
        },
    ]
    relationships = [
        {
            "relationship_ref": "relationship-ref:crm-local:alpha",
            "person_ref": "person-ref:crm-local:relationship-alpha",
            "organization_ref": "organization-ref:crm-local:alpha",
            "safe_display_label": "Relationship Alpha",
            "relationship_kind_ref": "relationship-kind-ref:crm-local:operator-network",
            "health_state": "warm",
            "safe_summary": "Warm relationship with active local follow up context.",
            "why_shown": "Shown because reviewed memory and evidence refs indicate current follow up value.",
            "timeline_event_refs": [
                "timeline-event-ref:crm-local:alpha:memory",
                "timeline-event-ref:crm-local:alpha:follow-up",
            ],
            "follow_up_refs": ["follow-up-ref:crm-local:alpha:due"],
            "opportunity_refs": ["opportunity-ref:crm-local:alpha:partnership"],
            "evidence_refs": ["evidence-ref:crm-local:alpha"],
            "memory_provenance_refs": ["memory-ref:crm-local:alpha"],
            "stale_state": "fresh",
        },
        {
            "relationship_ref": "relationship-ref:crm-local:beta",
            "person_ref": "person-ref:crm-local:relationship-beta",
            "organization_ref": "organization-ref:crm-local:beta",
            "safe_display_label": "Relationship Beta",
            "relationship_kind_ref": "relationship-kind-ref:crm-local:operator-network",
            "health_state": "stale",
            "safe_summary": "Relationship has a stale promise and missing evidence refs.",
            "why_shown": "Shown because the follow up queue found a stale promise ref.",
            "timeline_event_refs": [
                "timeline-event-ref:crm-local:beta:promise",
                "timeline-event-ref:crm-local:beta:blocked",
            ],
            "follow_up_refs": ["follow-up-ref:crm-local:beta:stale"],
            "opportunity_refs": ["opportunity-ref:crm-local:beta:project"],
            "evidence_refs": ["evidence-ref:crm-local:beta"],
            "memory_provenance_refs": ["memory-ref:crm-local:beta"],
            "stale_state": "stale",
        },
    ]
    timeline_events = [
        _timeline(
            "alpha:memory",
            "relationship-ref:crm-local:alpha",
            "memory_ref",
            "Reviewed memory indicates current relationship context.",
            "memory-ref:crm-local:alpha",
        ),
        _timeline(
            "alpha:follow-up",
            "relationship-ref:crm-local:alpha",
            "follow_up_ref",
            "Follow up is due from reviewed local evidence.",
            "follow-up-ref:crm-local:alpha:due",
        ),
        _timeline(
            "beta:promise",
            "relationship-ref:crm-local:beta",
            "decision_ref",
            "Stale promise needs review before any action.",
            "decision-ref:crm-local:beta:promise",
            stale="stale",
        ),
        _timeline(
            "beta:blocked",
            "relationship-ref:crm-local:beta",
            "evidence_ref",
            "Missing evidence keeps external action blocked.",
            "evidence-ref:crm-local:beta:missing",
            stale="missing_evidence",
        ),
    ]
    follow_ups = [
        _follow_up(
            "alpha:due",
            "relationship-ref:crm-local:alpha",
            "due",
            "high",
            "Due follow up with proof refs ready for Action Inbox review.",
        ),
        _follow_up(
            "beta:stale",
            "relationship-ref:crm-local:beta",
            "stale",
            "medium",
            "Stale promise needs evidence review before any outreach draft.",
        ),
        _follow_up(
            "alpha:proposed",
            "relationship-ref:crm-local:alpha",
            "proposed",
            "low",
            "Proposal-only relationship check-in is ready for review.",
        ),
    ]
    opportunities = [
        {
            "opportunity_ref": "opportunity-ref:crm-local:alpha:partnership",
            "relationship_ref": "relationship-ref:crm-local:alpha",
            "pipeline_ref": "pipeline-ref:crm-local:operator",
            "opportunity_kind": "partnership",
            "stage_ref": "stage-ref:crm-local:operator:qualified",
            "stage_label": "Qualified",
            "safe_summary": "Partnership opportunity is review-ready with safe proof refs.",
            "evidence_refs": ["evidence-ref:crm-local:alpha"],
            "proof_refs": ["proof-ref:crm-local:alpha:partnership"],
        },
        {
            "opportunity_ref": "opportunity-ref:crm-local:beta:project",
            "relationship_ref": "relationship-ref:crm-local:beta",
            "pipeline_ref": "pipeline-ref:crm-local:operator",
            "opportunity_kind": "project",
            "stage_ref": "stage-ref:crm-local:operator:needs-review",
            "stage_label": "Needs Review",
            "safe_summary": "Project opportunity is at risk until evidence is reviewed.",
            "evidence_refs": ["evidence-ref:crm-local:beta"],
            "proof_refs": ["proof-ref:crm-local:beta:project"],
        },
    ]
    pipelines = [_build_deal_stage_summary(opportunities)]
    smart_lists = _build_smart_lists(relationships, follow_ups, opportunities)
    return {
        "storage_state": storage_state,
        "seeded_demo": seeded_demo,
        "people": people,
        "organizations": organizations,
        "relationships": relationships,
        "timeline_events": timeline_events,
        "follow_ups": follow_ups,
        "opportunities": opportunities,
        "pipelines": pipelines,
        "smart_lists": smart_lists,
        "communication_drafts": [
            {
                "draft_ref": "draft-ref:crm-local:alpha:email",
                "relationship_ref": "relationship-ref:crm-local:alpha",
                "draft_kind": "email_draft",
                "bounded_redacted_summary": "Local review draft summary for relationship follow up.",
                "proof_refs": ["proof-ref:crm-local:alpha:draft"],
            },
            {
                "draft_ref": "draft-ref:crm-local:beta:meeting",
                "relationship_ref": "relationship-ref:crm-local:beta",
                "draft_kind": "meeting_agenda",
                "bounded_redacted_summary": "Local meeting agenda summary with missing evidence called out.",
                "proof_refs": ["proof-ref:crm-local:beta:draft"],
            },
        ],
        "ai_proposals": [
            {
                "proposal_ref": "proposal-ref:crm-local:alpha:next-follow-up",
                "proposal_type": "next_best_follow_up",
                "relationship_ref": "relationship-ref:crm-local:alpha",
                "safe_summary": "Deterministic proposal suggests reviewing the due follow up.",
                "proof_refs": ["proof-ref:crm-local:alpha:proposal"],
            },
            {
                "proposal_ref": "proposal-ref:crm-local:beta:risk",
                "proposal_type": "relationship_risk",
                "relationship_ref": "relationship-ref:crm-local:beta",
                "safe_summary": "Deterministic proposal flags stale evidence before outreach.",
                "proof_refs": ["proof-ref:crm-local:beta:proposal"],
            },
        ],
        "reports": [
            _report("follow-up-debt", "Follow-up debt", "2 open follow-up refs"),
            _report("stale-promises", "Stale promises", "1 stale promise ref"),
            _report(
                "relationship-health",
                "Relationship health",
                "1 warm and 1 stale relationship",
            ),
            _report(
                "opportunity-aging", "Opportunity aging", "1 opportunity needs review"
            ),
            _report(
                "source-ref-effectiveness",
                "Source ref effectiveness",
                "Evidence coverage is partial",
            ),
            _report(
                "activity-completion",
                "Activity completion",
                "1 completed or proposed activity ref",
            ),
            _report("pipeline-value", "Pipeline value", "No revenue claim recorded"),
            _report(
                "blocked-authority",
                "Blocked authority",
                "External sends and writes blocked",
            ),
            _report(
                "memory-evidence-coverage",
                "Memory evidence coverage",
                "2 memory provenance refs",
            ),
        ],
        "mutation_receipts": [],
        "mutation_replays": [],
    }


def _empty_state_payload() -> dict[str, Any]:
    state = _default_state_payload(storage_state="cleared_demo", seeded_demo=False)
    for key in [
        "people",
        "organizations",
        "relationships",
        "timeline_events",
        "follow_ups",
        "opportunities",
        "pipelines",
        "smart_lists",
        "communication_drafts",
        "ai_proposals",
        "reports",
        "mutation_receipts",
        "mutation_replays",
    ]:
        state[key] = []
    return state


def _state_to_read_model_payload(
    state: dict[str, Any],
    storage_status: CrmStorageStatusReadModel,
) -> dict[str, Any]:
    social_relationship_projection = build_crm_social_relationship_projection(
        people=state.get("people", []),
        organizations=state.get("organizations", []),
        relationships=state.get("relationships", []),
    )
    return {
        "authority_posture": CrmAuthorityPostureReadModel().model_dump(mode="python"),
        "storage_status": storage_status.model_dump(mode="python"),
        "people": state.get("people", []),
        "organizations": state.get("organizations", []),
        "relationships": state.get("relationships", []),
        "social_relationship_projection": social_relationship_projection.model_dump(
            mode="python"
        ),
        "timeline_events": state.get("timeline_events", []),
        "follow_ups": state.get("follow_ups", []),
        "opportunities": state.get("opportunities", []),
        "pipelines": state.get("pipelines", []),
        "smart_lists": state.get("smart_lists", []),
        "communication_drafts": state.get("communication_drafts", []),
        "ai_proposals": state.get("ai_proposals", []),
        "reports": state.get("reports", []),
        "connector_read_lanes": {
            "lanes": [
                {
                    "lane_ref": "lane-ref:crm-connector:local-file-import",
                    "status": "preview_only",
                    "safe_summary": "Local file import preview can inspect user-owned CSV candidates.",
                },
                {
                    "lane_ref": "lane-ref:crm-connector:email-metadata-read",
                    "status": "blocked",
                    "safe_summary": "Email metadata read is blocked until a single-source gateway lane, source policy, approval scope, audit schema, and redaction contract exist.",
                },
                {
                    "lane_ref": "lane-ref:crm-connector:calendar-metadata-read",
                    "status": "blocked",
                    "safe_summary": "Calendar metadata read requires an implemented calendar/read AuthorityLease scope, source policy, approval binding, audit schema, and redacted receipt.",
                },
                {
                    "lane_ref": "lane-ref:crm-connector:contacts-metadata-read",
                    "status": "blocked",
                    "safe_summary": "Contacts metadata read is blocked until the approved gateway, test scope, approval binding, and safe output receipt exist.",
                },
            ]
        },
        "sends_writes_authority_plan": {
            "lane_refs": [
                "lane-ref:crm-send:exact-email",
                "lane-ref:crm-send:exact-sms",
                "lane-ref:crm-write:calendar",
                "lane-ref:crm-write:external-crm",
                "lane-ref:crm-sync:contact",
                "lane-ref:crm-sync:task",
            ],
            "blocker_report_refs": [
                "docs-ref:crm-blocker:connector-read-lanes",
                "docs-ref:crm-blocker:sends-writes",
            ],
            "unblock_prompt_refs": [
                "prompt-ref:crm:unblock-connector-read-lanes",
                "prompt-ref:crm:unblock-sends-writes",
            ],
        },
        "import_export_posture": CrmImportExportPostureReadModel().model_dump(
            mode="python"
        ),
    }


def _timeline(
    suffix: str,
    relationship_ref: str,
    event_kind: str,
    summary: str,
    source_ref: str,
    *,
    stale: str = "fresh",
) -> dict[str, Any]:
    return {
        "event_ref": f"timeline-event-ref:crm-local:{suffix}",
        "relationship_ref": relationship_ref,
        "event_kind": event_kind,
        "occurred_at_ref": f"time-ref:crm-local:{_safe_suffix(suffix)}",
        "safe_summary": summary,
        "why_shown": "Shown from safe refs in the local CRM relationship read model.",
        "source_refs": [source_ref],
        "evidence_refs": [f"evidence-ref:crm-local:{_safe_suffix(suffix)}"],
        "memory_provenance_refs": [f"memory-ref:crm-local:{_safe_suffix(suffix)}"],
        "proof_refs": [f"proof-ref:crm-local:{_safe_suffix(suffix)}"],
        "stale_conflict_posture": stale,
    }


def _follow_up(
    suffix: str,
    relationship_ref: str,
    status: str,
    priority: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "follow_up_ref": f"follow-up-ref:crm-local:{suffix}",
        "relationship_ref": relationship_ref,
        "status": status,
        "priority": priority,
        "due_ref": f"due-ref:crm-local:{_safe_suffix(suffix)}",
        "safe_summary": summary,
        "reason_refs": [f"reason-ref:crm-local:{_safe_suffix(suffix)}"],
        "evidence_refs": [f"evidence-ref:crm-local:{_safe_suffix(suffix)}"],
        "memory_provenance_refs": [f"memory-ref:crm-local:{_safe_suffix(suffix)}"],
        "opportunity_refs": [],
        "action_inbox_handoff_proposal_ref": (
            f"proposal-ref:crm-local:action-inbox:{_safe_suffix(suffix)}"
        ),
    }


def _build_deal_stage_summary(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    stage_labels = {
        "stage-ref:crm-local:operator:new": "New",
        "stage-ref:crm-local:operator:qualified": "Qualified",
        "stage-ref:crm-local:operator:needs-review": "Needs Review",
        "stage-ref:crm-local:operator:blocked": "Blocked",
    }
    stages = []
    for stage_ref, label in stage_labels.items():
        stages.append(
            {
                "stage_ref": stage_ref,
                "safe_label": label,
                "opportunity_refs": [
                    str(item["opportunity_ref"])
                    for item in opportunities
                    if item.get("stage_ref") == stage_ref
                ],
            }
        )
    return {
        "pipeline_ref": "pipeline-ref:crm-local:operator",
        "safe_label": "Operator relationship pipeline",
        "stages": stages,
        "opportunity_refs": [str(item["opportunity_ref"]) for item in opportunities],
        "evidence_refs": ["evidence-ref:crm-local:pipeline"],
    }


def _build_smart_lists(
    relationships: list[dict[str, Any]],
    follow_ups: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rels = [str(item["relationship_ref"]) for item in relationships]
    due_followups = [
        str(item["follow_up_ref"])
        for item in follow_ups
        if item.get("status") in {"due", "stale", "proposed"}
    ]
    at_risk = [
        str(item["opportunity_ref"])
        for item in opportunities
        if item.get("stage_ref") == "stage-ref:crm-local:operator:needs-review"
    ]
    specs = [
        ("stale-promises", "Stale promises", rels[1:], due_followups[1:], []),
        ("warm-relationships", "Warm relationships", rels[:1], due_followups[:1], []),
        ("needs-follow-up", "Needs follow-up", rels, due_followups, []),
        ("high-context-contacts", "High-context contacts", rels[:1], [], []),
        ("unanswered-outreach", "Unanswered outreach", rels[1:], [], []),
        ("opportunity-at-risk", "Opportunity at risk", rels[1:], [], at_risk),
        ("needs-evidence", "Needs evidence", rels[1:], [], at_risk),
        (
            "ready-for-action-inbox",
            "Ready for Action Inbox",
            rels[:1],
            due_followups[:1],
            [],
        ),
        ("blocked-external-sync", "Blocked external sync", rels, [], []),
        ("recently-changed", "Recently changed", rels, due_followups, []),
    ]
    return [
        {
            "smart_list_ref": f"smart-list-ref:crm-local:{suffix}",
            "safe_label": label,
            "membership_rule_ref": f"rule-ref:crm-local:smart-list:{suffix}",
            "explanation": f"Deterministic membership for {label.lower()} using safe refs only.",
            "relationship_refs": relationship_refs,
            "follow_up_refs": follow_up_refs,
            "opportunity_refs": opportunity_refs,
            "evidence_refs": [f"evidence-ref:crm-local:smart-list:{suffix}"],
        }
        for suffix, label, relationship_refs, follow_up_refs, opportunity_refs in specs
    ]


def _report(suffix: str, label: str, value: str) -> dict[str, Any]:
    return {
        "report_ref": f"report-ref:crm-local:{suffix}",
        "safe_label": label,
        "value_label": value,
        "freshness_ref": f"freshness-ref:crm-local:{suffix}",
        "drilldown_refs": [f"drilldown-ref:crm-local:{suffix}"],
        "evidence_refs": [f"evidence-ref:crm-local:report:{suffix}"],
    }


def _apply_mutation(
    state: dict[str, Any],
    request: CrmLocalMutationRequest,
    receipt: CrmLocalMutationReceipt,
) -> None:
    if request.mutation_kind == "mark_follow_up_complete":
        _update_follow_up_status(state, request.target_ref, "completed")
    elif request.mutation_kind == "update_follow_up":
        _update_follow_up_status(
            state,
            request.target_ref,
            request.follow_up_status or "proposed",
        )
    elif request.mutation_kind == "create_follow_up":
        relationship_ref = (
            request.relationship_ref or "relationship-ref:crm-local:alpha"
        )
        state.setdefault("follow_ups", []).append(
            _follow_up(
                f"created:{_safe_suffix(request.target_ref)}",
                relationship_ref,
                request.follow_up_status or "proposed",
                "medium",
                request.safe_summary,
            )
        )
    elif request.mutation_kind == "move_opportunity_stage":
        for item in state.get("opportunities", []):
            if item.get("opportunity_ref") == request.target_ref:
                item["stage_ref"] = request.stage_ref or item["stage_ref"]
                item["stage_label"] = _safe_label_from_ref(str(item["stage_ref"]))
        state["pipelines"] = _rebuild_pipelines(state)
    elif request.mutation_kind == "add_note_summary_ref":
        relationship_ref = request.relationship_ref or request.target_ref
        state.setdefault("timeline_events", []).append(
            _timeline(
                f"note:{_safe_suffix(receipt.mutation_ref)}",
                relationship_ref,
                "note_ref",
                request.safe_summary,
                receipt.proof_ref,
            )
        )
    elif request.mutation_kind in {
        "select_social_context",
        "clear_social_context",
    }:
        for person in state.get("people", []):
            if person.get("person_ref") != request.target_ref:
                continue
            tags = list(person.get("tags", []))
            if request.mutation_kind == "select_social_context":
                if CRM_SOCIAL_RELATIONSHIP_TAG not in tags:
                    tags.append(CRM_SOCIAL_RELATIONSHIP_TAG)
            else:
                tags = [tag for tag in tags if tag != CRM_SOCIAL_RELATIONSHIP_TAG]
            person["tags"] = tags
            break
        else:
            raise CrmLocalCommandCenterError("CRM_LOCAL_PERSON_NOT_FOUND")
    else:
        raise CrmLocalCommandCenterError("CRM_LOCAL_MUTATION_UNSUPPORTED")


def _update_follow_up_status(
    state: dict[str, Any],
    follow_up_ref: str,
    status: str,
) -> None:
    for item in state.get("follow_ups", []):
        if item.get("follow_up_ref") == follow_up_ref:
            item["status"] = status
            return
    raise CrmLocalCommandCenterError("CRM_LOCAL_FOLLOW_UP_NOT_FOUND")


def _rebuild_pipelines(state: dict[str, Any]) -> list[dict[str, Any]]:
    opportunities = [dict(item) for item in state.get("opportunities", [])]
    return [_build_deal_stage_summary(opportunities)] if opportunities else []


def _local_mutation_payload_fingerprint_ref(
    request: CrmLocalMutationRequest,
) -> str:
    return _payload_fingerprint_ref(
        {
            "contract_ref": CRM_LOCAL_MUTATION_CONTRACT_REF,
            "mutation_kind": request.mutation_kind,
            "target_ref": request.target_ref,
            "relationship_ref": request.relationship_ref,
            "follow_up_status": request.follow_up_status,
            "stage_ref": request.stage_ref,
            "safe_summary": request.safe_summary,
            "metadata_refs": sorted(request.metadata_refs),
            "approval_ref": request.approval_ref,
        }
    )


def _crm_local_mutation_resource_refs(
    *,
    request: CrmLocalMutationRequest,
    idempotency_ref: str,
    payload_fingerprint_ref: str,
) -> list[str]:
    resource_refs = [
        request.target_ref,
        f"mutation-kind-ref:crm-local:{request.mutation_kind}",
        CRM_LOCAL_MUTATION_CONTRACT_REF,
        idempotency_ref,
        payload_fingerprint_ref,
        request.approval_ref,
    ]
    if request.relationship_ref:
        resource_refs.append(request.relationship_ref)
    if request.stage_ref:
        resource_refs.append(request.stage_ref)
    resource_refs.extend(request.metadata_refs)
    return resource_refs


def _crm_local_mutation_lease_issue_request(
    *,
    request: CrmLocalMutationRequest,
    idempotency_ref: str,
    payload_fingerprint_ref: str,
) -> AuthorityLeaseIssueRequest:
    resource_refs = _crm_local_mutation_resource_refs(
        request=request,
        idempotency_ref=idempotency_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    constraint_suffix = hashlib.sha256(
        payload_fingerprint_ref.encode("utf-8")
    ).hexdigest()[:24]
    return AuthorityLeaseIssueRequest(
        mode=TrustMode.ask_before_changes,
        scope=AuthorityLeaseScope.session,
        requested_domains={
            AuthorityDomain.contacts: [AuthorityCapability.write],
        },
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=(
                    f"authority-constraint-ref:crm-local:resources:{constraint_suffix}"
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=resource_refs,
                safe_summary=(
                    "Restrict one confirmed CRM mutation to its exact local "
                    "target, kind, approval, idempotency, and payload refs."
                ),
            ),
            AuthorityConstraint(
                constraint_ref=(
                    "authority-constraint-ref:crm-local:operation-budget:"
                    f"{constraint_suffix}"
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact confirmed local CRM mutation.",
            ),
        ],
        constraints={
            "exact_lane_ref": CRM_LOCAL_MUTATION_AUTHORITY_LANE_REF,
            "exact_action_ref": CRM_LOCAL_MUTATION_AUTHORITY_ACTION_REF,
            "exact_route_ref": CRM_LOCAL_MUTATION_ROUTE_REF,
            "exact_contract_ref": CRM_LOCAL_MUTATION_CONTRACT_REF,
            "exact_target_ref": request.target_ref,
            "exact_mutation_kind_ref": (
                f"mutation-kind-ref:crm-local:{request.mutation_kind}"
            ),
            "exact_idempotency_ref": idempotency_ref,
            "exact_payload_fingerprint_ref": payload_fingerprint_ref,
            "exact_approval_ref": request.approval_ref,
            "exact_safe_disable_ref": CRM_LOCAL_MUTATION_SAFE_DISABLE_REF,
        },
        decision_reason_ref=(
            "decision-reason-ref:crm-local-mutation:operator-confirmed"
        ),
        duration_minutes=5,
        safe_summary="Issue one exact operator-confirmed local CRM mutation lease.",
    )


def _validate_local_mutation_approval(
    *,
    request: CrmLocalMutationRequest,
    idempotency_ref: str,
    approval_authority: LocalApprovalAuthority | None,
) -> tuple[str, list[str]]:
    approval_request = crm_local_mutation_approval_request(
        request=request,
        idempotency_ref=idempotency_ref,
    )
    expected_ref = expected_crm_local_mutation_approval_ref(
        target_ref=request.target_ref,
        idempotency_ref=idempotency_ref,
    )
    if request.approval_ref != expected_ref:
        return "denied", ["approval-reason-ref:crm-local:approval-ref-mismatch"]
    authority = approval_authority or LocalApprovalAuthority()
    authority.create_request(approval_request)
    decision = authority.validate_for_request(approval_request, request.approval_ref)
    status = getattr(decision.status, "value", str(decision.status))
    reason_refs = [
        f"approval-reason-ref:crm-local:{_safe_suffix(str(reason))}"
        for reason in decision.reason_codes
    ]
    return str(status), reason_refs


def _find_replay(state: dict[str, Any], idempotency_ref: str) -> dict[str, Any] | None:
    for item in state.get("mutation_replays", []):
        if item.get("idempotency_ref") == idempotency_ref:
            return dict(item)
    return None


def _find_receipt(state: dict[str, Any], receipt_ref: str) -> dict[str, Any]:
    for item in state.get("mutation_receipts", []):
        if item.get("receipt_ref") == receipt_ref:
            return dict(item)
    raise CrmLocalCommandCenterError("CRM_LOCAL_MUTATION_RECEIPT_NOT_FOUND")


def _payload_fingerprint_ref(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"payload-fingerprint-ref:crm-local:{digest}"


def _hashed_ref(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _crm_local_derived_ref(prefix: str, *values: str) -> str:
    canonical = json.dumps(values, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _safe_suffix(value: str) -> str:
    suffix = SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _safe_label_from_ref(ref: str) -> str:
    label = ref.rsplit(":", 1)[-1].replace("-", " ").replace("_", " ").title()
    _validate_safe_text(label, "stage_label")
    return label


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        _validate_no_private_or_secret_text(value, field_name)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for item in value.values():
            _validate_safe_payload(item, field_name)
        return
