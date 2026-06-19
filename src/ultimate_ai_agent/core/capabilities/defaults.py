from __future__ import annotations

from functools import lru_cache

from ultimate_ai_agent.core.capabilities.models import CapabilityPolicy, CapabilitySpec, RiskLevel
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry


BLOCKED_FOUNDATION_CAPABILITY_NAMES = (
    "reddit_scanner",
    "news_scanner",
    "weather_provider_v1",
    "email_scanner",
    "message_scanner",
    "calendar_scanner",
    "companion_proactivity",
    "skill_factory",
    "self_improving_code",
    "autopilot_workflows",
    "external_high_autonomy_execution",
    "credentialed_provider_integrations",
    "truth_sensitive_scanners",
)


def foundation_blocked_capability_specs() -> list[CapabilitySpec]:
    return [
        CapabilitySpec(
            id=f"capability:{name}:foundation-gate-blocked",
            name=name,
            version="1.0.0",
            title=name.replace("_", " ").title(),
            description="Foundation Gate blocked capability metadata record.",
            tags={"foundation_gate", "blocked"},
            input_schema={"type": "object", "additionalProperties": False},
            output_schema=None,
            policy=CapabilityPolicy(risk=RiskLevel.READ_ONLY, requires_approval=True),
            source="internal",
            metadata={
                "foundation_gate_blocked": True,
                "enabled": False,
                "execution_authority": False,
            },
        )
        for name in BLOCKED_FOUNDATION_CAPABILITY_NAMES
    ]


@lru_cache(maxsize=1)
def default_foundation_capability_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_many(foundation_blocked_capability_specs())
    return registry


def capability_is_foundation_blocked(name: str, registry: CapabilityRegistry | None = None) -> bool:
    lowered = name.lower()
    if any(blocked in lowered for blocked in BLOCKED_FOUNDATION_CAPABILITY_NAMES):
        return True
    registries = [default_foundation_capability_registry()]
    if registry is not None:
        registries.append(registry)
    for active_registry in registries:
        for spec in active_registry.list():
            if spec.metadata.get("foundation_gate_blocked") and spec.name.lower() in lowered:
                return True
    return False
