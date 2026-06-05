# CCC iOS Local Read-Only Connection

Status: Active M45 contract for v0.49.0.

v0.49.0 / M45 implements CCC iOS Local Read-Only Connection as a
contract/status milestone. It adds local-only, loopback-only, read-only
connection metadata for the source-only CCC iOS skeleton. The connection surface
is non-authoritative and displays redacted summary refs only.

M45 adds no runtime network call. The iOS source shows local read-only
connection status and authority-boundary copy only. It does not use URLSession,
URLRequest, network frameworks, credentials, cookies, sensors, OS permissions,
background collection, or file APIs.

M45 adds no backend route, no mobile API route runtime, no approval capture, no
approval execution, no raw data, no raw payload, no context injection, no memory
write, no file mutation, no export, no execution, no mobile sensor access, no
credential handling, no cookie handling, and no production authority.

M45 also adds no Xcode project, no Swift package, no Info.plist, no
entitlements, no signing workflow, no store workflow, and no TestFlight
pipeline. The existing `apps/ccc-ios/` directory remains source-only.

Python Agent Core remains the authority boundary. CCC iOS is a control client,
not the agent brain. Model output, runtime output, memory, context packs, tool
intents, task plans, and approval refs are not authority.

M46 remains future and is limited to iOS Review/Receipt Read-Only Surfaces.
