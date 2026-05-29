# Open Questions Before Coding v0.5.1

These questions do not block M0-M2 if defaults are accepted, but they should be answered before deeper implementation.

## Stack choices

```text
1. Python-first, TypeScript-first, or polyglot monorepo?
2. FastAPI, plain Python package, or another service framework?
3. Pydantic-first models or generated models from JSON Schema?
4. Which migration tool: Alembic, Prisma, Drizzle, or other?
5. Which model providers are supported first?
6. Do we require local/private mode in the first MVP?
```

Recommended default: Python + Pydantic + pytest + Postgres + Alembic + GitHub Actions.

## Product choices

```text
1. Is the first version personal-only or multi-user from day one?
2. Is auth needed before Foundation Gate, or can it be stubbed locally?
3. Should File Manager write to local filesystem first or Git-backed workspace first?
4. Should Event Ledger start as Postgres or local JSONL for development?
5. Is the first UI a CLI, simple web dashboard, or none?
```

Recommended default: single-user local dev, local filesystem, Postgres event tables, CLI/dev scripts first, UI later.

## Safety choices

```text
1. Which actions always require human approval?
2. What data is forbidden from cloud model routing?
3. What is the default retention policy for traces?
4. What is the default cost budget for dev mode?
```

Recommended default: strict approvals, no real external actions, no real personal data ingestion until consent system is implemented.
