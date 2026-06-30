# Exact-Approved Provider Invocation Promotion Plan

Status: disabled-default live adapter lane implemented with usage/cost receipt
hardening; broad callable provider runtime remains future gated.

This plan defines the minimum promotion checklist for one tiny exact-approved
provider/model lane. The current implementation adds typed contracts, a
disabled-default Control Center route, CostGovernor blocking, redacted receipt
storage, actual usage/cost receipt completeness checks, CLI inspection, UI
posture labels, and two core-only single-provider adapter scopes:
OpenAI-compatible and Anthropic-compatible. Each adapter scope remains
disabled-by-default and blocked unless explicitly constructed with exact scoped
approval, known cost posture, injected transient credential resolution, durable
receipt replay storage, and its matching scoped transport. The second adapter
is prerequisite evidence for future fallback work; it does not itself enable
fallback execution.
It does not add provider
credential validation authority through the invocation lane, provider SDK
calls, broad callable provider routing, fallback execution, autonomous model
calls, background execution, or billing authority; provider credential
validation is handled by the separate exact-approved validation lane and still
does not authorize invocation. Provider Router Dry-Run is a later
proposal-only lane that can explain exact-approval candidate, blocked,
degraded, and cost-risky provider refs from local posture, but it cannot
execute providers or fallback.

The default API route still uses the disabled adapter and does not become
callable from metadata visibility. Any future product surface that enables the
scoped adapter must keep Provider Credential Readiness, CostGovernor Binding,
Credential Vault posture, exact approval, redacted receipts, CLI inspection
parity, and UI blocked-state parity green.

## Promotion Checklist

The tiny lane requires all of the following before adapter execution can occur:

- `credential_ref`
- `provider_ref`
- `model_ref`
- policy ref carried as part of the exact approval scope
- `PolicyEngine` policy validation before any scoped adapter call
- exact approval scope validated by `LocalApprovalAuthority`
- `CostGovernor` decision
- unknown paid cost blocked by default
- max approved USD
- idempotency ref
- redacted request receipt ref
- redacted response receipt ref
- actual usage ref
- actual cost ref
- receipt completeness status
- incomplete actual paid cost review posture
- `PolicyEngine` policy decision ref before any future enabled adapter can
  claim callable authority
- no raw prompt, response, or provider payload persistence
- rollback or safe-disable posture
- durable receipt replay guard before any scoped network call
- CLI inspection parity
- UI blocked, approved, and cost-blocked states
- live adapter blocked state when scoped adapter configuration is missing or
  denied
- provider router dry-run remains proposal-only and recommends exact approval
  scope refs without fallback execution

Every lane attempt must fail closed when any required ref, policy validation,
approval scope, budget decision, receipt ref, or safe-disable posture is
missing. The default API route uses a disabled adapter and does not load
approval grants, so it can only return blocked, cost-blocked, approval-required,
or approval-invalid posture. The Python core evaluator can reach
`approved_no_execution` only when an exact approval authority is injected and
cost/policy gates pass while the adapter remains disabled.

If a scoped network attempt occurs and actual paid-cost metadata is unavailable,
the receipt is marked `incomplete_cost_requires_review`; the lane blocks further
provider use through the same receipt store until that receipt is reviewed by a
later scoped process. In short, incomplete actual paid cost blocks further provider use.
A successful transport that cannot provide actual paid cost also
fails closed into this review-required receipt posture.

## Minimum Contract Shape

The contract distinguishes these states before broad callable provider runtime exists:

- `blocked_missing_credential_ref`
- `blocked_missing_provider_ref`
- `blocked_missing_model_ref`
- `blocked_missing_policy_validation`
- `blocked_missing_cost_estimate_ref`
- `blocked_missing_budget_decision_ref`
- `blocked_missing_max_approved_usd`
- `blocked_missing_expected_receipt_ref`
- `blocked_provider_not_allowed`
- `blocked_model_not_allowed`
- `approval_required`
- `approval_invalid`
- `cost_blocked`
- `unknown_paid_cost_blocked`
- `approved_no_execution`
- `live_adapter_blocked`
- `receipt_recorded`

Approval refs, credential refs, provider refs, model refs, and max-approved USD
refs remain identifiers. They do not authorize provider calls unless the exact
lane contract validates the complete scope, passes CostGovernor checks, runs
through the one scoped adapter, and records redacted receipts.

## Receipt And Evidence Rules

Receipts must store safe refs and redacted summaries only:

- request receipt ref
- response receipt ref
- policy ref, with `PolicyEngine` policy decision ref added before any future
  enabled adapter
- cost estimate ref
- explicit estimated cost ref
- actual usage ref
- actual cost ref
- receipt completeness status
- incomplete cost review and further-use-blocked flags when actual paid cost is
  unavailable
- CostGovernor decision ref
- budget decision ref
- max approved USD ref
- credential ref
- provider ref
- model ref
- approval scope ref
- idempotency ref
- rollback or safe-disable ref

Successful live adapter calls and provider-network-attempt failures both remain
receipt-backed. A repeated idempotency ref must return the existing redacted
receipt or fail closed on scope conflict before a second network call can occur.
Blocked-attempt receipts may record safe adapter refs and network posture, but
never raw prompt, response, credential, or provider payload content.
Incomplete actual paid-cost receipts are redacted receipts, not billing
authority; they require review and block follow-up provider use.

Receipts, evidence, logs, tests, and UI fixtures must not store raw prompt
content, raw response content, raw provider exchange content, raw provider
payloads, credentials, secrets, usernames, hostnames, local paths, env dumps, or
raw logs.

## UI And CLI Requirements

Control Center must show provider lane posture as one of these states from
backend-owned data:

- blocked
- approved no execution
- cost blocked
- unknown paid cost
- no provider authority
- live adapter blocked
- receipt recorded
- usage captured
- cost captured
- cost incomplete
- review required
- further use blocked
- disabled no execution

The same posture is inspectable through
`scripts/inspect_tiny_provider_invocation_lane.py`. UI labels must never imply
provider connection, provider readiness, model output authority, billing
authority, or callable runtime from metadata visibility.

## Non-Goals

- No provider SDK calls.
- No enabled runtime invocation by default.
- No credential validation authority through this invocation lane.
- No network calls by default.
- No network calls outside the two named exact-scoped live adapters.
- No fallback execution until a separate exact-approved fallback lane validates
  per-attempt approval, CostGovernor, idempotency, receipt, and safe-disable
  scopes.
- No model output authority.
- No raw prompt, response, or provider payload persistence.
- No broad provider enabled toggle.
- No fallback execution from provider router dry-run proposals.
- No billing authority.
- No provider response truth authority.
- No production authority.

## Promotion Gate

Any future adapter enablement PR must keep typed runtime contracts, focused
tests, OpenAPI/route truth, CLI inspection parity, Action Inbox/Settings/Models
blocked-state UI parity, CostGovernor enforcement, receipt storage, policy
validation, redaction tests, revocation or safe-disable proof, and a verifier
that fails if any provider lane can run without exact approval and complete
policy/cost/receipt posture.
