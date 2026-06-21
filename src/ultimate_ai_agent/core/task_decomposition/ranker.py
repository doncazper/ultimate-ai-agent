from __future__ import annotations

from typing import Iterable

from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityContract,
    CapabilityOutcomeMetrics,
    CapabilityRankScore,
    CostHint,
    TaskIntent,
    permission_requires_approval,
    risk_rank,
)


def _tokenize(value: str) -> set[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in value)
    return {part for part in cleaned.split() if part}


def _text_tokens(values: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        tokens.update(_tokenize(value))
    return tokens


class CapabilityRanker:
    def __init__(self, outcome_metrics: dict[str, CapabilityOutcomeMetrics] | None = None) -> None:
        self.outcome_metrics = outcome_metrics or {}

    def score(self, intent: TaskIntent, contract: CapabilityContract) -> CapabilityRankScore:
        card = contract.card
        query_tokens = _text_tokens(
            [
                intent.goal,
                intent.expected_output or "",
                *intent.constraints,
                *intent.success_criteria,
            ]
        )
        semantic_tokens = _text_tokens(
            [
                card.name,
                card.summary,
                *card.use_when,
                *card.do_not_use_when,
            ]
        )
        tag_tokens = _text_tokens([*card.domains, *card.tags])
        hint_tokens = _text_tokens([*card.input_hints, *card.output_hints])

        semantic_score = self._overlap_score(query_tokens, semantic_tokens)
        schema_score = self._overlap_score(query_tokens, hint_tokens)
        tag_domain_score = self._overlap_score(query_tokens, tag_tokens)
        historical_score = self._historical_score(card.id, card.reliability_score)
        cost_latency_score = self._cost_latency_score(card.cost_hint, card.typical_latency_ms)
        permission_score = self._permission_score(contract.required_permissions)
        risk_score = self._risk_score(intent, contract)

        total = (
            semantic_score * 0.32
            + schema_score * 0.16
            + tag_domain_score * 0.14
            + historical_score * 0.14
            + cost_latency_score * 0.10
            + permission_score * 0.08
            + risk_score * 0.06
        )
        reason_codes = ["CAPABILITY_RANKED"]
        if risk_score < 0.5:
            reason_codes.append("CAPABILITY_RISK_PENALIZED")
        if permission_score < 0.5:
            reason_codes.append("CAPABILITY_PERMISSION_PENALIZED")
        return CapabilityRankScore(
            capability_id=card.id,
            total_score=round(total, 6),
            semantic_score=round(semantic_score, 6),
            schema_score=round(schema_score, 6),
            tag_domain_score=round(tag_domain_score, 6),
            historical_score=round(historical_score, 6),
            cost_latency_score=round(cost_latency_score, 6),
            permission_score=round(permission_score, 6),
            risk_score=round(risk_score, 6),
            reason_codes=reason_codes,
        )

    def _overlap_score(self, query_tokens: set[str], candidate_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.5
        overlap = len(query_tokens & candidate_tokens)
        return min(1.0, overlap / max(1, min(len(query_tokens), 8)))

    def _historical_score(self, capability_id: str, reliability_score: float) -> float:
        metrics = self.outcome_metrics.get(capability_id)
        if metrics is None or metrics.total_calls == 0:
            return reliability_score
        return (metrics.success_rate + reliability_score) / 2

    def _cost_latency_score(self, cost_hint: CostHint, typical_latency_ms: int | None) -> float:
        cost_score = {
            CostHint.free: 1.0,
            CostHint.low: 0.85,
            CostHint.medium: 0.55,
            CostHint.high: 0.25,
        }[CostHint(cost_hint)]
        if typical_latency_ms is None:
            latency_score = 0.7
        elif typical_latency_ms <= 250:
            latency_score = 1.0
        elif typical_latency_ms <= 1000:
            latency_score = 0.75
        elif typical_latency_ms <= 5000:
            latency_score = 0.45
        else:
            latency_score = 0.2
        return (cost_score + latency_score) / 2

    def _permission_score(self, permissions: list[str]) -> float:
        if not permissions:
            return 1.0
        dangerous = sum(1 for permission in permissions if permission_requires_approval(permission))
        return max(0.0, 1.0 - dangerous / len(permissions))

    def _risk_score(self, intent: TaskIntent, contract: CapabilityContract) -> float:
        capability_risk = risk_rank(contract.card.risk_level)
        task_risk = risk_rank(intent.risk_level)
        if capability_risk <= task_risk:
            return 1.0
        return max(0.0, 1.0 - ((capability_risk - task_risk) * 0.35))
