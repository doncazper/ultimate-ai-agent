# OpenAPI Contract

v0.13.0 preserves the FastAPI OpenAPI boundary and adds local loopback validation routes without adding a public real execution route.

Contract rules:

- `info.version` must match `ultimate_ai_agent.__version__`.
- Every API operation must have a unique stable `operationId`.
- Routes must be grouped with tags.
- `/api/manifest` must be present.
- Forbidden runtime routes for cloud model invocation, provider invocation, web fetches, browser automation, scanner runtimes, direct tool execution, arbitrary URL execution, and runtime config loading must be absent.
- M9 local loopback routes may validate endpoints, validate execution policy, and produce simulated fallback responses only.

Verification:

```bash
python scripts/verify_openapi_contract.py
```

Export:

```bash
python scripts/export_openapi.py
python scripts/export_openapi.py --output docs/api/openapi_v0_13_0.json
```

The second command is only for intentional versioned snapshots.
