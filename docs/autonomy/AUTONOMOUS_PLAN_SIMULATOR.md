# Autonomous Plan Simulator

M64 implements the Autonomous Plan Simulator as contract-only and review-only
simulation over M63 autonomy policy decision records. The simulator is
dry-run-only and deterministic. It can order proposed simulation steps, validate
their dependency graph, and return a safe simulation result for review.

The simulator requires an already-reviewed policy decision. A policy decision is
still non-authoritative: approval refs are identifiers, policy decisions are
inputs for review, and neither one can grant runtime authority.

M64 validates that the simulation dependency graph is acyclic, rejects duplicate
simulation step refs, rejects missing dependency refs, and rejects self
dependencies. The simulation result contains safe refs and reason codes only.

M64 performs no policy activation, no session start, no autonomous actions, no
background worker, no execution, no tool execution, no shell execution, no
network tools, no browser automation, no plugin execution, no mobile sensor
access, no remote execution, no context injection, no memory write, no model or
provider authority, no backend route, no Control Center control, no dependency,
and no production authority.

M65 remains future and is reserved for Autonomy Audit + Replay Viewer work.
