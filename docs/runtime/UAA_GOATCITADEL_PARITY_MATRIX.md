# UAA And GoatCitadel Agent-Platform Parity Matrix

Status: active evidence-backed comparison; benchmark use is read-only

Snapshot date: 2026-07-10

UAA comparison scope: current repository state containing this matrix and its
cited implementation evidence

GoatCitadel benchmark snapshot: `91775e6905c8ca6c5083444f64eb3457b2d0aaa0`

This matrix measures implemented behavior only. Documentation, mock surfaces,
and planned adapters do not earn parity. GoatCitadel is benchmark material and
must not be modified by UAA work.

Status meanings:

- `UAA ahead`: UAA has stronger verified implementation evidence.
- `tie`: both repositories have comparable verified implementation evidence.
- `mixed`: each repository leads on a material part of the category.
- `GoatCitadel ahead`: GoatCitadel has broader or deeper verified behavior.
- `external blocker`: UAA needs an external credential, service, or hardware
  condition before the comparison can move.

## Current Matrix

| Area | Status | UAA implementation evidence | GoatCitadel implementation evidence | Concrete gap to tie or lead |
|---|---|---|---|---|
| Durable orchestration | GoatCitadel ahead | `src/ultimate_ai_agent/core/execution/durable_runs.py`, `run_storage.py`, and `staged_orchestration.py` provide append-first state, replay checks, dependencies, checkpoints, and exact RuntimeGateway command steps. `core/authority/dispatcher.py`, `durable_mission_plans.py`, `durable_mission_steps.py`, `mission_runner.py`, and `mission_orchestrator.py` now provide immutable full-plan/request bindings plus bounded synchronous topological execution of exact filesystem-metadata steps with mission-scoped lease preflight, per-step authority evaluation, atomic start deadlines, terminal replay, fail-fast dependency evidence, and redacted exact step inspection. | `apps/gateway/src/services/durable-run-service.ts` implements leases, heartbeats, retry budgets, boot recovery, resume, cancel, dead-letter recovery, and workflow execution; `orchestration-lifecycle-service.ts` binds live phases and child-run recovery. | Add background scheduling, a periodic heartbeat/lease-renewal loop, approval waits, retry budgets, after-start cancellation, mission completion receipts, settlement/dead-letter recovery, boot reconciliation, mutation controls, broader adapters, and Control Center parity. |
| Tool execution | GoatCitadel ahead | `core/authority/dispatcher.py` is a central typed dispatch boundary over explicitly injected safe tool-runtime adapters. Focused proof executes useful filesystem metadata and deterministic no-op with lease, exact approval where required, budget, start, settlement, cancellation, evidence, replay, and concurrency binding. There is no API/CLI mutation surface or universal tool catalog migration yet. | `apps/gateway/src/routes/tools-invoke.ts` and the tool invocation services provide a central callable tool route with policy and browser-action verification; orchestration invokes tools during live runs. | Add CLI/API/Control Center parity, route an implemented catalog through the dispatcher, and promote additional useful capabilities individually under AuthorityLease without broad dynamic dispatch. |
| Evidence receipts | Mixed | UAA has redacted runtime receipts, action signed evidence, portable local evidence envelopes, append-first receipt hashes, replay validation, and full-history hash-chained AuthorityLease budget, dispatch, mission-plan, and mission-step ledgers. Bounded synchronous missions bind every step definition and dispatch request to one immutable plan and cross-ledger terminal evidence without persisting raw input, paths, content, or output. | `apps/gateway/src/services/evidence-receipt-service.ts` signs canonical manifests with Ed25519 and verifies them offline; receipts include run lineage, approvals, artifacts, and side effects. | Add a durable mission-completion receipt and offline cryptographic verification without persisting raw execution content. |
| Memory | GoatCitadel ahead | UAA has reviewed memory decisions, lifecycle receipts, provenance, quality grouping, explicit context-pack previews, and no-hidden-injection rules. | `apps/gateway/src/services/memory-lifecycle-service.ts` implements broad lifecycle, recall, feedback, dedupe, quality, maintenance, structured scope, and write-gate behavior used by the runtime. | Bind reviewed UAA memory to live mission context under explicit leases while preserving recall-not-truth and operator review boundaries. |
| Provider observability | GoatCitadel ahead | UAA exposes provider readiness, exact approved tiny invocation lanes, CostGovernor posture, runtime measurements, local loopback receipts, and durable AuthorityLease operation/cost counters. The counters are not yet dispatcher-bound to provider execution; broad provider calls remain blocked. | GoatCitadel has a multi-provider runtime, per-step model selection, usage accounting, stream handling, and `llm-runtime-truth-service.ts` measurement/readiness truth. | Bind one fully configured provider lane to the durable budget ledger with authenticated CostGovernor decision, actual usage/cost settlement, runtime observability, failure receipts, and mission-step integration; external credentials may block live proof. |
| Operator cockpit UX | GoatCitadel ahead | Control Center exposes Founder Loop, Trust, Proof, Evidence, runtime readiness, capability posture, and AuthorityLease mode/lease state. | Mission Control ships Work, Projects, Library, Ops, and Settings with live Run Detail, approvals, providers, memory, tools, skills, runtime health, and spend surfaces. | Build the Authority cockpit and live Mission progress/approval/recovery workflow without raw JSON as the primary operator surface. |
| Extensibility | GoatCitadel ahead | UAA has manifest-first extension/skill catalogs, review and activation contracts, and safe posture inspection; runtime import and generic callable activation remain blocked. | GoatCitadel ships MCP/tool/skill/plugin runtime services, governed scoping, invocation, and operator catalog surfaces. | Implement a sandboxed callable catalog with explicit adapter readiness, AuthorityLease scopes, provenance, revocation, receipts, and no arbitrary import. |
| Recovery | GoatCitadel ahead | UAA durable records expose restart recovery, retry, cancel, dead-letter, replay, rollback refs, and read-only run observability; most live controls remain blocked. | GoatCitadel implements boot reconciliation, heartbeat lease loss, retry exhaustion, dead-letter recovery, live cancellation, child-run reattachment, and recovery UI traces. | Promote exact live cancel/resume/retry/recover operations through policy, lease, idempotency, receipts, CLI/API/UI parity, and safe-disable tests. |
| End-to-end usefulness | GoatCitadel ahead | UAA has a real local Founder Loop and exact local task/runtime utility actions, but broad mission execution and external adapters remain partial or unavailable. | GoatCitadel ships supervised Chat/Cowork/Code runs, tool invocation, multi-provider models, memory, evidence receipts, and a broad operator shell. | Complete one durable delegated local workspace mission end to end, then add external domains only when adapters and credentials are genuinely ready. |

## Milestone Movement

### AuthorityLease typed constraints V1

This milestone narrows the authority-safety gap but does not change any row to
parity:

- typed resource, path, app, host, and delegation-depth constraints are
  fail-closed during `evaluate_authority_request`;
- constraint contents are bound into LocalApprovalAuthority scope and lease
  identity;
- applied constraint refs are visible in policy decisions;
- AuthorityLease issue/revoke receipts bind semantic request fingerprints, and
  same-key request or approval drift is rejected;
- constraints remain safe-ref-only, and raw local paths are rejected.

Evidence:

- `src/ultimate_ai_agent/core/authority/contracts.py`
- `tests/test_authority_leases.py`
- `docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`

At that checkpoint, remaining constraint gaps included durable operation/cost
budgets, typed time-window and recipient/target constraints, renewal policy,
and dispatcher integration. The next milestone below implements the local
durable budget foundation while leaving the other gaps open.

### AuthorityLease durable budget ledger V1

This milestone narrows the durable authority and provider-budget foundations,
but GoatCitadel remains ahead in durable orchestration and provider
observability because UAA has not yet bound the ledger to a central executable
dispatcher or live mission step:

- `operation_budget` and `cost_budget_microusd` are typed lease constraints;
- reservations revalidate current policy, active lease identity, kill switch,
  exact claims, and cumulative capacity under the same single-writer lock as
  lease issue/revoke, while requiring structured cost-estimate and
  CostGovernor-decision refs plus an explicit allowed posture;
- settlement records actual usage, overage, execution status, and evidence
  refs, while unknown actual cost blocks future reservations;
- release is explicitly pre-execution and frees unused capacity;
- append-first receipts are fsync-backed, hash-chained, full-history
  idempotency and semantic-transition checked, and projected through
  AuthorityState API/JSON CLI;
- concurrency tests prove no local oversubscription or lost concurrent lease
  issue across separate store instances.

Evidence:

- `src/ultimate_ai_agent/core/authority/budgets.py`
- `src/ultimate_ai_agent/core/authority/budget_contracts.py`
- `tests/test_authority_budget*.py`
- `docs/runtime/UAA_AUTHORITY_LEASE_BUDGET_LEDGER.md`

At that checkpoint, remaining gaps included central dispatcher binding, durable
mission-step use, adapter-start proof for releases, reviewed unresolved-cost
remediation, Control Center budget UX, time-window and recipient/target
constraints, renewal, and multi-host storage. The next milestone closes the
initial dispatcher/start-proof portion only. No provider/model execution or
external spend authority was added.

### AuthorityLease governed dispatcher V1

This milestone closes the first central-dispatcher foundation gap while leaving
GoatCitadel ahead in tool breadth, live orchestration, and operator UX:

- one typed request binds lease, action, adapter, capability, run,
  idempotency, CostGovernor refs, operation/cost claims, and exact approval;
- append-first hash-chained budget and dispatch ledgers record prepare, durable
  budget start, adapter start, terminal settlement, and pre-start cancellation
  phases;
- lease, kill switch, exact approval revocation, budget activity, fixed tool
  authority domain, and redacted adapter/safe-root configuration identity are
  rechecked immediately before start;
- a started adapter is never replayed after a crash, while an interrupted
  cancellation claim is visible and retryable with the same cancellation refs;
- concurrent identical dispatches invoke the adapter exactly once;
- a started budget reservation cannot be released while its adapter is in
  flight, and a crash before the dispatch-start receipt replays the exact start
  claim;
- the first useful routed adapter returns bounded filesystem metadata under an
  injected safe root without returning raw content or absolute paths.

Evidence:

- `src/ultimate_ai_agent/core/authority/dispatcher.py`
- `src/ultimate_ai_agent/core/authority/dispatch_contracts.py`
- `tests/test_authority_dispatcher*.py`
- `docs/runtime/UAA_AUTHORITY_DISPATCHER_V1.md`

Remaining gaps are durable MissionRunner integration, heartbeat ownership,
retry budgets, approval waits, after-start cancellation, settlement recovery,
dead-letter handling, API/CLI/Control Center mutation parity, broader exact
adapter promotion, cryptographic envelope verification, and multi-host state.
No provider/model, shell, browser, connector-write, production, or generic
plugin authority was added.

### AuthorityLease synchronous MissionRunner step V1

This milestone closes only the first durable mission-step consumption gap:

- an append-first, fsync-backed, hash-chained safe-ref ledger records exact
  mission-step definitions, fenced TTL ownership, generations, one synchronous
  pre-execute claim renewal, an immutable dispatch ref plus
  full request fingerprint, and cross-ledger terminal evidence refs;
- one synchronous runner routes only exact filesystem metadata through the
  governed dispatcher under deterministic action, dispatch, and idempotency
  refs;
- the dispatcher retains every live authority decision, and a terminal replay
  after runner interruption does not start the adapter twice;
- automatic retry remains disabled and the ledger persists no raw content,
  path, tool input, provider payload, or output.

Evidence:

- `src/ultimate_ai_agent/core/execution/durable_mission_steps.py`
- `src/ultimate_ai_agent/core/execution/mission_runner.py`
- `tests/test_durable_mission_step_ledger.py`
- `tests/test_authority_mission_runner.py`

GoatCitadel remains ahead. This is not a background scheduler, general mission
engine, API/CLI/UI mutation surface, approval-wait loop, retry budget,
after-start cancellation path, settlement recovery worker, or dead-letter
system. No provider/model, shell, browser, connector-write, production, or
generic plugin authority was added.

### AuthorityLease bounded synchronous mission orchestration V1

This milestone closes the bounded synchronous dependency gap only:

- one immutable safe-ref plan binds ordered membership, dependencies, exact
  definitions, complete dispatch request fingerprints, deadlines, mission, and
  run before execution;
- accepted-plan membership is enforced at step creation and claim, while every
  step still routes exclusively through MissionOrchestrator, MissionRunner, and
  AuthorityDispatcher; a locked plan-wide fail-fast guard closes crash and
  direct-runner windows;
- stable topological execution re-evaluates current authority for each attempted
  step, terminal replay does not duplicate adapter starts, and fail-fast records
  durable dependency-blocked or halted evidence for all unscheduled work;
- a trusted start-admission timestamp binds deadline, lease, approval, and cost
  expiry checks inside the locked pre-start boundary;
- legacy V1 mission-step and dispatch ledger hashes remain readable.

Evidence:

- `src/ultimate_ai_agent/core/execution/durable_mission_plans.py`
- `src/ultimate_ai_agent/core/execution/mission_orchestrator.py`
- `tests/test_authority_mission_orchestrator.py`
- `tests/test_authority_mission_orchestrator_hardening.py`

GoatCitadel remains ahead. UAA still lacks a default-on local background worker,
periodic heartbeats, boot reconciliation, approval waits, retry/dead-letter
semantics, mission cancellation, mission-completion receipts, and operator
execution controls.
