# Master Plan v0.37.0

Status: historical release packet.
Release baseline: **v0.37.0**

v0.37.0 implements M33 so the Python Agent Core can produce one bounded
redacted file preview proposal under server-owned safe roots without returning
or storing raw file content.

## Scope

- Add `tool:filesystem.redacted_preview.v1`.
- Reuse M32 safe root and relative path policy.
- Add file size, file type, and UTF-8 encoding checks.
- Add deterministic redaction before result creation.
- Add redacted preview result and redaction summary contracts.
- Add no-raw-content receipt planning.
- Add tests, static verification, documentation, and Foundation Gate coverage.

## Non-Goals

- raw file output.
- full-file read output.
- content hash.
- directory listing or recursive traversal.
- symlink following.
- caller-selected arbitrary roots.
- hidden or secret-like path reads.
- file writes, deletes, or mutation.
- shell/subprocess execution.
- memory writes.
- network/model/browser/mobile/remote/plugin tools.
- context injection.
- backend raw-file or execute routes.
- Control Center raw-preview or execute controls.
- dependencies, M34 work, or production authority.

M34-M40 remain planned/provisional.
