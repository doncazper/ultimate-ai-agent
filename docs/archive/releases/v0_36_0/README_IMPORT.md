# README Import v0.36.0

Status: historical release packet for the current active baseline.

Current active baseline: **v0.36.0**

v0.36.0 implements M32 Safe Tool Runtime Expansion as one safe local filesystem
metadata tool. It extends the governed Tool Runtime Adapter allowlist from the
deterministic no-op tool to exactly one additional tool,
`tool:filesystem_metadata.v1`.

The filesystem metadata tool is metadata-only. It returns safe refs, existence,
kind, file size, extension, and modified-time metadata under server-owned safe
roots. It does not read file contents, preview text, compute hashes, list
directories, recurse, follow symlinks, accept arbitrary caller-selected roots,
or mutate the filesystem.

OpenAPI path count remains `74`. M33-M40 remain planned/provisional.
