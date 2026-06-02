# Event Timeline UI

Status: Active for v0.21.0; M16 Event Timeline remains read-only.

The Event Timeline UI is a CCC Web read-only page at `/events/timeline`. It displays redacted timeline summaries for events, runs, receipts, and Foundation Gate evidence refs.

M16 scope:

- show event ref, event type, source, actor summary, timestamp, status, redaction status, safe message, related receipt refs, related evidence refs, run ref, and correlation ref.
- show selected trace details as summary-only metadata.
- show event relation refs and parent/child refs as safe refs.
- show Foundation Gate evidence summaries as safe refs and status summaries.
- use frontend mock data that is visibly mock, preview-only, and non-authoritative.
- selecting `View trace` changes visible selection only and does not mutate event, receipt, or evidence data.

Safety boundary:

- read-only only.
- summary-only only.
- safe refs only.
- no execution controls.
- no approval grant, denial, or bypass control.
- no tool execution.
- no model/provider call.
- no remote dispatch.
- no mobile sensor access.
- no plugin enablement.
- no external telemetry export.
- No backend route is added.

The UI must show no raw prompts, no raw secrets, no raw file contents, no raw memory contents, no raw credentials, no raw provider payloads, and no raw event payload dumps.

M16 does not change the Python API boundary. OpenAPI path count remains `74`; only version metadata changes to `0.20.1`.

Review build hygiene:

- prefer temporary Vite output paths for release review builds, such as `npm run build -- --outDir /tmp/uaa-control-center-review-dist`.
- generated frontend build, dist, coverage, log, and dependency artifacts must remain ignored and untracked.
- v0.20.1 adds no M17 Evidence/File/Memory Viewer.
