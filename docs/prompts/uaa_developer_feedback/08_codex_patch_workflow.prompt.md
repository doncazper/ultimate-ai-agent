# Phase 08: Codex Patch Workflow

Implement and prove the task that Codex receives from the post-quit handoff.

Approval refs alone authorize nothing. Repository mutation, patch application,
Git commit, branch push, and draft-PR creation are separate exact capabilities;
each must pass its own fresh request-scoped evaluation immediately before
start.

The generated Codex task must:

1. Read `AGENTS.md` and applicable nested instructions.
2. Inspect Git status, current branch, worktrees, and existing user changes.
3. Resolve and inspect every operator-annotated screenshot/keyframe plus its
   timestamp/route/diagnostic context.
4. Review the supplied evidence beyond the operator's annotations for other
   observable defects.
5. Add a `codex_observation` only when evidence, surface, confidence, and a
   bounded explanation are recorded. Never rewrite operator notes.
6. Cluster duplicates and order fixes by blocking, broken, confusing, polish,
   and performance severity.
7. Create or reuse exactly one bundle-specific
   `codex/developer-feedback-*` branch only after a separate exact repository-
   mutation capability is accepted and freshly authorized. If that lane is
   absent, produce a reviewable patch proposal and blocked report without
   changing Git. If user changes cannot be preserved safely, stop and record
   the blocker rather than stashing or discarding them.
8. Apply evidence-supported fixes only under the exact patch-application lane.
   Do not perform unrelated refactors.
9. Add regression tests and visual coverage where practical.
10. Run focused checks after each fix and the broadest practical final checks.
11. Write schema-valid findings/fixes/tests/blockers/result output.
12. Treat Git commit, branch push, and draft-PR creation as three separate exact
    capabilities. Re-evaluate policy, approval, AuthorityLease, target,
    deadline, budget, readiness, kill switch, safe-disable, and idempotency
    immediately before each; otherwise leave the verified patch local and
    report the blocked operation. Never push `main`, force-push, mutate tags, or
    auto-merge.

Implement the result ingestion path:

- validate output schema and bundle binding;
- reconcile operator and Codex findings without overwriting source records;
- attach patch/commit/test/receipt/PR refs;
- distinguish patched, partially patched, verified, blocked, failed, deferred,
  duplicate, and wont-fix;
- expose next-launch summary through Python Core/API/CLI/UI;
- prevent a Codex narrative from overriding Git/test/backend truth.

Acceptance scenarios:

- operator-marked visual defect fixed and verified;
- additional Codex-observed defect found in the same screenshot and fixed;
- video timestamp defect fixed from keyframe and diagnostics;
- operator note is subjective and Codex proposes no unsafe change;
- dirty worktree preserved;
- one fix passes while another is blocked;
- tests fail and result remains `partially_patched` or `failed`;
- retry resumes idempotently without duplicate commits or findings.

Exit gate: when the exact repository-mutation and patch-application lanes are
separately accepted and freshly authorized, a real synthetic feedback bundle
results in a dedicated patch branch, evidence-backed operator/Codex finding
records, focused tests, and an accurate structured result consumable on next
launch. Without those lanes, a reviewed patch proposal, unchanged Git state,
and an explicit blocked result satisfy the proposal-only exit posture.
