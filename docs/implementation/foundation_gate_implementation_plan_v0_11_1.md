# Foundation Gate Implementation Plan v0.11.1

Status: Implemented for the M7 policy-correctness patch.

## Scope

v0.11.1 hardens the existing M7 Model Router and Cost/Resource Governor policy infrastructure. It is still contracts, validation, deterministic decisions, budget checks, and non-executing previews only.

## Implemented

```text
src/ultimate_ai_agent/core/model_router/router.py
src/ultimate_ai_agent/core/model_router/policies.py
src/ultimate_ai_agent/core/costs/governor.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/evaluators.py
```

## Validation

The Foundation Gate checks M1-M7 file presence, blocked-module absence, forbidden runtime integration absence, shell/subprocess absence in runtime source, broad filesystem scanning absence, secret hygiene, Tool Broker blocks, truth/evidence contracts, memory/file contracts, M5 shadow replay, M7 model-router decision-only behavior, M7 hard-budget blocking, arbitrary approval-ref rejection, context-budget exhaustion blocking, soft-budget warning semantics, hard-budget denial semantics, and route-decision cost warning visibility.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

v0.11.1 does not implement scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, real providers, models, web calls, tokenizers, billing APIs, network calls, external actions, browser automation, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, or high-autonomy execution.
