# Founder Loop V1 Milestone Conveyor

Status: completed bounded productization milestone record
Baseline: v0.103.0 / 0.103.0
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md`
Related boards: `docs/kanban/current_board.md`,
`docs/kanban/founder_command_center_board.md`

This document records the detailed FCC-V1 conveyor for turning the existing
contract/read-only Founder Command Center spine into one real receipt-bearing
Founder loop:

```text
Today item -> Action envelope -> exact approval -> durable receipt ->
Evidence Timeline update
```

The conveyor is complete through `FCC-V1-000` through `FCC-V1-007` for the
bounded Founder Loop V1 route-surface proof lane. Broader P2/provider,
packaging, public distribution, commercialization, or new runtime-authority
expansion still requires a separate scoped milestone. Future follow-up slices
must not skip release-surface truth, API perimeter, receipt, evidence, and
CLI/core/API inspection requirements.

This milestone list is planning and task-shaping only. It does not add backend
routes, Control Center controls, runtime model calls, connector runtime,
connector writes, shell/subprocess behavior, browser automation, automatic
memory writes, context injection, CRM sync, public beta, public distribution,
or production authority by itself.

## Shared Definition Of Done

Every FCC-V1 implementation slice must keep these requirements visible:

- Product behavior is backend-owned through Python Agent Core/API contracts,
  not React-only state.
- Mutations are exact-scoped, approval-bound where required, idempotent,
  append-first, auditable, rollback-aware or safe-disable-aware, and receipt
  backed.
- CLI or repo-local script inspection exists for operator-relevant state.
- Durable evidence uses safe refs, redacted summaries, bounded previews, and
  explicit blocked states only.
- Evidence never stores raw prompt content, raw response content, raw provider
  payloads, raw transcripts, raw local paths, raw logs, usernames, hostnames,
  environment dumps, credentials, tokens, or secret-like values.
- Model/provider/OpenWebUI/runtime output, memory recall, preview output, and
  React state are not truth authority, approval authority, or execution
  authority.

## FCC-V1-000 - Control Center Release Surface Manifest

Status: implemented by `docs/control_center/release_surface_manifest.json`,
`docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`,
`docs/schemas/control_center_release_surface.schema.json`,
`scripts/verify_control_center_release_surface.py`, and
`tests/test_control_center_release_surface_manifest.py`. At FCC-V1-000 no
route was promoted to `ship`, and no backend route or runtime authority was
added; FCC-V1-007 later promoted only `/actions`, `/chat`, `/memory`, and
`/evidence` through the focused proof lane.

Goal: make every visible route tell the truth before any workflow is promoted.

Tasks:

- Create a release surface schema and manifest.
- Add `docs/control_center/release_surface_manifest.json`.
- Every visible Control Center route must have `path`, `label`, `status`,
  `backend_routes`, `side_effect_class`, `route_classification`,
  `approval_required`, `proof_lanes`, `blocked_capabilities`, `evidence_refs`,
  and `owner`.
- Status vocabulary is exactly `ship`, `partial`, `blocked`, or
  `experimental`.
- Add `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`.
- Explain what each status means.
- Include promotion rules: a route cannot be `ship` unless behavior is
  backend-owned, tested, evidence-backed, and not React-only.
- Add `scripts/verify_control_center_release_surface.py`.
- Fail verification if a visible route in `apps/control-center/src/routes.tsx`
  is missing from the manifest.
- Fail verification if a `ship` route lacks proof lanes or backend route refs.
- Fail verification if UI route status and manifest status drift.

Definition of done: the repo can truthfully say which Control Center routes
are `ship`, `partial`, `blocked`, or `experimental`, and the verifier prevents
silent drift.

## FCC-V1-001 - API Perimeter For Real Mutations

Status: Implemented as contract/verifier coverage. Duplicate replay behavior
is defined as a future route-owner receipt-storage contract; runtime replay is
not implemented by this milestone.

Goal: finish the safety perimeter required before Action, Memory, or Chat
mutations become real.

Tasks:

- Complete or consume the mutating-route idempotency audit.
- Inventory every route that can change local state.
- Require `idempotency_key` or `idempotency_ref` for mutating routes.
- Add manifest posture for idempotency.
- Define duplicate replay behavior: the same key returns the prior receipt,
  while a conflicting payload is rejected.
- Add targeted rate-limit posture for sensitive and expensive routes first:
  chat, action decisions, approval capture, memory decisions, task
  decomposition, and file proposals.
- Keep rate limits local-first and document that rate limits are not
  production auth.
- Add enforcement tests so OpenAPI and `/api/manifest` expose route
  classification, side-effect class, auth posture, approval posture,
  idempotency posture, and rate-limit posture.
- Make tests fail if a new mutating route lacks the required metadata.

Definition of done: no new Founder Loop mutation can land without idempotency,
route classification, auth posture, approval posture, tests, and manifest
visibility.

## FCC-V1-002 - Action Inbox Backend State Machine

Status: implemented by `src/ultimate_ai_agent/core/control_center/action_decisions.py`,
Founder Loop storage decision tables, Control Center action decision routes,
`docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`,
`scripts/verify_fcc_v1_002_action_inbox_state_machine.py`, focused Python
tests, and Control Center render tests. Action execution remains blocked.

Goal: make Action Inbox decisions real backend-owned state changes.

Tasks:

- Define the action state model.
- Add `ActionEnvelope` and `ActionDecision` core contracts.
- Supported statuses: `proposed`, `approved`, `edited`, `rejected`,
  `deferred`, `expired`, `receipt_recorded`, and `blocked`.
- Include exact scope refs, risk class, side-effect class, approval
  requirement, expiry, idempotency ref, expected receipt ref, and
  rollback/safe-disable ref.
- Treat edit as a backend-owned decision that creates a new safe proposed
  envelope version or corrected envelope ref. Edit does not execute work and
  does not grant approval.
- Store action envelopes append-first.
- Store action decision events append-first.
- Store receipt refs.
- Store idempotency replay markers.
- Add routes:
  - `GET /control-center/actions/inbox`
  - `POST /control-center/actions/{action_id}/approve`
  - `POST /control-center/actions/{action_id}/edit`
  - `POST /control-center/actions/{action_id}/reject`
  - `POST /control-center/actions/{action_id}/defer`
  - `GET /control-center/actions/{action_id}/receipt`
- Bind decisions to approval authority.
- Approval refs remain identifiers until exact scope is validated.
- Approve must validate exact actor, action, resource refs, risk, expiry, and
  classification through `LocalApprovalAuthority`.
- Edit, reject, and defer still produce receipts, but do not grant execution
  authority.
- Replace review-only local button state in Control Center with backend calls.
- Show pending, success, edited, rejected, deferred, blocked, replayed, and
  failed states.
- Show receipt refs after every decision.

Definition of done: approve, edit, reject, and defer are no longer UI-only.
Every state change is backend-owned, idempotent, receipt-backed, and visible in
Action Inbox. Approved actions still do not execute and no connector,
shell/subprocess, provider/model, memory-write, public beta, distribution, or
production authority is granted.

## FCC-V1-003 - Founder Loop V1 Vertical Slice

Status: implemented for the first receipt-bearing vertical slice. The route,
storage, UI, CLI inspection path, verifier, and focused tests are present, but
approved actions still do not execute.

Goal: ship the first real loop: Today item -> Action envelope -> exact
approval -> durable receipt -> Evidence Timeline update.

Tasks:

- Promote one Today item into an Action envelope.
- Add a backend path to create an Action envelope from a Today item ref.
- The route must not execute the action. It only creates a reviewable envelope.
- The envelope must carry exact scope, risk, side-effect class, approval
  requirement, idempotency, expected receipt, and rollback posture.
- Wire approval decision to receipt.
- Approving the envelope produces a durable receipt.
- Rejecting, editing, or deferring also produces a receipt.
- Duplicate approval uses idempotency replay, not double mutation.
- Every envelope creation and decision writes an Evidence Timeline event.
- Evidence answers what was proposed, what was decided, what changed, what can
  be undone, and what remains blocked.
- Add or document a CLI/repo-local command or script to inspect the same
  Today/action/receipt/evidence state outside React.

Definition of done: a reviewer can open Today, create an Action envelope,
approve, edit, reject, or defer it, see the durable receipt, and see the
Evidence Timeline update.

Proof refs:

- `docs/control_center/FCC_V1_003_FOUNDER_LOOP_VERTICAL_SLICE.md`
- `scripts/verify_fcc_v1_003_founder_loop_vertical_slice.py`
- `tests/test_fcc_v1_003_founder_loop_vertical_slice.py`
- `scripts/dev/uaa_founder_loop.py`

## FCC-V1-004 - Control Center Chat Durable Receipt And Handoff

Status: implemented for durable Chat receipts and reviewable Actions/Plans
handoffs. The routes, storage, Control Center UI, release-surface refs,
verifier, and focused tests are present. Handoffs still do not execute work,
write memory, inject context, call providers, write connectors, grant public
beta authority, or grant production authority.

Goal: make Chat produce durable operator receipts and reviewable handoffs
without treating model output as authority.

Tasks:

- Define `ChatTurnReceipt`.
- Include `turn_ref`, `route_ref`, `model_ref`, `runtime_truth`,
  `auth_truth`, `tool_denial_truth`, `safe_summary_ref`, `handoff_refs`,
  `receipt_ref`, and `evidence_ref`.
- Explicitly exclude raw prompt, raw response, raw provider payload, raw
  transcript, and tool output.
- Add routes:
  - `POST /control-center/chat/turns`
  - `GET /control-center/chat/turns/{turn_ref}/receipt`
  - `POST /control-center/chat/turns/{turn_ref}/handoff`
- Add handoff targets:
  - `handoff_target=actions` creates a reviewable Action envelope.
  - `handoff_target=plans` creates a plan proposal or plan-envelope ref.
- Handoff does not execute work.
- Update Chat UI so a local turn shows receipt status after submission.
- Show model/runtime/auth/tool-denial truth.
- Add "Record actions proposal" and "Record plans proposal" only when backend
  handoff is available.

Definition of done: Control Center Chat can produce a durable safe receipt and
create reviewable handoff refs, while model output remains non-authoritative.

Proof refs:

- `docs/control_center/FCC_V1_004_CHAT_DURABLE_RECEIPT_HANDOFF.md`
- `scripts/verify_fcc_v1_004_chat_durable_receipt_handoff.py`
- `tests/test_fcc_v1_004_chat_durable_receipt_handoff.py`
- `apps/control-center/src/components/OperatorFlowPanels.tsx`

## FCC-V1-005 - Memory Review Decisions

Goal: make Memory Review accept, correct, and reject real scoped backend
behavior.

Status: implemented for backend-owned, idempotent, receipt-backed decisions.

Tasks:

- Define the memory decision model.
- Add `MemoryReviewDecision`.
- Fields: `candidate_ref`, `decision`, `corrected_summary_ref`,
  `source_refs`, `evidence_refs`, `reviewer_ref`, `receipt_ref`,
  `idempotency_ref`, and `blocked_state_refs`.
- Store accept, correct, and reject decisions append-first.
- Preserve rejected decisions so stale candidates do not silently return.
- Store correction summaries as redacted safe refs only.
- Add routes:
  - `GET /control-center/memory/review`
  - `GET /control-center/memory/review/{candidate_ref}/receipt`
  - `POST /control-center/memory/review/{candidate_ref}/accept`
  - `POST /control-center/memory/review/{candidate_ref}/correct`
  - `POST /control-center/memory/review/{candidate_ref}/reject`
- Preserve authority boundaries.
- Accept/correct create reviewed recall-only `LocalMemoryStore` records, not
  truth authority or automatic prompt/context injection.
- Governed Cognitive Memory Spine Phase 2 derives a read-only L1 hot local
  memory index from these reviewed recall-only records at
  `GET /control-center/memory/l1-index`; it does not add hidden context
  injection, automatic recall, embeddings/vector search, semantic search,
  background indexing, or authority.
- Correct stores a safe corrected summary ref posture, not raw content.
- Reject blocks promotion and records evidence.
- No context injection, connector write, CRM sync, or automatic action
  execution.
- Update Memory UI with real accept, correct, and reject controls.
- Show receipt refs after decisions.
- Add an Evidence Timeline entry for every memory decision.

Definition of done: Memory Review decisions are backend-owned, receipt-backed,
evidence-visible, create reviewed recall-only records for accept/correct, and
still do not grant context injection, truth authority, CRM/account sync,
connector writes, action execution, public beta, or production authority.

Proof refs:

- `docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md`
- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `tests/test_fcc_v1_005_memory_review_decisions.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`

## FCC-V1-006 - Evidence Timeline Productization

Status: implemented. Evidence is now the visible proof surface for the new real
loop via `GET /control-center/evidence/timeline`.

Goal: Evidence becomes the visible proof surface for the new real loop.

Tasks:

- Add evidence event types:
  - `action_envelope_created`
  - `action_decision_recorded`
  - `chat_turn_receipt_recorded`
  - `chat_handoff_created`
  - `memory_review_decision_recorded`
- Add an evidence summary route or carefully extend the existing Today summary.
- Prefer a dedicated evidence index route if the current Today route becomes
  overloaded.
- Keep safe refs and redacted summaries only.
- Update Evidence UI to show events grouped by Today item, Action, Chat turn,
  and Memory candidate.
- Show receipt refs, approval refs, idempotency refs, blocked states, and
  rollback posture.

Definition of done: met. Evidence Timeline is no longer just posture. It shows
the actual audit trail for the first real Founder loop as backend-owned safe
refs only.

Proof:

- `docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`
- `scripts/verify_fcc_v1_006_evidence_timeline_productization.py`
- `tests/test_fcc_v1_006_evidence_timeline_productization.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`

## FCC-V1-007 - Promotion And Proof Lane

Status: Implemented.

Goal: promote only the routes that actually became real.

Tasks:

- Add a focused proof command, such as:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_founder_loop_v1.py
```

- The proof command should validate the release surface manifest, route
  metadata, idempotency posture, receipt creation, Evidence Timeline update,
  and no raw-content leaks.
- Add pytest lanes for Action lifecycle tests.
- Add pytest lanes for Chat receipt and handoff tests.
- Add pytest lanes for Memory decision tests.
- Add pytest lanes for Evidence Timeline tests.
- Add Control Center route/render tests.
- Update release surface manifest statuses.
- Promote `/actions` only when backend state changes are real.
- Promote `/evidence` only when it displays actual receipt/evidence events.
- Promote `/chat` only when receipts and handoff work.
- Promote `/memory` only when accept/correct/reject work.
- Keep `/inbox`, `/settings`, and model lifecycle surfaces `blocked` or
  `partial` unless separately implemented.

Target definition of done: the proof lane can distinguish proofed route
surfaces from partial, blocked, or experimental surfaces, and promotion cannot happen without
manifest, route metadata, receipt, evidence, frontend, and redaction proof.

Definition of done: met. `/actions`, `/chat`, `/memory`, and `/evidence` use
`founder_loop_v1_proofed` route-status truth and `ship` release-surface truth
for their exact receipt-backed route behavior only. `/today` remains partial,
and `/inbox`, `/settings`, and model lifecycle surfaces remain blocked or
partial.

Proof:

- `docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`
- `scripts/verify_founder_loop_v1.py`
- `tests/test_founder_loop_v1_proof_lane.py`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`
- `apps/control-center/src/routes.tsx`

Still denied: action execution, handoff execution, context injection, automatic
memory writes, memory truth authority, connector writes, CRM/account sync,
provider/model authority, shell/subprocess authority, public beta, public
release, and production authority.
