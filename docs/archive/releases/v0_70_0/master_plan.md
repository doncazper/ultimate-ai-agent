# v0.70.0 Master Plan

## Milestone

M66 - Scoped Approval Bundles

## Scope

- Add scoped approval bundle contracts.
- Bind approval refs as identifiers to exact source scope and audit replay
  view refs.
- Require exact actor, resource, capability, allowlist, duration, risk,
  revocation, audit, and replay bindings.
- Require non-transferable, revocable, replay-safe bundles.
- Deny duplicate, test, revoked, expired, and replay-used bundles.
- Add tests, docs, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

## Non-Goals

- No policy activation.
- No session start.
- No autonomous actions.
- No background worker.
- No execution.
- No tool execution.
- No shell execution.
- No network tools.
- No browser automation.
- No plugin execution.
- No mobile sensor access.
- No remote execution.
- No memory write.
- No context injection.
- No model/provider authority.
- No backend routes.
- No Control Center controls.
- No dependencies.
- No M67 implementation.
- No production authority.
