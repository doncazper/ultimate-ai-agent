# Foundation Gate Implementation Plan v0.77.0

v0.77.0 adds Foundation Gate coverage for M73 Browser Automation Contract
Review.

Gate coverage includes:

- M73 Browser Automation Contract Review
- M73 Browser Automation Contract Static Safety
- M73 Browser Automation Contract Route Boundary
- M73 Roadmap Currentness

The Gate checks that M73 browser automation contract review exists, remains
contract-only and review-only, keeps browser automation disabled by default,
treats observe-only adapter work as M74 candidate only, denies browser observe,
browser navigation, browser click, form fill, screenshot, raw DOM, authenticated
browser profile, cookies or credentials, download or upload, remote browser,
network interception, network call, model call, tool execution, memory write,
context injection, backend route drift, Control Center control drift,
dependencies, and production authority.

The Gate checks that evaluator boundaries revalidate safety-critical fields.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M74 remains future.
