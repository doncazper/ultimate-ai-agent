# UAA Next Capability And Product Prompt Pack

Status: operator-run prompt pack
Purpose: Add the next protocol/capability foundations and product-readiness
lanes without copying a broad AI-ops-console shape or bypassing UAA authority
boundaries.

These prompts are execution prompts, not runtime system prompts. They do not
grant authority by themselves. Every implementation must preserve `AGENTS.md`,
Python Agent Core authority, Control Center shell boundaries, OpenAPI/API
manifest truth, LocalApprovalAuthority, PolicyEngine, redaction, route
side-effect classification, and Foundation Gate checks.

## Prompt 00 - Split Into Merge-Gated PR Lanes

Role: You are a Principal Software Engineer and product-minded safety reviewer
working inside the UAA repository.

Goal: Read this prompt pack completely, then split it into small,
merge-gated PR lanes. Do not run this file end to end as one giant
implementation unless a later operator instruction explicitly grants that
scope. The default posture is one narrow PR at a time, with each PR reviewed,
verified, and merged before starting the next implementation lane.

Default PR lane sequence:

1. Prompt 01 - MCP Gateway Foundation
2. Prompt 02 - A2A Gateway Foundation
3. Prompt 03 - Browser Automation Through WebAccessGateway
4. Prompt 04 - Release-Surface Manifest With Proof
5. Prompt 08 - Provider And Settings Diagnostics
6. CRM-M1-UI-001 - `/crm` fixture-only Control Center shell route, using the
   accepted CRM M1 fixture-only contracts and prompt guidance in
   `docs/prompts/crm_product_sequence.md`
7. Prompt 10 - Unified Work Thread
8. Prompt 07 - Durable Operator State, Recovery, Backup, Restore

Deferred optional lanes:

- Prompt 05 - macOS Setup And Launcher Polish
- Prompt 06 - Visual Regression Over Actual UI Routes
- Prompt 09 - Product-Forward Front Door

These deferred prompts may be promoted into their own PRs when they become the
next explicitly accepted lane. Do not mix them into MCP, A2A, browser,
release-surface, provider/settings, CRM, unified-thread, or backup/restore PRs.

Global rules:

- Treat `AGENTS.md` as binding.
- Preserve historical tags; do not retarget, delete, or force-push tags.
- Inspect current implementation before changing files.
- Preserve unrelated user changes.
- Keep each PR lane small enough to verify.
- If a prompt requires authority not yet accepted by current repo policy, create
  or update the contract, manifest, verifier, tests, docs, and blocked posture
  instead of silently adding runtime behavior.
- Do not add runtime model calls, provider SDK calls, direct web fetching,
  direct browser automation, connector writes, plugin runtime import,
  unrestricted shell/subprocess execution, remote execution, public beta,
  public distribution, production readiness claims, production authority, or
  broad autonomy.
- Browser, MCP, and A2A work must enter through explicit UAA gateway contracts
  with policy, approval, side-effect, evidence, rollback/safe-disable,
  redaction, OpenAPI, CLI/API/core parity, and tests.
- Every operator-relevant Control Center behavior must be backed by Python
  Core/API state, not React-only truth.
- Evidence must use safe refs, bounded previews, redacted summaries, and
  explicit blocked states only.

Execution loop:

1. Read this entire file, `AGENTS.md`, `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
   `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`,
   `docs/network/WEB_ACCESS_GATEWAY.md`,
   `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`,
   `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`,
   `docs/control_center/visual_regression_manifest.json`, and
   `docs/kanban/founder_command_center_board.md`.
2. Inspect `git status --short --branch`.
3. Select only the next accepted PR lane from the default sequence unless the
   operator explicitly requests a different lane.
4. For the selected lane:
   - derive concrete requirements;
   - inspect current code, docs, tests, and verifiers;
   - implement the smallest safe slice;
   - add or update focused tests/verifiers/docs;
   - run focused checks;
   - adversarially review for authority creep, raw evidence, UI-only truth,
     route/API drift, unsupported claims, and missing rollback/safe-disable;
   - repair before commit.
5. Before opening or updating the PR, run a lane consistency pass:
   - route manifest and OpenAPI operation IDs;
   - release-surface route statuses;
   - visual regression manifest coverage;
   - product-language claims;
   - docs indexes;
   - operational maturity and authority candidate manifests;
   - redaction/static guards.
6. Run focused checks for changed files plus:
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `.venv/bin/python scripts/verify_operational_maturity.py`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
   - `make frontend-check` if frontend files changed
   - `git diff --check`
7. Commit only if checks pass or blockers are explicitly documented and the
   user asks to commit a known-blocked slice.

Final response must include:

- prompts completed, blocked, or deferred;
- files changed;
- tests/verifiers run;
- skipped checks and reasons;
- behavior intentionally not added;
- remaining risks and next prompt if any.

## Prompt 01 - MCP Gateway Foundation

Role: You are implementing UAA's MCP foundation as a governed gateway boundary,
not as a generic plugin runtime or direct agent tool bus.

Goal: Promote MCP from watchlist-only planning into a UAA-owned inspectable
gateway foundation. The first implementation must make MCP concepts visible and
testable without granting broad tool invocation, remote server execution,
plugin runtime import, connector writes, provider calls, or unrestricted
network/shell authority. MCP is the interoperability layer. UAA remains the
governed operating system.

Product posture:

- Good path:
  `Agent proposes intent -> Planner selects candidate capability -> Authority Engine checks scope -> Approval Engine binds exact approval -> Capability Broker invokes MCP -> Receipt Ledger records result -> Evaluator decides next step`.
- Bad path:
  `Agent sees MCP tool -> Agent calls MCP tool -> Tool does thing`.
- The first prompt must implement the contracts, manifests, blocked states, and
  proof needed for the good path without making the final invocation step live.

Required outcome:

- Define a scoped milestone doc such as `docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md`.
- Add Python Core contracts for MCP server/tool/resource/prompt metadata,
  transport posture, auth posture, activation posture, side-effect class,
  credential-ref requirements, audit refs, revocation refs, and blocked states.
- Add MCP discovery contracts that answer:
  - What tools/resources/prompts exist?
  - What schemas do they expose?
  - What authority, privacy, cost, and side-effect risks do they imply?
- Add contract import from MCP-shaped metadata into UAA Capability records or
  extend existing helpers if already present. Imported records must include:
  - authority level;
  - risk class;
  - approval required;
  - rollback posture;
  - receipt requirement;
  - privacy posture;
  - cost posture;
  - credential-ref requirements;
  - transport/auth/activation posture;
  - safe-disable and revocation refs.
- Add dry-run/preview contracts for MCP-shaped capabilities. Before any future
  action, UAA must be able to ask:
  - What would this tool do?
  - What inputs would it need?
  - What evidence would it produce?
  The prompt must keep this no-side-effect and preview-only.
- Add approval-binding contracts proving that any future human approval ref must
  match the exact MCP server/tool ref, exact arguments or safe argument refs,
  exact scope, exact budget/cost posture, exact credential refs, and exact
  expiration. Approval refs are identifiers only until validated by
  LocalApprovalAuthority.
- Add execution-boundary contracts proving that only UAA's Capability Broker may
  invoke MCP in a later exact-scoped callable lane. React must never call MCP
  directly. Model output must never call MCP directly. Provider output must
  never call MCP directly.
- Add receipt contracts for future MCP calls. Every permitted or blocked MCP
  attempt must be able to produce:
  - safe summary;
  - redacted input/output refs;
  - capability ref;
  - approval ref or approval-missing ref;
  - timestamp;
  - result status;
  - rollback/refusal details;
  - audit/replay refs.
- Add replay/audit contracts proving UAA can reconstruct why a tool was
  selected, who approved it, what policy allowed or denied it, what happened,
  and what was blocked.
- Add a read-only API or CLI inspection path only if the current API perimeter
  accepts it; otherwise keep it CLI/docs/verifier-only.
- If adding API routes, update OpenAPI, `/api/manifest`, route classification,
  route side-effect docs, idempotency/auth/rate-limit posture where applicable,
  and focused tests.
- Add tests proving MCP metadata does not become callable authority by
  manifest presence alone.
- Add tests for the denial chain: MCP says it can send email with a schema; UAA
  imports it as a candidate capability; PolicyEngine requires exact approval;
  LocalApprovalAuthority has no matching approval; CapabilityBroker blocks it;
  ReceiptLedger records a blocked receipt; UI/API/CLI posture says human review
  is required.
- Add tests for unsafe transport, missing provenance, raw credential material,
  raw protocol payloads, requested external writes, plugin runtime import, and
  broad tool invocation denial.
- Add docs/index updates and product-language guardrails saying what is
  implemented, partial, blocked, and future-scoped.
- Add a staged MCP roadmap inside the milestone doc:
  - near term: read-only and fixture/dry-run capabilities only;
  - local file/resource inspection through safe refs;
  - calendar/email read contracts, not writes;
  - CRM fixture provider;
  - provider catalog inspection;
  - documentation/search index resources;
  - local deterministic workers;
  - no-op/dry-run action previews;
  - later: connector reads;
  - later: exact-approved low-risk writes;
  - later: scoped recurring workflows;
  - later: background execution;
  - later: broader external integrations.

Authority boundary:

- Allowed in this prompt: metadata inspection, manifest conversion, blocked
  posture, dry-run/preview contracts, approval-binding contracts, receipt
  schemas, replay/audit schemas, safe refs, read-only diagnostics, tests, docs,
  verifier.
- Not allowed in this prompt: remote MCP invocation, generic `tools/call`,
  external network transport, OAuth flow execution, secret resolution, server
  subprocess spawning, plugin import/execution, connector writes, browser
  execution, model/provider calls, public marketplace claims, production
  authority.
- Do not add a broad MCP enabled toggle.
- Do not add a UI button that implies MCP execution unless the backend contract
  exposes an exact blocked/planned/preview-only posture.
- Do not persist raw MCP protocol payloads, raw prompt content, raw response
  content, raw tool inputs, raw tool outputs, raw local paths, credentials, or
  secret-like values.

Suggested verification:

- New focused pytest file for MCP gateway contracts.
- New verifier script for the MCP foundation doc/manifest.
- Tests for discovery metadata import into UAA Capability records.
- Tests for dry-run/preview no-side-effect posture.
- Tests for exact approval-binding mismatch blocking.
- Tests for CapabilityBroker-only invocation posture.
- Tests for blocked receipt and replay/audit reconstruction metadata.
- Existing API manifest/OpenAPI checks if routes are added.
- Documentation integrity.

Definition of done:

- UAA can truthfully say it has an MCP gateway foundation for inspected metadata
  and future activation review.
- UAA can truthfully say MCP is treated as an interoperability layer whose
  discovered tools become governed UAA capability candidates, not direct agent
  authority.
- UAA has proof that an MCP tool declaration such as "send email" is blocked
  without exact approval and produces inspectable blocked posture/receipt
  metadata.
- UAA cannot yet claim callable MCP runtime support unless a later exact
  milestone implements and proves one narrow callable lane.

## Prompt 02 - A2A Gateway Foundation

Role: You are implementing UAA's A2A foundation as a governed delegation
contract boundary, not remote-agent authority.

Goal: Promote A2A from watchlist-only planning into an inspectable local
contract layer for agent cards, handoff envelopes, task/status metadata, and
delegation review posture.

Required outcome:

- Define a scoped milestone doc such as `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`.
- Add Python Core contracts for A2A agent identity, agent card metadata,
  task/handoff envelope, status summary, declared capabilities, requested
  grants, trust posture, auth posture, revocation refs, audit refs, evidence
  refs, and blocked authority refs.
- Bind A2A metadata to existing decision-router, task-decomposition, approval,
  evidence, and remote-worker concepts where appropriate.
- Add a read-only CLI/API inspection path only if route/API perimeter rules are
  updated and tested.
- Add tests proving remote agent/card/task metadata is not truth authority,
  approval authority, execution authority, memory authority, or delegation
  authority by itself.
- Add denial tests for missing peer identity, stale card version, unknown
  provenance, requested connector writes, requested browser/shell execution,
  credential-bearing delegation, and remote self-approval.
- Add docs/index/product-truth updates.

Authority boundary:

- Allowed in this prompt: metadata contracts, local validation, safe status
  summaries, task/handoff proposal envelopes, read-only inspection, no-go
  states, tests, docs, verifier.
- Not allowed in this prompt: remote dispatch, peer-auth runtime, gRPC/HTTP
  execution, public agent-card discovery, remote approvals, connector writes,
  remote tool invocation, browser/shell execution, provider calls, production
  authority.

Suggested verification:

- Focused tests for A2A contracts and route/API posture if added.
- Existing remote-worker and task-decomposition tests relevant to handoff
  boundaries.
- Documentation integrity.

Definition of done:

- UAA can truthfully say it has an A2A compatibility foundation for inspected
  agent/delegation metadata and future exact-scoped handoff review.
- UAA cannot claim remote A2A execution or live delegation yet.

## Prompt 03 - Browser Automation Through WebAccessGateway

Role: You are implementing the browser automation path as a staged
WebAccessGateway authority ladder.

Goal: Make browser automation a first-class future capability in UAA without
adding direct Playwright/Selenium/browser-provider calls outside approved
gateway adapters or granting click/form/auth/download/upload authority.

Required outcome:

- Update or create a scoped milestone doc such as
  `docs/browser/UAA_BROWSER_AUTOMATION_GATEWAY_LADDER.md`.
- Extend `ultimate_ai_agent.core.web_access` planning/contracts as needed for
  browser observe, browser action dry-run, low-risk exact-approved actions,
  blocked high-risk actions, audit records, source metadata, risk classes,
  policy decisions, and evidence refs.
- Add or update static guards so direct browser automation imports/calls remain
  denied outside approved adapter modules or explicit future exceptions.
- Add a read-only/metadata-only Control Center or CLI readiness surface only if
  it stays backend-owned and route-classified.
- Add tests proving no browser clicks, form fills, auth/cookies,
  downloads/uploads, POST-style mutations, or unrestricted observe/run actions
  are available in this milestone.
- Add future promotion gates for observe-only, action dry-run, and exact
  approved low-risk action lanes.

Authority boundary:

- Allowed in this prompt: contracts, gateway policy, static guards, disabled
  adapters, readiness diagnostics, dry-run planning shapes, audit schemas,
  tests, docs, verifier.
- Not allowed in this prompt: live browser execution, browser clicks, form
  filling, authenticated browsing, cookies, downloads/uploads, external POST/
  PUT/PATCH/DELETE, unrestricted browsing, direct Playwright/Selenium calls
  outside approved adapter modules, production authority.

Suggested verification:

- Existing `tests/test_web_access_static_guards.py` and related web runtime
  authority tests.
- New focused tests for browser ladder contracts.
- Documentation integrity.

Definition of done:

- UAA has a credible browser automation roadmap and guardrail foundation inside
  WebAccessGateway.
- No live browser action authority is granted by this prompt.

## Prompt 04 - Release-Surface Manifest With Proof

Role: You are tightening UAA's Control Center release-surface truth so every
visible route has a current status and proof chain.

Goal: Make the release-surface manifest stronger than a route list: every
visible Control Center route must be labeled `ship`, `partial`, `experimental`,
or `blocked`, with backend/API refs, visual proof refs, blocked capabilities,
owner, verifier refs, and promotion criteria.

Required outcome:

- Inspect `apps/control-center/src/routes.tsx`,
  `docs/control_center/release_surface_manifest.json`,
  `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`, and route-status
  docs.
- Ensure every visible route appears exactly once in the manifest.
- Ensure every route has:
  - route path and label;
  - owner;
  - status from the allowed vocabulary;
  - backend route refs or explicit no-backend rationale;
  - side-effect class and route classification;
  - proof lanes;
  - visual baseline refs or an explicit blocked/experimental reason;
  - blocked capabilities;
  - promotion criteria;
  - product-language caveats.
- Add/update verifier logic to fail on missing route, unknown status, missing
  proof lane, missing visual baseline ref, status drift between UI and manifest,
  raw evidence fragments, or unsupported release claims.
- Update docs/index references.

Authority boundary:

- This is truth/proof work only. Do not add runtime authority, backend actions,
  connector writes, provider calls, browser automation, public beta, production
  readiness, or production authority.

Suggested verification:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_release_surface_manifest.py -q`
- `.venv/bin/python scripts/verify_control_center_release_surface.py`
- Documentation integrity.
- Frontend tests if route metadata/UI changed.

Definition of done:

- A reviewer can open one manifest and know the truthful readiness state of
  every visible Control Center route.

## Prompt 05 - macOS Setup And Launcher Polish

Role: You are making UAA's first-run macOS setup feel trustworthy and
operator-readable without adding installer authority.

Goal: Improve Setup Assistant and launcher polish for macOS-first local use:
clear prerequisites, dry-run status, blocked states, rollback/safe-disable
refs, redacted summaries, next safe actions, and CLI parity.

Required outcome:

- Inspect `src/ultimate_ai_agent/core/macos_setup_assistant/`,
  Control Center Setup Assistant components, launcher scripts, macOS docs, and
  existing setup tests.
- Tighten backend-owned setup read models and UI copy so first-run setup shows:
  ready, missing, blocked, partial, skipped, and degraded states;
  safe local prerequisites;
  what will not happen;
  rollback/safe-disable posture;
  CLI inspection command refs;
  evidence refs.
- Improve launcher docs/scripts only within current allowed behavior.
- Add tests for no setup mutation, no LaunchAgent install/load/start, no
  credential handling, no downloads, no shell execution, no background service
  authority, no production setup claim.
- Update docs and product truth.

Authority boundary:

- Allowed in this prompt: read-only setup diagnostics, UI polish, CLI
  inspection, docs, tests, verifiers.
- Not allowed in this prompt: installer mutation, LaunchAgent mutation,
  background service install/start, downloads, credential writes, shell
  execution as setup behavior, rollback execution, public distribution,
  production setup claim.

Suggested verification:

- Focused macOS setup assistant tests.
- Control Center frontend tests for setup if changed.
- Documentation integrity.

Definition of done:

- A first-time macOS user can understand what is ready, missing, blocked, and
  safe before granting any future authority.

## Prompt 06 - Visual Regression Over Actual UI Routes

Role: You are making Control Center visual proof match actual routed UI, not
curated snapshots only.

Goal: Strengthen visual regression coverage for actual current Control Center
routes across desktop and mobile, while keeping screenshots redacted and safe.

Required outcome:

- Inspect existing Playwright visual tooling, visual baseline manifest,
  screenshot docs, and frontend test setup.
- Ensure visual capture runs against actual route URLs for every release-surface
  route that is `ship` or `partial`; experimental/blocked routes must either
  have labeled baselines or explicit blocked rationale.
- Ensure desktop and mobile viewport coverage.
- Ensure visual artifacts do not contain raw prompts, responses, provider
  payloads, paths, logs, usernames, hostnames, secrets, or private content.
- Add a verifier that cross-checks:
  - release-surface routes against visual manifest;
  - manifest refs against checked-in safe baseline files or accepted blocked
    reasons;
  - screenshot hashes;
  - status vocabulary.
- Update docs and scripts.

Authority boundary:

- Visual QA only. Do not add browser automation as product behavior, connector
  runtime, provider calls, live web, public beta, production authority, or raw
  private screenshot capture.

Suggested verification:

- Existing visual regression verifier.
- Playwright visual command if available.
- Frontend tests.
- Documentation integrity.

Definition of done:

- The visual proof lane can show what the current UI actually looks like for
  every visible route status without leaking private data.

## Prompt 07 - Durable Operator State, Recovery, Backup, Restore

Role: You are adding durable operator-state recovery posture before broader
authority.

Goal: Define and implement a minimal, local-first durable state and recovery
contract for Founder Loop operator state: actions, receipts, memory review,
evidence, briefing, settings posture, and future unified thread state.

Required outcome:

- Inspect existing storage, Founder Loop repository, backup docs/tests, event
  ledger, receipts, and Foundation Gate rollback/recovery docs.
- Define minimum operator backup set for current UAA state.
- Add or strengthen backup manifest contracts, backup verify, offline restore
  posture, and recovery diagnostics.
- Prefer CLI-first local inspection/verification before UI controls.
- If adding API/UI visibility, classify routes and keep restore mutation
  blocked unless a later exact milestone approves it.
- Add tests for backup create/verify metadata, missing required files, corrupt
  evidence refs, stale schema, unsafe raw content, restore blocked while active,
  and recovery diagnostics.
- Update docs/product truth.

Authority boundary:

- Allowed in this prompt: local backup/verify contracts, offline restore plan,
  diagnostics, CLI inspection, read-only UI status, tests, docs.
- Not allowed in this prompt: live destructive restore route, external backup
  upload, cloud sync, production recovery claim, raw private data in backup
  evidence, broad runtime authority.

Suggested verification:

- Focused backup/recovery tests.
- Foundation Gate report-only path if touched.
- Documentation integrity.

Definition of done:

- UAA has a credible local recovery story for operator state without pretending
  production restore is solved.

## Prompt 08 - Provider And Settings Diagnostics

Role: You are making provider/settings failure states readable to an operator.

Goal: Improve provider and Settings diagnostics so the user can see configured,
missing, blocked, degraded, revoked, expired, cost-blocked, disabled, and
future-scoped states without granting provider/model authority.

Required outcome:

- Inspect provider catalog/readiness/cost/vault/router-dry-run docs, core
  contracts, API routes, Control Center Settings components, and tests.
- Create or improve backend-owned diagnostics read models with:
  - human-readable status labels;
  - safe next actions;
  - blocked authority refs;
  - cost posture;
  - credential-ref posture without raw secrets;
  - provider/model lane posture;
  - CLI inspection refs;
  - evidence refs.
- Update Settings UI to render readable states instead of raw JSON for
  operator-critical flows.
- Add tests for missing credentials, revoked refs, expired refs, unknown paid
  cost, provider disabled, live adapter blocked, validation blocked, router
  dry-run proposal-only, and redaction.
- Update docs/product truth.

Authority boundary:

- Allowed in this prompt: diagnostics, readiness, cost posture, credential-ref
  posture, exact-approved validation posture where already supported, UI
  readability, tests, docs.
- Not allowed in this prompt: broad provider SDK calls, background/autonomous
  provider calls, billing authority toggle, router execution authority, secret
  reveal, raw provider payloads, model output authority, production authority.

Suggested verification:

- Focused provider/readiness/settings tests.
- Control Center frontend tests if UI changed.
- API manifest/OpenAPI checks if routes changed.
- Documentation integrity.

Definition of done:

- Settings tells a human what is wrong, what is safe to inspect, and what
  remains blocked.

## Prompt 09 - Product-Forward Front Door

Role: You are making UAA's front door read as a daily Founder Command Center,
not only a portfolio of safety infrastructure.

Goal: Update front-door product language so a new reader understands the daily
command-center loop first, while all safety/currentness caveats remain exact.

Required outcome:

- Inspect `README.md`, `docs/portfolio/CURRENT_STATUS.md`,
  `docs/portfolio/PRODUCT_NORTH_STAR.md`,
  `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`,
  `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, and docs index.
- Reframe the top-level narrative around:
  Morning Briefing -> Today Plan -> Action Inbox -> Approval Envelope ->
  Receipt -> Evidence -> Memory Review -> Weekly CEO Review.
- Keep current status labels for implemented, partial, blocked, planned,
  mock-only, future-scoped, and missing.
- Make the trust layer feel like product value, not caveat spam.
- Remove or demote language that makes UAA sound like a generic agent runtime
  before it sounds like a founder/operator command center.
- Update product truth docs only where needed.

Authority boundary:

- Docs/product-language only unless a currentness verifier requires metadata
  alignment. Do not add runtime behavior, routes, public beta claims,
  production readiness claims, connector authority, provider authority, browser
  authority, or broad autonomy.

Suggested verification:

- Product truth verifier.
- Documentation integrity.
- Any product-language tests/verifiers already present.

Definition of done:

- A reader can understand UAA's product in under a minute and still see the
  honest non-production, local-first, governed boundaries.

## Prompt 10 - Unified Work Thread

Role: You are designing and implementing the first UAA-native work thread
without copying a broad Chat/Cowork/Code console.

Goal: Create the narrow Founder Command Center thread spine:
Chat -> Plan -> Action -> Evidence. The thread must connect existing safe
receipts and proposals into one operator-readable path without letting model
output, React state, memory recall, or handoff text become authority.

Required outcome:

- Inspect Chat receipt/handoff, Plans-to-Actions, Action Inbox, Evidence
  Timeline, Memory Review, Today, and Control Center route/component code.
- Define a backend-owned unified thread read model that links:
  - chat turn receipt refs;
  - plan/proposal refs;
  - action envelope refs;
  - decision receipt refs;
  - local task commit refs where already exact-approved;
  - evidence timeline refs;
  - memory review refs;
  - blocked state refs;
  - next safe action refs.
- Add CLI/API/core parity for inspecting the thread.
- Add UI rendering that feels like one coherent work thread, not separate
  technical panels.
- Keep filters/expanded panels/tabs as React-only presentation state; all
  product truth must come from Python Core/API.
- Add tests for no model-output authority, no hidden memory write, no context
  injection, no action execution by handoff, no connector writes, no provider
  calls, no shell/browser execution, no raw content persistence, and receipt
  refs only.
- Update release-surface and product truth docs.

Authority boundary:

- Allowed in this prompt: backend-owned read model, receipt linking,
  proposal-only handoffs, local task refs already in scope, UI readability,
  CLI inspection, tests, docs.
- Not allowed in this prompt: executing plans, generic action execution,
  automatic memory writes, context injection, provider/model calls, connector
  writes, browser/shell execution, production authority.

Suggested verification:

- Focused backend tests for unified thread read model.
- Control Center frontend tests.
- API manifest/OpenAPI checks if routes are added.
- Documentation integrity.

Definition of done:

- UAA has a narrow, ownable work-thread experience that makes Chat, Plan,
  Action, and Evidence feel connected without inheriting external comparison runtime's broad
  Chat/Cowork/Code sprawl.
