# Foundation Gate Implementation Plan v0.5.7

Status: Active implementation plan after Runtime Hygiene, Local Runtime, Context Survival, SDK/A2A boundary, Truth Governance, and Observability Standards Mapping additions.

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

## M2 — Event Ledger, Deterministic Run State, and Observability Standards Mapping

Build append-only event records, event-level cost attribution, run-state transitions, receipts, trace IDs, actor context, temporal context, classification metadata, replay fixtures, and standards-mapping metadata. Event records must be mappable to OpenTelemetry GenAI spans/events/metrics and W3C Trace Context. CloudEvents and AsyncAPI compatibility should be documented for future export/event-stream use, but not implemented as runtime dependencies in M2.

## M2.5 — World State, Context Budget, Local Runtime, and SDK Adapter Boundaries

Implement or validate schemas/docs for:

```text
Structured World State
Context Budget Manager
Token accounting and calibration
Tool-result retention and strategic trimming
Prompt/tool prefix cache policy
Local runtime manifests and health checks
Local resource budgets
Privacy routing policy
Agent SDK adapter manifests
A2A minimal Agent Card schema
```

M2.5 may implement Pydantic models for these contracts but must not call real model runtimes or external agents yet.

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
real Agent SDK/A2A runtime delegation
external high-autonomy execution
```


## v0.5.7 Foundation Gate addition: M4.5 Truth Source Router and Evidence Governance

Before the Minimum Lovable Kernel can claim verified factual output, the system must prove:

```text
Truth Source Manifest schema validates.
Grounding Policy schema validates.
Evidence Manifest and ClaimEvidence schemas validate.
Source Conflict Report schema validates.
Retrieval Log Entry schema validates.
Execution Contract supports grounding_mode.
Hard/live facts route to APIs/databases/provider adapters.
Approved-document retrieval uses hybrid search and reranking.
Unsupported claims are refused or labeled according to policy.
High-stakes truth routes to human review.
```


## v0.5.7 Foundation Gate addition: Observability Standards Mapping

Before Foundation Gate, the system must prove:

```text
ObservabilityMapping schema validates.
EventExportProfile schema validates.
M2 Event Ledger records include trace-compatible IDs.
OpenTelemetry GenAI mapping is documented for agent/model/tool/error/cost events.
W3C Trace Context propagation is documented for API/tool/worker/provider/MCP/SDK/A2A boundaries.
CloudEvents export profile is documented for future event-stream export.
AsyncAPI is documented as the future contract format for message-driven APIs.
Redaction rules apply before any telemetry export.
```
