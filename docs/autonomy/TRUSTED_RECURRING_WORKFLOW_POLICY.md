# Trusted Recurring Workflow Policy

M132 policy records are contract-only, review-only,
trusted-recurring-workflow-only, deterministic, local-only, and safe-ref-only.

Required bindings:

- exact scope
- Mode 5
- exact M131 scoped work-session decision
- M97 recurring automation contract
- M98 scoped low-risk recurring decision
- cadence
- approval bundle
- approval renewal
- expiration
- stop conditions
- risk decision
- audit and replay
- revocation and kill-switch
- no-effect receipt

Denied authority:

- workflow start, active recurrence, recurring runtime, scheduler, background
  worker, long-running supervisor, autonomous actions, execution, tool
  execution, shell execution, network access, browser automation, plugin
  execution, connector runtime, account auth, model call, memory write,
  context injection, backend route, Control Center control, dependency, beta
  release, production authority, and M133 implementation.
