# Filesystem Metadata Non-Goals

Status: active M32 documentation.
Current active baseline: **v0.37.0**

M32 intentionally does not implement:

- arbitrary tool execution.
- general file tools.
- raw file reads.
- text previews.
- content hashing.
- directory listing.
- recursive traversal.
- symlink following.
- caller-selected arbitrary roots.
- file writes, deletes, moves, copies, chmod, chown, or rename operations.
- shell/subprocess execution.
- memory writes or Event Ledger mutation.
- network calls or web search.
- model/provider calls or local LLM calls.
- browser, mobile, remote, or plugin actions.
- backend file/tool execution routes.
- Control Center execute controls.
- dependencies.
- production authority.

M33 is implemented/released as bounded redacted file preview proposal only.
Raw file output, full-file reads, content hashes, directory listing, mutation,
backend raw-file/execute routes, Control Center raw-preview/execute controls,
and production authority remain non-goals. M34-M40 remain planned/provisional.
