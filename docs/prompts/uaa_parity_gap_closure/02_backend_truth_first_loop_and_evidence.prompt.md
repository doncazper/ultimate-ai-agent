# Phase 02: Backend Truth, First Founder Loop, And Evidence

Coverage: O02, B05, B14, L01, L03, and L04.

Objective: make the first founder/operator loop readable and entirely backed by
current Python-owned state. Critical surfaces must never look successful or
verified because frontend fixtures filled a missing backend response.

## Fresh Delta Gate

Re-run Phase 01 inventory after syncing `main`. Inspect all overlapping Founder
Command Center, north-star UI, Action Inbox, product-truth, and verification PRs.
Reuse only behavior now merged and proven. Do not overwrite active UI work owned
by another task.

## Required Outcomes

1. Define the critical truth set: Start Here, Today, Plans, Action Inbox,
   Approvals, Work Board, Morning Briefing, Memory, Evidence/Proof, Setup, Chat
   handoff, and active-run status.
2. Remove production success-path dependence on `mockControlCenterData`, static
   samples, placeholder receipts, and deterministic preview records for this
   set. Test-only fixtures remain allowed in tests.
3. When backend data is unavailable, malformed, stale, or contract-incompatible,
   show a truthful bounded unavailable/degraded state with last verified time,
   source ref, backend revision, retry action, and authority posture.
4. Never merge fallback fields into a response in a way that makes the combined
   record appear backend-owned. Preserve explicit per-section provenance if a
   non-critical decorative fallback remains.
5. Complete one readable path from Today or Chat through Plan, Action Inbox,
   exact local decision, Work Board state, receipt, Evidence, and optional
   reviewed Memory candidate.
6. Bind every completion and proof label to verified backend evidence. Stale,
   invalid, missing, mock, or unverified evidence must be visibly non-complete.
7. Add API/CLI inspection for any critical state that currently exists only in
   the Control Center.
8. Update capability, route-status, release-surface, product-truth, and operator
   language only to the level proven by runtime tests.

## End-To-End Acceptance

- Run the app against a real local Python backend and durable temporary or
  operator test state; do not intercept critical API calls with frontend mocks.
- Complete the founder loop through the browser or equivalent rendered app and
  prove the resulting state using CLI and API reads.
- Stop the backend during the walkthrough and prove that every critical panel
  becomes unavailable/stale rather than showing plausible sample data.
- Corrupt or age one evidence record and prove that verified/completed language
  disappears without mutating authority.
- Reload the Control Center and prove durable state survives while presentation
  preferences remain non-authoritative.

## Required Tests And Hardening

- backend-loss, malformed-response, partial-response, stale-revision, and
  out-of-order refresh tests;
- proof-source, hash/time, and optimistic-completion regression tests;
- frontend accessibility and visual checks for unavailable/stale states;
- API manifest/OpenAPI/route classification and CLI parity checks; and
- redaction tests for every new error or provenance field.

No critical route may be marked `ship` until this phase's real-backend browser,
API, CLI, and evidence proof passes.

Commit message:

```text
feat(control-center): enforce backend truth across the founder loop
```
