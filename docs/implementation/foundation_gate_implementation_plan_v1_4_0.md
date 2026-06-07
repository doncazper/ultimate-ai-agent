# Foundation Gate Implementation Plan v1.4.0

v1.4.0 / M100 adds Foundation Gate coverage for Mobile Permission Model v1.

Gate coverage:

- M100 Mobile Permission Model v1 contracts.
- M100 static safety.
- M100 route boundary.
- M100 roadmap currentness.

The Gate verifies that the mobile permission taxonomy, consent, revocation,
privacy copy, and permission audit contracts exist and remain contract-only. It
also verifies no mobile sensors, no runtime permission prompts, no native
permission request, no background collection, no push execution, no backend
route, no dependency, no M101 work, and no production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
provide a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for enablement.
