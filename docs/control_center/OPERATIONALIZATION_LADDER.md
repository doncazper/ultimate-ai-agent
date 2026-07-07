# Control Center Operationalization Ladder

Status: active AuthorityLease capability maturity gate
Baseline: v0.104.0 / 0.104.0
Manifest: `docs/control_center/operational_maturity_manifest.json`
Verifier: `scripts/verify_operational_maturity.py`

This ladder prevents Founder Command Center modules from staying in proposal
theatre or overclaiming operational behavior. A module may be broadly
review-only while one exact AuthorityLease capability is implemented; the
manifest must distinguish the module rank from any authority capability rank
and keep legacy lane metadata as compatibility/audit context only.

## Ladder

| Rank | Label | Meaning |
|---:|---|---|
| 0 | `docs_only` | Roadmap, spec, or planning language only. |
| 1 | `read_only_status` | Backend or UI can inspect status, but cannot propose or decide work. |
| 2 | `proposal_review` | Reviewable proposals or envelopes exist, with execution blocked. |
| 3 | `decision_receipts` | Backend-owned decisions and receipts exist, but no real local mutation happens. |
| 4 | `execution_ready_contract` | Exact scope, approval, idempotency, route metadata, and rollback/safe-disable posture are complete. |
| 5 | `local_execution_receipt_evidence` | One allowlisted local mutation can complete with durable receipt, evidence, CLI parity, and tests. |
| 6 | `rollback_safe_disable_verified` | The authority capability has verified rollback or safe-disable behavior under tests. |
| 7 | `routine_operational_loop` | The authority capability is a normal repeated operator workflow with monitoring and stale-state handling. |

## Promotion Rules

- Rank 3 or higher requires backend-owned receipt state.
- Rank 4 or higher requires exact scope, approval or approval posture,
  idempotency, route metadata, and rollback or safe-disable posture.
- Rank 5 or higher requires a real allowlisted local state change, durable
  receipt, Evidence Timeline event, CLI or repo-local parity, and focused tests.
- Rank 2 or higher backend-owned status routes require a manifest
  `ui_status_binding`: either the Control Center/API layer surfaces the typed
  read-only status with frontend endpoint, client, type, component, and test
  refs, or the module is explicitly marked backend-only with a documented
  reason and blocker. Backend-only status is not a silent promotion escape
  hatch.
- Future authority classes must pass the AuthorityLease capability conveyor
  before they can become implemented authority. The canonical authority
  foundation is `docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`; the
  candidate scorecard is
  `docs/control_center/authority_candidate_scorecard.json`; the legacy-stable
  conveyor doc path is `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`; and
  the same verifier owns the gate. The fixed first web implementation
  capability is `read_only_real_world_web_fetch` through `WebAccessGateway`;
  it is not a follow-on authority candidate. A future candidate may not become
  implemented authority unless exact mode, domain, capability, active lease
  requirement, approval, idempotency, receipt/evidence, rollback or
  safe-disable, redaction, CLI/API/core parity, and focused test refs all
  resolve.
- Support modules such as Evidence can rank by the operational receipts they
  index, but must say they support operations rather than perform them.
- No broad execution route, connector write, shell/subprocess execution,
  model/provider authority, memory write, context injection, public beta,
  production readiness, standing authority, or production authority is granted
  by this ladder. Unknown authority remains denied unless a known capability
  is evaluated inside an active AuthorityLease scope.

## First Implemented Authority Capability

`FCC-ACTION-001a` implements only the Action Inbox
`authority-capability:action-inbox:local-task-create` capability for
`local_task_create` at rank 5. The Action Inbox module remains rank 3 overall
because most Action items still stop at review decisions. The committed
capability is local-only and requires active `workspace/write`
AuthorityLease scope plus exact approval:

```text
approved local_task_create Action -> active workspace/write lease ->
exact local approval -> local task row -> commit receipt ->
Evidence Timeline local_task_created event
```

The route is typed and non-generic:
`POST /control-center/actions/{action_id}/local-task/commit`.

It cannot commit unsupported action kinds, connector writes, shell/subprocess
work, model/provider calls, memory writes, context injection, external side
effects, public beta claims, production readiness, standing authority, or broad
autonomy.
