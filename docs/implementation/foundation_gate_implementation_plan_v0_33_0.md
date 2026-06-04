# Foundation Gate Implementation Plan v0.33.0

Status: active implementation plan.

Current active baseline: **v0.33.0**

v0.33.0 adds M29 Foundation Gate coverage for Agent Task Planning Engine contracts.

Gate coverage:

- M29 planning module exists.
- Required planning docs exist.
- Default manifest disables task execution, auto-run, scheduler runtime, tool/action execution, file mutation, memory writes, network calls, model/provider calls, browser/mobile/remote/plugin execution, context injection, backend execution routes, Control Center execute controls, dependencies, and production authority.
- Safe review-only plan succeeds with `valid_for_review=True`.
- All decisions keep `execution_authorized=False`, `execution_performed=False`, and `scheduler_registered=False`.
- Raw prompt/model/file/transcript input is denied.
- Secret-like metadata is denied.
- Model output, memory, context-pack, tool-intent, approval, runtime, OpenWebUI, and unknown refs cannot authorize a task plan.
- Effectful and executing task steps are denied.
- Caller risk downgrade is denied.
- Duplicate, missing, and cyclic dependency graphs are denied.
- OpenAPI path count remains `74`.
- M30-M40 remain planned/provisional.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default. Any future skill package must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.

This plan adds no runtime execution, backend routes, frontend features,
dependencies, or production authority.
