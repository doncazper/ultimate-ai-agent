# Foundation Gate Implementation Plan v0.49.0

v0.49.0 adds Foundation Gate coverage for M45 CCC iOS Local Read-Only
Connection.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.49.0 does not enable skills, plugins, native build workflows, mobile
authority, or production authority.

Gate coverage:

- `m45_ccc_ios_local_read_only_connection` validates the default M45 contract,
  docs, no-authority flags, and M46 future boundary.
- `m45_ios_local_connection_static_safety` verifies Swift source is source-only,
  read-only, loopback-only status display and contains no runtime network,
  sensor, permission, credential, background, approval, context, memory, file, or
  execution APIs.
- `m45_mobile_route_boundary` keeps OpenAPI at the accepted 75-path boundary and
  denies mobile connection, raw-data, approval, context, memory, execution, and
  mobile runtime routes.
- `m45_roadmap_currentness` requires v0.49.0 / M45 implemented/released and
  M46-M60 planned/provisional.

The gate adds no runtime network call, backend route, approval capture,
approval execution, raw data, context injection, memory write, file mutation,
execution, background collection, sensor access, credential handling, signing,
TestFlight workflow, dependency, production authority, or M46 implementation.
