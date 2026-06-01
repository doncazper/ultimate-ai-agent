# API Boundary

The v0.13.1 API boundary is metadata-first, validation-first, approval-aware for local/dev policy checks, and simulated/fallback-first for model runtime behavior. It publishes the current OpenAPI schema and `/api/manifest` route inventory without adding cloud model calls, provider SDK calls, web fetching, browser automation, tokenizers, billing APIs, production auth, OAuth, or production persistence.

Use:

```bash
python scripts/export_openapi.py
python scripts/verify_openapi_contract.py
```

The export script writes JSON to stdout by default. Use `--output` only when an intentional artifact is needed.

M8 adds `/model-runtime/*` routes for manifest validation, request validation, response validation, and simulation. `/model-runtime/simulate` is a deterministic dry-run endpoint and must not call a live runtime.

M8.5 adds `/approvals/*` validation routes for local/dev approval request, grant, decision, and receipt contracts. These routes do not authenticate users, persist approvals, or perform external actions.

M9 adds `/model-runtime/local/*` validation and simulated fallback routes for local loopback endpoint policy checks. The public API does not expose default real loopback execution. Real local loopback execution remains a library-level dev-only path requiring explicit opt-in policy, validated approval, loopback endpoint policy, and injected transport. v0.13.1 hardens this boundary so remote hosts are denied even when caller-supplied policy allowlists include them or `deny_non_loopback=false` is supplied.

API validation errors are sanitized before they are returned. FastAPI/Pydantic validation failures must not echo raw invalid input values or secret-like field values.
