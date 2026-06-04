# Tool Runtime Invocation Contract

Status: active M32 documentation.
Current active baseline: **v0.37.1**

M32 defines typed invocation contracts for two allowlisted safe runtime paths:

- `tool:no_op.v1`
- `tool:filesystem_metadata.v1`

Runtime invocation requests must provide structured refs, a replay key, a safe
summary, and an exact allowlisted tool identity. Unknown tools, mismatched tool
names, effectful refs, raw prompt/model/file/transcript flags, secret-like
metadata, approval refs, approval_test_ refs, and authority refs are denied at
the evaluator boundary.

For filesystem metadata requests, the evaluator revalidates the current object
and metadata payload before a result can be returned. Constructor validation
alone is not trusted. Model_copy-mutated fields cannot enable raw content,
text preview, content hash, directory listing, recursive traversal, symlink
following, caller-selected root paths, or mutation.

No backend execute route is added in M32.

M33 adds `tool:filesystem.redacted_preview.v1` as bounded redacted preview
only. It remains safe-root-bound, redaction-before-return, no raw content
return/storage, no full-file output, no content hash, no directory listing, no
mutation, and no context injection. M34-M40 remain planned/provisional.
