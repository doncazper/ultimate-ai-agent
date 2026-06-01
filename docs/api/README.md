# API Boundary

The v0.11.2 API boundary is metadata-first and validation-only. It publishes the current OpenAPI schema and `/api/manifest` route inventory without adding runtime model calls, provider calls, web fetching, browser automation, or production persistence.

Use:

```bash
python scripts/export_openapi.py
python scripts/verify_openapi_contract.py
```

The export script writes JSON to stdout by default. Use `--output` only when an intentional artifact is needed.
