# Authority Lane 11: Streaming / Realtime Transport

Goal: Make long-running work visible without turning streams into a control
channel.

Allowed next promotion: Level 1 read-only progress stream.

Scope:

- Existing run refs only.
- SSE/WebSocket or equivalent read-only transport.
- Auth/local policy.
- Redacted progress events.
- Polling fallback.

Still blocked:

- Tool execution over stream.
- Live control messages.
- Provider streaming by default.
- External realtime transport authority.

Promotion condition:

One existing run can stream read-only progress, reconnect safely, and never
accept mutation/control events through the stream.

Tests/verifiers:

- streaming progress read-model tests.
- auth/local tests.
- no mutation over stream tests.
- disconnect/reconnect tests.

If blocked:

Generate an unblock prompt for the missing read model, transport guard,
auth/local policy, or reconnect contract.
