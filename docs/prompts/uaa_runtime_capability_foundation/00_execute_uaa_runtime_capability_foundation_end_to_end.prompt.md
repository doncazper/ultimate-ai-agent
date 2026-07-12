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
- Preserve the already implemented, exact WEB-HYBRID-001 through
  WEB-HYBRID-008 lanes: bounded SearXNG search, self-hosted Firecrawl one-page
  markdown extraction, free-plan Firecrawl Cloud one-page markdown extraction,
  and self-host-first routing with at most one separately authorized eligible
  cloud fallback through WebAccessGateway. Do not add any other live web fetch,
  browser action, authenticated browsing, provider SDK, connector write,
  unrestricted shell/subprocess, plugin runtime, remote execution, public
  beta/release, production authority, or broad autonomy.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI remain shells, not authority.
- Unknown authority is denied. Every executable capability must be exact,
  currently implemented, and eligible only for immediate request-scoped
  evaluation. An approval ref is an identifier only.
- Inside the final locked pre-start boundary, re-evaluate the PolicyEngine,
  exact LocalApprovalAuthority result, current AuthorityLease, capability and
  adapter, provider and target, mission and run, TTL and deadline, budget, kill
  switch, safe-disable, readiness, idempotency, and replay posture.
- Model output, memory, fetched content, UI state, orchestration state, and
  evidence refs never grant authority. Web content is untrusted evidence, never
  instruction authority.
- Product behavior must not live only in React state.
- CLI/API/core parity is required for operator-relevant mutation or durable
  state.
- Durable evidence must use safe refs and redacted summaries only.
- Every route change must update OpenAPI/API manifest checks and side-effect
  classification.
- Every UI addition must render backend-owned truth and avoid raw JSON as the
  primary operator workflow.
- If a capability is blocked, record its exact terminal classification only.
  Only the Phase 09 final deliverable may name at most one optional unactivated
  next program. Never generate or activate child prompts.

## Finite Mission And Endpoint

This program contains exactly ten merge-gated phases, Phase 00 through Phase
09, followed by at most two focused final repair passes. Pack hardening and the
truth/benchmark baseline are the same Phase 00 branch and PR; they are not an
extra phase.

The program ends after Phase 09 and the bounded repair passes when every
intentional PR is merged into a clean pushed `main`, or when a required hosted
facility remains `external_blocked` after the bounded retry rule. Missing score
targets are reported honestly and do not create more phases. Do not
automatically continue into another program. Stop at the finite endpoint.

## Preservation Contract

Every phase must preserve and regression-test:

- WebAccessGateway and the exact bounded SearXNG lane;
- self-hosted Firecrawl one-page markdown extraction;
- free-plan Firecrawl Cloud with serialized budget and credit reconciliation;
- self-host-first hybrid routing with at most one eligible cloud fallback;
- local web-service packaging and WEB-HYBRID CLI/API/Control Center truth;
- local web-service configuration, the WEB-HYBRID activation prompt, and the
  WEB-HYBRID implementation plan;
- the TypeScript 7 exact stable pin;
- pytest sharding, deterministic seeds, isolated basetemps, timing profiles,
  and test-performance refactors;
- verifier-maintainability refactors and extracted runtime CLI modules;
- mission failure management, approval waits, retries, dead letters, and
  cancellation fences; and
- bounded deterministic SSE progress-preview replay without live-streaming
  claims.

Deleting or replacing preserved work requires equal-or-stronger implementation
proof in the same phase. Preservation does not grandfather a stale or unsafe
preflight decision as satisfying current request-scoped authority.

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
- W9 missing portable tamper-aware/hash-chain receipts
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
orchestration, tamper-aware evidence receipts, operator cockpit UX, exact action/tool
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
shell, runtime model calls beyond separately accepted exact lanes, and plugin
execution stay blocked unless a later exact authority lane proves and grants
the specific scoped capability.

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

## Finite Phase Program

### Phase 00 — Pack Hardening, Truth Baseline, And Benchmark Harness

Harden this canonical pack, record the current 16-component scorecard, capture
verification timings, and add or refresh a deterministic redacted benchmark.

### Phase 01 — Reasoning And Task Understanding

Implement backend-owned intent assessment and immutable plan-revision truth
covering facts, assumptions, unknowns, ambiguity, confidence, and evidence.

### Phase 02 — Productized Founder Loop And Mission Completion

Complete one bounded input-to-receipt-to-memory-candidate workflow and finish
mission-wide budget settlement plus completion evidence.

### Phase 03 — Memory, Learning, And Governed Context

Harden provenance-bound retrieval, context manifests, corrections, staleness,
feedback, review, and context budgets without hidden injection.

### Phase 04 — Useful Exact Tool And Code Lanes

Promote only individually proven repository tools and sealed-sandbox work. Keep
CodeAct execution blocked if a real sandbox cannot prove isolation.

### Phase 05 — Web Research And Provider Observability

Build on the exact WEB-HYBRID lanes, harden final-start revalidation, add cited
bounded research aggregation, and improve provider readiness/cost/latency truth.

### Phase 06 — Portable Evidence And Observability

Unify content-free receipts, hash chains, offline verification, and readable
timelines. Add asymmetric signing only with a proven Keychain-backed lifecycle.

### Phase 07 — Extensibility Ecosystem

Mature inspectable catalogs and developer validation while keeping runtime
import and callability denied unless one isolated exact lane proves every gate.

### Phase 08 — macOS Cockpit And CLI/API Parity

Expose one backend-owned operator truth across macOS-first Control Center,
human-readable CLI, API, OpenAPI, and route classification.

### Phase 09 — Benchmark, Bounded Gap Closure, And Stop

Run the twelve accepted scenarios, allow at most two focused repair passes,
re-score honestly, classify remaining blockers, clean the repository, and stop.

## Execution Loop

For each phase:

1. Inspect the exact branch, SHA, remotes, tags, status, worktrees, open PRs,
   staged files, and overlapping branches.
2. Preserve unrelated work. Never reset, revert, clean, stash, or overwrite it.
3. Use one isolated `codex/capability-maturity-XX` branch and worktree.
4. Search for existing UAA implementation before editing and classify each
   capability as `implemented`, `partial`, `planned`, `mock-only`, `blocked`,
   `deprecated`, `contradicted`, or `unknown`.
5. Implement only the smallest UAA-native slice that the phase authorizes and
   stage intentional files only.
6. Add focused tests, verifiers, docs, and release-truth updates.
7. Run focused and affected regression gates.
8. Use read-only subagents for design, security, test, and final-diff audits.
9. Review and fix the diff adversarially for:
   - authority creep;
   - UI-only truth;
   - raw prompt, response, provider payload, path, log, or secret persistence;
   - route/API manifest drift;
   - missing CLI parity;
   - missing approval scope validation;
   - missing idempotency, replay, rollback, or safe-disable posture;
   - product-language overclaims;
   - unsupported parity claims against external comparison runtime.
10. Commit, push, and open one scoped PR.
11. Monitor hosted CI and actionable review feedback; fix and repeat until
    green.
12. If hosted CI fails before starting because of capacity, wait three minutes
    and rerun once. If it is still unavailable, record `external_blocked`, keep
    the PR clean and pushed, do not claim CI is green, and stop the program.
13. Do not merge around a CI outage unless the same invocation explicitly
    authorizes that exact exception.
14. Merge only when required evidence is green.
15. Fast-forward local `main`, verify the exact merge SHA, and push verified
    `main`.
16. Delete only clean, merged temporary branches and worktrees.
17. Confirm `main` is clean before the next phase.

Never force-push or mutate historical tags. Git operations, hosted CI, PR
merges, and local verification are development actions; they do not grant UAA
runtime or production authority.

Do not use paid CI, provider, review, or marketplace services. Keep the
Communication Center and Conversation Vault (`FCC-COMMS`) outside this finite
program.

## Score Targets

Scores are measurement gates, never claim generators or continuation triggers:

- normalized overall score at least 82/100;
- stretch score 86/100 only when evidence supports it;
- authority, safety, and evidence at least 9.0;
- planning and CLI/API parity at least 8.5;
- product loop, tools, web, provider, memory, and UX at least 8.0;
- reasoning, code, and extensibility at least 7.5; and
- learning at least 7.0.

Never increase a score without code, tests, and operator-visible evidence.
Unsafe or externally blocked targets remain honestly blocked and do not make
the program recursive.

## Final Benchmark Scenarios

Phase 09 must run exactly these twelve repeatable scenarios:

1. ambiguous intent;
2. plan revision;
3. DAG replay and crash;
4. approval expiry;
5. cancellation race;
6. budget exhaustion and settlement;
7. exact tool idempotency;
8. sandbox escape denial;
9. memory correction;
10. web citation and injection handling;
11. unavailable or stale provider; and
12. receipt tamper plus UI/CLI/API parity.

## Final Verification

Run focused tests for changed files plus the relevant subset of:

```bash
git diff --check
.venv/bin/python -m ruff check .
make test-sharded
.venv/bin/python scripts/verify_verifier_maintainability.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_security_redaction_artifacts.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
make frontend-check
make frontend-visual-check
PYTHONPATH=src .venv/bin/python scripts/verify_web_hybrid_contracts.py
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
- before/after component scores with evidence and confidence;
- final open-PR, branch, remote, worktree, and clean-status audit;
- exact pushed `main` SHA; and
- at most one optional next program that is not automatically activated, named
  only by the Phase 09 final deliverable.

For every phase also report its commit, branch, PR, hosted CI, merge, and
post-merge result; commands, test counts, timings, and blockers; unsupported or
external adapters; and the terminal classification for every unresolved item:
`blocked`, `unsupported`, `adapter required`, `configuration required`,
`external facility required`, or `deferred by authority policy`.

Do not automatically continue into the optional next program. Stop at the
finite endpoint.
