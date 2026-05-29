# Import Checklist v0.5.1

## First commit

```text
[ ] Create repository
[ ] Add README.md
[ ] Add docs/ directory from bundle
[ ] Add master plan v0.5.1
[ ] Add schemas
[ ] Add prompts
[ ] Add ADRs
[ ] Add Kanban and roadmap docs
[ ] Add issue seed list
[ ] Commit as: docs: import ultimate ai agent foundation v0.5.1
```

## Second commit

```text
[ ] Add /src directory
[ ] Add /tests directory
[ ] Add /scripts directory
[ ] Add package manager config
[ ] Add schema validation script
[ ] Add prompt registry validation script
[ ] Add .env.example
[ ] Add CI skeleton
[ ] Commit as: chore: add foundation validation skeleton
```

## Validation checks

```text
[ ] JSON files parse
[ ] Prompt registry paths exist
[ ] Schema files are discoverable
[ ] README points to active master plan
[ ] Foundation-first policy is visible
[ ] Advanced modules are marked blocked/parking lot
```

## Import warning

Do not import this bundle as generated application code. Import it as canonical project material.

## v0.5.2 Stack Import Addendum

```text
Create /services/agent-core.
Create /apps/openwebui as optional config shell.
Create /apps/control-center placeholder only if desired.
Create /packages/schemas for shared contracts.
Create /infra/compose for Docker Compose.
Do not wire OpenWebUI directly to database, files, memory, or tools.
```
