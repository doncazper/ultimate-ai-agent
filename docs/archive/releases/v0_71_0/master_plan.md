# v0.71.0 Master Plan

v0.71.0 / M67 implements Revocation + Kill Switch as a contract-only,
review-only milestone.

## Scope

- Add revocation and kill-switch record contracts.
- Bind records to exact scoped approval bundles.
- Preserve approval refs as identifiers.
- Record revocation requested and kill-switch requested states for review only.
- Revalidate scoped approval bundles at evaluator boundaries.
- Deny activation, session stop, process kill, execution, memory/context writes,
  model/provider authority, backend routes, dependencies, and production
  authority.
- Add tests, docs, static verification, and Foundation Gate coverage.

## Non-Goals

M67 does not perform revocation action, activate a kill switch, stop a session,
kill a process, start autonomy, execute tools, write memory, inject context,
call models/providers as authority, add backend routes, add Control Center
controls, add dependencies, implement M68, or grant production authority.
