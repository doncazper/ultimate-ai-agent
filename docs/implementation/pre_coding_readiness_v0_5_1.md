# Pre-Coding Readiness v0.5.1

Status: Ready for repo import; not yet runnable code.

## Readiness verdict

```text
Canonical docs: ready for import
ADRs: ready for import
Schemas: ready for import; JSON parses cleanly
Prompts: added in v0.5.1; ready as initial baseline
Evals: ready as planning/eval specs, not executable yet
Kanban/roadmap: ready as planning files
Implementation plan: ready for M0-M2
Application code: not created yet
Database migrations: not created yet
CI workflow: not created yet
```

## What to do in the next 30 hours

Use the waiting period to prepare the repo and remove ambiguity.

### 1. Decide implementation defaults

Recommended defaults unless changed later:

```text
Backend language: Python first for agent runtime and schemas
API: FastAPI or minimal service layer after core models
Validation: Pydantic models generated/handwritten from JSON schemas
Database: Postgres
Local DB: Docker Compose Postgres
Vector: pgvector later, not needed for M0-M2
Tests: pytest
Schema validation: jsonschema or check-jsonschema
CI: GitHub Actions
Frontend: defer until User Control Center shell
```

### 2. Prepare repository

```text
Create repo
Import v0.5.1 bundle
Create /src, /tests, /scripts
Add .gitignore
Add .env.example
Add pyproject.toml or package config
Add schema validation command
Add prompt registry validation command
Add first CI workflow
```

### 3. Start only M0-M2

```text
M0: repo + docs + schema/prompt validation
M1: Execution Contract + Context Pack models and validators
M2: Event Ledger append-only store and receipt generator
```

Do not build scanners, companion proactivity, Skill Factory, self-improving code, or external integrations yet.

## Before writing code, confirm these choices

```text
Primary programming language
Repo hosting location
License/private status
Model providers to support first
Whether local-only/private mode is required in MVP
Database migration tool
CI provider
```

If undecided, proceed with Python + Postgres + pytest + GitHub Actions as the default foundation stack.
