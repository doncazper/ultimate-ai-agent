# Execute UAA-GOATCITADEL-CATCHUP-001 End To End

Role: Principal AI agent systems architect, product strategist, security
reviewer, implementation lead, and adversarial hardening reviewer for UAA.

Goal: bring UAA materially closer to GoatCitadel's agent-platform maturity
while preserving UAA's stronger authority posture. Execute the stored prompt
sequence as a gated catch-up program, not as a broad rewrite.

## Read First

Read these files completely before implementation:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/uaa_goatcitadel_catchup/README.md`
- every prompt in `docs/prompts/uaa_goatcitadel_catchup/`
- current product and authority references:
  - `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
  - `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
  - `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
  - `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
  - `docs/api/openapi_contract.md`
  - `docs/api/route_inventory.md`

If the sibling GoatCitadel repo is available, inspect it read-only for
reference patterns only. Do not copy code. Useful reference areas include:

- `../GoatCitadel/README.md`
- `../GoatCitadel/benchmark/README.md`
- `../GoatCitadel/docs/DURABLE_RUNS_REPLAY_FOUNDATION.md`
- `../GoatCitadel/docs/execution-spine-operator-proof.md`
- `../GoatCitadel/docs/CAPABILITY_SYSTEM_V1.md`
- `../GoatCitadel/docs/ADDONS_TRUST_POLICY.md`
- `../GoatCitadel/docs/SKILL_IMPORT_AND_TRUST_POLICY.md`
- `../GoatCitadel/packages/contracts/src/durable.ts`
- `../GoatCitadel/packages/contracts/src/evidence.ts`
- `../GoatCitadel/packages/contracts/src/approvals.ts`
- `../GoatCitadel/packages/contracts/src/tool-catalog.ts`
- `../GoatCitadel/packages/contracts/src/memory.ts`
- `../GoatCitadel/packages/contracts/src/memory-write-gate.ts`
- `../GoatCitadel/packages/contracts/src/llm.ts`
- `../GoatCitadel/packages/contracts/src/capability-packs.ts`
- `../GoatCitadel/packages/contracts/src/runtime-decision-trace.ts`

## Global Rules

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not modify historical release tags.
- Do not force-push.
- Do not import GoatCitadel packages or copy implementation code.
- Do not add runtime model calls, provider SDK calls, web fetching, connector
  writes, browser automation, unrestricted shell/subprocess execution, plugin
  runtime import, remote execution, public beta/release claims, production
  authority, or broad autonomy.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI remain shells, not authority.
- Product behavior must not live only in React state.
- CLI/API/core parity is required for operator-relevant mutation or durable
  state.
- Durable evidence must use safe refs and redacted summaries only.
- Every route change must update OpenAPI/API manifest checks and side-effect
  classification.
- Every UI addition must render backend-owned truth and avoid raw JSON as the
  primary operator workflow.
- If a capability is blocked, state the blocker and produce a future exact-lane
  prompt instead of pretending readiness.

## Prompt Sequence

Execute these prompts in order:

1. `01_reference_gap_truth_and_age_adjusted_scoreboard.prompt.md`
2. `02_productized_agent_loop_spine.prompt.md`
3. `03_durable_orchestration_progress_and_recovery.prompt.md`
4. `04_action_tool_code_lanes_and_approval_receipts.prompt.md`
5. `05_memory_learning_context_and_feedback.prompt.md`
6. `06_evidence_audit_receipts_and_observability.prompt.md`
7. `07_model_provider_research_and_external_info_posture.prompt.md`
8. `08_cockpit_cli_api_parity_and_operator_ux.prompt.md`
9. `09_extensibility_ecosystem_and_final_hardening.prompt.md`

## Execution Loop

For each phase:

1. Inspect current branch, commit, remotes, and `git status --short --branch`.
2. Search for existing UAA implementation before editing.
3. Classify each capability as `implemented`, `partial`, `planned`,
   `mock-only`, `blocked`, `deprecated`, `contradicted`, or `unknown`.
4. Implement only the smallest UAA-native slice that the phase authorizes.
5. Add focused tests, verifiers, docs, and release-truth updates.
6. Run focused checks for changed files.
7. Review the diff adversarially for:
   - authority creep;
   - UI-only truth;
   - raw prompt, response, provider payload, path, log, or secret persistence;
   - route/API manifest drift;
   - missing CLI parity;
   - missing approval scope validation;
   - missing idempotency, replay, rollback, or safe-disable posture;
   - product-language overclaims;
   - unsupported parity claims against GoatCitadel.
8. Fix and harden before moving to the next phase.

If the full sequence is too large for one PR, stop after Phase 01 and convert
the rest into small merge-gated PR prompts. Do not make a sprawling unreviewable
change set.

## Final Verification

Run focused tests for changed files plus the relevant subset of:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
make frontend-visual-check
```

Run frontend checks only when frontend files changed. If an environment
dependency blocks a check, report it and do not claim success.

## Final Response Requirements

Report:

- prompt sequence executed;
- phase status: implemented, partial, blocked, or deferred;
- files changed;
- GoatCitadel patterns borrowed as UAA-native designs;
- GoatCitadel patterns explicitly not merged or not appropriate;
- authority still blocked;
- tests/verifiers run with pass/fail/blocker;
- hardening loops completed and faults fixed;
- remaining risks;
- current git status summary;
- recommended next exact prompt or PR lane.

