# Execute FCC-ACTION-INBOX-LOOP-001 End To End

Role: You are a Principal Software Engineer performing implementation,
adversarial review, hardening, verification, and git finalization.

Mode: execute the stored prompt sequence in order. Keep scope tight.

Prompt sequence:
1. `docs/prompts/fcc_action_inbox_loop/01_local_task_create_graduation_gate_review.prompt.md`
2. `docs/prompts/fcc_action_inbox_loop/02_local_task_receipt_refresh_reconciliation.prompt.md`
3. `docs/prompts/fcc_action_inbox_loop/03_action_inbox_review_ergonomics.prompt.md`
4. `docs/prompts/fcc_action_inbox_loop/04_morning_briefing_source_readiness.prompt.md`

Global rules:
- Treat `AGENTS.md` as binding.
- Do not modify historical release tags.
- Do not add runtime model calls, web fetching, provider SDK calls, connector
  writes, browser automation, unrestricted shell/subprocess execution, plugin
  runtime import, remote execution, memory writes, context injection, public
  beta/release claims, production authority, maturity rank promotion, or broad
  autonomy.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- CLI/API/core parity is required for operator-relevant mutation.
- Durable evidence must use safe refs or redacted summaries only.
- React may render backend-owned state and presentation-only filters/drilldowns,
  but must not mint authority, grants, eligibility, receipt truth, source
  readiness truth, risk, scope, or side-effect class.

Execution loop:
1. Read `AGENTS.md` and all four prompts completely.
2. Inspect `git status --short --branch`.
3. For each prompt in order:
   - implement the smallest in-scope changes;
   - add focused docs, tests, and verifiers;
   - run focused checks for changed areas;
   - review the diff adversarially for unsafe authority, UI-only truth,
     route/API drift, stale claims, redaction leaks, missing tests, and
     unsupported product language;
   - fix and harden until no in-scope faults remain.
4. If a prompt discovers that prerequisites are missing, record an explicit
   no-go or blocked posture and harden tests/verifiers. Do not fake readiness.
5. Run final focused verification:
   - `.venv/bin/python scripts/verify_operational_maturity.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
   - `make frontend-check` if frontend files changed
6. Stage only intentional changes and commit with a scoped message when the
   full loop passes.
7. Never force-push and never mutate tags.

Final response must include:
- prompt sequence executed
- loop count
- files changed
- faults found and fixed
- hardening/tests/verifier rules added
- behavior explicitly not added
- tests/verifiers run with pass/fail
- skipped or blocked checks
- remaining risks
- recommended next-step prompt path
- current git status summary
- commit hash when git finalization succeeds

