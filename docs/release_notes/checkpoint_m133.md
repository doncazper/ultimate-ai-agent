# Checkpoint M133 - Long-Running Task Supervisor

Checkpoint M133 implements review-only long-running task supervisor contracts
under the v1.7.2 product baseline.

Included:

- Long-running task supervisor policy, request, decision, and no-effect
  receipt plan contracts
- Exact bindings to Mode 5, M132 trusted workflow decisions, M131 scoped
  work-session decisions, task state, heartbeat plan, checkpoint plan, context
  budget, pause/resume/stop conditions, audit/replay, revocation, and
  kill-switch refs
- M133 docs, verifier coverage, and Foundation Gate criteria

Not included:

- No supervisor start, supervisor runtime, task supervision, heartbeat monitor,
  checkpoint scheduler, resume execution, recovery execution, human checkpoint
  scheduling, scheduler, background worker, autonomous actions, execution,
  routes, controls, dependencies, beta release, production authority, M134
  implementation, or M135 implementation

M134 remains planned/provisional.
