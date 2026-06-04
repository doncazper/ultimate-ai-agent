# Filesystem Metadata Tool

Status: active M32 documentation.
Current active baseline: **v0.37.1**

M32 implements one safe local filesystem metadata tool:

```text
tool:filesystem_metadata.v1
```

The tool runs only through the governed Tool Runtime Adapter. It accepts a
server-owned safe-root ref plus a normalized relative path and returns metadata
only:

- safe path ref.
- root ref.
- existence.
- file/directory/other/missing kind.
- byte size for regular files.
- extension for regular files.
- modified-time metadata.

The tool does not read raw file content, return text previews, compute content
hashes, list directory children, recurse, follow symlinks, or mutate the
filesystem. v0.36.1 hardens path safety so encoded traversal, home-directory
paths, Windows drive paths, doubled separators, hidden paths,
private-key-like paths, caller-selected roots, and metadata alias flags are
denied at the evaluator boundary.

Allowed runtime tools in M32:

- `tool:no_op.v1`
- `tool:filesystem_metadata.v1`

All other runtime tools remain denied.

M33 is implemented/released as First Safe Local File Read Proposal, Redacted
Preview Only. The filesystem metadata tool remains metadata-only and does not
return raw content, text previews, full-file output, content hashes, directory
listing, or mutation. M34-M40 remain planned/provisional.
