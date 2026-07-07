# Usable Authority Mode And Mission Lease Plan

Status: planning-only mode/domain/AuthorityLease implementation plan at a
legacy compatibility path; does not grant runtime authority
Scope: make UAA feel like a usable local-first command center while preserving
explicit AuthorityLease boundaries

## Problem

UAA has strong governance, but the product can feel blocked because authority
rules are currently exposed too much as product behavior. The goal is not to
remove governance. The goal is to move governance into the implementation layer
and apply friction only where consequences justify it.

The operator should experience:

- Here is your day.
- This needs your decision.
- I drafted this.
- Approve to send/apply/commit.
- Done. Here is the receipt.
- Here is why I suggested it.

The operator should not have to experience every surface as a wall of
contract-only, blocked, planned, or future-scoped states.

Compatibility note: this file path is retained for existing verifiers and
prompt references. The product model is no longer one-off lane promotion. The
durable model is operator-selected trust mode, explicit authority domain,
capability, session/mission AuthorityLease, policy decision, receipt, audit,
redaction, rollback/safe-disable posture, and visible kill switch.

## Product Doctrine

Earned authority, low friction by default, strict only where consequences
justify it.

UAA should aggressively ship useful low-risk product behavior:

- local UI state
- local read models
- previews
- drafts
- proposals
- review artifacts
- reversible local mutations

UAA should stay strict at consequence boundaries:

- external sends or writes
- paid provider/model calls
- filesystem mutation outside safe scopes
- connector account changes
- shell/subprocess execution
- browser actions
- background/standing authority
- production/public release claims

## Authority Tiers

### Tier 0: UI And Ephemeral State

Examples:

- selected tabs
- expanded cards
- filters and sorting
- unsaved draft text
- onboarding step display
- layout preferences

Rules:

- React/local UI may own this.
- No backend authority required.
- No approval receipt required.
- No product truth may be inferred from this state.

### Tier 1: Local Read And Preview

Examples:

- Today summary
- Action Inbox read model
- Evidence Timeline
- Memory Review read model
- Trust matrix
- proof detail inspection
- context pack preview
- file read preview
- web evidence preview

Rules:

- No approval required.
- Python Core/API owns durable product truth.
- Redaction and safe refs are required where data is sensitive.
- Lightweight audit/event refs are enough.

### Tier 2: Local Draft And Proposal

Examples:

- email draft proposal
- calendar draft proposal
- task proposal
- plan proposal
- file patch proposal
- provider/model draft output
- source-to-action proposal

Rules:

- No external side effect.
- No approval required to create the draft/proposal.
- Approval is required only to commit, send, apply, or execute.
- Draft/proposal status must be visible and backend-owned if operator-relevant.

### Tier 3: Reversible Local Mutation

Examples:

- create a local UAA task
- edit a local action proposal
- accept/correct a reviewed memory item
- archive or defer a local review item
- update local settings

Rules:

- Approval can be lightweight and session-scoped where the risk is low.
- Undo, rollback, supersede, or safe-disable must exist where practical.
- Receipts should exist, but they should not dominate the main workflow.
- The UI should behave like a normal app with visible undo/status.

### Tier 4: External Mutation

Examples:

- send email
- create or modify calendar event
- write to CRM
- post a message
- execute a filesystem write beyond safe local scopes
- call paid provider/model endpoint
- execute shell/subprocess command

Rules:

- Exact approval required.
- Idempotency required.
- Receipt required.
- Safe-disable required.
- Rollback or compensating action posture required.
- Redaction and tests required.

### Tier 5: Background Or Standing Authority

Examples:

- scheduled connector sync
- auto-send
- background provider calls
- recurring browser/shell work
- autonomous action selection

Rules:

- Explicit AuthorityLease mode/domain/capability expansion required.
- Policy decisions must remain one of allow, ask, deny, or degrade_to_draft.
- Revocable scope required.
- Expiry, pause/cancel/revoke, and kill switch visibility required.
- Budget, rate, retry, timeout, and observability limits required.
- Receipts, audit refs, redaction, rollback/safe-disable posture, and CLI/API
  parity required before the operator can rely on the authority.
- No hidden execution.

## Constraint Reframe

The existing constraints remain valuable, but they should be applied by tier.

Keep as global rules:

- Python Agent Core owns durable product truth.
- Control Center may present and initiate, but not invent durable truth.
- External side effects require exact authority.
- Broad autonomy remains denied unless an explicit AuthorityLease scope, policy
  decision, receipts, tested adapter, and operator-visible kill switch prove the
  specific domain/capability.
- No hidden context injection.

Loosen for product usability:

- UI-only state is allowed for presentation-only behavior.
- Drafts and proposals should not require approval before they exist.
- Receipts/proof should be available after important events, not interrupt every
  low-risk interaction.
- Raw user data may exist only in scoped local stores where the operator expects
  it, with retention and access boundaries. Raw data must not leak into receipts,
  evidence logs, screenshots, docs, manifests, broad read models, or proof
  surfaces.

Apply strict mutation requirements only to Tier 4 and Tier 5 by default. Apply a
lighter version to Tier 3.

## Target Product Loop

The first complete loop should be narrow, useful, and real:

1. Start Here shows local readiness and the next safe action.
2. Today shows one meaningful daily item.
3. UAA creates or surfaces one local action proposal.
4. Action Inbox lets the operator review it.
5. The operator approves an exact local task commit.
6. UAA commits the local task.
7. UAA shows receipt, evidence event, and proof detail.
8. Trust explains what was allowed and what remains blocked.

This loop does not need connector sends, broad model authority, shell execution,
browser automation, or production authority.

## Primary Product Surfaces

These are the surfaces that must feel real first:

- Start Here
- Today
- Action Inbox
- Run / Proof Detail
- Trust
- Evidence
- Memory
- Settings

Support/system surfaces should not dominate first-use navigation.

## Implementation Sequence

### PR 1: Authority Tier Manifest And Product Language

Goal: encode the tier model so product and verifier language stop treating all
authority as equally dangerous.

Tasks:

- Add authority tier taxonomy to operational maturity/product language docs.
- Map existing authority artifacts to tiers, domains, and capabilities.
- Update Trust/release language to distinguish preview, draft, reversible local
  mutation, external mutation, and standing authority.
- Add tests preventing Tier 1/2 surfaces from being labeled as broad runtime
  authority.

Acceptance criteria:

- Tier 0 through Tier 5 are documented.
- Existing blocked authority remains blocked.
- Product language can say "draft available" without implying "send available".
- Draft available is not send available. Preview available is not runtime
  execution.

### PR 2: Start Here Real Loop Contract

Goal: define the first complete daily loop as a backend-owned read model.

Tasks:

- Add or harden `GET /control-center/start-here/summary`.
- Include readiness state, next safe action, action proposal ref, proof ref,
  evidence refs, blocked authority refs, and local loop status.
- Add CLI inspection for the same read model.

Acceptance criteria:

- Start Here can explain the next useful action without docs.
- Missing prerequisites are specific and actionable.
- No UI-only product truth.

### PR 3: Universal Proof Detail Spine

Goal: make every meaningful product event inspectable.

Tasks:

- Add or harden `GET /control-center/proof/index`.
- Add or harden `GET /control-center/proof/{proof_ref}`.
- Support action decisions, local task commits, memory decisions, evidence
  events, source readiness, approvals, and setup/package proof.
- Add CLI inspection.

Acceptance criteria:

- Proof records use safe refs only.
- Every proof detail includes status, authority posture, route refs, receipt
  refs, evidence refs, rollback/safe-disable posture, redaction state, and next
  safe action.

### PR 4: Action Inbox As A Real Work Queue

Goal: make Action Inbox operate as a normal governed queue.

Tasks:

- Show action source/run/proof refs.
- Show decision state, approval posture, receipt state, and next safe action.
- Wire only exact existing backend mutation routes.
- Keep unavailable controls disabled or omitted.
- Make local task commit path visible after exact approval.

Acceptance criteria:

- Local task proposal can move through review to receipt/proof.
- No broad approve-all.
- No UI-only approval state.

### PR 5: Evidence And Memory Loop Binding

Goal: bind Evidence and Memory to the daily loop.

Tasks:

- Evidence Timeline items link to run/action/approval/receipt/proof refs.
- Memory items show candidate/memory refs, source refs, why-shown refs, related
  action/run/proof refs, and write/context posture.
- Memory recall remains recall, not truth.

Acceptance criteria:

- The operator can answer why an item appeared.
- Reviewed memory write capabilities remain exact-scoped.
- Runtime context injection remains blocked unless a separate
  AuthorityLease-gated capability is implemented, tested, receipted, and
  approved.

### PR 6: Trust As Authority Map, Not Blocker Wall

Goal: make Trust explain usable authority tiers clearly.

Tasks:

- Add or harden `GET /control-center/trust-authority/matrix`.
- Show authority by tier, trust mode, domain, capability, and active lease
  status.
- Distinguish read, preview, draft, reversible local mutation, external mutation,
  and background authority.
- Link rows to proof/verifier/docs refs.

Acceptance criteria:

- Trust says what UAA can do now.
- Trust says what requires approval.
- Trust says what remains blocked.
- It does not make normal draft/preview flows feel blocked.

### PR 7: Web Evidence Product Slice

Goal: productize a real safe web evidence capability.

Tasks:

- Use `WebAccessGateway`.
- Allow only HTTPS GET evidence fetches scoped to a configured host allowlist
  and the operator-supplied per-request host.
- Return bounded redacted previews transiently to the requester; durable Today,
  Evidence, Proof, and CLI inspection surfaces store safe refs and redacted
  WebAccessGateway audit summaries only.
- Attach evidence to Today/Action/Proof where useful.
- Keep the safe-disable env/route-off posture real, so the capability can be
  shut off before transport construction.

Blocked:

- browser actions
- auth/cookies
- downloads/uploads
- POST/PUT/PATCH/DELETE
- raw body persistence in receipts/proofs

Acceptance criteria:

- Operator can attach real web evidence to a loop.
- Prompt injection from fetched content is treated as untrusted data.
- Beta 08 Web Evidence beta slice hardening is verified by
  `scripts/verify_beta_08_web_evidence_product_slice.py`: full-strength Web
  Evidence remains useful real-world evidence and future browser/web
  workflows; the repo-safe version is Tier 1 configured host allowlist HTTPS GET
  through WebAccessGateway with transient preview, durable safe refs, request-ref
  idempotency, safe-disable, rollback posture, and redacted audit summary;
  blocked/needs-authority remains browser actions, auth/cookies, downloads or
  uploads, POST-style mutation, raw body/header/URL persistence, context
  injection, memory write, provider/model call, connector write, public release,
  and production authority; exact promotion requires a later verifier-backed PR
  with scope, approval binding where mutation appears, redaction, CLI/API
  parity, safe-disable, rollback, receipts, and proof. No broad runtime
  authority is added. This capability adds no broad runtime authority.

### PR 8: Provider Draft/Summarize Capability

Goal: make provider-assisted drafting useful and inspectable without granting
broad provider authority.

Full-strength version:

- Provider-assisted draft and summarize workflows can use approved live
  credentials, selected local context, explicit cost limits, receipts, Proof
  Detail, Trust posture, and operator review.

Repo-safe beta-09 version:

- Keep the existing provider draft/summarize capability as an exact core/CLI
  wrapper over the constrained provider path.
- Default inspection remains blocked/no-execution.
- Demo fixture proof uses injected transient test credential, exact
  LocalApprovalAuthority scope, CostGovernor posture, receipt store, and scoped
  transport while reporting no real provider network.
- `/proof` and `/trust` expose backend-owned inspection refs only; no
  provider-draft API route, Control Center invocation button, default live
  provider network, or durable draft preview persistence is added.

Tasks:

- Require exact provider/model/credential refs, user initiation, cost cap,
  safe prompt envelope refs, idempotency, redacted receipts, and proof refs.
- Treat model output as draft/proposal only, never truth or action authority.
- Verify durable records omit the transient draft preview.

Acceptance criteria:

- One exact core/CLI provider draft/summarize wrapper is fixture-proven and
  visible through Trust and Proof as an inspection-only capability.
- Default live credentials and default Control Center invocation remain
  blocked.
- No autonomous provider calls, provider SDK call, broad router fallback,
  output-as-truth, durable raw prompt/response/provider exchange, hidden
  memory/context injection, connector write, action execution, background
  provider call, public release, or production authority.
- Exact promotion requires a later verifier-backed PR with real
  operator-approved test credential, exact approval, CostGovernor decision,
  max-approved USD, receipt-store-before-network, complete usage/cost receipts,
  safe-disable/rollback, CLI/API/UI parity, Trust/Proof updates, and
  route/OpenAPI truth before any stronger provider capability is enabled.

### PR 9: Connector Draft-Only Capability

Goal: make email/calendar usefulness visible before sends/writes.

Full-strength version:

- Connector drafting eventually supports operator-reviewed send/write/sync
  workflows across email, calendar, messages, CRM, and future accounts, with
  exact account and target scope, idempotency, receipts, revocation,
  safe-disable, rollback, redaction, Proof Detail, and Trust posture.

Repo-safe beta-10 version:

- Connector Draft-Only proposals are embedded backend-owned safe refs under
  `GET /control-center/sources/readiness#connector_draft_proposals`, `/inbox`,
  `/proof`, `/trust`, and CLI inspection.
- No standalone or mutating connector draft route is added.
- The older M128 low-risk connector write contract remains outside beta-10 and
  is not wired to Source Readiness, Proof, Trust, or frontend controls.

Tasks:

- Add connector draft proposal read model.
- Support email/calendar draft refs without send/write.
- Show target/session refs, subject/body-summary refs, approval posture,
  idempotency refs, blocked send/write reasons, evidence/proof refs.

Acceptance criteria:

- Operator can see useful draft proposals.
- No connector write/send/account sync/OAuth broadening without exact
  mode/domain/capability scope.
- Verification is covered by `scripts/verify_beta_10_connector_draft_only.py`.

Blocked / needs authority:

- Connector runtime, send, write, sync, OAuth/account auth, auth-material
  collection, source ingestion, delivery workers, memory/context injection,
  provider/model calls, background runtime, public release, and production
  authority remain blocked for this capability.

Exact promotion path:

- A later PR must supply exact scope, test account or target allowlist,
  OAuth/account proof where needed, LocalApprovalAuthority binding,
  idempotency, delivery receipt, redaction, revocation, safe-disable, rollback,
  CLI/API/UI parity, OpenAPI/route truth, docs, and focused tests before any
  connector send/write/sync is promoted.

### Beta 11: Operator Workspace Spine

Full-strength version:

- UAA eventually becomes a useful operator workspace cockpit for workspace
  status, Git posture, preview status, run logs, coworker handoff, command
  receipts, proof, and evidence.

Repo-safe beta-11 version:

- Today, Proof, Trust, and `python scripts/inspect_operator_workspace_spine.py`
  expose a backend-owned `operator_workspace_spine_read_model`.
- The read model shows workspace, Git, preview, run-log, and coworker posture
  as safe refs only. It does not claim live branch/dirty state, raw diffs, raw
  logs, file contents, local paths, terminal access, or browser control.

Blocked / needs authority:

- File writes, patch apply, Git mutation, shell/subprocess execution, browser
  automation, dev-server lifecycle control, provider/model calls, connector
  writes, coworker dispatch, background autonomy, raw path/log persistence,
  public release, and production authority remain blocked.

Exact promotion path:

- Promote one exact domain/capability at a time: exact Git status read,
  dev-server manifest, allowlisted command/test receipt, or coworker handoff
  receipt. Each promotion needs Python Core ownership, route truth if a route is
  added, CLI parity, redaction, proof/evidence receipts,
  safe-disable/rollback, and focused tests.

### PR 10: Approved Test Send Or Test Write Capability

Goal: authorize the first external mutation only after drafts are real.

Current note: connector draft-only proposals are now real safe-ref review
artifacts. This PR must no-go rather than implement if connector read,
test-account credential/OAuth, target allowlist, and send/write receipt
prerequisites are still blocked.

Tasks:

- Pick one low-risk target, such as send-to-self/test-recipient only.
- Require exact approval, target allowlist, idempotency, receipt, safe-disable,
  and proof.

Acceptance criteria:

- One external connector mutation works safely.
- No broad sends.
- No production account access by default.

### PR 11: Frontend Decomposition And Route-Level Loading

Goal: make the product maintainable and reduce fake fullness.

Tasks:

- Split large frontend files by feature.
- Replace global bulk loading with route-level loading.
- Keep shared shell summary small.
- Make panel-level fallback explicit.

Acceptance criteria:

- No primary feature component over 1,500 lines.
- Mock fallback cannot enable controls.
- Proof-required surfaces fail closed.

### PR 12: Visual And Release Hardening

Goal: prove primary surfaces visually and prevent unsafe release posture.

Tasks:

- Add desktop/mobile baselines for Start Here, Today, Actions, Proof, Trust,
  Evidence, Memory, Settings.
- Add release verifier checks for visual proof on primary routes.
- Add release blockers for dev auth bypass and unsafe local model `/v1` posture.

Acceptance criteria:

- Primary product routes have checked visual baselines.
- Package/release proof fails unsafe auth/runtime posture.
- No public beta/production claim is introduced.

## Definition Of Done

This plan is complete when:

- Start Here leads to one complete governed daily loop.
- Action Inbox can commit one exact local task capability and show
  receipt/proof.
- Proof Detail explains every major loop event.
- Trust presents authority by tier without turning every surface into a blocker.
- Evidence and Memory are visibly bound to runs/actions/proofs.
- Web evidence is useful through a safe capability.
- One provider draft/summarize capability is safely available only as an exact
  core/CLI, fixture-proven, default-UI-blocked inspection capability.
- Connector draft-only proposals are real.
- One test external mutation may execute only if exact AuthorityLease scope,
  approval, idempotency, receipts, audit, redaction, safe-disable, and rollback
  or compensating-action posture are proven.
- Primary UI routes have visual baselines.
- Large backend/frontend monoliths are decomposed enough to evolve safely.
- Mock fallback cannot masquerade as authority.
- Existing broad dangerous authorities remain denied unless explicit
  mode/domain/lease scope and tested adapters prove the exact capability.

## Standard Checks

Run focused checks per PR, plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
make frontend-check
```

Run `make frontend-visual-check` for PRs that change primary UI surfaces or the
visual manifest.
