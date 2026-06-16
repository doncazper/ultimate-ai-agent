# Long-Running Task Supervisor

Checkpoint M133 implements Long-Running Task Supervisor as contract-only,
review-only, long-running-supervisor-only, deterministic, local-only, and
safe-ref-only.

M133 records a supervisor review envelope using exact scope refs, Mode 5,
M132 trusted workflow decision, M131 scoped work-session decision, supervisor
plan, task state, run state, heartbeat plan, checkpoint plan, checkpoint refs,
context budget, pause condition, resume condition, stop condition, risk
decision, audit, replay, revocation, kill-switch, and no-effect receipt refs.

M133 adds no supervisor start, no supervisor runtime, no task supervision, no
heartbeat monitor, no checkpoint scheduler, no resume execution, no recovery
execution, no human checkpoint scheduling, no scheduler, no background worker,
no autonomous actions, no execution, no tool execution, no shell execution, no
network access, no browser automation, no plugin execution, no connector
runtime, no account auth, no model call, no memory write, no context injection,
no backend route, no Control Center control, no dependency, no beta release,
and no production authority.

M134 remains future Human Checkpoint Scheduling work. M133 does not add a
runtime prompt, scheduler, background worker, or long-running supervisor loop.
