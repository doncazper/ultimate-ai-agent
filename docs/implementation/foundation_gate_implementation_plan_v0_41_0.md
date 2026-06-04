# Foundation Gate Implementation Plan v0.41.0

Status: current Foundation Gate implementation plan.
Release: **v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence**.

The v0.41.0 Foundation Gate adds M37 checks for:

- review approval capture contracts.
- safe-ref-only approval records.
- idempotency/replay protection.
- exact review packet binding.
- approval_test_ denial.
- no raw/context/memory/export/execution authority.
- the single allowed backend route:
  `POST /files/review/approvals/capture`.
- Control Center review-only approval capture controls.
- M38 planned/provisional currentness.

The gate must fail if M37 introduces raw file reads, raw file output/storage,
full-file reads, unredacted preview, context proposal, context injection, memory
writes, export/download, execution/tool controls, dependencies, M38 work, or
production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
