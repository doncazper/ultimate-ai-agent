# 09 — Roadmap v0.5.2

Status: Active foundation-first roadmap with scalable stack and UI strategy incorporated.

## North Star

Build a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, and scalable.

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

Foundation Gate implementation.

## Now: M0–M6 Foundation

```text
M0 — Repository, Canonical Foundation, and Stack Skeleton
M1 — Kernel Contracts: Execution Contract + Context Pack
M2 — Event Ledger / Observability
M3 — Consent Ledger + Tool Broker
M4 — Memory Service + File Manager
M5 — Orchestrator Minimal Vertical Slice
M6 — Contract Tests, Shadow Replay, Foundation Gate Decision
```

## M0 stack deliverables

```text
Repo layout for /services, /apps, /packages, /docs, /tests, /scripts, /infra
Python Agent Core skeleton
schema validation command
prompt registry validation command
basic FastAPI health/API boundary placeholder
Docker Compose Postgres placeholder or working local service
OpenWebUI config folder, optional chat shell only
TypeScript Control Center placeholder, optional until foundation API stabilizes
API boundary and bypass-prevention contract tests drafted
```

## Next: M7–M10 Controlled expansion

Only after Foundation Gate passes:

```text
M7 — Web Research V1 and Source Credibility
M8 — Code Workspace V1 with sandboxed execution
M9 — Basic Scanner Framework, read-only/digest-only
M10 — Proactive Intelligence V1, digest-first, no interrupt alerts until tuned
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

Do not build scanners, companion proactivity, Skill Factory, self-improving code, or autopilot workflows before the kernel, memory/files, event ledger, permission model, tool broker, model router, cost governor, rollback primitives, API boundary, and contract tests work.
