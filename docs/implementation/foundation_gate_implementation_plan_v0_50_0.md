# Foundation Gate Implementation Plan v0.50.0

v0.50.0 adds Foundation Gate coverage for M46 iOS Review/Receipt Read-Only
Surfaces.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.50.0 does not enable skills, plugins, native build workflows, mobile
authority, or production authority.

Gate coverage:

- `m46_ccc_ios_review_receipt_read_only_surfaces` validates the default M46
  contract, docs, no-authority flags, and M47 future boundary.
- `m46_ios_review_receipt_static_safety` verifies Swift source is source-only,
  read-only, redacted summary display and contains no runtime network, sensor,
  permission, credential, background, approval, context, memory, file, export,
  or execution APIs.
- `m46_mobile_route_boundary` keeps OpenAPI at the accepted 75-path boundary and
  denies mobile review/receipt, raw-data, approval, context, memory, execution,
  background, sensor, TestFlight, and mobile runtime routes.
- `m46_roadmap_currentness` requires v0.50.0 / M46 implemented/released and
  M47-M60 planned/provisional.

The gate adds no runtime network call, backend route, approval capture,
approval execution, raw data, context injection, memory write, file mutation,
export, execution, background collection, sensor access, credential handling,
signing, TestFlight workflow, dependency, production authority, or M47
implementation.
