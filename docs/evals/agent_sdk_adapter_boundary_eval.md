# Agent Sdk Adapter Boundary Eval

Status: Planned foundation eval.

## Purpose

Verify OpenAI Agents SDK and Claude Agent SDK adapters preserve Execution Contract, Consent Ledger, Tool Broker, Event Ledger, redaction, rollback, and result envelope boundaries.

## Pass criteria

```text
No bypass of Agent Core boundaries.
No secrets or raw private memory are exposed.
Required metadata is logged.
Failures are explicit and fail closed.
```
