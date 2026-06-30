# Provider Billing Authority Boundary

Status: planning-only provider billing authority boundary; provider billing
authority remains blocked.

This boundary defines the requirements before any future provider billing
authority can exist. It prefers exact per-request and per-session max USD
approvals over broad billing authority. It does not implement billing
integration, payment methods, subscription management, provider calls,
autonomous/background calls, runtime activation, a broad spend toggle, or
production authority.

Python Agent Core remains the authority boundary. Control Center and CLI may
inspect billing posture, CostGovernor decisions, approval refs, receipt refs,
revocation refs, audit refs, and blockers, but they do not grant spend or
billing authority. Approval refs remain identifiers until the exact scope is
validated by Python Agent Core and the required receipts exist.

## Current Baseline

The current provider lanes already require exact provider/model refs, exact
credential refs, CostGovernor decisions, max-approved USD refs, usage/cost
receipt refs, idempotency, safe-disable posture, and redacted receipts before
any provider-use claim can be considered. Exact-approved fallback requires each
attempt to carry separate approval, cost, receipt, and safe-disable refs.

The M146 Billing/Plan Boundary remains productization policy only. It records
review-only billing and plan refs, not provider spend authority. This provider
billing boundary does not change M146, does not add billing runtime, and does
not add plan enforcement.

## Billing Authority States

Any future provider-cost approval surface must use these explicit states before
it can be promoted:

| State | Required meaning |
|---|---|
| `no_billing_authority` | Default state. No provider spend, billing integration, payment method, subscription management, or billing runtime is authorized. |
| `per_request_max_usd` | A human-approved max USD amount for one exact request, provider ref, model ref, credential ref, approval scope, idempotency ref, and expected receipt set. It is not reusable. |
| `per_session_max_usd` | A human-approved max USD amount for one exact session/window with exact provider/model/credential refs, request ceilings, attempt ceilings, expiry, revocation, kill-switch refs, and expected receipt refs. |
| `spend_window_exhausted` | The approved request/session/window spend is exhausted. New enqueue, dispatch, fallback attempts, and retries are blocked until a new exact approval is granted. |
| `unknown_cost_blocked` | Cost is missing, unknown, stale, or not provider-actual where required. The request/session/window blocks before provider use. |
| `incomplete_cost_blocked` | Actual usage or actual paid-cost receipt is incomplete. Further provider use in the same receipt store/window blocks until human review resolves the receipt posture. |
| `billing_review_required` | A human must review cost, receipt completeness, budget exhaustion, revocation, kill-switch, or disputed usage/cost posture before any later provider work. |

No state may be implemented as a broad spend toggle. No state may authorize a
provider router, background queue, autonomous call, fallback attempt, or billing
integration outside its exact approved refs.

## Required Gates

All gates below are required before any later PR may implement provider billing
authority:

| Gate | Required before promotion |
|---|---|
| Exact approval | The approval must name the provider ref, model ref, credential ref, request or session ref, CostGovernor decision ref, max-approved USD value/ref, expiry, revocation ref, kill-switch ref, idempotency ref, expected usage/cost receipt refs, and blocked follow-on authorities. |
| CostGovernor hard limits | CostGovernor must hard-block when estimated spend exceeds per-request, per-session, or window limits; when cost is unknown; when max-approved USD is missing; when actual cost is incomplete; or when revocation/kill-switch posture is active. |
| Actual usage/cost receipts | Provider use cannot be treated as complete without actual usage refs, actual cost refs, receipt-completeness status, redacted request/response receipt refs, and further-use-blocked posture when cost is incomplete. |
| Incomplete-cost blocking | Missing actual usage or paid-cost data produces `incomplete_cost_blocked`, marks the scope review-required, and blocks retries, fallback attempts, background dispatch, and later provider use until reviewed. |
| Revocation | Revocation must invalidate request, session/window, provider, model, credential, budget, max-approved USD, and approval refs before any later provider work. |
| UI/CLI inspection | Control Center and CLI must show `no_billing_authority`, approved max USD scopes, exhausted windows, unknown-cost blocks, incomplete-cost blocks, review-required posture, revocation, kill-switch, and receipt refs from the same backend-owned contract. |
| Audit/replay posture | Approval, budget evaluation, enqueue/block, provider attempt, fallback attempt, actual usage, actual cost, review, revocation, kill-switch, and safe-disable events must produce UAA-owned audit and replay refs. Replay remains inspection-only, not re-execution. |
| Safe-disable/rollback posture | The lane must define safe-disable behavior, rollback or no-rollback rationale, queue drain, provider-scope disable, credential-scope disable, and evidence cleanup without deleting audit history. |
| No hidden prompt injection | Cost, billing, receipt, or provider-output content must not inject hidden context or instructions into later provider calls. |
| No raw payload persistence | Durable docs, receipts, tests, fixtures, logs, audit, replay, UI, and CLI output must not persist raw prompt content, raw response content, raw provider payloads, raw provider exchanges, credentials, local paths, usernames, hostnames, env dumps, or raw logs. |
| Red-team checks | Promotion requires adversarial tests for budget drain, stale approval reuse, broad-spend toggle drift, receipt tampering, unknown-cost bypass, incomplete-cost bypass, fallback-loop spend drain, revocation race, kill-switch race, and UI/CLI language drift. |

## Approval Rules

Provider billing approval must be exact-scoped:

- prefer `per_request_max_usd` for one request when the work is narrow
- prefer `per_session_max_usd` only for a bounded session/window with expiry,
  request ceilings, attempt ceilings, and revocation
- require exact provider, model, credential, CostGovernor, budget, receipt,
  approval, idempotency, revocation, and kill-switch refs
- block wildcard providers, wildcard models, family-level model expansion,
  provider-router spend delegation, and hidden retries
- block reuse of an approval across requests, sessions, fallback attempts,
  providers, models, credentials, spend windows, or budget scopes

Approval must not authorize:

- billing integration
- payment methods
- subscription management
- broad spend toggle
- provider calls outside exact refs
- autonomous/background calls
- scheduler runtime
- broad provider router
- unbounded fallback
- raw prompt, response, or provider payload persistence
- connector writes
- memory writes
- context injection
- provider output authority
- production authority

## Cost And Receipt Rules

CostGovernor must hard-block before provider use when:

- provider ref is missing
- model ref is missing
- credential ref is missing
- approval scope ref is missing
- cost estimate ref is missing
- budget decision ref is missing
- max-approved USD ref or value is missing
- estimated spend exceeds the per-request max USD
- estimated spend exceeds the per-session max USD
- spend window is exhausted
- unknown paid cost is present
- actual usage receipt is incomplete
- actual paid-cost receipt is incomplete
- prior incomplete cost in the same scope is unresolved
- revocation is active
- kill switch is active

Actual usage and actual paid-cost receipts are required evidence, not billing
authority. Unknown cost and incomplete cost are stop conditions, not warnings.

## UI And CLI Requirements

Any UI/CLI surface must distinguish:

- `no_billing_authority`
- `per_request_max_usd`
- `per_session_max_usd`
- `spend_window_exhausted`
- `unknown_cost_blocked`
- `incomplete_cost_blocked`
- `billing_review_required`
- approved-no-provider-use
- revoked
- safe-disabled
- receipt-recorded
- not-scoped

UI copy must not describe any control as enabling provider spend, background
provider calls, autonomous provider calls, billing, or a broad spend toggle
until the exact Python Agent Core contract, OpenAPI route, side-effect class,
approval boundary, CostGovernor hard blocks, actual usage/cost receipts,
revocation, kill switch, safe-disable/rollback posture, CLI parity, verifier,
and red-team checks are accepted.

## Promotion Sequence

Later work must proceed in this order:

1. Contract-only state schema and verifier, still no provider use.
2. Read-only UI/CLI inspection for billing authority states, still no provider
   use.
3. CostGovernor per-request/per-session hard-limit contract proof, still no
   provider use.
4. Actual usage/cost receipt completeness proof, still no billing integration.
5. Revocation, kill-switch, audit/replay, safe-disable, and red-team proof,
   still no billing integration.
6. Separate exact promotion for any provider billing authority route, with no
   background/autonomous execution unless separately scoped.

## Non-Goals

- No billing integration.
- No payment methods.
- No subscription management.
- No broad spend toggle.
- No production billing claims.
- No provider calls.
- No autonomous/background calls.
- No runtime activation.
- No payment provider runtime.
- No plan enforcement.
- No account runtime.
- No entitlement runtime.
- No pricing runtime fetch.
- No scheduler.
- No background execution.
- No broad provider router.
- No fallback execution from billing posture.
- No provider SDK calls.
- No new API runtime route.
- No raw prompt persistence.
- No raw response persistence.
- No raw provider payload persistence.
- No public beta.
- No public release.
- No production authority.

## Verification

This boundary is enforced by
`scripts/verify_provider_billing_authority_boundary.py` and
`tests/test_provider_billing_authority_boundary.py`. Product-language drift is
blocked by `docs/control_center/PRODUCT_LANGUAGE_RULES.md`.
