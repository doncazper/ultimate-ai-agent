# Scoped Approval Bundle Contracts

M66 introduces the `ScopedApprovalBundle` contract plus builder and validator:

- `ScopedApprovalBundle`
- `build_scoped_approval_bundle`
- `validate_scoped_approval_bundle`

These contracts are contract-only, review-only, deterministic, exact-scope,
non-transferable, revocable, and replay-safe. They group approval refs as
identifiers only.

## Required Bindings

Each scoped approval bundle must bind:

- exact source scope ref
- exact audit replay view ref
- exact simulation result ref
- exact actor ref
- exact resource refs
- exact capability refs
- exact allowlist refs
- exact duration ceiling
- exact risk ceiling
- exact revocation ref
- exact audit ref
- exact replay ref
- exact approval refs

## Validation Requirements

Validation denies:

- missing approval refs
- duplicate approval refs
- `approval_test_` refs
- revoked bundles
- expired bundles
- replay-used bundles
- transfer across actor, resource, capability, allowlist, duration, risk,
  revocation, audit, or replay boundaries
- unsafe or secret-like metadata
- policy activation
- session start
- autonomous actions
- background worker
- execution
- tool execution
- shell execution
- network tools
- browser automation
- plugin execution
- mobile sensor access
- remote execution
- memory write
- context injection
- model/provider authority
- backend route
- dependency
- production authority

M67 remains future.
