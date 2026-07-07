# Delegated Life OS North Star

Status: planning-only product north star
Baseline: v0.104.0 / 0.104.0
Related gates:
`docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`,
`docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md`,
`docs/canonical/40_credentials_secret_broker_and_provider_registry.md`,
`docs/canonical/42_autonomy_levels_and_standing_approvals.md`

This document preserves the long-term product ambition for UAA: a governed,
local-first delegated operator that can eventually handle ordinary life and
business work, including purchases, bookings, subscriptions, account tasks,
messages, calendar actions, and follow-up, after exact AuthorityLease
domain/capability support is implemented, tested, and granted.

This file grants no runtime authority. It adds no backend route, frontend
control, connector runtime, credential handling, payment method, purchase
authority, web/browser execution, provider/model call, shell/subprocess
execution, background worker, public beta, public release, public distribution,
or production authority.

## Product Thesis

UAA should eventually feel less like "answer this prompt" and more like "own
this delegated job until it is done." The target user experience is a single
trusted command center with memory, plans, action envelopes, approvals,
receipts, evidence, revocation, and calm interruption rules.

The long-term promise is not broad autonomy. The long-term promise is delegated
authority: UAA can do anything the user has explicitly delegated, inside clear
policy, with evidence, spend/risk limits, rollback or compensating-action
posture, and revocation.

## Current Boundary

Today, this is only product direction. UAA currently must not claim or imply:

- ordering goods or services
- using stored credentials for purchases or account actions
- holding raw passwords, raw payment data, or raw credential material
- sending email or messages
- modifying calendar events
- writing to CRM or external accounts
- authenticated browsing, cookies, form filling, downloads, uploads, or clicks
- background autonomy or recurring execution
- broad connector, browser, provider, shell, plugin, or model authority

Every future promotion must pass the Authority Graduation Program and the
operational maturity gates before it becomes product behavior.

## Delegation Model

Credential availability is not consent. A future stored credential, passkey,
OAuth token, payment method, virtual card, session grant, account connection, or
merchant token can only be used when a separate policy and approval check says
that exact use is allowed.

The safe shape is:

```text
user intent
-> reviewed memory and preferences
-> allowed source context
-> scoped action envelope
-> risk, spend, account, merchant, and destination checks
-> exact approval or bounded standing approval
-> credential/payment handle use through a broker
-> receipt, evidence, audit, and revocation visibility
```

Raw secrets should never enter chat, prompts, memory, docs, durable evidence,
logs, screenshots, model context, or user-visible receipts. The agent should
receive opaque refs and use brokered handles through approved adapters only.

## Everyday Authority Ladder

Future life-OS behavior should graduate by consequence, not by UI enthusiasm:

| Stage | Product behavior | Boundary |
|---|---|---|
| Observe | Read safe refs, source readiness, and metadata. | No account fetch or raw private content unless separately scoped. |
| Draft | Produce editable drafts, plans, carts, booking holds, or response proposals. | No send, write, purchase, booking, cancel, or account mutation. |
| Prepare | Build a complete action envelope for review. | Includes merchant/account refs, items, destination, spend, time, risk, and expiry. |
| Approve once | Execute one exact reviewed action. | Requires LocalApprovalAuthority validation, idempotency, receipt, audit, and safe-disable/rollback posture. |
| Bounded rule | Repeat a low-risk class within strict limits. | Requires revocation, budget/rate/time limits, queue visibility, and kill switch posture. |
| Review | Show what happened and what should be remembered. | Memory remains recall, not truth or authority. |

## Pizza Example

"Order my usual pizza" is a useful end-state test case because it combines
memory, local preferences, web or connector context, stored payment, delivery
address, merchant account, budget, and interruption judgment.

A future compliant flow would look like this:

1. Recall reviewed preferences, dietary constraints, usual merchant, address,
   tip preference, and budget as safe refs.
2. Inspect only allowed merchant/source context through approved adapters.
3. Draft a cart with item refs, substitutions, total, taxes, fees, tip, payment
   handle ref, delivery address ref, and ETA.
4. Present an approval envelope: merchant, items, total, max spend, address,
   credential/payment handle ref, cancellation posture, risk class, expiry, and
   evidence refs.
5. Execute only after exact approval or a separately approved bounded rule.
6. Record receipt, audit, evidence, actual charged amount, and delivery status
   refs.
7. Propose memory updates such as changed preference or merchant issue; do not
   silently write memory.

This same pattern should govern bookings, subscriptions, renewals, refunds,
calendar changes, message sends, CRM updates, and account administration.

## Interruption Rules

The trusted assistant should avoid interrupting for low-risk draft and preview
work, but must interrupt at consequence boundaries:

- external sends or account writes
- purchases, subscriptions, refunds, renewals, cancellations, or payments
- credential enrollment, credential use outside an approved scope, or account
  permission changes
- irreversible or hard-to-undo work
- high or unknown cost
- ambiguous intent, conflicting memory, stale source context, or missing
  evidence
- policy, redaction, idempotency, or rollback/safe-disable gaps

The anti-goal is a rubber-stamp approval wall. The product should batch,
summarize, and ask at the right consequence point instead of training the user
to approve everything.

## Memory Role

Memory should make delegation feel personal without becoming authority. UAA may
eventually remember preferences, vendors, addresses, budgets, trusted contacts,
recurring chores, subscription policies, travel habits, communication style,
and prior outcomes, but every authority-bearing use must cite reviewed recall
refs and evidence refs.

Memory can suggest. It cannot authorize.

## Future Milestone Seeds

These are future-scoped seeds only; they are not selected implementation lanes:

- `FCC-DELEGATION-001`: shared delegated-action envelope vocabulary for
  purchases, bookings, sends, account changes, and subscriptions.
- `FCC-CREDENTIALS-001`: credential/payment handle UX over Secret Broker refs,
  with no raw secret display and no invocation authority from vault presence.
- `FCC-PURCHASE-001`: purchase authority boundary with max spend, merchant
  scope, payment handle refs, receipt refs, cancellation posture, and Cost
  Governor checks.
- `FCC-BOOKING-001`: booking/hold proposal envelope with date/time, location,
  cancellation policy, identity/payment posture, and exact approval.
- `FCC-SUBSCRIPTIONS-001`: subscription inventory, renewal risk, cancel/change
  proposal envelopes, and explicit external account mutation gates.
- `FCC-STANDING-RULES-001`: bounded standing approval rules with expiry,
  revocation, queue visibility, spend/rate limits, audit, and kill switch
  posture.

The near-term Founder Command Center lane remains Today, Action Inbox, Plans,
Memory, Evidence, Settings, source readiness, and approval-envelope
readability. This north star exists so later authority work has a product spine
to graduate toward without pretending the authority exists today.
