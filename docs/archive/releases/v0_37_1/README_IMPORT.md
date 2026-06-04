# README Import v0.37.1

Status: active release packet.
Current active baseline: **v0.37.1**

v0.37.1 hardens M33 First Safe Local File Read Proposal, Redacted Preview Only.

This patch keeps the governed runtime expansion limited to:

- `tool:filesystem.redacted_preview.v1`

The patch strengthens redaction-before-return and path safety by rejecting
secret-like preview text at the output contract boundary and denying symlink
safe roots before any preview attempt. It also adds regression tests, static
verification, Foundation Gate coverage, and active documentation for those
hardening guarantees.

The tool remains safe-root-bound, relative-path-only, bounded,
redacted-preview-only, and non-authoritative. It returns no raw file content,
stores no raw content, exposes no raw absolute path, computes no content hash,
lists no directories, follows no symlinks, mutates no files, performs no
context injection, and adds no backend raw-file/execute routes, Control Center
raw-preview/execute controls, dependencies, or production authority.

OpenAPI path count remains `74`. M34-M40 remain planned/provisional.
