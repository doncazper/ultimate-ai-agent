# Exact-Approved Provider Invocation Promotion Plan

Status: disabled-default contract lane implemented; callable provider runtime remains future gated.

This plan defines the minimum promotion checklist for one tiny exact-approved
provider/model lane. The current implementation adds typed contracts, a
disabled-default Control Center route, CostGovernor blocking, redacted receipt
storage, CLI inspection, and UI posture labels. It does not add credential
validation, network access, provider SDK calls, live model calls, autonomous
model calls, background execution, or billing authority.

The lane may become callable only after Provider Credential Readiness,
CostGovernor Binding, Credential Vault Contract Shell posture, exact approval,
redacted receipts, CLI inspection parity, and UI blocked-state parity remain
green for a scoped adapter enablement milestone.

## Promotion Checklist

The tiny lane requires all of the following before adapter execution can occur:

- `credential_ref`
- `provider_ref`
- `model_ref`
- policy ref carried as part of the exact approval scope; `PolicyEngine`
  decision validation remains a future promotion gate before enabling a real
  adapter
- future enabled adapters must perform `PolicyEngine` policy validation before
  any provider call
- exact approval scope validated by `LocalApprovalAuthority`
- `CostGovernor` decision
- unknown paid cost blocked by default
- max approved USD
- idempotency ref
- redacted request receipt ref
- redacted response receipt ref
- `PolicyEngine` policy decision ref before any future enabled adapter can
  claim callable authority
- no raw prompt, response, or provider payload persistence
- rollback or safe-disable posture
- CLI inspection parity
- UI blocked, approved, and cost-blocked states

Every lane attempt must fail closed when any required ref, approval scope,
budget decision, receipt ref, or safe-disable posture is missing. The default
API route uses a disabled adapter and can only return blocked, cost-blocked,
approval-required, approval-invalid, or approved-no-execution posture.

## Minimum Contract Shape

The contract distinguishes these states before callable provider runtime exists:

- `blocked_missing_credential_ref`
- `blocked_missing_provider_ref`
- `blocked_missing_model_ref`
- `blocked_missing_policy_validation`
- `blocked_missing_exact_approval_scope`
- `cost_blocked`
- `unknown_paid_cost_blocked`
- `approved_no_execution`
- `receipt_recorded`
- `safe_disabled`

Approval refs, credential refs, provider refs, model refs, and max-approved USD
refs remain identifiers. They do not authorize provider calls unless the exact
lane contract validates the complete scope, passes CostGovernor checks, and
records redacted receipts.

## Receipt And Evidence Rules

Receipts must store safe refs and redacted summaries only:

- request receipt ref
- response receipt ref
- policy ref, with `PolicyEngine` policy decision ref added before any future
  enabled adapter
- cost estimate ref
- CostGovernor decision ref
- budget decision ref
- max approved USD ref
- credential ref
- provider ref
- model ref
- approval scope ref
- idempotency ref
- rollback or safe-disable ref

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
- receipt recorded
- safe disabled

The same posture is inspectable through
`scripts/inspect_tiny_provider_invocation_lane.py`. UI labels must never imply
provider connection, provider readiness, model output authority, billing
authority, or callable runtime from metadata visibility.

## Non-Goals

- No provider SDK calls.
- No enabled runtime invocation by default.
- No credential validation.
- No network calls.
- No model output authority.
- No raw prompt, response, or provider payload persistence.
- No broad provider enabled toggle.
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
