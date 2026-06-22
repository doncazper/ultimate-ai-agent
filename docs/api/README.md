# API Boundary

Current active baseline: **v0.102.3**

Current OpenAPI path count: `112`, generated from the FastAPI application and
exposed through `/api/manifest`.

The API boundary is metadata-first, validation-first, approval-aware for
local/dev policy checks, simulated/fallback-first for model runtime behavior,
status/readiness oriented for runtime surfaces, and preview-oriented for
Control Center contracts. It must preserve stable OpenAPI operation IDs,
route side-effect classification, `/api/manifest`, safe validation errors, and
Foundation Gate coverage.

Use:

```bash
.venv/bin/python scripts/export_openapi.py
.venv/bin/python scripts/verify_openapi_contract.py
```

The export script writes JSON to stdout by default. Use `--output` only when an
intentional artifact is needed.

Current API docs:

```text
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md
docs/api/UAA_P1_081_CENTRALIZED_FASTAPI_SECURITY_HEADERS.md
docs/api/UAA_P1_082_EXPLICIT_LOOPBACK_CORS_ALLOWLIST.md
docs/api/SAFE_STATIC_MANIFEST_CACHING.md
docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md
docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md
```

Current boundary summary:

- `/api/manifest` publishes typed route metadata, generated route count, and
  UAA-P1-080 route classification as `public_metadata`, `local_readonly`,
  `local_sensitive`, or `mutating_requires_authority`.
- UAA-P1-081 adds centralized FastAPI response security headers with
  HTTPS-only HSTS and no auth, CORS, rate-limit, or production authority claim.
- UAA-P1-082 adds an explicit local Control Center loopback CORS allowlist with
  exact dev/preview origins, no credentials, no wildcard CORS, and no auth
  claim.
- `/api/manifest` may cache only process-local static manifest metadata; policy
  decisions, approvals, runtime authority, user data, mutable state, and secrets
  remain excluded.
- Validation, preview, evaluate, dry-run, readiness, and status routes remain
  non-production authority surfaces.
- Local `/v1/models` and `/v1/chat/completions` are disabled by default,
  loopback/local-only, bearer-gated, and scoped to the approved local
  llama.cpp/OpenWebUI shell lane.
- Task decomposition and file routes remain local-dev scoped and governed by
  approval, policy, redaction, idempotency, and rollback contracts.
- `GET /extensions/catalog` exposes read-only inspectable extension metadata
  only. It is separate from any callable catalog and does not enable runtime
  import, plugin execution, connector writes, shell/subprocess behavior,
  unrestricted network/browser automation, mobile control, or public
  distribution.
- `GET /observability/session-events` and `POST /observability/client-errors`
  expose bounded redacted session summaries and client-error summaries only;
  they do not expose raw JSONL records, request or response bodies, prompts,
  provider payloads, terminal output, credentials, or external telemetry.
- `GET /web-evidence/status` and `POST /web-evidence/request` expose governed
  web evidence status and an allowlisted HTTPS GET evidence request envelope.
  They do not enable unrestricted browsing, browser automation, request bodies,
  redirects, downloads, raw page/body storage, raw header storage, or hidden
  network access.
- `/integrations/mattermost` exposes a disabled-by-default local bridge for
  Mattermost agent-room role metadata, bounded message ingress, role bindings,
  receipts, and audit summaries. It does not store raw transcripts, handle
  credentials or cookies, grant model-output authority, or perform unapproved
  connector writes.
- `GET /control-center/today/summary`, `GET /control-center/actions/inbox`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/storage/status` expose storage-backed Founder Loop
  summaries with safe refs and bounded summaries only. They do not grant
  action execution, connector writes, provider calls, email/calendar reads, or
  notification delivery.
- Route metadata must keep side-effect classes and public/protected route
  classification explicit.

Denied by the current API boundary:

- unrestricted runtime model/provider calls
- unrestricted web fetching
- unrestricted browser automation
- shell/subprocess execution routes
- connector writes outside exact-approved scoped milestones
- plugin runtime import or arbitrary plugin execution
- mobile control or mobile sensor runtime
- raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, or credential material in durable API
  evidence
- production authority claims without the exact scoped gate and reviewed
  evidence

Historical release notes and route-inventory sections may preserve older
OpenAPI counts such as `74` or `75` for the milestones where those counts were
true. They are audit history, not the current route count.

API validation errors are sanitized before they are returned. FastAPI/Pydantic
validation failures must not echo raw invalid input values or secret-like field
values.
