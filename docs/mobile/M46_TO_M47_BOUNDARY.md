# M46 to M47 Boundary

Status: Active boundary for v0.50.0 / M46.

M46 implements iOS Review/Receipt Read-Only Surfaces as source-only, read-only,
redacted summary display for mock non-authoritative review packet and receipt
data. It adds no runtime network call and no mobile API route runtime.

M46 does not add a backend route, approval capture, approval execution, raw
data, raw payload display, raw absolute path display, context injection, memory
write, file mutation, export, execution, mobile sensor access, OS permission
integration, background collection, credential handling, cookie handling, or
production authority.

M46 also adds no Xcode project, no Swift package, no Info.plist, no
entitlements, no signing workflow, no store workflow, and no TestFlight
pipeline.

Blocked until a dedicated reviewed M47 milestone:

- TestFlight Pipeline, Internal Only.
- native build workflow.
- signing workflow.
- provisioning workflow.
- store workflow.
- mobile approval capture.
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

M47 remains future after M46. It must remain internal-only and must not introduce
mobile authority, secrets, sensors, background collection, or production
authority.
