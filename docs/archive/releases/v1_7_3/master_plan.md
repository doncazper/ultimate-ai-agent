# v1.7.3 Master Plan

## Scope

- Harden local/dev file-manager hashing to avoid full in-memory file reads.
- Bound read-preview file reads while keeping redaction lookahead.
- Keep preview text capped to the requested byte budget.
- Reuse atomic replacement for apply-write and rollback paths.
- Clean temporary write files when atomic replacement fails.
- Add focused regression tests for preview metadata and replacement failure.
- Update active baseline metadata and release/archive packets.

## Non-Goals

- No new milestone or M151 work.
- No release publication, release tag, artifact build, artifact upload,
  artifact export, external distribution, beta release, or production
  authority.
- No backend routes.
- No Control Center controls.
- No dependencies.
- No shell/subprocess execution, network access, model/provider call, runtime
  tool/browser/plugin/mobile/remote authority, memory write, context injection,
  broad autonomy, or mobile sensor runtime.
