# M33 to M34 Boundary

Status: active M33 documentation.
Current active baseline: **v0.37.1**

v0.37.1 / M33 hardens the implemented/released First Safe Local File Read
Proposal, Redacted Preview Only.

M33 adds exactly one file-content-adjacent runtime tool:

- `tool:filesystem.redacted_preview.v1`

The tool is bounded, safe-root-bound, relative-path-only, redacted-preview-only,
and non-authoritative. It returns no raw file content, stores no raw file
content, exposes no raw absolute path, computes no content hash, lists no
directories, follows no symlinks, performs no mutation, and creates no context
injection.

v0.37.1 specifically denies symlink safe roots before preview and rejects
secret-like preview text at the output contract boundary. Evaluator boundaries
revalidate safety-critical fields; constructor validation alone is not
authority.

M34 remains planned/provisional. Any broader file read, file review, file write,
directory traversal, raw preview, context injection, backend route, Control
Center raw-preview control, or production authority requires a separate
reviewed milestone.
