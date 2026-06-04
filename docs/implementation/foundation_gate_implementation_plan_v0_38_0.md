# Foundation Gate Implementation Plan v0.38.0

Status: active Foundation Gate plan for v0.38.0.

v0.38.0 implements M34 Broader File Capability Review as a
planning/docs/verifier/Foundation Gate milestone only.

## Gate Coverage

Foundation Gate must cover:

- M34 broader file capability review docs exist.
- File Capability Boundary Matrix exists.
- File Capability Risk Register exists.
- File Capability Decision Record exists.
- M35 Safe File Review Workflow readiness doc exists.
- M34-to-M35 boundary doc exists.
- M34 is planning/review only.
- no raw file read routes.
- no file review UI.
- no approval capture or approval persistence.
- no context proposal or context injection.
- no memory write.
- no export.
- no execution or tool execution.
- no dependency additions.
- OpenAPI path count remains `74`.
- M35 remains planned/provisional.
- M36 remains planned/provisional.

## Blocked Drift

Gate must fail if M35 implementation appears, if file review UI appears, if
approval persistence appears, if raw file/context/memory/tool execution routes
appear, if route count changes unexpectedly, or if M35 is marked
implemented/released.

## No New Authority

M34 does not add runtime file capability, raw file reads, file review workflow,
review approval capture, context proposal, context injection, memory writes,
export, execution, backend routes, frontend runtime features, dependencies, or
production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
