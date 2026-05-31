# Foundation Gate Implementation Plan v0.7.1

Status: M0, M0.5, M1, M2, M2.5, M3, and M3.5 completed as contract-only foundation work. Ready for the next foundation milestone after review.

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

## Completed through v0.7.1

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M0.5 — Runtime Hygiene Primitives
M1 — Kernel Contracts: Execution Contract + Context Pack
M2 — Event Ledger, Deterministic Run State, Receipts, and Observability Mapping
M2.5 — World State, Context Budget, Local Runtime, and SDK/A2A Boundaries
M3 — Consent Ledger + Tool Broker
M3 hardening — stricter approval, idempotency, firewall, wildcard, and boundary rules
M3.5 — Secret Broker + Provider Registry contracts
```

## M3.5 Scope

M3.5 adds credential references, opaque secret handles, redacted secret access decisions, provider manifests, deterministic provider resolution, provider result envelopes, and weather/news normalization contracts.

## M3.5 Non-Goals

```text
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
real memory storage
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
