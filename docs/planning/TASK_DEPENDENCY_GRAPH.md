# Task Dependency Graph

Status: active M29 contract. Current active baseline: **v0.33.0**.

M29 validates task dependencies before a plan can be marked valid for review.

The dependency graph denies:

- duplicate step IDs
- missing dependency targets
- dependency cycles
- malformed dependency refs

Dependency validation is deterministic and local. It does not schedule work, run steps, execute tools, mutate files, write memory, or call networks/models.

M30-M40 remain planned/provisional.
