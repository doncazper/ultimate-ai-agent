# Memory Search / Filter Route

Goal: add a read-only search endpoint over reviewed safe summaries and safe refs.

Scope:
- Route: `GET /control-center/memory/search`.
- Search only safe summaries and refs already approved for read models.
- Filters: kind, source, project refs, person refs, org refs, deal refs,
  review state, quality state, stale state, and conflict state.

Boundaries:
- No semantic search, vector DB, embeddings, model/provider calls, raw-content
  inspection, or connector reads.

Verification:
- API route tests for each filter.
- Raw-content denial tests for unsafe query/filter refs.
- OpenAPI/API manifest checks.
