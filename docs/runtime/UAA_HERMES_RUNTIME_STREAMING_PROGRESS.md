# UAA Hermes Runtime Streaming Progress

Status: Phase 05 repo-safe read model.

UAA now exposes a backend-owned runtime streaming progress posture for optional
Hermes delegation. This is not a live stream subscription, SSE, WebSocket, or
direct runtime connection. It models ordered, redacted event previews for
delegated runtime progress with proof refs, event hash refs, stale-stream
labeling, bounded preview limits, and blocked live-transport refs.

Implemented:

- Python Core `RuntimeStreamingProgressReadModel`.
- Runtime progress event kinds for `token`, `tool_started`,
  `tool_completed`, `warning`, `approval_wait`, `stopped`, `failed`, and
  `completed`.
- Ordered event preview refs bound to runtime run ref, UAA durable run ref,
  proof ref, event hash ref, redaction status, and bounded preview limit.
- Stale/disconnected stream posture that prevents the UI from presenting a
  fixture or local preview as a live runtime stream.
- `GET /api/runtime/streaming-progress`.
- `scripts/dev/uaa_runtime.py inspect-streaming-progress`.
- Control Center `/runtime` display of the streaming progress route, CLI,
  event count, stale status, blocked live subscription, blocked SSE/WebSocket
  transports, event proof refs, event hash refs, and blocked transport refs.

Blocked:

- Live SSE subscription to Hermes or any delegated runtime.
- WebSocket subscription to Hermes or any delegated runtime.
- Direct Control Center-to-runtime subscription.
- Reconnect/resume semantics.
- Runtime event ingestion or durable stream storage beyond redacted preview
  contracts.
- Raw tool payload, raw runtime stream payload, raw generated content, raw log,
  raw prompt, raw response, provider payload, local path, account material, or
  credential persistence.
- Runtime model calls, provider SDK calls, tool execution, shell/subprocess
  execution, browser automation, connector writes, plugin runtime import,
  background autonomy, remote execution, and production authority.

Promotion path:

1. Define an exact read-only loopback or approved transport lane for runtime
   progress events.
2. Add bounded event retention with event hash verification and redacted
   preview limits.
3. Define reconnect/resume semantics that degrade stale streams to blocked
   inspection rather than fake liveness.
4. Bind each event to runtime run ref, UAA durable run ref, proof ref,
   receipt/proof spine refs, and redaction status.
5. Prove raw runtime/tool/generated/log payloads are not persisted.
6. Add CLI/API/Core/Control Center parity plus focused ordering, stale-stream,
   redaction, route-classification, retention, and event-hash verifiers.
