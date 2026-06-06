# 63 — Observability Standards Mapping

Status: Foundation specification, v0.5.7
Owner: Platform / Runtime / Observability
Layer: Layer 0 Kernel; Layer 3 Orchestration

## Purpose

The Ultimate AI Agent should be observable through its own Event Ledger first, while remaining compatible with common observability and eventing standards. This avoids vendor lock-in and lets future deployments export traces, metrics, and events to existing tooling without changing the core agent contracts.

## Core decision

The Event Ledger is authoritative. External standards are mapping/export targets:

```text
OpenTelemetry GenAI semantic conventions -> trace/span/metric/event export target
W3C Trace Context -> trace propagation format across services and tool calls
CloudEvents -> portable event envelope for external event streams
AsyncAPI -> documentation and contract format for future message-driven APIs
OpenAPI -> HTTP API boundary description
JSON Schema -> internal contract/schema validation
```

## OpenTelemetry mapping

M2 Event Ledger records should be designed so they can later export or mirror into OpenTelemetry-compatible telemetry. The initial implementation does not need a full OpenTelemetry collector, but it must preserve the fields needed for future mapping.

Minimum mapping targets:

```text
agent.run -> GenAI agent span
model.call -> GenAI model span
tool.call -> tool / MCP / client span
provider.call -> HTTP/client span plus provider attributes
file.operation -> file/object-store span or structured event
memory.retrieve/write -> database/vector-search span or structured event
approval.request/decision -> structured governance event
eval.run -> test/eval span
error -> exception event
cost -> metric/event attribution
```

## Trace context

Every meaningful run should carry trace-compatible identifiers:

```text
trace_id
span_id or event_id
parent_span_id or parent_event_id
correlation_id
causation_id
run_id
step_id
idempotency_key
```

When crossing API, tool, worker, model-runtime, MCP, A2A, or provider boundaries, the system should preserve trace context where possible.

## CloudEvents compatibility

Internal ledger records may be exported as CloudEvents later. Do not make CloudEvents the internal schema, but keep enough metadata to map reliably:

```text
id -> event_id
source -> service/component/workspace source
type -> event_type
time -> timestamp
subject -> run_id/step_id/resource reference
datacontenttype -> application/json
data -> redacted event payload
traceparent -> W3C traceparent, when available
```

## AsyncAPI compatibility

If the agent later exposes message-driven APIs for scanners, notifications, workflow events, approval queues, or tool execution, those channels should be documented with AsyncAPI. AsyncAPI is not required for M0-M2 code, but event types should be named and versioned consistently enough to document later.

## OpenAPI compatibility

The FastAPI Agent API Boundary should expose OpenAPI documentation for HTTP endpoints. HTTP clients must still go through Execution Contract, Consent Ledger, Tool Broker, Event Ledger, redaction, and rollback rules.

## Redaction and privacy

Exported telemetry must never leak secrets, raw private content, or sensitive prompt payloads. Observability export must use redacted summaries, references, hashes, and source IDs. M55 does not enable forensic trace export; any future forensic mode requires a later reviewed milestone and must remain disabled through M60.

## M2 acceptance addendum

M2 is complete only when:

```text
Event Ledger event fields can map to OpenTelemetry trace/span/event/metric concepts.
Trace-compatible IDs are present on run, step, model, tool, provider, file, memory, approval, eval, and error events.
W3C Trace Context propagation is documented for API/tool/worker boundaries.
CloudEvents export profile is documented for future event bus use.
AsyncAPI is listed as the future contract format for message-driven channels.
Redaction rules apply before any telemetry export.
```
