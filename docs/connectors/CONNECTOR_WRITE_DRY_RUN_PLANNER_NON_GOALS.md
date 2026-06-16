# Connector Write Dry-Run Planner Non-Goals

M127 does not implement connector write execution. It is connector write
dry-run planning only, review-only, exact-bound, and safe refs only.

Non-goals:

- no live connector runtime
- no account auth
- no network access
- no credential handling
- no raw connector content
- no full content read
- no connector write execution
- no connector send execution
- no connector delete execution
- no connector export
- no connector bulk export
- no attachment download
- no model call
- no memory write
- no context injection
- no execution
- no backend route
- no Control Center control
- no dependency
- no M128 work
- no beta release
- no production authority

Approval refs remain identifiers, not authority. `approval_test_` remains
denied. M128 remains future.
