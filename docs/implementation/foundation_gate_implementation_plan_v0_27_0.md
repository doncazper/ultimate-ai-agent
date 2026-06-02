# Foundation Gate Implementation Plan v0.27.0

Status: Current Foundation Gate plan for v0.27.0 / M23 First Real Local LLM
Call, Non-Tool, Non-Authoritative.

v0.27.0 adds the `m23_first_local_llm_call_safe` criterion.

The criterion and supporting verifiers confirm:

- M23 local call contracts, policy, fake transport, manual transport, CLI, docs,
  and tests exist.
- the fixed prompt id is `m23_fixed_local_model_smoke_v1`.
- dry-run performs no endpoint contact.
- execution requires `--execute-local-call`.
- execution requires validated local approval.
- local endpoints are loopback-only HTTP.
- URL credentials and secret-like query strings are rejected.
- arbitrary prompt, stdin prompt, file prompt, clipboard prompt, memory prompt,
  OpenWebUI transcript prompt, and user content are not accepted.
- fake transport is used for tests and Foundation Gate.
- model output is non-authoritative.
- raw responses are not stored.
- secret-like responses are blocked/redacted.
- tools, memory writes, file writes, remote calls, provider calls, runtime
  activation, and endpoint probes are absent.
- no backend route is added.
- OpenAPI path count remains `74`.
- roadmap docs mark M23 implemented/released and keep M24-M40
  planned/provisional.

This plan adds no backend API route, runtime activation, endpoint probe,
provider SDK, runtime package, arbitrary prompt path, user-content model call,
OpenWebUI runtime bridge, Control Center execution control, tool execution,
memory write, file write, remote execution, mobile sensor access, plugin
enablement, dependency, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

M23 does not enable skill packages, plugins, runtime tools, package installers,
or external execution.
