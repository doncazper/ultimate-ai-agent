# Local Runtime Activation Security Model

Status: Active M22 contract documentation for v0.27.0. Contract-only.

Python Agent Core remains the authority layer. Local runtime profiles are not authority. Approval refs are identifiers only and cannot authorize activation.

M22 security boundaries:

- no model was called.
- no runtime was activated.
- no endpoint was contacted.
- no user prompt, raw prompt, file content, memory content, credential, provider payload, or secret is represented.
- no tool call or memory write is allowed.
- no provider call or runtime execution is allowed.
- no backend API route is added.
- no dependency is added.

Secret-like metadata, URL credentials, secret-like query strings, remote hosts, private LAN hosts, public IP hosts, endpoint contact flags, runtime activation flags, provider credential flags, tool flags, and memory write flags are rejected by validation.

M23 is implemented/released by v0.27.0 as its own reviewed manual fixed-prompt
local model call path. M23 does not authorize runtime activation, endpoint
probes, arbitrary prompts, user-content model calls, OpenWebUI runtime behavior,
Control Center execution controls, tool execution, memory writes, file writes,
dependencies, or production authority.
