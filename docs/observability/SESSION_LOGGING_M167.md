# M167 Session Logging + Redacted Observability Spine

Status: shipped under the M167+ scoped productionization lane
Baseline: v2.0.0 / 2.0.0
Scope: passive local observability for UAA-managed app and session behavior only

This document defines the current M167 local session logging spine. It is a
production-readiness support feature for debugging UAA-managed startup,
backend, task, capability, ledger, receipt, latency, and Control Center client
failure summaries. It is not surveillance, telemetry export, provider tracing,
terminal capture, browser monitoring, or production autonomy.

## What Is Logged

Session records are redacted JSONL summaries for UAA-managed surfaces:

- launcher lifecycle summaries for the local developer backend, frontend, and
  OpenWebUI shell services
- backend API request lifecycle metadata using route patterns, methods, status
  codes, durations, and safe correlation IDs
- task decomposition audit and node lifecycle summaries linked to durable run,
  evidence, replay, rollback, and receipt refs
- capability execution started, succeeded, failed, timeout, and denied
  summaries
- Control Center client-error summaries with safe component, surface, route
  name, category, correlation ID, and optional stack hash
- passive duration classification for completed, slow, failed, timeout, skipped,
  and waiting-approval UAA-managed operations

## What Is Not Logged

The M167 spine does not record:

- raw prompts, raw provider payloads, raw request bodies, raw response bodies,
  raw files, raw terminal output, raw process streams, screenshots, DOM
  snapshots, storage snapshots, cookies, auth headers, credential material, or
  private content
- full URLs with query strings, arbitrary headers, hostnames, usernames,
  serials, environment dumps, or machine inventory
- OS-wide activity, unmanaged terminal/window activity, browser actions,
  network requests, provider/model calls, plugin execution, shell execution, or
  mobile sensor activity
- external telemetry, SaaS analytics, cloud traces, SIEM export, or public
  distribution evidence

Any future raw forensic/debug mode is out of scope and requires a separate
reviewed milestone.

## Storage

Default local storage is:

```text
.uaa/observability/session_events.jsonl
```

The path is local-only and ignored with other `.uaa/` state. Tests and local
operators may override the root with `UAA_SESSION_LOG_ROOT`. Logging can be
disabled for local troubleshooting with `UAA_SESSION_LOG_ENABLED=0`.

Records are append-friendly JSONL. Listing APIs are bounded by default and
return safe summary projections, not raw JSONL records. Malformed historical
lines are skipped during bounded listing and counted as skipped malformed
records.

Retention is metadata-only in this milestone. Destructive cleanup is not
implemented here. Operators should preserve the JSONL file as local evidence
when investigating a failure, or remove the ignored `.uaa/` local state only
through the separate rollback/safe-disable runbooks when that is appropriate.

## Schema

The canonical schema version is:

```text
uaa.session_event.v1
```

Core fields include:

- `event_id`, `session_id`, `run_id`, `trace_id`, `span_id`,
  `parent_span_id`, and `correlation_id`
- `service`, `surface`, `event_type`, `lifecycle_state`, `status`, and
  `severity`
- `started_at`, `completed_at`, `observed_at`, and `duration_ms`
- `safe_summary`, `reason_codes`, `error_code`, `error_summary`, and
  `stack_hash`
- prompt lineage fields limited to safe refs, hashes, and template IDs
- `input_refs`, `output_refs`, `evidence_refs`, and `receipt_refs`
- `redaction_summary` and bounded safe `metadata`

Unsafe metadata keys are rejected when they indicate raw content, bodies,
payloads, prompts, completions, responses, process streams, terminal output,
file content, cookies, authorization, tokens, secrets, keys, passwords,
credentials, or identity tokens. Secret-looking values, multiline values,
private local path-looking values, and oversized values are also rejected.

On rejection, the unsafe record is not persisted and the validation error is a
safe code only.

## Inspection

Use the read-only local API summary route for recent events:

```text
GET /observability/session-events
```

Useful filters include `session_id`, `run_id`, `event_type`, `severity`,
`status`, `surface`, `service`, `observed_after`, `observed_before`, and
`limit`. The response is bounded and safe-summary-only.

Control Center client errors may be reported locally through:

```text
POST /observability/client-errors
```

The endpoint accepts safe labels, a safe error message, an optional stack hash,
and correlation IDs. It does not accept raw stacks, DOM snapshots, storage
snapshots, cookies, credentials, raw user input, request bodies, response
bodies, provider payloads, or private content.

## Startup And Health Evidence

Launcher evidence uses event types such as:

- `launcher.start_requested`
- `service.start_requested`
- `service.process_spawned`
- `service.health_ready`
- `service.health_timeout`
- `service.process_exited`
- `launcher.stop_requested`

Structured records include service name, PID when available, duration, status,
reason codes, and a safe launcher log ref. They do not copy process stdout or
stderr into the structured session log.

To inspect a startup failure, filter:

```text
service=dev_launcher
status=failed
```

or:

```text
event_type=service.health_timeout
```

Then use the safe launcher log ref to locate the separate local process log
through the developer launcher docs. Do not paste process logs into release
evidence.

## Crash, Failure, Slow, And Timeout Evidence

Failures use redacted summaries and safe error codes. Raw stack traces are not
stored. When a client or integration can provide a stack hash, the hash may be
stored as `stack_hash` for grouping without retaining the stack.

Slow and timeout-like states are passive. M167 records `duration_ms` for
completed UAA-managed operations and classifies slow or timeout states only
inside existing request, task, capability, or launcher boundaries. It does not
add watchdogs, background monitors, process killers, OS-level stuck detection,
or unmanaged app observation.

## Task, Capability, Ledger, And Receipt Correlation

Task decomposition audit events are projected into session events with
`session_id`, `run_id`, `trace_id`, `span_id`, and `correlation_id`. Node
events use safe node refs and safe capability refs. Durable run, evidence,
replay, rollback, and receipt refs are linked when available.

Capability execution events record lifecycle state, reason codes, duration,
safe capability refs, and safe input/output refs. They do not copy raw
arguments, raw outputs, files, terminal output, provider payloads, or private
content.

Ledger and receipt data remain authoritative in their existing systems. M167
links to ledger, evidence, and receipt refs rather than duplicating payloads.

## Prompt Lineage

Prompt lineage is represented only by safe refs, hashes, template IDs, redacted
previews produced elsewhere, and safe input/output refs. M167 does not capture
raw prompts to compute hashes and does not make model/provider output
authoritative.

## Limitations

- No destructive retention cleanup is implemented in this milestone.
- No external telemetry/export is implemented.
- No Control Center rich observability dashboard is claimed; only bounded local
  API summaries and client-error reporting are implemented.
- No background monitor, watchdog, or process-control behavior is added.
- No raw forensic/debug mode is implemented.

## Verification

Focused regression coverage:

```text
PYTHONPATH=src .venv/bin/python -m pytest tests/test_session_logging.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_dev_launcher.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
