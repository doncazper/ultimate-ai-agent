# UAA Hermes Runtime Approval Bridge

Status: Phase 04 repo-safe read model.

UAA now exposes a backend-owned runtime approval bridge posture for optional
Hermes delegation. This is not an approval execution API. It models runtime
approval envelopes, Action Inbox projection refs, proof refs, denial preview
refs, timeout default-deny posture, and scope mismatch handling without sending
approval, denial, timeout, or scope-mismatch resolutions to Hermes or any
delegated runtime.

Implemented:

- Python Core `RuntimeApprovalBridgeReadModel`.
- Runtime approval envelope fields for runtime run ref, UAA durable run ref,
  Action Inbox item ref, proof ref, requested scope ref, idempotency key ref,
  side-effect class, timeout policy ref, denial receipt plan ref, and blocked
  authority refs.
- Scope validation that treats mismatches as blocked and keeps approval refs as
  identifiers only.
- Denial, timeout, and scope-mismatch decision previews that produce safe
  receipt-plan refs only.
- Action Inbox projection metadata that visibly separates “runtime requested”
  from “UAA approved.”
- `GET /api/runtime/approval-bridge`.
- `scripts/dev/uaa_runtime.py inspect-approval-bridge`.
- Control Center `/runtime` display of the bridge route, CLI, counts, Action
  Inbox projection, proof refs, and blocked resolution posture.

Blocked:

- Sending approval decisions to Hermes or any delegated runtime.
- Sending denial decisions to Hermes or any delegated runtime.
- Sending timeout/default-deny decisions to Hermes or any delegated runtime.
- Treating an approval ref as authority before exact `LocalApprovalAuthority`
  scope validation.
- Control Center direct runtime access or runtime-resolution controls.
- Runtime model calls, provider SDK calls, tool execution, shell/subprocess
  execution, browser automation, connector writes, plugin runtime import,
  background autonomy, remote execution, production authority, and raw prompt,
  response, provider payload, runtime approval payload, log, local path, or
  credential persistence.

Promotion path:

1. Define an exact runtime approval resolution lane with `LocalApprovalAuthority`
   scope validation and idempotency binding.
2. Bind each runtime approval ref to a UAA durable run ref, Action Inbox item
   ref, proof ref, side-effect class, timeout policy, denial receipt, and
   safe-disable posture.
3. Add default-deny timeout receipts and denial receipts before any runtime
   resolution send is permitted.
4. Prove stale approval and scope-mismatch replay are blocked.
5. Add CLI/API/Core/Control Center parity plus focused approval-scope, denial,
   timeout, idempotency, redaction, route-classification, and no-runtime-send
   verifiers.
