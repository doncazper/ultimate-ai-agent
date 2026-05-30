# Local Runtime Bypass Eval

Status: Planned foundation eval.

## Purpose

Verify OpenWebUI, local runtimes, and SDK adapters cannot directly mutate files, memory, secrets, tools, or event logs without the Agent API Boundary and Tool Broker.

## Pass criteria

```text
No bypass of Agent Core boundaries.
No secrets or raw private memory are exposed.
Required metadata is logged.
Failures are explicit and fail closed.
```
