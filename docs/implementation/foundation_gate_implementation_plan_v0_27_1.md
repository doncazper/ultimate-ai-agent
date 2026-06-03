# Foundation Gate Implementation Plan v0.27.1

Status: Current Foundation Gate plan for v0.27.1 / M23 Local LLM Call Safety
Hardening.

v0.27.1 hardens the `m23_first_local_llm_call_safe` criterion.

The criterion and supporting verifiers confirm:

- M23 local call contracts, policy, fake transport, manual transport, CLI, docs,
  and tests exist.
- the fixed prompt id is `m23_fixed_local_model_smoke_v1`.
- dry-run performs no endpoint contact.
- execution requires `--execute-local-call`.
- execution requires validated local approval evidence.
- forged allowed-looking approval decisions do not authorize transport calls.
- local endpoints are loopback-only HTTP.
- URL credentials, secret-like query keys, and secret-like query values are
  rejected.
- safe endpoint labels do not echo raw URL details.
- arbitrary prompt, stdin prompt, file prompt, clipboard prompt, memory prompt,
  OpenWebUI transcript prompt, user content, auth options, cookie options, and
  output-file options are not accepted.
- fake transport is used for tests and Foundation Gate.
- model output is non-authoritative.
- raw responses are not stored.
- secret-like responses are blocked/redacted.
- tools, memory writes, file writes, remote calls, provider calls, runtime
  activation, and endpoint probes are absent.
- no backend route is added.
- OpenAPI path count remains `74`.
- M24 remains future.

v0.27.1 also hardens Foundation Gate report writing. Latest JSON reports are
written to unique temp files in `reports/foundation_gate`, flushed and closed,
and published with atomic replace. Concurrent runs may be last-writer-wins, but
`latest_foundation_gate_report.json` must remain valid non-empty JSON.

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

M23 hardening does not enable skill packages, plugins, runtime tools, package
installers, or external execution.
