# Execute UAA-RUNTIME-CAPABILITY-FOUNDATION-001 End To End

Role: Principal AI agent systems architect, product strategist, security
reviewer, implementation lead, and adversarial hardening reviewer for UAA.

Goal: bring UAA materially closer to high-maturity agent/operator platform
quality, using the UAA vs GoatCitadel comparison as an evidence-backed coverage
target while preserving UAA's stronger authority posture. Execute the stored
prompt sequence as a gated catch-up program, not as a broad rewrite.

## Read First

Read these files completely before implementation:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/uaa_runtime_capability_foundation/README.md`
- every prompt in `docs/prompts/uaa_runtime_capability_foundation/`
- `docs/prompts/authority_graduation_program/README.md`
- `docs/prompts/authority_graduation_program/prompt_bundle_manifest.json`
- current product and authority references:
  - `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
  - `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
  - `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
  - `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
  - `docs/api/openapi_contract.md`
  - `docs/api/route_inventory.md`

If the sibling GoatCitadel or other external comparison runtime repo is
available, inspect it read-only for reference patterns only. Do not copy code.
Useful reference areas include:

- `external-runtime-ref:readme`
- `external-runtime-ref:benchmark-readme`
- `external-runtime-ref:durable-runs-replay-foundation`
- `external-runtime-ref:execution-spine-operator-proof`
- `external-runtime-ref:capability-system-v1`
- `external-runtime-ref:addons-trust-policy`
- `external-runtime-ref:skill-import-trust-policy`
- `external-runtime-ref:contracts-durable`
- `external-runtime-ref:contracts-evidence`
- `external-runtime-ref:contracts-approvals`
- `external-runtime-ref:contracts-tool-catalog`
- `external-runtime-ref:contracts-memory`
- `external-runtime-ref:contracts-memory-write-gate`
- `external-runtime-ref:contracts-llm`
- `external-runtime-ref:contracts-capability-packs`
- `external-runtime-ref:contracts-runtime-decision-trace`

## Global Rules

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not modify historical release tags.
- Do not force-push.
- Do not import external runtime packages or copy implementation code.
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

## High-Maturity Coverage Contract

This program must cover the 16 AI-agent system components:

1. reasoning and task understanding
2. planning and orchestration
3. learning and adaptation
4. memory and context management
5. communication and interaction quality
6. action and tool calling
7. autonomy and authority management
8. code and implementation assistance
9. research, web, and external information handling
10. model and provider management
11. evidence, audit, and observability
12. safety, security, and failure handling
13. UX as an AI cockpit
14. CLI/API parity
15. extensibility and ecosystem
16. productized agent loop

The implementation coverage map is W1-W19:

- W1 proposal-heavy product loop
- W2 durable planning/orchestration gaps
- W3 memory retrieval/lifecycle utility gaps
- W4 partial operator cockpit UX
- W5 limited exact action/tool execution
- W6 weak Code Mode/code-assistance workflow
- W7 web/research evidence utility gaps
- W8 model/provider management partiality
- W9 missing signed portable receipts
- W10 extensibility/catalog maturity gaps
- W11 incomplete end-to-end Founder Loop
- W12 missing system-level agent evals
- W13 release/product-truth alignment gaps
- W14 browser action authority graduation
- W15 connector write authority graduation
- W16 managed shell/runtime command graduation
- W17 runtime model call graduation
- W18 production authority graduation
- W19 extension/plugin callable graduation

Borrow these GoatCitadel strengths only as UAA-native patterns: durable
orchestration, signed evidence receipts, operator cockpit UX, exact action/tool
lanes, Code Mode discipline, model/provider observability, governed memory
retrieval, and extension catalog clarity.

High-authority milestones are delegated to
`docs/prompts/authority_graduation_program/`:

- M1 Browser Authority maps to `01_web_evidence_lane.prompt.md` and
  `02_browser_lane.prompt.md`.
- M2 Connector Writes maps to `04_connector_read_lane.prompt.md`,
  `05_connector_write_send_lane.prompt.md`, and
  `12_credential_oauth_account_lane.prompt.md`.
- M3 Managed Shell maps to `06_local_shell_subprocess_lane.prompt.md`.
- M4 Runtime Model Calls maps to `03_provider_model_invocation_lane.prompt.md`.
- M5 Production Authority maps to `14_production_authority_lane.prompt.md`.
- M6 Extension/Plugin Callable Promotion maps to
  `15_extension_plugin_callable_lane.prompt.md`.

Broad browser action, connector writes, production authority, unrestricted
shell, runtime model calls, and plugin execution stay blocked unless a later
exact authority lane proves and grants the specific scoped capability.

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
   - unsupported parity claims against external comparison runtime.
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
- external comparison runtime patterns borrowed as UAA-native designs;
- external comparison runtime patterns explicitly not merged or not appropriate;
- authority still blocked;
- tests/verifiers run with pass/fail/blocker;
- hardening loops completed and faults fixed;
- remaining risks;
- current git status summary;
- recommended next exact prompt or PR lane.
