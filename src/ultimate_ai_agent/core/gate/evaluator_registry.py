from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluatorRegistryEntry:
    name: str
    module: str
    status: str
    responsibility: str


EVALUATOR_REGISTRY: tuple[EvaluatorRegistryEntry, ...] = (
    EvaluatorRegistryEntry(
        name="legacy_foundation_gate_evaluator",
        module="ultimate_ai_agent.core.gate.evaluators",
        status="legacy_compatibility_facade",
        responsibility="Current public evaluator entrypoints and historical milestone checks.",
    ),
    EvaluatorRegistryEntry(
        name="route_contract_evaluators",
        module="ultimate_ai_agent.core.gate.evaluator_modules.route_contracts",
        status="extracted_route_boundary",
        responsibility="OpenAPI route counts, operation IDs, and side-effect class checks.",
    ),
    EvaluatorRegistryEntry(
        name="security_redaction_evaluators",
        module="ultimate_ai_agent.core.gate.evaluator_modules.security_redaction",
        status="planned_split",
        responsibility="Secret hygiene, raw-content denial, and evidence redaction checks.",
    ),
    EvaluatorRegistryEntry(
        name="frontend_product_evaluators",
        module="ultimate_ai_agent.core.gate.evaluator_modules.frontend_product",
        status="planned_split",
        responsibility="Control Center safety, product-language, and visual proof checks.",
    ),
    EvaluatorRegistryEntry(
        name="storage_backup_evaluators",
        module="ultimate_ai_agent.core.gate.evaluator_modules.storage_backup",
        status="planned_split",
        responsibility="Storage repository, backup manifest, and append-only proof checks.",
    ),
)


def evaluator_registry() -> tuple[EvaluatorRegistryEntry, ...]:
    return EVALUATOR_REGISTRY
