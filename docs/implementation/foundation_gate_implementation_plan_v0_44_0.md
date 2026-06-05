# Foundation Gate Implementation Plan v0.44.0

Status: current Foundation Gate implementation plan.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

The v0.44.0 Foundation Gate adds M40 checks for:

- Context Handoff Approval contract package existence.
- safe review-only handoff approval decision behavior.
- exact proposal binding enforcement.
- approval_ref alone denial.
- approval_test_ denial.
- model_copy-mutated context injection and OpenWebUI handoff denial.
- no context injection, OpenWebUI handoff, model call, memory write, export, or
  execution authorization.
- no context injection, OpenWebUI handoff, model call, memory write, export, or
  execution performed flags.
- safe-ref-only receipt plans with no raw content storage.
- no backend context proposal, context handoff, context injection, OpenWebUI
  handoff, memory write, raw-file, or execution routes.
- no dependency additions.
- M41 planned/provisional currentness.

The gate must fail if M40 introduces automatic context injection, OpenWebUI
handoff execution, OpenWebUI runtime integration, model/provider calls, memory
writes, raw file reads, raw content display/storage, full-file display,
unredacted preview display, raw absolute paths, export/download, execution,
backend routes, dependencies, M41 work, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before it can be trusted by a runtime boundary.
