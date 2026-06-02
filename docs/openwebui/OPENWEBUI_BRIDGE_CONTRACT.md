# OpenWebUI Bridge Contract

Status: Active M21 contract documentation for v0.25.0. Contract-only.

OpenWebUI is the preferred conversational web shell for the Ultimate AI Agent. OpenWebUI is not the agent brain. Python Agent Core remains the authority layer for policy, approvals, consent, tool authorization, event logging, secrets, redaction, memory governance, runtime boundaries, and Foundation Gate evidence.

M21 defines the future bridge contract only. No OpenWebUI integration is implemented. No OpenWebUI deployment config is added. No Docker Compose file is added. No OpenWebUI plugin, function, pipeline, tool, admin workflow, authentication, cookie, API key, admin token, browser profile access, or live connection is added.

No deployment config is added. No direct tool execution, no direct memory
write, no runtime execution, no provider call, and no backend API route are
added.

OpenWebUI bridge requests must eventually route through Python Agent Core. OpenWebUI must not directly call tools, approve actions, write memory, call model runtimes, call providers, access credentials, bypass Tool Broker, bypass Approval Authority, bypass Consent Ledger, bypass Event Ledger, bypass Secret Broker, bypass Redaction, or bypass Foundation Gate.

M21 adds contract-only Python models for:

- OpenWebUI bridge manifests.
- chat ingress envelopes.
- chat egress envelopes.
- session refs.
- transcript refs.
- message refs.
- validation decisions.
- future bridge plans.
- redacted receipt planning.

Content is summary-only, ref-only, or redacted-preview metadata. Raw content is blocked. Raw prompt bodies, raw transcript bodies, raw files, raw memory contents, raw credentials, cookies, API keys, admin tokens, and browser profile data are not represented by M21 contracts.

This patch adds no backend API route, OpenAPI path, runtime execution, model/provider call, local model runtime activation, memory write, file write, tool execution, remote execution, browser automation, Computer Use, mobile app code, mobile sensor API, plugin enablement, dependency, or production authority.
