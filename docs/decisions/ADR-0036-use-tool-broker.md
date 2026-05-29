# ADR-0036: Use a Tool Broker for All Tool Actions

Status: Accepted in v0.4.8

## Context

The Ultimate AI Agent will use files, memory, code execution, web research, scanners, email/messages, calendars, APIs, and possibly self-modifying skills. Direct tool access by arbitrary agents would be unsafe and impossible to audit.

## Decision

All tool calls must go through the Tool Broker. The Tool Broker validates schemas, checks Execution Contracts, checks Consent Ledger, classifies risk, requests approval, enforces dry-run/rollback, executes tools, validates outputs, and logs events.

## Consequences

Positive:
- Centralized safety and audit layer.
- Easier tool lifecycle management.
- Prevents untrusted content from directly triggering tools.
- Enables rollback-first design.

Tradeoffs:
- Adds runtime overhead and integration work.
- Requires tool manifests and contract tests for each tool.
