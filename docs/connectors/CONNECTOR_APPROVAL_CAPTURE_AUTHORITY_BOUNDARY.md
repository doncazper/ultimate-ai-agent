# Connector Approval Capture Authority Boundary

M126 connector approval capture is review-only and safe refs only. It records
that a user reviewed and approved or denied the M125 Connector Read-Only Runtime
record for governance review. It does not grant connector authority.

Approval refs remain identifiers, not authority. `approval_test_` refs are
denied. The captured approval is exact-bound, actor-bound, user-bound,
workspace-bound, resource-bound, replay-safe, revocable, and non-transferable.

The decision envelope always keeps live connector runtime, account auth, network
access, credential handling, raw connector content, full content read, connector
write, connector send, connector delete, connector export, connector bulk
export, attachment download, model call, memory write, context injection,
execution, backend route, Control Center control, dependency, beta release, and
production authority disabled.

No captured approval may be used as connector write authority, connector send
authority, connector delete authority, export authority, context authority,
memory authority, model authority, tool authority, route authority, or production
authority.
