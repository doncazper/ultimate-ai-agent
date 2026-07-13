# UAA And GoatCitadel Agent-Platform Parity Matrix

Status: active evidence-backed comparison; benchmark use is read-only

Snapshot date: 2026-07-11

UAA implementation snapshot: `d5eca61ee586ffc06b699ee196f8cd1af0702563`

The scored snapshot remains pinned above. The Tool execution row also records
the later sealed-calculation follow-up as current repository evidence without
retroactively changing the Phase 09 score.

GoatCitadel scored release snapshot: tag `v1.0.0` at
`dff26c018b44c394c189c170265a00ab640f1214`

The separately observed local GoatCitadel head
`91775e6905c8ca6c5083444f64eb3457b2d0aaa0` is a different package/version
target and is not assigned the `v1.0.0` score.

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
| Durable orchestration | Mixed | `mission_orchestrator.py`, `mission_completion.py`, approval waits, retry/dead-letter/cancellation controls, mission budgets, settlement recovery, and completion verification now provide exact lease-bound local orchestration. | `durable-run-service.test.ts` and its boot-recovery integration tests prove broader live scheduling and recovery. | GoatCitadel retains breadth; UAA retains stricter final-start authority. Add only exact local worker controls, not broad autonomy. |
| Tool execution | GoatCitadel ahead | The canonical orchestrator/runner/dispatcher path executes exact filesystem metadata and bounded sealed arithmetic with idempotency, budgets, atomic-start evidence, and content-free receipts. The calculation lane proves no network, host mounts/files, unsafe environment, subprocesses, shells, or packages. Generic tool dispatch and general CodeAct remain blocked. | `tools-invoke.test.ts`, the invocation coordinator, policy-engine tests, and broader sandbox tests still prove substantially greater callable breadth. | Promote additional UAA adapters individually; do not generalize the sealed arithmetic lane into a global tool or code switch. |
| Evidence receipts | Mixed | `portable_mission_evidence.py` and mission completion bind plan, lease, approval, budget, adapter, target, and terminal evidence into content-free, offline-verifiable hash chains with tamper/reorder/replay rejection. | GoatCitadel evidence-envelope service and storage tests prove broad persisted evidence integration. | UAA signing remains blocked until Keychain lifecycle proof; GoatCitadel should add UAA-style portable substitution checks. |
| Memory | Mixed | Governed context, deterministic correction precedence, feedback receipts, staleness/conflict exclusion, retrieval benchmarks, and operator review are implemented without hidden injection. | GoatCitadel retains deeper live context composition, maintenance, and runtime memory breadth. | Add exact reviewed context materialization in UAA; GoatCitadel should strengthen correction and content-free receipt boundaries. |
| Provider observability | GoatCitadel ahead | UAA now separates catalog, compatibility, configuration, health, authority, budget, safe-disable, and readiness; WEB-HYBRID adds bounded provider cost/readiness evidence. | `llm-runtime-truth-service.test.ts`, LLM routes, usage accounting, and spend UI prove wider live provider operation. | UAA needs one fully configured exact provider lane with actual cost settlement; credentials/configuration remain external. |
| Operator cockpit UX | GoatCitadel ahead | The macOS-first Control Center now renders backend-owned intent, uncertainty, mission progress, budgets, waits/retries/dead letters, evidence, provider/web truth, leases, and blocked reasons; fake/unwired controls were removed. | Mission Control retains broader live run, approvals, tools, memory, provider, and spend workflows with focused UI tests. | UAA should add only backend-wired exact controls and keep Linux/Windows as render placeholders. |
| Extensibility | GoatCitadel ahead | UAA's extension truth now covers declaration, compatibility, configuration, health, authority, budget, provenance, safe-disable, activation, and rollback while keeping inspection non-callable. | Extension SDK, integration-plugin tests, and skill import security tests prove a callable ecosystem. | Prove one isolated exact UAA adapter lane before any runtime import; do not copy arbitrary loading. |
| Recovery | Mixed | Approval wait, retry, dead-letter, cancellation, settlement recovery, crash replay, portable verification, and operator inspection are now implemented and tested under exact mission authority. | GoatCitadel retains broader boot reconciliation and live recovery operations. | Add only exact recovery mutations through the same Python contracts; no cached authority. |
| End-to-end usefulness | GoatCitadel ahead | UAA now completes a useful filesystem-metadata Founder Loop from intent and immutable plan through approval, mission lease, dispatcher, settlement, completion evidence, and reviewable memory candidate. | GoatCitadel still offers broader supervised Chat/Cowork/Code, tools, providers, memory, and operator workflows. | Expand UAA usefulness through exact adapters while retaining the completed governed loop and honest blocked states. |

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

At the Milestone 1 close, GoatCitadel remained ahead because UAA lacked a local
background worker, periodic heartbeats, and boot reconciliation in addition to
approval waits, retry/dead-letter semantics, mission cancellation,
mission-completion receipts, and operator execution controls. The following
Milestone 2 section records the worker, heartbeat, and reconciliation closure.

### AuthorityLease local mission worker V1

This milestone narrows the scheduling and boot-recovery gap without claiming
parity:

- a bounded macOS-only local queue is disabled by default and persists safe refs
  plus complete request fingerprints, never the request or tool input;
- queue and mission-step claims use monotonic generations, bounded TTLs, and
  periodic heartbeats;
- the dispatcher validates the exact worker and step fence inside its locked
  durable-start boundary, so a stale worker cannot start an adapter;
- execution advances one step per slice and rechecks configuration, kill
  switch, exact request material, plan binding, lease, policy, approval, budget,
  adapter, target, and deadline;
- boot inspection distinguishes pending, active/stale claims, prepared starts,
  unknown terminal starts, success, failure, dependency blocking, and recovery;
- a durable start is never reinvoked, and a restart requires an injected exact
  request resolver because raw request persistence is forbidden;
- protected API and human-first CLI inspection share one redacted backend read
  model; Linux and Windows remain render placeholders.

Evidence:

- `src/ultimate_ai_agent/core/execution/durable_mission_worker.py`
- `src/ultimate_ai_agent/core/execution/mission_worker_inspection.py`
- `tests/test_authority_mission_worker.py`
- `tests/test_authority_mission_worker_inspection.py`

GoatCitadel remains ahead overall. UAA still lacks approval waits, retries,
dead letters, mission cancellation, mission-wide budget settlement recovery,
completion receipts, Control Center worker controls, broader exact adapters,
and a safe-ref target registry for unattended reboot reconstruction. Generic
Hermes background jobs remain proposal-only.
