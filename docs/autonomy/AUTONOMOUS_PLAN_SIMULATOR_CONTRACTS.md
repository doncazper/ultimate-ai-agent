# Autonomous Plan Simulator Contracts

M64 adds deterministic, dry-run-only, review-only contracts for autonomous plan
simulation.

The contract set includes:

- `AutonomousPlanSimulationStep`.
- `AutonomousPlanSimulationRequest`.
- `AutonomousPlanSimulationResult`.
- validation helpers that revalidate model-copy-mutated fields at evaluator
  boundaries.

Each simulation request binds actor refs, resource refs, capability refs,
allowlist refs, audit refs, replay refs, and an M63 policy decision. The
simulator validates the dependency graph before producing a result. Duplicate
step refs, missing dependency refs, self dependencies, and cycles are denied.
The dependency graph must be acyclic.

The result is non-authoritative. It records a deterministic simulation ordering
and stable reason codes for review only. It does not activate policy, start a
session, perform execution, perform tool execution, perform shell execution,
perform network tools, perform browser automation, inject context, write memory,
start a background worker, add a backend route, add a dependency, or grant
production authority.

Approval refs are identifiers. `approval_test_` refs are denied and cannot
authorize simulation, execution, or authority.

M65 remains future.
