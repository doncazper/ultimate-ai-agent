# M47 to M48 Boundary

M47 implements TestFlight Pipeline, Internal Only as an internal-only contract
and checklist. It is preparation for future distribution review, not a build or
upload workflow.

Allowed in M47:

- source snapshot checklist contract
- build/archive plan contract
- signing asset presence check contract
- internal distribution review contract
- rollback plan contract
- redacted audit receipt plan contract
- static verification that no build, signing, upload, or production artifacts are present

Blocked in M47:

- build execution
- upload execution
- App Store Connect API calls
- signing asset storage
- provisioning profile storage
- certificate or private key storage
- Fastlane lanes
- CI upload workflows
- external beta distribution
- public distribution
- production authority
- mobile sensor access
- background collection
- approval execution
- context injection
- memory write
- raw data export

M48 remains future after M47. M48 must perform its own strict review before any
first internal TestFlight build is created or described as accepted.
