# Execute UAA Hermes/OpenClaw Parity Gap Closure End To End

Role: principal UAA product engineer, Python agent-core architect, TypeScript
Control Center engineer, safety reviewer, performance engineer, release
engineer, and adversarial completion auditor.

Goal: execute every phase in this stored pack, close every unresolved item in
the coverage matrix with production-quality UAA-native behavior, and merge each
green phase before continuing. Re-inventory after every merge so work landing
from other Codex tasks is proven and reused rather than reimplemented.

## Read Completely Before Acting

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/uaa_parity_gap_closure/README.md`
- the verified manifest snapshot and every prompt in this combined snapshot
- `docs/prompts/authority_graduation_program/README.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- `docs/control_center/capability_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

Inspect overlapping prompt packs, boards, branches, and pull requests, but do
not execute them recursively or create a competing roadmap. This pack is a
delta implementation program over the current repository truth.

## Permanent Rules

- Treat `AGENTS.md` as binding.
- Python Agent Core remains the brain; Control Center is never authority.
- Preserve unrelated dirty work and other task worktrees. Never reset, clean,
  stash, overwrite, or force-push them.
- Never mutate historical tags.
- Only current `main` plus passing tests counts as implemented baseline.
- Do not count contracts, docs, mocks, previews, disabled adapters, plans,
  open PRs, or unmerged branches as completed behavior.
- Do not create parallel routes, stores, manifests, boards, or prompt packs
  when an existing implementation can be extended.
- No raw prompt, response, provider payload, local path, log, transcript,
  credential, secret, hostname, username, or environment dump in durable
  evidence.
- Model output, memory recall, previews, UI state, competitor code, and
  approval identifiers never grant authority.
- Every mutation must be exact-scoped, current-policy evaluated,
  approval-bound where required, idempotent, auditable, rollback-aware,
  redacted, and tested.
- Every route change updates OpenAPI, `/api/manifest`, operation IDs, route
  side-effect classification, docs, and focused tests.
- Every operator-relevant durable state or mutation has Python Core, API, CLI,
  and Control Center parity.
- Runtime model calls, provider SDKs, unrestricted web/browser/shell,
  connector writes, plugin execution, remote execution, and production
  authority require a separately accepted exact-scoped milestone. This pack
  promotes nothing by itself.

## Continuous Execution Contract

Continue automatically through all independent phases. Do not stop merely
because:

- a work item is already implemented;
- a phase becomes a proof-only no-op;
- focused tests expose defects;
- a branch needs rebasing or a scoped conflict needs resolution;
- CI is still running;
- review feedback requires fixes; or
- a later phase can proceed while another task owns an overlap.

Fix failures, harden the affected code, and continue. Do not ask for ordinary
implementation confirmation.

Hard authority boundaries, missing credentials/accounts, unavailable external
facilities, or an overlapping branch actively owned by another task may block
one item. Record the exact blocker, continue every independent item, then
revisit it once in Phase 10. Never replace a blocker with mock success or claim
the phase complete.

## Fresh Inventory Before Every Phase

1. Fetch remotes without pruning or destructive cleanup.
2. Record local/remote `main`, branch, SHA, dirty state, worktrees, open PRs,
   recently merged PRs, and overlapping changed paths.
3. If Codex task-list/read tools are available, inspect active UAA tasks and
   their stated branch/PR ownership without steering or modifying them.
4. Rebuild the coverage ledger using the classification vocabulary in the
   pack README.
5. Prove every proposed skip from current `main` using code plus tests.
6. Use the current phase prompt and manifest from the verified combined snapshot.
   Refresh
   repository and code inventory from synchronized `main`, but do not replace
   the snapshot's manifest or prompt text with mutable worktree content.

When the current worktree is dirty or owned by another task, create a separate
clean orchestration worktree from current `origin/main`. Do not touch the
other task's worktree.

## Phase Git And Merge Loop

For each Phase 01 through Phase 10:

1. Refresh the inventory and phase ledger.
2. If every item is `merged_proven`, record a no-op proof and continue without
   an empty commit.
3. Otherwise create one dedicated `codex/parity-gap-XX-*` branch/worktree from
   current `main`.
4. Implement all unresolved in-scope outcomes for that phase. Do not stop at a
   contract, disabled adapter, mock UI, or follow-up list.
5. Run focused tests, the phase checks, and an adversarial hardening pass.
6. Fix every in-scope high/medium defect and re-run checks.
7. Stage intentional files only and commit with the phase's scoped message.
8. Push the branch and open one focused draft PR.
9. Monitor reviews and required hosted checks. Fix failures on the phase branch
   until green.
10. Merge only when required checks are green and the phase acceptance contract
    is satisfied.
11. Update local `main` to the exact remote merge SHA, run post-merge focused
    verification, and record the merge in the ledger.
12. Remove only clean, merged temporary phase branches/worktrees.
13. Refresh the entire inventory before continuing.

Do not commit repairs directly to `main`, do not merge a red PR, do not squash
away required phase traceability, and do not take ownership of another task's
unmerged PR without an explicit handoff.

If hosted CI infrastructure is unavailable, wait three minutes and retry once.
If it remains unavailable, mark `blocked_by_external_facility`, leave the PR
clean and pushed, continue non-dependent local phases on separate branches, and
revisit it in Phase 10. Do not claim hosted checks are green.

## Prompt Sequence

Execute in exact order:

1. `01_fresh_inventory_and_convergence_ledger.prompt.md`
2. `02_backend_truth_first_loop_and_evidence.prompt.md`
3. `03_live_local_setup_and_packaging.prompt.md`
4. `04_goals_durable_events_and_lifecycle.prompt.md`
5. `05_action_inbox_work_board_and_session_ux.prompt.md`
6. `06_morning_briefing_sources_and_background_worker.prompt.md`
7. `07_memory_search_backup_and_storage_integrity.prompt.md`
8. `08_performance_supply_chain_and_efficiency.prompt.md`
9. `09_cross_cutting_reliability_and_future_lane_proofs.prompt.md`
10. `10_end_to_end_acceptance_and_parity_truth.prompt.md`

## Common Verification Floor

Run focused checks first, then the applicable subset:

```bash
git diff --check
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

Run visual/browser verification for changed user-visible flows. Do not use
mock fallback as visual proof of backend behavior.

## Final Output

Phase 10 must create a redacted report under
`reports/parity_gap_closure/` containing:

- starting and final `main` SHAs;
- every coverage ID and terminal classification;
- evidence for every `merged_proven` item;
- phase branches, commits, PRs, checks, merge SHAs, and post-merge results;
- files and behavior added per phase;
- hardening defects found and fixed;
- tests, verifiers, builds, visual checks, benchmarks, and dogfood runs;
- live-data sources exercised and their safe refs;
- authority promoted by separately accepted exact lanes;
- authority still blocked;
- unresolved external or in-flight blockers;
- current capability/release/product-truth status; and
- final clean `main` and remote synchronization proof.

Phase 10 allows at most two focused repair passes. Then stop. Do not generate
another pack, recurse into another program, or call incomplete P0/P1 work
parity-ready.
