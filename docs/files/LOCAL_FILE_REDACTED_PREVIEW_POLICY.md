# Local File Redacted Preview Policy

Status: active M33 documentation.
Current active baseline: **v0.37.0**

M33 local file preview is a governed proposal path, not arbitrary local file
access. It may inspect one safe relative text path under a server-owned safe
root only long enough to produce a bounded redacted preview.

The policy denies absolute paths, traversal, hidden paths, secret-like path
segments, symlinks, directories, binary files, unsupported encodings, oversized
files, caller-selected roots, directory listing, recursive traversal, full-file
read output, raw content return, raw content storage, content hashing, file
mutation, backend raw-file routes, Control Center raw-preview controls, and
context injection.

M34 remains planned/provisional.

