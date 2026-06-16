# Human Checkpoint Scheduling Policy

M134 policy records are contract-only, review-only,
human-checkpoint-scheduling-only, deterministic, local-only, safe-ref-only, and
exact scope bound.

Every M134 policy requires safe refs for:

- Mode 5
- M133 supervisor decision
- M132 trusted workflow decision
- checkpoint plan
- schedule plan
- checkpoint window
- reviewer ref
- consent and expiration
- reminder plan
- escalation plan
- pause condition and stop condition
- risk decision
- audit and replay
- revocation and kill-switch
- no-effect receipt

M134 denies checkpoint scheduler runtime, prompt runtime, notification delivery,
reminder runtime, calendar write, approval capture, escalation runtime,
supervisor runtime, recovery execution, scheduler, background worker,
autonomous actions, execution, tool execution, shell execution, network access,
browser automation, plugin execution, connector runtime, account auth, mobile
sensor runtime, remote execution, model call, memory write, context injection,
backend route, Control Center control, dependency, beta release, production
authority, and M135 implementation.
