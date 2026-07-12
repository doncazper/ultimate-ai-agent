from __future__ import annotations

from enum import Enum
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.turn_classifier import (
    TURN_CLASSIFIER_POLICY_REF,
    classify_turn_contract,
)
from ultimate_ai_agent.core.decision_router.turn_contracts import TurnContractKind
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.safe_contract_text import validate_safe_contract_text_shape


INTENT_REASONING_TRUTH_SCHEMA_VERSION = "uaa-intent-reasoning-truth.v1"
INTENT_REASONING_TRUTH_CONTRACT_REF = "contract-ref:intent-reasoning-truth:v1"
INTENT_REASONING_TRUTH_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:reasoning-truth:no-approval-authority",
    "blocked-state:reasoning-truth:no-lease-authority",
    "blocked-state:reasoning-truth:no-tool-or-action-authority",
    "blocked-state:reasoning-truth:no-memory-truth-or-write",
    "blocked-state:reasoning-truth:no-provider-authority",
    "blocked-state:reasoning-truth:no-web-or-shell-authority",
    "blocked-state:reasoning-truth:no-production-authority",
)

_INSTRUCTION_SHAPED_PATTERNS = (
    re.compile(r"\bignore (?:all |any )?(?:previous|prior) instructions?\b", re.I),
    re.compile(r"\b(?:system|developer) (?:message|prompt|instructions?)\b", re.I),
    re.compile(r"\b(?:call|invoke|run) (?:the )?(?:tool|function|command)\b", re.I),
    re.compile(r"\b(?:grant|assume|override) (?:my )?(?:authority|approval)\b", re.I),
)


class ReasoningStatementKind(str, Enum):
    fact = "fact"
    assumption = "assumption"
    unknown = "unknown"


class IntentConfidenceBand(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    conflicting = "conflicting"


class IntentAmbiguityPosture(str, Enum):
    clear = "clear"
    ambiguous_missing_scope = "ambiguous_missing_scope"
    conflicting = "conflicting"
    insufficient_evidence = "insufficient_evidence"


class IntentContradictionPosture(str, Enum):
    none_observed = "none_observed"
    conflicting_safe_refs = "conflicting_safe_refs"


class InstructionContentPosture(str, Enum):
    untrusted_data = "untrusted_data"
    instruction_shaped_untrusted_data = "instruction_shaped_untrusted_data"


class IntentReasoningAuthorityPosture(str, Enum):
    non_authoritative_review_truth = "non_authoritative_review_truth"


class ModelAssistancePosture(str, Enum):
    deterministic_only = "deterministic_only"
    exact_provider_lane_required = "exact_provider_lane_required"


class _FrozenContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))}"


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} contains duplicate refs")
    for value in values:
        _validate_ref(value, field_name)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    if re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_-]*(?::[A-Za-z0-9][A-Za-z0-9:_-]*)+",
        value,
    ) is None:
        raise ValueError(f"{field_name} must contain opaque safe refs")


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    validate_safe_contract_text_shape(value, field_name)


class ReasoningStatement(_FrozenContract):
    statement_ref: str
    kind: ReasoningStatementKind
    safe_summary: str = Field(..., min_length=1, max_length=320)
    source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=12)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=12)
    review_required: bool

    @model_validator(mode="after")
    def validate_statement(self) -> "ReasoningStatement":
        _validate_ref(self.statement_ref, "reasoning_statement_ref")
        _validate_safe_text(self.safe_summary, "reasoning_statement_summary")
        _validate_refs(self.source_refs, "reasoning_statement_source_refs")
        _validate_refs(self.evidence_refs, "reasoning_statement_evidence_refs")
        if self.kind == ReasoningStatementKind.fact and not self.evidence_refs:
            raise ValueError("reasoning fact requires evidence refs")
        if self.kind in {
            ReasoningStatementKind.assumption,
            ReasoningStatementKind.unknown,
        } and not self.review_required:
            raise ValueError("assumptions and unknowns require review")
        return self


class OperatorQuestion(_FrozenContract):
    question_ref: str
    safe_question: str = Field(..., min_length=1, max_length=240)
    resolves_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)

    @model_validator(mode="after")
    def validate_question(self) -> "OperatorQuestion":
        _validate_ref(self.question_ref, "operator_question_ref")
        _validate_safe_text(self.safe_question, "operator_safe_question")
        _validate_refs(self.resolves_refs, "operator_question_resolves_refs")
        return self


class IntentAssessmentInput(_FrozenContract):
    intent_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    facts: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    assumptions: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    unknowns: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    contradiction_refs: tuple[str, ...] = Field(default=(), max_length=8)
    operator_questions: tuple[OperatorQuestion, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def validate_input(self) -> "IntentAssessmentInput":
        _validate_ref(self.intent_ref, "intent_ref")
        _validate_safe_text(self.safe_summary, "intent_safe_summary")
        for field_name in ("source_refs", "evidence_refs", "contradiction_refs"):
            _validate_refs(getattr(self, field_name), field_name)
        expected_kinds = (
            (self.facts, ReasoningStatementKind.fact, "facts"),
            (self.assumptions, ReasoningStatementKind.assumption, "assumptions"),
            (self.unknowns, ReasoningStatementKind.unknown, "unknowns"),
        )
        all_refs: list[str] = []
        for statements, expected_kind, field_name in expected_kinds:
            if any(statement.kind != expected_kind for statement in statements):
                raise ValueError(f"{field_name} contain the wrong statement kind")
            all_refs.extend(statement.statement_ref for statement in statements)
        if len(all_refs) != len(set(all_refs)):
            raise ValueError("reasoning statement refs must be unique")
        if self.contradiction_refs and not self.operator_questions:
            raise ValueError("contradictions require an operator question")
        unresolved_refs = {
            *self.contradiction_refs,
            *(statement.statement_ref for statement in self.unknowns),
        }
        if len(unresolved_refs) > 8:
            raise ValueError("intent input has too many unresolved refs")
        if self.operator_questions:
            covered_refs = {
                ref
                for question in self.operator_questions
                for ref in question.resolves_refs
            }
            if unresolved_refs - covered_refs:
                raise ValueError("operator questions do not cover unresolved refs")
        return self


class IntentReasoningTruth(_FrozenContract):
    schema_version: Literal["uaa-intent-reasoning-truth.v1"] = (
        INTENT_REASONING_TRUTH_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:intent-reasoning-truth:v1"] = (
        INTENT_REASONING_TRUTH_CONTRACT_REF
    )
    intent_ref: str
    intent_fingerprint_ref: str
    request_fingerprint_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=420)
    classification_ref: str
    turn_contract: TurnContractKind
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_band: IntentConfidenceBand
    ambiguity_posture: IntentAmbiguityPosture
    contradiction_posture: IntentContradictionPosture
    instruction_content_posture: InstructionContentPosture
    facts: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    assumptions: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    unknowns: tuple[ReasoningStatement, ...] = Field(default=(), max_length=16)
    operator_questions: tuple[OperatorQuestion, ...] = Field(default=(), max_length=8)
    source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    contradiction_refs: tuple[str, ...] = Field(default=(), max_length=8)
    reason_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    deterministic_policy_ref: str = TURN_CLASSIFIER_POLICY_REF
    model_assistance_posture: ModelAssistancePosture = (
        ModelAssistancePosture.deterministic_only
    )
    authority_posture: IntentReasoningAuthorityPosture = (
        IntentReasoningAuthorityPosture.non_authoritative_review_truth
    )
    blocked_authority_refs: tuple[str, ...] = (
        INTENT_REASONING_TRUTH_BLOCKED_AUTHORITY_REFS
    )
    backend_owned: Literal[True] = True
    safe_refs_only: Literal[True] = True
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_truth(self) -> "IntentReasoningTruth":
        for value, field_name in (
            (self.intent_ref, "intent_ref"),
            (self.intent_fingerprint_ref, "intent_fingerprint_ref"),
            (self.request_fingerprint_ref, "intent_request_fingerprint_ref"),
            (self.classification_ref, "intent_classification_ref"),
            (self.deterministic_policy_ref, "intent_deterministic_policy_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "intent_safe_summary")
        for field_name in (
            "source_refs",
            "evidence_refs",
            "contradiction_refs",
            "reason_refs",
            "blocked_authority_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        missing_blocked = set(INTENT_REASONING_TRUTH_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        )
        if missing_blocked:
            raise ValueError("intent reasoning truth is missing blocked authority refs")
        expected_kinds = (
            (self.facts, ReasoningStatementKind.fact, "facts"),
            (self.assumptions, ReasoningStatementKind.assumption, "assumptions"),
            (self.unknowns, ReasoningStatementKind.unknown, "unknowns"),
        )
        statement_refs: list[str] = []
        for statements, expected_kind, field_name in expected_kinds:
            if any(statement.kind != expected_kind for statement in statements):
                raise ValueError(f"intent reasoning {field_name} contain wrong kinds")
            statement_refs.extend(statement.statement_ref for statement in statements)
        if len(statement_refs) != len(set(statement_refs)):
            raise ValueError("intent reasoning statement refs must be unique")
        resolvable_refs = set(statement_refs) | set(self.contradiction_refs) | {
            self.intent_ref
        }
        if any(
            ref not in resolvable_refs
            for question in self.operator_questions
            for ref in question.resolves_refs
        ):
            raise ValueError("operator question resolves an unknown reasoning ref")
        required_question_refs = {
            *self.contradiction_refs,
            *(statement.statement_ref for statement in self.unknowns),
        }
        covered_question_refs = {
            ref
            for question in self.operator_questions
            for ref in question.resolves_refs
        }
        if required_question_refs - covered_question_refs:
            raise ValueError("operator questions do not cover unresolved refs")
        expected_band = _confidence_band(
            self.confidence_score,
            has_contradictions=bool(self.contradiction_refs),
        )
        if self.confidence_band != expected_band:
            raise ValueError("intent confidence band does not match score or conflicts")
        if bool(self.contradiction_refs) != (
            self.contradiction_posture
            == IntentContradictionPosture.conflicting_safe_refs
        ):
            raise ValueError("intent contradiction posture is inconsistent")
        if self.contradiction_refs and (
            self.ambiguity_posture != IntentAmbiguityPosture.conflicting
            or not self.operator_questions
        ):
            raise ValueError("conflicting intent must remain ambiguous and ask")
        if (
            self.confidence_band in {
                IntentConfidenceBand.low,
                IntentConfidenceBand.conflicting,
            }
            or self.ambiguity_posture != IntentAmbiguityPosture.clear
        ) and not self.operator_questions:
            raise ValueError("low-confidence or ambiguous intent must ask the operator")
        expected = _fingerprint("intent-fingerprint-ref", _truth_payload(self))
        if self.intent_fingerprint_ref != expected:
            raise ValueError("intent reasoning fingerprint mismatch")
        return self


def _confidence_band(
    score: float,
    *,
    has_contradictions: bool,
) -> IntentConfidenceBand:
    if has_contradictions:
        return IntentConfidenceBand.conflicting
    if score >= 0.8:
        return IntentConfidenceBand.high
    if score >= 0.6:
        return IntentConfidenceBand.medium
    return IntentConfidenceBand.low


def _truth_payload(truth: IntentReasoningTruth) -> dict[str, object]:
    return {
        "schema_version": truth.schema_version,
        "contract_ref": truth.contract_ref,
        "intent_ref": truth.intent_ref,
        "request_fingerprint_ref": truth.request_fingerprint_ref,
        "safe_summary": truth.safe_summary,
        "classification_ref": truth.classification_ref,
        "turn_contract": truth.turn_contract,
        "confidence_score": truth.confidence_score,
        "confidence_band": truth.confidence_band,
        "ambiguity_posture": truth.ambiguity_posture,
        "contradiction_posture": truth.contradiction_posture,
        "instruction_content_posture": truth.instruction_content_posture,
        "facts": [item.model_dump(mode="json") for item in truth.facts],
        "assumptions": [item.model_dump(mode="json") for item in truth.assumptions],
        "unknowns": [item.model_dump(mode="json") for item in truth.unknowns],
        "operator_questions": [
            item.model_dump(mode="json") for item in truth.operator_questions
        ],
        "source_refs": truth.source_refs,
        "evidence_refs": truth.evidence_refs,
        "contradiction_refs": truth.contradiction_refs,
        "reason_refs": truth.reason_refs,
        "deterministic_policy_ref": truth.deterministic_policy_ref,
        "model_assistance_posture": truth.model_assistance_posture,
        "authority_posture": truth.authority_posture,
        "blocked_authority_refs": truth.blocked_authority_refs,
        "backend_owned": truth.backend_owned,
        "safe_refs_only": truth.safe_refs_only,
        "raw_content_included": truth.raw_content_included,
    }


def assess_intent(
    raw_request: str,
    assessment_input: IntentAssessmentInput,
) -> IntentReasoningTruth:
    """Derive no-effect reasoning truth while keeping request content transient."""

    if not isinstance(raw_request, str) or not raw_request.strip():
        raise ValueError("transient request text is required")
    if len(raw_request) > 8_192:
        raise ValueError("transient request text exceeds the bounded limit")
    request_fingerprint_ref = (
        f"intent-request-fingerprint-ref:sha256:{hash_text(raw_request)}"
    )
    decision = classify_turn_contract(
        raw_request,
        decision_ref=(
            f"turn-decision:{_safe_suffix(assessment_input.intent_ref)}:"
            f"{request_fingerprint_ref.rsplit(':', 1)[-1]}"
        ),
        source_refs=list(assessment_input.source_refs),
        evidence_refs=list(assessment_input.evidence_refs),
    )
    instruction_shaped = any(
        pattern.search(raw_request) for pattern in _INSTRUCTION_SHAPED_PATTERNS
    )
    has_contradictions = bool(assessment_input.contradiction_refs)
    if has_contradictions:
        confidence_score = min(float(decision.confidence), 0.39)
        ambiguity_posture = IntentAmbiguityPosture.conflicting
    elif not assessment_input.facts:
        confidence_score = min(float(decision.confidence), 0.45)
        ambiguity_posture = IntentAmbiguityPosture.insufficient_evidence
    elif assessment_input.unknowns:
        confidence_score = min(float(decision.confidence), 0.55)
        ambiguity_posture = IntentAmbiguityPosture.ambiguous_missing_scope
    else:
        confidence_score = float(decision.confidence)
        ambiguity_posture = IntentAmbiguityPosture.clear
    confidence_score = round(confidence_score, 2)
    questions = assessment_input.operator_questions
    if (
        has_contradictions
        or ambiguity_posture != IntentAmbiguityPosture.clear
        or confidence_score < 0.6
    ) and not questions:
        unresolved_refs = tuple(
            dict.fromkeys(
                [
                    *assessment_input.contradiction_refs,
                    *(item.statement_ref for item in assessment_input.unknowns),
                ]
            )
        ) or (assessment_input.intent_ref,)
        questions = tuple(
            OperatorQuestion(
                question_ref=(
                    f"question-ref:intent:{index + 1}-{_safe_suffix(resolves_ref)}"
                ),
                safe_question=(
                    "Which exact reviewed scope should be used before this intent "
                    "is advanced?"
                ),
                resolves_refs=(resolves_ref,),
            )
            for index, resolves_ref in enumerate(unresolved_refs)
        )
    reason_refs = tuple(
        dict.fromkeys(
            [
                *decision.reason_refs,
                *(
                    ["reason-ref:intent:instruction-shaped-content-untrusted"]
                    if instruction_shaped
                    else []
                ),
                *(
                    ["reason-ref:intent:contradiction-requires-operator"]
                    if has_contradictions
                    else []
                ),
                *(
                    ["reason-ref:intent:unknowns-require-operator"]
                    if assessment_input.unknowns
                    else []
                ),
            ]
        )
    )
    payload = {
        "schema_version": INTENT_REASONING_TRUTH_SCHEMA_VERSION,
        "contract_ref": INTENT_REASONING_TRUTH_CONTRACT_REF,
        "intent_ref": assessment_input.intent_ref,
        "request_fingerprint_ref": request_fingerprint_ref,
        "safe_summary": assessment_input.safe_summary,
        "classification_ref": decision.decision_ref,
        "turn_contract": str(decision.turn_contract),
        "confidence_score": confidence_score,
        "confidence_band": _confidence_band(
            confidence_score,
            has_contradictions=has_contradictions,
        ),
        "ambiguity_posture": ambiguity_posture,
        "contradiction_posture": (
            IntentContradictionPosture.conflicting_safe_refs
            if has_contradictions
            else IntentContradictionPosture.none_observed
        ),
        "instruction_content_posture": (
            InstructionContentPosture.instruction_shaped_untrusted_data
            if instruction_shaped
            else InstructionContentPosture.untrusted_data
        ),
        "facts": [item.model_dump(mode="json") for item in assessment_input.facts],
        "assumptions": [
            item.model_dump(mode="json") for item in assessment_input.assumptions
        ],
        "unknowns": [
            item.model_dump(mode="json") for item in assessment_input.unknowns
        ],
        "operator_questions": [item.model_dump(mode="json") for item in questions],
        "source_refs": assessment_input.source_refs,
        "evidence_refs": assessment_input.evidence_refs,
        "contradiction_refs": assessment_input.contradiction_refs,
        "reason_refs": reason_refs,
        "deterministic_policy_ref": TURN_CLASSIFIER_POLICY_REF,
        "model_assistance_posture": ModelAssistancePosture.deterministic_only,
        "authority_posture": (
            IntentReasoningAuthorityPosture.non_authoritative_review_truth
        ),
        "blocked_authority_refs": INTENT_REASONING_TRUTH_BLOCKED_AUTHORITY_REFS,
        "backend_owned": True,
        "safe_refs_only": True,
        "raw_content_included": False,
    }
    return IntentReasoningTruth(
        **payload,
        intent_fingerprint_ref=_fingerprint("intent-fingerprint-ref", payload),
    )


def _safe_suffix(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-")[:96] or "unknown"
