# ADR-0038: Use OpenWebUI as Chat Shell, Not Agent Brain

Status: Accepted

## Context

The project needs a quick chat surface during early development, but the agent also needs controlled memory, permissions, tool access, event logs, rollback, model routing, and canonical files.

A UI shell should not own the durable core of the assistant.

## Decision

Use OpenWebUI as an optional early chat UI and model playground. Do not use it as the source of truth, memory system, tool execution authority, scanner scheduler, or self-improvement runtime.

OpenWebUI may connect to the Agent Core through:

```text
OpenAI-compatible Agent Gateway
pipeline/proxy
MCP/OpenAPI bridge mediated by Tool Broker
```

## Consequences

Benefits:

```text
Fast early chat UX.
Can test local/cloud models quickly.
Avoids building custom chat before the brain exists.
Keeps durable state and permissions inside our Agent Core.
```

Risks:

```text
OpenWebUI extensibility can bypass our controls if misused.
Developers may be tempted to put business logic in UI functions.
```

## Guardrail

OpenWebUI Functions, pipelines, or extensions must not directly mutate memory, files, consent, event logs, tools, or external systems. They must call Agent Core APIs and allow the Tool Broker/Event Ledger to control the action.
