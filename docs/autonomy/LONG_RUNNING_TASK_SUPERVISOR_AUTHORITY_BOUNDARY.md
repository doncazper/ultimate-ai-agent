# Long-Running Task Supervisor Authority Boundary

M133 can define safe refs for a long-running task supervisor review envelope.
The envelope can describe a bounded task, declared run state, heartbeat plan,
checkpoint plan, context budget, pause condition, resume condition, stop
condition, audit, replay, revocation, kill-switch, and no-effect receipt.

M133 is exact-bound to M132 trusted workflow decisions and M131 scoped
work-session decisions. It remains a local contract and does not create a live
supervisor.

M133 must not:

- start a supervisor
- run a supervisor runtime
- activate task supervision
- monitor heartbeats
- schedule checkpoints
- resume or recover work
- schedule human checkpoints
- run a scheduler or background worker
- execute tools, shell, network, browser, plugin, connector, mobile, remote,
  model, memory, or context work
- add backend routes or Control Center controls
- add dependencies
- implement M134 or M135
- enable beta release or production authority
