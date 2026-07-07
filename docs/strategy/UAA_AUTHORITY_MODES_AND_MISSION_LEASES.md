# UAA Authority Modes And Mission Leases

Status: active authority foundation canon for AuthorityLease V1
Date: 2026-07-06
Purpose: preserve the product/architecture direction for moving UAA from
permanent blocked-lane posture to governed, operator-selected autonomy.

This document records the active strategic correction from one-off lane
promotion toward mode/domain/lease authority. It is not itself runtime
authority and does not claim unsupported adapters are implemented. It is the
canon and implementation guide for AuthorityLease V1.

## Current Implementation Hook

AuthorityLease V1 is represented in Python Core by
`ultimate_ai_agent.core.authority`. The current operator-visible inspection
surfaces are:

- `GET /api/runtime/authority-state`
- `POST /api/runtime/authority-decisions/preview`
- `POST /api/runtime/authority-missions/plan`
- `GET /control-center/settings/status#authority_lease_state`
- `scripts/dev/uaa_runtime.py inspect-authority-state --json`
- `scripts/dev/uaa_runtime.py inspect-authority-state --summary`
- `scripts/dev/uaa_runtime.py preview-authority-decision --json`
- `scripts/dev/uaa_runtime.py plan-authority-mission --json`
- `POST /api/runtime/authority-leases`
- `POST /api/runtime/authority-leases/approve-and-issue`
- `POST /api/runtime/authority-leases/revoke`
- `scripts/dev/uaa_runtime.py select-authority-mode --approve`
- `scripts/dev/uaa_runtime.py revoke-authority-lease`
- `scripts/dev/uaa_runtime.py command run ... --mission-ref ...`
- `GET /control-center/trust-authority/matrix` rows map legacy compatibility refs to
  AuthorityLease domain, capability, required mode, and lease requirement refs.
- `GET /control-center/trust-authority/matrix#authority_domain_coverage`
  exposes backend-owned coverage rows for every target AuthorityLease domain,
  including implemented, partial, planned, hidden-ref, unsupported-adapter,
  `GET /api/runtime/authority-state`, and
  `repo-local-command:uaa-runtime-inspect-authority-state` inspection posture.
- `GET /control-center/trust-authority/matrix#authority_capability_catalog`
  projects each legacy Trust row into a governed AuthorityLease capability
  entry with mode, domain, capability, lease requirement, source row,
  safe-disable, rollback, blocked-authority, proof, verifier, API, and CLI refs.
  This is the compatibility bridge away from the old lane-promotion product
  concept: operators inspect governed capabilities, not broad allow flags.
- `GET /api/runtime/authority-state#capability_mappings` has at least one
  explicit mapping row for every target AuthorityLease domain; unsupported
  adapters remain `planned` or blocked rows and do not become executable.
- `GET /api/runtime/authority-state#decision_catalog` evaluates every
  capability mapping against the active AuthorityLease set and reports the
  current `allow`, `ask`, `deny`, or `degrade_to_draft` policy outcome with
  safe refs, route/CLI refs, audit refs, receipt refs when applicable, and
  no execution.
- `GET /api/runtime/authority-state#decision_summary` and
  `scripts/dev/uaa_runtime.py inspect-authority-state --summary` provide the
  compact operator/API parity view over the same decision catalog: capability
  totals, outcome counts, status/domain coverage, blocked reason refs,
  unsupported adapter refs, and no execution or mutation.
- `GET /api/runtime/authority-state#mode_catalog` and Control Center
  `/settings` show backend-evaluated readiness for each target trust mode:
  default requested domains, grantable local domain subsets, default grants,
  approval requirements, mission-scope requirements, blocked reason refs, and
  unsupported adapter refs. This catalog replaces lane-graduation copy with
  explicit mode/domain/lease posture; blocked high-authority defaults remain
  blocked until exact adapters and tests exist.
- `UAA_AUTHORITY_LEASE_KILL_SWITCH=1` engages the local AuthorityLease kill
  switch. New lease issue attempts are denied with a redacted receipt and
  `reason-ref:authority:lease-kill-switch-engaged`; state, Settings, CLI, and
  decision previews report `kill_switch_engaged` without executing adapters or
  mutating external systems. The core `evaluate_authority_request` path also
  applies this local kill-switch overlay, so direct route/service evaluators fail
  closed even if they do not pass an explicit request flag.
- Control Center `/settings` authority mode controls for implemented local
  domain subsets, revoke receipts, decision previews for concrete
  mode/domain/capability requests, and mission-plan previews for delegated
  AuthorityLease issue requirements. Issue-ready mission plans may be issued
  through `POST /api/runtime/authority-leases/approve-and-issue`, which captures
  an exact backend-owned LocalApprovalAuthority grant and then uses the same
  strict lease issue path. The lower-level `POST /api/runtime/authority-leases`
  route still denies authority-increasing requests without a matching approval
  grant. CLI `select-authority-mode --approve` is the repo-local parity path for
  capturing the same exact local operator approval without requiring hand-built
  grant JSON. Generic mode controls must send the backend
  `mode_catalog.default_requested_domains` and scope for issue-ready,
  session-scoped modes; mission-scoped defaults remain on the mission planner
  path instead of being issued from a generic button.

The first implementation is deliberately conservative: the default active
lease is read-only; operator-selected session leases persist safe receipts for
implemented local domain/capability subsets; existing governed lanes are mapped
into domains and required trust modes; RuntimeGateway decisions consume the
active lease store for command invocation, approval, and execution policy;
AuthorityLease issue/revoke routes are the mapped `system_settings/write`
control plane for selecting or reducing trust mode and only record idempotent
receipts, audit refs, redaction, rollback/safe-disable refs, and kill-switch
visibility;
authority-increasing issue requests are denied unless the filtered
mode/domain/capability scope validates against an exact LocalApprovalAuthority
grant; missing or invalid approval refs produce denied receipts with the
expected `approval_scope_ref`, approval status, reason codes, and no active
lease;
mode defaults are mode-specific, so Approved Safe Local Work defaults to
Workspace read/write/execute only, while Full Machine and Delegated Mission
defaults request unsupported machine/browser/payment domains and fail closed
until exact-scoped adapters are implemented or the operator explicitly requests an
implemented local domain subset;
Delegated Mission authority must be mission-scoped and bound to a safe
`mission_ref`, not issued as a standing session lease;
mission-bound RuntimeGateway requests carry a safe `mission_ref` through
`RuntimeInvocationRequest`, payload fingerprinting, policy decisions, redacted
storage, and receipt surfaces; mission-scoped leases grant only actions carrying
the matching mission ref in safe action refs, resource refs, or constraints, so a
delegated mission cannot become a broad standing grant;
Control Center `/settings` can preview workspace command, file proposal,
browser-click, and budgeted-purchase decisions against the active lease, and can
plan a delegated mission lease envelope without issuing a lease, executing work,
or mutating anything; issue-ready implemented local mission plans can then issue
the exact backend-generated mission-scoped lease request through the existing
lease receipt route; preview results show required modes, domain and capability
refs, receipt/audit refs, and unsupported-adapter reasons;
Control Center `/settings` and CLI `inspect-authority-state` show active lease
and lease-receipt issued/expires timestamps; Control Center `/settings` and CLI
`select-authority-mode --approve` show approval-required, approval-validated,
approval-status, approval-scope, denial reason, receipt, audit,
rollback/safe-disable, and kill-switch refs for AuthorityLease issue attempts;
unsupported browser/app/payment/calendar/messages/Home Assistant adapters remain
denied or draft-degraded instead of being presented as live execution. Read-only
command status may run under `workspace/read`; execution-capable command lanes
require an active `workspace/execute` lease. Work Board persisted reorder and
local-card-create lanes now require both exact approval and an active
`workspace/write` lease, returning readable authority-denied refs when the
operator remains in read-only mode. Today-to-Action envelope promotion requires
active `workspace/draft` AuthorityLease scope before a local review-only Action
envelope receipt is recorded; stronger local Workspace grants imply lower-risk
draft/prepare authority but still do not authorize execution. Action Inbox
approve/edit/reject/defer decision receipts now require active
`workspace/write` authority before local decision state is recorded; missing
authority records a blocked receipt and does not mint backend-owned approval.
Action Inbox local-task commit likewise requires exact approval plus active
`workspace/write` authority before local Founder Loop task state is written.
Memory Review accept/correct reviewed
recall writes require exact approval plus active `memory/write` authority before
the recall-only `LocalMemoryStore` record is written; reject, defer, merge,
supersede, and forget-request remain receipt/posture decisions without memory
write authority. Memory context-pack internal Action proposal creation now
requires active `memory/draft` AuthorityLease scope plus exact approval and
idempotency before a local proposal/envelope receipt is recorded; it does not
execute the action, inject context, write memory, call providers/models, write
connectors, or grant production authority. CRM local mutations require exact
approval plus active
`contacts/write` authority before local CRM state is changed; connector reads,
connector writes, sends, calendar writes, account sync, and external CRM writes
remain unsupported unless later adapters are implemented and tested.
File preview and tree preview require active `files/read` authority before
safe-root metadata is inspected. File write proposal and diff preview require
active `files/prepare` authority before proposal refs are reviewed. File Review
approval capture requires active `files/write` authority before the review-only
safe-ref record is persisted. AuthorityState distinguishes unsupported adapters
that block the current capability from adjacent blocked adapters: safe file
metadata/proposal and source-readiness metadata rows can evaluate as known
lease-gated capabilities while still showing raw-file, patch-apply, live-fetch,
and live-write adapter refs as unsupported. Raw file access, context injection,
memory writes, export, execution, patch apply, and rollback execution remain
unsupported until separately implemented and tested.
Task Decomposition local plan execution now requires an active
`workspace/execute` AuthorityLease with an `allow` decision before registered
local handlers run. `ask` is not execution authority for task plans until a
separate exact confirmation path validates it. Exact LocalApprovalAuthority
grants remain a separate second gate for approval-bound or high-risk
capabilities inside a plan. In read-only or ask-only mode,
`/task-decomposition/run` and `/task-decomposition/plans/execute` return a
durable, redacted blocked/draft decision with authority decision refs, required
domain/capability refs, audit refs, receipt posture, and rollback/safe-disable
refs instead of silently executing or claiming broad shell/tool authority.
The same task execution authority decision observes the local AuthorityLease
kill switch, so an active workspace lease cannot start registered handlers while
`UAA_AUTHORITY_LEASE_KILL_SWITCH=1` is engaged.
Governed Runtime Action Inbox command execution now re-evaluates the current
active AuthorityLease scope immediately before an approved command starts. A
command that was approved under a workspace execute lease degrades back to a
blocked draft receipt if that lease is no longer active at execution time; old
approval refs and stale policy decision refs cannot keep execution authority
alive.
RuntimeGateway storage does not treat a previously loaded lease snapshot as
durable execution authority: default stores re-read persisted active
AuthorityLease state and the local kill switch at create, approval binding,
safe-disable, and execution-policy refresh boundaries. Test-injected leases are
still deterministic fixtures, but runtime/API paths must observe revocation and
`UAA_AUTHORITY_LEASE_KILL_SWITCH=1` before any adapter runner can start.
Runtime Action Inbox approval envelopes also separate exact
LocalApprovalAuthority validation from AuthorityLease scope allowance, and
approval binding refreshes the current active lease decision so a pending
proposal can become executable after the operator selects the required
mode/domain lease.
Control Center Action Inbox renders those runtime authority facts directly:
authority decision outcome, lease, domain, capability, required mode, audit,
policy receipt, operator message, and blocked reason refs are cockpit-visible
without adding execution controls.
The repo-local `uaa_runtime inspect-action-inbox-bridge` CLI mirrors the same
inspection-only authority facts in readable text for API/CLI parity; it does not
mint leases, approve envelopes, or execute adapters.
The RuntimeGateway invocation lifecycle is also mapped into authority domains:
`POST /api/runtime/invocations` is a workspace draft record-only route,
`POST /api/runtime/invocations/{id}/approve` and
`POST /api/runtime/invocations/{id}/execute` are workspace execute routes with
exact approval/lease gates, and `POST /api/runtime/safe-disable` is a local
safety-control write that can only reduce runtime authority.
The governed runtime local-model call route now also uses the mode/domain
foundation: `POST /api/runtime/local-model/call` requires active
`provider_model_calls/execute` AuthorityLease scope with Full machine access
before the loopback model transport can run. Missing lease scope produces a
degraded draft decision naming Full machine access plus the
provider_model_calls domain and execute capability. The route remains
loopback/configured-endpoint only, records metadata-only receipts, treats model
output as untrusted proposal text, and does not authorize remote provider SDK
calls, tools/functions, streaming, memory/file writes, connector writes,
browser automation, billing, or production authority.
The exact-approved provider invocation capability now requires an active
`provider_model_calls/execute` AuthorityLease before it can proceed to its
existing PolicyEngine, CostGovernor, exact LocalApprovalAuthority, adapter,
idempotency, and redacted receipt gates. The default API route passes only
persisted active leases and returns `authority_required` without one; direct
core/CLI test paths must inject the explicit provider execution lease before
exact approval is meaningful. This does not grant broad provider routing,
autonomous/background model calls, billing authority, provider SDK authority, or
payload persistence, and the default adapter remains disabled/no-execution.
The exact-approved provider credential validation lane follows the same
mode/domain foundation for a narrower non-invoking scope: it requires active
`provider_model_calls/execute` AuthorityLease scope before PolicyEngine,
LocalApprovalAuthority, adapter, transport, idempotency, and redacted receipt
gates are evaluated. Missing lease scope produces an authority-required blocked
decision that names Full machine access plus the provider_model_calls domain and
execute capability. The validation lease does not authorize chat/completions,
provider SDK authority, billing authority, fallback routing, provider payload
persistence, or background/autonomous provider use.
The Control Center Web Evidence product-slice route now requires active
`browser/read` AuthorityLease scope before WebAccessGateway HTTPS GET transport
opens. This converts the old Tier 1 web-evidence lane into the mode/domain
system without widening it: configured host allowlist, HTTPS GET only, bounded
redacted preview, safe refs, authority decision refs, audit records, receipt
refs, rollback/safe-disable posture, and kill-switch visibility remain
mandatory. Browser actions, auth/cookies, downloads/uploads, POST-style
mutation, unrestricted browsing, context injection, memory writes, connector
writes, provider/model calls, and production authority remain denied.
Provider/model transport outside named implemented adapter capabilities remains
blocked by authority policy unless a supported provider/model execution lease is
implemented and tested. Existing local loopback model requests may carry
`mission_ref` for policy evaluation, but that does not grant remote provider
SDK calls, web fetching, tools/functions, streaming, or provider payload
persistence.
Hermes interface-mode chat is now mapped into the same runtime authority model:
`POST /api/runtime/hermes/chat` may run the exact guarded Hermes CLI chat argv
only after active `workspace/execute` AuthorityLease scope is present. Missing
scope returns a blocked receipt with authority decision refs before Hermes CLI
discovery or subprocess execution. Disabled mode and pure external handoff
remain non-executing; yolo/oneshot, arbitrary args, toolset passthrough, raw
prompt/output persistence, direct memory writes, browser automation, connector
writes, and production authority remain denied.

## Core Problem

UAA's current authority posture is too conservative for the intended product.
It protects aggressively, but it also risks freezing the product into permanent
review-only behavior. The current pattern is:

```text
This one named capability is allowed; everything else is blocked.
```

That is useful for early safety hardening, but it is not the end-state for the
Ultimate AI Assistant. UAA is supposed to become governed autonomy: capable of
real action across the user's machine, browser, apps, accounts, smart home,
communications, and purchases when the operator explicitly grants that trust.

The target pattern is:

```text
The operator selected a trust mode and granted domains, constraints, budget,
duration, and hard limits for this session or mission. Actions inside that
authority envelope are allowed and receipted. Actions outside it ask, degrade
to draft, or deny.
```

## Product North Star

UAA should eventually support commands like:

```text
There is a sale happening on this ticket website for a show. Wait for it to go
live and buy a pair of tickets up to $1000 total including fees.
```

For that mission, UAA should be able to:

- control the browser;
- wait/refresh/queue as needed;
- use an already-authorized session when available;
- select acceptable seats;
- purchase within the budget;
- keep receipts and an audit trail;
- stop or ask when the action exceeds scope.

It should not:

- buy unrelated items;
- exceed the budget;
- change payment methods without permission;
- change account settings without permission;
- delete broad local data;
- damage Home Assistant profiles/configuration;
- mutate production/cloud systems without explicit authority;
- go on an unbounded shopping spree.

The product goal is high agency with explicit operator intent, not a UI that
blocks every meaningful action by default.

## Authority Model

Authority should be modeled as operator-selected modes plus domain grants plus
mission/session leases.

### Operator Modes

| Mode | Meaning |
|---|---|
| Read-only | Inspect, summarize, explain, and plan. No mutation. |
| Ask before changes | Prepare changes and proposals; ask before mutations. |
| Approved safe local work | Low-risk local work may proceed for the session with receipts. |
| Full local workspace access | Broad authority inside the current repo/workspace for the session. |
| Full machine access | Local files, apps, shell/processes, browser/app control, and system settings on this machine for the session, bounded by hard safety rails. |
| Delegated mission / autonomous window | UAA may act across explicitly granted domains for a specific goal, time window, budget, and constraint envelope. |

### Authority Domains

Modes are not enough. UAA needs explicit authority domains:

| Domain | Example Capabilities |
|---|---|
| workspace | repo files, project-local commands, tests, builds, commits when allowed |
| files | local file read/write/organize, protected against destructive broad deletes |
| shell | local command execution, process/service control, dependency install when allowed |
| apps | local app control through accessibility/app automation |
| browser | observe, click, form fill, upload/download, purchases when granted |
| system_settings | display, sound, focus, network, accessibility, app preferences |
| calendar | read metadata/content, create/update/cancel events |
| messages | read thread metadata/content, draft, send |
| email | read metadata/content, draft, send, archive, label, move |
| contacts | read, create, update, merge |
| home_assistant | devices, scenes, automations, climate, lights, locks, cameras |
| shopping_payments | purchase under explicit merchant/item/budget constraints |
| provider_model_calls | local/remote model calls with cost and output authority posture |
| memory | reviewed memory writes, correction, deletion/export where scoped |
| cloud_production | deploys, cloud account mutations, production services |

Each domain should expose capability levels such as:

```text
observe/read
draft/prepare
mutate/write
send/purchase/commit
admin/destructive
```

## Authority Lease

The core primitive should be an `AuthorityLease`. It is session-scoped or
mission-scoped and evaluated by policy before each action.

Conceptual shape:

```json
{
  "lease_ref": "authority-lease-ref:example",
  "mode": "delegated_mission",
  "mission_ref": "mission-ref:buy-show-tickets",
  "duration_minutes": 120,
  "domains": {
    "browser": ["observe", "click", "form_fill", "purchase"],
    "shopping_payments": ["purchase_under_budget"]
  },
  "constraints": {
    "merchant_refs": ["merchant-ref:ticket-site"],
    "event_ref": "event-ref:specific-show",
    "quantity": 2,
    "max_total_usd": 1000,
    "fees_included": true,
    "time_window_ref": "sale-window-ref"
  },
  "ask_if": [
    "price_over_budget",
    "wrong_event",
    "new_payment_method",
    "third_party_redirect",
    "ambiguous_target"
  ],
  "hard_deny": [
    "unrelated_purchase",
    "change_account_settings",
    "save_new_payment_method",
    "destructive_unrelated_data_change"
  ],
  "receipts_required": true,
  "audit_required": true,
  "redaction_required": true,
  "kill_switch_required": true
}
```

## Policy Decision Outcomes

Policy should return one of:

```text
allow
ask
deny
degrade_to_draft
```

The core rule:

```text
Unknown authority is denied. Known authority inside an active lease is allowed.
```

This replaces the current product habit of treating meaningful action as
blocked unless a one-off lane was separately promoted. Future work should
instead ask whether the action has a known domain/capability, an active lease,
policy allow/ask/degrade/deny behavior, receipts, audit records, rollback or
safe-disable posture, and tested adapter support.

## Safety Rails

Even in high-trust modes, some actions should ask or deny unless explicitly
covered by the lease:

- wipe disk or broad destructive delete;
- delete Home Assistant profiles/configuration;
- credential export;
- new payment method;
- purchases outside budget;
- production deploys;
- destructive cloud account changes;
- disabling security systems;
- sending messages outside mission scope;
- exfiltrating private data;
- irreversible account deletion.

The operator should be able to grant powerful authority, but that authority
must be visible, revocable, bounded, and receipted.

## Canon Changes Needed

The canon should change from "all broad authority blocked behind one-off lane
promotion" to "authority requires explicit mode/domain/lease and policy
evaluation."

Likely files to update:

| File | Needed Change |
|---|---|
| `AGENTS.md` | Replace blanket no-broad-authority posture with explicit mode/domain/lease requirements. |
| `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md` | Reframe the former one-off lane conveyor to trust-mode/domain/mission-lease maturity. |
| `docs/control_center/authority_candidate_scorecard.json` | Track authority domains and lease requirements, not only blocked candidates. |
| `docs/control_center/operational_maturity_manifest.json` | Track domain maturity and mode support. |
| `docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md` | Become the authority mode and mission lease implementation plan. |
| `docs/control_center/PRODUCT_LANGUAGE_RULES.md` | Permit product copy such as "requires Full Machine Access" or "requires Shopping domain grant." |
| `docs/control_center/OPERATOR_SHELL_GAP_MAP.md` | Describe app, browser, system, home, payment, and account domains as grantable under leases, not permanently out of scope. |
| `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md` | Align the product north star around delegated operator missions. |
| `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md` | Add AuthorityLease, MissionRunner, DomainAdapters, and Operator Cockpit concepts. |

## Core Code Direction

Add a dedicated authority package:

```text
src/ultimate_ai_agent/core/authority/
  modes.py
  domains.py
  leases.py
  evaluator.py
  receipts.py
  risk.py
  mission_constraints.py
```

Key objects:

```text
TrustMode
AuthorityDomain
CapabilityGrant
AuthorityLease
MissionLease
ActionRisk
PolicyDecision
AuthorityEvaluationContext
```

Adapt existing systems:

| Existing Area | Change |
|---|---|
| `PolicyEngine` | Evaluate concrete `AuthorityActionRequest` objects against active leases and domain grants; legacy review-only policy contracts may record AuthorityLease decisions without granting execution. |
| `LocalApprovalAuthority` | Track and evaluate session/mission leases alongside one-action approval refs; no approval ref grants authority unless the lease domain/capability decision also allows or asks. |
| `RuntimeGateway` | Execute when the action is inside the active lease. |
| `WebAccessGateway` | Support browser/web domain policies beyond permanent blocked posture. |
| Connector modules | Use domain grants for calendar, messages, email, contacts, Home Assistant, and shopping. |
| Action Inbox | Show whether an action is allowed, ask-required, denied, or draft-only because of the active lease. |
| Evidence/Audit | Record every lease decision and action receipt. |
| Control Center | Expose mode/domain selection, active leases, kill switch, receipts, and escalation reasons. |

## UX Requirements

The Control Center should become an authority cockpit.

It should show:

- active mode;
- enabled domains;
- mission scope;
- time/budget limits;
- what UAA can do without asking;
- what UAA will ask about;
- what is hard-denied;
- live receipts/audit timeline;
- pause/cancel/kill switch;
- safe-disable and rollback posture where available.

Copy should shift from:

```text
Blocked: no active browser authority.
```

To:

```text
Requires Full Machine Access with Browser and Shopping domains enabled.
```

or:

```text
Allowed by delegated ticket-purchase mission lease; budget limit $1000.
```

## Implementation Sequence

1. Canon update: modes, domains, leases, mission authority, safety rails.
2. Schema/model update: `AuthorityLease`, `AuthorityDomain`, `TrustMode`.
3. Policy evaluator update: return `allow`, `ask`, `deny`, or `degrade_to_draft`.
4. UI update: authority cockpit for selecting mode/domain and inspecting leases.
5. Convert existing lane records into AuthorityLease domain/capability mappings.
6. Add Full Local Workspace mode.
7. Add Full Machine Access mode with hard local safety rails.
8. Add Delegated Mission V1, starting with browser/app mission dry-run and receipts.
9. Add real browser/app control under lease.
10. Add account/app domains such as Calendar, Messages, Home Assistant, and shopping/payments one domain at a time.

## Important Product Principle

Tiny lanes can remain implementation details. They should not be the user-facing
authority model.

The user-facing model should be:

```text
I choose the trust mode, domains, mission, limits, and duration.
UAA acts inside that envelope.
UAA asks or blocks only when it would exceed that envelope.
Everything meaningful is visible in receipts and audit trails.
```
