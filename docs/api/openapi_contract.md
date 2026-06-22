# OpenAPI Contract

Current active baseline: **v0.102.3**

Current OpenAPI path count: `112`.

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
- UAA-P1-080 route classification classifies every route as one of
  `public_metadata`, `local_readonly`, `local_sensitive`, or
  `mutating_requires_authority`. This classification vocabulary is now an
  implemented OpenAPI/API manifest invariant.
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
- `GET /control-center/today/summary`, `GET /control-center/actions/inbox`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/storage/status` expose storage-backed Founder Loop
  summaries using SQLite and JSONL refs only. They do not grant action
  execution, connector writes, model/provider calls, or notification delivery.

API boundary hardening:

- UAA-P1-080 adds route classification inventory only. It does not add
  middleware, auth, CORS, headers, rate limits, dependencies, or runtime
  authority.

- UAA-P1-081 adds centralized FastAPI response security headers as an
  implemented API boundary hardening invariant:
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `X-Frame-Options: DENY`, `Permissions-Policy` denying unused browser
  capabilities, `Content-Security-Policy` with strict posture and documented
  local dev loopback connect exceptions, and HSTS only for actual HTTPS
  requests. It does not add auth, sessions, CORS, idempotency enforcement,
  rate limits, dependencies, or runtime authority.
- UAA-P1-082 adds explicit loopback CORS allowlisting for configured local
  Control Center origins: `http://localhost:5173`,
  `http://127.0.0.1:5173`, `http://[::1]:5173`,
  `http://localhost:4173`, `http://127.0.0.1:4173`, and
  `http://[::1]:4173`. CORS is browser hardening, not authentication, and
  wildcard CORS remains denied. It does not add auth, sessions, idempotency
  enforcement, rate limits, dependencies, route authority, or runtime authority.
- UAA-P1-083 will add a simple local bearer/session gate for sensitive routes
  that expose logs, observability events, task runs, approvals, memory, file
  previews or write proposals, model gateway behavior, action previews, or
  sensitive runtime state. It is not enterprise auth, multi-user auth, OAuth,
  roles, or a password flow.
- UAA-P1-084 will audit mutating routes so every mutation requires an
  idempotency key or scoped idempotency ref before authority is claimed.
- UAA-P1-085 will add targeted rate limits for model/chat, task decomposition,
  action preview/proposal, and expensive validation or local-model paths.
- UAA-P1-086 will add OpenAPI, `/api/manifest`, and route inventory tests for
  the classification, auth, approval, idempotency, header, CORS, and rate-limit
  posture. These controls are planned and must not be described as implemented
  until the scoped milestones land.

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
