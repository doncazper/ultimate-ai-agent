from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import _model_payload
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


FOUNDER_LOOP_READ_ONLY_INTEGRATION_CONTRACT_DOCS = [
    "docs/connectors/FCC_READ_ONLY_INTEGRATION_CONTRACTS.md",
    "docs/connectors/EMAIL_CONNECTOR_CONTRACT_REFRESH.md",
    "docs/connectors/CALENDAR_CONNECTOR_CONTRACT_REFRESH.md",
    "docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md",
    "docs/kanban/founder_command_center_board.md",
]

FCC_SHARED_REASON_CODES = [
    "FCC_READ_ONLY_METADATA_CONTRACT_ONLY",
    "FCC_SAFE_REFS_ONLY",
    "FCC_CONNECTOR_RUNTIME_MISSING",
    "FCC_NO_AUTH_FETCH_WRITE_OR_BACKGROUND_COLLECTION",
]

FCC_DRAFT_ONLY_REASON_CODES = [
    "FCC_DRAFT_ONLY_EMAIL_PROPOSAL_CONTRACT",
    "FCC_DRAFT_PROPOSAL_SAFE_REFS_ONLY",
    "FCC_DRAFT_PROPOSAL_NO_SEND_WRITE_OR_ACCOUNT_AUTH",
    "FCC_DRAFT_PROPOSAL_CONNECTOR_RUNTIME_MISSING",
]

FCC_SHARED_SOURCE_READINESS_REFS = [
    "source-readiness-ref:fcc-p1:manual-or-fixture-only",
    "source-readiness-ref:fcc-p1:connector-runtime-missing",
    "source-readiness-ref:fcc-p1:no-account-connection",
]


class FCCCalendarReadOnlyContractStatus(str, Enum):
    calendar_event_metadata_contract = "calendar_event_metadata_contract"


class FCCEmailMetadataReadOnlyContractStatus(str, Enum):
    email_metadata_contract = "email_metadata_contract"


class FCCDraftEmailResponseProposalStatus(str, Enum):
    draft_email_response_proposal_contract = (
        "draft_email_response_proposal_contract"
    )


class FCCReadOnlyIntegrationPairStatus(str, Enum):
    paired_contracts = "paired_contracts"


class _FCCReadOnlyIntegrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class FCCCalendarReadOnlyPolicy(_FCCReadOnlyIntegrationModel):
    policy_ref: str = "fcc-calendar-read-only-policy:fcc-p1-007"
    contract_only: bool = True
    read_only_required: bool = True
    metadata_only_required: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing_required: bool = True
    account_auth_enabled: bool = False
    network_fetch_enabled: bool = False
    calendar_read_runtime_enabled: bool = False
    calendar_search_runtime_enabled: bool = False
    event_create_enabled: bool = False
    event_update_enabled: bool = False
    event_delete_enabled: bool = False
    invite_send_enabled: bool = False
    meeting_link_exposure_enabled: bool = False
    location_exposure_enabled: bool = False
    event_title_body_storage_enabled: bool = False
    raw_invite_body_enabled: bool = False
    background_collection_enabled: bool = False
    attachment_download_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class FCCEmailMetadataReadOnlyPolicy(_FCCReadOnlyIntegrationModel):
    policy_ref: str = "fcc-email-metadata-read-only-policy:fcc-p1-008"
    contract_only: bool = True
    read_only_required: bool = True
    metadata_only_required: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing_required: bool = True
    raw_body_enabled: bool = False
    subject_text_enabled: bool = False
    participant_identifiers_enabled: bool = False
    attachment_names_enabled: bool = False
    attachment_download_enabled: bool = False
    account_auth_enabled: bool = False
    email_fetch_runtime_enabled: bool = False
    email_search_runtime_enabled: bool = False
    send_enabled: bool = False
    delete_enabled: bool = False
    archive_enabled: bool = False
    label_write_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class FCCDraftEmailResponseProposalPolicy(_FCCReadOnlyIntegrationModel):
    policy_ref: str = "fcc-draft-email-response-proposal-policy:fcc-p1-009"
    contract_only: bool = True
    read_only_required: bool = True
    draft_only_required: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing_required: bool = True
    raw_body_enabled: bool = False
    raw_draft_body_enabled: bool = False
    subject_text_enabled: bool = False
    participant_identifiers_enabled: bool = False
    attachment_names_enabled: bool = False
    attachment_download_enabled: bool = False
    account_auth_enabled: bool = False
    account_write_enabled: bool = False
    email_fetch_runtime_enabled: bool = False
    email_search_runtime_enabled: bool = False
    reply_enabled: bool = False
    forward_enabled: bool = False
    send_enabled: bool = False
    delete_enabled: bool = False
    archive_enabled: bool = False
    label_write_enabled: bool = False
    move_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    background_sync_enabled: bool = False
    notification_delivery_enabled: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class FCCCalendarEventMetadataEnvelope(_FCCReadOnlyIntegrationModel):
    calendar_contract_ref: str
    product_loop_ref: str
    event_ref: str
    time_window_ref: str
    attendee_identity_refs: list[str]
    account_identity_ref: str
    source_readiness_refs: list[str]
    evidence_refs: list[str]
    audit_ref: str
    replay_ref: str
    meeting_prep_summary_ref: str
    redacted_meeting_prep_summary: str
    missing_runtime_ref: str
    blocked_runtime_refs: list[str]
    status: FCCCalendarReadOnlyContractStatus = (
        FCCCalendarReadOnlyContractStatus.calendar_event_metadata_contract
    )
    contract_only: bool = True
    read_only: bool = True
    metadata_only: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing: bool = True
    account_auth_enabled: bool = False
    network_fetch_enabled: bool = False
    calendar_read_runtime_enabled: bool = False
    calendar_search_runtime_enabled: bool = False
    event_create_enabled: bool = False
    event_update_enabled: bool = False
    event_delete_enabled: bool = False
    invite_send_enabled: bool = False
    meeting_link_exposure_enabled: bool = False
    location_exposure_enabled: bool = False
    event_title_body_storage_enabled: bool = False
    raw_invite_body_enabled: bool = False
    background_collection_enabled: bool = False
    attachment_download_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref_fields(
            [
                (self.calendar_contract_ref, "calendar_contract_ref"),
                (self.product_loop_ref, "product_loop_ref"),
                (self.event_ref, "event_ref"),
                (self.time_window_ref, "time_window_ref"),
                (self.account_identity_ref, "account_identity_ref"),
                (self.audit_ref, "audit_ref"),
                (self.replay_ref, "replay_ref"),
                (self.meeting_prep_summary_ref, "meeting_prep_summary_ref"),
                (self.missing_runtime_ref, "missing_runtime_ref"),
            ]
        )
        _validate_ref_list(self.attendee_identity_refs, "attendee_identity_ref")
        _validate_ref_list(self.source_readiness_refs, "source_readiness_ref")
        _validate_ref_list(self.evidence_refs, "evidence_ref")
        _validate_ref_list(self.blocked_runtime_refs, "blocked_runtime_ref")
        _validate_reason_codes(self.reason_codes)
        _validate_safe_text(
            self.redacted_meeting_prep_summary,
            "FCC_CALENDAR_PRIVATE_CONTENT_DENIED",
        )
        return self


class FCCEmailMetadataEnvelope(_FCCReadOnlyIntegrationModel):
    email_contract_ref: str
    product_loop_ref: str
    sender_summary_ref: str
    thread_ref: str
    time_window_ref: str
    label_summary_refs: list[str]
    source_readiness_refs: list[str]
    evidence_refs: list[str]
    audit_ref: str
    replay_ref: str
    inbox_summary_ref: str
    follow_up_summary_ref: str
    redacted_inbox_summary: str
    redacted_follow_up_summary: str
    missing_runtime_ref: str
    blocked_runtime_refs: list[str]
    status: FCCEmailMetadataReadOnlyContractStatus = (
        FCCEmailMetadataReadOnlyContractStatus.email_metadata_contract
    )
    contract_only: bool = True
    read_only: bool = True
    metadata_only: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing: bool = True
    raw_body_enabled: bool = False
    subject_text_enabled: bool = False
    participant_identifiers_enabled: bool = False
    attachment_names_enabled: bool = False
    attachment_download_enabled: bool = False
    account_auth_enabled: bool = False
    email_fetch_runtime_enabled: bool = False
    email_search_runtime_enabled: bool = False
    send_enabled: bool = False
    delete_enabled: bool = False
    archive_enabled: bool = False
    label_write_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref_fields(
            [
                (self.email_contract_ref, "email_contract_ref"),
                (self.product_loop_ref, "product_loop_ref"),
                (self.sender_summary_ref, "sender_summary_ref"),
                (self.thread_ref, "thread_ref"),
                (self.time_window_ref, "time_window_ref"),
                (self.audit_ref, "audit_ref"),
                (self.replay_ref, "replay_ref"),
                (self.inbox_summary_ref, "inbox_summary_ref"),
                (self.follow_up_summary_ref, "follow_up_summary_ref"),
                (self.missing_runtime_ref, "missing_runtime_ref"),
            ]
        )
        _validate_ref_list(self.label_summary_refs, "label_summary_ref")
        _validate_ref_list(self.source_readiness_refs, "source_readiness_ref")
        _validate_ref_list(self.evidence_refs, "evidence_ref")
        _validate_ref_list(self.blocked_runtime_refs, "blocked_runtime_ref")
        _validate_reason_codes(self.reason_codes)
        _validate_safe_text(
            self.redacted_inbox_summary,
            "FCC_EMAIL_PRIVATE_CONTENT_DENIED",
        )
        _validate_safe_text(
            self.redacted_follow_up_summary,
            "FCC_EMAIL_PRIVATE_CONTENT_DENIED",
        )
        return self


class FCCDraftEmailResponseProposalEnvelope(_FCCReadOnlyIntegrationModel):
    draft_proposal_contract_ref: str
    product_loop_ref: str
    proposal_ref: str
    source_email_metadata_refs: list[str]
    thread_ref: str
    sender_identity_ref: str
    recipient_identity_refs: list[str]
    account_identity_ref: str
    time_window_ref: str
    follow_up_refs: list[str]
    purpose_label: str
    intent_label: str
    tone_label: str
    style_label: str
    draft_summary_ref: str
    redacted_draft_summary: str
    response_outline_ref: str
    redacted_response_outline: list[str]
    evidence_refs: list[str]
    source_readiness_refs: list[str]
    audit_ref: str
    replay_ref: str
    stale_state: str
    missing_evidence_posture: str
    approval_posture: str
    blocked_send_write_states: list[str]
    next_safe_action: str
    missing_runtime_ref: str
    blocked_runtime_refs: list[str]
    status: FCCDraftEmailResponseProposalStatus = (
        FCCDraftEmailResponseProposalStatus.draft_email_response_proposal_contract
    )
    contract_only: bool = True
    read_only: bool = True
    draft_only: bool = True
    safe_refs_required: bool = True
    connector_runtime_missing: bool = True
    raw_body_enabled: bool = False
    raw_draft_body_enabled: bool = False
    subject_text_enabled: bool = False
    participant_identifiers_enabled: bool = False
    attachment_names_enabled: bool = False
    attachment_download_enabled: bool = False
    account_auth_enabled: bool = False
    account_write_enabled: bool = False
    email_fetch_runtime_enabled: bool = False
    email_search_runtime_enabled: bool = False
    reply_enabled: bool = False
    forward_enabled: bool = False
    send_enabled: bool = False
    delete_enabled: bool = False
    archive_enabled: bool = False
    label_write_enabled: bool = False
    move_enabled: bool = False
    connector_runtime_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    background_sync_enabled: bool = False
    notification_delivery_enabled: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref_fields(
            [
                (self.draft_proposal_contract_ref, "draft_proposal_contract_ref"),
                (self.product_loop_ref, "product_loop_ref"),
                (self.proposal_ref, "proposal_ref"),
                (self.thread_ref, "thread_ref"),
                (self.sender_identity_ref, "sender_identity_ref"),
                (self.account_identity_ref, "account_identity_ref"),
                (self.time_window_ref, "time_window_ref"),
                (self.draft_summary_ref, "draft_summary_ref"),
                (self.response_outline_ref, "response_outline_ref"),
                (self.audit_ref, "audit_ref"),
                (self.replay_ref, "replay_ref"),
                (self.missing_runtime_ref, "missing_runtime_ref"),
            ]
        )
        _validate_ref_list(
            self.source_email_metadata_refs,
            "source_email_metadata_ref",
        )
        _validate_ref_list(self.recipient_identity_refs, "recipient_identity_ref")
        _validate_ref_list(self.follow_up_refs, "follow_up_ref")
        _validate_ref_list(self.evidence_refs, "evidence_ref")
        _validate_ref_list(self.source_readiness_refs, "source_readiness_ref")
        _validate_ref_list(
            self.blocked_send_write_states,
            "blocked_send_write_state_ref",
        )
        _validate_ref_list(self.blocked_runtime_refs, "blocked_runtime_ref")
        _validate_reason_codes(self.reason_codes)
        for value in [
            self.purpose_label,
            self.intent_label,
            self.tone_label,
            self.style_label,
            self.redacted_draft_summary,
            self.stale_state,
            self.missing_evidence_posture,
            self.approval_posture,
            self.next_safe_action,
            *self.redacted_response_outline,
        ]:
            _validate_safe_text(value, "FCC_DRAFT_EMAIL_PRIVATE_CONTENT_DENIED")
        return self


class FCCReadOnlyIntegrationContractPair(_FCCReadOnlyIntegrationModel):
    pair_ref: str
    product_loop_ref: str
    calendar: FCCCalendarEventMetadataEnvelope
    email: FCCEmailMetadataEnvelope
    shared_source_readiness_refs: list[str]
    shared_blocked_runtime_refs: list[str]
    status: FCCReadOnlyIntegrationPairStatus = (
        FCCReadOnlyIntegrationPairStatus.paired_contracts
    )
    contract_only: bool = True
    read_only: bool = True
    metadata_only: bool = True
    connector_runtime_missing: bool = True
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref_fields(
            [
                (self.pair_ref, "pair_ref"),
                (self.product_loop_ref, "product_loop_ref"),
            ]
        )
        _validate_ref_list(self.shared_source_readiness_refs, "source_readiness_ref")
        _validate_ref_list(self.shared_blocked_runtime_refs, "blocked_runtime_ref")
        _validate_reason_codes(self.reason_codes)
        _validate_safe_text(self.safe_summary, "FCC_PRIVATE_CONTENT_DENIED")
        return self


def build_fcc_calendar_event_metadata_envelope(
    policy: FCCCalendarReadOnlyPolicy | None = None,
) -> FCCCalendarEventMetadataEnvelope:
    active_policy = validate_fcc_calendar_read_only_policy(
        policy or FCCCalendarReadOnlyPolicy()
    )
    envelope = FCCCalendarEventMetadataEnvelope(
        calendar_contract_ref="fcc-calendar-read-only-contract:fcc-p1-007",
        product_loop_ref="founder-command-center-product-loop:read-only-sources",
        event_ref="calendar-event-ref:fcc-p1-007:meeting-prep-placeholder",
        time_window_ref="time-window-ref:fcc-p1-007:bounded-meeting-window",
        attendee_identity_refs=[
            "attendee-identity-ref:fcc-p1-007:organizer-safe-ref",
            "attendee-identity-ref:fcc-p1-007:required-attendees-safe-ref",
        ],
        account_identity_ref="account-identity-ref:fcc-p1-007:calendar-account-safe-ref",
        source_readiness_refs=list(FCC_SHARED_SOURCE_READINESS_REFS),
        evidence_refs=[
            "evidence-ref:fcc-p1-007:meeting-prep-summary",
            "evidence-ref:fcc-p1-007:source-readiness-posture",
        ],
        audit_ref="audit-ref:fcc-p1-007:calendar-contract",
        replay_ref="replay-ref:fcc-p1-007:calendar-contract",
        meeting_prep_summary_ref=(
            "meeting-prep-summary-ref:fcc-p1-007:redacted-summary"
        ),
        redacted_meeting_prep_summary=(
            "Calendar meeting-prep contract is metadata-only and safe-ref-only; "
            "live calendar access remains missing until a future connector milestone."
        ),
        missing_runtime_ref="missing-runtime-ref:fcc-p1-007:calendar-connector",
        blocked_runtime_refs=[
            "blocked-runtime-ref:fcc-p1-007:no-account-auth",
            "blocked-runtime-ref:fcc-p1-007:no-calendar-fetch",
            "blocked-runtime-ref:fcc-p1-007:no-calendar-write",
            "blocked-runtime-ref:fcc-p1-007:no-background-collection",
        ],
        contract_only=active_policy.contract_only,
        read_only=active_policy.read_only_required,
        metadata_only=active_policy.metadata_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        connector_runtime_missing=active_policy.connector_runtime_missing_required,
        side_effects_performed=[],
        reason_codes=[
            "FCC_P1_007_CALENDAR_EVENT_METADATA_CONTRACT",
            *FCC_SHARED_REASON_CODES,
        ],
    )
    return validate_fcc_calendar_event_metadata_envelope(envelope)


def build_fcc_email_metadata_envelope(
    policy: FCCEmailMetadataReadOnlyPolicy | None = None,
) -> FCCEmailMetadataEnvelope:
    active_policy = validate_fcc_email_metadata_read_only_policy(
        policy or FCCEmailMetadataReadOnlyPolicy()
    )
    envelope = FCCEmailMetadataEnvelope(
        email_contract_ref="fcc-email-metadata-read-only-contract:fcc-p1-008",
        product_loop_ref="founder-command-center-product-loop:read-only-sources",
        sender_summary_ref="sender-summary-ref:fcc-p1-008:safe-sender-class",
        thread_ref="thread-ref:fcc-p1-008:follow-up-thread-safe-ref",
        time_window_ref="time-window-ref:fcc-p1-008:bounded-inbox-window",
        label_summary_refs=[
            "label-summary-ref:fcc-p1-008:priority-safe-ref",
            "label-summary-ref:fcc-p1-008:follow-up-safe-ref",
        ],
        source_readiness_refs=list(FCC_SHARED_SOURCE_READINESS_REFS),
        evidence_refs=[
            "evidence-ref:fcc-p1-008:inbox-readiness-summary",
            "evidence-ref:fcc-p1-008:follow-up-readiness-summary",
        ],
        audit_ref="audit-ref:fcc-p1-008:email-contract",
        replay_ref="replay-ref:fcc-p1-008:email-contract",
        inbox_summary_ref="inbox-summary-ref:fcc-p1-008:redacted-summary",
        follow_up_summary_ref="follow-up-summary-ref:fcc-p1-008:redacted-summary",
        redacted_inbox_summary=(
            "Email metadata contract is safe-ref-only and source-readiness-only; "
            "live inbox access remains missing until a future connector milestone."
        ),
        redacted_follow_up_summary=(
            "Follow-up readiness uses sender, thread, time-window, label, evidence, "
            "audit, and replay refs only; no message content is available."
        ),
        missing_runtime_ref="missing-runtime-ref:fcc-p1-008:email-connector",
        blocked_runtime_refs=[
            "blocked-runtime-ref:fcc-p1-008:no-account-auth",
            "blocked-runtime-ref:fcc-p1-008:no-email-fetch",
            "blocked-runtime-ref:fcc-p1-008:no-email-write",
            "blocked-runtime-ref:fcc-p1-008:no-background-collection",
        ],
        contract_only=active_policy.contract_only,
        read_only=active_policy.read_only_required,
        metadata_only=active_policy.metadata_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        connector_runtime_missing=active_policy.connector_runtime_missing_required,
        side_effects_performed=[],
        reason_codes=[
            "FCC_P1_008_EMAIL_METADATA_CONTRACT",
            *FCC_SHARED_REASON_CODES,
        ],
    )
    return validate_fcc_email_metadata_envelope(envelope)


def build_fcc_draft_email_response_proposal_envelope(
    policy: FCCDraftEmailResponseProposalPolicy | None = None,
) -> FCCDraftEmailResponseProposalEnvelope:
    active_policy = validate_fcc_draft_email_response_proposal_policy(
        policy or FCCDraftEmailResponseProposalPolicy()
    )
    envelope = FCCDraftEmailResponseProposalEnvelope(
        draft_proposal_contract_ref=(
            "fcc-draft-email-response-proposal-contract:fcc-p1-009"
        ),
        product_loop_ref="founder-command-center-product-loop:draft-only-email",
        proposal_ref="draft-email-response-proposal-ref:fcc-p1-009:follow-up-placeholder",
        source_email_metadata_refs=[
            "email-metadata-ref:fcc-p1-008:follow-up-thread-safe-ref",
            "email-metadata-ref:fcc-p1-008:inbox-readiness-summary",
        ],
        thread_ref="thread-ref:fcc-p1-008:follow-up-thread-safe-ref",
        sender_identity_ref="sender-identity-ref:fcc-p1-009:safe-sender-class",
        recipient_identity_refs=[
            "recipient-identity-ref:fcc-p1-009:operator-reviewed-recipient-class",
        ],
        account_identity_ref="account-identity-ref:fcc-p1-009:email-account-safe-ref",
        time_window_ref="time-window-ref:fcc-p1-009:bounded-follow-up-window",
        follow_up_refs=[
            "follow-up-ref:fcc-p1-009:reply-proposal-review",
        ],
        purpose_label="follow_up_review",
        intent_label="operator_reviewed_reply_outline",
        tone_label="concise_professional",
        style_label="safe_outline_only",
        draft_summary_ref="draft-summary-ref:fcc-p1-009:redacted-summary",
        redacted_draft_summary=(
            "Draft proposal is an editable outline over safe refs only; account "
            "changes and connector runtime remain blocked."
        ),
        response_outline_ref="response-outline-ref:fcc-p1-009:redacted-outline",
        redacted_response_outline=[
            "Acknowledge the safe follow-up category.",
            "List reviewed next-step refs for operator approval.",
            "Keep account changes blocked until a later connector milestone.",
        ],
        evidence_refs=[
            "evidence-ref:fcc-p1-009:draft-proposal-contract",
            "evidence-ref:fcc-p1-009:blocked-send-write-posture",
        ],
        source_readiness_refs=list(FCC_SHARED_SOURCE_READINESS_REFS),
        audit_ref="audit-ref:fcc-p1-009:draft-proposal-contract",
        replay_ref="replay-ref:fcc-p1-009:draft-proposal-contract",
        stale_state="recheck_safe_refs_before_review",
        missing_evidence_posture=(
            "connector_runtime_and_account_proof_missing_until_future_milestone"
        ),
        approval_posture="approval_refs_are_identifiers_only_not_send_authority",
        blocked_send_write_states=[
            "blocked-state-ref:fcc-p1-009:no-email-send",
            "blocked-state-ref:fcc-p1-009:no-email-write",
            "blocked-state-ref:fcc-p1-009:no-account-action",
        ],
        next_safe_action=(
            "Review the safe proposal refs; keep connector runtime and account "
            "changes blocked until separately scoped."
        ),
        missing_runtime_ref="missing-runtime-ref:fcc-p1-009:email-connector",
        blocked_runtime_refs=[
            "blocked-runtime-ref:fcc-p1-009:no-account-auth",
            "blocked-runtime-ref:fcc-p1-009:no-email-fetch",
            "blocked-runtime-ref:fcc-p1-009:no-email-send-or-write",
            "blocked-runtime-ref:fcc-p1-009:no-model-drafting-runtime",
        ],
        contract_only=active_policy.contract_only,
        read_only=active_policy.read_only_required,
        draft_only=active_policy.draft_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        connector_runtime_missing=active_policy.connector_runtime_missing_required,
        side_effects_performed=[],
        reason_codes=[
            "FCC_P1_009_DRAFT_ONLY_EMAIL_RESPONSE_PROPOSAL",
            *FCC_DRAFT_ONLY_REASON_CODES,
            *FCC_SHARED_REASON_CODES,
        ],
    )
    return validate_fcc_draft_email_response_proposal_envelope(envelope)


def build_fcc_read_only_integration_contract_pair(
    *,
    calendar: FCCCalendarEventMetadataEnvelope | None = None,
    email: FCCEmailMetadataEnvelope | None = None,
) -> FCCReadOnlyIntegrationContractPair:
    active_calendar = validate_fcc_calendar_event_metadata_envelope(
        calendar or build_fcc_calendar_event_metadata_envelope()
    )
    active_email = validate_fcc_email_metadata_envelope(
        email or build_fcc_email_metadata_envelope()
    )
    pair = FCCReadOnlyIntegrationContractPair(
        pair_ref="fcc-read-only-integration-contract-pair:fcc-p1-007-008",
        product_loop_ref="founder-command-center-product-loop:read-only-sources",
        calendar=active_calendar,
        email=active_email,
        shared_source_readiness_refs=list(FCC_SHARED_SOURCE_READINESS_REFS),
        shared_blocked_runtime_refs=[
            "blocked-runtime-ref:fcc-p1:no-account-auth",
            "blocked-runtime-ref:fcc-p1:no-network-fetch",
            "blocked-runtime-ref:fcc-p1:no-connector-runtime",
            "blocked-runtime-ref:fcc-p1:no-write-or-background-collection",
        ],
        side_effects_performed=[],
        reason_codes=[
            "FCC_P1_007_008_PAIRED_READ_ONLY_CONTRACTS",
            *FCC_SHARED_REASON_CODES,
        ],
        safe_summary=(
            "FCC-P1-007 and FCC-P1-008 define paired read-only metadata "
            "contracts for Founder Command Center source readiness. They add no "
            "account connection, connector runtime, fetch, write, route, UI "
            "control, model call, memory write, context injection, dependency, "
            "public release, or production authority."
        ),
    )
    return validate_fcc_read_only_integration_contract_pair(pair)


def validate_fcc_calendar_read_only_policy(
    policy: FCCCalendarReadOnlyPolicy | dict[str, Any],
) -> FCCCalendarReadOnlyPolicy:
    payload = _payload(policy)
    _reject_calendar_private_payload(
        payload,
        allowed_keys=set(FCCCalendarReadOnlyPolicy.model_fields),
    )
    validated = FCCCalendarReadOnlyPolicy.model_validate(payload)
    for field_name, reason in _CALENDAR_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _CALENDAR_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _reject_calendar_private_payload(validated.metadata)
    return validated


def validate_fcc_email_metadata_read_only_policy(
    policy: FCCEmailMetadataReadOnlyPolicy | dict[str, Any],
) -> FCCEmailMetadataReadOnlyPolicy:
    payload = _payload(policy)
    _reject_email_private_payload(
        payload,
        allowed_keys=set(FCCEmailMetadataReadOnlyPolicy.model_fields),
    )
    validated = FCCEmailMetadataReadOnlyPolicy.model_validate(payload)
    for field_name, reason in _EMAIL_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _EMAIL_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _reject_email_private_payload(validated.metadata)
    return validated


def validate_fcc_draft_email_response_proposal_policy(
    policy: FCCDraftEmailResponseProposalPolicy | dict[str, Any],
) -> FCCDraftEmailResponseProposalPolicy:
    payload = _payload(policy)
    _reject_draft_email_private_payload(
        payload,
        allowed_keys=set(FCCDraftEmailResponseProposalPolicy.model_fields),
    )
    validated = FCCDraftEmailResponseProposalPolicy.model_validate(payload)
    for field_name, reason in _DRAFT_EMAIL_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _DRAFT_EMAIL_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _reject_draft_email_private_payload(validated.metadata)
    return validated


def validate_fcc_calendar_event_metadata_envelope(
    envelope: FCCCalendarEventMetadataEnvelope | dict[str, Any],
) -> FCCCalendarEventMetadataEnvelope:
    payload = _payload(envelope)
    _reject_calendar_private_payload(
        payload,
        allowed_keys=set(FCCCalendarEventMetadataEnvelope.model_fields),
    )
    for field_name, reason in _CALENDAR_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = FCCCalendarEventMetadataEnvelope.model_validate(payload)
    for field_name, reason in _CALENDAR_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != FCCCalendarReadOnlyContractStatus.calendar_event_metadata_contract
    ):
        raise ValueError("FCC_CALENDAR_STATUS_REQUIRED")
    for field_name, reason in _CALENDAR_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_calendar_bindings(validated)
    _reject_calendar_private_payload(validated.metadata)
    return validated


def validate_fcc_email_metadata_envelope(
    envelope: FCCEmailMetadataEnvelope | dict[str, Any],
) -> FCCEmailMetadataEnvelope:
    payload = _payload(envelope)
    _reject_email_private_payload(
        payload,
        allowed_keys=set(FCCEmailMetadataEnvelope.model_fields),
    )
    for field_name, reason in _EMAIL_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = FCCEmailMetadataEnvelope.model_validate(payload)
    for field_name, reason in _EMAIL_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != FCCEmailMetadataReadOnlyContractStatus.email_metadata_contract:
        raise ValueError("FCC_EMAIL_STATUS_REQUIRED")
    for field_name, reason in _EMAIL_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_email_bindings(validated)
    _reject_email_private_payload(validated.metadata)
    return validated


def validate_fcc_draft_email_response_proposal_envelope(
    envelope: FCCDraftEmailResponseProposalEnvelope | dict[str, Any],
) -> FCCDraftEmailResponseProposalEnvelope:
    payload = _payload(envelope)
    _reject_draft_email_private_payload(
        payload,
        allowed_keys=set(FCCDraftEmailResponseProposalEnvelope.model_fields),
    )
    for field_name, reason in _DRAFT_EMAIL_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = FCCDraftEmailResponseProposalEnvelope.model_validate(payload)
    for field_name, reason in _DRAFT_EMAIL_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != FCCDraftEmailResponseProposalStatus.draft_email_response_proposal_contract
    ):
        raise ValueError("FCC_DRAFT_EMAIL_STATUS_REQUIRED")
    for field_name, reason in _DRAFT_EMAIL_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_draft_email_bindings(validated)
    _reject_draft_email_private_payload(validated.metadata)
    return validated


def validate_fcc_read_only_integration_contract_pair(
    pair: FCCReadOnlyIntegrationContractPair | dict[str, Any],
) -> FCCReadOnlyIntegrationContractPair:
    payload = _payload(pair)
    _reject_calendar_private_payload(
        payload.get("calendar", {}),
        allowed_keys=set(FCCCalendarEventMetadataEnvelope.model_fields),
    )
    _reject_email_private_payload(
        payload.get("email", {}),
        allowed_keys=set(FCCEmailMetadataEnvelope.model_fields),
    )
    validated = FCCReadOnlyIntegrationContractPair.model_validate(payload)
    if validated.status != FCCReadOnlyIntegrationPairStatus.paired_contracts:
        raise ValueError("FCC_PAIR_STATUS_REQUIRED")
    if not validated.contract_only:
        raise ValueError("CONTRACT_ONLY_REQUIRED")
    if not validated.read_only:
        raise ValueError("READ_ONLY_REQUIRED")
    if not validated.metadata_only:
        raise ValueError("METADATA_ONLY_REQUIRED")
    if not validated.connector_runtime_missing:
        raise ValueError("CONNECTOR_RUNTIME_MISSING_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    calendar = validate_fcc_calendar_event_metadata_envelope(validated.calendar)
    email = validate_fcc_email_metadata_envelope(validated.email)
    if validated.product_loop_ref != calendar.product_loop_ref:
        raise ValueError("FCC_CALENDAR_PRODUCT_LOOP_BINDING_MISMATCH")
    if validated.product_loop_ref != email.product_loop_ref:
        raise ValueError("FCC_EMAIL_PRODUCT_LOOP_BINDING_MISMATCH")
    for ref in FCC_SHARED_SOURCE_READINESS_REFS:
        if ref not in validated.shared_source_readiness_refs:
            raise ValueError("FCC_SHARED_SOURCE_READINESS_REF_REQUIRED")
        if ref not in calendar.source_readiness_refs:
            raise ValueError("FCC_CALENDAR_SOURCE_READINESS_REF_REQUIRED")
        if ref not in email.source_readiness_refs:
            raise ValueError("FCC_EMAIL_SOURCE_READINESS_REF_REQUIRED")
    return validated


def _payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return _model_payload(value)
    if isinstance(value, dict):
        return dict(value)
    raise ValueError("FCC_CONTRACT_PAYLOAD_REQUIRED")


def _validate_ref_fields(refs: list[tuple[str, str]]) -> None:
    for value, field_name in refs:
        _validate_m61_ref(value, field_name)


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    if not refs:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_reason_codes(reason_codes: list[str]) -> None:
    if not reason_codes:
        raise ValueError("REASON_CODE_REQUIRED")
    for reason_code in reason_codes:
        if not reason_code.startswith("FCC_"):
            raise ValueError("FCC_REASON_CODE_REQUIRED")


def _validate_safe_text(value: str, reason: str) -> None:
    try:
        _validate_safe_payload({"safe_text": value})
    except ValueError as exc:
        raise ValueError(reason) from exc


def _validate_calendar_bindings(envelope: FCCCalendarEventMetadataEnvelope) -> None:
    if envelope.calendar_contract_ref != "fcc-calendar-read-only-contract:fcc-p1-007":
        raise ValueError("FCC_CALENDAR_CONTRACT_REF_REQUIRED")
    for field_name, refs in [
        ("attendee_identity_ref", envelope.attendee_identity_refs),
        ("source_readiness_ref", envelope.source_readiness_refs),
        ("evidence_ref", envelope.evidence_refs),
        ("blocked_runtime_ref", envelope.blocked_runtime_refs),
    ]:
        _validate_ref_list(refs, field_name)
    for reason_code in FCC_SHARED_REASON_CODES:
        if reason_code not in envelope.reason_codes:
            raise ValueError("FCC_SHARED_REASON_CODE_REQUIRED")


def _validate_email_bindings(envelope: FCCEmailMetadataEnvelope) -> None:
    if envelope.email_contract_ref != "fcc-email-metadata-read-only-contract:fcc-p1-008":
        raise ValueError("FCC_EMAIL_CONTRACT_REF_REQUIRED")
    for field_name, refs in [
        ("label_summary_ref", envelope.label_summary_refs),
        ("source_readiness_ref", envelope.source_readiness_refs),
        ("evidence_ref", envelope.evidence_refs),
        ("blocked_runtime_ref", envelope.blocked_runtime_refs),
    ]:
        _validate_ref_list(refs, field_name)
    for reason_code in FCC_SHARED_REASON_CODES:
        if reason_code not in envelope.reason_codes:
            raise ValueError("FCC_SHARED_REASON_CODE_REQUIRED")


def _validate_draft_email_bindings(
    envelope: FCCDraftEmailResponseProposalEnvelope,
) -> None:
    if (
        envelope.draft_proposal_contract_ref
        != "fcc-draft-email-response-proposal-contract:fcc-p1-009"
    ):
        raise ValueError("FCC_DRAFT_EMAIL_CONTRACT_REF_REQUIRED")
    for field_name, refs in [
        ("source_email_metadata_ref", envelope.source_email_metadata_refs),
        ("recipient_identity_ref", envelope.recipient_identity_refs),
        ("follow_up_ref", envelope.follow_up_refs),
        ("evidence_ref", envelope.evidence_refs),
        ("source_readiness_ref", envelope.source_readiness_refs),
        ("blocked_send_write_state_ref", envelope.blocked_send_write_states),
        ("blocked_runtime_ref", envelope.blocked_runtime_refs),
    ]:
        _validate_ref_list(refs, field_name)
    for reason_code in [*FCC_DRAFT_ONLY_REASON_CODES, *FCC_SHARED_REASON_CODES]:
        if reason_code not in envelope.reason_codes:
            raise ValueError("FCC_DRAFT_EMAIL_REASON_CODE_REQUIRED")


def _reject_calendar_private_payload(
    payload: Any,
    *,
    allowed_keys: set[str] | None = None,
) -> None:
    if _contains_forbidden_key(payload, _CALENDAR_FORBIDDEN_KEY_RE, allowed_keys):
        raise ValueError("FCC_CALENDAR_PRIVATE_FIELD_DENIED")
    if _contains_forbidden_value(payload, _CALENDAR_FORBIDDEN_VALUE_RE):
        raise ValueError("FCC_CALENDAR_PRIVATE_CONTENT_DENIED")
    _reject_secret_like_payload(payload, "FCC_CALENDAR_PRIVATE_CONTENT_DENIED")


def _reject_email_private_payload(
    payload: Any,
    *,
    allowed_keys: set[str] | None = None,
) -> None:
    if _contains_forbidden_key(payload, _EMAIL_FORBIDDEN_KEY_RE, allowed_keys):
        raise ValueError("FCC_EMAIL_PRIVATE_FIELD_DENIED")
    if _contains_forbidden_value(payload, _EMAIL_FORBIDDEN_VALUE_RE):
        raise ValueError("FCC_EMAIL_PRIVATE_CONTENT_DENIED")
    _reject_secret_like_payload(payload, "FCC_EMAIL_PRIVATE_CONTENT_DENIED")


def _reject_draft_email_private_payload(
    payload: Any,
    *,
    allowed_keys: set[str] | None = None,
) -> None:
    if _contains_forbidden_key(payload, _DRAFT_EMAIL_FORBIDDEN_KEY_RE, allowed_keys):
        raise ValueError("FCC_DRAFT_EMAIL_PRIVATE_FIELD_DENIED")
    if _contains_forbidden_value(payload, _DRAFT_EMAIL_FORBIDDEN_VALUE_RE):
        raise ValueError("FCC_DRAFT_EMAIL_PRIVATE_CONTENT_DENIED")
    _reject_secret_like_payload(payload, "FCC_DRAFT_EMAIL_PRIVATE_CONTENT_DENIED")


def _reject_secret_like_payload(payload: Any, reason: str) -> None:
    try:
        _validate_safe_payload(payload)
    except ValueError as exc:
        raise ValueError(reason) from exc


def _contains_forbidden_key(
    payload: Any,
    pattern: re.Pattern[str],
    allowed_keys: set[str] | None = None,
) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key)
            if key_text not in (allowed_keys or set()) and pattern.search(key_text):
                return True
            if _contains_forbidden_key(value, pattern):
                return True
    elif isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_key(item, pattern) for item in payload)
    return False


def _contains_forbidden_value(payload: Any, pattern: re.Pattern[str]) -> bool:
    if isinstance(payload, str):
        return bool(pattern.search(payload))
    if isinstance(payload, dict):
        return any(_contains_forbidden_value(value, pattern) for value in payload.values())
    if isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_value(item, pattern) for item in payload)
    return False


_CALENDAR_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only_required", "READ_ONLY_REQUIRED"),
    ("metadata_only_required", "METADATA_ONLY_REQUIRED"),
    ("safe_refs_required", "SAFE_REFS_REQUIRED"),
    ("connector_runtime_missing_required", "CONNECTOR_RUNTIME_MISSING_REQUIRED"),
]

_EMAIL_REQUIRED_TRUE = list(_CALENDAR_REQUIRED_TRUE)

_DRAFT_EMAIL_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only_required", "READ_ONLY_REQUIRED"),
    ("draft_only_required", "DRAFT_ONLY_REQUIRED"),
    ("safe_refs_required", "SAFE_REFS_REQUIRED"),
    ("connector_runtime_missing_required", "CONNECTOR_RUNTIME_MISSING_REQUIRED"),
]

_CALENDAR_POLICY_DENIALS = [
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("network_fetch_enabled", "NETWORK_FETCH_DENIED"),
    ("calendar_read_runtime_enabled", "CALENDAR_READ_RUNTIME_DENIED"),
    ("calendar_search_runtime_enabled", "CALENDAR_SEARCH_RUNTIME_DENIED"),
    ("event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
    ("event_update_enabled", "CALENDAR_EVENT_UPDATE_DENIED"),
    ("event_delete_enabled", "CALENDAR_EVENT_DELETE_DENIED"),
    ("invite_send_enabled", "CALENDAR_INVITE_SEND_DENIED"),
    ("meeting_link_exposure_enabled", "MEETING_LINK_EXPOSURE_DENIED"),
    ("location_exposure_enabled", "LOCATION_EXPOSURE_DENIED"),
    ("event_title_body_storage_enabled", "EVENT_TITLE_BODY_STORAGE_DENIED"),
    ("raw_invite_body_enabled", "RAW_INVITE_BODY_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
    ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
    ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_EMAIL_POLICY_DENIALS = [
    ("raw_body_enabled", "RAW_BODY_DENIED"),
    ("subject_text_enabled", "SUBJECT_TEXT_DENIED"),
    ("participant_identifiers_enabled", "PARTICIPANT_IDENTIFIERS_DENIED"),
    ("attachment_names_enabled", "ATTACHMENT_NAMES_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("email_fetch_runtime_enabled", "EMAIL_FETCH_RUNTIME_DENIED"),
    ("email_search_runtime_enabled", "EMAIL_SEARCH_RUNTIME_DENIED"),
    ("send_enabled", "EMAIL_SEND_DENIED"),
    ("delete_enabled", "EMAIL_DELETE_DENIED"),
    ("archive_enabled", "EMAIL_ARCHIVE_DENIED"),
    ("label_write_enabled", "EMAIL_LABEL_WRITE_DENIED"),
    ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
    ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
    ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_DRAFT_EMAIL_POLICY_DENIALS = [
    ("raw_body_enabled", "RAW_BODY_DENIED"),
    ("raw_draft_body_enabled", "RAW_DRAFT_BODY_DENIED"),
    ("subject_text_enabled", "SUBJECT_TEXT_DENIED"),
    ("participant_identifiers_enabled", "PARTICIPANT_IDENTIFIERS_DENIED"),
    ("attachment_names_enabled", "ATTACHMENT_NAMES_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("account_write_enabled", "ACCOUNT_WRITE_DENIED"),
    ("email_fetch_runtime_enabled", "EMAIL_FETCH_RUNTIME_DENIED"),
    ("email_search_runtime_enabled", "EMAIL_SEARCH_RUNTIME_DENIED"),
    ("reply_enabled", "EMAIL_REPLY_DENIED"),
    ("forward_enabled", "EMAIL_FORWARD_DENIED"),
    ("send_enabled", "EMAIL_SEND_DENIED"),
    ("delete_enabled", "EMAIL_DELETE_DENIED"),
    ("archive_enabled", "EMAIL_ARCHIVE_DENIED"),
    ("label_write_enabled", "EMAIL_LABEL_WRITE_DENIED"),
    ("move_enabled", "EMAIL_MOVE_DENIED"),
    ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("background_sync_enabled", "BACKGROUND_SYNC_DENIED"),
    ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
    ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
    ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_CALENDAR_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only", "READ_ONLY_REQUIRED"),
    ("metadata_only", "METADATA_ONLY_REQUIRED"),
    ("safe_refs_required", "SAFE_REFS_REQUIRED"),
    ("connector_runtime_missing", "CONNECTOR_RUNTIME_MISSING_REQUIRED"),
]

_EMAIL_RECORD_REQUIRED_TRUE = list(_CALENDAR_RECORD_REQUIRED_TRUE)

_DRAFT_EMAIL_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only", "READ_ONLY_REQUIRED"),
    ("draft_only", "DRAFT_ONLY_REQUIRED"),
    ("safe_refs_required", "SAFE_REFS_REQUIRED"),
    ("connector_runtime_missing", "CONNECTOR_RUNTIME_MISSING_REQUIRED"),
]

_CALENDAR_RECORD_DENIALS = [
    *[
        (field, reason)
        for field, reason in _CALENDAR_POLICY_DENIALS
        if field not in {"backend_route_enabled", "control_center_control_enabled"}
    ],
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]

_EMAIL_RECORD_DENIALS = [
    *[
        (field, reason)
        for field, reason in _EMAIL_POLICY_DENIALS
        if field not in {"backend_route_enabled", "control_center_control_enabled"}
    ],
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]

_DRAFT_EMAIL_RECORD_DENIALS = [
    *[
        (field, reason)
        for field, reason in _DRAFT_EMAIL_POLICY_DENIALS
        if field not in {"backend_route_enabled", "control_center_control_enabled"}
    ],
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]

_CALENDAR_FORBIDDEN_KEY_RE = re.compile(
    r"(raw|body|title|subject|agenda|invite|location|address|meeting[_-]?link|"
    r"conference|organizer|attendee[_-]?name|participant|attachment[_-]?name|"
    r"credential|password|token|secret|api[_-]?key|authorization|bearer|oauth|"
    r"session|cookie)",
    re.IGNORECASE,
)

_EMAIL_FORBIDDEN_KEY_RE = re.compile(
    r"(raw|body|subject|participant|recipient|email[_-]?address|"
    r"(?:^|[_-])address(?:[_-]|$)|(?:^|[_-])from(?:[_-]|$)|"
    r"(?:^|[_-])to(?:[_-]|$)|(?:^|[_-])cc(?:[_-]|$)|"
    r"(?:^|[_-])bcc(?:[_-]|$)|attachment[_-]?name|attachment|account[_-]?id|credential|"
    r"password|token|secret|api[_-]?key|authorization|bearer|oauth|session|"
    r"cookie)",
    re.IGNORECASE,
)

_DRAFT_EMAIL_FORBIDDEN_KEY_RE = re.compile(
    r"(raw|body|draft[_-]?body|subject|participant|recipient[_-]?name|"
    r"sender[_-]?name|email[_-]?address|(?:^|[_-])address(?:[_-]|$)|"
    r"(?:^|[_-])from(?:[_-]|$)|(?:^|[_-])to(?:[_-]|$)|"
    r"(?:^|[_-])cc(?:[_-]|$)|(?:^|[_-])bcc(?:[_-]|$)|"
    r"attachment[_-]?name|attachment|account[_-]?id|credential|password|"
    r"token|secret|api[_-]?key|authorization|bearer|oauth|session|cookie|"
    r"provider[_-]?payload|transcript|source[_-]?content)",
    re.IGNORECASE,
)

_CALENDAR_FORBIDDEN_VALUE_RE = re.compile(
    r"(@|https?://|meet\.google|zoom\.us|teams\.microsoft|webex|"
    r"\btitle\s*:|\bsubject\s*:|\blocation\s*:|\baddress\s*:|"
    r"\bagenda\s*:|\binvite\s*:|\battendee\s*:|\borganizer\s*:|"
    r"\.ics\b|\.pdf\b|\.docx\b|api[_-]?key|password|token|secret|bearer|oauth)",
    re.IGNORECASE,
)

_EMAIL_FORBIDDEN_VALUE_RE = re.compile(
    r"(@|\bsubject\s*:|\bbody\s*:|\bfrom\s*:|\bto\s*:|\bcc\s*:|\bbcc\s*:|"
    r"\bparticipant\s*:|\battachment\s*:|\.pdf\b|\.docx\b|\.ics\b|"
    r"api[_-]?key|password|token|secret|bearer|oauth)",
    re.IGNORECASE,
)

_DRAFT_EMAIL_FORBIDDEN_VALUE_RE = re.compile(
    r"(@|\bsubject\s*:|\bbody\s*:|\bdraft\s*:|\bfrom\s*:|\bto\s*:|"
    r"\bcc\s*:|\bbcc\s*:|\bparticipant\s*:|\brecipient\s*:|"
    r"\battachment\s*:|\.pdf\b|\.docx\b|\.ics\b|provider[_-]?payload|"
    r"raw[_-]?provider|transcript|raw\s+source|source\s+content|api[_-]?key|"
    r"password|token|secret|bearer|oauth)",
    re.IGNORECASE,
)
