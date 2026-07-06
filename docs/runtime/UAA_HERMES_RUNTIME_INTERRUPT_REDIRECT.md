# UAA Hermes Runtime Interrupt / Redirect Posture

Status: Phase 37 repo-safe read model.  
Route: `GET /api/runtime/interrupt-redirect`  
CLI: `scripts/dev/uaa_runtime.py inspect-interrupt-redirect`

## Full-Strength

UAA operators can stop, pause, redirect, revise, or recover active delegated
work safely while UAA remains the authority owner. A full lane would bind a
specific UAA durable run to a specific delegated runtime process or session,
validate the stop or redirect scope, produce an idempotent cancellation or
revision receipt, bind proof, and expose recovery state.

## Repo-Safe

The current implementation is a backend-owned proposal/read model only:

- `RuntimeInterruptRedirectReadModel`
- explicit run-control proposals for pause, stop, redirect, revise, and recover
- route, CLI, proof, verifier, blocked authority, receipt plan, recovery state,
  approval scope, and idempotency refs
- Control Center display of proposal/blocked posture
- strict frontend fallback validation

This lane does not send stop requests, kill processes, mutate runtime state,
persist raw runtime payloads, or execute any runtime control action.

## Blocked / Needs Authority

The following remain blocked:

- live stop POST
- process kill
- runtime mutation
- background autonomy
- unscoped approval reuse
- shell execution
- provider/model calls
- browser automation
- connector writes
- Control Center authority minting
- raw runtime payload persistence
- raw log persistence

## Exact Promotion Path

Promotion requires all of the following before any live stop, redirect, or
recovery action can execute:

1. run ownership contract binding UAA durable run refs to delegated runtime refs
2. exact stop scope and redirect scope
3. idempotency key and replay protection
4. LocalApprovalAuthority scope validation
5. cancellation or redirect receipt
6. proof/event binding
7. recovery state transition contract
8. safe-disable posture
9. redaction verifier
10. CLI/API/Core parity tests

Planning text does not grant authority. Control Center can display and initiate
only backend-owned approval envelopes when a later exact lane exists.
