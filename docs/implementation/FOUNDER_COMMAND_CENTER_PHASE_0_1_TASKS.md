# Founder Command Center Phase 0/1 Tasks

Status: planning and task-breakdown artifact
Parent board: `docs/kanban/founder_command_center_board.md`

These tasks are designed for scoped Codex branches/PRs. Some baseline slices
are now implemented as review-ready local surfaces, but this document does not
grant runtime authority, connector access, model/provider calls, or production
claims. Most remaining tasks should land as small PRs with tests before product
claims change.

## Task 1 - FCC-P0-001 Capture UAA-P1-011 Readable Baseline

Type: full-stack

Current status: baseline implemented as a readable Operator Loop proof chain.
Future work should extend from this baseline instead of treating UAA-P1-011 as
the complete Founder Command Center daily loop.

New authority: no broad authority. Any safe capability action must use existing
scoped PolicyEngine and LocalApprovalAuthority boundaries.

Acceptance criteria:

- Control Center exposes the UAA-P1-011 loop as readable product flow.
- Runtime health, local model readiness, UAA `/v1` chat readiness, plan
  creation, safe capability approval, and receipt/audit/latency/rollback
  inspection are visible.
- Real, mock, skipped, blocked, denied, partial, and missing states remain
  distinct.
- No raw JSON is the primary UI.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `tests/test_operator_loop_p1_011.py`
- `tests/test_control_center_api_routes.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`

Likely files touched:

- `apps/control-center/src/components/OperatorLoopPanel.tsx`
- `apps/control-center/src/components/OperatorFlowPanels.tsx`
- `apps/control-center/src/api/client.ts`
- `apps/control-center/src/api/types.ts`
- `src/ultimate_ai_agent/core/task_decomposition/`
- `src/ultimate_ai_agent/api/app.py`

PR size: one PR if it binds existing routes only; split backend aggregation and
frontend UI if new route contracts are required.

## Task 2 - FCC-P0-002 Create Founder Command Center IA

Type: frontend/docs

Current status: implemented as grouped primary navigation for Today, Inbox,
Plans, Actions, Memory, Evidence, and Settings, with `/inbox` truthfully
blocked/planned until backend contracts exist.

New authority: no.

Acceptance criteria:

- Primary navigation or grouped route model is shaped around Today, Inbox,
  Plans, Actions, Memory, Evidence, and Settings.
- Existing operator/review routes remain reachable.
- Surface copy names readiness and blocked states accurately.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `scripts/verify_control_center_frontend.py` if product-language checks need
  new expected routes.

Likely files touched:

- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/App.tsx`
- `apps/control-center/src/App.test.tsx`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`

PR size: one frontend PR.

## Task 3 - FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core Surfaces

Type: frontend

New authority: no.

Acceptance criteria:

- Today, Inbox, Plans, Actions, Memory, Evidence, and Settings appear as the
  primary product workflow.
- Legacy review surfaces are grouped as supporting detail rather than
  first-order product loop steps.
- No existing route tests lose coverage.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/components/*Navigation*`
- `apps/control-center/src/styles.css`

PR size: one frontend PR after Task 2.

## Task 4 - FCC-P0-003 Implement Morning Briefing Workflow Skeleton

Type: frontend with possible backend aggregation later

Current status: scoped read-only Morning Briefing posture is implemented with
storage-backed briefing metadata, source-readiness labels, priority, per-item
blockers, stale-state posture, evidence gaps, missing email/calendar/
notification contract refs, and next safe action labels. Remaining work is the
email/calendar read-only source contract, refresh contract, notification
contract, and any source evidence binding under separate milestones.

New authority: no.

Acceptance criteria:

- Today/Morning Briefing shows priorities, blockers, next safe actions,
  evidence gaps, source-readiness posture, stale-state posture, missing source
  contract refs, and review counts.
- It uses storage-backed summaries or safe mock fixtures.
- It does not fetch email/calendar, refresh sources, deliver notifications, or
  generate background content.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/components/MorningBriefingPanel.tsx`
- `apps/control-center/src/components/TodaySurfacePanel.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts`
- `apps/control-center/src/api/types.ts`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`

PR size: one scoped full-stack read-only PR. Add source integrations only in
later scoped PRs.

## Task 5 - FCC-P1-007 Add Calendar Read-Only Integration Contract

Type: backend contract/test/docs

Current status: implemented as a contract-only, metadata-only Python core
envelope paired with FCC-P1-008 in
`docs/connectors/FCC_READ_ONLY_INTEGRATION_CONTRACTS.md`. No connector runtime,
account auth, backend route, or Control Center control is added.

New authority: no.

Acceptance criteria:

- Calendar event metadata contract exists with safe refs and redacted summary
  fields only.
- Contract denies account auth, network fetch, calendar write, background
  collection, raw event body storage, and connector runtime.
- Docs say this is contract-only.

Tests to add/update:

- New focused contract tests under `tests/`.
- `.venv/bin/python scripts/verify_documentation_integrity.py`

Likely files touched:

- `src/ultimate_ai_agent/core/` new connector/planning module or existing
  connector package if present.
- `docs/connectors/`
- `tests/`

PR size: one backend contract PR.

## Task 6 - FCC-P1-008 Add Email Metadata Read-Only Integration Contract

Type: backend contract/test/docs

Current status: implemented as a contract-only, metadata-only Python core
envelope paired with FCC-P1-007 in
`docs/connectors/FCC_READ_ONLY_INTEGRATION_CONTRACTS.md`. No connector runtime,
account auth, backend route, or Control Center control is added.

New authority: no.

Acceptance criteria:

- Email metadata envelope supports safe sender/thread/time/label summary refs.
- Contract denies raw body, attachment download, account auth, email fetch,
  send, delete, archive, label write, and connector runtime.

Tests to add/update:

- New focused contract tests under `tests/`.
- Redaction regression tests for unsafe body-like fields.

Likely files touched:

- `src/ultimate_ai_agent/core/`
- `docs/connectors/`
- `tests/`

PR size: one backend contract PR.

## Task 7 - FCC-P1-009 Add Draft-Only Email Response Proposal Contract

Type: backend contract/test/docs

Current status: implemented as a contract-only, draft-only Python core envelope
in `src/ultimate_ai_agent/core/connectors/`. No connector runtime, account auth,
email fetch/search, send/write/reply/forward/delete/archive/label/move action,
backend route, Control Center control, model call, memory write, context
injection, dependency, public claim, or production authority is added.

New authority: no.

Acceptance criteria:

- Draft proposal includes safe source email metadata refs, sender/recipient
  identity refs, account identity refs, time-window refs, follow-up refs,
  purpose/intent/tone/style labels, draft summary/outline refs, evidence refs,
  source-readiness refs, audit/replay refs, stale-state posture,
  missing-evidence posture, approval posture, blocked send/write states, and
  next safe action.
- Send/write/delete/archive fields are denied.
- Proposal output cannot authorize connector writes.

Tests to add/update:

- Contract tests for allowed draft proposal.
- Denial tests for send/write/delete/archive fields.

Likely files touched:

- `src/ultimate_ai_agent/core/connectors/`
- `tests/`
- `docs/connectors/`

PR size: one backend contract PR after Task 6.

## Task 8 - FCC-P0-004 Add Action Inbox Schema And UI

Type: full-stack if schema lands in Python; frontend-only if using mock-safe
fixtures first

Current status: scoped review-only Action Inbox posture is implemented with
storage-backed action metadata, approval-envelope/state-change readiness,
receipt/audit/idempotency refs, expiry posture, rollback/safe-disable posture,
next safe action labels, explicit blocked states, and no mutation controls.
Remaining work is the exact state-change/approval capture contract, durable
receipt binding, and any future review decision capture under a separate
milestone.

New authority: no.

Acceptance criteria:

- Action cards show title, safe summary, route refs, side-effect class, risk,
  approval requirement, evidence refs, idempotency, expiry, and rollback or
  safe-disable posture.
- Approval-envelope refs are displayed when available; missing envelope,
  receipt, audit, idempotency, rollback, and state-change refs remain explicit
  blockers.
- Approve, send, run, install, connect, write, and state-change controls are
  absent until exact backend grant binding exists.

Tests to add/update:

- Python schema tests if contract is added.
- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `src/ultimate_ai_agent/core/`
- `apps/control-center/src/components/ActionInboxPanel.tsx`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/mocks/controlCenterData.ts`

PR size: split into contract PR and UI PR if Python schema is added.

## Task 9 - FCC-P0-005 Add Memory Review Inbox Schema And UI

Type: full-stack

Current status: baseline implemented/ready for review as a read-only Founder
Loop Memory Review surface on `/memory` backed by
`GET /control-center/today/summary`. Remaining work is decision capture,
memory source/provenance modeling, cross-surface intake, business memory
candidate kinds, quality controls, memory write policy binding,
retention/delete contract, context-injection contract, CLI inspection path, and
durable receipt binding.

New authority: no automatic memory write, memory delete, context injection,
model/provider authority, connector write, raw source display, background sync,
or production authority.

Acceptance criteria:

- Memory candidates include provenance, source refs, evidence refs, review
  state, correction state, confidence, retention/delete posture, and safe
  summary.
- Accept/correct/reject/defer/merge/supersede/forget-request states are review
  states until existing memory write policy is explicitly bound.
- Memory candidates distinguish manual notes, external assistant review
  summaries, local chat summaries, local coding summaries, plans, actions,
  evidence refs, read-only calendar/email metadata refs, and CRM-lite business
  records.
- Business memory candidates cover profile, project, relationship,
  organization, deal/opportunity, promise, follow-up, preference, decision, and
  commitment refs.
- Quality posture distinguishes duplicate, conflict, stale/expired,
  low-confidence, source-missing, evidence-missing, blocked, and reviewed
  states.
- Route paths, operation IDs, and side-effect classes remain unchanged.
- `/memory` is human-readable first and does not expose raw transcript, prompt,
  source, path, log, provider payload, username, hostname, environment dump,
  credential, token, or secret-like values.

Tests to add/update:

- Focused Founder Loop storage/API contract tests.
- Memory source/provenance and decision-state tests.
- Memory quality/dedupe/conflict/stale posture tests.
- `apps/control-center/src/App.test.tsx`
- `make frontend-check`
- `.venv/bin/python scripts/verify_control_center_frontend.py`
- Docs integrity and OpenAPI/API manifest checks if route contracts change.
- Browser smoke for `/memory`.

Likely files touched:

- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/mocks/controlCenterData.ts`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/route_status_manifest.json`

PR size: split contract and UI if needed.

## Task 9a - UAA-P1-068 Today Product Spine Contract

Type: backend contract/test/docs/frontend-read-only first

New authority: no.

Acceptance criteria:

- Define how every module feeds Today, Actions, Evidence, and Memory.
- Today shows priorities, blockers, follow-ups, plan/action state, memory
  review count, stale-source posture, and next safe actions.
- Module completion definitions must avoid standalone "module complete" claims.
  Loop visibility is necessary but not sufficient for completion; Definition of
  Done, typed contract/schema coverage, focused tests, redaction checks,
  policy/approval boundaries, and route/API or CLI inspection paths still
  apply.
- Fixtures and rendered contract state use synthetic safe refs only. No raw
  private content, account identifiers, usernames, hostnames, local paths,
  raw logs, raw prompts, raw responses, provider payloads, credentials, or
  secret-like values are allowed.

Tests to add/update:

- `docs/schemas/today_product_spine_contract.schema.json`.
- `scripts/verify_uaa_p1_068_today_product_spine_contract.py`.
- `tests/test_uaa_p1_068_today_product_spine_contract.py`.
- Focused Founder Loop storage and API assertions for required loop surfaces,
  Today signals, module feed rows, necessary-not-sufficient completion posture,
  plan/action state, stale-source posture, and next safe actions.
- Read-only Today render assertions when the contract fields are surfaced.
- Documentation integrity.

PR size: one contract/docs PR.

## Task 9b - UAA-P1-069 Evidence History Grammar

Status: done.

Type: backend contract/test plus read-only UI display

New authority: no.

Acceptance criteria:

- Evidence entries answer: what was proposed, what was approved, what happened,
  what changed, what can be undone, what is stale, and what remains blocked.
- Memory, Plans, Chat, Code, and Actions can all reference this grammar.
- Evidence stays safe-ref/redacted-summary first, never raw logs or raw paths.

Tests to add/update:

- Evidence grammar contract tests.
- Founder Loop storage/API tests if persisted.
- Frontend render tests if surfaced.
- `docs/schemas/evidence_history_grammar.schema.json`.
- `scripts/verify_uaa_p1_069_evidence_history_grammar.py`.
- `tests/test_uaa_p1_069_evidence_history_grammar.py`.

PR size: one contract/docs/UI-read-only slice completed without new route or
authority.

## Task 9c - UAA-P1-070 Memory Source And Provenance Model

Status: complete.

Type: backend contract/test/docs

New authority: no.

Acceptance criteria:

- Define safe source refs for manual notes, external assistant review summaries,
  local chat summaries, local coding summaries, task plans, action proposals,
  evidence timeline refs, read-only calendar/email metadata refs, and CRM-lite
  business records.
- Deny raw prompt, raw response, raw provider payload, raw local path, raw log,
  account identifier, username, hostname, credential, token, and raw private
  content fields in durable evidence.
- Mark external assistant and local model output as untrusted source input until
  reviewed.

Tests to add/update:

- Focused memory source/provenance schema tests.
- Redaction denial tests for raw/private fields.
- Documentation integrity.

Completed evidence:

- `src/ultimate_ai_agent/core/memory/source_provenance.py`
- `docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md`
- `docs/schemas/memory_source_provenance.schema.json`
- `scripts/verify_uaa_p1_070_memory_source_provenance_model.py`
- `tests/test_uaa_p1_070_memory_source_provenance_model.py`

PR size: one backend contract plus read-only UI visibility PR.

## Task 9d - UAA-P1-071 Memory Review Decision Capture

Status: complete.

Type: backend contract/test plus UI display later

New authority: no automatic write/delete/export/context injection.

Acceptance criteria:

- Support accept, correct, reject, defer, merge, supersede, and forget-request
  review states.
- Decisions include actor refs, source refs, evidence refs, stale-state
  posture, retention posture, audit refs, receipt refs, and blocked-state refs.
- Decision capture does not turn memory into truth, approval evidence, or
  context-injection authority.

Tests to add/update:

- Focused decision-state tests.
- Founder Loop storage/API tests if persisted.
- Frontend tests if decision states are rendered.

Completed evidence:

- `src/ultimate_ai_agent/core/memory/review_decisions.py`
- `docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md`
- `docs/schemas/memory_review_decision_capture.schema.json`
- `scripts/verify_uaa_p1_071_memory_review_decision_capture.py`
- `tests/test_uaa_p1_071_memory_review_decision_capture.py`

PR size: split contract and UI if needed.

## Task 9e - UAA-P1-072 Business Memory And Memory Quality Controls

Status: implemented / ready for review.

Type: backend contract/test plus UI display later

New authority: no connector writes or account sync.

Acceptance criteria:

- Add candidate kinds for profile, project, relationship, organization,
  deal/opportunity, promise, follow-up, preference, decision, and commitment.
- Distinguish duplicate, conflict, stale/expired, low-confidence,
  source-missing, evidence-missing, blocked, and reviewed memory posture.
- Business memory feeds Today, Action Inbox, Evidence Timeline, and Weekly CEO
  Review as safe refs only.

Tests to add/update:

- Business memory schema tests.
- Memory quality contract tests.
- Raw-content denial tests.
- Control Center render tests when surfaced.
- Bound verifier:
  `scripts/verify_uaa_p1_072_business_memory_quality_controls.py`.

PR size: split contract and UI if needed.

## Task 9f - UAA-P1-073 Plans To Reviewable Action Envelopes

Type: backend contract/test plus UI display later

Status: implemented / ready for review.

New authority: no execution or approval grant.

Acceptance criteria:

- Plans produce approve/edit/reject/defer-ready Action envelopes with exact
  scope, side-effect class, risk, approval requirement, idempotency, expiry,
  evidence refs, expected receipt refs, rollback/safe-disable posture, and
  blocked-state reasons.
- Classification and decomposition are not treated as product completion.
- Approval refs remain identifiers unless exact LocalApprovalAuthority scope is
  validated by a later accepted implementation.

Tests to add/update:

- `tests/test_uaa_p1_073_plans_action_envelopes.py`.
- `tests/test_founder_loop_storage.py`.
- `tests/test_control_center_founder_loop_api.py`.
- `apps/control-center/src/App.test.tsx`.
- `scripts/verify_uaa_p1_073_plans_action_envelopes.py`.
- Documentation integrity.

Gate met: `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md` and
`docs/schemas/plans_action_envelopes.schema.json` define the reviewable Action
envelope contract on existing Today/Action Inbox surfaces without adding
execution authority.

## Task 9g - UAA-P1-074 First-Party Control Center Chat Local Operator Surface

Type: backend/local gateway plus first-party Control Center UI display later

Status: Done.

New authority: no provider SDK, tool execution, or memory write.

Acceptance criteria:

- Control Center Chat can send a local turn through the governed local gateway.
- Chat shows model/runtime/auth/tool-denial truth and safe evidence refs.
- Chat can hand off to Plans or Actions as proposals only.
- Model output is not truth, memory, approval evidence, or execution authority.
- OpenWebUI remains a secondary local/dev shell and compatibility surface, not
  the product state owner or the destination for wiring every workflow.

Tests to add/update:

- `tests/test_uaa_p1_074_chat_local_operator_surface.py`.
- `tests/test_founder_loop_storage.py`.
- `tests/test_control_center_founder_loop_api.py`.
- `apps/control-center/src/App.test.tsx`.
- `scripts/verify_uaa_p1_074_chat_local_operator_surface.py`.
- `docs/schemas/chat_local_operator_surface.schema.json`.

Gate met: `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`
defines the contract on existing Today/Chat/Evidence surfaces without adding
provider SDK calls, web fetching, tool execution, memory writes, hidden context
injection, connector writes, shell/subprocess execution, action execution,
approval grant capture, public beta, public distribution, or production
authority.

## Task 9h - UAA-P1-075 Governed Code Workbench V1

Type: backend contract/test plus Control Center metadata shape

Status: Done.

New authority: no unapproved mutation or unrestricted shell.

Acceptance criteria:

- Code proposals show repo-local scope, safe diff summary, validation plan,
  validation result refs, approval requirement, apply receipt, rollback receipt,
  and Evidence history entries.
- Apply remains approval-bound, atomic, idempotent, auditable, rollback-aware,
  and redacted.
- Broad coding-agent autonomy, unrestricted shell, and remote execution remain
  blocked.

Tests to add/update:

- `tests/test_uaa_p1_075_governed_code_workbench.py`.
- `tests/test_founder_loop_storage.py`.
- `tests/test_control_center_founder_loop_api.py`.
- `apps/control-center/src/App.test.tsx`.
- Redaction tests.
- `scripts/verify_uaa_p1_075_governed_code_workbench.py`.
- `docs/schemas/governed_code_workbench.schema.json`.

Gate met: `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
defines the contract on the existing Today/Evidence surfaces without adding
apply execution, approval grant capture, direct file-write runtime,
unrestricted shell, shell/subprocess execution, remote execution, broad
coding-agent autonomy, provider SDK calls, web fetching, connector writes,
diff body storage, memory writes, hidden context injection, public beta, public
distribution, or production authority.

## Task 9i - UAA-P1-076 Cross-Surface Memory Intake

Type: full-stack read-only/proposal

Status: Done.

New authority: no.

Acceptance criteria:

- Today, Chat, Plans, Actions, Evidence, local coding summaries, and manual
  external-assistant review imports can produce memory proposals with bounded
  safe summaries and source/evidence refs.
- Intake paths expose missing-evidence, confidence, stale-state, and next safe
  action labels.
- No provider calls, account fetch, browser import, shell history import, raw
  file import, automatic memory write, or context injection is added.

Tests to add/update:

- `tests/test_uaa_p1_076_cross_surface_memory_intake.py`.
- `tests/test_founder_loop_storage.py`.
- `tests/test_control_center_founder_loop_api.py`.
- `apps/control-center/src/App.test.tsx`.
- `scripts/verify_uaa_p1_076_cross_surface_memory_intake.py`.
- `docs/schemas/cross_surface_memory_intake.schema.json`.

Gate met: `docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md`
defines the review-only intake contract and keeps memory writes, automatic
recall, context injection, provider calls, account fetch, browser import, shell
history import, source import, connector runtime, public beta, public
distribution, and production authority blocked.

## Task 9j - UAA-P1-077 Memory-To-Loop Binding

Type: full-stack read-only product-surface binding

Status: Done.

New authority: no.

Acceptance criteria:

- Today, Action Inbox, Evidence Timeline, Memory Review, and Weekly CEO Review
  show memory candidates, accepted recall display-only refs, corrections,
  rejected items, follow-up commitments, stale-state posture, memory-derived
  Action proposals, and missing-evidence blockers.
- Every memory-derived action proposal names source refs, evidence refs,
  side-effect class, approval posture, and next safe action.

Tests to add/update:

- Founder Loop storage/API tests.
- `apps/control-center/src/App.test.tsx`
- `make frontend-check`
- `scripts/verify_uaa_p1_077_memory_to_loop_binding.py`.
- `docs/schemas/memory_to_loop_binding.schema.json`.
- Documentation integrity.

PR size: complete as one read-only UI/API binding PR after Tasks 9a-9i.

## Task 9k - UAA-P1-078 Private Beta-Readiness Gate

Status: Done.

Type: docs/test/release-evidence planning first

New authority: no public beta, distribution, or production claim.

Acceptance criteria:

- Define private local beta-test evidence for Morning Briefing, Action Inbox,
  Memory Review, Evidence Timeline, safe local Chat/Plans handoff, governed
  Code diffs, and CRM-lite follow-ups.
- Gate distinguishes pass, fail, skipped, blocked, partial, mock-only, and
  accepted-failure states.
- Public beta, public distribution, production readiness, broad autonomy,
  connector writes, provider/model authority, unrestricted shell, remote
  execution, and account sync remain blocked.

Tests to add/update:

- `docs/control_center/UAA_P1_078_PRIVATE_BETA_READINESS_GATE.md`.
- `docs/schemas/private_beta_readiness_gate.schema.json`.
- `scripts/verify_uaa_p1_078_private_beta_readiness_gate.py`.
- `tests/test_uaa_p1_078_private_beta_readiness_gate.py`.
- Founder Loop storage/API tests.
- Control Center render tests.
- Documentation integrity.

PR size: completed as one read-only contract/UI/test evidence slice.

## Task 9l - UAA-P1-079 User Intent Understanding V1

Type: later backend contract/test/docs

Status: Done.

New authority: no.

Acceptance criteria:

- Intent proposals include confidence, source refs, ambiguity posture,
  ask/act/defer routing, and evidence refs.
- Intent understanding depends on reviewed memory, evidence history, action
  envelopes, Chat receipts, and Code receipts.
- Low-confidence or conflicting intent asks the user rather than acting.

Tests to add/update:

- Intent taxonomy tests.
- Ambiguity and ask-rather-than-act tests.
- Documentation integrity.

PR size: completed as one read-only contract/UI/test evidence slice.

## Task 9m - UAA-P1-080 API Route Classification And Public/Protected Inventory

Type: API boundary contract/test/docs

Status: Done.

New authority: no.

Acceptance criteria:

- Every current FastAPI route is classified as `public_metadata`,
  `local_readonly`, `local_sensitive`, or `mutating_requires_authority`.
- `/api/manifest`, the frozen route inventory fixture, route-status manifest,
  and Control Center API Routes surface show the classification without adding
  routes, middleware, auth, headers, CORS, idempotency enforcement, rate limits,
  or runtime authority.
- Public/protected posture remains inventory truth only in this P1-080
  milestone; P1-083 through P1-086 are now complete in later perimeter-
  hardening milestones.

Tests to add/update:

- `tests/test_api_manifest.py`
- `tests/test_api_route_inventory_fixture.py`
- `tests/test_control_center_api_routes.py`
- `scripts/verify_uaa_p1_080_api_route_classification.py`
- Documentation integrity.

PR size: completed as one API contract/UI/docs/test evidence slice.

## Task 9n - UAA-P1-081 Centralized FastAPI Security Headers

Type: API boundary hardening/test/docs

Status: Done.

New authority: no.

Acceptance criteria:

- Handled FastAPI responses receive centralized response security headers.
- HSTS is emitted only for HTTPS requests.
- The milestone adds no auth, sessions, CORS, idempotency enforcement, rate
  limits, route authority, runtime authority, public beta, distribution, or
  production authority.

Tests to add/update:

- `tests/test_api_security_headers.py`
- `tests/test_api_manifest.py`
- `scripts/verify_uaa_p1_081_fastapi_security_headers.py`
- Documentation integrity.

PR size: completed as one API middleware/docs/test evidence slice.

## Task 9o - UAA-P1-082 Explicit Loopback CORS Allowlist

Type: API boundary hardening/test/docs

Status: Done.

New authority: no.

Acceptance criteria:

- Server-side CORS allows only explicit local Control Center dev/preview
  origins on `localhost`, `127.0.0.1`, and `[::1]` for ports `5173` and `4173`.
- Wildcard CORS, CORS credentials, external origins, LAN/private IP origins,
  wrong local ports, `0.0.0.0`, and `null` origins remain denied.
- CORS is documented as browser hardening, not authentication, authorization,
  route authority, public beta, distribution, or production authority.

Tests to add/update:

- `tests/test_api_cors.py`
- `tests/test_api_manifest.py`
- `scripts/verify_uaa_p1_082_loopback_cors.py`
- Documentation integrity.

PR size: completed as one API middleware/docs/test evidence slice.

## Task 9p - UAA-P1-087 Private Operator Trial And UI Functional Tuning

Type: local trial/test/docs/UI tuning

Status: Implemented through UAA-P1-087.2c; full UAA-P1-087.2 and
UAA-P1-087.3 are deferred until more Founder Loop implementation exists after
the proven local boot path, packet surface, acceptance ledger, and unanswered
manual review scaffold.

New authority: no.

Sub-milestone order:

- `UAA-P1-087.1` Local Launcher Dual-Surface Boot Readiness: implemented. The
  existing repo-local launcher and clickable macOS `.command` path now run
  `trial-boot`, open Control Center first, attempt OpenWebUI only as the
  secondary local shell, verify UAA-owned readiness before reusing ports, expose
  stop/log-ref posture, and report blocked states such as
  `primary_ready_secondary_blocked` without installing packages or pulling
  images.
- `UAA-P1-087.2a` Private Trial Packet And UI Tuning Surface: implemented. The
  safe-ref-only packet and read-only `/private-trial` surface record manual
  smoke checklist refs, friction refs, UI/copy task refs, core-loop gap refs,
  and blocked authority refs for full private UI tuning without adding backend
  routes or runtime authority.
- `UAA-P1-087.2b` Private Trial Findings Capture And Acceptance Ledger:
  implemented. The safe-ref-only acceptance ledger and read-only
  `/private-trial` visibility record manual smoke step refs, pending surface
  review refs, acceptance question refs, tuning decision refs, finding refs,
  and blocked authority refs without claiming accepted findings, adding backend
  routes, or adding runtime authority.
- `UAA-P1-087.2c` Private Trial Manual Review Intake Scaffold: implemented.
  The safe-ref-only scaffold and read-only `/private-trial` visibility record
  unanswered pending answer refs, missing implementation refs, deferred
  decision refs, and blocked authority refs without claiming accepted/revised
  findings, adding backend routes, or adding runtime authority.
- `UAA-P1-087.2` In-Person Private Operator UI Functional Tuning: deferred
  until more Founder Loop implementation exists; later use the proven local
  boot path, 087.2a packet, 087.2b acceptance ledger, and 087.2c scaffold for
  hands-on founder testing and capture accepted/revised friction, manual smoke
  evidence, UI/copy tasks, Today/Actions/Memory/Evidence/Chat handoff gaps, and
  CRM-lite follow-up gaps.
- `UAA-P1-087.3` Native SwiftUI Boot Cockpit Planning And Source-Only Scaffold:
  after the `.command` boot contract is proven and UI tuning evidence exists,
  plan/source-scaffold a native macOS boot cockpit over fixed launcher
  contracts only.

Acceptance criteria:

- Runs after UAA-P1-080 through UAA-P1-086 API boundary hardening.
- Captures local/in-person founder testing notes for Today, Actions, Memory,
  Evidence, Chat handoff, blocked-state language, and CRM-lite follow-up flow.
- Produces a manual smoke checklist, usability/friction findings, UI/copy
  tuning tasks, and beta-readiness evidence refs.
- Keeps trial scope local/private and does not claim public beta, public
  distribution, production readiness, connector writes, action execution,
  memory writes, provider/model authority, Code apply, or hidden automation.
- Keeps OpenWebUI secondary to Control Center, and denies Docker installation,
  arbitrary shell execution, LaunchAgent setup, daemon/background worker setup,
  signing, notarization, public distribution, OpenWebUI plugin/admin mutation,
  product-state ownership by OpenWebUI, and production authority.

Tests to add/update:

- UAA-P1-087.1 launcher/verifier tests for local boot readiness.
- UAA-P1-087.2a packet/verifier tests and read-only Control Center render test.
- UAA-P1-087.2b acceptance-ledger/verifier tests and read-only Control Center
  render test.
- UAA-P1-087.2c manual-review-scaffold/verifier tests and read-only Control
  Center render test.
- Manual smoke checklist acceptance artifact for full UAA-P1-087.2.
- Control Center render/frontend checks for tuned flows.
- Product-language checks.
- Documentation integrity.

PR size: UAA-P1-087.1 landed as the launcher boot-readiness slice; UAA-P1-087.2a
landed as the packet/surface slice; UAA-P1-087.2b landed as the acceptance-ledger
slice; UAA-P1-087.2c landed as the unanswered manual-review scaffold slice; keep
full UAA-P1-087.2 and UAA-P1-087.3 in their own later follow-up patches after
more Founder Loop implementation exists.

## Task 10 - FCC-P0-003 Test Follow-Up Add Product E2E Test For Morning Briefing

Type: test-only

New authority: no.

Acceptance criteria:

- Test proves Morning Briefing renders priorities, blockers, next safe action,
  evidence gap, and review count.
- Test proves no send/run/approve/mutate button is exposed by the briefing.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- `make frontend-check`

Likely files touched:

- `apps/control-center/src/App.test.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts` if fixtures are needed.

PR size: one test PR or bundled with Task 4.

## Task 11 - FCC-P1-009 Add Product E2E Test For Draft-Only Email Flow

Type: test-only

New authority: no.

Acceptance criteria:

- Test proves draft-only flow renders safe metadata and draft proposal state.
- Test proves no send/archive/delete/account-write button exists.
- Test proves blocked connector-runtime state is visible.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- Contract tests from Tasks 6 and 7 if backend contracts exist.

Likely files touched:

- `apps/control-center/src/App.test.tsx`
- `apps/control-center/src/mocks/controlCenterData.ts`

PR size: one test PR after draft-only UI exists.

## Task 12 - FCC-P1-012 Plan FastAPI Service-Module Extraction

Type: docs-only first

New authority: no.

Current status: implemented as a Founder Command Center alignment section in
`docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md`, with architecture and
board currentness updates. It does not move routes, add routes, create
APIRouter modules, rename paths, change operation IDs, change side-effect
classes, change auth posture, change schemas, add dependencies, add Control
Center UI, or implement UAA-P1-058.

Acceptance criteria:

- Plan maps routes to `system_service`, `runtime_service`,
  `task_decomposition_service` as the accepted current extraction name for
  planning routes, `approval_service`, `memory_service`,
  `workspace_files_service` as the accepted current extraction name for file
  routes, `evidence_service`, `integrations_service`,
  `governed_web_evidence_service`, `settings_service`, `workflow_service`, and
  related Control Center/observability/verification modules.
- Plan requires no route drift, stable operation IDs, side-effect class
  preservation, auth posture preservation, API manifest truth, route-status
  truth, OpenAPI truth, and Foundation Gate coverage.
- First UAA-P1-058 candidate remains `GET /health` and `GET /version` into
  `ultimate_ai_agent.api.routes.system_service`.

Tests to add/update:

- Documentation integrity.
- OpenAPI contract verification.
- API manifest and Control Center route tests.
- Foundation Gate report-only.
- `git diff --check`.

Likely files touched:

- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- `docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md`

PR size: one docs PR.

## Task 13 - FCC-P1-006 Build Human-Readable Evidence Timeline

Type: frontend plus existing-route backend aggregation

Current status: implemented as a storage-backed Evidence Timeline on
`/evidence` using `GET /control-center/today/summary`. The slice adds readable
receipt, audit, replay, rollback, latency, Foundation Gate, source-readiness,
redaction, stale-state, missing-evidence, blocker, and next-safe-action
posture without adding routes or runtime authority.

New authority: no.

Acceptance criteria:

- Timeline displays receipts, audits, task events, latency, Foundation Gate,
  and rollback status as readable safe summaries.
- Raw evidence is not displayed as the primary UI.

Tests to add/update:

- `apps/control-center/src/App.test.tsx`
- Redaction tests if new backend records are added.

Likely files touched:

- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/App.test.tsx`

PR size: one scoped full-stack product-readability PR using the existing
read-only Today summary route.

## Task 14 - FCC-P1-013 Add Local Setup/Onboarding Wizard Spec

Type: docs-only first

New authority: no.

Acceptance criteria:

- Spec covers prerequisite checks, loopback API, Control Center, local model
  readiness, OpenWebUI shell configuration, safe evidence, blocked states, and
  rollback/safe-disable guidance.
- Spec denies installer, signing, background agent, credential collection, and
  public distribution claims.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/developer/`
- `docs/macos/`
- `docs/strategy/`

PR size: one docs PR.

## Task 15 - FCC-P1-011 Add Settings Surface Spec With Kill Switch And Feature Flags

Type: docs-only first

New authority: no.

Current status: implemented as a docs-only spec foundation in
`docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md`. No Settings
mutation, feature-flag write, kill-switch execution, revocation execution,
credential collection, backend route, Control Center control, connector
runtime/write, model/provider authority, memory write, context injection,
background job, shell/subprocess execution, public claim, or production
authority is added.

Acceptance criteria:

- Spec names feature flag state, kill-switch state, disabled boundaries, audit
  refs, revocation refs, rollback/safe-disable refs, and approval needs.
- Spec says no credential collection and no authority toggle in current UI.
- Spec keeps feature flags and kill-switch states as posture labels only until
  a separate scoped milestone grants exact authority with route, policy,
  approval, evidence, rollback, and tests.

Tests to add/update:

- Documentation integrity.
- Frontend tests when implemented.

Likely files touched:

- `docs/control_center/`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`

PR size: one docs PR.

## Task 16 - FCC-P1-011 Define Scoped Permission Modes

Type: docs/backend contract later

New authority: no. This task documents planning labels and future contract
requirements only in
`docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md`. It does not
create approval refs, standing grants, enabled UI controls, backend routes,
mutating settings, runtime sessions, connector writes, background jobs,
revocation actions, or kill-switch actions.

Acceptance criteria:

- Modes distinguish inspect-only, draft-only, approval-required local mutation,
  governed read-only evidence, and blocked high-risk scopes.
- Planning names are explicit and shared by product surfaces: Observe, Draft,
  Propose, Approve once, Approve rule, Autopilot micro-scope, and Kill switch.
- Modes bind to PolicyEngine, LocalApprovalAuthority, side-effect class, audit,
  receipt, revocation, and rollback requirements.
- Naming a mode does not grant runtime authority.
- Approval-like mode names do not create approval refs, standing grants,
  background sessions, connector writes, execution rights, revocation actions, or
  kill-switch actions.
- Definitions must stay aligned with the MVP spec, target architecture, and
  Codex prompt vocabulary.

Tests to add/update:

- Docs integrity for planning.
- Policy/approval tests only if contracts are implemented.

Likely files touched:

- `docs/approvals/`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- `docs/codex/CODEX_EXECUTION_PROMPTS.md`
- `docs/control_center/`
- `src/ultimate_ai_agent/core/approvals/` in a later contract PR.

PR size: docs PR first; backend contract PR later.

## Task 17 - FCC-P1-010 Add Relationship/Follow-Up Memory Schema

Type: backend contract/test

Current status: implemented as a contract-only, review-only Python core schema
in `src/ultimate_ai_agent/core/memory/`. No automatic memory write, memory
delete execution, export execution, context injection, connector runtime/write,
account auth, email/calendar fetch, backend route, Control Center control,
model/provider authority, dependency, public claim, or production authority is
added.

New authority: no automatic memory write.

Acceptance criteria:

- Schema covers person, organization, project, deal, promise, follow-up,
  relationship, preference, business-context, semantic-local, and episodic
  candidate kinds.
- Candidates include safe display labels, redacted summaries, provenance refs,
  source refs, evidence refs, related person/org/project/deal/follow-up refs,
  review state, confidence posture, correction/rejection posture,
  retention/delete/export posture, stale-state posture, authority boundary,
  missing contract refs, blocked states, and next safe action.
- Model/provider output, connector output, and memory refs cannot authorize
  memory truth, approval, writes, delete/export execution, or context injection.

Tests to add/update:

- New memory schema tests.
- Redaction tests for unsafe names or secret-like values if applicable.

Likely files touched:

- `src/ultimate_ai_agent/core/memory/`
- focused tests under `tests/`
- Founder Command Center board/spec docs

PR size: one backend contract PR.

## Task 18 - FCC-P1-014 Add Lead/Follow-Up Tracker Spec

Type: docs-only first

New authority: no.

Acceptance criteria:

- Spec maps lead/opportunity/follow-up states to reviewed memory and action
  proposals.
- Spec denies connector writes, CRM writes, and hidden sync.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/strategy/`
- `docs/memory/`
- `docs/connectors/`

PR size: one docs PR.

## Task 19 - FCC-P1-013 Add One-Command Local Launcher Task

Type: infrastructure/docs, possible dev-script hardening

New authority: no production or broad runtime authority.

Acceptance criteria:

- Existing local launcher guidance has one clear command path for loopback-only
  API and Control Center dev startup.
- Generated local state remains under ignored `.uaa/` paths.
- Docs distinguish local dev launcher from installer or public distribution.

Tests to add/update:

- `make doctor`
- Existing launcher tests if scripts change.
- Documentation integrity.

Likely files touched:

- `docs/developer/LOCAL_LAUNCHER.md`
- `scripts/dev/README.md`
- `Makefile` if adding a wrapper target
- `tests/test_dev_launcher.py` if script behavior changes.

PR size: one small infra/docs PR.

## Task 20 - FCC-DOC-002 Add 3-Minute Product Demo Script/Checklist

Type: docs-only

New authority: no.

Acceptance criteria:

- Checklist demonstrates the current safe product loop without unsupported
  claims.
- It names prerequisites, expected blocked states, safe evidence refs, tests to
  run, and rollback/safe-disable review.
- It does not claim public distribution, public beta, broad autonomy, or
  unrestricted authority.

Tests to add/update:

- Documentation integrity.

Likely files touched:

- `docs/strategy/`
- `docs/control_center/`
- `docs/testing/`

PR size: one docs PR, ideally after Tasks 1-4.

## Founder Loop V1 Conveyor - FCC-V1-000 through FCC-V1-007

Type: staged full-stack productization with docs/test/manifest gates first

Status: FCC-V1-000 through FCC-V1-007 implemented for the bounded Founder Loop V1 conveyor.
FCC-V1-001 is contract/verifier coverage for the API
perimeter; duplicate replay runtime remains blocked until route-owner receipt
storage exists outside routes that implement their own receipt-backed replay.

New authority: no authority from this planning entry. Each implementation slice
must separately scope its route, storage, approval, idempotency, evidence,
rollback/safe-disable, frontend, CLI/core/API inspection, and test behavior.

Source of detailed goals:

- `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`

Milestones:

- `FCC-V1-000` Control Center Release Surface Manifest: implemented. The
  `ship`/`partial`/`blocked`/`experimental` manifest, schema, human-readable
  release surface docs, drift verifier, and focused tests now cover every
  visible Control Center route without promoting any route to `ship`.
- `FCC-V1-001` API Perimeter For Real Mutations: finish idempotency,
  route-classification, auth, approval, rate-limit, manifest, and enforcement
  posture before any Founder Loop mutation lands.
- `FCC-V1-002` Action Inbox Backend State Machine: make approve, edit, reject,
  and defer backend-owned Action decisions with append-first storage,
  `LocalApprovalAuthority` validation where required, idempotency, receipts,
  replay markers, and Control Center receipt visibility. Implemented for
  decision state only; approved actions still do not execute and no connector,
  shell/subprocess, provider/model, memory-write, public beta, or production
  authority is granted.
- `FCC-V1-003` Founder Loop V1 Vertical Slice: promote one Today item into an
  Action envelope, capture exact approval/edit/reject/defer decision, create a
  durable receipt, update Evidence Timeline, and provide CLI/repo-local
  inspection parity. Implemented for the first receipt-bearing vertical slice;
  action execution, connector writes, memory writes, provider/model calls,
  shell/subprocess work, public beta, and production authority remain blocked.
- `FCC-V1-004` Control Center Chat Durable Receipt And Handoff: implemented
  safe `ChatTurnReceipt` records and reviewable handoff receipts to Actions or
  Plans without treating model output as authority, executing work, writing
  memory, calling providers, writing connectors, or granting production
  authority.
- `FCC-V1-005` Memory Review Decisions: implemented backend-owned
  `MemoryReviewDecisionReceipt` records with `candidate_ref`, `decision`,
  `decision_ref`, `receipt_ref`, `idempotency_key_ref`,
  `payload_fingerprint_ref`, `evidence_timeline_event_ref`,
  `corrected_summary_ref` for corrections, `source_refs`, `evidence_refs`,
  `reviewer_ref`, and `blocked_state_refs`; stores accept/correct/reject
  append-first; preserves rejected decisions; stores correction summaries as
  safe refs only; exposes backend routes for review, accept, correct, and
  reject; shows real UI controls, receipt refs, and Evidence Timeline entries.
  Memory writes, truth authority, context injection, CRM/account sync,
  connector writes, action execution, public beta, and production authority
  remain blocked.
- `FCC-V1-006` Evidence Timeline Productization: implemented real evidence
  event types for action envelopes, action decisions, chat receipts, chat
  handoffs, and memory review decisions, grouped by Today item, Action, Chat
  turn, and Memory candidate through `GET /control-center/evidence/timeline`.
  Evidence remains read-only, safe-ref-only, and does not grant approval,
  rollback execution, action execution, context injection, connector writes,
  public beta, or production authority.
- `FCC-V1-007` Promotion And Proof Lane: implemented for the focused Founder
  Loop V1 proof command, pytest lane, Control Center route/render status
  alignment, release surface status promotion rules, and raw-content leak
  checks before `/actions`, `/chat`, `/memory`, and `/evidence` use `ship` for
  exact proofed route-surface behavior only.

Definition of done:

- A reviewer can follow the first real Founder loop from Today item to Action
  envelope to exact decision to durable receipt to Evidence Timeline update.
- Action Inbox decisions are no longer UI-only.
- Control Center Chat produces durable safe receipts and reviewable handoff
  refs.
- Memory Review accept/correct/reject decisions are backend-owned,
  receipt-backed, evidence-visible, and do not grant context injection.
- Unproofed visible routes remain `partial`, `blocked`, or `experimental`;
  FCC-V1-007 promotes only `/actions`, `/chat`, `/memory`, and `/evidence` to
  `ship` for exact proofed route-surface behavior.
- The bounded conveyor is complete after all `FCC-V1-000` through `FCC-V1-007` tasks
  are complete, with smaller follow-up slices added when needed rather than
  skipping manifest, idempotency, receipt, evidence, CLI/core/API inspection,
  or redaction gates.
