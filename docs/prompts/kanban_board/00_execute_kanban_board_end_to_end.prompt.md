# Execute UAA Kanban Board Prompt Pack End To End

Role: You are a Principal Software Engineer performing implementation,
adversarial review, hardening, verification, and git finalization for the UAA
Work Board / Kanban cockpit.

Mode: execute the stored prompt sequence in order. Keep scope tight. If a phase
is already implemented, prove it with code, tests, docs, and verifiers, then
harden any stale or weak surface instead of duplicating product truth.

Prompt sequence:
1. `docs/prompts/kanban_board/01_work_board_read_model_and_cli.prompt.md`
2. `docs/prompts/kanban_board/02_work_board_ui_interactions.prompt.md`
3. `docs/prompts/kanban_board/03_work_board_verification_and_docs.prompt.md`

Global rules:
- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not modify historical release tags.
- Do not force-push.
- Python Agent Core remains the brain and owns durable Work Board truth.
- Control Center is presentation/initiation only.
- React may own selected tabs, filters, local unsaved layout preview, and
  similar presentation state only.
- Do not persist raw prompts, raw responses, raw provider payloads, raw local
  paths, raw logs, credentials, tokens, cookies, private data, or unsafe
  generated content.
- Do not add runtime model calls, provider SDK calls, web fetching, connector
  writes, issue tracker writes, browser automation as UAA product behavior,
  unrestricted shell/subprocess execution, plugin runtime import, remote
  execution, public beta/release claims, production authority, or broad
  autonomy.
- Durable reorder, card create/archive, assignment, issue tracker sync, receipt,
  rollback, and external agent dispatch remain blocked until a later exact
  authority lane adds approval binding, idempotency, receipts, rollback,
  redaction, CLI parity, route classification, and verifier coverage.

Execution loop:
1. Read `AGENTS.md`, this README, and every prompt in the sequence.
2. Inspect branch, commit, remotes, and `git status --short --branch`.
3. Inspect existing Work Board implementation before editing:
   - `src/ultimate_ai_agent/core/control_center/work_board.py`
   - `src/ultimate_ai_agent/api/control_center.py`
   - `scripts/dev/uaa_work_board.py`
   - `apps/control-center/src/components/WorkBoardPanel.tsx`
   - Work Board tests, route manifests, release surface, and docs.
4. Execute each phase in order:
   - derive concrete requirements from the phase prompt;
   - if already implemented, prove it and harden weak spots;
   - otherwise implement the smallest backend-owned, tested, truth-preserving
     slice in scope;
   - run focused tests/checks;
   - review for authority creep, UI-only durable truth, route/API drift,
     missing CLI/API parity, stale product claims, redaction leaks, and missing
     blocked-state labels;
   - fix before moving to the next phase.
5. After the sequence, run a final hardening pass.
6. Run final verification:
   - `git diff --check`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_work_board.py`
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `.venv/bin/python scripts/verify_product_truth.py`
   - `.venv/bin/python scripts/verify_operational_maturity.py`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `.venv/bin/python scripts/verify_control_center_release_surface.py`
   - `make frontend-check` if frontend files changed
   - `make frontend-visual-check` if primary UI output or visual manifests
     changed.
7. Stage only intentional changes.
8. Commit with a scoped message only after verification passes.
9. Push the branch without force.

Final response must include:
- prompt sequence executed;
- phases implemented, already satisfied, or still blocked;
- files changed;
- faults found and fixed;
- verifiers/tests run with pass/fail;
- skipped checks with reasons;
- behavior explicitly not added;
- authority still blocked;
- commit hash and push result when git finalization succeeds.
