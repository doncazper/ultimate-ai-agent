# Tool Runtime Non-Goals

Status: active M32 documentation.
Current active baseline: **v0.37.1**

M32 intentionally does not implement:

- arbitrary tool execution.
- side-effecting tools.
- dynamic dispatch.
- plugins.
- shell/subprocess execution.
- raw file content reads.
- text previews.
- content hashing.
- directory listing.
- recursive traversal.
- symlink following.
- caller-selected arbitrary roots.
- file writes, deletes, moves, copies, chmod, chown, or rename operations.
- memory writes.
- network calls or web search.
- model/provider calls or local LLM calls.
- browser automation or Computer Use.
- mobile/device access.
- remote execution.
- schedulers, background workers, daemons, or autonomous loops.
- context injection runtime.
- backend public execute routes.
- Control Center execute controls.
- dependencies.
- production authority.

M32 proves only that a governed adapter can complete deterministic no-op and
one metadata-only filesystem lookup safely.

M33 adds only bounded redacted file preview proposals. Raw file output,
full-file reads, content hashes, directory listing, symlink following, file
mutation, context injection, arbitrary filesystem tools, backend raw-file or
execute routes, and Control Center raw-preview/execute controls remain
non-goals. M34-M40 remain planned/provisional.
