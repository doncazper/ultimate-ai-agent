# Foundation Gate Implementation Plan v1.7.2

v1.7.2 is a post-M103 versioning currentness repair follow-up.

Foundation Gate and verifier coverage should confirm:

- current baseline metadata is v1.7.2.
- M103 remains the latest implemented capability baseline.
- M104-M150 remain planned/provisional.
- already-pushed tags remain immutable historical internal milestone tags.
- future M104-M149 conveyor milestones use checkpoint labels instead of product
  SemVer tags.
- M150 is the next product release target v1.0.0-alpha.
- beta begins only after alpha UI and supporting safety/product work are
  reviewed, accepted, and promoted by a later roadmap patch.
- stale fast-version rows such as v1.8.0/M104, v1.7.2/M104, v1.7.48/M150, and
  v1.54.0/M150 beta are denied in active roadmap docs.
- no capability implementation, M104 work, backend route, Control Center
  control, dependency, execution, broad autonomy, mobile sensor runtime, memory
  write, context injection, model/provider call, production authority, or M151
  work is added.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for any runtime authority.
