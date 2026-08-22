# API Boundary

Current active baseline: **v0.104.0**

<!-- uaa-api-contract-counts:start -->
Current generated contract snapshot: `348` OpenAPI paths and `350` manifest route operations.
<!-- uaa-api-contract-counts:end -->

The counts are generated from the FastAPI application and `/api/manifest`.
The current inventory schema is `uaa-api-route-inventory.v5`; a separate
hand-reviewed security policy floor prevents refresh from blessing public,
mutating, auth, approval/idempotency, or targeted-rate-limit drift.
Governed runtime pilot routes intentionally have both `GET`
and `POST` contracts on `/api/runtime/invocations`, and the Turn Contract
Router preview plus AuthorityLease mission planning routes add no-effect
diagnostic/planning surfaces. The Hermes Runtime
Adoption delegation adapter, capability discovery, run-events, approval bridge,
streaming progress, profile isolation, tool registry, session-search,
session-lineage, virtual-provider Mixture-of-Agents posture, usage/cost
analytics posture, prompt stability tier posture, context budget pressure,
hardline command blocklist posture, managed scope policy posture, doctor
diagnostics posture, session continuity posture, MCP catalog filtering
posture, background job posture, subagent isolation posture,
worktree-per-agent posture, LSP diagnostics posture, context-reference,
optional disabled-by-default Hermes interface-mode/context-pack, and
checkpoint-rollback routes,
Governed Product
Pilot authority profile, and
runtime parity loop add protected read-only `/api/runtime/*` inspection routes.
Parity-gap closure Phase 04 adds persistent goal inspection plus exact,
idempotent local metadata create/edit/transition routes and upgrades
`GET /api/runtime/run-events` to bounded durable cursor replay for accepted
local run types. Goal completion remains split into request and deterministic
receipt/proof verification; the routes grant no standing or runtime authority.
AuthorityLease V1 adds `GET /api/runtime/authority-state` and
`GET /api/runtime/authority-domain-readiness` as protected read-only authority
mode/domain/lease inspection routes with safe refs only,
plus `POST /api/runtime/authority-leases` and
`POST /api/runtime/authority-leases/approve-and-issue` as exact
approval-bound local lease selection receipt routes, and
`POST /api/runtime/authority-leases/revoke` as the idempotency-bound
safe-disable lease revocation route.
The lower lease route accepts an approval ref as an identifier only and
resolves it against backend-owned durable approval state; caller-authored grant
objects are rejected by the OpenAPI schema. `approve-and-issue` is the bounded
backend capture path and persists no caller grant payload. Unknown, expired,
tampered, or exact-scope-mismatched approval state produces a redacted denial
receipt. CLI `--approve` uses the same core path, and no AuthorityLease CLI
option accepts grant JSON.
`POST /api/runtime/hermes/chat` is also AuthorityLease-gated: exact guarded
Hermes CLI chat requires active `workspace/execute` scope before Hermes
discovery or subprocess execution, and records authority decision refs on the
redacted receipt.
Runtime invocation lifecycle routes are mapped into AuthorityLease domains:
invocation creation is workspace draft/record-only, approval binding and
approved execution are workspace execute with exact approval and lease gates,
and runtime safe-disable is a local safety control that can only reduce
authority.
The mission failure-management boundary adds three protected, idempotent local
operator-intent routes: approval decision recording, append-first mission
cancellation, and dead-letter recovery intent. An approval decision is not
authority, cancellation can only block a future start, and recovery intent
does not reopen or replay a terminal step. The local worker must freshly
evaluate request-scoped approval, policy, lease, budget, kill switch, adapter,
target, deadline, and safe-disable posture immediately before any execution.
`POST /api/runtime/local-model/call` is AuthorityLease-gated as
`provider_model_calls/execute`: configured loopback local-model transport
requires Full machine access scope before execution, records metadata-only
receipts, treats model output as untrusted proposal text, and still denies
remote provider SDK calls, tools/functions, streaming, connector writes,
browser automation, billing, and production authority.
`POST /extensions/disabled-install-records/rollback` is a blocked rollback
boundary for local disabled extension metadata. It cannot execute until a
core-owned durable approval resolver supplies exact rollback validation;
plugin install, runtime import, plugin execution, marketplace fetch,
connector writes, shell/browser execution, provider/model calls, and production
authority remain blocked.
Hermes Runtime Adoption Phase 35 adds `GET /api/runtime/preview-rail` as a
protected read-only preview-rail posture route with safe refs and bounded
preview plans only.
Hermes Runtime Adoption Phase 36 adds `GET /api/runtime/slash-command-registry`
as a protected read-only command metadata route with command execution and
runtime invocation blocked.
Hermes Runtime Adoption Phase 37 adds `GET /api/runtime/interrupt-redirect`
as a protected read-only run-control proposal route with live stop, process
kill, runtime mutation, raw runtime payload persistence, and raw log
persistence blocked.
Hermes Runtime Adoption Phase 38 adds `GET /api/runtime/logging-profile` as a
protected read-only logging profile route with verbose toggling, raw log
persistence, provider payload persistence, and remote telemetry export blocked.
Hermes Runtime Adoption Phase 39 adds `GET /api/runtime/result-classification`
as a protected read-only result taxonomy route with tool-output-as-truth,
action authority, unverified evidence promotion, and raw output persistence
blocked.
Hermes Runtime Adoption Phase 41 adds `GET /api/runtime/voice-media-posture`
as a protected read-only voice/media posture route with microphone, camera,
upload, transcription, generation, provider call, external delivery, and media
material persistence blocked.
Hermes Runtime Adoption Phase 42 adds
`GET /api/runtime/messaging-gateway-posture` as a protected read-only messaging
gateway posture route with connector runtime, connector reads, sends, OAuth,
webhook exposure, account sync, external writes, raw message persistence, and
Control Center authority minting blocked.
Hermes Runtime Adoption Phase 43 adds
`GET /api/runtime/remote-execution-posture` as a protected read-only remote
execution posture route with host access, cloud sandboxes, remote command
sessions, file sync, protected material access, remote process control,
credential material persistence, and Control Center authority minting blocked.
Hermes Runtime Adoption Phase 44 adds
`GET /api/runtime/plugin-metadata-posture` as a protected read-only plugin
metadata posture route with runtime imports, hooks, package installation,
marketplace content execution, plugin code execution, connector writes,
provider calls, raw manifest persistence, and Control Center authority minting
blocked.
Hermes Runtime Adoption Phase 45 adds
`GET /api/runtime/skill-marketplace-posture` as a protected read-only skill
marketplace posture route with external code execution, direct marketplace
installation, runtime import, automatic skill writes, provider calls, browser
automation, connector writes, raw marketplace payload persistence, and Control
Center authority minting blocked.

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
docs/api/BETA_12_BACKEND_MODULARIZATION_API.md
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
  decomposition, action preview/proposal, Action Inbox decisions,
  `workspace/draft` AuthorityLease-gated Today to Action envelope promotion,
  Chat durable receipt/handoff routes, Memory Review decision receipt routes,
  Memory context-pack internal Action proposal routes,
  the exact-approved provider credential validation lane, the tiny
  exact-approved provider lane, governed runtime pilot mutation routes, the
  extension install-disabled record receipt route, and local model validation
  route groups. It does not add auth, distributed quota, dependencies,
  billing, or production authority.
- Governed Runtime Pilot Phase 07 keeps `/api/runtime/*` contract, policy,
  approval-binding, receipt, and safe-disable metadata routes while exposing
  configured local loopback model calls, one allowlisted read-only command
  status capability, and Action Inbox approved focused pytest, repo verifier,
  frontend check, and repo-doctor command execution through `RuntimeGateway`
  only when the required AuthorityLease scope validates, then makes those
  records visible through
  `uaa runtime ...`, `uaa actions approve|deny ...`, and Control Center runtime
  readiness/evidence timeline cards. It also hardens command root pinning,
  configured endpoint matching, receipt-detail execution truth, and CLI approval
  preflight. They are backend-owned safe-ref/metadata receipts; arbitrary
  shell/subprocess execution, focused tests, repo verifier, frontend-check, and
  repo-doctor execution outside implemented AuthorityLease-gated capabilities,
  arbitrary adapter execution, remote provider/model
  calls, browser automation, connector writes, plugin runtime import, remote
  execution, production authority, and public release claims remain blocked.
- `GET /api/runtime/governed-product-pilot-profile` exposes a Python Core
  Governed Product Pilot read model with sealed/default denial,
  AuthorityLease-gated capability posture, portable evidence envelope refs,
  durable orchestration posture, and blocked authority refs. It does not add a
  mutation capability.
- `GET /api/runtime/parity-loop` exposes the Phase 08 backend-owned runtime
  parity-loop inspection model across prepared turn, route binding, durable run,
  staged orchestration, provider evidence, Action Inbox approval, receipt,
  local hash-integrity evidence (with legacy signed identifiers), and
  blocked-state refs. It does not execute work or grant
  authority.
- CRM Local Command Center M2 adds six local read routes under
  `/control-center/crm/*` and one exact local mutation receipt route at
  `POST /control-center/crm/local-mutations`. These routes expose safe-ref CRM
  relationship, follow-up, timeline, pipeline, smart-list, report, storage,
  import/export-preview, proposal, `contacts/write` authority proof, and local
  receipt posture only. Connector runtime, connector writes, external CRM
  writes, account sync, sends, calendar writes, provider/model calls, live web,
  browser automation,
  public beta, public release, production readiness, and production authority
  remain blocked.
- Beta 12 extracts the app-owned Control Center shell/status route block into
  `ultimate_ai_agent.api.control_center` while preserving the then-current
  169-route
  OpenAPI/API manifest boundary, stable operation IDs, route classifications,
  side-effect classes, release-surface truth, and task-decomposition service
  compatibility. It adds no routes and no runtime authority.
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
  as an active `memory/draft` AuthorityLease-gated, exact-approved internal
  Action proposal receipt hook. It records authority decision refs and does
  not execute actions, inject prompt context, call providers, write connectors,
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
- `/api/manifest` exposes `web_access_posture` to identify
  `ultimate_ai_agent.core.web_access` as the central WebAccessGateway
  policy/audit boundary. This is boundary-only wording: unrestricted web
  fetching, browser execution, provider configuration, mutations, clicks,
  forms, auth/cookies, downloads, and uploads remain unavailable.
- Validation, preview, evaluate, dry-run, readiness, and status routes remain
  non-production authority surfaces.
- Local `/v1/models` and `/v1/chat/completions` are disabled by default,
  loopback/local-only, bearer-gated, and scoped to the approved local
  llama.cpp/OpenWebUI shell lane.
- Task decomposition and file routes remain local-dev scoped and governed by
  approval, policy, redaction, idempotency, and rollback contracts.
- `GET /extensions/catalog` exposes read-only inspectable extension metadata.
  `POST /extensions/disabled-install-records` and its rollback route reject
  caller-supplied approval grants and remain blocked until a core-owned durable
  approval resolver exists. Python Core builders still require an exact
  injected `LocalApprovalAuthority`, active `workspace/write` AuthorityLease,
  pinned hashes, and idempotency. These routes are separate from any callable
  catalog and do not enable package
  install persistence, runtime import, plugin execution, connector writes,
  shell/subprocess behavior, unrestricted network/browser automation, mobile
  control, or public distribution.
- `GET /observability/session-events` and `POST /observability/client-errors`
  expose bounded redacted session summaries and client-error summaries only;
  they do not expose raw JSONL records, request or response bodies, prompts,
  provider payloads, terminal output, credentials, or external telemetry.
- `GET /web-evidence/status` and `POST /web-evidence/request` expose governed
  web evidence status and an allowlisted HTTPS GET evidence request envelope.
  They do not enable unrestricted browsing, browser automation, request bodies,
  redirects, downloads, raw page/body storage, raw header storage, or hidden
  network access.
- `GET /control-center/providers/setup-guide` exposes reviewed static provider
  setup and cost-literacy metadata only. It does not collect credential values,
  store keys, validate providers, call provider SDKs, invoke models, fetch live
  pricing, or claim billing authority.
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
- `GET /control-center/work-board` exposes the Work Board Kanban cockpit read
  model with backend-owned safe refs, local-only drag/drop preview posture,
  blocked durable mutation refs, and CLI inspection refs. It does not persist
  board order, create tasks, execute work, write connectors, call providers, run
  shell/browser automation, or grant production authority.
- Route metadata must keep side-effect classes and public/protected route
  classification explicit.

Denied by the current API boundary:

- unrestricted runtime model/provider calls
- unrestricted web fetching
- unrestricted browser automation
- arbitrary or unrestricted shell/subprocess execution routes; the Phase 04
  governed runtime pilot allows only one exact allowlisted argv-only read-only
  status command with redacted receipts
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
