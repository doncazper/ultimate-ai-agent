# Authority Graduation Program Prompt Pack

Status: stored execution prompts, not runtime authority

This prompt pack turns the blocked authority list into a promotion program. It
is intentionally serious: each lane must open narrowly, dogfood with receipts,
then promote or freeze. The pack should be run one focused PR at a time even
when the end-to-end wrapper is used.

Primary board:

`docs/control_center/AUTHORITY_GRADUATION_BOARD.md`

## Wrapper Command

From the repo root:

```bash
bash scripts/dev/run_authority_graduation_program.sh
```

Optional:

```bash
CODEX_AUTH_GRAD_SANDBOX=workspace-write \
CODEX_AUTH_GRAD_MODEL=gpt-5.5 \
bash scripts/dev/run_authority_graduation_program.sh
```

The wrapper sends `00_execute_all_review_fix_merge.prompt.md` to Codex. The
orchestrator prompt instructs Codex to run each lane as a focused branch/PR,
review and harden the PR, merge only when green, then continue.

The orchestrator is overlap-aware. Before implementing a lane, it searches for
related work from earlier prompt packs, PRs, manifests, verifiers, docs, and
boards. If something is already partially implemented, it must harden or verify
that work instead of duplicating it. If something is already complete and
proven, it should update the board/evidence rather than reimplementing the
lane. If the required work exists only in an unmerged PR, it must mark the lane
blocked by that prerequisite or merge the prerequisite only when explicitly
allowed by the current run.

## Prompt Order

1. `00_execute_all_review_fix_merge.prompt.md`
2. `01_web_evidence_lane.prompt.md`
3. `02_browser_lane.prompt.md`
4. `03_provider_model_invocation_lane.prompt.md`
5. `04_connector_read_lane.prompt.md`
6. `05_connector_write_send_lane.prompt.md`
7. `06_local_shell_subprocess_lane.prompt.md`
8. `07_filesystem_mutation_lane.prompt.md`
9. `08_memory_write_context_injection_lane.prompt.md`
10. `09_action_execution_lane.prompt.md`
11. `10_background_worker_scheduler_lane.prompt.md`
12. `11_streaming_realtime_transport_lane.prompt.md`
13. `12_credential_oauth_account_lane.prompt.md`
14. `13_packaging_distribution_lane.prompt.md`
15. `14_production_authority_lane.prompt.md`
16. `99_blocker_report_and_unblock_prompts.prompt.md`

## Non-Negotiable Shape

- No lane promotes itself because a roadmap says so.
- No broad authority unlock.
- No UI-only operator truth.
- No raw payload persistence.
- No public beta, public release, production-readiness, or production authority
  claims unless the production lane is explicitly approved.
- Each blocker must produce a next unblock prompt, not vague TODO copy.
