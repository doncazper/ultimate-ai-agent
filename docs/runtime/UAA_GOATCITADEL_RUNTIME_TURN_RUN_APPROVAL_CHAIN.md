# UAA GoatCitadel Runtime Turn Run Approval Chain

Status: implemented as Phase 03 of the UAA GoatCitadel runtime parity pack.

This lane defines a UAA-native canonical chain for Turn -> Durable Run ->
Approval -> Result/Evidence/Recovery. It borrows GoatCitadel's state semantics
as a reference pattern only. It does not copy GoatCitadel code or import
GoatCitadel packages. It does not add runtime authority.

## Implemented Repo-Safe Slice

Python Agent Core now owns `TurnRunApprovalChainReadModel` with safe-ref
contracts for:

- `TurnRef`
- `DurableRunRef`
- `ApprovalRef`
- `CheckpointRef`
- `ReceiptRef`
- `RouteDecisionBindingRef`

The canonical chain states are:

- `created`
- `routed`
- `planning`
- `waiting_for_approval`
- `approved`
- `running`
- `retry_scheduled`
- `paused`
- `resumed`
- `cancelled`
- `failed`
- `blocked`
- `completed`

Transitions are append-only, replayable, idempotency-bound, safe-ref-only, and
receipt/evidence-backed. Approval refs remain identifiers only. A route
decision binding is not approval, and an approval cannot advance or resume a
changed run scope.

The CLI inspection path is:

```bash
.venv/bin/python scripts/dev/uaa_runtime.py inspect-turn-run-approval-chain --json
```

## Boundaries Preserved

This is a durable read-model and state-validation lane only. It does not add
background autonomy, provider/model calls, provider SDK calls, live web
fetching, browser automation, connector writes, plugin runtime import,
unrestricted shell/subprocess execution, remote execution, production
authority, public release claims, or broad autonomy.

Control Center can later display this backend-owned chain, but Control Center cannot mint authority.
Any future resume, run-start, retry, cancel, or execute
path must validate exact LocalApprovalAuthority scope, route-decision binding
freshness, idempotency, safe-disable posture, receipts, redaction, and route
side-effect classification before it can mutate anything.

## Evidence

- `src/ultimate_ai_agent/core/execution/turn_run_approval_chain.py`
- `src/ultimate_ai_agent/core/execution/__init__.py`
- `scripts/dev/uaa_runtime.py`
- `tests/test_turn_run_approval_chain.py`
- `scripts/verify_uaa_goatcitadel_runtime_turn_run_approval_chain.py`

## Still Blocked

- runtime model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes
- unrestricted shell/subprocess execution
- plugin runtime import
- remote execution
- production authority
- public release claims
- broad autonomy
- raw prompt, raw response, raw provider payload, raw local path, raw log,
  credential, or secret-like persistence

## Promotion Path

Later phases can attach the chain to staged orchestration, chat-turn
preparation, role-based provider evidence, exact action receipts, and cockpit
surfaces. Each attachment must keep Python Agent Core as durable truth, preserve
CLI/API/Core parity, expose blocked states honestly, and prove that approval
scope and route-decision scope cannot drift before any mutation.
