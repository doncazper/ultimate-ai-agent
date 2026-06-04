# Master Plan v0.37.1

Status: active release packet.
Current active baseline: **v0.37.1**

v0.37.1 hardens M33 so the Python Agent Core can produce bounded redacted file
preview proposals without allowing result-boundary secret leakage or symlink
safe-root bypasses.

## Scope

- Deny symlink safe roots before preview.
- Reject secret-like preview text at the `RedactedFilePreviewOutput` boundary.
- Preserve redaction-before-return guarantees.
- Preserve no-raw-content result and receipt boundaries.
- Strengthen static verifier and Foundation Gate probes.
- Add focused regression tests and active documentation updates.

## Non-Goals

- raw file output.
- full-file read output.
- unredacted preview.
- content hash.
- directory listing or recursive traversal.
- symlink following or symlink safe roots.
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
