# UAA Hermes Runtime Run Events

Status: Phase 03 AuthorityState-bound repo-safe read/proposal model.

UAA now exposes a backend-owned runtime run/event posture for optional Hermes
delegation. This is not a live runs API. It models lifecycle states, event refs,
stop posture, and approval-wait state under the Read-only `workspace/read`
AuthorityLease decision without creating, stopping, approving, or streaming
delegated runtime runs.

Implemented:

- Python Core `RuntimeRunEventsReadModel`.
- Lifecycle mapping from external runtime states to UAA durable run states.
- Safe event-ref grammar with proof binding and redaction status.
- One approval-wait proposal sample with blocked create, stop, approval
  resolution, retry/recovery, and live stream flags.
- AuthorityState binding as `lane-ref:runtime-run-events-read-model`, with
  route/CLI refs, catalog ref, decision ref, decision outcome, reason refs,
  unsupported adapter refs, and a decision-bound snapshot hash.
- `GET /api/runtime/run-events`.
- `scripts/dev/uaa_runtime.py inspect-run-events`.
- Control Center `/runtime` display of proposal, event, proof, and blocked
  posture plus the AuthorityState mapping and decision refs.

Blocked:

- POST run creation.
- Stop/cancel execution.
- Approval resolution sent to Hermes or any runtime.
- Live event streaming.
- Retry/recovery execution.
- Runtime model calls, provider SDK calls, tool execution, shell/subprocess
  execution, browser automation, connector writes, plugin runtime import,
  background autonomy, remote execution, production authority, and raw prompt,
  response, provider payload, runtime event payload, log, local path, or
  credential persistence.

Promotion path:

1. Add idempotent run creation with an exact approval envelope.
2. Bind runtime run refs to UAA durable run refs, receipt refs, proof refs, and
   safe-disable posture.
3. Add redacted event ingestion or streaming with bounded retention.
4. Prove cancellation/stop receipts and replay behavior.
5. Bind approval waits to Action Inbox scopes without treating approval refs as
   execution authority.
6. Add CLI/API/Core/Control Center parity plus focused state-transition,
   redaction, route-classification, and no-fake-completion verifiers.
