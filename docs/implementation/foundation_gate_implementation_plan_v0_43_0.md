# Foundation Gate Implementation Plan v0.43.0

Status: current Foundation Gate implementation plan.
Release: **v0.43.0 / M39 - CCC Context Proposal Surface**.

The v0.43.0 Foundation Gate adds M39 checks for:

- CCC context proposal surface existence.
- `/context/proposals` frontend route presence.
- mock and non-authoritative context proposal data.
- exact safe binding refs display.
- redacted proposal sections and redaction verification display.
- proposal-only decision and receipt-plan metadata display.
- no approve, deny, submit, save, mark-reviewed, handoff, inject, export,
  download, copy-raw, memory write, execute, run, tool, model-call, file picker,
  browser, upload, or root selector controls.
- no backend context handoff, context injection, OpenWebUI handoff, memory
  write, raw-file, or execution routes.
- no dependency additions.
- M40 planned/provisional currentness.

The gate must fail if M39 introduces context handoff approval, context
injection, OpenWebUI handoff, OpenWebUI runtime integration, model/provider
calls, memory writes, raw file reads, raw content display/storage, full-file
display, unredacted preview display, raw absolute paths, export/download,
execution, backend routes, dependencies, M40 work, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before it can be trusted by a runtime boundary.
