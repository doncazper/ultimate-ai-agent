# Control Center Product Language Rules

Status: active UAA-P1-031 product language rules
Baseline: v0.104.0 / 0.104.0
Source plan: `docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md` M172
Scope: Control Center UI strings and release-facing product docs
Readiness taxonomy: `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`

This ruleset is an enforceable language contract for production-facing copy. It
does not add runtime authority, backend routes, frontend controls,
shell/subprocess behavior, unrestricted network or browser automation,
connector writes, plugin runtime import, mobile control, autonomous background
execution, public distribution, or production readiness claims.

Control Center and OpenWebUI remain shells. Python Agent Core, PolicyEngine,
LocalApprovalAuthority, route side-effect classification, OpenAPI checks, and
Foundation Gate checks remain the authority boundaries.

Control Center is the first-party product UI for Start Here, Today, Action
Inbox, Proof, Evidence, Memory, Trust, Settings, Plans, Models, and future
first-party Chat. Founder Loop is the bounded operator workflow inside that
shell. Founder Command Center is a strategy and north-star planning label, not
a second app name or a separate runtime surface. OpenWebUI is a supported
local/dev conversational shell and compatibility surface only; copy must not
imply that OpenWebUI owns product state or is where every UAA workflow will be
wired.

Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and Settings
are the current beta-05 repo-safe daily-loop surfaces for product-language
enforcement. Source Inbox remains visible in primary navigation for route
reachability and visual-baseline continuity, but it is a supporting
source-readiness surface until read-only connector/source contracts graduate; it
must not be described as the primary daily work queue.

Action Inbox may be described as a real backend-owned work queue only when copy
is tied to `action_inbox_work_queue_read_model`, exact safe refs, approval
posture, receipt posture, proof refs, blocked authority refs, unsafe-ref
omission posture, and no-fake-mutation-control flags. It must not describe lane
filters, fallback data, approval refs, rollback refs, or safe-disable refs as
execution authority.

Proof Detail and Run Detail copy must describe backend-owned safe-ref
inspection, not execution. Proof refs, run-detail refs, approval refs,
rollback refs, and safe-disable refs are identifiers/evidence posture only and
must not be described as granting authority, applying changes, running tools,
sending connector data, calling providers, or completing blocked work.

The inherited founder-loop wording still applies to Today, Inbox, Plans,
Actions, Memory, Evidence, and Settings when checking older shell and
documentation guardrails.

## Usable Authority Tiers

Use `docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md` and
`docs/control_center/operational_maturity_manifest.json` for the current
low-friction authority tier vocabulary:

- Tier 0 UI/ephemeral state: presentation-only local UI state can stay in
  React/local browser state and must not imply durable operator truth.
- Tier 1 local read/preview: backend-owned local read models, safe refs,
  redacted previews, summaries, and proof details do not need approval when
  they have no side effect.
- Tier 2 local draft/proposal: local drafts and proposals do not need approval
  to create; approval starts only when the operator commits, sends, applies, or
  executes the draft.
- Tier 3 reversible local mutation: exact local mutation lanes may use
  lightweight/session-scoped approval or visible undo/safe-disable only when
  the Python core owns receipts and state.
- Tier 4 external mutation: sends, connector writes, paid provider calls,
  external account changes, and filesystem writes outside safe local scopes
  require exact approval, idempotency, receipt, redaction, safe-disable, and
  rollback or compensating posture.
- Tier 5 background/standing authority: scheduled, repeated, autonomous, or
  standing authority requires a separate scoped graduation and visible
  revocation, queue, budget, retry, timeout, and kill posture.

Draft available is not send available. Preview available is not runtime
execution. Product copy should let Tier 1 and Tier 2 work feel usable when the
backend read/proposal contract exists, while still blocking provider/model
calls, connector writes, browser automation, shell/subprocess execution,
runtime context injection, background autonomy, public release, and production
authority unless a later exact lane proves them.

## Governed Runtime Pilot Language

The v0.105.0 Governed Runtime Pilot is allowed as scoped milestone language
only when copy preserves the current truth:

- `sealed` is the default runtime profile and means no runtime model call or
  command execution.
- `local-runtime` may describe configured loopback/local runtime candidates
  behind RuntimeGateway policy, redaction, receipts, and verifiers only after
  the matching Python Core contracts are implemented. Phase 04 permits one
  exact allowlisted argv-only read-only local status command with redacted
  receipts. Phase 05 permits focused pytest, repo-verifier, and frontend-check
  command execution only after an exact validated `operator-approved` Action
  Inbox approval envelope; arbitrary commands remain blocked. Phase 06 may
  describe `uaa runtime ...`, `uaa actions approve|deny ...`, Control Center
  readiness/status cards, and runtime evidence timeline refs only as
  backend-owned inspection and exact-envelope decision surfaces. Phase 07 may
  describe command root pinning, configured endpoint matching, receipt-detail
  execution truth, approval preflight, blocked retry replay hardening, and
  Foundation Gate/frontend/visual release checks only as scoped internal
  RuntimeGateway pilot hardening.
- `operator-approved` may describe execution-capable runtime actions only when
  exact Action Inbox approval envelopes validate before execution and the same
  action is inspectable through CLI/API/Control Center truth.

The Governed Product Pilot authority profile may be described as a local
governed pilot profile only when copy also preserves the sealed/default profile
as deny-by-default. The profile may name exact local RuntimeGateway lanes,
portable local hash evidence envelopes, durable run orchestration posture, and
CLI/API/Core parity through
`GET /api/runtime/governed-product-pilot-profile`,
`scripts/dev/uaa_runtime.py authority-profile`, and the Python Core contract.
It must not be described as production authority, public beta, public release,
unrestricted provider/model authority, generic tool execution, unrestricted
shell/subprocess authority, browser automation, connector writes, plugin
runtime import, remote execution, broad autonomy, or raw prompt/response/
provider-payload/log/local-path persistence.

Allowed pilot copy may say that UAA is working toward governed local runtime
authority through RuntimeGateway. It must also say which portion is
implemented, planned, blocked, or pilot-scoped. The pilot must never be
described as unrestricted shell access, unrestricted provider/model authority,
browser automation, connector write authority, plugin runtime import, remote
execution, public beta, public release, production readiness, production
authority, or broad autonomy. Runtime receipts must be described as redacted,
bounded, safe-ref-only evidence; they must not imply raw prompt, raw response,
provider payload, command output, local path, environment dump, credential, or
secret-like durable persistence.

CRM and Communications copy is allowed as a contract-first product-line
language lane only when it preserves Control Center as the current first-party
shell and Founder Loop as the bounded operator workflow. CRM copy must
distinguish historical fixture proof, current backend-owned local read posture,
proposal posture, and callable runtime. It may name the current `/crm` Control
Center route as the CRM Local Command Center M2 only when it also says the lane
is local-first, backend-owned, safe-ref-only, partial, and blocked from
connector/source runtime and external writes. It may describe exact local CRM
mutation receipts only when idempotency, exact `LocalApprovalAuthority` scope,
and redacted receipt posture are present. It must not imply connector runtime,
connector writes, account auth, contact sync, contact import commit, sends,
calendar writes, silent merges, silent contact creation, model/provider calls,
live web, browser runtime, public beta, public release, production readiness,
or production authority until an accepted milestone adds the exact capability.

North-star visuals are allowed only as design direction. They must be labeled
as north-star visual targets and must not be described as shipped
implementation evidence unless matching route/API/UI behavior is verified.

CLI is a first-class operator surface. Product behavior must not live only in
React state; UI-only state is limited to presentation concerns such as filters,
expanded panels, selected tabs, and layout preferences. If the UI can trigger or
mutate an operator-relevant workflow, the same underlying operation must have a
Python core/API contract and a command-line or repo-local script inspection path
with tests and redacted evidence.

## Rules

| Rule | Required wording behavior | Release blocker |
|---|---|---|
| No hidden authority | Operator-critical copy must name or link the route, side-effect class, approval requirement, authority boundary, and evidence output. | Any visible action that implies authority without a route/status manifest entry is blocked. |
| No fake completion | Preview, validation, mock fallback, local UI state, and status-only views must say what did not happen. | Any unimplemented, blocked, skipped, or local-only action described as completed is blocked. |
| No standalone module completion | Module state visible in Today, Actions, Evidence, or Memory is necessary but not sufficient for completion. Copy must still name the typed contract, tests, redaction/policy gates, route/API or CLI inspection path, and blocked follow-on work. | Any module described as complete solely because it appears in the Today loop is blocked. |
| No raw JSON as primary UI for operator-critical flows | Human summaries, safe refs, route status, evidence refs, and blockers must appear before developer payload inspection. | Any chat, plan, model, approval, file, settings, evidence, latency, or rollback flow that relies on JSON as the main operator view is blocked. |
| No frontend-only product behavior | Operator-relevant workflows must identify the backing Python core/API contract and command-line or repo-local script inspection path. | Any Today, Inbox, Plans, Actions, Memory, Evidence, or Settings workflow that exists only in Control Center React state is blocked. |
| No backend status/UI truth drift | Rank 2+ backend-owned status routes must have a manifest `ui_status_binding`: surfaced through the Control Center API/client/type/component/test layer, or explicitly marked backend-only with a reason, doc ref, and blocker ref. | Any UI copy that says a surfaced backend status route is missing, mock-only, UI-only, not wired, or placeholder-only is blocked. |
| No blanket read-only shell claim when scoped authority exists | Global shell copy must distinguish no generic execution from exact, backend-approved local authority lanes such as Action Inbox `local_task_create`. | Any top-level copy that says the whole Control Center has no authority while an approved receipt-backed micro-lane exists is blocked. |
| No Action Inbox execution drift | Action Inbox may say `Record approval receipt`, `Record edit receipt`, `Record rejection receipt`, `Record defer receipt`, `Create local task record`, `Execute exact approved RuntimeGateway focused pytest command`, `Execute exact approved RuntimeGateway repo-verifier command`, and `Execute exact approved RuntimeGateway frontend-check command` when backed by the Python Core queue/read model, exact runtime envelope, CLI/API/Control Center refs, and receipt routes. The `local_task_create` lane creates local UAA task state only, and the runtime command lanes are focused pytest, repo-verifier, and frontend-check only. | Any Action Inbox copy using broad `Run`, `Execute`, `Send`, `Sync`, `Write`, `Approve action`, or generic `Apply` language is blocked unless a later exact authority lane proves connector write/send, provider/model call, broader shell/subprocess execution, browser execution, memory write, context injection, external side effect, rollback execution, public beta/release, production readiness, or production authority. |
| No production/public distribution claims without evidence | Copy must say production readiness and public distribution are not claimed unless an accepted release packet proves otherwise. | Any public or production claim without source, test, verifier, release note, and rollback evidence is blocked. |
| No model/provider output as authority | Model, provider, OpenWebUI, runtime, memory, and preview outputs may inform review but cannot authorize work. | Any copy that treats output as approval, truth authority, or execution authority is blocked. |
| No governed runtime pilot overclaim | Runtime pilot copy must name the active profile, approval posture, RuntimeGateway boundary, receipt/evidence posture, and blocked follow-on authority. `local-runtime` and `operator-approved` are exact scoped profiles, not blanket capability labels. | Any copy implying broad model/provider calls, arbitrary shell/subprocess execution, browser automation, connector writes, plugin runtime import, remote execution, raw prompt/response/provider payload/local path/command output persistence, public beta, public release, production readiness, production authority, or broad autonomy from the pilot is blocked. |
| No provider catalog authority drift | Provider setup and pricing guidance must say it is reviewed static metadata only. Provider guidance is not credential enrollment, pricing guidance is not billing authority, provider docs links are not runtime fetches, and catalog visibility is not callable runtime authority. | Any copy implying key capture, key storage, provider validation, provider connection, model invocation, automatic pricing refresh, billing authority, or provider output authority from the catalog is blocked. |
| No provider credential/cost readiness authority drift | Provider credential readiness and CostGovernor binding must say they are backend-owned safe-ref posture only. Configured/not-configured/revoked labels are metadata, unknown paid cost requires explicit approval, and future provider usage requires provider/model refs, cost estimate refs, budget decision refs, max-approved USD refs, and usage/cost receipt refs. | Any copy implying secret entry, credential validation, provider connection, provider SDK calls, model invocation, billing authority, spend authority, unknown paid-cost bypass, receipt bypass, or callable provider runtime from readiness/cost posture is blocked. |
| No credential vault contract authority drift | Credential vault shell records must say they are metadata-only safe refs. Credential Vault Backend V1 may say local safe-ref ledger only. Secret-ref availability, revoked, rotation-required, validation-required, and invocation-approval posture are review/blocker states only. | Any copy implying secret resolution, key paste, raw key display, OS keychain/Credential Manager access, provider validation, provider connection, provider SDK calls, model invocation, billing authority, provider runtime authority, or invocation authority from vault presence is blocked. |
| No provider invocation promotion authority drift | Exact-approved provider lane copy must say the current lane is disabled by default, exact-approval-bound, CostGovernor-gated, receipt-backed, and non-authorizing unless a later scoped adapter enablement milestone grants exact authority. It may name credential/provider/model refs, policy validation, exact approval, CostGovernor decisions, max-approved USD, redacted receipt refs, actual usage/cost refs, receipt completeness, incomplete-cost review, further-use-blocked posture, safe-disable posture, CLI parity, two named single-provider adapter scope refs, and UI blocked/approved/cost-blocked states. | Any copy implying provider SDK calls by default, enabled runtime invocation, credential validation, network calls outside exact-scoped adapters, fallback execution from adapter visibility, autonomous model calls, background execution, model output authority, raw prompt/response/provider payload persistence, broad provider-enabled toggles, billing authority, actual-cost bypass, incomplete-cost bypass, or callable provider runtime from the lane is blocked. |
| No provider credential validation authority drift | Exact-approved provider credential validation copy must say validation is one-provider, exact-approval-bound, policy/idempotency-bound, redacted-receipt-only, and not model invocation. It may show validation blocked, credential valid, credential invalid, approval required, and no provider authority states from backend data. | Any copy implying broad provider connection, provider SDK authority, chat/completions, model invocation, provider payload persistence, raw credential display, fallback, autonomous/background calls, billing authority, spend authority, provider output authority, or production authority is blocked. |
| No provider router dry-run authority drift | Provider router dry-run copy must say it is proposal-only local posture over safe refs. It may explain exact-approval candidate, blocked, degraded, cost-risky, validation-required, missing-credential, no-authority, and recommended exact approval scope refs. | Any copy implying provider invocation, fallback execution, network calls, provider SDK calls, credential validation, model calls, billing authority, autonomous/background calls, raw prompt/response/provider payload persistence, or broad provider router authority is blocked. |
| No provider/tool runtime safety contract authority drift | Provider and tool runtime safety contract copy must say the lane is contract-only, run-bound, exact-approval-bound, CostGovernor-gated, receipt-backed, safe-ref-only, and disabled for runtime activation. Unknown provider/tool refs must be described as blocked, not read-only or noop. | Any copy implying provider/model calls, provider SDK calls, arbitrary or dynamic tool execution, callable runtime activation, live streaming, scheduler/background worker behavior, connector writes, live web/browser/shell execution, billing authority, raw prompt/response/provider/tool payload persistence, public beta, public release, or production authority is blocked. |
| No connector delivery semantics authority drift | Connector delivery semantics copy must say the lane is contract-only, safe-ref-only, no-send, no-write, and blocked for runtime delivery. Target/session refs and outbound approval refs are identifiers only. | Any copy implying sent/delivered messages, email/calendar/CRM/message writes, account sync, OAuth, credential collection, connected accounts, live connector runtime, attachment download, background delivery workers, scheduler behavior, provider/model calls, live web/browser/shell execution, raw message/contact/file/path/account/credential persistence, public beta, public release, or production authority is blocked. |
| No fusion routing/delegation authority drift | Fusion routing and delegation copy must say work classification, route visibility, delegation proposal, cache/context posture, and private dogfood records are backend-owned review aids only. It may show selected/rejected/blocked route posture, proposed future-only delegate role, human-review posture, cost/context refs, blocked authority refs, and local/private safe-ref evidence. | Any copy implying worker runtime, automatic dispatch, action execution from classification, model/provider invocation, runtime model switching, approval shortcut, standing grant, connector writes, memory writes, context injection, raw prompt/response/provider payload persistence, benchmark superiority, public distribution, or production authority from this lane is blocked. |
| No MCP gateway authority drift | MCP gateway copy must say the current lane is metadata/import foundation only. It may name MCP discovery metadata, MCP-to-UAA capability candidates, risk/authority/cost/privacy/receipt metadata, preview/dry-run contracts, exact approval-binding contracts, blocked receipts, replay/audit refs, revocation refs, and the capability promotion ladder. Unknown MCP tools must be described as blocked/review-required, not read-only. | Any copy implying MCP runtime calls, generic `tools/call`, subprocess server start, network transport, OAuth runtime, secret resolution, connector writes, provider/model calls, browser automation, React/model/provider direct MCP calls, public marketplace support, public distribution, production authority, or read-only treatment for unknown MCP tools is blocked. |
| No A2A gateway authority drift | A2A gateway copy must say the current lane is metadata/import foundation only. It may name A2A agent-card metadata, spec-shaped A2A 1.0 fixture parsing, A2A-to-UAA capability candidates, task/handoff proposal envelopes, requested grant refs, trust/auth/activation posture, exact delegation approval-binding contracts, blocked receipts, replay/audit refs, revocation refs, and the capability promotion ladder. Unknown A2A agents must be described as blocked/review-required, not read-only or delegation-ready. | Any copy implying A2A support, remote dispatch, peer-auth runtime, gRPC/HTTP execution, public agent-card discovery, remote approvals, remote self-approval, connector writes, remote tool invocation, browser/shell execution, provider/model calls, direct React/model/provider A2A calls, live delegation, public distribution, production authority, or read-only treatment for unknown A2A agents is blocked. |
| No browser gateway ladder authority drift | Browser Gateway Ladder copy must say the current lane is contract-only and routed through WebAccessGateway. It may name browser intent metadata, observe planned/blocked posture, action dry-run planned/blocked posture, exact approval-binding refs, blocked receipts, replay/audit refs, redacted page/source refs, revocation refs, safe-disable refs, and the capability promotion ladder. Unknown browser capability metadata must be described as blocked/review-required, not read-only. | Any copy implying live web fetching, live browser observe runtime, browser execution, click/form/auth/cookies/download/upload/mutation authority, raw page/DOM/HTML/screenshot/provider payload persistence, direct browser automation imports or calls, provider/model calls, connector writes, React/model/provider direct browser authority, runtime activation, public beta, public release, production authority, or read-only treatment for unknown browser metadata is blocked. |
| No background/autonomous provider-call promotion authority drift | Background and autonomous provider-call copy must say the current lane is planning-only and blocked until a later scoped promotion proves a scoped autonomy window, exact provider/model refs, exact credential refs, per-window/per-request/per-session spend limits, CostGovernor hard blocks, queue inspection, kill switch, revocation, replay/audit, red-team checks, UI/CLI parity, explicit human approval boundaries, incomplete-cost blocking, and safe-disable or rollback posture. | Any copy implying background execution, scheduler runtime, autonomous model calls, provider calls, runtime activation, billing authority, broad provider router authority, hidden queues, hidden retries, raw prompt/response/provider payload persistence, incomplete-cost bypass, hidden prompt injection, approval reuse outside exact scope, new API runtime route availability, public beta, public release, or production authority is blocked. |
| No provider billing authority drift | Provider billing authority copy must say the current lane is planning-only and blocked until a later scoped promotion proves exact per-request or per-session max USD approval, CostGovernor hard limits, actual usage/cost receipts, incomplete-cost blocking, revocation, UI/CLI inspection, audit/replay posture, safe-disable/rollback posture, and no broad spend toggle. It may name `no_billing_authority`, `per_request_max_usd`, `per_session_max_usd`, `spend_window_exhausted`, `unknown_cost_blocked`, `incomplete_cost_blocked`, and `billing_review_required` states. | Any copy implying billing integration, payment methods, subscription management, broad spend toggle, provider calls from billing posture, autonomous/background calls, runtime activation, production billing claims, unknown-cost bypass, incomplete-cost bypass, raw prompt/response/provider payload persistence, public beta, public release, or production authority is blocked. |
| No memory-derived execution claims | Memory review, L1/L2/L3 indexes, context packs, and Phase 6 execution-hook contracts must be described as recall, inspection, proposal, or blocked proof surfaces only. | Any copy implying memory/context packs execute actions or that Phase 6 hooks are shipped/available is blocked. |
| No Evidence/Memory loop binding authority drift | Evidence/Memory loop binding copy must say the lane is backend-owned, safe-ref-only, and explanatory. It may show why memory appeared, what evidence supports it, and linked action/run/proof/receipt refs. | Any copy implying memory truth authority, runtime context injection, automatic memory write, memory delete/export, action execution, connector write/send, provider/model calls, shell/browser runtime, background autonomy, public beta, public release, or production authority is blocked. |
| No Trust authority map drift | Trust copy must say it is a backend-owned authority map over current tiers, proof refs, verifier refs, approval posture, and blocked capability refs. Draft available is not send available; preview available is not runtime execution. | Any copy implying Trust grants authority, approve-all, standing authority, connector write/send, provider/model calls, browser or shell execution, runtime context injection, background autonomy, public beta, public release, production readiness, or production authority is blocked. |
| No memory workbench authority drift | FCC-MEM-001 workbench, search, lifecycle receipts, and manual intake must be described as safe-ref review/read-model behavior. Manual intake creates candidates only; defer, merge, supersede, and forget-request are posture/receipt states only. | Any copy implying delete/export execution, semantic/vector search, hidden context injection, connector writes, CRM/account sync, or production authority from the workbench is blocked. |
| No model lifecycle completion words without backend receipts | Words such as loaded, running, switched, and updated identity require backend receipt/evidence refs from Python Agent Core. Without those refs, use planned, blocked, unknown, or status-only language. | Any Control Center or OpenWebUI copy that treats React state, `/v1/models`, logs, or model output as proof of local model lifecycle completion is blocked. |
| No completed-state language for blocked/skipped/pending work | Blocked, skipped, pending, mock-only, local-state-only, and partial states must keep that state visible. | Any blocked, skipped, pending, mock-only, or partial item labeled done, finished, succeeded, or completed is blocked. |
| No visual target as shipped evidence | Product north-star screenshots must say they are visual targets only. | Any north-star screenshot used as proof of implementation, public beta readiness, production readiness, connector authority, or workflow completion is blocked. |

## Approved State Language

Use the canonical operator-readiness taxonomy in
`docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`. These words are approved
when they match the implementation and evidence:

- shipped
- planned
- status available
- preview only
- validation only
- review only
- local UI state only
- mock only
- mock_only
- fixture_only
- read_only
- proposal_only
- partial
- blocked
- implemented
- pending evidence
- skipped prerequisite
- not scoped
- status-only
- unknown
- needs review
- accepted failure
- north-star visual target

Completion words are allowed only when the implementation produced accepted
durable evidence for the exact work described. A route returning a preview,
validation decision, local UI state change, mock fallback, or skipped
prerequisite is never completion evidence.

CRM and Communications state words with underscores are schema-facing aliases
for the same operator truth. Drafts are not sends. Calendar proposals are not
calendar writes. Identity match candidates are review candidates, not silent
merges. Derived contacts are review candidates, not silent contact creation.

MCP gateway state words must distinguish metadata/import foundation from
callable runtime. Unknown MCP tools are blocked and review-required, not
read-only. MCP metadata import, preview contracts, approval-binding contracts,
blocked receipts, replay/audit records, and revocation refs do not imply
`tools/call`, server start, transport, OAuth, connector writes, provider/model
calls, browser automation, A2A remote dispatch, remote approvals, or production
authority.

Browser Gateway Ladder state words must distinguish contract-only posture from
browser runtime. Unknown browser capability metadata is blocked and
review-required, not read-only. Browser intent metadata, observe planned/blocked
posture, action dry-run planned/blocked posture, exact approval-binding refs,
blocked receipts, replay/audit records, redacted page/source refs, revocation
refs, and safe-disable refs do not imply live web fetching, browser observe
runtime, browser execution, click/form/auth/cookies/download/upload/mutation
authority, direct browser automation imports or calls, provider/model calls,
connector writes, runtime activation, public beta, public release, or production
authority.

Skill Workbench state words must distinguish external metadata and adoption
review from local enablement. `external_metadata_only`, `candidate`,
`quarantined_untrusted`, `review_required`, `rejected`,
`adapted_uaa_owned`, `enabled_local`, and `blocked_by_policy` are allowed only
when they match backend-owned contracts. External popularity, stars, downloads,
reviews, publisher claims, and marketplace screenshots are discovery signals,
not trust. Skill Workbench copy must not call the surface a Skill Store and must
not imply external skill install, wholesale external-code copy, runtime import,
execution, package-manager scripts, browser marketplace UX, provider/model
calls, connector writes, local enablement, public beta, public release, or
production authority until later exact lanes prove them.

Provider and tool runtime safety state words must distinguish contract-only
run binding from callable runtime. Unknown provider/tool refs are blocked and
review-required, not read-only or noop. Invocation envelopes, result contracts,
redacted stream event contracts, validation decisions, replay sanitization,
approval refs, cost refs, receipt refs, and evidence refs do not imply
provider/model calls, provider SDK calls, arbitrary tool execution, live
streaming, scheduler/background worker behavior, connector writes, shell/browser
execution, billing authority, public beta, public release, or production
authority.

## UI Requirements

Operator-critical surfaces must show a human-readable state first. Safe refs,
route names, side-effect classes, approval requirements, and evidence refs can
support that state, but they cannot replace it.

Buttons and menu labels must describe the real action available in the current
UI. Preview-only controls use preview/review/view wording. Local-state-only
controls must say review-only or local state. Disabled or missing work must stay
blocked, partial, or not scoped.

Future Control Center surfaces for Today, Inbox, Plans, Actions, Memory,
Evidence, Settings, Models, and first-party Chat must remain inspectable
through backend/core contracts and, where appropriate, CLI commands or
repo-local scripts. The frontend can make those workflows easier to operate,
but it cannot become the only access path.

Status panels must avoid standalone readiness claims. When a backend field uses
a readiness-shaped name, the UI must frame it as a claim status or evidence
status and keep false/unproven values visibly unclaimed.

## Current Gaps

The current Control Center still has blocked, mock-only, local-state-only, and
partial surfaces. The route status manifest is the current release evidence for
visible action truth, not evidence that the full operator loop is complete.
FCC-V1-007 proofed only `/actions`, `/chat`, `/memory`, and `/evidence` for
their exact backend-owned route-surface behavior. Chat handoff execution,
Models lifecycle controls, Settings, Inbox, broader Today-spine completion,
CRM connector reads, CRM sends/writes, connector workflows, public beta, public
release, production readiness, and production authority remain blocked or
partial until later gates add reviewed routes, UI, evidence, and rollback
proof.

## Enforcement

These checks enforce the rules:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
```

`scripts/verify_control_center_frontend.py` checks the Control Center copy,
route status manifest, and required product-language documentation. The
documentation integrity verifier checks release-facing doc links, product-truth
claims, Kanban status, and unsafe public or production language.

## Rollback

Rollback is to remove this document, remove its active links, remove the
P1-031 verifier/test assertions, restore the previous two runtime status
labels, and move UAA-P1-031 out of Done on the Kanban board. No runtime state,
route, authority, migration, or persistent user data is changed.
