from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ultimate_ai_agent.core.decision_router.turn_contracts import (
    RiskFlag,
    TurnContractKind,
    TurnDecision,
)


TURN_CLASSIFIER_POLICY_REF = "policy-ref:turn-contract-router:deterministic-classifier:v1"


@dataclass(frozen=True)
class _ClassificationResult:
    turn_contract: TurnContractKind
    confidence: float
    reason_refs: tuple[str, ...]
    risk_flags: tuple[RiskFlag, ...] = ()
    safe_summary: str = "Deterministic turn classifier selected a safe contract from bounded rule refs."


_BLOCKED_UNSAFE_PATTERNS = (
    re.compile(r"\b(credential theft|steal credentials|phishing|malware|ransomware)\b", re.IGNORECASE),
    re.compile(r"\b(hack into|bypass security|exfiltrate|keylogger|unauthorized access)\b", re.IGNORECASE),
)
_HIGH_RISK_EXTERNAL_PATTERNS = (
    re.compile(r"\b(use my card|credit card|debit card|checkout|buy|purchase|pay|order|book|reserve)\b", re.IGNORECASE),
    re.compile(r"\b(cancel|submit|sign|transfer|withdraw|grant access|change password)\b", re.IGNORECASE),
)
_CREDENTIAL_PRIVACY_PATTERNS = (
    re.compile(r"\b(credentials?|password|account|merchant|money|identity|payment)\b", re.IGNORECASE),
    re.compile(r"\b(private|personal|confidential)\s+(account|data|file|document|information)\b", re.IGNORECASE),
)
_EXTERNAL_SIDE_EFFECT_PATTERNS = (
    re.compile(r"\b(send|email|message|post|share|upload)\b", re.IGNORECASE),
    re.compile(r"\b(delete|remove|overwrite|destroy)\b", re.IGNORECASE),
)
_MEMORY_WRITE_PATTERNS = (
    re.compile(r"\b(remember this|save this|remember that|store this|keep this in memory)\b", re.IGNORECASE),
)
_MEMORY_READ_PATTERNS = (
    re.compile(r"\b(using what you know|what you know about me|my preferences|my office|my home)\b", re.IGNORECASE),
    re.compile(r"\b(my files|my calendar|last time|what did i tell you|based on my previous|from my account)\b", re.IGNORECASE),
)
_FRESH_CURRENT_PATTERNS = (
    re.compile(r"\b(latest|current|today|this week|near me|search|look up|cite sources)\b", re.IGNORECASE),
    re.compile(r"\b(current price|availability|inventory)\b", re.IGNORECASE),
)
_DRAFT_PLAN_PATTERNS = (
    re.compile(r"\b(make a plan|shopping list|itinerary|proposal|compare options)\b", re.IGNORECASE),
    re.compile(r"\b(break into tasks|draft|outline|checklist)\b", re.IGNORECASE),
)
_BASE_ANSWER_PATTERNS = (
    re.compile(r"\b(base answer path|base_answer|base answer)\b", re.IGNORECASE),
)
_CLARIFY_PATTERNS = (
    re.compile(r"\b(handle that thing|take care of it|do the thing|you know what to do)\b", re.IGNORECASE),
)
_DIY_DIRECT_PATTERNS = (
    re.compile(r"\b(diy|wood|table|chair|shelf|construct|build|make)\b", re.IGNORECASE),
)
_SOFTWARE_DIRECT_PATTERNS = (
    re.compile(r"\b(react|python|sql|api|component|function|class|package|repo|code|compile|test)\b", re.IGNORECASE),
)


def classify_turn_contract(
    request_text: str,
    *,
    decision_ref: str = "turn-decision:deterministic-classifier",
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> TurnDecision:
    """Classify one turn with no effects and without storing the request text."""
    normalized = _normalize_request(request_text)
    result = _classify_normalized_request(normalized)
    return TurnDecision(
        decision_ref=decision_ref,
        turn_contract=result.turn_contract,
        confidence=result.confidence,
        safe_summary=result.safe_summary,
        reason_refs=list(result.reason_refs),
        source_refs=source_refs or ["source:turn-contract:deterministic-classifier"],
        evidence_refs=evidence_refs or ["evidence:turn-contract:deterministic-rules"],
        risk_flags=list(result.risk_flags),
    )


def _classify_normalized_request(text: str) -> _ClassificationResult:
    if _matches_any(text, _BLOCKED_UNSAFE_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.blocked_unsafe,
            confidence=0.98,
            reason_refs=("reason-ref:turn-contract:blocked-unsafe",),
            risk_flags=(RiskFlag.unsafe,),
            safe_summary="Deterministic classifier blocked the turn because unsafe signals were present.",
        )
    if _matches_any(text, _HIGH_RISK_EXTERNAL_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.approval_required,
            confidence=0.95,
            reason_refs=("reason-ref:turn-contract:high-risk-external-side-effect",),
            risk_flags=(RiskFlag.external_side_effect, RiskFlag.credential_or_payment),
            safe_summary="Deterministic classifier required approval for a high-risk external action boundary.",
        )
    if _matches_any(text, _CREDENTIAL_PRIVACY_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.approval_required,
            confidence=0.92,
            reason_refs=("reason-ref:turn-contract:credential-account-privacy-boundary",),
            risk_flags=(RiskFlag.privacy_boundary, RiskFlag.credential_or_payment),
            safe_summary="Deterministic classifier required approval for a credential, account, or privacy boundary.",
        )
    if _matches_any(text, _EXTERNAL_SIDE_EFFECT_PATTERNS):
        flags = [RiskFlag.external_side_effect]
        if re.search(r"\b(delete|remove|overwrite|destroy)\b", text, re.IGNORECASE):
            flags.append(RiskFlag.destructive)
        return _ClassificationResult(
            turn_contract=TurnContractKind.approval_required,
            confidence=0.9,
            reason_refs=("reason-ref:turn-contract:external-side-effect",),
            risk_flags=tuple(flags),
            safe_summary="Deterministic classifier required approval for an external or destructive action boundary.",
        )
    if _matches_any(text, _MEMORY_WRITE_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.approval_required,
            confidence=0.88,
            reason_refs=("reason-ref:turn-contract:memory-write-review-required",),
            risk_flags=(RiskFlag.memory_requested, RiskFlag.privacy_boundary),
            safe_summary="Deterministic classifier required review before any durable memory change.",
        )
    if _matches_any(text, _MEMORY_READ_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.answer_with_reviewed_memory,
            confidence=0.84,
            reason_refs=("reason-ref:turn-contract:reviewed-memory-request",),
            risk_flags=(RiskFlag.memory_requested,),
            safe_summary="Deterministic classifier selected reviewed memory context for a personal-context request.",
        )
    if _matches_any(text, _FRESH_CURRENT_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.prepare_tool_or_action,
            confidence=0.82,
            reason_refs=("reason-ref:turn-contract:fresh-current-research-request",),
            risk_flags=(RiskFlag.freshness_required,),
            safe_summary="Deterministic classifier selected read-only preparation for current or research signals.",
        )
    if _matches_any(text, _DRAFT_PLAN_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.draft_or_plan,
            confidence=0.78,
            reason_refs=("reason-ref:turn-contract:draft-plan-request",),
            safe_summary="Deterministic classifier selected a draft or planning contract.",
        )
    if _matches_any(text, _BASE_ANSWER_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.base_answer,
            confidence=0.86,
            reason_refs=("reason-ref:turn-contract:explicit-base-answer-request",),
            safe_summary="Deterministic classifier selected the explicit base answer path.",
        )
    if _matches_any(text, _CLARIFY_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.ask_clarifying_question,
            confidence=0.62,
            reason_refs=("reason-ref:turn-contract:clarification-needed",),
            safe_summary="Deterministic classifier selected clarification because the request was underspecified.",
        )
    if _matches_any(text, _SOFTWARE_DIRECT_PATTERNS) or _matches_any(text, _DIY_DIRECT_PATTERNS):
        return _ClassificationResult(
            turn_contract=TurnContractKind.answer_directly,
            confidence=0.74,
            reason_refs=("reason-ref:turn-contract:informational-direct-answer",),
            risk_flags=(RiskFlag.low_risk,),
            safe_summary="Deterministic classifier selected a direct informational answer.",
        )
    return _ClassificationResult(
        turn_contract=TurnContractKind.answer_directly,
        confidence=0.7,
        reason_refs=("reason-ref:turn-contract:default-direct-answer",),
        risk_flags=(RiskFlag.low_risk,),
        safe_summary="Deterministic classifier selected the default direct answer contract.",
    )


def _normalize_request(request_text: str) -> str:
    return re.sub(r"\s+", " ", request_text.strip()).lower()


def _matches_any(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)
