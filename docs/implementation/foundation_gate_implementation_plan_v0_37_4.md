# Foundation Gate Implementation Plan v0.37.4

Status: active Foundation Gate implementation plan for v0.37.4.

v0.37.4 is a roadmap/docs/verifier-only patch. The Foundation Gate expectation
is documentation currentness, roadmap supersession consistency, and no route or
capability drift.

## Gate Expectations

- VERSION, Python package version, pyproject version, and Control Center package
  version agree on `0.37.4`.
- README, documentation index, canonical map, canonical roadmap, and post-M20
  roadmap docs point to the active M34-M60 supersession source.
- M34-M60 labels match the active supersession sequence.
- Old active M35-M40 projection labels are rejected by documentation-integrity
  verification.
- OpenAPI path count remains `74`.
- No backend routes, frontend features, dependencies, runtime behavior,
  mobile/TestFlight implementation, or production authority are added.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before it can be trusted by a runtime boundary.
