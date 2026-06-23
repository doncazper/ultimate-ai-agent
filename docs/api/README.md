# API Boundary

Current active baseline: **v0.103.0**

Current OpenAPI path count: `133`, generated from the FastAPI application and
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
docs/api/UAA_P1_083_LOCAL_BEARER_SESSION_GATE.md
docs/api/UAA_P1_084_MUTATING_ROUTE_IDEMPOTENCY_AUDIT.md
docs/api/SAFE_STATIC_MANIFEST_CACHING.md
docs/api/FCC_V1_001_API_PERIMETER_FOR_REAL_MUTATIONS.md
docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md
docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md
docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md
docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md
```

Current boundary summary:

- `/api/manifest` publishes typed route metadata, generated route count, and
  UAA-P1-080 route classification as `public_metadata`, `local_readonly`,
  `local_sensitive`, or `mutating_requires_authority`.
- FCC-V1-001 adds route-level `auth_posture` and `approval_posture` metadata
  plus summary counts to `/api/manifest` and the frozen route inventory. This
  is contract/verifier visibility only, not production auth or runtime
  approval authority.
- UAA-P1-081 adds centralized FastAPI response security headers with
  HTTPS-only HSTS and no auth, CORS, rate-limit, or production authority claim.
- UAA-P1-082 adds an explicit local Control Center loopback CORS allowlist with
  exact dev/preview origins, no credentials, no wildcard CORS, and no auth
  claim.
- UAA-P1-083 adds a fail-closed local bearer gate for non-public route
  classifications while keeping `GET /health`, `GET /version`,
  `GET /api/manifest`, and `GET /openapi.json` public metadata. An explicit
  local-dev bypass exists for harnesses only. It is not enterprise auth, OAuth,
  a password flow, or production authority.
- UAA-P1-084 adds a runtime idempotency header gate for
  `mutating_requires_authority` routes. It requires `X-UAA-Idempotency-Key` or
  `X-UAA-Idempotency-Ref` before mutating handlers run, without durable dedupe,
  exactly-once execution, rate-limit, mutation authority, or production
  authority claims.
- UAA-P1-085 adds targeted local fixed-window rate limits for model/chat, task
  decomposition, action preview/proposal, Action Inbox decisions, Today to
  Action envelope promotion, Chat durable receipt/handoff routes, Memory Review
  decision receipt routes, Memory context-pack internal Action proposal routes,
  and local model validation route groups. It does not
  add auth, distributed quota,
  dependencies, billing, or production
  authority.
- FCC-V1-001 consumes UAA-P1-080 through UAA-P1-086 for the Founder Loop
  mutation perimeter. Duplicate replay behavior is defined as a future
  route-owner requirement and remains blocked until append-first receipt
  storage exists for the route.
- FCC-V1-002 adds backend-owned Action Inbox decision routes for approve,
  edit, reject, defer, and receipt inspection. These routes record decision
  state and local receipt refs only; they do not execute approved actions,
  perform connector writes, call providers, run shell/subprocess work, write
  memory, or grant production authority.
- FCC-V1-005 adds backend-owned Memory Review accept/correct/reject decision
  receipts. They record safe refs, idempotency/replay posture, and Evidence
  Timeline visibility only; they do not inject context, make memory/source truth
  authoritative, sync CRM/accounts, perform connector writes, execute actions,
  or grant public beta or production authority.
- Governed Cognitive Memory Spine Phase 2 adds
  `GET /control-center/memory/l1-index` as a read-only derived preview over
  reviewed recall-only Memory Review records. It does not add embeddings,
  vector DBs, semantic search, background indexing, automatic writes, context
  injection, connector writes, action execution, or production authority.
- Governed Cognitive Memory Spine Phase 3 adds
  `GET /control-center/memory/l2-index` as read-only deterministic
  factual/graph/temporal ref projection over L1 previews. It does not add
  truth authority, embeddings, vector DBs, semantic search, LLM extraction,
  background indexing, automatic writes, context injection, connector writes,
  action execution, or production authority.
- Governed Cognitive Memory Spine Phase 5 adds
  `GET /control-center/memory/context-packs` as read-only proposal envelopes
  over reviewed L1/L2/L3 safe refs. It does not add hidden context injection,
  prompt context writing, provider/model calls, connector writes, CRM/account
  sync, action execution, public beta, or production authority.
- Governed Cognitive Memory Spine Phase 6.1 adds
  `POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal`
  as an exact-approved internal Action proposal receipt hook. It does not
  execute actions, inject prompt context, call providers, write connectors,
  sync CRM/accounts, or grant broad Phase 6 execution authority.
- Governed Cognitive Memory Spine Phase 4 adds
  `GET /control-center/memory/l3-index` as read-only deterministic
  identity/session/preference/commitment representation proposals over L2 safe
  refs. It does not add truth authority, CRM/account sync, context-pack
  injection, semantic extraction, automatic writes, context injection,
  connector writes, action execution, or production authority.
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
  `POST /control-center/chat/turns`,
  `GET /control-center/chat/turns/{turn_ref}/receipt`,
  `POST /control-center/chat/turns/{turn_ref}/handoff`,
  `GET /control-center/morning-briefing/summary`, and
  `GET /control-center/storage/status` expose storage-backed Founder Loop
  summaries and Chat receipt/handoff refs with safe refs and bounded summaries
  only. They do not grant action execution, connector writes, provider calls,
  memory writes, email/calendar reads, or notification delivery.
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
