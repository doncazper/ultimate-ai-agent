# Eval — Trace Context Propagation

## Goal

Verify that trace-compatible identifiers survive API, worker, model-router, tool-broker, provider, MCP, and A2A adapter boundaries.

## Checks

```text
run_id remains stable across all events in a run.
trace_id remains stable across all spans/events in a run.
parent_event_id or parent_span_id is present when one operation causes another.
correlation_id groups related operations.
causation_id links retries, rollbacks, approvals, and follow-up events.
idempotency_key is present for mutable actions.
```

## Pass criteria

A replay of a Minimum Lovable Kernel trace can reconstruct the causal graph of contract -> context -> tool request -> file mutation -> rollback metadata -> QA receipt.
