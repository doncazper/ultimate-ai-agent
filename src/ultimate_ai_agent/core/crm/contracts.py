from __future__ import annotations

from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


CRM_COMMUNICATIONS_SPINE_CONTRACT_REF = (
    "contract-ref:crm-communications-spine-m0:v1"
)
CRM_COMMUNICATIONS_SPINE_DOC_REF = (
    "docs-ref:crm-communications-spine-m0-contracts"
)
CRM_COMMUNICATIONS_SPINE_VERIFIER_REF = (
    "script-ref:verify-crm-communications-spine-m0"
)

CRM_COMMUNICATIONS_SPINE_LOCKED_ARCHITECTURE = [
    "global_identity",
    "workspace_context",
    "pipeline_object",
    "communications_spine",
    "work_queue_or_proposal",
    "action_inbox_evidence_memory",
]

CRM_COMMUNICATIONS_CANONICAL_NOUNS = [
    "Person",
    "Organization",
    "Workspace",
    "WorkspaceContext",
    "Relationship",
    "PipelineObject",
    "Activity",
    "CommunicationItem",
    "WorkQueue",
    "GovernedPlaybook",
    "EngagementSignal",
    "IdentityMatchCandidate",
    "CrmProposal",
    "ApprovalRecord",
    "EvidenceRef",
    "MemoryProvenance",
    "PresetPack",
]

CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS = [
    "mock_only",
    "fixture_only",
    "read_only",
    "proposal_only",
    "blocked",
    "implemented",
]

CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS = [
    "blocked-state-ref:crm-comms-m0:no-connector-writes",
    "blocked-state-ref:crm-comms-m0:no-email-or-message-sends",
    "blocked-state-ref:crm-comms-m0:no-calendar-writes",
    "blocked-state-ref:crm-comms-m0:no-silent-identity-merge",
    "blocked-state-ref:crm-comms-m0:no-silent-contact-creation",
    "blocked-state-ref:crm-comms-m0:no-provider-model-calls",
    "blocked-state-ref:crm-comms-m0:no-live-web-or-browser-runtime",
    "blocked-state-ref:crm-comms-m0:no-account-sync",
    "blocked-state-ref:crm-comms-m0:no-backend-crm-route-or-runtime-ui-authority",
]

SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:;()+#&%_'-]{0,799}$")
RAW_PATH_FRAGMENT_RE = re.compile(
    r"(?i)(^|[\s\"'`])(~[/\\]?|/(Users|home|usr|var|private|tmp|etc)(/|$)|"
    r"[A-Z]:[\\/]|\\\\[^\\\s]+\\)"
)
FORBIDDEN_KEY_RE = re.compile(
    r"(raw|prompt|response|provider[_-]?(payload|exchange|content)|"
    r"source[_-]?(body|text|content)|message[_-]?body|email[_-]?body|"
    r"calendar[_-]?body|transcript|path|local[_-]?path|log|username|"
    r"hostname|environment|env[_-]?dump|credential|password|token|secret|"
    r"api[_-]?key|authorization|bearer|oauth|session|cookie|account[_-]?id|"
    r"mailbox|phone|address|contact[_-]?details)",
    re.IGNORECASE,
)
FORBIDDEN_VALUE_RE = re.compile(
    r"(@|/users/|/home/|/var/|/private/|/tmp/|/etc/|[a-z]:\\|"
    r"\braw[_ -]?(prompt|response|transcript)\b|\bprompt\s*:|"
    r"\bresponse\s*:|\bprovider[_ -]?(payload|exchange|content)\b|"
    r"\bsource[_ -]?(body|text|content)\b|\bmessage\s+body\b|"
    r"\bemail\s+body\b|\bcalendar\s+body\b|\blog\s*:|\busername\s*:|"
    r"\bhostname\s*:|\benv(?:ironment)?[_ -]?dump\b|api[_-]?key|"
    r"password|token|secret|bearer|oauth|cookie)",
    re.IGNORECASE,
)


class CrmImplementationState(str, Enum):
    mock_only = "mock_only"
    fixture_only = "fixture_only"
    read_only = "read_only"
    proposal_only = "proposal_only"
    blocked = "blocked"
    implemented = "implemented"


class CrmAuthorityMode(str, Enum):
    metadata_only = "metadata_only"
    fixture_only = "fixture_only"
    read_only = "read_only"
    proposal_only = "proposal_only"
    blocked = "blocked"


class CrmWorkspaceKind(str, Enum):
    real_estate = "real_estate"
    finance_insurance = "finance_insurance"
    healthcare = "healthcare"
    retail_ecommerce = "retail_ecommerce"
    professional_services = "professional_services"


class CrmCommunicationKind(str, Enum):
    email = "email"
    text = "text"
    call = "call"
    calendar = "calendar"
    message = "message"
    note = "note"
    reminder = "reminder"


class CrmProposalKind(str, Enum):
    record_update = "record_update"
    identity_merge = "identity_merge"
    workspace_link = "workspace_link"
    communication_attach = "communication_attach"
    follow_up_task = "follow_up_task"
    pipeline_stage_change = "pipeline_stage_change"
    calendar_draft = "calendar_draft"
    email_draft = "email_draft"
    message_draft = "message_draft"
    playbook_step = "playbook_step"


class CrmApprovalState(str, Enum):
    not_requested = "not_requested"
    required = "required"
    blocked = "blocked"
    proposal_only = "proposal_only"


class _CrmModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CrmAuthorityBoundary(_CrmModel):
    authority_ref: str
    mode: CrmAuthorityMode = CrmAuthorityMode.metadata_only
    route_or_ui_visibility_grants_authority: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    silent_merge_enabled: bool = False
    silent_contact_creation_enabled: bool = False
    provider_model_call_enabled: bool = False
    live_web_enabled: bool = False
    browser_runtime_enabled: bool = False
    model_output_authority_enabled: bool = False
    memory_truth_authority_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmAuthorityBoundary":
        _validate_ref(self.authority_ref, "authority_ref")
        _deny_true_flags(self, CRM_AUTHORITY_DENIALS)
        return self


class CrmEvidenceRef(_CrmModel):
    evidence_ref: str
    safe_summary: str
    source_posture: CrmImplementationState = CrmImplementationState.fixture_only
    safe_refs_only: bool = True
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    raw_provider_exchange_included: bool = False
    raw_source_body_included: bool = False
    raw_log_included: bool = False
    raw_path_included: bool = False
    private_material_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmEvidenceRef":
        _validate_ref(self.evidence_ref, "evidence_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if not self.safe_refs_only:
            raise ValueError("CRM_EVIDENCE_SAFE_REFS_REQUIRED")
        _deny_true_flags(self, CRM_EVIDENCE_DENIALS)
        return self


class CrmMemoryProvenance(_CrmModel):
    memory_ref: str
    review_state: str = "reviewed_recall_only"
    evidence_refs: list[str]
    source_refs: list[str] = Field(default_factory=list)
    memory_is_recall_not_truth: bool = True
    context_injection_enabled: bool = False
    automatic_memory_write_enabled: bool = False
    raw_memory_content_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmMemoryProvenance":
        _validate_ref(self.memory_ref, "memory_ref")
        _validate_safe_text(self.review_state, "review_state", max_chars=80)
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if self.source_refs:
            _validate_ref_list(self.source_refs, "source_refs")
        if not self.memory_is_recall_not_truth:
            raise ValueError("CRM_MEMORY_RECALL_NOT_TRUTH_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("context_injection_enabled", "CRM_MEMORY_CONTEXT_INJECTION_DENIED"),
                ("automatic_memory_write_enabled", "CRM_MEMORY_WRITE_DENIED"),
                ("raw_memory_content_included", "CRM_MEMORY_RAW_CONTENT_DENIED"),
            ],
        )
        return self


class CrmPerson(_CrmModel):
    person_ref: str
    safe_display_label: str
    workspace_context_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    global_identity: bool = True
    silent_contact_creation_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPerson":
        _validate_ref(self.person_ref, "person_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label", max_chars=120)
        _validate_optional_ref_list(self.workspace_context_refs, "workspace_context_refs")
        _validate_optional_ref_list(self.evidence_refs, "evidence_refs")
        if not self.global_identity:
            raise ValueError("CRM_PERSON_GLOBAL_IDENTITY_REQUIRED")
        if self.silent_contact_creation_enabled:
            raise ValueError("CRM_PERSON_SILENT_CONTACT_CREATION_DENIED")
        return self


class CrmOrganization(_CrmModel):
    organization_ref: str
    safe_display_label: str
    workspace_context_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    global_identity: bool = True
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmOrganization":
        _validate_ref(self.organization_ref, "organization_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label", max_chars=120)
        _validate_optional_ref_list(self.workspace_context_refs, "workspace_context_refs")
        _validate_optional_ref_list(self.evidence_refs, "evidence_refs")
        if not self.global_identity:
            raise ValueError("CRM_ORGANIZATION_GLOBAL_IDENTITY_REQUIRED")
        if self.account_sync_enabled:
            raise ValueError("CRM_ORGANIZATION_ACCOUNT_SYNC_DENIED")
        return self


class CrmWorkspace(_CrmModel):
    workspace_ref: str
    workspace_kind: CrmWorkspaceKind
    safe_display_label: str
    preset_pack_ref: str
    state: CrmImplementationState = CrmImplementationState.fixture_only
    hard_boundary: bool = True
    authority: CrmAuthorityBoundary

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmWorkspace":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_safe_text(self.safe_display_label, "safe_display_label", max_chars=120)
        _validate_ref(self.preset_pack_ref, "preset_pack_ref")
        if not self.hard_boundary:
            raise ValueError("CRM_WORKSPACE_HARD_BOUNDARY_REQUIRED")
        return self


class CrmWorkspaceContext(_CrmModel):
    context_ref: str
    workspace_ref: str
    subject_ref: str
    role_ref: str
    field_schema_ref: str
    permission_scope_ref: str
    owner_ref: str
    terminology_ref: str
    state: CrmImplementationState = CrmImplementationState.fixture_only
    workspace_boundary_enforced: bool = True
    grants_runtime_authority: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmWorkspaceContext":
        for field_name in [
            "context_ref",
            "workspace_ref",
            "subject_ref",
            "role_ref",
            "field_schema_ref",
            "permission_scope_ref",
            "owner_ref",
            "terminology_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        if not self.workspace_boundary_enforced:
            raise ValueError("CRM_WORKSPACE_CONTEXT_BOUNDARY_REQUIRED")
        if self.grants_runtime_authority:
            raise ValueError("CRM_WORKSPACE_CONTEXT_AUTHORITY_DENIED")
        return self


class CrmRelationship(_CrmModel):
    relationship_ref: str
    person_ref: str
    organization_ref: str | None = None
    workspace_context_refs: list[str]
    evidence_refs: list[str]
    memory_provenance_refs: list[str] = Field(default_factory=list)
    why_shown_ref: str
    relationship_graph_only: bool = True

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmRelationship":
        _validate_ref(self.relationship_ref, "relationship_ref")
        _validate_ref(self.person_ref, "person_ref")
        if self.organization_ref is not None:
            _validate_ref(self.organization_ref, "organization_ref")
        _validate_ref_list(self.workspace_context_refs, "workspace_context_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_optional_ref_list(self.memory_provenance_refs, "memory_provenance_refs")
        _validate_ref(self.why_shown_ref, "why_shown_ref")
        if not self.relationship_graph_only:
            raise ValueError("CRM_RELATIONSHIP_GRAPH_ONLY_REQUIRED")
        return self


class CrmPipelineObject(_CrmModel):
    object_ref: str
    workspace_ref: str
    object_kind_ref: str
    stage_ref: str
    owner_ref: str
    evidence_refs: list[str]
    state: CrmImplementationState = CrmImplementationState.fixture_only
    external_sync_enabled: bool = False
    stage_write_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPipelineObject":
        for field_name in [
            "object_ref",
            "workspace_ref",
            "object_kind_ref",
            "stage_ref",
            "owner_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _deny_true_flags(
            self,
            [
                ("external_sync_enabled", "CRM_PIPELINE_EXTERNAL_SYNC_DENIED"),
                ("stage_write_enabled", "CRM_PIPELINE_STAGE_WRITE_DENIED"),
            ],
        )
        return self


class CrmActivity(_CrmModel):
    activity_ref: str
    activity_kind_ref: str
    related_record_refs: list[str]
    evidence_refs: list[str]
    state: CrmImplementationState = CrmImplementationState.fixture_only
    mutation_performed: bool = False
    raw_source_content_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmActivity":
        _validate_ref(self.activity_ref, "activity_ref")
        _validate_ref(self.activity_kind_ref, "activity_kind_ref")
        _validate_ref_list(self.related_record_refs, "related_record_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _deny_true_flags(
            self,
            [
                ("mutation_performed", "CRM_ACTIVITY_MUTATION_DENIED"),
                ("raw_source_content_included", "CRM_ACTIVITY_RAW_SOURCE_DENIED"),
            ],
        )
        return self


class CrmCommunicationItem(_CrmModel):
    communication_ref: str
    communication_kind: CrmCommunicationKind
    safe_subject_ref: str
    source_posture_ref: str
    person_refs: list[str] = Field(default_factory=list)
    organization_refs: list[str] = Field(default_factory=list)
    workspace_context_refs: list[str] = Field(default_factory=list)
    pipeline_object_refs: list[str] = Field(default_factory=list)
    work_queue_refs: list[str] = Field(default_factory=list)
    next_action_ref: str | None = None
    evidence_refs: list[str]
    approval_state: CrmApprovalState = CrmApprovalState.proposal_only
    metadata_only: bool = True
    raw_body_included: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    connector_read_performed: bool = False
    connector_write_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmCommunicationItem":
        _validate_ref(self.communication_ref, "communication_ref")
        _validate_ref(self.safe_subject_ref, "safe_subject_ref")
        _validate_ref(self.source_posture_ref, "source_posture_ref")
        for field_name in [
            "person_refs",
            "organization_refs",
            "workspace_context_refs",
            "pipeline_object_refs",
            "work_queue_refs",
        ]:
            _validate_optional_ref_list(getattr(self, field_name), field_name)
        if self.next_action_ref is not None:
            _validate_ref(self.next_action_ref, "next_action_ref")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        if not self.metadata_only:
            raise ValueError("CRM_COMMUNICATION_METADATA_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("raw_body_included", "CRM_COMMUNICATION_RAW_BODY_DENIED"),
                ("send_enabled", "CRM_COMMUNICATION_SEND_DENIED"),
                ("calendar_write_enabled", "CRM_COMMUNICATION_CALENDAR_WRITE_DENIED"),
                ("connector_read_performed", "CRM_COMMUNICATION_CONNECTOR_READ_DENIED"),
                ("connector_write_enabled", "CRM_COMMUNICATION_CONNECTOR_WRITE_DENIED"),
            ],
        )
        return self


class CrmWorkQueue(_CrmModel):
    queue_ref: str
    workspace_ref: str
    smart_view_ref: str
    item_refs: list[str]
    priority_reason_refs: list[str]
    state: CrmImplementationState = CrmImplementationState.fixture_only
    review_only: bool = True
    automatic_task_creation_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmWorkQueue":
        _validate_ref(self.queue_ref, "queue_ref")
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.smart_view_ref, "smart_view_ref")
        _validate_ref_list(self.item_refs, "item_refs")
        _validate_ref_list(self.priority_reason_refs, "priority_reason_refs")
        if not self.review_only:
            raise ValueError("CRM_WORK_QUEUE_REVIEW_ONLY_REQUIRED")
        if self.automatic_task_creation_enabled:
            raise ValueError("CRM_WORK_QUEUE_TASK_CREATION_DENIED")
        return self


class CrmGovernedPlaybook(_CrmModel):
    playbook_ref: str
    workspace_ref: str
    template_ref: str
    proposal_kinds: list[CrmProposalKind]
    state: CrmImplementationState = CrmImplementationState.proposal_only
    proposal_only: bool = True
    external_action_execution_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmGovernedPlaybook":
        _validate_ref(self.playbook_ref, "playbook_ref")
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.template_ref, "template_ref")
        if not self.proposal_kinds:
            raise ValueError("CRM_PLAYBOOK_PROPOSAL_KINDS_REQUIRED")
        if not self.proposal_only:
            raise ValueError("CRM_PLAYBOOK_PROPOSAL_ONLY_REQUIRED")
        if self.external_action_execution_enabled:
            raise ValueError("CRM_PLAYBOOK_EXECUTION_DENIED")
        return self


class CrmEngagementSignal(_CrmModel):
    signal_ref: str
    workspace_ref: str
    signal_kind_ref: str
    related_record_refs: list[str]
    evidence_refs: list[str]
    safe_summary: str
    source_metadata_only: bool = True
    raw_event_payload_included: bool = False
    live_tracking_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmEngagementSignal":
        _validate_ref(self.signal_ref, "signal_ref")
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.signal_kind_ref, "signal_kind_ref")
        _validate_ref_list(self.related_record_refs, "related_record_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if not self.source_metadata_only:
            raise ValueError("CRM_SIGNAL_METADATA_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("raw_event_payload_included", "CRM_SIGNAL_RAW_PAYLOAD_DENIED"),
                ("live_tracking_enabled", "CRM_SIGNAL_LIVE_TRACKING_DENIED"),
            ],
        )
        return self


class CrmIdentityMatchCandidate(_CrmModel):
    candidate_ref: str
    candidate_kind_ref: str
    subject_refs: list[str]
    evidence_refs: list[str]
    confidence_posture: str = "review_required_before_identity_change"
    review_only: bool = True
    merge_execution_enabled: bool = False
    silent_contact_creation_enabled: bool = False
    account_sync_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmIdentityMatchCandidate":
        _validate_ref(self.candidate_ref, "candidate_ref")
        _validate_ref(self.candidate_kind_ref, "candidate_kind_ref")
        _validate_ref_list(self.subject_refs, "subject_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_safe_text(self.confidence_posture, "confidence_posture")
        if not self.review_only:
            raise ValueError("CRM_IDENTITY_MATCH_REVIEW_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("merge_execution_enabled", "CRM_IDENTITY_MERGE_EXECUTION_DENIED"),
                ("silent_contact_creation_enabled", "CRM_IDENTITY_CONTACT_CREATION_DENIED"),
                ("account_sync_enabled", "CRM_IDENTITY_ACCOUNT_SYNC_DENIED"),
            ],
        )
        return self


class CrmApprovalRecord(_CrmModel):
    approval_ref: str
    approval_state: CrmApprovalState = CrmApprovalState.required
    scope_ref: str
    evidence_refs: list[str]
    approval_ref_grants_execution: bool = False
    exact_scope_validated: bool = False
    execution_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmApprovalRecord":
        _validate_ref(self.approval_ref, "approval_ref")
        _validate_ref(self.scope_ref, "scope_ref")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _deny_true_flags(
            self,
            [
                ("approval_ref_grants_execution", "CRM_APPROVAL_REF_AUTHORITY_DENIED"),
                ("exact_scope_validated", "CRM_APPROVAL_SCOPE_RUNTIME_DENIED"),
                ("execution_enabled", "CRM_APPROVAL_EXECUTION_DENIED"),
            ],
        )
        return self


class CrmProposal(_CrmModel):
    proposal_ref: str
    proposal_kind: CrmProposalKind
    scope_ref: str
    idempotency_ref: str
    evidence_refs: list[str]
    expected_receipt_ref: str
    blocked_authority_refs: list[str]
    rollback_posture: str = "rollback_requires_later_exact_write_lane"
    safe_disable_posture: str = "safe_disable_is_blocked_state_only"
    approval_required: bool = True
    proposal_only: bool = True
    execution_enabled: bool = False
    external_write_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    silent_merge_enabled: bool = False
    silent_contact_creation_enabled: bool = False
    connector_runtime_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmProposal":
        for field_name in [
            "proposal_ref",
            "scope_ref",
            "idempotency_ref",
            "expected_receipt_ref",
        ]:
            _validate_ref(getattr(self, field_name), field_name)
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_safe_text(self.rollback_posture, "rollback_posture")
        _validate_safe_text(self.safe_disable_posture, "safe_disable_posture")
        if not self.approval_required:
            raise ValueError("CRM_PROPOSAL_APPROVAL_REQUIRED")
        if not self.proposal_only:
            raise ValueError("CRM_PROPOSAL_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("execution_enabled", "CRM_PROPOSAL_EXECUTION_DENIED"),
                ("external_write_enabled", "CRM_PROPOSAL_EXTERNAL_WRITE_DENIED"),
                ("send_enabled", "CRM_PROPOSAL_SEND_DENIED"),
                ("calendar_write_enabled", "CRM_PROPOSAL_CALENDAR_WRITE_DENIED"),
                ("silent_merge_enabled", "CRM_PROPOSAL_SILENT_MERGE_DENIED"),
                ("silent_contact_creation_enabled", "CRM_PROPOSAL_CONTACT_CREATION_DENIED"),
                ("connector_runtime_enabled", "CRM_PROPOSAL_CONNECTOR_RUNTIME_DENIED"),
            ],
        )
        return self


class CrmPresetPack(_CrmModel):
    preset_pack_ref: str
    workspace_kind: CrmWorkspaceKind
    version_ref: str
    nav_ref: str
    object_kind_refs: list[str]
    work_queue_refs: list[str]
    pipeline_refs: list[str]
    inspector_section_refs: list[str]
    fixture_only: bool = True
    customization_runtime_enabled: bool = False
    import_export_enabled: bool = False
    schema_migration_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmPresetPack":
        for field_name in ["preset_pack_ref", "version_ref", "nav_ref"]:
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in [
            "object_kind_refs",
            "work_queue_refs",
            "pipeline_refs",
            "inspector_section_refs",
        ]:
            _validate_ref_list(getattr(self, field_name), field_name)
        if not self.fixture_only:
            raise ValueError("CRM_PRESET_FIXTURE_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("customization_runtime_enabled", "CRM_PRESET_CUSTOMIZATION_DENIED"),
                ("import_export_enabled", "CRM_PRESET_IMPORT_EXPORT_DENIED"),
                ("schema_migration_enabled", "CRM_PRESET_SCHEMA_MIGRATION_DENIED"),
            ],
        )
        return self


class CrmCommunicationsSpineContract(_CrmModel):
    contract_ref: str = CRM_COMMUNICATIONS_SPINE_CONTRACT_REF
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            CRM_COMMUNICATIONS_SPINE_DOC_REF,
            CRM_COMMUNICATIONS_SPINE_VERIFIER_REF,
        ]
    )
    canonical_nouns: list[str] = Field(
        default_factory=lambda: list(CRM_COMMUNICATIONS_CANONICAL_NOUNS)
    )
    locked_architecture: list[str] = Field(
        default_factory=lambda: list(CRM_COMMUNICATIONS_SPINE_LOCKED_ARCHITECTURE)
    )
    state_words: list[str] = Field(
        default_factory=lambda: list(CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS)
    )
    preset_packs: list[CrmPresetPack]
    authority: CrmAuthorityBoundary
    sample_evidence_refs: list[CrmEvidenceRef]
    sample_memory_provenance: list[CrmMemoryProvenance]
    sample_proposals: list[CrmProposal]
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS)
    )
    m0_contract_only: bool = True
    backend_routes_added: bool = False
    control_center_route_added: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    send_enabled: bool = False
    calendar_write_enabled: bool = False
    silent_merge_enabled: bool = False
    silent_contact_creation_enabled: bool = False
    provider_model_call_enabled: bool = False
    live_web_enabled: bool = False
    browser_runtime_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> "CrmCommunicationsSpineContract":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref_list(self.docs_refs, "docs_refs")
        _validate_string_set(
            self.canonical_nouns,
            CRM_COMMUNICATIONS_CANONICAL_NOUNS,
            "CRM_CANONICAL_NOUNS_REQUIRED",
        )
        _validate_string_set(
            self.locked_architecture,
            CRM_COMMUNICATIONS_SPINE_LOCKED_ARCHITECTURE,
            "CRM_LOCKED_ARCHITECTURE_REQUIRED",
        )
        _validate_string_set(
            self.state_words,
            CRM_COMMUNICATIONS_REQUIRED_STATE_WORDS,
            "CRM_STATE_WORDS_REQUIRED",
        )
        if {preset.workspace_kind for preset in self.preset_packs} != set(CrmWorkspaceKind):
            raise ValueError("CRM_PRESET_PACKS_REQUIRED")
        if len(self.preset_packs) != len(set(preset.workspace_kind for preset in self.preset_packs)):
            raise ValueError("CRM_PRESET_PACK_DUPLICATE_DENIED")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        for ref in CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("CRM_BLOCKED_AUTHORITY_REFS_REQUIRED")
        if not self.sample_evidence_refs:
            raise ValueError("CRM_SAMPLE_EVIDENCE_REQUIRED")
        if not self.sample_memory_provenance:
            raise ValueError("CRM_SAMPLE_MEMORY_PROVENANCE_REQUIRED")
        if not self.sample_proposals:
            raise ValueError("CRM_SAMPLE_PROPOSALS_REQUIRED")
        if not self.m0_contract_only:
            raise ValueError("CRM_M0_CONTRACT_ONLY_REQUIRED")
        _deny_true_flags(self, CRM_CONTRACT_DENIALS)
        return self


def build_crm_communications_spine_contract() -> CrmCommunicationsSpineContract:
    evidence = CrmEvidenceRef(
        evidence_ref="evidence-ref:crm-comms-m0:fixture-only-contract",
        safe_summary=(
            "CRM communications spine M0 defines safe refs and fixtures only."
        ),
    )
    memory = CrmMemoryProvenance(
        memory_ref="memory-ref:crm-comms-m0:reviewed-recall-only",
        evidence_refs=[evidence.evidence_ref],
        source_refs=["source-ref:crm-comms-m0:contract-fixture"],
    )
    return CrmCommunicationsSpineContract(
        preset_packs=[_preset_pack(kind) for kind in CrmWorkspaceKind],
        authority=CrmAuthorityBoundary(
            authority_ref="authority-ref:crm-comms-m0:metadata-only",
            mode=CrmAuthorityMode.metadata_only,
        ),
        sample_evidence_refs=[evidence],
        sample_memory_provenance=[memory],
        sample_proposals=[
            CrmProposal(
                proposal_ref="proposal-ref:crm-comms-m0:follow-up-task",
                proposal_kind=CrmProposalKind.follow_up_task,
                scope_ref="scope-ref:crm-comms-m0:review-only-follow-up",
                idempotency_ref="idempotency-ref:crm-comms-m0:follow-up-task",
                evidence_refs=[evidence.evidence_ref],
                expected_receipt_ref="receipt-ref:crm-comms-m0:proposal-reviewed",
                blocked_authority_refs=list(CRM_COMMUNICATIONS_REQUIRED_DENIAL_REFS),
            )
        ],
    )


def validate_crm_communications_spine_contract(
    contract: CrmCommunicationsSpineContract | dict[str, Any],
) -> CrmCommunicationsSpineContract:
    payload = _payload(contract)
    _reject_private_payload(
        payload,
        allowed_keys=CRM_ALLOWED_SAFETY_KEYS,
    )
    validated = CrmCommunicationsSpineContract.model_validate(payload)
    _reject_private_payload(
        validated.model_dump(mode="python"),
        allowed_keys=CRM_ALLOWED_SAFETY_KEYS,
    )
    return validated


def _preset_pack(kind: CrmWorkspaceKind) -> CrmPresetPack:
    ref_suffix = kind.value.replace("_", "-")
    return CrmPresetPack(
        preset_pack_ref=f"preset-pack-ref:crm-comms-m0:{ref_suffix}",
        workspace_kind=kind,
        version_ref="preset-version-ref:crm-comms-m0:v1",
        nav_ref=f"nav-ref:crm-comms-m0:{ref_suffix}",
        object_kind_refs=[f"object-kind-ref:crm-comms-m0:{ref_suffix}:primary"],
        work_queue_refs=[f"work-queue-ref:crm-comms-m0:{ref_suffix}:daily"],
        pipeline_refs=[f"pipeline-ref:crm-comms-m0:{ref_suffix}:primary"],
        inspector_section_refs=[
            f"inspector-section-ref:crm-comms-m0:{ref_suffix}:relationship-graph",
            f"inspector-section-ref:crm-comms-m0:{ref_suffix}:evidence",
        ],
    )


def _payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if isinstance(value, dict):
        return dict(value)
    raise ValueError("CRM_CONTRACT_PAYLOAD_REQUIRED")


def _validate_ref(value: str, field_name: str) -> str:
    _validate_no_private_or_secret_text(value, field_name)
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_REF")
    return value


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    if not refs:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    for ref in refs:
        _validate_ref(ref, field_name)


def _validate_optional_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        _validate_ref(ref, field_name)


def _validate_safe_text(value: str, field_name: str, max_chars: int = 800) -> str:
    _validate_no_private_or_secret_text(value, field_name)
    if len(value) > max_chars:
        raise ValueError(f"{field_name.upper()}_TOO_LONG")
    if not SAFE_TEXT_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_TEXT")
    return value


def _validate_string_set(values: list[str], required: list[str], reason: str) -> None:
    if set(values) != set(required):
        raise ValueError(reason)
    if len(values) != len(set(values)):
        raise ValueError(reason)
    for value in values:
        _validate_safe_text(value, "canonical_value", max_chars=120)


def _reject_private_payload(
    payload: Any,
    *,
    allowed_keys: set[str] | None = None,
) -> None:
    if _contains_forbidden_key(payload, allowed_keys or set()):
        raise ValueError("CRM_PRIVATE_FIELD_DENIED")
    if _contains_forbidden_value(payload):
        raise ValueError("CRM_PRIVATE_CONTENT_DENIED")
    if contains_obvious_secret(payload):
        raise ValueError("CRM_PRIVATE_CONTENT_DENIED")


def _contains_forbidden_key(payload: Any, allowed_keys: set[str]) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key)
            if key_text not in allowed_keys and FORBIDDEN_KEY_RE.search(key_text):
                return True
            if _contains_forbidden_key(value, allowed_keys):
                return True
    elif isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_key(item, allowed_keys) for item in payload)
    return False


def _contains_forbidden_value(payload: Any) -> bool:
    if isinstance(payload, str):
        return bool(FORBIDDEN_VALUE_RE.search(payload))
    if isinstance(payload, dict):
        return any(_contains_forbidden_value(value) for value in payload.values())
    if isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_value(item) for item in payload)
    return False


def _validate_no_private_or_secret_text(value: str, field_name: str) -> None:
    if FORBIDDEN_VALUE_RE.search(value):
        raise ValueError(f"{field_name.upper()}_PRIVATE_CONTENT_DENIED")
    if RAW_PATH_FRAGMENT_RE.search(value):
        raise ValueError(f"{field_name.upper()}_RAW_PATH_DENIED")
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")


def _deny_true_flags(model: Any, flags: list[tuple[str, str]]) -> None:
    for field_name, reason in flags:
        if getattr(model, field_name):
            raise ValueError(reason)


CRM_AUTHORITY_DENIALS = [
    ("route_or_ui_visibility_grants_authority", "CRM_AUTHORITY_VISIBILITY_DENIED"),
    ("connector_runtime_enabled", "CRM_AUTHORITY_CONNECTOR_RUNTIME_DENIED"),
    ("connector_write_enabled", "CRM_AUTHORITY_CONNECTOR_WRITE_DENIED"),
    ("account_sync_enabled", "CRM_AUTHORITY_ACCOUNT_SYNC_DENIED"),
    ("send_enabled", "CRM_AUTHORITY_SEND_DENIED"),
    ("calendar_write_enabled", "CRM_AUTHORITY_CALENDAR_WRITE_DENIED"),
    ("silent_merge_enabled", "CRM_AUTHORITY_SILENT_MERGE_DENIED"),
    ("silent_contact_creation_enabled", "CRM_AUTHORITY_CONTACT_CREATION_DENIED"),
    ("provider_model_call_enabled", "CRM_AUTHORITY_PROVIDER_MODEL_DENIED"),
    ("live_web_enabled", "CRM_AUTHORITY_LIVE_WEB_DENIED"),
    ("browser_runtime_enabled", "CRM_AUTHORITY_BROWSER_RUNTIME_DENIED"),
    ("model_output_authority_enabled", "CRM_AUTHORITY_MODEL_OUTPUT_DENIED"),
    ("memory_truth_authority_enabled", "CRM_AUTHORITY_MEMORY_TRUTH_DENIED"),
    ("production_authority_enabled", "CRM_AUTHORITY_PRODUCTION_DENIED"),
]

CRM_EVIDENCE_DENIALS = [
    ("raw_prompt_included", "CRM_EVIDENCE_RAW_PROMPT_DENIED"),
    ("raw_response_included", "CRM_EVIDENCE_RAW_RESPONSE_DENIED"),
    ("raw_provider_payload_included", "CRM_EVIDENCE_PROVIDER_PAYLOAD_DENIED"),
    ("raw_provider_exchange_included", "CRM_EVIDENCE_PROVIDER_EXCHANGE_DENIED"),
    ("raw_source_body_included", "CRM_EVIDENCE_SOURCE_BODY_DENIED"),
    ("raw_log_included", "CRM_EVIDENCE_RAW_LOG_DENIED"),
    ("raw_path_included", "CRM_EVIDENCE_RAW_PATH_DENIED"),
    ("private_material_included", "CRM_EVIDENCE_PRIVATE_MATERIAL_DENIED"),
]

CRM_CONTRACT_DENIALS = [
    ("backend_routes_added", "CRM_CONTRACT_BACKEND_ROUTE_DENIED"),
    ("control_center_route_added", "CRM_CONTRACT_CONTROL_CENTER_ROUTE_DENIED"),
    ("connector_runtime_enabled", "CRM_CONTRACT_CONNECTOR_RUNTIME_DENIED"),
    ("connector_write_enabled", "CRM_CONTRACT_CONNECTOR_WRITE_DENIED"),
    ("account_sync_enabled", "CRM_CONTRACT_ACCOUNT_SYNC_DENIED"),
    ("send_enabled", "CRM_CONTRACT_SEND_DENIED"),
    ("calendar_write_enabled", "CRM_CONTRACT_CALENDAR_WRITE_DENIED"),
    ("silent_merge_enabled", "CRM_CONTRACT_SILENT_MERGE_DENIED"),
    ("silent_contact_creation_enabled", "CRM_CONTRACT_CONTACT_CREATION_DENIED"),
    ("provider_model_call_enabled", "CRM_CONTRACT_PROVIDER_MODEL_DENIED"),
    ("live_web_enabled", "CRM_CONTRACT_LIVE_WEB_DENIED"),
    ("browser_runtime_enabled", "CRM_CONTRACT_BROWSER_RUNTIME_DENIED"),
    ("production_authority_enabled", "CRM_CONTRACT_PRODUCTION_DENIED"),
]

CRM_ALLOWED_SAFETY_KEYS: set[str] = set().union(
    CrmActivity.model_fields,
    CrmApprovalRecord.model_fields,
    CrmAuthorityBoundary.model_fields,
    CrmCommunicationItem.model_fields,
    CrmCommunicationsSpineContract.model_fields,
    CrmEngagementSignal.model_fields,
    CrmEvidenceRef.model_fields,
    CrmGovernedPlaybook.model_fields,
    CrmIdentityMatchCandidate.model_fields,
    CrmMemoryProvenance.model_fields,
    CrmOrganization.model_fields,
    CrmPerson.model_fields,
    CrmPipelineObject.model_fields,
    CrmPresetPack.model_fields,
    CrmProposal.model_fields,
    CrmRelationship.model_fields,
    CrmWorkQueue.model_fields,
    CrmWorkspace.model_fields,
    CrmWorkspaceContext.model_fields,
)
