# Foundation Gate Implementation Plan v1.7.1

v1.7.1 is a post-M103 versioning currentness repair.

Foundation Gate and verifier coverage should confirm:

- current baseline metadata is v1.7.1.
- M103 remains the latest implemented capability baseline.
- M104-M150 remain planned/provisional.
- already-pushed v1.0.0 through v1.7.0 tags remain historical internal
  milestone tags and are not rewritten.
- future M104-M149 conveyor snapshots use incremental v1.7.x internal tags.
- M150 is the public product target v1.2.0-alpha.
- beta begins only after alpha UI and supporting safety/product work are
  reviewed, accepted, and promoted by a later roadmap patch.
- stale fast-version rows such as v1.8.0/M104 and v1.54.0/M150 beta are denied
  in active roadmap docs.
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
