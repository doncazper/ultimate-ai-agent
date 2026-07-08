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

GoatCitadel patterns to borrow, adapted to UAA-native governance:

- durable orchestration with run records, steps, approval waits, retries,
  recovery state, timeline, and diagnostics;
- signed evidence receipts with canonical manifests, hashes, verification, and
  portable artifact refs;
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

| Phase | Components covered |
|---|---|
| 01 Reference gap truth | reasoning, evidence, product truth, eval targets |
| 02 Productized loop spine | productized agent loop, communication, UX cockpit |
| 03 Durable orchestration | planning/orchestration, recovery, observability |
| 04 Action/tool/code lanes | action/tool calling, Code Mode, authority |
| 05 Memory/learning/context | memory, learning/adaptation, context governance |
| 06 Evidence/audit | signed receipts, provenance, observability |
| 07 Model/provider/research | model/provider posture, web/external evidence |
| 08 Cockpit/CLI/API | UX cockpit, communication, CLI/API parity |
| 09 Extensibility/final hardening | extensibility, safety, product truth |

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

This bundle does not grant runtime model calls, provider SDK calls, live web
fetching, browser automation, connector writes, unrestricted shell/subprocess
execution, plugin runtime import, memory writes, context injection, remote
execution, public beta/release claims, production authority, or broad autonomy.

If a phase discovers that a GoatCitadel-style capability requires one of those
authorities, it must produce a no-go posture or an exact future authority
graduation prompt. It must not silently implement the authority.

## Authority Graduation Delegation

High-authority work is delegated to the existing
`docs/prompts/authority_graduation_program/` pack. The runtime-capability pack
may record posture, blockers, read models, and exact next prompts, but it must
not duplicate or bypass the authority lanes.

| Milestone | Runtime-capability posture | Executable authority prompt lane |
|---|---|---|
| M1 Browser Authority | Browser action remains blocked here; show read-only/observe/dry-run posture only. | `01_web_evidence_lane.prompt.md` and `02_browser_lane.prompt.md` |
| M2 Connector Writes | Connector writes remain blocked here; show read-only/draft/write-gate posture only. | `04_connector_read_lane.prompt.md`, `05_connector_write_send_lane.prompt.md`, and `12_credential_oauth_account_lane.prompt.md` |
| M3 Managed Shell | Unrestricted shell remains blocked here; show managed command profile posture only. | `06_local_shell_subprocess_lane.prompt.md` |
| M4 Runtime Model Calls | Runtime model calls remain blocked here; show readiness/routing/cost posture only. | `03_provider_model_invocation_lane.prompt.md` |
| M5 Production Authority | Production authority remains blocked here; show release blockers only. | `14_production_authority_lane.prompt.md` |
| M6 Extension/Plugin Callable Promotion | Plugin runtime import and callable promotion remain blocked here; show inspectable catalog posture only. | `15_extension_plugin_callable_lane.prompt.md` |

Broad browser action, connector writes, production authority, unrestricted
shell, runtime model calls, and plugin execution stay blocked unless a later
exact authority lane proves and grants the specific scoped capability.

## Verification

Validate the bundle:

```bash
.venv/bin/python scripts/verify_uaa_runtime_capability_foundation_prompt_pack.py
```

Run the focused unit test:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_runtime_capability_foundation_prompt_pack.py -q
```
