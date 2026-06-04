# Execution Dependency Policy

Status: active M30 source-of-truth documentation.

M30 dependency validation is deterministic and local.

Rules:

- duplicate execution step IDs are denied.
- missing dependency step IDs are denied.
- self-dependencies are denied.
- direct and indirect dependency cycles are denied.
- a dependent step cannot advance until all dependency steps are
  `completed_no_effect`.
- ready-step ordering is deterministic by step ID after dependency filtering.
- out-of-order completion is denied when a step is not `ready`.
- optional dependency metadata cannot hide required dependencies or authority
  dependencies.

Dependency validation authorizes no execution. It only determines whether a
no-effect state transition may be represented as safe state-machine progress.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
The dependency graph must be acyclic. Duplicate execution step IDs, missing
dependency refs, self-dependencies, direct dependency cycles, and indirect
dependency cycles are denied before any no-effect transition is approved.
