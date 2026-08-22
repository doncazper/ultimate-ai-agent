"""Encrypted Inbox and source-artifact workbench for ECO-007.

The repository owns local source bindings, source artifacts, threads, and
review-only proposals.  It deliberately provides no connector read, account
authentication, background sync, model call, or target-domain mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.local_data import (
    ArchiveRecord,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    LocalRecord,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_INBOX_SCHEMA_VERSION = "uaa-eco-007-inbox-source-workbench.v1"
ECO_INBOX_MUTATION_ACTION = "ecosystem.inbox.apply"
ECO_INBOX_MODULE_REF = "module-ref:inbox"
ECO_INBOX_BINDING_RECORD_KIND_REF = "record-kind-ref:inbox-source-binding"
ECO_INBOX_ARTIFACT_RECORD_KIND_REF = "record-kind-ref:inbox-source-artifact"
ECO_INBOX_THREAD_RECORD_KIND_REF = "record-kind-ref:inbox-conversation-thread"
ECO_INBOX_PROPOSAL_RECORD_KIND_REF = "record-kind-ref:inbox-source-proposal"
ECO_INBOX_DEFAULT_RETENTION_REF = "retention-ref:inbox-workspace-default"

_ALL_BINDINGS_TERM = "inbox-source-binding:all"
_ALL_ARTIFACTS_TERM = "inbox-source-artifact:all"
_ALL_THREADS_TERM = "inbox-conversation-thread:all"
_ALL_PROPOSALS_TERM = "inbox-source-proposal:all"
_MAX_CONTENT_BYTES = 512 * 1024
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`(:=,\[])(?:~[/\\]|"
    r"/(?:users|home|usr|var|private|tmp|etc)(?:/|$)|[a-z]:[/\\]|\\\\[^\\\s]+\\)"
)
_TOKEN_RE = re.compile(r"[^\W_][\w-]*", re.UNICODE)


class InboxError(RuntimeError):
    """Fail-closed Inbox error with a content-free stable code."""


class InboxConflict(InboxError):
    pass


class InboxSourceMode(str, Enum):
    manual = "manual"
    synthetic = "synthetic"


class InboxBindingState(str, Enum):
    ready = "ready"
    disabled = "disabled"


class InboxPrivacyScope(str, Enum):
    workspace = "workspace"
    restricted_private = "restricted_private"


class InboxArtifactKind(str, Enum):
    email = "email"
    message = "message"
    meeting = "meeting"
    form = "form"
    file = "file"
    note = "note"
    newsletter = "newsletter"
    receipt = "receipt"
    transactional = "transactional"
    lead_intake = "lead_intake"


class InboxTriageState(str, Enum):
    untriaged = "untriaged"
    review = "review"
    linked = "linked"
    deferred = "deferred"


class InboxLinkKind(str, Enum):
    relates_to = "relates_to"
    derived_from = "derived_from"
    supports = "supports"


class InboxProposalKind(str, Enum):
    task = "task"
    event = "event"
    crm_update = "crm_update"
    board_placement = "board_placement"
    communication_draft = "communication_draft"
    defer = "defer"
    archive = "archive"


class InboxProposalReviewState(str, Enum):
    proposed = "proposed"
    accepted_for_changeset = "accepted_for_changeset"
    rejected = "rejected"
    superseded = "superseded"


class _InboxModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if (
        not _SAFE_REF_RE.fullmatch(value)
        or _RAW_PATH_RE.search(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"ECO_INBOX_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_INBOX_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _canonical_timestamp(value: str, code: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(code) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{code}_TIMEZONE_REQUIRED")
    # Keep the explicit UTC offset because Python 3.10's fromisoformat does not
    # accept the trailing-Z form used by newer interpreters.
    return parsed.astimezone(timezone.utc).isoformat(timespec="auto")


def _timestamps_equal(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return left is right
    return datetime.fromisoformat(
        left.replace("Z", "+00:00")
    ) == datetime.fromisoformat(right.replace("Z", "+00:00"))


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _content_ref(content: str) -> str:
    return _stable_ref("inbox-content-ref", content)


def _hashed_term(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _private_search_terms(*values: str, maximum: int = 60) -> tuple[str, ...]:
    terms: dict[str, None] = {}
    for value in values:
        for token in _TOKEN_RE.findall(value.casefold()):
            if 1 < len(token) <= 128:
                terms.setdefault(token, None)
            if len(terms) >= maximum:
                return tuple(terms)
    return tuple(terms)


def _all_private_tokens(*values: str) -> frozenset[str]:
    return frozenset(
        token
        for value in values
        for token in _TOKEN_RE.findall(value.casefold())
        if 1 < len(token) <= 128
    )


class InboxSourceBinding(_InboxModel):
    schema_version: Literal["uaa-eco-007-inbox-source-workbench.v1"] = (
        ECO_INBOX_SCHEMA_VERSION
    )
    workspace_ref: str
    binding_ref: str
    source_mode: InboxSourceMode
    source_type_ref: str
    display_name: str = Field(..., repr=False)
    privacy_scope: InboxPrivacyScope = InboxPrivacyScope.workspace
    state: InboxBindingState = InboxBindingState.ready
    retention_ref: str = ECO_INBOX_DEFAULT_RETENTION_REF
    allowed_surface_refs: tuple[str, ...] = (
        "surface-ref:inbox",
        "surface-ref:today",
        "surface-ref:morning-briefing",
    )
    connector_read_enabled: Literal[False] = False
    account_auth_enabled: Literal[False] = False
    background_sync_enabled: Literal[False] = False
    external_write_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_binding(self) -> "InboxSourceBinding":
        for field_name in (
            "workspace_ref",
            "binding_ref",
            "source_type_ref",
            "retention_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.allowed_surface_refs, "allowed_surface_ref")
        _private_text(
            self.display_name,
            maximum=1_024,
            code="ECO_INBOX_BINDING_DISPLAY_NAME_INVALID",
        )
        if not self.allowed_surface_refs:
            raise ValueError("ECO_INBOX_BINDING_SURFACE_REQUIRED")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "inbox-binding-summary-ref",
            {
                "binding_ref": self.binding_ref,
                "privacy_scope": self.privacy_scope.value,
                "source_mode": self.source_mode.value,
                "state": self.state.value,
            },
        )


class InboxEntityLink(_InboxModel):
    workspace_ref: str
    entity_ref: str
    owner_app: CanonicalOwnerId
    link_kind: InboxLinkKind = InboxLinkKind.relates_to

    @model_validator(mode="after")
    def validate_link(self) -> "InboxEntityLink":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.entity_ref, "entity_ref")
        return self


class InboxSourceArtifact(_InboxModel):
    schema_version: Literal["uaa-eco-007-inbox-source-workbench.v1"] = (
        ECO_INBOX_SCHEMA_VERSION
    )
    workspace_ref: str
    artifact_ref: str
    binding_ref: str
    source_mode: InboxSourceMode
    artifact_kind: InboxArtifactKind
    title: str = Field(..., repr=False)
    content: str = Field(..., repr=False)
    content_ref: str
    source_locator_ref: str
    received_at: str
    privacy_scope: InboxPrivacyScope = InboxPrivacyScope.workspace
    triage_state: InboxTriageState = InboxTriageState.untriaged
    classification_ref: str = "classification-ref:unreviewed"
    thread_ref: str | None = None
    participant_refs: tuple[str, ...] = Field(default=(), max_length=128)
    attachment_refs: tuple[str, ...] = Field(default=(), max_length=128)
    tag_refs: tuple[str, ...] = Field(default=(), max_length=64)
    links: tuple[InboxEntityLink, ...] = Field(default=(), max_length=64)
    deferred_until: str | None = None
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=64)
    retention_ref: str = ECO_INBOX_DEFAULT_RETENTION_REF
    expires_at: str | None = None
    external_read_performed: Literal[False] = False
    untrusted_content_has_authority: Literal[False] = False
    model_call_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "InboxSourceArtifact":
        for field_name in (
            "workspace_ref",
            "artifact_ref",
            "binding_ref",
            "content_ref",
            "source_locator_ref",
            "classification_ref",
            "retention_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.thread_ref is not None:
            _validate_ref(self.thread_ref, "thread_ref")
        for field_name in (
            "participant_refs",
            "attachment_refs",
            "tag_refs",
            "evidence_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        if len({link.entity_ref for link in self.links}) != len(self.links):
            raise ValueError("ECO_INBOX_ARTIFACT_DUPLICATE_LINK")
        if any(link.workspace_ref != self.workspace_ref for link in self.links):
            raise ValueError("ECO_INBOX_ARTIFACT_CROSS_WORKSPACE_LINK_DENIED")
        _private_text(
            self.title,
            maximum=4_096,
            code="ECO_INBOX_ARTIFACT_TITLE_INVALID",
        )
        _private_text(
            self.content,
            maximum=_MAX_CONTENT_BYTES,
            code="ECO_INBOX_ARTIFACT_CONTENT_INVALID",
        )
        if contains_obvious_secret(self.content):
            raise ValueError("ECO_INBOX_ARTIFACT_SECRET_LIKE_CONTENT_DENIED")
        if self.content_ref != _content_ref(self.content):
            raise ValueError("ECO_INBOX_ARTIFACT_CONTENT_REF_MISMATCH")
        object.__setattr__(
            self,
            "received_at",
            _canonical_timestamp(
                self.received_at, "ECO_INBOX_ARTIFACT_RECEIVED_AT_INVALID"
            ),
        )
        if self.deferred_until is not None:
            object.__setattr__(
                self,
                "deferred_until",
                _canonical_timestamp(
                    self.deferred_until,
                    "ECO_INBOX_ARTIFACT_DEFERRED_UNTIL_INVALID",
                ),
            )
        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _canonical_timestamp(
                    self.expires_at, "ECO_INBOX_ARTIFACT_EXPIRES_AT_INVALID"
                ),
            )
        if self.triage_state == InboxTriageState.linked and not self.links:
            raise ValueError("ECO_INBOX_ARTIFACT_LINK_REQUIRED")
        if self.triage_state == InboxTriageState.deferred:
            if self.deferred_until is None:
                raise ValueError("ECO_INBOX_ARTIFACT_DEFERRED_UNTIL_REQUIRED")
        elif self.deferred_until is not None:
            raise ValueError("ECO_INBOX_ARTIFACT_DEFERRED_UNTIL_NOT_APPLICABLE")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "inbox-artifact-summary-ref",
            {
                "artifact_ref": self.artifact_ref,
                "binding_ref": self.binding_ref,
                "content_ref": self.content_ref,
                "privacy_scope": self.privacy_scope.value,
                "triage_state": self.triage_state.value,
            },
        )


class InboxConversationThread(_InboxModel):
    schema_version: Literal["uaa-eco-007-inbox-source-workbench.v1"] = (
        ECO_INBOX_SCHEMA_VERSION
    )
    workspace_ref: str
    thread_ref: str
    binding_ref: str
    artifact_refs: tuple[str, ...] = Field(..., min_length=1, max_length=256)
    participant_refs: tuple[str, ...] = Field(default=(), max_length=128)
    privacy_scope: InboxPrivacyScope = InboxPrivacyScope.workspace

    @model_validator(mode="after")
    def validate_thread(self) -> "InboxConversationThread":
        for field_name in ("workspace_ref", "thread_ref", "binding_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.artifact_refs, "artifact_ref")
        _validate_refs(self.participant_refs, "participant_ref")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "inbox-thread-summary-ref",
            {
                "artifact_refs": sorted(self.artifact_refs),
                "binding_ref": self.binding_ref,
                "thread_ref": self.thread_ref,
            },
        )


_PROPOSAL_OWNER_BY_KIND = {
    InboxProposalKind.task: CanonicalOwnerId.tasks,
    InboxProposalKind.event: CanonicalOwnerId.calendar,
    InboxProposalKind.crm_update: CanonicalOwnerId.crm,
    InboxProposalKind.board_placement: CanonicalOwnerId.boards,
    InboxProposalKind.communication_draft: CanonicalOwnerId.inbox,
    InboxProposalKind.defer: CanonicalOwnerId.inbox,
    InboxProposalKind.archive: CanonicalOwnerId.inbox,
}


class InboxSourceProposal(_InboxModel):
    schema_version: Literal["uaa-eco-007-inbox-source-workbench.v1"] = (
        ECO_INBOX_SCHEMA_VERSION
    )
    workspace_ref: str
    proposal_ref: str
    binding_ref: str
    artifact_ref: str
    proposal_kind: InboxProposalKind
    target_owner: CanonicalOwnerId
    proposed_target_ref: str
    proposal_summary_ref: str
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=64)
    review_state: InboxProposalReviewState = InboxProposalReviewState.proposed
    reviewer_ref: str | None = None
    decision_reason_ref: str | None = None
    reviewed_at: str | None = None
    due_at: str | None = None
    privacy_scope: InboxPrivacyScope = InboxPrivacyScope.workspace
    mutation_authorized: Literal[False] = False
    target_write_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    model_output_is_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_proposal(self) -> "InboxSourceProposal":
        for field_name in (
            "workspace_ref",
            "proposal_ref",
            "binding_ref",
            "artifact_ref",
            "proposed_target_ref",
            "proposal_summary_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.evidence_refs, "evidence_ref")
        if self.target_owner != _PROPOSAL_OWNER_BY_KIND[self.proposal_kind]:
            raise ValueError("ECO_INBOX_PROPOSAL_TARGET_OWNER_MISMATCH")
        if self.due_at is not None:
            object.__setattr__(
                self,
                "due_at",
                _canonical_timestamp(self.due_at, "ECO_INBOX_PROPOSAL_DUE_AT_INVALID"),
            )
        reviewed = self.review_state != InboxProposalReviewState.proposed
        review_fields = (
            self.reviewer_ref,
            self.decision_reason_ref,
            self.reviewed_at,
        )
        if reviewed and any(value is None for value in review_fields):
            raise ValueError("ECO_INBOX_PROPOSAL_REVIEW_FIELDS_REQUIRED")
        if not reviewed and any(value is not None for value in review_fields):
            raise ValueError("ECO_INBOX_PROPOSAL_REVIEW_FIELDS_NOT_APPLICABLE")
        if self.reviewer_ref is not None:
            _validate_ref(self.reviewer_ref, "reviewer_ref")
        if self.decision_reason_ref is not None:
            _validate_ref(self.decision_reason_ref, "decision_reason_ref")
        if self.reviewed_at is not None:
            object.__setattr__(
                self,
                "reviewed_at",
                _canonical_timestamp(
                    self.reviewed_at, "ECO_INBOX_PROPOSAL_REVIEWED_AT_INVALID"
                ),
            )
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "inbox-proposal-summary-ref",
            {
                "artifact_ref": self.artifact_ref,
                "proposal_kind": self.proposal_kind.value,
                "proposal_ref": self.proposal_ref,
                "review_state": self.review_state.value,
                "target_owner": self.target_owner.value,
            },
        )


class InboxManualImportPlan(_InboxModel):
    workspace_ref: str
    binding_ref: str
    artifact_ref: str
    source_mode: InboxSourceMode
    content_ref: str
    artifact_payload_ref: str
    content_byte_count: int = Field(..., ge=1, le=_MAX_CONTENT_BYTES)
    operation_ref: str
    idempotency_ref: str
    plan_ref: str
    approval_resource_refs: tuple[str, ...]
    writes_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    source_path_included: Literal[False] = False
    external_read_performed: Literal[False] = False
    background_work_started: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> "InboxManualImportPlan":
        for field_name in (
            "workspace_ref",
            "binding_ref",
            "artifact_ref",
            "content_ref",
            "artifact_payload_ref",
            "operation_ref",
            "idempotency_ref",
            "plan_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.approval_resource_refs, "approval_resource_ref")
        return self


@dataclass(frozen=True)
class PreparedInboxImport:
    """Ephemeral private artifact plus a persistable, content-free plan."""

    plan: InboxManualImportPlan
    artifact: InboxSourceArtifact


class InboxArtifactRecord(_InboxModel):
    artifact: InboxSourceArtifact = Field(..., repr=False)
    record_version: int = Field(..., ge=1)
    archived: bool
    retention_ref: str
    expires_at: str | None = None

    @model_validator(mode="after")
    def validate_record(self) -> "InboxArtifactRecord":
        _validate_ref(self.retention_ref, "retention_ref")
        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _canonical_timestamp(
                    self.expires_at, "ECO_INBOX_RECORD_EXPIRES_AT_INVALID"
                ),
            )
        return self


class InboxArtifactSearchResult(_InboxModel):
    workspace_ref: str
    query_ref: str
    artifacts: tuple[InboxArtifactRecord, ...]
    result_ref: str
    raw_query_included: Literal[False] = False
    external_read_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "InboxArtifactSearchResult":
        for field_name in ("workspace_ref", "query_ref", "result_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        if any(
            item.artifact.workspace_ref != self.workspace_ref for item in self.artifacts
        ):
            raise ValueError("ECO_INBOX_SEARCH_CROSS_WORKSPACE_RESULT_DENIED")
        return self


class InboxRepository:
    """Canonical Inbox repository on the encrypted ECO-001 data plane."""

    def __init__(self, platform: EcosystemLocalDataPlatform) -> None:
        self.platform = platform

    @staticmethod
    def mutation_resource_refs(
        *,
        workspace_ref: str,
        record_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        related_refs: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    workspace_ref,
                    idempotency_ref,
                    operation_ref,
                    record_ref,
                    *related_refs,
                )
            )
        )

    def create_binding(
        self,
        *,
        binding: InboxSourceBinding,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        return self._create(
            workspace_ref=binding.workspace_ref,
            record_ref=binding.binding_ref,
            record_kind_ref=ECO_INBOX_BINDING_RECORD_KIND_REF,
            safe_summary_ref=binding.safe_summary_ref,
            private_payload=binding.model_dump(mode="json"),
            search_terms=(
                _ALL_BINDINGS_TERM,
                _hashed_term("inbox-source-mode", binding.source_mode.value),
            ),
            retention_ref=binding.retention_ref,
            expires_at=None,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            related_refs=(),
            approval=approval,
        )

    def read_binding(
        self, *, workspace_ref: str, binding_ref: str
    ) -> InboxSourceBinding:
        record = self.platform.read(workspace_ref=workspace_ref, record_ref=binding_ref)
        binding = self._binding_from_record(record)
        if binding.workspace_ref != workspace_ref or binding.binding_ref != binding_ref:
            raise InboxError("ECO_INBOX_BINDING_RECORD_BINDING_INVALID")
        return binding

    def prepare_manual_import(
        self,
        *,
        workspace_ref: str,
        binding_ref: str,
        artifact_ref: str,
        artifact_kind: InboxArtifactKind,
        title: str,
        content: str,
        source_locator_ref: str,
        received_at: str,
        operation_ref: str,
        idempotency_ref: str,
        classification_ref: str = "classification-ref:unreviewed",
        thread_ref: str | None = None,
        participant_refs: tuple[str, ...] = (),
        attachment_refs: tuple[str, ...] = (),
        tag_refs: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        expires_at: str | None = None,
    ) -> PreparedInboxImport:
        return self._prepare_import(
            expected_mode=InboxSourceMode.manual,
            workspace_ref=workspace_ref,
            binding_ref=binding_ref,
            artifact_ref=artifact_ref,
            artifact_kind=artifact_kind,
            title=title,
            content=content,
            source_locator_ref=source_locator_ref,
            received_at=received_at,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            classification_ref=classification_ref,
            thread_ref=thread_ref,
            participant_refs=participant_refs,
            attachment_refs=attachment_refs,
            tag_refs=tag_refs,
            evidence_refs=evidence_refs,
            expires_at=expires_at,
        )

    def prepare_synthetic_import(self, **kwargs: Any) -> PreparedInboxImport:
        return self._prepare_import(expected_mode=InboxSourceMode.synthetic, **kwargs)

    def _prepare_import(
        self,
        *,
        expected_mode: InboxSourceMode,
        workspace_ref: str,
        binding_ref: str,
        artifact_ref: str,
        artifact_kind: InboxArtifactKind,
        title: str,
        content: str,
        source_locator_ref: str,
        received_at: str,
        operation_ref: str,
        idempotency_ref: str,
        classification_ref: str = "classification-ref:unreviewed",
        thread_ref: str | None = None,
        participant_refs: tuple[str, ...] = (),
        attachment_refs: tuple[str, ...] = (),
        tag_refs: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        expires_at: str | None = None,
    ) -> PreparedInboxImport:
        binding = self.read_binding(
            workspace_ref=workspace_ref, binding_ref=binding_ref
        )
        if binding.state != InboxBindingState.ready:
            raise InboxConflict("ECO_INBOX_BINDING_NOT_READY")
        if binding.source_mode != expected_mode:
            raise InboxConflict("ECO_INBOX_SOURCE_MODE_MISMATCH")
        artifact = InboxSourceArtifact(
            workspace_ref=workspace_ref,
            artifact_ref=artifact_ref,
            binding_ref=binding_ref,
            source_mode=expected_mode,
            artifact_kind=artifact_kind,
            title=title,
            content=content,
            content_ref=_content_ref(content),
            source_locator_ref=source_locator_ref,
            received_at=received_at,
            privacy_scope=binding.privacy_scope,
            classification_ref=classification_ref,
            thread_ref=thread_ref,
            participant_refs=participant_refs,
            attachment_refs=attachment_refs,
            tag_refs=tag_refs,
            evidence_refs=evidence_refs,
            retention_ref=binding.retention_ref,
            expires_at=expires_at,
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=artifact_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            related_refs=(binding_ref,),
        )
        material = {
            "artifact_ref": artifact_ref,
            "binding_ref": binding_ref,
            "content_byte_count": len(content.encode("utf-8")),
            "content_ref": artifact.content_ref,
            "artifact_payload_ref": _stable_ref(
                "inbox-artifact-payload-ref", artifact.model_dump(mode="json")
            ),
            "operation_ref": operation_ref,
            "source_mode": expected_mode.value,
            "workspace_ref": workspace_ref,
        }
        plan = InboxManualImportPlan(
            workspace_ref=workspace_ref,
            binding_ref=binding_ref,
            artifact_ref=artifact_ref,
            source_mode=expected_mode,
            content_ref=artifact.content_ref,
            artifact_payload_ref=material["artifact_payload_ref"],
            content_byte_count=len(content.encode("utf-8")),
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            plan_ref=_stable_ref("inbox-import-plan-ref", material),
            approval_resource_refs=resources,
        )
        return PreparedInboxImport(plan=plan, artifact=artifact)

    def commit_import(
        self,
        prepared: PreparedInboxImport,
        *,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        self._validate_prepared_import(prepared)
        artifact = prepared.artifact
        plan = prepared.plan
        return self._create(
            workspace_ref=artifact.workspace_ref,
            record_ref=artifact.artifact_ref,
            record_kind_ref=ECO_INBOX_ARTIFACT_RECORD_KIND_REF,
            safe_summary_ref=artifact.safe_summary_ref,
            private_payload=artifact.model_dump(mode="json"),
            search_terms=self._artifact_search_terms(artifact),
            retention_ref=artifact.retention_ref,
            expires_at=artifact.expires_at,
            operation_ref=plan.operation_ref,
            idempotency_ref=plan.idempotency_ref,
            related_refs=(artifact.binding_ref,),
            approval=approval,
        )

    def read_artifact(
        self, *, workspace_ref: str, artifact_ref: str
    ) -> InboxArtifactRecord:
        record = self.platform.read(
            workspace_ref=workspace_ref, record_ref=artifact_ref
        )
        artifact = self._artifact_from_record(record)
        if (
            artifact.workspace_ref != workspace_ref
            or artifact.artifact_ref != artifact_ref
        ):
            raise InboxError("ECO_INBOX_ARTIFACT_RECORD_BINDING_INVALID")
        return InboxArtifactRecord(
            artifact=artifact,
            record_version=record.version,
            archived=record.archived,
            retention_ref=record.retention_ref,
            expires_at=record.expires_at,
        )

    def triage_artifact(
        self,
        *,
        workspace_ref: str,
        artifact_ref: str,
        triage_state: InboxTriageState,
        classification_ref: str,
        links: tuple[InboxEntityLink, ...] = (),
        deferred_until: str | None = None,
        tag_refs: tuple[str, ...] | None = None,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = _stable_ref(
            "inbox-request-context-ref",
            {
                "artifact_ref": artifact_ref,
                "classification_ref": classification_ref,
                "deferred_until": deferred_until,
                "idempotency_ref": idempotency_ref,
                "links": [link.model_dump(mode="json") for link in links],
                "operation_ref": operation_ref,
                "tag_refs": None if tag_refs is None else list(tag_refs),
                "triage_state": triage_state.value,
                "workspace_ref": workspace_ref,
            },
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=artifact_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self.platform.replay_receipt(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                resource_refs=resources,
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            current = self.read_artifact(
                workspace_ref=workspace_ref, artifact_ref=artifact_ref
            )
            if current.archived:
                raise InboxConflict("ECO_INBOX_ARTIFACT_ARCHIVED")
            updated = InboxSourceArtifact.model_validate(
                {
                    **current.artifact.model_dump(mode="json"),
                    "triage_state": triage_state,
                    "classification_ref": classification_ref,
                    "links": links,
                    "deferred_until": deferred_until,
                    "tag_refs": (
                        current.artifact.tag_refs if tag_refs is None else tag_refs
                    ),
                }
            )
            self._validate_artifact_binding(updated)
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(
                    self._artifact_put(
                        updated,
                        operation_ref=operation_ref,
                        expected_version=current.record_version,
                    ),
                ),
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def create_thread(
        self,
        *,
        thread: InboxConversationThread,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        binding = self.read_binding(
            workspace_ref=thread.workspace_ref, binding_ref=thread.binding_ref
        )
        if binding.privacy_scope != thread.privacy_scope:
            raise InboxConflict("ECO_INBOX_THREAD_PRIVACY_SCOPE_MISMATCH")
        for artifact_ref in thread.artifact_refs:
            artifact = self.read_artifact(
                workspace_ref=thread.workspace_ref, artifact_ref=artifact_ref
            )
            if (
                artifact.archived
                or artifact.artifact.binding_ref != thread.binding_ref
                or artifact.artifact.privacy_scope != thread.privacy_scope
            ):
                raise InboxConflict("ECO_INBOX_THREAD_ARTIFACT_BINDING_INVALID")
        return self._create(
            workspace_ref=thread.workspace_ref,
            record_ref=thread.thread_ref,
            record_kind_ref=ECO_INBOX_THREAD_RECORD_KIND_REF,
            safe_summary_ref=thread.safe_summary_ref,
            private_payload=thread.model_dump(mode="json"),
            search_terms=(
                _ALL_THREADS_TERM,
                _hashed_term("inbox-binding", thread.binding_ref),
            ),
            retention_ref=binding.retention_ref,
            expires_at=None,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            related_refs=(thread.binding_ref, *thread.artifact_refs),
            approval=approval,
        )

    def read_thread(
        self, *, workspace_ref: str, thread_ref: str
    ) -> InboxConversationThread:
        record = self.platform.read(workspace_ref=workspace_ref, record_ref=thread_ref)
        try:
            thread = InboxConversationThread.model_validate(record.private_payload)
        except Exception as exc:
            raise InboxError("ECO_INBOX_THREAD_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_INBOX_MODULE_REF
            or record.record_kind_ref != ECO_INBOX_THREAD_RECORD_KIND_REF
            or record.safe_summary_ref != thread.safe_summary_ref
            or thread.workspace_ref != workspace_ref
            or thread.thread_ref != thread_ref
        ):
            raise InboxError("ECO_INBOX_THREAD_RECORD_BINDING_INVALID")
        return thread

    def create_proposal(
        self,
        *,
        proposal: InboxSourceProposal,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        artifact = self.read_artifact(
            workspace_ref=proposal.workspace_ref,
            artifact_ref=proposal.artifact_ref,
        )
        if artifact.archived:
            raise InboxConflict("ECO_INBOX_PROPOSAL_ARCHIVED_ARTIFACT_DENIED")
        if (
            artifact.artifact.binding_ref != proposal.binding_ref
            or artifact.artifact.privacy_scope != proposal.privacy_scope
        ):
            raise InboxConflict("ECO_INBOX_PROPOSAL_ARTIFACT_BINDING_INVALID")
        if proposal.review_state != InboxProposalReviewState.proposed:
            raise InboxConflict("ECO_INBOX_PROPOSAL_INITIAL_STATE_INVALID")
        return self._create(
            workspace_ref=proposal.workspace_ref,
            record_ref=proposal.proposal_ref,
            record_kind_ref=ECO_INBOX_PROPOSAL_RECORD_KIND_REF,
            safe_summary_ref=proposal.safe_summary_ref,
            private_payload=proposal.model_dump(mode="json"),
            search_terms=(
                _ALL_PROPOSALS_TERM,
                _hashed_term("inbox-binding", proposal.binding_ref),
                f"inbox-proposal-kind:{proposal.proposal_kind.value}",
                f"inbox-proposal-review:{proposal.review_state.value}",
            ),
            retention_ref=artifact.retention_ref,
            expires_at=artifact.expires_at,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            related_refs=(proposal.binding_ref, proposal.artifact_ref),
            approval=approval,
        )

    def read_proposal(
        self, *, workspace_ref: str, proposal_ref: str
    ) -> InboxSourceProposal:
        record = self.platform.read(
            workspace_ref=workspace_ref, record_ref=proposal_ref
        )
        return self._proposal_from_record(record, workspace_ref, proposal_ref)

    def review_proposal(
        self,
        *,
        workspace_ref: str,
        proposal_ref: str,
        review_state: Literal[
            InboxProposalReviewState.accepted_for_changeset,
            InboxProposalReviewState.rejected,
            InboxProposalReviewState.superseded,
        ],
        reviewer_ref: str,
        decision_reason_ref: str,
        reviewed_at: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if review_state not in {
            InboxProposalReviewState.accepted_for_changeset,
            InboxProposalReviewState.rejected,
            InboxProposalReviewState.superseded,
        }:
            raise InboxConflict("ECO_INBOX_PROPOSAL_REVIEW_STATE_INVALID")
        request_context_ref = _stable_ref(
            "inbox-request-context-ref",
            {
                "decision_reason_ref": decision_reason_ref,
                "operation_ref": operation_ref,
                "proposal_ref": proposal_ref,
                "review_state": review_state.value,
                "reviewed_at": reviewed_at,
                "reviewer_ref": reviewer_ref,
                "workspace_ref": workspace_ref,
            },
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=proposal_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self.platform.replay_receipt(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                resource_refs=resources,
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            record = self.platform.read(
                workspace_ref=workspace_ref, record_ref=proposal_ref
            )
            if record.archived:
                raise InboxConflict("ECO_INBOX_PROPOSAL_ARCHIVED")
            current = self._proposal_from_record(record, workspace_ref, proposal_ref)
            if current.review_state != InboxProposalReviewState.proposed:
                raise InboxConflict("ECO_INBOX_PROPOSAL_ALREADY_REVIEWED")
            updated = InboxSourceProposal.model_validate(
                {
                    **current.model_dump(mode="json"),
                    "review_state": review_state,
                    "reviewer_ref": reviewer_ref,
                    "decision_reason_ref": decision_reason_ref,
                    "reviewed_at": reviewed_at,
                }
            )
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(
                    PutRecord(
                        operation_ref=operation_ref,
                        module_ref=ECO_INBOX_MODULE_REF,
                        record_ref=proposal_ref,
                        record_kind_ref=ECO_INBOX_PROPOSAL_RECORD_KIND_REF,
                        safe_summary_ref=updated.safe_summary_ref,
                        private_payload=updated.model_dump(mode="json"),
                        search_terms=(
                            _ALL_PROPOSALS_TERM,
                            _hashed_term("inbox-binding", updated.binding_ref),
                            f"inbox-proposal-kind:{updated.proposal_kind.value}",
                            f"inbox-proposal-review:{updated.review_state.value}",
                        ),
                        expected_version=record.version,
                        retention_ref=record.retention_ref,
                        expires_at=record.expires_at,
                    ),
                ),
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def search_artifacts(
        self, *, workspace_ref: str, query: str
    ) -> InboxArtifactSearchResult:
        normalized = " ".join(query.casefold().split())
        if not normalized or len(normalized) > 128:
            raise ValueError("ECO_INBOX_SEARCH_QUERY_INVALID")
        query_terms = _private_search_terms(normalized)
        if not query_terms:
            raise ValueError("ECO_INBOX_SEARCH_QUERY_INVALID")
        blind_matches = [
            set(self.platform.search(workspace_ref=workspace_ref, term=term))
            for term in query_terms
        ]
        candidate_refs = set.intersection(*blind_matches)
        artifacts_by_ref = {
            item.artifact.artifact_ref: item
            for item in self.list_artifacts(workspace_ref=workspace_ref)
            if not item.archived
            and set(query_terms).issubset(
                _all_private_tokens(item.artifact.title, item.artifact.content)
            )
        }
        # Blind indexes provide the normal lookup path. The bounded local
        # decrypt-and-filter pass preserves complete search semantics when a
        # term falls beyond ECO-001's 64-term per-record index limit.
        ordered_refs = sorted(
            artifacts_by_ref,
            key=lambda record_ref: (record_ref not in candidate_refs, record_ref),
        )
        artifacts = [artifacts_by_ref[record_ref] for record_ref in ordered_refs]
        query_ref = _stable_ref("inbox-search-query-ref", normalized)
        result_ref = _stable_ref(
            "inbox-search-result-ref",
            {
                "artifact_refs": [item.artifact.artifact_ref for item in artifacts],
                "query_ref": query_ref,
                "workspace_ref": workspace_ref,
            },
        )
        return InboxArtifactSearchResult(
            workspace_ref=workspace_ref,
            query_ref=query_ref,
            artifacts=tuple(artifacts),
            result_ref=result_ref,
        )

    def list_artifacts(
        self, *, workspace_ref: str, binding_ref: str | None = None
    ) -> tuple[InboxArtifactRecord, ...]:
        term = (
            _ALL_ARTIFACTS_TERM
            if binding_ref is None
            else _hashed_term("inbox-binding", binding_ref)
        )
        refs = self.platform.search(workspace_ref=workspace_ref, term=term)
        items: list[InboxArtifactRecord] = []
        for artifact_ref in refs:
            try:
                item = self.read_artifact(
                    workspace_ref=workspace_ref, artifact_ref=artifact_ref
                )
            except InboxError:
                continue
            if binding_ref is None or item.artifact.binding_ref == binding_ref:
                items.append(item)
        return tuple(sorted(items, key=lambda item: item.artifact.artifact_ref))

    def archive_artifact(
        self,
        *,
        workspace_ref: str,
        artifact_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        request_context_ref = _stable_ref(
            "inbox-request-context-ref",
            {
                "artifact_ref": artifact_ref,
                "kind": "archive",
                "operation_ref": operation_ref,
                "workspace_ref": workspace_ref,
            },
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=artifact_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self.platform.replay_receipt(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                resource_refs=resources,
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            current = self.read_artifact(
                workspace_ref=workspace_ref, artifact_ref=artifact_ref
            )
            if current.archived:
                raise InboxConflict("ECO_INBOX_ARTIFACT_ALREADY_ARCHIVED")
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(
                    ArchiveRecord(
                        operation_ref=operation_ref,
                        record_ref=artifact_ref,
                        expected_version=current.record_version,
                    ),
                ),
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )

    def retention_candidates(
        self, *, workspace_ref: str, as_of: str
    ) -> tuple[str, ...]:
        candidates = self.platform.retention_candidates(
            workspace_ref=workspace_ref, as_of=as_of
        )
        selected: list[str] = []
        for record_ref in candidates:
            try:
                record = self.platform.read(
                    workspace_ref=workspace_ref, record_ref=record_ref
                )
            except EcosystemLocalDataError:
                continue
            if (
                record.module_ref == ECO_INBOX_MODULE_REF
                and record.record_kind_ref == ECO_INBOX_ARTIFACT_RECORD_KIND_REF
            ):
                selected.append(record_ref)
        return tuple(selected)

    def to_today_candidate(
        self,
        *,
        workspace_ref: str,
        proposal_ref: str,
        source_result_ref: str,
    ) -> Any:
        proposal = self.read_proposal(
            workspace_ref=workspace_ref, proposal_ref=proposal_ref
        )
        if proposal.review_state != InboxProposalReviewState.accepted_for_changeset:
            raise InboxConflict("ECO_INBOX_PROPOSAL_NOT_REVIEWED_FOR_TODAY")
        _validate_ref(source_result_ref, "source_result_ref")
        from ultimate_ai_agent.core.ecosystem.today import (  # noqa: PLC0415
            TodayItemKind,
            TodaySupplementalCandidate,
        )

        return TodaySupplementalCandidate(
            owner_app=CanonicalOwnerId.inbox,
            canonical_ref=proposal.proposal_ref,
            workspace_ref=proposal.workspace_ref,
            item_kind=TodayItemKind.source_proposal,
            source_result_refs=(source_result_ref,),
            why_shown_refs=("why-shown-ref:eco-007/reviewed-source-proposal",),
            evidence_refs=proposal.evidence_refs,
            due_at=(
                None
                if proposal.due_at is None
                else datetime.fromisoformat(proposal.due_at.replace("Z", "+00:00"))
            ),
        )

    def _create(
        self,
        *,
        workspace_ref: str,
        record_ref: str,
        record_kind_ref: str,
        safe_summary_ref: str,
        private_payload: dict[str, Any],
        search_terms: tuple[str, ...],
        retention_ref: str,
        expires_at: str | None,
        operation_ref: str,
        idempotency_ref: str,
        related_refs: tuple[str, ...],
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        private_payload = self._validated_private_payload(
            record_kind_ref=record_kind_ref,
            private_payload=private_payload,
            safe_summary_ref=safe_summary_ref,
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=record_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            related_refs=related_refs,
        )
        request_context_ref = _stable_ref(
            "inbox-request-context-ref",
            {
                "private_payload": private_payload,
                "record_kind_ref": record_kind_ref,
                "resources": resources,
            },
        )
        with self.platform.approval_authority.hold_validation_lock():
            replay = self.platform.replay_receipt(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                resource_refs=resources,
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
            if replay is not None:
                return replay
            try:
                self.platform.read(workspace_ref=workspace_ref, record_ref=record_ref)
            except EcosystemLocalDataError as exc:
                if str(exc) != "ECO_RECORD_NOT_FOUND":
                    raise
            else:
                raise InboxConflict("ECO_INBOX_RECORD_ALREADY_EXISTS")
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(
                    PutRecord(
                        operation_ref=operation_ref,
                        module_ref=ECO_INBOX_MODULE_REF,
                        record_ref=record_ref,
                        record_kind_ref=record_kind_ref,
                        safe_summary_ref=safe_summary_ref,
                        private_payload=private_payload,
                        search_terms=search_terms,
                        expected_version=0,
                        retention_ref=retention_ref,
                        expires_at=expires_at,
                    ),
                ),
                approval=approval,
                requested_action=ECO_INBOX_MUTATION_ACTION,
                request_context_ref=request_context_ref,
                approval_resource_refs=related_refs,
            )

    def _validate_prepared_import(self, prepared: PreparedInboxImport) -> None:
        artifact = prepared.artifact
        plan = prepared.plan
        if (
            plan.workspace_ref != artifact.workspace_ref
            or plan.binding_ref != artifact.binding_ref
            or plan.artifact_ref != artifact.artifact_ref
            or plan.source_mode != artifact.source_mode
            or plan.content_ref != artifact.content_ref
            or plan.artifact_payload_ref
            != _stable_ref(
                "inbox-artifact-payload-ref", artifact.model_dump(mode="json")
            )
            or plan.content_byte_count != len(artifact.content.encode("utf-8"))
        ):
            raise InboxConflict("ECO_INBOX_IMPORT_PLAN_BINDING_INVALID")
        resources = self.mutation_resource_refs(
            workspace_ref=plan.workspace_ref,
            record_ref=plan.artifact_ref,
            operation_ref=plan.operation_ref,
            idempotency_ref=plan.idempotency_ref,
            related_refs=(plan.binding_ref,),
        )
        material = {
            "artifact_ref": plan.artifact_ref,
            "binding_ref": plan.binding_ref,
            "content_byte_count": plan.content_byte_count,
            "content_ref": plan.content_ref,
            "artifact_payload_ref": plan.artifact_payload_ref,
            "operation_ref": plan.operation_ref,
            "source_mode": plan.source_mode.value,
            "workspace_ref": plan.workspace_ref,
        }
        if plan.approval_resource_refs != resources or plan.plan_ref != _stable_ref(
            "inbox-import-plan-ref", material
        ):
            raise InboxConflict("ECO_INBOX_IMPORT_PLAN_INTEGRITY_INVALID")
        self._validate_artifact_binding(artifact)

    @staticmethod
    def _validated_private_payload(
        *,
        record_kind_ref: str,
        private_payload: dict[str, Any],
        safe_summary_ref: str,
    ) -> dict[str, Any]:
        model_type = {
            ECO_INBOX_BINDING_RECORD_KIND_REF: InboxSourceBinding,
            ECO_INBOX_ARTIFACT_RECORD_KIND_REF: InboxSourceArtifact,
            ECO_INBOX_THREAD_RECORD_KIND_REF: InboxConversationThread,
            ECO_INBOX_PROPOSAL_RECORD_KIND_REF: InboxSourceProposal,
        }.get(record_kind_ref)
        if model_type is None:
            raise InboxError("ECO_INBOX_RECORD_KIND_INVALID")
        try:
            validated = model_type.model_validate(private_payload)
        except Exception as exc:
            raise InboxError("ECO_INBOX_PRIVATE_PAYLOAD_INVALID") from exc
        if validated.safe_summary_ref != safe_summary_ref:
            raise InboxError("ECO_INBOX_SAFE_SUMMARY_BINDING_INVALID")
        return validated.model_dump(mode="json")

    def _validate_artifact_binding(self, artifact: InboxSourceArtifact) -> None:
        binding = self.read_binding(
            workspace_ref=artifact.workspace_ref,
            binding_ref=artifact.binding_ref,
        )
        if (
            binding.state != InboxBindingState.ready
            or binding.source_mode != artifact.source_mode
            or binding.privacy_scope != artifact.privacy_scope
            or binding.retention_ref != artifact.retention_ref
        ):
            raise InboxConflict("ECO_INBOX_ARTIFACT_SOURCE_BINDING_INVALID")

    @staticmethod
    def _artifact_search_terms(artifact: InboxSourceArtifact) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    _ALL_ARTIFACTS_TERM,
                    _hashed_term("inbox-binding", artifact.binding_ref),
                    f"inbox-artifact-kind:{artifact.artifact_kind.value}",
                    f"inbox-triage-state:{artifact.triage_state.value}",
                    *_private_search_terms(artifact.title, artifact.content),
                )
            )
        )[:64]

    @staticmethod
    def _artifact_put(
        artifact: InboxSourceArtifact,
        *,
        operation_ref: str,
        expected_version: int,
    ) -> PutRecord:
        return PutRecord(
            operation_ref=operation_ref,
            module_ref=ECO_INBOX_MODULE_REF,
            record_ref=artifact.artifact_ref,
            record_kind_ref=ECO_INBOX_ARTIFACT_RECORD_KIND_REF,
            safe_summary_ref=artifact.safe_summary_ref,
            private_payload=artifact.model_dump(mode="json"),
            search_terms=InboxRepository._artifact_search_terms(artifact),
            expected_version=expected_version,
            retention_ref=artifact.retention_ref,
            expires_at=artifact.expires_at,
        )

    @staticmethod
    def _binding_from_record(record: LocalRecord) -> InboxSourceBinding:
        try:
            binding = InboxSourceBinding.model_validate(record.private_payload)
        except Exception as exc:
            raise InboxError("ECO_INBOX_BINDING_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_INBOX_MODULE_REF
            or record.record_kind_ref != ECO_INBOX_BINDING_RECORD_KIND_REF
            or record.safe_summary_ref != binding.safe_summary_ref
            or record.archived
        ):
            raise InboxError("ECO_INBOX_BINDING_RECORD_BINDING_INVALID")
        return binding

    @staticmethod
    def _artifact_from_record(record: LocalRecord) -> InboxSourceArtifact:
        try:
            artifact = InboxSourceArtifact.model_validate(record.private_payload)
        except Exception as exc:
            raise InboxError("ECO_INBOX_ARTIFACT_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_INBOX_MODULE_REF
            or record.record_kind_ref != ECO_INBOX_ARTIFACT_RECORD_KIND_REF
            or record.safe_summary_ref != artifact.safe_summary_ref
            or record.retention_ref != artifact.retention_ref
            or not _timestamps_equal(record.expires_at, artifact.expires_at)
        ):
            raise InboxError("ECO_INBOX_ARTIFACT_RECORD_BINDING_INVALID")
        return artifact

    @staticmethod
    def _proposal_from_record(
        record: LocalRecord, workspace_ref: str, proposal_ref: str
    ) -> InboxSourceProposal:
        try:
            proposal = InboxSourceProposal.model_validate(record.private_payload)
        except Exception as exc:
            raise InboxError("ECO_INBOX_PROPOSAL_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_INBOX_MODULE_REF
            or record.record_kind_ref != ECO_INBOX_PROPOSAL_RECORD_KIND_REF
            or record.safe_summary_ref != proposal.safe_summary_ref
            or proposal.workspace_ref != workspace_ref
            or proposal.proposal_ref != proposal_ref
        ):
            raise InboxError("ECO_INBOX_PROPOSAL_RECORD_BINDING_INVALID")
        return proposal


__all__ = [
    "ECO_INBOX_ARTIFACT_RECORD_KIND_REF",
    "ECO_INBOX_BINDING_RECORD_KIND_REF",
    "ECO_INBOX_DEFAULT_RETENTION_REF",
    "ECO_INBOX_MODULE_REF",
    "ECO_INBOX_MUTATION_ACTION",
    "ECO_INBOX_PROPOSAL_RECORD_KIND_REF",
    "ECO_INBOX_SCHEMA_VERSION",
    "ECO_INBOX_THREAD_RECORD_KIND_REF",
    "InboxArtifactKind",
    "InboxArtifactRecord",
    "InboxArtifactSearchResult",
    "InboxBindingState",
    "InboxConflict",
    "InboxConversationThread",
    "InboxEntityLink",
    "InboxError",
    "InboxLinkKind",
    "InboxManualImportPlan",
    "InboxPrivacyScope",
    "InboxProposalKind",
    "InboxProposalReviewState",
    "InboxRepository",
    "InboxSourceArtifact",
    "InboxSourceBinding",
    "InboxSourceMode",
    "InboxSourceProposal",
    "InboxTriageState",
    "PreparedInboxImport",
]
