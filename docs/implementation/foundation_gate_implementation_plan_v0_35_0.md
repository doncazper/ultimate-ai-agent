# Foundation Gate Implementation Plan v0.35.0

Status: active implementation plan.

Current active baseline: **v0.35.0**

v0.35.0 adds Foundation Gate coverage for M31 Real Tool Runtime Adapter, Single
Safe No-Op Tool.

Gate coverage requires:

- Tool Runtime Adapter module files exist.
- M31 tool-runtime docs exist.
- manifest enables only the no-op runtime tool.
- arbitrary, dynamic, and side-effecting tools are disabled.
- shell/file/memory/network/model/browser/mobile/remote/plugin tools are
  disabled.
- no-op invocation succeeds deterministically.
- no-op result does not echo raw input.
- `side_effects_performed=[]`.
- unknown/effectful tools are denied.
- dynamic dispatch is denied.
- approval_ref and approval_test_ refs are denied as authority.
- task plan, context, memory, tool-intent, approval, and model refs cannot
  authorize arbitrary tool execution.
- raw/secret model_copy mutations are denied.
- replay-key reuse is denied.
- no backend execute route is added.
- OpenAPI path count remains `74`.
- M32-M40 remain planned/provisional.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default. Any future skill package must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

This plan adds no arbitrary tool execution, route, dependency, side effect, or
production authority.
