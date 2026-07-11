# AuthorityLease Local Mission Worker V1

Status: implemented local macOS-first worker; disabled by default

Date: 2026-07-10

## Boundary

The local mission worker adds bounded background scheduling around the existing
`MissionOrchestrator -> AuthorityMissionRunner -> AuthorityDispatcher` path. It
now supports durable approval-wait posture, exact typed retries for explicitly
idempotent adapters, immutable dead letters, and append-first cancellation. It
does not add another execution path, remote queue, public daemon, production
scheduler, automatic approval authority, dead-letter replay, safe after-start
cancellation, or Control Center mutation.

Activation requires `UAA_LOCAL_MISSION_WORKER_ENABLED=1` on macOS and an active
mission-scoped `AuthorityLease` that matches the immutable plan and every step.
Configuration, worker refs, claims, and heartbeats never grant authority.
Policy, lease, approval, budget, adapter, target, deadline, safe-disable, and
kill-switch posture are re-evaluated before each one-step orchestration slice
and inside the dispatcher's locked durable-start boundary.

Linux and Windows operator surfaces are `render_placeholder` only. The Python
core remains testable on hosted Linux CI, but executable local-worker activation
is macOS-only in V1.

## Durable truth

`local_mission_worker_receipts.jsonl` is bounded, append-only, fsync-backed,
hash-chained, transition-validated, and protected by hardened no-follow regular
file locks. It stores only safe refs and fingerprints: job, plan, mission, run,
ordered step, dispatch-request fingerprint, worker, claim, generation,
deadline, heartbeat, reason, and evidence refs.

It never stores the orchestration request, tool input, path, file content, raw
output, provider payload, log, prompt, response, credential, environment dump,
username, or hostname. After restart an injected request resolver must
re-supply the exact request. The worker revalidates the whole plan and every
fingerprint; missing material remains pending and changed material is rejected
before claim or start. Fully unattended reboot will need a future safe-ref
target registry rather than raw request persistence.

## Fencing, heartbeat, and recovery

Queue claims and mission-step claims use monotonic generations and bounded TTL
heartbeats. Claim takeover and dispatcher start fencing serialize on the same
authority-state lock. The dispatcher persists an `execution_fence_ref` only
after current job and step claims match the worker, generations, request
fingerprint, and trusted time. Stale workers cannot start adapters.

Boot inspection derives `pending`, `actively_claimed`, `stale_claim`,
`prepared_dispatch`, `started_unknown_terminal`, `succeeded`, `failed`,
`dependency_blocked`, and `recovery_required` without executing recovery. A
durable `started` or `cancellation_pending` dispatch is never invoked again.
Prepared dispatches resume only after exact request resolution and fresh
request-scoped authority checks. An approval decision receipt is durable
operator intent only. It never grants execution authority, and a resumed worker
must freshly validate `LocalApprovalAuthority`, policy, lease, budget, kill
switch, adapter, target, deadline, idempotency, and safe-disable posture before
the dispatcher's locked pre-start boundary.

Graceful shutdown stops new slices and releases the queue claim between steps.
`UAA_AUTHORITY_LEASE_KILL_SWITCH=1` blocks new claims or starts. V1 is
fail-fast, one local worker, and one mission slice at a time. Retry defaults to
off. A retry may occur only for a prebound typed retry category, an explicitly
idempotent adapter, an unchanged request fingerprint, an exact mission-lease
retry constraint, remaining deadline and budget, and a fresh dispatcher
evaluation. Unknown execution truth and authority or approval denial never
retry. Exhaustion becomes a durable dead letter with no automatic replay.

## Inspection parity

- API: `GET /api/runtime/authority-missions/worker-state`
- CLI: `scripts/dev/uaa_runtime.py inspect-authority-mission-worker`
- Safe JSON: add `--json`

Both use the same backend-owned redacted projection. Inspection is protected,
read-only, and cannot enqueue, claim, heartbeat, reconcile, start, approve,
issue a lease, or mint authority. The Hermes
`GET /api/runtime/background-jobs` contract remains proposal-only.

The separate protected failure-management API and CLI record exact approval
decisions, cancellation fences, and dead-letter recovery intent. These surfaces
append safe operator state only; they do not resume a worker, grant authority,
or execute an adapter.

Parallel execution, remote queues, public or production daemons, default-on
execution, restart-time approval-request resolver proof,
automatic dead-letter replay, retries for unknown execution truth, safe
after-start cancellation, mission-level settlement recovery, provider/model
calls, browser or connector actions, broad shell, and Control Center mission
controls remain separate milestones.
