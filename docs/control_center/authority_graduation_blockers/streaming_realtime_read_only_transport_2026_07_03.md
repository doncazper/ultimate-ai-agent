# Streaming / Realtime Read-Only Transport Blocker

Status: blocked, no live streaming transport promoted
Lane: Streaming / Realtime Transport
Attempted promotion: Level 1 read-only progress stream
Date: 2026-07-03

## Existing Verified Posture

UAA already has a backend-owned run progress read model:

- doc: `docs/architecture/STREAMING_PROGRESS_READ_MODEL.md`
- core: `src/ultimate_ai_agent/core/execution/read_models.py`
- CLI:
  `PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run-progress`
- tests: `tests/test_streaming_progress_read_model.py`

The read model projects ordered durable-run metadata and safe progress refs from
append-first storage. It supports progress vocabulary such as
`stream_started`, `stream_delta_redacted`, and `stream_heartbeat`, but those
names are recorded metadata only. They do not mean that live SSE, WebSocket,
provider stream, tool stream, or external realtime transport is active.

## Why This Was Not Unblocked

The requested promotion requires a read-only SSE/WebSocket or equivalent
transport for existing run refs, local/auth policy, reconnect behavior, redacted
events, polling fallback, and tests proving the stream never accepts mutation
or control messages.

That promotion was not safe in this run because:

- no live stream transport route exists;
- no auth/local policy exists for stream subscription;
- no reconnect or cursor contract exists;
- no polling fallback contract is bound to the stream route;
- no no-control-channel verifier exists;
- no route side-effect classification exists for a streaming endpoint;
- current docs and tests explicitly deny SSE/WebSocket/live streaming runtime.

## Missing Contract / Test / Evidence

- exact stream route and operation ID;
- local/auth subscription policy;
- run-ref allowlist and unknown-run denial;
- reconnect cursor and bounded replay behavior;
- polling fallback route/CLI equivalence;
- redacted event schema with safe refs only;
- tests proving no POST/control/mutation channel exists over the stream;
- disconnect/reconnect tests;
- route status/OpenAPI/API manifest updates;
- Control Center presentation, if added, bound to backend truth only.

## Smallest Next Safe Action

Run a dedicated streaming transport unblock PR that adds only a read-only local
progress transport for existing durable run refs. It must not add run start,
resume, cancel, retry, provider streaming, tool streaming, connector delivery,
worker scheduling, or external realtime transport authority.

## Authority Still Blocked

- live SSE/WebSocket/realtime transport
- streamed tool execution
- live control messages
- run start/resume/cancel/retry over a stream
- provider/model streaming by default
- provider SDK calls
- connector writes/sends
- shell/browser/live web execution
- background workers or schedulers
- external realtime transport authority
- raw prompt/response/provider/tool payload/chunk persistence
- public beta, public release, or production authority
