# Foundation Gate Implementation Plan v0.52.0

v0.52.0 adds Foundation Gate coverage for M48 First Internal TestFlight Build.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.52.0 does not enable skills, plugins, native build workflows, mobile
authority, build execution, upload execution, or production authority.

Gate coverage:

- M48 first internal TestFlight build candidate contract exists and validates.
- The M48 candidate is reviewed-candidate-only, review-only, internal-only, and
  redacted metadata/ref-only.
- Build execution, committed build artifacts, IPA creation, TestFlight upload,
  signing material storage, App Store Connect API calls, external beta, public
  distribution, mobile sensors, approval execution, context injection, memory
  write, raw data export, and production authority are denied.
- Static verification rejects Xcode projects, Swift packages, Info.plist,
  entitlements, ExportOptions.plist, archives, IPAs, provisioning profiles,
  certificates, private keys, Fastlane lanes, CI upload workflows, and runtime
  upload code.
- OpenAPI remains at 75 paths and adds no mobile build, TestFlight upload,
  signing, App Store Connect, context, memory, sensor, or execution route.
- Active roadmap docs mark M48 implemented/released and keep M49-M60
  planned/provisional.

v0.52.0 adds no build execution, committed build artifact, IPA, App Store
Connect API call, TestFlight upload, signing material storage, credential
handling, external beta, public distribution, mobile approval capture,
production authority, dependency, or M49 implementation.
