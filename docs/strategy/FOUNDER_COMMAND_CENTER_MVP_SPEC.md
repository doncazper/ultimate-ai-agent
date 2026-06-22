# Founder Command Center MVP Spec

Status: planning and implementation-shaping artifact

This MVP spec is scoped to docs, contracts, tests, and future exact PRs. It
grants no new runtime authority. Any backend route, frontend control, connector
behavior, mutation, persistence change, model/provider call, shell/browser
behavior, plugin import, or public distribution claim must be separately scoped
and gated.

## Next Implementation Lane

Work the next implementation lane in this order, starting from the accepted
`UAA-P1-011` readable-loop baseline:

Current status: UAA-P1-068 Today Product Spine Contract, UAA-P1-069 Evidence
History Grammar, UAA-P1-070 Memory Source And Provenance Model, UAA-P1-071
Memory Review Decision Capture, and UAA-P1-072 Business Memory And Memory
Quality Controls, and UAA-P1-073 Plans To Reviewable Action Envelopes are
implemented as contract/test/read-only UI slices. UAA-P1-074 Chat Local
Operator Surface is implemented as a first-party local operator truth slice.
UAA-P1-075 Governed Code Workbench V1 is implemented as a governed repo-local
Code proposal and Evidence Timeline metadata slice. UAA-P1-076 Cross-Surface
Memory Intake is implemented as a review-only proposal/intake slice. UAA-P1-077
Memory-To-Loop Binding is implemented as a read-only loop-binding slice.
UAA-P1-078 Private Beta-Readiness Gate is implemented as a local/private
beta-test acceptance evidence gate. UAA-P1-079 User Intent Understanding V1 is
implemented as a reviewable intent proposal slice. UAA-P1-080 through
UAA-P1-086 remain planned/queued API boundary hardening lanes.

1. Today product spine contract: every module feeds Today, Actions, Evidence,
   and Memory. Avoid standalone "module complete" definitions. Loop visibility
   is necessary but not sufficient for completion; typed contracts, tests,
   redaction, policy/approval, route/API or CLI inspection, and blocked
   follow-on work remain visible.
2. Evidence history grammar: Evidence reads as what was proposed, approved,
   happened, changed, can be undone, is stale, and remains blocked.
3. Memory source/provenance model: define safe source refs and review-required
   posture for manual notes, external assistant review summaries, local chat,
   local coding, task plans, action proposals, evidence timeline refs,
   read-only calendar/email metadata refs, and CRM-lite business records.
4. Memory review decision capture: add accept/correct/reject/defer-ready
   review decisions without granting writes, deletes, context injection,
   connector runtime, model/provider authority, or production claims.
5. Business memory and memory quality controls: define CRM-lite memory
   candidate kinds and duplicate/conflict/stale/expired/low-confidence/
   source-missing/evidence-missing posture before any memory is treated as
   useful reviewed recall.
6. Plans to Action envelopes: implemented. Plans produce
   approve/edit/reject/defer-ready
   envelopes with exact scope, receipts, expiry, idempotency, evidence, and
   rollback/safe-disable posture.
7. First-party Control Center chat local operator surface: implemented. Chat sends a local
   turn through the governed local gateway, shows model/runtime/auth/tool-denial
   truth, produces safe evidence, and hands off to Plans or Actions. OpenWebUI
   remains a secondary local/dev shell, not the product state owner.
8. Governed Code workbench: implemented. Repo-local safe diff summary refs,
   validation proof refs, approval-bound apply posture, rollback receipt
   posture, and evidence before broad coding-agent autonomy.
9. Cross-surface memory intake: implemented. Bind safe memory proposals from
   Today, Chat, Plans, Actions, Evidence, local coding summaries, and manual
   external-assistant review imports without automatic memory writes or context
   injection.
10. Memory-to-loop binding: implemented. Today, Action Inbox, Evidence
   Timeline, and Weekly CEO Review show memory candidates, accepted recall
   refs, corrections, rejected items, follow-up commitments, stale-state
   posture, and missing-evidence blockers without write or context-injection
   authority.
11. Private beta-readiness gate: implemented. Local/private beta-test
   acceptance evidence distinguishes pass, fail, skipped, blocked, partial,
   mock-only, and accepted-failure states for Morning Briefing, Action Inbox,
   Memory Review, Evidence Timeline, Chat/Plans handoff, governed Code
   proposal refs, and CRM-lite follow-ups without public beta, distribution, or
   production readiness claims.
12. User intent understanding: implemented. Reviewable intent proposals include
   confidence, source refs, evidence refs, ambiguity posture, and ask/act/defer
   routing without hidden authority or action execution. Low-confidence or
   conflicting intent asks the user rather than acting.
13. Sequential API boundary hardening: before authority-heavy Plans, Chat, Code,
   loop binding, or beta-readiness claims, classify routes as
   `public_metadata`, `local_readonly`, `local_sensitive`, or
   `mutating_requires_authority`; plan centralized security headers, explicit
   loopback CORS, simple local bearer/session protection for sensitive routes,
   mutating-route idempotency enforcement, targeted rate limits, and OpenAPI/API
   manifest/route inventory checks. This is not enterprise auth and does not
   add runtime authority.
14. Local Control Center macOS-first Setup Assistant hardening: tighten
   dry-run/read-only setup posture, redacted summaries, blocked states,
   rollback refs, and safe local prerequisite visibility.
12. First product loop readability: make Today, Plans, Actions, Memory,
   Evidence, and Settings easier to scan without adding route authority.
13. Action Inbox / approval envelope UX: expose exact scope, risk, side-effect
   class, approval requirement, expiry, idempotency, evidence, and rollback
   posture before any approve affordance is wired.
14. Morning Briefing skeleton: compose existing safe summaries, mock/degraded
   states, priorities, blockers, and next safe actions.
15. Read-only email/calendar integration contracts: metadata-only calendar/email
   contracts are implemented as contract-only source-readiness support, and the
   draft-only email response proposal contract is implemented as contract-only
   proposal posture. Connector runtime, draft UI, account auth, and send/write
   authority remain out of scope.

This lane is docs/contracts/tests/inspection first. It grants no new backend
route, frontend mutation control, setup mutation, connector runtime,
model/provider call, shell/browser/plugin/mobile/remote execution, installer
authority, public distribution, or production authority.

Current partial API coverage is limited to OpenAPI/API manifest metadata,
side-effect classes, route-status auth posture, bearer-gated local `/v1`
planning, and idempotency concepts in durable run/action contracts. Centralized
security headers, explicit loopback CORS, a broad local bearer/session gate,
route-wide public/protected classification, mutating-route idempotency
enforcement, targeted rate limits, and enforcement tests remain future scoped
work.

UI direction: Control Center / Founder Command Center is the proprietary
primary product UI for the loop. OpenWebUI remains a supported local/dev
conversational shell and compatibility surface; it should not own product state
or become the destination for wiring every workflow.

## Planning-Only Permission Language

Future Founder Command Center surfaces should use one shared permission
vocabulary, without granting authority by naming it:

- Observe: read or summarize safe refs only.
- Draft: create editable proposals that cannot send, write, execute, or persist
  as truth.
- Propose: describe a scoped action envelope for review with evidence, risk,
  side-effect class, expiry, idempotency, receipt refs, and rollback/safe-disable
  posture.
- Approve once: future exact-scope approval for one reviewed action only.
- Approve rule: future bounded rule approval with expiry, revocation, audit, and
  receipt requirements.
- Autopilot micro-scope: future narrowly bounded repeated action class only
  after separate scoped approval.
- Kill switch: visible status/plan for future stop, disable, or revoke
  behavior.

These are inert planning labels, not runtime modes, API capabilities, approval
grants, UI affordances, feature flags, connector scopes, or background sessions.
Observe does not fetch, crawl, refresh, or collect account/network data. Draft
does not send, write, persist as truth, or authorize outbound side effects.
Propose does not dispatch, schedule, retry, execute, or create a durable run.
Approve once and Approve rule do not create approval refs, reusable grants, or
standing authority. Autopilot micro-scope does not start background autonomy,
polling, repeated execution, or connector writes. Kill switch is posture text
only unless a later scoped mutation path is accepted. Any future implementation
must be separately scoped, tested, auditable, revocable, and bound to
PolicyEngine and LocalApprovalAuthority.

## MVP v0 Surface Map

### Today Surface

User goal: Start the day with current state, priorities, blockers, meetings,
follow-ups, proposed actions, evidence gaps, and memory review count.

Current repo evidence / status:

- `apps/control-center/src/routes.tsx` has `/operator-loop`, `/dashboard`,
  `/runtime`, `/chat`, `/plans`, `/models`, `/evidence`, and `/settings`.
- `apps/control-center/src/components/OperatorLoopPanel.tsx` and
  `OperatorFlowPanels.tsx` expose the current UAA-P1-011 loop posture.
- `docs/kanban/current_board.md` treats UAA-P1-011 as the accepted
  readable-loop baseline for the next Founder Command Center tasks.

Required backend routes or service changes:

- Prefer aggregation over new authority. First use existing
  `/control-center/dashboard`, `/control-center/status`,
  `/control-center/runtime-readiness/summary`,
  `/control-center/foundation-gate/summary`, `/control-center/routes`, and
  task decomposition summaries.
- Future route, if scoped: `GET /control-center/today/summary` as
  validation/status-only aggregation with no mutation and no raw content.

Required frontend components:

- `TodaySurfacePanel`
- `MorningBriefingPanel`
- `PriorityPlanSummary`
- `BlockedNextActionList`

Safety/approval requirements:

- Read-only/status-only until a future scoped task.
- Must distinguish real, degraded, mock-only, skipped, blocked, partial, and
  missing states.
- Must name route side-effect classes and authority boundaries for visible
  actions.

Tests needed:

- Control Center render test for Morning Briefing sections and blocked states.
- API route test only if a new route is introduced.
- Documentation/product-language verifier update if new copy is added.

Not scoped:

- Calendar/email connector runtime.
- Automatic memory writes.
- Background briefing generation.
- Raw private-content display.

### Inbox Surface

User goal: Triage incoming work safely, with draft-only responses and no send
or write authority.

Current repo evidence / status:

- Connector contracts and mobile/account connector reviews exist historically,
  but no live email/calendar connector runtime is available in this MVP.
- Product truth packet blocks connector writes and credential handling.

Required backend routes or service changes:

- After the readability lane: email metadata read-only contract models over
  safe refs and redacted summaries.
- Draft-only response proposal contract exists as a Python-core contract-only
  envelope; draft UI and connector runtime remain future scoped work.
- Optional future status route for injected safe fixtures only.

Required frontend components:

- `InboxTriagePanel`
- `DraftOnlyReplyPanel`
- `InboxSourceStatusPanel`

Safety/approval requirements:

- Metadata-only or injected fixture-only until a connector milestone.
- Draft-only means no send, archive, delete, label, move, or account write.
- No raw email bodies, subjects, participants, attachment names, account
  identifiers, or other private message metadata in durable evidence.

Tests needed:

- Contract tests for read-only metadata envelope.
- Contract tests for draft proposal denial of send/write fields.
- Frontend test proving no send button exists.

Not scoped:

- Account auth.
- Inbox fetch.
- Message send/write/delete.
- Attachment download.

### Plans Surface

User goal: Turn goals into task plans with clear approval needs, evidence, and
durable run posture.

Current repo evidence / status:

- `TaskDecompositionService` supports capability registry, classification,
  decomposition, validation, approval state, audit, durable run storage,
  restart visibility, replay refs, and rollback refs.
- `/task-decomposition/*` routes exist under local authority.
- UAA-P1-011 provides the readable operator-loop baseline; broader product
  Plans workflow binding remains separately scoped.

Required backend routes or service changes:

- No new route required for first pass. Bind existing route summaries into the
  product loop.
- Future aggregation route can be scoped after UAA-P1-011 proof.

Required frontend components:

- `PlanBuilderPanel`
- `PlanApprovalNeedsPanel`
- `PlanRunEvidencePanel`

Safety/approval requirements:

- Plan creation does not imply execution.
- Safe registered capability execution requires exact approval.
- Route side-effect classes and approval requirements must be visible.

Tests needed:

- `tests/test_task_decomposition_production_api.py` updates for product loop
  semantics if backend changes.
- Control Center test for route posture and approval-bound wording.

Not scoped:

- Unreviewed handler imports.
- Unrestricted external execution.
- Background autonomous sessions.

### Actions Surface

User goal: Review proposed actions and approve, edit, reject, or defer them.

Current repo evidence / status:

- Action Preview posts to `/control-center/actions/preview`.
- Approvals have validation and task-decomposition grant routes.
- Live product approval UX remains partial.

Required backend routes or service changes:

- Action Inbox schema and validation helpers.
- Future `GET /control-center/actions/inbox` summary route only after route
  scope is approved.

Required frontend components:

- `ActionInboxPanel`
- `ActionProposalCard`
- `ApprovalBoundaryBadge`

Safety/approval requirements:

- Exact scope, risk, side-effect class, authority boundary, evidence refs,
  idempotency key, expiry, and rollback/safe-disable posture.
- Edit/reject can be local review state until backend capture is scoped.

Tests needed:

- Schema tests for required safe refs and denial of raw content.
- Frontend tests proving approve buttons are absent until scoped backend grant
  route binding exists.

Not scoped:

- Broad action execution.
- Connector writes.
- Shell/browser/plugin/mobile/remote actions.

### Memory Surface

User goal: Review proposed profile, project, relationship, episodic, business,
and semantic-local knowledge memory with provenance and correction paths.
Memory should help the founder reconcile useful context from UAA chat, local
coding, task planning, action proposals, evidence, calendar/email metadata,
manual notes, and external assistant review summaries without treating any
source as truth or authority.

Current repo evidence / status:

- `LocalMemoryStore` supports reviewed local recall records, in-memory or
  SQLite, and redacted export.
- Memory is recall, not truth or authority.
- Current Control Center memory surface is mostly evidence/ref viewing.
- Relationship/follow-up memory schema exists as a Python-core contract-only,
  review-only candidate envelope. It does not write, delete, export, inject
  context, call models/providers, run connectors, add routes, or add UI
  controls.

Required backend routes or service changes:

- Memory Review Inbox schema.
- Memory candidate schemas for profile, project, relationship, episodic,
  business, and semantic-local knowledge layers.
- Memory source/provenance schema for manual notes, external assistant review
  summaries, local chat summaries, local coding session summaries, plans,
  actions, evidence refs, read-only calendar/email metadata refs, and CRM-lite
  business records.
- Memory review decision schema for accept, correct, reject, defer, merge,
  supersede, and forget-request posture before any candidate becomes reviewed
  recall.
- Memory quality posture for duplicate, conflicting, stale/expired,
  low-confidence, source-missing, evidence-missing, and blocked candidates.
- Relationship/follow-up memory schema is contract-only and available for safe
  candidate validation; future routes can summarize reviewed candidate refs
  without raw content.
- Future route can summarize reviewed candidate refs without raw content.

Required frontend components:

- `MemoryReviewInboxPanel`
- `RelationshipMemoryCard`
- `MemoryCorrectionPanel`
- `MemorySourceProvenancePanel`
- `MemoryQualityBadge`
- `BusinessMemoryCandidateCard`

Safety/approval requirements:

- No automatic memory writes.
- No context injection.
- Every memory candidate needs provenance, source refs, evidence refs, review
  state, retention/deletion posture, and correction support.
- External assistant output, local coding summaries, and local chat summaries
  are untrusted source inputs until reviewed; they cannot become truth,
  approval evidence, context injection, or action authority by themselves.
- Business memory for people, organizations, opportunities, promises,
  follow-ups, preferences, and decisions must remain safe-ref and
  redacted-summary only until later scoped connector or CRM runtime authority
  exists.

Tests needed:

- Memory schema tests for provenance and raw-content denial.
- Memory review decision tests for accept/correct/reject/defer/merge/supersede
  and forget-request posture.
- Memory quality tests for duplicate/conflict/stale/low-confidence/missing
  evidence states.
- Redacted export regression tests if export shape changes.

Not scoped:

- Hidden context injection.
- Model-output-to-memory writes.
- Vector DB or embeddings.
- Automatic ChatGPT/browser/account imports.
- Connector runtime or external CRM writes.

### Evidence Surface

User goal: See what happened in plain language: proposals, approvals, receipts,
audits, latency, rollback, and blocked states.

Current repo evidence / status:

- Evidence, receipts, events, timeline, Foundation Gate, route inventory, and
  observability summaries already exist.
- Current evidence is partial and ref-heavy.

Required backend routes or service changes:

- Human-readable Evidence Timeline contract over existing safe refs.
- Future aggregation route if needed; no raw source body storage.

Required frontend components:

- `EvidenceTimelinePanel`
- `ReceiptSummaryCard`
- `RollbackStatusCard`

Safety/approval requirements:

- Safe refs and redacted summaries only.
- No raw prompts, responses, provider payloads, paths, logs, environment
  dumps, usernames, hostnames, credentials, or secret-like values.

Tests needed:

- Redaction tests for timeline records.
- Frontend test for readable evidence before developer details.

Not scoped:

- Raw forensic mode.
- External telemetry export.

### Settings Surface

User goal: Understand setup, safe defaults, feature flags, kill-switch posture,
and disabled authority boundaries.

Current repo evidence / status:

- Current Settings is inspection-only and shows safe local setup status plus
  disabled boundaries.
- FCC-P1-011 adds the docs-only Settings posture spec:
  `docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md`.
- No settings mutation route exists.

Required backend routes or service changes:

- Settings surface spec first; FCC-P1-011 is that spec foundation only.
- Future `GET /settings/summary` and validation-only feature flag/kill-switch
  posture routes only after scoped approval.

Required frontend components:

- `SetupStatusPanel`
- `FeatureFlagStatusPanel`
- `KillSwitchStatusPanel`
- `DisabledBoundaryList`

Safety/approval requirements:

- No credential collection.
- No authority toggle.
- Kill-switch posture is status-only in this MVP. `KillSwitchStatusPanel` and
  any settings summary route must not expose enabled stop, revoke, disable,
  feature-flag write, credential, or authority-toggle controls.
- Feature-flag and scoped permission-mode names are posture vocabulary only;
  naming them does not create approval refs, standing grants, execution rights,
  connector writes, revocation actions, kill-switch actions, or production
  authority.
- Any future setting that enables runtime authority or mutation requires exact
  approval, audit, receipt, revocation, rollback/safe-disable, and tests.
- Future safe-disable or revocation behavior is a separate mutating path and
  must be exact-scoped, PolicyEngine-classified, LocalApprovalAuthority-bound,
  audited, receipt-backed, idempotent, redacted, and rollback-aware.

Tests needed:

- Frontend test proving no secret/token text boxes or save-key buttons.
- API manifest/OpenAPI tests if routes are added.

Not scoped:

- Credential vault runtime.
- Provider invocation.
- Runtime lifecycle mutation.

## MVP Workflows

### 1. Morning Briefing

Inputs: existing local status summaries, route manifest, task decomposition
state, evidence summaries, and injected safe fixtures where needed.

Output: readable Today briefing with priorities, blockers, next safe actions,
and evidence gaps.

No new authority: yes.

### 2. Draft-Only Email Triage

Inputs: FCC-P1-008 email metadata contract or injected safe metadata fixtures.

Output: draft response proposal and triage summary.

No send/write authority: required.

### 3. Calendar Read-Only + Meeting Prep

Inputs: FCC-P1-007 calendar read-only contract or injected safe event fixtures.

Output: meeting prep summary, open questions, follow-ups, and evidence refs.

No account auth or calendar write: required.

### 4. Follow-Up Tracker

Inputs: reviewed memory, explicit task refs, safe email/calendar metadata refs,
and manual user entries after scoped UI.

Output: follow-up state, owner, due window, and next safe action.

No connector write: required.

### 4a. First-Party Integration Planning

Inputs: contract-only refs for future contacts lookup contract planning, task
creation proposals, governed article/evidence capture, GitHub read-only project
status, and CRM-lite local lead/follow-up store.

Output: safe proposal and metadata shapes for later scoped review.

No account auth, connector runtime, contacts read/search/lookup runtime,
connector write, browser automation, plugin execution, or production authority:
required.

### 5. Action Inbox

Inputs: action proposal contracts from Plans, Inbox, Files, and Memory.

Output: review queue with approve eligibility, edit/reject/defer states, and
exact authority metadata.

No execution without exact scoped approval: required.

### 6. Memory Review Inbox

Inputs: memory candidate refs with provenance from manual notes, external
assistant review summaries, local chat summaries, local coding summaries,
plans, actions, evidence refs, read-only calendar/email metadata refs, and
CRM-lite business records.

Output: accepted, corrected, rejected, deferred, merged, superseded, or
forget-request memory records through reviewed contracts, with quality posture
for duplicate, conflicting, stale, low-confidence, source-missing, and
evidence-missing candidates.

No automatic memory write or hidden context injection: required.

### 7. Evidence Timeline

Inputs: receipts, events, task audit, Foundation Gate summaries, latency refs,
and rollback refs.

Output: human-readable timeline with safe refs and redaction status.

No raw evidence display: required.

### 8. Weekly CEO Review

Inputs: Today, Plans, Actions, Follow-Up, Memory, Evidence summaries, and
business memory candidates for people, organizations, opportunities, promises,
preferences, decisions, and commitments.

Output: decisions made, commitments, unresolved blockers, carry-forward tasks,
memory corrections, stale memory to revisit, and follow-up opportunities.

No broad autonomy: required.
