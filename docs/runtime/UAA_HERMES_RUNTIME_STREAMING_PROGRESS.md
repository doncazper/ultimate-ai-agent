# UAA Hermes Runtime Streaming Progress

Status: Phase 05 AuthorityState-bound read model with bounded read-only preview replay.

UAA exposes a backend-owned runtime streaming progress posture for optional
Hermes delegation. It is not a live runtime subscription, event-ingestion
transport, WebSocket, or control channel. It models ordered, redacted event
previews and may serialize that already-built bounded snapshot as local
read-only `text/event-stream` output. The replay carries proof refs, event hash
refs, stale-stream labeling, bounded preview limits, and blocked live-transport
refs. The read model evaluates as
`lane-ref:runtime-streaming-progress-read-model` under the Read-only
`workspace/read` AuthorityLease decision.

Implemented:

- Python Core `RuntimeStreamingProgressReadModel`.
- Runtime progress event kinds for `token`, `tool_started`,
  `tool_completed`, `warning`, `approval_wait`, `stopped`, `failed`, and
  `completed`.
- Ordered event preview refs bound to runtime run ref, UAA durable run ref,
  proof ref, event hash ref, redaction status, and bounded preview limit.
- Stale/disconnected stream posture that prevents the UI from presenting a
  fixture or local preview as a live runtime stream.
- AuthorityState binding with route/CLI refs, catalog ref, decision ref,
  decision outcome, reason refs, unsupported adapter refs, and a
  decision-bound snapshot hash.
- `GET /api/runtime/streaming-progress`.
- `GET /api/runtime/streaming-progress?transport=sse&run_ref=<safe-ref>` for
  deterministic preview replay only. It materializes the bounded safe-ref
  snapshot before returning, accepts no control messages, and supports an
  explicit `after_sequence` replay cursor.
- `scripts/dev/uaa_runtime.py inspect-streaming-progress`.
- `scripts/dev/uaa_runtime.py inspect-streaming-progress --replay-sse
  --run-ref <safe-ref> [--after-sequence N]` using the same Python Core model.
- Control Center `/runtime` display of the streaming progress route, CLI,
  preview-replay route/CLI/source, event count, stale status, blocked live
  subscription, blocked live SSE/WebSocket transports, event proof refs, event
  hash refs, and blocked transport refs.

Blocked:

- Live SSE subscription to Hermes or any delegated runtime. The implemented SSE
  representation replays deterministic redacted previews only.
- WebSocket subscription to Hermes or any delegated runtime.
- Direct Control Center-to-runtime subscription.
- Live reconnect and durable resume semantics. `after_sequence` only filters the
  current bounded preview snapshot; it does not reconnect to a runtime.
- Runtime event ingestion or durable stream storage beyond redacted preview
  contracts.
- Raw tool payload, raw runtime stream payload, raw generated content, raw log,
  raw prompt, raw response, provider payload, local path, account material, or
  credential persistence.
- Runtime model calls, provider SDK calls, tool execution, shell/subprocess
  execution, browser automation, connector writes, plugin runtime import,
  background autonomy, remote execution, and production authority.

Promotion path:

1. Define an exact read-only loopback or approved live transport lane for
   runtime progress events; do not treat preview replay as that lane.
2. Add durable bounded event retention with event hash verification and redacted
   preview limits.
3. Define live reconnect/resume semantics that degrade stale streams to blocked
   inspection rather than fake liveness.
4. Bind each event to runtime run ref, UAA durable run ref, proof ref,
   receipt/proof spine refs, and redaction status.
5. Prove raw runtime/tool/generated/log payloads are not persisted.
6. Add CLI/API/Core/Control Center parity plus focused ordering, stale-stream,
   redaction, route-classification, retention, and event-hash verifiers.
