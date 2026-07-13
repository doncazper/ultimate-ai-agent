# Phase 08: Codex Patch Workflow

Implement and prove the task that Codex receives from the post-quit handoff.

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
   `codex/developer-feedback-*` branch. If user changes cannot be preserved
   safely, stop and record the blocker rather than stashing or discarding them.
8. Implement evidence-supported fixes only. Do not perform unrelated refactors.
9. Add regression tests and visual coverage where practical.
10. Run focused checks after each fix and the broadest practical final checks.
11. Write schema-valid findings/fixes/tests/blockers/result output.
12. Commit and push normally only when authorized/configured and checks pass;
    optionally open a draft PR. Never push `main`, force-push, mutate tags, or
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

Exit gate: a real synthetic feedback bundle results in a dedicated patch
branch, evidence-backed operator/Codex finding records, focused tests, and an
accurate structured result consumable on next launch.
