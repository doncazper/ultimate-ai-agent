# M126 to M127 Boundary

Checkpoint M126 implements Connector Approval Capture only. It captures
review-only approvals and denials over exact-bound M125 Connector Read-Only
Runtime records. It is actor-bound, user-bound, workspace-bound, resource-bound,
replay-safe, revocable, safe refs only, and backed by a no-effect receipt plan.

M127 remains future as Connector Write Dry-Run Planner. M126 does not add write
planning, write execution, connector send, connector delete, connector export,
live connector runtime, account auth, network access, credential handling, raw
connector content, full content read, attachment download, model call, memory
write, context injection, execution, backend route, Control Center control,
dependency, beta release, or production authority.

Approval refs remain identifiers, not authority. `approval_test_` refs are
denied. M150 remains the planned v1.2.0-alpha target.
