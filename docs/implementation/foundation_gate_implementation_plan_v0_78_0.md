# Foundation Gate Implementation Plan v0.78.0

v0.78.0 adds Foundation Gate coverage for M74 Browser Observe-Only Adapter.

New criteria:

- M74 Browser Observe-Only Adapter
- M74 Browser Observe-Only Static Safety
- M74 Browser Observe-Only Route Boundary
- M74 Roadmap Currentness

The Gate checks that M74 browser observe-only adapter exists, requires an
explicit injected observation, returns redacted visible text preview outputs
with safe refs only, denies browser automation, navigation, clicks, form fill,
screenshots, raw DOM, authenticated browser profiles, cookies or credentials,
downloads/uploads, remote browser control, network interception, network calls,
model calls, tool execution, memory writes, context injection, backend routes,
Control Center controls, dependencies, and production authority.

The OpenAPI path count remains 75. No backend browser observe or browser
control route is added.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M75 remains future.
