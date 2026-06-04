# Master Plan v0.36.0

Status: historical release packet for the current active baseline.

Current active baseline: **v0.36.0**

v0.36.0 implements M32 so the Python Agent Core can perform one safe local
filesystem metadata lookup through the governed runtime adapter without
granting file content, mutation, shell, network, model, browser, mobile,
remote, plugin, or production authority.

Scope:

- add `tool:filesystem_metadata.v1`.
- keep `tool:no_op.v1`.
- update runtime allowlist, policy, result, and receipt contracts.
- enforce server-owned safe-root refs.
- deny unsafe paths, symlinks, content reads, previews, hashes, listings,
  recursion, caller roots, and mutation.
- deny authority-ref bypasses.
- add tests, static verification, Foundation Gate coverage, and docs.

Non-goals:

- arbitrary tool execution.
- raw file content reads.
- file previews or hashes.
- directory listing or traversal.
- file mutation.
- shell/subprocess execution.
- memory writes.
- network/model/provider calls.
- backend execution routes.
- Control Center execute controls.
- dependencies.
- M33 work.
- production authority.

M33-M40 remain planned/provisional.
