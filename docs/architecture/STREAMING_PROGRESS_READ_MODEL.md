# Streaming And Progress Read Model

Status: backend-owned read-model foundation.

This lane makes progress observable as ordered durable-run metadata. It does not
add live streaming, SSE, WebSockets, provider/model calls, provider SDK calls,
tool execution, connector writes, scheduler behavior, background workers,
autonomous execution, public beta claims, production claims, or raw payload
persistence.

## Scope

The implementation adds:

- `RunProgressReadModel`
- `RunProgressEventReadModel`
- `build_run_progress_read_model`
- `validate_run_progress_event_sequence`
- `append_run_progress_event_receipt`
- repo-local CLI inspection through `inspect-run-progress`

The read model is derived from `AppendFirstRunStorage` ordering. It is a
projection over durable run records and safe progress receipt metadata, not a
separate runtime event bus.

## Data Shape

The progress read model exposes:

- run ref
- sequence start and sequence end
- event count
- latest status
- progress state
- redacted delta refs
- heartbeat refs
- receipt refs
- evidence refs
- blocked state refs
- ordered event refs

Progress events can represent recorded metadata such as:

- `step_started`
- `step_progress`
- `step_blocked`
- `step_completed`
- `stream_started`
- `stream_delta_redacted`
- `stream_heartbeat`
- `stream_completed`
- `stream_failed`
- `stream_canceled`
- `stream_redaction_applied`

The `stream_*` names are contract vocabulary for recorded safe refs only. They
do not mean that a live stream transport, provider stream, tool stream, SSE, or
WebSocket is active.

## Safety Rules

Progress events are safe-ref-only. Validators reject raw-content-shaped fields
and values, including prompt, completion, response, payload, chunk, body,
output, local path, environment dump, credential, cookie, token, secret,
username, hostname, and file-content markers.

Persisted progress receipts contain safe refs and status metadata only. They do
not persist prompt text, response text, provider payloads, tool payloads, local
paths, raw chunks, output bodies, credentials, or secret-like material.

The read model keeps these authority flags hard-false:

- live streaming runtime
- SSE/WebSocket transport
- provider streaming
- tool streaming
- provider/model calls
- background worker
- scheduler
- mutation controls
- execution performed

## Ordering

Ordering comes from the append-first durable run storage sequence. Bounded reads
may show only the last `N` events, but sequence numbers preserve their original
durable append positions.

Terminal stream-like progress states require a terminal progress event when a
run reaches a completed, failed, or canceled progress state with stream-like
events present.

## Inspection

CLI inspection uses the same backend-owned durable state:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-run-progress task-decomposition-run:example
```

No API route or Control Center panel is added in this lane. Future API or UI
surfaces must remain read-only unless a later accepted authority lane adds exact
mutation contracts, route classification, OpenAPI coverage, CLI parity, and
tests.

## Non-Goals

- No live stream transport.
- No SSE or WebSocket surface.
- No provider/model calls.
- No provider SDK calls.
- No tool execution.
- No connector writes.
- No background worker or scheduler.
- No run start, resume, cancel, or retry mutation.
- No raw prompt, completion, response, provider payload, tool payload, raw
  chunk, output body, local path, credential, cookie, token, username, hostname,
  or secret-like persistence.

## Verification

Focused verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_streaming_progress_read_model.py
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_truth.py
```
