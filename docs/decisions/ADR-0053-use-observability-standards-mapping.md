# ADR-0053: Use Observability Standards Mapping

Status: Accepted
Date: 2026-05-30

## Context

The Ultimate AI Agent needs an authoritative Event Ledger for audit, replay, receipts, cost attribution, rollback, and verification. At the same time, modern agent systems should integrate with standard observability tooling and distributed trace propagation.

## Decision

Keep the Event Ledger as the internal source of truth, but design M2 events so they can map to:

```text
OpenTelemetry GenAI semantic conventions
W3C Trace Context
CloudEvents export envelopes
AsyncAPI documentation for future message-driven APIs
OpenAPI for HTTP API boundaries
JSON Schema for internal contract validation
```

## Consequences

Benefits:

```text
Improves future observability/tooling compatibility.
Avoids vendor lock-in.
Supports distributed tracing across API, workers, tools, models, providers, MCP, and A2A adapters.
Makes future event streams easier to document and govern.
```

Tradeoffs:

```text
Adds some fields and naming discipline to early Event Ledger design.
Requires redaction before any external telemetry export.
Does not replace internal ledger semantics with external standards.
```

## Non-goals

```text
Do not implement a full OpenTelemetry collector in M0.
Do not expose raw prompts, secrets, private content, or unredacted payloads in traces.
Do not let external telemetry standards override Consent Ledger, Tool Broker, rollback, or evidence-governance rules.
```
