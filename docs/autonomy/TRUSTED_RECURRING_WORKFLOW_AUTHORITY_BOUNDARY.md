# Trusted Recurring Workflow Authority Boundary

M132 can define safe refs for a trusted recurring workflow review envelope.
It cannot start a workflow, activate recurrence, run a scheduler, start a
background worker, execute tools, perform autonomous actions, or grant
production authority.

M132 is exact-bound to M131 scoped work-session decisions, M97 recurring
automation contracts, M98 scoped low-risk recurring records, cadence refs,
approval bundle refs, approval renewal refs, expiration refs, stop condition
refs, risk refs, audit refs, replay refs, revocation refs, kill-switch refs,
and no-effect receipt refs.

Forbidden boundary crossings:

- start trusted recurring workflows
- activate recurrence
- start recurring runtime
- run schedulers, daemons, or background workers
- implement M133 or long-running supervisor authority
- execute tools, shell, browser, network, plugin, connector, mobile, remote,
  model, memory, or context work
- add backend routes, Control Center controls, dependencies, beta release, or
  production authority
