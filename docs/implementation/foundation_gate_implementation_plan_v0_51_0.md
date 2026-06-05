# Foundation Gate Implementation Plan v0.51.0

v0.51.0 adds Foundation Gate coverage for M47 TestFlight Pipeline, Internal
Only.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.51.0 does not enable skills, plugins, native build workflows, mobile
authority, build/upload execution, or production authority.

Gate coverage:

- M47 internal TestFlight pipeline contract exists and validates.
- M47 pipeline stages are internal-only, contract-only, checklist-only, and
  review-required.
- Build execution, upload execution, signing asset storage, App Store Connect
  API calls, external beta, public distribution, and production authority are
  denied.
- Static verification rejects Xcode projects, Swift packages, Info.plist,
  entitlements, ExportOptions.plist, provisioning profiles, certificates,
  private keys, Fastlane lanes, CI upload workflows, and runtime upload code.
- OpenAPI remains at 75 paths and adds no mobile TestFlight/signing/upload
  route.
- Active roadmap docs mark M47 implemented/released and keep M48-M60
  planned/provisional.

v0.51.0 adds no build execution, upload execution, App Store Connect API call,
signing asset storage, credential handling, external beta, public distribution,
production authority, dependency, or M48 implementation.
