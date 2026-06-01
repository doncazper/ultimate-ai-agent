# Foundation Gate Implementation Plan v0.10.0

Status: Implemented for M6.

## Scope

M6 adds Contract Tests, Shadow Replay, and Foundation Gate evaluation. It is verification, replay, audit, and release gating only.

## Implemented

```text
src/ultimate_ai_agent/core/gate/enums.py
src/ultimate_ai_agent/core/gate/criteria.py
src/ultimate_ai_agent/core/gate/reports.py
src/ultimate_ai_agent/core/gate/evaluators.py
src/ultimate_ai_agent/core/gate/shadow_replay.py
src/ultimate_ai_agent/core/gate/validation.py
scripts/run_foundation_gate.py
reports/foundation_gate/sample_foundation_gate_report.json
reports/foundation_gate/sample_foundation_gate_report.md
```

## Validation

The Foundation Gate checks version consistency, release docs, M1-M6 file presence, blocked-module absence, forbidden runtime integration absence, shell/subprocess absence in runtime source, broad filesystem scanning absence, secret hygiene, Tool Broker blocks for MCP/A2A/SDK/Skill categories, truth/evidence contracts, memory/file contracts, and M5 shadow replay.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

M6 does not implement scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, real providers, models, web calls, external actions, browser automation, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, or high-autonomy execution.
