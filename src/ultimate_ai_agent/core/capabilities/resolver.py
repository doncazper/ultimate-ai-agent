from __future__ import annotations

from collections.abc import Iterable

from ultimate_ai_agent.core.capabilities.models import CapabilitySpec
from ultimate_ai_agent.core.capabilities.policy import policy_denial_reasons


def resolve_capabilities(
    specs: Iterable[CapabilitySpec],
    *,
    agent_name: str,
    user_scopes: set[str],
    query: str | None = None,
    tags: set[str] | None = None,
    max_tools: int = 20,
) -> list[CapabilitySpec]:
    requested_tags = tags or set()
    scored: list[tuple[int, str, CapabilitySpec]] = []
    for spec in specs:
        if policy_denial_reasons(spec, agent_name, user_scopes):
            continue
        if requested_tags and not requested_tags.issubset(spec.tags):
            continue
        scored.append((_score(spec, query), spec.name, spec))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [spec for _, _, spec in scored[:max_tools]]


def _score(spec: CapabilitySpec, query: str | None) -> int:
    if not query:
        return 0
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return 0
    score = 0
    fields = {
        "name": spec.name.lower(),
        "title": spec.title.lower(),
        "description": spec.description.lower(),
        "tags": " ".join(sorted(tag.lower() for tag in spec.tags)),
    }
    for term in terms:
        if term == fields["name"]:
            score += 30
        if term in fields["name"]:
            score += 12
        if term in fields["title"]:
            score += 8
        if term in fields["tags"]:
            score += 6
        if term in fields["description"]:
            score += 3
    return score
