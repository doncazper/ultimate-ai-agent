# v0.48.1 README Import

v0.48.1 hardens M44 CCC iOS Skeleton, No Authority.

It preserves the source-only SwiftUI skeleton introduced by v0.48.0 and repairs
release verification so the reviewed `apps/ccc-ios/README.md` and Swift source
files under `apps/ccc-ios/Sources/UltimateAIAgentCCC/` are allowed. Native
build, signing, store, sensor, permission, runtime, and authority files remain
blocked by M44 and mobile safety verifiers.

No runtime authority is added. M45 remains future.
