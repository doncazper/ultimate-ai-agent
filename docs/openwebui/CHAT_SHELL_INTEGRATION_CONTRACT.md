# Chat Shell Integration Contract

Status: Active M21 contract documentation for v0.25.1. Contract-only.

OpenWebUI is a supported local/dev conversational shell and compatibility
surface. The proprietary first-party chat product surface belongs in Control
Center / Founder Command Center. Future chat shell integration must use Python
Agent Core as the authority layer and must never make OpenWebUI the agent
brain or the source of product state.

Future chat ingress envelopes describe user-to-Agent-Core messages using safe refs and user-visible summaries. Future chat egress envelopes describe Agent-Core-to-user summaries using redacted metadata. Both envelope directions are planning contracts in M21 and do not create a runtime bridge.

Ingress rules:

- raw content is blocked.
- secret-like content is denied.
- direct tool execution is denied.
- direct memory write is denied.
- direct runtime execution is denied.
- direct provider calls are denied.
- arbitrary approval refs are not authority.
- OpenWebUI session refs are not authority.

Egress rules:

- model output is non-authoritative.
- action execution is denied.
- tool execution is denied.
- memory writes are denied.
- provider calls are denied.
- runtime calls are denied.
- approval grants are denied.
- receipt refs and event refs must be redacted safe refs.

All future agent work must go through Python Agent Core and the governed stack: Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, and Foundation Gate. Future raw chat content handling requires a later reviewed contract before any implementation.

M21 adds no OpenWebUI integration, deployment config, backend API route, model/runtime/provider call, memory write, file write, tool execution, approval execution, external network call, dependency, or production authority.
