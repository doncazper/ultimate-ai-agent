# Foundation Gate Implementation Plan v0.80.0

v0.80.0 adds Foundation Gate coverage for M76 OpenWebUI Runtime Bridge v1.

New criteria:

- M76 OpenWebUI Runtime Bridge v1
- M76 OpenWebUI Runtime Bridge Static Safety
- M76 OpenWebUI Runtime Bridge Route Boundary
- M76 Roadmap Currentness

The Gate checks that the M76 OpenWebUI runtime bridge exists, produces
deterministic review-only bridge envelopes from safe refs only, denies live
OpenWebUI connections, OpenWebUI runtime calls, OpenWebUI handoff execution,
provider calls, model calls, model authority, tool execution, memory writes,
context injection, network calls, credentials or cookies, raw prompts, raw
provider payloads, raw content, backend routes, Control Center controls,
dependencies, and production authority.

The OpenAPI path count remains 75. No OpenWebUI runtime bridge route, handoff
route, chat send route, model/provider route, tool execution route, memory
write route, context injection route, or raw payload route is added.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M77 remains future.
