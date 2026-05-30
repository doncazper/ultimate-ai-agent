# A2A Interop Contract Eval

Status: Planned foundation eval.

## Purpose

Verify A2A client/server adapters expose only allowed Agent Cards, do not leak internal memory/secrets, and route remote-agent tasks through local approval and event logging.

## Pass criteria

```text
No bypass of Agent Core boundaries.
No secrets or raw private memory are exposed.
Required metadata is logged.
Failures are explicit and fail closed.
```
