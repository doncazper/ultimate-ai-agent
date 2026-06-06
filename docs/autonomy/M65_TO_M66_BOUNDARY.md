# M65 to M66 Boundary

M65 implements Autonomy Audit + Replay Viewer as contract-only, review-only,
replay-view-only, deterministic validation work over M64 simulation results.

M65 may:

- define exact simulation result binding.
- define exact replay step binding.
- display safe audit and replay refs.
- validate that replay views grant no authority.
- revalidate mutated simulation result fields at evaluator boundaries.
- document and verify no-authority behavior.

M65 must not:

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

M66 remains future. M66 may define scoped approval bundles only after M65 is
accepted Green, and approval refs remain identifiers unless a later reviewed
milestone explicitly changes a narrowly scoped contract.
