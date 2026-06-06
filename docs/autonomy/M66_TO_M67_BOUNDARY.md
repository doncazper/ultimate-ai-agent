# M66 to M67 Boundary

M66 implements Scoped Approval Bundles as contract-only, review-only,
deterministic validation work over exact source scopes and exact M65 audit
replay views.

M66 may:

- define scoped approval bundle contracts.
- group exact approval refs as identifiers.
- bind bundles to exact source scopes.
- bind bundles to exact audit replay views.
- require actor-bound, resource-bound, capability-bound, allowlist-bound,
  non-transferable, revocable, and replay-safe records.
- deny expired, revoked, replay-used, duplicate, or test approval refs.
- document and verify no-authority behavior.

M66 must not:

- activate policy.
- start sessions.
- enable autonomous actions.
- run background workers.
- execute.
- execute tools.
- execute shell commands.
- use network tools.
- run browser automation.
- enable plugins.
- access mobile sensors.
- perform remote execution.
- write memory.
- inject context.
- call models/providers as authority.
- add backend routes.
- add Control Center controls.
- add dependencies.
- grant production authority.

M67 remains future. M67 may define revocation and kill switch contracts only
after M66 is accepted Green.
