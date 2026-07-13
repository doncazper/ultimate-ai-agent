# Phase 02: Python Core, Storage, API, And CLI

Implement the backend-owned developer-feedback foundation. Do not implement
native screenshot/video capture or launch Codex in this phase.

Deliver:

1. `DeveloperFeedbackService` in Python Core with injectable clock, artifact
   root, Git context provider, and diagnostic limits.
2. Ignored local storage for settings, sessions, artifact registry, captures,
   annotations, findings, diagnostics, and handoff/result posture.
3. Atomic writes, fsync/finalization behavior, schema migration/version
   handling, crash recovery, idempotent replay, corruption quarantine, cleanup,
   and bounded retention.
4. Opaque artifact refs resolved transiently to a validated regular file under
   the configured session root. Reject symlinks, traversal, device files,
   oversized artifacts, stale hashes, and cross-session refs.
5. Protected local API routes for settings/status, session lifecycle, capture
   metadata, annotations, findings, validated diagnostic batches, Feedback
   Inbox reads, finalization, and handoff/result posture.
6. CLI parity under `uaa developer-feedback` for status, start, inspect,
   findings, finalize, handoff status/retry, artifact resolution, and cleanup.
7. OpenAPI operation IDs, `/api/manifest`, route inventory, side-effect class,
   authentication, idempotency, targeted rate limits, and redacted errors.
8. Read models suitable for the global title bar and Feedback Inbox.

Rules:

- React does not own or synthesize completed capture/finalization/handoff state.
- Storage remains local and ignored.
- Durable Evidence contains safe refs/hashes/summaries only.
- Diagnostic ingestion rejects forbidden fields and enforces batch, event,
  size, and time-window bounds.
- Empty finalized sessions are not eligible for Codex.

Verification:

- state-machine and repository tests using temporary roots;
- API authentication/idempotency/rate-limit/manifest/OpenAPI tests;
- CLI/core/API parity tests;
- artifact traversal/symlink/corruption/adversarial tests;
- restart/crash recovery and duplicate-finalization tests;
- documentation and product-language verification.

Exit gate: backend storage, API, and CLI can manage complete synthetic feedback
sessions and fail safely, while native capture and Codex execution remain
disabled.
