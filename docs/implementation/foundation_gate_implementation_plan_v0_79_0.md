# Foundation Gate Implementation Plan v0.79.0

v0.79.0 adds Foundation Gate coverage for M75 Browser Action Dry-Run Planner.

New criteria:

- M75 Browser Action Dry-Run Planner
- M75 Browser Action Dry-Run Static Safety
- M75 Browser Action Dry-Run Route Boundary
- M75 Roadmap Currentness

The Gate checks that the M75 browser action dry-run planner exists, produces
deterministic reviewable action plans from safe refs only, denies browser action
execution, browser session start, browser navigation execution, browser click
execution, form fill execution, screenshots, raw DOM, authenticated browser
profiles, cookies or credentials, downloads/uploads, remote browser control,
network interception, network calls, model calls, tool execution, memory writes,
context injection, backend routes, Control Center controls, dependencies, and
production authority.

The OpenAPI path count remains 75. No backend browser action planner route,
browser action execution route, browser control route, tool execution route,
network expansion route, memory write route, or context injection route is
added.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M76 remains future.
