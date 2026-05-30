# Foundation Gate Implementation Plan v0.5.4

Status: Active implementation plan after Runtime Hygiene Micro-Foundation.

## Active stack

```text
Python Agent Core
FastAPI API boundary
Pydantic models/validators
Postgres + pgvector for memory retrieval later
Alembic migrations later
pytest tests
Docker Compose local services
OpenWebUI optional shell only
TypeScript Control Center later
```

## M0 — Repository, Canonical Foundation, and Stack Skeleton

Build validation and stack scaffolding only:

```text
pyproject.toml
Python package skeleton
FastAPI health/version/API boundary placeholders
validation scripts
prompt registry validation
schema validation
.gitignore and .env.example
minimal CI
```

Do not build real memory, tools, scanners, providers, model calls, code execution, or self-improvement.

## M0.5 — Runtime Hygiene Primitives

Implement shared models/schemas/helpers for:

```text
ResultEnvelope
ErrorEnvelope
IdempotencyPolicy
ActorContext
TemporalContext
DataClassification
RedactionPolicy
CapabilityFlag
Service boundary interfaces
```

These primitives may be implemented as Pydantic models and tested locally. They should not require a database.

## M1 — Kernel Contracts, v0/provisional

Build provisional Execution Contract, Context Pack, verification contract references, and schema validation. M1 contracts should reference runtime hygiene primitives but remain provisional until the Minimum Lovable Kernel exercises them.

## M2 — Event Ledger and Deterministic Run State

Build append-only event records, event-level cost attribution, run-state transitions, receipts, trace IDs, actor context, temporal context, classification metadata, and replay fixtures.

## M3 — Consent Ledger + Tool Broker

Build permission checks, autonomy level enforcement, standing approval rules, tool validation, idempotency enforcement for mutable actions, and rollback metadata.

## M3.5 — Secret Broker + Provider Registry

Build credential references, provider manifests, normalized result envelopes, redaction tests, and free-first provider resolution. Do not build real paid/provider integrations yet.

## M4 — Memory Service + File Manager

Build source-linked memory, pgvector/full-text retrieval design, file diffs, atomic writes, rollback, and canonical precedence.

## M5 — Minimum Lovable Kernel

Implement the first real end-to-end file mutation through the kernel.

## M6 — Contract Tests, Shadow Replay, Foundation Gate

Run all foundation evals, replay the Minimum Lovable Kernel trace, verify rollback, and decide controlled expansion.

## Gate blockers

```text
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
provider-specific credentialed integrations
external high-autonomy execution
```
