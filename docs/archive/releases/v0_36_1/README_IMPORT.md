# README Import v0.36.1

Status: historical release packet for the current active baseline.

Current active baseline: **v0.36.1**

v0.36.1 hardens M32 Safe Tool Runtime Expansion and the
`tool:filesystem_metadata.v1` path-safety boundary.

The filesystem metadata tool remains metadata-only and bound to server-owned
safe roots. This hardening release denies encoded traversal, home-directory
paths, Windows drive paths, doubled separators, unsafe separators, hidden
paths, private-key-like paths, caller-selected roots, mismatched or
non-allowlisted tool refs, and metadata alias flags that attempt to enable raw
content, previews, hashes, listings, recursion, symlink following, or mutation.

OpenAPI path count remains `74`. M33-M40 remain planned/provisional.
