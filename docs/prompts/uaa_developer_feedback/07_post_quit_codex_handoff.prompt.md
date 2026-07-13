# Phase 07: Post-Quit Codex Handoff

Implement the exact launcher-side handoff from a finalized feedback bundle to
the installed Codex CLI.

Before implementation:

- verify `codex exec --help` and the installed version;
- read the official Codex developer-command documentation;
- inspect current launcher, AuthorityLease, LocalApprovalAuthority,
  idempotency, command allowlist, subprocess, receipt, and safe-disable lanes;
- preserve the rule that the UAA app process must exit before Codex edits the
  repository.

Deliver:

1. Handoff eligibility evaluator with exact reasons for eligible, empty,
   incomplete, stale, corrupt, already-running, already-complete, safe-disabled,
   unauthenticated, non-Git, or dirty-worktree-blocked/degraded state.
2. Atomic shutdown finalization and a launcher-observed process-exit proof.
3. Exact argv builder allowing only:
   - `codex exec`;
   - `--cd` for the bound repository;
   - `--sandbox workspace-write`;
   - `--json`;
   - `--output-schema`;
   - `--output-last-message`;
   - repeated `--image` for registered screenshots/keyframes;
   - `-` for prompt stdin.
4. Explicit denials for dangerous bypass flags, danger-full-access,
   ignored rules/config, skip-repo-check, arbitrary config overrides, arbitrary
   models/providers, shell strings, pipelines, and environment injection.
5. Generated bounded prompt containing session/finding/annotation/timestamp/
   diagnostic refs, operator notes, repository instructions, required branch,
   test expectations, and final result schema.
6. Image/keyframe resolver with regular-file/root/hash/size/count checks.
7. Concurrency lock, idempotency key, timeout, cancellation, retry, safe-disable,
   stdout/stderr bounding, JSONL event parsing, and receipt storage.
8. Clear behavior for missing authentication, missing CLI, unsupported flags,
   model failure, tool denial, timeout, nonzero exit, malformed output, and
   partial patch.

Do not implement dangerous unattended authority. The current operator request
authorizes this exact local post-quit feedback lane only. It does not authorize
direct-main push, force-push, tag mutation, auto-merge, unrelated repository
work, network expansion, or arbitrary command execution.

Verification:

- exact argv allow/deny tests;
- fake Codex process protocol tests;
- process-exit ordering proof;
- duplicate shutdown/concurrency/idempotency tests;
- image/path/hash/size/count adversarial tests;
- timeout/cancel/retry/safe-disable tests;
- local smoke using a read-only/no-change synthetic bundle before enabling a
  workspace-write patch acceptance case.

Exit gate: quitting UAA with an eligible bundle starts exactly one bounded
Codex run after process exit, while empty or invalid sessions start none and
every failure remains inspectable/retryable.
