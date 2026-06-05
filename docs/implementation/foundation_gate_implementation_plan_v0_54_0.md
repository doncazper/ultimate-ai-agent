# Foundation Gate Implementation Plan v0.54.0

v0.54.0 implements M50 Mobile Approval Audit Hardening.

Foundation Gate coverage requires:

- M50 mobile approval audit hardening criteria.
- safe-ref-only audit reports over M49 approval records.
- status/decision consistency checks.
- duplicate idempotency mismatch denial.
- model_copy-mutated raw, unredacted, path, context, memory, export, execution,
  sensor, and background fields denied.
- secret-like metadata denied without echoing secrets.
- OpenAPI route boundary remains at 75 paths.
- no mobile audit/export/raw/context/memory/sensor/execution backend routes.
- no native audit UI, dependencies, M51 implementation, or production
  authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
declare permissions, source/provenance metadata, version pinning,
revocation/disable support, Tool Broker permission mapping, and Event Ledger
logging. It requires static review, sandbox test execution, and human approval
for high-risk capabilities before any use. M50 adds no skill package execution
capability.

The canonical checklist requires a manifest, declared permissions, Event Ledger logging, and human approval for high-risk capabilities.
