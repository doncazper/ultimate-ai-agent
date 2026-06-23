# FCC-ACTION-INBOX-LOOP-002 Execute Next Planned Steps

Role: You are a Principal Software Engineer performing planned execution,
adversarial review, hardening, verification, and git finalization.

Mode: gate-driven implementation. Do not skip gates. Keep scope tight.

Task: Execute the next Founder Command Center work in a planned sequence:

1. Re-run the exact-scope `local_task_create` graduation-gate review.
2. If the gate passes or has only small fixable conditions, implement
   `FCC-ACTION-001b` safe-disable / rollback posture for the existing
   `local_task_create` lane.
3. Polish Action Inbox review ergonomics for backend-owned lanes and receipt
   posture.
4. Implement the next read-only Morning Briefing/source-readiness slice.
5. Review, verify, harden, clean the worktree, commit, and push.
6. Create one recommended next-step prompt for the follow-on work.

Treat `AGENTS.md` as binding.

Global non-goals:
- Do not add generic execution.
- Do not add connector writes.
- Do not add shell/subprocess execution.
- Do not add browser automation.
- Do not add provider/model authority.
- Do not add memory writes.
- Do not add context injection.
- Do not add plugin runtime import.
- Do not add remote execution.
- Do not add production/public release claims.
- Do not claim a maturity rank promotion unless the manifest and verifier
  support it.
- Do not add new broad route authority.
- Do not modify historical release tags.

Core invariants:
- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- React may own presentation state only.
- Approval refs are identifiers until `LocalApprovalAuthority` validates exact
  scope.
- Every mutating path must be exact-scoped, approval-bound, idempotent,
  auditable, rollback/safe-disable aware, redacted, and tested.
- Durable evidence must use safe refs or redacted summaries only.

## Phase 0 - Baseline

1. Read `AGENTS.md` completely.
2. Inspect `git status --short --branch`.
3. Read:
   - `docs/prompts/fcc_action_inbox_loop/05_recommended_next_local_task_create_gate.prompt.md`
   - `docs/control_center/OPERATIONALIZATION_LADDER.md`
   - `docs/control_center/operational_maturity_manifest.json`
   - `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
   - `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
   - `docs/kanban/founder_command_center_board.md`
   - Action Inbox backend/API/frontend/storage/tests
   - Morning Briefing backend/API/frontend/tests
4. Identify changed files and do not revert unrelated user changes.

## Phase 1 - Gate Review

Run the review gate from:

`docs/prompts/fcc_action_inbox_loop/05_recommended_next_local_task_create_gate.prompt.md`

Gate question:
Can an operator safely understand live `/actions` eligibility, approval,
pending receipt state, committed state, replay posture, and conflict posture
from backend-owned data only, with no React-minted authority or UI-only success
truth?

If the gate fails:
- Do not implement safe-disable/rollback or source-readiness work.
- Fix only the smallest gate-blocking truth/test/verifier issue if it is
  clearly in scope.
- Otherwise record a no-go posture in docs/tests and create a follow-up prompt.

If the gate passes or has only small fixable conditions:
- Fix the conditions first.
- Re-run focused checks.
- Continue to Phase 2.

## Phase 2 - FCC-ACTION-001b Safe-Disable / Rollback Posture

Goal:
Make the existing `local_task_create` lane visibly and verifiably
rollback/safe-disable aware without adding broad authority.

Allowed scope:
- Existing `local_task_create` Action Inbox lane only.
- Existing typed route:
  `POST /control-center/actions/{action_id}/local-task/commit`.
- Existing side-effect class:
  `local_dev_workspace_only`.
- Existing route classification:
  `mutating_requires_authority`.

Requirements:
- Backend/core/storage must check a backend-owned safe-disable posture before
  local task mutation.
- If the lane is disabled, commit is denied with explicit safe refs and blocked
  reasons.
- `/actions` must show safe-disable/rollback posture from backend/API data.
- CLI/script parity must expose inspection of the same posture or clearly
  report a documented blocker.
- Receipts/evidence must include safe-disable/rollback refs where present.
- Verifier/tests must fail if the lane claims rank 5+ without safe-disable /
  rollback posture.
- Do not implement rollback execution unless it already exists and is exact
  scoped. If rollback execution is missing, represent it honestly as a blocker.

Tests to add/update:
- Commit succeeds when safe-disable posture is enabled and exact approval
  validates.
- Commit is denied when the lane is safe-disabled.
- Denial uses safe refs only.
- Receipt/evidence includes rollback/safe-disable posture for success.
- `/actions` displays enabled/disabled posture from backend data.
- React cannot override safe-disable posture.
- CLI/verifier catches missing posture.

## Phase 3 - Action Inbox Review Polish

Goal:
Improve operator scanability without changing authority.

Requirements:
- Preserve the six backend-owned lanes:
  - `ready_for_decision`
  - `approved_local_task_lane`
  - `blocked_by_authority`
  - `expired_stale`
  - `receipt_recorded`
  - `proposal_only_no_execution_path`
- Add or refine presentation-only filters/drilldowns for:
  - blocked authority refs
  - stale/expiry posture
  - replay/conflict posture
  - receipt visibility
  - missing backend contract states
- React must not mint lane membership, eligibility, approval envelope fields,
  receipt refs, replay/conflict posture, safe-disable posture, or authority.
- No generic execute button.

Tests:
- Filters/drilldowns are presentation-only over backend group IDs and item
  fields.
- Blocked/proposal/stale lanes never show commit or generic execution controls.
- Receipt/replay/conflict details remain visible.
- Mock/degraded data remains explicitly non-authoritative.

## Phase 4 - Morning Briefing Read-Only Source Readiness

Goal:
Move Morning Briefing/source readiness one step forward while staying
read-only/proposal-only.

Allowed scope:
- Read-only source metadata/status contracts.
- Local manifest/config/status inspection only.
- No account auth, connector runtime, background polling, raw message/calendar
  ingestion, web fetch, notification delivery, connector write, memory write,
  model/provider call, or context injection.

Requirements:
- Surface source readiness for Morning Briefing using backend/API-owned or
  documented read-only data.
- If a backend route is added, it must be read-only, typed, classified
  non-mutating, safe-ref-only, and covered by OpenAPI/API manifest tests.
- If no backend route is safely available, mark source readiness explicitly
  backend-only/missing with blocker refs rather than fake UI truth.
- `/briefing` and `/today` should show source readiness, missing contracts,
  next safe action, and blocked authority classes.
- Docs/board/gap map must remain honest that no connector runtime exists.

Tests:
- Morning Briefing shows source readiness from backend/API-owned or documented
  read-only data.
- Missing source contracts render explicit blockers.
- No refresh/send/connect/write/notify/provider/memory/context controls appear.
- Status data remains redacted and safe-ref-only.

## Phase 5 - Review, Harden, Verify

After each phase:
- Review the diff adversarially for unsafe authority, UI-only truth, stale
  product claims, redaction leaks, route/API drift, and missing tests.
- Fix in-scope faults.
- Re-run focused checks.

Final verification:
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
- `make frontend-check`

Report blockers clearly if a check is blocked by environment/dependencies.

## Phase 6 - Finalization

1. Create a recommended next-step prompt based on the outcome.
2. Update prompt bundle docs/manifests if prompt files are added.
3. Stage only intentional changes.
4. Commit with a scoped message.
5. Push the current branch if the operator requested git finalization.
6. Do not force-push and do not mutate tags.

Final response must include:
- gate decision
- phases completed
- loop count
- files changed
- faults found/fixed
- hardening/tests/verifier rules added
- behavior explicitly not added
- tests/verifiers run with pass/fail
- skipped or blocked checks
- remaining risks
- recommended next prompt path
- current git status summary
- commit hash and push result if finalized
