# Foundation Gate Implementation Plan v0.5.3

Status: Active implementation plan after review remediation.

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

Same as v0.5.2, with `.gitignore`, validation scripts, and no advanced modules.

## M1 — Kernel Contracts, v0/provisional

Build provisional Execution Contract, Context Pack, verification contract references, and schema validation.

## M2 — Event Ledger and Deterministic Run State

Build append-only event records, event-level cost attribution, run-state transitions, receipts, and replay fixtures.

## M3 — Consent Ledger + Tool Broker

Build permission checks, autonomy level enforcement, standing approval rules, tool validation, and rollback metadata.

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
