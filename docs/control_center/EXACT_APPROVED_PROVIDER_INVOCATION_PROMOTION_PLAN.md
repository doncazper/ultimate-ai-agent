# Exact-Approved Provider Invocation Promotion Plan

Status: planning-only future gated lane.

This plan defines the minimum future promotion checklist for one tiny
exact-approved provider/model invocation lane. It does not implement provider
runtime, credential validation, network access, provider SDK calls, or model
invocation.

The lane may be promoted only after Provider Credential Readiness, CostGovernor
Binding, and Credential Vault Contract Shell posture remain green and the new
runtime contract has exact approval, redacted receipts, CLI inspection parity,
and UI blocked-state parity.

## Promotion Checklist

The first provider invocation lane must require all of the following before any
callable runtime can exist:

- `credential_ref`
- `provider_ref`
- `model_ref`
- `PolicyEngine` policy validation
- exact approval scope validated by `LocalApprovalAuthority`
- `CostGovernor` decision
- unknown paid cost blocked by default
- max approved USD
- idempotency ref
- redacted request receipt ref
- redacted response receipt ref
- no raw prompt, response, or provider payload persistence
- rollback or safe-disable posture
- CLI inspection parity
- UI blocked, approved, and cost-blocked states

Every future invocation attempt must fail closed when any required ref, policy
validation, approval scope, budget decision, receipt ref, or safe-disable posture
is missing.

## Minimum Contract Shape

The future runtime contract must distinguish these states before it is callable:

- `blocked_missing_credential_ref`
- `blocked_missing_provider_ref`
- `blocked_missing_model_ref`
- `blocked_missing_policy_validation`
- `blocked_missing_exact_approval_scope`
- `cost_blocked`
- `unknown_paid_cost_blocked`
- `approved_no_execution_until_receipts_ready`
- `receipt_recorded`
- `safe_disabled`

Approval refs, credential refs, provider refs, model refs, and max-approved USD
refs remain identifiers. They do not authorize provider calls unless the exact
future invocation contract validates the complete scope and records redacted
receipts.

## Receipt And Evidence Rules

Future receipts must store safe refs and redacted summaries only:

- request receipt ref
- response receipt ref
- `PolicyEngine` policy decision ref
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

Before promotion, Control Center must show provider invocation posture as one of
these states from backend-owned data:

- blocked
- approved no execution
- cost blocked
- unknown paid cost
- no provider authority
- receipt recorded
- safe disabled

The same posture must be inspectable through a repo-local CLI script before the
UI can present it as reviewable. UI labels must never imply provider connection,
provider readiness, model output authority, billing authority, or callable
runtime from metadata visibility.

## Non-Goals

- No provider SDK calls.
- No runtime invocation.
- No credential validation.
- No network calls.
- No model output authority.
- No raw prompt, response, or provider payload persistence.
- No broad provider enabled toggle.
- No billing authority.
- No provider response truth authority.
- No production authority.

## Promotion Gate

The future implementation PR must add typed runtime contracts, focused tests,
OpenAPI/route truth only if a route is added, CLI inspection parity, Action
Inbox/Settings/Models blocked-state UI parity, CostGovernor enforcement, receipt
storage, `PolicyEngine` validation, redaction tests, revocation or safe-disable
proof, and a verifier that fails if any provider invocation can occur without
exact approval and complete policy/cost/receipt posture.
