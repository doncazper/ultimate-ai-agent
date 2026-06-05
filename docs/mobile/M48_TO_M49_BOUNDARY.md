# M48 to M49 Boundary

M48 implements First Internal TestFlight Build as a reviewed internal build
candidate record. It is review-only and internal-only, not a runtime build,
upload, approval, or distribution workflow.

Allowed in M48:

- first internal TestFlight build candidate contract
- safe refs for reviewed build candidate, source snapshot, M47 pipeline
  manifest, and redacted audit receipt plan
- internal-only review status
- static verification that no committed build artifact, no IPA, no signing
  material, and no App Store Connect upload workflow are present
- documentation, tests, verifier coverage, and Foundation Gate criteria

Blocked in M48:

- build execution
- committed build artifact
- Xcode archive storage
- IPA storage
- TestFlight upload
- App Store Connect API call
- signing material storage
- provisioning profile storage
- certificate or private key storage
- Fastlane lane
- CI upload workflow
- external beta distribution
- public distribution
- production authority
- mobile sensor access
- background collection
- mobile approval capture
- approval execution
- context injection
- memory write
- raw data export
- export
- execution

M49 remains future after M48. M49 may only add Mobile Review Approval Capture
after a dedicated implementation, validation, and strict pushed-release review.
