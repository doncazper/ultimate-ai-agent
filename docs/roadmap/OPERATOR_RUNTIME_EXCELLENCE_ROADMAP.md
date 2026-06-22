# Operator Runtime Excellence Roadmap

Status: Active product/runtime excellence plan.

This plan is a repo-owned execution artifact for bringing Ultimate AI Agent to
credible parity with mature local operator-console systems, then moving beyond
them through a stronger foundation, cleaner structure, lower latency, tighter
security, and more durable local operation.

This plan does not grant production authority. It does not add runtime model
calls, shell/subprocess execution, unrestricted network access, browser
automation, plugin execution, mobile sensor access, connector writes, public
distribution, or broad autonomy by itself. Any item that needs those powers must
use a scoped milestone with authority boundary, risk ceiling, approval model,
persistence model, test plan, verifier updates, and rollback plan.

## Strategic Position

Mature peer operator consoles are ahead as shipped products: broader UI,
gateway runtime, durable workflows, code workbenches, integrations, release
evidence, packaging, and public security posture.

Ultimate AI Agent is ahead as a governed Python core: stricter contracts,
safe-ref discipline, exact approval boundaries, milestone gates, OpenAPI
discipline, and a sharper M160-M167 local model production-readiness lane.

The goal is not to clone a peer console. The goal is to build the better
architecture:

- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- PolicyEngine and LocalApprovalAuthority remain hard boundaries.
- Runtime authority is opt-in, exact-scope, redacted, replay-safe, revocable,
  and test-bound.
- Product surfaces expose operational truth instead of hiding state.
- Performance and durability are first-class release gates, not cleanup tasks.

Product decision: UAA is a two-layer product architecture. The governance
kernel is the automated guardrail layer: it owns contracts, policy, approvals,
route authority, redaction, audit, receipts, replay, rollback, and release
evidence. The operator shell is the developer/user cockpit: it makes those
guardrails usable through clear workflows for runtime health, local models,
plans, approvals, files, evidence, observability, settings, and release
readiness. UAA should compete with mature operator consoles by building both
layers together, but runtime authority still flows only through scoped,
evidence-backed guardrails. Until the first full local operator loop is usable
end to end, product loop completion has priority over additional roadmap-only
expansion.

## Excellence Targets

| Pillar | Peer Strength | UAA Excellence Target |
|---|---|---|
| Product shell | Full Mission Control surface | Leaner operator shell with fewer but deeper truth surfaces |
| Runtime gateway | Broad Fastify gateway | Typed FastAPI gateway with stable OpenAPI, side-effect classes, and hard policy gates |
| Local models | Provider/local runtime support | Exact-approved GGUF acquisition, llama.cpp lifecycle, OpenWebUI E2E, tuning, and M166/M167 evidence gates |
| Durable work | Durable runs and replay proof | Simpler append-first local run spine with idempotency, restart recovery, receipt hashes, and rollback |
| Code/workspace | Governed Code Mode | Safer local workspace workbench before shell, with atomic patching and rollback by default |
| Memory | Operator-visible lifecycle | Source-prioritized recall, no hidden prompt injection, explicit write policy, and decay/dedupe evidence |
| Security | Public policy and many tests | More formal authority map, redaction invariants, route side-effect classes, and security-lane gates |
| Performance | Product verification lanes | p50/p95 budget gates for API, planning, file preview, local model, and UI smoke paths |
| Packaging | Docker and Windows installers | Reproducible loopback-first local stack, signed-release path later, no trust claims without proof |
| Ecosystem | MCP, skills, extensions | Manifest-first skill/plugin ecosystem with no runtime import until explicitly approved |

## Accepted Catch-Up Recommendations

These recommendations are accepted into the roadmap as task-shaping guidance.
They do not mark the capability shipped and do not grant new authority.

| Recommendation | Roadmap task(s) | Priority | Gate |
|---|---|---|---|
| Decide product posture | `UAA-STRAT-001` Two-layer architecture: governance kernel plus operator cockpit | P0 | README/product truth/roadmap wording remains consistent and says guardrails allow scoped product actions only through policy, approval, audit, rollback, redaction, and verifier gates |
| Preserve the first readable operator-loop baseline before broadening product surfaces | `UAA-P1-011` Done: task decomposition operator loop baseline | P0 | Runtime health, local model readiness, UAA `/v1` chat, plan creation, one safe approval, receipt/audit/latency/rollback inspection are covered without hidden authority |
| Promote a Today-spine, memory-first private beta path | `UAA-P1-067` Done: Today-Spine Founder Command Center beta-readiness planning/currentness path; `UAA-P1-068` Done: Today Product Spine Contract; `UAA-P1-069` Done: Evidence History Grammar; `UAA-P1-070` Done: Memory Source And Provenance Model; `UAA-P1-071` Done: Memory Review Decision Capture; `UAA-P1-072` Done: Business Memory And Memory Quality Controls; `UAA-P1-073` Done: Plans To Reviewable Action Envelopes; `UAA-P1-074` Ready Next: Chat Local Operator Surface; then `UAA-P1-075` through `UAA-P1-078` for governed Code workbench, loop binding, and beta-readiness evidence | P0 | Today becomes the product spine; every module feeds Today, Actions, Evidence, and Memory. Memory becomes the product differentiator only after the loop has reviewable evidence, action envelopes, safe source refs from ChatGPT/manual review/local coding/calendar/email metadata, no hidden prompt injection, no raw private content, and no public beta or connector authority claim |
| Reconcile Founder Command Center planning before the next UI pass | `UAA-P1-065` Done: Founder Command Center review/cleanup lane | P0/P1 | The subordinate FCC board is classified, stale sequencing is removed, and exactly one later UI/readability task is promoted without adding routes, frontend implementation, connector runtime, setup mutation, model/provider calls, or runtime authority |
| Split the API into clearer service modules | `UAA-P1-021` FastAPI route grouping and side-effect classes, `UAA-P1-052` API service-module extraction plan | P1 | OpenAPI path count, operation IDs, route side-effect classes, auth posture, and API manifest remain unchanged or intentionally updated with tests |
| Harden the browser-facing API perimeter before new authority | `UAA-P1-080` through `UAA-P1-086` planned: route classification, security headers, loopback CORS, local auth gate, idempotency audit, targeted rate limits, and OpenAPI/API manifest enforcement | P1 | Control Center remains local-first while every route gets an explicit public/protected classification and sensitive or mutating paths have auth, approval, idempotency, redaction, and test posture before authority-heavy Plans, Chat, Code, loop-binding, or beta-readiness claims |
| Expand CI into named release lanes | `UAA-P1-013` Done, `UAA-P1-053` Done: CI lane workflow expansion | P1 | docs, OpenAPI, Foundation Gate, API safety, frontend, security/redaction, local model, durability, performance, and packaging lanes are visible in CI without unsafe artifact leakage |
| Add product-grade Control Center screens for UAA differentiators | `UAA-P1-054` Done: Control Center differentiator screens | P1 | route authority, approval state, receipts/evidence, safe workspace previews, local model status, and observability timeline are readable surfaces, not raw JSON |
| Preserve UAA's stricter authority model | `UAA-P1-020` PolicyEngine consolidation map | P0/P1 | No copied peer runtime feature ships without exact policy, approval, audit, rollback, and redaction gates |
| Add automated security scanning and artifact redaction checks | `UAA-P1-055` Done: security automation and artifact redaction lane | P1 | Security scans and artifact checks are safe, local/CI bounded, and do not claim external audit or public distribution |
| Add governed local model switching only after cleanup and status truth | `UAA-P1-062` Done: Local Model Manager / Memory-Aware Runtime Control lane shape; `UAA-P1-064` Done: read-only local model inventory backend + CLI; `UAA-P1-066` queued: read-only Control Center inventory/status only | P1 | Python Agent Core owns discovery, memory-fit planning, llama.cpp lifecycle, switch receipts, and rollback; Control Center and OpenWebUI remain shells over approved backend state. Runtime stages remain blocked until later exact scoped milestones. UAA-P1-066 supports the memory-first product path but does not displace it. |
| Productize extension boundary carefully | `UAA-P2-048` Static package review, `UAA-P2-056` Extension trust product surface | P2 | Trust/provenance inspection improves before plugin execution exists; runtime import remains disabled |
| Treat installer/release workflows as catch-up after local loop usability | `UAA-P2-047` Signed installer and public distribution lane shaping | P2 | No signed/public distribution claim until local loop, security, durability, and artifact proof gates are green |
| Preserve blocked/scoped/planned truthfulness | `UAA-P1-031` Done, `UAA-P1-057` Done, `UAA-P1-060` Done, `UAA-P1-061` Done | P0/P1 | Planned, blocked, skipped, mock, and not-scoped work cannot be described as complete or production-ready; readiness language maps through a shared taxonomy and reconciliation artifacts |

## Non-Negotiable Invariants

- No raw prompt, raw response, raw provider payload, raw path, raw log, username,
  hostname, serial, environment dump, or credential material in durable evidence.
- No OpenWebUI authority over UAA. OpenWebUI remains a supported local/dev
  conversational shell and compatibility surface, not the destination for
  wiring every product workflow.
- Control Center / Founder Command Center is the proprietary primary product
  UI for Today, Inbox, Plans, Actions, Memory, Evidence, Settings, Models, and
  first-party Chat. Product state must land there through Python Agent Core
  contracts, not in OpenWebUI-owned state.
- No model/provider output as production authority by itself.
- No tool, shell, network, browser, plugin, connector, mobile, or remote action
  without reviewed capability scope and exact approval where required.
- No bypass around PolicyEngine, LocalApprovalAuthority, route side-effect
  classification, OpenAPI checks, or Foundation Gate checks.
- Browser-facing API perimeter hardening is required before new authority-heavy
  Control Center workflows: route classification, security headers, loopback
  CORS, local auth, idempotency, rate-limit posture, and enforcement tests must
  be explicit.
- Every mutating API route or local mutation path must require an idempotency key
  or scoped idempotency ref, plus audit, rollback, and test evidence.
- Every product claim must be backed by source, tests, docs, or release evidence.

## Program Milestones

### M168 - Currentness and Product Truth

Goal: make the repo tell one current story.

Tasks:

- `UAA-P0-001` Repair README/version/current-baseline truth across M150-M167.
- `UAA-P0-002` Add repo-owned product gap and excellence matrix in
  `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.
- `UAA-P0-008` Update docs index/canonical map for M160-M167 and this roadmap.
- `UAA-P0-009` Make OpenAPI path count and API manifest current.
- `UAA-P0-010` Add verifier rule for stale active-board labels.

Acceptance:

- Current baseline, latest checkpoint tags, README status, roadmap status, and
  OpenAPI route count do not contradict each other.
- External benchmark and peer-console context is recorded as product-shaping
  evidence only, not as a product dependency, implementation dependency,
  authority source, or implementation template.
- Documentation integrity and OpenAPI checks pass.

Verification:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
```

### M169 - Public Trust and Security Package

Goal: match and improve on the public trust posture expected from mature local
operator products.

Tasks:

- `UAA-P0-003` Add `SECURITY.md` with supported lines, private reporting path,
  severity definitions, response targets, and invariants.
- `UAA-P0-011` Add security triage runbook for secret scanning, dependency
  alerts, unsafe logging, route auth, and redaction regressions.
- `UAA-P0-012` Add static checks for raw prompt/provider payload/path/log
  language in release-facing docs.
- `UAA-P0-013` Add API safe-error and no-secret-output regression tests to the
  required verification lane.
- `UAA-P0-014` Add rate-limit posture to mutating local-dev routes.

Acceptance:

- External reporters can understand how to report vulnerabilities.
- Maintainers have a repeatable triage process.
- Safe exception messages, redaction, and no-raw evidence checks are tested.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_safe_exception_messages.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_secret_broker_redaction.py
.venv/bin/python scripts/verify_all.py --skip-ruff --skip-pytest
```

### M170 - Local Model Product Loop

Goal: convert the M160-M167 local model lane into the first visible product loop
where UAA is strongest on local model safety and operational clarity.

Tasks:

- `UAA-P0-004` Build the M167 live evidence matrix with safe refs, reviewer refs,
  hardware profiles, blockers, and status in
  `docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md`.
- `UAA-P0-005` Add local model E2E smoke harness over approved GGUF, llama.cpp,
  local `/v1/models`, local `/v1/chat/completions`, and OpenWebUI shell in
  `docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md`.
- `UAA-P0-015` Add installer/runtime packaging checklist for llama-server
  discovery, provenance, checksum/signature review, rollback, and offline mode
  in `docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md`.
- `UAA-P0-016` Add tuning advisor hardening cases for lag, OOM, crash loop,
  reload loop, slow tokens per second, and one-change rollback.
- `UAA-P0-017` Add local model operator runbook for cache cleanup, corrupted
  GGUF, stuck download, port conflict, credential rotation, rollback, offline
  mode, safe evidence collection, blocked/unknown model state, and safe-disable
  in `docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md`.
- `UAA-P1-062` Done: shape the Local Model Manager / Memory-Aware Runtime Control
  lane after cleanup and status truth. The staged order is cleanup and
  consolidation; read-only model status; approval-bound start/stop for the
  current server; dry-run switch planning with RAM/VRAM/context impact,
  one-big-model enforcement, expected alias, and rollback plan; executable
  switch with `/health` and `/v1/models` verification, UAA/OpenWebUI identity
  receipt, and redacted evidence; then model downloads/acquisition only after
  switching is solid.
- The exact-scoped Local Model Manager sequence now has UAA-P1-064 completed
  for read-only inventory over consolidated local roots and CLI-first
  `uaa local-model status/list/inspect`. UAA-P1-066 remains queued for
  read-only Control Center status only and supports, but does not supersede,
  the memory-first product beta-readiness path. Later stages still require separate
  exact scoped milestones: GGUF-only
  `llama-server --models-dir <approved-gguf-cache-ref> --models-max 1`
  planning, dry-run switch planning, approval-bound switch, Desktop/Hermes UI
  activation only after CLI/API safety, and MLX/Ollama/LM Studio adapters.
- `UAA-P1-064` Done: implements only the read-only Python Agent Core inventory
  and CLI inspection slice from that sequence. This milestone excludes
  lifecycle control, switching, downloads, route/OpenAPI authority, Control
  Center activation controls, model/provider calls, and runtime adapters.
- `UAA-P1-066` Queued support lane: promote a strictly read-only Control
  Center model inventory/status surface over UAA-P1-064 Python-core inventory
  and CLI inspection. This milestone must not add lifecycle control, switching,
  start/stop/activate/unload behavior, Desktop/Hermes activation, downloads,
  runtime adapter execution, React-owned model truth, raw local path evidence,
  or production-readiness claims.

Acceptance:

- OpenWebUI can be tested as a shell against UAA's local `/v1` gateway.
- Tools/functions and streaming remain denied unless separately scoped later.
- All evidence is redacted summary only and safe-ref only.
- M166 authority remains exact-bound to local llama.cpp/OpenWebUI shell scope.
- For `UAA-P1-062`, Control Center/OpenWebUI are never the authority: Python
  Agent Core owns installed-model discovery, memory-fit planning, lifecycle
  state, model-switch receipts, identity updates, safe-disable, and rollback.
- `UAA-P1-062` does not ship until CLI parity, route side-effect classes,
  exact approval requirements, redacted evidence, rollback/safe-disable
  behavior, and verifier coverage are accepted for each staged capability.
- `UAA-P1-062` shape evidence is
  `docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md`; later
  implementation stages require separate documented scope.
- `UAA-P1-064` implementation evidence is
  `docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md`; it is
  accepted only for read-only inventory and CLI inspection.
- `UAA-P1-066` scope evidence is
  `docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md`;
  it is accepted only for the next read-only Control Center inventory/status
  milestone and does not grant lifecycle, switch, download, or runtime adapter
  authority.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m166_production_release_gate.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m167_live_model_hardening.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_m151_openwebui_local_gateway_api.py
```

### M171 - Durable Local Runtime Spine

Goal: add the minimal durable state model needed for reliable operator work
without creating a sprawling runtime.

Tasks:

- `UAA-P1-010` Done: define durable run records, run states, transitions,
  idempotency keys, audit refs, receipt refs, replay refs, rollback refs,
  restart recovery, checksum snapshot validation, and safety tests.
- `UAA-P1-025` Done: implement append-first local storage for runs and receipt
  summaries with atomic writes and corruption detection.
- `UAA-P1-026` Done: add pause, resume, cancel, retry, dead-letter, and
  restart recovery contracts.
- `UAA-P1-027` Done: bind task decomposition runs to durable run records,
  approval refs, receipt refs, replay validation, restart visibility, and
  explicit idempotency replay denial.
- `UAA-P1-028` Done: define backup minimum set, verification checks, rollback,
  and offline/operator-run restore plan.
- `UAA-P1-029` Done: add replay-safe receipt hashing for mutating local paths.

Acceptance:

- A local task run can survive process restart without losing run truth.
- Duplicate mutation attempts are blocked by idempotency keys.
- Receipt hashes support replay validation without exposing private runtime
  content.
- Restore is offline/operator-run until a later scoped milestone proves live
  restore safety.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_execution_state_machine_safety.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_ledger_append_only.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_atomic_writes.py
```

### M172 - Control Center Operator Shell v1

Goal: build a focused set of surfaces and make each one operationally truthful,
fast, and inspectable.

UI surface direction: Control Center / Founder Command Center is the
first-party product cockpit. OpenWebUI remains useful as a local/dev
conversational shell for `/v1` smoke, llama.cpp compatibility, and developer
chat, but it is not the product cockpit and is not the surface where all UAA
product workflows should be wired.

Required surfaces:

- Chat Shell: first-party Control Center chat operator surface with
  model/runtime/auth/tool-denial truth; OpenWebUI remains a separate local/dev
  shell over the same governed gateway.
- Plans: task decomposition, approval needs, DAG status, and safe execution.
- Models: GGUF search, acquisition status, llama.cpp status, tuning, and rollback.
- Approvals: exact-scope pending approvals, grant capture, revoke, and audit.
- Files: safe refs, bounded preview, diff proposal, atomic apply, rollback.
- Runtime: health, latency, queue, local model status, storage status.
- Evidence: receipts, audit summaries, verifier reports, and release proof.
- Settings: loopback/auth tokens, feature flags, safe defaults, kill switches.

Tasks:

- `UAA-P0-007` Map each surface to current routes and missing routes in
  `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`.
- `UAA-P1-011` Done baseline: preserve the first readable operator-loop proof
  chain through Control Center: inspect runtime health, inspect local model
  readiness, chat through UAA `/v1`, create a task decomposition plan, approve
  one safe registered capability, inspect receipt/audit/latency/rollback
  status, and preserve durable run truth.
- `UAA-P1-030` Done: add route status manifest for visible surface readiness in
  `docs/control_center/ROUTE_STATUS_MANIFEST.md`.
- `UAA-P1-031` Done: add enforceable product language rules in
  `docs/control_center/PRODUCT_LANGUAGE_RULES.md` for no hidden authority, no
  fake completion, no raw JSON as the primary UI for operator-critical flows,
  no unsupported production/public distribution claims, no model/provider output
  as authority, and no completed-state language for blocked/skipped/pending work.
- `UAA-P1-032` Done: add browser smoke readiness for the first product loop in
  `docs/control_center/LOCAL_BROWSER_SMOKE.md`,
  `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`, and
  `apps/control-center/src/App.test.tsx` with real/mocked/skipped/blocked
  states and explicit blockers for missing prerequisites.
- `UAA-P1-033` Done: add accessible loading/error/empty/blocked/denied
  operator states for Chat Shell, Plans, Models, Approvals, Files, Runtime,
  Evidence, and Settings in `apps/control-center/src/components/OperatorSurfaceStates.tsx`,
  `apps/control-center/src/routes.tsx`, `apps/control-center/src/App.test.tsx`,
  and `scripts/verify_control_center_frontend.py`.
- `UAA-P1-054` Done: added product-grade Control Center differentiator screens for
  route authority, approval state, evidence receipts, safe workspace previews,
  local model status, and an observability timeline over M167 safe summaries.
- `UAA-P1-065` Done: reconciled the Founder Command Center board against
  completed and review-ready slices, removed stale sequencing, classified FCC
  cards, and promoted exactly one later task: FCC-P0-002 Follow-Up
  Collapse/Organize Control Center Around Core Surfaces. The pass adds no
  routes, Control Center implementation, connector runtime, setup mutation,
  model/provider calls, or runtime authority.

Acceptance:

- A user can complete the first product loop without reading raw API payloads:
  select local model, run local shell smoke, create plan, approve safe handler,
  inspect receipt, and rollback a local file proposal.
- The loop distinguishes real, mocked, skipped, blocked, and denied states and
  does not imply completion or authority for missing prerequisites.
- Every visible action maps to route authority and side-effect class.
- Product language rules are documented and statically checked for
  Control Center and release-facing copy where practical.
- Browser smoke coverage opens the shell, verifies safe readable UI states for
  the first product loop, and reports blocked prerequisites without hidden
  authority or raw JSON primary UI.
- Loading, error, empty, blocked, and denied states are accessible,
  operator-actionable, and distinct from product readiness or authority claims.

Verification:

```bash
make frontend-check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
```

### M172.1 - Today-Spine Founder Command Center Beta-Readiness Path

Goal: make Today the product spine and make robust reviewed memory the product
differentiator for a private local beta-test candidate. Every module must feed
Today, Actions, Evidence, and Memory. Chat, Plans, Code, and Evidence are not
standalone-complete modules; they are complete only when their outputs land in
the governed daily loop with safe refs, review decisions, action envelopes,
rollback posture, and human-readable history.

Tasks:

- `UAA-P1-067` Done: define the Today-spine, memory-first Founder Command
  Center beta-readiness path, promote product-loop sequencing ahead of broad
  surface expansion, and record the milestone conveyor. This is
  planning/currentness only and grants no runtime authority.
- `UAA-P1-068` Done: Today product spine contract: define the shared loop
  contract every module must feed: Today, Actions, Evidence, and Memory. Today
  shows current priorities, blockers, follow-ups, plan/action state, memory
  review count, stale-source posture, and next safe actions. Loop visibility is
  necessary but not sufficient for completion; normal Definition of Done,
  redaction, policy/approval, route, CLI/repo-local inspection, and test gates
  still apply.
- `UAA-P1-069` Done: Evidence history grammar: make Evidence read like history:
  what was proposed, what was approved, what happened, what changed, what can
  be undone, what is stale, and what remains blocked. This grammar is now the
  receipt language for Memory, Plans, Chat, Code, and Actions.
- `UAA-P1-070` Done: Memory source and provenance model: define safe source refs for
  manual notes, ChatGPT/exported review summaries, local chat turns, local
  coding session summaries, task plans, action proposals, evidence timeline
  refs, read-only calendar/email metadata, and CRM-lite business records. Raw
  prompts, raw responses, raw provider payloads, raw paths, raw logs, account
  identifiers, and raw private content remain denied in durable evidence.
- `UAA-P1-071` Done: Memory Review decision capture: add exact reviewed states for
  accept, correct, reject, defer, merge, supersede, and forget-request posture
  before any memory candidate becomes recall. Decisions need actor refs,
  source refs, provenance refs, evidence refs, stale-state posture, retention
  posture, audit refs, receipt refs, blocked-state refs, source provenance
  binding, and review-only denied authority flags.
- `UAA-P1-072` Done: Business memory and memory quality controls: add profile, project,
  relationship, organization, deal/opportunity, promise, follow-up, decision,
  preference, and commitment candidate kinds with provenance, review posture,
  dedupe, conflict, stale/expired, low-confidence, source-missing, and
  evidence-missing posture. External CRM writes and account sync remain out of
  scope.
- `UAA-P1-073` Done: Plans to reviewable Action envelopes: Plans produce
  approve/edit/reject/defer-ready Action envelopes with exact scope,
  side-effect class, risk, approval requirement, idempotency, expiry,
  evidence refs, expected receipt refs, rollback/safe-disable posture, and
  blocked-state reasons. Classification/decomposition alone is not enough.
- `UAA-P1-074` Ready Next: First-party Control Center chat local operator surface: Chat
  must send a local turn through the governed local gateway, show
  model/runtime/auth/tool-denial truth, produce safe evidence, and hand off to
  Plans or Actions without treating model output as authority, truth, memory,
  or execution permission. OpenWebUI remains a secondary local/dev shell, not
  the source of product state.
- `UAA-P1-075` Governed Code workbench v1: Code should be narrower than Goat
  but better governed: repo-local safe diffs, validation proof, exact approval
  before apply, atomic apply, rollback receipts, and evidence timeline binding.
  Broad coding-agent autonomy, unrestricted shell, and remote execution remain
  blocked.
- `UAA-P1-076` Cross-surface memory intake: bind safe memory candidates from
  Today, Chat, Plans, Actions, Evidence, local coding summaries, and manual
  external-assistant review imports. This is intake/proposal only; it must not
  call providers, fetch accounts, import browser state, read shell history, or
  inject context.
- `UAA-P1-077` Memory-to-loop binding: Today, Action Inbox, Evidence Timeline,
  and Weekly CEO Review must show memory candidates, accepted recall refs,
  corrections, rejected items, follow-up commitments, and missing-evidence
  blockers in human-readable form.
- `UAA-P1-078` Private beta-readiness gate: define local/private beta-test
  acceptance evidence for Morning Briefing, Action Inbox, Memory Review,
  Evidence Timeline, safe local Chat/Plans handoff, governed Code diffs, and
  CRM-lite follow-ups. This gate is not public beta, public distribution,
  production readiness, or broad autonomy.
- `UAA-P1-079` Later intent understanding v1: only after the above loop has
  reviewed memory, evidence history, action envelopes, and Chat/Code receipts,
  add a reviewable intent classifier that proposes user intent with confidence,
  source refs, ambiguity posture, and ask/act/defer routing. It must not become
  hidden authority or broad autonomy.
- API Boundary Hardening Lane, planned/queued before authority-heavy claims from
  Plans, Chat, Code, loop binding, or private beta-readiness:
  `UAA-P1-080` API route classification and public/protected inventory;
  `UAA-P1-081` centralized FastAPI security headers;
  `UAA-P1-082` explicit loopback CORS allowlist;
  `UAA-P1-083` simple local bearer/session gate for sensitive routes;
  `UAA-P1-084` mutating-route idempotency enforcement audit;
  `UAA-P1-085` targeted rate limits for expensive/sensitive routes; and
  `UAA-P1-086` OpenAPI/API manifest/route inventory enforcement tests. This
  lane is planning only until implemented and does not add middleware, auth,
  CORS, headers, dependencies, or runtime authority.

Acceptance:

- Today is the product spine; module completion means the module feeds Today,
  Actions, Evidence, and Memory with safe refs and human-readable state.
- Authority-heavy product claims for Plans, Chat, Code, loop binding, and
  private beta-readiness must either pass the UAA-P1-080 through UAA-P1-086 API
  boundary gates or explicitly remain blocked on missing perimeter controls.
- Evidence reads as narrative history, not compliance paperwork.
- Memory is reviewable product state, not hidden prompt stuffing.
- Plans produce reviewable Action envelopes with approve/edit/reject/defer
  posture, exact scope, receipts, and rollback/safe-disable posture.
- Chat shows local model/runtime/auth/tool-denial truth, produces evidence, and
  hands off to Plans or Actions without granting authority.
- Code work stays repo-local and governed by safe diffs, validation proof,
  approval-bound apply, rollback, and evidence.
- A user can import or summarize external assistant review output as safe
  memory candidates without treating external output as truth or authority.
- Local coding and Chat surfaces can create memory proposals with source/evidence
  refs, but cannot write memory automatically or inject it into context.
- Business memory supports people, organizations, projects, opportunities,
  promises, follow-ups, preferences, decisions, and stale-state posture.
- Every accepted memory has provenance, evidence, review decision, retention
  posture, correction path, deletion/export posture, and audit/receipt refs.
- Private beta readiness requires completed local workflows and safe evidence;
  public beta, account sync, connector writes, provider authority, browser
  automation, unrestricted shell, remote execution, and production authority
  remain blocked.

Verification:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_founder_loop_api.py
make frontend-check
```

### M172.5 - API Service Boundaries and Route Modularity

Goal: split API organization into clearer service modules as UAA grows while
preserving the current OpenAPI contract, operation IDs, side-effect classes,
auth posture, and API manifest truth.

Tasks:

- `UAA-P1-021` FastAPI route grouping and side-effect classes.
- `UAA-P1-052` Define an API service-module extraction plan for health,
  manifest, local model gateway, task decomposition, workspace files,
  approvals, evidence/receipts, observability, extensions, and release
  verification routes.
- `UAA-P1-058` Extract one low-risk read-only route group as the first module
  without changing path behavior, auth posture, side-effect classification, or
  OpenAPI operation IDs.
- `UAA-P1-059` Add route-module ownership tests so future route additions
  declare owner, service module, side-effect class, risk, auth posture,
  evidence behavior, and release status.

Acceptance:

- The API becomes easier to navigate without route-contract drift.
- `/api/manifest`, OpenAPI, route inventory, and Control Center route manifest
  continue to agree.
- Refactors do not add runtime authority or broaden side effects.

Verification:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
```

### M173 - Safer Workspace Workbench

Goal: sequence safety before shell execution and make local workspace mutation
reversible by default.

Tasks:

- `UAA-P1-012` Build file tree safe refs and bounded previews.
- `UAA-P1-034` Add patch proposal contracts with exact file/path binding.
- `UAA-P1-035` Add atomic apply and rollback receipts.
- `UAA-P1-036` Add secret-like diff blocking and redacted preview.
- `UAA-P1-037` Add approval-bound mutation only; no shell execution.
- `UAA-P2-038` Shape future shell/subprocess lane separately after M171-M173 are
  green.

Acceptance:

- UAA can safely review and apply local patches with rollback evidence before
  any shell/code-execution authority exists.
- All file writes are exact-approved, idempotent, audit-bound, and reversible.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_write_proposals.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_rollback.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_file_secret_blocking.py
```

### M174 - Performance and Latency Gate

Goal: make speed a release blocker.

Tasks:

- `UAA-P0-006` Done: add p50/p95 timing harness with budget definitions and
  latest safe reports under `reports/performance`; canonical doc is
  `docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md`.
- `UAA-P1-039` Done: enforce latency budget gate coverage for API manifest,
  model route preview, task decomposition, file preview, local model list,
  local chat, and an explicit safe skipped dashboard render row.
- `UAA-P1-040` Done: add machine-readable and human-readable performance
  regression reports under `reports/performance` with safe environment summary,
  budget comparisons, skipped/blocked status, and retention guidance.
- `UAA-P1-041` Done: add safe hot-path profiling for task decomposition and
  OpenAPI build with timing-summary-only JSON and Markdown reports.
- `UAA-P1-042` Done: cache safe static API manifest data without caching
  authority decisions, approvals, policy outcomes, user data, mutable state, or
  secrets; canonical doc is `docs/api/SAFE_STATIC_MANIFEST_CACHING.md`.
- `UAA-P1-043` Done: add typed Foundation Gate `latency_gate` report output
  with p50/p95 status, pass/fail/skipped path state, accepted failures, report
  refs, optional prerequisite visibility, and environment-safe summary.

Initial budgets:

| Path | Local target |
|---|---:|
| `/health` | p95 under 50 ms |
| `/api/manifest` | p95 under 150 ms |
| `/models/route/preview` | p95 under 150 ms |
| `/task-decomposition/classify` | p95 under 100 ms |
| `/task-decomposition/decompose` | p95 under 250 ms |
| `/files/read/preview` bounded text | p95 under 150 ms |
| `/v1/models` local gateway | p95 under 100 ms |
| `/v1/chat/completions` local path | p95 under 250 ms |
| Control Center first useful local render | p95 under 1500 ms |

Acceptance:

- Every release candidate reports latency budgets.
- Authority decisions are never skipped for speed.
- Cache invalidation is explicit and tested.

Verification:

```bash
.venv/bin/python scripts/benchmark_foundation_gate.py
.venv/bin/python scripts/check_foundation_gate_latency.py
```

### M175 - Release, Packaging, and Recovery Proof

Goal: match mature release discipline without overclaiming distribution.

Tasks:

- `UAA-P1-013` Done: add named release verification lanes for docs, OpenAPI,
  API safety, security/redaction, local model E2E, durability, frontend, and
  performance with pass/fail/skipped/blocked/accepted-failure semantics;
  canonical doc is `docs/production/RELEASE_VERIFICATION_LANES.md`.
- `UAA-P1-014` Done: add Docker/local runtime packaging with loopback-only
  defaults, generated local secret refs, rollback instructions, and no public
  distribution or signed-installer claim; canonical doc is
  `docs/production/LOCAL_RUNTIME_PACKAGING.md`.
- `UAA-P1-044` Done: add release evidence packet format with commit refs,
  verification lanes, report refs, accepted failures, artifact hashes, rollback
  notes, non-goals, release blockers, and static validation; canonical doc is
  `docs/production/RELEASE_EVIDENCE_PACKET.md`.
- `UAA-P1-045` Done: add backup/restore verification for the UAA-P1-028
  minimum local state set with synthetic safe refs, SHA-256 integrity checks,
  offline restore validation, corruption detection, and no live restore claim;
  canonical doc is `docs/production/BACKUP_RESTORE_VERIFICATION.md`.
- `UAA-P1-046` Done: add local state rollback runbook for local model cache,
  settings, registry, approvals, audit state, and run/receipt state with
  backup-before-rollback, safe-disable, backup restore, unsupported recovery,
  and redacted evidence guidance; canonical doc is
  `docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md`.
- `UAA-P1-053` Done: expanded CI workflow posture around the named release lanes:
  docs, OpenAPI, Foundation Gate, API safety, frontend, security/redaction,
  local model, durability, performance, and packaging. This should wire lane
  visibility and safe reports, not weaken or skip lane checks.
- `UAA-P1-055` Done: added automated security scanning and release artifact
  redaction checks. Reports must be safe for release evidence and must not claim
  external audit, signed release, hosted production support, or public
  distribution.
- `UAA-P2-047` Shape signed installer and public distribution lane only after
  local loop, security, and durability gates are green.

Acceptance:

- A local release candidate can produce redacted verification evidence for the
  backup minimum set, synthetic offline restore, and rollback plan without
  claiming live restore or populated real-state restore safety.
- Public distribution remains unclaimed until signed artifact proof exists.
- Security automation and artifact checks are additional evidence lanes, not
  substitutes for existing redaction, OpenAPI, Foundation Gate, or pytest lanes.

Verification:

```bash
.venv/bin/python scripts/verify_all.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

### M176 - Ecosystem and Extension Boundary

Goal: make extension trust visible and non-magical before broad plugin runtime
authority exists.

Tasks:

- `UAA-P1-024` Done: define plugin/skill manifest trust schema and ecosystem
  boundary before runtime import, including package identity, provenance,
  per-file hashes, declared capabilities, risk class, requested grants,
  exact-scope activation records, revocation behavior, audit refs, inspectable
  catalog separation, and no callable/runtime catalog claim; canonical doc is
  `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`; canonical schema is
  `docs/schemas/plugin_skill_trust_manifest.schema.json`.
- `UAA-P2-048` Add static package review with provenance and per-file hashes.
- `UAA-P2-049` Done: add read-only inspectable catalog route/model/schema
  separate from any callable catalog; canonical doc is
  `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`; canonical schema is
  `docs/schemas/inspectable_extension_catalog.schema.json`; canonical API is
  `GET /extensions/catalog`.
- `UAA-P2-050` Done: add exact-scope activation and revocation record
  contracts without runtime import or execution; canonical doc is
  `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`; canonical schema is
  `docs/schemas/extension_activation_grant.schema.json`.
- `UAA-P2-051` Done: add MCP/A2A compatibility watchlist without runtime
  authority, connector writes, plugin execution, broad tool invocation, or
  network authority; canonical doc is
  `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`.
- `UAA-P2-056` Add an extension trust product surface that displays static
  package review status, provenance, per-file hash refs, declared capabilities,
  requested grants, activation/revocation state, blocked/unknown status, and
  risk flags without enabling runtime import or execution.

Acceptance:

- Users can inspect extension capabilities before activation.
- Runtime import remains disabled by default.
- Activation is exact-scope, revocable, and audit-bound.

### M177 - Product Truth Regression and Honest Readiness

Goal: preserve UAA's strongest differentiator: the repo stays honest about
what is shipped, blocked, scoped, planned, skipped, mocked, and not
production-ready.

Tasks:

- `UAA-P1-057` Done: add product truth regression checks for release-facing docs and
  Control Center copy so blocked, skipped, pending, mock-only, planned, and
  not-scoped states cannot be described as complete, production-ready, or
  publicly released without evidence.
- `UAA-P1-060` Done: add an operator-readiness status taxonomy shared by docs,
  route manifests, Control Center states, release evidence packets, and
  Foundation Gate summaries.
- `UAA-P1-061` Done: add a morning reconciliation report template check for looped
  work sessions so completed, deferred, rejected, and blocked recommendations
  are traceable to evidence refs.

Acceptance:

- Product-facing claims remain evidence-backed.
- No peer comparison, prompt loop, generated report, or Control Center surface
  can silently upgrade blocked/planned work to shipped readiness language.
- The Operator Excellence loop produces reviewable reconciliation artifacts
  instead of autonomous, unbounded change batches.

Verification:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_all.py --skip-ruff --skip-pytest
```

## ASAP Task List

### First 48 Hours

- `UAA-P0-001` Done: repair baseline/currentness.
- `UAA-P0-002` Done: land product release-truth packet.
- `UAA-P0-003` Done: add public security posture.
- `UAA-P0-004` Done: create M167 evidence matrix skeleton.
- `UAA-P0-005` Done: add local model E2E smoke harness.
- `UAA-P0-006` Done: add first performance budget harness.

### First Week

- `UAA-P0-007` Done: Control Center operator-shell gap map.
- `UAA-P0-015` Done: llama-server packaging/provenance checklist.
- `UAA-P0-016` Done: tuning advisor hardening cases.
- `UAA-P0-017` Done: Local model operational runbook.

### Weeks 2-3

- `UAA-P1-010` Done: durable run spine spec and tests.
- `UAA-P1-025` Done: append-first local run storage.
- `UAA-P1-026` Done: durable run lifecycle contracts.
- `UAA-P1-027` Done: task decomposition to durable run binding.
- `UAA-P1-028` Done: backup/verify/offline restore plan.
- `UAA-P1-029` Done: replay-safe receipt hashing for mutating local paths.
- `UAA-P1-030` Done: visible route status manifest.
- `UAA-P1-031` Done: product language rules.
- `UAA-P1-032` Done: browser smoke readiness for first product loop.
- `UAA-P1-033` Done: accessible loading/error/empty/blocked/denied states for
  eight Control Center operator surfaces.

### Weeks 4-6

- `UAA-P1-012` Workspace workbench safe refs and previews.
- `UAA-P1-034` Patch proposal contracts.
- `UAA-P1-035` Atomic apply and rollback receipts.
- `UAA-P1-039` Done: Latency budget gate.
- `UAA-P1-040` Done: Performance regression reports.
- `UAA-P1-041` Done: Hot-path profiling.
- `UAA-P1-042` Done: Safe static manifest caching.
- `UAA-P1-013` Done: Release verification lanes.
- `UAA-P1-014` Done: Docker/local runtime packaging.
- `UAA-P1-044` Done: Release evidence packet.
- `UAA-P1-045` Done: Backup/restore verification.
- `UAA-P1-046` Done: Rollback runbook.
- `UAA-P1-024` Done: Plugin/skill ecosystem boundary.
- `UAA-P2-049` Done: Inspectable extension catalog.
- `UAA-P2-050` Done: Extension activation grant records.
- `UAA-P2-051` Done: MCP/A2A compatibility watchlist.
- `UAA-P1-011` Done baseline: first readable operator-loop proof chain exists;
  Founder Command Center work now builds readability and product surfaces on top.
- `UAA-P1-020` Done: PolicyEngine consolidation map.
- `UAA-P1-021` Done: FastAPI route grouping and side-effect classes.
- `UAA-P1-052` Done: API service-module extraction plan.
- `UAA-P1-053` Done: CI lane workflow expansion.
- `UAA-P1-054` Done: Control Center differentiator screens.
- `UAA-P1-055` Done: security automation and artifact redaction lane.
- `UAA-P1-057` Done: product truth regression checks.
- `UAA-P1-060` Done: operator-readiness status taxonomy.
- `UAA-P1-061` Done: morning reconciliation artifact check.
- `UAA-P1-067` Done: Today-spine, memory-first Founder Command Center
  beta-readiness planning/currentness path.
- `UAA-P1-068` Done: Today product spine contract for how every module feeds
  Today, Actions, Evidence, and Memory.
- `UAA-P1-069` Done: Evidence history grammar for proposed/approved/happened/
  changed/undoable/stale/blocked history.
- `UAA-P1-070` Done: memory source/provenance model for manual notes,
  external assistant review summaries, local chat/coding summaries, plans,
  actions, evidence refs, and read-only calendar/email metadata refs.
- `UAA-P1-071` Done: Memory Review decision capture for accept, correct,
  reject, defer, merge, supersede, and forget-request posture.
- `UAA-P1-072` Done: business memory and memory quality controls for CRM-lite
  candidate kinds, dedupe, conflicts, stale state, low confidence,
  source-missing, and evidence-missing posture.
- `UAA-P1-073` Done: Plans to reviewable Action envelopes with exact scope,
  approve/edit/reject/defer posture, receipts, and rollback/safe-disable state.
- `UAA-P1-074` Ready Next: first-party Control Center chat local operator surface
  with turn send, model/runtime/auth/tool-denial truth, safe evidence, and
  handoff to Plans or Actions. OpenWebUI remains a secondary local/dev shell.
- `UAA-P1-075` Shape: governed Code workbench v1 for repo-local safe diffs,
  validation proof, approval-bound apply, rollback, and evidence.
- `UAA-P1-076` Shape: cross-surface memory intake from Today, Chat, Plans,
  Actions, Evidence, local coding summaries, and manual external-assistant
  review imports.
- `UAA-P1-077` Shape: bind memory state into Today, Action Inbox, Evidence
  Timeline, and Weekly CEO Review.
- `UAA-P1-078` Shape: private beta-readiness gate for the local Founder Command
  Center loop without public beta/distribution claims.
- `UAA-P1-079` Later: user-intent understanding v1 after memory, evidence,
  Chat, Plans, Code, and Actions produce reviewable loop evidence.
- `UAA-P1-080` Planned: API route classification and public/protected inventory
  using `public_metadata`, `local_readonly`, `local_sensitive`, and
  `mutating_requires_authority`.
- `UAA-P1-081` Planned: centralized FastAPI response security headers for the
  browser-facing Control Center boundary.
- `UAA-P1-082` Planned: explicit loopback CORS allowlist for local Control
  Center origins; CORS is browser hardening, not auth.
- `UAA-P1-083` Planned: simple local bearer/session gate for sensitive routes;
  no enterprise auth, OAuth, roles, or password flow.
- `UAA-P1-084` Planned: mutating-route idempotency enforcement audit for
  idempotency keys or scoped idempotency refs.
- `UAA-P1-085` Planned: targeted rate limits for model/chat, task
  decomposition, action preview/proposal, and expensive validation paths.
- `UAA-P1-086` Planned: OpenAPI/API manifest/route inventory tests enforcing
  classification, auth, approval, idempotency, headers, CORS, and rate-limit
  posture.
- `UAA-P2-056` Shape: extension trust product surface.
- `UAA-P2-058` Shape: Provider Credential Vault Adapter v1 as a
  disabled-by-default opaque-ref adapter contract. This gate must not collect,
  store, reveal, validate, or transmit raw credential material.
- `UAA-P2-059` Shape: Provider Credential Validation v1 as a separate
  disabled-by-default validation contract with consent, policy, approval,
  revocation, redacted receipt, and no raw provider response persistence.
- `UAA-P2-060` Shape: Governed Provider Invocation v1 as a separate
  disabled-by-default invocation contract requiring PolicyEngine,
  LocalApprovalAuthority or successor approval, provider allowlists, credential
  refs, redacted summaries, receipts, audit refs, safe-disable behavior, and
  rate/budget boundaries.

## Definition of Ready

An item may enter Ready only when it has:

- exact capability/surface name
- authority boundary
- risk ceiling
- approval model
- persistence model
- redaction and audit requirements
- test plan
- verifier updates
- rollback plan
- docs impact

## Definition of Done

An item is Done only when:

- implementation or docs match the scoped milestone
- tests pass for the changed surface
- OpenAPI/Foundation Gate impact is updated when applicable
- no raw private data or secret-like evidence is introduced
- user-facing claims match implementation
- rollback or non-goal language is explicit
- the Kanban board is updated

## Excellence Scorecard

| Capability | Current UAA | Target State | Priority |
|---|---|---|---|
| Current release truth | mixed M150-M167 story | single currentness packet | P0 |
| Public security posture | missing tracked `SECURITY.md` | public reporting and triage | P0 |
| Today product spine | partial Today summary | every module feeds Today, Actions, Evidence, and Memory | P0 |
| Memory-first product loop | review-only memory and safe refs | robust reviewed business memory feeding Today, Actions, Evidence, and Weekly Review | P0 |
| Evidence history | receipts and audit refs | human-readable proposed/approved/happened/changed/undoable history | P0 |
| Plans to Actions | decomposition/classification | approve/edit/reject/defer Action envelopes with exact scope and receipts | P0 |
| Chat operator surface | readiness/probe shell | local turn send, model/runtime/auth/tool-denial truth, safe evidence, handoff to Plans/Actions | P0 |
| Governed Code workbench | safe file contracts and previews | repo-local safe diffs, validation proof, approval-bound apply, rollback, evidence | P0/P1 |
| Local model product loop | strong contracts, partial live lane | real redacted E2E proof supporting local Chat/Code | P0/P1 |
| Operator UI | small Control Center | focused memory-first product shell | P0 |
| Durable runtime | contracts and local pieces | restart-safe run spine | P1 |
| Workspace workbench | file contracts and previews | safe patch/apply/rollback | P1 |
| Performance gate | foundation latency scripts | release-blocking p95 budgets | P1 |
| Packaging/release | local dev and CI | reproducible local stack and evidence packet | P1 |
| Extension ecosystem | capability/plugin contracts | inspectable, activatable, revocable catalog | P2 |
| Mobile companion | iOS skeleton/read-only contracts | companion after core loop is stable | P2 |
| API organization | large FastAPI surface | service modules with unchanged route contracts | P1 |
| API perimeter | side-effect metadata, route inventory, and partial bearer-gated `/v1` lane | route classification, local auth, headers, CORS, idempotency audit, targeted rate limits, and manifest enforcement | P1 |
| CI/security posture | named local lanes | visible CI lanes plus safe security/artifact redaction checks | P1 |
| Product truthfulness | strong docs rules | regression checks across docs, UI, reports, and loop artifacts | P0/P1 |

## First Product Loop

The first loop that proves UAA is becoming a private local beta-testable
product:

1. Open Control Center to Today.
2. Review Morning Briefing, priorities, blockers, follow-ups, and memory review
   count.
3. Inspect Evidence as history: what was proposed, approved, happened, changed,
   can be undone, is stale, or remains blocked.
4. Inspect memory candidates from manual notes, Chat/local coding summaries,
   plans, actions, evidence refs, and read-only calendar/email metadata refs.
5. Accept, correct, reject, defer, merge, or mark forget-request posture for
   memory candidates through reviewed decision capture.
6. Convert relevant briefing, plan, memory, chat, or code items into Action
   Inbox envelopes with approve/edit/reject/defer posture, exact scope,
   side-effect class, risk, evidence refs, idempotency, receipts, and rollback
   or safe-disable posture.
7. Use Chat as a real local operator surface: send a turn, see
   model/runtime/auth/tool-denial truth, produce safe evidence, and hand off to
   Plans or Actions.
8. Use governed Code for repo-local safe diffs with validation proof,
   approval-bound apply, rollback, and evidence.
9. Inspect Evidence Timeline and Weekly CEO Review summaries showing what was
   proposed, approved, blocked, corrected, remembered, rejected, changed, or
   stale.

Local model readiness, UAA `/v1`, task decomposition, and safe workspace work
remain important support lanes. They should feed the memory-first daily loop
instead of displacing it as the product spine.

`UAA-P1-011` has shipped the readable baseline for the earlier operator-loop
shape. The broader Founder Command Center daily loop now builds on that
baseline and remains partial until the Today-spine beta-readiness milestones
land with evidence.
