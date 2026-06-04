# Foundation Gate Implementation Plan v0.36.1

Status: active implementation plan.

Current active baseline: **v0.36.1**

v0.36.1 hardens Foundation Gate coverage for M32 Safe Tool Runtime Expansion,
Filesystem Metadata Path Safety.

Gate coverage requires:

- filesystem metadata runtime module exists.
- M32 filesystem metadata docs exist.
- manifest allowlists exactly `tool:no_op.v1` and
  `tool:filesystem_metadata.v1`.
- arbitrary/effectful tools remain disabled.
- file content read, text preview, content hash, directory listing, recursive
  traversal, symlink following, caller-selected roots, file write, and file
  delete flags remain disabled.
- safe metadata request under a server-owned safe root succeeds.
- result is metadata-only and leaks no raw file content or absolute local path.
- absolute, traversal, encoded traversal, home-directory, Windows drive,
  doubled-separator, hidden, private-key-like, secret-like, and glob paths are
  denied.
- caller-selected roots are denied.
- symlink paths are denied.
- model_copy-mutated raw file flags, path/root fields, tool_ref, and metadata
  alias flags are denied.
- authority refs cannot authorize metadata access or execution.
- no backend execution route or raw-file route is added.
- OpenAPI path count remains `74`.
- M33-M40 remain planned/provisional.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.

This plan adds no arbitrary tool execution, raw file content read, file
mutation, backend route, dependency, M33 work, or production authority.
