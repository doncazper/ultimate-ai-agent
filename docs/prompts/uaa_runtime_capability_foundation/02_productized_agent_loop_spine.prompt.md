# Phase 02: Productized Founder Loop And Mission Completion

Goal: complete one genuinely useful bounded workflow:

operator input -> intent assessment -> immutable plan -> action proposal ->
exact approval -> mission-scoped AuthorityLease -> MissionOrchestrator ->
AuthorityMissionRunner -> AuthorityDispatcher -> exact adapter -> terminal
receipt and evidence -> reviewable memory candidate.

## Required Work

1. Reuse the existing synchronous DAG, failure-management, approval-wait,
   retry, dead-letter, cancellation, dispatcher, budget, evidence, Founder Loop,
   API, CLI, and Control Center contracts.
2. Choose one already implemented low-risk exact adapter. Do not fake an
   adapter and do not broaden its authority.
3. Bind immutable plan membership, dependency edges, definition and request
   fingerprints, exact targets, mission/run refs, deadlines, approval scope,
   lease scope, idempotency, and terminal receipts.
4. Finish mission-wide operation, time, cost, and concurrency budgets with
   atomic reserve/start/settle/release, unresolved-cost posture, concurrency
   protection, and crash-safe settlement recovery.
5. Produce a content-free completion manifest bound to plan fingerprint, lease,
   approvals, dispatcher evidence, budget settlement, cancellation/dead-letter
   posture, step terminal receipts, redaction status, and safe refs.
6. Add deterministic offline completion verification. Do not claim signatures
   unless real key-backed signing and verification exist.
7. Expose the same backend truth across existing CLI/API/macOS UI surfaces.

## Required Proofs

- bounded success from operator input through reviewable memory candidate;
- approval expiry and revocation;
- lease revocation;
- budget exhaustion and unknown metered budget;
- kill switch and safe-disable;
- changed request or target;
- duplicate concurrent start;
- cancellation race;
- crash during settlement;
- unchanged replay without double execution or charge; and
- no unsafe durable payloads.

## Authority Boundary

Every start flows only through MissionOrchestrator -> AuthorityMissionRunner ->
AuthorityDispatcher. Inside the final locked pre-start boundary, re-evaluate
policy, exact approval, current mission lease, capability/adapter/provider/
target, mission/run, TTL/deadline, budget, kill switch, safe-disable,
readiness, idempotency, and replay posture.

## Exit

One bounded useful workflow is real, receipt-backed, crash/replay safe, and
operator-visible. Unsupported adapters remain explicitly blocked.
