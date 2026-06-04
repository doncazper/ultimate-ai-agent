# Ultimate AI Agent Version

Current active baseline: **v0.32.1**

v0.32.1 hardens M28 Approval Authority v2 + Action Policy Expansion. It adds
evaluator-side revalidation for `ActionIntent`, `ApprovalGrant`, and
`ActionPolicy` objects before any policy-only allow decision, blocks
`model_copy(update=...)` bypasses for raw prompt/model/file/transcript flags,
secret-like summaries, secret-like metadata, metadata refs, `approval_test_`
grant refs, expired/revoked/replayed grants, and wildcard/mismatched bindings,
and adds regression tests, static verifier probes, and Foundation Gate coverage.
It preserves safe no-effect/read-metadata policy decisions with
`execution_authorized=False` and `execution_performed=False`. It adds no action
execution, tool execution, shell/subprocess execution, file mutation, memory
writes, network calls, model/provider calls, browser automation, mobile/device
access, remote execution, plugin enablement, backend execution routes, frontend
execute controls, dependencies, production authority, or M29 work. M29-M40
remain planned/provisional.
