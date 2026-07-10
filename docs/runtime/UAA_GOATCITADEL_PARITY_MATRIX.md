# UAA And GoatCitadel Agent-Platform Parity Matrix

Status: active evidence-backed comparison; benchmark use is read-only

Snapshot date: 2026-07-10

UAA baseline: `383b1e284fdb621c0c8f315367f49158a9d1e7a4`

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
| Durable orchestration | GoatCitadel ahead | `src/ultimate_ai_agent/core/execution/durable_runs.py`, `run_storage.py`, and `staged_orchestration.py` provide append-first state, replay checks, dependencies, checkpoints, and exact RuntimeGateway command steps. `core/authority/budgets.py` adds local atomic lease-capacity reservation and settlement, but no mission dispatcher consumes it yet. | `apps/gateway/src/services/durable-run-service.ts` implements leases, heartbeats, retry budgets, boot recovery, resume, cancel, dead-letter recovery, and workflow execution; `orchestration-lifecycle-service.ts` binds live phases and child-run recovery. | Add one governed executable MissionRunner that binds the new budget ledger to durable step dispatch, heartbeat ownership, retry budgets, approval waits, cancellation, and crash-resume proof. |
| Tool execution | GoatCitadel ahead | RuntimeGateway executes four exact approved utility command shapes; the Action/Tool/Code catalog distinguishes callable and blocked entries. | `apps/gateway/src/routes/tools-invoke.ts` and the tool invocation services provide a central callable tool route with policy and browser-action verification; orchestration invokes tools during live runs. | Add a central typed dispatcher over an implemented UAA tool catalog, then promote capabilities individually under AuthorityLease evaluation. |
| Evidence receipts | Mixed | UAA has redacted runtime receipts, action signed evidence, portable local evidence envelopes, append-first receipt hashes, replay validation, and a full-history hash-chained AuthorityLease budget ledger. | `apps/gateway/src/services/evidence-receipt-service.ts` signs canonical manifests with Ed25519 and verifies them offline; receipts include run lineage, approvals, artifacts, and side effects. | Consolidate UAA receipts into one verifiable authority/execution envelope covering decision, approval, budget reservation/settlement, dispatch, cancellation, rollback posture, and mission completion. |
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
  idempotency checked, and projected through AuthorityState API/JSON CLI;
- concurrency tests prove no local oversubscription or lost concurrent lease
  issue across separate store instances.

Evidence:

- `src/ultimate_ai_agent/core/authority/budgets.py`
- `src/ultimate_ai_agent/core/authority/budget_contracts.py`
- `tests/test_authority_budgets.py`
- `docs/runtime/UAA_AUTHORITY_LEASE_BUDGET_LEDGER.md`

Remaining gaps are central dispatcher binding, durable mission-step use,
adapter-start proof for releases, reviewed unresolved-cost remediation,
Control Center budget UX, time-window and recipient/target constraints,
renewal, and multi-host storage. No provider/model execution or external spend
authority was added.
