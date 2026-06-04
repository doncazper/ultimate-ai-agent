# Redacted File Preview Tool

Status: active M33 documentation.
Current active baseline: **v0.38.2**

M33 implements the first safe local file read proposal as one governed tool
runtime adapter entry:

- `tool:filesystem.redacted_preview.v1`

The tool produces a bounded redacted preview proposal for one explicitly scoped
text file under a server-owned safe root. It is redacted preview only. It is not
a full-file reader, not raw file output, not context injection, and not
production authority.

Allowed behavior:

- server-owned or explicit test fixture safe roots only.
- relative paths only.
- M32 path policy reuse for traversal, hidden path, secret-like path, glob,
  home-directory, Windows-drive, and doubled-separator denial.
- file type, file size, and UTF-8 text checks before preview result creation.
- bounded preview bytes only.
- redaction before result creation.
- redacted preview and redaction summary only.
- result-boundary validation that rejects unredacted secret-like preview
  content even if an output object is constructed directly.
- safe-root validation that denies a symlink safe root before any preview
  attempt.
- non-authoritative receipt plan with no raw content storage.

Denied behavior:

- raw file content returned or stored.
- full-file read output.
- content hash.
- directory listing or recursive traversal.
- glob, rglob, or os.walk behavior.
- symlink following.
- caller-selected arbitrary roots.
- file writes, deletes, chmod, chown, rename, copy, move, or mutation.
- shell, subprocess, memory write, network call, model/provider call, browser,
  mobile, remote, plugin, scheduler, background worker, or daemon behavior.
- backend raw-file or execute routes.
- Control Center raw-preview or execute controls.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. M35 remains planned/provisional for Safe File
Review Workflow Contracts.
