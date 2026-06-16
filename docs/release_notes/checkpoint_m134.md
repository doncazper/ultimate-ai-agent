# Checkpoint M134 - Human Checkpoint Scheduling

Checkpoint M134 implements review-only human checkpoint scheduling contracts
under the v1.7.2 product baseline.

Included:

- Human checkpoint scheduling policy, request, decision, and no-effect receipt
  plan contracts
- Exact bindings to Mode 5, M133 supervisor decisions, M132 trusted workflow
  decisions, checkpoint plans, schedule plans, checkpoint windows, reviewer
  refs, consent, expiration, reminder plans, escalation plans,
  pause/stop conditions, audit/replay, revocation, and kill-switch refs
- M134 docs, verifier coverage, and Foundation Gate criteria

Not included:

- No checkpoint scheduled state, scheduling, prompt, notification delivery,
  reminder runtime, calendar write, approval capture, escalation runtime,
  supervisor runtime, recovery execution, scheduler, background worker,
  autonomous actions, execution, routes, controls, dependencies, beta release,
  production authority, or M135 implementation

M135 remains planned/provisional.
