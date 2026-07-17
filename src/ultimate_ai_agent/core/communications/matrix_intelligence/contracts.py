from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .constants import (
    MATRIX_INTELLIGENCE_BUDGET_REF,
    MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS,
    MATRIX_INTELLIGENCE_DISCLOSURE_REF,
    MATRIX_INTELLIGENCE_KILL_SWITCH_REF,
    MATRIX_INTELLIGENCE_LANES,
    MATRIX_INTELLIGENCE_MAX_BYTES,
    MATRIX_INTELLIGENCE_MAX_EVENTS,
    MATRIX_INTELLIGENCE_MAX_TOKENS,
    MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS,
    MATRIX_INTELLIGENCE_PROVIDER_REF,
    MATRIX_INTELLIGENCE_REDACTION_REF,
    MATRIX_INTELLIGENCE_RETENTION_REF,
    MATRIX_INTELLIGENCE_RUNTIME_REF,
    MATRIX_INTELLIGENCE_SAFE_DISABLE_REF,
    MATRIX_INTELLIGENCE_SCHEMA_VERSION,
    MATRIX_INTELLIGENCE_TARGET_REF,
    MatrixIntelligenceFamily,
    MatrixIntelligenceOperation,
    matrix_intelligence_lane,
    matrix_intelligence_rollback_ref,
)


_SAFE_SUMMARY_DENY = re.compile(
    r"(?i)(?:"
    r"bearer\s+[a-z0-9._~-]+|"
    r"(?:api[_-]?key|password|secret|token)\s*[:=]|"
    r"file://|"
    r"(?:^|\s)/(?:users|home|private|tmp|var|etc|opt|volumes)/|"
    r"[a-z]:\\|"
    r"-----begin [a-z ]+private key-----"
    r")"
)


def stable_matrix_intelligence_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _safe_ref(value: str, field_name: str) -> str:
    validate_execution_ref(value, field_name)
    if len(value) > 240:
        raise ValueError(f"{field_name} exceeds safe reference length")
    return value


def _safe_refs(values: list[str] | tuple[str, ...], field_name: str) -> tuple[str, ...]:
    refs = tuple(dict.fromkeys(values))
    if len(refs) != len(values):
        raise ValueError(f"{field_name} must be unique")
    for ref in refs:
        _safe_ref(ref, field_name)
    return refs


def _safe_summary(value: str) -> str:
    stripped = " ".join(value.split())
    if not stripped or len(stripped) > 500 or _SAFE_SUMMARY_DENY.search(stripped):
        raise ValueError("MATRIX_INTELLIGENCE_SAFE_SUMMARY_DENIED")
    return stripped


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixRoomAIPolicyMode(str, Enum):
    off = "off"
    ask_each_time = "ask_each_time"
    scoped_allow = "scoped_allow"


class MatrixIntelligenceProposalKind(str, Enum):
    unread_summary = "unread_summary"
    period_summary = "period_summary"
    reply_draft = "reply_draft"
    open_questions = "open_questions"
    decisions = "decisions"
    commitments = "commitments"
    task_date_extraction = "task_date_extraction"
    translation = "translation"
    message = "message"
    meeting = "meeting"
    follow_up = "follow_up"
    task = "task"


class MatrixIntelligenceFamilyPosture(_Model):
    family: MatrixIntelligenceFamily
    authority_lane_refs: tuple[str, ...]
    status: Literal["accepted_request_scoped", "blocked_missing_exact_authority"]
    stage_b_runtime_enabled: StrictBool
    blocker_refs: tuple[str, ...] = ()
    safe_summary: str

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixIntelligenceFamilyPosture":
        _safe_refs(self.authority_lane_refs, "authority_lane_refs")
        _safe_refs(self.blocker_refs, "blocker_refs")
        _safe_summary(self.safe_summary)
        accepted = self.status == "accepted_request_scoped"
        if accepted != bool(self.stage_b_runtime_enabled):
            raise ValueError("MATRIX_INTELLIGENCE_FAMILY_RUNTIME_POSTURE_DRIFTED")
        if accepted == bool(self.blocker_refs):
            raise ValueError("MATRIX_INTELLIGENCE_FAMILY_BLOCKER_POSTURE_DRIFTED")
        return self


class MatrixIntelligencePosture(_Model):
    schema_version: Literal["uaa-matrix-intelligence-posture.v1"] = (
        "uaa-matrix-intelligence-posture.v1"
    )
    posture_ref: str
    runtime_status: Literal["partial_exact_local_lanes"] = "partial_exact_local_lanes"
    family_postures: tuple[MatrixIntelligenceFamilyPosture, ...]
    policy_modes: tuple[MatrixRoomAIPolicyMode, ...] = tuple(MatrixRoomAIPolicyMode)
    proposal_kinds: tuple[MatrixIntelligenceProposalKind, ...] = tuple(
        MatrixIntelligenceProposalKind
    )
    cross_surface_link_refs: tuple[str, ...]
    request_scoped_evaluation_required: Literal[True] = True
    standing_content_authority: Literal[False] = False
    provider_invocation_enabled: Literal[False] = False
    attachment_analysis_enabled: Literal[False] = False
    autonomous_send_enabled: Literal[False] = False
    automatic_memory_write_enabled: Literal[False] = False
    context_injection_enabled: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    desktop_only: Literal[True] = True
    safe_summary: str

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixIntelligencePosture":
        _safe_ref(self.posture_ref, "posture_ref")
        _safe_refs(self.cross_surface_link_refs, "cross_surface_link_refs")
        _safe_summary(self.safe_summary)
        if tuple(item.family for item in self.family_postures) != tuple(
            MatrixIntelligenceFamily
        ):
            raise ValueError("MATRIX_INTELLIGENCE_FAMILY_SET_DRIFTED")
        return self


class MatrixRoomAIPolicyRecord(_Model):
    schema_version: Literal["uaa-matrix-room-ai-policy.v1"] = (
        "uaa-matrix-room-ai-policy.v1"
    )
    policy_ref: str
    account_ref: str
    room_ref: str
    policy: MatrixRoomAIPolicyMode
    scope_ref: str
    context_grant_ref: str | None = None
    expires_at: datetime | None = None
    updated_at: datetime
    receipt_ref: str
    safe_disable_ref: Literal["safe-disable-ref:matrix-intelligence:enabled"] = (
        MATRIX_INTELLIGENCE_SAFE_DISABLE_REF
    )
    context_materialization_eligible: bool
    provider_invocation_authorized: Literal[False] = False
    autonomous_send_authorized: Literal[False] = False
    memory_write_authorized: Literal[False] = False
    context_injection_authorized: Literal[False] = False
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_policy(self) -> "MatrixRoomAIPolicyRecord":
        for field_name in (
            "policy_ref",
            "account_ref",
            "room_ref",
            "scope_ref",
            "receipt_ref",
            "safe_disable_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        if self.policy == MatrixRoomAIPolicyMode.scoped_allow:
            if self.context_grant_ref is None or self.expires_at is None:
                raise ValueError("MATRIX_INTELLIGENCE_SCOPED_ALLOW_GRANT_REQUIRED")
            _safe_ref(self.context_grant_ref, "context_grant_ref")
            if self.expires_at <= self.updated_at:
                raise ValueError("MATRIX_INTELLIGENCE_SCOPED_ALLOW_EXPIRED")
            if not self.context_materialization_eligible:
                raise ValueError("MATRIX_INTELLIGENCE_SCOPED_ALLOW_POSTURE_DRIFTED")
        elif self.context_grant_ref is not None or self.expires_at is not None:
            raise ValueError("MATRIX_INTELLIGENCE_NONSCOPED_GRANT_FORBIDDEN")
        elif self.context_materialization_eligible != (
            self.policy == MatrixRoomAIPolicyMode.ask_each_time
        ):
            raise ValueError("MATRIX_INTELLIGENCE_POLICY_ELIGIBILITY_DRIFTED")
        return self


class MatrixRoomContextManifest(_Model):
    schema_version: Literal["uaa-matrix-room-context-manifest.v1"] = (
        "uaa-matrix-room-context-manifest.v1"
    )
    context_manifest_ref: str
    context_receipt_ref: str
    account_ref: str
    room_ref: str
    event_range_ref: str
    event_refs: tuple[str, ...]
    content_fingerprint_refs: tuple[str, ...]
    source_count: int = Field(ge=1, le=MATRIX_INTELLIGENCE_MAX_EVENTS)
    content_unit_estimate: int = Field(ge=1, le=MATRIX_INTELLIGENCE_MAX_TOKENS)
    byte_count: int = Field(ge=1, le=MATRIX_INTELLIGENCE_MAX_BYTES)
    policy_ref: str
    context_grant_ref: str
    created_at: datetime
    expires_at: datetime
    disclosure_ref: Literal["disclosure-ref:matrix-intelligence:local-only"] = (
        MATRIX_INTELLIGENCE_DISCLOSURE_REF
    )
    retention_ref: Literal["retention-ref:matrix-intelligence:bounded-v1"] = (
        MATRIX_INTELLIGENCE_RETENTION_REF
    )
    redaction_ref: Literal["redaction-ref:matrix-intelligence:safe-v1"] = (
        MATRIX_INTELLIGENCE_REDACTION_REF
    )
    messages_treated_as_untrusted: Literal[True] = True
    content_free_manifest: Literal[True] = True
    raw_content_returned: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    hidden_context_injection: Literal[False] = False
    provider_invocation_performed: Literal[False] = False
    action_execution_performed: Literal[False] = False
    memory_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "MatrixRoomContextManifest":
        for field_name in (
            "context_manifest_ref",
            "context_receipt_ref",
            "account_ref",
            "room_ref",
            "event_range_ref",
            "policy_ref",
            "context_grant_ref",
            "disclosure_ref",
            "retention_ref",
            "redaction_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.event_refs, "event_refs")
        _safe_refs(self.content_fingerprint_refs, "content_fingerprint_refs")
        if self.source_count != len(self.event_refs) or self.source_count != len(
            self.content_fingerprint_refs
        ):
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_SOURCE_COUNT_DRIFTED")
        if self.expires_at <= self.created_at:
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_EXPIRY_INVALID")
        if self.expires_at > self.created_at + timedelta(
            seconds=MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS
        ):
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_TTL_EXCEEDED")
        return self


class MatrixIntelligenceProposalDraft(_Model):
    proposal_ref: str
    proposal_kind: MatrixIntelligenceProposalKind
    account_ref: str
    room_ref: str
    context_manifest_ref: str
    source_refs: tuple[str, ...] = Field(min_length=1, max_length=64)
    cross_surface_refs: tuple[str, ...] = Field(default=(), max_length=32)
    confidence_ref: str
    safe_summary: str = Field(max_length=500)
    exact_destination_ref: str | None = None
    exact_time_ref: str | None = None
    expires_at: datetime
    model_output_is_authority: Literal[False] = False
    action_authority_granted: Literal[False] = False
    memory_write_authorized: Literal[False] = False
    autonomous_send_authorized: Literal[False] = False
    raw_model_output_included: Literal[False] = False
    raw_source_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_draft(self) -> "MatrixIntelligenceProposalDraft":
        for field_name in (
            "proposal_ref",
            "account_ref",
            "room_ref",
            "context_manifest_ref",
            "confidence_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        for optional_name in ("exact_destination_ref", "exact_time_ref"):
            optional_ref = getattr(self, optional_name)
            if optional_ref is not None:
                _safe_ref(optional_ref, optional_name)
        _safe_refs(self.source_refs, "source_refs")
        _safe_refs(self.cross_surface_refs, "cross_surface_refs")
        self.safe_summary = _safe_summary(self.safe_summary)
        if (
            self.proposal_kind
            in {
                MatrixIntelligenceProposalKind.message,
                MatrixIntelligenceProposalKind.meeting,
                MatrixIntelligenceProposalKind.follow_up,
                MatrixIntelligenceProposalKind.task,
                MatrixIntelligenceProposalKind.reply_draft,
            }
            and self.exact_destination_ref is None
        ):
            raise ValueError("MATRIX_INTELLIGENCE_EXACT_DESTINATION_REQUIRED")
        if self.proposal_kind == MatrixIntelligenceProposalKind.meeting and (
            self.exact_time_ref is None
        ):
            raise ValueError("MATRIX_INTELLIGENCE_EXACT_TIME_REQUIRED")
        return self


def matrix_intelligence_proposal_fingerprint_ref(
    draft: MatrixIntelligenceProposalDraft,
) -> str:
    return stable_matrix_intelligence_ref(
        "proposal-fingerprint-ref:matrix-intelligence",
        draft.model_dump(mode="json"),
    )


class MatrixIntelligenceProposalRecord(MatrixIntelligenceProposalDraft):
    created_at: datetime
    receipt_ref: str
    proposal_fingerprint_ref: str
    receipt_status: Literal["persisted_review_only"] = "persisted_review_only"
    review_required: Literal[True] = True
    proposal_only: Literal[True] = True
    execution_path_present: Literal[False] = False

    @model_validator(mode="after")
    def validate_record(self) -> "MatrixIntelligenceProposalRecord":
        _safe_ref(self.receipt_ref, "receipt_ref")
        _safe_ref(self.proposal_fingerprint_ref, "proposal_fingerprint_ref")
        draft = MatrixIntelligenceProposalDraft.model_validate(
            self.model_dump(
                exclude={
                    "created_at",
                    "receipt_ref",
                    "proposal_fingerprint_ref",
                    "receipt_status",
                    "review_required",
                    "proposal_only",
                    "execution_path_present",
                }
            )
        )
        if (
            self.proposal_fingerprint_ref
            != matrix_intelligence_proposal_fingerprint_ref(draft)
        ):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_FINGERPRINT_MISMATCH")
        if self.expires_at <= self.created_at or self.expires_at > (
            self.created_at
            + timedelta(seconds=MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS)
        ):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_TTL_INVALID")
        return self


class MatrixIntelligenceReadiness(_Model):
    schema_version: Literal["uaa-matrix-intelligence-readiness.v1"] = (
        "uaa-matrix-intelligence-readiness.v1"
    )
    readiness_ref: str
    request_fingerprint_ref: str
    adapter_ref: str
    status: Literal["ready", "blocked", "unknown"]
    observed_at: datetime
    expires_at: datetime
    kill_switch_engaged: StrictBool
    safe_disable_active: StrictBool
    local_store_available: StrictBool
    transient_context_adapter_available: StrictBool
    reason_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_readiness(self) -> "MatrixIntelligenceReadiness":
        for field_name in (
            "readiness_ref",
            "request_fingerprint_ref",
            "adapter_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.reason_refs, "reason_refs")
        if self.expires_at <= self.observed_at:
            raise ValueError("MATRIX_INTELLIGENCE_READINESS_EXPIRY_INVALID")
        return self


class MatrixIntelligenceCommand(_Model):
    schema_version: Literal["uaa-matrix-intelligence.v1"] = (
        MATRIX_INTELLIGENCE_SCHEMA_VERSION
    )
    operation: MatrixIntelligenceOperation
    request_ref: str
    task_ref: str
    mission_ref: str
    run_ref: str
    dispatch_ref: str
    idempotency_ref: str
    lease_ref: str
    account_ref: str
    room_ref: str
    event_range_ref: str
    event_refs: tuple[str, ...] = Field(
        default=(), max_length=MATRIX_INTELLIGENCE_MAX_EVENTS
    )
    policy_ref: str
    context_grant_ref: str | None = None
    proposal_ref: str | None = None
    proposal_fingerprint_ref: str | None = None
    requested_policy: MatrixRoomAIPolicyMode | None = None
    policy_expires_at: datetime | None = None
    target_ref: Literal["target-ref:communications:matrix-intelligence-exact-room"] = (
        MATRIX_INTELLIGENCE_TARGET_REF
    )
    provider_ref: Literal["provider-ref:communications:matrix-local-core"] = (
        MATRIX_INTELLIGENCE_PROVIDER_REF
    )
    runtime_ref: Literal["runtime-ref:matrix-intelligence:local-core-v1"] = (
        MATRIX_INTELLIGENCE_RUNTIME_REF
    )
    model_destination_ref: Literal[
        "model-destination-ref:matrix-intelligence:blocked"
    ] = "model-destination-ref:matrix-intelligence:blocked"
    disclosure_ref: Literal["disclosure-ref:matrix-intelligence:local-only"] = (
        MATRIX_INTELLIGENCE_DISCLOSURE_REF
    )
    retention_ref: Literal["retention-ref:matrix-intelligence:bounded-v1"] = (
        MATRIX_INTELLIGENCE_RETENTION_REF
    )
    redaction_ref: Literal["redaction-ref:matrix-intelligence:safe-v1"] = (
        MATRIX_INTELLIGENCE_REDACTION_REF
    )
    budget_ref: Literal["budget-ref:matrix-intelligence:bounded-local-v1"] = (
        MATRIX_INTELLIGENCE_BUDGET_REF
    )
    safe_disable_ref: Literal["safe-disable-ref:matrix-intelligence:enabled"] = (
        MATRIX_INTELLIGENCE_SAFE_DISABLE_REF
    )
    kill_switch_ref: Literal["kill-switch-ref:matrix-intelligence:clear"] = (
        MATRIX_INTELLIGENCE_KILL_SWITCH_REF
    )
    rollback_ref: str
    readiness_ref: str
    max_events: int = Field(
        default=MATRIX_INTELLIGENCE_MAX_EVENTS, ge=1, le=MATRIX_INTELLIGENCE_MAX_EVENTS
    )
    max_tokens: int = Field(
        default=MATRIX_INTELLIGENCE_MAX_TOKENS, ge=1, le=MATRIX_INTELLIGENCE_MAX_TOKENS
    )
    max_bytes: int = Field(
        default=MATRIX_INTELLIGENCE_MAX_BYTES, ge=1, le=MATRIX_INTELLIGENCE_MAX_BYTES
    )
    context_ttl_seconds: int = Field(
        default=MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS,
        ge=1,
        le=MATRIX_INTELLIGENCE_CONTEXT_TTL_SECONDS,
    )
    proposal_ttl_seconds: int = Field(
        default=MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS,
        ge=1,
        le=MATRIX_INTELLIGENCE_PROPOSAL_TTL_SECONDS,
    )
    request_created_at: datetime
    start_deadline: datetime
    request_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_command(self) -> "MatrixIntelligenceCommand":
        for field_name in (
            "request_ref",
            "task_ref",
            "mission_ref",
            "run_ref",
            "dispatch_ref",
            "idempotency_ref",
            "lease_ref",
            "account_ref",
            "room_ref",
            "event_range_ref",
            "policy_ref",
            "target_ref",
            "provider_ref",
            "runtime_ref",
            "model_destination_ref",
            "disclosure_ref",
            "retention_ref",
            "redaction_ref",
            "budget_ref",
            "safe_disable_ref",
            "kill_switch_ref",
            "rollback_ref",
            "readiness_ref",
            "request_fingerprint_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.event_refs, "event_refs")
        for field_name in (
            "context_grant_ref",
            "proposal_ref",
            "proposal_fingerprint_ref",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _safe_ref(value, field_name)
        if self.start_deadline <= self.request_created_at:
            raise ValueError("MATRIX_INTELLIGENCE_START_DEADLINE_INVALID")
        expected_rollback = matrix_intelligence_rollback_ref(self.operation)
        if self.rollback_ref != expected_rollback:
            raise ValueError("MATRIX_INTELLIGENCE_ROLLBACK_REF_MISMATCH")
        policy_write = (
            self.operation == MatrixIntelligenceOperation.room_ai_policy_write
        )
        if policy_write != (self.requested_policy is not None):
            raise ValueError("MATRIX_INTELLIGENCE_POLICY_MUTATION_SCOPE_INVALID")
        if (
            policy_write
            and self.requested_policy == MatrixRoomAIPolicyMode.scoped_allow
        ):
            if self.context_grant_ref is None or self.policy_expires_at is None:
                raise ValueError("MATRIX_INTELLIGENCE_SCOPED_POLICY_BINDING_REQUIRED")
        elif self.policy_expires_at is not None:
            raise ValueError("MATRIX_INTELLIGENCE_POLICY_EXPIRY_SCOPE_INVALID")
        context_op = self.operation == MatrixIntelligenceOperation.context_materialize
        proposal_persist = (
            self.operation == MatrixIntelligenceOperation.proposal_persist
        )
        if context_op and not self.event_refs:
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_EVENT_SCOPE_INVALID")
        if not (context_op or proposal_persist) and self.event_refs:
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_EVENT_SCOPE_INVALID")
        grant_expected = context_op or (
            policy_write
            and self.requested_policy == MatrixRoomAIPolicyMode.scoped_allow
        )
        if grant_expected != (self.context_grant_ref is not None):
            raise ValueError("MATRIX_INTELLIGENCE_CONTEXT_GRANT_SCOPE_INVALID")
        proposal_ops = {
            MatrixIntelligenceOperation.proposal_read,
            MatrixIntelligenceOperation.proposal_persist,
            MatrixIntelligenceOperation.proposal_delete,
        }
        if (self.operation in proposal_ops) != (self.proposal_ref is not None):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_SCOPE_INVALID")
        if proposal_persist != (self.proposal_fingerprint_ref is not None):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_FINGERPRINT_SCOPE_INVALID")
        expected = matrix_intelligence_request_fingerprint_ref(self)
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_INTELLIGENCE_REQUEST_FINGERPRINT_MISMATCH")
        return self


def matrix_intelligence_request_fingerprint_ref(
    command: MatrixIntelligenceCommand | dict[str, Any],
) -> str:
    if isinstance(command, MatrixIntelligenceCommand):
        payload = command.model_dump(mode="python", exclude={"request_fingerprint_ref"})
    else:
        candidate = MatrixIntelligenceCommand.model_construct(
            **dict(command),
            request_fingerprint_ref="request-fingerprint-ref:matrix-intelligence:pending",
        )
        payload = candidate.model_dump(
            mode="python", exclude={"request_fingerprint_ref"}
        )
    return stable_matrix_intelligence_ref(
        "request-fingerprint-ref:matrix-intelligence", payload
    )


def build_matrix_intelligence_command(**payload: object) -> MatrixIntelligenceCommand:
    candidate = MatrixIntelligenceCommand.model_construct(
        **payload,
        request_fingerprint_ref="request-fingerprint-ref:matrix-intelligence:pending",
    )
    normalized = candidate.model_dump(
        mode="python", exclude={"request_fingerprint_ref"}
    )
    normalized["request_fingerprint_ref"] = matrix_intelligence_request_fingerprint_ref(
        normalized
    )
    return MatrixIntelligenceCommand.model_validate(normalized)


def matrix_intelligence_exact_resource_refs(
    command: MatrixIntelligenceCommand,
) -> tuple[str, ...]:
    lane = matrix_intelligence_lane(command.operation)
    refs = [
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.idempotency_ref,
        command.lease_ref,
        command.target_ref,
        command.provider_ref,
        command.runtime_ref,
        command.model_destination_ref,
        command.account_ref,
        command.room_ref,
        command.event_range_ref,
        command.policy_ref,
        command.disclosure_ref,
        command.retention_ref,
        command.redaction_ref,
        command.budget_ref,
        command.readiness_ref,
        command.safe_disable_ref,
        command.kill_switch_ref,
        command.rollback_ref,
        command.request_fingerprint_ref,
        stable_matrix_intelligence_ref(
            "deadline-ref:matrix-intelligence",
            {"start_deadline": command.start_deadline.isoformat()},
        ),
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
        *command.event_refs,
    ]
    refs.extend(
        ref
        for ref in (
            command.context_grant_ref,
            command.proposal_ref,
            command.proposal_fingerprint_ref,
        )
        if ref is not None
    )
    return tuple(dict.fromkeys(refs))


class MatrixIntelligenceDispatchMetadata(_Model):
    command: MatrixIntelligenceCommand


class MatrixIntelligenceCommandProposal(_Model):
    schema_version: Literal["uaa-matrix-intelligence-command-proposal.v1"] = (
        "uaa-matrix-intelligence-command-proposal.v1"
    )
    proposal_ref: str
    operation: MatrixIntelligenceOperation
    family: MatrixIntelligenceFamily
    request_fingerprint_ref: str
    exact_resource_refs: tuple[str, ...]
    approval_required: Literal[True] = True
    exact_session_lease_required: Literal[True] = True
    provider_call_enabled: Literal[False] = False
    attachment_analysis_enabled: Literal[False] = False
    autonomous_send_enabled: Literal[False] = False
    memory_write_enabled: Literal[False] = False
    raw_content_included: Literal[False] = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_proposal(self) -> "MatrixIntelligenceCommandProposal":
        _safe_ref(self.proposal_ref, "proposal_ref")
        _safe_ref(self.request_fingerprint_ref, "request_fingerprint_ref")
        _safe_refs(self.exact_resource_refs, "exact_resource_refs")
        _safe_summary(self.safe_summary)
        return self


def build_matrix_intelligence_command_proposal(
    command: MatrixIntelligenceCommand,
) -> MatrixIntelligenceCommandProposal:
    lane = matrix_intelligence_lane(command.operation)
    return MatrixIntelligenceCommandProposal(
        proposal_ref=stable_matrix_intelligence_ref(
            "proposal-ref:matrix-intelligence-command",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        operation=command.operation,
        family=lane.family,
        request_fingerprint_ref=command.request_fingerprint_ref,
        exact_resource_refs=matrix_intelligence_exact_resource_refs(command),
        safe_summary="Review one exact room-scoped Matrix intelligence operation; no provider call, send, action, or Memory write is authorized.",
    )


def build_default_matrix_intelligence_posture() -> MatrixIntelligencePosture:
    context_lanes = tuple(
        lane.lane_ref
        for lane in MATRIX_INTELLIGENCE_LANES.values()
        if lane.family == MatrixIntelligenceFamily.context_materialization
    )
    proposal_lanes = tuple(
        lane.lane_ref
        for lane in MATRIX_INTELLIGENCE_LANES.values()
        if lane.family == MatrixIntelligenceFamily.proposal_persistence
    )
    families = (
        MatrixIntelligenceFamilyPosture(
            family=MatrixIntelligenceFamily.context_materialization,
            authority_lane_refs=context_lanes,
            status="accepted_request_scoped",
            stage_b_runtime_enabled=True,
            safe_summary="Exact room policy and transient context manifest lanes are accepted only after fresh request-scoped approval, lease, policy, budget, readiness, and scope evaluation.",
        ),
        MatrixIntelligenceFamilyPosture(
            family=MatrixIntelligenceFamily.provider_invocation,
            authority_lane_refs=(
                "authority-lane-ref:matrix-intelligence-provider-invoke",
            ),
            status="blocked_missing_exact_authority",
            stage_b_runtime_enabled=False,
            blocker_refs=(
                "blocked-reason-ref:msg-mx:model-provider-runtime-prohibited",
                "blocked-reason-ref:msg-mx:model-context-authority-not-accepted",
            ),
            safe_summary="Model and provider invocation remains blocked; this milestone adds no runtime model or provider call.",
        ),
        MatrixIntelligenceFamilyPosture(
            family=MatrixIntelligenceFamily.proposal_persistence,
            authority_lane_refs=proposal_lanes,
            status="accepted_request_scoped",
            stage_b_runtime_enabled=True,
            safe_summary="Redacted proposal metadata may be persisted, read, or deleted only for one exact account, room, proposal, and idempotency scope.",
        ),
        MatrixIntelligenceFamilyPosture(
            family=MatrixIntelligenceFamily.attachment_analysis,
            authority_lane_refs=(
                "authority-lane-ref:matrix-intelligence-attachment-materialize",
                "authority-lane-ref:matrix-intelligence-attachment-scan",
                "authority-lane-ref:matrix-intelligence-attachment-analyze",
                "authority-lane-ref:matrix-intelligence-attachment-cleanup",
            ),
            status="blocked_missing_exact_authority",
            stage_b_runtime_enabled=False,
            blocker_refs=(
                "blocked-reason-ref:msg-mx:attachment-scanner-adapter-missing",
                "blocked-reason-ref:msg-mx:attachment-composite-binding-not-proven",
            ),
            safe_summary="Attachment intelligence remains blocked because materialization, scanner, analysis, and cleanup have not passed as one exact composite family.",
        ),
    )
    return MatrixIntelligencePosture(
        posture_ref="posture-ref:matrix-intelligence:partial-exact-local-v1",
        family_postures=families,
        cross_surface_link_refs=(
            "surface-ref:crm:safe-link-only",
            "surface-ref:calendar:safe-link-only",
            "surface-ref:work-board:safe-link-only",
            "surface-ref:knowledge:safe-link-only",
            "surface-ref:communications:safe-link-only",
        ),
        safe_summary="Room AI policy, transient context manifests, and redacted proposal records have exact local lanes; model invocation, attachment analysis, autonomous send, and automatic Memory remain blocked.",
    )


__all__ = [
    "MatrixIntelligenceCommand",
    "MatrixIntelligenceCommandProposal",
    "MatrixIntelligenceDispatchMetadata",
    "MatrixIntelligenceFamilyPosture",
    "MatrixIntelligencePosture",
    "MatrixIntelligenceProposalDraft",
    "MatrixIntelligenceProposalKind",
    "MatrixIntelligenceProposalRecord",
    "MatrixIntelligenceReadiness",
    "MatrixRoomAIPolicyMode",
    "MatrixRoomAIPolicyRecord",
    "MatrixRoomContextManifest",
    "build_default_matrix_intelligence_posture",
    "build_matrix_intelligence_command",
    "build_matrix_intelligence_command_proposal",
    "matrix_intelligence_exact_resource_refs",
    "matrix_intelligence_proposal_fingerprint_ref",
    "matrix_intelligence_request_fingerprint_ref",
    "stable_matrix_intelligence_ref",
]
