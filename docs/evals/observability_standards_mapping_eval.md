# Eval — Observability Standards Mapping

## Goal

Verify that Event Ledger records can be mapped to external observability standards without losing core agent governance semantics.

## Checks

```text
agent.run maps to an agent span.
model.call maps to a model span.
tool.call maps to a client/tool span.
error events map to exception events.
cost events map to metrics or attributed events.
redaction is applied before export.
internal Event Ledger remains authoritative.
```

## Pass criteria

All required event types have stable mapping metadata and no exported payload includes raw secrets, private content, or unredacted prompts.
