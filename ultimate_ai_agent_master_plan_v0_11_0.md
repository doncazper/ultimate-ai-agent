# Ultimate AI Agent Master Plan v0.11.0

Status: Active project baseline after Milestone M7 (Model Router and Cost/Resource Governor policy foundation).

## v0.11.0 change log

v0.11.0 implements M7 as the first controlled post-Foundation-Gate expansion. It remains policy/decision infrastructure only.

M7 added:

```text
src/ultimate_ai_agent/core/model_router/
src/ultimate_ai_agent/core/costs/
tests/test_model_profiles.py
tests/test_model_routing_policy.py
tests/test_model_router_decisions.py
tests/test_model_router_privacy.py
tests/test_model_router_context_budget.py
tests/test_model_router_no_execution.py
tests/test_cost_budgets.py
tests/test_cost_governor.py
tests/test_resource_governor.py
tests/test_m7_api_routes.py
tests/test_m7_gate_integration.py
```

Updated:

```text
src/ultimate_ai_agent/api/app.py
src/ultimate_ai_agent/core/gate/
scripts/run_foundation_gate.py
scripts/verify_all.py
scripts/verify_current_baseline.py
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
```

## Rule

M7 selects route metadata, not model outputs. Model profiles are capability and policy descriptors. Model route previews are deterministic decisions. Cost/resource governance uses local estimates and configured budgets. Credentials are referenced by handle only and are never resolved into raw secrets.

The implementation does not call models, providers, runtime servers, billing APIs, tokenizer APIs, web/network resources, external tools, browser automation, SDK/A2A runtimes, production databases, pgvector, embeddings, production truth connectors, or production secret stores.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
