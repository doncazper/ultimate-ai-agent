# Execute FCC Planned Sequence End To End

Role: You are a Principal Software Engineer performing implementation,
adversarial review, hardening, verification, and git finalization.

Mode: execute the stored prompt sequence in order. Keep scope tight. Stop or
record a no-go when a prompt would require authority outside its accepted
milestone.

Prompt sequence:
1. `docs/prompts/fcc_planned_sequence/01_uaa_p1_066_local_model_manager_read_only_status.prompt.md`
2. `docs/prompts/fcc_planned_sequence/02_fcc_inbox_001_deeper_approval_envelope_ux.prompt.md`
3. `docs/prompts/fcc_planned_sequence/03_fcc_briefing_001_morning_briefing_today_plan.prompt.md`
4. `docs/prompts/fcc_planned_sequence/04_fcc_sources_001_source_readiness_draft_only_inputs.prompt.md`
5. `docs/prompts/fcc_planned_sequence/05_fcc_memory_crm_001_professional_memory_crm_binding.prompt.md`
6. `docs/prompts/fcc_planned_sequence/06_fcc_review_001_evidence_weekly_review.prompt.md`
7. `docs/prompts/fcc_planned_sequence/07_fcc_health_001_self_healing_recommendations.prompt.md`
8. `docs/prompts/fcc_planned_sequence/08_fcc_dogfood_001_fourteen_day_private_harness.prompt.md`
9. `docs/prompts/fcc_planned_sequence/09_fcc_action_001_approval_bound_local_micro_lanes.prompt.md`
10. `docs/prompts/fcc_planned_sequence/10_fcc_polish_001_native_apple_grade_ux.prompt.md`

Global rules:
- Treat `AGENTS.md` as binding.
- Do not modify historical release tags.
- Do not force-push.
- Do not add runtime model calls, web fetching, provider SDK calls, connector
  writes, browser automation as product behavior, unrestricted shell/subprocess
  execution, plugin runtime import, remote execution, public beta/release
  claims, production authority, or broad autonomy unless a later accepted exact
  scoped milestone authorizes that exact lane and every gate passes.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI are shells, not authority.
- CLI/API/core parity is required for operator-relevant mutation.
- Durable evidence must use safe refs or redacted summaries only.
- React may own only presentation state.

Execution loop:
1. Read `AGENTS.md`, this README, and all prompts in the sequence.
2. Inspect `git status --short --branch` and preserve unrelated user changes.
3. For each prompt in order:
   - derive concrete requirements from the prompt and referenced docs;
   - inspect current implementation before changing files;
   - if already implemented, prove it with tests/docs/verifier evidence and fix
     stale currentness docs;
   - otherwise implement the smallest backend-owned, tested, truth-preserving
     slice in scope;
   - run focused checks;
   - review adversarially for unsafe authority, UI-only truth, route/API drift,
     stale claims, redaction leaks, missing tests, and unsupported product
     language;
   - fix and harden before moving to the next prompt.
4. After the sequence, run a final hard review and repair pass.
5. Run final verification:
   - `.venv/bin/python scripts/verify_operational_maturity.py`
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `.venv/bin/python scripts/verify_product_truth.py --root .`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
   - `make frontend-check` if frontend files changed
   - `git diff --check`
6. Stage only intentional changes.
7. Commit with a scoped message only after verification passes.
8. Create an annotated tag only after the verified commit exists. Treat old
   tags as immutable audit records.
9. Push the branch and tag without force.

Final response must include:
- prompt sequence executed;
- prompts that were implemented, blocked, or deferred;
- files changed;
- faults found and fixed;
- verifiers/tests run with pass/fail;
- skipped checks with reasons;
- behavior explicitly not added;
- remaining risks;
- commit hash, tag name, and push result when git finalization succeeds.
