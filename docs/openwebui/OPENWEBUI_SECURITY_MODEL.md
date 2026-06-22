# OpenWebUI Security Model

Status: Active M21 contract documentation for v0.25.1. Contract-only.

OpenWebUI is a supported local/dev conversational shell and compatibility
surface, not the agent brain, not the proprietary product cockpit, and not the
source of product state. Python Agent Core remains authority. Control Center /
Founder Command Center is the first-party product UI path.

Primary risks:

- prompt injection through chat content.
- malicious or forged chat refs.
- session confusion.
- transcript confusion.
- credential leakage.
- cookie, API key, admin token, or session token exposure.
- browser profile data exposure.
- plugin, function, pipeline, or tool bypass.
- direct memory writes.
- direct tool execution.
- direct runtime/model/provider calls.
- model output being treated as truth or control authority.

Controls:

- Python Agent Core authority.
- Approval Authority for governed actions.
- Consent Ledger for user permission state.
- Tool Broker for tool authorization.
- Event Ledger for auditable records.
- Secret Broker for credential boundaries.
- Redaction for summaries and refs.
- Foundation Gate and verifier scripts for release checks.
- summary-only, ref-only, or redacted-preview contracts.
- raw content blocked until a later reviewed contract.

M21 adds no OpenWebUI integration, deployment config, Docker Compose, plugin/function/pipeline/tool bridge, authentication, cookies, API keys, admin tokens, session scraping, browser profile access, network call, runtime execution, model/provider call, memory write, tool execution, remote execution, dependency, or production authority.
