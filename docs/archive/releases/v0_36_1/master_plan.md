# Master Plan v0.36.1

Status: historical release packet for the current active baseline.

Current active baseline: **v0.36.1**

v0.36.1 hardens M32 so safe local filesystem metadata lookup remains
safe-root-bound, metadata-only, deterministic, and non-authoritative.

Scope:

- strengthen relative path normalization.
- deny encoded traversal, home-directory paths, Windows drive paths, doubled
  separators, hidden paths, and private-key-like paths.
- deny caller-selected roots and metadata alias flags at the evaluator
  boundary.
- revalidate model_copy-mutated path, root, tool_ref, and metadata fields.
- add regression tests, static verifier probes, Foundation Gate coverage, and
  docs for the hardening cases.

Non-goals:

- arbitrary tool execution.
- raw file content reads.
- file previews or hashes.
- directory listing or traversal.
- symlink following.
- file mutation.
- shell/subprocess execution.
- memory writes.
- network/model/provider calls.
- backend execution or raw-file routes.
- Control Center execute or raw-preview controls.
- dependencies.
- M33 work.
- production authority.

M33-M40 remain planned/provisional.
