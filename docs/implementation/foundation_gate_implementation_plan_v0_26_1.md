# Foundation Gate Implementation Plan v0.26.1

Status: Current Foundation Gate plan for v0.26.1 / M22 safety hardening.

v0.26.1 keeps the `m22_local_model_runtime_activation_contract_safe` criterion
and hardens its supporting checks.

The criterion and supporting verifiers confirm:

- M22 contract files, docs, and tests exist.
- default local runtime activation manifest is contract-only.
- provider profiles are metadata-only and planned-disabled.
- activation, real model calls, runtime execution, provider calls, endpoint
  probes, user content, tool calls, memory writes, and secret material are
  disabled.
- metadata keys and values in activation policy/request/decision contracts are
  secret-hygiene checked.
- M22 scanner fragments do not fail harmless metadata `.get(...)` access.
- qualified runtime/network/model client calls remain blocked.
- no model was called.
- no runtime was activated.
- no endpoint was contacted.
- OpenAPI path count remains `74`.
- activation/probe/call backend routes are absent.
- roadmap docs mark M22 implemented and M23 planned/provisional.

This plan adds no backend API route, runtime execution, local LLM call, provider
call, endpoint probe, tool execution, memory write, file write, OpenWebUI
runtime behavior, dependency, or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

M22 does not enable skill packages, plugins, runtime tools, package installers,
or external execution.
