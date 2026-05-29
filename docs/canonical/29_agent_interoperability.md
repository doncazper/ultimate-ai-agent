# 29 — Agent Interoperability

Status: Future-facing interoperability spec, v0.5.3
Owner: Ecosystem / Integrations

## Purpose

Define how the Ultimate AI Agent will later interoperate with tools, data sources, and other agents without collapsing its trust model.

## Split of concerns

```text
MCP-style servers: tools, resources, prompts, data sources.
A2A-style protocols: independent agents communicating or delegating.
Provider Registry: external APIs normalized behind adapters.
Tool Broker: only allowed action path.
Consent Ledger: user permission boundary.
Event Ledger: audit boundary.
```

## Rules

```text
External agents are untrusted by default.
No external agent can call tools directly.
No external tool/server can write memory directly.
Capability manifests must declare permissions and data access.
Interoperability stays blocked until Foundation Gate passes.
```

## First implementation stance

Do not implement agent-to-agent collaboration in the foundation. Implement stable API boundaries and tool/provider manifests first.
