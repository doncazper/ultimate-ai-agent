# Phase 01: Contract, Authority, And Schema

Implement the exact contract and authority foundation for
`UAA-DEV-FEEDBACK-001`. This phase is contract-first and adds no screenshot,
video, native capture, or Codex subprocess execution.

Read:

- `AGENTS.md`;
- `docs/implementation/UAA_DEVELOPER_FEEDBACK_IMPLEMENTATION_PLAN.md`;
- private trial, Evidence, Action Inbox, local launcher, route classification,
  idempotency, rate-limit, and product-language contracts;
- current screenshot-denial posture contracts so this new lane stays separate.

Deliver:

1. Versioned Python contracts and JSON schemas for settings, session, capture,
   annotation, finding, diagnostic event/journal, artifact registry, handoff,
   Codex result, and next-launch summary.
2. Explicit state machines with legal transitions and fail-closed invalid
   transition behavior.
3. A capability/authority entry for the exact local developer-feedback lane.
4. Default settings proving Developer Mode and extreme structured diagnostics
   are enabled, capture is manual, and post-quit handoff is enabled only for a
   nonempty finalized bundle.
5. Safe-disable, rollback, idempotency, timeout, concurrency, retention, and
   cleanup contracts.
6. Exact allowed/forbidden `codex exec` argument policy. Validate against the
   installed `codex exec --help` and official developer-command documentation.
7. Route/API/CLI proposal map and side-effect classifications without adding
   runtime routes yet.
8. Updated roadmap/board/product-truth language that promotes only this exact
   local developer capability and keeps broader authority blocked.

Required invariants:

- Screenshot/video media remains ignored local state.
- Operator notes are immutable source findings; later Codex analysis is stored
  separately.
- A `codex_observation` requires observable evidence and confidence.
- Extreme diagnostics are structured and bounded, not raw payload logging or
  keystroke recording.
- Existing generic screenshot, browser automation, CUA, and preview-rail
  authority flags remain unchanged.
- No dangerous Codex flags, shell command strings, direct-main push,
  force-push, tag mutation, or auto-merge.

Tests must cover defaults, state transitions, forbidden flags, unsafe refs,
invalid geometry/timestamps, missing evidence for Codex observations,
idempotency conflicts, duplicate handoff, and schema drift.

Exit gate: reviewers can identify owner, side effects, exact authority,
failure behavior, rollback, safe-disable, evidence, and verification for every
later phase without any runtime capture or subprocess having been added.
