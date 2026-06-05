# CCC iOS Skeleton, No Authority

Status: Current M44 mobile skeleton contract for v0.48.0.

v0.48.0 / M44 implements CCC iOS Skeleton, No Authority as a source-only,
mock-only, read-only, non-authoritative SwiftUI skeleton. The skeleton is a
review surface for future native-client work; it is not production workflow and
not runtime authority.

M44 adds static Swift source under `apps/ccc-ios/` only. It adds no Xcode
project, no Swift package, no Info.plist, no entitlements, no backend route, no
mobile API route runtime, no network, no mobile sensor access, no OS permission
integration, no approval capture, no approval execution, no context injection,
no memory write, no file mutation, no execution, no credential handling, no
cookie handling, no background collection, no TestFlight pipeline, no signing
workflow, no store workflow, and no production authority.

M44 skeleton rules:

- source-only.
- mock-only.
- read-only.
- non-authoritative.
- no Xcode project.
- no Swift package.
- no Info.plist.
- no entitlements.
- no backend route.
- no mobile API route runtime.
- no network.
- no mobile sensor access.
- no OS permission integration.
- no approval capture.
- no approval execution.
- no context injection.
- no memory write.
- no file mutation.
- no execution.
- no credential handling.
- no cookie handling.
- no background collection.
- no production authority.

Python Agent Core remains the authority boundary. CCC iOS is a future
governance/control surface and is not the agent brain. Model output, runtime
output, memory refs, context pack refs, tool-intent refs, task-plan refs, mobile
endpoint refs, and approval refs cannot authorize iOS behavior.

M45 remains future and is limited to CCC iOS Local Read-Only Connection.
