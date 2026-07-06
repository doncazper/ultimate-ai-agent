# UAA Authority Modes And Mission Leases

Status: active authority foundation canon for AuthorityLease V1
Date: 2026-07-06
Purpose: preserve the product/architecture direction for moving UAA from
permanent blocked-lane posture to governed, operator-selected autonomy.

This document records the active strategic correction from tiny-lane-first
graduation toward mode/domain/lease authority. It is not itself runtime
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
- `scripts/dev/uaa_runtime.py preview-authority-decision --json`
- `scripts/dev/uaa_runtime.py plan-authority-mission --json`
- `POST /api/runtime/authority-leases`
- `POST /api/runtime/authority-leases/revoke`
- `scripts/dev/uaa_runtime.py select-authority-mode`
- `scripts/dev/uaa_runtime.py revoke-authority-lease`
- Control Center `/settings` authority mode controls for implemented local
  domain subsets, revoke receipts, decision previews for concrete
  mode/domain/capability requests, and mission-plan previews for delegated
  AuthorityLease issue requirements. Issue-ready mission plans may be issued
  through the same `POST /api/runtime/authority-leases` receipt path when the
  backend-generated lease request has no denied domains or unsupported adapters.

The first implementation is deliberately conservative: the default active
lease is read-only; operator-selected session leases persist safe receipts for
implemented local domain/capability subsets; existing exact lanes are mapped
into domains and required trust modes; RuntimeGateway API/CLI decisions consume
the active lease store for command invocation, approval, and execution policy;
mission-scoped leases grant only actions carrying the matching mission ref in
safe action refs or constraints, so a delegated mission cannot become a broad
standing grant;
Control Center `/settings` can preview workspace command, file proposal,
browser-click, and budgeted-purchase decisions against the active lease, and can
plan a delegated mission lease envelope without issuing a lease, executing work,
or mutating anything; issue-ready implemented local mission plans can then issue
the exact backend-generated mission-scoped lease request through the existing
lease receipt route; preview results show required modes, domain and capability
refs, receipt/audit refs, and unsupported-adapter reasons;
unsupported browser/app/payment/calendar/messages/Home Assistant adapters remain
denied or draft-degraded instead of being presented as live execution. Read-only
command status may run under `workspace/read`; execution-capable command lanes
require an active `workspace/execute` lease. Work Board persisted reorder and
local-card-create lanes now require both exact approval and an active
`workspace/write` lease, returning readable authority-denied refs when the
operator remains in read-only mode. Action Inbox local-task commit likewise
requires exact approval plus active `workspace/write` authority before local
Founder Loop task state is written. Memory Review accept/correct reviewed
recall writes require exact approval plus active `memory/write` authority before
the recall-only `LocalMemoryStore` record is written; reject, defer, merge,
supersede, and forget-request remain receipt/posture decisions without memory
write authority. CRM local mutations require exact approval plus active
`contacts/write` authority before local CRM state is changed; connector reads,
connector writes, sends, calendar writes, account sync, and external CRM writes
remain unsupported unless later adapters are implemented and tested.
File preview and tree preview require active `files/read` authority before
safe-root metadata is inspected. File write proposal and diff preview require
active `files/prepare` authority before proposal refs are reviewed. File Review
approval capture requires active `files/write` authority before the review-only
safe-ref record is persisted. Raw file access, context injection, memory
writes, export, execution, patch apply, and rollback execution remain
unsupported until separately implemented and tested.
Task Decomposition local plan execution now requires an active
`workspace/execute` AuthorityLease before registered local handlers run. Exact
LocalApprovalAuthority grants remain a separate second gate for approval-bound
or high-risk capabilities inside a plan. In read-only mode, `/task-decomposition/run`
and `/task-decomposition/plans/execute` return a durable, redacted blocked/draft
decision with authority decision refs, required domain/capability refs, audit
refs, receipt posture, and rollback/safe-disable refs instead of silently
executing or claiming broad shell/tool authority.
Provider/model transport remains blocked by authority policy unless a later
supported provider/model execution lease is implemented and tested.

## Core Problem

UAA's current authority posture is too conservative for the intended product.
It protects aggressively, but it also risks freezing the product into permanent
review-only behavior. The current pattern is:

```text
This exact tiny lane is allowed; everything else is blocked.
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
blocked unless a microscopic lane was separately promoted.

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

The canon should change from "all broad authority blocked until tiny lane
graduation" to "authority requires explicit mode/domain/lease and policy
evaluation."

Likely files to update:

| File | Needed Change |
|---|---|
| `AGENTS.md` | Replace blanket no-broad-authority posture with explicit mode/domain/lease requirements. |
| `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md` | Reframe from tiny-lane conveyor to trust-mode/domain/mission-lease maturity. |
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
| `PolicyEngine` | Evaluate actions against active leases and domain grants. |
| `LocalApprovalAuthority` | Issue session/mission leases, not only one-action approval refs. |
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
Blocked until exact lane graduates.
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
5. Convert existing tiny lanes into capability-pack members.
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
