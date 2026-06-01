# API Boundary

The v0.12.2 API boundary is metadata-first, validation-first, approval-aware for local/dev policy checks, and simulated-only for model runtime behavior. It publishes the current OpenAPI schema and `/api/manifest` route inventory without adding real model calls, provider calls, web fetching, browser automation, tokenizers, billing APIs, production auth, OAuth, or production persistence.

Use:

```bash
python scripts/export_openapi.py
python scripts/verify_openapi_contract.py
```

The export script writes JSON to stdout by default. Use `--output` only when an intentional artifact is needed.

M8 adds `/model-runtime/*` routes for manifest validation, request validation, response validation, and simulation. `/model-runtime/simulate` is a deterministic dry-run endpoint and must not call a live runtime.

M8.5 adds `/approvals/*` validation routes for local/dev approval request, grant, decision, and receipt contracts. These routes do not authenticate users, persist approvals, or perform external actions.

API validation errors are sanitized before they are returned. FastAPI/Pydantic validation failures must not echo raw invalid input values or secret-like field values.
