# Checkpoint M132 - Autonomy Mode 5, Trusted Recurring Workflow

Checkpoint M132 implements review-only trusted recurring workflow contracts
while the product baseline remains v1.7.2.

Included:

- `TrustedRecurringWorkflowPolicy`
- `TrustedRecurringWorkflowRequest`
- `TrustedRecurringWorkflowDecision`
- `TrustedRecurringWorkflowReceiptPlan`
- M132 docs, verifier coverage, and Foundation Gate criteria

Safety boundary:

- contract-only, review-only, trusted-recurring-workflow-only, deterministic,
  local-only, safe-ref-only
- exact-bound to M131 scoped work-session decisions, M97 recurring automation
  contracts, M98 scoped low-risk recurring records, cadence, approval renewal,
  expiration, stop conditions, audit, replay, revocation, kill-switch, and
  no-effect receipt refs
- no workflow start, active recurrence, recurring runtime, scheduler,
  background worker, long-running supervisor, execution, routes, controls,
  dependencies, beta release, production authority, or M133 implementation

M133 remains planned/provisional.
