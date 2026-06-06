# Foundation Gate Implementation Plan v0.83.0

v0.83.0 adds Foundation Gate coverage for M79 Plugin Install Review, Disabled
by Default.

Gate coverage:
- M79 plugin install review contracts exist and build a review-ready disabled
  decision.
- Exact approval binding is enforced.
- M78 manifest security decision binding is enforced.
- Plugin install, plugin enablement, plugin execution, runtime import, network
  access, model/provider call, browser automation, shell execution, mobile
  device access, remote execution, credentials or cookies, raw manifest content,
  raw package content, raw prompt, raw provider payload, backend route, Control
  Center control, dependency, and production authority remain denied.
- Evaluator boundaries revalidate model-copy-mutated safety fields.
- M80 remains future.

The OpenAPI path count remains 75.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.
