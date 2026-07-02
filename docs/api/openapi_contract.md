# OpenAPI Contract

Current active baseline: **v0.104.0**

Current OpenAPI path count: `163`.

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
- Route metadata must preserve explicit auth posture and approval posture.
- UAA-P1-080 route classification classifies every route as one of
  `public_metadata`, `local_readonly`, `local_sensitive`, or
  `mutating_requires_authority`. This classification vocabulary is now an
  implemented OpenAPI/API manifest invariant.
- Local-dev workspace routes must remain local-dev scoped, policy-bound, and
  blocked from production authority by default.
- Governed web evidence routes may use the `governed_network_read_only`
  side-effect class and must remain HTTPS GET only, allowlisted, bounded,
  redacted, receipt-ref oriented, and blocked from unrestricted browsing.
- `POST /control-center/providers/credentials/validate` may use the
  `governed_network_read_only` side-effect class only for the exact-approved
  credential validation lane. It requires exact approval, policy scope,
  idempotency, redacted receipt refs, revocation/safe-disable posture, and an
  approved injected transport before any provider network validation can occur.
  No built-in provider transport is enabled by default, and the lane remains
  blocked from model invocation, provider SDKs, raw credential display, provider
  payload persistence, fallback, autonomous/background calls, billing authority,
  and production authority.
- `POST /control-center/providers/router/dry-run` is a proposal-only provider
  routing posture lane. Its OpenAPI visibility does not grant callable runtime:
  provider invocation, fallback execution, network calls, provider SDK calls,
  credential validation, model calls, billing authority, background execution,
  and raw prompt/response/provider payload persistence remain blocked.
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
  `POST /control-center/actions/{action_id}/approve`,
  `POST /control-center/actions/{action_id}/edit`,
  `POST /control-center/actions/{action_id}/reject`,
  `POST /control-center/actions/{action_id}/defer`,
  `POST /control-center/actions/{action_id}/local-task/commit`,
  `POST /control-center/today/action-envelope`,
  `GET /control-center/actions/{action_id}/receipt`,
  `POST /control-center/chat/turns`,
  `GET /control-center/chat/turns/{turn_ref}/receipt`,
  `POST /control-center/chat/turns/{turn_ref}/handoff`,
  `GET /control-center/memory/l1-index`,
  `GET /control-center/memory/l2-index`,
  `GET /control-center/memory/l3-index`,
  `GET /control-center/memory/retrieval-diagnostics`,
  `GET /control-center/memory/citation-integrity`,
  `GET /control-center/memory/quality-issues`,
  `GET /control-center/memory/maintenance-runs`,
  `GET /control-center/memory/context-manifest`,
  `GET /control-center/memory/context-packs`,
  `POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal`,
  `POST /control-center/memory/feedback`,
  `GET /control-center/memory/review`,
  `GET /control-center/memory/review/{candidate_ref}/receipt`,
  `POST /control-center/memory/review/{candidate_ref}/accept`,
  `POST /control-center/memory/review/{candidate_ref}/correct`,
  `POST /control-center/memory/review/{candidate_ref}/reject`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/storage/status` expose storage-backed Founder Loop
  summaries plus Action Inbox and Chat receipts using SQLite and JSONL refs
  only. Today to Action envelope, Action decision, Chat handoff, and Memory
  Review decision routes record backend-owned review state and receipt refs;
  accept/correct create reviewed recall-only records. The L1, L2, L3, and context-pack
  routes provide derived read-only recall previews, factual/graph/temporal ref
  projections, and identity/session/preference/commitment representation
  proposals plus proposal-only context-pack envelopes from reviewed source
  lanes with source, evidence, and receipt refs. Phase 6.1 may create an
  internal Action proposal receipt from an exact-approved context-pack ref only.
  `local_task_create` commits local task state only after exact local approval,
  idempotency, durable receipt, and Evidence Timeline event posture. They do
  not grant generic action execution,
  connector writes, CRM/account sync, model/provider calls, automatic memory
  writes, context injection, shell/subprocess work, embeddings/vector search,
  semantic search, LLM extraction, background indexing, context-pack injection, or notification
  delivery.

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
  `http://[::1]:4173`, with the `Authorization` request header allowed for the
  UAA-P1-083 local bearer. CORS is browser hardening, not authentication, and
  wildcard CORS remains denied. It does not add auth, sessions, idempotency
  enforcement, rate limits, dependencies, route authority, or runtime authority.
- UAA-P1-083 adds a simple local bearer gate for protected routes classified
  as `local_readonly`, `local_sensitive`, or
  `mutating_requires_authority`. Protected routes fail closed unless a valid
  `UAA_API_LOCAL_BEARER` is configured and sent, or the explicit
  `UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY=1` local-dev bypass is set; it is
  not enterprise auth, multi-user auth, OAuth, roles, or a password flow.
- UAA-P1-084 adds a runtime boundary check for routes classified as
  `mutating_requires_authority`: requests must carry
  `X-UAA-Idempotency-Key` or `X-UAA-Idempotency-Ref` before the mutating
  handler can run. It does not add durable idempotency storage, replay
  execution, mutation authority, or production authority.
- UAA-P1-085 adds targeted local fixed-window rate limits for model/chat, task
  decomposition, action preview/proposal, Action Inbox decisions and the
  Action Inbox local task commit lane,
  Today-to-Action envelope promotion, Chat durable receipts/handoffs, Memory
  Review decision receipts, the tiny exact-approved provider lane, and
  expensive validation or local-model paths. It
  does not add auth, distributed
  quota, dependencies, billing, or production authority.
- UAA-P1-086 adds enforcement tests for OpenAPI, `/api/manifest`, and route
  inventory alignment across classification, auth, approval, idempotency,
  header, CORS, and rate-limit posture. This does not add routes, middleware,
  runtime authority, public beta, or production authority.
- FCC-V1-001 adds manifest-visible `auth_posture` and `approval_posture`
  fields plus summary counts for every route, updates the frozen route
  inventory fixture to `uaa-api-route-inventory.v4`, and adds a Founder Loop
  mutation perimeter verifier. Duplicate replay is a future route-owner
  receipt-storage requirement, not current runtime replay.

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
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_boundary_enforcement.py
.venv/bin/python scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py
.venv/bin/python scripts/verify_fcc_v1_001_api_perimeter.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
```

Export:

```bash
.venv/bin/python scripts/export_openapi.py
```

Use `--output` only for an intentional versioned snapshot. Historical docs may
mention earlier path counts such as `74` or `75`; those counts are audit
history, not the current OpenAPI route count.
