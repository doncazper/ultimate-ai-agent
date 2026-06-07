# Multi-Tool Dry-Run Promotion Authority Boundary

M93 is not runtime authority. It creates a review-only decision that says whether dry-run and real-run plan metadata are equivalent enough for human review.

Exact M92 binding is required. Exact promotion approval is required. Wildcard approval denied prevents approval refs, approval_test_ refs, model refs, memory refs, context refs, tool-intent refs, task-plan refs, or broad approvals from authorizing real execution.

M93 grants no unapproved real execution, no real-run execution, no tool execution, no autonomous execution, no session start, no command execution, no shell execution, no subprocess execution, no filesystem mutation, no network access, no browser click, no browser form, no plugin execution, no remote execution, no model call, no memory write, no context injection, no background worker, no backend route, no Control Center control, no dependency, and no production authority.

Evaluator boundaries revalidate model_copy-mutated authority flags. M94 remains future.
