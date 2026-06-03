# Foundation Gate Implementation Plan v0.29.4

Status: Active for v0.29.4 documentation archive reference repair.

## Scope

v0.29.4 strengthens documentation archive reference integrity checks only.

## Gate Criteria

- Active version files point to v0.29.4.
- Current release packets live under `docs/archive/releases/v0_29_4/`.
- `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md` exists and is indexed.
- Historical version verifiers do not live at root or under active `scripts/`.
- Archived historical verifiers are marked historical and not part of current
  validation.
- Active docs do not require root historical release packet files.
- M25 remains implemented/hardened.
- M26 remains planned/provisional.
- OpenAPI path count remains `74`.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

v0.29.4 does not enable skill packages, plugins, runtime tools, package
installers, external execution, or M26 context-pack behavior.
