# M32 to M33 Boundary

Status: active M33 documentation.
Current active baseline: **v0.37.1**

M32 is implemented/released as Safe Local Filesystem Metadata Tool.

M32 adds exactly one runtime expansion beyond no-op:

```text
tool:filesystem_metadata.v1
```

That tool is metadata-only under server-owned safe roots. It does not add file
content reads, text previews, content hashes, directory listing, recursive
traversal, symlink following, file mutation, shell/subprocess execution, memory
writes, network calls, model/provider calls, backend execution routes, Control
Center execute controls, dependencies, or production authority.

M33 is implemented/released as First Safe Local File Read Proposal, Redacted
Preview Only. It adds one bounded runtime tool,
`tool:filesystem.redacted_preview.v1`, which may produce a redacted preview
proposal under server-owned safe roots after path, size, type, encoding, and
redaction checks.

M33 does not add raw file output, full-file read output, content hashes,
directory listing, recursive traversal, symlink following, file mutation,
backend raw-file/execute routes, Control Center raw-preview/execute controls,
context injection, dependencies, or production authority. v0.38.0 implements
M34 Broader File Capability Review as planning/docs/verifier only, and
M36-M60 remain planned/provisional.
