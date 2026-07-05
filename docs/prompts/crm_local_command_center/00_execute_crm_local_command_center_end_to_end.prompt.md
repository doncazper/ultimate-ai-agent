# Execute UAA CRM Local Command Center Prompt Pack End To End

You are working in the Ultimate AI Agent repository root.

Role: You are a Principal Software Engineer and product-minded agent architect
implementing UAA's governed, local-first CRM command center.

Goal: Build UAA CRM into a local-first relationship operating system that
captures the best public feature patterns from paid real estate CRMs such as
Follow Up Boss and Wise Agent while preserving UAA's proof, memory, approval,
redaction, local-first, and operator-control invariants.

Do not clone proprietary apps. Do not copy proprietary UI, code, text,
templates, screenshots, data, schemas, branding, or private behavior. Build
UAA-native CRM workflows from public feature patterns and UAA's existing
architecture.

Read first:

- `AGENTS.md`
- `README.md`
- `docs/prompts/crm_local_command_center/README.md`
- every phase prompt in `docs/prompts/crm_local_command_center/`
- `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`
- `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/kanban/current_board.md`

Prompt sequence:

1. `docs/prompts/crm_local_command_center/01_crm_product_truth_feature_map.prompt.md`
2. `docs/prompts/crm_local_command_center/02_crm_backend_read_model.prompt.md`
3. `docs/prompts/crm_local_command_center/03_crm_control_center_cockpit.prompt.md`
4. `docs/prompts/crm_local_command_center/04_crm_local_storage_seed.prompt.md`
5. `docs/prompts/crm_local_command_center/05_crm_relationship_timeline.prompt.md`
6. `docs/prompts/crm_local_command_center/06_crm_follow_up_queue.prompt.md`
7. `docs/prompts/crm_local_command_center/07_crm_smart_lists.prompt.md`
8. `docs/prompts/crm_local_command_center/08_crm_pipeline_board.prompt.md`
9. `docs/prompts/crm_local_command_center/09_crm_exact_local_mutations.prompt.md`
10. `docs/prompts/crm_local_command_center/10_crm_communication_drafts.prompt.md`
11. `docs/prompts/crm_local_command_center/11_crm_ai_proposal_layer.prompt.md`
12. `docs/prompts/crm_local_command_center/12_crm_local_import_export.prompt.md`
13. `docs/prompts/crm_local_command_center/13_crm_reporting.prompt.md`
14. `docs/prompts/crm_local_command_center/14_crm_connector_read_lanes.prompt.md`
15. `docs/prompts/crm_local_command_center/15_crm_sends_writes_authority_plan.prompt.md`
16. `docs/prompts/crm_local_command_center/16_crm_qa_gate.prompt.md`

Global rules:

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not modify historical release tags.
- Do not force-push.
- Python Agent Core owns durable CRM truth.
- Control Center is presentation/initiation only.
- CLI/repo-local inspection exists for operator-relevant CRM state.
- No UI-only durable workflow truth.
- No raw prompt, raw response, provider payload, raw source body, raw message
  body, raw email body, raw calendar body, raw local path, log body, username,
  hostname, environment dump, credential, token, cookie, account identifier, or
  private contact details in durable artifacts unless a later exact safe schema
  explicitly permits a redacted/local-only form.
- CRM memory is recall, not truth or authority.
- Model output is proposal-only.
- No connector writes, sends, SMS, email sending, calendar writes, account sync,
  browser automation inside UAA runtime, provider/model calls, unrestricted
  shell/subprocess execution, background autonomy, public beta/release claims,
  or production authority unless an exact phase grants that scope with tests.
- If a lane cannot be safely promoted, keep the full-strength goal visible,
  write/update a blocker report, generate an unblock prompt, and continue only
  if the next phase does not depend on the blocked lane.

Execution loop:

1. Inspect branch, commit, remotes, and `git status --short --branch`.
2. Inspect existing CRM implementation before editing:
   - `src/ultimate_ai_agent/core/crm/`
   - `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`
   - `docs/control_center/CRM_M1_FIXTURE_ONLY_VERTICAL_SHELL.md`
   - `apps/control-center/src/routes.tsx`
   - `apps/control-center/src/mocks/controlCenterData.ts`
   - CRM tests and verifiers.
3. Execute each phase in order:
   - create/use the phase branch named in the phase prompt;
   - derive concrete requirements from the phase prompt;
   - if already implemented, prove it with code/tests/docs and harden stale
     surfaces instead of duplicating product truth;
   - otherwise implement the smallest backend-owned, tested,
     truth-preserving slice in scope;
   - run focused tests and verifiers;
   - review for authority creep, UI-only durable truth, stale product claims,
     redaction leaks, route/API drift, missing CLI/API parity, and missing
     blocked-state labels;
   - fix before moving to the next phase.
4. After each phase:
   - run `git status`;
   - run `git diff --check`;
   - run focused tests for changed files;
   - run documentation integrity;
   - run product truth and operational maturity verifiers;
   - run OpenAPI verifier if API/routes changed;
   - run Control Center release-surface verifier if Control Center/release
     surface changed;
   - run `make frontend-check` if frontend changed;
   - run visual check if primary UI output or visual manifests changed;
   - stage only scoped files;
   - commit with the phase commit message;
   - push branch;
   - open/update a focused PR.
5. Merge only when green and only when the operator has explicitly approved
   merge behavior in the active run. If merge is not approved, stop after the
   PR is ready and report the next phase.
6. After the final phase, run a final hardening pass and final verification.

Final response must include:

- prompt sequence executed;
- phases implemented, already satisfied, blocked, or skipped;
- branches and PRs;
- files changed;
- faults found and fixed;
- tests/verifiers run with pass/fail;
- skipped checks with reasons;
- authority newly enabled by exact lane;
- authority still blocked;
- blocker reports and unblock prompts created;
- current commit and final git status.
