# Founder Command Center MVP Spec

Status: planning and implementation-shaping artifact

This MVP spec is scoped to docs, contracts, tests, and future exact PRs. It
grants no new runtime authority. Any backend route, frontend control, connector
behavior, mutation, persistence change, model/provider call, shell/browser
behavior, plugin import, or public distribution claim must be separately scoped
and gated.

## MVP v0 Surface Map

### Today Surface

User goal: Start the day with current state, priorities, blockers, meetings,
follow-ups, proposed actions, evidence gaps, and memory review count.

Current repo evidence / status:

- `apps/control-center/src/routes.tsx` has `/operator-loop`, `/dashboard`,
  `/runtime`, `/chat`, `/plans`, `/models`, `/evidence`, and `/settings`.
- `apps/control-center/src/components/OperatorLoopPanel.tsx` and
  `OperatorFlowPanels.tsx` expose the current UAA-P1-011 loop posture.
- `docs/kanban/current_board.md` keeps UAA-P1-011 in Now / Building.

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

- Email metadata read-only contract models.
- Draft-only response proposal contract.
- Optional future status route for injected safe fixtures only.

Required frontend components:

- `InboxTriagePanel`
- `DraftOnlyReplyPanel`
- `InboxSourceStatusPanel`

Safety/approval requirements:

- Metadata-only or injected fixture-only until a connector milestone.
- Draft-only means no send, archive, delete, label, move, or account write.
- No raw email bodies in durable evidence.

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

User goal: Review proposed business memory about people, projects, deals, and
promises with provenance and correction paths.

Current repo evidence / status:

- `LocalMemoryStore` supports reviewed local recall records, in-memory or
  SQLite, and redacted export.
- Memory is recall, not authority.
- Current Control Center memory surface is mostly evidence/ref viewing.

Required backend routes or service changes:

- Memory Review Inbox schema.
- Relationship/follow-up memory schema.
- Future route can summarize reviewed candidate refs without raw content.

Required frontend components:

- `MemoryReviewInboxPanel`
- `RelationshipMemoryCard`
- `MemoryCorrectionPanel`

Safety/approval requirements:

- No automatic memory writes.
- Every memory candidate needs provenance, source refs, evidence refs, review
  state, retention/deletion posture, and correction support.

Tests needed:

- Memory schema tests for provenance and raw-content denial.
- Redacted export regression tests if export shape changes.

Not scoped:

- Hidden context injection.
- Model-output-to-memory writes.
- Vector DB or embeddings.

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
- No settings mutation route exists.

Required backend routes or service changes:

- Settings surface spec first.
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
- Any future setting that enables runtime authority or mutation requires exact
  approval, audit, receipt, revocation, rollback/safe-disable, and tests.

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

Inputs: future email metadata contract or injected safe metadata fixtures.

Output: draft response proposal and triage summary.

No send/write authority: required.

### 3. Calendar Read-Only + Meeting Prep

Inputs: future calendar read-only contract or injected safe event fixtures.

Output: meeting prep summary, open questions, follow-ups, and evidence refs.

No account auth or calendar write: required.

### 4. Follow-Up Tracker

Inputs: reviewed memory, explicit task refs, safe email/calendar metadata refs,
and manual user entries after scoped UI.

Output: follow-up state, owner, due window, and next safe action.

No connector write: required.

### 5. Action Inbox

Inputs: action proposal contracts from Plans, Inbox, Files, and Memory.

Output: approve/edit/reject/defer review queue with exact authority metadata.

No execution without exact scoped approval: required.

### 6. Memory Review Inbox

Inputs: memory candidate refs with provenance.

Output: accepted/corrected/rejected memory records through reviewed contracts.

No automatic memory write: required.

### 7. Evidence Timeline

Inputs: receipts, events, task audit, Foundation Gate summaries, latency refs,
and rollback refs.

Output: human-readable timeline with safe refs and redaction status.

No raw evidence display: required.

### 8. Weekly CEO Review

Inputs: Today, Plans, Actions, Follow-Up, Memory, and Evidence summaries.

Output: decisions made, commitments, unresolved blockers, carry-forward tasks,
and memory corrections.

No broad autonomy: required.
