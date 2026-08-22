"""Deterministic, cited proposal intelligence for ECO-010.

The extractor consumes already-normalized, redacted facts.  It does not read
source content, call a model, create target records, or grant ChangeSet
eligibility.  Its output is review-only metadata for later owner-app workflows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import ipaddress
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.ecosystem.contracts import (
    CanonicalOwnerId,
    EntityKind,
    PrivacyScope,
)
from ultimate_ai_agent.core.ecosystem.ownership import canonical_owner_for
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_PROPOSAL_SCHEMA_VERSION = "uaa-eco-010-proposal-intelligence.v1"
ECO_PROPOSAL_CONTRACT_REF = "contract-ref:eco-010:deterministic-proposals:v1"
MAX_PROPOSAL_FACTS = 64

_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]{2,190}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`(:=,\[])(?:~[/\\]|"
    r"/(?:users|home|usr|var|private|tmp|etc)(?:/|$)|[a-z]:[/\\]|\\\\[^\\\s]+\\)"
)
_EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_HOST_RE = re.compile(
    r"(?:\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b)|"
    r"(?:\b(?:\d{1,3}\.){3}\d{1,3}\b)",
    re.IGNORECASE,
)
_LOCAL_HOST_RE = re.compile(
    r"(?i)(?:^|[^a-z0-9-])localhost(?:[^a-z0-9-]|$)|"
    r"(?:^|[^a-z0-9-])[a-z0-9-]+\.local(?:[^a-z0-9-]|$)"
)
_IPV6_CANDIDATE_RE = re.compile(
    r"(?i)(?<![a-z0-9])(?:\[[0-9a-f:.%]+\]|(?:[0-9a-f]{0,4}:){2,}[0-9a-f:.%]*)(?![a-z0-9])"
)


class ProposalCandidateKind(str, Enum):
    event = "event"
    task = "task"
    person = "person"
    commitment = "commitment"
    meeting = "meeting"


class ProposalReviewPosture(str, Enum):
    ready_for_review = "ready_for_review"
    needs_review = "needs_review"
    blocked_stale_source = "blocked_stale_source"


class ProposalConfidencePosture(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


_TARGET_ENTITY_BY_KIND = {
    ProposalCandidateKind.event: EntityKind.event,
    ProposalCandidateKind.task: EntityKind.task,
    ProposalCandidateKind.person: EntityKind.person,
    ProposalCandidateKind.commitment: EntityKind.commitment,
    ProposalCandidateKind.meeting: EntityKind.event,
}


class _ProposalModel(BaseModel):
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
        raise ValueError(f"ECO_PROPOSAL_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_PROPOSAL_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _validate_safe_summary(value: str) -> str:
    if not value or value != value.strip() or len(value) > 320:
        raise ValueError("ECO_PROPOSAL_SAFE_SUMMARY_BOUNDS_INVALID")
    if (
        "\n" in value
        or "\r" in value
        or "://" in value
        or _RAW_PATH_RE.search(value)
        or _EMAIL_RE.search(value)
        or _HOST_RE.search(value)
        or _LOCAL_HOST_RE.search(value)
        or _contains_ipv6_address(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError("ECO_PROPOSAL_SAFE_SUMMARY_REDACTION_REQUIRED")
    return value


def _contains_ipv6_address(value: str) -> bool:
    for match in _IPV6_CANDIDATE_RE.finditer(value):
        candidate = match.group(0).strip("[]")
        if "%" in candidate:
            candidate = candidate.split("%", 1)[0]
        try:
            if ipaddress.ip_address(candidate).version == 6:
                return True
        except ValueError:
            continue
    return False


def _canonical_timestamp(value: str, field_name: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"ECO_PROPOSAL_{field_name.upper()}_UTC_TIMESTAMP_REQUIRED"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"ECO_PROPOSAL_{field_name.upper()}_UTC_TIMESTAMP_REQUIRED")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class ProposalSourceRevisionBinding(_ProposalModel):
    source_artifact_ref: str
    current_source_revision_ref: str

    @field_validator("source_artifact_ref", "current_source_revision_ref")
    @classmethod
    def validate_refs(cls, value: str, info: Any) -> str:
        return _validate_ref(value, info.field_name)


class ProposalFact(_ProposalModel):
    workspace_ref: str
    fact_ref: str
    source_artifact_ref: str
    source_revision_ref: str
    candidate_kind: ProposalCandidateKind
    safe_summary: str
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=24)
    subject_ref: str | None = None
    participant_refs: tuple[str, ...] = Field(default=(), max_length=24)
    occurred_at: str | None = None
    due_at: str | None = None
    confidence_percent: int = Field(..., ge=0, le=100)
    privacy_scope: PrivacyScope = PrivacyScope.workspace
    ambiguity_refs: tuple[str, ...] = Field(default=(), max_length=24)
    missing_evidence_refs: tuple[str, ...] = Field(default=(), max_length=24)
    model_generated: Literal[False] = False
    raw_source_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_fact(self) -> "ProposalFact":
        for field_name in (
            "workspace_ref",
            "fact_ref",
            "source_artifact_ref",
            "source_revision_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.subject_ref is not None:
            _validate_ref(self.subject_ref, "subject_ref")
        for field_name in (
            "evidence_refs",
            "participant_refs",
            "ambiguity_refs",
            "missing_evidence_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        _validate_safe_summary(self.safe_summary)
        if self.occurred_at is not None:
            object.__setattr__(
                self,
                "occurred_at",
                _canonical_timestamp(self.occurred_at, "occurred_at"),
            )
        if self.due_at is not None:
            object.__setattr__(
                self,
                "due_at",
                _canonical_timestamp(self.due_at, "due_at"),
            )
        return self


class ProposalExtractionRequest(_ProposalModel):
    workspace_ref: str
    facts: tuple[ProposalFact, ...] = Field(
        ..., min_length=1, max_length=MAX_PROPOSAL_FACTS
    )
    source_revision_bindings: tuple[ProposalSourceRevisionBinding, ...] = Field(
        ..., min_length=1, max_length=MAX_PROPOSAL_FACTS
    )
    requested_at: str
    maximum_candidates: int = Field(default=20, ge=1, le=MAX_PROPOSAL_FACTS)

    @model_validator(mode="after")
    def validate_request(self) -> "ProposalExtractionRequest":
        _validate_ref(self.workspace_ref, "workspace_ref")
        object.__setattr__(
            self,
            "requested_at",
            _canonical_timestamp(self.requested_at, "requested_at"),
        )
        if any(fact.workspace_ref != self.workspace_ref for fact in self.facts):
            raise ValueError("ECO_PROPOSAL_CROSS_WORKSPACE_FACT_DENIED")
        fact_refs = [fact.fact_ref for fact in self.facts]
        if len(fact_refs) != len(set(fact_refs)):
            raise ValueError("ECO_PROPOSAL_DUPLICATE_FACT_REF")
        binding_refs = [
            item.source_artifact_ref for item in self.source_revision_bindings
        ]
        if len(binding_refs) != len(set(binding_refs)):
            raise ValueError("ECO_PROPOSAL_DUPLICATE_SOURCE_BINDING")
        known = set(binding_refs)
        if any(fact.source_artifact_ref not in known for fact in self.facts):
            raise ValueError("ECO_PROPOSAL_SOURCE_REVISION_BINDING_REQUIRED")
        return self


class ProposalCandidate(_ProposalModel):
    schema_version: Literal["uaa-eco-010-proposal-intelligence.v1"] = (
        ECO_PROPOSAL_SCHEMA_VERSION
    )
    proposal_ref: str
    candidate_ref: str
    candidate_kind: ProposalCandidateKind
    target_entity_kind: EntityKind
    target_owner: CanonicalOwnerId
    workspace_ref: str
    source_fact_ref: str
    source_artifact_ref: str
    source_revision_ref: str
    current_source_revision_ref: str
    safe_summary: str
    citation_refs: tuple[str, ...]
    subject_ref: str | None
    participant_refs: tuple[str, ...]
    occurred_at: str | None
    due_at: str | None
    confidence_percent: int
    confidence_posture: ProposalConfidencePosture
    privacy_scope: PrivacyScope
    ambiguity_refs: tuple[str, ...]
    missing_evidence_refs: tuple[str, ...]
    stale_state: Literal["current", "stale"]
    review_posture: ProposalReviewPosture
    why_proposed_refs: tuple[str, ...]
    deterministic_extraction: Literal[True] = True
    proposal_only: Literal[True] = True
    direct_commit_allowed: Literal[False] = False
    change_set_eligible: Literal[False] = False
    model_call_performed: Literal[False] = False
    model_output_is_authority: Literal[False] = False
    source_read_performed: Literal[False] = False
    target_write_performed: Literal[False] = False
    external_write_performed: Literal[False] = False


def _confidence_posture(percent: int) -> ProposalConfidencePosture:
    if percent >= 80:
        return ProposalConfidencePosture.high
    if percent >= 60:
        return ProposalConfidencePosture.medium
    return ProposalConfidencePosture.low


def _required_evidence_gaps(fact: ProposalFact) -> tuple[str, ...]:
    gaps = set(fact.missing_evidence_refs)
    if (
        fact.candidate_kind
        in {
            ProposalCandidateKind.event,
            ProposalCandidateKind.meeting,
        }
        and fact.occurred_at is None
    ):
        gaps.add("evidence-missing-ref:eco-010:time")
    if (
        fact.candidate_kind == ProposalCandidateKind.meeting
        and not fact.participant_refs
    ):
        gaps.add("evidence-missing-ref:eco-010:participants")
    if fact.candidate_kind == ProposalCandidateKind.person and fact.subject_ref is None:
        gaps.add("evidence-missing-ref:eco-010:person-identity")
    return tuple(sorted(gaps))


def extract_proposal_candidates(
    request: ProposalExtractionRequest,
) -> dict[str, object]:
    """Return bounded, deterministic proposal metadata for human review."""

    current_revision_by_artifact = {
        item.source_artifact_ref: item.current_source_revision_ref
        for item in request.source_revision_bindings
    }
    candidates: list[ProposalCandidate] = []
    for fact in sorted(request.facts, key=lambda item: item.fact_ref):
        current_revision_ref = current_revision_by_artifact[fact.source_artifact_ref]
        stale_state: Literal["current", "stale"] = (
            "current" if fact.source_revision_ref == current_revision_ref else "stale"
        )
        missing_evidence_refs = _required_evidence_gaps(fact)
        confidence_posture = _confidence_posture(fact.confidence_percent)
        if stale_state == "stale":
            review_posture = ProposalReviewPosture.blocked_stale_source
        elif (
            missing_evidence_refs
            or fact.ambiguity_refs
            or confidence_posture == ProposalConfidencePosture.low
        ):
            review_posture = ProposalReviewPosture.needs_review
        else:
            review_posture = ProposalReviewPosture.ready_for_review
        target_entity_kind = _TARGET_ENTITY_BY_KIND[fact.candidate_kind]
        binding = {
            "candidate_kind": fact.candidate_kind.value,
            "current_source_revision_ref": current_revision_ref,
            "fact_ref": fact.fact_ref,
            "source_artifact_ref": fact.source_artifact_ref,
            "source_revision_ref": fact.source_revision_ref,
            "workspace_ref": fact.workspace_ref,
        }
        candidates.append(
            ProposalCandidate(
                proposal_ref=_stable_ref("proposal-ref", binding),
                candidate_ref=_stable_ref(
                    "proposal-candidate-ref", {**binding, "summary": fact.safe_summary}
                ),
                candidate_kind=fact.candidate_kind,
                target_entity_kind=target_entity_kind,
                target_owner=canonical_owner_for(target_entity_kind),
                workspace_ref=fact.workspace_ref,
                source_fact_ref=fact.fact_ref,
                source_artifact_ref=fact.source_artifact_ref,
                source_revision_ref=fact.source_revision_ref,
                current_source_revision_ref=current_revision_ref,
                safe_summary=fact.safe_summary,
                citation_refs=fact.evidence_refs,
                subject_ref=fact.subject_ref,
                participant_refs=fact.participant_refs,
                occurred_at=fact.occurred_at,
                due_at=fact.due_at,
                confidence_percent=fact.confidence_percent,
                confidence_posture=confidence_posture,
                privacy_scope=fact.privacy_scope,
                ambiguity_refs=fact.ambiguity_refs,
                missing_evidence_refs=missing_evidence_refs,
                stale_state=stale_state,
                review_posture=review_posture,
                why_proposed_refs=(
                    f"why-proposed-ref:eco-010:{fact.candidate_kind.value}",
                    f"why-proposed-ref:eco-010:confidence-{confidence_posture.value}",
                    "why-proposed-ref:eco-010:cited-normalized-fact",
                ),
            )
        )
    bounded = candidates[: request.maximum_candidates]
    posture_counts = {
        posture.value: sum(item.review_posture == posture for item in bounded)
        for posture in ProposalReviewPosture
    }
    return {
        "schema_version": ECO_PROPOSAL_SCHEMA_VERSION,
        "contract_ref": ECO_PROPOSAL_CONTRACT_REF,
        "status": "ready" if bounded else "ready_empty",
        "requested_at": request.requested_at,
        "workspace_ref": request.workspace_ref,
        "candidate_count": len(bounded),
        "truncated": len(candidates) > len(bounded),
        "maximum_candidates": request.maximum_candidates,
        "review_posture_counts": posture_counts,
        "candidates": [item.model_dump(mode="json") for item in bounded],
        "deterministic_extraction": True,
        "proposal_only": True,
        "raw_source_content_included": False,
        "source_read_performed": False,
        "model_call_performed": False,
        "model_output_is_authority": False,
        "change_set_created": False,
        "approval_grant_created": False,
        "target_write_performed": False,
        "external_write_performed": False,
        "blocked_authority_refs": [
            "blocked-authority-ref:eco-010:model-assisted-generation",
            "blocked-authority-ref:eco-010:changeset-creation",
            "blocked-authority-ref:eco-010:direct-target-commit",
            "blocked-authority-ref:eco-010:external-write",
        ],
        "evidence_refs": [
            "evidence-ref:eco-010:deterministic-safe-facts-only",
            "evidence-ref:eco-010:source-revision-bound-citations",
        ],
    }
