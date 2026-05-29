# 09 — Roadmap v0.5.3

Status: Active foundation-first roadmap. This is the single roadmap source of truth.

## North Star

Build a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

## Stack baseline

```text
Python/FastAPI/Pydantic Agent Core
TypeScript Control Center later
OpenWebUI optional early chat shell
Postgres canonical database
Docker Compose local development
Stable Agent API Boundary
```

OpenWebUI is a window into the agent, not the agent brain.

## Current phase

Pre-coding foundation remediation and Minimum Lovable Kernel preparation.

## Minimum Lovable Kernel

Before committing to the full foundation build, prove one genuine end-to-end task:

```text
Create a local project artifact through the agent kernel.
Use Execution Contract + Context Pack.
Check Consent Ledger.
Route File Manager through Tool Broker.
Write an actual file.
Log event-level cost attribution.
Create rollback metadata.
Verify the artifact and receipt.
Write source-linked memory.
```

## Now: Foundation Gate sequence

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M1 — Kernel Contracts: Execution Contract + Context Pack, v0/provisional
M2 — Event Ledger, Deterministic Run State, and Receipts
M3 — Consent Ledger + Tool Broker
M3.5 — Secret Broker + Provider Registry + Normalized Provider Envelopes
M4 — Memory Service + File Manager
M5 — Minimum Lovable Kernel Vertical Slice
M6 — Contract Tests, Shadow Replay, Foundation Gate Decision
```

## M0 acceptance

```text
Repo layout exists.
Python Agent Core skeleton exists.
JSON/schema validation command exists.
Prompt registry validation command exists.
FastAPI health/API boundary placeholder exists.
Docker Compose Postgres scaffold exists.
OpenWebUI config is present only as optional shell.
Foundation-first rule is visible.
```

## M1 acceptance

```text
Execution Contract and Context Pack schemas/models validate.
Contracts are marked v0/provisional.
Advanced modules are rejected until Foundation Gate.
Verification contract references are supported.
```

## M2 acceptance

```text
Run/event records support append-only logging.
Event-level cost attribution exists.
Receipts can be generated without secrets.
Custom deterministic state machine is documented as initial durable-execution substrate.
```

## M3 acceptance

```text
Consent grants can be created, checked, expired, revoked, and audited.
Tool calls are schema-validated, consent-checked, risk-classified, logged, and rollback-aware.
Autonomy levels L0-L5 map to risk and approval requirements.
```

## M3.5 acceptance

```text
Secrets are referenced by ID, not value.
Secret Broker interface exists.
Provider Registry manifests validate.
Provider result envelopes normalize weather/news/provider responses.
No secret can enter chat, prompts, memory, logs, canonical files, or git.
```

## M4 acceptance

```text
Memory writes are source-linked, scoped, supersedable, and retrieval-aware.
Memory Retrieval V1 uses Postgres + pgvector + full-text + reranking design.
File writes use diffs/atomic operations and produce rollback metadata.
Canonical files outrank memory.
```

## M5 acceptance

```text
Minimum Lovable Kernel completes successfully.
One real file mutation is performed through Tool Broker and File Manager.
Event Ledger, rollback, QA receipt, and source-linked memory all work.
```

## M6 acceptance

```text
Contract tests pass.
Shadow replay can replay the Minimum Lovable Kernel trace.
OpenWebUI/API boundary bypass tests pass.
Foundation Gate review decides whether controlled expansion can begin.
```

## Controlled expansion after gate

Only after M6 passes:

```text
M7 — Web Research V1 and Source Credibility
M8 — Code Workspace V1 with sandboxed execution
M9 — Weather Provider V1 using free/no-key provider first
M10 — News Provider V1 with normalized events/articles
M11 — Basic Scanner Framework, read-only/digest-only
M12 — Proactive Intelligence V1, digest-first, no interrupt alerts until tuned
```

## Later

```text
Companion proactivity
Skill Factory
Self-improving coding framework
High-autonomy external execution
Autopilot workflows
Agent interoperability
Voice/mobile UX
```

## Non-negotiable sequencing rule

Do not build scanners, companion proactivity, Skill Factory, self-improving code, autopilot workflows, provider-specific integrations, or high-autonomy external execution before the kernel, memory/files, event ledger, permission model, Tool Broker, Model Router, Cost Governor, Secret Broker, Provider Registry, rollback primitives, API boundary, and contract tests work.
