# Foundation Gate Implementation Plan v0.42.0

Status: current Foundation Gate implementation plan.
Release: **v0.42.0 / M38 - Safe Context Proposal From Approved Review**.

The v0.42.0 Foundation Gate adds M38 checks for:

- safe context proposal contracts.
- exact approved-review binding.
- redaction verification.
- proposal-only, non-authoritative decisions.
- denial of `approval_ref` alone.
- denial of `approval_test_` refs.
- denial of model_copy-mutated raw, full-file, unredacted, context injection,
  OpenWebUI handoff, model call, memory write, export, execution, and mismatched
  file/path refs.
- receipt plans that store safe refs only.
- no backend context injection, OpenWebUI handoff, memory write, raw-file, or
  execution routes.
- no Control Center context proposal surface.
- M39 planned/provisional currentness.

The gate must fail if M38 introduces context injection, OpenWebUI handoff,
model/provider calls, memory writes, raw file reads, raw output/storage,
full-file reads, unredacted preview, export/download, execution, dependencies,
M39 work, M40 handoff work, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
