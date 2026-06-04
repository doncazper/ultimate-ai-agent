# Redacted File Preview Non-Goals

Status: active M33 documentation.
Current active baseline: **v0.38.1**

M33 intentionally does not implement:

- raw file content output.
- raw file content storage.
- full-file read output.
- unredacted file preview.
- content hash.
- directory listing.
- recursive traversal.
- glob, rglob, or os.walk behavior.
- symlink following.
- symlink safe roots.
- hidden file reads.
- secret-like path reads.
- caller-selected arbitrary roots.
- file writes, deletes, chmod, chown, rename, copy, move, or mutation.
- arbitrary filesystem tools.
- shell/subprocess execution.
- memory writes.
- network calls or web search.
- model/provider/local LLM calls.
- browser automation or Computer Use.
- plugin enablement.
- retrieval, RAG, vector, or embedding functionality.
- context injection runtime.
- autonomous loops, schedulers, background workers, or daemons.
- backend raw-file/execute routes.
- Control Center raw-preview/execute controls.
- mobile/device sensor access.
- remote execution.
- dependencies or production authority.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. M35 remains planned/provisional for Safe File
Review Workflow Contracts.
