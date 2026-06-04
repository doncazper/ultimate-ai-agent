# Local File Redacted Preview Policy

Status: active M33 documentation.
Current active baseline: **v0.38.1**

M33 local file preview is a governed proposal path, not arbitrary local file
access. It may inspect one safe relative text path under a server-owned safe
root only long enough to produce a bounded redacted preview.

The policy denies absolute paths, traversal, hidden paths, secret-like path
segments, symlinks, directories, binary files, unsupported encodings, oversized
files, caller-selected roots, directory listing, recursive traversal, full-file
read output, raw content return, raw content storage, content hashing, file
mutation, backend raw-file routes, Control Center raw-preview controls, and
context injection.

v0.37.1 also denies a safe-root path that is itself a symlink before any preview
attempt. The redacted preview output contract rejects secret-like preview text
so raw secrets cannot be carried by direct result construction or a
model_copy-mutated output.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. M35 remains planned/provisional for Safe File
Review Workflow Contracts.
