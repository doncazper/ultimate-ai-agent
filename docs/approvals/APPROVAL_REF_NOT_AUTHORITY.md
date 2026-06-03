# Approval Ref Is Not Authority

Status: active
Current through: v0.32.0
Purpose: Preserve the approval authority boundary in M28.

`approval_ref` is an identifier, not authority. A caller-provided approval ref
does not authorize action execution, tool execution, file mutation, memory
writes, network calls, model/provider calls, browser/mobile/remote/plugin
actions, shell execution, or production authority.

M28 denies:

- `approval_ref` alone.
- `approval_test_` refs as runtime authority.
- `consent_ref` alone.
- model output refs as authorization.
- memory refs as authorization.
- context-pack refs as authorization.
- tool-intent refs as authorization.

Only a validated, matching, active, unexpired, unrevoked, unreplayed approval
grant can support a policy-only decision, and even that decision keeps
`execution_authorized=False` and `execution_performed=False`.

M29 remains planned/provisional.
