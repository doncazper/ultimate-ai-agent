# M44 to M45 Boundary

Status: Active boundary for v0.48.0 / M44.

M44 implements CCC iOS Skeleton, No Authority as source-only SwiftUI skeleton
work. It creates static mock read-only views and no-authority boundary copy. It
does not add an Xcode project, Swift package, Info.plist, entitlements, native
build workflow, signing/store workflow, TestFlight pipeline, backend route,
mobile API route runtime, network call, approval capture, approval execution,
mobile sensor access, OS permission integration, background collection,
credential handling, cookie handling, context injection, memory write, file
mutation, execution, or production authority.

The M44 skeleton cannot use M43 planned endpoint refs as callable routes. It
cannot capture approvals, connect to a backend, write memory, inject context, or
execute tools/actions/tasks.

Blocked until a dedicated reviewed M45 milestone:

- local read-only connection.
- backend/mobile connection runtime.
- network call.
- approval capture.
- approval execution.
- mobile sensor access.
- OS permission integration.
- background collection.
- raw data.
- credential handling.
- cookie handling.
- context injection.
- memory write.
- file mutation.
- execution.
- production authority.

M45 remains future after M44 and is limited to CCC iOS Local Read-Only
Connection. M45 must remain read-only and local-only.
