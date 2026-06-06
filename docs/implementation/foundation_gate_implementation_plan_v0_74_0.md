# Foundation Gate Implementation Plan - v0.74.0

v0.74.0 adds Foundation Gate coverage for M70 Autonomy Foundation Freeze.

The gate checks that Autonomy Foundation Freeze contracts exist, remain
contract-only, review-only, freeze-only, deterministic, and no-authority, and
revalidate accepted M61-M69 milestone refs, checklist refs, execution flags,
route flags, dependency flags, and secret-like metadata.

The gate also checks static safety, OpenAPI route stability, documentation
currentness, and that M71 remains future.

Skill Package Security Rule:

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
