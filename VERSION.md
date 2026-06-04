# Ultimate AI Agent Version

Current active baseline: **v0.36.1**

v0.36.1 hardens M32 Safe Tool Runtime Expansion and the safe local filesystem
metadata tool. It strengthens source path normalization, encoded traversal
denial, home/Windows/double-separator path denial, hidden/private-key-like path
denial, caller-selected root denial, metadata alias flag denial, model_copy
evaluator revalidation, static verification, documentation, and Foundation Gate
coverage.

It preserves `tool:filesystem_metadata.v1` as metadata-only and bound to
server-owned safe roots. It adds no raw file reads, text previews, content
hashing, directory listing, recursive traversal, symlink following, file
mutation, arbitrary tool execution, shell/subprocess execution, memory writes,
network calls, model/provider calls, backend execution or raw-file routes,
Control Center execute/raw-preview controls, dependencies, M33 work, or
production authority.
