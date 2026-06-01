# Ultimate AI Agent Master Plan v0.11.1

Status: Active project baseline after the M7 policy-correctness patch.

## v0.11.1 change log

v0.11.1 is a patch release for M7. It does not start M8 and does not change the architecture.

v0.11.1 hardened:

```text
src/ultimate_ai_agent/core/model_router/router.py
src/ultimate_ai_agent/core/model_router/policies.py
src/ultimate_ai_agent/core/costs/governor.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
tests/test_model_router_privacy.py
tests/test_model_router_context_budget.py
tests/test_model_router_decisions.py
tests/test_cost_governor.py
tests/test_m7_gate_integration.py
```

Updated:

```text
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
README_IMPORT_v0_11_1.md
docs/release_notes/v0_11_1.md
docs/implementation/foundation_gate_implementation_plan_v0_11_1.md
```

## Rule

M7 selects route metadata, not model outputs. Model profiles are capability and policy descriptors. Model route previews are deterministic decisions. Cost/resource governance uses local estimates and configured budgets. Credentials are referenced by handle only and are never resolved into raw secrets. Approval refs are not authority unless they match the explicit local/test validation policy for this foundation patch.

The implementation does not call models, providers, runtime servers, billing APIs, tokenizer APIs, web/network resources, external tools, browser automation, SDK/A2A runtimes, production databases, pgvector, embeddings, production truth connectors, or production secret stores.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
