"""Review-only autocorrect controls built on ECO-008 ChangeSet truth.

The module accepts content-free field diffs for existing local records.  It
can prepare and review a correction candidate, but it cannot create or apply a
ChangeSet, mutate canonical state, execute rollback, call a model, or perform
an external write.  Accepted reviews remain bound to a separately governed
ECO-008 child lane.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import ipaddress
import json
import re
from threading import RLock
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.ecosystem.changesets import FieldDiff
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId, EntityKind
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


AUTOCORRECT_SCHEMA_VERSION = "uaa-autocorrect-controls.v1"
AUTOCORRECT_CONTRACT_REF = "contract-ref:queue-v2:Q28:autocorrect-controls:v1"
AUTOCORRECT_MIN_REVIEW_CONFIDENCE = 60
AUTOCORRECT_MAX_DIFFS = 16
AUTOCORRECT_MAX_SESSION_RECEIPTS = 256

_SUPPORTED_TARGETS: dict[EntityKind, CanonicalOwnerId] = {
    EntityKind.task: CanonicalOwnerId.tasks,
    EntityKind.task_occurrence: CanonicalOwnerId.tasks,
    EntityKind.board: CanonicalOwnerId.boards,
    EntityKind.board_template: CanonicalOwnerId.boards,
    EntityKind.calendar_set: CanonicalOwnerId.calendar,
}
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`(:=,\[])(?:~[/\\]|"
    r"/(?:users|home|usr|var|private|tmp|etc)(?:/|$)|[a-z]:[/\\]|\\\\[^\\\s]+\\)"
)
_DNS_CANDIDATE_RE = re.compile(
    r"\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b",
    re.IGNORECASE,
)
_IPV4_CANDIDATE_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_CANDIDATE_RE = re.compile(
    r"(?i)(?<![a-z0-9])(?:\[[0-9a-f:.%]+\]|(?:[0-9a-f]{0,4}:){2,}[0-9a-f:.%]*)(?![a-z0-9])"
)
_UNSAFE_SCHEME_RE = re.compile(r"(?i)(?:^|:)(?:file|ftp|https?):")


class AutocorrectError(RuntimeError):
    """Fail-closed error with a stable content-free code."""


class AutocorrectConflict(AutocorrectError):
    """Raised when an idempotency or proposal binding changes."""


class CorrectionConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class CorrectionProposalState(str, Enum):
    ready_for_review = "ready_for_review"
    blocked_low_confidence = "blocked_low_confidence"
    blocked_safe_disabled = "blocked_safe_disabled"
    stale = "stale"


class CorrectionDecision(str, Enum):
    accept = "accept"
    reject = "reject"
    supersede = "supersede"


class CorrectionReviewOutcome(str, Enum):
    accepted_for_changeset_review = "accepted_for_changeset_review"
    rejected = "rejected"
    superseded = "superseded"
    blocked = "blocked"
    stale = "stale"


class _CorrectionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _contains_dns_hostname(value: str) -> bool:
    return any(
        any(character.isalpha() for character in match.group(0).rsplit(".", 1)[-1])
        for match in _DNS_CANDIDATE_RE.finditer(value)
    )


def _contains_ipv6_address(value: str) -> bool:
    for match in _IPV6_CANDIDATE_RE.finditer(value):
        candidate = match.group(0).strip("[]").split("%", 1)[0]
        try:
            if ipaddress.ip_address(candidate).version == 6:
                return True
        except ValueError:
            continue
    return False


def _validate_ref(value: str, field_name: str) -> str:
    if (
        not _SAFE_REF_RE.fullmatch(value)
        or "/" in value
        or "\\" in value
        or _RAW_PATH_RE.search(value)
        or _UNSAFE_SCHEME_RE.search(value)
        or _contains_dns_hostname(value)
        or _IPV4_CANDIDATE_RE.search(value)
        or _contains_ipv6_address(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"AUTOCORRECT_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"AUTOCORRECT_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class CorrectionProposalRequest(_CorrectionModel):
    workspace_ref: str
    source_proposal_ref: str
    target_kind: EntityKind
    target_owner: CanonicalOwnerId
    target_ref: str
    expected_revision_ref: str
    current_revision_ref: str
    confidence_percent: int = Field(..., ge=0, le=100)
    field_diffs: tuple[FieldDiff, ...] = Field(
        ..., min_length=1, max_length=AUTOCORRECT_MAX_DIFFS
    )
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=24)
    reason_refs: tuple[str, ...] = Field(default=(), max_length=24)
    rejection_history_refs: tuple[str, ...] = Field(default=(), max_length=24)
    safe_disabled: bool = False
    model_generated: Literal[False] = False
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_request(self) -> "CorrectionProposalRequest":
        for field_name in (
            "workspace_ref",
            "source_proposal_ref",
            "target_ref",
            "expected_revision_ref",
            "current_revision_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in ("evidence_refs", "reason_refs", "rejection_history_refs"):
            _validate_refs(getattr(self, field_name), field_name)
        expected_owner = _SUPPORTED_TARGETS.get(self.target_kind)
        if expected_owner is None:
            raise ValueError("AUTOCORRECT_TARGET_KIND_NOT_SUPPORTED_BY_ECO008")
        if self.target_owner != expected_owner:
            raise ValueError("AUTOCORRECT_CANONICAL_OWNER_BINDING_INVALID")
        operation_refs: set[str] = set()
        field_refs: set[str] = set()
        for diff in self.field_diffs:
            for field_name in (
                "operation_ref",
                "target_ref",
                "field_ref",
                "before_fingerprint_ref",
                "after_fingerprint_ref",
            ):
                value = getattr(diff, field_name)
                if value is not None:
                    _validate_ref(value, f"diff_{field_name}")
            if diff.target_ref != self.target_ref:
                raise ValueError("AUTOCORRECT_DIFF_TARGET_BINDING_INVALID")
            if diff.operation_ref in operation_refs:
                raise ValueError("AUTOCORRECT_DUPLICATE_OPERATION_REF")
            if diff.field_ref in field_refs:
                raise ValueError("AUTOCORRECT_DUPLICATE_FIELD_REF")
            operation_refs.add(diff.operation_ref)
            field_refs.add(diff.field_ref)
        return self


class CorrectionComparisonView(_CorrectionModel):
    target_ref: str
    expected_revision_ref: str
    current_revision_ref: str
    field_diffs: tuple[FieldDiff, ...]
    changed_field_count: int
    exact_revision_match: bool
    raw_values_included: Literal[False] = False


class CorrectionRollbackReadiness(_CorrectionModel):
    rollback_plan_ref: str
    rollback_ready: bool
    rollback_requires_applied_changeset_receipt: Literal[True] = True
    rollback_execution_available: Literal[False] = False
    safe_disable_available: Literal[True] = True


class CorrectionProposal(_CorrectionModel):
    schema_version: Literal["uaa-autocorrect-controls.v1"] = AUTOCORRECT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q28:autocorrect-controls:v1"] = (
        AUTOCORRECT_CONTRACT_REF
    )
    proposal_ref: str
    proposal_fingerprint_ref: str
    source_proposal_ref: str
    workspace_ref: str
    target_kind: EntityKind
    target_owner: CanonicalOwnerId
    target_ref: str
    state: CorrectionProposalState
    confidence_percent: int
    confidence: CorrectionConfidence
    comparison: CorrectionComparisonView
    evidence_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]
    rejection_history_refs: tuple[str, ...]
    expected_approval_scope_ref: str
    expected_changeset_plan_ref: str
    review_packet_ref: str
    rollback: CorrectionRollbackReadiness
    next_safe_action: str
    blocked_authority_refs: tuple[str, ...]
    canonical_state_mutated: Literal[False] = False
    changeset_created: Literal[False] = False
    approval_granted: Literal[False] = False
    rollback_executed: Literal[False] = False
    model_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


class CorrectionReviewRequest(_CorrectionModel):
    proposal: CorrectionProposalRequest
    proposal_ref: str
    proposal_fingerprint_ref: str
    decision: CorrectionDecision
    reviewer_ref: str
    idempotency_ref: str
    superseding_proposal_ref: str | None = None

    @model_validator(mode="after")
    def validate_review(self) -> "CorrectionReviewRequest":
        for field_name in (
            "proposal_ref",
            "proposal_fingerprint_ref",
            "reviewer_ref",
            "idempotency_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.superseding_proposal_ref is not None:
            _validate_ref(self.superseding_proposal_ref, "superseding_proposal_ref")
        if self.decision == CorrectionDecision.supersede:
            if (
                self.superseding_proposal_ref is None
                or self.superseding_proposal_ref == self.proposal_ref
            ):
                raise ValueError("AUTOCORRECT_SUPERSEDING_PROPOSAL_REF_REQUIRED")
        elif self.superseding_proposal_ref is not None:
            raise ValueError("AUTOCORRECT_SUPERSEDING_PROPOSAL_REF_NOT_ALLOWED")
        return self


class CorrectionReviewReceipt(_CorrectionModel):
    schema_version: Literal["uaa-autocorrect-controls.v1"] = AUTOCORRECT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q28:autocorrect-controls:v1"] = (
        AUTOCORRECT_CONTRACT_REF
    )
    receipt_ref: str
    review_fingerprint_ref: str
    proposal_ref: str
    proposal_fingerprint_ref: str
    reviewer_ref: str
    idempotency_ref: str
    decision: CorrectionDecision
    outcome: CorrectionReviewOutcome
    superseding_proposal_ref: str | None = None
    rejection_learning_ref: str | None = None
    expected_changeset_plan_ref: str | None = None
    expected_approval_scope_ref: str | None = None
    rollback_plan_ref: str
    evidence_refs: tuple[str, ...]
    next_safe_action: str
    replayed: bool = False
    canonical_state_mutated: Literal[False] = False
    changeset_created: Literal[False] = False
    approval_granted: Literal[False] = False
    rollback_executed: Literal[False] = False
    model_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


class AutocorrectControlStatus(_CorrectionModel):
    schema_version: Literal["uaa-autocorrect-controls.v1"] = AUTOCORRECT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q28:autocorrect-controls:v1"] = (
        AUTOCORRECT_CONTRACT_REF
    )
    status: Literal["implemented_proposal_only"] = "implemented_proposal_only"
    supported_target_kinds: tuple[EntityKind, ...]
    minimum_review_confidence: int
    process_local_review_capacity: int
    exact_revision_required: Literal[True] = True
    idempotency_conflicts_fail_closed: Literal[True] = True
    rejection_learning_content_free: Literal[True] = True
    canonical_mutation_enabled: Literal[False] = False
    changeset_creation_enabled: Literal[False] = False
    rollback_execution_enabled: Literal[False] = False
    model_calls_enabled: Literal[False] = False
    external_writes_enabled: Literal[False] = False
    safe_summary: str
    blocked_authority_refs: tuple[str, ...]
    next_safe_action: str


def build_autocorrect_control_status() -> AutocorrectControlStatus:
    return AutocorrectControlStatus(
        supported_target_kinds=tuple(_SUPPORTED_TARGETS),
        minimum_review_confidence=AUTOCORRECT_MIN_REVIEW_CONFIDENCE,
        process_local_review_capacity=AUTOCORRECT_MAX_SESSION_RECEIPTS,
        safe_summary=(
            "Autocorrect prepares content-free exact-diff correction reviews; "
            "canonical writes and rollback execution remain separate governed lanes."
        ),
        blocked_authority_refs=(
            "blocked-authority-ref:autocorrect:canonical-mutation",
            "blocked-authority-ref:autocorrect:changeset-creation",
            "blocked-authority-ref:autocorrect:rollback-execution",
            "blocked-authority-ref:autocorrect:model-call",
            "blocked-authority-ref:autocorrect:external-write",
        ),
        next_safe_action=(
            "Review the exact diff and revision binding, then use a separately "
            "approved ECO-008 child lane if the correction should be applied."
        ),
    )


def build_correction_proposal(request: CorrectionProposalRequest) -> CorrectionProposal:
    payload = request.model_dump(mode="json")
    proposal_fingerprint_ref = _stable_ref(
        "correction-proposal-fingerprint-ref", payload
    )
    proposal_ref = _stable_ref("correction-proposal-ref", payload)
    exact_revision_match = request.expected_revision_ref == request.current_revision_ref
    confidence = (
        CorrectionConfidence.high
        if request.confidence_percent >= 80
        else CorrectionConfidence.medium
        if request.confidence_percent >= AUTOCORRECT_MIN_REVIEW_CONFIDENCE
        else CorrectionConfidence.low
    )
    if not exact_revision_match:
        state = CorrectionProposalState.stale
        next_safe_action = (
            "Refresh the canonical target revision and prepare a new proposal."
        )
    elif request.safe_disabled:
        state = CorrectionProposalState.blocked_safe_disabled
        next_safe_action = (
            "Keep correction review disabled until the safe-disable is lifted."
        )
    elif request.confidence_percent < AUTOCORRECT_MIN_REVIEW_CONFIDENCE:
        state = CorrectionProposalState.blocked_low_confidence
        next_safe_action = (
            "Add evidence or correct the candidate before requesting review."
        )
    else:
        state = CorrectionProposalState.ready_for_review
        next_safe_action = (
            "Record an accept, reject, or supersede review; acceptance only prepares "
            "a separately governed ECO-008 child lane."
        )
    binding = {
        "proposal_ref": proposal_ref,
        "proposal_fingerprint_ref": proposal_fingerprint_ref,
        "workspace_ref": request.workspace_ref,
        "target_kind": request.target_kind.value,
        "target_owner": request.target_owner.value,
        "target_ref": request.target_ref,
        "expected_revision_ref": request.expected_revision_ref,
        "current_revision_ref": request.current_revision_ref,
        "field_diffs": [item.model_dump(mode="json") for item in request.field_diffs],
    }
    expected_changeset_plan_ref = _stable_ref("changeset-plan-ref", binding)
    expected_approval_scope_ref = _stable_ref(
        "approval-scope-ref",
        {**binding, "action": "ecosystem.changesets.apply"},
    )
    rollback_plan_ref = _stable_ref(
        "rollback-plan-ref",
        {**binding, "changeset_plan_ref": expected_changeset_plan_ref},
    )
    review_packet_ref = _stable_ref(
        "correction-review-packet-ref",
        {
            **binding,
            "evidence_refs": request.evidence_refs,
            "reason_refs": request.reason_refs,
            "rejection_history_refs": request.rejection_history_refs,
            "state": state.value,
        },
    )
    return CorrectionProposal(
        proposal_ref=proposal_ref,
        proposal_fingerprint_ref=proposal_fingerprint_ref,
        source_proposal_ref=request.source_proposal_ref,
        workspace_ref=request.workspace_ref,
        target_kind=request.target_kind,
        target_owner=request.target_owner,
        target_ref=request.target_ref,
        state=state,
        confidence_percent=request.confidence_percent,
        confidence=confidence,
        comparison=CorrectionComparisonView(
            target_ref=request.target_ref,
            expected_revision_ref=request.expected_revision_ref,
            current_revision_ref=request.current_revision_ref,
            field_diffs=request.field_diffs,
            changed_field_count=len(request.field_diffs),
            exact_revision_match=exact_revision_match,
        ),
        evidence_refs=request.evidence_refs,
        reason_refs=request.reason_refs,
        rejection_history_refs=request.rejection_history_refs,
        expected_approval_scope_ref=expected_approval_scope_ref,
        expected_changeset_plan_ref=expected_changeset_plan_ref,
        review_packet_ref=review_packet_ref,
        rollback=CorrectionRollbackReadiness(
            rollback_plan_ref=rollback_plan_ref,
            rollback_ready=state == CorrectionProposalState.ready_for_review,
        ),
        next_safe_action=next_safe_action,
        blocked_authority_refs=(
            "blocked-authority-ref:autocorrect:canonical-mutation",
            "blocked-authority-ref:autocorrect:changeset-creation",
            "blocked-authority-ref:autocorrect:rollback-execution",
        ),
    )


class CorrectionReviewSession:
    """Process-local idempotency guard for review-only correction outcomes."""

    def __init__(self, *, max_receipts: int = AUTOCORRECT_MAX_SESSION_RECEIPTS) -> None:
        if not 1 <= max_receipts <= AUTOCORRECT_MAX_SESSION_RECEIPTS:
            raise ValueError("AUTOCORRECT_REVIEW_SESSION_CAPACITY_INVALID")
        self._lock = RLock()
        self._max_receipts = max_receipts
        self._receipts: dict[str, tuple[str, CorrectionReviewReceipt]] = {}

    def review(self, request: CorrectionReviewRequest) -> CorrectionReviewReceipt:
        proposal = build_correction_proposal(request.proposal)
        if (
            request.proposal_ref != proposal.proposal_ref
            or request.proposal_fingerprint_ref != proposal.proposal_fingerprint_ref
        ):
            raise AutocorrectConflict("AUTOCORRECT_PROPOSAL_BINDING_CHANGED")
        review_material = request.model_dump(mode="json")
        review_fingerprint_ref = _stable_ref(
            "correction-review-fingerprint-ref", review_material
        )
        with self._lock:
            existing = self._receipts.get(request.idempotency_ref)
            if existing is not None:
                existing_fingerprint, existing_receipt = existing
                if existing_fingerprint != review_fingerprint_ref:
                    raise AutocorrectConflict(
                        "AUTOCORRECT_IDEMPOTENCY_PAYLOAD_CONFLICT"
                    )
                return existing_receipt.model_copy(update={"replayed": True})
            if len(self._receipts) >= self._max_receipts:
                raise AutocorrectError("AUTOCORRECT_REVIEW_SESSION_CAPACITY_REACHED")

            if proposal.state == CorrectionProposalState.stale:
                outcome = CorrectionReviewOutcome.stale
                next_safe_action = "Refresh the target revision; the stale correction cannot be reviewed."
            elif proposal.state != CorrectionProposalState.ready_for_review:
                outcome = CorrectionReviewOutcome.blocked
                next_safe_action = (
                    "Resolve the proposal blocker and prepare a new bound correction."
                )
            elif request.decision == CorrectionDecision.accept:
                outcome = CorrectionReviewOutcome.accepted_for_changeset_review
                next_safe_action = (
                    "Prepare the exact ECO-008 child ChangeSet and obtain its scoped "
                    "LocalApprovalAuthority decision before any write."
                )
            elif request.decision == CorrectionDecision.reject:
                outcome = CorrectionReviewOutcome.rejected
                next_safe_action = "Keep the content-free rejection signal for later reviewed learning."
            else:
                outcome = CorrectionReviewOutcome.superseded
                next_safe_action = "Review the separately bound superseding proposal."

            rejection_learning_ref = (
                _stable_ref(
                    "correction-learning-ref",
                    {
                        "proposal_ref": proposal.proposal_ref,
                        "review_fingerprint_ref": review_fingerprint_ref,
                        "decision": request.decision.value,
                        "prior_rejection_refs": proposal.rejection_history_refs,
                    },
                )
                if outcome
                in {
                    CorrectionReviewOutcome.rejected,
                    CorrectionReviewOutcome.superseded,
                }
                else None
            )
            receipt_ref = _stable_ref(
                "correction-review-receipt-ref",
                {
                    "review_fingerprint_ref": review_fingerprint_ref,
                    "outcome": outcome.value,
                    "rollback_plan_ref": proposal.rollback.rollback_plan_ref,
                },
            )
            receipt = CorrectionReviewReceipt(
                receipt_ref=receipt_ref,
                review_fingerprint_ref=review_fingerprint_ref,
                proposal_ref=proposal.proposal_ref,
                proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
                reviewer_ref=request.reviewer_ref,
                idempotency_ref=request.idempotency_ref,
                decision=request.decision,
                outcome=outcome,
                superseding_proposal_ref=request.superseding_proposal_ref,
                rejection_learning_ref=rejection_learning_ref,
                expected_changeset_plan_ref=(
                    proposal.expected_changeset_plan_ref
                    if outcome == CorrectionReviewOutcome.accepted_for_changeset_review
                    else None
                ),
                expected_approval_scope_ref=(
                    proposal.expected_approval_scope_ref
                    if outcome == CorrectionReviewOutcome.accepted_for_changeset_review
                    else None
                ),
                rollback_plan_ref=proposal.rollback.rollback_plan_ref,
                evidence_refs=proposal.evidence_refs,
                next_safe_action=next_safe_action,
            )
            self._receipts[request.idempotency_ref] = (
                review_fingerprint_ref,
                receipt,
            )
            return receipt


__all__ = [
    "AUTOCORRECT_CONTRACT_REF",
    "AUTOCORRECT_MAX_DIFFS",
    "AUTOCORRECT_MAX_SESSION_RECEIPTS",
    "AUTOCORRECT_MIN_REVIEW_CONFIDENCE",
    "AUTOCORRECT_SCHEMA_VERSION",
    "AutocorrectConflict",
    "AutocorrectControlStatus",
    "AutocorrectError",
    "CorrectionComparisonView",
    "CorrectionConfidence",
    "CorrectionDecision",
    "CorrectionProposal",
    "CorrectionProposalRequest",
    "CorrectionProposalState",
    "CorrectionReviewOutcome",
    "CorrectionReviewReceipt",
    "CorrectionReviewRequest",
    "CorrectionReviewSession",
    "CorrectionRollbackReadiness",
    "build_autocorrect_control_status",
    "build_correction_proposal",
]
