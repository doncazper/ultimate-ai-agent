# M65 Autonomy Audit + Replay Viewer

M65 adds an autonomy audit + replay viewer as contract-only, review-only, and
replay-view-only work over M64 Autonomous Plan Simulator result records.

The viewer displays deterministic safe refs for an exact simulation result,
its exact simulation request, exact policy decision, and exact replay step
sequence. The replay viewer is not a replay runner. It is a local validation
contract for inspecting already-simulated autonomy plans without granting
authority.

## Contract Boundary

- The viewer binds to the exact simulation result ref.
- The viewer binds to the exact replay step refs derived from the simulation.
- The viewer is deterministic.
- Approval refs are identifiers and never authority.
- `approval_test_` refs are denied.
- Safe summaries and metadata must remain redacted and secret-free.
- Evaluator boundaries revalidate the current simulation result and replay
  fields instead of trusting constructor-time validation.

## Non-Authority Boundary

M65 grants no authority and performs no side effects:

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

M66 remains future.
