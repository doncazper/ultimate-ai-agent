# Execute UAA Developer Feedback End To End

Role: You are the principal engineer responsible for implementing, reviewing,
testing, and hardening the global UAA Developer Feedback and post-quit Codex
loop.

Execute these prompts in order:

1. `docs/prompts/uaa_developer_feedback/01_contract_authority_and_schema.prompt.md`
2. `docs/prompts/uaa_developer_feedback/02_core_storage_api_cli.prompt.md`
3. `docs/prompts/uaa_developer_feedback/03_native_shell_global_developer_mode.prompt.md`
4. `docs/prompts/uaa_developer_feedback/04_screenshot_annotation_workflow.prompt.md`
5. `docs/prompts/uaa_developer_feedback/05_video_timeline_keyframes.prompt.md`
6. `docs/prompts/uaa_developer_feedback/06_extreme_diagnostics_and_feedback_inbox.prompt.md`
7. `docs/prompts/uaa_developer_feedback/07_post_quit_codex_handoff.prompt.md`
8. `docs/prompts/uaa_developer_feedback/08_codex_patch_workflow.prompt.md`
9. `docs/prompts/uaa_developer_feedback/09_whole_app_acceptance_hardening.prompt.md`

Global rules:

- Read `AGENTS.md`, the implementation plan, this README, and every phase prompt
  completely before editing.
- Inspect the current branch, worktrees, open PRs, and dirty files. Preserve all
  user-owned changes and use a separate worktree if needed.
- Start from the latest integrated `origin/main` unless the operator explicitly
  names another base.
- Use one dedicated `codex/uaa-developer-feedback-XX-*` branch and one PR per
  phase, starting from the latest integrated `origin/main`.
- Keep Python Core as the owner of settings, sessions, findings, diagnostics,
  artifact refs, lifecycle, handoff eligibility, and results.
- Keep React and SwiftUI presentation from becoming durable authority.
- Developer Mode and extreme structured diagnostics default to enabled.
- Screenshot and video capture remain manual.
- Do not add background capture, keystroke logging, raw prompt/response/provider
  payload persistence, secret persistence, unrestricted shell execution,
  direct-main push, force-push, tag mutation, or automatic merge.
- The post-quit runner must use exact argv-only `codex exec`,
  `--sandbox workspace-write`, and a Git repository check. Dangerous bypass,
  ignored-rule, ignored-config, and danger-full-access modes are forbidden.
- Do not claim a phase complete from mocks, target renders, or contract-only
  code. Prove the runtime behavior required by its exit gate.

Execution loop for every phase:

1. Inspect existing implementation and tests before changing code.
2. Implement the smallest complete slice that meets the prompt.
3. Add focused backend, frontend, native, CLI, API, and verifier coverage as
   applicable.
4. Run focused checks.
5. Review the diff adversarially for capture failures, state lies, duplicate
   handoffs, unsafe artifact resolution, secret leaks, path traversal,
   unbounded logs, UI-only truth, stale product language, missing CLI/API
   parity, and unsafe Codex/Git behavior.
6. Fix every reproducible in-scope issue before advancing.
7. Stage only intentional files, commit, and push normally without force.
8. Open the phase PR as draft, complete local review/hardening, then mark it
   ready only after local checks pass.
9. Run required repository-scoped self-hosted macOS CI only; never paid or
   GitHub-hosted compute.
10. Merge only when required checks are green and no actionable review finding
    remains.
11. Update local `main` to the exact remote merge and run post-merge
    verification. Do not commit or push a repair directly to `main`; any defect
    or divergence requires a new scoped repair branch and PR. Confirm the
    verified local SHA already matches `origin/main`, then remove only clean
    merged phase branches/worktrees.
12. Confirm `main` is clean before starting the next phase.

Final verification must include:

- all phase-specific tests and verifiers;
- `.venv/bin/python scripts/verify_documentation_integrity.py`;
- `.venv/bin/python scripts/verify_product_truth.py`;
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`;
- focused API manifest and route classification tests;
- `make frontend-check` and visual checks when frontend changed;
- native Swift/macOS build and tests when the shell changed;
- `.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`;
- `git diff --check`;
- a real local end-to-end acceptance run proving capture through next-launch
  result display.

Git finalization:

- stage intentional files only;
- preserve unrelated changes;
- commit with scoped messages;
- push normally without force;
- open one draft PR per phase for review;
- never merge around failed checks or unresolved blockers.

Final response must include phases completed, files changed, behavior proven,
operator and Codex finding handling, faults found/fixed, tests and verifiers,
skipped checks, remaining blockers, branch/commit/PR state, and final worktree
status.
