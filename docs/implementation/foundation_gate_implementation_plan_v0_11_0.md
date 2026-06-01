# Foundation Gate Implementation Plan v0.11.0

Status: Implemented for M7.

## Scope

M7 adds Model Router and Cost/Resource Governor policy infrastructure after the Foundation Gate. It is contracts, validation, deterministic decisions, budget checks, and non-executing previews only.

## Implemented

```text
src/ultimate_ai_agent/core/model_router/enums.py
src/ultimate_ai_agent/core/model_router/profiles.py
src/ultimate_ai_agent/core/model_router/policies.py
src/ultimate_ai_agent/core/model_router/requests.py
src/ultimate_ai_agent/core/model_router/decisions.py
src/ultimate_ai_agent/core/model_router/router.py
src/ultimate_ai_agent/core/model_router/validation.py
src/ultimate_ai_agent/core/costs/enums.py
src/ultimate_ai_agent/core/costs/budgets.py
src/ultimate_ai_agent/core/costs/estimates.py
src/ultimate_ai_agent/core/costs/decisions.py
src/ultimate_ai_agent/core/costs/governor.py
src/ultimate_ai_agent/core/costs/validation.py
```

## Validation

The Foundation Gate checks M1-M7 file presence, blocked-module absence, forbidden runtime integration absence, shell/subprocess absence in runtime source, broad filesystem scanning absence, secret hygiene, Tool Broker blocks, truth/evidence contracts, memory/file contracts, M5 shadow replay, M7 model-router decision-only behavior, and M7 cost-governor over-budget blocking.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

M7 does not implement scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, real providers, models, web calls, external actions, browser automation, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, tokenizer APIs, billing APIs, or high-autonomy execution.
