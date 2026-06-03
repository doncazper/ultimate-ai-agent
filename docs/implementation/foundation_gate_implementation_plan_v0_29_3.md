# Foundation Gate Implementation Plan v0.29.3

Status: Active for v0.29.3 documentation organization.

## Scope

v0.29.3 strengthens documentation organization and integrity checks only.

## Gate Criteria

- Active version files point to v0.29.3.
- `docs/README.md` and archive entrypoints exist.
- Current release packets live under `docs/archive/releases/v0_29_3/`.
- Historical root release/import/master-plan packets are no longer required in
  the repository root.
- `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` is marked as a historical roadmap
  projection while remaining available for compatibility.
- Active docs identify v0.29.3 as docs organization only.
- v0.29.2 remains documented as the accepted pre-M26 security hardening
  baseline.
- M25 remains implemented/hardened.
- M26 remains planned/provisional.
- OpenAPI path count remains `74`.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

v0.29.3 does not enable skill packages, plugins, runtime tools, package
installers, external execution, or M26 context-pack behavior.
