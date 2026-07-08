# UAA Runtime Capability Scoreboard

Status: Phase 10 High-Maturity Agent Spine coverage. This document remains
documentation and verifier coverage only; runtime product truth is now also
projected through the backend-owned
`GET /control-center/agent-loop/thread#high_maturity_spine_readiness` read
model and `scripts/dev/uaa_founder_loop.py inspect-high-maturity-spine`.
It is not runtime authority and does not grant execution authority.

Baseline: UAA v0.104.0 / package 0.104.0. external comparison runtime is used as a read-only reference comparator for product and architecture patterns. This report is not copied from external runtime references, does not import external runtime packages, and does not adopt external comparison runtime authority assumptions.

## Snapshot

| System | Repo Snapshot | Runtime Shape | Main Operator Surfaces | Current Truth Posture |
|---|---|---|---|---|
| UAA | Active baseline v0.104.0/package 0.104.0 on current mainline source truth. | Python Agent Core, FastAPI API boundary, React/TypeScript Control Center shell, repo-local CLI/verifier scripts. | Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, Settings, Runtime, local model status, CRM, Coding Cockpit, Work Board, Agent Loop Thread, and High-Maturity Agent Spine coverage. | Strong governance, redaction, OpenAPI/manifest checks, proof/evidence refs, CLI/API parity, and a backend-owned W1-W13 high-maturity coverage projection. Product loop is useful but still partial for exact execution lanes. |
| external comparison runtime | Branch `codex/mac-desktop-e2e-hardening`, commit `89c03cc5`, README release line `0.1.0-rc.1`; sibling worktree has an unrelated local report. | TypeScript monorepo, Fastify gateway runtime, Mission Control Next shell, shared contract packages. | Work surface with Chat/Cowork/Code, Projects, Library/Capabilities, Ops/Runtime, Settings/Providers. | Broader product cockpit and runtime-operation story, including durable run claims, signed evidence, capability catalogs, model/provider surfaces, and code mode. Treat docs/contracts as evidence, not proof of UAA readiness. |

## Source Files Inspected

UAA evidence inspected:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`
- `src/ultimate_ai_agent/api/founder_loop.py`
- `src/ultimate_ai_agent/api/app.py`
- `src/ultimate_ai_agent/api/routes/runtime_pilot_service.py`
- `src/ultimate_ai_agent/core/control_center/action_tool_code_catalog.py`
- `src/ultimate_ai_agent/core/control_center/agent_loop.py`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/runtime_gateway/__init__.py`
- `tests/test_api_manifest.py`
- `tests/test_control_center_api_routes.py`
- `tests/test_runtime_action_tool_code_lanes.py`
- `tests/test_runtime_memory_learning.py`
- `tests/test_runtime_evidence_audit.py`
- `tests/test_runtime_agent_loop_spine.py`
- `scripts/verify_uaa_runtime_cockpit_cli_api.py`
- `scripts/verify_uaa_runtime_extensibility_final.py`
- `scripts/dev/uaa_extensions.py`
- `src/ultimate_ai_agent/core/extension_catalog/contracts.py`
- `src/ultimate_ai_agent/core/extension_catalog/install_disabled.py`
- `src/ultimate_ai_agent/core/extension_catalog/runtime.py`
- `docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md`
- `scripts/verify_uaa_runtime_action_tool_code_lanes.py`
- `scripts/verify_uaa_runtime_memory_learning.py`
- `scripts/verify_uaa_runtime_evidence_audit.py`
- `scripts/verify_uaa_runtime_capability_foundation_prompt_pack.py`
- `docs/prompts/uaa_runtime_capability_foundation/`

External runtime read-only evidence inspected:

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

Status labels used in this report: implemented, partial, planned, mock-only,
blocked, deprecated, contradicted, unknown.

## Component Scoreboard

Scores are 0-10 and reflect system-level AI-agent capability evidence, not raw
model intelligence. Code and tests are weighted above roadmap claims.

| Component | UAA Score | UAA Status | external comparison runtime Score | external comparison runtime Status | Current Winner | Key Evidence | Main UAA Catch-Up Gap |
|---|---:|---|---:|---|---|---|---|
| Reasoning and task understanding | 6 | partial | 8 | implemented | external comparison runtime | UAA has chat handoff, intent/readiness surfaces, proof refs, and strict model-output-not-authority language. external comparison runtime documents auto Chat/Cowork/Code routing, route-decision visibility, planner skip paths, and decision traces. | Make UAA turn contracts and answer-preservation/router outputs operator-visible and tied to run/proof refs. |
| Planning and orchestration | 6 | partial | 8 | implemented | external comparison runtime | UAA has durable run contracts, task decomposition, Action Inbox approvals, and local receipts. external comparison runtime documents durable mission sessions, checkpoints, retries, approval waits, dead letters, and fan-out. | Add richer durable progress/recovery read models before any broader execution authority. |
| Learning and adaptation | 7 | implemented | 7 | partial | Tie | UAA has reviewed memory decisions, L1/L2/L3 indexes, context-pack proposal lanes, memory quality issues, memory-to-loop binding, and Phase 05 backend-owned learning posture with lifecycle counts, feedback/correction/rejection/forget-request posture, provenance, and blocked-authority refs. external comparison runtime contracts expose memory retrieval, action ledgers, freshness, feedback, and memory-write gates. | Add automatic write/injection/delete/export lanes only through exact scoped milestones; keep memory as recall and reviewable context. |
| Memory and context management | 7 | implemented | 7 | partial | Tie | UAA has governed recall-only memory with provenance, review receipts, safe refs, and redaction. external comparison runtime has broader structured memory contracts and model/provider metadata. | Improve freshness/conflict/operator correction surfaces while preserving recall-only authority. |
| Communication and interaction quality | 6 | partial | 8 | implemented | external comparison runtime | UAA Control Center communicates blocked states and proof refs but remains spread across many modules. external comparison runtime README shows a unified Work/Projects/Library/Ops/Settings cockpit. | Make the UAA loop feel like one cockpit instead of a set of partial panels. |
| Action and tool calling | 6 | partial | 8 | implemented | external comparison runtime | UAA has exact Action Inbox decisions, one approved local-task lane, CRM local mutation receipts, and blocked generic execution. external comparison runtime shows capability/tool catalogs, policy-gated invocation, approvals, and code-mode receipts. | Add inspectable/callable catalog separation and richer action proposals while keeping generic tool execution blocked. |
| Autonomy and authority management | 9 | implemented | 8 | implemented | UAA | UAA AGENTS, Security, LocalApprovalAuthority, PolicyEngine, route classification, OpenAPI checks, and product-language rules keep broad authority denied. external comparison runtime has external scoped grants and scoped grants but exposes broader runtime claims. | Preserve UAA's narrower authority model while improving operator usefulness. |
| Code and implementation assistance | 6 | partial | 8 | implemented | external comparison runtime | UAA has Coding Cockpit shell, workspace workbench contracts, patch proposals/apply receipts in product truth, and blocked shell authority. external comparison runtime has Code Mode v1 contracts, hashes, approval, artifact refs, and sandbox posture. | Make UAA code proposals, diffs, receipts, and test lanes more coherent before broader command authority. |
| Research, web, and external information handling | 5 | partial | 7 | partial | external comparison runtime | UAA has WebAccessGateway guardrails and one allowlisted web evidence preview lane. external comparison runtime has provider/research and browser/evidence posture in docs/contracts. | Keep UAA web evidence read-only and gateway-owned; do not enable browser action or unrestricted web fetching without a separate AuthorityLease-gated capability. |
| Model/provider management | 5 | partial | 8 | implemented | external comparison runtime | UAA has local model status/readiness, RuntimeGateway pilot contracts, and blocked provider/model authority. external comparison runtime has provider catalog, local llama.cpp posture, model discovery, provider summaries, and model-router trace contracts. | Add metadata, secret-status, cost/readiness, and route-decision traces without live provider/model calls. |
| Evidence, audit, and observability | 8 | implemented | 9 | implemented | external comparison runtime | UAA has Evidence Timeline, receipts, redaction, proof refs, route/API/verifier evidence, debug logging posture, and Phase 06 backend-owned evidence audit receipt spine with grouped lineage, artifact hash refs, verifier refs, missing receipt refs, and CLI parity. external comparison runtime claims signed offline-verifiable evidence and compliance bundles. | Add later signed portable evidence export/verification only through scoped local evidence milestones; no production compliance claims yet. |
| Safety, security, and failure handling | 9 | implemented | 8 | implemented | UAA | UAA strongly blocks raw payload persistence, broad runtime authority, provider SDK calls, browser automation, shell execution, connector writes, and production claims. external comparison runtime has broad governance but more active runtime surface area. | Keep strict deny-by-default while introducing exact lanes only with rollback/safe-disable and receipts. |
| UX as an AI cockpit | 6 | partial | 9 | implemented | external comparison runtime | UAA has many backend-owned surfaces but still feels modular. external comparison runtime presents one Work cockpit with Library/Ops/Settings and visual proof. | Productize UAA's Today/Actions/Chat/Proof/Evidence/Memory/Coding/Work Board into one flow. |
| CLI/API parity | 8 | implemented | 7 | partial | UAA | UAA treats CLI and OpenAPI as first-class truth, with `/api/manifest` and verifier-backed route metadata. external comparison runtime has gateway APIs and contracts but less evidence here from inspected files. | Keep parity as UAA's differentiator while adding cockpit read models. |
| Extensibility and ecosystem | 7 | partial | 8 | implemented | external comparison runtime | UAA has inspectable extension catalog, trust manifests, activation/revocation records, Phase 09 operator posture fields, disabled-install posture with AuthorityLease/approval/receipt/hash refs, CLI inspection, blocked reasons, safe adoption posture, and runtime import blocked. external comparison runtime has capability packs, add-on policy, skill import trust, and MCP/tool scoping claims. | Persist a disabled local install record only after exact AuthorityLease + LocalApprovalAuthority + idempotency proof; add one exact callable capability lane only after scoped authority exists. |
| Productized agent loop | 6 | partial | 9 | implemented | external comparison runtime | UAA has a governed Founder Loop across Start, Today, Actions, Proof, Evidence, Memory, and Trust, but many lanes remain partial. external comparison runtime presents a broader input-to-plan-to-action-to-evidence-to-memory loop. | Make the UAA agent loop legible end to end with backend-owned run state and proof details. |

## Age-Adjusted Interpretation

UAA is younger and more conservative in active runtime authority. That is a
strength where operator trust matters: UAA's policy boundaries, route inventory,
OpenAPI checks, product-language rules, redaction posture, and CLI/API parity
are stricter than the broader product claims visible in external comparison runtime's docs.

The external comparison runtime is ahead where an older or broader product surface matters:
unified Work/Cowork/Code cockpit, external domain model, durable execution
visibility, signed evidence claims, capability catalog, provider/model control
surfaces, and Code Mode productization. Those are catch-up targets for UAA, not
authority shortcuts.

The catch-up path should stay UAA-native: add backend-owned read models,
scorecards, verifiers, proof details, run lineage, catalog separation, and
operator-visible statuses first. Capabilities that require runtime model calls,
provider SDK calls, live web fetching, browser automation, connector writes,
unrestricted shell/subprocess execution, plugin runtime import, memory-write
authority, remote execution, public release claims, production authority, or
broad autonomy remain blocked until a later exact-scoped milestone proves
approval binding, idempotency, redaction, rollback/safe-disable, receipts,
tests, and CLI/API/core parity.

## Ranked Catch-Up Backlog

| Rank | Gap | Target Status | Owner Surface | Route/API/CLI/UI Impact | Authority Needed Or Blocked | Tests And Verifiers Required | First Safe PR Lane |
|---:|---|---|---|---|---|---|---|
| 1 | Productized agent loop spine across chat, actions, proof, evidence, memory, and trust. | implemented read-model | Python Core plus Control Center read models | `GET /control-center/agent-loop/thread`, `scripts/dev/uaa_founder_loop.py inspect-agent-loop`, and Today UI render the backend-owned thread. | No new runtime authority. | `tests/test_runtime_agent_loop_spine.py`, route/API manifest checks, product truth, docs integrity. | Phase 02 implemented: Agent Loop Spine |
| 2 | Durable orchestration progress, recovery, cancellation, retry, blocked, and dead-letter visibility. | implemented read-model | Python execution core | `GET /control-center/runs/observability`, CLI inspect, Control Center Evidence run panel. | Background autonomy, queue workers, retry/resume/cancel execution blocked. | `tests/test_run_observability_surface.py`, durable lifecycle tests, Phase 03 verifier. | Phase 03: Durable Orchestration |
| 3 | Action/tool/code lane catalog with inspectable/callable separation. | implemented read-model | Python tool/action/catalog core | Catalog read models, proposal posture, receipt refs, CLI inspection, and Action Inbox UI panel; no generic execution. | Unrestricted shell/subprocess execution, generic tool execution, plugin runtime import, connector writes, provider/model calls, browser automation, and broad autonomy blocked. | `tests/test_runtime_action_tool_code_lanes.py`, `scripts/verify_uaa_runtime_action_tool_code_lanes.py`, catalog verifier, approval/receipt tests, product-language tests. | Phase 04 implemented: Action/Tool/Code Lanes |
| 4 | Memory learning lifecycle with feedback, stale/wrong/conflict/duplicate states. | implemented read-model | Python memory core | Memory Workbench learning posture, CLI `memory-learning-posture`, Control Center Memory panel. | Broad memory-write authority, automatic memory writes, hidden context injection, memory-as-truth, delete/export execution, connector writes, model/provider calls, live web fetch, background autonomy, and production authority blocked. | `tests/test_runtime_memory_learning.py`, `scripts/verify_uaa_runtime_memory_learning.py`, memory provenance and redaction tests. | Phase 05 implemented: Memory/Learning |
| 5 | Signed portable evidence and same-run lineage detail. | implemented read-model | Evidence/proof core | Evidence audit receipt spine, grouped timeline/read-model, receipt envelopes, missing receipt refs, artifact hash refs, verifier refs, CLI inspection. | External telemetry/export and production compliance claims blocked. | `tests/test_runtime_evidence_audit.py`, `scripts/verify_uaa_runtime_evidence_audit.py`, redaction and missing receipt tests. | Phase 06 implemented: Evidence/Audit |
| 6 | Model/provider/research metadata parity. | implemented read-model | RuntimeGateway/local model core | Provider readiness/catalog metadata, route-decision trace read models, model-output truth posture, and WebAccessGateway external-information posture. | Runtime model calls, provider SDK calls, browser automation, and live web fetching by the control plane blocked. | `tests/test_runtime_model_provider_research.py`, `scripts/verify_uaa_runtime_model_provider_research.py`, runtime metadata tests and authority guard verifier. | Phase 07 implemented: Model/Provider/Research |
| 7 | Cockpit UX parity for Today/Actions/Chat/Proof/Evidence/Memory/Runtime/Coding/Work Board. | implemented read-model/UI parity | Control Center presentation over Python truth | `GET /control-center/agent-loop/thread`, `scripts/dev/uaa_founder_loop.py inspect-cockpit-parity`, and Today UI expose the same backend-owned operator decision matrix. | Browser automation inside UAA blocked; mutation controls stay exact-lane only. | `tests/test_runtime_agent_loop_spine.py`, `apps/control-center/src/App.test.tsx`, `scripts/verify_uaa_runtime_cockpit_cli_api.py`, frontend checks. | Phase 08 implemented: Cockpit/CLI/API |
| 8 | Extension ecosystem clarity. | implemented read-model/CLI hardening | Extension catalog core | Inspectable catalog, grant records, trust statuses, callable posture, required grant refs, blocked reasons, review evidence refs, safe adoption posture, disabled-install posture, and CLI inspection. | Connector writes, callable catalog, plugin package install persistence, plugin runtime import, remote execution, public release claims, production authority, and broad autonomy blocked. | `tests/test_runtime_extensibility_final.py`, `tests/test_inspectable_extension_catalog.py`, `scripts/verify_uaa_runtime_extensibility_final.py`, documentation/product truth/verifier gates. | Phase 09 implemented: Extensibility Final plus install-disabled posture |

## External Runtime Patterns Borrowed As UAA-Native Designs

- Unified Work/Cowork/Code inspiration becomes a UAA-owned loop thread/read
  model; it must not become a second runtime or a React-only product truth.
- Inspectable catalog versus callable catalog separation becomes a UAA catalog
  posture so discovery does not imply execution authority.
- Same-run same-truth lineage becomes a Proof/Run Detail requirement across
  Actions, Evidence, Memory, Runtime, Coding, and Work Board.
- Durable status taxonomy becomes a read-model target for queued, running,
  approval-wait, blocked, retrying, cancelled, failed, completed, and
  dead-lettered local run states.
- Evidence envelope and verification concepts become UAA portable evidence
  contracts with safe refs, hashes, policy decision, approval refs, and
  verifier version.
- Memory write gates become reviewed/proposed/blocked memory lifecycle
  language; memory remains recall, not truth or authority.
- Provider catalog and model-router traces become metadata and decision-trace
  read models before any live model/provider execution is considered.

## External Runtime Patterns Not Merged

- external runtime code, packages, schemas, and implementation files are not copied.
- The external domain model is not adopted as a UAA product object in this phase.
- Fastify gateway architecture is not adopted; UAA remains Python Agent Core
  plus FastAPI boundary and Control Center shell.
- Broad agent fan-out, background worker execution, and autonomous high-risk
  activation are not merged.
- Code Mode execution, Docker/Aider execution, shell execution, and workspace
  mutation authority are not merged.
- Provider SDK execution, live model routing, and external provider calls are
  not merged.
- Browser automation, connector sends/writes, MCP runtime import, plugin
  runtime import, and external sync are not merged.
- Public release, production authority, signed installer, or compliance-bundle
  claims are not imported from external comparison runtime.

## Blocked Authority Preserved

The following remain blocked unless a later exact-scoped AuthorityLease
capability explicitly implements them with tests, redaction, approval binding,
rollback/safe-disable, idempotency, receipts, CLI/API/core parity, and
product-language updates:

- runtime model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes
- unrestricted shell/subprocess execution
- plugin runtime import
- memory-write authority
- remote execution
- public release claims
- production authority
- broad autonomy

Additional blocked or constrained states remain visible: raw prompt content,
raw response content, raw provider payload content, raw local path content, raw
log content, account material, credential material, hidden context injection,
and model/provider output as authority.

## Phase 02 Evidence

Phase 02 is implemented as a repo-safe read-model slice. It adds
`docs/control_center/UAA_RUNTIME_AGENT_LOOP_SPINE.md`, Python Core
contract `contract-ref:runtime-agent-loop-thread:v1`, API route
`GET /control-center/agent-loop/thread`, CLI command
`scripts/dev/uaa_founder_loop.py inspect-agent-loop`, Control Center Today
rendering, and focused tests. Runtime model calls, provider SDK calls, live web
fetching, browser automation, connector writes, unrestricted shell/subprocess
execution, plugin runtime import, background autonomy, and production authority
remain blocked.

## Phase 03 Evidence

Phase 03 is implemented as a repo-safe durable orchestration read-model
hardening slice. It adds
`docs/control_center/UAA_RUNTIME_DURABLE_ORCHESTRATION.md`,
first-class Run Observability fields for current phase/step, checkpoint
summaries, retry/recovery posture, approval wait state,
cancellation/dead-letter state, and redacted error summaries. The existing
API route `GET /control-center/runs/observability`, CLI command
`python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run-observability`,
and Control Center Evidence panel remain read-only, backend-owned, and
safe-ref-only. Cancel, resume, retry, recovery, dead-letter execution, live
streaming, background workers, schedulers, provider/model calls, tool
execution, connector writes/sends, browser automation, unrestricted
shell/subprocess execution, and production authority remain blocked.

## Phase 04 Evidence

Phase 04 is implemented as a repo-safe action/tool/code lane catalog read-model
slice. It adds
`docs/control_center/UAA_RUNTIME_ACTION_TOOL_CODE_LANES.md`,
Python Core contract
`contract-ref:runtime-action-tool-code-catalog:v1`, Action Inbox
embedding through `GET /control-center/actions/inbox`, CLI command
`scripts/dev/uaa_founder_loop.py inspect-action-tool-code-catalog`, Control
Center Action Inbox rendering, and focused tests/verifier coverage.

The catalog shows four Tool Broker v2 entries as preview-only, Action Inbox
`local_task_create` as one exact local mutation lane, RuntimeGateway focused
pytest as one exact approval-required lane, Coding patch proposal as
proposal-only, and Coding patch apply, allowlisted test command, Git review,
and live preview as blocked missing exact authority. Generic tool execution remains blocked.
Unrestricted shell/subprocess execution, arbitrary command
strings, connector writes, browser automation, plugin runtime import, remote
execution, provider/model calls, background autonomy, production authority,
public beta, and public release claims remain blocked.

## Phase 05 Evidence

Phase 05 is implemented as a repo-safe memory learning posture read-model
slice. It adds
`docs/control_center/UAA_RUNTIME_MEMORY_LEARNING.md`, Python Core
contract `contract-ref:runtime-memory-learning-posture:v1`,
Memory Workbench embedding through `GET /control-center/memory/workbench`, CLI
command `scripts/dev/uaa_founder_loop.py memory-learning-posture`, Control
Center Memory rendering, and focused tests/verifier coverage. Memory remains
recall and reviewable context, not truth or authority.

The posture shows proposed, active, needs-review, corrected, rejected, stale,
forgotten, and blocked counts; feedback, correction, rejection, and
forget-request receipt support; context-pack proposal posture; provenance
requirements; quality controls; receipt refs; reviewed recall refs; blocked
authority refs; and next safe action. Broad memory writes, automatic memory writes,
hidden/automatic context injection, memory-as-truth, action execution from
memory, connector writes, model/provider calls, live web fetching, background
autonomy, hard delete, export execution, public release, and production
authority remain blocked.

## Phase 06 Evidence

Phase 06 is implemented as a repo-safe evidence audit receipt spine read-only
lineage read-model slice. It adds
`docs/control_center/UAA_RUNTIME_EVIDENCE_AUDIT.md`, Python Core
contract `contract-ref:runtime-evidence-audit-spine:v1`, the
existing `GET /control-center/evidence/timeline` API payload field
`evidence_audit_receipt_spine`, CLI command
`scripts/dev/uaa_founder_loop.py inspect-evidence-audit-spine`, Control Center
Evidence rendering, and focused tests/verifier coverage.

The spine groups plan changes, approval waits, action proposals, receipt
events, memory decisions, blocked/no-go events, and recovery posture. Receipt
envelopes expose safe refs, artifact hash refs, verifier refs, redaction
status, missing receipt refs, and blocked-authority refs only. External
telemetry/export, production compliance claims, provider/model calls, browser
automation, connector writes, shell execution, background autonomy, and
production authority remain blocked.

## Phase 07 Evidence

Phase 07 is implemented as a repo-safe model/provider/research posture read
model slice. It adds
`docs/control_center/UAA_RUNTIME_MODEL_PROVIDER_RESEARCH.md` and
Python Core contract
`contract-ref:runtime-model-provider-research-posture:v1`,
embedded as `model_provider_research_posture` in the existing
`GET /control-center/providers/runtime-control-plane` payload. CLI parity stays
on `scripts/inspect_model_provider_control_plane.py`, with focused verifier
coverage in
`scripts/verify_uaa_runtime_model_provider_research.py`.

The posture summarizes provider readiness rows, credential readiness status,
static cost/latency metadata posture, exact-lane or guidance-only authority
modes, blocked reason refs, diagnostic receipt refs, model-output truth, and
WebAccessGateway-governed external-information posture. Model output is
proposal/evidence only, verified facts require separate evidence refs, and
external content remains untrusted evidence, never instructions.

Provider SDK calls, remote model calls by the read model, live web fetching,
browser observe/action, credential entry, secret display, provider output as
authority, memory/action/context escalation, connector writes, production
authority, and broad autonomy remain blocked.

## Phase 08 Evidence

Phase 08 is implemented as a repo-safe cockpit CLI/API parity read-model and
Control Center readability slice. It adds
`docs/control_center/UAA_RUNTIME_COCKPIT_CLI_API.md`, Python Core
contract `contract-ref:runtime-cockpit-cli-api-parity:v1`,
the `operator_decision_matrix` field on the existing
`GET /control-center/agent-loop/thread` payload, CLI command
`scripts/dev/uaa_founder_loop.py inspect-cockpit-parity`, Today cockpit
rendering, and focused tests/verifier coverage.

The matrix gives the operator route refs, CLI refs, capability status,
approval posture, side-effect class, safe action text, evidence/proof/receipt
refs, blocked-state refs, and no-go reasons for Today, Action Inbox, Plans,
Evidence, Memory, Trust, Runtime/Providers, Coding, and Work Board. It is
backend-owned, safe-ref-only, and states that Control Center cannot mint
authority. Runtime model calls, provider SDK calls, live web fetching, browser
automation inside UAA, connector writes, unrestricted shell/subprocess
execution, plugin runtime import, broad memory writes, background autonomy,
public release claims, production authority, and broad action execution remain
blocked.

## Phase 09 Evidence

Phase 09 is implemented as a repo-safe extensibility ecosystem final hardening
slice. It adds
`docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md`, explicit
operator posture fields on the existing
`uaa_inspectable_extension_catalog.v1` read model, CLI commands
`scripts/dev/uaa_extensions.py inspect-catalog` and
`scripts/dev/uaa_extensions.py inspect-install-disabled-posture`, and focused tests/verifier
coverage in `tests/test_runtime_extensibility_final.py` and
`scripts/verify_uaa_runtime_extensibility_final.py`.

The existing `GET /extensions/catalog` route remains read-only and now gives
operators visibility status, trust posture, callable posture, required grant
refs, blocked reason, review evidence refs, safe adoption posture, and
install-disabled posture. The install-disabled posture includes AuthorityLease
decision refs, exact LocalApprovalAuthority requirement, hash refs, receipt
plan refs, rollback refs, safe-disable refs, and blocked capability refs
without persisting an install record. The route and CLI use safe refs and
redacted summaries only. Visibility is separate from callability: callable
catalog behavior, plugin package install persistence, plugin runtime import,
skill runtime import, connector writes, live web fetching, browser automation,
arbitrary shell/subprocess execution, provider/model calls, remote execution,
public release claims, production authority, and broad autonomy remain blocked.
Plugin runtime import remains blocked. Connector writes remain blocked.
Production authority remains blocked.

The final 30-day plan is ranked by impact, effort, risk, and authority needed
in `docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md`.

## Merge-Gated Follow-Up Prompts

Each prompt below should run as a separate branch/PR after Phase 01 merges or
is accepted as the active scorecard baseline.

### Phase 02 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/02_productized_agent_loop_spine.prompt.md`
only. Start from latest main or the accepted integration branch, inspect the
current UAA loop implementation, and add the smallest backend-owned agent-loop
read model that ties chat, actions, proof, evidence, memory, and trust through
safe refs. Do not add runtime model calls, provider SDK calls, live web
fetching, connector writes, shell execution, browser automation, memory-write
authority, production authority, or broad autonomy. Run focused tests,
documentation integrity, product truth, `git diff --check`, and any route/API
verifiers if routes change.

### Phase 03 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/03_durable_orchestration_progress_and_recovery.prompt.md`
only. Add durable orchestration progress and recovery visibility using UAA
Python Core/read models, not background execution. Preserve blocked background
autonomy and generic queue execution. Run durable-run tests, docs/product
verifiers, and route/OpenAPI checks if API routes change.

### Phase 04 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/04_action_tool_code_lanes_and_approval_receipts.prompt.md`
only. Add or harden inspectable action/tool/code catalogs and proposal/receipt
read models without generic callable execution. Preserve blocked unrestricted
shell/subprocess execution, plugin runtime import, connector writes, provider
calls, and broad autonomy. Run catalog, approval, receipt, and product-language
tests.

### Phase 05 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/05_memory_learning_context_and_feedback.prompt.md`
only. Improve governed memory feedback, stale/wrong/conflict/duplicate states,
and context-pack preview posture without memory-write authority or hidden
context injection. Run memory provenance, redaction, CLI/API parity, and
product-truth checks.

### Phase 06 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/06_evidence_audit_receipts_and_observability.prompt.md`
only. Add or harden portable evidence envelopes, same-run lineage, receipts,
debuggability, and redacted observability. Do not claim public compliance,
production audit, or external telemetry. Run evidence, redaction, docs, and
product-truth verifiers.

### Phase 07 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/07_model_provider_research_and_external_info_posture.prompt.md`
only. Add metadata/readiness/cost/secret-status/provider-catalog/read-model
surfaces only; no runtime model calls, provider SDK calls, or live web fetching.
Keep WebAccessGateway governed and default-deny. Run runtime metadata tests and
authority guard verifiers.

### Phase 08 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/08_cockpit_cli_api_parity_and_operator_ux.prompt.md`
only. Productize cockpit surfaces over backend-owned truth with CLI/API parity:
Today, Actions, Chat, Proof, Evidence, Memory, Runtime, Coding, Work Board, and
Trust. Browser automation inside UAA remains blocked. Run frontend tests and
visual checks if primary UI output changes.

### Phase 09 Prompt

Execute `docs/prompts/uaa_runtime_capability_foundation/09_extensibility_ecosystem_and_final_hardening.prompt.md`
only. Harden inspectable extension and capability catalog posture, activation
records, trust labels, and final catch-up evidence. Do not add plugin runtime
import, connector writes, remote execution, public release claims, production
authority, or broad autonomy. Run final docs, product truth, OpenAPI if needed,
catalog tests, and `git diff --check`.

## Phase 01 Acceptance Result

Phase 01 intentionally stops at a verified, evidence-backed baseline. It creates
a safe catch-up map and merge-gated follow-up prompts for Phases 02-09. It does
not change APIs, UI routes, runtime behavior, authority profiles, provider
execution, connector behavior, web fetching, browser automation, memory writes,
or shell execution.

## Phase 10 Evidence

Phase 10 adds a backend-owned High-Maturity Agent Spine projection to the
existing Agent Loop Thread instead of creating a new authority surface.

- Core:
  `src/ultimate_ai_agent/core/control_center/agent_loop.py`
- API:
  `GET /control-center/agent-loop/thread#high_maturity_spine_readiness`
- CLI:
  `scripts/dev/uaa_founder_loop.py inspect-high-maturity-spine`
- Control Center:
  the Agent Loop Thread panel renders W1-W13 component rows, score projection,
  evidence refs, test refs, gaps, recommendations, and blocked authority refs.
- Code/evidence truth:
  W6 now counts Coding proposal evidence as implemented only for deterministic
  safe-ref signed envelopes; exact patch apply remains blocked. W9 includes
  both Runtime action signed evidence and Coding patch proposal signed evidence.
- Tests/verifier:
  `tests/test_runtime_agent_loop_spine.py` and
  `scripts/verify_uaa_runtime_agent_loop_spine.py`

The projection is deterministic and read-only. It adds no runtime model calls,
provider SDK calls, live web fetching, browser automation, connector writes,
unrestricted shell/subprocess execution, plugin runtime import, memory-write
authority, hidden context injection, background autonomy, public release claim,
or production authority.
