# M68 to M69 Boundary

M68 implements Autonomy Risk Classifier contracts as contract-only, review-only,
deterministic validation over exact scoped approval bundles and Revocation +
Kill Switch records.

M68 may:

- define autonomy risk classifier request and decision contracts.
- define risk signal contracts.
- derive the highest risk from declared risk, scoped approval bundle risk, and
  explicit risk signals.
- deny risk downgrade. Risk downgrade denied is a stable M68 safety invariant.
- bind classifier decisions to exact actor, resource, capability, allowlist,
  bundle, revocation-record, source scope, audit, and replay refs.
- keep approval refs as identifiers.
- revalidate scoped approval bundles, Revocation + Kill Switch records, risk
  signals, and derived risk at evaluator boundaries.
- document and verify no-authority behavior.

M68 must not:

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

M69 remains future. M69 may define low-risk autonomous dry-run contracts only
after M68 is accepted Green.
