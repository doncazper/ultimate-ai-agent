# Long-Running Task Supervisor Policy

M133 policy records are contract-only, review-only,
long-running-supervisor-only, deterministic, local-only, safe-ref-only, and
exact scope bound.

Every M133 policy requires safe refs for:

- Mode 5
- M132 trusted workflow decision
- M131 scoped work-session decision
- supervisor plan
- task state and run state
- heartbeat plan
- checkpoint plan and checkpoint refs
- context budget
- pause condition, resume condition, and stop condition
- risk decision
- audit and replay
- revocation and kill-switch
- no-effect receipt

M133 denies supervisor runtime, supervisor start, task supervision, heartbeat
monitor, checkpoint scheduler, resume execution, recovery execution, human
checkpoint scheduling, scheduler, background worker, autonomous actions,
execution, tool execution, shell execution, network access, browser automation,
plugin execution, connector runtime, account auth, mobile sensor runtime,
remote execution, model call, memory write, context injection, backend route,
Control Center control, dependency, beta release, production authority, M134
implementation, and M135 recovery implementation.
