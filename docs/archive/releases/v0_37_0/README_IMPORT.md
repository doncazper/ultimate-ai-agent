# README Import v0.37.0

Status: historical release packet.
Release baseline: **v0.37.0**

v0.37.0 implements M33 First Safe Local File Read Proposal, Redacted Preview
Only.

This release adds exactly one governed runtime expansion:

- `tool:filesystem.redacted_preview.v1`

The tool is safe-root-bound, relative-path-only, bounded, redacted-preview-only,
and non-authoritative. It returns no raw file content, stores no raw content,
exposes no raw absolute path, computes no content hash, lists no directories,
follows no symlinks, mutates no files, performs no context injection, and adds
no backend raw-file/execute routes, Control Center raw-preview/execute controls,
dependencies, or production authority.

OpenAPI path count remains `74`. M34-M40 remain planned/provisional.
