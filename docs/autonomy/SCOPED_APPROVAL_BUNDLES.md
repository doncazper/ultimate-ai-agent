# M66 Scoped Approval Bundles

M66 adds scoped approval bundles as contract-only, review-only, deterministic
records for grouping exact approval refs under one already-reviewed autonomy
scope.

Scoped approval bundles are not approval authority. They bind safe approval refs
to the exact source scope, exact audit replay view, exact actor, exact resource
refs, exact capability refs, exact allowlist refs, exact duration ceiling, exact
risk ceiling, exact revocation ref, exact audit ref, and exact replay ref.

## Contract Boundary

- Scoped approval bundles are exact-scope.
- Scoped approval bundles are actor-bound.
- Scoped approval bundles are resource-bound.
- Scoped approval bundles are capability-bound.
- Scoped approval bundles are allowlist-bound.
- Scoped approval bundles are non-transferable.
- Scoped approval bundles are revocable.
- Scoped approval bundles are replay-safe.
- Approval refs are identifiers and never authority.
- `approval_test_` refs are denied.
- Revoked, expired, or replay-used bundles are denied.
- Evaluator boundaries revalidate source scope and audit replay view fields.

## Non-Authority Boundary

M66 grants no authority and performs no side effects:

- no policy activation
- no session start
- no autonomous actions
- no background worker
- no execution
- no tool execution
- no shell execution
- no network tools
- no browser automation
- no plugin execution
- no mobile sensor access
- no remote execution
- no memory write
- no context injection
- no model/provider authority
- no backend route
- no Control Center control
- no dependency
- no production authority

M67 remains future.
