# UAA Runtime Capability Foundation Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: make this the canonical high-maturity UAA agent-platform prompt
program while preserving UAA's contract-first Python Agent Core, local-first
authority model, redacted evidence posture, CLI/API parity, and Founder
Command Center product spine.

This pack incorporates the UAA vs GoatCitadel comparison as a high-maturity
coverage target. GoatCitadel is a reference for product and architecture
patterns only, not a dependency to import, runtime to adopt, or authority model
to copy. The operator running the pack must prove each UAA capability with UAA
code, tests, route contracts, CLI/API surfaces, Control Center UX, redacted
evidence, and product-language truth.

## Wrapper Command

From the repo root:

```bash
bash scripts/dev/run_uaa_runtime_capability_foundation_prompt_pack.sh
```

Dry-run and emit the combined prompt without invoking Codex:

```bash
bash scripts/dev/run_uaa_runtime_capability_foundation_prompt_pack.sh --dry-run
```

Emit a reviewable combined prompt to a chosen path:

```bash
bash scripts/dev/run_uaa_runtime_capability_foundation_prompt_pack.sh --dry-run --output /tmp/uaa-runtime-capability-foundation.md
```

## Prompt Order

1. `00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md`
2. `01_reference_gap_truth_and_age_adjusted_scoreboard.prompt.md`
3. `02_productized_agent_loop_spine.prompt.md`
4. `03_durable_orchestration_progress_and_recovery.prompt.md`
5. `04_action_tool_code_lanes_and_approval_receipts.prompt.md`
6. `05_memory_learning_context_and_feedback.prompt.md`
7. `06_evidence_audit_receipts_and_observability.prompt.md`
8. `07_model_provider_research_and_external_info_posture.prompt.md`
9. `08_cockpit_cli_api_parity_and_operator_ux.prompt.md`
10. `09_extensibility_ecosystem_and_final_hardening.prompt.md`

Use `00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md` when the
operator wants a single orchestrated run. The wrapper sends that prompt to
Codex after validating the bundle hash and file list.

## Finite Completion Contract

The pack is exactly ten merge-gated phases, Phase 00 through Phase 09. Phase 00
combines pack hardening with the truth/benchmark baseline. Phase 09 permits at
most two focused repair passes, then the program stops with an honest scorecard
and remaining blockers. Missing score targets do not create new phases or
recursive prompts.

Each phase uses one isolated `codex/capability-maturity-XX` branch/worktree,
focused verification, read-only subagent audits, one PR, hosted CI, post-merge
verification, and clean merged-branch/worktree removal. A hosted CI capacity
failure is retried once after three minutes; if it still cannot start, the
phase is `external_blocked` and is not mislabeled green.

## Preservation Contract

Every phase preserves WebAccessGateway, exact SearXNG search, self-hosted
Firecrawl markdown, free-plan Firecrawl Cloud, self-host-first single eligible
fallback, cloud budget serialization/reconciliation, local web-service
packaging, WEB-HYBRID CLI/API/Control Center truth, the TypeScript 7 exact pin,
local web-service configuration, the WEB-HYBRID activation prompt and
implementation plan,
pytest sharding/timing/seed/basetemp work, verifier/runtime CLI refactors,
mission failure management, and bounded SSE preview replay. Replacement
requires equal-or-stronger proof in the same phase.

## Catch-Up Target

The pack aims to make UAA stronger in the areas where GoatCitadel or other
agent/operator systems have a more operator-visible product shape:

- Mission Control-style cockpit clarity;
- durable run lifecycle, checkpoints, progress, resume, and recovery;
- action/tool/code execution lanes with approval, receipts, hashes, and
  reviewability;
- memory lifecycle with review, feedback, quality, provenance, and correction;
- evidence receipts and audit surfaces that operators can inspect;
- model/provider/catalog posture with cost and readiness literacy;
- inspectable extension/capability catalogs with activation boundaries;
- benchmark and release-proof habits.

## High-Maturity Coverage Contract

Every run of this pack must keep the 16 AI-agent system components visible:

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

The W1-W19 weakness map is the required coverage queue:

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

GoatCitadel patterns to borrow, adapted to UAA-native governance:

- durable orchestration with run records, steps, approval waits, retries,
  recovery state, timeline, and diagnostics;
- tamper-aware evidence receipts with canonical manifests, local SHA-256 hash
  verification, and portable artifact refs; asymmetric signing remains blocked
  until a real Keychain-backed lifecycle is proven;
- operator cockpit UX with readable activity rows, approval cards, evidence
  receipts, and blocked-state explanations;
- exact action/tool lanes with central catalogs, policy decisions, idempotency,
  dry-run or preview posture, and receipts;
- Code Mode discipline with proposal artifacts, hashes, validation plans,
  stdout/stderr previews, and one-time approvals;
- model/provider observability with readiness, cost/context metadata, routing
  evidence, and no model-output authority;
- governed memory retrieval with lexical scoring, recency, provenance,
  citations, staleness, conflict handling, and review decisions;
- extensibility catalog clarity that separates inspectable assets from callable
  authority and keeps imports disabled by default.

Phase-to-component coverage:

The numbered filenames are legacy-stable repository paths. Their H1 titles and
the mapping below are the authoritative finite phase semantics; the verifier
binds each legacy path to its current phase contract.

| Phase | Components covered |
|---|---|
| 00 Pack/baseline | finite pack integrity, benchmark truth, timings, gap ownership |
| 01 Reasoning/task understanding | intent, facts/assumptions/unknowns, immutable revisions |
| 02 Founder Loop/mission completion | planning, authority, budgets, productized loop |
| 03 Memory/learning/context | memory, learning/adaptation, context governance |
| 04 Exact tool/code lanes | action/tool calling, code proposals, sandbox proof posture |
| 05 Web/provider observability | governed research, WEB-HYBRID, provider truth |
| 06 Portable evidence | tamper-aware/hash-chain receipts, provenance, observability |
| 07 Extensibility ecosystem | catalogs, compatibility, validation, blocked callability |
| 08 macOS cockpit/CLI/API | UX cockpit, communication, CLI/API parity |
| 09 Benchmark/gap closure/stop | twelve scenarios, bounded repair, final score and hygiene |

The pack also protects UAA's current strengths:

- Python Agent Core remains the brain;
- Control Center remains a shell, not authority;
- policy, approval, route classification, OpenAPI, and Foundation Gate checks
  stay hard boundaries;
- no broad autonomy or production authority is inferred from UI, docs, or
  prompt execution;
- every mutation lane remains exact-scoped, approval-bound, idempotent,
  auditable, rollback-aware, redacted, and tested.

## Authority Boundary

This bundle preserves the already implemented exact WEB-HYBRID-001 through
WEB-HYBRID-008 lanes: bounded SearXNG search, self-hosted Firecrawl one-page
markdown extraction, free-plan Firecrawl Cloud one-page markdown extraction,
and self-host-first routing with at most one separately authorized eligible
cloud fallback through WebAccessGateway. Those lanes are read-only evidence
operations; external content remains untrusted and grants no authority.

The bundle grants no other live web fetching, browser automation, auth/cookies,
downloads/uploads, arbitrary external POST/PUT/PATCH/DELETE, connector writes,
unrestricted shell/subprocess execution, provider SDK authority, plugin runtime
import, hidden context injection, remote execution, public beta/release claims,
production authority, or broad autonomy.

If a phase discovers that a GoatCitadel-style capability requires one of those
authorities, it records only a terminal no-go or blocked classification. Only
the Phase 09 final deliverable may name at most one optional unactivated next
program. It must not silently implement the authority or activate another
prompt pack.

## Measurement Targets

The evidence targets are overall 82/100, authority/safety/evidence 9.0,
planning and CLI/API parity 8.5, product loop/tools/web/provider/memory/UX 8.0,
reasoning/code/extensibility 7.5, and learning 7.0. A stretch score of 86/100
may be reported only when code, tests, runtime proof, and operator visibility
support it. Scores never mint product truth or prolong the finite program.

## Authority Graduation Delegation

High-authority work is delegated to the existing
`docs/prompts/authority_graduation_program/` pack. The runtime-capability pack
may record posture, blockers, read models, terminal classifications, and refs
to existing lanes, but it must not generate prompts, duplicate authority, or
bypass the authority lanes.

| Milestone | Runtime-capability posture | Executable authority prompt lane |
|---|---|---|
| M1 Browser Authority | Exact SearXNG/Firecrawl read-only evidence remains implemented; browser observe/action beyond those lanes stays blocked here. | `01_web_evidence_lane.prompt.md` and `02_browser_lane.prompt.md` |
| M2 Connector Writes | Connector writes remain blocked here; show read-only/draft/write-gate posture only. | `04_connector_read_lane.prompt.md`, `05_connector_write_send_lane.prompt.md`, and `12_credential_oauth_account_lane.prompt.md` |
| M3 Managed Shell | Unrestricted shell remains blocked here; show managed command profile posture only. | `06_local_shell_subprocess_lane.prompt.md` |
| M4 Runtime Model Calls | Exact separately accepted local/provider lanes may be regression-tested; every broader runtime model/provider lane remains blocked here. | `03_provider_model_invocation_lane.prompt.md` |
| M5 Production Authority | Production authority remains blocked here; show release blockers only. | `14_production_authority_lane.prompt.md` |
| M6 Extension/Plugin Callable Promotion | Plugin runtime import and callable promotion remain blocked here; show inspectable catalog posture only. | `15_extension_plugin_callable_lane.prompt.md` |

Broad browser action, connector writes, production authority, unrestricted
shell, runtime model calls beyond separately accepted exact lanes, and plugin
execution stay blocked unless a later exact authority lane proves and grants
the specific scoped capability.

## Verification

Validate the bundle:

```bash
.venv/bin/python scripts/verify_uaa_runtime_capability_foundation_prompt_pack.py
```

Run the focused unit test:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_runtime_capability_foundation_prompt_pack.py -q
```
