# Phase 06: Extreme Diagnostics And Feedback Inbox

Implement maximum-detail structured local diagnostics and the global Developer
Feedback workspace.

Deliver the correlated diagnostic journal described by the implementation plan
across:

- native shell/window/capture lifecycle;
- React route, interaction, render, error-boundary, layout-shift, long-task,
  and client-request events;
- API operation ID, status class, latency, retry, auth, idempotency, and
  correlation refs;
- Python service/storage/state-transition/policy/receipt events;
- relevant runtime/Matrix/connector state refs without raw content;
- shutdown flush, Codex queue/run, Git patch, and verification result events.

Requirements:

1. Developer Mode starts `extreme_structured` diagnostics by default.
2. Use a bounded ring buffer plus durable ignored session segments with atomic
   rotation and final flush.
3. Correlate events to app run, feedback session, route, capture, annotation,
   finding, request, receipt, and handoff refs.
4. Reject raw prompt/response/provider/message content, credentials, tokens,
   recovery material, environment dumps, keystrokes, full raw console logs,
   and user-specific absolute paths.
5. Support diagnostic windows around screenshots and video timestamp notes.
6. Provide CLI inspection with bounded human-readable summaries and optional
   schema-valid structured output.
7. Build a global Feedback Inbox with session, surface, media, origin,
   severity, category, status, patch, test, and PR filters.
8. Keep `operator_annotation` wording immutable and render later
   `codex_observation` analysis separately.
9. Show open, patching, patched, verified, partially patched, deferred,
   duplicate, blocked, wont-fix, and failed states distinctly.
10. Bind safe Evidence and Action Inbox proposal refs without making Evidence
    carry raw media or raw logs.

Verification:

- high-volume ordering/rotation/backpressure/drop-accounting tests;
- forbidden-field and secret-pattern tests;
- correlation, restart, crash, and shutdown-flush tests;
- React performance observer and error-boundary tests;
- Feedback Inbox component, filtering, keyboard, and visual tests;
- diagnostic-only finding creation and false-success prevention tests.

Exit gate: one feedback session produces a bounded, correlated, inspectable
diagnostic bundle and a readable global issue queue without raw-log dumping or
UI-owned truth.
