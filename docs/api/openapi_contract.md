# OpenAPI Contract

v0.11.2 stabilizes the FastAPI OpenAPI boundary.

Contract rules:

- `info.version` must match `ultimate_ai_agent.__version__`.
- Every API operation must have a unique stable `operationId`.
- Routes must be grouped with tags.
- `/api/manifest` must be present.
- Forbidden runtime routes for model invocation, provider invocation, web fetches, browser automation, scanner runtimes, direct tool execution, and runtime config loading must be absent.

Verification:

```bash
python scripts/verify_openapi_contract.py
```

Export:

```bash
python scripts/export_openapi.py
python scripts/export_openapi.py --output docs/api/openapi_v0_11_2.json
```

The second command is only for intentional versioned snapshots.
