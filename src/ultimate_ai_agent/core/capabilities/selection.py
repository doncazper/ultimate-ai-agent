from __future__ import annotations

from typing import Any, Protocol

from ultimate_ai_agent.core.capabilities.models import (
    CapabilityCatalogEntry,
    CapabilitySearchFilters,
    CapabilitySelection,
)
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry


class LLMSelector(Protocol):
    def select(
        self,
        query: str,
        candidates: list[CapabilityCatalogEntry],
        context: dict[str, Any],
    ) -> CapabilitySelection:
        ...


class DeterministicSelector:
    def select(
        self,
        query: str,
        candidates: list[CapabilityCatalogEntry],
        context: dict[str, Any] | None = None,
    ) -> CapabilitySelection:
        selected = candidates[:1]
        rejected = candidates[1:]
        return CapabilitySelection(
            query=query,
            selected_capability_ids=[entry.id for entry in selected],
            rejected_capability_ids=[entry.id for entry in rejected],
            candidate_scores={entry.id: entry.score for entry in candidates},
            selector_kind="deterministic",
            reason_codes=["DETERMINISTIC_TOP_SCORE_SELECTED"] if selected else ["NO_CAPABILITY_SELECTED"],
            confidence=min(max(selected[0].score / 100, 0), 1) if selected else 0,
            requires_manifest_ids=[entry.id for entry in selected],
        )


def select_capabilities(
    query: str,
    registry: CapabilityRegistry,
    context: dict[str, Any] | None = None,
    filters: CapabilitySearchFilters | None = None,
    *,
    llm_selector: LLMSelector | None = None,
    llm_candidate_limit: int = 5,
) -> CapabilitySelection:
    candidates = registry.search(query, context or {}, filters)
    if llm_selector is None or not candidates:
        return DeterministicSelector().select(query, candidates, context or {})
    top_candidates = candidates[:llm_candidate_limit]
    selection = llm_selector.select(query, top_candidates, context or {})
    return CapabilitySelection.model_validate(selection.model_dump())
