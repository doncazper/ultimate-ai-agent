# Action Policy

Status: active
Current through: v0.32.1
Purpose: Define non-executing M28 action policy evaluation.

M28 action policy evaluates structured action intents and returns policy
decisions only. It can allow a safe no-effect or read-metadata action for policy
planning with `execution_authorized=False` and `execution_performed=False`.

v0.32.1 hardens evaluator-side revalidation. Before any policy-only allow
decision, the evaluator rechecks current `ActionIntent`, `ApprovalGrant`, and
`ActionPolicy` state so `model_copy(update=...)` mutations cannot smuggle in raw
prompt/model/file/transcript flags, secret-like summaries, secret-like metadata,
metadata refs, `approval_test_` grant refs, wildcard scope, expired/revoked/
replayed grants, or actor/action/resource/scope mismatches.

Action policy denies:

- action execution, tool execution, shell execution, and destructive actions.
- file mutation, memory writes, Event Ledger mutation, network calls, and
  model/provider calls.
- browser, mobile/device, remote, and plugin actions.
- wildcard, expired, revoked, replayed, or mismatched approval grants.
- `approval_ref` alone, `approval_test_`, and `consent_ref` alone.
- model, memory, context-pack, or tool-intent refs as authorization.
- raw prompt, model, file, transcript, or secret-like action inputs.

Action policy decisions are non-authoritative planning records. They do not run,
dispatch, connect, send, mutate, approve production access, or create backend
execution routes.

M29 remains planned/provisional.
