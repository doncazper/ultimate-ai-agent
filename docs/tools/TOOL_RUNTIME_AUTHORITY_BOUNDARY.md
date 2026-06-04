# Tool Runtime Authority Boundary

Status: active M31 documentation.
Current active baseline: **v0.35.1**

M31 proves a runtime adapter path without granting broad execution authority.

The following cannot authorize arbitrary tool execution:

- `approval_ref`
- `approval_test_*`
- approval decisions
- action policy decisions
- tool intents
- task plans
- execution state transitions
- context packs
- memory refs
- model output
- runtime output
- OpenWebUI output
- arbitrary strings

The only allowed runtime invocation is `tool:no_op.v1`. Approval refs are
identifiers, not authority. `approval_test_*` refs are test-only and are denied
as runtime authority.

v0.35.1 also denies caller-mutated hidden dispatch or side-effect fields before
authority checks can be treated as sufficient. A request cannot become
authorized by adding model_copy-only module/callable fields, side-effect fields,
or metadata that implies dynamic dispatch, file/memory/network/model/shell
access, environment reads, secret lookups, browser/mobile/remote/plugin actions,
or an alternate tool identity.

M31 adds no shell/file/memory/network/model/browser/mobile/remote/plugin tools,
no dynamic dispatch, no backend execute route, no Control Center execute
control, and no production authority.

M32-M40 remain planned/provisional.
