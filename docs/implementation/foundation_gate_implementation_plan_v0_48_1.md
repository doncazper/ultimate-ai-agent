# Foundation Gate Implementation Plan v0.48.1

v0.48.1 keeps the Foundation Gate aligned with M44 CCC iOS Skeleton, No
Authority after the pushed v0.48.0 review found a verifier mismatch.

The Gate continues to require that the CCC iOS skeleton is source-only,
mock-only, read-only, non-authoritative, route-stable, and free of native build,
signing, store, sensor, permission, runtime, and authority files. The release
adds regression coverage so the reviewed `apps/ccc-ios/` source-only files are
accepted while broader native mobile artifacts remain denied.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.48.1 does not enable skills, plugins, native build workflows, mobile
authority, or production authority.
