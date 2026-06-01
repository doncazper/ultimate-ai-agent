# Foundation Gate Implementation Plan v0.10.1

Status: Implemented for M6.1 hardening.

## Scope

M6.1 hardens the M6 Foundation Gate baseline. It is release hygiene, CI polish, warning cleanup, and verifier/report ergonomics only.

## Implemented

```text
.github/workflows/ci.yml
src/ultimate_ai_agent/core/time.py
scripts/verify_all.py
scripts/verify_current_baseline.py
scripts/run_foundation_gate.py
tests/test_foundation_gate_report.py
tests/test_foundation_gate_secret_hygiene.py
tests/test_run_foundation_gate_script.py
```

## Validation

The Foundation Gate still checks version consistency, release docs, M1-M6 file presence, blocked-module absence, forbidden runtime integration absence, shell/subprocess absence in runtime source, broad filesystem scanning absence, secret hygiene, Tool Broker blocks for MCP/A2A/SDK/Skill categories, truth/evidence contracts, memory/file contracts, and M5 shadow replay.

M6.1 also verifies that core runtime code no longer uses deprecated `datetime.utcnow()` call sites and that gate report ordering and runner output remain stable.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

## Non-goals

M6.1 does not implement scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, real providers, models, web calls, external actions, browser automation, SDK/A2A runtime delegation, production databases, pgvector, embeddings, production secrets, production truth connectors, or high-autonomy execution.
