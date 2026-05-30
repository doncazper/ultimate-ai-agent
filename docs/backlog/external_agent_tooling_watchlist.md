# External Agent Tooling Watchlist

Status: Backlog reference, v0.5.8 cleanup
Owner: Commander / Architecture

## Purpose

Track open-source and vendor agent tools that may provide useful ideas, benchmarks, or future adapters without allowing them to become the Ultimate AI Agent's core authority.

## Watchlist

```text
Gemini CLI
OpenHands
Goose
Aider
Continue
Claude Code / Claude Agent SDK
OpenAI Agents SDK / Codex-style coding tools
GitHub Copilot agent workflows
Cursor / Roo Code / Cline / OpenCode-style coding agents
```

## Evaluation use cases

```text
competitor parity
developer-assist workflows
adapter boundary tests
coding-agent benchmarks
CLI and desktop UX ideas
sandboxing and repo-map ideas
event streaming and trace format ideas
CI review/check patterns
```

## Hard rule

External coding agents and SDKs may assist development, but they may not bypass the Ultimate AI Agent's:

```text
Agent Core
Execution Contract
Context Pack
Tool Broker
Consent Ledger
Event Ledger
Secret Broker
Evidence Manifest
redaction policy
rollback rules
capability flags
Trusted Computing Base
Foundation Gate
```

## Current decision

Keep these tools as inspiration, benchmark targets, dev-assist utilities, or future controlled adapters. Do not make them the orchestrator, permission layer, memory layer, event ledger, or source of truth.
