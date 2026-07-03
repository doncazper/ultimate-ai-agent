from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.connectors.founder_loop_read_only_integration_contracts import (
    FCCDraftEmailResponseProposalEnvelope,
    build_fcc_calendar_event_metadata_envelope,
    build_fcc_draft_email_response_proposal_envelope,
)
from ultimate_ai_agent.core.execution.connector_delivery import (
    CONNECTOR_DELIVERY_SOURCE_FREEZE_REF,
    ConnectorDeliveryEnvelopeContract,
    ConnectorDeliveryTimelineEventContract,
    ConnectorDeliveryValidationContext,
    validate_connector_delivery_contract_payload,
    validate_connector_delivery_envelope,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CONNECTOR_DRAFT_PROPOSAL_READ_MODEL_SCHEMA_VERSION = (
    "connector_draft_proposal_read_model.v1"
)
CONNECTOR_DRAFT_PROPOSAL_ITEM_SCHEMA_VERSION = "connector_draft_proposal_item.v1"
CONNECTOR_DRAFT_PROPOSAL_CONTRACT_REF = (
    "contract-ref:connector-draft-only-proposals:v1"
)
CONNECTOR_DRAFT_PROPOSAL_PROOF_REF = "proof-ref:connector-draft-only-proposals:v1"
CONNECTOR_DRAFT_PROPOSAL_CLI_REF = "python scripts/inspect_connector_draft_proposals.py"
CONNECTOR_DRAFT_PROPOSAL_ROUTE_REF = (
    "GET /control-center/sources/readiness#connector_draft_proposals"
)
CONNECTOR_DRAFT_PROPOSAL_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:no-connector-write",
    "blocked-state:no-email-send",
    "blocked-state:no-calendar-write",
    "blocked-state:connector-draft-only:no-connector-runtime",
    "blocked-state:connector-draft-only:no-account-auth",
    "blocked-state:connector-draft-only:no-oauth",
    "blocked-state:connector-draft-only:no-auth-material-collection",
    "blocked-state:connector-draft-only:no-raw-source-ingestion",
    "blocked-state:connector-draft-only:no-connector-send",
    "blocked-state:connector-draft-only:no-connector-write",
    "blocked-state:connector-draft-only:no-background-sync",
    "blocked-state:connector-draft-only:no-scheduler",
    "blocked-state:connector-draft-only:no-provider-model-call",
    "blocked-state:connector-draft-only:no-memory-write",
    "blocked-state:connector-draft-only:no-context-injection",
    "blocked-state:connector-draft-only:no-production-authority",
)


class ConnectorDraftProposalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CONNECTOR_DRAFT_PROPOSAL_ITEM_SCHEMA_VERSION
    proposal_ref: str
    draft_ref: str
    draft_kind: Literal["email_response", "calendar_event_hold"]
    source_kind: Literal["email", "calendar"]
    status: Literal["draft_proposal_ready"]
    connector_ref: str
    channel_ref: str
    target_session_ref: str
    delivery_ref: str
    delivery_state: Literal["draft_created_metadata_only"] = (
        "draft_created_metadata_only"
    )
    delivery_event_ref: str
    source_metadata_refs: list[str] = Field(default_factory=list)
    redacted_subject_ref: str
    redacted_body_summary_ref: str
    draft_summary_ref: str
    response_outline_ref: str
    outbound_approval_ref: str
    approval_posture_ref: str
    approval_posture: str = (
        "draft_review_only_no_send_write_authority"
    )
    idempotency_ref: str
    rollback_posture_ref: str
    safe_disable_posture_ref: str
    audit_ref: str
    replay_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=lambda: [CONNECTOR_DRAFT_PROPOSAL_PROOF_REF])
    blocked_send_write_reason_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CONNECTOR_DRAFT_PROPOSAL_BLOCKED_AUTHORITY_REFS)
    )
    safe_summary: str
    redacted_outline: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Review the draft proposal refs; use a separately graduated exact lane "
        "before any send, write, account action, or connector runtime."
    )
    safe_refs_only: bool = True
    draft_only: bool = True
    metadata_only: bool = True
    approval_required_to_draft: bool = False
    approval_required_to_send: bool = True
    outbound_approval_ref_grants_authority: bool = False
    target_session_ref_grants_authority: bool = False
    raw_payloads_persisted: bool = False
    raw_body_persisted: bool = False
    raw_content_persisted: bool = False
    raw_draft_body_persisted: bool = False
    contact_data_persisted: bool = False
    credential_material_persisted: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_delivery_worker_enabled: bool = False
    background_sync_enabled: bool = False
    scheduler_enabled: bool = False
    provider_model_calls_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    delivery_execution_performed: bool = False
    connector_write_performed: bool = False
    connector_send_performed: bool = False
    account_sync_performed: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_item(self) -> "ConnectorDraftProposalItem":
        for ref in [
            self.proposal_ref,
            self.draft_ref,
            self.connector_ref,
            self.channel_ref,
            self.target_session_ref,
            self.delivery_ref,
            self.delivery_event_ref,
            self.redacted_subject_ref,
            self.redacted_body_summary_ref,
            self.draft_summary_ref,
            self.response_outline_ref,
            self.outbound_approval_ref,
            self.approval_posture_ref,
            self.idempotency_ref,
            self.rollback_posture_ref,
            self.safe_disable_posture_ref,
            self.audit_ref,
            self.replay_ref,
        ]:
            validate_execution_ref(ref, "connector_draft_proposal_ref")
        for refs in [
            self.source_metadata_refs,
            self.evidence_refs,
            self.proof_refs,
            self.blocked_send_write_reason_refs,
            self.blocked_authority_refs,
        ]:
            for ref in refs:
                validate_execution_ref(ref, "connector_draft_proposal_ref")
        for text in [
            self.schema_version,
            self.status,
            self.draft_kind,
            self.source_kind,
            self.delivery_state,
            self.approval_posture,
            self.safe_summary,
            self.next_safe_action,
            *self.redacted_outline,
        ]:
            validate_safe_execution_text(text, "connector_draft_proposal_text")
        denied_flags = [
            self.outbound_approval_ref_grants_authority,
            self.target_session_ref_grants_authority,
            self.raw_payloads_persisted,
            self.raw_body_persisted,
            self.raw_content_persisted,
            self.raw_draft_body_persisted,
            self.contact_data_persisted,
            self.credential_material_persisted,
            self.connector_runtime_enabled,
            self.account_auth_enabled,
            self.oauth_enabled,
            self.credential_collection_enabled,
            self.connector_write_enabled,
            self.connector_send_enabled,
            self.connector_delete_enabled,
            self.connector_delivery_worker_enabled,
            self.background_sync_enabled,
            self.scheduler_enabled,
            self.provider_model_calls_enabled,
            self.memory_write_enabled,
            self.context_injection_enabled,
            self.delivery_execution_performed,
            self.connector_write_performed,
            self.connector_send_performed,
            self.account_sync_performed,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_AUTHORITY_DENIED")
        if not self.safe_refs_only or not self.draft_only or not self.metadata_only:
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_SAFE_DRAFT_ONLY_REQUIRED")
        if not self.approval_required_to_send:
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_SEND_APPROVAL_REQUIRED")
        if self.approval_required_to_draft:
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_DRAFT_APPROVAL_NOT_REQUIRED")
        if validate_connector_delivery_contract_payload(_raw_checked_item_payload(self)):
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_RAW_CONTENT_DENIED")
        return self

    def storage_record(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json",
            exclude={
                "credential_material_persisted",
                "credential_collection_enabled",
            },
        )


class ConnectorDraftProposalReadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CONNECTOR_DRAFT_PROPOSAL_READ_MODEL_SCHEMA_VERSION
    source: str = "python_core_connector_draft_proposal_read_model"
    backend_owned: bool = True
    status: Literal["draft_proposals_ready_no_send_write"] = (
        "draft_proposals_ready_no_send_write"
    )
    contract_ref: str = CONNECTOR_DRAFT_PROPOSAL_CONTRACT_REF
    route_ref: str = CONNECTOR_DRAFT_PROPOSAL_ROUTE_REF
    cli_ref: str = CONNECTOR_DRAFT_PROPOSAL_CLI_REF
    proposal_count: int = Field(..., ge=0)
    proposals: list[ConnectorDraftProposalItem] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=lambda: [CONNECTOR_DRAFT_PROPOSAL_PROOF_REF])
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CONNECTOR_DRAFT_PROPOSAL_BLOCKED_AUTHORITY_REFS)
    )
    safe_summary: str = (
        "Connector draft proposals are backend-owned, safe-ref-only review "
        "artifacts. They create no connector send, write, account action, "
        "OAuth flow, background worker, provider/model call, memory write, or "
        "context injection."
    )
    next_safe_action: str = (
        "Review the draft refs locally. A later exact approved test-send lane "
        "is required before any connector send or write can occur."
    )
    safe_refs_only: bool = True
    draft_only: bool = True
    metadata_only: bool = True
    raw_payloads_persisted: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    oauth_enabled: bool = False
    credential_collection_enabled: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    background_sync_enabled: bool = False
    scheduler_enabled: bool = False
    provider_model_calls_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_read_model(self) -> "ConnectorDraftProposalReadModel":
        if not self.backend_owned:
            raise ValueError("CONNECTOR_DRAFT_PROPOSALS_BACKEND_OWNED_REQUIRED")
        if self.proposal_count != len(self.proposals):
            raise ValueError("CONNECTOR_DRAFT_PROPOSAL_COUNT_MISMATCH")
        for ref in [
            self.contract_ref,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "connector_draft_proposal_ref")
        for text in [
            self.schema_version,
            self.source,
            self.status,
            self.route_ref,
            self.cli_ref,
            self.safe_summary,
            self.next_safe_action,
        ]:
            validate_safe_execution_text(text, "connector_draft_proposal_text")
        denied_flags = [
            self.raw_payloads_persisted,
            self.connector_runtime_enabled,
            self.account_auth_enabled,
            self.oauth_enabled,
            self.credential_collection_enabled,
            self.connector_writes_enabled,
            self.connector_sends_enabled,
            self.background_sync_enabled,
            self.scheduler_enabled,
            self.provider_model_calls_enabled,
            self.memory_write_enabled,
            self.context_injection_enabled,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("CONNECTOR_DRAFT_PROPOSALS_AUTHORITY_DENIED")
        if not self.safe_refs_only or not self.draft_only or not self.metadata_only:
            raise ValueError("CONNECTOR_DRAFT_PROPOSALS_SAFE_DRAFT_ONLY_REQUIRED")
        if validate_connector_delivery_contract_payload(
            {
                "safe_summary": self.safe_summary,
                "next_safe_action": self.next_safe_action,
                "proposals": [
                    _raw_checked_item_payload(proposal) for proposal in self.proposals
                ],
            }
        ):
            raise ValueError("CONNECTOR_DRAFT_PROPOSALS_RAW_CONTENT_DENIED")
        return self

    def storage_record(self) -> dict[str, Any]:
        payload = self.model_dump(
            mode="json",
            exclude={"credential_collection_enabled", "proposals"},
        )
        payload["proposals"] = [proposal.storage_record() for proposal in self.proposals]
        return payload


def build_connector_draft_proposal_read_model() -> ConnectorDraftProposalReadModel:
    email = build_fcc_draft_email_response_proposal_envelope()
    calendar = build_fcc_calendar_event_metadata_envelope()
    proposals = [
        _email_draft_item(email),
        _calendar_draft_item(calendar),
    ]
    evidence_refs = sorted(
        dict.fromkeys(ref for proposal in proposals for ref in proposal.evidence_refs)
    )
    return ConnectorDraftProposalReadModel(
        proposal_count=len(proposals),
        proposals=proposals,
        evidence_refs=evidence_refs,
    )


def _email_draft_item(
    email: FCCDraftEmailResponseProposalEnvelope,
) -> ConnectorDraftProposalItem:
    envelope = _delivery_envelope(
        delivery_ref="connector-draft-delivery-ref:email-response:fcc-p1-009",
        run_ref="run-ref:connector-draft-only:email-response",
        connector_ref="connector-ref:email:draft-only",
        channel_ref="connector-channel-ref:email:response-draft",
        target_session_ref="target-session-ref:local-operator:email-draft-review",
        origin_ref=email.proposal_ref,
        outbound_approval_ref="approval-ref:connector-draft-only:email-send-future",
        idempotency_ref="idempotency-ref:connector-draft-only:email-response",
        redacted_subject_ref="redacted-subject-ref:connector-draft-only:email-response",
        redacted_body_summary_ref=email.draft_summary_ref,
        expected_receipt_ref="receipt-ref:connector-draft-only:email-response:expected",
        rollback_posture_ref="rollback-posture-ref:connector-draft-only:email-response",
        safe_disable_posture_ref="safe-disable-posture-ref:connector-draft-only:email-response",
        audit_ref=email.audit_ref,
        replay_ref=email.replay_ref,
        evidence_refs=email.evidence_refs,
    )
    event = ConnectorDeliveryTimelineEventContract.from_envelope(
        envelope,
        event_ref="connector-draft-event-ref:email-response:draft-created",
        delivery_state="draft_created_metadata_only",
        safe_summary="Email response draft proposal was created as metadata-only safe refs; no send or write occurred.",
    )
    return ConnectorDraftProposalItem(
        proposal_ref=email.proposal_ref,
        draft_ref="connector-draft-ref:email-response:fcc-p1-009",
        draft_kind="email_response",
        source_kind="email",
        status="draft_proposal_ready",
        connector_ref=envelope.connector_ref,
        channel_ref=envelope.channel_ref,
        target_session_ref=envelope.target_session_ref,
        delivery_ref=envelope.delivery_ref,
        delivery_event_ref=event.event_ref,
        source_metadata_refs=[
            *email.source_email_metadata_refs,
            email.thread_ref,
            email.sender_identity_ref,
            *email.recipient_identity_refs,
            email.account_identity_ref,
        ],
        redacted_subject_ref=envelope.redacted_subject_ref,
        redacted_body_summary_ref=envelope.redacted_body_summary_ref,
        draft_summary_ref=email.draft_summary_ref,
        response_outline_ref=email.response_outline_ref,
        outbound_approval_ref=envelope.outbound_approval_ref,
        approval_posture_ref="approval-posture-ref:connector-draft-only:email-send-required",
        idempotency_ref=envelope.idempotency_key_ref,
        rollback_posture_ref=envelope.rollback_posture_ref,
        safe_disable_posture_ref=envelope.safe_disable_posture_ref,
        audit_ref=envelope.audit_ref,
        replay_ref=envelope.replay_ref,
        evidence_refs=[*email.evidence_refs, *event.evidence_refs],
        proof_refs=[CONNECTOR_DRAFT_PROPOSAL_PROOF_REF, email.draft_proposal_contract_ref],
        blocked_send_write_reason_refs=list(email.blocked_send_write_states),
        safe_summary=email.redacted_draft_summary,
        redacted_outline=list(email.redacted_response_outline),
    )


def _calendar_draft_item(calendar: Any) -> ConnectorDraftProposalItem:
    envelope = _delivery_envelope(
        delivery_ref="connector-draft-delivery-ref:calendar-event:fcc-p1-007",
        run_ref="run-ref:connector-draft-only:calendar-event",
        connector_ref="connector-ref:calendar:draft-only",
        channel_ref="connector-channel-ref:calendar:event-draft",
        target_session_ref="target-session-ref:local-operator:calendar-draft-review",
        origin_ref=calendar.calendar_contract_ref,
        outbound_approval_ref="approval-ref:connector-draft-only:calendar-write-future",
        idempotency_ref="idempotency-ref:connector-draft-only:calendar-event",
        redacted_subject_ref="redacted-subject-ref:connector-draft-only:calendar-event",
        redacted_body_summary_ref=calendar.meeting_prep_summary_ref,
        expected_receipt_ref="receipt-ref:connector-draft-only:calendar-event:expected",
        rollback_posture_ref="rollback-posture-ref:connector-draft-only:calendar-event",
        safe_disable_posture_ref="safe-disable-posture-ref:connector-draft-only:calendar-event",
        audit_ref=calendar.audit_ref,
        replay_ref=calendar.replay_ref,
        evidence_refs=calendar.evidence_refs,
    )
    event = ConnectorDeliveryTimelineEventContract.from_envelope(
        envelope,
        event_ref="connector-draft-event-ref:calendar-event:draft-created",
        delivery_state="draft_created_metadata_only",
        safe_summary="Calendar event draft proposal was created as metadata-only safe refs; no event write or invite send occurred.",
    )
    return ConnectorDraftProposalItem(
        proposal_ref="connector-draft-proposal-ref:calendar-event:fcc-p1-007",
        draft_ref="connector-draft-ref:calendar-event:fcc-p1-007",
        draft_kind="calendar_event_hold",
        source_kind="calendar",
        status="draft_proposal_ready",
        connector_ref=envelope.connector_ref,
        channel_ref=envelope.channel_ref,
        target_session_ref=envelope.target_session_ref,
        delivery_ref=envelope.delivery_ref,
        delivery_event_ref=event.event_ref,
        source_metadata_refs=[
            calendar.event_ref,
            calendar.time_window_ref,
            *calendar.attendee_identity_refs,
            calendar.account_identity_ref,
        ],
        redacted_subject_ref=envelope.redacted_subject_ref,
        redacted_body_summary_ref=envelope.redacted_body_summary_ref,
        draft_summary_ref=calendar.meeting_prep_summary_ref,
        response_outline_ref="response-outline-ref:connector-draft-only:calendar-event",
        outbound_approval_ref=envelope.outbound_approval_ref,
        approval_posture_ref="approval-posture-ref:connector-draft-only:calendar-write-required",
        idempotency_ref=envelope.idempotency_key_ref,
        rollback_posture_ref=envelope.rollback_posture_ref,
        safe_disable_posture_ref=envelope.safe_disable_posture_ref,
        audit_ref=envelope.audit_ref,
        replay_ref=envelope.replay_ref,
        evidence_refs=[*calendar.evidence_refs, *event.evidence_refs],
        proof_refs=[CONNECTOR_DRAFT_PROPOSAL_PROOF_REF, calendar.calendar_contract_ref],
        blocked_send_write_reason_refs=[
            "blocked-state-ref:connector-draft-only:no-calendar-write",
            "blocked-state-ref:connector-draft-only:no-invite-send",
            "blocked-state-ref:connector-draft-only:no-account-action",
        ],
        safe_summary=(
            "Calendar draft proposal is a safe hold/outline over calendar metadata "
            "refs only; event create, update, invite send, and account actions remain blocked."
        ),
        redacted_outline=[
            "Review bounded calendar metadata refs.",
            "Prepare a draft hold outline for local operator review.",
            "Keep calendar writes and invite sends blocked until a later exact lane.",
        ],
    )


def _delivery_envelope(
    *,
    delivery_ref: str,
    run_ref: str,
    connector_ref: str,
    channel_ref: str,
    target_session_ref: str,
    origin_ref: str,
    outbound_approval_ref: str,
    idempotency_ref: str,
    redacted_subject_ref: str,
    redacted_body_summary_ref: str,
    expected_receipt_ref: str,
    rollback_posture_ref: str,
    safe_disable_posture_ref: str,
    audit_ref: str,
    replay_ref: str,
    evidence_refs: list[str],
) -> ConnectorDeliveryEnvelopeContract:
    envelope = ConnectorDeliveryEnvelopeContract(
        source_connector_safety_freeze_ref=CONNECTOR_DELIVERY_SOURCE_FREEZE_REF,
        delivery_ref=delivery_ref,
        run_ref=run_ref,
        connector_ref=connector_ref,
        channel_ref=channel_ref,
        target_session_ref=target_session_ref,
        origin_ref=origin_ref,
        origin_cleanup_posture_ref=f"origin-cleanup-posture-ref:{delivery_ref.replace(':', '-')}",
        outbound_approval_ref=outbound_approval_ref,
        idempotency_key_ref=idempotency_ref,
        redacted_subject_ref=redacted_subject_ref,
        redacted_body_summary_ref=redacted_body_summary_ref,
        evidence_refs=evidence_refs,
        expected_receipt_refs=[expected_receipt_ref],
        rollback_posture_ref=rollback_posture_ref,
        safe_disable_posture_ref=safe_disable_posture_ref,
        audit_ref=audit_ref,
        replay_ref=replay_ref,
    )
    decision = validate_connector_delivery_envelope(
        envelope,
        ConnectorDeliveryValidationContext(
            known_connector_refs=[connector_ref],
            known_channel_refs=[channel_ref],
            outbound_approval_ref=outbound_approval_ref,
            outbound_approval_state="approved_metadata_only",
        ),
    )
    if not decision.contract_valid or decision.delivery_permitted:
        raise ValueError("CONNECTOR_DRAFT_PROPOSAL_DELIVERY_CONTRACT_DENIED")
    return envelope


def _raw_checked_item_payload(item: ConnectorDraftProposalItem) -> dict[str, Any]:
    return {
        "proposal_ref": item.proposal_ref,
        "draft_ref": item.draft_ref,
        "connector_ref": item.connector_ref,
        "channel_ref": item.channel_ref,
        "target_session_ref": item.target_session_ref,
        "delivery_ref": item.delivery_ref,
        "delivery_event_ref": item.delivery_event_ref,
        "source_metadata_refs": list(item.source_metadata_refs),
        "redacted_subject_ref": item.redacted_subject_ref,
        "redacted_body_summary_ref": item.redacted_body_summary_ref,
        "draft_summary_ref": item.draft_summary_ref,
        "outline_ref": item.response_outline_ref,
        "outbound_approval_ref": item.outbound_approval_ref,
        "approval_posture_ref": item.approval_posture_ref,
        "idempotency_ref": item.idempotency_ref,
        "evidence_refs": list(item.evidence_refs),
        "proof_refs": list(item.proof_refs),
        "blocked_send_write_reason_refs": list(item.blocked_send_write_reason_refs),
        "safe_summary": item.safe_summary,
        "redacted_outline": list(item.redacted_outline),
        "next_safe_action": item.next_safe_action,
    }
