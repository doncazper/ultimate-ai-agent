# Task Dependency Graph

Status: active M29 contract. Current active baseline: **v0.34.1**.

M29 validates task dependencies before a plan can be marked valid for review.

The dependency graph denies:

- duplicate step IDs
- missing dependency targets
- self-dependencies
- direct dependency cycles
- indirect dependency cycles
- dependency cycles
- malformed dependency refs

Dependency validation is deterministic and local. Optional dependencies cannot hide required policy, approval, or authority dependencies. Dependency ordering is review metadata only; it does not schedule work, run steps, execute tools, mutate files, write memory, or call networks/models.

M31-M40 remain planned/provisional.
