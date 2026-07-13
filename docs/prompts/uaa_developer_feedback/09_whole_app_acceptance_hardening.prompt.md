# Phase 09: Whole-App Acceptance And Hardening

Run a full adversarial product acceptance pass over the integrated Developer
Feedback loop. Fix every reproducible in-scope defect and do not weaken tests or
authority boundaries to obtain green results.

Required product walkthroughs:

Run each walkthrough only when every exact capability it invokes has been
separately accepted and passes fresh request-scoped evaluation immediately
before start. Screenshot capture, video capture, artifact cleanup, Codex
launch, content disclosure, repository mutation, patch application, Git
commit, branch push, and draft-PR creation remain separate capabilities. An
unavailable lane produces an explicit blocked acceptance result with safe refs;
it neither authorizes execution nor turns the whole pack into a false failure.

1. Launch UAA and prove Developer Mode/extreme diagnostics are enabled by
   default.
2. Exercise the title bar on Today, Messenger, CRM, Calendar, Work Board,
   Knowledge, Activity & Trust, Settings, and shell chrome.
3. Capture full-window/content/region screenshots in light/dark and normal/
   compact widths.
4. Create multiple annotations and findings on one screenshot.
5. Record a multi-route video with description, timestamp notes, route markers,
   and keyframes.
6. Generate native, React, API, backend, capture, and shutdown diagnostics in
   one correlated session.
7. Quit with an empty session and prove no Codex run starts.
8. Quit with actionable findings and prove exactly one Codex run starts only
   after UAA exits.
9. Prove Codex reads operator notes and can add separate evidence-backed
   observations.
10. Prove scoped patching, tests, structured result, and next-launch display.
11. Exercise failed capture, partial video, corrupt artifact, disk bound,
    diagnostic overflow, missing Codex CLI/auth, timeout, cancellation, dirty
    worktree, failed tests, failed push, and retry.
12. Exercise safe-disable, cleanup, retention, and rollback.

Adversarial review:

- secret/credential/recovery material leakage;
- raw prompt/response/provider/message body persistence;
- local path leakage in durable evidence;
- path traversal, symlinks, stale hashes, oversized media, malformed geometry,
  malicious notes, and prompt injection in captured content;
- duplicate handoffs, races, zombie processes, edits while UAA is open, and
  incorrect success states;
- Codex scope drift, dangerous flags, direct-main push, force-push, tag
  mutation, auto-merge, or lost user work;
- UI-only durable truth, raw JSON primary UX, missing accessibility, and stale
  product language.

Final verification:

- all focused backend/frontend/native/handoff tests;
- documentation integrity and product truth;
- OpenAPI, API manifest, route inventory, auth, idempotency, and rate limits;
- security/redaction and static authority guards;
- frontend typecheck/lint/unit/build/visual tests;
- native Swift build/unit/integration tests;
- Foundation Gate report-only;
- `git diff --check`;
- real local end-to-end acceptance evidence using safe refs/hashes in durable
  reports.

Update the smallest active docs, indexes, roadmap, board, release truth,
security, runbook, and troubleshooting references. Product language must say
implemented only for behavior proven by the final acceptance run.

Final response must list files changed, defects found/fixed, operator findings,
Codex observations, tests/verifiers with pass/fail, skipped checks with reason,
remaining blockers, safe-disable/rollback posture, branch/commit/PR state, and
current Git status.

Exit gate: every separately accepted exact lane is proven usable for daily
solo-developer UAA dogfooding, while unavailable lanes are truthfully reported
as blocked. The integrated mechanism accurately reports every success, partial
result, failure, and blocker without claiming unproven runtime behavior.
