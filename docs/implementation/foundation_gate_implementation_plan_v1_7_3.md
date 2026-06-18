# Foundation Gate Implementation Plan v1.7.3

v1.7.3 is a post-M150 local file-manager hardening baseline.

Foundation Gate and verifier coverage should confirm:

- current baseline metadata is v1.7.3.
- M150 remains the accepted v1.2.0-alpha target packet.
- file references use streaming content hashes rather than whole-file in-memory
  reads.
- file read previews are bounded to the requested preview budget with only a
  small redaction lookahead.
- apply-write and rollback use atomic replacement.
- failed atomic replacement removes temporary write files and preserves target
  content.
- no dependency, backend route, Control Center control, shell/subprocess
  execution, network access, model/provider call, memory write, context
  injection, broad autonomy, beta release, M151 work, or production authority is
  added.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for any runtime authority.
