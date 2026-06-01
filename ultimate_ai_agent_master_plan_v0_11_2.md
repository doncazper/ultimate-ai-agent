# Ultimate AI Agent Master Plan v0.11.2

Status: Active project baseline after the M7.5 API boundary stabilization patch.

## v0.11.2 change log

v0.11.2 is a patch release for M7.5. It does not start M8 and does not change the architecture.

v0.11.2 adds or updates:

```text
AGENTS.md
src/ultimate_ai_agent/api/contracts.py
src/ultimate_ai_agent/api/manifest.py
src/ultimate_ai_agent/api/openapi.py
src/ultimate_ai_agent/api/app.py
scripts/export_openapi.py
scripts/verify_openapi_contract.py
scripts/verify_all.py
scripts/run_foundation_gate.py
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/standards/agents_md_support.md
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
```

## Rule

The API boundary publishes metadata, validates typed contracts, previews deterministic decisions, and exposes Foundation Gate status. OpenAPI is the public contract; `/api/manifest` is the route inventory contract.

The implementation does not call models, providers, runtime servers, billing APIs, tokenizer APIs, web/network resources, external tools, browser automation, SDK/A2A runtimes, production databases, pgvector, embeddings, production truth connectors, runtime agent config, or production secret stores.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
