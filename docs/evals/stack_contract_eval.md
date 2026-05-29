# Stack Contract Eval v0.5.2

## Purpose

Verify the hybrid stack boundaries: Python Agent Core owns durable policy and execution; TypeScript owns control UI; OpenWebUI is an optional chat shell.

## Pass criteria

```text
Agent Core owns foundation state.
Control Center uses API client only.
OpenWebUI cannot bypass Tool Broker.
OpenAPI/JSON Schema contracts can generate or validate clients.
All mutating calls produce event receipts.
```
