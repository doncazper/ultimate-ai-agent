# Foundation Gate Implementation Plan v0.7.0

Status: M0, M0.5, M1, M2, M2.5, and M3 completed. Ready for M3.5 (Secret Broker + Provider Registry) build.

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

## M0 — Repository, Canonical Foundation, and Stack Skeleton (Completed)

Build validation and stack scaffolding only:

```text
pyproject.toml (Done)
Python package skeleton (Done)
FastAPI health/version/API boundary placeholders (Done)
validation scripts (Done)
prompt registry validation (Done)
schema validation (Done)
.gitignore and .env.example (Done)
minimal CI (Pending)
```

## M0.5 — Runtime Hygiene Primitives (Completed)

Implemented shared models/schemas/helpers for:

```text
ResultEnvelope (Done)
ErrorEnvelope (Done)
IdempotencyPolicy (Done)
ActorContext (Done)
TemporalContext (Done)
DataClassification (Done)
RedactionPolicy (Done)
CapabilityFlag (Done)
```

These primitives are implemented as Pydantic v2 models and tested locally.

## M1 — Kernel Contracts, v0/provisional (Completed)

Build provisional Execution Contract, Context Pack, verification contract references, and schema validation. M1 contracts reference runtime hygiene primitives and are fully validated and tested.

## M2 — Event Ledger, Deterministic Run State, and Observability Standards Mapping (Completed)

Build append-only event records, event-level cost attribution, run-state transitions, receipts, trace IDs, actor context, temporal context, classification metadata, replay fixtures, and standards-mapping metadata. Event records must be mappable to OpenTelemetry GenAI spans/events/metrics and W3C Trace Context. CloudEvents and AsyncAPI compatibility should be documented for future export/event-stream use, but not implemented as runtime dependencies in M2.

## M2.5 — World State, Context Budget, Local Runtime, and SDK Adapter Boundaries (Completed)

Implement or validate schemas/docs for structured world state, context budget manager with token accounting and output trimming, local runtime manifests with capability profiles, and SDK/A2A validation boundary constraints.

## M3 — Consent Ledger + Tool Broker (Completed)

Build permission checks, autonomy level enforcement, standing approval rules, tool validation, capability firewall policies, Foundation Gate blocks, dry-run decision planners, and validation API routes.

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
real Agent SDK/A2A delegation
skill installation/loading/execution
external high-autonomy execution
```

## v0.7.0 Foundation Gate status: Consent & Tool Governance Contracts

Before Tool Broker execution or Secret Broker storage can move beyond design/spec work, the system must prove Consent & Tool governance rules:

```text
Consent Ledger models validate.
Tool Registry handles mock manifests.
Capability Firewall policies evaluate correctly.
Foundation Gate strictly blocks Skill, MCP, A2A, and SDK categories.
Credential references are denied until M3.5 Secret Broker exists.
High-risk tools and mutating actions require human approval.
Dry-Run returns DryRunPlan with zero side effects.
```

## v0.7.0 Foundation Gate addition: Skill Package Security Rule

Before Skill Factory, reusable skill loading, imported skill packages, or executable skill adapters can move beyond design/spec work, the system must prove the Skill Package Security Rule. All skills are untrusted packages by default. A skill may not be installed, loaded, executed, granted credentials, exposed to tools, or used in autonomous workflows until it has:

```text
1. a manifest
2. declared permissions
3. source/provenance metadata
4. static review where applicable
5. sandbox test execution
6. Tool Broker permission mapping
7. Event Ledger logging
8. version pinning
9. revocation/disable support
10. human approval for high-risk capabilities
```

This requirement is documentation-only at v0.7.0 and should be implemented later when the Skill Factory milestone begins. Until then, all executable skill loading remains blocked by the Foundation Gate.
