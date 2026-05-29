# Pre-Coding Readiness v0.5.2

Status: Ready for repo import; not yet runnable code.

## Readiness verdict

```text
Canonical docs: ready for import
ADRs: ready for import
Schemas: ready for import; JSON parses cleanly
Prompts: ready as initial baseline
Evals: ready as planning/eval specs, not executable yet
Kanban/roadmap: ready as planning files
Implementation plan: ready for M0-M2
Stack decision: accepted
Application code: not created yet
Database migrations: not created yet
Production CI: not created yet
```

## Implementation defaults

```text
Agent Core: Python 3.12+
API boundary: FastAPI
Validation: Pydantic
Database: Postgres
Migrations: Alembic
Tests: pytest
Local dev: Docker Compose
Frontend shell: OpenWebUI first, optional
Custom UI: TypeScript/Next.js Control Center later
TypeScript package manager: pnpm later
Vector search: pgvector later, not needed for M0-M2
```

## Next 30 hours checklist

```text
Create repository.
Import v0.5.2 bundle.
Create branch: foundation/m0-import.
Review README_IMPORT_v0_5_2.md.
Create /services/agent-core skeleton.
Create /scripts validation commands.
Create /tests/contract skeleton.
Create .env.example.
Create Docker Compose scaffold.
Optionally create /apps/openwebui config folder.
Do not build advanced modules.
```

## Start only M0-M2

```text
M0: repo + docs + schema/prompt validation + stack skeleton
M1: Execution Contract + Context Pack models and validators
M2: Event Ledger append-only store and receipt generator
```

## Decisions now locked unless changed by ADR

```text
Python Agent Core
TypeScript Control Center later
OpenWebUI optional chat shell only
Postgres canonical database
Stable API Boundary
Foundation-first build order
```
