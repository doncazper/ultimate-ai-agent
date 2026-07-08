# Execute Authority Graduation Program End To End

Role: Principal engineer, safety reviewer, product reviewer, and release
engineer for UAA authority graduation.

Goal: Open useful real authority lanes without turning UAA reckless. Execute the
saved prompt sequence one lane at a time. For each lane, implement the narrowest
safe promotion, review and harden the PR based on Codex/GitHub feedback, merge
to `main` only when green, push, then continue.

Read first:

- `AGENTS.md`
- `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
- every prompt in `docs/prompts/authority_graduation_program/`
- overlapping prompt packs and boards that may already contain partial or
  complete authority-lane work:
  - `docs/prompts/fcc_authority_ramp/`
  - `docs/prompts/fcc_action_inbox_loop/`
  - `docs/prompts/fcc_memory_module_sequence/`
  - `docs/prompts/fcc_planned_sequence/`
  - `docs/prompts/uaa_runtime_capability_foundation/`
  - `docs/prompts/uaa_next_capability_product_prompts.md`
  - `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`
  - `docs/control_center/OPERATIONALIZATION_LADDER.md`
  - `docs/control_center/operational_maturity_manifest.json`
  - `docs/control_center/authority_candidate_scorecard.json`

Prompt sequence:

1. `01_web_evidence_lane.prompt.md`
2. `02_browser_lane.prompt.md`
3. `03_provider_model_invocation_lane.prompt.md`
4. `04_connector_read_lane.prompt.md`
5. `05_connector_write_send_lane.prompt.md`
6. `06_local_shell_subprocess_lane.prompt.md`
7. `07_filesystem_mutation_lane.prompt.md`
8. `08_memory_write_context_injection_lane.prompt.md`
9. `09_action_execution_lane.prompt.md`
10. `10_background_worker_scheduler_lane.prompt.md`
11. `11_streaming_realtime_transport_lane.prompt.md`
12. `12_credential_oauth_account_lane.prompt.md`
13. `13_packaging_distribution_lane.prompt.md`
14. `14_production_authority_lane.prompt.md`
15. `15_extension_plugin_callable_lane.prompt.md`
16. `99_blocker_report_and_unblock_prompts.prompt.md`

Per-lane loop:

1. Sync `main`. Do not work from a dirty or stale base.
2. Create a branch named `codex/authority-<lane>-<level>`.
3. Run the overlap-aware preflight for the lane.
4. Re-read the lane row in `AUTHORITY_GRADUATION_BOARD.md`.
5. Implement only the next safe promotion level, or verify/harden existing
   overlapping work if the lane is already partially implemented.
6. Add backend/core/API/CLI/UI/docs/tests only as needed for the lane.
7. Run focused tests and verifiers.
8. Commit, push, and open a draft PR.
9. Review PR feedback, failing checks, product-language risks, redaction risks,
   route/API drift, UI-only truth, and authority overreach.
10. Fix and harden until the lane PR is green or blocked.
11. If green and in scope, mark ready, merge to `main`, pull `main`, and push.
12. If blocked, do not fake readiness. Add a blocked report and an unblock
    prompt using `99_blocker_report_and_unblock_prompts.prompt.md`.
13. Continue to the next lane only after the current lane is merged or blocked
    with a concrete unblock prompt.

Overlap-aware preflight:

For each lane, assume prior prompt packs may have already implemented,
partially implemented, or planned related work. Do not trip over this and do
not duplicate it.

1. Search the repo for the lane's existing contracts, docs, routes, CLI scripts,
   tests, verifiers, manifests, PR notes, and board entries.
2. Classify the lane's actual current level:
   - `missing`
   - `contract_only`
   - `partial`
   - `read_only_or_dry_run`
   - `manual_foreground`
   - `scoped_repeatable`
   - `limited_automation`
   - `broader_capability`
   - `blocked_by_unmerged_pr`
   - `blocked_by_missing_evidence`
3. If an existing implementation already satisfies the lane's requested next
   promotion, do not reimplement it. Instead:
   - add missing tests/verifiers/docs only if needed;
   - tighten product-language and release-surface truth;
   - collect or point to dogfood evidence;
   - update the board with the verified current level;
   - open a hardening/verification PR if there are changes.
4. If a lane is partially implemented, use the existing implementation as the
   base. Harden it rather than creating duplicate routes, duplicate manifests,
   duplicate prompt packs, or competing roadmaps.
5. If related work exists only in an open/unmerged PR, do not pretend `main`
   has it. Either wait for/merge the prerequisite PR when explicitly allowed,
   or mark this lane `blocked_by_unmerged_pr` and generate the next prompt.
6. If a lane's next promotion depends on another lane, do not bypass the
   dependency. Record the dependency and generate the unblock prompt.
7. If a lane is already ahead of the board, update the board only when tests
   and evidence prove it. Otherwise downgrade the claim to the proven level.
8. Treat existing partial work as a clue, not as authority. It must still pass
   exact scope, redaction, approval, idempotency, rollback/safe-disable,
   product-language, and verifier gates.

Required checks by default:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
```

Also run lane-specific tests named in the lane prompt. Run `make
frontend-check` when frontend changes. Run release/product-language/visual
verifiers when manifests or visible routes change.

Global hard stops:

- Do not force-push.
- Do not mutate historical tags.
- Do not merge a red PR.
- Do not use broad approve-all or standing authority.
- Do not promote multiple new write/autonomy lanes in one PR.
- Do not promote plugin runtime import or callable extension activation from a
  catalog review alone.
- Do not hide blockers in docs. Produce unblock prompts.

Final report:

- lanes attempted
- lanes merged
- lanes blocked
- prompts generated for blockers
- tests/verifiers run
- authority still blocked
- dogfood evidence collected
- current `main` commit
- PR URLs and merge SHAs
