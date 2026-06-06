# M67 Revocation + Kill Switch

M67 adds Revocation + Kill Switch contracts as contract-only, review-only,
deterministic records over M66 scoped approval bundles.

Revocation + Kill Switch records are not runtime authority. They record
revocation requested and kill-switch requested states for review only, bind those
requests to an exact scoped approval bundle, and preserve approval refs as
identifiers. They do not revoke a live bundle, activate a kill switch, stop a
session, kill a process, start or activate autonomy, execute tools, write memory,
inject context, or call models/providers as authority.

## Contract Boundary

- Revocation + Kill Switch records are contract-only.
- Revocation + Kill Switch records are review-only.
- Revocation + Kill Switch records are exact-bound to a scoped approval bundle.
- Records bind exact bundle ref, source scope ref, audit replay view ref,
  simulation result ref, actor ref, resource refs, capability refs, allowlist
  refs, revocation ref, audit ref, replay ref, and approval refs.
- Revocation requested is a recorded review state only.
- Kill-switch requested is a recorded review state only.
- Approval refs are identifiers and never authority.
- `approval_test_` refs are denied.
- Records are actor-bound, resource-bound, capability-bound, allowlist-bound,
  non-transferable, and replay-safe.
- Evaluator boundaries revalidate the scoped approval bundle and safety-critical
  record fields.

## Non-Authority Boundary

M67 grants no authority and performs no side effects:

- no revocation action
- no kill-switch activation
- no session stop
- no process kill
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

M68 remains future.
