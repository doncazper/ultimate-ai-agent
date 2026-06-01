# Foundation Gate Implementation Plan v0.11.2

Status: Implemented for the M7.5 API boundary stabilization patch.

## Scope

v0.11.2 stabilizes the API boundary with typed metadata, deterministic OpenAPI route contracts, workspace guidance, and gate coverage. It is still contracts, validation, deterministic decisions, metadata export, and verification only.

## Implemented

```text
AGENTS.md
src/ultimate_ai_agent/api/contracts.py
src/ultimate_ai_agent/api/manifest.py
src/ultimate_ai_agent/api/openapi.py
src/ultimate_ai_agent/api/app.py
scripts/export_openapi.py
scripts/verify_openapi_contract.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
```

## Validation

The Foundation Gate checks M1-M7 file presence, blocked-module absence, forbidden runtime integration absence, shell/subprocess absence in runtime source, broad filesystem scanning absence, secret hygiene, Tool Broker blocks, truth/evidence contracts, memory/file contracts, M5 shadow replay, M7 model-router and cost-governor policy semantics, and M7.5 API boundary hygiene.

M7.5 criteria cover API manifest presence, OpenAPI contract validity, unique operation IDs, forbidden runtime route absence, AGENTS.md guidance, and absence of runtime agent config loading.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

v0.11.2 does not implement scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, real providers, models, web calls, tokenizers, billing APIs, network calls, external actions, browser automation, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, runtime agent config loading, or high-autonomy execution.
