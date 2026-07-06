# OpenAPI Contract

Current active baseline: **v0.104.0**

Current OpenAPI path count: `236`.

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
  `GET /api/runtime/delegation-adapter` exposes the Hermes Runtime Adoption
  Phase 01 backend-owned runtime delegation adapter readiness model with
  runtime identity refs, endpoint posture, authority mode, capability refs,
  health refs, proof refs, blocked reasons, and next safe actions. It is
  read-only readiness only: UAA controls authority, Control Center does not
  talk directly to Hermes, and live run submission, model/provider calls, tool
  execution, shell/subprocess execution, browser automation, connector writes,
  background autonomy, production authority, and raw prompt/response/provider
  payload/log/local-path persistence remain blocked.
  `GET /api/runtime/interface-mode` exposes the backend-owned
  `runtime_interface_mode.v1` contract for optional Hermes interface mode. The
  default mode is `disabled`: UAA remains UAA-native, does not discover or probe
  Hermes, does not project context, and does not execute Hermes chat unless
  `UAA_HERMES_INTERFACE_MODE_ENABLED=1` is explicitly set. The contract also
  shows opt-in `shell_guarded`, `operator_override`, and
  `pure_hermes_pass_through` postures, keeps UAA-native agent
  planning/execution off, reports Hermes CLI posture, and labels blocked unsafe
  Hermes flags, arbitrary args, shell strings, direct memory writes, raw
  persistence, browser automation, connector writes, and production authority.
  `GET /api/runtime/hermes/context-pack` exposes the
  `hermes_context_pack.v1` bridge. While the interface is disabled it reports
  `projection_enabled=false` and zero projected sections. When explicitly
  enabled, it projects Memory, CRM, Chat, Cowork/Plans, Today, Action Inbox,
  Evidence, Proof, and Sources into Hermes-safe summaries. It carries provenance
  refs, why-shown refs, evidence/proof refs, and explicit false flags for raw
  Memory/CRM/chat/path/log/credential exposure.
  `POST /api/runtime/hermes/chat` is a mutating-requires-authority local
  interface route for exact Hermes CLI chat argv only. It requires idempotency,
  returns a redacted receipt, hashes the query, summarizes output, and keeps
  Hermes output as untrusted proposal text with Memory updates candidate-only.
  `GET /api/runtime/capability-discovery` exposes the Hermes Runtime Adoption
  Phase 02 backend-owned runtime capability discovery posture for models, runs,
  events, approvals, sessions, skills, toolsets, jobs, and blocked actions. It
  distinguishes runtime-supported reference metadata from UAA-authorized
  execution, treats stale or unreachable runtime state as blocked, includes a
  snapshot hash ref, and performs no live runtime call. It also includes the
  Phase 09 runtime toolset capability posture, which maps runtime support to
  UAA allowance states while keeping runtime tool invocation, Hermes toolset
  enablement, toolset config mutation, raw tool payload persistence, and
  production authority disabled.
  `GET /api/runtime/tool-registry` exposes the Hermes Runtime Adoption Phase
  10 backend-owned runtime tool registry availability posture. It lists
  UAA-native preview tools and delegated Hermes/Codex/Claude/MCP/future runtime
  tool references with availability, configured status, authority class,
  side-effect class, risk, blocker refs, proof refs, and next safe actions. It
  is read-only metadata only and does not invoke tools, perform remote
  discovery, fetch the web, call providers/models, import plugins, activate
  connector writes, persist raw tool payloads, or grant production authority.
  `GET /api/runtime/session-search` exposes the Hermes Runtime Adoption Phase
  12 backend-owned session/run search posture. It returns safe refs and bounded
  summaries only, stays separate from durable memory, requires operator-selected
  attach refs before any future context use, and grants no raw transcript
  persistence, prompt/response exposure, semantic provider call, embedding or
  vector index, hidden context injection, memory write, action execution, or
  production authority.
  `GET /api/runtime/session-lineage` exposes the Hermes Runtime Adoption Phase
  19 backend-owned session lineage and fork posture. It returns safe
  parent/child, user request, task, run, proof, branch, reason, redacted
  fork-envelope, retrieval-log, compare-view, verifier, and blocked authority
  refs only. It does not clone raw transcripts, persist raw prompts or
  responses, inject hidden context, dispatch runtimes, call providers/models,
  write connectors, run shell/subprocess commands, automate browsers, or grant
  production authority.
  `GET /api/runtime/virtual-provider-moa` exposes the Hermes Runtime Adoption
  Phase 20 backend-owned virtual provider Mixture-of-Agents posture. It returns
  preset, agent-slot, route-decision trace, cost-estimate, approval-mode,
  output-envelope, comparison-proof, safe-disable, verifier, and blocked
  authority refs only. It does not perform live model fan-out, call provider
  SDKs, dispatch external runtimes, use hidden advisor prompts, treat agent
  output as authority, write connectors, run shell/subprocess commands,
  automate browsers, or grant production authority.
  `GET /api/runtime/usage-cost-analytics` exposes the Hermes Runtime Adoption
  Phase 22 backend-owned usage and cost analytics posture. It returns redacted
  accounting record refs, runtime/provider/model refs, task-value refs, receipt
  refs, estimate refs, bounded usage estimates, latency estimates, cost minor
  units, proof refs, verifier refs, and blocked authority refs only. It does
  not perform billing actions, provider calls, provider SDK calls, live pricing
  fetches, operator export, raw prompt/response/provider-payload persistence,
  model-output authority, or production authority.
  `GET /api/runtime/prompt-stability-tiers` exposes the Hermes Runtime
  Adoption Phase 23 backend-owned prompt stability tier posture. It returns
  prompt tier refs, manifest refs, redacted hash refs, cache policy refs, safe
  source refs, proof refs, verifier refs, next-safe-action refs, and blocked
  authority refs only. It does not persist raw prompts or responses, inject
  hidden prompt/context material, call models or provider SDKs, write caches,
  treat model output as authority, or grant production authority.
  `GET /api/runtime/context-budget-pressure` exposes the Hermes Runtime
  Adoption Phase 24 backend-owned context budget pressure posture. It returns
  context budget segment refs, pressure levels, warning refs, review-only
  trimming and summary proposal refs, source refs, retrieval log refs, proof
  refs, verifier refs, next-safe-action refs, and blocked authority refs only.
  It does not perform hidden compression, automatic context mutation, model
  summarization calls, context injection, provider SDK calls, cache writes, raw
  context/prompt/response/provider-payload persistence, or production
  authority.
  `GET /api/runtime/hardline-command-blocklist` exposes the Hermes Runtime
  Adoption Phase 25 backend-owned hardline command blocklist posture. It
  returns command-shape classification refs, denied category refs, allowed
  shape counts, hardline rule refs, proof refs, verifier refs,
  next-safe-action refs, and blocked authority refs only. It does not run
  commands, accept raw command strings, persist raw command text or output,
  permit floor override, or grant production authority.
  `GET /api/runtime/managed-scope-policy` exposes the Hermes Runtime Adoption
  Phase 27 backend-owned managed scope policy posture. It returns pinned local
  policy source refs, precedence, checksum refs, drift warning refs, rollback
  refs, admin/operator proof refs, verifier refs, next-safe-action refs, and
  blocked authority refs only. It does not write system config, perform
  privileged writes, deliver MDM profiles, manage secrets, accept unsigned
  runtime config overrides, persist raw config/local path/account/credential
  material, or claim production enforcement.
  `GET /api/runtime/doctor-diagnostics` exposes the Hermes Runtime Adoption
  Phase 28 backend-owned runtime doctor diagnostics posture. It returns
  diagnostic refs, setup/runtime/provider/tool/protected-material/service/
  authority status refs, CLI refs, proof refs, next-safe-action refs, and
  blocked authority refs only. It does not install dependencies, start
  services, write credentials, mutate runtime config, persist raw logs or local
  paths, persist provider payloads, or mint authority from Control Center.
  `GET /api/runtime/session-continuity` exposes the Hermes Runtime Adoption
  Phase 29 backend-owned multi-surface session continuity posture. It returns
  session refs, source labels, staleness refs, conflict refs, proof refs,
  verifier refs, and blocked authority refs only. It does not enable external
  messaging gateways, account sync, connector writes, remote sessions, raw
  transcript or provider payload persistence, or Control Center authority
  minting.
  `GET /api/runtime/mcp-catalog-filtering` exposes the Hermes Runtime Adoption
  Phase 30 backend-owned MCP catalog filtering posture. It returns metadata
  catalog refs, tool filter contracts, blocked activation states, proof refs,
  verifier refs, and blocked authority refs only. Installing MCP servers,
  running subprocess MCPs, OAuth login, tool invocation, connector writes, raw
  manifest persistence, and Control Center authority minting remain blocked.
  `GET /api/runtime/background-jobs` exposes the Hermes Runtime Adoption Phase
  31 backend-owned background job posture. It returns durable job proposal refs,
  schedule policies, approval scope refs, idempotency refs, safe-disable refs,
  receipt plans, failure handling refs, proof refs, verifier refs, and blocked
  authority refs only. Schedulers, workers, run-now, pause/resume mutation,
  autonomous retries, external delivery, provider calls, shell execution, and
  connector writes remain blocked.
  `GET /api/runtime/subagent-isolation` exposes the Hermes Runtime Adoption
  Phase 32 backend-owned subagent isolation posture. It returns role refs,
  scope envelopes, context/tool/memory grant refs, budget refs, kill-switch
  refs, review artifacts, proof refs, verifier refs, and blocked authority refs
  only. Live dispatch, background fan-out, cross-agent memory transfer, tool
  sharing, autonomous delegation, raw transcript persistence, and raw agent
  output persistence remain blocked.
  `GET /api/runtime/worktree-per-agent` exposes the Hermes Runtime Adoption
  Phase 33 backend-owned worktree-per-agent posture. It returns lane refs,
  workspace scope refs, branch proposal refs, worktree refs, checkpoint plans,
  Git receipt plans, rollback plans, proof refs, verifier refs, and blocked
  authority refs only. Git worktree create/delete, branch mutation, file
  writes, commits, pushes, raw path persistence, shell execution, and provider
  calls remain blocked.
  `GET /api/runtime/lsp-diagnostics` exposes the Hermes Runtime Adoption Phase
  34 backend-owned semantic diagnostics proof posture. It returns diagnostic
  refs, safe source scope refs, evidence refs, receipt-plan refs, proof refs,
  verifier refs, promotion refs, redaction refs, and blocked authority refs
  only. Language-server launch, dependency install, shell execution, file
  reads/writes, provider calls, raw path persistence, and raw diagnostic
  payload persistence remain blocked.
  `GET /api/runtime/preview-rail` exposes the Hermes Runtime Adoption Phase 35
  backend-owned right preview rail posture. It returns safe source refs,
  source-classification refs, bounded preview refs, redaction policy refs,
  attach-plan refs, receipt-plan refs, proof refs, verifier refs, promotion
  refs, and blocked authority refs only. Browser automation, screenshot
  capture, raw sensitive file display, direct runtime payload rendering, file
  reads/writes, shell execution, provider calls, Control Center authority
  minting, raw path persistence, raw file-content persistence, and raw runtime
  payload persistence remain blocked.
  `GET /api/runtime/slash-command-registry` exposes the Hermes Runtime Adoption
  Phase 36 backend-owned slash command registry posture. It returns command
  refs, trigger labels, command status, authority class, side-effect class,
  docs refs, approval policy refs, idempotency policy refs, receipt-plan refs,
  proof refs, verifier refs, promotion refs, and blocked authority refs only.
  Chat slash-command execution, runtime invocation, state mutation, shell
  execution, provider calls, browser automation, connector writes, Control
  Center authority minting, raw prompt persistence, raw response persistence,
  production authority, and public release claims remain blocked.
  `GET /api/runtime/interrupt-redirect` exposes the Hermes Runtime Adoption
  Phase 37 backend-owned interrupt/redirect run-control posture. It returns
  pause, stop, redirect, revise, and recovery proposal refs, approval scope
  refs, idempotency refs, receipt-plan refs, recovery-state refs, proof refs,
  verifier refs, promotion refs, and blocked authority refs only. Live stop
  POST, process kill, runtime mutation, background autonomy, shell execution,
  provider calls, browser automation, connector writes, Control Center
  authority minting, raw runtime payload persistence, raw log persistence,
  production authority, and public release claims remain blocked.
  `GET /api/runtime/logging-profile` exposes the Hermes Runtime Adoption Phase
  38 backend-owned logging profile posture. It returns quiet, redacted
  troubleshooting, and forensic safe-ref profile refs, flag scope refs, TTL
  policy refs, retention policy refs, redaction policy/verifier refs, proof
  refs, verifier refs, promotion refs, and blocked authority refs only. Verbose
  toggling, raw log persistence, raw prompt/response/provider payload/path
  persistence, credential persistence, remote telemetry export, background log
  streaming, production authority, and public release claims remain blocked.
  `GET /api/runtime/result-classification` exposes the Hermes Runtime Adoption
  Phase 39 backend-owned result taxonomy posture. It returns evidence,
  mutation, warning, blocked, proposal, diagnostic, and untrusted-data class
  refs, provenance policy refs, redaction policy refs, receipt requirement
  refs, proof binding refs, verifier refs, promotion refs, and blocked authority
  refs only. Treating tool output as truth, treating output as action
  authority, mutation without receipt, unverified evidence promotion, raw output
  persistence, provider payload persistence, production authority, and public
  release claims remain blocked.
  `GET /api/runtime/context-references` exposes the Hermes Runtime Adoption
  Phase 16 backend-owned context-reference posture. It returns safe-ref grammar,
  preview refs, budget estimates, why-included refs, and blocked URL/live-fetch
  posture for file, folder, diff, URL evidence, run, proof, task, memory, CRM
  object, and issue refs. It grants no live URL fetch, raw path persistence,
  raw file-content persistence, protected config read, automatic context
  injection, provider/model call, connector write, shell/subprocess execution,
  browser automation, or production authority.
  `GET /api/runtime/checkpoint-rollback` exposes the Hermes Runtime Adoption
  Phase 18 backend-owned checkpoint/rollback posture. It returns exact lane
  checkpoint, receipt, rollback-plan, proof, verifier, and blocked authority
  refs only; rollback execution, broad filesystem snapshots, Git mutation, raw
  path/content persistence, and production authority remain blocked.
  `GET /api/runtime/run-events` exposes the Hermes Runtime Adoption Phase 03
  backend-owned runtime run/event posture for lifecycle mappings, event refs,
  stop posture, and approval-wait proposals. It is read/proposal only and does
  not create runs, stop runs, resolve approvals, or stream live events.
  `GET /api/runtime/approval-bridge` exposes the Hermes Runtime Adoption Phase
  04 backend-owned runtime approval bridge posture for approval envelopes,
  Action Inbox projection refs, proof refs, denial/timeout/scope-mismatch
  previews, and default-deny timeout posture. It is read-model only and does
  not send approval, denial, timeout, or scope-mismatch resolutions to Hermes or
  any delegated runtime.
  `GET /api/runtime/streaming-progress` exposes the Hermes Runtime Adoption
  Phase 05 backend-owned runtime streaming progress posture for ordered,
  redacted event previews, stale/disconnected stream state, event hash refs,
  and proof refs. It is read-model only and does not open SSE/WebSocket
  subscriptions, reconnect to Hermes, ingest live runtime events, or persist
  raw runtime/tool/generated/log/prompt/response payloads.
  `GET /api/runtime/profiles` exposes the Hermes Runtime Adoption Phase 06
  backend-owned runtime profile isolation posture for UAA-owned profile refs
  that are separate from delegated runtime profile refs, safe display labels,
  role, configured status, authority posture, workspace and memory scope refs,
  toolset posture, profile health, blocked reasons, and proof refs. It is
  read-model only and does not create profiles, delete profiles, write runtime
  config, copy sensitive material, change runtime defaults, allow cross-profile
  authority bleed, expose raw delegated profile names, or expose workspace
  paths.
  Phase 07
  preserves configured local loopback model calls and the exact read-only status
  command while adding exact Action Inbox approved focused pytest, repo verifier, and frontend check command execution
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
  outside the exact pytest lane, run repo verifier/frontend check work outside named exact lanes, invoke
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
  disagreement, handoff, Pair Agents preview/readiness, blocker,
  promotion-path, proof, and unblock-prompt refs only. The nested Pair Agents
  model is not a foreground runner and grants no generic agent bus, adapter
  process execution, provider/model call, shell/subprocess execution, Git
  mutation, raw transcript persistence, or background autonomy.
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
