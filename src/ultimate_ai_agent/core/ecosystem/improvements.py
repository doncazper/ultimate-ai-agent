"""Proposal-only governed improvement contracts for Queue V2 Q29.

The module turns content-free evaluation, correction, feedback, and outcome
evidence into reviewable proposals and outcome observations.  It never edits a
target, creates a patch, trains a model, grants approval, promotes a proposal,
or performs Git or external operations.
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

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


IMPROVEMENT_SCHEMA_VERSION = "uaa-governed-improvement.v1"
IMPROVEMENT_CONTRACT_REF = "contract-ref:queue-v2:Q29:governed-improvement:v1"
IMPROVEMENT_MAX_SESSION_RECEIPTS = 256

_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`(:=,\[])(?:~[/\\]|"
    r"/(?:users|home|usr|var|private|tmp|etc)(?:/|$)|[a-z]:[/\\]|\\\\[^\\\s]+\\)"
)
_DNS_RE = re.compile(
    r"\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b",
    re.IGNORECASE,
)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_RE = re.compile(
    r"(?i)(?<![a-z0-9])(?:\[[0-9a-f:.%]+\]|(?:[0-9a-f]{0,4}:){2,}[0-9a-f:.%]*)(?![a-z0-9])"
)
_UNSAFE_SCHEME_RE = re.compile(r"(?i)(?:^|:)(?:file|ftp|https?):")


class ImprovementError(RuntimeError):
    """Fail-closed Q29 error with a content-free code."""


class ImprovementConflict(ImprovementError):
    """Raised when an idempotency or proposal binding changes."""


class ImprovementEvidenceKind(str, Enum):
    evaluation_gap = "evaluation_gap"
    correction_decision = "correction_decision"
    operator_feedback = "operator_feedback"
    verified_outcome = "verified_outcome"


class ImprovementRightsPosture(str, Enum):
    permitted = "permitted"
    unknown = "unknown"
    denied = "denied"


class ImprovementTargetKind(str, Enum):
    evaluation_case = "evaluation_case"
    workflow_playbook = "workflow_playbook"
    instruction_template = "instruction_template"
    routing_rule = "routing_rule"
    code_change = "code_change"
    tcb_change = "tcb_change"


class ImprovementProposalState(str, Enum):
    ready_for_human_review = "ready_for_human_review"
    blocked_rights = "blocked_rights"
    blocked_missing_evidence = "blocked_missing_evidence"
    blocked_safe_disabled = "blocked_safe_disabled"


class ImprovementDecision(str, Enum):
    accept = "accept"
    reject = "reject"
    supersede = "supersede"


class ImprovementReviewOutcome(str, Enum):
    accepted_for_separate_change_review = "accepted_for_separate_change_review"
    rejected = "rejected"
    superseded = "superseded"
    blocked = "blocked"


class ObservedImprovementOutcome(str, Enum):
    improved = "improved"
    neutral = "neutral"
    regressed = "regressed"
    unknown = "unknown"


class _ImprovementModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _contains_dns(value: str) -> bool:
    return any(
        any(character.isalpha() for character in match.group(0).rsplit(".", 1)[-1])
        for match in _DNS_RE.finditer(value)
    )


def _contains_ipv6(value: str) -> bool:
    for match in _IPV6_RE.finditer(value):
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
        or _contains_dns(value)
        or _IPV4_RE.search(value)
        or _contains_ipv6(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"IMPROVEMENT_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"IMPROVEMENT_{field_name.upper()}_DUPLICATE_REF")
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


class ImprovementEvidenceSource(_ImprovementModel):
    source_kind: ImprovementEvidenceKind
    source_receipt_ref: str
    source_revision_ref: str
    provenance_ref: str
    rights_posture: ImprovementRightsPosture
    rights_evidence_ref: str | None = None
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=24)
    redacted: Literal[True] = True
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_source(self) -> "ImprovementEvidenceSource":
        for field_name in (
            "source_receipt_ref",
            "source_revision_ref",
            "provenance_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.rights_evidence_ref is not None:
            _validate_ref(self.rights_evidence_ref, "rights_evidence_ref")
        _validate_refs(self.evidence_refs, "evidence_refs")
        if (
            self.rights_posture == ImprovementRightsPosture.permitted
            and self.rights_evidence_ref is None
        ):
            raise ValueError("IMPROVEMENT_PERMITTED_RIGHTS_EVIDENCE_REQUIRED")
        return self


class ImprovementProposalRequest(_ImprovementModel):
    workspace_ref: str
    target_kind: ImprovementTargetKind
    target_ref: str
    target_revision_ref: str
    source_evidence: tuple[ImprovementEvidenceSource, ...] = Field(
        ..., min_length=1, max_length=32
    )
    intended_delta_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    expected_regression_refs: tuple[str, ...] = Field(..., min_length=1, max_length=24)
    exception_refs: tuple[str, ...] = Field(default=(), max_length=16)
    rollback_plan_ref: str
    safe_disabled: bool = False
    model_generated: Literal[False] = False
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_request(self) -> "ImprovementProposalRequest":
        for field_name in (
            "workspace_ref",
            "target_ref",
            "target_revision_ref",
            "rollback_plan_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in (
            "intended_delta_refs",
            "expected_regression_refs",
            "exception_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        source_refs = [source.source_receipt_ref for source in self.source_evidence]
        if len(source_refs) != len(set(source_refs)):
            raise ValueError("IMPROVEMENT_DUPLICATE_SOURCE_RECEIPT_REF")
        return self


class ImprovementProposal(_ImprovementModel):
    schema_version: Literal["uaa-governed-improvement.v1"] = IMPROVEMENT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q29:governed-improvement:v1"] = (
        IMPROVEMENT_CONTRACT_REF
    )
    proposal_ref: str
    proposal_fingerprint_ref: str
    workspace_ref: str
    target_kind: ImprovementTargetKind
    target_ref: str
    target_revision_ref: str
    state: ImprovementProposalState
    source_receipt_refs: tuple[str, ...]
    source_revision_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    intended_delta_refs: tuple[str, ...]
    expected_regression_refs: tuple[str, ...]
    exception_refs: tuple[str, ...]
    rights_evidence_refs: tuple[str, ...]
    rollback_plan_ref: str
    review_packet_ref: str
    expected_change_review_scope_ref: str
    dedicated_adr_required: bool
    next_safe_action: str
    blocked_authority_refs: tuple[str, ...]
    target_mutated: Literal[False] = False
    patch_created: Literal[False] = False
    model_trained: Literal[False] = False
    approval_granted: Literal[False] = False
    proposal_promoted: Literal[False] = False
    git_operation_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


class ImprovementReviewRequest(_ImprovementModel):
    proposal: ImprovementProposalRequest
    proposal_ref: str
    proposal_fingerprint_ref: str
    decision: ImprovementDecision
    reviewer_ref: str
    independent_review_ref: str
    idempotency_ref: str
    superseding_proposal_ref: str | None = None

    @model_validator(mode="after")
    def validate_review(self) -> "ImprovementReviewRequest":
        for field_name in (
            "proposal_ref",
            "proposal_fingerprint_ref",
            "reviewer_ref",
            "independent_review_ref",
            "idempotency_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.superseding_proposal_ref is not None:
            _validate_ref(self.superseding_proposal_ref, "superseding_proposal_ref")
        if self.reviewer_ref == self.independent_review_ref:
            raise ValueError("IMPROVEMENT_INDEPENDENT_REVIEW_REF_REQUIRED")
        if self.decision == ImprovementDecision.supersede:
            if (
                self.superseding_proposal_ref is None
                or self.superseding_proposal_ref == self.proposal_ref
            ):
                raise ValueError("IMPROVEMENT_SUPERSEDING_PROPOSAL_REF_REQUIRED")
        elif self.superseding_proposal_ref is not None:
            raise ValueError("IMPROVEMENT_SUPERSEDING_PROPOSAL_REF_NOT_ALLOWED")
        return self


class ImprovementReviewReceipt(_ImprovementModel):
    schema_version: Literal["uaa-governed-improvement.v1"] = IMPROVEMENT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q29:governed-improvement:v1"] = (
        IMPROVEMENT_CONTRACT_REF
    )
    receipt_ref: str
    review_fingerprint_ref: str
    proposal_ref: str
    proposal_fingerprint_ref: str
    reviewer_ref: str
    independent_review_ref: str
    idempotency_ref: str
    decision: ImprovementDecision
    outcome: ImprovementReviewOutcome
    superseding_proposal_ref: str | None = None
    expected_change_review_scope_ref: str | None = None
    rollback_plan_ref: str
    next_safe_action: str
    replayed: bool = False
    target_mutated: Literal[False] = False
    patch_created: Literal[False] = False
    model_trained: Literal[False] = False
    approval_granted: Literal[False] = False
    proposal_promoted: Literal[False] = False
    git_operation_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


class ImprovementOutcomeRequest(_ImprovementModel):
    proposal_ref: str
    proposal_fingerprint_ref: str
    accepted_review_receipt_ref: str
    implemented_change_receipt_ref: str
    implemented_revision_ref: str
    independent_review_ref: str
    regression_evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=32)
    observed_outcome: ObservedImprovementOutcome
    rollback_evidence_ref: str | None = None
    reverted: bool = False
    idempotency_ref: str

    @model_validator(mode="after")
    def validate_outcome(self) -> "ImprovementOutcomeRequest":
        for field_name in (
            "proposal_ref",
            "proposal_fingerprint_ref",
            "accepted_review_receipt_ref",
            "implemented_change_receipt_ref",
            "implemented_revision_ref",
            "independent_review_ref",
            "idempotency_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        _validate_refs(self.regression_evidence_refs, "regression_evidence_refs")
        if self.rollback_evidence_ref is not None:
            _validate_ref(self.rollback_evidence_ref, "rollback_evidence_ref")
        if self.observed_outcome == ObservedImprovementOutcome.regressed:
            if not self.reverted or self.rollback_evidence_ref is None:
                raise ValueError("IMPROVEMENT_REGRESSION_ROLLBACK_EVIDENCE_REQUIRED")
        elif self.reverted:
            raise ValueError("IMPROVEMENT_REVERTED_ONLY_ALLOWED_FOR_REGRESSION")
        return self


class ImprovementOutcomeReceipt(_ImprovementModel):
    schema_version: Literal["uaa-governed-improvement.v1"] = IMPROVEMENT_SCHEMA_VERSION
    contract_ref: Literal["contract-ref:queue-v2:Q29:governed-improvement:v1"] = (
        IMPROVEMENT_CONTRACT_REF
    )
    receipt_ref: str
    outcome_fingerprint_ref: str
    proposal_ref: str
    proposal_fingerprint_ref: str
    accepted_review_receipt_ref: str
    implemented_change_receipt_ref: str
    implemented_revision_ref: str
    independent_review_ref: str
    regression_evidence_refs: tuple[str, ...]
    observed_outcome: ObservedImprovementOutcome
    rollback_evidence_ref: str | None
    reverted: bool
    idempotency_ref: str
    eligible_as_future_evidence: bool
    next_safe_action: str
    replayed: bool = False
    historical_fact_rewritten: Literal[False] = False
    automatic_learning_performed: Literal[False] = False
    target_mutated: Literal[False] = False
    model_trained: Literal[False] = False
    proposal_promoted: Literal[False] = False


def build_improvement_proposal(
    request: ImprovementProposalRequest,
) -> ImprovementProposal:
    payload = request.model_dump(mode="json")
    proposal_fingerprint_ref = _stable_ref(
        "improvement-proposal-fingerprint-ref", payload
    )
    proposal_ref = _stable_ref("improvement-proposal-ref", payload)
    rights_ready = all(
        source.rights_posture == ImprovementRightsPosture.permitted
        and source.rights_evidence_ref is not None
        for source in request.source_evidence
    )
    evidence_ready = all(source.evidence_refs for source in request.source_evidence)
    if request.safe_disabled:
        state = ImprovementProposalState.blocked_safe_disabled
    elif not rights_ready:
        state = ImprovementProposalState.blocked_rights
    elif not evidence_ready:
        state = ImprovementProposalState.blocked_missing_evidence
    else:
        state = ImprovementProposalState.ready_for_human_review
    dedicated_adr_required = request.target_kind == ImprovementTargetKind.tcb_change
    if state == ImprovementProposalState.ready_for_human_review:
        next_safe_action = (
            "Obtain independent human review for a separately governed change lane."
        )
    elif state == ImprovementProposalState.blocked_rights:
        next_safe_action = "Resolve source-specific rights before reuse review."
    elif state == ImprovementProposalState.blocked_missing_evidence:
        next_safe_action = "Attach bounded regression evidence before review."
    else:
        next_safe_action = "Keep the proposal inert while safe-disable is active."
    return ImprovementProposal(
        proposal_ref=proposal_ref,
        proposal_fingerprint_ref=proposal_fingerprint_ref,
        workspace_ref=request.workspace_ref,
        target_kind=request.target_kind,
        target_ref=request.target_ref,
        target_revision_ref=request.target_revision_ref,
        state=state,
        source_receipt_refs=tuple(
            source.source_receipt_ref for source in request.source_evidence
        ),
        source_revision_refs=tuple(
            source.source_revision_ref for source in request.source_evidence
        ),
        evidence_refs=tuple(
            evidence_ref
            for source in request.source_evidence
            for evidence_ref in source.evidence_refs
        ),
        intended_delta_refs=request.intended_delta_refs,
        expected_regression_refs=request.expected_regression_refs,
        exception_refs=request.exception_refs,
        rights_evidence_refs=tuple(
            source.rights_evidence_ref
            for source in request.source_evidence
            if source.rights_evidence_ref is not None
        ),
        rollback_plan_ref=request.rollback_plan_ref,
        review_packet_ref=_stable_ref(
            "improvement-review-packet-ref", proposal_fingerprint_ref
        ),
        expected_change_review_scope_ref=_stable_ref(
            "approval-scope-ref:improvement-change-review", proposal_fingerprint_ref
        ),
        dedicated_adr_required=dedicated_adr_required,
        next_safe_action=next_safe_action,
        blocked_authority_refs=(
            "blocked-authority-ref:self-modifying-code",
            "blocked-authority-ref:automatic-training",
            "blocked-authority-ref:automatic-promotion",
            "blocked-authority-ref:automatic-git-publication",
            "blocked-authority-ref:automatic-merge",
        ),
    )


class ImprovementSession:
    """Bounded process-local review and outcome receipt registry."""

    def __init__(self, *, max_receipts: int = IMPROVEMENT_MAX_SESSION_RECEIPTS):
        if max_receipts < 1 or max_receipts > IMPROVEMENT_MAX_SESSION_RECEIPTS:
            raise ValueError("IMPROVEMENT_SESSION_CAPACITY_INVALID")
        self._max_receipts = max_receipts
        self._reviews: dict[str, ImprovementReviewReceipt] = {}
        self._outcomes: dict[str, ImprovementOutcomeReceipt] = {}
        self._lock = RLock()

    def review(self, request: ImprovementReviewRequest) -> ImprovementReviewReceipt:
        proposal = build_improvement_proposal(request.proposal)
        if (
            request.proposal_ref != proposal.proposal_ref
            or request.proposal_fingerprint_ref != proposal.proposal_fingerprint_ref
        ):
            raise ImprovementConflict("IMPROVEMENT_PROPOSAL_BINDING_CONFLICT")
        payload = request.model_dump(mode="json")
        fingerprint = _stable_ref("improvement-review-fingerprint-ref", payload)
        with self._lock:
            replay = self._reviews.get(request.idempotency_ref)
            if replay is not None:
                if replay.review_fingerprint_ref != fingerprint:
                    raise ImprovementConflict("IMPROVEMENT_REVIEW_IDEMPOTENCY_CONFLICT")
                return replay.model_copy(update={"replayed": True})
            if len(self._reviews) + len(self._outcomes) >= self._max_receipts:
                raise ImprovementError("IMPROVEMENT_SESSION_CAPACITY_REACHED")
            if proposal.state != ImprovementProposalState.ready_for_human_review:
                outcome = ImprovementReviewOutcome.blocked
                scope_ref = None
                next_action = proposal.next_safe_action
            elif request.decision == ImprovementDecision.accept:
                outcome = ImprovementReviewOutcome.accepted_for_separate_change_review
                scope_ref = proposal.expected_change_review_scope_ref
                next_action = "Open a separate exact-scoped change review; no change is authorized."
            elif request.decision == ImprovementDecision.reject:
                outcome = ImprovementReviewOutcome.rejected
                scope_ref = None
                next_action = "Retain the rejection as evidence without changing truth."
            else:
                outcome = ImprovementReviewOutcome.superseded
                scope_ref = None
                next_action = "Review the separately bound superseding proposal."
            receipt = ImprovementReviewReceipt(
                receipt_ref=_stable_ref("improvement-review-receipt-ref", fingerprint),
                review_fingerprint_ref=fingerprint,
                proposal_ref=proposal.proposal_ref,
                proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
                reviewer_ref=request.reviewer_ref,
                independent_review_ref=request.independent_review_ref,
                idempotency_ref=request.idempotency_ref,
                decision=request.decision,
                outcome=outcome,
                superseding_proposal_ref=request.superseding_proposal_ref,
                expected_change_review_scope_ref=scope_ref,
                rollback_plan_ref=proposal.rollback_plan_ref,
                next_safe_action=next_action,
            )
            self._reviews[request.idempotency_ref] = receipt
            return receipt

    def record_outcome(
        self, request: ImprovementOutcomeRequest
    ) -> ImprovementOutcomeReceipt:
        payload = request.model_dump(mode="json")
        fingerprint = _stable_ref("improvement-outcome-fingerprint-ref", payload)
        with self._lock:
            replay = self._outcomes.get(request.idempotency_ref)
            if replay is not None:
                if replay.outcome_fingerprint_ref != fingerprint:
                    raise ImprovementConflict(
                        "IMPROVEMENT_OUTCOME_IDEMPOTENCY_CONFLICT"
                    )
                return replay.model_copy(update={"replayed": True})
            if len(self._reviews) + len(self._outcomes) >= self._max_receipts:
                raise ImprovementError("IMPROVEMENT_SESSION_CAPACITY_REACHED")
            accepted = next(
                (
                    receipt
                    for receipt in self._reviews.values()
                    if receipt.receipt_ref == request.accepted_review_receipt_ref
                ),
                None,
            )
            if (
                accepted is None
                or accepted.outcome
                != ImprovementReviewOutcome.accepted_for_separate_change_review
                or accepted.proposal_ref != request.proposal_ref
                or accepted.proposal_fingerprint_ref != request.proposal_fingerprint_ref
                or accepted.independent_review_ref != request.independent_review_ref
            ):
                raise ImprovementConflict("IMPROVEMENT_OUTCOME_REVIEW_BINDING_CONFLICT")
            eligible = request.observed_outcome in {
                ObservedImprovementOutcome.improved,
                ObservedImprovementOutcome.neutral,
            }
            receipt = ImprovementOutcomeReceipt(
                receipt_ref=_stable_ref("improvement-outcome-receipt-ref", fingerprint),
                outcome_fingerprint_ref=fingerprint,
                proposal_ref=request.proposal_ref,
                proposal_fingerprint_ref=request.proposal_fingerprint_ref,
                accepted_review_receipt_ref=request.accepted_review_receipt_ref,
                implemented_change_receipt_ref=request.implemented_change_receipt_ref,
                implemented_revision_ref=request.implemented_revision_ref,
                independent_review_ref=request.independent_review_ref,
                regression_evidence_refs=request.regression_evidence_refs,
                observed_outcome=request.observed_outcome,
                rollback_evidence_ref=request.rollback_evidence_ref,
                reverted=request.reverted,
                idempotency_ref=request.idempotency_ref,
                eligible_as_future_evidence=eligible,
                next_safe_action=(
                    "A future proposal may cite this receipt after fresh rights review."
                    if eligible
                    else "Keep the outcome blocked from reuse pending investigation."
                ),
            )
            self._outcomes[request.idempotency_ref] = receipt
            return receipt


def build_improvement_status() -> dict[str, Any]:
    """Return an inspectable content-free status for the Q29 boundary."""

    return {
        "schema_version": IMPROVEMENT_SCHEMA_VERSION,
        "contract_ref": IMPROVEMENT_CONTRACT_REF,
        "status": "proposal_only_human_review_required",
        "accepted_source_kinds": [kind.value for kind in ImprovementEvidenceKind],
        "source_specific_rights_required": True,
        "independent_review_required": True,
        "rollback_plan_required": True,
        "outcome_receipts_available": True,
        "self_modifying_code_enabled": False,
        "automatic_training_enabled": False,
        "automatic_promotion_enabled": False,
        "automatic_git_publication_enabled": False,
        "automatic_merge_enabled": False,
        "raw_content_included": False,
    }


__all__ = [
    "IMPROVEMENT_CONTRACT_REF",
    "IMPROVEMENT_MAX_SESSION_RECEIPTS",
    "IMPROVEMENT_SCHEMA_VERSION",
    "ImprovementConflict",
    "ImprovementDecision",
    "ImprovementError",
    "ImprovementEvidenceKind",
    "ImprovementEvidenceSource",
    "ImprovementOutcomeReceipt",
    "ImprovementOutcomeRequest",
    "ImprovementProposal",
    "ImprovementProposalRequest",
    "ImprovementProposalState",
    "ImprovementReviewOutcome",
    "ImprovementReviewReceipt",
    "ImprovementReviewRequest",
    "ImprovementRightsPosture",
    "ImprovementSession",
    "ImprovementTargetKind",
    "ObservedImprovementOutcome",
    "build_improvement_proposal",
    "build_improvement_status",
]
