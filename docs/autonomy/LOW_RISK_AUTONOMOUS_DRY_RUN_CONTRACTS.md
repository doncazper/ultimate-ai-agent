# Low-Risk Autonomous Dry Run Contracts

M69 defines deterministic low-risk autonomous dry-run records for review only.

## Request Contract

A Low-Risk Autonomous Dry Run request contains:

- `dry_run_request_ref`
- exact M68 Autonomy Risk Classifier decision
- exact `risk_decision_ref`
- actor, resource, capability, allowlist, bundle, revocation-record, source
  scope, audit, and replay refs copied from the M68 decision
- one or more low-risk dry-run step records

The request is contract-only, review-only, dry-run-only, low risk only, and
deterministic. It cannot activate policy, start sessions, run autonomous
actions, run background workers, execute, execute tools, execute shell commands,
use network tools, run browser automation, write memory, inject context, call
models/providers as authority, add routes, or grant production authority.

## Step Contract

A Low-Risk Autonomous Dry Run step contains safe refs for the step, intent,
capability, resource, and dry-run outcome. The step risk class must be low.
The step cannot grant authority, request execution, perform execution, or hide
side effects.

## Record Contract

A Low-Risk Autonomous Dry Run record contains:

- `dry_run_request_ref`
- `risk_decision_ref`
- copied binding refs
- `step_refs`
- derived risk class
- stable reason codes
- safe summary

The record is a review-only dry-run artifact. It is not a session, not policy
activation, not autonomous action authority, not background worker authority,
not execution authority, not context injection authority, and not memory write
authority.

Evaluator boundaries revalidate the current object fields and do not trust
constructor-time validation alone. Model-copy mutated risk decisions, binding
refs, step risks, authority flags, execution flags, background-worker flags,
context-injection flags, memory-write flags, and secret-like metadata are
denied.

M70 remains future.
