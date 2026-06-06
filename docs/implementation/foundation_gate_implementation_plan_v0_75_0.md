# Foundation Gate Implementation Plan v0.75.0

v0.75.0 adds Foundation Gate coverage for M71 Network Tool Contract Review.

The gate checks that M71 network tool contract review files exist, the default
policy is contract-only, review-only, disabled by default, deterministic, and
M72-candidate-only, and that request, decision, and receipt contracts grant no
runtime authority.

Gate coverage includes:

- M71 Network Tool Contract Review
- M71 Network Tool Contract Static Safety
- M71 Network Tool Contract Route Boundary
- M71 Roadmap Currentness

The Gate denies route drift for network fetch/request routes, HTTP fetch/request
routes, tool-runtime execution routes, browser/plugin execution routes, memory
write routes, and context injection routes. Static safety checks reject source
fragments that imply network calls, HTTP fetches, unrestricted/authenticated
network actions, credentials or cookies, request bodies, non-GET methods,
downloads, exports, raw response bodies, backend routes, Control Center
controls, dependencies, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M71 adds no dependency, no plugin enablement, no shell execution, no browser
automation, and no external service.

M72 remains future.
