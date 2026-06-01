# Foundation Gate Implementation Plan v0.9.0

Status: M0, M0.5, M1, M2, M2.5, M3, M3.5, M4, M4.5, and M5 completed as foundation work. Advanced modules remain blocked by the Foundation Gate.

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

## Completed through v0.9.0

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
M4.5 — Truth Source Router + Evidence Governance contracts
M5 — Minimum Lovable Kernel local/dev slice
```

## M5 Scope

M5 adds the smallest end-to-end kernel path that proves the foundation composes correctly. It can perform one controlled local/dev file mutation inside an explicit workspace root using the Execution Contract, Context Pack, Consent Ledger, Tool Broker, Event Ledger, World State, LocalFileManager proposal/diff/apply, optional source-linked Memory, receipt generation, and rollback support.

## M5 Non-Goals

```text
scanners
companion proactivity
Skill Factory
self-improving code
autopilot workflows
real provider integrations
web fetching
real model calls
embedding execution
pgvector migrations
production memory database
production truth connectors
external tools
browser automation
SDK/A2A runtime delegation
high-autonomy execution
OAuth flows
production secret persistence
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
production truth connectors
```

## Skill Package Security Rule

All skills are untrusted packages by default. A skill may not be installed, loaded, executed, granted credentials, exposed to tools, or used in autonomous workflows until it has a manifest, declared permissions, source/provenance metadata, applicable static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.
