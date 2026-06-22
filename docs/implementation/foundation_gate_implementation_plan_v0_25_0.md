# Foundation Gate Implementation Plan v0.25.0

Status: Historical Foundation Gate implementation plan for v0.25.0.

v0.25.0 adds the M21 criterion:

- `m21_openwebui_bridge_contract_safe`

The evaluator and verification suite verify:

- M21 OpenWebUI bridge source files exist.
- M21 OpenWebUI bridge docs exist.
- default OpenWebUI bridge manifest is contract-only.
- OpenWebUI is a supported local/dev conversational shell and compatibility
  surface.
- OpenWebUI is not the product cockpit or source of product state.
- OpenWebUI is not the agent brain.
- Python Agent Core remains authority.
- no OpenWebUI integration, deployment config, or runtime config is present.
- no OpenWebUI plugin/function/pipeline/tool/admin/auth workflow is enabled.
- no backend OpenWebUI routes are added.
- OpenAPI path count remains `74`.
- chat ingress and egress contracts reject raw content and secret-like metadata.
- chat ingress rejects direct tool execution, memory writes, runtime calls, and
  provider calls.
- chat egress rejects action execution, tool execution, memory writes, provider
  calls, runtime calls, and approval grants.
- arbitrary approval refs and session refs are identifiers only and never
  authority.
- M22 and M23 remain planned/provisional.

Safety boundary:

- no OpenWebUI implementation.
- no live OpenWebUI connection.
- no backend API route.
- no frontend feature.
- no runtime execution.
- no local LLM call.
- no model/provider call.
- no tool execution.
- no memory write.
- no file access.
- no remote execution.
- no browser automation.
- no Computer Use.
- no mobile sensor access.
- no plugin enablement.
- no dependency.
- no production authority.

## Skill Package Security Rule

v0.25.0 does not change the Skill Package Security Rule. It adds no plugin
enablement, tool installation, native build workflow, Computer Use automation,
Chrome authenticated profile control, or external action.

All skills are untrusted packages by default until a manifest with declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities
exist.
