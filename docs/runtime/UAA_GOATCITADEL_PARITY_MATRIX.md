# UAA And GoatCitadel Agent-Platform Parity Matrix

Status: active evidence-backed comparison; benchmark use is read-only

Snapshot date: 2026-07-10

UAA baseline: `f11cbcbaa59074e9562f27ec715cef6d9282d47f`

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
| Durable orchestration | GoatCitadel ahead | `src/ultimate_ai_agent/core/execution/durable_runs.py`, `run_storage.py`, and `staged_orchestration.py` provide append-first state, replay checks, dependencies, checkpoints, and exact RuntimeGateway command steps. | `apps/gateway/src/services/durable-run-service.ts` implements leases, heartbeats, retry budgets, boot recovery, resume, cancel, dead-letter recovery, and workflow execution; `orchestration-lifecycle-service.ts` binds live phases and child-run recovery. | Add one governed executable MissionRunner with durable step dispatch, heartbeat ownership, retry budgets, approval waits, cancellation, and crash-resume proof. |
| Tool execution | GoatCitadel ahead | RuntimeGateway executes four exact approved utility command shapes; the Action/Tool/Code catalog distinguishes callable and blocked entries. | `apps/gateway/src/routes/tools-invoke.ts` and the tool invocation services provide a central callable tool route with policy and browser-action verification; orchestration invokes tools during live runs. | Add a central typed dispatcher over an implemented UAA tool catalog, then promote capabilities individually under AuthorityLease evaluation. |
| Evidence receipts | Mixed | UAA has redacted runtime receipts, action signed evidence, portable local evidence envelopes, append-first receipt hashes, and replay validation. | `apps/gateway/src/services/evidence-receipt-service.ts` signs canonical manifests with Ed25519 and verifies them offline; receipts include run lineage, approvals, artifacts, and side effects. | Consolidate UAA receipts into one verifiable authority/execution envelope covering decision, approval, dispatch, cancellation, rollback posture, and mission completion. |
| Memory | GoatCitadel ahead | UAA has reviewed memory decisions, lifecycle receipts, provenance, quality grouping, explicit context-pack previews, and no-hidden-injection rules. | `apps/gateway/src/services/memory-lifecycle-service.ts` implements broad lifecycle, recall, feedback, dedupe, quality, maintenance, structured scope, and write-gate behavior used by the runtime. | Bind reviewed UAA memory to live mission context under explicit leases while preserving recall-not-truth and operator review boundaries. |
| Provider observability | GoatCitadel ahead | UAA exposes provider readiness, exact approved tiny invocation lanes, CostGovernor posture, runtime measurements, and local loopback receipts; broad provider calls remain blocked. | GoatCitadel has a multi-provider runtime, per-step model selection, usage accounting, stream handling, and `llm-runtime-truth-service.ts` measurement/readiness truth. | Add one fully configured provider lane with durable cost/usage budgets, runtime observability, failure receipts, and mission-step integration; external credentials may block live proof. |
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

Remaining constraint gaps are durable operation/cost budgets, typed time-window
and recipient/target constraints, renewal policy, and dispatcher integration.
