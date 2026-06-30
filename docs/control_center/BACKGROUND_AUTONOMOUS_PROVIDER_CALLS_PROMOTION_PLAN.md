# Background and Autonomous Provider Calls Promotion Plan

Status: planning-only promotion requirements; background and autonomous
provider calls remain blocked.

This plan defines the requirements before UAA can consider any background or
autonomous provider-call lane. It does not implement background execution,
scheduler runtime, autonomous model calls, provider calls, runtime activation,
billing authority, broad provider routing, broad fallback, memory writes,
context injection, connector writes, a new API runtime route, public beta,
public release, or production authority.

Python Agent Core remains the authority boundary. Control Center and CLI may
inspect posture, queues, receipts, approvals, and blockers, but they do not
grant authority. The current exact-approved provider invocation lane remains
disabled by default, exact-approval-bound, CostGovernor-gated, receipt-backed,
and non-autonomous. The exact-approved fallback lane remains limited to two
named single-provider adapter scopes with per-attempt approval, cost, receipt,
and safe-disable refs. Provider Router Dry-Run remains proposal-only.

## Current Baseline

The current baseline allows only these provider-related postures:

- Provider Catalog and Provider Credential Readiness metadata.
- Credential Vault metadata and local safe-ref ledger posture.
- Exact-approved credential validation, not invocation authority.
- Tiny exact-approved provider invocation contracts and disabled-default route
  posture.
- Core/CLI exact-approved two-provider fallback, with each attempt carrying
  its own exact provider, model, credential, approval, cost, idempotency,
  receipt, and safe-disable refs.
- Provider Router Dry-Run proposals only, without invocation or fallback
  execution authority.

No existing provider posture grants background execution, autonomous calls,
standing spend authority, hidden queues, scheduler authority, broad provider
router authority, provider output authority, raw payload persistence, or
production authority.

## Promotion Gates

All gates below are required before any later PR may implement background or
autonomous provider calls.

| Gate | Required before promotion |
|---|---|
| Scoped autonomy window | A window ref exact-bound to actor, purpose, allowed task refs, allowed provider refs, allowed model refs, allowed credential refs, max attempts, start time, expiry time, renewal rule, revocation ref, kill-switch ref, audit ref, replay ref, and explicit human approval boundaries. |
| Exact provider/model refs | Each queued request and each fallback attempt must name exact allowed provider/model refs. Broad provider routing, wildcard providers, and model-family expansion are blocked. |
| Exact credential refs | Each queued request and each fallback attempt must name exact allowed credential refs. Credential presence, vault posture, and validation receipts are identifiers and blockers, not invocation authority. |
| Max spend per window | The autonomy window must carry a hard max spend per window with a safe max-spend ref. Missing, unknown, or stale spend scope blocks enqueue and dispatch. |
| Per-request and per-session budgets | Every queue item must carry per-request and per-session cost estimate refs, budget decision refs, max-approved USD refs, token ceilings, attempt ceilings, and retry ceilings. |
| CostGovernor hard block | CostGovernor must run before enqueue, before dispatch, and before every fallback attempt. Denied, unknown paid cost, stale estimate, missing max-approved USD, or incomplete actual paid cost blocks the request and the window. |
| Queue inspection | A backend-owned queue read model and CLI inspection path must show queued, paused, running, blocked, cost-blocked, approval-required, revoked, expired, receipt-recorded, and incomplete-cost states before any dispatch. There must be no hidden queue. |
| Kill switch | A kill switch must stop new enqueue, pause dispatch, prevent retries, and block fallback attempts for the affected window/provider/credential scope. It must record a redacted receipt and be inspectable through UI and CLI parity. |
| Revocation | Revocation must invalidate the window, credential scope, provider scope, model scope, queue item, and approval scope before any later dispatch. Revoked refs must fail closed at evaluator boundaries. |
| Replay and audit | Enqueue, approval, dispatch, provider attempt, fallback attempt, response summary, cost, kill-switch, revocation, retry, and stop events must produce UAA-owned audit and replay refs. Replay is inspection-only, not re-execution. |
| Red-team checks | Promotion requires adversarial checks for prompt injection, hidden-context injection, budget drain, retry loops, fallback loops, stale approval reuse, credential exfiltration, raw payload leakage, queue hiding, kill-switch race, revocation race, receipt tampering, incomplete-cost bypass, UI/CLI drift, and model-output authority drift. |
| UI/CLI parity | Any Control Center visibility must map to the same Python core/API contract and repo-local CLI inspection path. UI must show blocked and partial states before raw developer payloads. |
| No hidden prompt injection | Provider output, memory recall, router proposal output, or prior queue state must not inject hidden context or instructions into later provider calls. Any context candidate must stay explicit, safe-ref-only, reviewed, and approval-bound. |
| No raw payload persistence | Durable docs, receipts, fixtures, tests, logs, audit, replay, UI, and CLI output must not persist raw prompt content, raw response content, raw provider payloads, raw provider exchanges, credentials, local paths, usernames, hostnames, env dumps, or raw logs. |
| Incomplete-cost receipt blocking | Any missing actual usage or actual paid-cost receipt marks the item and window review-required, blocks further provider use, and requires explicit human review before any later provider work can proceed. |
| Explicit human approval boundaries | Human approval must name the autonomy window, queue item, provider/model refs, credential refs, spend refs, attempt ceiling, expiry, revocation, kill switch, expected receipt refs, and blocked follow-on authorities. Approval refs remain identifiers only. |
| Safe-disable and rollback posture | The lane must define safe-disable behavior, rollback or no-rollback rationale, receipt replay, queue drain, credential-scope disable, provider-scope disable, and evidence cleanup without deleting audit history. |

## Required Queue Contract

The future queue must be backend-owned and inspectable before it can dispatch.
At minimum it must expose:

- queue item ref
- autonomy window ref
- actor ref
- purpose ref
- provider ref
- model ref
- credential ref
- approval scope ref
- cost estimate ref
- budget decision ref
- max-approved USD ref
- expected request receipt ref
- expected response receipt ref
- expected usage receipt ref
- expected cost receipt ref
- idempotency ref
- status
- created time
- expiry time
- attempt count
- max attempts
- retry policy ref
- fallback policy ref
- kill-switch ref
- revocation ref
- safe-disable ref
- audit ref
- replay ref
- blocked reason refs

Queue item status must include blocked states before dispatch:

- `queued_no_authority`
- `approval_required`
- `approval_invalid`
- `cost_blocked`
- `unknown_paid_cost_blocked`
- `paused_by_kill_switch`
- `revoked`
- `expired`
- `dispatch_blocked`
- `fallback_blocked`
- `incomplete_cost_requires_review`
- `receipt_recorded`

## Human Approval Boundary

Background or autonomous provider calls require explicit human approval for the
exact autonomy window and exact queue item. A later promotion must prove that
approval cannot be reused across providers, models, credentials, windows,
queues, fallback attempts, or spend scopes.

Approval must not authorize:

- broad provider routing
- unbounded fallback
- scheduler authority outside the approved window
- hidden retries
- raw prompt or provider payload persistence
- memory writes
- context injection
- connector writes
- browser automation
- shell/subprocess execution
- provider spend or use outside the exact max-approved USD scope
- provider output authority
- production authority

## Cost And Receipt Rules

CostGovernor must hard-block before any background or autonomous dispatch when:

- provider ref is missing
- model ref is missing
- credential ref is missing
- cost estimate ref is missing
- budget decision ref is missing
- max-approved USD ref is missing
- estimated spend exceeds the per-request budget
- estimated spend exceeds the per-session budget
- estimated spend exceeds the window budget
- unknown paid cost is present without exact approval
- actual usage receipt is incomplete
- actual paid-cost receipt is incomplete
- a prior item in the same window has incomplete cost requiring review
- the queue item, window, provider, model, or credential scope is revoked
- a kill switch is active

Incomplete cost is a stop condition. It is not a warning, not billing
authority, and not a recoverable background retry state.

## Red-Team Requirements

A later promotion must include red-team scenarios and regression checks for:

- prompt injection attempting to widen provider/model scope
- hidden prompt injection through memory, provider output, router proposals, or
  queued state
- cost drain through retries, loops, long output, or fallback
- stale approval replay
- stale credential ref replay
- revoked credential/provider/model/window reuse
- queue item mutation after approval
- queue invisibility in UI or CLI
- kill-switch race between dispatch and retry
- revocation race between fallback attempts
- incomplete actual-cost bypass
- raw prompt, raw response, or raw provider payload persistence
- provider output treated as approval, truth, or execution authority
- Control Center and CLI language drift

## UI And CLI Requirements

Control Center must show human-readable status before any developer payload.
The CLI must inspect the same backend-owned queue, window, approval, budget,
receipt, kill-switch, revocation, and replay refs. Both surfaces must
distinguish planned, blocked, paused, queued-no-authority, approved-no-dispatch,
cost-blocked, incomplete-cost-review, revoked, expired, safe-disabled,
receipt-recorded, and not-scoped states.

No UI control may be described as enabling background or autonomous provider
calls until the exact backend route, OpenAPI operation, side-effect class,
approval boundary, queue contract, CostGovernor hard block, receipt storage,
kill switch, revocation path, replay posture, CLI parity, verifier, and
red-team checks are accepted.

## Promotion Sequence

Later work must proceed in this order:

1. Contract-only queue/window schema and verifier, still no dispatch.
2. Read-only queue inspection UI and CLI, still no dispatch.
3. Kill-switch and revocation contract/read-model proof, still no dispatch.
4. CostGovernor window and per-item budget contract proof, still no dispatch.
5. Red-team harness and product-language verifier updates, still no dispatch.
6. Exact single-window, single-item disabled adapter proof, still no background
   dispatch by default.
7. Separate exact promotion for any background dispatch, with a new API route
   only if OpenAPI, route side-effect metadata, approval scope, receipt storage,
   replay, rollback/safe-disable, UI, CLI, and tests are accepted.

## Non-Goals

- No background execution.
- No scheduler.
- No autonomous model calls.
- No provider calls.
- No runtime activation.
- No billing authority.
- No broad provider router.
- No broad fallback.
- No new API runtime route.
- No queue dispatch.
- No hidden retries.
- No credential enrollment.
- No secret resolution API.
- No raw prompt persistence.
- No raw response persistence.
- No raw provider payload persistence.
- No memory writes.
- No context injection.
- No connector writes.
- No browser automation.
- No shell/subprocess execution.
- No provider output authority.
- No public beta.
- No public release.
- No production authority.

## Verification

This planning lane is guarded by:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_background_autonomous_provider_plan.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_background_autonomous_provider_plan.py
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make verify
```

Any later runtime promotion must add focused tests for queue inspection,
approval binding, CostGovernor hard blocks, incomplete-cost blocking,
kill-switch and revocation boundaries, replay/audit refs, UI/CLI parity,
product-language drift, redaction, and exact OpenAPI route truth.
