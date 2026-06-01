# Foundation Gate Implementation Plan v0.8.0

Status: M0, M0.5, M1, M2, M2.5, M3, M3.5, and M4 completed as foundation work. Ready for M4.5 Truth Source Router after review.

## Active stack

```text
Python Agent Core
FastAPI API boundary
Pydantic models/validators
pytest tests
ruff checks
OpenWebUI optional shell only
TypeScript Control Center later
```

## Completed through v0.8.0

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M0.5 — Runtime Hygiene Primitives
M1 — Kernel Contracts: Execution Contract + Context Pack
M2 — Event Ledger, Deterministic Run State, Receipts, and Observability Mapping
M2.5 — World State, Context Budget, Local Runtime, and SDK/A2A Boundaries
M3 — Consent Ledger + Tool Broker
M3 hardening — stricter approval, idempotency, firewall, wildcard, and boundary rules
M3.5 — Secret Broker + Provider Registry contracts
M4 — Memory Service + File Manager contracts and local/dev stores
```

## M4 Scope

M4 adds memory contracts, source references, local/dev in-memory memory storage, deterministic scoped retrieval, supersession/correction/deletion metadata, redaction, safe file refs, local/dev workspace file previews, write proposals, deterministic diffs, atomic writes, snapshots, rollback metadata, and validation/preview API routes.

## M4 Non-Goals

```text
M4.5 Truth Source Router
M5 Minimum Lovable Kernel
production memory database
pgvector migrations
embedding execution
model-generated memory extraction
production file persistence
broad filesystem scanning
shell execution
real provider calls
paid provider integrations
network calls
production secret persistence
OAuth flows
API clients
weather/news fetchers
model calls
scanners
real tool execution
external SDK/A2A delegation
```

## Gate Blockers Remain

```text
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
provider-specific credentialed integrations
real Agent SDK/A2A delegation
skill installation/loading/execution
external high-autonomy execution
```

## Skill Package Security Rule

All skills are untrusted packages by default. A skill may not be installed, loaded, executed, granted credentials, exposed to tools, or used in autonomous workflows until it has a manifest, declared permissions, source/provenance metadata, applicable static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.
