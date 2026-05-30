# 58 — Agent SDK and A2A Adapter Strategy

Status: Active foundation contract in v0.5.5.

## Decision

The Ultimate AI Agent will not depend on one vendor agent SDK as its brain. It will own its Agent Core and support external agent runtimes through adapters.

## Supported adapter classes

```text
openai_agents_sdk_adapter
claude_agent_sdk_adapter
responses_api_adapter
anthropic_client_sdk_adapter
local_openai_compatible_runtime_adapter
mcp_tool_server_adapter
a2a_client_adapter
a2a_server_adapter
custom_internal_agent_adapter
```

## Roles

```text
OpenAI Agents SDK
  Optional managed agent-runtime adapter for workflows where its tools, handoffs, sessions, guardrails, tracing, or sandbox agents are useful.

Claude Agent SDK
  Optional coding/local-filesystem agent adapter. Must be restricted so built-in Read/Edit/Bash/Web tools cannot bypass our Tool Broker, Consent Ledger, Event Ledger, redaction, or rollback.

MCP
  Agent-to-tool/resource protocol. MCP servers are tools/resources, not trusted authorities.

A2A
  Agent-to-agent interoperability protocol. Use for external agent discovery, delegation, and collaboration after the internal kernel is stable.
```

## Boundary rule

External SDKs may perform work only inside an adapter boundary. The adapter must translate between the external runtime and our native contracts:

```text
Execution Contract
Context Pack
ActorContext
Consent/approval references
Tool Broker policy
Event Ledger events
Result/Error Envelope
Rollback metadata
Data classification and redaction
Cost attribution
```

## Hard prohibitions

- No external SDK may directly write memory, canonical files, secrets, event logs, or tool state.
- No external SDK may directly execute high-risk tools without Tool Broker approval.
- No external SDK session state is canonical unless imported through Event Ledger and World State.
- No A2A remote agent may receive secrets, raw private memory, or internal chain-of-thought.
- No A2A remote agent may trigger external side effects without our local approval path.

## Foundation sequencing

Agent SDK/A2A support is documentation and adapter contract only before M6. Real integration waits until the Foundation Gate has passed or a tightly scoped adapter spike is approved.
