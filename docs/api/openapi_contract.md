# OpenAPI Contract

Current active baseline: **v0.102.1**

Current OpenAPI path count: `108`.

The OpenAPI schema is the public route contract for the current FastAPI API
boundary. `/api/manifest` is the typed metadata and route-inventory endpoint
for the same boundary. The schema and manifest must stay aligned with
`ultimate_ai_agent.__version__`, route side-effect classification, and
Foundation Gate checks.

Contract rules:

- `info.version` must match `ultimate_ai_agent.__version__`.
- Every API operation must have a unique stable `operationId`.
- Routes must be grouped with tags.
- `/api/manifest` must be present.
- API validation errors must be sanitized and must not echo raw invalid input
  values or secret-like field values.
- Route metadata must preserve explicit side-effect classes.
- Local-dev workspace routes must remain local-dev scoped, policy-bound, and
  blocked from production authority by default.
- Governed web evidence routes may use the `governed_network_read_only`
  side-effect class and must remain HTTPS GET only, allowlisted, bounded,
  redacted, receipt-ref oriented, and blocked from unrestricted browsing.
- The local `/v1` gateway must remain disabled by default, loopback/local-only,
  bearer-gated, and constrained to the accepted local model lane.
- `GET /extensions/catalog` must remain a read-only inspectable metadata route
  only; it is not a callable catalog and does not enable plugin runtime import
  or extension execution.
- `/observability/session-events` and `/observability/client-errors` must remain
  local, bounded, redacted-summary routes only; they must not expose raw JSONL
  records, request or response bodies, prompts, provider payloads, terminal
  output, credentials, or external telemetry.

Forbidden by the current API boundary:

- cloud/provider model invocation as production authority
- unrestricted web fetches or source fetching
- unrestricted browser automation
- shell/subprocess execution routes
- arbitrary tool execution routes
- connector writes outside exact-approved scoped milestones
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, or credential material in durable schema,
  manifest, report, or test evidence
- runtime config loading that bypasses reviewed policy boundaries

Verification:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
```

Export:

```bash
.venv/bin/python scripts/export_openapi.py
```

Use `--output` only for an intentional versioned snapshot. Historical docs may
mention earlier path counts such as `74` or `75`; those counts are audit
history, not the current OpenAPI route count.
