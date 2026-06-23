# Execute FCC-AUTH-RAMP-001 End To End

Role: You are a Principal Software Engineer performing implementation,
adversarial review, hardening, verification, and git finalization.

Mode: execute the stored prompt sequence in order. Keep scope tight.

Prompt sequence:
1. `docs/prompts/fcc_authority_ramp/01_fcc_auth_ramp_charter.prompt.md`
2. `docs/prompts/fcc_authority_ramp/02_read_only_proposal_foundation.prompt.md`
3. `docs/prompts/fcc_authority_ramp/03_authority_candidate_ranking.prompt.md`
4. `docs/prompts/fcc_authority_ramp/04_first_micro_lane_graduation.prompt.md`

Global rules:
- Treat `AGENTS.md` as binding.
- Do not modify historical release tags.
- Do not add runtime model calls, web fetching, provider SDK calls, connector
  writes, browser automation, unrestricted shell/subprocess execution, plugin
  runtime import, remote execution, memory writes, context injection, public
  beta/release claims, production authority, or broad autonomy unless the
  current prompt explicitly reaches an accepted exact micro-lane and every gate
  passes.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- CLI/API/core parity is required for operator-relevant mutation.
- Durable evidence must use safe refs or redacted summaries only.

Execution loop:
1. Read `AGENTS.md` and all four prompts completely.
2. Inspect `git status --short --branch`.
3. For each prompt in order:
   - implement the smallest in-scope changes;
   - add focused docs, tests, and verifiers;
   - run the focused checks for changed areas;
   - review the diff adversarially for unsafe authority, stale claims,
     UI-only truth, route/API drift, redaction leaks, missing tests, and
     unsupported product language;
   - fix and harden until no in-scope faults remain.
4. If Prompt 4 cannot safely graduate one exact micro-lane, do not fake it.
   Record the blocked/no-go posture and harden the verifier instead.
5. Run final focused verification:
   - `.venv/bin/python scripts/verify_operational_maturity.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
   - `make frontend-check` if frontend files changed
6. Clean the working directory by staging only intentional changes.
7. Commit with a scoped message.
8. If working on a feature branch, merge to `main` after verification and push.
   If already on `main`, commit on `main` only when the operator explicitly
   requested it, then push `main`.
9. Never force-push and never mutate tags.

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
- current git status summary
- commit hash and push result when git finalization succeeds
