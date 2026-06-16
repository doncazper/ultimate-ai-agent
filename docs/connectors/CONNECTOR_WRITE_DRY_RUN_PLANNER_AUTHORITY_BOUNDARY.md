# Connector Write Dry-Run Planner Authority Boundary

M127 connector write dry-run planning is review-only, dry-run-only, and safe
refs only. It records that a proposed connector write intent was prepared for
governed inspection. It does not grant connector authority.

The dry-run plan is exact-bound to the M126 connector approval capture record,
the M125 Connector Read-Only Runtime record, actor-bound refs, user-bound refs,
workspace-bound refs, connector scope refs, connector allowlist refs, source
operation allowlist refs, redacted metadata preview refs, safe write target
refs, safe payload summary refs, audit refs, replay refs, and idempotency keys.

Approval refs remain identifiers, not authority. `approval_test_` refs are
denied. A dry-run plan is non-transferable, replay-safe, revocable, and cannot
be promoted without a later reviewed M128 milestone.

The decision envelope always keeps live connector runtime, account auth, network
access, credential handling, raw connector content, full content read, connector
write execution, connector send execution, connector delete execution, connector
export, connector bulk export, attachment download, model call, memory write,
context injection, execution, backend route, Control Center control, dependency,
beta release, and production authority disabled.

No M127 dry-run plan may be used as connector write authority, connector send
authority, connector delete authority, export authority, context authority,
memory authority, model authority, tool authority, route authority, or
production authority.
