# Foundation Gate Implementation Plan v1.5.0

v1.5.0 adds M101 Mobile Sensor Contract Review Foundation Gate coverage.

Gate checks require:

- M101 contract module and tests exist
- mobile sensor capability classes are contract-only
- permission-state contract records are defined
- sensor risk classification is defined
- consent, revocation, and audit requirements are present
- sensors default off
- unknown sensor denied
- model-copy-mutated runtime flags are rejected
- OpenAPI path count remains stable
- no mobile sensor runtime route exists
- no native permission prompt, background collection, dependency, or production
  authority is added

M102 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static
review, sandbox test execution, Tool Broker permission mapping, Event Ledger
logging, version pinning, revocation/disable support, and human approval for
high-risk capabilities before any future enablement.

Required review terms include static review, Event Ledger logging, and human approval for high-risk capabilities.

M101 does not change the Skill Package Security Rule. Mobile Sensor Contract
Review is contract-only and adds no skill install, plugin enablement, tool
execution, backend route, dependency, or production authority.
