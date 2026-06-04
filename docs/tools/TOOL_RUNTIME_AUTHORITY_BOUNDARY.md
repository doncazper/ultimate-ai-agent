# Tool Runtime Authority Boundary

Status: active M32 documentation.
Current active baseline: **v0.37.1**

M32 adds one metadata-only filesystem tool without granting broad execution or
filesystem authority.

The following cannot authorize filesystem metadata access or arbitrary runtime
tools:

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
- Control Center refs
- arbitrary strings

The filesystem metadata tool remains bound to server-owned safe roots and
metadata-only output. It adds no shell, file content, file mutation, memory,
network, model, browser, mobile, remote, or plugin tools; no backend execute
routes; no Control Center execute controls; and no production authority.

M33 redacted file preview proposals are not authority and are not context
injection. Approval refs, `approval_test_*`, task plans, tool intents, context
packs, memory, model/runtime/OpenWebUI output, Control Center refs, and
arbitrary strings cannot authorize arbitrary filesystem access. v0.37.4
supersedes the future roadmap and M34-M60 remain planned/provisional.
