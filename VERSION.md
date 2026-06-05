# Ultimate AI Agent Version

Current active baseline: **v0.48.1**

v0.48.1 hardens M44 CCC iOS Skeleton, No Authority. It preserves the
source-only CCC iOS SwiftUI skeleton from v0.48.0 and repairs verifier policy so
the reviewed `apps/ccc-ios/` source-only skeleton is allowed while native build,
signing, store, sensor, permission, runtime, and authority files remain blocked.

It adds no Xcode project, Swift package, Info.plist, entitlements, native build
workflow, signing/store workflow, TestFlight pipeline, backend route, mobile API
route runtime, network call, mobile sensor access, OS permission integration,
background collection, approval capture, approval execution, context injection,
memory write, file mutation, raw data, credential handling, cookie handling,
execution, remote execution, plugin enablement, dependencies, M45
implementation, or production authority.
