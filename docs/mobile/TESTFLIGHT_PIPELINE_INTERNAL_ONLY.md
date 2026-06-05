# TestFlight Pipeline, Internal Only

v0.51.0 / M47 defines the TestFlight Pipeline, Internal Only milestone as an
internal-only contract and checklist.

M47 is not a build release. It adds no build execution, no upload execution, no
signing asset storage, no App Store Connect API call, no credential handling, no
mobile sensor access, no background collection, no external beta, no public
distribution, and no production authority.

No public distribution is added.
No mobile sensor access is added.

The short-form boundary is: no build execution, no upload execution, no signing
asset storage, no App Store Connect API call, no external beta, and no
production authority.

The pipeline contract records the future stages that must be reviewed before a
later internal build:

- reviewed source snapshot
- build/archive plan
- signing asset presence check, with no signing asset storage
- internal distribution review
- rollback plan
- redacted audit receipt plan

All stages are contract-only and checklist-only. They require human review and
cannot execute a build, upload a build, call App Store Connect, store signing
materials, enable external beta distribution, enable public distribution, or
grant production authority.

M47 adds no Xcode project, no Swift package, no Info.plist, no entitlements, no
ExportOptions.plist, no provisioning profile, no certificate, no private key, no
Fastlane lane, no CI upload workflow, and no signing/store workflow. The CCC iOS
source remains source-only and read-only.

M48 remains future. M48 is the first internal TestFlight build milestone and is
the earliest place a reviewed internal build artifact may be considered.
