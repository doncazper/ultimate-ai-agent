# Foundation Gate Implementation Plan v0.37.0

Status: active Foundation Gate plan.
Current active baseline: **v0.37.0**

v0.37.0 adds Foundation Gate coverage for M33 First Safe Local File Read
Proposal, Redacted Preview Only.

Gate coverage includes:

- redacted preview runtime module exists.
- M33 redacted preview docs exist.
- tool runtime allowlist is exactly no-op, filesystem metadata, and redacted
  file preview.
- default policy disables raw content, full-file reads, content hashes,
  directory listing, recursive traversal, symlink following, caller-selected
  roots, file mutation, context injection, and production authority.
- safe text fixture preview succeeds and redacts secret-like values.
- result returns redacted preview and redaction summary only.
- result returns no raw content, stores no raw content, leaks no raw absolute
  path, and records no side effects.
- binary, unsupported encoding, oversized, directory, symlink, traversal,
  hidden, and secret-like paths are denied.
- model_copy-mutated raw-read flags and raw-read tool refs are denied.
- approval refs, `approval_test_*`, model/memory/context/tool-intent/task-plan
  refs, and arbitrary strings cannot authorize filesystem preview access.
- OpenAPI path count remains `74` and no raw-file/execute routes are added.
- M34 remains planned/provisional.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.

M33 adds no file mutation, memory write, network call, model/provider call,
browser/mobile/remote/plugin execution, backend raw-file/execute route,
Control Center raw-preview/execute control, dependency, M34 work, or production
authority.
