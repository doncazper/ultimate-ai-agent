# OpenAPI Contract

Current active baseline: **v0.104.0**

Current OpenAPI path count: `202`.

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
- `POST /control-center/web-evidence/attach` is the current Tier 1 web
  evidence product-slice route. It uses `WebAccessGateway` for one allowlisted
  HTTPS GET preview, returns a bounded redacted preview to the requester, stores
  only safe receipt/evidence/audit refs in Founder Loop durable surfaces, and
  grants no browser action, session state, download/upload, mutation method,
  context injection, memory write, provider/model call, connector write,
  public release, or production authority.
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
- `POST /control-center/turn-router/preview` is a no-effect diagnostic route
  for the UAA Turn Contract Router. It may classify sample or ephemeral request
  text for immediate inspection, but returns safe refs, selected contract,
  policy posture, no-effect proof flags, and redaction refs only. It does not
  persist raw request text, call providers/models, execute tools/actions,
  retrieve memory bodies, inject context, run shell/browser work, write
  connectors, or wire chat runtime behavior.
- `/api/runtime/*` is the governed runtime pilot contract surface. The
  Governed Product Pilot authority profile is exposed at
  `GET /api/runtime/governed-product-pilot-profile` as a protected read-only
  Python Core read model for exact lane posture, portable evidence envelopes,
  durable orchestration posture, and blocked authority refs.
  `GET /api/runtime/staged-orchestration` exposes a protected read-only
  Python Core staged orchestration plan/checkpoint/dependency read model and
  grants no scheduling, dispatch, background autonomy, model call, browser
  action, connector write, shell/subprocess authority, or production authority.
  `GET /api/runtime/prepared-turn` exposes a protected read-only Python Core
  prepared-turn read model over turn contract, route binding, readiness,
  durable run, and evidence refs without persisting raw prompt text or granting
  runtime authority.
  `GET /api/runtime/parity-loop` exposes the Phase 08 backend-owned runtime
  parity-loop inspection model that ties prepared turn, route decision, durable
  run, staged orchestration, provider evidence, Action Inbox approval, receipt,
  signed evidence, and blocked-state refs together without executing work.
  Phase 07
  preserves configured local loopback model calls and the exact read-only status
  command while adding exact Action Inbox approved focused pytest command execution
  through `RuntimeGateway`, plus CLI/Control Center/evidence timeline parity
  over the same backend-owned records. It also records command root pinning,
  configured endpoint matching, receipt-detail execution truth, and CLI approval
  preflight posture. It records
  capability metadata, safe-ref invocation metadata, policy decisions,
  approval-ref bindings, metadata-only local model receipts, redacted command
  receipts, blocked execution receipts, and safe-disable posture. Model output
  is untrusted proposal text, and command output is redacted and bounded.
  `uaa runtime status`, `uaa runtime capabilities`, `uaa runtime invocations
  list/show`, `uaa runtime receipts show`, `uaa runtime safe-disable`, and
  `uaa actions approve|deny` are local inspection/exact-envelope decision
  surfaces over those records; approval refs remain identifiers, not authority.
  It does not run arbitrary shell/subprocess commands, execute focused tests
  outside the exact pytest lane, run repo verifiers or frontend checks, invoke
  remote providers, read
  or persist raw prompts/responses/command output/local paths/env, automate
  browsers, write connectors, import plugins, dispatch remote work, grant
  production authority, or claim public release readiness.
- `/control-center/crm/*` is the CRM Local Command Center M2 contract surface.
  Six CRM routes are local read routes, and
  `POST /control-center/crm/local-mutations` is one exact local mutation
  receipt lane requiring idempotency and exact `LocalApprovalAuthority`
  validation. CRM routes expose safe refs, bounded summaries, redacted storage
  posture, deterministic proposal refs, import/export preview posture, and
  receipt refs only. They do not add connector runtime, connector writes,
  external CRM writes, account sync, sends, calendar writes, provider/model
  calls, live web, browser automation, background autonomy, public beta, public
  release, production readiness, or production authority.
- The local `/v1` gateway must remain disabled by default, loopback/local-only,
  bearer-gated, and constrained to the accepted local model lane.
- `GET /extensions/catalog` must remain a read-only inspectable metadata route
  only. It may expose safe refs, visibility status, trust posture, callable
  posture, blocked reasons, review evidence refs, and safe adoption posture,
  but it is not a callable catalog and does not enable plugin runtime import or
  extension execution.
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
  `GET /control-center/memory/context-packs/{context_pack_ref}/preview`,
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
- `GET /control-center/coding/session` exposes the repo-safe Coding Cockpit
  shell seed as a backend-owned read model with safe refs, blocked authority
  refs, and proof refs only. `GET /control-center/coding/context` exposes the
  read-only context-pack preview as safe refs, excluded refs, comparison refs,
  budget posture, proof refs, and redaction refs only.
  `GET /control-center/coding/patch-proposal` exposes proposal-only patch file
  refs, hunk refs, bounded diff summaries, proof refs, and redaction refs only.
  `GET /control-center/coding/patch-apply-readiness` exposes the blocked
  Prompt 04 apply-readiness model with safe prerequisite, receipt, rollback,
  blocker, promotion-path, proof, and unblock-prompt refs only.
  `GET /control-center/coding/test-command-readiness` exposes the blocked
  Prompt 05 allowlisted test-command readiness model with suggested command,
  allowlist, expected receipt, proof, blocker, promotion-path, and
  unblock-prompt refs only.
  `GET /control-center/coding/git-review` exposes the blocked Prompt 06 Git
  review model with status, diff, changed-file, commit proposal,
  pull-request proposal, expected receipt, proof, blocker, promotion-path, and
  unblock-prompt refs only.
  `GET /control-center/coding/live-preview` exposes the blocked Prompt 07 live
  preview model with dev-server status, preview URL, screenshot, console,
  visual-proof, route-checklist, viewport, proof, blocker, promotion-path, and
  unblock-prompt refs only.
  `GET /control-center/coding/multi-agent-review` exposes the blocked Prompt
  08 multi-agent review model with agent slot, plan, review, diff-comparison,
  disagreement, handoff, blocker, promotion-path, proof, and unblock-prompt
  refs only.
  `GET /control-center/work-board` exposes the backend-owned Work Board Kanban
  read model with safe card, column, proof, evidence, blocker, promotion-path,
  drag/drop posture, exact approved reorder posture, and CLI inspection refs.
  `POST /control-center/work-board/reorder` persists one exact approved local
  order with idempotency, safe refs, receipt refs, rollback/safe-disable
  posture, and no external side effects. Card creation, task creation, issue
  tracker sync, provider/model calls, shell/browser work, connector writes, and
  production authority remain blocked.
  These routes do not write files, apply patches, read or persist raw file
  content, run shell/subprocess commands, execute commands, mutate Git state,
  start or inspect dev servers, persist raw URLs, capture screenshots, read
  console output, call providers or models, call provider SDKs, dispatch local
  agents, inject context, persist raw prompts or responses, automate browsers,
  write connectors, launch background agents, or grant production authority.

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
  expensive validation, governed runtime pilot, or local-model paths. It
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
- arbitrary or unrestricted shell/subprocess execution routes; the Phase 04
  governed runtime pilot allows only one exact allowlisted argv-only read-only
  status command with redacted receipts
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
