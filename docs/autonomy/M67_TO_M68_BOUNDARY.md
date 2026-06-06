# M67 to M68 Boundary

M67 implements Revocation + Kill Switch contracts as contract-only, review-only,
deterministic validation work over exact M66 scoped approval bundles.

M67 may:

- define revocation and kill-switch review records.
- record revocation requested state.
- record kill-switch requested state.
- bind records to exact scoped approval bundles.
- bind records to exact source scope, audit replay view, simulation result,
  actor, resource, capability, allowlist, revocation, audit, replay, and
  approval refs.
- keep approval refs as identifiers.
- revalidate scoped approval bundles at evaluator boundaries.
- deny hidden authority flags, activation flags, and side effects.
- document and verify no-authority behavior.

M67 must not:

- perform revocation action.
- activate a kill switch.
- stop sessions.
- kill processes.
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

M68 remains future. M68 may define autonomy risk classifier contracts only after
M67 is accepted Green.
